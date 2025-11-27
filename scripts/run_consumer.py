#!/usr/bin/env python3
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ICUWorkflowConsumer(VitalSignsConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = MedicalDataValidator()
        self.processor = StreamProcessor()
        self.influx_db = InfluxDBManager()
        self.sql_db = DatabaseManager()
        self.workflow_stats = {"received": 0, "processed": 0, "storage_success": 0}

    def process_callback(self, reading):
        self.workflow_stats["received"] += 1
        patient_id = reading.get('patient_id', 'Unknown')

        try:
            # 1. Validate
            cleaned_reading, is_valid = self.validator.validate_and_clean(reading)
            if not is_valid: return False

            # 2. Process Risk
            processed_result = self.processor.process_vital_signs(cleaned_reading)
            risk_score = processed_result.get('risk_score', 0.0)
            risk_level = processed_result.get('risk_level', 'STABLE')
            
            self.workflow_stats["processed"] += 1

            # 3. Storage - InfluxDB (QUAN TRỌNG: Flattening chuẩn)
            vital_signs = cleaned_reading.get('vital_signs', {})
            data_to_save = {}
            
            # Tự động tách Huyết áp và ép kiểu số
            for key, value in vital_signs.items():
                if isinstance(value, dict):
                    if key == 'blood_pressure':
                        if 'systolic' in value: data_to_save['bp_systolic'] = float(value['systolic'])
                        if 'diastolic' in value: data_to_save['bp_diastolic'] = float(value['diastolic'])
                else:
                    try:
                        # Chỉ lấy dữ liệu convert được sang float
                        data_to_save[key] = float(value)
                    except (ValueError, TypeError):
                        pass

            # Thêm Risk Score
            data_to_save['risk_score'] = float(risk_score)
            
            # Ghi vào InfluxDB
            if data_to_save:
                if self.influx_db.write_vital_signs(
                    patient_id=patient_id,
                    data=data_to_save,
                    tags={'risk_level': risk_level},
                    timestamp=cleaned_reading.get('timestamp')
                ):
                    self.workflow_stats["storage_success"] += 1

            # 4. Update Postgres
            self.sql_db.update_patient_risk_status(patient_id, risk_score, risk_level)

            # Log monitor
            if self.workflow_stats["processed"] % 10 == 0:
                logger.info(f"✅ Processed: {self.workflow_stats['processed']} | Saved: {patient_id}")

            return True
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return False

    def close(self):
        self.sql_db.close()
        self.influx_db.close()
        super().close()

if __name__ == "__main__":
    consumer = ICUWorkflowConsumer()
    try:
        consumer.consume_messages(process_callback=consumer.process_callback)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()