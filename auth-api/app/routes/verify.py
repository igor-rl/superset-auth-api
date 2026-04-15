from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.auth_service import validar_token
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/verify")
async def verify(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Nginx chama este endpoint antes de liberar qualquer acesso ao Superset.

    Fluxo:
    - Lê o token do cookie
    - Valida no banco (ativo, não expirado, não excluído)
    - 200 → Nginx passa pro Superset com headers do usuário
    - 401 → Nginx redireciona pro login PHP
    """

    # lê o token do cookie
    token = request.cookies.get(settings.cookie_name)

    if not token:
        return Response(status_code=401, content="sem token")

    # valida no banco
    usuario = await validar_token(token, db)

    if not usuario:
        return Response(status_code=401, content="token inválido ou expirado")

    # retorna 200 com headers que o Nginx injeta no request pro Superset
    headers = {
        "X-User-Id": str(usuario.codigo),
        "X-Empresa-Id": str(usuario.cntContas_codigo),
        "X-User-Login": usuario.login,
        "X-User-Nome": usuario.nome,
        "X-User-Tipo": str(usuario.cntUsuariosTipo_codigo or ""),
    }

    return Response(status_code=200, headers=headers)