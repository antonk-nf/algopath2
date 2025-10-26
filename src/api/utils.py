"""Utility functions for API operations."""

import math
from typing import List, Dict, Any, Tuple
import pandas as pd

from .models import PaginatedResponse, PaginationParams


def paginate_dataframe(
    df: pd.DataFrame,
    pagination: PaginationParams
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Paginate a DataFrame and return the page data with metadata.
    
    Args:
        df: DataFrame to paginate
        pagination: Pagination parameters
        
    Returns:
        Tuple of (paginated_df, pagination_metadata)
    """
    total_items = len(df)
    total_pages = math.ceil(total_items / pagination.page_size) if total_items > 0 else 1
    
    # Calculate offset
    offset = (pagination.page - 1) * pagination.page_size
    
    # Get the page data
    paginated_df = df.iloc[offset:offset + pagination.page_size]
    
    # Create pagination metadata
    pagination_metadata = {
        "total": total_items,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": total_pages,
        "has_next": pagination.page < total_pages,
        "has_previous": pagination.page > 1
    }
    
    return paginated_df, pagination_metadata


def dataframe_to_dict_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert DataFrame to list of dictionaries with proper type handling.
    
    Args:
        df: DataFrame to convert
        
    Returns:
        List of dictionaries
    """
    # Handle NaN values and convert to appropriate types
    df_clean = df.copy()
    
    # Replace NaN with None for JSON serialization
    df_clean = df_clean.where(pd.notnull(df_clean), None)
    
    # Convert to list of dictionaries
    records = df_clean.to_dict('records')
    
    # Post-process records to handle special cases
    for record in records:
        # Handle topics field - convert string to list if needed
        if 'topics' in record and isinstance(record['topics'], str):
            record['topics'] = [t.strip() for t in record['topics'].split(',') if t.strip()]
        elif 'topics' in record and record['topics'] is None:
            record['topics'] = []
        
        # Handle primary_topics field
        if 'primary_topics' in record and isinstance(record['primary_topics'], str):
            record['primary_topics'] = [t.strip() for t in record['primary_topics'].split(',') if t.strip()]
        elif 'primary_topics' in record and record['primary_topics'] is None:
            record['primary_topics'] = []
        
        # Ensure numeric fields are properly typed
        for field in ['frequency', 'total_frequency', 'acceptance_rate', 'avg_acceptance_rate', 'trend_score']:
            if field in record and record[field] is not None:
                try:
                    record[field] = float(record[field])
                except (ValueError, TypeError):
                    record[field] = None
        
        for field in ['company_count']:
            if field in record and record[field] is not None:
                try:
                    record[field] = int(record[field])
                except (ValueError, TypeError):
                    record[field] = None
    
    return records


def create_paginated_response(
    data: List[Dict[str, Any]],
    pagination_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a paginated response dictionary.
    
    Args:
        data: List of data items
        pagination_metadata: Pagination metadata
        
    Returns:
        Paginated response dictionary
    """
    return {
        "data": data,
        **pagination_metadata
    }


def apply_sorting(df: pd.DataFrame, sort_by: str, sort_order: str = "desc") -> pd.DataFrame:
    """
    Apply sorting to DataFrame.
    
    Args:
        df: DataFrame to sort
        sort_by: Column to sort by
        sort_order: Sort order ("asc" or "desc")
        
    Returns:
        Sorted DataFrame
    """
    if sort_by not in df.columns:
        return df
    
    ascending = sort_order.lower() == "asc"
    return df.sort_values(sort_by, ascending=ascending)


def validate_numeric_range(value: float, min_val: float = None, max_val: float = None) -> bool:
    """
    Validate that a numeric value is within the specified range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        True if valid, False otherwise
    """
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    return True


def clean_search_term(term: str) -> str:
    """
    Clean and normalize a search term.
    
    Args:
        term: Search term to clean
        
    Returns:
        Cleaned search term
    """
    if not term:
        return ""
    
    # Strip whitespace and convert to lowercase
    cleaned = term.strip().lower()
    
    # Remove extra spaces
    cleaned = " ".join(cleaned.split())
    
    return cleaned


def extract_topics_from_string(topics_str: str) -> List[str]:
    """
    Extract topics from a comma-separated string.
    
    Args:
        topics_str: Comma-separated topics string
        
    Returns:
        List of cleaned topic strings
    """
    if not topics_str or not isinstance(topics_str, str):
        return []
    
    topics = [t.strip() for t in topics_str.split(',') if t.strip()]
    return topics


def format_percentage(value: float, decimal_places: int = 2) -> float:
    """
    Format a percentage value.
    
    Args:
        value: Percentage value (0.0 to 1.0)
        decimal_places: Number of decimal places
        
    Returns:
        Formatted percentage
    """
    if value is None:
        return None
    
    return round(value * 100, decimal_places) if 0 <= value <= 1 else value