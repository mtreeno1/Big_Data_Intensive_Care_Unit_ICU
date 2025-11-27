"""
InfluxDB Storage Manager for time-series vital signs data
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from config.config import settings

logger = logging.getLogger(__name__)


class InfluxDBManager:
    """
    Manage InfluxDB operations for vital signs storage
    """
    
    def __init__(self):
        """Initialize InfluxDB client"""
        try:
            self.client = InfluxDBClient(
                url=settings.INFLUX_URL,
                token=settings.INFLUX_TOKEN,
                org=settings.INFLUX_ORG
            )
            
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            self.bucket = settings.INFLUX_BUCKET
            
            logger.info(f"✅ InfluxDB connected: {settings.INFLUX_URL}")
            
        except Exception as e:
            logger.error(f"❌ InfluxDB connection failed: {e}")
            raise
    
    def _flatten_vital_signs(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Flatten nested vital signs structure
        
        Handles:
        - Simple values: {'heart_rate': 72}
        - Nested dicts: {'heart_rate': {'value': 72}}
        - Blood pressure: {'blood_pressure': {'systolic': 120, 'diastolic': 80}}
        
        Returns:
            Flat dictionary with numeric values only
        """
        flattened = {}
        
        for key, value in data.items():
            # Skip None values
            if value is None:
                continue
            
            # Case 1: Already a number
            if isinstance(value, (int, float)):
                flattened[key] = float(value)
                continue
            
            # Case 2: String number
            if isinstance(value, str):
                try:
                    flattened[key] = float(value)
                    continue
                except ValueError:
                    logger.debug(f"Cannot convert string to float: {key}={value}")
                    continue
            
            # Case 3: Dict with 'value' key
            if isinstance(value, dict):
                # Blood pressure special case
                if key == 'blood_pressure' or ('systolic' in value and 'diastolic' in value):
                    if 'systolic' in value:
                        try:
                            flattened['blood_pressure_systolic'] = float(value['systolic'])
                        except (ValueError, TypeError):
                            pass
                    if 'diastolic' in value:
                        try:
                            flattened['blood_pressure_diastolic'] = float(value['diastolic'])
                        except (ValueError, TypeError):
                            pass
                    continue
                
                # Standard nested value
                if 'value' in value:
                    try:
                        flattened[key] = float(value['value'])
                        continue
                    except (ValueError, TypeError):
                        pass
                
                if 'mean' in value:
                    try:
                        flattened[key] = float(value['mean'])
                        continue
                    except (ValueError, TypeError):
                        pass
                
                # If no known pattern, log warning
                logger.debug(f"Unknown dict structure for {key}: {value}")
        
        return flattened
    
    def write_vital_signs(
        self, 
        patient_id: str, 
        data: Dict[str, Any],
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Write vital signs data to InfluxDB
        
        Args:
            patient_id: Patient identifier
            data: Dictionary of vital signs (can be nested)
            tags: Optional tags (e.g., {'risk_level': 'HIGH'})
            timestamp: Optional timestamp (defaults to now)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Flatten nested structures
            flat_data = self._flatten_vital_signs(data)
            
            if not flat_data:
                logger.warning(f"⚠️  No valid fields to write for {patient_id}")
                return False
            
            # Create point
            point = Point("vital_signs")
            
            # Add patient_id as tag
            point.tag("patient_id", patient_id)
            
            # Add additional tags
            if tags:
                for key, value in tags.items():
                    if value is not None:
                        point.tag(key, str(value))
            
            # Add fields
            for metric, value in flat_data.items():
                point.field(metric, float(value))
            
            # Set timestamp
            if timestamp:
                point.time(timestamp)
            
            # Write to InfluxDB
            self.write_api.write(
                bucket=self.bucket,
                org=settings.INFLUX_ORG,
                record=point
            )
            
            logger.debug(f"✅ Wrote {len(flat_data)} fields to InfluxDB for {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing to InfluxDB for {patient_id}: {e}")
            return False
    
    def write_risk_score(
        self,
        patient_id: str,
        risk_score: float,
        risk_level: str,
        mews_score: int,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Write risk assessment to InfluxDB
        """
        try:
            point = Point("risk_assessment") \
                .tag("patient_id", patient_id) \
                .tag("risk_level", risk_level) \
                .field("risk_score", float(risk_score)) \
                .field("mews_score", int(mews_score))
            
            if timestamp:
                point.time(timestamp)
            
            self.write_api.write(
                bucket=self.bucket,
                org=settings.INFLUX_ORG,
                record=point
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing risk score: {e}")
            return False
    
    def query_latest_vitals(self, patient_id: str, hours: int = 1):
        """
        Query latest vital signs for a patient
        """
        try:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r["_measurement"] == "vital_signs")
                |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(query)
            return result
            
        except Exception as e:
            logger.error(f"❌ Query error for {patient_id}: {e}")
            return None
    
    def close(self):
        """Close InfluxDB client"""
        try:
            self.client.close()
            logger.info("✅ InfluxDB connection closed")
        except Exception as e:
            logger.error(f"Error closing InfluxDB: {e}")


# Singleton instance
_influx_manager = None

def get_influx_manager() -> InfluxDBManager:
    """Get or create InfluxDB manager singleton"""
    global _influx_manager
    if _influx_manager is None:
        _influx_manager = InfluxDBManager()
    return _influx_manager