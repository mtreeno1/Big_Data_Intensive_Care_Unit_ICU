#!/usr/bin/env python3
"""
Run Kafka Consumer with Full Data Pipeline (Validation -> Processing -> Storage -> Alerting)
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from src.kafka_consumer.consumer import VitalSignsConsumer
from src.stream_processing.data_validator import MedicalDataValidator
from src.stream_processing.processor import StreamProcessor
from src.storage.influx_storage import InfluxDBManager
from src.database.db_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class ICUWorkflowConsumer(VitalSignsConsumer):
    """
    Consumer thông minh: Không chỉ đọc mà còn Xử lý và Lưu trữ
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Khởi tạo các module con
        logger.info("🔧 Initializing Sub-systems...")
        self.validator = MedicalDataValidator()
        self.processor = StreamProcessor()
        self.influx_db = InfluxDBManager()
        self.sql_db = DatabaseManager()
        
        # Thống kê hiệu năng
        self.workflow_stats = {
            "received": 0,
            "valid": 0,
            "invalid": 0,
            "processed": 0,
            "storage_success": 0,
            "storage_failed": 0,
            "alerts_generated": 0
        }
    
    def process_callback(self, reading):
        """
        Đây là trái tim của hệ thống. Nó chạy mỗi khi có 1 tin nhắn mới.
        """
        self.workflow_stats["received"] += 1
        patient_id = reading.get('patient_id', 'Unknown')

        try:
            # --- BƯỚC 1: VALIDATION (Kiểm tra dữ liệu) ---
            cleaned_reading, is_valid = self.validator.validate_and_clean(reading)
            
            if not is_valid:
                self.workflow_stats["invalid"] += 1
                logger.debug(f"⚠️  Invalid data for {patient_id}")
                return False

            self.workflow_stats["valid"] += 1
            
            # --- BƯỚC 2: STREAM PROCESSING (Tính toán rủi ro) ---
            processed_result = self.processor.process_vital_signs(cleaned_reading)
            
            risk_score = processed_result.get('risk_score', 0.0)
            risk_level = processed_result.get('risk_level', 'STABLE')
            mews_score = processed_result.get('mews_score', 0)
            
            self.workflow_stats["processed"] += 1
            
            # --- BƯỚC 3: STORAGE (Lưu trữ) ---
            
            # 3.1. Prepare data for InfluxDB
            # Extract vital signs (handle both flat and nested structures)
            vital_signs = cleaned_reading.get('vital_signs', {})
            
            # Flatten if needed
            data_to_save = {}
            for key, value in vital_signs.items():
                if isinstance(value, dict) and 'value' in value:
                    data_to_save[key] = value['value']
                else:
                    data_to_save[key] = value
            
            # Add risk score
            data_to_save['risk_score'] = risk_score
            data_to_save['mews_score'] = mews_score
            
            # 3.2. Write to InfluxDB
            influx_success = self.influx_db.write_vital_signs(
                patient_id=patient_id,
                data=data_to_save,
                tags={'risk_level': risk_level},
                timestamp=cleaned_reading.get('timestamp')
            )
            
            if influx_success:
                self.workflow_stats["storage_success"] += 1
            else:
                self.workflow_stats["storage_failed"] += 1
                logger.warning(f"⚠️  Failed to write to InfluxDB for {patient_id}")
            
            # 3.3. Update PostgreSQL risk status
            try:
                self.sql_db.update_patient_risk_status(
                    patient_id=patient_id,
                    risk_score=risk_score,
                    risk_level=risk_level
                )
            except Exception as e:
                logger.warning(f"⚠️  Failed to update PostgreSQL for {patient_id}: {e}")

            # --- BƯỚC 4: ALERTING (Cảnh báo) ---
            if risk_level in ['HIGH', 'CRITICAL']:
                self.workflow_stats["alerts_generated"] += 1
                
                anomalies = processed_result.get('anomalies', [])
                warnings = processed_result.get('warnings', [])
                
                alert_msg = f"🚨 ALERT [{patient_id}]: Risk {risk_level} (Score: {risk_score:.2f}, MEWS: {mews_score})"
                logger.warning(alert_msg)
                
                if anomalies:
                    logger.warning(f"   Anomalies: {len(anomalies)}")
                if warnings:
                    for warning in warnings[:3]:  # Show first 3 warnings
                        logger.warning(f"   {warning}")

            # Log progress every 10 messages
            if self.workflow_stats["processed"] % 10 == 0:
                success_rate = (self.workflow_stats["storage_success"] / 
                               self.workflow_stats["processed"] * 100)
                logger.info(
                    f"✅ Processed: {self.workflow_stats['processed']} | "
                    f"Storage: {success_rate:.1f}% | "
                    f"Alerts: {self.workflow_stats['alerts_generated']}"
                )

            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing message for {patient_id}: {e}", exc_info=True)
            return False

    def close(self):
        """Dọn dẹp khi tắt"""
        logger.info("\n🛑 Closing Consumer...")
        
        # Print detailed stats
        logger.info("📊 Workflow Statistics:")
        logger.info(f"   Received: {self.workflow_stats['received']}")
        logger.info(f"   Valid: {self.workflow_stats['valid']}")
        logger.info(f"   Invalid: {self.workflow_stats['invalid']}")
        logger.info(f"   Processed: {self.workflow_stats['processed']}")
        logger.info(f"   Storage Success: {self.workflow_stats['storage_success']}")
        logger.info(f"   Storage Failed: {self.workflow_stats['storage_failed']}")
        logger.info(f"   Alerts Generated: {self.workflow_stats['alerts_generated']}")
        
        # Đóng kết nối DB
        try:
            self.sql_db.close()
        except Exception as e:
            logger.error(f"Error closing SQL DB: {e}")
        
        try:
            self.influx_db.close()
        except Exception as e:
            logger.error(f"Error closing InfluxDB: {e}")
        
        super().close()


def main():
    logger.info("=" * 80)
    logger.info("🏥 ICU INTELLIGENT CONSUMER")
    logger.info("=" * 80)
    logger.info("Pipeline: Validation → Processing → Storage → Alerting")
    logger.info("=" * 80)
    
    consumer = None
    try:
        consumer = ICUWorkflowConsumer()
        logger.info("\n📊 Consumer ready and listening...")
        logger.info("Press Ctrl+C to stop\n")
        
        # Bắt đầu vòng lặp vô tận
        consumer.consume_messages(process_callback=consumer.process_callback)
        
    except KeyboardInterrupt:
        logger.info("\n👋 User stopped the consumer")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()


if __name__ == "__main__":
    main()