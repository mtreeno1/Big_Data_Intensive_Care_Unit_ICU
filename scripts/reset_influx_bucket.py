import sys
import os
# Thêm đường dẫn để import config
sys.path.append(os.getcwd())

from config.config import settings
from influxdb_client import InfluxDBClient

def reset_bucket():
    # Kết nối InfluxDB
    client = InfluxDBClient(
        url=settings.INFLUX_URL,
        token=settings.INFLUX_TOKEN,
        org=settings.INFLUX_ORG
    )

    buckets_api = client.buckets_api()
    bucket_name = settings.INFLUX_BUCKET

    # 1. Xóa Bucket cũ (nếu có)
    print(f"🗑️ Đang tìm Bucket '{bucket_name}'...")
    bucket = buckets_api.find_bucket_by_name(bucket_name)

    if bucket:
        print(f"   -> Tìm thấy ID: {bucket.id}. Đang xóa...")
        buckets_api.delete_bucket(bucket)
        print("   ✅ Đã xóa Bucket cũ.")
    else:
        print("   -> Không tìm thấy Bucket cũ (Sạch sẽ).")

    # 2. Tạo Bucket mới
    print(f"🆕 Đang tạo lại Bucket '{bucket_name}'...")
    
    # --- ĐOẠN FIX LỖI ---
    org_api = client.organizations_api()
    
    # Lấy tất cả Org về rồi tự lọc (Tránh lỗi phiên bản thư viện)
    orgs = org_api.find_organizations()
    target_org = next((o for o in orgs if o.name == settings.INFLUX_ORG), None)

    if not target_org:
        print(f"❌ Lỗi: Không tìm thấy Organization có tên '{settings.INFLUX_ORG}'")
        print(f"   Danh sách Org hiện có: {[o.name for o in orgs]}")
        print("👉 Hãy kiểm tra lại file .env hoặc config.py")
        exit(1)
        
    print(f"   -> Tìm thấy Org ID: {target_org.id}")
    
    # Tạo bucket mới (Retention rule: 0 means infinite)
    buckets_api.create_bucket(bucket_name=bucket_name, org_id=target_org.id)

    print("✅ Hoàn tất! InfluxDB đã được reset thành công.")
    client.close()

if __name__ == "__main__":
    reset_bucket()