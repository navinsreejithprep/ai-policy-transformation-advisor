from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "openai"  # "openai" or "anthropic" — see app/agents/definitions.py
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-haiku-4-5-20251001"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    chroma_path: str = "./chroma_db"
    vector_db_path: str = ""  # alias for chroma_path, kept for naming parity with the spec
    # Relative to the backend process's working directory (run from backend/, per README).
    knowledge_base_path: str = "./knowledge_base"

    top_k_default: int = 5
    retrieval_relevance_threshold: float = 0.35  # cosine similarity floor; below this a hit is dropped
    chunk_size: int = 900
    chunk_overlap: int = 120

    max_upload_mb: int = 20
    revision_max_cycles: int = 2

    log_path: str = "./logs/app.log"

    # Comma-separated list of allowed frontend origins for CORS. Defaults to local
    # dev; set to your deployed frontend's URL (e.g. https://your-app.vercel.app)
    # in production — see ALLOWED_ORIGINS in .env.example.
    allowed_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def resolved_chroma_path(self) -> str:
        return self.vector_db_path or self.chroma_path

    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
