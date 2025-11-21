"""
Vital Signs Generator with Dynamic Profile Transitions
"""
import random
from enum import Enum
from typing import Dict, Optional
from datetime import datetime, timezone
import numpy as np

class PatientProfile(Enum):
    """Health profile types"""
    HEALTHY = "HEALTHY"
    AT_RISK = "AT_RISK"
    CRITICAL = "CRITICAL"

# Transition probabilities
TRANSITION_MATRIX = {
    "HEALTHY": {"HEALTHY": 0.985, "AT_RISK": 0.015, "CRITICAL": 0.0},
    "AT_RISK": {"HEALTHY": 0.06, "AT_RISK": 0.88, "CRITICAL": 0.06},
    "CRITICAL": {"HEALTHY": 0.0, "AT_RISK": 0.12, "CRITICAL": 0.88},
}

# Vital ranges per profile
VITAL_RANGES = {
    "HEALTHY": {
        "heart_rate": (60, 80),
        "spo2": (96, 100),
        "temperature": (36.4, 37.1),
        "respiratory_rate": (12, 18),
        "systolic_bp": (105, 125),
        "diastolic_bp": (65, 80),
    },
    "AT_RISK": {
        "heart_rate": (80, 105),
        "spo2": (92, 96),
        "temperature": (36.8, 38.0),
        "respiratory_rate": (18, 26),
        "systolic_bp": (120, 145),
        "diastolic_bp": (80, 95),
    },
    "CRITICAL": {
        "heart_rate": (105, 135),
        "spo2": (85, 93),
        "temperature": (37.8, 39.7),
        "respiratory_rate": (26, 36),
        "systolic_bp": (85, 105),
        "diastolic_bp": (50, 70),
    },
}

class VitalSignsGenerator:
    """Generates realistic vital signs with state transitions"""
    
    def __init__(
        self,
        patient_id: str,
        profile: PatientProfile = PatientProfile.HEALTHY,
        device_id: Optional[str] = None,
        enable_transitions: bool = True,
    ):
        self.patient_id = patient_id
        self.profile = profile
        self.initial_profile = profile
        self.device_id = device_id or f"DEV-{patient_id}"
        self.enable_transitions = enable_transitions
        self.readings_count = 0
        
        # Initialize with baseline values
        self._update_baseline()
        self.current = self.baseline.copy()
    
    def _update_baseline(self):
        """Update baseline vitals for current profile"""
        rng = VITAL_RANGES[self.profile.value]
        self.baseline = {
            k: np.mean(v) for k, v in rng.items()
        }
    
    def _maybe_transition(self) -> bool:
        """Check if profile should change"""
        if not self.enable_transitions:
            return False
        
        # Transition check every ~12 readings
        if self.readings_count % random.randint(10, 14) != 0:
            return False
        
        # Weighted random pick
        mat = TRANSITION_MATRIX[self.profile.value]
        profiles = list(mat.keys())
        probs = list(mat.values())
        
        new_prof = np.random.choice(profiles, p=probs)
        if new_prof != self.profile.value:
            self.profile = PatientProfile[new_prof]
            self._update_baseline()
            return True
        
        return False
    
    def generate_reading(self) -> Dict:
        """Generate a single vital signs reading"""
        self.readings_count += 1
        changed = self._maybe_transition()
        
        rng = VITAL_RANGES[self.profile.value]
        vitals = {}
        
        for vital, (mn, mx) in rng.items():
            # Smooth transition toward new baseline
            target = random.uniform(mn, mx)
            self.current[vital] = 0.7 * self.current[vital] + 0.3 * target
            # Add noise
            noise = np.random.normal(0, (mx - mn) * 0.03)
            value = np.clip(self.current[vital] + noise, mn, mx)
            vitals[vital] = round(value, 2)
        
        return {
            "patient_id": self.patient_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "profile": self.profile.value,
            "vital_signs": {
                "heart_rate": vitals["heart_rate"],
                "spo2": vitals["spo2"],
                "temperature": vitals["temperature"],
                "respiratory_rate": vitals["respiratory_rate"],
                "blood_pressure": {
                    "systolic": vitals["systolic_bp"],
                    "diastolic": vitals["diastolic_bp"],
                },
            },
            "metadata": {
                "device_id": self.device_id,
                "has_anomaly": False,
                "data_quality": random.choice(["good", "good", "fair"]),
                "profile_changed": changed,
                "readings_count": self.readings_count,
            },
        }