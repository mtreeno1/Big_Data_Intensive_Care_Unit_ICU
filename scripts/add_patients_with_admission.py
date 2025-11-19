#!/usr/bin/env python3
"""
Add patients with active admissions for testing
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.session import SessionLocal
from src.database.models import Patient, Admission
from sqlalchemy import select

def add_test_patients():
    """Add 5 test patients with active admissions"""
    
    test_patients = [
        {
            "patient_id": "PT-0001",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-01-15",
            "gender": "M",
            "blood_type": "O+",
            "device_id": "DEV-0001",
            "active_monitoring": True,
            "severity": "HIGH"
        },
        {
            "patient_id": "PT-0002",
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1975-05-20",
            "gender": "F",
            "blood_type": "A+",
            "device_id": "DEV-0002",
            "active_monitoring": True,
            "severity": "CRITICAL"
        },
        {
            "patient_id": "PT-0003",
            "first_name": "Bob",
            "last_name": "Johnson",
            "date_of_birth": "1990-08-10",
            "gender": "M",
            "blood_type": "B+",
            "device_id": "DEV-0003",
            "active_monitoring": True,
            "severity": "MODERATE"
        },
        {
            "patient_id": "PT-0004",
            "first_name": "Alice",
            "last_name": "Williams",
            "date_of_birth": "1985-03-25",
            "gender": "F",
            "blood_type": "AB+",
            "device_id": "DEV-0004",
            "active_monitoring": True,
            "severity": "HIGH"
        },
        {
            "patient_id": "PT-0005",
            "first_name": "Charlie",
            "last_name": "Brown",
            "date_of_birth": "1992-11-30",
            "gender": "M",
            "blood_type": "O-",
            "device_id": "DEV-0005",
            "active_monitoring": True,
            "severity": "MODERATE"
        },
    ]
    
    with SessionLocal() as db:
        print("=" * 70)
        print("🏥 Adding Test Patients with Active Admissions")
        print("=" * 70)
        
        for patient_data in test_patients:
            patient_id = patient_data["patient_id"]
            
            # Check if patient exists
            existing = db.execute(
                select(Patient).where(Patient.patient_id == patient_id)
            ).scalar_one_or_none()
            
            if existing:
                print(f"✅ Patient {patient_id} already exists")
                patient = existing
            else:
                # Create patient
                patient = Patient(**patient_data)
                db.add(patient)
                print(f"✅ Created patient {patient_id}")
            
            # Check if active admission exists
            existing_admission = db.execute(
                select(Admission).where(
                    Admission.patient_id == patient_id,
                    Admission.discharge_time.is_(None)
                )
            ).scalar_one_or_none()
            
            if existing_admission:
                print(f"   ℹ️  Already has active admission: {existing_admission.admission_id}")
            else:
                # Create active admission
                admission = Admission(
                    patient_id=patient_id,
                    admit_time=datetime.utcnow(),
                    admit_reason=f"ICU Monitoring - {patient_data['severity']} severity",
                    severity_score=3 if patient_data['severity'] == 'CRITICAL' else 2,
                    attending_physician="Dr. Smith",
                    discharge_time=None,  # Active admission
                    current_risk_score=0.5,
                    risk_level="MEDIUM"
                )
                db.add(admission)
                print(f"   ✅ Created active admission for {patient_id}")
        
        db.commit()
        
        # Verify
        print("\n" + "=" * 70)
        print("📊 Verification")
        print("=" * 70)
        
        active_admissions = db.execute(
            select(Admission).where(Admission.discharge_time.is_(None))
        ).scalars().all()
        
        print(f"✅ Total active admissions: {len(active_admissions)}")
        for adm in active_admissions:
            print(f"   - {adm.patient_id}: {adm.admission_id} (Risk: {adm.risk_level})")
        
        print("\n" + "=" * 70)
        print("🎉 Setup Complete!")
        print("=" * 70)
        print("\nNow run:")
        print("  Terminal 1: python scripts/run_producer.py")
        print("  Terminal 2: python scripts/run_consumer.py")
        print("  Terminal 3: streamlit run src/dashboard/streamlit_app.py")
        print()

if __name__ == "__main__":
    add_test_patients()