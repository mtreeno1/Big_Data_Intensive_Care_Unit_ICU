"""
Kafka Producer for Patient Vital Signs
Streams real-time patient data to Kafka topics
"""

import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
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
                'sent_at': datetime.utcnow().isoformat(),
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


class StreamingProducer:
    """
    Continuous streaming producer
    Manages patient simulators and continuously streams data
    """
    
    def __init__(
        self,
        producer: VitalSignsProducer,
        interval_seconds: float = 1.0
    ):
        """
        Initialize streaming producer
        
        Args:
            producer: VitalSignsProducer instance
            interval_seconds: Time between readings (seconds)
        """
        self.producer = producer
        self.interval = interval_seconds
        self.is_running = False
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'start_time': None,
            'batches_sent': 0
        }
    
    def start_streaming(self, simulator, duration_seconds: Optional[int] = None):
        """
        Start streaming data from simulator
        
        Args:
            simulator: MultiPatientSimulator instance
            duration_seconds: How long to stream (None = infinite)
        """
        self.is_running = True
        self.stats['start_time'] = datetime.utcnow()
        
        logger.info("🚀 Starting streaming producer...")
        logger.info(f"⏱️  Interval: {self.interval} seconds")
        logger.info(f"👥 Patients: {simulator.num_patients}")
        
        if duration_seconds:
            logger.info(f"⏳ Duration: {duration_seconds} seconds")
        else:
            logger.info("⏳ Duration: Infinite (press Ctrl+C to stop)")
        
        start_time = time.time()
        
        try:
            while self.is_running:
                # Check duration
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    logger.info(f"⏰ Duration limit reached ({duration_seconds}s)")
                    break
                
                # Generate batch
                batch = simulator.generate_batch()
                
                # Send to Kafka
                batch_stats = self.producer.send_batch(batch)
                
                # Update statistics
                self.stats['total_sent'] += batch_stats['successful']
                self.stats['total_failed'] += batch_stats['failed']
                self.stats['batches_sent'] += 1
                
                # Log progress every 10 batches
                if self.stats['batches_sent'] % 10 == 0:
                    elapsed = (datetime.utcnow() - self.stats['start_time']).total_seconds()
                    rate = self.stats['total_sent'] / elapsed if elapsed > 0 else 0
                    logger.info(
                        f"📈 Progress: {self.stats['batches_sent']} batches, "
                        f"{self.stats['total_sent']} readings, "
                        f"{rate:.1f} readings/sec"
                    )
                
                # Wait for next interval
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Streaming interrupted by user")
        
        except Exception as e:
            logger.error(f"❌ Error during streaming: {e}")
            raise
        
        finally:
            self.stop_streaming()
    
    def stop_streaming(self):
        """Stop streaming and show final statistics"""
        self.is_running = False
        
        if self.stats['start_time']:
            elapsed = (datetime.utcnow() - self.stats['start_time']).total_seconds()
            
            logger.info("\n" + "=" * 60)
            logger.info("📊 STREAMING STATISTICS")
            logger.info("=" * 60)
            logger.info(f"⏱️  Total time: {elapsed:.1f} seconds")
            logger.info(f"📦 Batches sent: {self.stats['batches_sent']}")
            logger.info(f"✅ Readings sent: {self.stats['total_sent']}")
            logger.info(f"❌ Failed: {self.stats['total_failed']}")
            
            if elapsed > 0:
                logger.info(f"📈 Average rate: {self.stats['total_sent'] / elapsed:.1f} readings/sec")
            
            logger.info("=" * 60)


# Example usage
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from src.data_generation.patient_simulator import MultiPatientSimulator
    
    # Configuration
    KAFKA_BROKER = 'localhost:9092'
    TOPIC = 'patient-vital-signs'
    NUM_PATIENTS = 10
    INTERVAL = 1.0  # 1 second between readings
    DURATION = 60  # Stream for 60 seconds
    
    try:
        # Initialize components
        logger.info("Initializing system...")
        
        # Create patient simulator
        simulator = MultiPatientSimulator(num_patients=NUM_PATIENTS)
        logger.info(f"✅ Created simulator with {NUM_PATIENTS} patients")
        
        # Create Kafka producer
        producer = VitalSignsProducer(
            bootstrap_servers=KAFKA_BROKER,
            topic=TOPIC
        )
        
        # Create streaming producer
        streamer = StreamingProducer(producer, interval_seconds=INTERVAL)
        
        # Start streaming
        streamer.start_streaming(simulator, duration_seconds=DURATION)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    
    finally:
        # Cleanup
        if 'producer' in locals():
            producer.close()
        
        logger.info("👋 Program terminated")