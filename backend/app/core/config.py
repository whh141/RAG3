from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Agentic RAG QA"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "sqlite:///./qa_system.db"
    upload_dir: str = "./data/uploads"
    chroma_db_dir: str = "./data/chroma"
    default_model_provider: str = "zhipuai"
    default_agent_mode: str = "agentic_rag"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_runtime_dirs(self) -> None:
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_db_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_runtime_dirs()
