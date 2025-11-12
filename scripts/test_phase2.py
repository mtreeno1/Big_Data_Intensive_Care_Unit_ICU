#!/usr/bin/env python3
"""
Phase 2 Testing Script
Tests consumer, storage, and stream processing
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
from src.data_generation.patient_simulator import MultiPatientSimulator
from src.kafka_producer.producer import VitalSignsProducer
from src.kafka_consumer.consumer import VitalSignsConsumer
from src.storage.influx_schema import InfluxDBWriter
from src.storage.postgres_schema import PostgreSQLWriter
from src.stream_processing.processor import VitalSignsProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connections():
    """Test 1: Database Connections"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 1: Database Connections")
    logger.info("=" * 60)
    
    try:
        # Test InfluxDB
        logger.info("📊 Testing InfluxDB connection...")
        influx = InfluxDBWriter(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG,
            bucket=settings.INFLUX_BUCKET
        )
        influx.close()
        logger.info("✅ InfluxDB connection successful")
        
        # Test PostgreSQL
        logger.info("🗄️  Testing PostgreSQL connection...")
        postgres = PostgreSQLWriter(connection_url=settings.get_postgres_url())
        postgres.close()
        logger.info("✅ PostgreSQL connection successful")
        
        logger.info("✅ Database Connections Test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database Connections Test: FAILED - {e}")
        return False


def test_data_storage():
    """Test 2: Data Storage"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Data Storage")
    logger.info("=" * 60)
    
    try:
        # Create test data
        from src.data_generation.patient_simulator import VitalSignsGenerator
        patient = VitalSignsGenerator("PT-TEST-002", "HEALTHY")
        reading = patient.generate_reading()
        
        # Test InfluxDB write
        logger.info("💾 Testing InfluxDB write...")
        influx = InfluxDBWriter(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG,
            bucket=settings.INFLUX_BUCKET
        )
        success = influx.write_vital_signs(reading)
        influx.close()
        
        if not success:
            raise Exception("Failed to write to InfluxDB")
        
        logger.info("✅ InfluxDB write successful")
        
        # Test PostgreSQL write
        logger.info("🗄️  Testing PostgreSQL write...")
        postgres = PostgreSQLWriter(connection_url=settings.get_postgres_url())
        success = postgres.upsert_patient(
            patient_id=reading['patient_id'],
            profile=reading['profile']
        )
        postgres.close()
        
        if not success:
            raise Exception("Failed to write to PostgreSQL")
        
        logger.info("✅ PostgreSQL write successful")
        
        logger.info("✅ Data Storage Test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data Storage Test: FAILED - {e}")
        return False


def test_end_to_end():
    """Test 3: End-to-End Pipeline"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: End-to-End Pipeline (15 seconds)")
    logger.info("=" * 60)
    
    try:
        # Setup
        influx = InfluxDBWriter(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG,
            bucket=settings.INFLUX_BUCKET
        )
        
        postgres = PostgreSQLWriter(connection_url=settings.get_postgres_url())
        
        processor = VitalSignsProcessor(
            influx_writer=influx,
            postgres_writer=postgres
        )
        
        # Create producer
        simulator = MultiPatientSimulator(num_patients=3)
        producer = VitalSignsProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            topic=settings.KAFKA_TOPIC_VITAL_SIGNS
        )
        
        # Produce data for 5 seconds
        logger.info("📡 Producing data for 5 seconds...")
        for i in range(15):  # 5 seconds * 3 patients
            batch = simulator.generate_batch()
            producer.send_batch(batch)
            time.sleep(1)
        
        producer.close()
        logger.info("✅ Data production complete")
        
        # Consume and process
        logger.info("📥 Consuming and processing data...")
        consumer = VitalSignsConsumer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            topic=settings.KAFKA_TOPIC_VITAL_SIGNS,
            group_id='test-consumer-group'
        )
        
        processed = 0
        
        def process_callback(reading):
            nonlocal processed
            success = processor.process_reading(reading)
            if success:
                processed += 1
            return success
        
        consumer.consume_messages(
            process_callback=process_callback,
            max_messages=45  # 15 seconds * 3 patients
        )
        
        consumer.close()
        
        logger.info(f"✅ Processed {processed} messages")
        
        # Check stats
        stats = processor.get_statistics()
        logger.info(f"📊 Processor Stats: {stats}")
        
        # Cleanup
        influx.close()
        postgres.close()
        
        if processed > 0:
            logger.info("✅ End-to-End Pipeline Test: PASSED")
            return True
        else:
            logger.error("❌ No messages were processed")
            return False
        
    except Exception as e:
        logger.error(f"❌ End-to-End Pipeline Test: FAILED - {e}")
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 PHASE 2 TESTING")
    logger.info("=" * 60)
    
    results = {
        'database_connections': test_database_connections(),
        'data_storage': test_data_storage(),
        'end_to_end': test_end_to_end()
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
        logger.info("✅ Phase 2 is complete and working!")
        return 0
    else:
        logger.error("\n❌ SOME TESTS FAILED")
        logger.error("Please fix the issues and try again")
        return 1


if __name__ == "__main__":
    sys.exit(main())