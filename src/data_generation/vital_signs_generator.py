"""
Vital Signs Generator with Dynamic Profile Transitions
"""

import random
import numpy as np
from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime, timezone


class PatientProfile(Enum):
    """Health profile types for patients"""
    HEALTHY = "HEALTHY"
    AT_RISK = "AT_RISK"
    CRITICAL = "CRITICAL"


class ProfileTransition:
    """
    Manages profile transitions with probabilities
    """
    # Transition probabilities per reading
    TRANSITION_MATRIX = {
        'HEALTHY': {
            'HEALTHY': 0.98,      # 98% stay healthy
            'AT_RISK': 0.02,      # 2% deteriorate
            'CRITICAL': 0.0       # Can't jump to critical
        },
        'AT_RISK': {
            'HEALTHY': 0.05,      # 5% recover
            'AT_RISK': 0.90,      # 90% stay at risk
            'CRITICAL': 0.05      # 5% deteriorate
        },
        'CRITICAL': {
            'HEALTHY': 0.0,       # Can't jump to healthy
            'AT_RISK': 0.10,      # 10% improve
            'CRITICAL': 0.90      # 90% stay critical
        }
    }
    
    @staticmethod
    def get_next_profile(current_profile: str) -> str:
        """
        Determine next profile based on transition probabilities
        
        Args:
            current_profile: Current health profile
            
        Returns:
            Next profile (may be same)
        """
        probabilities = ProfileTransition.TRANSITION_MATRIX[current_profile]
        profiles = list(probabilities.keys())
        probs = list(probabilities.values())
        
        next_profile = np.random.choice(profiles, p=probs)
        return next_profile


class VitalSignsGenerator:
    """
    Generates realistic vital signs with dynamic profile transitions
    """
    
    # Normal ranges for vital signs
    VITAL_RANGES = {
        'HEALTHY': {
            'heart_rate': (60, 80),
            'spo2': (95, 100),
            'temperature': (36.5, 37.2),
            'respiratory_rate': (12, 18),
            'systolic_bp': (100, 120),
            'diastolic_bp': (60, 80),
        },
        'AT_RISK': {
            'heart_rate': (80, 100),
            'spo2': (92, 96),
            'temperature': (37.0, 37.8),
            'respiratory_rate': (18, 24),
            'systolic_bp': (120, 140),
            'diastolic_bp': (80, 90),
        },
        'CRITICAL': {
            'heart_rate': (100, 130),
            'spo2': (85, 94),
            'temperature': (37.8, 39.5),
            'respiratory_rate': (24, 35),
            'systolic_bp': (85, 100),
            'diastolic_bp': (50, 65),
        }
    }
    
    def __init__(
        self,
        patient_id: str,
        profile: PatientProfile = PatientProfile.HEALTHY,
        device_id: Optional[str] = None,
        enable_transitions: bool = True
    ):
        """
        Initialize vital signs generator with dynamic transitions
        
        Args:
            patient_id: Unique patient identifier
            profile: Initial health profile
            device_id: Medical device ID
            enable_transitions: Enable automatic profile transitions
        """
        self.patient_id = patient_id
        self.profile = profile
        self.initial_profile = profile
        self.device_id = device_id or f"MONITOR-{patient_id}"
        self.enable_transitions = enable_transitions
        
        # Transition tracking
        self.readings_count = 0
        self.transition_history: List[Dict] = []
        self.time_in_current_profile = 0
        
        # Get ranges for current profile
        self.ranges = self.VITAL_RANGES[profile.value]
        
        # Initialize baseline values
        self._update_baseline()
        
        # Current values (start at baseline)
        self.current = self.baseline.copy()
    
    def _update_baseline(self):
        """Update baseline based on current profile"""
        self.baseline = {
            'heart_rate': np.mean(self.ranges['heart_rate']),
            'spo2': np.mean(self.ranges['spo2']),
            'temperature': np.mean(self.ranges['temperature']),
            'respiratory_rate': np.mean(self.ranges['respiratory_rate']),
            'systolic_bp': np.mean(self.ranges['systolic_bp']),
            'diastolic_bp': np.mean(self.ranges['diastolic_bp']),
        }
    
    def _check_profile_transition(self) -> bool:
        """
        Check if profile should transition
        
        Returns:
            True if transition occurred
        """
        if not self.enable_transitions:
            return False
        
        # Check every 10-20 readings
        if self.readings_count % random.randint(10, 20) != 0:
            return False
        
        old_profile = self.profile.value
        new_profile_name = ProfileTransition.get_next_profile(old_profile)
        
        if new_profile_name != old_profile:
            # Transition occurred!
            self.profile = PatientProfile[new_profile_name]
            self.ranges = self.VITAL_RANGES[new_profile_name]
            self._update_baseline()
            
            # Log transition
            transition = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'from_profile': old_profile,
                'to_profile': new_profile_name,
                'reading_number': self.readings_count
            }
            self.transition_history.append(transition)
            
            # Reset time counter
            self.time_in_current_profile = 0
            
            return True
        
        return False
    
    def _smooth_transition_to_new_profile(self):
        """
        Smoothly transition vital signs to new profile's range
        """
        # Gradually adjust current values toward new baseline
        for vital in self.current.keys():
            target = self.baseline[vital]
            # Smooth transition over multiple readings
            self.current[vital] = self.current[vital] * 0.7 + target * 0.3
    
    def _add_noise(self, value: float, min_val: float, max_val: float, 
                   noise_factor: float = 0.05) -> float:
        """Add random noise to a value while keeping it within range"""
        range_width = max_val - min_val
        noise = np.random.normal(0, range_width * noise_factor)
        new_value = value + noise
        return np.clip(new_value, min_val, max_val)
    
    def _smooth_transition(self, current: float, target: float, alpha: float = 0.3) -> float:
        """Smooth transition between current and target value"""
        return current * (1 - alpha) + target * alpha
    
    def _inject_anomaly(self, vitals: Dict, anomaly_prob: float = 0.1) -> Dict:
        """Randomly inject anomalies into vital signs"""
        if random.random() > anomaly_prob:
            return vitals
        
        vital_to_modify = random.choice([
            'heart_rate', 'spo2', 'temperature', 'respiratory_rate'
        ])
        
        if vital_to_modify == 'heart_rate':
            vitals[vital_to_modify] = random.choice([
                random.uniform(40, 50),
                random.uniform(120, 150)
            ])
        elif vital_to_modify == 'spo2':
            vitals[vital_to_modify] = random.uniform(80, 90)
        elif vital_to_modify == 'temperature':
            vitals[vital_to_modify] = random.choice([
                random.uniform(35.0, 35.8),
                random.uniform(38.5, 40.0)
            ])
        elif vital_to_modify == 'respiratory_rate':
            vitals[vital_to_modify] = random.choice([
                random.uniform(6, 10),
                random.uniform(30, 40)
            ])
        
        return vitals
    
    def generate_reading(self, inject_anomaly: bool = True) -> Dict:
        """
        Generate a single vital signs reading with possible profile transition
        
        Args:
            inject_anomaly: Whether to randomly inject anomalies
        
        Returns:
            Dictionary with patient vitals and metadata
        """
        self.readings_count += 1
        self.time_in_current_profile += 1
        
        # Check for profile transition
        profile_changed = self._check_profile_transition()
        
        if profile_changed:
            self._smooth_transition_to_new_profile()
        
        # Update current values with noise
        for vital in ['heart_rate', 'spo2', 'temperature', 'respiratory_rate', 
                      'systolic_bp', 'diastolic_bp']:
            min_val, max_val = self.ranges[vital]
            
            # Smooth transition to new target
            target = random.uniform(min_val, max_val)
            self.current[vital] = self._smooth_transition(
                self.current[vital], 
                target, 
                alpha=0.2
            )
            
            # Add noise
            self.current[vital] = self._add_noise(
                self.current[vital],
                min_val,
                max_val,
                noise_factor=0.03
            )
        
        # Create vital signs dict
        vitals = {
            'heart_rate': round(self.current['heart_rate'], 1),
            'spo2': round(self.current['spo2'], 1),
            'temperature': round(self.current['temperature'], 2),
            'respiratory_rate': round(self.current['respiratory_rate'], 1),
            'blood_pressure': {
                'systolic': round(self.current['systolic_bp'], 1),
                'diastolic': round(self.current['diastolic_bp'], 1)
            }
        }
        
        # Inject anomaly sometimes
        has_anomaly = False
        if inject_anomaly and random.random() < 0.1:
            vitals = self._inject_anomaly(vitals)
            has_anomaly = True
        
        # Create full reading
        reading = {
            'patient_id': self.patient_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'profile': self.profile.value,
            'vital_signs': vitals,
            'metadata': {
                'device_id': self.device_id,
                'has_anomaly': has_anomaly,
                'data_quality': random.choice(['good', 'good', 'good', 'fair']),
                'profile_changed': profile_changed,
                'readings_count': self.readings_count,
                'time_in_profile': self.time_in_current_profile,
                'initial_profile': self.initial_profile.value
            }
        }
        
        return reading
    
    def get_transition_history(self) -> List[Dict]:
        """Get history of profile transitions"""
        return self.transition_history
    
    def force_transition(self, new_profile: str):
        """
        Force transition to a specific profile
        
        
        Args:
            new_profile: Target profile name (HEALTHY, AT_RISK, CRITICAL)
        """
        old_profile = self.profile.value
        self.profile = PatientProfile[new_profile]
        self.ranges = self.VITAL_RANGES[new_profile]
        self._update_baseline()
        
        transition = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'from_profile': old_profile,
            'to_profile': new_profile,
            'reading_number': self.readings_count,
            'forced': True
        }
        self.transition_history.append(transition)
        self.time_in_current_profile = 0
    
    def get_current_vitals(self) -> Dict:
        """Get current vital signs values"""
        return self.current.copy()
    
    def reset_to_baseline(self):
        """Reset current values to baseline"""
        self.current = self.baseline.copy()


# Example usage
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    import time
    
    print("=" * 80)
    print("DYNAMIC PATIENT STATE TRANSITIONS TEST")
    print("=" * 80)
    
    # Create patient that starts HEALTHY
    generator = VitalSignsGenerator(
        patient_id="PT-DYNAMIC-001",
        profile=PatientProfile.HEALTHY,
        enable_transitions=True
    )
    
    print(f"\n🏥 Starting Profile: {generator.profile.value}")
    print("📊 Generating 50 readings (profile may change)...\n")
    
    for i in range(50):
        reading = generator.generate_reading()
        
        # Show when profile changes
        if reading['metadata']['profile_changed']:
            print(f"\n🔄 PROFILE CHANGE at reading {i+1}!")
            print(f"   New profile: {reading['profile']}")
            print(f"   Transitions so far: {len(generator.transition_history)}\n")
        
        # Show every 10th reading
        if (i + 1) % 10 == 0:
            vitals = reading['vital_signs']
            print(f"Reading {i+1:3d} | Profile: {reading['profile']:8s} | "
                  f"HR: {vitals['heart_rate']:5.1f} | SpO2: {vitals['spo2']:5.1f}% | "
                  f"Temp: {vitals['temperature']:5.2f}°C")
    
    # Show transition summary
    print(f"\n{'='*80}")
    print("📈 TRANSITION SUMMARY")
    print(f"{'='*80}")
    print(f"Total readings: 50")
    print(f"Total transitions: {len(generator.transition_history)}")
    print(f"Final profile: {generator.profile.value}")
    print(f"\nTransition history:")
    for t in generator.transition_history:
        print(f"  • Reading {t['reading_number']}: {t['from_profile']} → {t['to_profile']}")