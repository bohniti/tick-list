from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://tick_list:secret@localhost:5432/tick_list"
    api_token: str = "changeme"
    environment: str = "development"
    photo_dir: str = "data/photos"


settings = Settings()
