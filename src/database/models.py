"""
SQLAlchemy ORM models for patient records
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional
<<<<<<< HEAD
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Boolean, TIMESTAMP, ForeignKey
=======
import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Boolean, TIMESTAMP, ForeignKey, Float
>>>>>>> 5518597 (Initial commit: reset and push to master)

class Base(DeclarativeBase):
    """Base class for all models"""
    pass

class Patient(Base):
    """Patient master record"""
    __tablename__ = "patients"
    
    patient_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200))
<<<<<<< HEAD
    dob: Mapped[date] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    active_monitoring: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    
    admissions: Mapped[list["Admission"]] = relationship(back_populates="patient")

class Admission(Base):
    """ICU admission record"""
    __tablename__ = "admissions"
    
    admission_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"))
    
    admit_time: Mapped[datetime] = mapped_column(TIMESTAMP)
    discharge_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    admit_reason: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    severity_score: Mapped[Optional[int]]
    attending_physician: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    discharge_reason: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    
    patient: Mapped[Patient] = relationship(back_populates="admissions")
=======
    date_of_birth: Mapped[date] = mapped_column(Date)  # ✅ Changed from 'dob'
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # ✅ ADD: Medical information
    blood_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="Unknown")
    allergies: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default="None")
    chronic_conditions: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default="None")
    
    active_monitoring: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    
    # Relationships
    admissions: Mapped[list["Admission"]] = relationship(back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient(id={self.patient_id}, name={self.full_name})>"


# ✅ ADD: Doctor model
class Doctor(Base):
    """Doctor/Physician record"""
    __tablename__ = "doctors"
    
    doctor_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200))
    specialization: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admissions: Mapped[list["Admission"]] = relationship(back_populates="doctor")
    
    def __repr__(self):
        return f"<Doctor(id={self.doctor_id}, name={self.full_name}, dept={self.department})>"


class Admission(Base):
    """Patient admission record with risk assessment"""
    __tablename__ = "admissions"
    
    admission_id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"ADM-{uuid.uuid4().hex[:8].upper()}")
    patient_id: Mapped[str] = mapped_column(String(50), ForeignKey("patients.patient_id"))
    doctor_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("doctors.doctor_id"), nullable=True)  # ✅ ADD
    
    # Admission details
    admission_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)  # ✅ Changed from admit_time
    discharge_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # ✅ ADD
    initial_diagnosis: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # ✅ Changed from admit_reason
    discharge_summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # ✅ Changed from discharge_reason
    
    severity_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    attending_physician: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Deprecated, use doctor_id
    
    # Risk assessment fields
    current_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=None)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=None)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient: Mapped["Patient"] = relationship(back_populates="admissions")
    doctor: Mapped[Optional["Doctor"]] = relationship(back_populates="admissions")  # ✅ ADD
    
    def __repr__(self):
        return f"<Admission(id={self.admission_id}, patient={self.patient_id}, risk={self.risk_level})>"
>>>>>>> 5518597 (Initial commit: reset and push to master)
