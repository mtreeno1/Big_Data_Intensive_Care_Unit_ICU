"""
Data Validator - Clean and validate incoming vital signs
SAFE VERSION (Handles NoneType)
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

class MedicalDataValidator:
    def __init__(self):
        # Ngưỡng sinh lý hợp lệ (Physiological Ranges)
        self.ranges = {
            'heart_rate': (30, 200),
            'spo2': (50, 100),
            'temperature': (30, 45),
            'respiratory_rate': (4, 60),
            'blood_pressure_systolic': (50, 250),
            'blood_pressure_diastolic': (20, 150)
        }
        
        # Bộ nhớ đệm để làm mịn dữ liệu (Smoothing history)
        self.history = {}

    def validate_and_clean(self, reading):
        """
        Validate and clean a single reading
        """
        try:
            cleaned = reading.copy()
            vitals = cleaned.get('vital_signs', {})
            patient_id = reading.get('patient_id')
            
            if not vitals:
                return cleaned, False

            # Khởi tạo history cho bệnh nhân mới
            if patient_id not in self.history:
                self.history[patient_id] = {}

            cleaned_vitals = {}
            
            for key, value in vitals.items():
                # --- FIX QUAN TRỌNG: BỎ QUA NẾU VALUE LÀ NONE ---
                if value is None:
                    continue
                
                # Chuyển đổi sang float an toàn
                try:
                    val = float(value)
                except (ValueError, TypeError):
                    continue # Bỏ qua nếu không phải số

                # Kiểm tra ngưỡng (Range Check)
                if key in self.ranges:
                    min_val, max_val = self.ranges[key]
                    
                    # Nếu ngoài ngưỡng -> coi là Outlier -> Impute (Sửa lỗi)
                    if not (min_val <= val <= max_val):
                        # Nếu có lịch sử, dùng giá trị cũ gần nhất
                        if key in self.history[patient_id]:
                            imputed_val = self.history[patient_id][key]
                            # logger.warning(f"⚠️ {patient_id}: {key} outlier ({val}), imputed with {imputed_val}")
                            cleaned_vitals[key] = imputed_val
                        else:
                            # Không có lịch sử -> Bỏ qua hoặc lấy min/max
                            # logger.error(f"❌ {patient_id}: {key} invalid ({val}) and no history")
                            pass 
                        continue

                # Smoothing (Làm mịn gai dữ liệu)
                # Nếu giá trị nhảy quá xa so với trung bình cũ -> Smooth lại
                if key in self.history[patient_id]:
                    prev_val = self.history[patient_id][key]
                    change = abs(val - prev_val)
                    
                    # Ngưỡng thay đổi đột ngột (tùy chỉnh)
                    threshold = 20 if key == 'heart_rate' else 5 
                    
                    if change > threshold:
                        # Smooth: Lấy trung bình trọng số (70% cũ, 30% mới)
                        smooth_val = (prev_val * 0.7) + (val * 0.3)
                        # logger.warning(f"⚠️ {patient_id}: {key} spike, smoothed to {smooth_val:.1f}")
                        val = smooth_val

                # Lưu vào history
                self.history[patient_id][key] = val
                cleaned_vitals[key] = val

            # Cập nhật lại vitals đã làm sạch
            cleaned['vital_signs'] = cleaned_vitals
            
            # Chỉ coi là hợp lệ nếu có ít nhất 1 chỉ số sinh tồn
            is_valid = len(cleaned_vitals) > 0
            
            return cleaned, is_valid

        except Exception as e:
            logger.error(f"Validation Error: {e}")
            return reading, False