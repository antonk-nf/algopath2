"""Pydantic models for API request/response validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..models.data_models import Difficulty, Timeframe


class DifficultyFilter(str, Enum):
    """Difficulty filter options for API."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    UNKNOWN = "UNKNOWN"


class TimeframeFilter(str, Enum):
    """Timeframe filter options for API."""
    THIRTY_DAYS = "30d"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"
    MORE_THAN_SIX_MONTHS = "6m+"
    ALL = "all"


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class ProblemResponse(BaseModel):
    """Response model for individual problem data."""
    title: str
    difficulty: str
    frequency: float
    acceptance_rate: float
    link: str
    topics: List[str]
    company: str
    timeframe: str
    # Metadata fields (optional)
    likes: Optional[int] = None
    dislikes: Optional[int] = None
    originality_score: Optional[float] = None
    total_votes: Optional[int] = None
    quality_percentile: Optional[float] = None
    quality_tier: Optional[str] = None
    age_category: Optional[str] = None
    engagement_score: Optional[float] = None
    has_solution: Optional[bool] = None
    has_video_solution: Optional[bool] = None
    is_paid_only: Optional[bool] = None
    metadata_available: Optional[bool] = None


class ProblemStatsResponse(BaseModel):
    """Response model for aggregated problem statistics."""
    title: str
    total_frequency: float
    company_count: int
    avg_acceptance_rate: float
    difficulty: str
    primary_topics: List[str]
    trend_score: Optional[float] = None
    # Metadata fields (optional)
    likes: Optional[int] = None
    dislikes: Optional[int] = None
    originality_score: Optional[float] = None
    total_votes: Optional[int] = None
    quality_percentile: Optional[float] = None
    quality_tier: Optional[str] = None
    age_category: Optional[str] = None
    engagement_score: Optional[float] = None


class TopProblemsRequest(BaseModel):
    """Request model for top problems endpoint."""
    companies: Optional[List[str]] = Field(None, description="Filter by specific companies")
    timeframes: Optional[List[TimeframeFilter]] = Field(None, description="Filter by timeframes")
    difficulties: Optional[List[DifficultyFilter]] = Field(None, description="Filter by difficulties")
    topics: Optional[List[str]] = Field(None, description="Filter by topics")
    min_frequency: Optional[float] = Field(None, ge=0, description="Minimum frequency threshold")
    max_frequency: Optional[float] = Field(None, ge=0, description="Maximum frequency threshold")
    min_acceptance_rate: Optional[float] = Field(None, ge=0, le=1, description="Minimum acceptance rate")
    max_acceptance_rate: Optional[float] = Field(None, ge=0, le=1, description="Maximum acceptance rate")
    # Quality-based filters
    min_originality_score: Optional[float] = Field(None, ge=0, le=1, description="Minimum originality score")
    max_originality_score: Optional[float] = Field(None, ge=0, le=1, description="Maximum originality score")
    min_likes: Optional[int] = Field(None, ge=0, description="Minimum number of likes")
    max_total_votes: Optional[int] = Field(None, ge=0, description="Maximum total votes")
    quality_tiers: Optional[List[str]] = Field(None, description="Filter by quality tiers")
    age_categories: Optional[List[str]] = Field(None, description="Filter by age categories")
    exclude_paid: Optional[bool] = Field(False, description="Exclude paid-only problems")
    require_solution: Optional[bool] = Field(False, description="Require official solution")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    sort_by: str = Field("total_frequency", description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")


class ProblemSearchRequest(BaseModel):
    """Request model for problem search endpoint."""
    title_contains: Optional[str] = Field(None, description="Search in problem titles")
    companies: Optional[List[str]] = Field(None, description="Filter by companies")
    difficulties: Optional[List[DifficultyFilter]] = Field(None, description="Filter by difficulties")
    topics: Optional[List[str]] = Field(None, description="Filter by topics")
    min_frequency: Optional[float] = Field(None, ge=0, description="Minimum frequency")
    max_frequency: Optional[float] = Field(None, ge=0, description="Maximum frequency")
    min_acceptance_rate: Optional[float] = Field(None, ge=0, le=1, description="Minimum acceptance rate")
    max_acceptance_rate: Optional[float] = Field(None, ge=0, le=1, description="Maximum acceptance rate")
    # Quality-based filters
    min_originality_score: Optional[float] = Field(None, ge=0, le=1, description="Minimum originality score")
    max_originality_score: Optional[float] = Field(None, ge=0, le=1, description="Maximum originality score")
    min_likes: Optional[int] = Field(None, ge=0, description="Minimum number of likes")
    max_total_votes: Optional[int] = Field(None, ge=0, description="Maximum total votes")
    quality_tiers: Optional[List[str]] = Field(None, description="Filter by quality tiers")
    age_categories: Optional[List[str]] = Field(None, description="Filter by age categories")
    exclude_paid: Optional[bool] = Field(False, description="Exclude paid-only problems")
    require_solution: Optional[bool] = Field(False, description="Require official solution")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    sort_by: str = Field("frequency", description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")


class TopicTrendResponse(BaseModel):
    """Response model for topic trend analysis."""
    topic: str
    timeframe_frequencies: Dict[str, float]
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float


class CompanyStatsResponse(BaseModel):
    """Response model for company statistics."""
    company: str
    total_problems: int
    unique_problems: int
    avg_frequency: float
    avg_acceptance_rate: float
    difficulty_distribution: Dict[str, int]
    top_topics: List[str]
    timeframe_coverage: List[str]


class CorrelationResponse(BaseModel):
    """Response model for correlation analysis."""
    analysis_type: str
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    top_correlations: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    data: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class StudyPlanSkillLevel(str, Enum):
    """Skill level options for study plan recommendations."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class StudyPlanRecommendationRequest(BaseModel):
    """Request model for study plan problem recommendations."""
    companies: Optional[List[str]] = Field(None, description="Target companies to prioritize")
    focus_topics: Optional[List[str]] = Field(None, description="Topics to emphasize")
    skill_level: StudyPlanSkillLevel = Field(StudyPlanSkillLevel.INTERMEDIATE, description="Candidate skill level")
    duration_weeks: int = Field(..., ge=1, le=52, description="Study duration in weeks")
    daily_goal: int = Field(..., ge=1, le=20, description="Problems per day")
    balance_companies: bool = Field(True, description="Balance problems across companies")
    max_per_company: Optional[int] = Field(None, gt=0, description="Maximum problems per company")

    @validator('focus_topics')
    def normalize_topics(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        normalized = [topic.strip() for topic in value if topic and topic.strip()]
        return normalized or None


class RecommendedProblem(BaseModel):
    """Response entry for a recommended study problem."""
    title: str
    difficulty: Optional[str]
    topics: List[str]
    acceptance_rate: Optional[float]
    frequency: Optional[float]
    companies: List[str]
    recommended_company: Optional[str]
    link: Optional[str]
    # Quality metrics (optional)
    quality_metrics: Optional[Dict[str, Any]] = None


class StudyPlanRecommendationResponse(BaseModel):
    """Response payload for study plan recommendations."""
    recommendations: List[RecommendedProblem]
    requested_count: int
    selected_count: int
    available_pool: int
    skill_level: StudyPlanSkillLevel
    filters: Dict[str, Any]
    # Quality insights (optional)
    quality_insights: Optional[Dict[str, Any]] = None


class ProblemPreview(BaseModel):
    title: Optional[str] = None
    title_slug: Optional[str] = None
    question_id: Optional[str] = None
    difficulty: Optional[str] = None
    likes: Optional[int] = None
    dislikes: Optional[int] = None
    ac_rate: Optional[float] = None
    is_paid_only: Optional[bool] = None
    has_solution: Optional[bool] = None
    has_video_solution: Optional[bool] = None
    freq_bar: Optional[str] = None
    topic_tags: Optional[List[Dict[str, Any]]] = None
    content_html: Optional[str] = None
    content_text: Optional[str] = None
    metadata_fetched_at: Optional[str] = None


class ProblemPreviewResponse(BaseModel):
    """Response model for problem preview data."""
    preview: ProblemPreview


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    version: str
    data_freshness: Dict[str, Any]
    cache_status: Dict[str, Any]
    system_metrics: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: Dict[str, Any] = Field(
        ...,
        example={
            "code": "VALIDATION_ERROR",
            "message": "Invalid request parameters",
            "details": "Difficulty must be one of: EASY, MEDIUM, HARD",
            "correlation_id": "req_123456789"
        }
    )


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page")

    @validator('page_size')
    def validate_page_size(cls, v):
        if v > 1000:
            raise ValueError('Page size cannot exceed 1000')
        return v
