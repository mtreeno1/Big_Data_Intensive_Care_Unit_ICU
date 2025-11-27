#!/usr/bin/env python3
# filepath: scripts/debug_influx_detailed.py
"""
Debug InfluxDB: Check connection, write test, and query recent data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from src.storage.influx_storage import InfluxDBManager

def debug_influx():
    print("=" * 80)
    print("🔍 DETAILED INFLUXDB DEBUG")
    print("=" * 80)
    
    try:
        influx = InfluxDBManager()
        print("✅ InfluxDB Connected")
        
        # Test write
        print("\n📝 Testing Write...")
        test_data = {
            'heart_rate': 75.0,
            'spo2': 98.0,
            'temperature': 36.5,
            'risk_score': 10.0
        }
        
        success = influx.write_vital_signs(
            patient_id="TEST-PATIENT",
            data=test_data,
            tags={'risk_level': 'STABLE'}
        )
        
        if success:
            print("✅ Test write successful")
        else:
            print("❌ Test write failed")
            return
        
        # Query recent data
        print("\n📊 Querying recent data...")
        query = f'''
        from(bucket: "{influx.bucket}")
          |> range(start: -10m)
          |> filter(fn: (r) => r["_measurement"] == "vital_signs")
          |> limit(n: 10)
        '''
        
        result = influx.query_api.query(query)
        
        if result:
            print("✅ Found data:")
            for table in result:
                for record in table.records:
                    time_str = record.get_time().strftime('%H:%M:%S') if record.get_time() else 'N/A'
                    patient = record.values.get('patient_id', 'N/A')
                    field = record.get_field()
                    value = record.get_value()
                    print(f"   {time_str} | {patient} | {field}: {value}")
        else:
            print("❌ No data found in last 10 minutes")
            
            # Check all data
            print("\n🔍 Checking ALL data in bucket...")
            all_query = f'''
            from(bucket: "{influx.bucket}")
              |> range(start: 0)
              |> filter(fn: (r) => r["_measurement"] == "vital_signs")
              |> limit(n: 5)
            '''
            
            all_result = influx.query_api.query(all_query)
            if all_result:
                print("✅ Found historical data:")
                for table in all_result:
                    for record in table.records:
                        time_str = record.get_time().strftime('%Y-%m-%d %H:%M:%S') if record.get_time() else 'N/A'
                        print(f"   {time_str} | {record.values.get('patient_id')} | {record.get_field()}: {record.get_value()}")
            else:
                print("❌ No data at all in InfluxDB")
        
        influx.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_influx()