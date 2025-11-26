"""
Audit Trail for Compliance and Debugging
"""
import logging
import json
from datetime import datetime
from typing import Dict
from src.database.session import SessionLocal
from sqlalchemy import Column, Integer, String, JSON, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuditLog(Base):
    """Store audit trail in PostgreSQL"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    patient_id = Column(String(50), index=True)
    event_type = Column(String(50), index=True)  # "reading", "alert", "error", "inference"
    event_data = Column(JSON)
    risk_score = Column(Float, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    error_message = Column(String(500), nullable=True)

logger = logging.getLogger(__name__)

class AuditLogger:
    """Log all events for audit trail"""
    
    @staticmethod
    def log_reading(reading: Dict, processing_time: float):
        """Log vital signs reading"""
        try:
            with SessionLocal() as db:
                log = AuditLog(
                    patient_id=reading["patient_id"],
                    event_type="reading",
                    event_data=reading,
                    risk_score=reading.get("risk_assessment", {}).get("risk_score"),
                    processing_time_ms=processing_time
                )
                db.add(log)
                db.commit()
        except Exception as e:
            logger.error(f"❌ Audit log failed: {e}")
    
    @staticmethod
    def log_alert(alert: Dict):
        """Log alert event"""
        try:
            with SessionLocal() as db:
                log = AuditLog(
                    patient_id=alert["patient_id"],
                    event_type="alert",
                    event_data=alert,
                    risk_score=alert.get("risk_score")
                )
                db.add(log)
                db.commit()
        except Exception as e:
            logger.error(f"❌ Audit log failed: {e}")
    
    @staticmethod
    def log_error(patient_id: str, error: str, event_data: Dict = None):
        """Log error event"""
        try:
            with SessionLocal() as db:
                log = AuditLog(
                    patient_id=patient_id,
                    event_type="error",
                    event_data=event_data or {},
                    error_message=error[:500]
                )
                db.add(log)
                db.commit()
        except Exception as e:
            logger.error(f"❌ Audit log failed: {e}")