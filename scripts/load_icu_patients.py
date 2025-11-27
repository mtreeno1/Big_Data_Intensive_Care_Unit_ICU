# scripts/load_icu_patients.py
"""
Load filtered ICU patients from icu_like_cases.csv into PostgreSQL database
"""
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_manager import DatabaseManager
from src.database.models import Patient, Admission
from config.config import settings

def generate_patient_data(row, idx):
    """Generate patient data from VitalDB row"""
    caseid = int(row['caseid'])
    patient_id = f"ICU-{caseid:06d}"
    
    # Patient basic info
    patient_data = {
        'patient_id': patient_id,
        'full_name': f"Patient {caseid}",
        'date_of_birth': datetime.now().date() - timedelta(days=int(row['age']) * 365) if pd.notna(row['age']) else None,
        'gender': str(row['sex']).upper() if pd.notna(row['sex']) and str(row['sex']).upper() in ['M', 'F'] else 'M',
        'blood_type': random.choice(['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-', 'AB-']),
        'device_id': f"MON-{caseid:04d}",
        'chronic_conditions': row['dx'] if pd.notna(row['dx']) else 'Unknown',
        'active_monitoring': True  # ✅ THÊM DÒNG NÀY
    }
    
    # Admission data
    admission_data = {
        'patient_id': patient_id,
        'admission_time': datetime.now() - timedelta(days=int(row.get('icu_days', 1))),
        'admission_type': 'Emergency' if row.get('emop', 0) == 1 else 'Elective',
        'department': row['department'] if pd.notna(row.get('department')) else 'ICU',
        'initial_diagnosis': row['dx'] if pd.notna(row.get('dx')) else 'Unknown',
        'attending_physician': f"Dr. {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'])}",
        'discharge_time': None,  # ✅ THÊM DÒNG NÀY - Chưa discharge
        'status': 'ACTIVE'       # ✅ THÊM DÒNG NÀY
    }
    
    # Calculate risk level based on ASA and other factors
    asa = row.get('asa', 2)
    age = row.get('age', 50)
    icu_days = row.get('icu_days', 0)
    death = row.get('death_inhosp', 0)
    
    risk_score = (asa * 5) + (age / 20) + (icu_days * 2) + (death * 20)
    
    if risk_score > 30 or death == 1:
        risk_level = 'CRITICAL'
    elif risk_score > 20:
        risk_level = 'HIGH'
    elif risk_score > 10:
        risk_level = 'MODERATE'
    else:
        risk_level = 'STABLE'
    
    admission_data['risk_level'] = risk_level
    admission_data['current_risk_score'] = risk_score
    
    return patient_data, admission_data

def load_icu_patients(csv_file='data/icu_like_cases.csv', limit=None):
    """Load ICU patients from CSV to database"""
    print("🔄 Loading ICU patients from VitalDB data...")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_file)
        print(f"📊 Found {len(df)} ICU cases in file")
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file}")
        print("💡 Run filter_icu_cases.py first to create this file")
        return
    
    # Limit if specified
    if limit:
        df = df.head(limit)
        print(f"📊 Limited to {limit} patients")
    
    # Initialize database
    db = DatabaseManager()
    
    added_patients = 0
    added_admissions = 0
    errors = 0
    
    print("\n" + "="*60)
    print("Adding patients to database...")
    print("="*60)
    
    for idx, row in df.iterrows():
        try:
            # Generate data
            patient_data, admission_data = generate_patient_data(row, idx)
            
            # Add patient
            patient = db.add_patient(patient_data)
            if patient:
                added_patients += 1
                
                # Add admission
                admission = db.add_admission(admission_data)
                if admission:
                    added_admissions += 1
                
                # Progress indicator
                if (idx + 1) % 50 == 0:
                    print(f"✅ Processed {idx + 1}/{len(df)} patients")
            
        except Exception as e:
            errors += 1
            print(f"❌ Error processing case {row['caseid']}: {e}")
            continue
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"✅ Patients added: {added_patients}")
    print(f"✅ Admissions created: {added_admissions}")
    print(f"❌ Errors: {errors}")
    print(f"📈 Success rate: {(added_patients/len(df)*100):.1f}%")
    print("="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load ICU patients into database')
    parser.add_argument('--file', type=str, default='data/icu_like_cases.csv',
                        help='CSV file with ICU cases')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of patients to load')
    
    args = parser.parse_args()
    
    load_icu_patients(args.file, args.limit)