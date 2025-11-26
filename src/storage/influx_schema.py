"""
InfluxDB Schema and Writer for Time-Series Vital Signs Data
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)

class InfluxDBWriter:
    """Write vital signs data to InfluxDB with proper schema"""
    
    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str
    ):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        
        try:
            self.client = InfluxDBClient(url=url, token=token, org=org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            logger.info(f"✅ Connected to InfluxDB: {url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to InfluxDB: {e}")
            raise
    
    def write_vital_signs(self, reading: Dict) -> bool:
        """
        Write vital signs to InfluxDB with separate fields
        
        Schema:
            measurement: vital_signs
            tags: patient_id, device_id
            fields: heart_rate, spo2, temperature, respiratory_rate, 
                   blood_pressure_systolic, blood_pressure_diastolic
            timestamp: reading timestamp
        """
        try:
            # Extract vital signs
            vitals = reading.get("vital_signs", {})
            
            # ✅ Create point with MULTIPLE FIELDS (not single "value")
            point = Point("vital_signs") \
                .tag("patient_id", reading["patient_id"]) \
                .tag("device_id", reading.get("device_id", "unknown"))
            
            # ✅ Add each vital sign as SEPARATE FIELD
            if "heart_rate" in vitals:
                point = point.field("heart_rate", float(vitals["heart_rate"]))
            
            if "spo2" in vitals:
                point = point.field("spo2", float(vitals["spo2"]))
            
            if "temperature" in vitals:
                point = point.field("temperature", float(vitals["temperature"]))
            
            if "respiratory_rate" in vitals:
                point = point.field("respiratory_rate", float(vitals["respiratory_rate"]))
            
            # Blood pressure (split into systolic and diastolic)
            if "blood_pressure" in vitals:
                bp = vitals["blood_pressure"]
                if isinstance(bp, str) and "/" in bp:
                    # Format: "120/80"
                    systolic, diastolic = bp.split("/")
                    point = point.field("blood_pressure_systolic", float(systolic))
                    point = point.field("blood_pressure_diastolic", float(diastolic))
                elif isinstance(bp, dict):
                    # Format: {"systolic": 120, "diastolic": 80}
                    if "systolic" in bp:
                        point = point.field("blood_pressure_systolic", float(bp["systolic"]))
                    if "diastolic" in bp:
                        point = point.field("blood_pressure_diastolic", float(bp["diastolic"]))
            
            # Use reading timestamp
            timestamp = reading.get("timestamp")
            if timestamp:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                point = point.time(timestamp, WritePrecision.NS)
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, record=point)
            
            logger.debug(f"✅ Wrote vital signs for {reading['patient_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to write to InfluxDB: {e}", exc_info=True)
            return False
    
    def write_batch(self, readings: List[Dict]) -> int:
        """Write multiple readings in batch"""
        success_count = 0
        
        try:
            points = []
            for reading in readings:
                vitals = reading.get("vital_signs", {})
                
                point = Point("vital_signs") \
                    .tag("patient_id", reading["patient_id"]) \
                    .tag("device_id", reading.get("device_id", "unknown"))
                
                # Add fields
                if "heart_rate" in vitals:
                    point = point.field("heart_rate", float(vitals["heart_rate"]))
                if "spo2" in vitals:
                    point = point.field("spo2", float(vitals["spo2"]))
                if "temperature" in vitals:
                    point = point.field("temperature", float(vitals["temperature"]))
                if "respiratory_rate" in vitals:
                    point = point.field("respiratory_rate", float(vitals["respiratory_rate"]))
                
                # Blood pressure
                if "blood_pressure" in vitals:
                    bp = vitals["blood_pressure"]
                    if isinstance(bp, str) and "/" in bp:
                        systolic, diastolic = bp.split("/")
                        point = point.field("blood_pressure_systolic", float(systolic))
                        point = point.field("blood_pressure_diastolic", float(diastolic))
                    elif isinstance(bp, dict):
                        if "systolic" in bp:
                            point = point.field("blood_pressure_systolic", float(bp["systolic"]))
                        if "diastolic" in bp:
                            point = point.field("blood_pressure_diastolic", float(bp["diastolic"]))
                
                timestamp = reading.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    point = point.time(timestamp, WritePrecision.NS)
                
                points.append(point)
            
            self.write_api.write(bucket=self.bucket, record=points)
            success_count = len(points)
            logger.info(f"✅ Batch wrote {success_count} readings")
            
        except Exception as e:
            logger.error(f"❌ Batch write failed: {e}", exc_info=True)
        
        return success_count
    
    def close(self):
        """Close InfluxDB connection"""
        try:
            self.client.close()
            logger.info("✅ InfluxDB connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing InfluxDB: {e}")