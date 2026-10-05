from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Sistema de Gestión y Venta EPMVS"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://sgv_epmvs:CAMBIAR_CLAVE_SEGURA@db:5432/sgv_epmvs"
    secret_key: str = "CAMBIAR_SECRET_KEY"
    jwt_secret_key: str = "CAMBIAR_JWT_SECRET_KEY"
    access_token_expire_minutes: int = 60
    upload_path: str = "/app/storage"
    tz: str = "America/Guayaquil"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
