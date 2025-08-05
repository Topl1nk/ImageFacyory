"""
Performance Monitor for PixelFlow Studio.

This module provides comprehensive performance monitoring and metrics
collection to identify bottlenecks and optimize application performance.
"""

from __future__ import annotations

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import contextmanager

from .logging_config import get_logger

logger = get_logger("performance_monitor")


@dataclass
class PerformanceMetric:
    """A single performance metric."""
    
    name: str
    value: float
    timestamp: float
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationTiming:
    """Timing information for an operation."""
    
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.
    
    Features:
    - Operation timing
    - Memory usage tracking
    - CPU usage monitoring
    - Custom metrics
    - Performance alerts
    - Historical data
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize the performance monitor.
        
        Args:
            max_history: Maximum number of historical records to keep
        """
        self.max_history = max_history
        self.metrics: deque = deque(maxlen=max_history)
        self.operation_timings: Dict[str, List[OperationTiming]] = defaultdict(list)
        self.custom_metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.alerts: List[str] = []
        self.monitoring_enabled = True
        self._lock = threading.Lock()
        
        # System monitoring
        self.process = psutil.Process()
        self.last_cpu_check = time.time()
        self.last_memory_check = time.time()
        
        logger.info("Performance monitor initialized")
    
    @contextmanager
    def time_operation(self, operation_name: str):
        """
        Context manager for timing operations.
        
        Args:
            operation_name: Name of the operation to time
        """
        timing = OperationTiming(
            operation_name=operation_name,
            start_time=time.time()
        )
        
        try:
            yield timing
            timing.success = True
        except Exception as e:
            timing.success = False
            timing.error_message = str(e)
            raise
        finally:
            timing.end_time = time.time()
            timing.duration = timing.end_time - timing.start_time
            
            with self._lock:
                self.operation_timings[operation_name].append(timing)
                if len(self.operation_timings[operation_name]) > self.max_history:
                    self.operation_timings[operation_name].pop(0)
            
            logger.debug(f"Operation '{operation_name}' took {timing.duration:.3f}s")
    
    def record_metric(self, name: str, value: float, unit: str = "", metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a custom performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            metadata: Additional metadata
        """
        if not self.monitoring_enabled:
            return
        
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            unit=unit,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics.append(metric)
            self.custom_metrics[name].append(metric)
            if len(self.custom_metrics[name]) > self.max_history:
                self.custom_metrics[name].pop(0)
    
    def get_system_metrics(self) -> Dict[str, float]:
        """
        Get current system performance metrics.
        
        Returns:
            Dictionary with system metrics
        """
        current_time = time.time()
        
        # CPU usage (check every 1 second to avoid overhead)
        cpu_percent = 0.0
        if current_time - self.last_cpu_check > 1.0:
            try:
                cpu_percent = self.process.cpu_percent()
                self.last_cpu_check = current_time
            except Exception as e:
                logger.warning(f"Failed to get CPU usage: {e}")
        
        # Memory usage
        memory_info = {}
        if current_time - self.last_memory_check > 1.0:
            try:
                memory = self.process.memory_info()
                memory_info = {
                    "memory_rss_mb": memory.rss / (1024 * 1024),
                    "memory_vms_mb": memory.vms / (1024 * 1024),
                    "memory_percent": self.process.memory_percent()
                }
                self.last_memory_check = current_time
            except Exception as e:
                logger.warning(f"Failed to get memory usage: {e}")
        
        return {
            "cpu_percent": cpu_percent,
            **memory_info
        }
    
    def get_operation_stats(self, operation_name: str, window_seconds: int = 300) -> Dict[str, Any]:
        """
        Get statistics for a specific operation.
        
        Args:
            operation_name: Name of the operation
            window_seconds: Time window for statistics (default: 5 minutes)
            
        Returns:
            Dictionary with operation statistics
        """
        if operation_name not in self.operation_timings:
            return {}
        
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Filter recent operations
        recent_operations = [
            op for op in self.operation_timings[operation_name]
            if op.end_time and op.end_time > cutoff_time
        ]
        
        if not recent_operations:
            return {}
        
        # Calculate statistics
        durations = [op.duration for op in recent_operations if op.duration]
        successful_ops = [op for op in recent_operations if op.success]
        
        stats = {
            "total_operations": len(recent_operations),
            "successful_operations": len(successful_ops),
            "success_rate": len(successful_ops) / len(recent_operations) * 100,
            "window_seconds": window_seconds
        }
        
        if durations:
            stats.update({
                "min_duration": min(durations),
                "max_duration": max(durations),
                "avg_duration": sum(durations) / len(durations),
                "total_duration": sum(durations)
            })
        
        return stats
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive performance summary.
        
        Returns:
            Dictionary with performance summary
        """
        system_metrics = self.get_system_metrics()
        
        # Get recent metrics (last 5 minutes)
        current_time = time.time()
        recent_metrics = [
            metric for metric in self.metrics
            if current_time - metric.timestamp < 300
        ]
        
        # Calculate operation statistics
        operation_stats = {}
        for operation_name in self.operation_timings:
            stats = self.get_operation_stats(operation_name, window_seconds=300)
            if stats:
                operation_stats[operation_name] = stats
        
        return {
            "system": system_metrics,
            "operations": operation_stats,
            "recent_metrics_count": len(recent_metrics),
            "total_metrics_count": len(self.metrics),
            "alerts_count": len(self.alerts),
            "monitoring_enabled": self.monitoring_enabled
        }
    
    def add_alert(self, message: str) -> None:
        """
        Add a performance alert.
        
        Args:
            message: Alert message
        """
        alert = f"[{time.strftime('%H:%M:%S')}] {message}"
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        logger.warning(f"Performance alert: {message}")
    
    def check_performance_thresholds(self) -> List[str]:
        """
        Check performance against thresholds and generate alerts.
        
        Returns:
            List of new alerts
        """
        new_alerts = []
        system_metrics = self.get_system_metrics()
        
        # CPU threshold
        if system_metrics.get("cpu_percent", 0) > 80:
            alert = f"High CPU usage: {system_metrics['cpu_percent']:.1f}%"
            new_alerts.append(alert)
            self.add_alert(alert)
        
        # Memory threshold
        if system_metrics.get("memory_percent", 0) > 85:
            alert = f"High memory usage: {system_metrics['memory_percent']:.1f}%"
            new_alerts.append(alert)
            self.add_alert(alert)
        
        # Operation duration thresholds
        for operation_name, stats in self.get_performance_summary()["operations"].items():
            avg_duration = stats.get("avg_duration", 0)
            if avg_duration > 1.0:  # More than 1 second
                alert = f"Slow operation '{operation_name}': {avg_duration:.3f}s avg"
                new_alerts.append(alert)
                self.add_alert(alert)
        
        return new_alerts
    
    def clear_history(self) -> None:
        """Clear all historical data."""
        with self._lock:
            self.metrics.clear()
            self.operation_timings.clear()
            self.custom_metrics.clear()
            self.alerts.clear()
        
        logger.info("Performance history cleared")
    
    def enable_monitoring(self, enabled: bool = True) -> None:
        """
        Enable or disable performance monitoring.
        
        Args:
            enabled: Whether to enable monitoring
        """
        self.monitoring_enabled = enabled
        status = "enabled" if enabled else "disabled"
        logger.info(f"Performance monitoring {status}")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def time_operation(operation_name: str):
    """Decorator for timing operations."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.time_operation(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator 