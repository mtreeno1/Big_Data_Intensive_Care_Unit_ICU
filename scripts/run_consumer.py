#!/usr/bin/env python3
"""
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


if __name__ == "__main__":
    main()