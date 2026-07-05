import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Suproc Agent"
    API_V1_STR: str = "/api/v1"
    
    # Dataset Paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATASET_DIR: Path = BASE_DIR / "dataset"
    
    # Ollama LLM Settings
    OLLAMA_API_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    MOCK_LLM: bool = False
    
    # Agent Settings
    MAX_CORRECTION_ATTEMPTS: int = 3
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure dataset directory exists
settings.DATASET_DIR.mkdir(parents=True, exist_ok=True)
