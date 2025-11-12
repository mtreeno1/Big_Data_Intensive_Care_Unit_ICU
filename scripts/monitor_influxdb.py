#!/usr/bin/env python3
"""
Monitor InfluxDB - Xem dữ liệu time-series đã lưu
"""

import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
from influxdb_client import InfluxDBClient


def main():
    print("=" * 100)
    print("💾 INFLUXDB DATA MONITOR (Last 5 minutes)")
    print("=" * 100)
    print(f"URL: {settings.INFLUX_URL}")
    print(f"Bucket: {settings.INFLUX_BUCKET}")
    print("=" * 100)
    print()
    
    # Connect to InfluxDB
    client = InfluxDBClient(
        url=settings.INFLUX_URL,
        token=settings.INFLUX_TOKEN,
        org=settings.INFLUX_ORG
    )
    query_api = client.query_api()
    
    try:
        while True:
            print(f"\n⏰ Querying data at {datetime.now().strftime('%H:%M:%S')}...")
            
            # Query for each patient
            query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
              |> range(start: -5m)
              |> filter(fn: (r) => r["_measurement"] == "vital_signs")
              |> group(columns: ["patient_id", "vital_type"])
              |> last()
            '''
            
            try:
                tables = query_api.query(query)
                
                # Group by patient
                patient_data = {}
                
                for table in tables:
                    for record in table.records:
                        patient_id = record.values.get('patient_id')
                        vital_type = record.values.get('vital_type')
                        value = record.values.get('_value')
                        profile = record.values.get('profile', 'UNKNOWN')
                        
                        if patient_id not in patient_data:
                            patient_data[patient_id] = {'profile': profile}
                        
                        patient_data[patient_id][vital_type] = value
                
                if patient_data:
                    print(f"\n📊 Found data for {len(patient_data)} patients:")
                    print("-" * 100)
                    
                    # Header
                    print(f"{'Patient ID':<15} {'Profile':<12} {'HR':<8} {'SpO2':<8} {'Temp':<8} {'RR':<8} {'Systolic':<10} {'Diastolic'}")
                    print("-" * 100)
                    
                    # Data rows
                    for patient_id, data in sorted(patient_data.items()):
                        profile = data.get('profile', 'N/A')
                        hr = data.get('heart_rate', 0)
                        spo2 = data.get('spo2', 0)
                        temp = data.get('temperature', 0)
                        rr = data.get('respiratory_rate', 0)
                        sys_bp = data.get('systolic_bp', 0)
                        dia_bp = data.get('diastolic_bp', 0)
                        
                        # Color based on profile
                        if profile == 'HEALTHY':
                            color = '\033[92m'
                            symbol = '✅'
                        elif profile == 'AT_RISK':
                            color = '\033[93m'
                            symbol = '⚠️ '
                        else:
                            color = '\033[91m'
                            symbol = '🚨'
                        
                        reset = '\033[0m'
                        
                        print(f"{color}{symbol} {patient_id:<13} {profile:<12} {hr:<8.0f} {spo2:<8.1f} {temp:<8.2f} {rr:<8.0f} {sys_bp:<10.0f} {dia_bp:.0f}{reset}")
                    
                    print("-" * 100)
                    
                    # Stats
                    print(f"\n📈 Statistics:")
                    print(f"   Total patients: {len(patient_data)}")
                    print(f"   Healthy: {sum(1 for d in patient_data.values() if d.get('profile') == 'HEALTHY')}")
                    print(f"   At Risk: {sum(1 for d in patient_data.values() if d.get('profile') == 'AT_RISK')}")
                    print(f"   Critical: {sum(1 for d in patient_data.values() if d.get('profile') == 'CRITICAL')}")
                else:
                    print("⚠️  No data found in the last 5 minutes")
                    print("   Make sure producer and consumer are running!")
                
            except Exception as e:
                print(f"❌ Query error: {e}")
            
            print("\n⏳ Refreshing in 10 seconds... (Press Ctrl+C to stop)")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")
    finally:
        client.close()


if __name__ == "__main__":
    main()