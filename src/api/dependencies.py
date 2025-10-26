"""Dependency injection for FastAPI endpoints."""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, Request, Query
from functools import lru_cache

from ..analytics.analytics_engine import AnalyticsEngine
from ..services.dataset_manager import DatasetManager
from ..config.settings import config
from .exceptions import DataNotFoundError, DataProcessingError
from .models import PaginationParams

logger = logging.getLogger(__name__)


@lru_cache()
def get_analytics_engine() -> AnalyticsEngine:
    """Get analytics engine instance (cached)."""
    return AnalyticsEngine()


@lru_cache()
def get_dataset_manager() -> DatasetManager:
    """Get dataset manager instance (cached)."""
    from ..services.cache_manager import CacheManager
    from ..services.data_processor import DataProcessor
    from ..services.csv_discovery import CSVDiscovery
    from ..services.csv_loader import CSVLoader
    
    # Get configuration values
    cache_dir = config.get_config("CACHE_DIR", ".cache")
    root_path = config.get_config("DATA_ROOT_PATH", ".")
    max_workers = config.get_config("PARALLEL_WORKERS", 4)
    
    # Initialize required components with proper configuration
    cache_manager = CacheManager(cache_dir=cache_dir)
    data_processor = DataProcessor(standardize_topics=True)
    csv_discovery = CSVDiscovery(root_directory=root_path)
    csv_loader = CSVLoader(max_workers=max_workers)
    
    return DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)


def get_unified_dataset(
    dataset_manager: DatasetManager = Depends(get_dataset_manager)
):
    """Get the unified dataset, loading from cache or processing if needed."""
    try:
        logger.info("Loading unified dataset")
        dataset = dataset_manager.get_unified_dataset()
        
        if dataset is None or dataset.empty:
            logger.error("No data available in unified dataset")
            raise DataNotFoundError("No data available. Please ensure data has been loaded and processed.")
        
        logger.info(f"Loaded dataset with {len(dataset)} records")
        return dataset
        
    except Exception as e:
        logger.error(f"Failed to load unified dataset: {str(e)}")
        raise DataProcessingError(f"Failed to load dataset: {str(e)}")


def get_correlation_id(request: Request) -> Optional[str]:
    """Extract correlation ID from request state."""
    return getattr(request.state, 'correlation_id', None)


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: Optional[int] = Query(50, ge=1, le=1000, description="Items per page", alias="page_size"),
    page_size_camel: Optional[int] = Query(None, ge=1, le=1000, alias="pageSize")
) -> PaginationParams:
    """Get and validate pagination parameters."""
    page_size_value = page_size_camel if page_size_camel is not None else page_size

    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be >= 1")

    if page_size_value is None or page_size_value < 1 or page_size_value > 1000:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 1000")

    return PaginationParams(page=page, page_size=page_size_value)


def validate_sort_field(sort_by: str, valid_fields: list) -> str:
    """Validate that sort field is allowed."""
    if sort_by not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field '{sort_by}'. Valid options: {', '.join(valid_fields)}"
        )
    return sort_by


def validate_companies(companies: Optional[list], available_companies: set) -> Optional[list]:
    """Validate that requested companies exist in the dataset."""
    if not companies:
        return None
    
    invalid_companies = set(companies) - available_companies
    if invalid_companies:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown companies: {', '.join(invalid_companies)}"
        )
    
    return companies


def validate_topics(topics: Optional[list], available_topics: set) -> Optional[list]:
    """Validate that requested topics exist in the dataset."""
    if not topics:
        return None
    
    # For topics, we'll be more lenient since they can be partial matches
    # Just ensure they're non-empty strings
    valid_topics = [topic.strip() for topic in topics if topic and topic.strip()]
    
    if not valid_topics:
        raise HTTPException(
            status_code=400,
            detail="At least one valid topic must be provided"
        )
    
    return valid_topics


class DatasetValidator:
    """Validator for dataset-dependent parameters."""
    
    def __init__(self, dataset):
        self.dataset = dataset
        self._available_companies = None
        self._available_topics = None
    
    @property
    def available_companies(self) -> set:
        """Get set of available companies."""
        if self._available_companies is None:
            self._available_companies = set(self.dataset['company'].unique())
        return self._available_companies
    
    @property
    def available_topics(self) -> set:
        """Get set of available topics."""
        if self._available_topics is None:
            topics = set()
            for topics_str in self.dataset['topics'].dropna():
                if isinstance(topics_str, str):
                    topics.update(t.strip() for t in topics_str.split(',') if t.strip())
            self._available_topics = topics
        return self._available_topics
    
    def validate_companies(self, companies: Optional[list]) -> Optional[list]:
        """Validate companies against dataset."""
        return validate_companies(companies, self.available_companies)
    
    def validate_topics(self, topics: Optional[list]) -> Optional[list]:
        """Validate topics against dataset."""
        return validate_topics(topics, self.available_topics)


def get_dataset_validator(dataset=Depends(get_unified_dataset)) -> DatasetValidator:
    """Get dataset validator with current dataset."""
    return DatasetValidator(dataset)


# Rate limiting dependencies (placeholder for future implementation)
def rate_limit_dependency():
    """Rate limiting dependency (to be implemented)."""
    # TODO: Implement rate limiting logic
    pass


# Authentication dependencies (placeholder for future implementation)
def get_current_user():
    """Get current authenticated user (to be implemented)."""
    # TODO: Implement authentication logic
    return None
