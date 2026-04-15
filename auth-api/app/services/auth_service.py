from datetime import date
from typing import Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.usuario import CntUsuarios, UsuarioValidado

# Configuração de log para ajudar no debug via Docker logs
logger = logging.getLogger(__name__)

async def validar_token(token: str, db: AsyncSession) -> Optional[UsuarioValidado]:
    """
    Valida o token de sessão consultando o banco de dados via túnel SSH.
    
    Verificações:
    - Token coincide com 'regravar_token'
    - Usuário está ativo (ativo = 1)
    - Usuário não foi removido (excluido = 0)
    - Data de expiração é hoje ou no futuro (data_expiracao >= hoje)
    """
    if not token:
        return None

    try:
        hoje = date.today()

        # Executa a consulta de forma assíncrona
        result = await db.execute(
            select(CntUsuarios).where(
                CntUsuarios.regravar_token == token,
                CntUsuarios.ativo == 1,
                CntUsuarios.excluido == 0,
                CntUsuarios.data_expiracao >= hoje
            )
        )
        
        usuario = result.scalar_one_or_none()

        if not usuario:
            # Se não retornar nada, o token pode estar errado ou expirado
            return None

        # Retorna o Pydantic Model (UsuarioValidado) preenchido
        return UsuarioValidado(
            codigo=usuario.codigo,
            nome=usuario.nome,
            login=usuario.login,
            cntContas_codigo=usuario.cntContas_codigo,
            cntUsuariosTipo_codigo=usuario.cntUsuariosTipo_codigo,
            ultimo_acesso_ip=usuario.ultimo_acesso_ip,
            ultimo_acesso_datahora=usuario.ultimo_acesso_datahora,
        )

    except Exception as e:
        # Se o túnel SSH cair ou o banco falhar, o erro aparece no 'docker compose logs'
        logger.error(f"❌ Erro ao validar token no banco de dados: {str(e)}")
        raise