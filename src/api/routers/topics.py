"""Topic analysis API endpoints."""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
import pandas as pd

from ..dependencies import (
    get_analytics_engine,
    get_unified_dataset,
    get_correlation_id,
    get_pagination_params,
    get_dataset_validator
)
from ..models import (
    TopicTrendResponse,
    PaginationParams,
    TimeframeFilter,
    SortOrder
)
from ..utils import (
    paginate_dataframe,
    dataframe_to_dict_list,
    create_paginated_response
)
from ..exceptions import ValidationError, DataProcessingError
from ...analytics.analytics_engine import AnalyticsEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/trends", response_model=Dict[str, Any])
async def get_topic_trends(
    # Query parameters
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of topics"),
    min_frequency: Optional[float] = Query(None, ge=0, description="Minimum topic frequency"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order for trend strength"),
    sort_by_abs: bool = Query(False, description="Sort by absolute trend strength"),
    
    # Dependencies
    pagination: PaginationParams = Depends(get_pagination_params),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Analyze topic trends across different timeframes.
    
    Returns trending topics with frequency changes over time,
    trend direction, and strength indicators.
    """
    try:
        logger.info("Analyzing topic trends", extra={"correlation_id": correlation_id})
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Filter dataset if needed
        filtered_dataset = dataset.copy()
        if companies:
            filtered_dataset = filtered_dataset[filtered_dataset['company'].isin(companies)]
        
        # Convert timeframes to string values
        timeframe_values = None
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
        
        # Get topic trends from analytics engine
        trends_df = analytics_engine.analyze_topic_trends(filtered_dataset, timeframe_values)
        
        if trends_df.empty:
            logger.warning("No topic trends found", extra={"correlation_id": correlation_id})
            return create_paginated_response([], {
                "total": 0, "page": pagination.page, "page_size": pagination.page_size,
                "total_pages": 0, "has_next": False, "has_previous": False
            })
        
        # Apply frequency filter if specified
        if min_frequency is not None:
            # Filter based on maximum frequency across timeframes
            if 'max_frequency' in trends_df.columns:
                trends_df = trends_df[trends_df['max_frequency'] >= min_frequency]
            elif 'total_frequency' in trends_df.columns:
                trends_df = trends_df[trends_df['total_frequency'] >= min_frequency]
        
        # Sort by trend strength or total frequency
        if 'trend_strength' in trends_df.columns:
            trends_df['trend_strength_abs'] = trends_df['trend_strength'].abs()
        
        sort_column = 'trend_strength'
        if sort_by_abs and 'trend_strength_abs' in trends_df.columns:
            sort_column = 'trend_strength_abs'
            sort_ascending = False
        else:
            sort_column = 'trend_strength' if 'trend_strength' in trends_df.columns else 'total_frequency'
            sort_ascending = sort_order == SortOrder.ASC
        if sort_column in trends_df.columns:
            trends_df = trends_df.sort_values(sort_column, ascending=sort_ascending)
        
        # Limit results before pagination
        if limit:
            trends_df = trends_df.head(limit)
        
        # Paginate results
        paginated_df, pagination_metadata = paginate_dataframe(trends_df, pagination)
        
        # Convert to response format
        trends_data = dataframe_to_dict_list(paginated_df)
        
        logger.info(
            f"Returning {len(trends_data)} topic trends (page {pagination.page})",
            extra={"correlation_id": correlation_id}
        )
        
        return create_paginated_response(trends_data, pagination_metadata)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing topic trends: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to analyze topic trends: {str(e)}")


@router.get("/frequency", response_model=Dict[str, Any])
async def get_topic_frequency(
    # Query parameters
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of topics"),
    min_frequency: Optional[float] = Query(None, ge=0, description="Minimum frequency"),
    
    # Dependencies
    pagination: PaginationParams = Depends(get_pagination_params),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get topic frequency analysis across companies and timeframes.
    
    Returns topics ranked by frequency with company and timeframe breakdowns.
    """
    try:
        logger.info("Analyzing topic frequencies", extra={"correlation_id": correlation_id})
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Filter dataset if needed
        filtered_dataset = dataset.copy()
        if companies:
            filtered_dataset = filtered_dataset[filtered_dataset['company'].isin(companies)]
        
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            filtered_dataset = filtered_dataset[filtered_dataset['timeframe'].isin(timeframe_values)]
        
        # Get topic frequency from analytics engine
        frequency_df = analytics_engine.topic_analyzer.get_topic_frequency(
            filtered_dataset, 
            limit=limit
        )
        
        if frequency_df.empty:
            logger.warning("No topic frequencies found", extra={"correlation_id": correlation_id})
            return create_paginated_response([], {
                "total": 0, "page": pagination.page, "page_size": pagination.page_size,
                "total_pages": 0, "has_next": False, "has_previous": False
            })
        
        # Apply frequency filter if specified
        if min_frequency is not None and 'frequency' in frequency_df.columns:
            frequency_df = frequency_df[frequency_df['frequency'] >= min_frequency]
        
        # Paginate results
        paginated_df, pagination_metadata = paginate_dataframe(frequency_df, pagination)
        
        # Convert to response format
        frequency_data = dataframe_to_dict_list(paginated_df)
        
        logger.info(
            f"Returning {len(frequency_data)} topic frequencies (page {pagination.page})",
            extra={"correlation_id": correlation_id}
        )
        
        return create_paginated_response(frequency_data, pagination_metadata)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing topic frequencies: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to analyze topic frequencies: {str(e)}")


@router.get("/correlations", response_model=Dict[str, Any])
async def get_topic_correlations(
    # Query parameters
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    min_correlation: Optional[float] = Query(0.1, ge=-1, le=1, description="Minimum correlation strength"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of correlations"),
    
    # Dependencies
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get topic correlation analysis.
    
    Returns correlations between topics based on co-occurrence patterns
    across problems and companies.
    """
    try:
        logger.info("Analyzing topic correlations", extra={"correlation_id": correlation_id})
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Filter dataset if needed
        filtered_dataset = dataset.copy()
        if companies:
            filtered_dataset = filtered_dataset[filtered_dataset['company'].isin(companies)]
        
        # Get topic correlations from analytics engine
        correlations_result = analytics_engine.topic_analyzer.get_topic_correlations(filtered_dataset)
        
        if not correlations_result or 'correlations' not in correlations_result:
            logger.warning("No topic correlations found", extra={"correlation_id": correlation_id})
            return {
                "correlations": [],
                "correlation_matrix": {},
                "metadata": {
                    "total_topics": 0,
                    "total_correlations": 0,
                    "min_correlation_threshold": min_correlation
                }
            }
        
        # Filter correlations by minimum threshold
        correlations = correlations_result['correlations']
        if min_correlation is not None:
            correlations = [
                corr for corr in correlations 
                if abs(corr.get('correlation', 0)) >= min_correlation
            ]
        
        # Limit results
        correlations = correlations[:limit]
        
        result = {
            "correlations": correlations,
            "correlation_matrix": correlations_result.get('correlation_matrix', {}),
            "metadata": {
                "total_topics": correlations_result.get('total_topics', 0),
                "total_correlations": len(correlations),
                "min_correlation_threshold": min_correlation,
                "analysis_type": "topic_correlation"
            }
        }
        
        logger.info(
            f"Returning {len(correlations)} topic correlations",
            extra={"correlation_id": correlation_id}
        )
        
        return result
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing topic correlations: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to analyze topic correlations: {str(e)}")


@router.get("/heatmap", response_model=Dict[str, Any])
async def get_topic_heatmap(
    # Query parameters
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    top_topics: int = Query(20, ge=5, le=100, description="Number of top topics to include"),
    
    # Dependencies
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get topic heatmap data for visualization.
    
    Returns topic frequency data structured for heatmap visualization,
    showing topic popularity across companies and timeframes.
    """
    try:
        logger.info("Generating topic heatmap data", extra={"correlation_id": correlation_id})
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Filter dataset if needed
        filtered_dataset = dataset.copy()
        if companies:
            filtered_dataset = filtered_dataset[filtered_dataset['company'].isin(companies)]
        
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            filtered_dataset = filtered_dataset[filtered_dataset['timeframe'].isin(timeframe_values)]
        
        # Get topic heatmap data from analytics engine
        heatmap_data = analytics_engine.generate_topic_heatmap(
            filtered_dataset,
            companies=companies,
            top_n=top_topics
        )
        
        if not heatmap_data:
            logger.warning("No heatmap data generated", extra={"correlation_id": correlation_id})
            return {
                "heatmap_data": [],
                "topics": [],
                "companies": [],
                "timeframes": [],
                "metadata": {
                    "total_topics": 0,
                    "total_companies": 0,
                    "total_timeframes": 0
                }
            }
        
        logger.info(
            f"Generated heatmap data for {len(heatmap_data.get('topics', []))} topics",
            extra={"correlation_id": correlation_id}
        )
        
        return heatmap_data
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error generating topic heatmap: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to generate topic heatmap: {str(e)}")
