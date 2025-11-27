#!/usr/bin/env python3
# filepath: /home/hdoop/UET/BigData/ICU/scripts/run_producer.py
"""
Producer: Load active patients from DB, auto-refresh, stream to Kafka
"""
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

<<<<<<< HEAD
from sqlalchemy import select
=======
from sqlalchemy import select, text
>>>>>>> 5518597 (Initial commit: reset and push to master)
from src.database.session import SessionLocal
from src.database.models import Patient
from src.data_generation.patient_simulator import PatientSimulator  
from src.kafka_producer.producer import VitalSignsProducer
from config.config import settings

class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"

def load_active_patients():
<<<<<<< HEAD
    """Load active patients from DB"""
    with SessionLocal() as db:
        rows = db.execute(
            select(Patient).where(Patient.active_monitoring.is_(True))
        ).scalars().all()
        
        patients = []
        for r in rows:
            patients.append({
                "patient_id": r.patient_id,
                "profile": "HEALTHY",
                "device_id": r.device_id or f"DEV-{r.patient_id}",
            })
        return patients
=======
    """Load active patients from DB, tolerant to missing columns."""
    with SessionLocal() as db:
        try:
            # Try minimal raw SQL to avoid schema mismatch (e.g., missing date_of_birth)
            q = text("""
                SELECT p.patient_id,
                       COALESCE(p.device_id, '') AS device_id,
                       COALESCE(a.risk_level, 'STABLE') AS risk_level
                FROM patients p
                JOIN admissions a ON a.patient_id = p.patient_id
                WHERE p.active_monitoring IS TRUE
                  AND a.discharge_time IS NULL
            """)
            rows = db.execute(q).fetchall()
            patients = []
            risk_to_profile = {
                'CRITICAL': 'CRITICAL',
                'HIGH': 'CRITICAL',
                'MODERATE': 'AT_RISK',
                'STABLE': 'HEALTHY',
                None: 'HEALTHY'
            }
            for patient_id, device_id, risk_level in rows:
                pid = str(patient_id)
                dev = device_id or f"DEV-{pid}"
                prof = risk_to_profile.get(risk_level, 'HEALTHY')
                patients.append({
                    "patient_id": pid,
                    "profile": prof,
                    "device_id": dev,
                })
            return patients
        except Exception:
            # Fallback to ORM if the above fails for any reason
            rows = db.execute(
                select(Patient).where(Patient.active_monitoring.is_(True))
            ).scalars().all()
            patients = []
            for r in rows:
                patients.append({
                    "patient_id": r.patient_id,
                    "profile": "HEALTHY",
                    "device_id": r.device_id or f"DEV-{r.patient_id}",
                })
            return patients
>>>>>>> 5518597 (Initial commit: reset and push to master)

class VisualProducer:
    """Producer with real-time dashboard"""
    
    def __init__(self, refresh_sec: float = 10.0, interval: float = 1.0):
        self.refresh_sec = refresh_sec
        self.interval = interval
        self.sim = PatientSimulator()
        self.stats = {"sent": 0, "failed": 0, "batches": 0, "start": None}
        self.patient_stats = defaultdict(lambda: {
            "count": 0,
            "profile": "UNKNOWN",
            "last": {},
        })
        self.last_refresh = 0
    
    def refresh_patients(self):
        """Load active patients from DB"""
        patients = load_active_patients()
        self.sim.upsert_patients(patients)
    
    def clear(self):
        os.system("clear" if os.name == "posix" else "cls")
    
    def dashboard(self):
        """Display dashboard"""
        self.clear()
        print(
            f"{Colors.BOLD}{Colors.CYAN}"
            f"{'='*100}\n"
            f"🏥 ICU PRODUCER (DB-DRIVEN STREAMING)\n"
            f"{'='*100}{Colors.END}"
        )
        
        print(
            f"\n{Colors.BOLD}Configuration:{Colors.END}\n"
            f"  Kafka: {settings.KAFKA_BOOTSTRAP_SERVERS}\n"
            f"  Topic: {settings.KAFKA_TOPIC_VITAL_SIGNS}\n"
            f"  Refresh: {self.refresh_sec}s | Interval: {self.interval}s"
        )
        
        uptime = time.time() - self.stats["start"] if self.stats["start"] else 0
        rate = self.stats["sent"] / uptime if uptime > 0 else 0
        
        print(
            f"\n{Colors.BOLD}Statistics:{Colors.END}\n"
            f"  Uptime: {int(uptime)}s\n"
            f"  Active Patients: {len(self.sim.generators)}\n"
            f"  Batches: {self.stats['batches']}\n"
            f"  Messages Sent: {self.stats['sent']}\n"
            f"  Failed: {self.stats['failed']}\n"
            f"  Rate: {rate:.1f} msg/sec"
        )
        
        print(f"\n{Colors.BOLD}Patient Vital Signs:{Colors.END}")
        print(f"{'Patient ID':<15} {'Profile':<12} {'HR':<6} {'SpO2':<6} {'Temp':<7} {'RR':<5} {'Readings':<8}")
        print("-" * 70)
        
        shown = 0
        for pid in sorted(self.patient_stats.keys())[:15]:
            st = self.patient_stats[pid]
            vit = st["last"]
            hr = vit.get("heart_rate", "-")
            spo2 = vit.get("spo2", "-")
            temp = vit.get("temperature", "-")
            rr = vit.get("respiratory_rate", "-")
            
            print(
                f"{pid:<15} {st['profile']:<12} {hr:<6} {spo2:<6} {temp:<7} {rr:<5} {st['count']:<8}"
            )
            shown += 1
        
        if shown == 0:
            print(f"{Colors.YELLOW}No active patients. Add with: scripts/patients.py add ...{Colors.END}")
        
        print(f"\n{Colors.CYAN}Press Ctrl+C to stop{Colors.END}\n")
    
    def run(self):
        """Main producer loop"""
        prod = VitalSignsProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            topic=settings.KAFKA_TOPIC_VITAL_SIGNS,
        )
        
        self.stats["start"] = time.time()
        
        # Initial load
        print("Loading patients from database...")
        self.refresh_patients()
        self.dashboard()
        
        try:
            while True:
                now = time.time()
                if now - self.last_refresh >= self.refresh_sec:
                    self.refresh_patients()
                    self.last_refresh = now
                
                batch = self.sim.generate_batch()
                
                for reading in batch:
                    pid = reading["patient_id"]
                    self.patient_stats[pid]["count"] += 1
                    self.patient_stats[pid]["profile"] = reading.get("profile", "UNKNOWN")
                    self.patient_stats[pid]["last"] = reading["vital_signs"]
                    
                    if prod.send_reading(reading):
                        self.stats["sent"] += 1
                    else:
                        self.stats["failed"] += 1
                
                self.stats["batches"] += 1
                self.dashboard()
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Stopping producer...{Colors.END}")
        
        finally:
            prod.close()
            print(f"{Colors.GREEN}✅ Producer stopped{Colors.END}\n")

def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="ICU Producer")
    ap.add_argument("--refresh-sec", type=float, default=10.0, help="DB refresh interval")
    ap.add_argument("--interval", type=float, default=1.0, help="Stream interval")
    args = ap.parse_args()
    
    VisualProducer(refresh_sec=args.refresh_sec, interval=args.interval).run()

if __name__ == "__main__":
    main()