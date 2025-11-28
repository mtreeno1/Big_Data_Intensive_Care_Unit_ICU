import threading
import time
import json
import vitaldb
import pandas as pd
import numpy as np
from datetime import datetime
from kafka import KafkaProducer

# CẤU HÌNH
KAFKA_SERVER = 'localhost:9092'
KAFKA_TOPIC = 'patient-vital-signs'
SPEED_FACTOR = 10  

# Danh sách bệnh nhân
TARGET_CASES = {
    3962: "ICU-003962",  
    1926: "ICU-001926", 
    5175: "ICU-005175", 
    5603: "ICU-005603",
    1835: "ICU-001835",
    5262: "ICU-005262",
    4009: "ICU-004009",
    4744: "ICU-004744",
    4898: "ICU-004898",
    5753: "ICU-005753",
    1229: "ICU-001229" 
}

# Mapping
TRACKS_MAPPING = {
    'SNUADC/HR': 'heart_rate', 'Solar8000/HR': 'heart_rate',
    'SNUADC/SPO2': 'spo2', 'Solar8000/PLETH_SPO2': 'spo2',
    'SNUADC/ART_SBP': 'blood_pressure_systolic', 'Solar8000/ART_SBP': 'blood_pressure_systolic',
    'SNUADC/ART_DBP': 'blood_pressure_diastolic', 'Solar8000/ART_DBP': 'blood_pressure_diastolic',
    'Solar8000/BT': 'temperature', 'Primus/TEMP_BLD': 'temperature',
    'Solar8000/RR': 'respiratory_rate', 'Primus/RR_CO2': 'respiratory_rate'
}

def stream_one_patient(case_id, patient_id):
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_SERVER],
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )
    
    print(f"📥 [Patient {patient_id}] Đang tải Case {case_id}...")
    
    # 1. Tải dữ liệu
    vf = vitaldb.load_case(case_id, list(TRACKS_MAPPING.keys()), 1)
    raw_df = pd.DataFrame(vf, columns=TRACKS_MAPPING.keys())
    
    # 2. Gộp cột (Coalesce)
    df = pd.DataFrame()
    for target in set(TRACKS_MAPPING.values()):
        cols = [k for k, v in TRACKS_MAPPING.items() if v == target]
        series = pd.Series(np.nan, index=raw_df.index)
        for c in cols:
            if c in raw_df.columns:
                series = series.fillna(raw_df[c])
        df[target] = series

    # 3. LỌC BỎ DỮ LIỆU RÁC (QUAN TRỌNG NHẤT)
    initial_len = len(df)
    # Loại bỏ dòng nếu HR hoặc SpO2 bị NaN (trống)
    df = df.dropna(subset=['heart_rate', 'spo2'])
    
    print(f"✅ [Patient {patient_id}] Sẵn sàng stream! (Lọc {initial_len} -> {len(df)} dòng sạch)")

    # 4. Stream Loop
    count = 0
    for _, row in df.iterrows():
        # Kiểm tra lần cuối (Double Check)
        if pd.isna(row['heart_rate']): continue

        msg = {
            "patient_id": patient_id,
            # SỬA DÒNG NÀY: Dùng UTC để đồng bộ với InfluxDB
            "timestamp": datetime.utcnow().isoformat(), 
            "vital_signs": row.replace({np.nan: None}).to_dict()
        }
        
        producer.send(KAFKA_TOPIC, value=msg)
        count += 1
        
        # Log mỗi 50 dòng để đỡ spam
        if count % 50 == 0:
            print(f"   🚀 [{patient_id}] Sent HR: {row['heart_rate']} | SpO2: {row['spo2']}")
            
        time.sleep(1.0 / SPEED_FACTOR)

def main():
    threads = []
    print(f"🔥 Kích hoạt Replayer Đa luồng (Speed x{SPEED_FACTOR})...")
    
    for cid, pid in TARGET_CASES.items():
        t = threading.Thread(target=stream_one_patient, args=(cid, pid))
        t.start()
        threads.append(t)
        time.sleep(1)
        
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()