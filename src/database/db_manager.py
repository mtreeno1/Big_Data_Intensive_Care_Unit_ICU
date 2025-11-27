"""
Database Management Layer for CRUD operations
FULL VERSION (Includes Delete Methods)
"""
import logging
from datetime import date, datetime
from sqlalchemy.exc import SQLAlchemyError
from src.database.session import SessionLocal
from src.database.models import Base, Patient, Admission, engine

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        """Initialize database connection"""
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            
        self.db = SessionLocal()

    def add_patient(self, patient_data: dict) -> bool:
        try:
            existing = self.db.query(Patient).filter(
                Patient.patient_id == str(patient_data["patient_id"])
            ).first()

            if existing:
                return True

            dob = date(datetime.now().year - int(patient_data.get("age", 30)), 1, 1)
            
            new_patient = Patient(
                patient_id=str(patient_data["patient_id"]),
                full_name=patient_data.get("name", "Unknown"),
                date_of_birth=dob,
                gender=patient_data.get("gender", "Unknown"),
                device_id=f"DEV-{patient_data['patient_id']}",
                blood_type=patient_data.get("blood_type", "Unknown"),
                active_monitoring=True
            )
            
            self.db.add(new_patient)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding patient: {e}")
            return False

    def add_admission(self, patient_id: str, status: str = "ACTIVE", department: str = "ICU") -> bool:
        try:
            active_adm = self.db.query(Admission).filter(
                Admission.patient_id == str(patient_id),
                Admission.discharge_time.is_(None)
            ).first()
            
            if active_adm:
                return True
                
            new_admission = Admission(
                patient_id=str(patient_id),
                department=department,
                admission_time=datetime.now(),
                initial_diagnosis="Observation",
                risk_level="STABLE"
            )
            
            self.db.add(new_admission)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding admission: {e}")
            return False

    def update_patient_risk_status(self, patient_id: str, risk_score: float, risk_level: str):
        try:
            admission = self.db.query(Admission).filter(
                Admission.patient_id == str(patient_id),
                Admission.discharge_time.is_(None)
            ).first()
            
            if not admission:
                # Auto-create logic
                patient = self.db.query(Patient).filter(Patient.patient_id == str(patient_id)).first()
                if not patient:
                    new_patient = Patient(
                        patient_id=str(patient_id),
                        full_name=f"Patient {patient_id}",
                        date_of_birth=date(1970, 1, 1),
                        gender="Unknown",
                        active_monitoring=True
                    )
                    self.db.add(new_patient)
                    self.db.commit()
                
                admission = Admission(
                    patient_id=str(patient_id),
                    admission_time=datetime.now(),
                    department="ICU-Emergency",
                    initial_diagnosis="Auto-admitted from Stream",
                    risk_level=risk_level,
                    current_risk_score=risk_score
                )
                self.db.add(admission)
                self.db.commit()
                return True

            admission.current_risk_score = risk_score
            admission.risk_level = risk_level
            admission.updated_at = datetime.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating risk status for {patient_id}: {e}")
            return False

    def get_active_patients(self):
        return self.db.query(Patient).join(Admission).filter(
            Admission.discharge_time.is_(None)
        ).all()

    # --- CÁC HÀM XÓA BẠN ĐANG CẦN ---
    
    def delete_patient(self, patient_id: str) -> bool:
        """Soft delete (Đánh dấu xóa)"""
        try:
            patient = self.db.query(Patient).filter(Patient.patient_id == str(patient_id)).first()
            if patient:
                patient.active_monitoring = False
                patient.deleted_at = datetime.now() # Đánh dấu thời gian xóa
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting patient: {e}")
            return False

    def hard_delete_patient(self, patient_id: str) -> bool:
        """Hard delete (Xóa vĩnh viễn khỏi DB)"""
        try:
            patient = self.db.query(Patient).filter(Patient.patient_id == str(patient_id)).first()
            if patient:
                self.db.delete(patient) # Lệnh này sẽ xóa cả Admissions liên quan nhờ cascade
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error hard deleting patient: {e}")
            return False

    def close(self):
        self.db.close()