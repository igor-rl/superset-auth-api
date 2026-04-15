import logging
import os
from celery.schedules import crontab
from flask_appbuilder.security.manager import AUTH_REMOTE_USER

logger = logging.getLogger()

# Autenticação via Remote User (Nginx)
AUTH_TYPE = AUTH_REMOTE_USER
AUTH_USER_REGISTRATION = True 
AUTH_USER_REGISTRATION_ROLE = "Admin"
# O Flask lê o header "REMOTE_USER" do Nginx como "REMOTE_USER"
AUTH_REMOTE_USER_ENV_VAR = "REMOTE_USER"

# Segurança e Proxy Fix
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "TEST_NON_DEV_SECRET")
ENABLE_PROXY_FIX = True

# FIX: Necessário para evitar erro de inicialização se a chave não existir
RECAPTCHA_ENABLED = False
RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_PUBLIC_KEY", "dummy")
RECAPTCHA_PRIVATE_KEY = os.getenv("RECAPTCHA_PRIVATE_KEY", "dummy")

# Banco de Dados
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@"
    f"{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_DB')}"
)

# Cache e Redis
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_CELERY_DB = os.getenv("REDIS_CELERY_DB", "0")
REDIS_RESULTS_DB = os.getenv("REDIS_RESULTS_DB", "1")

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": REDIS_RESULTS_DB,
}
DATA_CACHE_CONFIG = CACHE_CONFIG
THUMBNAIL_CACHE_CONFIG = CACHE_CONFIG

# Celery
class CeleryConfig:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    imports = ("superset.sql_lab", "superset.tasks.scheduler", "superset.tasks.thumbnails", "superset.tasks.cache")
    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    worker_prefetch_multiplier = 1
    task_acks_late = False
    beat_schedule = {
        "reports.scheduler": {"task": "reports.scheduler", "schedule": crontab(minute="*", hour="*")},
        "reports.prune_log": {"task": "reports.prune_log", "schedule": crontab(minute=10, hour=0)},
    }

CELERY_CONFIG = CeleryConfig

# Feature Flags
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "EMBEDDED_SUPERSET": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DATASET_FOLDERS": True,
}

# Jinja Context (RLS)
def get_user_id_header():
    from flask import request
    return request.headers.get('X-User-Id')

def get_empresa_id_header():
    from flask import request
    return request.headers.get('X-Empresa-Id')

JINJA_CONTEXT_ADDONS = {
    'current_user_id': get_user_id_header,
    'current_user_empresa_id': get_empresa_id_header,
}

logger.info("✅ Superset Config Ativa (Mock Mode)")