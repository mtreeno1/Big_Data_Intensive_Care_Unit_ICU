"""
Configuration Management
Loads settings from environment variables with sensible defaults
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    LOG_DIR: Path = PROJECT_ROOT / "logs"
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_TOPIC_VITAL_SIGNS: str = Field(default="patient-vital-signs", env="KAFKA_TOPIC_VITAL_SIGNS")
    KAFKA_TOPIC_ALERTS: str = Field(default="patient-alerts", env="KAFKA_TOPIC_ALERTS")
    KAFKA_CONSUMER_GROUP: str = Field(default="icu-consumers", env="KAFKA_CONSUMER_GROUP")
    
    # PostgreSQL Configuration
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="icu_monitoring", env="POSTGRES_DB")
    POSTGRES_USER: str = Field(default="icu_user", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="icu_password", env="POSTGRES_PASSWORD")
    
    # InfluxDB Configuration
    INFLUX_URL: str = Field(default="http://localhost:8086", env="INFLUX_URL")
    INFLUX_TOKEN: str = Field(default="my-super-secret-auth-token", env="INFLUX_TOKEN")
    INFLUX_ORG: str = Field(default="icu_org", env="INFLUX_ORG")
    INFLUX_BUCKET: str = Field(default="vital_signs", env="INFLUX_BUCKET")
    
    # Simulation Configuration
    NUM_PATIENTS: int = Field(default=10, env="NUM_PATIENTS")
    READING_INTERVAL_SECONDS: float = Field(default=1.0, env="READING_INTERVAL_SECONDS")
    PROFILE_DISTRIBUTION_HEALTHY: float = Field(default=0.7, env="PROFILE_DISTRIBUTION_HEALTHY")
    PROFILE_DISTRIBUTION_AT_RISK: float = Field(default=0.2, env="PROFILE_DISTRIBUTION_AT_RISK")
    PROFILE_DISTRIBUTION_CRITICAL: float = Field(default=0.1, env="PROFILE_DISTRIBUTION_CRITICAL")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def get_postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    def get_profile_distribution(self) -> dict:
        """Get patient profile distribution"""
        return {
            'HEALTHY': self.PROFILE_DISTRIBUTION_HEALTHY,
            'AT_RISK': self.PROFILE_DISTRIBUTION_AT_RISK,
            'CRITICAL': self.PROFILE_DISTRIBUTION_CRITICAL
        }


# Create global settings instance
settings = Settings()

# Create directories if they don't exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
(settings.DATA_DIR / "raw").mkdir(exist_ok=True)
(settings.DATA_DIR / "processed").mkdir(exist_ok=True)
(settings.DATA_DIR / "models").mkdir(exist_ok=True)
(settings.DATA_DIR / "synthetic").mkdir(exist_ok=True)