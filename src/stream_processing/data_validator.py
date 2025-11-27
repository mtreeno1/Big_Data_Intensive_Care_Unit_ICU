"""
Medical Data Validator with Outlier Detection
"""
import logging
from typing import Dict, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

class MedicalDataValidator:
    """Validate and clean medical vital signs data"""
    
    # Medical reference ranges (normal ranges)
    VITAL_RANGES = {
        "heart_rate": (40, 200),           # bpm
        "spo2": (70, 100),                 # %
        "temperature": (35.0, 42.0),       # Celsius
        "respiratory_rate": (8, 40),       # breaths/min
        "blood_pressure_systolic": (70, 220),   # mmHg
        "blood_pressure_diastolic": (40, 140)   # mmHg
    }
    
    # Critical thresholds
    CRITICAL_THRESHOLDS = {
        "heart_rate": (50, 180),
        "spo2": (85, 100),
        "temperature": (36.0, 39.5),
        "respiratory_rate": (10, 35),
        "blood_pressure_systolic": (90, 180),
        "blood_pressure_diastolic": (60, 110)
    }
    
    def __init__(self):
        self.history = {}  # Store recent values per patient
        self.max_history = 20
    
    def validate_and_clean(self, reading: Dict) -> Tuple[Dict, bool]:
        """
        Validate and clean vital signs
        
        Returns:
            (cleaned_reading, is_valid)
        """
        patient_id = reading["patient_id"]
        vitals = reading.get("vital_signs", {})
        
        cleaned_vitals = {}
        is_valid = True
        issues = []
        
        for vital, value in vitals.items():
            if vital not in self.VITAL_RANGES:
                cleaned_vitals[vital] = value
                continue
            
            # ✅ 1. Check range
            min_val, max_val = self.VITAL_RANGES[vital]
            
            if not (min_val <= value <= max_val):
                issues.append(f"{vital}={value} out of range [{min_val}, {max_val}]")
                
                # Try to impute with recent average
                imputed = self._impute_value(patient_id, vital)
                if imputed is not None:
                    cleaned_vitals[vital] = imputed
                    logger.warning(f"⚠️  {patient_id}: {vital} outlier, imputed with {imputed:.1f}")
                else:
                    is_valid = False
                    logger.error(f"❌ {patient_id}: {vital} invalid and no history for imputation")
                continue
            
            # ✅ 2. Check sudden change (spike detection)
            if patient_id in self.history and vital in self.history[patient_id]:
                recent_values = self.history[patient_id][vital]
                avg = np.mean(recent_values)
                std = np.std(recent_values)
                
                # Z-score > 3 = outlier
                if std > 0:
                    z_score = abs(value - avg) / std
                    if z_score > 3:
                        issues.append(f"{vital} spike detected (z={z_score:.2f})")
                        # Use smoothed value
                        smoothed = self._smooth_value(patient_id, vital, value)
                        cleaned_vitals[vital] = smoothed
                        logger.warning(f"⚠️  {patient_id}: {vital} spike, smoothed to {smoothed:.1f}")
                        continue
            
            # ✅ 3. Valid value
            cleaned_vitals[vital] = value
            
            # Store in history
            if patient_id not in self.history:
                self.history[patient_id] = {}
            if vital not in self.history[patient_id]:
                self.history[patient_id][vital] = []
            
            self.history[patient_id][vital].append(value)
            
            # Keep only recent values
            if len(self.history[patient_id][vital]) > self.max_history:
                self.history[patient_id][vital].pop(0)
        
        # Update reading
        reading["vital_signs"] = cleaned_vitals
        
        if issues:
            reading["data_quality_issues"] = issues
        
        return reading, is_valid
    
    def _impute_value(self, patient_id: str, vital: str) -> Optional[float]:
        """Impute missing/invalid value with recent average"""
        if patient_id in self.history and vital in self.history[patient_id]:
            recent = self.history[patient_id][vital]
            if len(recent) >= 3:
                return float(np.mean(recent[-3:]))  # Average of last 3
        return None
    
    def _smooth_value(self, patient_id: str, vital: str, current: float) -> float:
        """Smooth spike using exponential moving average"""
        if patient_id in self.history and vital in self.history[patient_id]:
            recent = self.history[patient_id][vital]
            if len(recent) >= 2:
                # EMA with alpha=0.3
                ema = recent[-1]
                alpha = 0.3
                smoothed = alpha * current + (1 - alpha) * ema
                return float(smoothed)
        return current
    
    def get_data_quality_score(self, patient_id: str) -> float:
        """Calculate data quality score (0-1)"""
        if patient_id not in self.history:
            return 0.5
        
        total_values = sum(len(values) for values in self.history[patient_id].values())
        if total_values == 0:
            return 0.5
        
        # Simple metric: more data = higher quality
        score = min(total_values / (len(self.VITAL_RANGES) * self.max_history), 1.0)
        return score