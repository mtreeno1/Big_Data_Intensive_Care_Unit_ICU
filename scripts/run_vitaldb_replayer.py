# scripts/run_vitaldb_replayer.py
import time
import json
import vitaldb
import pandas as pd
import numpy as np
from datetime import datetime
from kafka import KafkaProducer

# --- CẤU HÌNH ---
KAFKA_SERVER = 'localhost:9092'
KAFKA_TOPIC = 'patient-vital-signs'
SPEED_FACTOR = 5  # Tốc độ phát lại (1 giây thực tế = 5 giây dữ liệu). Đặt 1 để chạy real-time.
CASE_ID = 10      # Chọn Case số 10 (Dữ liệu khá đẹp và đầy đủ)
PATIENT_ID_SIM = "VITALDB-010" # ID giả lập cho hệ thống ICU của bạn

# Mapping: Tên trong VitalDB -> Tên trong hệ thống ICU của bạn
TRACKS_MAPPING = {
    'SNUADC/HR': 'heart_rate',
    'SNUADC/SPO2': 'spo2',
    'SNUADC/ART_SBP': 'blood_pressure_systolic', # Huyết áp xâm lấn
    'SNUADC/ART_DBP': 'blood_pressure_diastolic',
    'Primus/RR_CO2': 'respiratory_rate', # Nhịp thở từ máy gây mê
    'Primus/TEMP_BLD': 'temperature'      # Nhiệt độ máu
}

def setup_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=[KAFKA_SERVER],
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

def fetch_vitaldb_data(case_id):
    """Tải dữ liệu từ VitalDB server"""
    print(f"📥 Đang tải dữ liệu Case {case_id} từ VitalDB (có thể mất vài giây)...")
    
    # Lấy danh sách track cần thiết
    track_names = list(TRACKS_MAPPING.keys())
    
    # interval=1: Lấy mẫu 1 giây/lần
    vf = vitaldb.load_case(case_id, track_names, interval=1)
    
    # Chuyển sang DataFrame
    df = pd.DataFrame(vf, columns=track_names)
    
    # Đổi tên cột cho giống hệ thống của bạn
    df.rename(columns=TRACKS_MAPPING, inplace=True)
    
    # Loại bỏ các dòng đầu tiên nếu toàn NaN (lúc chưa gắn máy)
    df.dropna(how='all', inplace=True)
    
    print(f"✅ Đã tải xong! Tổng cộng: {len(df)} dòng dữ liệu.")
    return df

def run_replay():
    producer = setup_kafka_producer()
    df = fetch_vitaldb_data(CASE_ID)
    
    print(f"🚀 Bắt đầu Stream dữ liệu (Speed: x{SPEED_FACTOR})...")
    print("Nhấn Ctrl+C để dừng.")

    try:
        # Loop qua từng dòng dữ liệu
        for i, row in df.iterrows():
            start_time = time.time()
            
            # 1. Tạo Message Payload
            # Lưu ý: Cần convert numpy float sang python float để JSON không lỗi
            vital_signs = {}
            for col in TRACKS_MAPPING.values():
                val = row.get(col)
                if pd.notna(val): # Chỉ gửi giá trị không phải NaN
                    # Xử lý riêng cho BP (Hệ thống bạn dùng nested dict cho BP đúng không?)
                    if 'blood_pressure' in col:
                        # Logic gộp BP systolic/diastolic vào dictionary nếu cần
                        # Ở đây tôi gửi phẳng, Consumer của bạn cần map lại hoặc tôi map ngay tại đây:
                        pass 
                    else:
                        vital_signs[col] = float(val)
            
            # Xử lý riêng BP để khớp với format JSON của bạn ở đầu bài: 
            # "blood_pressure": {"systolic": 140, "diastolic": 95}
            if pd.notna(row.get('blood_pressure_systolic')) and pd.notna(row.get('blood_pressure_diastolic')):
                vital_signs['blood_pressure'] = {
                    "systolic": int(row['blood_pressure_systolic']),
                    "diastolic": int(row['blood_pressure_diastolic'])
                }

            # Nếu dòng này không có data gì (máy lỏng dây), bỏ qua
            if not vital_signs:
                continue

            message = {
                "patient_id": PATIENT_ID_SIM,
                "device_id": f"DEV-{PATIENT_ID_SIM}",
                "timestamp": datetime.now().isoformat(),
                "vital_signs": vital_signs,
                "metadata": {
                    "source": "VitalDB",
                    "case_id": CASE_ID,
                    "risk_profile": "UNKNOWN" # Để Consumer tự tính
                }
            }

            # 2. Gửi vào Kafka
            producer.send(KAFKA_TOPIC, value=message)
            
            # Log nhẹ ra màn hình để biết đang chạy
            if i % 10 == 0: # 10 dòng in 1 lần cho đỡ spam
                print(f"Sent [{i}/{len(df)}] HR: {vital_signs.get('heart_rate')} | SpO2: {vital_signs.get('spo2')}")

            # 3. Giả lập thời gian thực (Sleep)
            # Nếu Speed = 1, sleep 1 giây. Speed = 5, sleep 0.2 giây
            process_time = time.time() - start_time
            sleep_time = (1.0 / SPEED_FACTOR) - process_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n🛑 Đã dừng Replay.")
    finally:
        producer.close()

if __name__ == "__main__":
    run_replay()