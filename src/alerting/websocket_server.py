"""
FastAPI WebSocket Server for Real-time Alert Broadcasting
"""
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Set, Dict, List
import json
from datetime import datetime
import uvicorn

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ICU Alert WebSocket Server")

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.alert_queue: List[Dict] = []
        self.max_queue_size = 100
        
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"✅ New connection | Total: {len(self.active_connections)}")
        
        # Send recent alerts to new client
        if self.alert_queue:
            recent_alerts = self.alert_queue[-10:]  # Last 10 alerts
            await websocket.send_json({
                "type": "alert_history",
                "alerts": recent_alerts,
                "count": len(recent_alerts)
            })
    
    def disconnect(self, websocket: WebSocket):
        """Remove disconnected client"""
        self.active_connections.discard(websocket)
        logger.info(f"❌ Connection closed | Total: {len(self.active_connections)}")
    
    async def broadcast_alert(self, alert: Dict):
        """
        Broadcast alert to all connected clients
        
        Args:
            alert: Alert dictionary with structure:
                {
                    "alert_id": str,
                    "patient_id": str,
                    "patient_name": str,
                    "timestamp": str (ISO format),
                    "risk_level": str (CRITICAL/HIGH/MODERATE),
                    "risk_score": float,
                    "mews_score": int,
                    "vital_signs": dict,
                    "warnings": list,
                    "priority": int (1-5)
                }
        """
        # Add to queue
        self.alert_queue.append(alert)
        if len(self.alert_queue) > self.max_queue_size:
            self.alert_queue.pop(0)
        
        # Prepare message
        message = {
            "type": "alert",
            "data": alert,
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to all clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logger.info(f"📤 Sent {alert['risk_level']} alert to client: {alert['patient_id']}")
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
        
        logger.info(f"🚨 Alert broadcasted to {len(self.active_connections)} clients")
    
    async def send_heartbeat(self):
        """Send periodic heartbeat to keep connections alive"""
        message = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat(),
            "active_connections": len(self.active_connections)
        }
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


# Global connection manager
manager = ConnectionManager()


@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alerts
    
    Usage from JavaScript:
        const ws = new WebSocket("ws://localhost:8001/ws/alerts");
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "alert") {
                // Handle alert
                showPopup(data.data);
                playSound(data.data.priority);
            }
        };
    """
    await manager.connect(websocket)
    
    try:
        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            
            # Handle client messages (e.g., acknowledgment)
            try:
                message = json.loads(data)
                if message.get("type") == "ack":
                    logger.info(f"✅ Client acknowledged alert: {message.get('alert_id')}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/alerts/broadcast")
async def broadcast_alert_api(alert: Dict):
    """
    REST API endpoint to broadcast alert
    
    Called by Consumer when HIGH/CRITICAL alert detected
    
    Example usage:
        import requests
        requests.post("http://localhost:8001/api/alerts/broadcast", json=alert_dict)
    """
    await manager.broadcast_alert(alert)
    return {
        "status": "success",
        "alert_id": alert.get("alert_id"),
        "broadcasted_to": len(manager.active_connections)
    }


@app.get("/api/alerts/recent")
async def get_recent_alerts(limit: int = 10):
    """Get recent alerts from queue"""
    recent = manager.alert_queue[-limit:] if manager.alert_queue else []
    return {
        "alerts": recent,
        "count": len(recent),
        "total_in_queue": len(manager.alert_queue)
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "alerts_in_queue": len(manager.alert_queue),
        "timestamp": datetime.now().isoformat()
    }


# Background task for heartbeat
async def heartbeat_task():
    """Send heartbeat every 30 seconds"""
    while True:
        await asyncio.sleep(30)
        await manager.send_heartbeat()


@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(heartbeat_task())
    logger.info("🚀 WebSocket server started on ws://localhost:8001")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
