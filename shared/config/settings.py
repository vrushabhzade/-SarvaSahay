"""
SarvaSahay Platform Configuration
Centralized configuration management using Pydantic Settings
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(default="postgresql://localhost/sarvasahay", env="DATABASE_URL")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    echo: bool = Field(default=False, env="DB_ECHO")
    
    class Config:
        env_prefix = "DB_"


class RedisSettings(BaseSettings):
    """Redis cache configuration"""
    url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    
    class Config:
        env_prefix = "REDIS_"


class AIMLSettings(BaseSettings):
    """AI/ML configuration"""
    model_path: str = Field(default="ml/models/eligibility", env="ML_MODEL_PATH")
    model_accuracy_threshold: float = Field(default=0.89, env="ML_ACCURACY_THRESHOLD")
    max_evaluation_time: float = Field(default=5.0, env="ML_MAX_EVALUATION_TIME")
    retrain_interval_hours: int = Field(default=168, env="ML_RETRAIN_INTERVAL")  # Weekly
    
    @validator('model_accuracy_threshold')
    def validate_accuracy(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Model accuracy threshold must be between 0 and 1')
        return v
    
    class Config:
        env_prefix = "ML_"


class GovernmentAPISettings(BaseSettings):
    """Government API integration settings"""
    pm_kisan_base_url: str = Field(default="https://api.pmkisan.gov.in", env="PM_KISAN_API_URL")
    dbt_base_url: str = Field(default="https://api.dbt.gov.in", env="DBT_API_URL")
    pfms_base_url: str = Field(default="https://api.pfms.gov.in", env="PFMS_API_URL")
    
    api_timeout: int = Field(default=30, env="GOV_API_TIMEOUT")
    max_retries: int = Field(default=3, env="GOV_API_MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="GOV_API_RETRY_DELAY")
    
    # API Keys (should be set via environment variables)
    pm_kisan_api_key: Optional[str] = Field(None, env="PM_KISAN_API_KEY")
    dbt_api_key: Optional[str] = Field(None, env="DBT_API_KEY")
    pfms_api_key: Optional[str] = Field(None, env="PFMS_API_KEY")
    
    class Config:
        env_prefix = "GOV_API_"


class SecuritySettings(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(default="dev-secret-key-change-in-production-32chars", env="SECRET_KEY")
    encryption_key: str = Field(default="dev-encryption-key-change-in-production-32chars", env="ENCRYPTION_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # Password hashing
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")
    
    @validator('secret_key', 'encryption_key')
    def validate_keys(cls, v):
        if len(v) < 32:
            raise ValueError('Security keys must be at least 32 characters long')
        return v
    
    class Config:
        env_prefix = "SECURITY_"


class SMSSettings(BaseSettings):
    """SMS service configuration"""
    provider: str = Field(default="twilio", env="SMS_PROVIDER")
    account_sid: Optional[str] = Field(None, env="TWILIO_ACCOUNT_SID")
    auth_token: Optional[str] = Field(None, env="TWILIO_AUTH_TOKEN")
    from_number: Optional[str] = Field(None, env="TWILIO_FROM_NUMBER")
    
    class Config:
        env_prefix = "SMS_"


class PerformanceSettings(BaseSettings):
    """Performance and monitoring configuration"""
    max_concurrent_users: int = Field(default=1000, env="MAX_CONCURRENT_USERS")
    max_simultaneous_evaluations: int = Field(default=10000, env="MAX_SIMULTANEOUS_EVALUATIONS")
    uptime_requirement: float = Field(default=0.995, env="UPTIME_REQUIREMENT")  # 99.5%
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    class Config:
        env_prefix = "PERF_"


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    file_path: Optional[str] = Field(None, env="LOG_FILE_PATH")
    max_file_size: str = Field(default="100MB", env="LOG_MAX_FILE_SIZE")
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    class Config:
        env_prefix = "LOG_"


class Settings(BaseSettings):
    """Main application settings"""
    # Application metadata
    app_name: str = Field(default="SarvaSahay Platform", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # API configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    
    # CORS settings
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE"], env="CORS_METHODS")
    
    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    ai_ml: AIMLSettings = AIMLSettings()
    government_apis: GovernmentAPISettings = GovernmentAPISettings()
    security: SecuritySettings = SecuritySettings()
    sms: SMSSettings = SMSSettings()
    performance: PerformanceSettings = PerformanceSettings()
    logging: LoggingSettings = LoggingSettings()
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of: {allowed_envs}')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from .env file


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance"""
    return settings