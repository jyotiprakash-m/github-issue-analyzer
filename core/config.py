from pydantic_settings import BaseSettings

# Configuration settings for the application
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///database.db"  # or use your preferred database URL
    USERNAME: str = "admin" # default username for basic auth
    PASSWORD: str = "password" # default password for basic auth
    OPENAI_API_KEY: str = "your-openai-api-key" # OpenAI API key
    class Config:
        env_file = ".env"

settings = Settings()