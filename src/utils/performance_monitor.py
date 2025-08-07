import time
import asyncio
from typing import Dict, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Performance monitoring utility for tracking metrics and bottlenecks"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.response_times = defaultdict(list)
    
    def start_timer(self, operation: str, request_id: Optional[str] = None):
        """Start timing an operation"""
        key = f"{operation}_{request_id}" if request_id else operation
        self.start_times[key] = time.perf_counter()
    
    def end_timer(self, operation: str, request_id: Optional[str] = None):
        """End timing an operation and record the duration"""
        key = f"{operation}_{request_id}" if request_id else operation
        if key in self.start_times:
            duration = time.perf_counter() - self.start_times[key]
            self.response_times[operation].append(duration)
            self.metrics[operation].append(duration)
            del self.start_times[key]
    
    def record_request(self, endpoint: str):
        """Record a request to an endpoint"""
        self.request_counts[endpoint] += 1
    
    def record_error(self, endpoint: str, error_type: str):
        """Record an error"""
        self.error_counts[f"{endpoint}_{error_type}"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        stats = {
            "request_counts": dict(self.request_counts),
            "error_counts": dict(self.error_counts),
            "response_times": {}
        }
        
        for operation, times in self.response_times.items():
            if times:
                stats["response_times"][operation] = {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times) * 1000,
                    "min_ms": min(times) * 1000,
                    "max_ms": max(times) * 1000,
                    "p95_ms": sorted(times)[int(len(times) * 0.95)] * 1000 if len(times) > 0 else 0
                }
        
        return stats
    
    def get_slow_operations(self, threshold_ms: float = 1000) -> Dict[str, float]:
        """Get operations that are slower than the threshold"""
        slow_ops = {}
        for operation, times in self.response_times.items():
            if times:
                avg_ms = sum(times) / len(times) * 1000
                if avg_ms > threshold_ms:
                    slow_ops[operation] = avg_ms
        
        return slow_ops

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_operation(operation: str):
    """Decorator to monitor operation performance"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            performance_monitor.start_timer(operation)
            try:
                result = await func(*args, **kwargs)
                performance_monitor.end_timer(operation)
                return result
            except Exception as e:
                performance_monitor.record_error(operation, type(e).__name__)
                performance_monitor.end_timer(operation)
                raise
        
        def sync_wrapper(*args, **kwargs):
            performance_monitor.start_timer(operation)
            try:
                result = func(*args, **kwargs)
                performance_monitor.end_timer(operation)
                return result
            except Exception as e:
                performance_monitor.record_error(operation, type(e).__name__)
                performance_monitor.end_timer(operation)
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
