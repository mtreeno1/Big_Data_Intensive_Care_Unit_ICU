"""
<<<<<<< HEAD
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
=======
Database session management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool
from config.config import settings

# ✅ FIX: Use get_postgres_url() instead of POSTGRES_DSN
DATABASE_URL = settings.get_postgres_url()

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,        # Maximum number of connections
    max_overflow=20,     # Maximum overflow connections
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False           # Set to True for SQL debugging
>>>>>>> 5518597 (Initial commit: reset and push to master)
)

# Session factory
SessionLocal = sessionmaker(
<<<<<<< HEAD
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

def get_session() -> Session:
    """Dependency for FastAPI/generators"""
=======
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_session() -> Session:
    """
    Dependency for FastAPI or other frameworks
    
    Usage:
        @app.get("/patients")
        def get_patients(db: Session = Depends(get_session)):
            return db.query(Patient).all()
    """
>>>>>>> 5518597 (Initial commit: reset and push to master)
    db = SessionLocal()
    try:
        yield db
    finally:
<<<<<<< HEAD
        db.close()
=======
        db.close()

# Optional: Add connection pool event listeners for monitoring
@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Called when a new DB connection is created"""
    # Can add custom connection setup here
    pass

@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Called when a connection is retrieved from the pool"""
    # Can add connection validation here
    pass
>>>>>>> 5518597 (Initial commit: reset and push to master)
