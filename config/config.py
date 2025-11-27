<<<<<<< HEAD
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_VITAL_SIGNS: str = "patient-vital-signs"
    KAFKA_TOPIC_ALERTS: str = "patient-alerts"
    KAFKA_CONSUMER_GROUP: str = "icu-consumers"
    
    # PostgreSQL
    POSTGRES_USER: str = "icu_user"
    POSTGRES_PASSWORD: str = "icu_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "icu_db"
    
    @property
    def POSTGRES_DSN(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_postgres_url(self) -> str:
        return self.POSTGRES_DSN
    
    # InfluxDB (v2 style - with token auth)
=======
"""
Configuration management for ICU Monitoring System
"""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "icu_user"
    POSTGRES_PASSWORD: str = "icu_password"
    POSTGRES_DB: str = "icu_db"
    
    # InfluxDB
>>>>>>> 5518597 (Initial commit: reset and push to master)
    INFLUX_URL: str = "http://localhost:8086"
    INFLUX_TOKEN: str = "my-super-secret-auth-token"
    INFLUX_ORG: str = "icu_org"
    INFLUX_BUCKET: str = "vital_signs"
    
<<<<<<< HEAD
    # InfluxDB (v1 style - legacy, kept for backward compatibility)
    INFLUX_HOST: str = "localhost"
    INFLUX_PORT: int = 8086
    INFLUX_USER: str = "admin"
    INFLUX_PASSWORD: str = "admin123"
    INFLUX_DB: str = "icu_db"
=======
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "127.0.0.1:9092"
    KAFKA_TOPIC_VITAL_SIGNS: str = "patient-vital-signs"
    KAFKA_TOPIC_ALERTS: str = "patient-alerts"
    KAFKA_CONSUMER_GROUP: str = "icu-consumers"
    
    # Redis (for caching and alerts)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Application
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    # ✅ ADD: Logging directory
    LOG_DIR: Path = Path(__file__).parent.parent / "logs"

    # ML Model Integration
    USE_ML_MODEL: bool = True
    MODEL_PATH: Path = Path(__file__).parent.parent / "data" / "models" / "risk_model.joblib"
>>>>>>> 5518597 (Initial commit: reset and push to master)
    
    # Producer settings
    NUM_PATIENTS: int = 10
    READING_INTERVAL_SECONDS: float = 1.0
    
<<<<<<< HEAD
    # Profile distribution
=======
    # Patient profile distribution
>>>>>>> 5518597 (Initial commit: reset and push to master)
    PROFILE_DISTRIBUTION_HEALTHY: float = 0.7
    PROFILE_DISTRIBUTION_AT_RISK: float = 0.2
    PROFILE_DISTRIBUTION_CRITICAL: float = 0.1
    
<<<<<<< HEAD
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = Path("logs")
    ALERT_MODEL_PATH: str = "data/models/alert_classifier.joblib"
    ALERT_MODEL_THRESHOLD: float = 0.5
    TRAINING_DATA_PATH: str = "data/patients_data_with_alerts.xlsx"
=======
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ✅ Ensure log directory exists
        self.LOG_DIR.mkdir(exist_ok=True)
    
    def get_postgres_url(self, async_driver: bool = False) -> str:
        """Get PostgreSQL connection URL"""
        driver = "postgresql+asyncpg" if async_driver else "postgresql+psycopg2"
        return (
            f"{driver}://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    def get_postgres_dsn(self) -> str:
        """Get PostgreSQL DSN for direct connections"""
        return (
            f"host={self.POSTGRES_HOST} "
            f"port={self.POSTGRES_PORT} "
            f"dbname={self.POSTGRES_DB} "
            f"user={self.POSTGRES_USER} "
            f"password={self.POSTGRES_PASSWORD}"
        )
>>>>>>> 5518597 (Initial commit: reset and push to master)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
<<<<<<< HEAD
        extra = "allow"  # Allow extra fields from .env without error

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
=======
        extra = "allow"

# Global settings instance
settings = Settings()
>>>>>>> 5518597 (Initial commit: reset and push to master)
