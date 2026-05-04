from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_PATH: str = "/app/media"
    MEDIA_URL_PREFIX: str = "/media"

    OPENAI_API_KEY: str
    FLUX_ENABLED: bool = False
    FLUX_API_URL: str = ""
    FLUX_API_KEY: str = ""

    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_MIME_TYPES: str = "image/jpeg,image/png,image/webp"

    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_GENERATIONS_PER_DAY: int = 50

    LOG_LEVEL: str = "INFO"
    APP_ENV: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
