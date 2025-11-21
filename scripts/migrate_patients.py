#!/usr/bin/env python3
# filepath: /home/hdoop/UET/BigData/ICU/scripts/migrate_patients.py
"""
Initialize patient/admission tables
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.models import Base
from src.database.session import engine

def main():
    print("🔄 Creating patient/admission tables...")
    Base.metadata.create_all(engine)
    print("✅ Schema migrated successfully")

if __name__ == "__main__":
    main()