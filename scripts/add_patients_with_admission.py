#!/usr/bin/env python3
"""
Add patients with realistic ICU admissions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime, timedelta
import random

from src.database.session import SessionLocal
from src.database.models import Patient, Admission, Doctor

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Risk profile configurations
RISK_PROFILES = {
    "STABLE": {
        "initial_risk": 0.15,
        "departments": ["General ICU", "Post-Surgery ICU"],
        "admission_reasons": [
            "Post-operative monitoring",
            "Routine ICU observation",
            "Recovery from minor surgery"
        ]
    },
    "MODERATE": {
        "initial_risk": 0.45,
        "departments": ["Cardiac ICU", "Respiratory ICU"],
        "admission_reasons": [
            "Chest pain monitoring",
            "Respiratory distress",
            "Heart rhythm abnormalities"
        ]
    },
    "HIGH": {
        "initial_risk": 0.75,
        "departments": ["Cardiac ICU", "Trauma ICU"],
        "admission_reasons": [
            "Acute myocardial infarction",
            "Severe sepsis",
            "Multi-organ failure risk"
        ]
    },
    "CRITICAL": {
        "initial_risk": 0.92,
        "departments": ["Trauma ICU", "Cardiac ICU"],
        "admission_reasons": [
            "Multiple trauma",
            "Cardiogenic shock",
            "Severe septic shock"
        ]
    }
}

def get_or_create_doctors(db):
    """Get or create sample doctors for ALL departments"""
    doctors = db.query(Doctor).all()
    
    if not doctors:
        # ✅ FIX: Create doctors for ALL possible departments
        sample_doctors = [
            # Cardiac ICU
            Doctor(
                doctor_id="DR-001",
                full_name="Dr. Nguyen Thanh Long",
                specialization="Cardiology",
                department="Cardiac ICU"
            ),
            Doctor(
                doctor_id="DR-002",
                full_name="Dr. Tran Van Hieu",
                specialization="Cardiothoracic Surgery",
                department="Cardiac ICU"
            ),
            # Trauma ICU
            Doctor(
                doctor_id="DR-003",
                full_name="Dr. Le Quang Minh",
                specialization="Emergency Medicine",
                department="Trauma ICU"
            ),
            Doctor(
                doctor_id="DR-004",
                full_name="Dr. Pham Duc Anh",
                specialization="Trauma Surgery",
                department="Trauma ICU"
            ),
            # Respiratory ICU
            Doctor(
                doctor_id="DR-005",
                full_name="Dr. Hoang Thu Hien",
                specialization="Pulmonology",
                department="Respiratory ICU"
            ),
            # General ICU
            Doctor(
                doctor_id="DR-006",
                full_name="Dr. Tran Mai Anh",
                specialization="Intensive Care",
                department="General ICU"
            ),
            Doctor(
                doctor_id="DR-007",
                full_name="Dr. Nguyen Van Tuan",
                specialization="Critical Care",
                department="General ICU"
            ),
            # Post-Surgery ICU
            Doctor(
                doctor_id="DR-008",
                full_name="Dr. Le Thi Lan",
                specialization="Anesthesiology",
                department="Post-Surgery ICU"
            ),
        ]
        
        for doctor in sample_doctors:
            db.add(doctor)
        db.commit()
        doctors = sample_doctors
        logger.info(f"✅ Created {len(doctors)} doctors")
    
    return doctors

def assign_risk_profile(patient: Patient) -> str:
    """Assign risk profile based on patient characteristics"""
    conditions = patient.chronic_conditions.lower()
    
    if any(c in conditions for c in ['heart disease', 'kidney disease', 'copd']):
        return random.choice(['HIGH', 'CRITICAL'])
    elif any(c in conditions for c in ['diabetes', 'hypertension', 'asthma']):
        return random.choice(['MODERATE', 'HIGH'])
    else:
        return random.choice(['STABLE', 'MODERATE'])

def create_admission(db, patient: Patient, doctors: list, risk_profile: str = None):
    """Create ICU admission with risk profile"""
    
    # Auto-assign if not specified
    if not risk_profile:
        risk_profile = assign_risk_profile(patient)
    
    profile = RISK_PROFILES[risk_profile]
    
    # Select department
    department = random.choice(profile['departments'])
    
    # ✅ FIX: Find doctors in this department, fallback to any doctor if none found
    dept_doctors = [d for d in doctors if d.department == department]
    
    if not dept_doctors:
        logger.warning(f"⚠️  No doctors found for {department}, using fallback")
        dept_doctors = doctors  # Use any doctor as fallback
    
    doctor = random.choice(dept_doctors)
    
    # Generate admission details
    admission_time = datetime.now() - timedelta(hours=random.randint(1, 48))
    
    admission = Admission(
        admission_id=f"ADM-{patient.patient_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        admission_time=admission_time,
        department=department,
        initial_diagnosis=random.choice(profile['admission_reasons']),
        current_risk_score=profile['initial_risk'] + random.uniform(-0.05, 0.05),
        risk_level=risk_profile
    )
    
    db.add(admission)
    db.commit()
    
    return admission

def main():
    """Main function to add patients and create admissions"""
    
    logger.info("\n" + "=" * 70)
    logger.info("🏥 PATIENT IMPORT WITH RISK PROFILING")
    logger.info("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Read CSV
        csv_path = "data/patients.csv"
        df = pd.read_csv(csv_path)
        logger.info(f"📂 Found {len(df)} patients in CSV")
        
        # Get/create doctors
        doctors = get_or_create_doctors(db)
        
        # Import patients
        imported = 0
        admitted = 0
        
        for _, row in df.iterrows():
            # Check if exists
            existing = db.query(Patient).filter_by(patient_id=row['patient_id']).first()
            
            if existing:
                logger.info(f"⏭️  {row['patient_id']} already exists")
                patient = existing
            else:
                # Create patient
                patient = Patient(
                    patient_id=row['patient_id'],
                    full_name=row['full_name'],
                    date_of_birth=datetime.strptime(row['dob'], '%Y-%m-%d').date(),
                    gender=row['gender'],
                    device_id=row['device_id'],
                    blood_type=row.get('blood_type', 'Unknown'),
                    allergies=row.get('allergies', 'None'),
                    chronic_conditions=row.get('chronic_conditions', 'None')
                )
                db.add(patient)
                db.commit()
                imported += 1
                logger.info(f"✅ Imported: {patient.patient_id} - {patient.full_name}")
            
            # Check if already admitted
            active_admission = db.query(Admission).filter_by(
                patient_id=patient.patient_id,
                discharge_time=None
            ).first()
            
            if not active_admission:
                admission = create_admission(db, patient, doctors)
                admitted += 1
                logger.info(f"   🏥 Admitted as {admission.risk_level} (score: {admission.current_risk_score:.2f})")
        
        logger.info("\n" + "=" * 70)
        logger.info("📊 SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Patients imported: {imported}")
        logger.info(f"🏥 Admissions created: {admitted}")
        
        # Show distribution
        from sqlalchemy import func
        risk_dist = db.query(
            Admission.risk_level, 
            func.count(Admission.admission_id)
        ).filter(Admission.discharge_time.is_(None)).group_by(Admission.risk_level).all()
        
        logger.info("\n🎯 Risk Distribution:")
        for level, count in sorted(risk_dist, key=lambda x: ['STABLE', 'MODERATE', 'HIGH', 'CRITICAL'].index(x[0]) if x[0] in ['STABLE', 'MODERATE', 'HIGH', 'CRITICAL'] else 999):
            emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MODERATE': '🟡', 'STABLE': '🟢'}.get(level, '⚪')
            logger.info(f"   {emoji} {level:10} {count} patients")
        
        logger.info("=" * 70)
    
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()