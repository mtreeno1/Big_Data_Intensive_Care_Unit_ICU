"""
Stream Processor - Calculate risk scores and detect anomalies
SAFE VERSION (Handles NoneType)
"""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class StreamProcessor:
    def __init__(self):
        self.processed_count = 0
    
    def _safe_get(self, vitals: Dict, key: str) -> float:
        """Hàm lấy dữ liệu an toàn: Trả về None nếu không có dữ liệu hợp lệ"""
        val = vitals.get(key)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def process_vital_signs(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        try:
            vitals = reading.get('vital_signs', {})
            patient_id = reading.get('patient_id', 'Unknown')
            
            # Tính toán
            mews_score = self._calculate_mews(vitals)
            risk_score = self._calculate_risk_score(vitals, mews_score)
            risk_level = self._determine_risk_level(risk_score, mews_score)
            anomalies = self._detect_anomalies(vitals)
            warnings = self._generate_warnings(vitals, mews_score)
            
            self.processed_count += 1
            
            return {
                'patient_id': patient_id,
                'timestamp': reading.get('timestamp', datetime.utcnow()),
                'risk_score': round(risk_score, 2),
                'risk_level': risk_level,
                'mews_score': mews_score,
                'anomalies': anomalies,
                'warnings': warnings,
                'vital_signs': vitals
            }
            
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
        score = 0
        
        # Helper để check an toàn
        def check(key, ranges):
            val = self._safe_get(vitals, key)
            if val is None: return 0
            for r_min, r_max, pts in ranges:
                if r_min <= val <= r_max: return pts
            return 0

        # Heart Rate
        hr = self._safe_get(vitals, 'heart_rate')
        if hr is not None:
            if hr <= 40: score += 2
            elif 41 <= hr <= 50: score += 1
            elif 101 <= hr <= 110: score += 1
            elif 111 <= hr <= 129: score += 2
            elif hr >= 130: score += 3
        
        # Resp Rate
        rr = self._safe_get(vitals, 'respiratory_rate')
        if rr is not None:
            if rr < 9: score += 2
            elif 15 <= rr <= 20: score += 1
            elif 21 <= rr <= 29: score += 2
            elif rr >= 30: score += 3

        # Temp
        temp = self._safe_get(vitals, 'temperature')
        if temp is not None:
            if temp < 35 or temp >= 38.5: score += 2

        # BP Systolic
        bp = self._safe_get(vitals, 'blood_pressure_systolic')
        if bp is None: # Check fallback keys
             bp = self._safe_get(vitals, 'bp_systolic')
             
        if bp is not None:
            if bp <= 70: score += 3
            elif 71 <= bp <= 80: score += 2
            elif 81 <= bp <= 100: score += 1
            elif bp >= 200: score += 2

        # SpO2
        spo2 = self._safe_get(vitals, 'spo2')
        if spo2 is not None:
            if spo2 < 85: score += 3
            elif 85 <= spo2 <= 89: score += 2
            elif 90 <= spo2 <= 93: score += 1
            
        return min(score, 14)
    
    def _calculate_risk_score(self, vitals: Dict[str, float], mews_score: int) -> float:
        base_score = (mews_score / 14.0) * 70
        critical_score = 0
        
        hr = self._safe_get(vitals, 'heart_rate')
        if hr and (hr < 40 or hr > 140): critical_score += 10
        
        spo2 = self._safe_get(vitals, 'spo2')
        if spo2 and spo2 < 85: critical_score += 10
        elif spo2 and spo2 < 90: critical_score += 5
        
        return min(base_score + critical_score, 100)
    
    def _determine_risk_level(self, risk_score: float, mews_score: int) -> str:
        if risk_score >= 75 or mews_score >= 5: return 'CRITICAL' # Hạ ngưỡng xuống để dễ thấy alert
        elif risk_score >= 50 or mews_score >= 4: return 'HIGH'
        elif risk_score >= 20 or mews_score >= 2: return 'MODERATE'
        return 'STABLE'
    
    def _detect_anomalies(self, vitals: Dict[str, float]) -> list:
        anomalies = []
        hr = self._safe_get(vitals, 'heart_rate')
        if hr and hr > 130: anomalies.append({'type': 'tachycardia', 'val': hr})
        
        spo2 = self._safe_get(vitals, 'spo2')
        if spo2 and spo2 < 90: anomalies.append({'type': 'hypoxia', 'val': spo2})
        
        return anomalies

    def _generate_warnings(self, vitals: Dict, mews: int) -> list:
        warnings = []
        if mews >= 5: warnings.append(f"High MEWS Score: {mews}")
        return warnings