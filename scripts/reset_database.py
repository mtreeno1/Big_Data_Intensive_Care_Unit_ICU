#!/usr/bin/env python3
"""
<<<<<<< HEAD
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
=======
Reset PostgreSQL and InfluxDB databases
WARNING: This will delete all data!
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from sqlalchemy import create_engine, text
from influxdb_client import InfluxDBClient

from config.config import settings
from src.database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_postgresql():
    """Reset PostgreSQL database"""
>>>>>>> 5518597 (Initial commit: reset and push to master)
    logger.info("=" * 60)
    logger.info("🔄 POSTGRESQL DATABASE RESET")
    logger.info("=" * 60)
    logger.info("⚠️  This will delete all existing data!")
    logger.info("=" * 60)
    
<<<<<<< HEAD
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
=======
    try:
        logger.info("🗄️  Resetting PostgreSQL database...")
        
        # Create engine
        engine = create_engine(settings.get_postgres_url())
        
        # ✅ FIX: Drop tables with CASCADE
        with engine.begin() as conn:
            logger.info("🗑️  Dropping all existing tables with CASCADE...")
            
            # Drop tables in reverse order (child → parent)
            tables_to_drop = [
                'admissions',
                'patients', 
                'doctors',
                'audit_logs'  # If exists
            ]
            
            for table in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    logger.info(f"   ✅ Dropped table: {table}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Could not drop {table}: {e}")
        
        # Recreate all tables
        logger.info("🔨 Creating fresh tables...")
        Base.metadata.create_all(engine)
        
        logger.info("✅ PostgreSQL reset complete")
        engine.dispose()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to reset PostgreSQL: {e}")
        return False

def reset_influxdb():
    """Reset InfluxDB bucket"""
    logger.info("\n" + "=" * 60)
    logger.info("🔄 INFLUXDB BUCKET RESET")
    logger.info("=" * 60)
    
    try:
        logger.info("💾 Resetting InfluxDB bucket...")
        
        client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG
        )
        
        buckets_api = client.buckets_api()
        
        # Delete existing bucket
        try:
            existing_bucket = buckets_api.find_bucket_by_name(settings.INFLUX_BUCKET)
            if existing_bucket:
                buckets_api.delete_bucket(existing_bucket)
                logger.info(f"🗑️  Deleted existing bucket: {settings.INFLUX_BUCKET}")
        except Exception as e:
            logger.warning(f"⚠️  Could not delete bucket: {e}")
        
        # Create fresh bucket
        bucket = buckets_api.create_bucket(
            bucket_name=settings.INFLUX_BUCKET,
            org=settings.INFLUX_ORG,
            retention_rules=[{
                "type": "expire",
                "everySeconds": 2592000  # 30 days
            }]
        )
        
        logger.info(f"✅ Created fresh bucket: {bucket.name}")
        client.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to reset InfluxDB: {e}")
        return False

def main():
    """Main reset workflow"""
    
    print("\n" + "=" * 70)
    print("⚠️  DATABASE RESET WARNING")
    print("=" * 70)
    print("This will DELETE ALL DATA in:")
    print(f"  - PostgreSQL database: {settings.POSTGRES_DB}")
    print(f"  - InfluxDB bucket: {settings.INFLUX_BUCKET}")
    print()
    
    confirmation = input("Type 'YES' to confirm: ")
    
    if confirmation != "YES":
        logger.info("❌ Reset cancelled")
        return
    
    # Reset PostgreSQL
    pg_success = reset_postgresql()
    
    # Reset InfluxDB
    influx_success = reset_influxdb()
    
    # Summary
    print("\n" + "=" * 70)
    if pg_success and influx_success:
        print("✅ DATABASE RESET COMPLETE")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. python scripts/init_databases.py")
        print("  2. python scripts/add_patients_with_admission.py")
    else:
        print("⚠️  DATABASE RESET INCOMPLETE")
        print("=" * 70)
        if not pg_success:
            print("❌ PostgreSQL reset failed")
        if not influx_success:
            print("❌ InfluxDB reset failed")

if __name__ == "__main__":
    main()
>>>>>>> 5518597 (Initial commit: reset and push to master)
