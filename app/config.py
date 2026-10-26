from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "FurniFind AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT.as_posix()}/furnifind.db"

    # Retrieval Models
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    VISION_MODEL_NAME: str = "clip-ViT-B-32"
    USE_LOCAL_EMBEDDINGS: bool = True
    INDEX_CACHE_DIR: Path = PROJECT_ROOT / ".cache"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    SAMPLE_CATALOGUE_PATH: Path = PROJECT_ROOT / "data" / "sample_catalogue.json"
    EVALUATION_QUERIES_PATH: Path = PROJECT_ROOT / "data" / "evaluation_queries.json"

    # Optional LLM
    LLM_PROVIDER: str = "none"  # "none", "openai", "gemini"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
