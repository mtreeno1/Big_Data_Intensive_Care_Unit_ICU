#!/usr/bin/env python3
"""
Clean old data from InfluxDB
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
from influxdb_client import InfluxDBClient

def clean_influxdb():
    """Delete all data from vital_signs measurement"""
    
    print("⚠️  WARNING: This will delete ALL data from InfluxDB!")
    confirm = input("Type 'YES' to confirm: ")
    
    if confirm != "YES":
        print("❌ Cancelled")
        return
    
    try:
        client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG
        )
        
        delete_api = client.delete_api()
        
        # Delete all data from vital_signs measurement
        start = "1970-01-01T00:00:00Z"
        stop = "2099-12-31T23:59:59Z"
        
        delete_api.delete(
            start=start,
            stop=stop,
            predicate='_measurement="vital_signs"',
            bucket=settings.INFLUX_BUCKET,
            org=settings.INFLUX_ORG
        )
        
        print("✅ Deleted all data from InfluxDB")
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clean_influxdb()