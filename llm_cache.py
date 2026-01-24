#!/usr/bin/env python3
"""
LLM Response Caching System
Caches LLM responses to avoid re-processing identical or similar text
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class LLMCache:
    """Thread-safe LLM response cache"""
    
    def __init__(self, cache_dir: Path = None, cache_ttl_days: int = 30):
        """
        Initialize cache
        
        Args:
            cache_dir: Directory to store cache files (default: ./llm_cache)
            cache_ttl_days: Time-to-live for cache entries in days (default: 30)
        """
        self.cache_dir = cache_dir or Path("llm_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl = timedelta(days=cache_ttl_days)
        
        # In-memory cache for fast access
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def _generate_cache_key(self, text: str, prompt_type: str, 
                           prompt_version: str = "2.0") -> str:
        """
        Generate cache key from text hash and prompt type
        
        Args:
            text: Input text (first 2000 chars used for hashing)
            prompt_type: Type of extraction (e.g., "theory", "method")
            prompt_version: Version of prompt (for cache invalidation)
        
        Returns:
            Cache key string
        """
        # Use first 2000 chars for hashing (enough to identify similar papers)
        text_hash = hashlib.md5(text[:2000].encode('utf-8')).hexdigest()
        return f"{prompt_type}_{prompt_version}_{text_hash}"
    
    def get(self, text: str, prompt_type: str, 
            prompt_version: str = "2.0") -> Optional[Dict[str, Any]]:
        """
        Get cached response
        
        Args:
            text: Input text
            prompt_type: Type of extraction
            prompt_version: Prompt version
        
        Returns:
            Cached response dict or None if not found
        """
        cache_key = self._generate_cache_key(text, prompt_type, prompt_version)
        
        with self.cache_lock:
            self.stats['total_requests'] += 1
            
            # Check memory cache first
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if self._is_valid(entry):
                    self.stats['hits'] += 1
                    logger.debug(f"Cache HIT: {prompt_type} (memory)")
                    return entry['response']
                else:
                    # Expired, remove from memory
                    del self.memory_cache[cache_key]
            
            # Check disk cache
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        entry = json.load(f)
                    
                    if self._is_valid(entry):
                        # Load into memory cache
                        self.memory_cache[cache_key] = entry
                        self.stats['hits'] += 1
                        logger.debug(f"Cache HIT: {prompt_type} (disk)")
                        return entry['response']
                    else:
                        # Expired, delete file
                        cache_file.unlink()
                        self.stats['evictions'] += 1
                        logger.debug(f"Cache entry expired: {cache_key}")
                except Exception as e:
                    logger.warning(f"Error reading cache file {cache_file}: {e}")
            
            # Cache miss
            self.stats['misses'] += 1
            logger.debug(f"Cache MISS: {prompt_type}")
            return None
    
    def set(self, text: str, prompt_type: str, response: Dict[str, Any],
            prompt_version: str = "2.0"):
        """
        Cache response
        
        Args:
            text: Input text
            prompt_type: Type of extraction
            response: LLM response to cache
            prompt_version: Prompt version
        """
        cache_key = self._generate_cache_key(text, prompt_type, prompt_version)
        
        entry = {
            'response': response,
            'prompt_type': prompt_type,
            'prompt_version': prompt_version,
            'cached_at': datetime.now().isoformat(),
            'text_hash': hashlib.md5(text[:2000].encode('utf-8')).hexdigest()
        }
        
        with self.cache_lock:
            # Store in memory cache
            self.memory_cache[cache_key] = entry
            
            # Store on disk
            cache_file = self.cache_dir / f"{cache_key}.json"
            try:
                with open(cache_file, 'w') as f:
                    json.dump(entry, f, indent=2, default=str)
                logger.debug(f"Cached response: {prompt_type}")
            except Exception as e:
                logger.warning(f"Error writing cache file {cache_file}: {e}")
    
    def _is_valid(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid (not expired)"""
        if 'cached_at' not in entry:
            return False
        
        try:
            cached_at = datetime.fromisoformat(entry['cached_at'])
            age = datetime.now() - cached_at
            return age < self.cache_ttl
        except Exception:
            return False
    
    def invalidate(self, prompt_type: Optional[str] = None, 
                   prompt_version: Optional[str] = None):
        """
        Invalidate cache entries
        
        Args:
            prompt_type: If specified, only invalidate this type
            prompt_version: If specified, only invalidate this version
        """
        with self.cache_lock:
            if prompt_type is None and prompt_version is None:
                # Clear all
                self.memory_cache.clear()
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                logger.info("Cache cleared")
            else:
                # Clear specific entries
                keys_to_remove = []
                for key, entry in self.memory_cache.items():
                    if (prompt_type is None or entry.get('prompt_type') == prompt_type) and \
                       (prompt_version is None or entry.get('prompt_version') == prompt_version):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.memory_cache[key]
                    cache_file = self.cache_dir / f"{key}.json"
                    if cache_file.exists():
                        cache_file.unlink()
                
                logger.info(f"Invalidated {len(keys_to_remove)} cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.cache_lock:
            hit_rate = (self.stats['hits'] / self.stats['total_requests'] * 100) \
                      if self.stats['total_requests'] > 0 else 0.0
            
            return {
                **self.stats,
                'hit_rate': hit_rate,
                'memory_cache_size': len(self.memory_cache),
                'disk_cache_size': len(list(self.cache_dir.glob("*.json")))
            }
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        with self.cache_lock:
            expired_count = 0
            keys_to_remove = []
            
            for key, entry in self.memory_cache.items():
                if not self._is_valid(entry):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.memory_cache[key]
                cache_file = self.cache_dir / f"{key}.json"
                if cache_file.exists():
                    cache_file.unlink()
                expired_count += 1
            
            # Also check disk cache
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        entry = json.load(f)
                    if not self._is_valid(entry):
                        cache_file.unlink()
                        expired_count += 1
                except Exception:
                    pass
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired cache entries")
            
            return expired_count

# Global cache instance
_cache = None

def get_cache() -> LLMCache:
    """Get singleton cache instance"""
    global _cache
    if _cache is None:
        _cache = LLMCache()
    return _cache

