"""
Add active_monitoring column to patients table
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.database.models import engine


def migrate():
    """Add active_monitoring and status columns"""
    
    print("=" * 80)
    print("🔄 ADDING MONITORING COLUMNS")
    print("=" * 80)
    
    try:
        with engine.connect() as conn:
            # Add active_monitoring to patients
            print("\n📦 Adding 'active_monitoring' to patients table...")
            try:
                conn.execute(text("""
                    ALTER TABLE patients 
                    ADD COLUMN active_monitoring BOOLEAN DEFAULT TRUE NOT NULL
                """))
                conn.commit()
                print("✅ Added active_monitoring column")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⚠️  active_monitoring column already exists")
                else:
                    raise
            
            # Add status to admissions
            print("\n📦 Adding 'status' to admissions table...")
            try:
                conn.execute(text("""
                    ALTER TABLE admissions 
                    ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE'
                """))
                conn.commit()
                print("✅ Added status column")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⚠️  status column already exists")
                else:
                    raise
            
            # Set all existing patients to active monitoring
            print("\n📊 Setting existing patients to active monitoring...")
            conn.execute(text("""
                UPDATE patients 
                SET active_monitoring = TRUE 
                WHERE active_monitoring IS NULL
            """))
            conn.commit()
            
            # Set all existing admissions to ACTIVE
            print("📊 Setting existing admissions to ACTIVE...")
            conn.execute(text("""
                UPDATE admissions 
                SET status = 'ACTIVE' 
                WHERE status IS NULL AND discharge_time IS NULL
            """))
            conn.commit()
            
            # Check results
            result = conn.execute(text("SELECT COUNT(*) FROM patients WHERE active_monitoring = TRUE"))
            active_count = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM patients"))
            total_count = result.scalar()
            
            print("\n" + "=" * 80)
            print("✅ MIGRATION COMPLETE")
            print("=" * 80)
            print(f"Active patients: {active_count}/{total_count}")
            print("=" * 80)
            
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    success = migrate()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())