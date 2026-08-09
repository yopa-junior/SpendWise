from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SpendWise"
    ENVIRONMENT: str = "development"

    # Base de données
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/spendwise"

    # Sécurité / JWT
    SECRET_KEY: str = "change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str = "SpendWise"
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    
    # IA
    
    GEMINI_API_KEY: str
    

    # Frontend (pour les liens dans les emails)
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()