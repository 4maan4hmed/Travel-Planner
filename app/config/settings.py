from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str
    serpapi_key: str
    mongo_uri: str 
    mongo_db_name: str = "travel_planner"

    model_config = SettingsConfigDict(
        env_file=".env",         
        env_file_encoding="utf-8",
        case_sensitive=False,    
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()