#!/usr/bin/env python3
# filepath: /home/hdoop/UET/BigData/ICU/scripts/patients.py
"""
CLI for patient management
"""
import argparse
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.database.session import SessionLocal
from src.database.models import Patient

def add_patient(args):
    """Add a new patient"""
    with SessionLocal() as db:
        if db.query(Patient).filter(Patient.patient_id == args.patient_id).first():
            print(f"❌ Patient {args.patient_id} already exists")
            return
        
        p = Patient(
            patient_id=args.patient_id,
            full_name=args.full_name,
            dob=date.fromisoformat(args.dob),
            gender=args.gender,
            device_id=args.device_id,
            active_monitoring=not args.inactive,
        )
        db.add(p)
        db.commit()
        print(f"✅ Added: {p.patient_id}")

def update_patient(args):
    """Update patient details"""
    with SessionLocal() as db:
        p = db.query(Patient).filter(Patient.patient_id == args.patient_id).first()
        if not p:
            print(f"❌ Patient {args.patient_id} not found")
            return
        
        if args.full_name:
            p.full_name = args.full_name
        if args.dob:
            p.dob = date.fromisoformat(args.dob)
        if args.gender:
            p.gender = args.gender
        if args.device_id is not None:
            p.device_id = args.device_id
        
        db.commit()
        print(f"✅ Updated: {p.patient_id}")

def delete_patient(args):
    """Delete patient"""
    with SessionLocal() as db:
        p = db.query(Patient).filter(Patient.patient_id == args.patient_id).first()
        if not p:
            print(f"❌ Patient {args.patient_id} not found")
            return
        
        db.delete(p)
        db.commit()
        print(f"✅ Deleted: {args.patient_id}")

def set_active(args, active: bool):
    """Activate/deactivate patient monitoring"""
    with SessionLocal() as db:
        p = db.query(Patient).filter(Patient.patient_id == args.patient_id).first()
        if not p:
            print(f"❌ Patient {args.patient_id} not found")
            return
        
        p.active_monitoring = active
        db.commit()
        status = "activated" if active else "deactivated"
        print(f"✅ {status.capitalize()}: {args.patient_id}")
def list_patients(args):
    """List all patients"""
    with SessionLocal() as db:
        q = db.query(Patient).order_by(Patient.patient_id)
        if args.active_only:
            q = q.filter(Patient.active_monitoring.is_(True))
        
        rows = q.all()
        if not rows:
            print("No patients found")
            return
        
        print(f"\n{'Patient ID':<15} {'Name':<30} {'DOB':<12} {'Gender':<7} {'Active':<8} {'Device':<15}")
        print("=" * 85)
        for r in rows:
            # ✅ Format DOB explicitly to avoid truncation issues
            dob_str = r.dob.strftime('%Y-%m-%d') if r.dob else '-'
            print(f"{r.patient_id:<15} {r.full_name:<30} {dob_str:<12} {r.gender or '-':<7} {str(r.active_monitoring):<8} {r.device_id or '-':<15}")
        print(f"\nTotal: {len(rows)}")
def main():
    ap = argparse.ArgumentParser(description="Patient Management CLI")
    sub = ap.add_subparsers(dest="cmd")

    # add
    sp = sub.add_parser("add", help="Add new patient")
    sp.add_argument("--patient-id", required=True, help="Unique patient ID")
    sp.add_argument("--full-name", required=True, help="Patient full name")
    sp.add_argument("--dob", required=True, help="Date of birth (YYYY-MM-DD)")
    sp.add_argument("--gender", default=None, help="M/F")
    sp.add_argument("--device-id", default=None, help="Monitor device ID")
    sp.add_argument("--inactive", action="store_true", help="Create inactive")
    sp.set_defaults(func=add_patient)

    # update
    sp = sub.add_parser("update", help="Update patient")
    sp.add_argument("--patient-id", required=True)
    sp.add_argument("--full-name")
    sp.add_argument("--dob")
    sp.add_argument("--gender")
    sp.add_argument("--device-id")
    sp.set_defaults(func=update_patient)

    # delete
    sp = sub.add_parser("delete", help="Delete patient")
    sp.add_argument("--patient-id", required=True)
    sp.set_defaults(func=delete_patient)

    # activate
    sp = sub.add_parser("activate", help="Activate monitoring")
    sp.add_argument("--patient-id", required=True)
    sp.set_defaults(func=lambda a: set_active(a, True))

    # deactivate
    sp = sub.add_parser("deactivate", help="Deactivate monitoring")
    sp.add_argument("--patient-id", required=True)
    sp.set_defaults(func=lambda a: set_active(a, False))

    # list
    sp = sub.add_parser("list", help="List patients")
    sp.add_argument("--active-only", action="store_true", help="Only active")
    sp.set_defaults(func=list_patients)

    args = ap.parse_args()
    if not getattr(args, "cmd", None):
        ap.print_help()
        return
    args.func(args)

if __name__ == "__main__":
    main()