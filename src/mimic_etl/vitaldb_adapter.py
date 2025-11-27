# src/mimic_etl/vitaldb_adapter.py
import vitaldb
import pandas as pd
import numpy as np

def get_vitaldb_case_data(case_id=1, interval=1):
    """
    Tải dữ liệu 1 ca phẫu thuật từ VitalDB Online
    """
    # Các track quan trọng tương đương ICU
    track_names = [
        'SNUADC/HR',       # Nhịp tim
        'SNUADC/SPO2',     # SpO2
        'SNUADC/ART_SBP',  # Huyết áp tâm thu (Xâm lấn)
        'SNUADC/ART_DBP',  # Huyết áp tâm trương
        'Primus/CO2'       # EtCO2 (Thường dùng trong gây mê/thở máy)
    ]
    
    print(f"📥 Đang tải Case {case_id} từ VitalDB server...")
    
    # Tải dữ liệu về dạng Numpy
    # interval=1 nghĩa là lấy mẫu 1 giây 1 lần (Rất tốt cho Kafka)
    vf = vitaldb.load_case(case_id, track_names, interval)
    
    # Chuyển sang Pandas DataFrame cho dễ xử lý
    df = pd.DataFrame(vf, columns=['heart_rate', 'spo2', 'bp_systolic', 'bp_diastolic', 'etco2'])
    
    # Loại bỏ các dòng NaN (lúc chưa gắn máy)
    df = df.dropna()
    
    # Thêm cột thời gian giả lập (để Replayer dùng)
    # Vì vitaldb không trả về datetime thực, ta chỉ cần biết thứ tự dòng
    return df

if __name__ == "__main__":
    # Test thử
    df = get_vitaldb_case_data(10)
    print(df.head())
    print(f"Số lượng bản ghi: {len(df)}")