# filepath: src/database/session.py
"""
Database session configuration
"""
from sqlalchemy.orm import sessionmaker
from .models import engine

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_session():
    """Get database session"""
    session = SessionLocal()
    try:
        return session
    finally:
        session.close()