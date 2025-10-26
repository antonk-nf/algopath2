"""Core data models for the LeetCode Analytics API."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum


class Difficulty(str, Enum):
    """Problem difficulty levels."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    UNKNOWN = "UNKNOWN"


class Timeframe(str, Enum):
    """Time window categories."""
    THIRTY_DAYS = "30d"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"
    MORE_THAN_SIX_MONTHS = "6m+"
    ALL = "all"


@dataclass
class CSVFileInfo:
    """Information about a CSV file to be processed."""
    file_path: str
    company: str
    timeframe: Timeframe
    last_modified: datetime


@dataclass
class ProblemRecord:
    """Unified problem record after processing."""
    difficulty: Difficulty
    title: str
    frequency: float
    acceptance_rate: float
    link: str
    topics: List[str]
    company: str
    timeframe: Timeframe
    source_file: str
    last_updated: datetime


@dataclass
class ProblemStats:
    """Aggregated statistics for a problem across companies."""
    title: str
    total_frequency: float
    company_count: int
    avg_acceptance_rate: float
    difficulty: Difficulty
    primary_topics: List[str]
    trend_score: float


@dataclass
class ValidationResult:
    """Result of data validation operations."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    processed_rows: int
    skipped_rows: int


@dataclass
class FilterCriteria:
    """Criteria for filtering analytics queries."""
    companies: Optional[List[str]] = None
    timeframes: Optional[List[Timeframe]] = None
    difficulties: Optional[List[Difficulty]] = None
    topics: Optional[List[str]] = None
    min_frequency: Optional[float] = None
    max_frequency: Optional[float] = None
    min_acceptance_rate: Optional[float] = None
    max_acceptance_rate: Optional[float] = None