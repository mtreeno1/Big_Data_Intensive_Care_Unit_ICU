"""
Stream Processor
Main processing logic for incoming vital signs
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from .aggregator import WindowAggregator

logger = logging.getLogger(__name__)


class VitalSignsProcessor:
    """Process incoming vital signs readings"""
    
    def __init__(self, influx_writer, postgres_writer):
        """
        Initialize processor
        
        Args:
            influx_writer: InfluxDBWriter instance
            postgres_writer: PostgreSQLWriter instance
        """
        self.influx_writer = influx_writer
        self.postgres_writer = postgres_writer
        
        # Create aggregators for different time windows
        self.aggregators = {
            '1m': WindowAggregator(window_seconds=60),
            '5m': WindowAggregator(window_seconds=300),
            '1h': WindowAggregator(window_seconds=3600)
        }
        
        # Track patient states
        self.patient_states: Dict[str, Dict] = {}
        
        logger.info("✅ VitalSignsProcessor initialized")
    
    def process_reading(self, reading: Dict) -> bool:
        """
        Process a single vital signs reading
        
        Args:
            reading: Patient reading from Kafka
            
        Returns:
            True if successful, False otherwise
        """
        try:
            patient_id = reading['patient_id']
            timestamp_str = reading['timestamp']
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            vitals = reading['vital_signs']
            profile = reading.get('profile', 'UNKNOWN')
            metadata = reading.get('metadata', {})
            
            # 1. Store raw data in InfluxDB
            success_influx = self.influx_writer.write_vital_signs(reading)
            
            if not success_influx:
                logger.warning(f"⚠️  Failed to write to InfluxDB: {patient_id}")
            
            # 2. Update patient record in PostgreSQL
            success_postgres = self.postgres_writer.upsert_patient(
                patient_id=patient_id,
                profile=profile,
                metadata=metadata
            )
            
            if not success_postgres:
                logger.warning(f"⚠️  Failed to update patient: {patient_id}")
            
            # 3. Add to aggregation windows
            for window_name, aggregator in self.aggregators.items():
                aggregator.add_reading(patient_id, timestamp, vitals)
            
            # 4. Check for anomalies
            if metadata.get('has_anomaly', False):
                self._handle_anomaly(reading, timestamp)
            
            # 5. Update patient state
            self._update_patient_state(patient_id, reading)
            
            # 6. Every minute, compute and store aggregates
            if self._should_compute_aggregates(patient_id):
                self._compute_and_store_aggregates(patient_id, timestamp)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing reading: {e}")
            return False
    
    def _handle_anomaly(self, reading: Dict, timestamp: datetime):
        """Handle detected anomaly"""
        try:
            patient_id = reading['patient_id']
            anomaly_details = reading['metadata'].get('anomaly_details', {})
            
            # Create event in PostgreSQL
            self.postgres_writer.insert_event(
                patient_id=patient_id,
                event_type='anomaly',
                timestamp=timestamp,
                severity='MEDIUM',
                description='Anomaly detected in vital signs',
                vital_signs=reading['vital_signs'],
                metadata=anomaly_details
            )
            
            logger.info(f"🚨 Anomaly detected: {patient_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling anomaly: {e}")
    
    def _update_patient_state(self, patient_id: str, reading: Dict):
        """Update internal patient state"""
        self.patient_states[patient_id] = {
            'last_reading_time': datetime.utcnow(),
            'profile': reading.get('profile'),
            'reading_count': self.patient_states.get(patient_id, {}).get('reading_count', 0) + 1
        }
    
    def _should_compute_aggregates(self, patient_id: str) -> bool:
        """Check if it's time to compute aggregates"""
        state = self.patient_states.get(patient_id, {})
        reading_count = state.get('reading_count', 0)
        
        # Compute aggregates every 60 readings (approximately 1 minute)
        return reading_count > 0 and reading_count % 60 == 0
    
    def _compute_and_store_aggregates(self, patient_id: str, timestamp: datetime):
        """Compute and store aggregated statistics"""
        try:
            for window_name, aggregator in self.aggregators.items():
                aggregates = aggregator.get_aggregates(patient_id)
                
                if aggregates:
                    self.influx_writer.write_aggregated_data(
                        patient_id=patient_id,
                        window=window_name,
                        aggregates=aggregates,
                        timestamp=timestamp.isoformat()
                    )
                    
                    logger.debug(f"📊 Stored aggregates for {patient_id} ({window_name})")
        
        except Exception as e:
            logger.error(f"❌ Error computing aggregates: {e}")
    
    def get_statistics(self) -> Dict:
        """Get processor statistics"""
        return {
            'active_patients': len(self.patient_states),
            'total_readings': sum(
                state.get('reading_count', 0) 
                for state in self.patient_states.values()
            ),
            'aggregator_buffers': {
                window: len(agg.get_active_patients())
                for window, agg in self.aggregators.items()
            }
        }