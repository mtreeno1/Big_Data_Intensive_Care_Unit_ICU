"""
Enrich Active Patients
Script này tìm các bệnh nhân đang 'Active' trong Database nhưng thiếu thông tin (Unknown/Auto-admitted),
sau đó tra cứu lại trong file clinical_data.csv để cập nhật thông tin chính xác.
"""
import sys
import os
import pandas as pd
import random
from pathlib import Path

# Thêm đường dẫn để import src
sys.path.append(os.getcwd())

from src.database.db_manager import DatabaseManager
from src.database.models import Patient, Admission

# Cấu hình đường dẫn file dữ liệu gốc VitalDB
DATA_FILE = "data/clinical_data.csv"

def enrich_data():
    print("🔄 Bắt đầu quy trình làm giàu dữ liệu bệnh nhân...")
    
    # 1. Load dữ liệu gốc VitalDB
    if not os.path.exists(DATA_FILE):
        print(f"❌ Không tìm thấy file dữ liệu gốc: {DATA_FILE}")
        return

    print("📖 Đang đọc dữ liệu gốc VitalDB...")
    df_source = pd.read_csv(DATA_FILE)
    
    # Chuyển caseid sang string để dễ so sánh
    df_source['caseid'] = df_source['caseid'].astype(str)
    
    # Tạo từ điển tra cứu nhanh theo Case ID
    # { '3962': { 'sex': 'M', 'age': 55, 'dx': '...' } }
    patient_lookup = df_source.set_index('caseid').to_dict('index')

    # 2. Kết nối Database
    db_manager = DatabaseManager()
    session = db_manager.db
    
    try:
        # 3. Lấy danh sách bệnh nhân đang Active
        active_patients = db_manager.get_active_patients()
        print(f"📋 Tìm thấy {len(active_patients)} bệnh nhân đang theo dõi.")
        
        count_updated = 0
        
        for p in active_patients:
            # Chỉ xử lý các ID chuẩn ICU-xxxxxx
            if not p.patient_id.startswith("ICU-"):
                continue
                
            # Trích xuất Case ID từ Patient ID (VD: ICU-003962 -> 3962)
            # Loại bỏ số 0 ở đầu nếu có (3962 thay vì 003962) để khớp với CSV
            case_id = str(int(p.patient_id.split('-')[1]))
            
            # Tra cứu thông tin gốc
            if case_id in patient_lookup:
                info = patient_lookup[case_id]
                needs_update = False
                
                print(f"   🔍 Đang kiểm tra: {p.full_name} (Case {case_id})...")

                # --- A. CẬP NHẬT GIỚI TÍNH (GENDER) ---
                real_gender = "Male" if info['sex'] == 'M' else "Female"
                if p.gender == "Unknown" or p.gender is None:
                    p.gender = real_gender
                    print(f"      + Cập nhật Giới tính: {real_gender}")
                    needs_update = True

                # --- B. CẬP NHẬT CHẨN ĐOÁN (DIAGNOSIS) ---
                # Tìm Admission đang active của bệnh nhân này
                active_adm = session.query(Admission).filter(
                    Admission.patient_id == p.patient_id,
                    Admission.discharge_time.is_(None)
                ).first()
                
                if active_adm:
                    current_dx = active_adm.initial_diagnosis
                    # Nếu chẩn đoán đang là mặc định (Auto...) -> Lấy từ file gốc
                    if "Auto-" in current_dx or current_dx == "Observation":
                        # Ưu tiên lấy tên phẫu thuật (opname), nếu không có thì lấy chẩn đoán (dx)
                        real_diagnosis = info.get('opname')
                        if pd.isna(real_diagnosis):
                            real_diagnosis = info.get('dx', 'Unknown Diagnosis')
                        
                        active_adm.initial_diagnosis = str(real_diagnosis)
                        print(f"      + Cập nhật Chẩn đoán: {real_diagnosis}")
                        needs_update = True
                        
                        # Cập nhật luôn khoa phòng nếu chưa có
                        if not active_adm.department or "ICU" in active_adm.department:
                            dept = info.get('department')
                            if pd.notna(dept):
                                active_adm.department = str(dept)

                # --- C. CẬP NHẬT NHÓM MÁU & THIẾT BỊ (FAKE DATA) ---
                # Vì file gốc không có nhóm máu, ta random lại cho nhất quán nếu đang thiếu
                if p.blood_type == "None" or p.blood_type is None:
                    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
                    random.seed(int(case_id)) # Seed cố định theo ID để không bị đổi mỗi lần chạy
                    p.blood_type = random.choice(blood_types)
                    needs_update = True
                
                if p.device_id == "None" or p.device_id is None:
                    p.device_id = f"MON-{int(case_id):04d}"
                    needs_update = True

                if needs_update:
                    count_updated += 1
            else:
                print(f"   ⚠️ Không tìm thấy dữ liệu gốc cho Case {case_id} trong file CSV!")

        # 4. Lưu thay đổi
        if count_updated > 0:
            session.commit()
            print(f"\n✅ Đã cập nhật thành công thông tin cho {count_updated} bệnh nhân!")
        else:
            print("\n✅ Tất cả bệnh nhân đã có thông tin đầy đủ. Không cần cập nhật.")
            
    except Exception as e:
        session.rollback()
        print(f"❌ Lỗi: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    enrich_data()