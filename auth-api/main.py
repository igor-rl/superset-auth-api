from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
import sys

from app.config import get_settings
from app.database.connection import engine
from app.routes import verify, logout, guest_token


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    print(f"🔍 Verificando conexão com o banco: {settings.db_host}")
    
    try:
        # Tenta conectar e executar uma query simples
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Banco de dados conectado com sucesso!")
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: Não foi possível conectar ao banco.")
        print(f"Detalhes: {e}")
        # Encerra o processo com erro. 
        # Se estiver no Docker/K8s, o orquestrador tentará reiniciar.
        sys.exit(1) 

    yield
    
    # --- SHUTDOWN ---
    await engine.dispose()
    print("🔴 Auth API encerrada")


app = FastAPI(
    title="Auth API",
    description="Autenticação SSO entre PHP e Superset",
    version="1.0.0",
    lifespan=lifespan,
    # desabilita docs em produção
    docs_url="/docs" if settings.api_env == "development" else None,
    redoc_url="/redoc" if settings.api_env == "development" else None,
)

# CORS — apenas origens permitidas
origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

# rotas
app.include_router(verify.router,      prefix="/auth", tags=["auth"])
app.include_router(logout.router,      prefix="/auth", tags=["auth"])
app.include_router(guest_token.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health():
    """Nginx usa para verificar se a API está de pé."""
    return {"status": "ok"}