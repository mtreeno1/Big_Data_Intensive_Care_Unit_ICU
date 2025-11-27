#!/usr/bin/env python3
"""
Initialize Databases
Creates tables and initial setup for PostgreSQL and InfluxDB
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
<<<<<<< HEAD
from src.storage.postgres_schema import PostgreSQLWriter, Base
from src.storage.influx_schema import InfluxDBWriter
=======
from src.storage.postgres_schema import PostgreSQLWriter, Base as StorageBase
from src.storage.influx_schema import InfluxDBWriter
from src.database.models import Base as AppBase
>>>>>>> 5518597 (Initial commit: reset and push to master)
from sqlalchemy import create_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_postgresql():
    """Initialize PostgreSQL database"""
    logger.info("🗄️  Initializing PostgreSQL...")
    
    try:
        # Create engine
        engine = create_engine(settings.get_postgres_url())
        
<<<<<<< HEAD
        # Create all tables
        Base.metadata.create_all(engine)
        
        logger.info("✅ PostgreSQL initialized successfully")
        logger.info(f"   Created tables: {', '.join(Base.metadata.tables.keys())}")
=======
        # Create all tables for app ORM (patients, admissions, doctors)
        AppBase.metadata.create_all(engine)
        # Create storage tables (events, alerts, consumer_metrics, patients_storage)
        StorageBase.metadata.create_all(engine)
        
        logger.info("✅ PostgreSQL initialized successfully")
        from sqlalchemy import inspect
        insp = inspect(engine)
        tables = insp.get_table_names()
        logger.info(f"   Created tables: {', '.join(tables)}")
>>>>>>> 5518597 (Initial commit: reset and push to master)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize PostgreSQL: {e}")
        return False


def init_influxdb():
    """Initialize InfluxDB"""
    logger.info("💾 Initializing InfluxDB...")
    
    try:
        writer = InfluxDBWriter(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG,
            bucket=settings.INFLUX_BUCKET
        )
        
        writer.close()
        
        logger.info("✅ InfluxDB initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize InfluxDB: {e}")
        return False


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("🔧 DATABASE INITIALIZATION")
    logger.info("=" * 60)
    
    results = {
        'postgresql': init_postgresql(),
        'influxdb': init_influxdb()
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 INITIALIZATION SUMMARY")
    logger.info("=" * 60)
    
    for db, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"{db}: {status}")
    
    all_success = all(results.values())
    
    if all_success:
        logger.info("\n🎉 All databases initialized successfully!")
        return 0
    else:
        logger.error("\n❌ Some databases failed to initialize")
        return 1


if __name__ == "__main__":
    sys.exit(main())