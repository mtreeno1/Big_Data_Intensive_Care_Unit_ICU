"""
Stream Processor - Calculate risk scores and detect anomalies
"""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamProcessor:
    """
    Process vital signs and calculate risk scores
    Uses Modified Early Warning Score (MEWS) system
    """
    
    def __init__(self):
        self.processed_count = 0
    
    def process_vital_signs(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing function
        
        Args:
            reading: Cleaned vital signs data with structure:
                {
                    'patient_id': str,
                    'timestamp': datetime,
                    'vital_signs': {
                        'heart_rate': float,
                        'spo2': float,
                        'temperature': float,
                        'respiratory_rate': float,
                        'blood_pressure_systolic': float,
                        'blood_pressure_diastolic': float
                    }
                }
        
        Returns:
            Dictionary with risk assessment:
                {
                    'risk_score': float,
                    'risk_level': str,
                    'mews_score': int,
                    'anomalies': list,
                    'warnings': list
                }
        """
        try:
            vitals = reading.get('vital_signs', {})
            patient_id = reading.get('patient_id', 'Unknown')
            
            # Calculate MEWS (Modified Early Warning Score)
            mews_score = self._calculate_mews(vitals)
            
            # Calculate overall risk score (0-100)
            risk_score = self._calculate_risk_score(vitals, mews_score)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score, mews_score)
            
            # Detect anomalies
            anomalies = self._detect_anomalies(vitals)
            
            # Generate warnings
            warnings = self._generate_warnings(vitals, mews_score)
            
            self.processed_count += 1
            
            result = {
                'patient_id': patient_id,
                'timestamp': reading.get('timestamp', datetime.utcnow()),
                'risk_score': round(risk_score, 2),
                'risk_level': risk_level,
                'mews_score': mews_score,
                'anomalies': anomalies,
                'warnings': warnings,
                'vital_signs': vitals
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing vital signs: {e}")
            return {
                'risk_score': 0.0,
                'risk_level': 'UNKNOWN',
                'mews_score': 0,
                'anomalies': [],
                'warnings': [f"Processing error: {str(e)}"]
            }
    
    def _calculate_mews(self, vitals: Dict[str, float]) -> int:
        """
        Calculate Modified Early Warning Score (MEWS)
        Score range: 0-14 (higher = more critical)
        """
        score = 0
        
        # Heart Rate scoring
        hr = vitals.get('heart_rate', 0)
        if hr <= 40:
            score += 2
        elif 41 <= hr <= 50:
            score += 1
        elif 101 <= hr <= 110:
            score += 1
        elif 111 <= hr <= 129:
            score += 2
        elif hr >= 130:
            score += 3
        
        # Respiratory Rate scoring
        rr = vitals.get('respiratory_rate', 0)
        if rr < 9:
            score += 2
        elif 9 <= rr <= 14:
            score += 0
        elif 15 <= rr <= 20:
            score += 1
        elif 21 <= rr <= 29:
            score += 2
        elif rr >= 30:
            score += 3
        
        # Temperature scoring (Celsius)
        temp = vitals.get('temperature', 0)
        if temp < 35:
            score += 2
        elif temp >= 38.5:
            score += 2
        
        # Blood Pressure Systolic scoring
        bp_sys = vitals.get('blood_pressure_systolic', 0)
        if bp_sys <= 70:
            score += 3
        elif 71 <= bp_sys <= 80:
            score += 2
        elif 81 <= bp_sys <= 100:
            score += 1
        elif bp_sys >= 200:
            score += 2
        
        # SpO2 scoring
        spo2 = vitals.get('spo2', 0)
        if spo2 < 85:
            score += 3
        elif 85 <= spo2 <= 89:
            score += 2
        elif 90 <= spo2 <= 93:
            score += 1
        
        return min(score, 14)  # Cap at 14
    
    def _calculate_risk_score(self, vitals: Dict[str, float], mews_score: int) -> float:
        """
        Calculate overall risk score (0-100)
        Combines MEWS with individual vital thresholds
        """
        # Base score from MEWS (0-70)
        base_score = (mews_score / 14.0) * 70
        
        # Additional scoring based on critical thresholds (0-30)
        critical_score = 0
        
        # Critical HR
        hr = vitals.get('heart_rate', 0)
        if hr < 40 or hr > 140:
            critical_score += 10
        elif hr < 50 or hr > 120:
            critical_score += 5
        
        # Critical SpO2
        spo2 = vitals.get('spo2', 0)
        if spo2 < 85:
            critical_score += 10
        elif spo2 < 90:
            critical_score += 5
        
        # Critical Temperature
        temp = vitals.get('temperature', 0)
        if temp < 35 or temp > 39:
            critical_score += 10
        
        total_score = min(base_score + critical_score, 100)
        return total_score
    
    def _determine_risk_level(self, risk_score: float, mews_score: int) -> str:
        """
        Determine risk level based on score
        """
        if risk_score >= 75 or mews_score >= 10:
            return 'CRITICAL'
        elif risk_score >= 50 or mews_score >= 7:
            return 'HIGH'
        elif risk_score >= 25 or mews_score >= 4:
            return 'MODERATE'
        else:
            return 'STABLE'
    
    def _detect_anomalies(self, vitals: Dict[str, float]) -> list:
        """
        Detect anomalies in vital signs
        """
        anomalies = []
        
        # Heart Rate anomalies
        hr = vitals.get('heart_rate', 0)
        if hr < 40:
            anomalies.append({'type': 'bradycardia', 'value': hr, 'severity': 'HIGH'})
        elif hr > 130:
            anomalies.append({'type': 'tachycardia', 'value': hr, 'severity': 'HIGH'})
        
        # SpO2 anomalies
        spo2 = vitals.get('spo2', 0)
        if spo2 < 90:
            anomalies.append({'type': 'hypoxemia', 'value': spo2, 'severity': 'CRITICAL'})
        
        # Temperature anomalies
        temp = vitals.get('temperature', 0)
        if temp < 35:
            anomalies.append({'type': 'hypothermia', 'value': temp, 'severity': 'HIGH'})
        elif temp > 39:
            anomalies.append({'type': 'hyperthermia', 'value': temp, 'severity': 'HIGH'})
        
        # Blood Pressure anomalies
        bp_sys = vitals.get('blood_pressure_systolic', 0)
        if bp_sys < 80:
            anomalies.append({'type': 'hypotension', 'value': bp_sys, 'severity': 'HIGH'})
        elif bp_sys > 180:
            anomalies.append({'type': 'hypertension', 'value': bp_sys, 'severity': 'MODERATE'})
        
        return anomalies
    
    def _generate_warnings(self, vitals: Dict[str, float], mews_score: int) -> list:
        """
        Generate human-readable warnings
        """
        warnings = []
        
        if mews_score >= 10:
            warnings.append("🚨 CRITICAL: MEWS score indicates immediate intervention required")
        elif mews_score >= 7:
            warnings.append("⚠️ HIGH RISK: Close monitoring required")
        elif mews_score >= 4:
            warnings.append("⚡ MODERATE: Increase monitoring frequency")
        
        # Specific vital warnings
        hr = vitals.get('heart_rate', 0)
        if hr < 50:
            warnings.append(f"💓 Bradycardia detected: {hr} bpm")
        elif hr > 120:
            warnings.append(f"💓 Tachycardia detected: {hr} bpm")
        
        spo2 = vitals.get('spo2', 0)
        if spo2 < 90:
            warnings.append(f"🫁 Critical oxygen saturation: {spo2}%")
        
        return warnings
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'total_processed': self.processed_count
        }