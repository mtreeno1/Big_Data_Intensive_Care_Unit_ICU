"""
Feature Engineering for Time Series Vital Signs
"""
import logging
from typing import Dict, List
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Extract time-series features for ML models"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.patient_windows = {}  # Store sliding windows per patient
    
    def extract_features(self, reading: Dict) -> Dict:
        """
        Extract time-series features
        
        Features:
        - Rolling mean (last N readings)
        - Rolling std (volatility)
        - Trend (gradient)
        - Min/Max in window
        - Rate of change
        """
        patient_id = reading["patient_id"]
        vitals = reading.get("vital_signs", {})
        
        # Initialize window for new patient
        if patient_id not in self.patient_windows:
            self.patient_windows[patient_id] = {}
        
        features = {}
        
        for vital, value in vitals.items():
            # Initialize deque for this vital
            if vital not in self.patient_windows[patient_id]:
                self.patient_windows[patient_id][vital] = deque(maxlen=self.window_size)
            
            window = self.patient_windows[patient_id][vital]
            window.append(value)
            
            if len(window) >= 3:
                values = list(window)
                
                # ✅ Rolling statistics
                features[f"{vital}_mean"] = float(np.mean(values))
                features[f"{vital}_std"] = float(np.std(values))
                features[f"{vital}_min"] = float(np.min(values))
                features[f"{vital}_max"] = float(np.max(values))
                
                # ✅ Trend (linear regression slope)
                x = np.arange(len(values))
                trend = np.polyfit(x, values, 1)[0]  # Slope
                features[f"{vital}_trend"] = float(trend)
                
                # ✅ Rate of change (velocity)
                if len(values) >= 2:
                    rate = values[-1] - values[-2]
                    features[f"{vital}_rate"] = float(rate)
                
                # ✅ Acceleration (2nd derivative)
                if len(values) >= 3:
                    accel = (values[-1] - values[-2]) - (values[-2] - values[-3])
                    features[f"{vital}_accel"] = float(accel)
        
        # Add features to reading
        reading["time_series_features"] = features
        
        return reading
    
    def get_window_summary(self, patient_id: str) -> Dict:
        """Get summary statistics for patient's window"""
        if patient_id not in self.patient_windows:
            return {}
        
        summary = {}
        for vital, window in self.patient_windows[patient_id].items():
            if len(window) > 0:
                values = list(window)
                summary[vital] = {
                    "count": len(values),
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "trend": float(np.polyfit(np.arange(len(values)), values, 1)[0]) if len(values) >= 2 else 0.0
                }
        
        return summary