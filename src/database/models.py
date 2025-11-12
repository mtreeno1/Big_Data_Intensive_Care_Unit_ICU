"""
SQLAlchemy ORM models for patient records
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Boolean, TIMESTAMP, ForeignKey

class Base(DeclarativeBase):
    """Base class for all models"""
    pass

class Patient(Base):
    """Patient master record"""
    __tablename__ = "patients"
    
    patient_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200))
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