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
    INFLUX_URL: str = "http://localhost:8086"
    INFLUX_TOKEN: str = "my-super-secret-auth-token"
    INFLUX_ORG: str = "icu_org"
    INFLUX_BUCKET: str = "vital_signs"
    
    # InfluxDB (v1 style - legacy, kept for backward compatibility)
    INFLUX_HOST: str = "localhost"
    INFLUX_PORT: int = 8086
    INFLUX_USER: str = "admin"
    INFLUX_PASSWORD: str = "admin123"
    INFLUX_DB: str = "icu_db"
    
    # Producer settings
    NUM_PATIENTS: int = 10
    READING_INTERVAL_SECONDS: float = 1.0
    
    # Profile distribution
    PROFILE_DISTRIBUTION_HEALTHY: float = 0.7
    PROFILE_DISTRIBUTION_AT_RISK: float = 0.2
    PROFILE_DISTRIBUTION_CRITICAL: float = 0.1
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = Path("logs")
    ALERT_MODEL_PATH: str = "data/models/alert_classifier.joblib"
    ALERT_MODEL_THRESHOLD: float = 0.5
    TRAINING_DATA_PATH: str = "data/patients_data_with_alerts.xlsx"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env without error

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()