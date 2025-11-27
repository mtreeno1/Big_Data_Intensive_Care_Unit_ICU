"""
WebSocket Alert Server
Broadcasts real-time alerts to connected dashboard clients
"""
import asyncio
import json
import logging
import websockets
from kafka import KafkaConsumer
from typing import Set
from datetime import datetime
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertWebSocketServer:
    """WebSocket server for broadcasting alerts to multiple clients"""
    
    def __init__(self, kafka_bootstrap_servers: str = 'localhost:9092',
                 kafka_topic: str = 'patient-alerts',
                 host: str = 'localhost',
                 port: int = 8765):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.alert_history = deque(maxlen=50)  # Keep last 50 alerts
        self.consumer = None
        
    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send recent alert history to new client
        for alert in self.alert_history:
            try:
                await websocket.send(json.dumps(alert))
            except Exception as e:
                logger.error(f"Error sending history to client: {e}")
    
    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_alert(self, alert_data: dict):
        """Broadcast alert to all connected clients"""
        if not self.clients:
            logger.debug("No clients connected to broadcast alert")
            return
        
        # Add to history
        self.alert_history.append(alert_data)
        
        message = json.dumps(alert_data)
        disconnected_clients = set()
        
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            await self.unregister_client(client)
        
        logger.info(f"Alert broadcasted to {len(self.clients)} clients")
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle WebSocket client connection"""
        await self.register_client(websocket)
        
        try:
            # Keep connection alive and handle incoming messages
            async for message in websocket:
                logger.debug(f"Received message from client: {message}")
                # Handle client acknowledgments or other messages if needed
                try:
                    data = json.loads(message)
                    if data.get('type') == 'ping':
                        await websocket.send(json.dumps({'type': 'pong'}))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed normally")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def consume_kafka_alerts(self):
        """Consume alerts from Kafka and broadcast to WebSocket clients"""
        logger.info(f"Starting Kafka consumer for topic: {self.kafka_topic}")
        
        # Run Kafka consumer in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        try:
            self.consumer = KafkaConsumer(
                self.kafka_topic,
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',  # Only get new alerts
                enable_auto_commit=True,
                group_id='alert-websocket-server'
            )
            
            logger.info("Kafka consumer connected successfully")
            
            # Process messages
            for message in self.consumer:
                alert_data = message.value
                logger.info(f"Received alert from Kafka: {alert_data.get('patient_id')} - {alert_data.get('risk_level')}")
                
                # Broadcast to all WebSocket clients
                await self.broadcast_alert(alert_data)
                
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
    
    async def start(self):
        """Start the WebSocket server and Kafka consumer"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        # Start WebSocket server
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"WebSocket server listening on ws://{self.host}:{self.port}")
            
            # Start Kafka consumer in background
            kafka_task = asyncio.create_task(self.consume_kafka_alerts())
            
            try:
                # Keep server running
                await asyncio.Future()  # Run forever
            except KeyboardInterrupt:
                logger.info("Shutting down server...")
                kafka_task.cancel()
            except Exception as e:
                logger.error(f"Server error: {e}")
                kafka_task.cancel()


async def main():
    """Main entry point"""
    server = AlertWebSocketServer(
        kafka_bootstrap_servers='localhost:9092',
        kafka_topic='patient-alerts',
        host='localhost',
        port=8765
    )
    
    await server.start()


if __name__ == '__main__':
    asyncio.run(main())
