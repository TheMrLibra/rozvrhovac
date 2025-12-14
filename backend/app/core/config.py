from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Rozvrhovac"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rozvrhovac"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - accept comma-separated string from env, convert to list
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Multi-tenancy
    ENV: str = "dev"  # dev or prod
    DEFAULT_TENANT_SLUG: Optional[str] = None  # Default tenant slug for dev
    MIGRATION_DEFAULT_TENANT_ID: Optional[str] = None  # UUID for migration backfill
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS to a list"""
        origins = os.getenv("CORS_ORIGINS", self.CORS_ORIGINS)
        if isinstance(origins, str):
            return [origin.strip() for origin in origins.split(",") if origin.strip()]
        return origins if isinstance(origins, list) else []
    
    @property
    def is_dev(self) -> bool:
        """Check if running in development mode"""
        return self.ENV.lower() == "dev"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

