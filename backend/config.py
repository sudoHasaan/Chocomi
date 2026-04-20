from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")  # must stay snake_case

    ollamaBaseUrl: str = "http://localhost:11434"
    ollamaModel: str = "qwen2.5:1.5b" # CHANGE
    corsOrigins: list[str] = ["http://localhost:3000"]

    maxRecentPairs: int = 4
    maxMiddlePairs: int = 4
    maxTotalChars: int = 6000

    # Voice pipeline
    asrModel: str = "UsefulSensors/moonshine-tiny"  # Moonshine model name on Hub
    ttsModel: str = "en_US-lessac-medium"
    ttsDataDir: str = "tts_models"

settings = Settings()
