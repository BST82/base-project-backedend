from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Restaurant Cloud Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database & Cache (Live Supabase Cloud Database)
    DATABASE_URL: str = "postgresql://postgres:9flG9GDbl4HlCTVf@db.wakrdqdxtyzxbplxfibc.supabase.co:5432/postgres"
    # Local Database (Commented out):
    # DATABASE_URL: str = "postgresql://postgres:root@localhost:5432/restaurant"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # JWT Authentication
    SECRET_KEY: str = "super_secret_jwt_signing_key_change_in_production_32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Payment Gateways
    RAZORPAY_KEY_ID: str = "rzp_test_sample"
    RAZORPAY_KEY_SECRET: str = "rzp_secret_sample"
    RAZORPAY_WEBHOOK_SECRET: str = "rzp_webhook_secret_sample"

    STRIPE_SECRET_KEY: str = "sk_test_sample"
    STRIPE_WEBHOOK_SECRET: str = "whsec_sample"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost", "http://localhost:80", "http://localhost:4200"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            import json
            return json.loads(v)
        return v

    # Reservation settings
    RESERVATION_HOLD_SECONDS: int = 600  # 10 minutes hold in Redis while completing payment
    PREPAYMENT_DEPOSIT_AMOUNT: float = 25.00  # Default deposit per reservation

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
