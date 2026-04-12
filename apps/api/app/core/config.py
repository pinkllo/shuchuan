from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_prefix: str = "/api"
    app_name: str = "data-platform-api"
    database_url: str = "sqlite:///./data-platform.db"
    secret_key: str = "dev-secret-key"
    access_token_expire_minutes: int = 60
    upload_root: str = "uploads"
    frontend_origins: str = ",".join(
        [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )


settings = Settings()
