"""
InfluxDB Storage Manager for time-series vital signs data
SYNCHRONOUS WRITE VERSION (Fix for "Empty Database" issue)
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS # <--- QUAN TRỌNG NHẤT

from config.config import settings

logger = logging.getLogger(__name__)

class InfluxDBManager:
    """
    Manage InfluxDB operations for vital signs storage
    """
    
    def __init__(self):
        """Initialize InfluxDB client with SYNCHRONOUS write"""
        try:
            self.client = InfluxDBClient(
                url=settings.INFLUX_URL,
                token=settings.INFLUX_TOKEN,
                org=settings.INFLUX_ORG
            )
            
            # --- FIX QUAN TRỌNG: Dùng SYNCHRONOUS để ghi ngay lập tức ---
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            
            self.query_api = self.client.query_api()
            self.bucket = settings.INFLUX_BUCKET
            
            logger.info(f"✅ InfluxDB connected: {settings.INFLUX_URL}")
            
        except Exception as e:
            logger.error(f"❌ InfluxDB connection failed: {e}")
            raise
    
    def _flatten_vital_signs(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Flatten nested structure (Giữ nguyên logic cũ)"""
        flattened = {}
        for key, value in data.items():
            if value is None: continue
            
            # Case: Number
            if isinstance(value, (int, float)):
                flattened[key] = float(value)
            # Case: String number
            elif isinstance(value, str) and value.replace('.','',1).isdigit():
                flattened[key] = float(value)
            # Case: Dict (BP)
            elif isinstance(value, dict):
                if key == 'blood_pressure':
                    if 'systolic' in value: flattened['bp_systolic'] = float(value['systolic'])
                    if 'diastolic' in value: flattened['bp_diastolic'] = float(value['diastolic'])
                elif 'value' in value:
                    flattened[key] = float(value['value'])
        return flattened
    
    def write_vital_signs(
        self, 
        patient_id: str, 
        data: Dict[str, Any],
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Write data to InfluxDB"""
        try:
            # 1. Làm phẳng dữ liệu
            flat_data = self._flatten_vital_signs(data)
            if not flat_data:
                return False
            
            # 2. Tạo Point
            point = Point("vital_signs").tag("patient_id", patient_id)
            
            if tags:
                for k, v in tags.items():
                    if v: point.tag(k, str(v))
            
            for k, v in flat_data.items():
                point.field(k, v)
            
            # Nếu bản tin có timestamp (từ VitalDB), dùng nó. Nếu không dùng giờ server.
            # Lưu ý: InfluxDB rất nhạy cảm với timestamp quá khứ/tương lai
            if timestamp:
                point.time(timestamp) 
            else:
                point.time(datetime.utcnow())

            # 3. Ghi ngay lập tức (Synchronous)
            self.write_api.write(
                bucket=self.bucket,
                org=settings.INFLUX_ORG,
                record=point
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing to InfluxDB: {e}")
            return False

    def close(self):
        if self.client:
            self.client.close()

# Singleton
_influx_manager = None
def get_influx_manager():
    global _influx_manager
    if _influx_manager is None:
        _influx_manager = InfluxDBManager()
    return _influx_manager