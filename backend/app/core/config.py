from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Rozvrhovac"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rozvrhovac"
    
    # Registry Database (for multi-tenant setup)
    REGISTRY_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rozvrhovac_registry"
    
    # Database connection defaults (used when creating new school databases)
    DEFAULT_DB_HOST: str = "localhost"
    DEFAULT_DB_PORT: int = 5432
    DEFAULT_DB_USER: str = "postgres"
    DEFAULT_DB_PASSWORD: str = "postgres"  # Should be set via environment variable in production
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - accept comma-separated string from env, convert to list
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS to a list"""
        origins = os.getenv("CORS_ORIGINS", self.CORS_ORIGINS)
        if isinstance(origins, str):
            return [origin.strip() for origin in origins.split(",") if origin.strip()]
        return origins if isinstance(origins, list) else []
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

