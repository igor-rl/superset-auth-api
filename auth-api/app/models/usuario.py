from sqlalchemy import Column, Integer, String, DateTime, Date, SmallInteger
from sqlalchemy.dialects.mysql import TIMESTAMP
from app.database.connection import Base
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


# ─── SQLAlchemy ORM ───────────────────────────────────────────────────────────
# Apenas mapeamento de leitura — não cria nem altera nada no banco

class CntUsuarios(Base):
    __tablename__ = "cntUsuarios"

    codigo                 = Column(Integer, primary_key=True, autoincrement=True)
    cadastrado             = Column(TIMESTAMP)                        # timestamp nullable
    cntContas_codigo       = Column(Integer, nullable=False)          # empresa do usuário
    nome                   = Column(String(200), nullable=False)
    login                  = Column(String(30), nullable=False)
    senha                  = Column(String(32), nullable=False)
    email                  = Column(String(200), nullable=False)
    flag_restricao_tags    = Column(SmallInteger, nullable=False, default=0)  # tinyint(1)
    data_expiracao         = Column(Date)                             # DATE, não DATETIME
    regravar_datahora      = Column(TIMESTAMP)                        # timestamp nullable
    regravar_token         = Column(String(32))                       # varchar(32)
    ultimo_acesso_ip       = Column(String(15))                       # varchar(15)
    ultimo_acesso_datahora = Column(DateTime)
    ativo                  = Column(SmallInteger, nullable=False, default=1)  # tinyint(1)
    excluido               = Column(SmallInteger, nullable=False, default=0)  # tinyint(1)
    excluido_data_hora     = Column(DateTime)
    cntUsuariosTipo_codigo = Column(Integer, default=1)


# ─── Pydantic Schema ──────────────────────────────────────────────────────────

class UsuarioValidado(BaseModel):
    """Retorno após validação bem sucedida do token"""
    codigo: int
    nome: str
    login: str
    cntContas_codigo: int
    cntUsuariosTipo_codigo: Optional[int]
    ultimo_acesso_ip: Optional[str]
    ultimo_acesso_datahora: Optional[datetime]

    class Config:
        from_attributes = True