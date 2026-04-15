import httpx
from typing import Optional
from app.config import get_settings

settings = get_settings()

# token admin em memória para reutilizar enquanto válido
_superset_token: Optional[str] = None


async def _login_superset() -> str:
    """Autentica no Superset e retorna o access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.superset_url}/api/v1/security/login",
            json={
                "username": settings.superset_admin_user,
                "password": settings.superset_admin_password,
                "provider": "db",
                "refresh": True,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def _get_csrf_token(access_token: str) -> str:
    """Obtém o CSRF token necessário para o guest token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.superset_url}/api/v1/security/csrf_token/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["result"]


async def gerar_guest_token(
    dashboard_id: str,
    conta_codigo: int,
    usuario_codigo: int,
) -> str:
    """
    Gera um Guest Token do Superset com RLS da empresa.
    O RLS injeta automaticamente: empresa_id = conta_codigo em todas as queries.
    """
    access_token = await _login_superset()
    csrf_token = await _get_csrf_token(access_token)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.superset_url}/api/v1/security/guest_token/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-CSRFToken": csrf_token,
                "Content-Type": "application/json",
            },
            json={
                "user": {
                    "username": f"guest_u{usuario_codigo}",
                    "first_name": "Guest",
                    "last_name": f"Empresa{conta_codigo}",
                },
                "resources": [
                    {
                        "type": "dashboard",
                        "id": dashboard_id,
                    }
                ],
                "rls": [
                    {
                        # injeta WHERE empresa_id = conta_codigo em todas as queries
                        "clause": f"empresa_id = {conta_codigo}"
                    }
                ],
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["token"]