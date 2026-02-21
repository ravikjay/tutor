from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./voicecoach.db"
    google_api_key: str = ""
    modulate_api_key: str = ""
    airia_api_key: str = ""
    airia_pipeline_id: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
