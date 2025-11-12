"""
Patient Simulator: Manages multiple patients and generates vital signs
"""
import logging
from typing import Dict, List
from datetime import datetime

from .vital_signs_generator import VitalSignsGenerator, PatientProfile  # ✅ Added PatientProfile

logger = logging.getLogger(__name__)

class PatientSimulator:
    """Manages simulation for multiple patients"""
    
    def __init__(self):
        self.generators: Dict[str, VitalSignsGenerator] = {}
        self.patient_profiles: Dict[str, str] = {}
    
    def upsert_patients(self, patients: List[Dict]):
        """
        Update active patients list.
        Remove generators for patients not in list.
        Add/update generators for patients in list.
        """
        active_patient_ids = {p["patient_id"] for p in patients}
        
        # Remove inactive patients
        to_remove = [pid for pid in self.generators if pid not in active_patient_ids]
        for pid in to_remove:
            del self.generators[pid]
            del self.patient_profiles[pid]
            logger.info(f"🗑️ Removed patient {pid}")
        
        # Add/update active patients
        for patient in patients:
            pid = patient["patient_id"]
            device_id = patient.get("device_id", f"DEV-{pid}")
            
            if pid not in self.generators:
                # New patient
                self.generators[pid] = VitalSignsGenerator(
                    patient_id=pid,
                    device_id=device_id,
                    profile=PatientProfile.HEALTHY  
                )
                self.patient_profiles[pid] = "HEALTHY"
                logger.info(f"➕ Added patient {pid} ({device_id})")
            else:
                # Update device_id if changed
                self.generators[pid].device_id = device_id
    
    def generate_batch(self) -> List[Dict]:
        """Generate one reading for each active patient"""
        readings = []
        for pid, generator in self.generators.items():
            try:
                reading = generator.generate_reading()
                readings.append(reading)
            except Exception as e:
                logger.error(f"Failed to generate for {pid}: {e}")
        
        return readings
    
    def get_stats(self) -> Dict:
        """Get current stats"""
        return {
            "active_patients": len(self.generators),
            "patient_profiles": self.patient_profiles.copy(),
        }