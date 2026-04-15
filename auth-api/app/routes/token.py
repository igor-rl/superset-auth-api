from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.usuario import TokenRequest, TokenResponse
from app.services.auth_service import gerar_token
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/token", response_model=TokenResponse)
async def criar_token(
    payload: TokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    PHP chama este endpoint após autenticar o usuário com sucesso.

    Fluxo:
    1. PHP valida login/senha normalmente
    2. PHP chama POST /auth/token com usuario_codigo e conta_codigo
    3. FastAPI gera token seguro e salva no banco
    4. PHP recebe o token e seta o cookie httpOnly no browser
    """

    ip = payload.ip or (request.client.host if request.client else None)

    try:
        token, expira_em = await gerar_token(
            usuario_codigo=payload.usuario_codigo,
            conta_codigo=payload.conta_codigo,
            ip=ip,
            db=db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar token: {str(e)}")

    return TokenResponse(token=token, expira_em=expira_em)