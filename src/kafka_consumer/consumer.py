"""
<<<<<<< HEAD
Kafka Consumer for Patient Vital Signs
Consumes streaming data and stores in databases
"""

import json
import time
=======
Kafka Consumer for vital signs data
"""
import json
>>>>>>> 5518597 (Initial commit: reset and push to master)
import logging
from typing import Dict, Optional, Callable
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError

<<<<<<< HEAD
logger = logging.getLogger(__name__)


class VitalSignsConsumer:
    """Kafka consumer for patient vital signs"""
    
    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        topic: str = 'patient-vital-signs',
        group_id: str = 'icu-consumers',
        auto_offset_reset: str = 'earliest'
    ):
        """
        Initialize Kafka consumer
        
        Args:
            bootstrap_servers: Kafka broker address
            topic: Kafka topic to consume from
            group_id: Consumer group ID
            auto_offset_reset: Where to start reading ('earliest' or 'latest')
        """
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        
        self.consumer = None
        self.available = False

        try:
            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
=======
from config.config import settings
from src.stream_processing.processor import StreamProcessor
from src.storage.influx_schema import InfluxDBWriter
from src.storage.postgres_schema import PostgreSQLWriter
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
        # Storage for alerts/metrics
        try:
            self.pg_storage = PostgreSQLWriter(connection_url=settings.get_postgres_url())
        except Exception:
            self.pg_storage = None
        # Initialize alert producer lazily to avoid failing if Kafka isn't ready
        try:
            self.alert_producer = VitalSignsProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS, topic=settings.KAFKA_TOPIC_ALERTS)
        except Exception as e:
            logger.warning(f"⚠️  Alert producer init failed: {e}. Will retry on-demand when sending alerts.")
            self.alert_producer = None
        
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
>>>>>>> 5518597 (Initial commit: reset and push to master)
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                max_poll_records=100,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
<<<<<<< HEAD
            self.available = True
            logger.info(f"✅ Kafka Consumer initialized: {bootstrap_servers}")
            logger.info(f"📡 Subscribed to topic: {topic}")
            logger.info(f"👥 Consumer group: {group_id}")
        
        except KafkaError as e:
            logger.error(f"❌ Failed to initialize Kafka Consumer: {e}")
            self.consumer = None
            self.available = False
    
    def consume_messages(
        self,
        process_callback: Callable[[Dict], bool],
        max_messages: Optional[int] = None,
        timeout_ms: int = 1000
    ):
        """
        Consume messages from Kafka and process them
        
        Args:
            process_callback: Function to process each message
            max_messages: Maximum number of messages to consume (None = infinite)
            timeout_ms: Timeout for polling
        """
        if not self.available or self.consumer is None:
            logger.error("Kafka consumer unavailable; skipping message consumption")
            return

        messages_processed = 0
        messages_failed = 0
        start_time = time.time()
        
        logger.info("🚀 Starting consumer...")
        logger.info(f"⏳ Max messages: {max_messages if max_messages else 'Infinite'}")
=======
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
>>>>>>> 5518597 (Initial commit: reset and push to master)
        
        try:
            for message in self.consumer:
                try:
<<<<<<< HEAD
                    # Extract message data
                    reading = message.value
                    partition = message.partition
                    offset = message.offset
                    
                    logger.debug(
                        f"📨 Received: Patient {reading['patient_id']} "
                        f"(partition: {partition}, offset: {offset})"
                    )
                    
                    # Process message
                    processing_start = time.time()
                    success = process_callback(reading)
                    processing_time = (time.time() - processing_start) * 1000
                    
                    if success:
                        messages_processed += 1
                        logger.debug(f"✅ Processed in {processing_time:.2f}ms")
                    else:
                        messages_failed += 1
                        logger.warning(f"⚠️  Processing failed for {reading['patient_id']}")
                    
                    # Log progress every 100 messages
                    if messages_processed % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = messages_processed / elapsed if elapsed > 0 else 0
                        logger.info(
                            f"📈 Progress: {messages_processed} processed, "
                            f"{messages_failed} failed, {rate:.1f} msg/sec"
                        )
                    
                    # Check if we've reached max messages
                    if max_messages and messages_processed >= max_messages:
                        logger.info(f"✅ Reached max messages: {max_messages}")
                        break
                
                except Exception as e:
                    messages_failed += 1
                    logger.error(f"❌ Error processing message: {e}")
=======
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
                    
                    # Send alert if current risk is high
                    risk = processed_reading["risk_assessment"]
                    risk_level = risk["risk_level"]
                    if risk_level in ["HIGH", "CRITICAL"]:
                        self._send_alert(
                            processed_reading,
                            alert_type="HIGH_RISK",
                            message=f"🚨 {risk_level} RISK: {processed_reading['patient_id']}"
                        )
                        self.stats["alerts_sent"] += 1
                    # Forecast alert if future risk is high
                    forecast = risk.get("forecast")
                    if forecast and forecast.get("risk_level") in ["HIGH", "CRITICAL"]:
                        self._send_alert(
                            processed_reading,
                            alert_type="FORECAST_HIGH_RISK",
                            message=f"⏭️  Forecast {forecast['risk_level']} in {forecast['horizon_sec']}s: {processed_reading['patient_id']}"
                        )
                        self.stats["alerts_sent"] += 1
                    
                    self.stats["processed"] += 1
                    
                    # Log progress every 10 messages
                    if self.stats["processed"] % 10 == 0:
                        logger.info(f"📈 Processed: {self.stats['processed']} | "
                                  f"Alerts: {self.stats['alerts_sent']}")
                
                except Exception as e:
                    self.stats["failed"] += 1
                    logger.error(f"❌ Processing error: {e}")
>>>>>>> 5518597 (Initial commit: reset and push to master)
                    continue
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Consumer interrupted by user")
        
<<<<<<< HEAD
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
            raise
        
        finally:
            self._log_summary(messages_processed, messages_failed, start_time)
    
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
        """Close the consumer"""
        if not self.consumer:
            return
        try:
            self.consumer.close()
            logger.info("✅ Kafka Consumer closed")
=======
        finally:
            self._log_summary()
    
    def _send_alert(self, reading: Dict, alert_type: str, message: str):
        """Send alert for patient"""
        risk = reading["risk_assessment"]
        alert = {
            "patient_id": reading["patient_id"],
            "alert_type": alert_type,
            "risk_level": risk.get("risk_level"),
            "risk_score": risk.get("risk_score"),
            "critical_event": risk.get("critical_event"),
            "timestamp": reading.get("timestamp"),
            "message": message,
        }
        try:
            # Send to Kafka if producer available
            if self.alert_producer:
                self.alert_producer.send_alert(alert)
            # Persist to Postgres storage if available
            if self.pg_storage:
                try:
                    self.pg_storage.insert_alert(
                        patient_id=alert["patient_id"],
                        alert_type=alert_type,
                        timestamp=datetime.utcnow(),
                        severity=alert.get("risk_level") or "UNKNOWN",
                        vital_type="risk",
                        value=float(alert.get("risk_score") or 0.0),
                        threshold=0.0,
                        message=message,
                    )
                except Exception:
                    pass
            logger.warning(f"🚨 {alert_type} for {reading['patient_id']}")
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
>>>>>>> 5518597 (Initial commit: reset and push to master)
        except Exception as e:
            logger.error(f"❌ Error closing consumer: {e}")