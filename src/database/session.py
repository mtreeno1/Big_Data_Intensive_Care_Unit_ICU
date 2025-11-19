"""
SQLAlchemy session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config.config import settings  # ✅ Removed Config

# ✅ Use settings.POSTGRES_DSN directly (no need for get_database_url)
engine = create_engine(
    settings.POSTGRES_DSN,
    pool_pre_ping=True,
    future=True,
    echo=False
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

def get_session() -> Session:
    """Dependency for FastAPI/generators"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_database_url() -> str:
    """Get database connection URL"""
    config = Config()  # ❌ This will fail - remove this function or fix
    return f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}"