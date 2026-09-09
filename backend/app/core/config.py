from pydantic_settings import BaseSettings


from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    supervisor_registration_code: str

    class Config:
        env_file = str(ENV_PATH)


settings = Settings()