"""
Save All Patient Groups
Tự động lọc và lưu danh sách bệnh nhân theo từng phân loại cụ thể ra các file CSV riêng biệt.
"""
import pandas as pd
import os

# Cấu hình đường dẫn
DATA_DIR = "data"
INPUT_FILE = os.path.join(DATA_DIR, "clinical_data.csv")

def load_data():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Không tìm thấy file: {INPUT_FILE}")
        return None
    print("🔄 Đang đọc dữ liệu gốc...")
    return pd.read_csv(INPUT_FILE)

def filter_and_save(df):
    # Định nghĩa các bộ lọc
    filters = {
        "critical": {
            "desc": "Nguy kịch (ASA >= 4)",
            "condition": lambda d: d['asa'] >= 4
        },
        "transplant": {
            "desc": "Ghép tạng (Tim, Gan, Phổi, Thận)",
            "condition": lambda d: d['opname'].str.contains('transplantation|transplant', case=False, na=False)
        },
        "cardio": {
            "desc": "Phẫu thuật Tim mạch & Lồng ngực",
            "condition": lambda d: d['department'].str.contains('Thoracic', case=False, na=False)
        },
        "long_surgery": {
            "desc": "Đại phẫu (> 6 tiếng)",
            "condition": lambda d: (d['caseend'] - d['casestart']) / 3600 >= 6
        }
    }

    print(f"\n{'='*60}")
    print(f"BẮT ĐẦU PHÂN LOẠI VÀ LƯU FILE")
    print(f"{'='*60}")

    summary = []

    for key, rule in filters.items():
        # Áp dụng bộ lọc
        filtered_df = df[rule["condition"](df)].copy()
        
        # Sắp xếp ưu tiên ca nặng
        filtered_df = filtered_df.sort_values(by=['asa', 'age'], ascending=False)
        
        # Lưu file
        output_filename = f"patients_{key}.csv"
        output_path = os.path.join(DATA_DIR, output_filename)
        filtered_df.to_csv(output_path, index=False)
        
        # In thông báo
        count = len(filtered_df)
        print(f"✅ [{key.upper()}] - {rule['desc']}")
        print(f"   👉 Tìm thấy: {count} bệnh nhân")
        print(f"   💾 Đã lưu tại: {output_path}")
        print("-" * 60)
        
        summary.append({"Group": key, "Count": count, "File": output_filename})

    return summary

if __name__ == "__main__":
    df = load_data()
    if df is not None:
        filter_and_save(df)
        print("\n🎉 HOÀN TẤT!")