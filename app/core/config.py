"""
Athena AI - Enterprise Configuration Engine
Module: app.core.config
Description: Validates environment variables dynamically using Pydantic Settings,
             providing absolute type safety across core systems.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnterpriseSettings(BaseSettings):
    """Encapsulates system settings with automatic environment fallback overrides."""
    
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "athena-dev-secret-key-change-in-production-123456789"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Secure API Credential Binding Layer
    OPENAI_API_KEY: str = "mock-openai-key-for-dev-and-testing"
    
    # FIX: Set to a valid, high-speed OpenAI production model identifier
    TARGET_LLM_MODEL: str = "gpt-4o-mini"
    
    # Network Bindings
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    BACKEND_URL: str = "http://127.0.0.1:8000"
    
    # Persistent Database Connections
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/athena"
    DOCUMENT_STORAGE_DIR: str = "storage/documents"
    TEMP_UPLOADS_DIR: str = "storage/temp_uploads"
    
    # Core ML Inference Hyperparameters
    DEFAULT_CONFIDENCE_THRESHOLD: float = 30.0
    MAX_BATCH_SIZE: int = 64
    
    # Pydantic reads your .env file automatically—no manual os.getenv() required!
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def initialize_storage_directories(self) -> None:
        """Enforces physical creation of required runtime data directories."""
        for path_str in [self.DOCUMENT_STORAGE_DIR, self.TEMP_UPLOADS_DIR]:
            Path(path_str).mkdir(parents=True, exist_ok=True)


# Instantiate the global configuration manager instance cleanly
settings = EnterpriseSettings()
settings.initialize_storage_directories()