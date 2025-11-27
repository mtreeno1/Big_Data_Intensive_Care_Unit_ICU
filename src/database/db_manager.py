"""
Database Manager for ICU monitoring system
"""
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional, List, Dict
import logging

from .models import Patient, Admission, Doctor, VitalSigns, Base, engine
from .session import SessionLocal

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage database operations"""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    # ==================== PATIENT OPERATIONS ====================
    
    def add_patient(self, patient_data: Dict) -> Optional[Patient]:
        """Add a new patient"""
        try:
            # Check if patient already exists
            existing = self.session.query(Patient).filter(
                Patient.patient_id == patient_data['patient_id']
            ).first()
            
            if existing:
                logger.debug(f"Patient {patient_data['patient_id']} already exists")
                return existing
            
            # Calculate age if date_of_birth provided
            if 'date_of_birth' in patient_data and patient_data['date_of_birth']:
                dob = patient_data['date_of_birth']
                if isinstance(dob, str):
                    dob = datetime.strptime(dob, '%Y-%m-%d').date()
                
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                patient_data['age'] = age
            
            patient = Patient(**patient_data)
            self.session.add(patient)
            self.session.commit()
            
            logger.info(f"✅ Added patient: {patient.patient_id}")
            return patient
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error adding patient: {e}")
            return None
    
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID"""
        return self.session.query(Patient).filter(
            Patient.patient_id == patient_id
        ).first()
    
    def get_all_patients(self, limit: int = 100) -> List[Patient]:
        """Get all patients"""
        return self.session.query(Patient).limit(limit).all()
    
    def update_patient(self, patient_id: str, update_data: Dict) -> bool:
        """Update patient information"""
        try:
            patient = self.get_patient(patient_id)
            if not patient:
                logger.error(f"Patient {patient_id} not found")
                return False
            
            for key, value in update_data.items():
                if hasattr(patient, key):
                    setattr(patient, key, value)
            
            patient.updated_at = datetime.utcnow()
            self.session.commit()
            
            logger.info(f"✅ Updated patient: {patient_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error updating patient: {e}")
            return False
    
    # ==================== ADMISSION OPERATIONS ====================
    
    def add_admission(self, admission_data: Dict) -> Optional[Admission]:
        """Add admission record"""
        try:
            # Verify patient exists
            patient = self.get_patient(admission_data['patient_id'])
            if not patient:
                logger.error(f"Patient {admission_data['patient_id']} not found")
                return None
            
            admission = Admission(**admission_data)
            self.session.add(admission)
            self.session.commit()
            
            logger.info(f"✅ Added admission for patient: {admission_data['patient_id']}")
            return admission
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error adding admission: {e}")
            return None
    
    def get_active_admissions(self) -> List[Admission]:
        """Get all active admissions (not discharged)"""
        return self.session.query(Admission).filter(
            Admission.discharge_time.is_(None)
        ).all()
    
    def get_patient_current_admission(self, patient_id: str) -> Optional[Admission]:
        """Get current active admission for a patient"""
        return self.session.query(Admission).filter(
            Admission.patient_id == patient_id,
            Admission.discharge_time.is_(None)
        ).first()
    
    def update_patient_risk_status(
        self, 
        patient_id: str, 
        risk_score: float, 
        risk_level: str
    ) -> bool:
        """
        Update patient's risk status in current admission
        This is called by the consumer after processing vital signs
        
        Args:
            patient_id: Patient ID
            risk_score: Calculated risk score (0-100)
            risk_level: Risk level (STABLE, MODERATE, HIGH, CRITICAL)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current admission
            admission = self.get_patient_current_admission(patient_id)
            
            if not admission:
                logger.warning(f"No active admission for patient {patient_id}")
                return False
            
            # Update risk status
            admission.current_risk_score = risk_score
            admission.risk_level = risk_level
            
            # Commit changes
            self.session.commit()
            
            logger.debug(f"✅ Updated risk for {patient_id}: {risk_level} ({risk_score:.2f})")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error updating risk status for {patient_id}: {e}")
            return False
    
    def discharge_patient(self, admission_id: int) -> bool:
        """Discharge a patient"""
        try:
            admission = self.session.query(Admission).filter(
                Admission.admission_id == admission_id
            ).first()
            
            if not admission:
                logger.error(f"Admission {admission_id} not found")
                return False
            
            admission.discharge_time = datetime.utcnow()
            admission.status = 'DISCHARGED'
            self.session.commit()
            
            logger.info(f"✅ Discharged patient: {admission.patient_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error discharging patient: {e}")
            return False
    
    # ==================== VITAL SIGNS OPERATIONS ====================
    
    def add_vital_signs(self, vital_data: Dict) -> Optional[VitalSigns]:
        """Add vital signs reading"""
        try:
            vitals = VitalSigns(**vital_data)
            self.session.add(vitals)
            self.session.commit()
            return vitals
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Error adding vital signs: {e}")
            return None
    
    def get_patient_vitals(self, patient_id: str, limit: int = 100) -> List[VitalSigns]:
        """Get vital signs for a patient"""
        return self.session.query(VitalSigns).filter(
            VitalSigns.patient_id == patient_id
        ).order_by(VitalSigns.timestamp.desc()).limit(limit).all()
    
    # ==================== UTILITY OPERATIONS ====================
    
    def close(self):
        """Close database session"""
        self.session.close()
        logger.info("Database session closed")