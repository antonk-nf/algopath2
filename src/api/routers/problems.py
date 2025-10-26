"""Problem-related API endpoints."""

import logging
import json
from typing import List, Optional, Dict, Any
from collections import defaultdict
import math
import re
from fastapi import APIRouter, Depends, Query, HTTPException
import pandas as pd
from bs4 import BeautifulSoup

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - numpy is already a dependency but we guard defensively
    np = None  # type: ignore

from ..dependencies import (
    get_analytics_engine,
    get_unified_dataset,
    get_correlation_id,
    get_pagination_params,
    get_dataset_validator,
    validate_sort_field
)
from ...services.metadata_lookup_service import metadata_lookup_service
from ..models import (
    TopProblemsRequest,
    ProblemSearchRequest,
    ProblemResponse,
    ProblemStatsResponse,
    PaginationParams,
    DifficultyFilter,
    TimeframeFilter,
    SortOrder,
    StudyPlanRecommendationRequest,
    StudyPlanRecommendationResponse,
    StudyPlanSkillLevel,
    RecommendedProblem,
    ProblemPreviewResponse,
    ProblemPreview
)
from ..utils import (
    paginate_dataframe,
    dataframe_to_dict_list,
    create_paginated_response,
    apply_sorting,
    clean_search_term
)
from ..exceptions import ValidationError, DataProcessingError
from ...models.data_models import FilterCriteria, Difficulty, Timeframe
from ...analytics.analytics_engine import AnalyticsEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/problems", tags=["problems"])


def _resolve_title_slug(problem_title: str) -> str:
    return clean_search_term(problem_title).lower() if problem_title else ''


def _is_missing(value: Any) -> bool:
    if value is None:
        return True

    try:
        if hasattr(pd, 'isna'):
            result = pd.isna(value)
            if isinstance(result, (bool, int)):
                return bool(result)
            if np is not None and isinstance(result, np.ndarray):
                return bool(result.all())
    except Exception:
        return False

    return False


def _coerce_scalar(value: Any) -> Any:
    """Convert numpy arrays/lists with a single meaningful value into scalars."""
    if np is not None and isinstance(value, np.ndarray):
        if value.size == 0:
            return None
        if value.ndim == 0:
            return value.item()
        for item in value.flat:
            if not _is_missing(item):
                return item
        return None

    if isinstance(value, list):
        for item in value:
            if not _is_missing(item):
                return item
        return None

    return value


def _get_scalar(record: pd.Series, *keys: str) -> Any:
    """Get the first non-missing scalar value for the provided keys."""
    for key in keys:
        value = record.get(key)
        if _is_missing(value):
            continue
        coerced = _coerce_scalar(value)
        if _is_missing(coerced):
            continue
        return coerced
    return None


def _get_value(record: pd.Series, *keys: str) -> Any:
    """Get the first non-missing value (preserving sequences where needed)."""
    for key in keys:
        value = record.get(key)
        if _is_missing(value):
            continue
        if np is not None and isinstance(value, np.ndarray):
            value = value.tolist()
        return value
    return None


def _safe_int(value: Any) -> Optional[int]:
    try:
        if _is_missing(value):
            return None
        return int(value)
    except Exception:
        return None


def _safe_float(value: Any) -> Optional[float]:
    try:
        if _is_missing(value):
            return None
        return float(value)
    except Exception:
        return None


def _safe_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lower = value.lower()
        if lower in {'true', '1', 'yes'}:
            return True
        if lower in {'false', '0', 'no'}:
            return False
    if _is_missing(value):
        return None
    return None


def _safe_str(value: Any) -> Optional[str]:
    if _is_missing(value):
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _format_timestamp(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return value
    try:
        return pd.to_datetime(value).isoformat()
    except Exception:
        return None


def _extract_slug_from_link(link: Any) -> Optional[str]:
    if not isinstance(link, str) or not link:
        return None
    match = re.search(r"https?://leetcode\.com/problems/([\w-]+)/?", link)
    if match:
        return match.group(1).strip().lower()
    return None


def _sanitize_html(html: Any) -> Optional[str]:
    if not isinstance(html, str) or not html.strip():
        return None
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
    for a_tag in soup.find_all('a'):
        a_tag['rel'] = 'noopener noreferrer'
        a_tag['target'] = '_blank'
    for img_tag in soup.find_all('img'):
        img_tag.attrs.pop('width', None)
        img_tag.attrs.pop('height', None)
        img_tag['loading'] = 'lazy'
    sanitized = soup.decode()
    return sanitized.strip()


def _extract_plain_text(html: Any) -> Optional[str]:
    if not isinstance(html, str) or not html.strip():
        return None
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text('\n')
    return text.strip()


def _build_problem_preview(record: pd.Series) -> ProblemPreview:
    raw_html = _get_scalar(record, 'leetcode_content_html')
    raw_fallback = _get_scalar(record, 'leetcode_content_raw')

    content_html = _safe_str(raw_html)
    if not content_html:
        content_html = _safe_str(raw_fallback)

    preview = ProblemPreview(
        title=_safe_str(_get_scalar(record, 'leetcode_title', 'title')),
        title_slug=_safe_str(_get_scalar(record, 'title_slug')),
        question_id=_safe_str(_get_scalar(record, 'leetcode_questionfrontendid', 'question_frontend_id')),
        difficulty=_safe_str(_get_scalar(record, 'leetcode_difficulty', 'difficulty')),
        likes=_safe_int(_get_scalar(record, 'leetcode_likes', 'likes')),
        dislikes=_safe_int(_get_scalar(record, 'leetcode_dislikes', 'dislikes')),
        ac_rate=_safe_float(_get_scalar(record, 'leetcode_acrate', 'acceptance_rate')),
        is_paid_only=_safe_bool(_get_scalar(record, 'leetcode_ispaidonly', 'is_paid_only')),
        has_solution=_safe_bool(_get_scalar(record, 'leetcode_hassolution', 'has_solution')),
        has_video_solution=_safe_bool(_get_scalar(record, 'leetcode_hasvideosolution', 'has_video_solution')),
        freq_bar=_safe_str(_get_scalar(record, 'leetcode_freqbar')),
        content_html=content_html,
        content_text=_safe_str(_get_scalar(record, 'leetcode_content_text')),
        metadata_fetched_at=_format_timestamp(_get_scalar(record, 'leetcode_fetched_at'))
    )

    if not preview.content_html and raw_fallback:
        fallback_str = _safe_str(raw_fallback)
        if fallback_str:
            preview.content_html = _sanitize_html(fallback_str)

    if preview.content_html and not preview.content_text:
        preview.content_text = _extract_plain_text(preview.content_html)

    topic_tags = _get_value(
        record,
        'leetcode_topictags',
        'leetcode_topic_tags',
        'topic_tags'
    )
    if isinstance(topic_tags, list):
        preview.topic_tags = topic_tags
    elif isinstance(topic_tags, str):
        try:
            parsed = json.loads(topic_tags)
            if isinstance(parsed, list):
                preview.topic_tags = parsed
        except json.JSONDecodeError:
            preview.topic_tags = None

    return preview


@router.get("/top", response_model=Dict[str, Any])
async def get_top_problems(
    # Query parameters
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    difficulties: Optional[List[DifficultyFilter]] = Query(None, description="Filter by difficulties"),
    topics: Optional[List[str]] = Query(None, description="Filter by topics"),
    min_frequency: Optional[float] = Query(None, ge=0, description="Minimum frequency"),
    max_frequency: Optional[float] = Query(None, ge=0, description="Maximum frequency"),
    min_acceptance_rate: Optional[float] = Query(None, ge=0, le=1, description="Minimum acceptance rate"),
    max_acceptance_rate: Optional[float] = Query(None, ge=0, le=1, description="Maximum acceptance rate"),
    # Quality-based filters
    min_originality_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum originality score"),
    max_originality_score: Optional[float] = Query(None, ge=0, le=1, description="Maximum originality score"),
    min_likes: Optional[int] = Query(None, ge=0, description="Minimum number of likes"),
    max_total_votes: Optional[int] = Query(None, ge=0, description="Maximum total votes"),
    quality_tiers: Optional[List[str]] = Query(None, description="Filter by quality tiers"),
    age_categories: Optional[List[str]] = Query(None, description="Filter by age categories"),
    exclude_paid: Optional[bool] = Query(False, description="Exclude paid-only problems"),
    require_solution: Optional[bool] = Query(False, description="Require official solution"),
    sort_by: str = Query("total_frequency", description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    
    # Dependencies
    pagination: PaginationParams = Depends(get_pagination_params),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get top problems ranked across all companies.
    
    Returns aggregated statistics for the most frequently asked problems,
    with support for filtering by company, difficulty, topics, and other criteria.
    """
    try:
        logger.info(f"Getting top problems with filters", extra={"correlation_id": correlation_id})
        
        # Validate sort field
        valid_sort_fields = [
            "total_frequency", "company_count", "avg_acceptance_rate", 
            "difficulty", "title", "trend_score", "originality_score", 
            "likes", "total_votes", "quality_percentile", "engagement_score"
        ]
        sort_by = validate_sort_field(sort_by, valid_sort_fields)
        
        # Validate companies and topics against dataset
        companies = dataset_validator.validate_companies(companies)
        topics = dataset_validator.validate_topics(topics)
        
        # Create filter criteria
        filters = FilterCriteria(
            companies=companies,
            timeframes=[Timeframe(tf.value) for tf in timeframes] if timeframes else None,
            difficulties=[Difficulty(d.value) for d in difficulties] if difficulties else None,
            topics=topics,
            min_frequency=min_frequency,
            max_frequency=max_frequency,
            min_acceptance_rate=min_acceptance_rate,
            max_acceptance_rate=max_acceptance_rate
        )
        
        # Get top problems from analytics engine
        top_problems_df = analytics_engine.get_top_problems(
            dataset, 
            filters=filters, 
            limit=limit * 2,  # Get more results for pagination
            sort_by=sort_by
        )
        
        if top_problems_df.empty:
            logger.warning("No problems found matching criteria", extra={"correlation_id": correlation_id})
            return create_paginated_response([], {
                "total": 0, "page": pagination.page, "page_size": pagination.page_size,
                "total_pages": 0, "has_next": False, "has_previous": False
            })
        
        # Enrich with metadata if service is available
        if metadata_lookup_service.is_ready():
            top_problems_df = metadata_lookup_service.enrich_problems_dataframe(top_problems_df)
            
            # Apply quality filters if specified
            quality_filters = {}
            if min_originality_score is not None:
                quality_filters['min_originality_score'] = min_originality_score
            if max_originality_score is not None:
                quality_filters['max_originality_score'] = max_originality_score
            if min_likes is not None:
                quality_filters['min_likes'] = min_likes
            if max_total_votes is not None:
                quality_filters['max_total_votes'] = max_total_votes
            if quality_tiers:
                quality_filters['quality_tiers'] = quality_tiers
            if age_categories:
                quality_filters['age_categories'] = age_categories
            if exclude_paid:
                quality_filters['exclude_paid'] = exclude_paid
            if require_solution:
                quality_filters['require_solution'] = require_solution
            
            if quality_filters:
                top_problems_df = metadata_lookup_service.get_quality_filtered_problems(
                    top_problems_df, quality_filters
                )
                logger.info(f"Applied quality filters, {len(top_problems_df)} problems remaining", 
                           extra={"correlation_id": correlation_id})
            
            logger.info("Enriched top problems with metadata", extra={"correlation_id": correlation_id})
        
        # Apply sorting
        top_problems_df = apply_sorting(top_problems_df, sort_by, sort_order.value)
        
        # Paginate results
        paginated_df, pagination_metadata = paginate_dataframe(top_problems_df, pagination)
        
        # Convert to response format
        problems_data = dataframe_to_dict_list(paginated_df)
        
        logger.info(
            f"Returning {len(problems_data)} top problems (page {pagination.page})",
            extra={"correlation_id": correlation_id}
        )
        
        return create_paginated_response(problems_data, pagination_metadata)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error getting top problems: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to get top problems: {str(e)}")


@router.get("/search", response_model=Dict[str, Any])
async def search_problems(
    # Query parameters
    title_contains: Optional[str] = Query(None, description="Search in problem titles"),
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    difficulties: Optional[List[DifficultyFilter]] = Query(None, description="Filter by difficulties"),
    topics: Optional[List[str]] = Query(None, description="Filter by topics"),
    min_frequency: Optional[float] = Query(None, ge=0, description="Minimum frequency"),
    max_frequency: Optional[float] = Query(None, ge=0, description="Maximum frequency"),
    min_acceptance_rate: Optional[float] = Query(None, ge=0, le=1, description="Minimum acceptance rate"),
    max_acceptance_rate: Optional[float] = Query(None, ge=0, le=1, description="Maximum acceptance rate"),
    # Quality-based filters
    min_originality_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum originality score"),
    max_originality_score: Optional[float] = Query(None, ge=0, le=1, description="Maximum originality score"),
    min_likes: Optional[int] = Query(None, ge=0, description="Minimum number of likes"),
    max_total_votes: Optional[int] = Query(None, ge=0, description="Maximum total votes"),
    quality_tiers: Optional[List[str]] = Query(None, description="Filter by quality tiers"),
    age_categories: Optional[List[str]] = Query(None, description="Filter by age categories"),
    exclude_paid: Optional[bool] = Query(False, description="Exclude paid-only problems"),
    require_solution: Optional[bool] = Query(False, description="Require official solution"),
    sort_by: str = Query("frequency", description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    
    # Dependencies
    pagination: PaginationParams = Depends(get_pagination_params),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Search problems with flexible filtering criteria.
    
    Supports text search in problem titles and comprehensive filtering
    by company, difficulty, topics, frequency, and acceptance rate.
    """
    try:
        logger.info(f"Searching problems with criteria", extra={"correlation_id": correlation_id})
        
        # Validate sort field
        valid_sort_fields = [
            "frequency", "acceptance_rate", "difficulty", "title", 
            "company", "timeframe", "originality_score", "likes", 
            "total_votes", "quality_percentile", "engagement_score"
        ]
        sort_by = validate_sort_field(sort_by, valid_sort_fields)
        
        # Validate companies and topics against dataset
        companies = dataset_validator.validate_companies(companies)
        topics = dataset_validator.validate_topics(topics)
        
        # Clean search term
        if title_contains:
            title_contains = clean_search_term(title_contains)
            if not title_contains:
                raise ValidationError("Search term cannot be empty")
        
        # Create search criteria
        search_criteria = {
            "companies": companies,
            "difficulties": [d.value for d in difficulties] if difficulties else None,
            "topics": topics,
            "min_frequency": min_frequency,
            "max_frequency": max_frequency,
            "min_acceptance_rate": min_acceptance_rate,
            "max_acceptance_rate": max_acceptance_rate,
            "sort_by": sort_by,
            "ascending": sort_order.value == "asc",
            "limit": limit * 2  # Get more results for pagination
        }
        
        if title_contains:
            search_criteria["title_contains"] = title_contains
        
        # Search problems using analytics engine
        search_results_df = analytics_engine.search_problems(dataset, search_criteria)
        
        if search_results_df.empty:
            logger.warning("No problems found matching search criteria", extra={"correlation_id": correlation_id})
            return create_paginated_response([], {
                "total": 0, "page": pagination.page, "page_size": pagination.page_size,
                "total_pages": 0, "has_next": False, "has_previous": False
            })
        
        # Enrich with metadata if service is available
        if metadata_lookup_service.is_ready():
            search_results_df = metadata_lookup_service.enrich_problems_dataframe(search_results_df)
            
            # Apply quality filters if specified
            quality_filters = {}
            if min_originality_score is not None:
                quality_filters['min_originality_score'] = min_originality_score
            if max_originality_score is not None:
                quality_filters['max_originality_score'] = max_originality_score
            if min_likes is not None:
                quality_filters['min_likes'] = min_likes
            if max_total_votes is not None:
                quality_filters['max_total_votes'] = max_total_votes
            if quality_tiers:
                quality_filters['quality_tiers'] = quality_tiers
            if age_categories:
                quality_filters['age_categories'] = age_categories
            if exclude_paid:
                quality_filters['exclude_paid'] = exclude_paid
            if require_solution:
                quality_filters['require_solution'] = require_solution
            
            if quality_filters:
                search_results_df = metadata_lookup_service.get_quality_filtered_problems(
                    search_results_df, quality_filters
                )
                logger.info(f"Applied quality filters, {len(search_results_df)} problems remaining", 
                           extra={"correlation_id": correlation_id})
            
            logger.info("Enriched search results with metadata", extra={"correlation_id": correlation_id})
        
        # Paginate results
        paginated_df, pagination_metadata = paginate_dataframe(search_results_df, pagination)
        
        # Convert to response format
        problems_data = dataframe_to_dict_list(paginated_df)
        
        logger.info(
            f"Returning {len(problems_data)} search results (page {pagination.page})",
            extra={"correlation_id": correlation_id}
        )
        
        return create_paginated_response(problems_data, pagination_metadata)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error searching problems: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to search problems: {str(e)}")


@router.get("/{title_slug}/preview", response_model=ProblemPreviewResponse)
async def get_problem_preview(
    title_slug: str,
    dataset = Depends(get_unified_dataset),
    correlation_id: str = Depends(get_correlation_id)
):
    """Get a sanitized preview of a specific problem."""

    slug = title_slug.strip().lower()
    if not slug:
        raise HTTPException(status_code=400, detail="title_slug must be provided")

    try:
        record = None

        if 'title_slug' in dataset.columns:
            slug_series = dataset['title_slug'].astype('string').str.strip().str.lower()
            matches = dataset.loc[slug_series == slug]
            if not matches.empty:
                record = matches.iloc[0]

        if record is None and 'link' in dataset.columns:
            derived_slugs = dataset['link'].apply(_extract_slug_from_link)
            matches = dataset.loc[derived_slugs == slug]
            if not matches.empty:
                record = matches.iloc[0]

        if record is None:
            raise HTTPException(status_code=404, detail="Problem preview not found")

        preview = _build_problem_preview(record)

        if metadata_lookup_service.is_ready():
            meta_key = preview.title
            if not meta_key:
                meta_key = _safe_str(_get_scalar(record, 'title'))
            if meta_key:
                metadata = metadata_lookup_service.get_problem_metadata(meta_key)
                if metadata:
                    if preview.likes is None:
                        preview.likes = _safe_int(metadata.get('likes'))
                    if preview.dislikes is None:
                        preview.dislikes = _safe_int(metadata.get('dislikes'))
                    if not preview.difficulty:
                        preview.difficulty = _safe_str(metadata.get('difficulty'))
                    if not preview.topic_tags and metadata.get('topic_tags'):
                        preview.topic_tags = metadata.get('topic_tags')
                    if not preview.content_text and metadata.get('content_preview'):
                        preview.content_text = _safe_str(metadata.get('content_preview'))

        logger.info("Providing preview for problem %s", slug, extra={"correlation_id": correlation_id})
        return ProblemPreviewResponse(preview=preview)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error generating preview for %s: %s", slug, exc, extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to generate preview for {title_slug}: {exc}")


@router.get("/{problem_title}", response_model=Dict[str, Any])
async def get_problem_details(
    problem_title: str,
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    
    # Dependencies
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get detailed information for a specific problem.
    
    Returns all instances of the problem across different companies and timeframes,
    with aggregated statistics and company-specific data.
    """
    try:
        logger.info(f"Getting details for problem: {problem_title}", extra={"correlation_id": correlation_id})
        
        # Clean problem title
        problem_title = problem_title.strip()
        if not problem_title:
            raise ValidationError("Problem title cannot be empty")
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Filter dataset for the specific problem
        problem_data = dataset[dataset['title'].str.contains(problem_title, case=False, na=False)]
        
        if companies:
            problem_data = problem_data[problem_data['company'].isin(companies)]
        
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            problem_data = problem_data[problem_data['timeframe'].isin(timeframe_values)]
        
        if problem_data.empty:
            logger.warning(f"Problem not found: {problem_title}", extra={"correlation_id": correlation_id})
            raise HTTPException(status_code=404, detail=f"Problem '{problem_title}' not found")
        
        # Get exact matches first, then partial matches
        exact_matches = problem_data[problem_data['title'].str.lower() == problem_title.lower()]
        if not exact_matches.empty:
            problem_data = exact_matches
        
        # Calculate aggregated statistics
        stats = {
            "title": problem_data['title'].iloc[0],
            "total_instances": len(problem_data),
            "companies": sorted(problem_data['company'].unique().tolist()),
            "timeframes": sorted(problem_data['timeframe'].unique().tolist()),
            "difficulties": problem_data['difficulty'].unique().tolist(),
            "avg_frequency": float(problem_data['frequency'].mean()),
            "max_frequency": float(problem_data['frequency'].max()),
            "min_frequency": float(problem_data['frequency'].min()),
            "avg_acceptance_rate": float(problem_data['acceptance_rate'].mean()),
            "link": problem_data['link'].iloc[0] if 'link' in problem_data.columns else None,
            "all_topics": []
        }
        
        # Extract all topics
        all_topics = set()
        for topics_str in problem_data['topics'].dropna():
            if isinstance(topics_str, str):
                topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                all_topics.update(topics)
        stats["all_topics"] = sorted(list(all_topics))
        
        # Get company-specific data
        company_data = []
        for _, row in problem_data.iterrows():
            company_entry = {
                "company": row['company'],
                "timeframe": row['timeframe'],
                "frequency": float(row['frequency']),
                "acceptance_rate": float(row['acceptance_rate']),
                "difficulty": row['difficulty'],
                "topics": [t.strip() for t in row['topics'].split(',') if t.strip()] if pd.notna(row['topics']) else []
            }
            company_data.append(company_entry)
        
        # Sort company data by frequency
        company_data.sort(key=lambda x: x['frequency'], reverse=True)
        
        result = {
            "problem_stats": stats,
            "company_data": company_data
        }
        
        logger.info(
            f"Returning details for problem: {problem_title} ({len(company_data)} instances)",
            extra={"correlation_id": correlation_id}
        )
        
        return result
        
    except ValidationError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting problem details: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to get problem details: {str(e)}")


@router.post("/recommendations", response_model=StudyPlanRecommendationResponse)
async def recommend_problems_for_study_plan(
    request: StudyPlanRecommendationRequest,
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """Recommend problems tailored for study plan generation."""

    try:
        logger.info(
            "Generating study plan recommendations",
            extra={
                "correlation_id": correlation_id,
                "skill_level": request.skill_level.value,
                "companies": request.companies,
                "focus_topics": request.focus_topics,
                "duration_weeks": request.duration_weeks,
                "daily_goal": request.daily_goal
            }
        )

        total_needed = request.duration_weeks * 7 * request.daily_goal
        if total_needed <= 0:
            raise ValidationError("Requested study plan size must be greater than zero")

        companies = dataset_validator.validate_companies(request.companies)
        focus_topics = dataset_validator.validate_topics(request.focus_topics)

        required_columns = {'title', 'company', 'difficulty', 'frequency', 'topics', 'link'}
        missing_columns = required_columns - set(dataset.columns)
        if missing_columns:
            raise DataProcessingError(
                f"Unified dataset is missing required columns: {', '.join(sorted(missing_columns))}"
            )

        df = dataset[['title', 'company', 'difficulty', 'frequency', 'topics', 'link', 'acceptance_rate']].copy()
        df['frequency'] = pd.to_numeric(df['frequency'], errors='coerce')
        df['acceptance_rate'] = pd.to_numeric(df['acceptance_rate'], errors='coerce')

        if companies:
            df = df[df['company'].isin(companies)]

        if focus_topics:
            focus_lower = [topic.lower() for topic in focus_topics]

            def has_focus_topic(topics_value: Any) -> bool:
                if not isinstance(topics_value, str):
                    return False
                topic_tokens = [t.strip().lower() for t in topics_value.split(',') if t.strip()]
                return any(topic in topic_tokens for topic in focus_lower)

            df = df[df['topics'].apply(has_focus_topic)]

        if df.empty:
            logger.warning("No problems found after applying filters", extra={"correlation_id": correlation_id})
            return StudyPlanRecommendationResponse(
                recommendations=[],
                requested_count=total_needed,
                selected_count=0,
                available_pool=0,
                skill_level=request.skill_level,
                filters={
                    "companies": companies,
                    "focus_topics": focus_topics
                }
            )

        def collect_topics(series: pd.Series) -> List[str]:
            topics: set[str] = set()
            for value in series.dropna():
                for token in str(value).split(','):
                    token = token.strip()
                    if token:
                        topics.add(token)
            return sorted(topics)

        def first_valid_link(series: pd.Series) -> Optional[str]:
            for value in series:
                if isinstance(value, str) and value.startswith('http'):
                    return value
            for value in series:
                if isinstance(value, str) and value:
                    return value
            return None

        def primary_difficulty(series: pd.Series) -> Optional[str]:
            non_null = series.dropna()
            if non_null.empty:
                return None
            mode = non_null.mode()
            if not mode.empty:
                return str(mode.iloc[0])
            return str(non_null.iloc[0])

        aggregated = (
            df.groupby('title')
            .agg(
                difficulty=('difficulty', primary_difficulty),
                acceptance_rate=('acceptance_rate', 'mean'),
                frequency=('frequency', 'mean'),
                topics=('topics', collect_topics),
                companies=('company', lambda x: sorted(set(x.dropna()))),
                link=('link', first_valid_link)
            )
            .reset_index()
        )

        if aggregated.empty:
            return StudyPlanRecommendationResponse(
                recommendations=[],
                requested_count=total_needed,
                selected_count=0,
                available_pool=0,
                skill_level=request.skill_level,
                filters={
                    "companies": companies,
                    "focus_topics": focus_topics
                }
            )

        difficulty_priority_map = {
            StudyPlanSkillLevel.BEGINNER: ['EASY', 'MEDIUM', 'HARD'],
            StudyPlanSkillLevel.INTERMEDIATE: ['MEDIUM', 'EASY', 'HARD'],
            StudyPlanSkillLevel.ADVANCED: ['HARD', 'MEDIUM', 'EASY']
        }
        difficulty_rank = {value: index for index, value in enumerate(difficulty_priority_map[request.skill_level])}

        aggregated['difficulty_rank'] = aggregated['difficulty'].map(
            lambda x: difficulty_rank.get(str(x), len(difficulty_rank))
        )
        aggregated['frequency'] = aggregated['frequency'].fillna(0.0)
        aggregated['acceptance_rate'] = aggregated['acceptance_rate'].fillna(float('nan'))

        if request.skill_level == StudyPlanSkillLevel.ADVANCED:
            aggregated = aggregated.sort_values(
                by=['difficulty_rank', 'frequency', 'acceptance_rate'],
                ascending=[True, False, True]
            )
        else:
            aggregated = aggregated.sort_values(
                by=['difficulty_rank', 'frequency', 'acceptance_rate'],
                ascending=[True, False, False]
            )

        available_pool = len(aggregated)
        requested_companies_set = set(companies or [])
        company_counts: defaultdict[str, int] = defaultdict(int)
        for company in requested_companies_set:
            company_counts[company] = 0

        max_per_company = request.max_per_company or (
            math.ceil(total_needed / max(len(requested_companies_set), 1)) if requested_companies_set else None
        )

        recommendations: List[RecommendedProblem] = []

        for record in aggregated.to_dict('records'):
            candidate_companies = record.get('companies') or []
            preferred = (
                [c for c in candidate_companies if c in requested_companies_set]
                if requested_companies_set else candidate_companies
            )

            if not preferred:
                preferred = candidate_companies

            if not preferred:
                continue

            chosen_company = min(preferred, key=lambda c: company_counts[c])

            if request.balance_companies and max_per_company is not None and company_counts[chosen_company] >= max_per_company:
                alternatives = sorted(preferred, key=lambda c: company_counts[c])
                chosen_company = None
                for alt in alternatives:
                    if company_counts[alt] < max_per_company:
                        chosen_company = alt
                        break
                if chosen_company is None:
                    continue

            if request.balance_companies and requested_companies_set:
                average_count = sum(company_counts[c] for c in requested_companies_set) / max(len(requested_companies_set), 1)
                if company_counts[chosen_company] > average_count + 2:
                    alternatives = sorted(preferred, key=lambda c: company_counts[c])
                    for alt in alternatives:
                        if company_counts[alt] <= average_count + 1:
                            chosen_company = alt
                            break

            company_counts[chosen_company] += 1

            recommendations.append(
                RecommendedProblem(
                    title=record['title'],
                    difficulty=record.get('difficulty'),
                    topics=record.get('topics') or [],
                    acceptance_rate=(
                        float(record['acceptance_rate'])
                        if record.get('acceptance_rate') is not None and not math.isnan(record['acceptance_rate'])
                        else None
                    ),
                    frequency=(float(record['frequency']) if record.get('frequency') is not None else None),
                    companies=record.get('companies') or [],
                    recommended_company=chosen_company,
                    link=record.get('link')
                )
            )

            if len(recommendations) >= total_needed:
                break

        selected_count = len(recommendations)

        return StudyPlanRecommendationResponse(
            recommendations=recommendations,
            requested_count=total_needed,
            selected_count=selected_count,
            available_pool=available_pool,
            skill_level=request.skill_level,
            filters={
                "companies": companies,
                "focus_topics": focus_topics,
                "balance_companies": request.balance_companies,
                "max_per_company": request.max_per_company
            }
        )

    except ValidationError:
        raise
    except Exception as exc:
        logger.error(
            "Failed to generate study plan recommendations",
            extra={"correlation_id": correlation_id, "error": str(exc)}
        )
        raise DataProcessingError(f"Failed to generate study plan recommendations: {str(exc)}")


@router.get("/quality-analysis", response_model=Dict[str, Any])
async def get_quality_analysis(
    # Quality analysis parameters
    analysis_type: str = Query("overview", description="Type of analysis: overview, hidden_gems, classics, rising_stars"),
    min_originality: float = Query(0.85, ge=0, le=1, description="Minimum originality score for gems/stars"),
    max_total_votes: int = Query(1000, ge=0, description="Maximum total votes for hidden gems"),
    min_likes: int = Query(5000, ge=0, description="Minimum likes for classics"),
    min_votes: int = Query(50, ge=0, description="Minimum votes for rising stars"),
    max_votes: int = Query(500, ge=0, description="Maximum votes for rising stars"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    exclude_paid: bool = Query(True, description="Exclude paid-only problems"),
    
    # Dependencies
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get quality-based analysis and recommendations.
    
    Provides various types of quality analysis including:
    - Overview: General quality statistics and insights
    - Hidden Gems: High-quality, less-known problems
    - Classics: Most essential interview problems
    - Rising Stars: Newer problems gaining traction
    """
    try:
        logger.info(f"Getting quality analysis: {analysis_type}", extra={"correlation_id": correlation_id})
        
        if not metadata_lookup_service.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="Quality analysis service unavailable - metadata not loaded"
            )
        
        if analysis_type == "overview":
            # Get comprehensive quality analysis
            result = {
                "analysis_type": "overview",
                "quality_statistics": metadata_lookup_service.processor.get_quality_analysis_summary(),
                "difficulty_reality": metadata_lookup_service.processor.analyze_difficulty_reality(),
                "metadata_statistics": metadata_lookup_service.processor.get_metadata_statistics(),
                "cache_stats": metadata_lookup_service.get_cache_statistics()
            }
            
        elif analysis_type == "hidden_gems":
            # Find hidden gems
            gems = metadata_lookup_service.processor.find_hidden_gems(
                min_originality=min_originality,
                max_total_votes=max_total_votes,
                limit=limit,
                exclude_paid=exclude_paid
            )
            result = {
                "analysis_type": "hidden_gems",
                "problems": gems,
                "criteria": {
                    "min_originality": min_originality,
                    "max_total_votes": max_total_votes,
                    "exclude_paid": exclude_paid
                },
                "count": len(gems)
            }
            
        elif analysis_type == "classics":
            # Find interview classics
            classics = metadata_lookup_service.processor.find_interview_classics(
                min_likes=min_likes,
                limit=limit,
                exclude_paid=exclude_paid
            )
            result = {
                "analysis_type": "classics",
                "problems": classics,
                "criteria": {
                    "min_likes": min_likes,
                    "exclude_paid": exclude_paid
                },
                "count": len(classics)
            }
            
        elif analysis_type == "rising_stars":
            # Find rising stars
            rising = metadata_lookup_service.processor.find_rising_stars(
                min_originality=min_originality,
                min_votes=min_votes,
                max_votes=max_votes,
                limit=limit,
                exclude_paid=exclude_paid
            )
            result = {
                "analysis_type": "rising_stars",
                "problems": rising,
                "criteria": {
                    "min_originality": min_originality,
                    "min_votes": min_votes,
                    "max_votes": max_votes,
                    "exclude_paid": exclude_paid
                },
                "count": len(rising)
            }
            
        else:
            raise ValidationError(f"Invalid analysis type: {analysis_type}")
        
        logger.info(
            f"Quality analysis completed: {analysis_type}",
            extra={"correlation_id": correlation_id}
        )
        
        return result
        
    except ValidationError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quality analysis: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to perform quality analysis: {str(e)}")


@router.get("/quality-ranking", response_model=Dict[str, Any])
async def get_quality_ranking(
    # Ranking parameters
    strategy: str = Query("balanced", description="Ranking strategy: quality, popularity, balanced, hidden_gems"),
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    difficulties: Optional[List[DifficultyFilter]] = Query(None, description="Filter by difficulties"),
    topics: Optional[List[str]] = Query(None, description="Filter by topics"),
    exclude_paid: bool = Query(True, description="Exclude paid-only problems"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    
    # Dependencies
    pagination: PaginationParams = Depends(get_pagination_params),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get problems ranked by quality metrics.
    
    Provides different ranking strategies:
    - Quality: Rank by originality score and engagement
    - Popularity: Rank by likes and community votes
    - Balanced: Balanced ranking considering multiple factors
    - Hidden Gems: High quality but low exposure
    """
    try:
        logger.info(f"Getting quality ranking: {strategy}", extra={"correlation_id": correlation_id})
        
        if not metadata_lookup_service.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="Quality ranking service unavailable - metadata not loaded"
            )
        
        # Validate inputs
        companies = dataset_validator.validate_companies(companies)
        topics = dataset_validator.validate_topics(topics)
        
        # Filter dataset
        filtered_df = dataset.copy()
        
        if companies:
            filtered_df = filtered_df[filtered_df['company'].isin(companies)]
        
        if difficulties:
            difficulty_values = [d.value for d in difficulties]
            filtered_df = filtered_df[filtered_df['difficulty'].isin(difficulty_values)]
        
        if topics:
            # Filter by topics (assuming topics are comma-separated in the dataset)
            topic_filter = filtered_df['topics'].str.contains('|'.join(topics), case=False, na=False)
            filtered_df = filtered_df[topic_filter]
        
        if filtered_df.empty:
            logger.warning("No problems found after filtering", extra={"correlation_id": correlation_id})
            return create_paginated_response([], {
                "total": 0, "page": pagination.page, "page_size": pagination.page_size,
                "total_pages": 0, "has_next": False, "has_previous": False
            })
        
        # Apply quality ranking
        ranked_df = metadata_lookup_service.get_quality_based_ranking(filtered_df, strategy)
        
        # Apply paid filter if requested
        if exclude_paid and 'is_paid_only' in ranked_df.columns:
            ranked_df = ranked_df[~ranked_df['is_paid_only']]
        
        # Limit results
        if len(ranked_df) > limit:
            ranked_df = ranked_df.head(limit)
        
        # Paginate results
        paginated_df, pagination_metadata = paginate_dataframe(ranked_df, pagination)
        
        # Convert to response format
        problems_data = dataframe_to_dict_list(paginated_df)
        
        result = create_paginated_response(problems_data, pagination_metadata)
        result["ranking_strategy"] = strategy
        result["filters_applied"] = {
            "companies": companies,
            "difficulties": [d.value for d in difficulties] if difficulties else None,
            "topics": topics,
            "exclude_paid": exclude_paid
        }
        
        logger.info(
            f"Quality ranking completed: {strategy}, {len(problems_data)} results",
            extra={"correlation_id": correlation_id}
        )
        
        return result
        
    except ValidationError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quality ranking: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to perform quality ranking: {str(e)}")


@router.get("/metadata-statistics", response_model=Dict[str, Any])
async def get_metadata_statistics(
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get comprehensive metadata statistics for dashboard overview.
    
    Returns statistics about the loaded metadata including:
    - Total problems with metadata
    - Quality distribution
    - Coverage by difficulty and categories
    - Value ranges for key metrics
    """
    try:
        logger.info("Getting metadata statistics", extra={"correlation_id": correlation_id})
        
        if not metadata_lookup_service.is_ready():
            return {
                "loaded": False,
                "error": "Metadata service not available",
                "message": "Quality features are currently unavailable"
            }
        
        stats = metadata_lookup_service.processor.get_metadata_statistics()
        
        logger.info("Metadata statistics retrieved successfully", extra={"correlation_id": correlation_id})
        return stats
        
    except Exception as e:
        logger.error(f"Error getting metadata statistics: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to get metadata statistics: {str(e)}")
