"""
Patient Simulator with Dynamic State Transitions
"""

import random
from typing import Dict, List
from datetime import datetime
from .vital_signs_generator import VitalSignsGenerator, PatientProfile


class MultiPatientSimulator:
    """
    Manages multiple patients with dynamic health state transitions
    """
    
    def __init__(
        self,
        num_patients: int = 10,
        profile_distribution: Dict[str, float] = None,
        enable_transitions: bool = True
    ):
        """
        Initialize multi-patient simulator
        
        Args:
            num_patients: Number of patients to simulate
            profile_distribution: Initial distribution of health profiles
            enable_transitions: Enable automatic profile transitions
        """
        self.num_patients = num_patients
        self.enable_transitions = enable_transitions
        
        # Default distribution
        if profile_distribution is None:
            profile_distribution = {
                'HEALTHY': 0.7,
                'AT_RISK': 0.2,
                'CRITICAL': 0.1
            }
        
        self.profile_distribution = profile_distribution
        self.patient_generators = {}
        
        # Create patient generators
        self._create_patients()
    
    def _create_patients(self):
        """Create patient generators based on distribution"""
        profiles = []
        
        # Calculate number of patients for each profile
        for profile_name, ratio in self.profile_distribution.items():
            count = int(self.num_patients * ratio)
            profiles.extend([profile_name] * count)
        
        # Fill remaining slots with HEALTHY
        while len(profiles) < self.num_patients:
            profiles.append('HEALTHY')
        
        # Shuffle to randomize
        random.shuffle(profiles)
        
        # Create generators with transitions enabled
        for i, profile_name in enumerate(profiles):
            patient_id = f"PT-{i+1:04d}"
            profile = PatientProfile[profile_name]
            
            self.patient_generators[patient_id] = VitalSignsGenerator(
                patient_id=patient_id,
                profile=profile,
                enable_transitions=self.enable_transitions
            )
    
    def generate_batch(self) -> List[Dict]:
        """
        Generate one reading for each patient
        Profiles may change during generation!
        
        Returns:
            List of readings (one per patient)
        """
        batch = []
        
        for patient_id, generator in self.patient_generators.items():
            reading = generator.generate_reading()
            batch.append(reading)
        
        return batch
    
    def get_patient_summary(self) -> Dict:
        """
        Get current summary of all patients
        
        Returns:
            Dictionary with patient information and statistics
        """
        summary = {
            'total_patients': len(self.patient_generators),
            'profiles': {},
            'patients': {},
            'transitions': []
        }
        
        # Count by current profile (may have changed!)
        for patient_id, generator in self.patient_generators.items():
            current_profile = generator.profile.name
            initial_profile = generator.initial_profile.name
            
            # Count current profiles
            if current_profile not in summary['profiles']:
                summary['profiles'][current_profile] = 0
            summary['profiles'][current_profile] += 1
            
            # Store patient info
            summary['patients'][patient_id] = {
                'profile': current_profile,
                'initial_profile': initial_profile,
                'device_id': generator.device_id,
                'readings_count': generator.readings_count,
                'transitions': len(generator.transition_history)
            }
            
            # Collect all transitions
            for transition in generator.transition_history:
                summary['transitions'].append({
                    'patient_id': patient_id,
                    **transition
                })
        
        return summary
    
    def get_transition_report(self) -> Dict:
        """Get detailed transition report for all patients"""
        report = {
            'total_transitions': 0,
            'by_patient': {},
            'by_type': {
                'HEALTHY → AT_RISK': 0,
                'HEALTHY → CRITICAL': 0,
                'AT_RISK → HEALTHY': 0,
                'AT_RISK → CRITICAL': 0,
                'CRITICAL → AT_RISK': 0,
                'CRITICAL → HEALTHY': 0
            }
        }
        
        for patient_id, generator in self.patient_generators.items():
            transitions = generator.get_transition_history()
            report['total_transitions'] += len(transitions)
            report['by_patient'][patient_id] = {
                'count': len(transitions),
                'current_profile': generator.profile.value,
                'initial_profile': generator.initial_profile.value,
                'transitions': transitions
            }
            
            # Count by type
            for t in transitions:
                key = f"{t['from_profile']} → {t['to_profile']}"
                if key in report['by_type']:
                    report['by_type'][key] += 1
        
        return report
    
    def get_patient(self, patient_id: str) -> VitalSignsGenerator:
        """Get generator for specific patient"""
        return self.patient_generators.get(patient_id)
    
    def get_all_patients(self) -> Dict[str, VitalSignsGenerator]:
        """Get all patient generators"""
        return self.patient_generators


# Example usage - SỬA PHẦN NÀY
if __name__ == "__main__":
    # Fix import for direct execution
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Now import properly
    from src.data_generation.vital_signs_generator import VitalSignsGenerator, PatientProfile
    
    print("=" * 80)
    print("MULTI-PATIENT SIMULATOR WITH TRANSITIONS")
    print("=" * 80)
    
    # Create simulator with transitions enabled
    simulator = MultiPatientSimulator(
        num_patients=5,
        enable_transitions=True
    )
    
    initial_summary = simulator.get_patient_summary()
    print(f"\n📊 Initial State:")
    print(f"Total patients: {initial_summary['total_patients']}")
    print(f"Profiles: {initial_summary['profiles']}")
    
    # Generate 30 batches
    print(f"\n🔄 Generating 30 batches...")
    for i in range(30):
        batch = simulator.generate_batch()
        
        if (i + 1) % 10 == 0:
            summary = simulator.get_patient_summary()
            print(f"\nAfter {i+1} batches:")
            print(f"  Profiles: {summary['profiles']}")
            print(f"  Total transitions: {len(summary['transitions'])}")
    
    # Final report
    print(f"\n{'='*80}")
    print("📈 FINAL TRANSITION REPORT")
    print(f"{'='*80}")
    
    report = simulator.get_transition_report()
    print(f"Total transitions across all patients: {report['total_transitions']}")
    
    print(f"\n🔄 Transitions by type:")
    for trans_type, count in report['by_type'].items():
        if count > 0:
            print(f"  {trans_type}: {count}")
    
    print(f"\n👥 Per patient:")
    for patient_id, data in report['by_patient'].items():
        if data['count'] > 0:
            print(f"  {patient_id}: {data['initial_profile']} → {data['current_profile']} "
                  f"({data['count']} transitions)")