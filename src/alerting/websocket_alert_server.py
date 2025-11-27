"""
Real-time Alert WebSocket Server
Broadcasts critical alerts to all connected clients
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from kafka import KafkaConsumer
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertManager:
    """Manage WebSocket connections and alert broadcasting"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.alert_history = []
        self.max_history = 100
    
    async def connect(self, websocket: WebSocket):
        """Register new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ Client connected. Total: {len(self.active_connections)}")
        
        # Send recent alerts to new client
        if self.alert_history:
            await websocket.send_json({
                "type": "history",
                "alerts": self.alert_history[-10:]  # Last 10 alerts
            })
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"❌ Client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast_alert(self, alert_data: dict):
        """Broadcast alert to all connected clients"""
        # Add timestamp
        alert_data["broadcast_time"] = datetime.now().isoformat()
        
        # Store in history
        self.alert_history.append(alert_data)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        # Broadcast to all clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": "alert",
                    "data": alert_data
                })
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        self.active_connections -= disconnected
        
        logger.info(f"📢 Broadcast alert to {len(self.active_connections)} clients: "
                   f"{alert_data.get('patient_id')} - {alert_data.get('severity')}")
    
    def get_stats(self):
        """Get server statistics"""
        return {
            "active_connections": len(self.active_connections),
            "total_alerts": len(self.alert_history),
            "recent_alerts": self.alert_history[-5:] if self.alert_history else []
        }


# Create FastAPI app
app = FastAPI(title="ICU Alert WebSocket Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Alert manager instance
alert_manager = AlertManager()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "ICU Alert WebSocket Server",
        "stats": alert_manager.get_stats()
    }


@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    return alert_manager.get_stats()


@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts"""
    await alert_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        alert_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        alert_manager.disconnect(websocket)


def kafka_alert_listener():
    """Listen to Kafka alerts topic and broadcast via WebSocket"""
    logger.info("🎧 Starting Kafka alert listener...")
    
    try:
        consumer = KafkaConsumer(
            'patient-alerts',
            bootstrap_servers='localhost:9092',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='websocket-alert-broadcaster'
        )
        
        logger.info("✅ Connected to Kafka topic: patient-alerts")
        
        for message in consumer:
            alert_data = message.value
            
            # Broadcast to WebSocket clients (run in event loop)
            asyncio.run(alert_manager.broadcast_alert(alert_data))
    
    except Exception as e:
        logger.error(f"❌ Kafka listener error: {e}")


def start_kafka_listener():
    """Start Kafka listener in background thread"""
    thread = threading.Thread(target=kafka_alert_listener, daemon=True)
    thread.start()
    logger.info("✅ Kafka listener thread started")


@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup"""
    logger.info("🚀 Starting WebSocket Alert Server...")
    start_kafka_listener()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8765,
        log_level="info"
    )
