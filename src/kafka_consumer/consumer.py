"""
Kafka Consumer for Patient Vital Signs
Consumes streaming data and stores in databases
"""

import json
import time
import logging
from typing import Dict, Optional, Callable
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError

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
        
        try:
            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                max_poll_records=100,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            logger.info(f"✅ Kafka Consumer initialized: {bootstrap_servers}")
            logger.info(f"📡 Subscribed to topic: {topic}")
            logger.info(f"👥 Consumer group: {group_id}")
        
        except KafkaError as e:
            logger.error(f"❌ Failed to initialize Kafka Consumer: {e}")
            raise
    
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
        messages_processed = 0
        messages_failed = 0
        start_time = time.time()
        
        logger.info("🚀 Starting consumer...")
        logger.info(f"⏳ Max messages: {max_messages if max_messages else 'Infinite'}")
        
        try:
            for message in self.consumer:
                try:
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
                    continue
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Consumer interrupted by user")
        
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
        try:
            self.consumer.close()
            logger.info("✅ Kafka Consumer closed")
        except Exception as e:
            logger.error(f"❌ Error closing consumer: {e}")