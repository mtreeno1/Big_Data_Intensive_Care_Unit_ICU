#!/usr/bin/env python3
<<<<<<< HEAD
# filepath: /home/hdoop/UET/BigData/ICU/scripts/migrate_patients.py
"""
Initialize patient/admission tables
=======
"""
Migrate database schema: Create tables and add new columns
>>>>>>> 5518597 (Initial commit: reset and push to master)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

<<<<<<< HEAD
from src.database.models import Base
from src.database.session import engine

def main():
    print("🔄 Creating patient/admission tables...")
    Base.metadata.create_all(engine)
    print("✅ Schema migrated successfully")

if __name__ == "__main__":
    main()
=======
from sqlalchemy import create_engine, text, inspect
from src.database.models import Base
from config.config import settings

def migrate_database():
    """Create tables and add new columns"""
    engine = create_engine(settings.get_postgres_url())
    inspector = inspect(engine)
    
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    print("✅ Tables created/verified")
    
    # Check and add missing columns to admissions table
    with engine.connect() as conn:
        table_name = "admissions"
        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        # Add created_at if missing
        if 'created_at' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE admissions ADD COLUMN created_at TIMESTAMP DEFAULT NOW()"))
                conn.commit()
                print("✅ Added created_at column")
            except Exception as e:
                print(f"ℹ️  created_at: {e}")
        else:
            print("ℹ️  created_at column already exists")
        
        # Add updated_at if missing
        if 'updated_at' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE admissions ADD COLUMN updated_at TIMESTAMP"))
                conn.commit()
                print("✅ Added updated_at column")
            except Exception as e:
                print(f"ℹ️  updated_at: {e}")
        else:
            print("ℹ️  updated_at column already exists")
        
        # Add current_risk_score if missing
        if 'current_risk_score' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE admissions ADD COLUMN current_risk_score FLOAT"))
                conn.commit()
                print("✅ Added current_risk_score column")
            except Exception as e:
                print(f"ℹ️  current_risk_score: {e}")
        else:
            print("ℹ️  current_risk_score column already exists")
        
        # Add risk_level if missing
        if 'risk_level' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE admissions ADD COLUMN risk_level VARCHAR(20)"))
                conn.commit()
                print("✅ Added risk_level column")
            except Exception as e:
                print(f"ℹ️  risk_level: {e}")
        else:
            print("ℹ️  risk_level column already exists")
    
    print("🎉 Schema migration completed")

if __name__ == "__main__":
    migrate_database()
>>>>>>> 5518597 (Initial commit: reset and push to master)
