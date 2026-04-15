from fastapi import APIRouter, Request, Response, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.auth_service import validar_token
from app.services.superset_service import gerar_guest_token
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/guest-token")
async def guest_token(
    request: Request,
    dashboard_id: str = Query(..., description="UUID do dashboard no Superset"),
    db: AsyncSession = Depends(get_db),
):
    """
    Gera um Guest Token do Superset para embeddar dashboards.

    Fluxo:
    1. Valida a sessão do usuário (mesmo cookie)
    2. Usa o cntContas_codigo para montar o RLS
    3. Retorna o guest token para o frontend
    4. Frontend usa o token para embeddar o dashboard via iframe

    O RLS garante que o usuário só vê dados da empresa dele.
    """

    token = request.cookies.get(settings.cookie_name)

    if not token:
        raise HTTPException(status_code=401, detail="não autenticado")

    usuario = await validar_token(token, db)

    if not usuario:
        raise HTTPException(status_code=401, detail="sessão inválida ou expirada")

    try:
        guest = await gerar_guest_token(
            dashboard_id=dashboard_id,
            conta_codigo=usuario.cntContas_codigo,
            usuario_codigo=usuario.codigo,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar guest token: {str(e)}")

    return {"guest_token": guest}