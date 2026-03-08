from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")  # must stay snake_case

    ollamaBaseUrl: str = "http://localhost:11434"
    ollamaModel: str = "qwen2.5:3b"
    corsOrigins: list[str] = ["http://localhost:3000"]

    maxRecentPairs: int = 6
    maxMiddlePairs: int = 4
    maxTotalChars: int = 6000

settings = Settings()
