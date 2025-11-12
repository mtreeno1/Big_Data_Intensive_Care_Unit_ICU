"""
Data Generation Module
Patient simulation and vital signs generation
"""

from .vital_signs_generator import VitalSignsGenerator, PatientProfile
from .patient_simulator import MultiPatientSimulator

__all__ = [
    'VitalSignsGenerator',
    'PatientProfile',
    'MultiPatientSimulator'
]