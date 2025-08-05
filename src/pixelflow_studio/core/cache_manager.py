"""
Cache Manager for PixelFlow Studio.

This module provides intelligent caching for frequently accessed data
to improve application performance and reduce redundant operations.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass
from collections import OrderedDict

from .logging_config import get_logger

T = TypeVar('T')

logger = get_logger("cache_manager")


@dataclass
class CacheEntry(Generic[T]):
    """A cache entry with metadata."""
    
    data: T
    timestamp: float
    access_count: int = 0
    size: int = 0


class CacheManager:
    """
    Intelligent cache manager with LRU eviction and size limits.
    
    Features:
    - LRU (Least Recently Used) eviction
    - Size-based limits
    - TTL (Time To Live) support
    - Access statistics
    - Automatic cleanup
    """
    
    def __init__(self, max_size: int = 100, max_memory_mb: int = 100):
        """
        Initialize the cache manager.
        
        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.total_memory = 0
        self.hits = 0
        self.misses = 0
        
        logger.info(f"Cache manager initialized: max_size={max_size}, max_memory={max_memory_mb}MB")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        if key in self.cache:
            entry = self.cache[key]
            entry.access_count += 1
            self.cache.move_to_end(key)  # Move to end (most recently used)
            self.hits += 1
            logger.debug(f"Cache hit: {key}")
            return entry.data
        else:
            self.misses += 1
            logger.debug(f"Cache miss: {key}")
            return default
    
    def set(self, key: str, value: T, ttl_seconds: Optional[int] = None, size: Optional[int] = None) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            size: Estimated size in bytes
        """
        # Remove existing entry if present
        if key in self.cache:
            self._remove_entry(key)
        
        # Calculate entry size
        if size is None:
            size = self._estimate_size(value)
        
        # Check if we need to evict entries
        while (len(self.cache) >= self.max_size or 
               self.total_memory + size > self.max_memory_bytes):
            self._evict_oldest()
        
        # Create cache entry
        entry = CacheEntry(
            data=value,
            timestamp=time.time(),
            size=size
        )
        
        # Add to cache
        self.cache[key] = entry
        self.total_memory += size
        
        logger.debug(f"Cached: {key} (size: {size} bytes)")
    
    def invalidate(self, key: str) -> bool:
        """
        Remove a specific key from cache.
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if key was found and removed
        """
        if key in self.cache:
            self._remove_entry(key)
            logger.debug(f"Invalidated cache key: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.total_memory = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "entries": len(self.cache),
            "max_size": self.max_size,
            "memory_used_mb": self.total_memory / (1024 * 1024),
            "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": hit_rate,
            "total_requests": total_requests
        }
    
    def cleanup_expired(self, ttl_seconds: int) -> int:
        """
        Remove expired entries.
        
        Args:
            ttl_seconds: Time to live threshold
            
        Returns:
            Number of removed entries
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry.timestamp > ttl_seconds
        ]
        
        for key in expired_keys:
            self._remove_entry(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def _remove_entry(self, key: str) -> None:
        """Remove a cache entry."""
        if key in self.cache:
            entry = self.cache[key]
            self.total_memory -= entry.size
            del self.cache[key]
    
    def _evict_oldest(self) -> None:
        """Evict the oldest (least recently used) entry."""
        if self.cache:
            oldest_key = next(iter(self.cache))
            self._remove_entry(oldest_key)
            logger.debug(f"Evicted oldest cache entry: {oldest_key}")
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate the size of a value in bytes."""
        try:
            import sys
            return sys.getsizeof(value)
        except:
            # Fallback estimation
            return 1024  # 1KB default


# Global cache instances
node_cache = CacheManager(max_size=50, max_memory_mb=50)
image_cache = CacheManager(max_size=20, max_memory_mb=200)
property_cache = CacheManager(max_size=100, max_memory_mb=10)


def get_node_cache() -> CacheManager:
    """Get the node cache instance."""
    return node_cache


def get_image_cache() -> CacheManager:
    """Get the image cache instance."""
    return image_cache


def get_property_cache() -> CacheManager:
    """Get the property cache instance."""
    return property_cache 