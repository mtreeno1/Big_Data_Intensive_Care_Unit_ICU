#!/usr/bin/env python3
"""
Monitor PostgreSQL - Xem events và alerts đã lưu
"""

import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
from sqlalchemy import create_engine, text


def main():
    print("=" * 100)
    print("🗄️  POSTGRESQL DATA MONITOR")
    print("=" * 100)
    print(f"Database: {settings.POSTGRES_DB}")
    print(f"Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    print("=" * 100)
    print()
    
    # Connect to PostgreSQL
    engine = create_engine(settings.get_postgres_url())
    
    try:
        while True:
            print(f"\n⏰ Querying data at {datetime.now().strftime('%H:%M:%S')}...")
            
            with engine.connect() as conn:
                # 1. Patient summary
                print("\n👥 PATIENTS:")
                print("-" * 100)
                result = conn.execute(text("""
                    SELECT patient_id, profile, created_at, 
                           (SELECT COUNT(*) FROM events WHERE events.patient_id = patients.patient_id) as event_count
                    FROM patients
                    ORDER BY patient_id
                """))
                
                rows = result.fetchall()
                if rows:
                    print(f"{'Patient ID':<15} {'Profile':<12} {'Created At':<20} {'Events'}")
                    print("-" * 100)
                    
                    for row in rows:
                        profile = row[1]
                        
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
                        
                        created = row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else 'N/A'
                        print(f"{color}{symbol} {row[0]:<13} {profile:<12} {created:<20} {row[3]}{reset}")
                    
                    print(f"\nTotal patients: {len(rows)}")
                else:
                    print("⚠️  No patients found")
                
                # 2. Recent events (last 10)
                print("\n\n🔔 RECENT EVENTS (Last 10):")
                print("-" * 100)
                result = conn.execute(text("""
                    SELECT patient_id, event_type, severity, description, timestamp
                    FROM events
                    ORDER BY timestamp DESC
                    LIMIT 10
                """))
                
                rows = result.fetchall()
                if rows:
                    print(f"{'Patient ID':<15} {'Type':<15} {'Severity':<12} {'Description':<30} {'Time'}")
                    print("-" * 100)
                    
                    for row in rows:
                        severity = row[2]
                        
                        if severity in ['LOW', 'MEDIUM']:
                            color = '\033[93m'
                        else:
                            color = '\033[91m'
                        
                        reset = '\033[0m'
                        
                        timestamp = row[4].strftime('%H:%M:%S') if row[4] else 'N/A'
                        desc = row[3][:28] + '..' if row[3] and len(row[3]) > 30 else (row[3] or 'N/A')
                        
                        print(f"{color}{row[0]:<15} {row[1]:<15} {severity:<12} {desc:<30} {timestamp}{reset}")
                    
                    print(f"\nTotal events in database: {len(rows)} (showing last 10)")
                else:
                    print("⚠️  No events found")
                
                # 3. Recent alerts (last 10)
                print("\n\n🚨 RECENT ALERTS (Last 10):")
                print("-" * 100)
                result = conn.execute(text("""
                    SELECT patient_id, alert_type, severity, vital_type, value, threshold, timestamp
                    FROM alerts
                    ORDER BY timestamp DESC
                    LIMIT 10
                """))
                
                rows = result.fetchall()
                if rows:
                    print(f"{'Patient ID':<15} {'Type':<15} {'Severity':<10} {'Vital':<15} {'Value':<10} {'Threshold':<10} {'Time'}")
                    print("-" * 100)
                    
                    for row in rows:
                        severity = row[2]
                        
                        if severity == 'CRITICAL':
                            color = '\033[91m'
                            symbol = '🚨'
                        elif severity == 'HIGH':
                            color = '\033[93m'
                            symbol = '⚠️ '
                        else:
                            color = '\033[92m'
                            symbol = 'ℹ️ '
                        
                        reset = '\033[0m'
                        
                        timestamp = row[6].strftime('%H:%M:%S') if row[6] else 'N/A'
                        
                        print(f"{color}{symbol} {row[0]:<13} {row[1]:<15} {severity:<10} {row[3]:<15} {row[4]:<10.1f} {row[5]:<10.1f} {timestamp}{reset}")
                    
                    print(f"\nTotal alerts in database: {len(rows)} (showing last 10)")
                else:
                    print("⚠️  No alerts found")
                
                # 4. Consumer metrics
                print("\n\n📊 CONSUMER METRICS (Last entry):")
                print("-" * 100)
                result = conn.execute(text("""
                    SELECT timestamp, messages_processed, messages_failed, processing_time_ms, lag
                    FROM consumer_metrics
                    ORDER BY timestamp DESC
                    LIMIT 1
                """))
                
                row = result.fetchone()
                if row:
                    timestamp = row[0].strftime('%Y-%m-%d %H:%M:%S') if row[0] else 'N/A'
                    success_rate = (row[1] / (row[1] + row[2]) * 100) if (row[1] + row[2]) > 0 else 0
                    
                    print(f"   Time: {timestamp}")
                    print(f"   Messages Processed: {row[1]}")
                    print(f"   Messages Failed: {row[2]}")
                    print(f"   Success Rate: {success_rate:.1f}%")
                    print(f"   Avg Processing Time: {row[3]:.2f} ms")
                    print(f"   Consumer Lag: {row[4]}")
                else:
                    print("⚠️  No metrics found")
            
            print("\n⏳ Refreshing in 10 seconds... (Press Ctrl+C to stop)")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()