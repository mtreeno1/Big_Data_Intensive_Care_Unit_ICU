"""
Stream processor: Analyze vital signs and update risk scores
"""
from typing import Dict, List
import logging
from datetime import datetime

from src.database.session import SessionLocal
from src.database.models import Admission
from src.ml_models.risk_scorer import RiskScorer


logger = logging.getLogger(__name__)

class StreamProcessor:
    """Processes streaming vital signs and updates risk assessments"""
    
    def __init__(self):
        self.risk_scorer = RiskScorer()
    
    def process_reading(self, reading: Dict) -> Dict:
        """
        Process a single vital signs reading
        Update admission risk score if patient is admitted
        """
        patient_id = reading["patient_id"]
        vital_signs = reading["vital_signs"]
        critical_event = reading.get("critical_event", "none")
        
        # Calculate risk
        risk_assessment = self.risk_scorer.assess_patient_risk(
            vital_signs, critical_event
        )
        
        # Update database if patient has active admission
        self._update_admission_risk(patient_id, risk_assessment)
        
        # Add risk data to reading
        enriched_reading = reading.copy()
        enriched_reading["risk_assessment"] = risk_assessment
        
        logger.info(f"📊 Risk assessment for {patient_id}: {risk_assessment['risk_level']} ({risk_assessment['risk_score']})")
        
        return enriched_reading
    
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