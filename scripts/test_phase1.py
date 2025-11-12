#!/usr/bin/env python3
"""
Phase 1 Testing Script
Tests patient simulator and Kafka producer
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_generation.patient_simulator import VitalSignsGenerator, MultiPatientSimulator
from src.kafka_producer.producer import VitalSignsProducer, StreamingProducer
from config.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_patient_simulator():
    """Test 1: Patient Data Simulator"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 1: Patient Data Simulator")
    logger.info("=" * 60)
    
    try:
        # Test single patient
        logger.info("\n📋 Testing single patient (HEALTHY)...")
        patient = VitalSignsGenerator("PT-TEST-001", "HEALTHY")
        
        for i in range(3):
            reading = patient.generate_reading()
            logger.info(f"✅ Reading {i+1}: HR={reading['vital_signs']['heart_rate']}, "
                       f"SpO2={reading['vital_signs']['spo2']}")
        
        # Test multi-patient
        logger.info("\n📋 Testing multi-patient simulator...")
        simulator = MultiPatientSimulator(num_patients=5)
        summary = simulator.get_patient_summary()
        logger.info(f"✅ Created {summary['total_patients']} patients: {summary['profiles']}")
        
        batch = simulator.generate_batch()
        logger.info(f"✅ Generated batch of {len(batch)} readings")
        
        logger.info("✅ Patient Simulator Test: PASSED")
        return True
    
    except Exception as e:
        logger.error(f"❌ Patient Simulator Test: FAILED - {e}")
        return False


def test_kafka_connection():
    """Test 2: Kafka Connection"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Kafka Connection")
    logger.info("=" * 60)
    
    try:
        logger.info(f"📡 Connecting to Kafka: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        producer = VitalSignsProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            topic=settings.KAFKA_TOPIC_VITAL_SIGNS
        )
        
        # Send test message
        test_reading = {
            'patient_id': 'PT-TEST-999',
            'timestamp': '2025-01-01T00:00:00Z',
            'vital_signs': {'test': True}
        }
        
        success = producer.send_reading(test_reading)
        
        if success:
            logger.info("✅ Kafka Connection Test: PASSED")
            producer.close()
            return True
        else:
            logger.error("❌ Failed to send test message")
            return False
    
    except Exception as e:
        logger.error(f"❌ Kafka Connection Test: FAILED - {e}")
        logger.error("   Make sure Kafka is running: ./scripts/start.sh")
        return False


def test_streaming():
    """Test 3: Short Streaming Test"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Streaming Test (10 seconds)")
    logger.info("=" * 60)
    
    try:
        # Create simulator with 3 patients
        simulator = MultiPatientSimulator(num_patients=3)
        logger.info(f"✅ Created simulator with 3 patients")
        
        # Create producer
        producer = VitalSignsProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            topic=settings.KAFKA_TOPIC_VITAL_SIGNS
        )
        
        # Create streamer
        streamer = StreamingProducer(producer, interval_seconds=1.0)
        
        # Stream for 10 seconds
        logger.info("📡 Starting 10-second stream...")
        streamer.start_streaming(simulator, duration_seconds=10)
        
        # Check results
        if streamer.stats['total_sent'] > 0:
            logger.info("✅ Streaming Test: PASSED")
            producer.close()
            return True
        else:
            logger.error("❌ No data was sent")
            return False
    
    except Exception as e:
        logger.error(f"❌ Streaming Test: FAILED - {e}")
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 PHASE 1 TESTING")
    logger.info("=" * 60)
    
    results = {
        'patient_simulator': test_patient_simulator(),
        'kafka_connection': test_kafka_connection(),
        'streaming': test_streaming()
    }
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED!")
        logger.info("✅ Phase 1 is complete and working!")
        return 0
    else:
        logger.error("\n❌ SOME TESTS FAILED")
        logger.error("Please fix the issues and try again")
        return 1


if __name__ == "__main__":
    sys.exit(main())