import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY: str | None = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set in the environment")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    SETTINGS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("SETTINGS_TOKEN_EXPIRE_MINUTES", "10")
    )
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./auth.db")


settings = Settings()
