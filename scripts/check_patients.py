#!/usr/bin/env python3
# filepath: scripts/check_patients.py
"""
Check if patients exist in database
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from config.config import settings

def main():
    print("=" * 80)
    print("🔍 CHECKING PATIENT DATA")
    print("=" * 80)
    
    try:
        # Connect to PostgreSQL
        engine = create_engine(settings.get_postgres_url())
        
        with engine.connect() as conn:
            # Check patients table
            result = conn.execute(text("SELECT COUNT(*) FROM patients"))
            patient_count = result.scalar()
            
            print(f"\n📊 Database: {settings.POSTGRES_DB}")
            print(f"👥 Total patients: {patient_count}")
            
            if patient_count == 0:
                print("\n❌ No patients found!")
                print("\n💡 You need to add patients first:")
                print("   Option 1 (Recommended): Load from VitalDB data")
                print("     python scripts/load_icu_patients.py --limit 50")
                print("\n   Option 2: Add patients with admission data")
                print("     python scripts/add_patients_with_admission.py")
                print("\n   Option 3: Bulk add patients")
                print("     python scripts/bulk_add_patients.py")
                return False
            
            # Show sample patients
            result = conn.execute(text("""
                SELECT patient_id, gender, age, admission_date 
                FROM patients 
                LIMIT 5
            """))
            
            print("\n📋 Sample patients:")
            print("-" * 80)
            for row in result:
                print(f"   {row.patient_id} | {row.gender} | Age: {row.age} | "
                      f"Admitted: {row.admission_date}")
            
            print("\n✅ Patients ready for simulation!")
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)