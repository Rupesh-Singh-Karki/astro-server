from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"

# Load .env file into os.environ so that all variables are available
# This is needed for variables like GEMINI_API_KEY that aren't in Settings
load_dotenv(ENV_PATH)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    db_uri: str
    root_path: str = ""
    logging_level: str = "INFO"
    jwt_secret_key: str
    jwt_algorithm: str = "HS512"
    jwt_access_token_expire_minutes: int = 720
    jwt_refresh_token_expire_days: int = 7

    # SMTP Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str = "Astro Server"

    # OTP Configuration
    otp_length: int = 6
    otp_expire_minutes: int = 10
    otp_max_attempts: int = 5

    # Backend URL for keep-alive pings
    base_url: str = "http://localhost:8000"


settings = Settings()
