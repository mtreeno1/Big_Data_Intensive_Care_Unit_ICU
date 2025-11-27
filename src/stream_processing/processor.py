"""
<<<<<<< HEAD
Stream Processor
Main processing logic for incoming vital signs
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from .aggregator import WindowAggregator
from ..ml.alert_model import AlertInferenceService

logger = logging.getLogger(__name__)


class VitalSignsProcessor:
    """Process incoming vital signs readings"""
    
    def __init__(self, influx_writer, postgres_writer, alert_service: Optional[AlertInferenceService] = None):
        """
        Initialize processor
        
        Args:
            influx_writer: InfluxDBWriter instance
            postgres_writer: PostgreSQLWriter instance
        """
        self.influx_writer = influx_writer
        self.postgres_writer = postgres_writer
        self.alert_service = alert_service
        
        # Create aggregators for different time windows
        self.aggregators = {
            '1m': WindowAggregator(window_seconds=60),
            '5m': WindowAggregator(window_seconds=300),
            '1h': WindowAggregator(window_seconds=3600)
        }
        
        # Track patient states
        self.patient_states: Dict[str, Dict] = {}
        
        if self.alert_service:
            logger.info("🤖 Vital alert model loaded for streaming inference")
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

            # Run ML-based alert detection before downstream processing.
            self._apply_alert_model(reading, vitals)

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
            },
            'model_loaded': bool(self.alert_service)
        }

    def _apply_alert_model(self, reading: Dict, vitals: Dict):
        """Score vitals with the alert classifier and merge results into metadata."""
        if not self.alert_service:
            return
        try:
            model_result = self.alert_service.predict(vitals)
        except Exception as exc:
            logger.error(f"❌ Alert model inference failed: {exc}")
            return

        if not model_result:
            return

        metadata = reading.setdefault('metadata', {})
        metadata['model_alerts'] = model_result

        summary = model_result.get('summary', {})
        if summary.get('has_alert'):
            metadata['has_anomaly'] = True
            alerts = model_result.get('alerts', {})
            existing_details = metadata.get('anomaly_details')
            if not isinstance(existing_details, dict):
                existing_details = {}

            sources = list(existing_details.get('sources', []))
            if 'alert_model' not in sources:
                sources.append('alert_model')

            existing_details.update({
                'sources': sources,
                'alert_model': alerts
            })
            metadata['anomaly_details'] = existing_details

            logger.debug(
                "🚨 Alert model flagged anomalies: %s",
                {key: val for key, val in alerts.items() if val.get('is_alert')}
            )
=======
Stream processor: Analyze vital signs and update risk scores
"""
from typing import Dict, List
import logging
from datetime import datetime

from src.database.session import SessionLocal
from src.database.models import Admission
from config.config import settings
from src.ml_models.risk_scorer import RiskScorer
from src.stream_processing.forecaster import VitalForecaster
try:
    from src.ml_models.joblib_predictor import RiskModelPredictor
except Exception:
    RiskModelPredictor = None  # type: ignore


logger = logging.getLogger(__name__)

class StreamProcessor:
    """Processes streaming vital signs and updates risk assessments"""
    
    def __init__(self, forecast_horizon_sec: int = 300):
        self.risk_scorer = RiskScorer()
        self.ml_predictor = None
        self.forecaster = VitalForecaster(window_size=60)
        self.forecast_horizon_sec = forecast_horizon_sec
        if getattr(settings, "USE_ML_MODEL", False) and RiskModelPredictor is not None:
            try:
                self.ml_predictor = RiskModelPredictor()
                logger.info("✅ ML predictor enabled for risk assessment")
            except Exception as e:
                logger.warning(f"⚠️  Could not enable ML predictor: {e}. Falling back to heuristic scorer.")
    
    def process_reading(self, reading: Dict) -> Dict:
        """
        Process a single vital signs reading
        Update admission risk score if patient is admitted
        """
        patient_id = reading["patient_id"]
        vital_signs = reading["vital_signs"]
        critical_event = reading.get("critical_event", "none")
        ts = reading.get("timestamp")
        if isinstance(ts, str):
            try:
                ts_dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except Exception:
                ts_dt = datetime.utcnow()
        elif isinstance(ts, datetime):
            ts_dt = ts
        else:
            ts_dt = datetime.utcnow()
        
        # Heuristic baseline risk
        heuristic = self.risk_scorer.assess_patient_risk(vital_signs, critical_event)
        final_assessment = heuristic.copy()
        final_assessment["source"] = "heuristic"
        
        # Optional ML model risk for current state
        if self.ml_predictor is not None:
            try:
                ml_pred = self.ml_predictor.predict(reading)
                # Apply critical event multiplier similar to heuristic
                event_multiplier = {
                    "none": 1.0,
                    "cardiac_arrest": 2.0,
                    "respiratory_failure": 1.8,
                    "shock": 1.8,
                    "sepsis": 1.5,
                }.get(critical_event, 1.0)
                ml_score = min(1.0, float(ml_pred.get("risk_score", 0.0)) * event_multiplier)
                # Choose ML as primary if enabled
                final_assessment = {
                    "risk_score": round(ml_score, 3),
                    "risk_level": self.risk_scorer.get_risk_level(ml_score).value,
                    "critical_event": critical_event,
                    "assessment_time": datetime.utcnow().isoformat() + "Z",
                    "source": ml_pred.get("model", "ml"),
                    "ml_details": {k: v for k, v in ml_pred.items() if k not in ("risk_score", "risk_level")},
                    "heuristic_backup": {
                        "risk_score": heuristic["risk_score"],
                        "risk_level": heuristic["risk_level"],
                    },
                }
            except Exception as e:
                logger.error(f"❌ ML prediction failed for {patient_id}: {e}. Using heuristic result.")
        
        # Forecast risk at horizon
        forecast = self._forecast_risk(patient_id, ts_dt, vital_signs, critical_event)
        if forecast:
            final_assessment["forecast"] = forecast
        
        # Update database if patient has active admission
        self._update_admission_risk(patient_id, final_assessment)
        
        # Add risk data to reading
        enriched_reading = reading.copy()
        enriched_reading["risk_assessment"] = final_assessment
        
        logger.info(
            f"📊 Risk assessment for {patient_id}: {final_assessment['risk_level']} ({final_assessment['risk_score']})"
            + (f" | ⏭️  {forecast['risk_level']}@{forecast['horizon_sec']}s ({forecast['risk_score']})" if forecast else "")
        )
        
        return enriched_reading

    def _forecast_risk(self, patient_id: str, timestamp: datetime, vitals: Dict, critical_event: str) -> Dict | None:
        try:
            fc_vitals = self.forecaster.forecast_vitals(
                patient_id, timestamp, vitals, horizon_sec=self.forecast_horizon_sec
            )
            if not fc_vitals:
                return None
            # Heuristic forecast
            heur_fc = self.risk_scorer.assess_patient_risk(fc_vitals, critical_event)
            fc_assessment = {
                "risk_score": heur_fc["risk_score"],
                "risk_level": heur_fc["risk_level"],
                "horizon_sec": self.forecast_horizon_sec,
            }
            # ML forecast if available
            if self.ml_predictor is not None:
                fc_reading = {
                    "patient_id": patient_id,
                    "timestamp": (timestamp).isoformat(),
                    "vital_signs": fc_vitals,
                    "critical_event": critical_event,
                }
                try:
                    ml_fc = self.ml_predictor.predict(fc_reading)
                    ml_score = float(ml_fc.get("risk_score", fc_assessment["risk_score"]))
                    ml_score = max(0.0, min(1.0, ml_score))
                    # Prefer ML forecast
                    fc_assessment.update({
                        "risk_score": round(ml_score, 3),
                        "risk_level": self.risk_scorer.get_risk_level(ml_score).value,
                        "model": ml_fc.get("model", "ml"),
                    })
                except Exception:
                    pass
            return fc_assessment
        except Exception as e:
            logger.debug(f"Forecasting failed for {patient_id}: {e}")
            return None
    
    def _update_admission_risk(self, patient_id: str, risk_assessment: Dict):
        """Update admission record with latest risk score"""
        try:
            with SessionLocal() as db:
                # Find active admission for patient
                admission = db.query(Admission).filter(
                    Admission.patient_id == patient_id,
                    Admission.discharge_time.is_(None)  # Active admission
                ).first()
                
                if admission:
                    admission.current_risk_score = risk_assessment["risk_score"]
                    admission.risk_level = risk_assessment["risk_level"]
                    admission.updated_at = datetime.utcnow()
                    
                    db.commit()
                    logger.info(f"✅ Updated risk for admission {admission.admission_id}")
                else:
                    logger.debug(f"No active admission found for {patient_id}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to update risk for {patient_id}: {e}")
    
    def process_batch(self, readings: List[Dict]) -> List[Dict]:
        """Process batch of readings"""
        processed = []
        for reading in readings:
            try:
                processed_reading = self.process_reading(reading)
                processed.append(processed_reading)
            except Exception as e:
                logger.error(f"Failed to process reading for {reading.get('patient_id')}: {e}")
        
        return processed

# Backward compatibility alias for older imports
VitalSignsProcessor = StreamProcessor
>>>>>>> 5518597 (Initial commit: reset and push to master)
