"""
Kafka Consumer for Patient Vital Signs with Risk Processing
"""
import json
import time
import logging
from typing import Dict, Optional, Callable
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from config.config import settings
from src.stream_processing.processor import StreamProcessor
from src.kafka_producer.producer import VitalSignsProducer
from src.storage.influx_schema import InfluxDBWriter

logger = logging.getLogger(__name__)

class VitalSignsConsumer:
    """Kafka consumer for patient vital signs with risk processing"""
    
    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
        group_id: str = None,
        auto_offset_reset: str = 'earliest',
        session_timeout_ms: int = 30000,
        heartbeat_interval_ms: int = 10000
    ):
        self.topic = topic or settings.KAFKA_TOPIC_VITAL_SIGNS
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.group_id = group_id or settings.KAFKA_CONSUMER_GROUP
        
        # Initialize components
        self.processor = StreamProcessor()
        self.alert_producer = VitalSignsProducer(topic=settings.KAFKA_TOPIC_ALERTS)
        self.influx_storage = InfluxDBWriter( 
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG,
            bucket=settings.INFLUX_BUCKET
        )
        
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                max_poll_records=100,
                session_timeout_ms=session_timeout_ms,
                heartbeat_interval_ms=heartbeat_interval_ms
            )
            logger.info(f"✅ Kafka Consumer initialized: {self.bootstrap_servers}")
            logger.info(f"📡 Subscribed to topic: {self.topic}")
        
        except KafkaError as e:
            logger.error(f"❌ Failed to initialize Kafka Consumer: {e}")
            raise
    
    def consume_messages(
        self,
        process_callback: Optional[Callable[[Dict], bool]] = None,
        max_messages: Optional[int] = None,
        timeout_ms: int = 1000
    ):
        """Consume and process messages with full risk assessment pipeline"""
        messages_processed = 0
        messages_failed = 0
        start_time = time.time()
        
        logger.info("🚀 Starting consumer with risk processing...")
        
        try:
            for message in self.consumer:
                try:
                    reading = message.value
                    
                    # 🔄 Process with risk scoring
                    enriched_reading = self.processor.process_reading(reading)
                    
                    # 📊 Store in InfluxDB
                    self.influx_storage.write_vital_signs(enriched_reading)
                    
                    # 🚨 Send alerts for high-risk
                    if enriched_reading["risk_assessment"]["risk_level"] in ["HIGH", "CRITICAL"]:
                        self._send_alert(enriched_reading)
                    
                    # 🎯 Custom processing callback
                    if process_callback:
                        success = process_callback(enriched_reading)
                        if success:
                            messages_processed += 1
                        else:
                            messages_failed += 1
                    else:
                        messages_processed += 1
                    
                    # Progress logging
                    if messages_processed % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = messages_processed / elapsed if elapsed > 0 else 0
                        logger.info(f"📈 Processed {messages_processed} messages ({rate:.1f} msg/sec)")
                
                except Exception as e:
                    messages_failed += 1
                    logger.error(f"❌ Error processing message: {e}")
                    continue
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Consumer interrupted")
        
        finally:
            self._log_summary(messages_processed, messages_failed, start_time)
    
    def _send_alert(self, reading: Dict):
        """Send alert for high-risk patient"""
        alert = {
            "patient_id": reading["patient_id"],
            "alert_type": "HIGH_RISK",
            "risk_level": reading["risk_assessment"]["risk_level"],
            "risk_score": reading["risk_assessment"]["risk_score"],
            "critical_event": reading["risk_assessment"]["critical_event"],
            "timestamp": reading["timestamp"],
            "message": f"🚨 {reading['risk_assessment']['risk_level']} RISK: {reading['patient_id']}"
        }
        
        try:
            self.alert_producer.send_alert(alert)
            logger.warning(f"🚨 Alert sent for {reading['patient_id']}")
        except Exception as e:
            logger.error(f"❌ Failed to send alert: {e}")
    
    def _log_summary(self, processed: int, failed: int, start_time: float):
        """Log consumption summary"""
        elapsed = time.time() - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 CONSUMER STATISTICS")
        logger.info("=" * 60)
        logger.info(f"⏱️  Total time: {elapsed:.1f} seconds")
        logger.info(f"✅ Messages processed: {processed}")
        logger.info(f"❌ Messages failed: {failed}")
        
        if elapsed > 0:
            logger.info(f"📈 Average rate: {processed / elapsed:.1f} messages/sec")
        
        success_rate = (processed / (processed + failed) * 100) if (processed + failed) > 0 else 0
        logger.info(f"🎯 Success rate: {success_rate:.1f}%")
        logger.info("=" * 60)
    
    def close(self):
        """Close all connections"""
        try:
            self.consumer.close()
            self.alert_producer.close()
            self.influx_storage.close()
            logger.info("✅ Consumer and dependencies closed")
        except Exception as e:
            logger.error(f"❌ Error closing consumer: {e}")