# filepath: scripts/init_databases.py
"""
Initialize all databases (PostgreSQL tables and InfluxDB buckets)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.models import init_db, engine
from config.config import settings
from sqlalchemy import text


def init_postgres():
    """Initialize PostgreSQL database"""
    print("=" * 80)
    print("🐘 INITIALIZING POSTGRESQL")
    print("=" * 80)
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"\n✅ Connected to PostgreSQL")
            print(f"   Version: {version[:50]}...")
        
        # Create tables
        print("\n📦 Creating tables...")
        init_db()
        
        # Verify tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            
            print(f"\n✅ Tables created: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ PostgreSQL initialization failed: {e}")
        return False


def init_influxdb():
    """Initialize InfluxDB bucket"""
    print("\n" + "=" * 80)
    print("📊 INITIALIZING INFLUXDB")
    print("=" * 80)
    
    try:
        from influxdb_client import InfluxDBClient
        from influxdb_client.rest import ApiException
        
        client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG
        )
        
        # Check bucket
        buckets_api = client.buckets_api()
        bucket = buckets_api.find_bucket_by_name(settings.INFLUX_BUCKET)
        
        if not bucket:
            print(f"\n📦 Creating bucket: {settings.INFLUX_BUCKET}")
            buckets_api.create_bucket(
                bucket_name=settings.INFLUX_BUCKET,
                org=settings.INFLUX_ORG
            )
            print(f"✅ Bucket created")
        else:
            print(f"\n✅ Bucket already exists: {settings.INFLUX_BUCKET}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"\n❌ InfluxDB initialization failed: {e}")
        print(f"💡 Make sure InfluxDB is running: docker-compose up -d influxdb")
        return False


def main():
    """Initialize all databases"""
    print("\n" + "=" * 80)
    print("🔧 DATABASE INITIALIZATION")
    print("=" * 80)
    
    success = True
    
    # PostgreSQL
    if not init_postgres():
        success = False
    
    # InfluxDB
    if not init_influxdb():
        success = False
    
    # Summary
    print("\n" + "=" * 80)
    if success:
        print("✅ ALL DATABASES INITIALIZED SUCCESSFULLY")
    else:
        print("⚠️  SOME DATABASES FAILED TO INITIALIZE")
    print("=" * 80)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())