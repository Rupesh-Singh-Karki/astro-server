from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH, env_file_encoding="utf-8", extra="ignore"
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


settings = Settings()
