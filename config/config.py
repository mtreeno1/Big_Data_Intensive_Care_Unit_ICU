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
    POSTGRES_DB: str = "icu_monitoring"
    
    # InfluxDB
    INFLUX_URL: str = "http://localhost:8086"
    INFLUX_TOKEN: str = "your-super-secret-influx-token"
    INFLUX_ORG: str = "icu_org"
    INFLUX_BUCKET: str = "vital_signs"
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
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
    
    # Producer settings
    NUM_PATIENTS: int = 10
    READING_INTERVAL_SECONDS: float = 1.0
    
    # Patient profile distribution
    PROFILE_DISTRIBUTION_HEALTHY: float = 0.7
    PROFILE_DISTRIBUTION_AT_RISK: float = 0.2
    PROFILE_DISTRIBUTION_CRITICAL: float = 0.1
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

# Global settings instance
settings = Settings()