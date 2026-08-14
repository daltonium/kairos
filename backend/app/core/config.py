from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    OPENROUTER_API_KEY: str
    AI_MODEL_REASONING: str = "deepseek/deepseek-r1:free"
    AI_MODEL_CODE: str = "qwen/qwen3-coder:free"
    APP_URL: str = "http://localhost:8000"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RESEND_API_KEY: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = ""

    class Config:
        env_file = ".env"

settings = Settings()