from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b" # change to 3b
    max_history_chars: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

settings = Settings()