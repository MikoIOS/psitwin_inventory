# app/config/settings.py

from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


class Settings(BaseSettings):

    # ============================================================
    # APLICACION
    # ============================================================

    app_name: str = "PsiTwin Inventory API"

    api_prefix: str = "/api/v1"


    # ============================================================
    # MONGODB
    # ============================================================

    mongodb_url: str = "mongodb://localhost:27017"

    mongodb_database: str = "psitwin_inventory"

    # ============================================================
    # OLLAMA / SAIKI
    # ============================================================

    ollama_base_url: str = "http://localhost:11434"

    ollama_model: str = "qwen3:4b"

    ollama_connect_timeout_seconds: float = 5.0

    ollama_read_timeout_seconds: float = 180.0


    # ============================================================
    # SEGURIDAD
    # ============================================================

    secret_key: str = (
        "psitwin-secret-key-cambiar-en-produccion"
    )

    algorithm: str = "HS256"

    access_token_expire_minutes: int = 60

    email_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True
    frontend_url: str | None = None
    email_verification_ttl_minutes: int = 10
    email_verification_cooldown_seconds: int = 60
    email_verification_max_attempts: int = 5


    # ============================================================
    # CORS
    #
    # Lista separada por comas. Ej:
    #
    # CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
    # ============================================================

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:

        return [
            origen.strip()
            for origen in self.cors_origins.split(",")
            if origen.strip()
        ]


    # ============================================================
    # MQTT (SENSORES)
    #
    # Broker Mosquitto: ver infra/mosquitto/README.md.
    # Si el broker no está, la API arranca igual y el
    # consumidor reintenta en segundo plano.
    # ============================================================

    mqtt_enabled: bool = True

    mqtt_host: str = "localhost"

    mqtt_port: int = 1883

    mqtt_tls: bool = False

    mqtt_ca_file: str | None = None

    mqtt_user: str = "psitwin-backend"

    mqtt_password: str = "backend-dev-123"


    # ============================================================
    # ENV
    # ============================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:

    return Settings()


# ================================================================
# INSTANCIA GLOBAL
#
# Permite usar:
#
# from app.config.settings import settings
#
# además de:
#
# settings = get_settings()
# ================================================================

settings = get_settings()
