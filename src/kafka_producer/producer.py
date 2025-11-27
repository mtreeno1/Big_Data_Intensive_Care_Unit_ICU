"""
Kafka Producer for ICU Patient Vital Signs
Sends patient data to Kafka topic
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from kafka import KafkaProducer
from kafka.errors import KafkaError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VitalSignsProducer:
    """Kafka producer for streaming patient vital signs"""
    
    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        topic: str = 'patient-vital-signs',
        batch_size: int = 16384,
        linger_ms: int = 10
    ):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka broker address
            topic: Kafka topic name
            batch_size: Batch size for sending messages
            linger_ms: Time to wait before sending batch
        """
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                batch_size=batch_size,
                linger_ms=linger_ms,
                compression_type='gzip'
            )
            logger.info(f"✅ Kafka Producer initialized: {bootstrap_servers}")
            logger.info(f"📡 Target topic: {topic}")
        
        except KafkaError as e:
            logger.error(f"❌ Failed to initialize Kafka Producer: {e}")
            raise
    
    def send_reading(self, reading: Dict, key: Optional[str] = None) -> bool:
        """
        Send a single patient reading to Kafka
        
        Args:
            reading: Patient vital signs reading
            key: Message key (typically patient_id for partitioning)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use patient_id as key for consistent partitioning
            if not key:
                key = reading.get('patient_id', 'unknown')
            
            # Add producer metadata
            reading['producer_metadata'] = {
                'sent_at': datetime.now(timezone.utc).isoformat(),
                'topic': self.topic
            }
            
            # Send to Kafka
            future = self.producer.send(
                self.topic,
                key=key,
                value=reading
            )
            
            # Wait for confirmation (with timeout)
            record_metadata = future.get(timeout=10)
            
            logger.debug(
                f"✉️  Sent: {key} -> Topic: {record_metadata.topic}, "
                f"Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}"
            )
            
            return True
        
        except KafkaError as e:
            logger.error(f"❌ Failed to send reading for {key}: {e}")
            return False
        
        except Exception as e:
            logger.error(f"❌ Unexpected error sending reading: {e}")
            return False
    
    def send_batch(self, readings: List[Dict]) -> Dict[str, int]:
        """
        Send multiple readings to Kafka
        
        Args:
            readings: List of patient readings
        
        Returns:
            Statistics dictionary
        """
        stats = {
            'total': len(readings),
            'successful': 0,
            'failed': 0
        }
        
        for reading in readings:
            if self.send_reading(reading):
                stats['successful'] += 1
            else:
                stats['failed'] += 1
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        
        logger.info(
            f"📊 Batch sent: {stats['successful']}/{stats['total']} successful, "
            f"{stats['failed']} failed"
        )
        
        return stats
    
    def close(self):
        """Close the producer and flush remaining messages"""
        try:
            logger.info("🔄 Flushing remaining messages...")
            self.producer.flush(timeout=30)
            self.producer.close()
            logger.info("✅ Kafka Producer closed successfully")
        except Exception as e:
            logger.error(f"❌ Error closing producer: {e}")
    
    


# Test
if __name__ == "__main__":
    # Test producer
    producer = VitalSignsProducer()
    
    # Test message
    test_reading = {
        'patient_id': 'PT-TEST-001',
        'timestamp': datetime.utcnow().isoformat(),
        'profile': 'HEALTHY',
        'vital_signs': {
            'heart_rate': 72,
            'spo2': 98.5,
            'temperature': 36.8
        }
    }
    
    # Send test message
    success = producer.send_reading(test_reading)
    print(f"Test message sent: {'✅ Success' if success else '❌ Failed'}")
    
    # Close
    producer.close()
