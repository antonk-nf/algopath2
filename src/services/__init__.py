# Business logic and data processing services

from .csv_discovery import CSVDiscovery
from .csv_loader import CSVLoader
from .data_normalizer import DataNormalizer
from .metadata_enricher import MetadataEnricher
from .topic_exploder import TopicExploder
from .data_processor import DataProcessor

# Optional imports that require external dependencies
try:
    from .cache_manager import CacheManager
    _CACHE_AVAILABLE = True
except ImportError:
    _CACHE_AVAILABLE = False

try:
    from .dataset_manager import DatasetManager
    _DATASET_MANAGER_AVAILABLE = True
except ImportError:
    _DATASET_MANAGER_AVAILABLE = False

try:
    from .database_manager import DatabaseManager, DatabaseConfig
    _DATABASE_AVAILABLE = True
except ImportError:
    _DATABASE_AVAILABLE = False

__all__ = [
    'CSVDiscovery', 
    'CSVLoader', 
    'DataNormalizer', 
    'MetadataEnricher', 
    'TopicExploder', 
    'DataProcessor'
]

# Add optional components to __all__ if available
if _CACHE_AVAILABLE:
    __all__.append('CacheManager')
if _DATASET_MANAGER_AVAILABLE:
    __all__.append('DatasetManager')
if _DATABASE_AVAILABLE:
    __all__.extend(['DatabaseManager', 'DatabaseConfig'])