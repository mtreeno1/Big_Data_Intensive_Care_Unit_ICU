"""
Add real high-risk patients from icu_like_cases.csv to existing system
These patients will be automatically picked up by run_producer.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime, timedelta
import random
from src.database.session import SessionLocal
from src.database.models import Patient, Admission

def load_high_risk_from_csv():
    """Load high-risk patients from icu_like_cases.csv"""
    
    db = SessionLocal()
    
    # Read CSV
    csv_path = Path(__file__).parent.parent / 'data' / 'icu_like_cases.csv'
    
    if not csv_path.exists():
        print(f"❌ File not found: {csv_path}")
        return
    
    print("\n" + "="*80)
    print("🏥 ADDING HIGH-RISK PATIENTS FROM ICU_LIKE_CASES.CSV")
    print("="*80)
    
    df = pd.read_csv(csv_path)
    print(f"\n📊 Total cases in CSV: {len(df)}")
    
    # Filter HIGH-RISK patients
    high_risk_criteria = []
    
    if 'asa' in df.columns:
        high_risk_criteria.append(df['asa'] >= 4)
    
    if 'icu_days' in df.columns:
        high_risk_criteria.append(df['icu_days'] >= 3)
    
    if 'emop' in df.columns:
        high_risk_criteria.append(df['emop'] == 1)
    
    # At least 2 criteria must be met
    high_risk_mask = sum(high_risk_criteria) >= 2
    high_risk_df = df[high_risk_mask]
    
    # Sort by risk (ASA + ICU days)
    if 'asa' in df.columns and 'icu_days' in df.columns:
        high_risk_df = high_risk_df.sort_values(['asa', 'icu_days'], ascending=[False, False])
    
    # Take top 10
    top_patients = high_risk_df.head(10)
    
    print(f"✅ Found {len(high_risk_df)} high-risk patients")
    print(f"📋 Adding top 10 to database...\n")
    
    blood_types = ['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-', 'AB-']
    departments = ['ICU', 'SICU', 'MICU', 'CCU']
    physicians = ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams', 'Dr. Brown', 'Dr. Jones']
    
    added_count = 0
    
    for idx, row in top_patients.iterrows():
        caseid = int(row['caseid'])
        patient_id = f"ICU-{caseid:06d}"
        
        # Check if exists
        existing = db.query(Patient).filter_by(patient_id=patient_id).first()
        if existing:
            print(f"⚠️  {patient_id} already exists - skipping")
            continue
        
        # Extract data
        age = int(row['age']) if pd.notna(row['age']) else random.randint(50, 85)
        gender = row['sex'] if pd.notna(row['sex']) else random.choice(['M', 'F'])
        diagnosis = row['dx'] if 'dx' in row and pd.notna(row['dx']) else 'Critical illness'
        asa = int(row['asa']) if pd.notna(row['asa']) else 3
        icu_days = int(row['icu_days']) if pd.notna(row['icu_days']) else 1
        emop = int(row['emop']) if pd.notna(row['emop']) else 0
        
        # Create patient
        patient = Patient(
            patient_id=patient_id,
            full_name=f"Patient {caseid}",
            date_of_birth=datetime.now().date() - timedelta(days=age * 365),
            gender=gender,
            blood_type=random.choice(blood_types),
            device_id=f"MON-{caseid:04d}",
            chronic_conditions=diagnosis,
            active_monitoring=True  # ✅ Important: Enable monitoring
        )
        db.add(patient)
        
        # Calculate risk score
        risk_score = (asa * 15) + (icu_days * 5) + (emop * 10)
        
        # Determine risk level
        if risk_score >= 70 or asa >= 5:
            risk_level = 'CRITICAL'
        elif risk_score >= 50 or asa >= 4:
            risk_level = 'HIGH'
        else:
            risk_level = 'MODERATE'
        
        # Create admission
        admission = Admission(
            patient_id=patient_id,
            admission_time=datetime.now() - timedelta(days=icu_days),
            admission_type='Emergency' if emop == 1 else 'Elective',
            department=random.choice(departments),
            initial_diagnosis=diagnosis,
            attending_physician=random.choice(physicians),
            risk_level=risk_level,
            current_risk_score=float(risk_score),
            discharge_time=None,  # ✅ Active admission
            status='ACTIVE'
        )
        db.add(admission)
        
        risk_icon = '🔴' if risk_level == 'CRITICAL' else '🟠'
        print(f"{risk_icon} {patient_id} | {gender}/{age}y | {risk_level} (Score: {risk_score:.0f})")
        print(f"   ASA: {asa} | ICU: {icu_days} days | {diagnosis}")
        
        added_count += 1
    
    try:
        db.commit()
        
        print("\n" + "="*80)
        print("✅ HIGH-RISK PATIENTS ADDED SUCCESSFULLY")
        print("="*80)
        print(f"\n📊 Added {added_count} new high-risk patients")
        
        # Show current distribution
        critical = db.query(Admission).filter(
            Admission.discharge_time.is_(None),
            Admission.risk_level == 'CRITICAL'
        ).count()
        
        high = db.query(Admission).filter(
            Admission.discharge_time.is_(None),
            Admission.risk_level == 'HIGH'
        ).count()
        
        moderate = db.query(Admission).filter(
            Admission.discharge_time.is_(None),
            Admission.risk_level == 'MODERATE'
        ).count()
        
        total_active = critical + high + moderate
        
        print(f"\n🚨 Current Active Patients in System:")
        print(f"   🔴 CRITICAL: {critical} patients")
        print(f"   🟠 HIGH:     {high} patients")
        print(f"   🟡 MODERATE: {moderate} patients")
        print(f"   ────────────────────────")
        print(f"   📊 TOTAL:    {total_active} patients")
        
        print("\n" + "="*80)
        print("🚀 NEXT STEPS")
        print("="*80)
        print("\n1. Start/Restart Producer (will include new patients):")
        print("   pkill -f run_producer.py")
        print("   python scripts/run_producer.py &")
        
        print("\n2. Consumer will automatically process alerts")
        print("   (If not running: python scripts/run_consumer.py &)")
        
        print("\n3. Start Alert Server (if not running):")
        print("   python scripts/run_alert_server.py &")
        
        print("\n4. View on Dashboard:")
        print("   streamlit run src/dashboard/streamlit_app.py")
        
        print("\n5. Test alerts:")
        print("   firefox test_alert_sound.html")
        
        print("\n" + "="*80)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    load_high_risk_from_csv()