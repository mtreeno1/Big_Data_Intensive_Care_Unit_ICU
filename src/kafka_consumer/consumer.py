"""
Kafka Consumer for ICU Vital Signs
"""
import json
import logging
from typing import Callable, Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from config.config import settings
from src.kafka_producer.producer import VitalSignsProducer

logger = logging.getLogger(__name__)


class VitalSignsConsumer:
    """
    Base Kafka Consumer for Vital Signs
    """
    
    def __init__(
        self,
        bootstrap_servers: str = settings.KAFKA_BOOTSTRAP_SERVERS,
        topic: str = settings.KAFKA_TOPIC_VITAL_SIGNS,
        group_id: str = "icu-consumers",
        auto_offset_reset: str = "latest"
    ):
        """
        Initialize Kafka Consumer
        
        Args:
            bootstrap_servers: Kafka broker address
            topic: Topic to consume from
            group_id: Consumer group ID
            auto_offset_reset: Where to start reading ('earliest' or 'latest')
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        
        # Create Kafka consumer
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=True,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        # Alert producer (for sending alerts)
        self.alert_producer = VitalSignsProducer(
            bootstrap_servers=self.bootstrap_servers,
            topic=settings.KAFKA_TOPIC_ALERTS
        )
        
        # Statistics
        self.stats = {
            'received': 0,
            'processed': 0,
            'failed': 0,
            'alerts_sent': 0
        }
        
        logger.info("✅ Consumer initialized")
        logger.info(f"📡 Topic: {self.topic}")
        logger.info(f"👥 Group: {self.group_id}")
    
    def consume_messages(
        self,
        process_callback: Optional[Callable] = None,
        max_messages: Optional[int] = None
    ):
        """
        Main consumption loop
        
        Args:
            process_callback: Function to process each message
            max_messages: Maximum messages to consume (None = infinite)
        """
        logger.info("🚀 Starting consumer...")
        logger.info("⏳ Waiting for messages...")
        
        message_count = 0
        
        try:
            for message in self.consumer:
                try:
                    # Parse message
                    reading = message.value
                    self.stats['received'] += 1
                    
                    # Process message
                    if process_callback:
                        success = process_callback(reading)
                    else:
                        # Default processing
                        success = self._default_process(reading)
                    
                    if success:
                        self.stats['processed'] += 1
                    else:
                        self.stats['failed'] += 1
                    
                    # Check max messages limit
                    message_count += 1
                    if max_messages and message_count >= max_messages:
                        logger.info(f"✅ Reached max messages limit: {max_messages}")
                        break
                
                except Exception as e:
                    self.stats['failed'] += 1
                    logger.error(f"❌ Processing error: {e}")
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Consumer interrupted by user")
        
        finally:
            self._print_summary()
    
    def _default_process(self, reading: dict) -> bool:
        """
        Default message processing (can be overridden)
        
        Args:
            reading: Message data
        
        Returns:
            True if processed successfully
        """
        patient_id = reading.get('patient_id', 'Unknown')
        timestamp = reading.get('timestamp', 'Unknown')
        
        logger.info(f"📨 Received: {patient_id} at {timestamp}")
        
        # Check for critical vitals
        vital_signs = reading.get('vital_signs', {})
        
        # Simple alerting logic
        hr = vital_signs.get('heart_rate', 0)
        spo2 = vital_signs.get('spo2', 100)
        
        if hr > 120 or hr < 50 or spo2 < 90:
            logger.warning(f"🚨 Critical vitals for {patient_id}!")
            self._send_alert(reading, "CRITICAL_VITALS")
        
        return True
    
    def _send_alert(self, reading: dict, alert_type: str):
        """Send alert to Kafka alert topic"""
        try:
            alert = {
                'alert_type': alert_type,
                'patient_id': reading.get('patient_id'),
                'timestamp': reading.get('timestamp'),
                'vital_signs': reading.get('vital_signs'),
                'severity': 'HIGH'
            }
            
            self.alert_producer.send_message(alert)
            self.stats['alerts_sent'] += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to send alert: {e}")
    
    def _print_summary(self):
        """Print consumption summary"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 CONSUMER SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Messages processed: {self.stats['processed']}")
        logger.info(f"❌ Messages failed: {self.stats['failed']}")
        logger.info(f"🚨 Alerts sent: {self.stats['alerts_sent']}")
        logger.info("=" * 70)
    
    def close(self):
        """Close consumer and cleanup"""
        try:
            self.consumer.close()
            self.alert_producer.close()
            logger.info("✅ Consumer closed successfully")
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")


class FaultTolerantConsumer(VitalSignsConsumer):
    """
    Fault-tolerant consumer with retry logic
    """
    
    def __init__(self, *args, max_retries: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
    
    def consume_messages(self, process_callback=None, max_messages=None):
        """Override with retry logic"""
        
        def retry_wrapper(reading):
            """Wrapper with retry logic"""
            for attempt in range(self.max_retries):
                try:
                    if process_callback:
                        return process_callback(reading)
                    else:
                        return self._default_process(reading)
                
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"⚠️  Retry {attempt + 1}/{self.max_retries}: {e}")
                    else:
                        logger.error(f"❌ Failed after {self.max_retries} attempts: {e}")
                        return False
            
            return False
        
        # Call parent with retry wrapper
        super().consume_messages(
            process_callback=retry_wrapper,
            max_messages=max_messages
        )