"""
Cache management system for LeetCode Analytics API.

This module provides caching functionality using Parquet files with
cache invalidation based on source file modification times.
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages Parquet file caching with automatic invalidation based on source file modification times.
    
    Features:
    - Cache key generation and validation
    - Source file modification time tracking
    - Automatic cache invalidation
    - Compressed Parquet storage
    """
    
    def __init__(self, cache_dir: str = "cache", compression: str = "snappy"):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            compression: Compression algorithm for Parquet files
        """
        self.cache_dir = Path(cache_dir)
        self.compression = compression
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different cache types
        (self.cache_dir / "datasets").mkdir(exist_ok=True)
        (self.cache_dir / "analytics").mkdir(exist_ok=True)
        (self.cache_dir / "metadata").mkdir(exist_ok=True)
        
        logger.info(f"CacheManager initialized with cache_dir: {self.cache_dir}")
    
    def generate_cache_key(self, identifier: str, source_files: List[str] = None) -> str:
        """
        Generate a unique cache key based on identifier and source files.
        
        Args:
            identifier: Base identifier for the cache entry
            source_files: List of source file paths that affect this cache entry
            
        Returns:
            Unique cache key string
        """
        # Create a hash based on identifier and source file paths
        hash_input = identifier
        if source_files:
            # Sort source files for consistent hashing
            sorted_files = sorted(source_files)
            hash_input += "|" + "|".join(sorted_files)
        
        # Generate MD5 hash for the cache key
        cache_key = hashlib.md5(hash_input.encode()).hexdigest()
        logger.debug(f"Generated cache key '{cache_key}' for identifier '{identifier}'")
        return cache_key
    
    def _get_cache_path(self, cache_key: str, cache_type: str = "datasets") -> Path:
        """
        Get the full path for a cache file.
        
        Args:
            cache_key: Unique cache key
            cache_type: Type of cache (datasets, analytics, metadata)
            
        Returns:
            Path to the cache file
        """
        return self.cache_dir / cache_type / f"{cache_key}.parquet"
    
    def _get_metadata_path(self, cache_key: str) -> Path:
        """
        Get the path for cache metadata file.
        
        Args:
            cache_key: Unique cache key
            
        Returns:
            Path to the metadata file
        """
        return self.cache_dir / "metadata" / f"{cache_key}.json"
    
    def _get_source_files_mtime(self, source_files: List[str]) -> Dict[str, float]:
        """
        Get modification times for source files.
        
        Args:
            source_files: List of source file paths
            
        Returns:
            Dictionary mapping file paths to modification times
        """
        mtimes = {}
        for file_path in source_files:
            try:
                if os.path.exists(file_path):
                    mtimes[file_path] = os.path.getmtime(file_path)
                else:
                    logger.warning(f"Source file not found: {file_path}")
                    mtimes[file_path] = 0.0
            except OSError as e:
                logger.error(f"Error getting mtime for {file_path}: {e}")
                mtimes[file_path] = 0.0
        return mtimes
    
    def _save_cache_metadata(self, cache_key: str, source_files: List[str], 
                           created_at: datetime) -> None:
        """
        Save cache metadata including source file modification times.
        
        Args:
            cache_key: Unique cache key
            source_files: List of source file paths
            created_at: Cache creation timestamp
        """
        metadata = {
            "cache_key": cache_key,
            "created_at": created_at.isoformat(),
            "source_files": source_files,
            "source_mtimes": self._get_source_files_mtime(source_files)
        }
        
        metadata_path = self._get_metadata_path(cache_key)
        try:
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.debug(f"Saved cache metadata for key '{cache_key}'")
        except Exception as e:
            logger.error(f"Error saving cache metadata for key '{cache_key}': {e}")
    
    def _load_cache_metadata(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Load cache metadata.
        
        Args:
            cache_key: Unique cache key
            
        Returns:
            Cache metadata dictionary or None if not found
        """
        metadata_path = self._get_metadata_path(cache_key)
        if not metadata_path.exists():
            return None
        
        try:
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            logger.debug(f"Loaded cache metadata for key '{cache_key}'")
            return metadata
        except Exception as e:
            logger.error(f"Error loading cache metadata for key '{cache_key}': {e}")
            return None
    
    def is_cache_valid(self, cache_key: str, source_files: List[str] = None) -> bool:
        """
        Check if cache is valid based on source file modification times.
        
        Args:
            cache_key: Unique cache key
            source_files: List of source file paths to check
            
        Returns:
            True if cache is valid, False otherwise
        """
        cache_path = self._get_cache_path(cache_key)
        if not cache_path.exists():
            logger.debug(f"Cache file not found for key '{cache_key}'")
            return False
        
        # Load cache metadata
        metadata = self._load_cache_metadata(cache_key)
        if not metadata:
            logger.debug(f"Cache metadata not found for key '{cache_key}'")
            return False
        
        # If no source files provided, use files from metadata
        if source_files is None:
            source_files = metadata.get("source_files", [])
        
        if not source_files:
            logger.debug(f"No source files to check for cache key '{cache_key}'")
            return True
        
        # Check if any source file has been modified
        cached_mtimes = metadata.get("source_mtimes", {})
        current_mtimes = self._get_source_files_mtime(source_files)
        
        for file_path in source_files:
            cached_mtime = cached_mtimes.get(file_path, 0.0)
            current_mtime = current_mtimes.get(file_path, 0.0)
            
            if current_mtime > cached_mtime:
                logger.debug(f"Source file '{file_path}' has been modified, cache invalid")
                return False
        
        logger.debug(f"Cache is valid for key '{cache_key}'")
        return True
    
    def save_to_cache(self, data: pd.DataFrame, cache_key: str, 
                     source_files: List[str] = None, cache_type: str = "datasets") -> bool:
        """
        Save DataFrame to cache as Parquet file.
        
        Args:
            data: DataFrame to cache
            cache_key: Unique cache key
            source_files: List of source file paths that generated this data
            cache_type: Type of cache (datasets, analytics, metadata)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(cache_key, cache_type)
            
            # Save DataFrame as Parquet with compression
            data.to_parquet(
                cache_path,
                compression=self.compression,
                index=False,
                engine='pyarrow'
            )
            
            # Save metadata
            if source_files:
                self._save_cache_metadata(cache_key, source_files, datetime.now())
            
            logger.info(f"Saved {len(data)} records to cache with key '{cache_key}'")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to cache with key '{cache_key}': {e}")
            return False
    
    def load_from_cache(self, cache_key: str, cache_type: str = "datasets") -> Optional[pd.DataFrame]:
        """
        Load DataFrame from cache.
        
        Args:
            cache_key: Unique cache key
            cache_type: Type of cache (datasets, analytics, metadata)
            
        Returns:
            Cached DataFrame or None if not found/invalid
        """
        try:
            cache_path = self._get_cache_path(cache_key, cache_type)
            
            if not cache_path.exists():
                logger.debug(f"Cache file not found for key '{cache_key}'")
                return None
            
            # Load DataFrame from Parquet
            data = pd.read_parquet(cache_path, engine='pyarrow')
            logger.info(f"Loaded {len(data)} records from cache with key '{cache_key}'")
            return data
            
        except Exception as e:
            logger.error(f"Error loading from cache with key '{cache_key}': {e}")
            return None
    
    def invalidate_cache(self, cache_key: str, cache_type: str = "datasets") -> bool:
        """
        Invalidate (delete) a cache entry.
        
        Args:
            cache_key: Unique cache key
            cache_type: Type of cache (datasets, analytics, metadata)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(cache_key, cache_type)
            metadata_path = self._get_metadata_path(cache_key)
            
            # Remove cache file
            if cache_path.exists():
                cache_path.unlink()
                logger.debug(f"Removed cache file for key '{cache_key}'")
            
            # Remove metadata file
            if metadata_path.exists():
                metadata_path.unlink()
                logger.debug(f"Removed metadata file for key '{cache_key}'")
            
            logger.info(f"Invalidated cache for key '{cache_key}'")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating cache for key '{cache_key}': {e}")
            return False
    
    def clear_cache(self, cache_type: str = None) -> bool:
        """
        Clear all cache entries of a specific type or all cache entries.
        
        Args:
            cache_type: Type of cache to clear (datasets, analytics, metadata) or None for all
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if cache_type:
                # Clear specific cache type
                cache_dir = self.cache_dir / cache_type
                if cache_dir.exists():
                    for cache_file in cache_dir.glob("*.parquet"):
                        cache_file.unlink()
                    logger.info(f"Cleared all {cache_type} cache entries")
            else:
                # Clear all cache types
                for subdir in ["datasets", "analytics", "metadata"]:
                    cache_dir = self.cache_dir / subdir
                    if cache_dir.exists():
                        for cache_file in cache_dir.glob("*"):
                            cache_file.unlink()
                logger.info("Cleared all cache entries")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "cache_dir": str(self.cache_dir),
            "compression": self.compression,
            "cache_types": {}
        }
        
        for cache_type in ["datasets", "analytics", "metadata"]:
            cache_dir = self.cache_dir / cache_type
            if cache_dir.exists():
                files = list(cache_dir.glob("*"))
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                stats["cache_types"][cache_type] = {
                    "file_count": len(files),
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                }
            else:
                stats["cache_types"][cache_type] = {
                    "file_count": 0,
                    "total_size_bytes": 0,
                    "total_size_mb": 0.0
                }
        
        return stats