"""Company statistics API endpoints."""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
import pandas as pd

from ..dependencies import (
    get_analytics_engine,
    get_unified_dataset,
    get_correlation_id,
    get_pagination_params,
    get_dataset_validator,
)
from ..models import (
    CompanyStatsResponse,
    PaginationParams,
    TimeframeFilter,
    DifficultyFilter,
    SortOrder
)
from ..utils import (
    paginate_dataframe,
    dataframe_to_dict_list,
    create_paginated_response,
    apply_sorting
)
from ..exceptions import ValidationError, DataProcessingError
from ...analytics.analytics_engine import AnalyticsEngine

def _normalize_topics(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(topic).strip() for topic in value if str(topic).strip()]
    if isinstance(value, str):
        return [t.strip() for t in value.split(',') if t.strip()]
    return []

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/companies", tags=["companies"])


TIMEFRAME_COLUMN_MAP = {
    "30d": "timeframe_30d",
    "3m": "timeframe_3m",
    "6m": "timeframe_6m",
    "6m+": "timeframe_6m_plus",
    "all": "timeframe_all"
}


def _build_difficulty_distribution(row: pd.Series) -> Dict[str, int]:
    easy = int(row.get('easy_count', 0) or 0)
    medium = int(row.get('medium_count', 0) or 0)
    hard = int(row.get('hard_count', 0) or 0)
    known_total = easy + medium + hard
    total = int(row.get('total_problems', 0) or 0)
    unknown = max(total - known_total, 0)
    return {
        'EASY': easy,
        'MEDIUM': medium,
        'HARD': hard,
        'UNKNOWN': unknown
    }


def _build_timeframe_coverage(row: pd.Series) -> List[str]:
    coverage = []
    for tf_value, column_name in TIMEFRAME_COLUMN_MAP.items():
        column_value = row.get(column_name)
        if column_value is not None:
            try:
                if float(column_value) > 0:
                    coverage.append(tf_value)
            except (ValueError, TypeError):
                continue
    return coverage


def _normalize_top_topics(topics_value: Any) -> List[str]:
    if isinstance(topics_value, dict):
        sorted_topics = sorted(
            topics_value.items(),
            key=lambda item: item[1],
            reverse=True
        )
        return [topic for topic, _ in sorted_topics]
    if isinstance(topics_value, list):
        return [str(topic) for topic in topics_value]
    if isinstance(topics_value, str):
        return [t.strip() for t in topics_value.split(',') if t.strip()]
    return []


@router.get("/stats", response_model=Dict[str, Any])
async def get_company_statistics(
    # Query parameters
    companies: Optional[List[str]] = Query(None, description="Filter by specific companies"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    sort_by: str = Query("total_problems", description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    
    # Dependencies
    pagination: PaginationParams = Depends(get_pagination_params),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get comprehensive statistics for companies.
    
    Returns detailed statistics for each company including problem counts,
    difficulty distributions, topic preferences, and timeframe coverage.
    """
    try:
        logger.info("Getting company statistics", extra={"correlation_id": correlation_id})
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)

        # Retrieve cached company statistics for consistent performance
        from ...services.dataset_manager import DatasetManager
        from ..dependencies import get_dataset_manager

        dataset_manager: DatasetManager = get_dataset_manager()

        stats_df = dataset_manager.create_company_statistics(unified_df=dataset, force_refresh=False).copy()

        # Apply company filter if provided
        if companies:
            stats_df = stats_df[stats_df['company'].isin(companies)]

        # Filter by timeframe coverage using aggregated counts
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            for timeframe_value in timeframe_values:
                column_name = TIMEFRAME_COLUMN_MAP.get(timeframe_value)
                if column_name and column_name in stats_df.columns:
                    stats_df = stats_df[stats_df[column_name] > 0]

        if stats_df.empty:
            logger.warning("No data found for specified filters", extra={"correlation_id": correlation_id})
            return create_paginated_response([], {
                "total": 0, "page": pagination.page, "page_size": pagination.page_size,
                "total_pages": 0, "has_next": False, "has_previous": False
            })

        # Enrich aggregated stats with derived fields matching response contract
        stats_df['difficulty_distribution'] = stats_df.apply(_build_difficulty_distribution, axis=1)
        stats_df['timeframe_coverage'] = stats_df.apply(_build_timeframe_coverage, axis=1)
        stats_df['top_topics'] = stats_df['top_topics'].apply(_normalize_top_topics)

        # Ensure average fields are standard Python floats
        numeric_columns = ['avg_frequency', 'max_frequency', 'min_frequency', 'avg_acceptance_rate']
        for column in numeric_columns:
            if column in stats_df.columns:
                stats_df[column] = pd.to_numeric(stats_df[column], errors='coerce')

        # Validate sort field
        valid_sort_fields = [
            'company', 'total_problems', 'unique_problems', 'avg_frequency',
            'max_frequency', 'min_frequency', 'avg_acceptance_rate', 'total_unique_topics'
        ]
        if sort_by not in valid_sort_fields:
            raise ValidationError(f"Invalid sort field '{sort_by}'. Valid options: {', '.join(valid_sort_fields)}")

        # Apply sorting
        stats_df = apply_sorting(stats_df, sort_by, sort_order.value)

        # Paginate results
        paginated_df, pagination_metadata = paginate_dataframe(stats_df, pagination)

        # Remove internal columns not part of response contract
        drop_columns = [
            'easy_count', 'medium_count', 'hard_count',
            'timeframe_30d', 'timeframe_3m', 'timeframe_6m',
            'timeframe_6m_plus', 'timeframe_all', 'created_at'
        ]
        existing_drop_columns = [col for col in drop_columns if col in paginated_df.columns]
        if existing_drop_columns:
            paginated_df = paginated_df.drop(columns=existing_drop_columns)

        # Convert to response format
        stats_data = dataframe_to_dict_list(paginated_df)
        
        logger.info(
            f"Returning statistics for {len(stats_data)} companies (page {pagination.page})",
            extra={"correlation_id": correlation_id}
        )
        
        return create_paginated_response(stats_data, pagination_metadata)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error getting company statistics: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to get company statistics: {str(e)}")


@router.get("/rankings", response_model=Dict[str, Any])
async def get_company_rankings(
    # Query parameters
    metric: str = Query("total_problems", description="Metric to rank by"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    difficulties: Optional[List[DifficultyFilter]] = Query(None, description="Filter by difficulties"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of companies"),
    
    # Dependencies
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get company rankings based on various metrics.
    
    Returns companies ranked by the specified metric with comparative statistics.
    """
    try:
        logger.info(f"Getting company rankings by {metric}", extra={"correlation_id": correlation_id})
        
        # Filter dataset if needed
        filtered_dataset = dataset.copy()
        
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            filtered_dataset = filtered_dataset[filtered_dataset['timeframe'].isin(timeframe_values)]
        
        if difficulties:
            difficulty_values = [d.value for d in difficulties]
            filtered_dataset = filtered_dataset[filtered_dataset['difficulty'].isin(difficulty_values)]
        
        # Create filter criteria for analytics engine
        from ...models.data_models import FilterCriteria, Timeframe, Difficulty
        filters = FilterCriteria(
            timeframes=[Timeframe(tf.value) for tf in timeframes] if timeframes else None,
            difficulties=[Difficulty(d.value) for d in difficulties] if difficulties else None
        )
        
        # Get company rankings from analytics engine
        rankings_df = analytics_engine.cross_company_analyzer.get_company_rankings(
            filtered_dataset, 
            filters,
            metric=metric,
            limit=limit
        )
        
        if rankings_df.empty:
            logger.warning("No company rankings found", extra={"correlation_id": correlation_id})
            return {
                "rankings": [],
                "metadata": {
                    "metric": metric,
                    "total_companies": 0,
                    "filters_applied": {
                        "timeframes": [tf.value for tf in timeframes] if timeframes else None,
                        "difficulties": [d.value for d in difficulties] if difficulties else None
                    }
                }
            }
        
        # Convert to response format
        rankings_data = dataframe_to_dict_list(rankings_df)
        
        # Add ranking positions
        for i, company_data in enumerate(rankings_data):
            company_data['rank'] = i + 1
        
        result = {
            "rankings": rankings_data,
            "metadata": {
                "metric": metric,
                "total_companies": len(rankings_data),
                "filters_applied": {
                    "timeframes": [tf.value for tf in timeframes] if timeframes else None,
                    "difficulties": [d.value for d in difficulties] if difficulties else None
                }
            }
        }
        
        logger.info(
            f"Returning rankings for {len(rankings_data)} companies",
            extra={"correlation_id": correlation_id}
        )
        
        return result
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error getting company rankings: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to get company rankings: {str(e)}")


@router.get("/compare", response_model=Dict[str, Any])
async def compare_companies(
    # Query parameters
    companies: List[str] = Query(..., description="Companies to compare (2-10 companies)"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    
    # Dependencies
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Compare multiple companies across various metrics.
    
    Returns detailed comparison of companies including problem overlap,
    difficulty preferences, topic similarities, and statistical comparisons.
    """
    try:
        logger.info(f"Comparing companies: {companies}", extra={"correlation_id": correlation_id})
        
        # Validate input
        if len(companies) < 2:
            raise ValidationError("At least 2 companies are required for comparison")
        if len(companies) > 10:
            raise ValidationError("Maximum 10 companies can be compared at once")
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Filter dataset
        filtered_dataset = dataset[dataset['company'].isin(companies)]
        
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            filtered_dataset = filtered_dataset[filtered_dataset['timeframe'].isin(timeframe_values)]
        
        if filtered_dataset.empty:
            logger.warning("No data found for specified companies", extra={"correlation_id": correlation_id})
            raise HTTPException(status_code=404, detail="No data found for the specified companies")
        
        # Generate comparison data
        comparison_result = {}
        
        # Basic statistics for each company
        company_stats = {}
        for company in companies:
            company_data = filtered_dataset[filtered_dataset['company'] == company]
            if not company_data.empty:
                stats = {
                    'total_problems': len(company_data),
                    'unique_problems': company_data['title'].nunique(),
                    'avg_frequency': float(company_data['frequency'].mean()),
                    'avg_acceptance_rate': float(company_data['acceptance_rate'].mean()),
                    'difficulty_distribution': company_data['difficulty'].value_counts().to_dict(),
                    'timeframe_coverage': sorted(company_data['timeframe'].unique().tolist())
                }
                company_stats[company] = stats
        
        comparison_result['company_statistics'] = company_stats
        
        # Problem overlap analysis
        company_problems = {}
        for company in companies:
            company_data = filtered_dataset[filtered_dataset['company'] == company]
            company_problems[company] = set(company_data['title'].unique())
        
        # Calculate overlaps
        overlaps = {}
        for i, company1 in enumerate(companies):
            for company2 in companies[i+1:]:
                if company1 in company_problems and company2 in company_problems:
                    overlap = company_problems[company1] & company_problems[company2]
                    union = company_problems[company1] | company_problems[company2]
                    
                    overlap_data = {
                        'common_problems': len(overlap),
                        'total_unique_problems': len(union),
                        'overlap_percentage': (len(overlap) / len(union) * 100) if union else 0,
                        'company1_unique': len(company_problems[company1] - company_problems[company2]),
                        'company2_unique': len(company_problems[company2] - company_problems[company1])
                    }
                    overlaps[f"{company1}_vs_{company2}"] = overlap_data
        
        comparison_result['problem_overlaps'] = overlaps
        
        # Topic similarity analysis
        topic_similarities = {}
        for i, company1 in enumerate(companies):
            for company2 in companies[i+1:]:
                company1_data = filtered_dataset[filtered_dataset['company'] == company1]
                company2_data = filtered_dataset[filtered_dataset['company'] == company2]
                
                # Extract topics for each company
                company1_topics = set()
                company2_topics = set()
                
                for topics_str in company1_data['topics'].dropna():
                    if isinstance(topics_str, str):
                        topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                        company1_topics.update(topics)
                
                for topics_str in company2_data['topics'].dropna():
                    if isinstance(topics_str, str):
                        topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                        company2_topics.update(topics)
                
                if company1_topics and company2_topics:
                    common_topics = company1_topics & company2_topics
                    all_topics = company1_topics | company2_topics
                    
                    similarity_data = {
                        'common_topics': len(common_topics),
                        'total_unique_topics': len(all_topics),
                        'similarity_percentage': (len(common_topics) / len(all_topics) * 100) if all_topics else 0,
                        'common_topic_list': sorted(list(common_topics))[:10]  # Top 10 common topics
                    }
                    topic_similarities[f"{company1}_vs_{company2}"] = similarity_data
        
        comparison_result['topic_similarities'] = topic_similarities
        
        # Summary insights
        comparison_result['summary'] = {
            'companies_compared': len(companies),
            'total_problems_across_companies': len(set().union(*company_problems.values())),
            'most_similar_pair': max(overlaps.items(), key=lambda x: x[1]['overlap_percentage']) if overlaps else None,
            'least_similar_pair': min(overlaps.items(), key=lambda x: x[1]['overlap_percentage']) if overlaps else None
        }
        
        logger.info(
            f"Generated comparison for {len(companies)} companies",
            extra={"correlation_id": correlation_id}
        )
        
        return comparison_result
        
    except ValidationError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing companies: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to compare companies: {str(e)}")


@router.get("/{company_name}", response_model=Dict[str, Any])
async def get_company_details(
    company_name: str,
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    
    # Dependencies
    dataset = Depends(get_unified_dataset),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get detailed information for a specific company.
    
    Returns comprehensive statistics and problem data for the specified company.
    """
    try:
        logger.info(f"Getting details for company: {company_name}", extra={"correlation_id": correlation_id})
        
        # Clean company name
        company_name = company_name.strip()
        if not company_name:
            raise ValidationError("Company name cannot be empty")
        
        # Filter dataset for the specific company
        company_data = dataset[dataset['company'].str.lower() == company_name.lower()]
        
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            company_data = company_data[company_data['timeframe'].isin(timeframe_values)]
        
        if company_data.empty:
            logger.warning(f"Company not found: {company_name}", extra={"correlation_id": correlation_id})
            raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")
        
        # Get the actual company name from data (for case consistency)
        actual_company_name = company_data['company'].iloc[0]
        
        # Calculate detailed statistics
        stats = {
            'company': actual_company_name,
            'total_problems': len(company_data),
            'unique_problems': company_data['title'].nunique(),
            'avg_frequency': float(company_data['frequency'].mean()),
            'max_frequency': float(company_data['frequency'].max()),
            'min_frequency': float(company_data['frequency'].min()),
            'avg_acceptance_rate': float(company_data['acceptance_rate'].mean()),
            'timeframes_available': sorted(company_data['timeframe'].unique().tolist()),
            'difficulty_distribution': company_data['difficulty'].value_counts().to_dict()
        }
        
        # Top problems by frequency
        top_problems = company_data.nlargest(20, 'frequency')[
            ['title', 'frequency', 'acceptance_rate', 'difficulty', 'timeframe', 'link']
        ].to_dict('records')
        
        # Topic analysis
        all_topics = []
        for topics_str in company_data['topics'].dropna():
            if isinstance(topics_str, str):
                topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                all_topics.extend(topics)
        
        if all_topics:
            topic_counts = pd.Series(all_topics).value_counts()
            stats['top_topics'] = topic_counts.head(20).to_dict()
            stats['total_unique_topics'] = len(topic_counts)
        else:
            stats['top_topics'] = {}
            stats['total_unique_topics'] = 0
        
        # Timeframe breakdown
        timeframe_stats = {}
        for timeframe in company_data['timeframe'].unique():
            tf_data = company_data[company_data['timeframe'] == timeframe]
            timeframe_stats[timeframe] = {
                'total_problems': len(tf_data),
                'unique_problems': tf_data['title'].nunique(),
                'avg_frequency': float(tf_data['frequency'].mean()),
                'avg_acceptance_rate': float(tf_data['acceptance_rate'].mean())
            }
        
        result = {
            'company_stats': stats,
            'top_problems': top_problems,
            'timeframe_breakdown': timeframe_stats
        }
        
        logger.info(
            f"Returning details for company: {actual_company_name} ({len(top_problems)} top problems)",
            extra={"correlation_id": correlation_id}
        )
        
        return result
        
    except ValidationError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company details: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to get company details: {str(e)}")


@router.get("/{company_name}/problems", response_model=Dict[str, Any])
async def get_company_problems(
    company_name: str,
    limit: int = Query(25, ge=1, le=200, description="Maximum number of problems to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    topic: Optional[str] = Query(None, description="Filter problems by topic"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order for frequency"),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """Return a paginated list of problems for the specified company."""
    try:
        logger.info(
            "Fetching company problems",
            extra={"company": company_name, "correlation_id": correlation_id}
        )

        validated_companies = dataset_validator.validate_companies([company_name])
        if not validated_companies:
            raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")

        normalized_company = validated_companies[0]
        company_data = dataset[dataset['company'] == normalized_company]

        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            company_data = company_data[company_data['timeframe'].isin(timeframe_values)]

        if topic:
            topic_lower = topic.lower()
            company_data = company_data[company_data['topics'].fillna('').str.lower().str.contains(topic_lower)]

        total_matches = len(company_data)
        logger.info(
            "Company problems selection",
            extra={
                "company": normalized_company,
                "total_matches": int(total_matches),
                "topic_filter": topic,
                "timeframes": timeframes,
                "correlation_id": correlation_id
            }
        )
        if total_matches == 0:
            return {
                'company': normalized_company,
                'total': 0,
                'limit': limit,
                'offset': offset,
                'has_more': False,
                'problems': []
            }

        ascending = sort_order == SortOrder.ASC
        if 'frequency' in company_data.columns:
            company_data = company_data.sort_values(
                by=['frequency', 'acceptance_rate'],
                ascending=[ascending, ascending],
                na_position='last'
            )
        else:
            company_data = company_data.sort_values(
                by=['acceptance_rate'],
                ascending=[ascending],
                na_position='last'
            )

        if offset >= total_matches:
            return {
                'company': normalized_company,
                'total': int(total_matches),
                'limit': limit,
                'offset': offset,
                'has_more': False,
                'problems': []
            }

        # Deduplicate by title - aggregate across timeframes
        aggregated_records = []
        for title, group in company_data.groupby('title'):
            first_row = group.iloc[0]
            # Collect all timeframes for this problem
            timeframes_list = sorted(group['timeframe'].dropna().unique().tolist())
            # Use max frequency across timeframes
            max_freq = group['frequency'].max()
            # Use mean acceptance rate
            mean_acc = group['acceptance_rate'].mean()
            # Collect all topics
            all_topics = set()
            for topics_val in group['topics'].dropna():
                all_topics.update(_normalize_topics(topics_val))

            aggregated_records.append({
                'title': title,
                'difficulty': first_row.get('difficulty'),
                'frequency': max_freq,
                'acceptance_rate': mean_acc,
                'timeframes': timeframes_list,
                'topics': sorted(all_topics) if all_topics else [],
                'link': first_row.get('leetcode_link') or first_row.get('link') or first_row.get('url'),
                'company': first_row.get('company')
            })

        deduplicated_df = pd.DataFrame(aggregated_records)

        if deduplicated_df.empty:
            return {
                'company': normalized_company,
                'total': 0,
                'limit': limit,
                'offset': offset,
                'has_more': False,
                'problems': []
            }

        # Re-sort after aggregation
        ascending = sort_order == SortOrder.ASC
        deduplicated_df = deduplicated_df.sort_values(
            by=['frequency', 'acceptance_rate'],
            ascending=[ascending, ascending],
            na_position='last'
        )

        # Update total after deduplication
        total_matches = len(deduplicated_df)

        if offset >= total_matches:
            return {
                'company': normalized_company,
                'total': int(total_matches),
                'limit': limit,
                'offset': offset,
                'has_more': False,
                'problems': []
            }

        paginated_df = deduplicated_df.iloc[offset:offset + limit]

        titles = paginated_df['title'].dropna().unique().tolist()
        company_counts = dataset[dataset['title'].isin(titles)].groupby('title')['company'].nunique()

        problems = []
        for _, row in paginated_df.iterrows():
            timeframes_list = row.get('timeframes', [])
            problem = {
                'title': row.get('title'),
                'difficulty': row.get('difficulty'),
                'frequency': float(row['frequency']) if pd.notna(row.get('frequency')) else None,
                'acceptance_rate': float(row['acceptance_rate']) if pd.notna(row.get('acceptance_rate')) else None,
                'timeframe': timeframes_list[0] if timeframes_list else None,  # backwards compat
                'timeframes': timeframes_list,
                'topics': row.get('topics', []),
                'link': row.get('link'),
                'company_count': int(company_counts.get(row.get('title'), 0)),
                'company': row.get('company')
            }
            problems.append(problem)

        next_offset = offset + len(problems)

        return {
            'company': normalized_company,
            'total': int(total_matches),
            'limit': limit,
            'offset': offset,
            'has_more': next_offset < total_matches,
            'next_offset': next_offset if next_offset < total_matches else None,
            'problems': problems
        }

    except ValidationError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching company problems: {str(e)}",
            extra={"company": company_name, "correlation_id": correlation_id}
        )
        raise DataProcessingError(f"Failed to get company problems: {str(e)}")
