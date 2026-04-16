from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.database.connection import get_db
from app.services.auth_service import validar_token
from app.config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/verify")
async def verify(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Nginx chama este endpoint antes de liberar qualquer acesso ao Superset.
    """

    # 1. Tenta ler o token real do cookie
    token = request.cookies.get(settings.cookie_name)
    
    # 2. Lógica de "Fallback" para Teste
    # Se não houver cookie, mas existir a variável de ambiente TEST_SESSION_TOKEN
    test_token = os.getenv("TEST_SESSION_TOKEN")
    
    if not token and test_token:
        token = test_token
        print(f"⚠️  [TEST MODE] Token injetado via variável de ambiente: {token}")
    else:
        print(f"[VERIFY] cookies={dict(request.cookies)} token={token}")

    # Se mesmo após o fallback não houver token, barra o acesso
    if not token:
        return Response(status_code=401, content="sem token")

    # 3. Valida no banco (O token injetado também será validado no MySQL)
    usuario = await validar_token(token, db)

    if not usuario:
        print(f"❌ [AUTH FAILED] Token inválido ou expirado no banco: {token}")
        return Response(status_code=401, content="token inválido ou expirado")

    # 4. Sucesso: Retorna os headers para o Nginx
    headers = {
        "X-User-Id": str(usuario.codigo),
        "X-Empresa-Id": str(usuario.cntContas_codigo),
        "X-User-Login": usuario.login,
        "X-User-Nome": usuario.nome,
        "X-User-Tipo": str(usuario.cntUsuariosTipo_codigo or ""),
    }

    return Response(status_code=200, headers=headers)