import logging

import os

from celery.schedules import crontab

from flask_appbuilder.security.manager import AUTH_REMOTE_USER



logger = logging.getLogger()



# ---------------------------------------------------------

# Autenticação via Nginx (Remote User)

# ---------------------------------------------------------

AUTH_TYPE = AUTH_REMOTE_USER

AUTH_USER_REGISTRATION = True  # Cria o usuário automaticamente no 1º acesso

AUTH_USER_REGISTRATION_ROLE = "Public"  # Role inicial (ajuste para Alpha se precisar de mais poder)

AUTH_REMOTE_USER_ENV_VAR = "HTTP_X_USER_LOGIN"



# Segurança e Proxy

SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "TEST_NON_DEV_SECRET")

RECAPTCHA_ENABLED = False

ENABLE_PROXY_FIX = True



# ---------------------------------------------------------

# Conexão com o Banco de Dados (Postgres Interno)

# ---------------------------------------------------------

SQLALCHEMY_DATABASE_URI = (

    f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@"

    f"{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_DB')}"

)



# ---------------------------------------------------------

# Configurações de Cache e Redis

# ---------------------------------------------------------

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



# ---------------------------------------------------------

# Celery (Workers)

# ---------------------------------------------------------

class CeleryConfig:

    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"

    imports = (

        "superset.sql_lab",

        "superset.tasks.scheduler",

        "superset.tasks.thumbnails",

        "superset.tasks.cache",

    )

    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"

    worker_prefetch_multiplier = 1

    task_acks_late = False

    beat_schedule = {

        "reports.scheduler": {

            "task": "reports.scheduler",

            "schedule": crontab(minute="*", hour="*"),

        },

        "reports.prune_log": {

            "task": "reports.prune_log",

            "schedule": crontab(minute=10, hour=0),

        },

    }



CELERY_CONFIG = CeleryConfig



# ---------------------------------------------------------

# Feature Flags e UI

# ---------------------------------------------------------

FEATURE_FLAGS = {

    "ALERT_REPORTS": True,

    "EMBEDDED_SUPERSET": True,

    "DASHBOARD_NATIVE_FILTERS": True,

    "DATASET_FOLDERS": True,

}



# ---------------------------------------------------------

# Injeção de Contexto (Jinja) para Filtros RLS

# ---------------------------------------------------------

def get_user_id_header():

    from flask import request

    try:

        return request.headers.get('X-User-Id')

    except Exception:

        return None



def get_empresa_id_header():

    from flask import request

    try:

        return request.headers.get('X-Empresa-Id')

    except Exception:

        return None



JINJA_CONTEXT_ADDONS = {

    'current_user_id': get_user_id_header,

    'current_user_empresa_id': get_empresa_id_header,

}



logger.info("✅ Superset Config (Produção/SSO) carregado com sucesso!")