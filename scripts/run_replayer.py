# scripts/run_replayer.py (Đoạn cập nhật)
import time
import json
from datetime import datetime
from kafka import KafkaProducer
from src.mimic_etl.vitaldb_adapter import get_vitaldb_case_data # Import cái mới

# ... (Phần khởi tạo Kafka giữ nguyên) ...

# CHỌN DATA SOURCE
USE_VITALDB = True 

if USE_VITALDB:
    # Lấy dữ liệu online, không cần file CSV
    # Case 10 là một ca mẫu có tín hiệu tốt
    df = get_vitaldb_case_data(case_id=10, interval=1) 
    print("✅ Đã tải xong data từ VitalDB. Bắt đầu streaming...")
else:
    # Code cũ đọc từ file CSV MIMIC
    pass

# ... (Phần Loop gửi tin nhắn) ...
for index, row in df.iterrows():
    # Vì VitalDB interval = 1s, ta sleep 1 giây (hoặc chia cho speed factor)
    time.sleep(1.0 / SPEED_FACTOR) 
    
    message = {
        "patient_id": "VITALDB-010", # ID giả lập
        "timestamp": datetime.now().isoformat(),
        "vital_signs": {
            "heart_rate": row['heart_rate'],
            "spo2": row['spo2'],
            "bp_systolic": row['bp_systolic'],
             # ...
        }
    }
    producer.send(KAFKA_TOPIC, value=message)