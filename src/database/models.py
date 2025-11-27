"""
Database models for ICU monitoring system
"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, 
    ForeignKey, Text, Date, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from config.config import settings

# Create Base
Base = declarative_base()

# Create engine
engine = create_engine(
    settings.get_postgres_url(),
    pool_pre_ping=True,
    echo=False
)


class Patient(Base):
    __tablename__ = 'patients'
    
    patient_id = Column(String(50), primary_key=True)
    full_name = Column(String(200), nullable=False)
    date_of_birth = Column(Date)
    age = Column(Integer)
    gender = Column(String(10))
    blood_type = Column(String(10))
    admission_date = Column(DateTime, default=datetime.utcnow)
    device_id = Column(String(50))
    chronic_conditions = Column(Text)
    
    # ✅ NEW: Active monitoring flag
    active_monitoring = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admissions = relationship("Admission", back_populates="patient")
    vital_signs = relationship("VitalSigns", back_populates="patient")


class Admission(Base):
    __tablename__ = 'admissions'
    
    admission_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(50), ForeignKey('patients.patient_id'), nullable=False)
    admission_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    discharge_time = Column(DateTime)
    admission_type = Column(String(50))  # Emergency, Elective, Transfer
    department = Column(String(100))
    initial_diagnosis = Column(Text)
    attending_physician = Column(String(200))
    risk_level = Column(String(20))  # STABLE, MODERATE, HIGH, CRITICAL
    current_risk_score = Column(Float)
    notes = Column(Text)
    
    # ✅ NEW: Status flag
    status = Column(String(20), default='ACTIVE')  # ACTIVE, DISCHARGED, TRANSFERRED
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="admissions")


class VitalSigns(Base):
    __tablename__ = 'vital_signs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(50), ForeignKey('patients.patient_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    heart_rate = Column(Float)
    blood_pressure_systolic = Column(Float)
    blood_pressure_diastolic = Column(Float)
    temperature = Column(Float)
    respiratory_rate = Column(Float)
    spo2 = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="vital_signs")


class Doctor(Base):
    __tablename__ = 'doctors'
    
    doctor_id = Column(String(50), primary_key=True)
    full_name = Column(String(200), nullable=False)
    specialization = Column(String(100))
    department = Column(String(100))
    contact_number = Column(String(20))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully")


def drop_all():
    """Drop all tables - USE WITH CAUTION!"""
    Base.metadata.drop_all(engine)
    print("⚠️  All tables dropped")


if __name__ == "__main__":
    # Create tables when run directly
    init_db()