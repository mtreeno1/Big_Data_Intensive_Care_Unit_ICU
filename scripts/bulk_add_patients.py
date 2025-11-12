#!/usr/bin/env python3
"""
Bulk add patients from CSV file
"""
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.exc import IntegrityError
from src.database.session import SessionLocal
from src.database.models import Patient

def bulk_add_patients(csv_file: str):
    """Add patients from CSV file"""
    patients_added = 0
    errors = []
    
    with SessionLocal() as db:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse date
                    dob = datetime.strptime(row['dob'], '%Y-%m-%d').date()
                    
                    # Create patient
                    patient = Patient(
                        patient_id=row['patient_id'],
                        full_name=row['full_name'],
                        dob=dob,
                        gender=row['gender'],
                        device_id=row.get('device_id', f"DEV-{row['patient_id']}"),
                        active_monitoring=True  # Default to active
                    )
                    
                    db.add(patient)
                    patients_added += 1
                    print(f"✅ Added {row['patient_id']}: {row['full_name']}")
                    
                except IntegrityError:
                    errors.append(f"❌ Duplicate patient_id: {row['patient_id']}")
                    db.rollback()
                except Exception as e:
                    errors.append(f"❌ Error with {row.get('patient_id', 'unknown')}: {e}")
                    db.rollback()
            
            # Commit all
            try:
                db.commit()
                print(f"\n🎉 Successfully added {patients_added} patients")
            except Exception as e:
                print(f"❌ Commit failed: {e}")
                db.rollback()
    
    # Show errors
    if errors:
        print(f"\n⚠️ {len(errors)} errors:")
        for error in errors:
            print(f"   {error}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/bulk_add_patients.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    bulk_add_patients(csv_file)