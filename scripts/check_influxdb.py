#!/usr/bin/env python3
"""
Check if data is stored in InfluxDB
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
from influxdb_client import InfluxDBClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_influxdb():
    """Check InfluxDB data"""
    
    print("\n" + "=" * 70)
    print("🔍 CHECKING INFLUXDB DATA")
    print("=" * 70)
    print(f"📍 InfluxDB URL: {settings.INFLUX_URL}")
    print(f"🏢 Organization: {settings.INFLUX_ORG}")
    print(f"📦 Bucket: {settings.INFLUX_BUCKET}")
    print("=" * 70 + "\n")
    
    try:
        client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG
        )
        
        # Test connection
        logger.info("🔗 Connecting to InfluxDB...")
        health = client.health()
        logger.info(f"✅ Connection successful: {health.status}")
        
        query_api = client.query_api()
        
        # Query vital signs data from last 2 hours
        query = f'''
        from(bucket:"{settings.INFLUX_BUCKET}")
          |> range(start: -2h)
          |> filter(fn: (r) => r._measurement == "vital_signs")
          |> limit(n: 100)
        '''
        
        logger.info("\n📊 Querying vital_signs measurement (last 2 hours)...\n")
        result = query_api.query(query)
        
        if not result:
            logger.error("❌ NO DATA FOUND in InfluxDB")
            logger.info("\n💡 Possible reasons:")
            logger.info("   1. Consumer not running or not writing to InfluxDB")
            logger.info("   2. Producer not sending data to Kafka")
            logger.info("   3. Data older than 2 hours")
            return False
        
        record_count = 0
        patients = set()
        measurements = {}
        
        for table in result:
            for record in table.records:
                record_count += 1
                # ✅ Fix: Use get_field() method
                patient_id = record.values.get("patient_id", "N/A")
                field = record.get_field()  # ✅ Changed from record.field
                value = record.get_value()  # ✅ Changed from record.value
                time = record.get_time()    # ✅ Keep as is
                
                patients.add(patient_id)
                
                if field not in measurements:
                    measurements[field] = 0
                measurements[field] += 1
                
                # Print first 5 records
                if record_count <= 5:
                    print(f"📊 Record #{record_count}")
                    print(f"   Patient: {patient_id}")
                    print(f"   Field: {field}")
                    print(f"   Value: {value}")
                    print(f"   Time: {time}\n")
        
        print("=" * 70)
        print(f"✅ SUMMARY:")
        print(f"   Total records: {record_count}")
        print(f"   Unique patients: {len(patients)}")
        print(f"   Patients: {sorted(patients)}")
        print(f"   Measurements breakdown:")
        for field, count in sorted(measurements.items()):
            print(f"      - {field}: {count}")
        print("=" * 70 + "\n")
        
        client.close()
        return record_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = check_influxdb()
    sys.exit(0 if success else 1)