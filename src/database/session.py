"""
SQLAlchemy session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config.config import settings

# Create engine
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