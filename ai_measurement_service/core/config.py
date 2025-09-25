"""
Configuration settings for AI Measurement Service
"""

import os
from typing import List, Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic app configuration
    PROJECT_NAME: str = "AI Measurement Service"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]
    
    # Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "your-secret-key-change-in-production"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/jpg"]
    UPLOAD_DIR: str = os.path.join(os.path.dirname(__file__), "..", "uploads")
    
    # AI/ML Configuration
    MEDIAPIPE_MODEL_COMPLEXITY: int = 1  # 0, 1, or 2
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE: float = 0.5
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE: float = 0.5
    
    # Measurement calculation settings
    REFERENCE_HEIGHT_CM: float = 170.0  # Default reference height
    PIXEL_TO_CM_RATIO: Optional[float] = None  # Will be calculated per image
    
    # Integration with Django Fashion App
    DJANGO_API_URL: str = os.getenv(
        "DJANGO_API_URL", 
        "http://localhost:8000/api"
    )
    DJANGO_API_KEY: Optional[str] = os.getenv("DJANGO_API_KEY")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Database (optional - for caching results)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    class Config:
        case_sensitive = True
        env_file = ".env"


# Create settings instance
settings = Settings()


# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)