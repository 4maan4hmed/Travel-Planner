from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str
    serpapi_key: str
    mongo_uri: str
    mongo_db_name: str = "travel_planner"

    # LangSmith observability (optional). Set LANGSMITH_TRACING=true to enable.
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "travel-planner"
    langsmith_endpoint: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()
