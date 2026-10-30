# app/config/settings.py

from functools import lru_cache
import os
from pydantic import Field, field_validator
from app.config.paths import BACKEND_ROOT, REPOSITORY_ROOT, runtime_path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


class Settings(BaseSettings):

    @field_validator('autogluon_artifact_dir', 'autogluon_python', 'autogluon_cache_dir',
                     'saiki_voice_python', 'saiki_voice_site_packages', 'saiki_piper_model', mode='after')
    @classmethod
    def stable_runtime_paths(cls, value):
        return str(runtime_path(value)) if value else value

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

    autogluon_artifact_dir: str = "artifacts/autogluon.local/psitwin_forecasting"
    autogluon_python: str = ".autogluon.local/Scripts/python.exe" if os.name == "nt" else ".autogluon.local/bin/python"
    autogluon_cache_dir: str = "artifacts/autogluon-cache.local"
    autogluon_timeout_seconds: int = 300
    autogluon_remote_url: str = ""
    ai_service_api_key: str = ""
    # Solo en EC2: Ollama local; Render usa OLLAMA_BASE_URL por HTTPS.
    ai_ollama_local_url: str = "http://127.0.0.1:11434"

    # ============================================================
    # OLLAMA / SAIKI
    # ============================================================

    ollama_base_url: str = "http://localhost:11434"

    ollama_model: str = "qwen3:4b"

    ollama_connect_timeout_seconds: float = 5.0

    ollama_read_timeout_seconds: float = 180.0
    ollama_num_threads: int = Field(default=4, ge=1, le=64)
    ollama_keep_alive: str = '5m'


    # ============================================================
    # SEGURIDAD
    # ============================================================

    secret_key: str = (
        "psitwin-secret-key-cambiar-en-produccion"
    )

    algorithm: str = "HS256"

    access_token_expire_minutes: int = 60
    google_client_id: str = ''
    google_client_secret: str = ''
    google_redirect_uri: str = 'http://localhost:5173/auth/google/callback'
    google_oauth_ttl_seconds: int = 600
    saiki_idle_timeout_seconds: float = 10.0
    saiki_request_timeout_seconds: float = 360.0
    saiki_database_timeout_seconds: float = 10.0
    saiki_model_start_timeout_seconds: float = 45.0
    saiki_model_max_tokens: int = Field(default=512, ge=32, le=8192)
    saiki_tts_enabled: bool = True
    saiki_tts_provider: str = 'kokoro'
    saiki_tts_model: str = 'hexgrad/Kokoro-82M'
    saiki_tts_voice: str = 'em_santa'
    saiki_tts_language: str = 'es'
    saiki_tts_speed: float = 1.0
    saiki_voice_python: str = '.voice.local/Scripts/python.exe' if os.name == 'nt' else '.voice.local/bin/python'
    saiki_voice_site_packages: str = ''
    saiki_voice_timeout_seconds: float = 120.0
    saiki_stt_enabled: bool = True
    saiki_stt_model: str = 'base'
    saiki_piper_model: str = ''

    email_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_app_password: str | None = None
    smtp_from_name: str = 'PsiTwin Inventory'
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True
    frontend_url: str | None = None

    @property
    def smtp_secret(self) -> str | None:
        return self.smtp_app_password or self.smtp_password
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
    sensor_disconnect_seconds: float = Field(default=5, gt=0, le=86400)
    sensor_max_reading_age_seconds: float = Field(default=5, gt=0, le=86400)

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
        env_file=(REPOSITORY_ROOT / '.env', BACKEND_ROOT / '.env'),
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
