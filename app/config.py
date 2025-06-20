from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration with environment variable support."""
    
    app_name: str = Field(default="FastAPI Health Check Demo", description="Application name",)
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Database Configuration (optional) 
    database_url: Optional[str] = Field(default=None, description="Database connection string")
    
    # Redis Configuration (optional)
    redis_url: Optional[str] = Field(default=None, description="Redis connection string")
    
    # Health Check Configuration
    health_check_timeout: float = Field(default=5.0, description="Health check timeout in seconds")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    return Settings()