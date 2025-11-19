"""
SQLAlchemy ORM models for patient records
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional
import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Boolean, TIMESTAMP, ForeignKey, Float

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
    """Patient admission record with risk assessment"""
    __tablename__ = "admissions"
    
    admission_id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: f"ADM-{uuid.uuid4().hex[:8].upper()}")
    patient_id: Mapped[str] = mapped_column(String(50), ForeignKey("patients.patient_id"))
    admit_time: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    discharge_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    admit_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    discharge_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    severity_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    attending_physician: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # ✅ Add created_at
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    
    # ✅ Add updated_at
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, default=None)
    
    # Risk assessment fields
    current_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=None)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=None)
    
    # Relationships
    patient: Mapped["Patient"] = relationship(back_populates="admissions")