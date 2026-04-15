from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/logout")
async def logout():
    """
    Não altera nada no banco.
    Redireciona para o endpoint de logout do PHP.
    O PHP é responsável por invalidar o token e limpar o cookie.
    """
    return RedirectResponse(url=settings.php_logout_url, status_code=302)