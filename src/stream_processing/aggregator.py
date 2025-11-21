"""
Stream Aggregator
Performs windowed aggregations on vital signs data
"""

import logging
from typing import Dict, List
from collections import defaultdict, deque
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class WindowAggregator:
    """Aggregates vital signs over time windows"""
    
    def __init__(self, window_seconds: int = 60):
        """
        Initialize aggregator
        
        Args:
            window_seconds: Size of the time window in seconds
        """
        self.window_seconds = window_seconds
        self.window_duration = timedelta(seconds=window_seconds)
        
        # Store readings for each patient: patient_id -> deque of (timestamp, vitals)
        self.patient_buffers: Dict[str, deque] = defaultdict(lambda: deque())
        
        logger.info(f"✅ WindowAggregator initialized: {window_seconds}s window")
    
    def add_reading(self, patient_id: str, timestamp: datetime, vitals: Dict):
        """
        Add a new reading to the buffer
        
        Args:
            patient_id: Patient identifier
            timestamp: Reading timestamp
            vitals: Vital signs dictionary
        """
        buffer = self.patient_buffers[patient_id]
        buffer.append((timestamp, vitals))
        
        # Clean old readings outside the window
        cutoff_time = timestamp - self.window_duration
        while buffer and buffer[0][0] < cutoff_time:
            buffer.popleft()
    
    def get_aggregates(self, patient_id: str) -> Dict[str, Dict[str, float]]:
        """
        Calculate aggregated statistics for a patient
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Dictionary of statistics per vital sign
        """
        buffer = self.patient_buffers[patient_id]
        
        if not buffer:
            return {}
        
        # Extract vital signs
        vital_types = [
            'heart_rate',
            'spo2',
            'temperature',
            'respiratory_rate'
        ]
        
        # Also handle blood pressure
        bp_types = ['systolic', 'diastolic']
        
        aggregates = {}
        
        # Aggregate each vital type
        for vital_type in vital_types:
            values = [reading[1][vital_type] for reading in buffer 
                     if vital_type in reading[1]]
            
            if values:
                aggregates[vital_type] = self._calculate_stats(values)
        
        # Aggregate blood pressure
        for bp_type in bp_types:
            values = [reading[1]['blood_pressure'][bp_type] for reading in buffer 
                     if 'blood_pressure' in reading[1] and bp_type in reading[1]['blood_pressure']]
            
            if values:
                aggregates[f'{bp_type}_bp'] = self._calculate_stats(values)
        
        return aggregates
    
    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate statistics for a list of values
        
        Args:
            values: List of numeric values
            
        Returns:
            Dictionary with mean, min, max, std, count
        """
        arr = np.array(values)
        return {
            'mean': float(np.mean(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'std': float(np.std(arr)),
            'count': len(values),
            'median': float(np.median(arr))
        }
    
    def get_buffer_size(self, patient_id: str) -> int:
        """Get number of readings in buffer for a patient"""
        return len(self.patient_buffers[patient_id])
    
    def clear_patient(self, patient_id: str):
        """Clear buffer for a patient"""
        if patient_id in self.patient_buffers:
            del self.patient_buffers[patient_id]
    
    def get_active_patients(self) -> List[str]:
        """Get list of patients with data in buffers"""
        return list(self.patient_buffers.keys())