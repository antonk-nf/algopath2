"""Core interfaces for the LeetCode Analytics API system."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd

from .data_models import (
    CSVFileInfo, ProblemRecord, ValidationResult, 
    FilterCriteria, ProblemStats
)


class DataLoaderInterface(ABC):
    """Interface for data loading operations."""
    
    @abstractmethod
    def discover_csv_files(self, root_path: str) -> List[CSVFileInfo]:
        """Discover CSV files in the directory structure."""
        pass
    
    @abstractmethod
    def load_csv_batch(self, file_infos: List[CSVFileInfo]) -> pd.DataFrame:
        """Load a batch of CSV files into a unified DataFrame."""
        pass
    
    @abstractmethod
    def validate_csv_structure(self, df: pd.DataFrame) -> ValidationResult:
        """Validate the structure and content of loaded CSV data."""
        pass


class DataProcessorInterface(ABC):
    """Interface for data processing and normalization."""
    
    @abstractmethod
    def normalize_data(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize raw CSV data to standard format."""
        pass
    
    @abstractmethod
    def add_metadata(self, df: pd.DataFrame, file_info: CSVFileInfo) -> pd.DataFrame:
        """Add company and timeframe metadata to DataFrame."""
        pass
    
    @abstractmethod
    def explode_topics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Explode comma-separated topics into individual records."""
        pass


class StorageManagerInterface(ABC):
    """Interface for data storage and caching."""
    
    @abstractmethod
    def save_to_cache(self, df: pd.DataFrame, cache_key: str) -> bool:
        """Save DataFrame to cache storage."""
        pass
    
    @abstractmethod
    def load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Load DataFrame from cache storage."""
        pass
    
    @abstractmethod
    def is_cache_valid(self, cache_key: str, source_files: List[str]) -> bool:
        """Check if cache is valid compared to source files."""
        pass
    
    @abstractmethod
    def save_to_database(self, df: pd.DataFrame, table_name: str) -> bool:
        """Save DataFrame to database (optional)."""
        pass


class AnalyticsEngineInterface(ABC):
    """Interface for analytics operations."""
    
    @abstractmethod
    def get_top_problems(self, filters: FilterCriteria, limit: int = 100) -> pd.DataFrame:
        """Get top problems based on frequency across companies."""
        pass
    
    @abstractmethod
    def analyze_topic_trends(self, timeframes: List[str]) -> pd.DataFrame:
        """Analyze topic trends across different timeframes."""
        pass
    
    @abstractmethod
    def get_company_correlations(self, metric: str) -> pd.DataFrame:
        """Calculate correlations between companies for a given metric."""
        pass
    
    @abstractmethod
    def calculate_difficulty_stats(self, groupby: str) -> pd.DataFrame:
        """Calculate difficulty-based statistics grouped by specified field."""
        pass


class ConfigManagerInterface(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        pass
    
    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        pass
    
    @abstractmethod
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        pass
    
    @abstractmethod
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        pass