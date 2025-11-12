#!/usr/bin/env python3
"""
Reset PostgreSQL Database
Drops all tables and recreates them
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
from src.storage.postgres_schema import Base
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def reset_postgresql():
    """Reset PostgreSQL database"""
    logger.info("🗄️  Resetting PostgreSQL database...")
    
    try:
        # Create engine
        engine = create_engine(settings.get_postgres_url())
        
        # Drop all tables
        logger.info("🗑️  Dropping all existing tables...")
        Base.metadata.drop_all(engine)
        logger.info("✅ All tables dropped")
        
        # Recreate all tables
        logger.info("🔨 Creating tables with new schema...")
        Base.metadata.create_all(engine)
        logger.info("✅ Tables created successfully")
        logger.info(f"   Tables: {', '.join(Base.metadata.tables.keys())}")
        
        # Verify table structure
        with engine.connect() as conn:
            # Check patients table columns
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'patients' ORDER BY ordinal_position"
            ))
            columns = [row[0] for row in result]
            logger.info(f"   'patients' table columns: {', '.join(columns)}")
        
        engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to reset PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("🔄 POSTGRESQL DATABASE RESET")
    logger.info("=" * 60)
    logger.info("⚠️  This will delete all existing data!")
    logger.info("=" * 60)
    
    success = reset_postgresql()
    
    if success:
        logger.info("\n✅ PostgreSQL database reset successfully!")
        logger.info("✅ You can now run: python scripts/test_phase2.py")
        return 0
    else:
        logger.error("\n❌ Failed to reset database")
        return 1


if __name__ == "__main__":
    sys.exit(main())