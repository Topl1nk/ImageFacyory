"""
Integration tests for performance monitoring and optimization.

These tests verify that the application performs well under various conditions
and that performance monitoring works correctly.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from src.pixelflow_studio.core.performance_monitor import (
    PerformanceMonitor, get_performance_monitor, time_operation
)
from src.pixelflow_studio.core.cache_manager import (
    CacheManager, get_node_cache, get_image_cache
)


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    def test_performance_monitor_initialization(self):
        """Test that performance monitor initializes correctly."""
        monitor = PerformanceMonitor()
        
        assert monitor.monitoring_enabled is True
        assert monitor.max_history > 0
        assert len(monitor.metrics) == 0
        assert len(monitor.operation_timings) == 0
    
    def test_operation_timing(self):
        """Test operation timing functionality."""
        monitor = PerformanceMonitor()
        
        with monitor.time_operation("test_operation"):
            time.sleep(0.1)  # Simulate work
        
        assert "test_operation" in monitor.operation_timings
        operations = monitor.operation_timings["test_operation"]
        assert len(operations) == 1
        
        operation = operations[0]
        assert operation.success is True
        assert operation.duration is not None
        assert operation.duration >= 0.1
    
    def test_operation_timing_with_exception(self):
        """Test operation timing when exception occurs."""
        monitor = PerformanceMonitor()
        
        with pytest.raises(ValueError):
            with monitor.time_operation("failing_operation"):
                raise ValueError("Test exception")
        
        operations = monitor.operation_timings["failing_operation"]
        assert len(operations) == 1
        
        operation = operations[0]
        assert operation.success is False
        assert "Test exception" in operation.error_message
    
    def test_metric_recording(self):
        """Test custom metric recording."""
        monitor = PerformanceMonitor()
        
        monitor.record_metric("test_metric", 42.5, "units", {"key": "value"})
        
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.unit == "units"
        assert metric.metadata["key"] == "value"
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        monitor = PerformanceMonitor()
        
        # Add some test data
        with monitor.time_operation("test_op"):
            time.sleep(0.01)
        
        monitor.record_metric("test_metric", 100)
        
        summary = monitor.get_performance_summary()
        
        assert "system" in summary
        assert "operations" in summary
        assert "test_op" in summary["operations"]
        assert summary["recent_metrics_count"] >= 1
    
    def test_performance_alerts(self):
        """Test performance alert system."""
        monitor = PerformanceMonitor()
        
        monitor.add_alert("Test alert")
        
        assert len(monitor.alerts) == 1
        assert "Test alert" in monitor.alerts[0]
    
    def test_monitoring_enable_disable(self):
        """Test enabling/disabling monitoring."""
        monitor = PerformanceMonitor()
        
        # Disable monitoring
        monitor.enable_monitoring(False)
        assert monitor.monitoring_enabled is False
        
        # Record metric while disabled
        monitor.record_metric("test", 1.0)
        assert len(monitor.metrics) == 0
        
        # Re-enable monitoring
        monitor.enable_monitoring(True)
        assert monitor.monitoring_enabled is True
        
        # Record metric while enabled
        monitor.record_metric("test", 1.0)
        assert len(monitor.metrics) == 1


class TestCacheManager:
    """Test caching functionality."""
    
    def test_cache_initialization(self):
        """Test cache manager initialization."""
        cache = CacheManager(max_size=10, max_memory_mb=50)
        
        assert cache.max_size == 10
        assert cache.max_memory_bytes == 50 * 1024 * 1024
        assert len(cache.cache) == 0
        assert cache.total_memory == 0
    
    def test_basic_caching(self):
        """Test basic get/set operations."""
        cache = CacheManager()
        
        # Set value
        cache.set("test_key", "test_value")
        assert len(cache.cache) == 1
        
        # Get value
        value = cache.get("test_key")
        assert value == "test_value"
        
        # Get non-existent value
        value = cache.get("non_existent", "default")
        assert value == "default"
    
    def test_cache_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = CacheManager(max_size=2)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache.cache) == 2
        
        # Add one more - should evict oldest
        cache.set("key3", "value3")
        assert len(cache.cache) == 2
        
        # Oldest key should be evicted
        assert "key1" not in cache.cache
        assert "key2" in cache.cache
        assert "key3" in cache.cache
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = CacheManager()
        
        cache.set("test_key", "test_value")
        assert "test_key" in cache.cache
        
        # Invalidate
        result = cache.invalidate("test_key")
        assert result is True
        assert "test_key" not in cache.cache
        
        # Invalidate non-existent key
        result = cache.invalidate("non_existent")
        assert result is False
    
    def test_cache_statistics(self):
        """Test cache statistics."""
        cache = CacheManager()
        
        # Add some data
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access some keys
        cache.get("key1")
        cache.get("key2")
        cache.get("key1")  # Hit
        cache.get("non_existent")  # Miss
        
        stats = cache.get_stats()
        
        assert stats["entries"] == 2
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate_percent"] == 50.0
    
    def test_cache_clear(self):
        """Test cache clearing."""
        cache = CacheManager()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache.cache) == 2
        
        cache.clear()
        assert len(cache.cache) == 0
        assert cache.total_memory == 0


class TestPerformanceIntegration:
    """Integration tests for performance features."""
    
    def test_global_performance_monitor(self):
        """Test global performance monitor singleton."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        assert monitor1 is monitor2
    
    def test_global_cache_instances(self):
        """Test global cache instances."""
        node_cache = get_node_cache()
        image_cache = get_image_cache()
        
        assert isinstance(node_cache, CacheManager)
        assert isinstance(image_cache, CacheManager)
        assert node_cache is not image_cache
    
    def test_decorator_timing(self):
        """Test the time_operation decorator."""
        monitor = get_performance_monitor()
        
        @time_operation("decorated_function")
        def test_function():
            time.sleep(0.01)
            return "result"
        
        result = test_function()
        assert result == "result"
        
        # Check that timing was recorded
        stats = monitor.get_operation_stats("decorated_function")
        assert stats["total_operations"] == 1
        assert stats["successful_operations"] == 1
    
    def test_concurrent_operations(self):
        """Test performance monitoring under concurrent load."""
        monitor = PerformanceMonitor()
        results = []
        
        def worker(worker_id):
            with monitor.time_operation(f"worker_{worker_id}"):
                time.sleep(0.01)
                results.append(worker_id)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(results) == 5
        assert len(monitor.operation_timings) == 5
        
        for i in range(5):
            stats = monitor.get_operation_stats(f"worker_{i}")
            assert stats["total_operations"] == 1
            assert stats["successful_operations"] == 1


class TestPerformanceThresholds:
    """Test performance threshold monitoring."""
    
    @patch('psutil.Process')
    def test_cpu_threshold_alert(self, mock_process):
        """Test CPU threshold alert generation."""
        # Mock high CPU usage
        mock_process_instance = Mock()
        mock_process_instance.cpu_percent.return_value = 85.0
        mock_process_instance.memory_info.return_value = Mock(rss=1000000, vms=2000000)
        mock_process_instance.memory_percent.return_value = 50.0
        mock_process.return_value = mock_process_instance
        
        monitor = PerformanceMonitor()
        alerts = monitor.check_performance_thresholds()
        
        assert len(alerts) >= 1
        assert any("High CPU usage" in alert for alert in alerts)
    
    @patch('psutil.Process')
    def test_memory_threshold_alert(self, mock_process):
        """Test memory threshold alert generation."""
        # Mock high memory usage
        mock_process_instance = Mock()
        mock_process_instance.cpu_percent.return_value = 50.0
        mock_process_instance.memory_info.return_value = Mock(rss=1000000, vms=2000000)
        mock_process_instance.memory_percent.return_value = 90.0
        mock_process.return_value = mock_process_instance
        
        monitor = PerformanceMonitor()
        alerts = monitor.check_performance_thresholds()
        
        assert len(alerts) >= 1
        assert any("High memory usage" in alert for alert in alerts)
    
    def test_slow_operation_alert(self):
        """Test slow operation alert generation."""
        monitor = PerformanceMonitor()
        
        # Simulate slow operation
        with monitor.time_operation("slow_operation"):
            time.sleep(1.1)  # More than 1 second threshold
        
        alerts = monitor.check_performance_thresholds()
        
        assert len(alerts) >= 1
        assert any("Slow operation" in alert for alert in alerts)


if __name__ == "__main__":
    pytest.main([__file__]) 