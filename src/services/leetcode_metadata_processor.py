"""
LeetCode Metadata Processing Service

This service handles loading, processing, and enriching the LeetCode metadata
from the parquet file, calculating quality metrics and providing lookup services.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class LeetCodeMetadataProcessor:
    """
    Processes LeetCode metadata to provide quality metrics and problem enrichment.
    
    Features:
    - Load and process leetcode_metadata.parquet
    - Calculate derived quality metrics (originality_score, total_votes, quality_percentiles)
    - Provide metadata lookup service for problem enrichment
    - Generate quality-based insights and recommendations
    """
    
    def __init__(self, metadata_file_path: str = "leetcode_metadata.parquet"):
        """
        Initialize the metadata processor.
        
        Args:
            metadata_file_path: Path to the leetcode_metadata.parquet file
        """
        self.metadata_file_path = metadata_file_path
        self.metadata_df: Optional[pd.DataFrame] = None
        self.quality_stats: Optional[Dict[str, Any]] = None
        self._is_loaded = False
        
        logger.info(f"LeetCodeMetadataProcessor initialized with file: {metadata_file_path}")
    
    def load_metadata(self) -> bool:
        """
        Load and process the metadata file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            metadata_path = Path(self.metadata_file_path)
            if not metadata_path.exists():
                logger.error(f"Metadata file not found: {self.metadata_file_path}")
                return False
            
            logger.info(f"Loading metadata from {self.metadata_file_path}")
            self.metadata_df = pd.read_parquet(self.metadata_file_path)
            
            # Calculate derived metrics
            self._calculate_derived_metrics()
            
            # Generate quality statistics
            self._generate_quality_stats()
            
            self._is_loaded = True
            logger.info(f"Successfully loaded {len(self.metadata_df)} problems with metadata")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load metadata: {str(e)}")
            return False
    
    def _calculate_derived_metrics(self):
        """Calculate derived quality and age metrics."""
        if self.metadata_df is None:
            return
        
        logger.info("Calculating derived quality metrics")
        
        # Core quality metrics with zero-division protection
        self.metadata_df['total_votes'] = self.metadata_df['likes'] + self.metadata_df['dislikes']
        self.metadata_df['originality_score'] = np.where(
            self.metadata_df['total_votes'] > 0,
            self.metadata_df['likes'] / self.metadata_df['total_votes'],
            0.5  # Default to neutral score for problems with no votes
        )
        
        # Quality percentiles
        self.metadata_df['quality_percentile'] = self.metadata_df['originality_score'].rank(pct=True)
        
        # Age categorization based on total votes (proxy for problem age/exposure)
        self.metadata_df['age_category'] = pd.cut(
            self.metadata_df['total_votes'],
            bins=[0, 100, 1000, 5000, float('inf')],
            labels=['New', 'Growing', 'Established', 'Classic']
        )
        
        # Quality tiers
        self.metadata_df['quality_tier'] = pd.cut(
            self.metadata_df['originality_score'],
            bins=[0, 0.5, 0.7, 0.9, 1.0],
            labels=['Poor', 'Average', 'Good', 'Excellent']
        )
        
        # Difficulty-adjusted acceptance rate (normalized within difficulty)
        for difficulty in self.metadata_df['difficulty'].unique():
            mask = self.metadata_df['difficulty'] == difficulty
            if mask.sum() > 0:
                self.metadata_df.loc[mask, 'difficulty_adjusted_acceptance'] = (
                    self.metadata_df.loc[mask, 'acrate'].rank(pct=True)
                )
        
        # Community engagement score (combines likes and solution availability)
        self.metadata_df['engagement_score'] = (
            (self.metadata_df['likes'] / self.metadata_df['likes'].max()) * 0.6 +
            (self.metadata_df['hassolution'].astype(int)) * 0.3 +
            (self.metadata_df['hasvideosolution'].astype(int)) * 0.1
        )
        
        logger.info("Derived metrics calculated successfully")
    
    def _generate_quality_stats(self):
        """Generate summary statistics for quality metrics."""
        if self.metadata_df is None:
            return
        
        logger.info("Generating quality statistics")
        
        self.quality_stats = {
            'total_problems_with_metadata': len(self.metadata_df),
            'average_originality_score': float(self.metadata_df['originality_score'].mean()),
            'median_originality_score': float(self.metadata_df['originality_score'].median()),
            'quality_distribution': {
                'excellent': int((self.metadata_df['quality_tier'] == 'Excellent').sum()),
                'good': int((self.metadata_df['quality_tier'] == 'Good').sum()),
                'average': int((self.metadata_df['quality_tier'] == 'Average').sum()),
                'poor': int((self.metadata_df['quality_tier'] == 'Poor').sum())
            },
            'age_distribution': {
                'new': int((self.metadata_df['age_category'] == 'New').sum()),
                'growing': int((self.metadata_df['age_category'] == 'Growing').sum()),
                'established': int((self.metadata_df['age_category'] == 'Established').sum()),
                'classic': int((self.metadata_df['age_category'] == 'Classic').sum())
            },
            'community_engagement': {
                'total_likes': int(self.metadata_df['likes'].sum()),
                'total_dislikes': int(self.metadata_df['dislikes'].sum()),
                'average_acceptance_rate': float(self.metadata_df['acrate'].mean()),
                'problems_with_solutions': int(self.metadata_df['hassolution'].sum()),
                'problems_with_video_solutions': int(self.metadata_df['hasvideosolution'].sum()),
                'paid_problems': int(self.metadata_df['ispaidonly'].sum())
            },
            'difficulty_breakdown': {}
        }
        
        # Add difficulty-specific statistics
        for difficulty in self.metadata_df['difficulty'].unique():
            difficulty_data = self.metadata_df[self.metadata_df['difficulty'] == difficulty]
            self.quality_stats['difficulty_breakdown'][difficulty] = {
                'count': len(difficulty_data),
                'avg_originality': float(difficulty_data['originality_score'].mean()),
                'avg_acceptance_rate': float(difficulty_data['acrate'].mean()),
                'avg_likes': float(difficulty_data['likes'].mean()),
                'quality_distribution': {
                    tier: int((difficulty_data['quality_tier'] == tier).sum())
                    for tier in ['Poor', 'Average', 'Good', 'Excellent']
                }
            }
        
        logger.info("Quality statistics generated successfully")
    
    def get_problem_metadata(self, problem_title: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific problem.
        
        Args:
            problem_title: Title of the problem to look up
            
        Returns:
            Dictionary with problem metadata or None if not found
        """
        if not self._is_loaded or self.metadata_df is None:
            logger.warning("Metadata not loaded, cannot lookup problem")
            return None
        
        # Try exact match first
        exact_match = self.metadata_df[self.metadata_df['title'] == problem_title]
        if not exact_match.empty:
            return self._format_problem_metadata(exact_match.iloc[0])
        
        # Try case-insensitive match
        case_insensitive = self.metadata_df[
            self.metadata_df['title'].str.lower() == problem_title.lower()
        ]
        if not case_insensitive.empty:
            return self._format_problem_metadata(case_insensitive.iloc[0])
        
        # Try partial match
        partial_match = self.metadata_df[
            self.metadata_df['title'].str.contains(problem_title, case=False, na=False)
        ]
        if not partial_match.empty:
            # Return the best match (highest originality score)
            best_match = partial_match.loc[partial_match['originality_score'].idxmax()]
            return self._format_problem_metadata(best_match)
        
        logger.debug(f"No metadata found for problem: {problem_title}")
        return None
    
    def _format_problem_metadata(self, row: pd.Series) -> Dict[str, Any]:
        """Format a metadata row into a dictionary."""
        # Safely get content with fallback - use content_text or content_html if available
        content = row.get('content_text', '') or row.get('content_html', '') or row.get('content', '')
        if pd.isna(content):
            content = ''
        content_str = str(content)
        content_preview = content_str[:200] + '...' if len(content_str) > 200 else content_str
        
        # Safely get topic tags
        topic_tags = row.get('topictags', [])
        if not isinstance(topic_tags, list):
            topic_tags = []
        
        return {
            'title': row['title'],
            'difficulty': row['difficulty'],
            'likes': int(row['likes']),
            'dislikes': int(row['dislikes']),
            'originality_score': float(row['originality_score']),
            'total_votes': int(row['total_votes']),
            'quality_percentile': float(row['quality_percentile']),
            'quality_tier': str(row['quality_tier']),
            'age_category': str(row['age_category']),
            'acceptance_rate': float(row['acrate']),
            'difficulty_adjusted_acceptance': float(row.get('difficulty_adjusted_acceptance', 0)),
            'engagement_score': float(row['engagement_score']),
            'has_solution': bool(row['hassolution']),
            'has_video_solution': bool(row['hasvideosolution']),
            'is_paid_only': bool(row['ispaidonly']),
            'content_preview': content_preview,
            'topic_tags': topic_tags
        }
    
    def enrich_problems_dataframe(self, problems_df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich a problems DataFrame with metadata.
        
        Args:
            problems_df: DataFrame with problem data (must have 'title' column)
            
        Returns:
            Enhanced DataFrame with metadata columns
        """
        if not self._is_loaded or self.metadata_df is None:
            logger.warning("Metadata not loaded, returning original DataFrame")
            return problems_df
        
        if 'title' not in problems_df.columns:
            logger.error("Problems DataFrame must have 'title' column for enrichment")
            return problems_df
        
        logger.info(f"Enriching {len(problems_df)} problems with metadata")
        
        # Create a copy to avoid modifying original
        enriched_df = problems_df.copy()
        
        # Merge with metadata on title
        metadata_subset = self.metadata_df[[
            'title', 'likes', 'dislikes', 'originality_score', 'total_votes',
            'quality_percentile', 'quality_tier', 'age_category', 'engagement_score',
            'difficulty_adjusted_acceptance', 'hassolution', 'hasvideosolution', 'ispaidonly'
        ]].copy()
        
        # Perform left join to preserve all original problems
        enriched_df = enriched_df.merge(
            metadata_subset,
            on='title',
            how='left',
            suffixes=('', '_metadata')
        )
        
        # Fill missing values with defaults
        enriched_df['likes'] = enriched_df['likes'].fillna(0)
        enriched_df['dislikes'] = enriched_df['dislikes'].fillna(0)
        enriched_df['originality_score'] = enriched_df['originality_score'].fillna(0.5)
        enriched_df['total_votes'] = enriched_df['total_votes'].fillna(0)
        enriched_df['quality_percentile'] = enriched_df['quality_percentile'].fillna(0.5)
        enriched_df['quality_tier'] = enriched_df['quality_tier'].fillna('Unknown')
        enriched_df['age_category'] = enriched_df['age_category'].fillna('Unknown')
        enriched_df['engagement_score'] = enriched_df['engagement_score'].fillna(0.0)
        enriched_df['difficulty_adjusted_acceptance'] = enriched_df['difficulty_adjusted_acceptance'].fillna(0.5)
        enriched_df['hassolution'] = enriched_df['hassolution'].fillna(False)
        enriched_df['hasvideosolution'] = enriched_df['hasvideosolution'].fillna(False)
        enriched_df['ispaidonly'] = enriched_df['ispaidonly'].fillna(False)
        
        # Rename columns to match expected names in quality filters
        enriched_df = enriched_df.rename(columns={
            'hassolution': 'has_solution',
            'hasvideosolution': 'has_video_solution',
            'ispaidonly': 'is_paid_only'
        })
        
        matched_count = enriched_df['likes'].notna().sum()
        logger.info(f"Successfully enriched {matched_count}/{len(problems_df)} problems with metadata")
        
        return enriched_df
    
    def find_hidden_gems(self, min_originality: float = 0.85, max_total_votes: int = 1000, 
                        limit: int = 20, exclude_paid: bool = True) -> List[Dict[str, Any]]:
        """
        Find high-quality, less-known problems (hidden gems).
        
        Args:
            min_originality: Minimum originality score threshold
            max_total_votes: Maximum total votes (to find less exposed problems)
            limit: Maximum number of results
            exclude_paid: Whether to exclude paid-only problems
            
        Returns:
            List of hidden gem problems with metadata
        """
        if not self._is_loaded or self.metadata_df is None:
            logger.warning("Metadata not loaded, cannot find hidden gems")
            return []
        
        logger.info(f"Finding hidden gems with originality >= {min_originality} and votes <= {max_total_votes}")
        
        # Apply filters
        filtered_df = self.metadata_df[
            (self.metadata_df['originality_score'] >= min_originality) & 
            (self.metadata_df['total_votes'] <= max_total_votes)
        ]
        
        if exclude_paid:
            filtered_df = filtered_df[~filtered_df['ispaidonly']]
        
        # Sort by originality score and engagement
        gems = filtered_df.nlargest(limit, ['originality_score', 'engagement_score'])
        
        result = []
        for _, row in gems.iterrows():
            gem_data = self._format_problem_metadata(row)
            gem_data['why_gem'] = (
                f"High quality ({row['originality_score']:.1%} positive) "
                f"but only {row['total_votes']} community votes"
            )
            result.append(gem_data)
        
        logger.info(f"Found {len(result)} hidden gems")
        return result
    
    def find_interview_classics(self, min_likes: int = 5000, limit: int = 20, 
                               exclude_paid: bool = True) -> List[Dict[str, Any]]:
        """
        Find most essential interview problems (classics).
        
        Args:
            min_likes: Minimum number of likes
            limit: Maximum number of results
            exclude_paid: Whether to exclude paid-only problems
            
        Returns:
            List of interview classic problems with metadata
        """
        if not self._is_loaded or self.metadata_df is None:
            logger.warning("Metadata not loaded, cannot find interview classics")
            return []
        
        logger.info(f"Finding interview classics with likes >= {min_likes}")
        
        # Apply filters
        filtered_df = self.metadata_df[self.metadata_df['likes'] >= min_likes]
        
        if exclude_paid:
            filtered_df = filtered_df[~filtered_df['ispaidonly']]
        
        # Sort by likes and originality score
        classics = filtered_df.nlargest(limit, ['likes', 'originality_score'])
        
        result = []
        for _, row in classics.iterrows():
            classic_data = self._format_problem_metadata(row)
            classic_data['why_classic'] = (
                f"Community favorite with {row['likes']:,} likes "
                f"and {row['originality_score']:.1%} positive rating"
            )
            result.append(classic_data)
        
        logger.info(f"Found {len(result)} interview classics")
        return result
    
    def find_rising_stars(self, min_originality: float = 0.8, min_votes: int = 50, 
                         max_votes: int = 500, limit: int = 20, exclude_paid: bool = True) -> List[Dict[str, Any]]:
        """
        Find newer problems gaining positive traction (rising stars).
        
        Args:
            min_originality: Minimum originality score
            min_votes: Minimum total votes (to ensure some community validation)
            max_votes: Maximum total votes (to find newer problems)
            limit: Maximum number of results
            exclude_paid: Whether to exclude paid-only problems
            
        Returns:
            List of rising star problems with metadata
        """
        if not self._is_loaded or self.metadata_df is None:
            logger.warning("Metadata not loaded, cannot find rising stars")
            return []
        
        logger.info(f"Finding rising stars with originality >= {min_originality} and votes {min_votes}-{max_votes}")
        
        # Apply filters
        filtered_df = self.metadata_df[
            (self.metadata_df['originality_score'] >= min_originality) &
            (self.metadata_df['total_votes'] >= min_votes) &
            (self.metadata_df['total_votes'] <= max_votes)
        ]
        
        if exclude_paid:
            filtered_df = filtered_df[~filtered_df['ispaidonly']]
        
        # Sort by originality score and engagement
        rising = filtered_df.nlargest(limit, ['originality_score', 'engagement_score'])
        
        result = []
        for _, row in rising.iterrows():
            rising_data = self._format_problem_metadata(row)
            rising_data['why_rising'] = (
                f"Newer problem ({row['total_votes']} votes) "
                f"with excellent {row['originality_score']:.1%} rating"
            )
            result.append(rising_data)
        
        logger.info(f"Found {len(result)} rising stars")
        return result
    
    def get_quality_analysis_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive quality analysis summary.
        
        Returns:
            Dictionary with quality analysis data
        """
        if not self._is_loaded or self.quality_stats is None:
            logger.warning("Metadata not loaded, cannot provide quality analysis")
            return {}
        
        return self.quality_stats.copy()
    
    def analyze_difficulty_reality(self) -> Dict[str, Any]:
        """
        Analyze actual vs perceived difficulty using acceptance rates and community feedback.
        
        Returns:
            Dictionary with difficulty reality analysis
        """
        if not self._is_loaded or self.metadata_df is None:
            logger.warning("Metadata not loaded, cannot analyze difficulty reality")
            return {}
        
        logger.info("Analyzing difficulty reality")
        
        # Group by difficulty and calculate statistics
        difficulty_stats = self.metadata_df.groupby('difficulty').agg({
            'acrate': ['mean', 'std', 'min', 'max'],
            'originality_score': 'mean',
            'likes': 'mean',
            'total_votes': 'mean'
        }).round(3)
        
        analysis = {
            'difficulty_analysis': {},
            'insights': []
        }
        
        for difficulty in self.metadata_df['difficulty'].unique():
            if difficulty in difficulty_stats.index:
                stats = difficulty_stats.loc[difficulty]
                analysis['difficulty_analysis'][difficulty] = {
                    'avg_acceptance_rate': float(stats[('acrate', 'mean')]),
                    'acceptance_std': float(stats[('acrate', 'std')]),
                    'acceptance_range': [
                        float(stats[('acrate', 'min')]),
                        float(stats[('acrate', 'max')])
                    ],
                    'avg_originality': float(stats[('originality_score', 'mean')]),
                    'avg_likes': float(stats[('likes', 'mean')]),
                    'avg_total_votes': float(stats[('total_votes', 'mean')])
                }
        
        # Generate insights
        easy_data = self.metadata_df[self.metadata_df['difficulty'] == 'Easy']
        if not easy_data.empty:
            hard_easy_problems = easy_data[easy_data['acrate'] < 40]
            if len(hard_easy_problems) > 0:
                analysis['insights'].append({
                    'type': 'difficulty_mismatch',
                    'title': 'Misleading Easy Problems',
                    'description': f"{len(hard_easy_problems)} 'Easy' problems have <40% acceptance rate",
                    'examples': hard_easy_problems.nsmallest(3, 'acrate')['title'].tolist()
                })
        
        # Find controversial problems
        controversial = self.metadata_df[self.metadata_df['originality_score'] < 0.6]
        if len(controversial) > 0:
            analysis['insights'].append({
                'type': 'quality_warning',
                'title': 'Controversial Problems',
                'description': f"{len(controversial)} problems have <60% positive rating",
                'count': len(controversial)
            })
        
        return analysis
    
    def get_metadata_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive metadata statistics for dashboard overview.
        
        Returns:
            Dictionary with metadata statistics
        """
        if not self._is_loaded or self.metadata_df is None:
            return {
                'loaded': False,
                'error': 'Metadata not loaded'
            }
        
        return {
            'loaded': True,
            'total_problems': len(self.metadata_df),
            'quality_stats': self.quality_stats,
            'coverage': {
                'difficulties': self.metadata_df['difficulty'].value_counts().to_dict(),
                'quality_tiers': self.metadata_df['quality_tier'].value_counts().to_dict(),
                'age_categories': self.metadata_df['age_category'].value_counts().to_dict()
            },
            'ranges': {
                'likes': {
                    'min': int(self.metadata_df['likes'].min()),
                    'max': int(self.metadata_df['likes'].max()),
                    'median': int(self.metadata_df['likes'].median())
                },
                'acceptance_rate': {
                    'min': float(self.metadata_df['acrate'].min()),
                    'max': float(self.metadata_df['acrate'].max()),
                    'median': float(self.metadata_df['acrate'].median())
                },
                'originality_score': {
                    'min': float(self.metadata_df['originality_score'].min()),
                    'max': float(self.metadata_df['originality_score'].max()),
                    'median': float(self.metadata_df['originality_score'].median())
                }
            }
        }
    
    def is_loaded(self) -> bool:
        """Check if metadata is loaded and ready."""
        return self._is_loaded
    
    def reload_metadata(self) -> bool:
        """Reload metadata from file."""
        self._is_loaded = False
        self.metadata_df = None
        self.quality_stats = None
        return self.load_metadata()