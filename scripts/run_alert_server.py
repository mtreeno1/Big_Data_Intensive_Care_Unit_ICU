#!/usr/bin/env python3
"""
Launch WebSocket Alert Server
Broadcasts alerts from Kafka to all connected dashboard clients
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from src.alerting.websocket_server import AlertWebSocketServer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    logger.info("🚀 Starting ICU Alert WebSocket Server...")
    
    server = AlertWebSocketServer(
        host='0.0.0.0',  # Listen on all interfaces
        port=8765,
        kafka_topic='patient-alerts'
    )
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("⚠️ Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down server...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Alert server stopped gracefully")
