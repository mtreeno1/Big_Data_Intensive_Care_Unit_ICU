#!/usr/bin/env python3
"""
Monitor Kafka - Xem dữ liệu đang streaming
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
from kafka import KafkaConsumer


def format_vital_signs(vitals):
    """Format vital signs for display"""
    return (
        f"HR: {vitals['heart_rate']:>5.0f} bpm | "
        f"SpO2: {vitals['spo2']:>5.1f}% | "
        f"BP: {vitals['blood_pressure']['systolic']:>3.0f}/{vitals['blood_pressure']['diastolic']:<3.0f} | "
        f"Temp: {vitals['temperature']:>5.2f}°C | "
        f"RR: {vitals['respiratory_rate']:>3.0f} /min"
    )


def main():
    print("=" * 100)
    print("📡 KAFKA STREAMING DATA MONITOR")
    print("=" * 100)
    print(f"Topic: {settings.KAFKA_TOPIC_VITAL_SIGNS}")
    print(f"Server: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    print("=" * 100)
    print()
    
    # Create consumer
    consumer = KafkaConsumer(
        settings.KAFKA_TOPIC_VITAL_SIGNS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='latest',  # Only read new messages
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=1000
    )
    
    print("🎧 Listening to Kafka stream... (Press Ctrl+C to stop)")
    print()
    
    message_count = 0
    
    try:
        for message in consumer:
            message_count += 1
            reading = message.value
            
            # Extract data
            patient_id = reading['patient_id']
            profile = reading.get('profile', 'UNKNOWN')
            timestamp = reading['timestamp']
            vitals = reading['vital_signs']
            has_anomaly = reading.get('metadata', {}).get('has_anomaly', False)
            
            # Color based on profile
            if profile == 'HEALTHY':
                color = '\033[92m'  # Green
                symbol = '✅'
            elif profile == 'AT_RISK':
                color = '\033[93m'  # Yellow
                symbol = '⚠️ '
            else:
                color = '\033[91m'  # Red
                symbol = '🚨'
            
            reset = '\033[0m'
            
            # Display message
            time_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%H:%M:%S')
            anomaly_str = " [ANOMALY]" if has_anomaly else ""
            
            print(f"{color}[{message_count:>4}] {symbol} {time_str} | {patient_id:<12} | {profile:<10} | {format_vital_signs(vitals)}{anomaly_str}{reset}")
            
    except KeyboardInterrupt:
        print(f"\n\n✅ Stopped. Total messages received: {message_count}")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()