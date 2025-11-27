"""
Fault-tolerant Kafka Consumer with retry mechanism
"""
import logging
from typing import Dict
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import time

from src.kafka_consumer.consumer import VitalSignsConsumer

logger = logging.getLogger(__name__)

class FaultTolerantConsumer(VitalSignsConsumer):
    """Consumer with automatic retry and error recovery"""
    
    def __init__(self, *args, max_retries: int = 3, retry_delay: int = 5, **kwargs):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.failed_messages = []
        super().__init__(*args, **kwargs)
    
    def process_with_retry(self, message) -> bool:
        """Process message with retry mechanism"""
        retries = 0
        
        while retries < self.max_retries:
            try:
                reading = message.value
                
                # ✅ Validate data before processing
                if not self._validate_reading(reading):
                    logger.warning(f"⚠️  Invalid reading for {reading.get('patient_id')}, skipping")
                    return False
                
                # Process normally
                enriched_reading = self.processor.process_reading(reading)
                self.influx_storage.write_vital_signs(enriched_reading)
                
                # Alert if high-risk
                if enriched_reading["risk_assessment"]["risk_level"] in ["HIGH", "CRITICAL"]:
                    self._send_alert(enriched_reading)
                
                return True
                
            except Exception as e:
                retries += 1
                logger.error(f"❌ Attempt {retries}/{self.max_retries} failed: {e}")
                
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    # Store failed message for later retry
                    self.failed_messages.append(message)
                    logger.error(f"🚨 Message failed after {self.max_retries} retries")
                    return False
    
    def _validate_reading(self, reading: Dict) -> bool:
        """Validate reading has required fields"""
        required = ["patient_id", "timestamp", "vital_signs"]
        return all(field in reading for field in required)
    
    def retry_failed_messages(self):
        """Retry processing failed messages"""
        logger.info(f"🔄 Retrying {len(self.failed_messages)} failed messages...")
        
        success_count = 0
        still_failed = []
        
        for message in self.failed_messages:
            if self.process_with_retry(message):
                success_count += 1
            else:
                still_failed.append(message)
        
        self.failed_messages = still_failed
        logger.info(f"✅ Recovered {success_count} messages, {len(still_failed)} still failed")