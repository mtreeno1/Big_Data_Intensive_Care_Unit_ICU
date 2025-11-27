import sys
import os
# Thêm thư mục gốc vào đường dẫn tìm kiếm
sys.path.append(os.getcwd()) 

from src.storage.influx_storage import InfluxDBManager

influx = InfluxDBManager()
print("🔍 Đang kiểm tra dữ liệu trong InfluxDB...")

# Lấy dữ liệu 1 giờ qua của bất kỳ ai
query = f'''
from(bucket: "{influx.bucket}")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "vital_signs")
  |> limit(n: 5)
'''
result = influx.query_api.query(query)

if not result:
    print("❌ InfluxDB TRỐNG RỖNG! Consumer chưa ghi được dòng nào.")
else:
    print("✅ InfluxDB ĐÃ CÓ DỮ LIỆU!")
    for table in result:
        for record in table.records:
            print(f"   - Time: {record.get_time()} | Patient: {record.values.get('patient_id')} | {record.get_field()}: {record.get_value()}")

influx.close()