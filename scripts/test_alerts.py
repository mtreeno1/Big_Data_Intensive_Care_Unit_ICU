#!/usr/bin/env python3
"""
Test Alert System - Simulate Critical Patient Condition
Sends test alerts to verify WebSocket alerting is working
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
from kafka import KafkaProducer
from datetime import datetime
from config.config import settings

def create_producer():
    """Create Kafka producer"""
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def send_test_alert(producer, severity='CRITICAL', patient_id='P001'):
    """Send a test alert"""
    
    test_scenarios = {
        'CRITICAL': {
            'alert_type': 'Severe Hypoxemia + Tachycardia',
            'vital_signs': {
                'heart_rate': 145,
                'spo2': 82,
                'temperature': 38.8,
                'blood_pressure_systolic': 185,
                'blood_pressure_diastolic': 115,
                'respiratory_rate': 28
            }
        },
        'HIGH': {
            'alert_type': 'Moderate Hypotension',
            'vital_signs': {
                'heart_rate': 125,
                'spo2': 88,
                'temperature': 38.2,
                'blood_pressure_systolic': 85,
                'blood_pressure_diastolic': 55,
                'respiratory_rate': 24
            }
        },
        'MODERATE': {
            'alert_type': 'Elevated Heart Rate',
            'vital_signs': {
                'heart_rate': 115,
                'spo2': 91,
                'temperature': 37.8,
                'blood_pressure_systolic': 140,
                'blood_pressure_diastolic': 90,
                'respiratory_rate': 20
            }
        }
    }
    
    scenario = test_scenarios.get(severity, test_scenarios['CRITICAL'])
    
    alert = {
        'patient_id': patient_id,
        'severity': severity,
        'risk_level': severity,
        'alert_type': scenario['alert_type'],
        'vital_signs': scenario['vital_signs'],
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'warnings': [scenario['alert_type']]
    }
    
    print(f"📤 Sending {severity} alert for {patient_id}...")
    producer.send('patient-alerts', alert)
    producer.flush()
    print(f"✅ Alert sent!")
    return alert


def run_test_sequence():
    """Run a sequence of test alerts"""
    print("🧪 ICU Alert System - Test Suite")
    print("=" * 60)
    print("")
    
    producer = create_producer()
    
    tests = [
        ("Test 1: Critical Alert", 'CRITICAL', 'P001', 5),
        ("Test 2: High Alert", 'HIGH', 'P002', 5),
        ("Test 3: Moderate Alert", 'MODERATE', 'P003', 5),
        ("Test 4: Multiple Critical (Alert Flood)", 'CRITICAL', 'P001', 2),
    ]
    
    for test_name, severity, patient_id, wait_time in tests:
        print(f"\n🔬 {test_name}")
        print("-" * 60)
        alert = send_test_alert(producer, severity, patient_id)
        print(f"   Patient ID: {patient_id}")
        print(f"   Severity: {severity}")
        print(f"   Alert Type: {alert['alert_type']}")
        print(f"   Vitals:")
        for key, value in alert['vital_signs'].items():
            print(f"      - {key}: {value}")
        print(f"\n⏳ Waiting {wait_time} seconds...")
        time.sleep(wait_time)
    
    # Test 5: Rapid-fire alerts
    print(f"\n🔬 Test 5: Rapid-Fire Alerts (3 in 1 second)")
    print("-" * 60)
    for i in range(3):
        send_test_alert(producer, 'CRITICAL', f'P{i+10:03d}')
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\nExpected Results:")
    print("1. Each alert should appear in dashboard within 1 second")
    print("2. Audio should play for each alert")
    print("3. Browser notifications should appear")
    print("4. Connection status should remain 🟢 Connected")
    print("5. Critical alerts should require manual acknowledgment")
    print("6. Non-critical alerts should auto-dismiss after 60s")
    print("")
    print("If any of the above fails, check:")
    print("- WebSocket server is running (scripts/run_alert_server.py)")
    print("- Dashboard has granted notification permission")
    print("- Browser tab is not muted")
    print("- Check browser console for errors (F12)")
    print("")

if __name__ == "__main__":
    try:
        run_test_sequence()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
