"""
Risk scoring engine for ICU patients
Analyzes vital signs to calculate risk scores and levels
"""
from typing import Dict, Optional
from enum import Enum
from datetime import datetime 
import math

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskScorer:
    """Calculates patient risk scores based on vital signs"""
    
    def __init__(self):
        # Risk weights for different vital signs
        self.risk_weights = {
            "heart_rate": {
                "normal_range": (60, 100),
                "critical_low": 40,
                "critical_high": 120,
                "weight": 0.25
            },
            "spo2": {
                "normal_range": (95, 100),
                "critical_low": 90,
                "critical_high": 100,
                "weight": 0.20
            },
            "temperature": {
                "normal_range": (36.5, 37.5),
                "critical_low": 35.0,
                "critical_high": 38.5,
                "weight": 0.15
            },
            "respiratory_rate": {
                "normal_range": (12, 20),
                "critical_low": 8,
                "critical_high": 25,
                "weight": 0.20
            },
            "blood_pressure_systolic": {
                "normal_range": (90, 140),
                "critical_low": 80,
                "critical_high": 160,
                "weight": 0.15
            },
            "blood_pressure_diastolic": {
                "normal_range": (60, 90),
                "critical_low": 50,
                "critical_high": 100,
                "weight": 0.05
            }
        }
    
    def calculate_risk_score(self, vital_signs: Dict) -> float:
        """
        Calculate risk score from 0.0 (low risk) to 1.0 (critical)
        """
        total_risk = 0.0
        total_weight = 0.0
        
        for vital, config in self.risk_weights.items():
            if vital in vital_signs:
                value = vital_signs[vital]
                risk = self._calculate_vital_risk(value, config)
                total_risk += risk * config["weight"]
                total_weight += config["weight"]
        
        # Normalize to 0-1 range
        if total_weight > 0:
            return min(1.0, total_risk / total_weight)
        return 0.0
    
    def _calculate_vital_risk(self, value: float, config: Dict) -> float:
        """Calculate risk for a single vital sign (0.0 to 1.0)"""
        normal_min, normal_max = config["normal_range"]
        
        if normal_min <= value <= normal_max:
            return 0.0  # Normal
        
        # Calculate deviation
        if value < normal_min:
            deviation = (normal_min - value) / normal_min
        else:
            deviation = (value - normal_max) / normal_max
        
        # Apply critical thresholds
        if value <= config["critical_low"] or value >= config["critical_high"]:
            deviation *= 2.0  # Double risk for critical values
        
        return min(1.0, deviation)
    
    def get_risk_level(self, risk_score: float) -> RiskLevel:
        """Convert risk score to risk level"""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def assess_patient_risk(self, vital_signs: Dict, critical_event: str = "none") -> Dict:
        """
        Full risk assessment including critical events
        """
        base_score = self.calculate_risk_score(vital_signs)
        
        # Boost score for critical events
        event_multiplier = {
            "none": 1.0,
            "cardiac_arrest": 2.0,
            "respiratory_failure": 1.8,
            "shock": 1.8,
            "sepsis": 1.5
        }.get(critical_event, 1.0)
        
        final_score = min(1.0, base_score * event_multiplier)
        risk_level = self.get_risk_level(final_score)
        
        return {
            "risk_score": round(final_score, 3),
            "risk_level": risk_level.value,
            "critical_event": critical_event,
            "assessment_time": datetime.utcnow().isoformat() + "Z"
        }