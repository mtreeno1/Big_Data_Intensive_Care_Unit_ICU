"""
Monitoring and Metrics
Track consumer and processing performance
"""

import time
import logging
from typing import Dict, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor consumer and processor performance"""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize performance monitor
        
        Args:
            window_size: Number of measurements to keep for rolling averages
        """
        self.window_size = window_size
        
        # Metrics storage
        self.processing_times = deque(maxlen=window_size)
        self.message_count = 0
        self.error_count = 0
        self.start_time = time.time()
        
        # Partition metrics
        self.partition_offsets: Dict[int, int] = {}
        self.partition_lags: Dict[int, int] = {}
        
        logger.info(f"✅ PerformanceMonitor initialized (window: {window_size})")
    
    def record_processing_time(self, duration_ms: float):
        """Record processing time for a message"""
        self.processing_times.append(duration_ms)
        self.message_count += 1
    
    def record_error(self):
        """Record processing error"""
        self.error_count += 1
    
    def update_partition_metrics(self, partition: int, offset: int, lag: int):
        """Update partition-level metrics"""
        self.partition_offsets[partition] = offset
        self.partition_lags[partition] = lag
    
    def get_metrics(self) -> Dict:
        """Get current performance metrics"""
        elapsed_time = time.time() - self.start_time
        
        metrics = {
            'uptime_seconds': elapsed_time,
            'messages_processed': self.message_count,
            'errors': self.error_count,
            'success_rate': self._calculate_success_rate(),
            'throughput_msg_per_sec': self.message_count / elapsed_time if elapsed_time > 0 else 0,
        }
        
        if self.processing_times:
            metrics.update({
                'avg_processing_time_ms': sum(self.processing_times) / len(self.processing_times),
                'min_processing_time_ms': min(self.processing_times),
                'max_processing_time_ms': max(self.processing_times),
            })
        
        if self.partition_offsets:
            metrics['partitions'] = {
                'count': len(self.partition_offsets),
                'offsets': dict(self.partition_offsets),
                'total_lag': sum(self.partition_lags.values()),
                'max_lag': max(self.partition_lags.values()) if self.partition_lags else 0
            }
        
        return metrics
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage"""
        total = self.message_count + self.error_count
        if total == 0:
            return 100.0
        return (self.message_count / total) * 100
    
    def log_metrics(self):
        """Log current metrics"""
        metrics = self.get_metrics()
        
        logger.info("=" * 60)
        logger.info("📊 PERFORMANCE METRICS")
        logger.info("=" * 60)
        logger.info(f"⏱️  Uptime: {metrics['uptime_seconds']:.1f}s")
        logger.info(f"✅ Processed: {metrics['messages_processed']}")
        logger.info(f"❌ Errors: {metrics['errors']}")
        logger.info(f"🎯 Success Rate: {metrics['success_rate']:.1f}%")
        logger.info(f"📈 Throughput: {metrics['throughput_msg_per_sec']:.1f} msg/sec")
        
        if 'avg_processing_time_ms' in metrics:
            logger.info(f"⚡ Avg Processing: {metrics['avg_processing_time_ms']:.2f}ms")
        
        if 'partitions' in metrics:
            logger.info(f"📦 Partitions: {metrics['partitions']['count']}")
            logger.info(f"⏳ Total Lag: {metrics['partitions']['total_lag']}")
        
        logger.info("=" * 60)
    
    def should_log(self, interval_seconds: int = 60) -> bool:
        """Check if it's time to log metrics"""
        elapsed = time.time() - self.start_time
        return int(elapsed) % interval_seconds == 0 and self.message_count > 0