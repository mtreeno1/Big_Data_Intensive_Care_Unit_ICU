"""
Kafka Consumer for vital signs data
"""
import json
import logging
from typing import Dict, Optional, Callable
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from config.config import settings
from src.stream_processing.processor import StreamProcessor
from src.storage.influx_schema import InfluxDBWriter
from src.kafka_producer.producer import VitalSignsProducer

# ✅ FIX: Change onnx_predictor to nnx_predictor
# from src.ml_models.nnx_predictor import ONNXPredictor

logger = logging.getLogger(__name__)

class VitalSignsConsumer:
    """Kafka consumer for processing vital signs"""
    
    def __init__(
        self,
        bootstrap_servers: str = None,
        topic: str = None,
        group_id: str = None
    ):
        self.topic = topic or settings.KAFKA_TOPIC_VITAL_SIGNS
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.group_id = group_id or settings.KAFKA_CONSUMER_GROUP
        
        # Initialize components
        self.processor = StreamProcessor()
        self.influx_storage = InfluxDBWriter(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG,
            bucket=settings.INFLUX_BUCKET
        )
        self.alert_producer = VitalSignsProducer(topic=settings.KAFKA_TOPIC_ALERTS)
        
        # Statistics
        self.stats = {
            "processed": 0,
            "failed": 0,
            "alerts_sent": 0
        }
        
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                max_poll_records=100,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            logger.info(f"✅ Consumer initialized")
            logger.info(f"📡 Topic: {self.topic}")
            logger.info(f"👥 Group: {self.group_id}")
        
        except KafkaError as e:
            logger.error(f"❌ Failed to initialize consumer: {e}")
            raise
    
    def consume_messages(self, process_callback: Optional[Callable] = None):
        """
        Main consumption loop
        
        Args:
            process_callback: Optional callback for custom processing
        """
        logger.info("🚀 Starting consumer...")
        logger.info("⏳ Waiting for messages...")
        
        try:
            for message in self.consumer:
                try:
                    reading = message.value
                    
                    # Call custom callback if provided
                    if process_callback:
                        should_continue = process_callback(reading)
                        if not should_continue:
                            continue
                    
                    # Process reading
                    processed_reading = self.processor.process_reading(reading)
                    
                    # Store in InfluxDB
                    self.influx_storage.write_vital_signs(processed_reading)
                    
                    # Send alert if high risk
                    risk_level = processed_reading["risk_assessment"]["risk_level"]
                    if risk_level in ["HIGH", "CRITICAL"]:
                        self._send_alert(processed_reading)
                        self.stats["alerts_sent"] += 1
                    
                    self.stats["processed"] += 1
                    
                    # Log progress every 10 messages
                    if self.stats["processed"] % 10 == 0:
                        logger.info(f"📈 Processed: {self.stats['processed']} | "
                                  f"Alerts: {self.stats['alerts_sent']}")
                
                except Exception as e:
                    self.stats["failed"] += 1
                    logger.error(f"❌ Processing error: {e}")
                    continue
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Consumer interrupted by user")
        
        finally:
            self._log_summary()
    
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
    
    def _log_summary(self):
        """Log consumption summary"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 CONSUMER SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Messages processed: {self.stats['processed']}")
        logger.info(f"❌ Messages failed: {self.stats['failed']}")
        logger.info(f"🚨 Alerts sent: {self.stats['alerts_sent']}")
        
        if self.stats["processed"] > 0:
            success_rate = (self.stats["processed"] / (self.stats["processed"] + self.stats["failed"]) * 100)
            logger.info(f"🎯 Success rate: {success_rate:.2f}%")
        
        logger.info("=" * 70)
    
    def close(self):
        """Close all connections"""
        try:
            self.consumer.close()
            self.alert_producer.close()
            self.influx_storage.close()
            logger.info("✅ Consumer closed successfully")
        except Exception as e:
            logger.error(f"❌ Error closing consumer: {e}")