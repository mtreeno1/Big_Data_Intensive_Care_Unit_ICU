"""
PostgreSQL Schema and Writer
Handles relational storage for patient metadata and events
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, JSON, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Patient(Base):
    """Patient information table"""
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50), unique=True, nullable=False, index=True)
    profile = Column(String(20), nullable=False)  # HEALTHY, AT_RISK, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSON)


class Event(Base):
    """Events and anomalies table"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # anomaly, alert, status_change
    timestamp = Column(DateTime, nullable=False, index=True)
    severity = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text)
    vital_signs = Column(JSON)
    extra_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """Alerts table"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # threshold, ml_anomaly, pattern
    timestamp = Column(DateTime, nullable=False, index=True)
    severity = Column(String(20), nullable=False)
    vital_type = Column(String(50))  # heart_rate, spo2, etc.
    value = Column(Float)
    threshold = Column(Float)
    message = Column(Text)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class ConsumerMetrics(Base):
    """Consumer performance metrics"""
    __tablename__ = 'consumer_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    messages_processed = Column(Integer)
    messages_failed = Column(Integer)
    processing_time_ms = Column(Float)
    lag = Column(Integer)
    partition = Column(Integer)
    offset = Column(Integer)


class PostgreSQLWriter:
    """Write data to PostgreSQL"""
    
    def __init__(self, connection_url: str):
        """
        Initialize PostgreSQL writer
        
        Args:
            connection_url: SQLAlchemy connection URL
        """
        try:
            self.engine = create_engine(connection_url, pool_pre_ping=True)
            Base.metadata.create_all(self.engine)  # ✅ ĐÃ SỬA: metadata thay vì extra_data
            self.Session = sessionmaker(bind=self.engine)
            logger.info(f"✅ Connected to PostgreSQL")
            self.available = True
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            self.engine = None
            self.Session = None
            self.available = False
    
    def upsert_patient(self, patient_id: str, profile: str, metadata: Optional[Dict] = None) -> bool:
        """
        Insert or update patient record
        
        Args:
            patient_id: Patient identifier
            profile: Health profile
            metadata: Additional metadata (stored in extra_data column)
            
        Returns:
            True if successful
        """
        if not self.available or self.Session is None:
            logger.debug("Skipping PostgreSQL upsert; writer unavailable")
            return False

        session = self.Session()
        try:
            patient = session.query(Patient).filter_by(patient_id=patient_id).first()
            
            if patient:
                # Update existing
                patient.profile = profile
                patient.extra_data = metadata
                patient.updated_at = datetime.utcnow()
            else:
                # Create new
                patient = Patient(
                    patient_id=patient_id,
                    profile=profile,
                    extra_data=metadata
                )
                session.add(patient)
            
            session.commit()
            logger.debug(f"✅ Upserted patient {patient_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to upsert patient: {e}")
            return False
        finally:
            session.close()
    
    def insert_event(self, patient_id: str, event_type: str, timestamp: datetime,
                    severity: str, description: str, vital_signs: Dict,
                    metadata: Optional[Dict] = None) -> bool:
        """
        Insert an event
        
        Args:
            patient_id: Patient identifier
            event_type: Type of event
            timestamp: Event timestamp
            severity: Event severity
            description: Event description
            vital_signs: Associated vital signs
            metadata: Additional metadata (stored in extra_data column)
            
        Returns:
            True if successful
        """
        if not self.available or self.Session is None:
            logger.debug("Skipping PostgreSQL event insert; writer unavailable")
            return False

        session = self.Session()
        try:
            event = Event(
                patient_id=patient_id,
                event_type=event_type,
                timestamp=timestamp,
                severity=severity,
                description=description,
                vital_signs=vital_signs,
                extra_data=metadata
            )
            session.add(event)
            session.commit()
            logger.debug(f"✅ Inserted event for patient {patient_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to insert event: {e}")
            return False
        finally:
            session.close()
    
    def insert_alert(self, patient_id: str, alert_type: str, timestamp: datetime,
                    severity: str, vital_type: str, value: float,
                    threshold: float, message: str) -> bool:
        """
        Insert an alert
        
        Args:
            patient_id: Patient identifier
            alert_type: Type of alert
            timestamp: Alert timestamp
            severity: Alert severity
            vital_type: Vital sign type
            value: Measured value
            threshold: Threshold value
            message: Alert message
            
        Returns:
            True if successful
        """
        if not self.available or self.Session is None:
            logger.debug("Skipping PostgreSQL alert insert; writer unavailable")
            return False

        session = self.Session()
        try:
            alert = Alert(
                patient_id=patient_id,
                alert_type=alert_type,
                timestamp=timestamp,
                severity=severity,
                vital_type=vital_type,
                value=value,
                threshold=threshold,
                message=message
            )
            session.add(alert)
            session.commit()
            logger.debug(f"✅ Inserted alert for patient {patient_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to insert alert: {e}")
            return False
        finally:
            session.close()
    
    def insert_metrics(self, messages_processed: int, messages_failed: int,
                      processing_time_ms: float, lag: int, partition: int,
                      offset: int) -> bool:
        """
        Insert consumer metrics
        
        Args:
            messages_processed: Number of messages processed
            messages_failed: Number of failed messages
            processing_time_ms: Processing time in milliseconds
            lag: Consumer lag
            partition: Kafka partition
            offset: Current offset
            
        Returns:
            True if successful
        """
        if not self.available or self.Session is None:
            logger.debug("Skipping PostgreSQL metrics insert; writer unavailable")
            return False

        session = self.Session()
        try:
            metrics = ConsumerMetrics(
                messages_processed=messages_processed,
                messages_failed=messages_failed,
                processing_time_ms=processing_time_ms,
                lag=lag,
                partition=partition,
                offset=offset
            )
            session.add(metrics)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to insert metrics: {e}")
            return False
        finally:
            session.close()
    
    def close(self):
        """Close database connection"""
        if self.engine is None:
            return
        self.engine.dispose()
        logger.info("✅ PostgreSQL connection closed")