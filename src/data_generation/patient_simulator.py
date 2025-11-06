"""
Patient Vital Signs Simulator
Generates realistic patient vital signs with temporal patterns and anomalies
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class PatientProfile:
    """Define patient health profiles"""
    
    HEALTHY = {
        'heart_rate': {'mean': 75, 'std': 10, 'min': 60, 'max': 100},
        'spo2': {'mean': 98, 'std': 1, 'min': 95, 'max': 100},
        'systolic_bp': {'mean': 120, 'std': 10, 'min': 90, 'max': 140},
        'diastolic_bp': {'mean': 80, 'std': 8, 'min': 60, 'max': 90},
        'temperature': {'mean': 37.0, 'std': 0.3, 'min': 36.1, 'max': 37.5},
        'respiratory_rate': {'mean': 16, 'std': 2, 'min': 12, 'max': 20},
        'anomaly_probability': 0.02  # 2% chance of anomaly
    }
    
    AT_RISK = {
        'heart_rate': {'mean': 85, 'std': 15, 'min': 55, 'max': 110},
        'spo2': {'mean': 96, 'std': 2, 'min': 92, 'max': 99},
        'systolic_bp': {'mean': 135, 'std': 15, 'min': 100, 'max': 160},
        'diastolic_bp': {'mean': 88, 'std': 10, 'min': 65, 'max': 100},
        'temperature': {'mean': 37.2, 'std': 0.4, 'min': 36.0, 'max': 38.0},
        'respiratory_rate': {'mean': 18, 'std': 3, 'min': 10, 'max': 24},
        'anomaly_probability': 0.08  # 8% chance of anomaly
    }
    
    CRITICAL = {
        'heart_rate': {'mean': 105, 'std': 20, 'min': 45, 'max': 140},
        'spo2': {'mean': 93, 'std': 3, 'min': 85, 'max': 97},
        'systolic_bp': {'mean': 150, 'std': 20, 'min': 80, 'max': 180},
        'diastolic_bp': {'mean': 95, 'std': 12, 'min': 55, 'max': 110},
        'temperature': {'mean': 37.8, 'std': 0.6, 'min': 35.5, 'max': 39.5},
        'respiratory_rate': {'mean': 22, 'std': 4, 'min': 8, 'max': 30},
        'anomaly_probability': 0.15  # 15% chance of anomaly
    }


class VitalSignsGenerator:
    """Generate realistic vital signs with temporal patterns"""
    
    def __init__(self, patient_id: str, profile: str = 'HEALTHY', seed: Optional[int] = None):
        """
        Initialize the generator
        
        Args:
            patient_id: Unique patient identifier
            profile: Patient health profile (HEALTHY, AT_RISK, CRITICAL)
            seed: Random seed for reproducibility
        """
        self.patient_id = patient_id
        self.profile_name = profile
        self.profile = getattr(PatientProfile, profile)
        self.time_offset = 0  # Simulates time progression
        
        if seed:
            random.seed(seed)
            np.random.seed(seed)
        
        # Initialize baseline values
        self.baseline = self._initialize_baseline()
        
        # For adding temporal correlation
        self.previous_values = self.baseline.copy()
    
    def _initialize_baseline(self) -> Dict[str, float]:
        """Initialize baseline vital signs for this patient"""
        baseline = {}
        for vital, params in self.profile.items():
            if vital == 'anomaly_probability':
                continue
            baseline[vital] = params['mean']
        return baseline
    
    def _add_circadian_rhythm(self, base_value: float, vital_name: str) -> float:
        """
        Add circadian rhythm patterns (24-hour cycle)
        Vital signs vary throughout the day
        """
        # Convert time offset to hours (assuming each call = 1 second)
        hours = (self.time_offset / 3600.0) % 24
        
        # Different patterns for different vitals
        if vital_name in ['heart_rate', 'systolic_bp', 'diastolic_bp']:
            # Lower at night (2-6 AM), higher during day
            variation = 0.1 * np.sin(2 * np.pi * (hours - 6) / 24)
            return base_value * (1 + variation)
        
        elif vital_name == 'temperature':
            # Lower in early morning, higher in evening
            variation = 0.02 * np.sin(2 * np.pi * (hours - 4) / 24)
            return base_value + variation
        
        elif vital_name == 'respiratory_rate':
            # Slightly lower during rest
            variation = 0.08 * np.sin(2 * np.pi * (hours - 6) / 24)
            return base_value * (1 + variation)
        
        return base_value
    
    def _add_temporal_correlation(self, current_value: float, vital_name: str) -> float:
        """
        Add temporal correlation - values don't jump randomly
        Current value influenced by previous value
        """
        # Correlation coefficient (0.7 = strong correlation with previous)
        alpha = 0.7
        previous = self.previous_values.get(vital_name, current_value)
        
        # Weighted average of current and previous
        correlated_value = alpha * previous + (1 - alpha) * current_value
        
        return correlated_value
    
    def _inject_anomaly(self, value: float, vital_name: str) -> tuple[float, bool]:
        """
        Randomly inject anomalies based on profile
        Returns: (value, is_anomaly)
        """
        if random.random() < self.profile['anomaly_probability']:
            # Create anomaly
            anomaly_type = random.choice(['high', 'low', 'spike'])
            
            if anomaly_type == 'high':
                # Push value towards max
                max_val = self.profile[vital_name]['max']
                value = value + random.uniform(0.3, 0.6) * (max_val - value)
            
            elif anomaly_type == 'low':
                # Push value towards min
                min_val = self.profile[vital_name]['min']
                value = value - random.uniform(0.3, 0.6) * (value - min_val)
            
            else:  # spike
                # Random spike in either direction
                value = value * random.uniform(1.15, 1.35) if random.random() > 0.5 else value * random.uniform(0.65, 0.85)
            
            return value, True
        
        return value, False
    
    def _generate_single_vital(self, vital_name: str) -> tuple[float, bool]:
        """Generate a single vital sign value"""
        params = self.profile[vital_name]
        
        # Step 1: Generate base value with normal distribution
        base_value = np.random.normal(params['mean'], params['std'])
        
        # Step 2: Add circadian rhythm
        base_value = self._add_circadian_rhythm(base_value, vital_name)
        
        # Step 3: Add temporal correlation
        base_value = self._add_temporal_correlation(base_value, vital_name)
        
        # Step 4: Possibly inject anomaly
        value, is_anomaly = self._inject_anomaly(base_value, vital_name)
        
        # Step 5: Clamp to valid range
        value = np.clip(value, params['min'], params['max'])
        
        # Store for next iteration
        self.previous_values[vital_name] = value
        
        return value, is_anomaly
    
    def generate_reading(self) -> Dict:
        """
        Generate a complete set of vital signs
        
        Returns:
            Dictionary with patient data and vital signs
        """
        # Generate all vitals
        heart_rate, hr_anomaly = self._generate_single_vital('heart_rate')
        spo2, spo2_anomaly = self._generate_single_vital('spo2')
        systolic, sys_anomaly = self._generate_single_vital('systolic_bp')
        diastolic, dia_anomaly = self._generate_single_vital('diastolic_bp')
        temperature, temp_anomaly = self._generate_single_vital('temperature')
        respiratory_rate, rr_anomaly = self._generate_single_vital('respiratory_rate')
        
        # Check if any anomaly occurred
        has_anomaly = any([hr_anomaly, spo2_anomaly, sys_anomaly, 
                          dia_anomaly, temp_anomaly, rr_anomaly])
        
        # Create reading
        reading = {
            'patient_id': self.patient_id,
            'timestamp': datetime.utcnow().isoformat(),
            'profile': self.profile_name,
            'vital_signs': {
                'heart_rate': round(heart_rate, 1),
                'spo2': round(spo2, 1),
                'blood_pressure': {
                    'systolic': round(systolic, 1),
                    'diastolic': round(diastolic, 1)
                },
                'temperature': round(temperature, 2),
                'respiratory_rate': round(respiratory_rate, 1)
            },
            'metadata': {
                'has_anomaly': has_anomaly,
                'anomaly_details': {
                    'heart_rate': hr_anomaly,
                    'spo2': spo2_anomaly,
                    'systolic_bp': sys_anomaly,
                    'diastolic_bp': dia_anomaly,
                    'temperature': temp_anomaly,
                    'respiratory_rate': rr_anomaly
                } if has_anomaly else None,
                'reading_number': self.time_offset,
                'simulated_time_hours': round(self.time_offset / 3600.0, 2)
            }
        }
        
        # Increment time for next reading
        self.time_offset += 1  # Each reading = 1 second
        
        return reading


class MultiPatientSimulator:
    """Manage multiple patient simulators"""
    
    def __init__(self, num_patients: int = 10, profile_distribution: Optional[Dict[str, float]] = None):
        """
        Initialize multi-patient simulator
        
        Args:
            num_patients: Number of patients to simulate
            profile_distribution: Distribution of profiles (e.g., {'HEALTHY': 0.7, 'AT_RISK': 0.2, 'CRITICAL': 0.1})
        """
        self.num_patients = num_patients
        
        # Default distribution: 70% healthy, 20% at-risk, 10% critical
        self.profile_distribution = profile_distribution or {
            'HEALTHY': 0.7,
            'AT_RISK': 0.2,
            'CRITICAL': 0.1
        }
        
        self.patients = self._initialize_patients()
    
    def _initialize_patients(self) -> List[VitalSignsGenerator]:
        """Create patient simulators based on distribution"""
        patients = []
        
        # Calculate number of patients per profile
        profiles = []
        for profile, ratio in self.profile_distribution.items():
            count = int(self.num_patients * ratio)
            profiles.extend([profile] * count)
        
        # Fill remaining slots with healthy patients
        while len(profiles) < self.num_patients:
            profiles.append('HEALTHY')
        
        # Shuffle for randomness
        random.shuffle(profiles)
        
        # Create patient simulators
        for i, profile in enumerate(profiles):
            patient_id = f"PT-{i+1:04d}"
            patients.append(VitalSignsGenerator(patient_id, profile))
        
        return patients
    
    def generate_batch(self) -> List[Dict]:
        """Generate readings for all patients"""
        readings = []
        for patient in self.patients:
            readings.append(patient.generate_reading())
        return readings
    
    def get_patient_summary(self) -> Dict:
        """Get summary of all patients"""
        summary = {
            'total_patients': self.num_patients,
            'profiles': {}
        }
        
        for profile in ['HEALTHY', 'AT_RISK', 'CRITICAL']:
            count = sum(1 for p in self.patients if p.profile_name == profile)
            summary['profiles'][profile] = count
        
        return summary


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Patient Vital Signs Simulator - Test")
    print("=" * 60)
    
    # Test single patient
    print("\n1. Single Patient Test (HEALTHY):")
    print("-" * 60)
    patient = VitalSignsGenerator("PT-0001", "HEALTHY", seed=42)
    
    for i in range(5):
        reading = patient.generate_reading()
        print(f"\nReading {i+1}:")
        print(json.dumps(reading, indent=2))
    
    # Test multi-patient
    print("\n\n2. Multi-Patient Test (10 patients):")
    print("-" * 60)
    simulator = MultiPatientSimulator(num_patients=10)
    print(json.dumps(simulator.get_patient_summary(), indent=2))
    
    print("\n\nGenerating one batch of readings...")
    batch = simulator.generate_batch()
    print(f"Generated {len(batch)} readings")
    
    # Show first 3 readings
    for i, reading in enumerate(batch[:3]):
        print(f"\n--- Patient {i+1} ({reading['profile']}) ---")
        print(json.dumps(reading['vital_signs'], indent=2))