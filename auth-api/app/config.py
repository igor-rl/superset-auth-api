from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Banco de dados
    db_host: str
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str

    # API
    api_port: int = 8001
    api_env: str = "production"
    api_secret_key: str

    # Cookie
    cookie_name: str = "session_token"
    cookie_secret: str

    # Superset
    superset_url: str
    superset_admin_user: str
    superset_admin_password: str

    # PHP
    php_login_url: str
    php_logout_url: str
    php_base_url: str

    # Segurança
    allowed_origins: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()