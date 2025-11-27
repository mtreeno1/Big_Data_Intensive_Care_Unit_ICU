"""
<<<<<<< HEAD
InfluxDB Schema and Writer
Handles time-series storage for patient vital signs
"""

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class InfluxDBWriter:
    """Write vital signs to InfluxDB"""
    
    def __init__(self, url: str, token: str, org: str, bucket: str):
        """
        Initialize InfluxDB writer
        
        Args:
            url: InfluxDB URL
            token: Authentication token
            org: Organization name
            bucket: Bucket name for vital signs
        """
=======
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
>>>>>>> 5518597 (Initial commit: reset and push to master)
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
<<<<<<< HEAD
        Write patient vital signs to InfluxDB
        
        Args:
            reading: Patient reading from Kafka
            
        Returns:
            True if successful, False otherwise
        """
        try:
            patient_id = reading['patient_id']
            timestamp = reading['timestamp']
            vitals = reading['vital_signs']
            profile = reading.get('profile', 'UNKNOWN')
            
            # Create InfluxDB point for each vital sign
            points = []
            
            # Heart Rate
            points.append(
                Point("vital_signs")
                .tag("patient_id", patient_id)
                .tag("profile", profile)
                .tag("vital_type", "heart_rate")
                .field("value", float(vitals['heart_rate']))
                .time(timestamp, WritePrecision.NS)
            )
            
            # SpO2
            points.append(
                Point("vital_signs")
                .tag("patient_id", patient_id)
                .tag("profile", profile)
                .tag("vital_type", "spo2")
                .field("value", float(vitals['spo2']))
                .time(timestamp, WritePrecision.NS)
            )
            
            # Blood Pressure - Systolic
            points.append(
                Point("vital_signs")
                .tag("patient_id", patient_id)
                .tag("profile", profile)
                .tag("vital_type", "systolic_bp")
                .field("value", float(vitals['blood_pressure']['systolic']))
                .time(timestamp, WritePrecision.NS)
            )
            
            # Blood Pressure - Diastolic
            points.append(
                Point("vital_signs")
                .tag("patient_id", patient_id)
                .tag("profile", profile)
                .tag("vital_type", "diastolic_bp")
                .field("value", float(vitals['blood_pressure']['diastolic']))
                .time(timestamp, WritePrecision.NS)
            )
            
            # Temperature
            points.append(
                Point("vital_signs")
                .tag("patient_id", patient_id)
                .tag("profile", profile)
                .tag("vital_type", "temperature")
                .field("value", float(vitals['temperature']))
                .time(timestamp, WritePrecision.NS)
            )
            
            # Respiratory Rate
            points.append(
                Point("vital_signs")
                .tag("patient_id", patient_id)
                .tag("profile", profile)
                .tag("vital_type", "respiratory_rate")
                .field("value", float(vitals['respiratory_rate']))
                .time(timestamp, WritePrecision.NS)
            )
            
            # Write all points
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger.debug(f"✅ Wrote {len(points)} points for patient {patient_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to write to InfluxDB: {e}")
            return False
    
    def write_aggregated_data(self, patient_id: str, window: str, 
                             aggregates: Dict, timestamp: str) -> bool:
        """
        Write aggregated statistics
        
        Args:
            patient_id: Patient identifier
            window: Time window (1m, 5m, 1h)
            aggregates: Dictionary of aggregated values
            timestamp: Timestamp for the aggregation
            
        Returns:
            True if successful
        """
        try:
            points = []
            
            for vital_type, stats in aggregates.items():
                point = (
                    Point("vital_signs_aggregated")
                    .tag("patient_id", patient_id)
                    .tag("vital_type", vital_type)
                    .tag("window", window)
                    .field("mean", float(stats.get('mean', 0)))
                    .field("min", float(stats.get('min', 0)))
                    .field("max", float(stats.get('max', 0)))
                    .field("std", float(stats.get('std', 0)))
                    .field("count", int(stats.get('count', 0)))
                    .time(timestamp, WritePrecision.NS)
                )
                points.append(point)
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger.debug(f"✅ Wrote aggregated data for patient {patient_id}, window {window}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to write aggregated data: {e}")
            return False
=======
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
>>>>>>> 5518597 (Initial commit: reset and push to master)
    
    def close(self):
        """Close InfluxDB connection"""
        try:
<<<<<<< HEAD
            self.write_api.close()
            self.client.close()
            logger.info("✅ InfluxDB connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing InfluxDB connection: {e}")
=======
            self.client.close()
            logger.info("✅ InfluxDB connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing InfluxDB: {e}")
>>>>>>> 5518597 (Initial commit: reset and push to master)
