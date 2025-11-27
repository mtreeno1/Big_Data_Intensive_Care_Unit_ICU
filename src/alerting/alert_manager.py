"""
Multi-Channel Alert System (Email, Slack, SMS, WebSocket)
"""
import logging
from typing import Dict, List
import redis
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AlertManager:
    """Manage real-time alerts with deduplication"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.alert_ttl = 300  # 5 minutes cooldown
    
    def send_alert(self, alert: Dict) -> bool:
        """
        Send alert through multiple channels
        
        Deduplication: Don't send same alert within cooldown period
        """
        patient_id = alert["patient_id"]
        alert_key = f"alert:{patient_id}:{alert['alert_type']}"
        
        # ✅ Check if alert already sent recently
        if self.redis_client.exists(alert_key):
            logger.debug(f"⏭️  Alert cooldown active for {patient_id}, skipping")
            return False
        
        # ✅ Send to channels
        channels_sent = []
        
        # 1. Dashboard (WebSocket)
        if self._send_to_dashboard(alert):
            channels_sent.append("dashboard")
        
        # 2. Slack
        if alert["risk_level"] in ["HIGH", "CRITICAL"]:
            if self._send_to_slack(alert):
                channels_sent.append("slack")
        
        # 3. Email (critical only)
        if alert["risk_level"] == "CRITICAL":
            if self._send_email(alert):
                channels_sent.append("email")
        
        # ✅ Store in Redis for deduplication
        self.redis_client.setex(alert_key, self.alert_ttl, json.dumps(alert))
        
        logger.info(f"🚨 Alert sent for {patient_id} via {channels_sent}")
        return len(channels_sent) > 0
    
    def _send_to_dashboard(self, alert: Dict) -> bool:
        """Send to WebSocket/dashboard"""
        try:
            # Publish to Redis pub/sub for dashboard
            self.redis_client.publish("alerts", json.dumps(alert))
            return True
        except Exception as e:
            logger.error(f"❌ Dashboard alert failed: {e}")
            return False
    
    def _send_to_slack(self, alert: Dict) -> bool:
        """Send to Slack webhook"""
        # TODO: Implement Slack webhook
        logger.info(f"📢 Slack: {alert['message']}")
        return True
    
    def _send_email(self, alert: Dict) -> bool:
        """Send email notification"""
        # TODO: Implement email sending
        logger.info(f"📧 Email: {alert['message']}")
        return True
    
    def get_recent_alerts(self, patient_id: str = None, limit: int = 50) -> List[Dict]:
        """Get recent alerts from Redis"""
        # TODO: Implement alert history retrieval
        return []