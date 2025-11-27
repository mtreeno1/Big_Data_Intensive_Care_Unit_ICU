#!/usr/bin/env python3
"""
<<<<<<< HEAD
Main Consumer Application
Runs the complete consumer pipeline with monitoring
"""

import sys
import io
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import settings
from src.kafka_consumer.consumer import VitalSignsConsumer
from src.storage.influx_schema import InfluxDBWriter
from src.storage.postgres_schema import PostgreSQLWriter
from src.stream_processing.processor import VitalSignsProcessor
from src.monitoring.metrics import PerformanceMonitor
from src.ml.alert_model import AlertInferenceService

# Setup logging
log_dir = settings.LOG_DIR
if not log_dir.is_absolute():
    log_dir = (Path(__file__).parent.parent / log_dir).resolve()
log_dir.mkdir(parents=True, exist_ok=True)

file_handler = logging.FileHandler(log_dir / 'consumer.log', encoding='utf-8')
stream_handler = logging.StreamHandler(
    stream=io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger(__name__)


class ConsumerApplication:
    """Main consumer application"""
    
    def __init__(self):
        """Initialize all components"""
        logger.info("🚀 Initializing Consumer Application...")
        
        # Initialize storage
        self.influx_writer = InfluxDBWriter(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG,
            bucket=settings.INFLUX_BUCKET
        )
        
        self.postgres_writer = PostgreSQLWriter(
            connection_url=settings.get_postgres_url()
        )
        
        # Load alert inference service if available
        self.alert_service = AlertInferenceService.from_settings(settings)

        # Initialize processor
        self.processor = VitalSignsProcessor(
            influx_writer=self.influx_writer,
            postgres_writer=self.postgres_writer,
            alert_service=self.alert_service
        )
        
        # Initialize monitor
        self.monitor = PerformanceMonitor()
        
        # Initialize consumer
        self.consumer = VitalSignsConsumer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            topic=settings.KAFKA_TOPIC_VITAL_SIGNS,
            group_id=settings.KAFKA_CONSUMER_GROUP
        )
        
        logger.info("✅ Consumer Application initialized successfully")
    
    def process_message(self, reading: dict) -> bool:
        """
        Process a single message
        
        Args:
            reading: Patient vital signs reading
            
        Returns:
            True if successful
        """
        start_time = time.time()
        
        try:
            # Process the reading
            success = self.processor.process_reading(reading)
            
            # Record metrics
            processing_time = (time.time() - start_time) * 1000
            self.monitor.record_processing_time(processing_time)
            
            if not success:
                self.monitor.record_error()
            
            # Log metrics periodically
            if self.monitor.should_log(interval_seconds=60):
                self.monitor.log_metrics()
                
                # Log processor statistics
                proc_stats = self.processor.get_statistics()
                logger.info(f"📊 Processor Stats: {proc_stats}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error in process_message: {e}")
            self.monitor.record_error()
            return False
    
    def run(self, max_messages: int = None):
        """
        Run the consumer
        
        Args:
            max_messages: Maximum messages to process (None = infinite)
        """
        logger.info("=" * 60)
        logger.info("🎯 STARTING CONSUMER")
        logger.info("=" * 60)
        logger.info(f"📡 Kafka: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        logger.info(f"📌 Topic: {settings.KAFKA_TOPIC_VITAL_SIGNS}")
        logger.info(f"👥 Group: {settings.KAFKA_CONSUMER_GROUP}")
        logger.info(f"💾 InfluxDB: {settings.INFLUX_URL}")
        logger.info(f"🗄️  PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        logger.info("=" * 60)
        
        try:
            self.consumer.consume_messages(
                process_callback=self.process_message,
                max_messages=max_messages
            )
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Consumer interrupted by user")
        
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
            raise
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("🔄 Shutting down...")
        
        # Log final metrics
        self.monitor.log_metrics()
        
        # Close connections
        self.consumer.close()
        self.influx_writer.close()
        self.postgres_writer.close()
        
        logger.info("✅ Consumer Application shut down successfully")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run ICU Consumer')
    parser.add_argument(
        '--max-messages',
        type=int,
        default=None,
        help='Maximum number of messages to process (default: infinite)'
    )
    
    args = parser.parse_args()
    
    # Create and run application
    app = ConsumerApplication()
    app.run(max_messages=args.max_messages)

=======
Run Kafka Consumer with Data Validation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from src.kafka_consumer.consumer import VitalSignsConsumer
from src.stream_processing.data_validator import MedicalDataValidator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnhancedConsumer(VitalSignsConsumer):
    """Consumer with data validation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = MedicalDataValidator()
        # ✅ FIX: Use separate dict for validation stats
        self.validation_stats = {"validated": 0, "invalid": 0, "quality_issues": 0}
    
    def process_callback(self, reading):
        """Process with validation"""
        try:
            # Validate data
            cleaned_reading, is_valid = self.validator.validate_and_clean(reading)
            
            if not is_valid:
                self.validation_stats["invalid"] += 1
                logger.warning(f"⚠️  Invalid data for {reading.get('patient_id')}")
                return False
            
            # Log data quality issues
            if "data_quality_issues" in cleaned_reading:
                self.validation_stats["quality_issues"] += 1
                issues = cleaned_reading['data_quality_issues']
                logger.warning(f"⚠️  {reading.get('patient_id')}: {issues}")
            
            self.validation_stats["validated"] += 1
            
            # Update the reading with cleaned version
            reading.update(cleaned_reading)
            
            # Continue with parent's processing
            return True
            
        except Exception as e:
            logger.error(f"❌ Validation error: {e}", exc_info=True)
            return False
    
    def log_validation_summary(self):
        """Log validation statistics"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 VALIDATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Valid messages: {self.validation_stats['validated']}")
        logger.info(f"⚠️  Quality issues: {self.validation_stats['quality_issues']}")
        logger.info(f"❌ Invalid messages: {self.validation_stats['invalid']}")
        
        total = (self.validation_stats['validated'] + 
                self.validation_stats['invalid'])
        if total > 0:
            success_rate = (self.validation_stats['validated'] / total) * 100
            logger.info(f"🎯 Validation success rate: {success_rate:.2f}%")
        
        logger.info("=" * 70)

def main():
    """Run consumer with validation"""
    
    logger.info("\n" + "=" * 70)
    logger.info("🏥 ICU CONSUMER WITH DATA VALIDATION")
    logger.info("=" * 70)
    logger.info("⏳ Starting consumer...")
    
    consumer = None
    
    try:
        consumer = EnhancedConsumer()
        consumer.consume_messages(
            process_callback=consumer.process_callback
        )
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Shutting down by user request...")
    
    except Exception as e:
        logger.error(f"❌ Consumer error: {e}", exc_info=True)
    
    finally:
        if consumer:
            # Log validation stats first
            consumer.log_validation_summary()
            
            # Close consumer (will log its own summary)
            consumer.close()
>>>>>>> 5518597 (Initial commit: reset and push to master)

if __name__ == "__main__":
    main()