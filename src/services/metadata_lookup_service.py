"""
Metadata Lookup Service

Provides a unified interface for metadata enrichment across the analytics system.
Integrates with the existing data processing pipeline to add quality metrics.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from functools import lru_cache

from .leetcode_metadata_processor import LeetCodeMetadataProcessor

logger = logging.getLogger(__name__)


class MetadataLookupService:
    """
    Service for looking up and enriching problem data with LeetCode metadata.
    
    Features:
    - Singleton pattern for efficient memory usage
    - Caching for fast lookups
    - Integration with existing data processing pipeline
    - Fallback handling for missing metadata
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetadataLookupService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.processor = LeetCodeMetadataProcessor()
            self._metadata_cache: Dict[str, Dict[str, Any]] = {}
            self._cache_hits = 0
            self._cache_misses = 0
            MetadataLookupService._initialized = True
            logger.info("MetadataLookupService initialized")
    
    def initialize(self, metadata_file_path: str = "leetcode_metadata.parquet") -> bool:
        """
        Initialize the service with metadata file.
        
        Args:
            metadata_file_path: Path to the metadata file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if metadata_file_path != self.processor.metadata_file_path:
                self.processor = LeetCodeMetadataProcessor(metadata_file_path)
                self._clear_cache()
            
            success = self.processor.load_metadata()
            if success:
                logger.info("MetadataLookupService initialized successfully")
            else:
                logger.error("Failed to initialize MetadataLookupService")
            
            return success
            
        except Exception as e:
            logger.error(f"Error initializing MetadataLookupService: {str(e)}")
            return False
    
    def is_ready(self) -> bool:
        """Check if the service is ready to provide metadata."""
        return self.processor.is_loaded()
    
    @lru_cache(maxsize=1000)
    def get_problem_metadata(self, problem_title: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific problem with caching.
        
        Args:
            problem_title: Title of the problem
            
        Returns:
            Dictionary with metadata or None if not found
        """
        if not self.is_ready():
            logger.debug("Metadata service not ready")
            return None
        
        # Check cache first
        if problem_title in self._metadata_cache:
            self._cache_hits += 1
            return self._metadata_cache[problem_title]
        
        # Lookup metadata
        metadata = self.processor.get_problem_metadata(problem_title)
        
        # Cache the result (even if None)
        self._metadata_cache[problem_title] = metadata
        
        if metadata is None:
            self._cache_misses += 1
        else:
            self._cache_hits += 1
        
        return metadata
    
    def enrich_problem_record(self, problem_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single problem record with metadata.
        
        Args:
            problem_record: Dictionary with problem data
            
        Returns:
            Enhanced problem record with metadata fields
        """
        if 'title' not in problem_record:
            logger.warning("Problem record missing 'title' field")
            return problem_record
        
        metadata = self.get_problem_metadata(problem_record['title'])
        
        if metadata is None:
            # Add default metadata values
            enhanced_record = problem_record.copy()
            enhanced_record.update({
                'likes': 0,
                'dislikes': 0,
                'originality_score': 0.5,
                'total_votes': 0,
                'quality_percentile': 0.5,
                'quality_tier': 'Unknown',
                'age_category': 'Unknown',
                'engagement_score': 0.0,
                'has_solution': False,
                'has_video_solution': False,
                'is_paid_only': False,
                'metadata_available': False
            })
        else:
            # Merge with metadata
            enhanced_record = problem_record.copy()
            enhanced_record.update({
                'likes': metadata['likes'],
                'dislikes': metadata['dislikes'],
                'originality_score': metadata['originality_score'],
                'total_votes': metadata['total_votes'],
                'quality_percentile': metadata['quality_percentile'],
                'quality_tier': metadata['quality_tier'],
                'age_category': metadata['age_category'],
                'engagement_score': metadata['engagement_score'],
                'difficulty_adjusted_acceptance': metadata['difficulty_adjusted_acceptance'],
                'has_solution': metadata['has_solution'],
                'has_video_solution': metadata['has_video_solution'],
                'is_paid_only': metadata['is_paid_only'],
                'metadata_available': True
            })
        
        return enhanced_record
    
    def enrich_problems_dataframe(self, problems_df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich a DataFrame of problems with metadata.
        
        Args:
            problems_df: DataFrame with problem data
            
        Returns:
            Enhanced DataFrame with metadata columns
        """
        if not self.is_ready():
            logger.warning("Metadata service not ready, returning original DataFrame")
            return problems_df
        
        return self.processor.enrich_problems_dataframe(problems_df)
    
    def get_quality_filtered_problems(self, problems_df: pd.DataFrame, 
                                    quality_filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Filter problems based on quality criteria.
        
        Args:
            problems_df: DataFrame with problems (will be enriched if needed)
            quality_filters: Dictionary with quality filter criteria
            
        Returns:
            Filtered DataFrame
        """
        if not self.is_ready():
            logger.warning("Metadata service not ready, returning original DataFrame")
            return problems_df
        
        # Enrich with metadata if not already done
        if 'originality_score' not in problems_df.columns:
            enriched_df = self.enrich_problems_dataframe(problems_df)
        else:
            enriched_df = problems_df.copy()
        
        # Apply quality filters
        filtered_df = enriched_df.copy()
        
        if 'min_originality_score' in quality_filters:
            filtered_df = filtered_df[
                filtered_df['originality_score'] >= quality_filters['min_originality_score']
            ]
        
        if 'max_originality_score' in quality_filters:
            filtered_df = filtered_df[
                filtered_df['originality_score'] <= quality_filters['max_originality_score']
            ]
        
        if 'min_likes' in quality_filters:
            filtered_df = filtered_df[
                filtered_df['likes'] >= quality_filters['min_likes']
            ]
        
        if 'max_total_votes' in quality_filters:
            filtered_df = filtered_df[
                filtered_df['total_votes'] <= quality_filters['max_total_votes']
            ]
        
        if 'quality_tiers' in quality_filters:
            filtered_df = filtered_df[
                filtered_df['quality_tier'].isin(quality_filters['quality_tiers'])
            ]
        
        if 'age_categories' in quality_filters:
            filtered_df = filtered_df[
                filtered_df['age_category'].isin(quality_filters['age_categories'])
            ]
        
        if 'exclude_paid' in quality_filters and quality_filters['exclude_paid']:
            filtered_df = filtered_df[~filtered_df['is_paid_only']]
        
        if 'require_solution' in quality_filters and quality_filters['require_solution']:
            filtered_df = filtered_df[filtered_df['has_solution']]
        
        logger.info(f"Quality filtering reduced problems from {len(enriched_df)} to {len(filtered_df)}")
        return filtered_df
    
    def get_quality_based_ranking(self, problems_df: pd.DataFrame, 
                                 ranking_strategy: str = 'balanced') -> pd.DataFrame:
        """
        Rank problems based on quality metrics.
        
        Args:
            problems_df: DataFrame with problems
            ranking_strategy: Strategy for ranking ('quality', 'popularity', 'balanced', 'hidden_gems')
            
        Returns:
            DataFrame sorted by quality ranking
        """
        if not self.is_ready():
            logger.warning("Metadata service not ready, returning original DataFrame")
            return problems_df
        
        # Enrich with metadata if needed
        if 'originality_score' not in problems_df.columns:
            enriched_df = self.enrich_problems_dataframe(problems_df)
        else:
            enriched_df = problems_df.copy()
        
        # Apply ranking strategy
        if ranking_strategy == 'quality':
            # Rank by originality score and engagement
            enriched_df['quality_rank'] = (
                enriched_df['originality_score'] * 0.7 +
                enriched_df['engagement_score'] * 0.3
            )
            sort_columns = ['quality_rank']
            ascending = [False]
            
        elif ranking_strategy == 'popularity':
            # Rank by likes and total votes with zero-division protection
            max_likes = max(enriched_df['likes'].max(), 1)
            max_votes = max(enriched_df['total_votes'].max(), 1)
            enriched_df['popularity_rank'] = (
                enriched_df['likes'] / max_likes * 0.6 +
                enriched_df['total_votes'] / max_votes * 0.4
            )
            sort_columns = ['popularity_rank']
            ascending = [False]
            
        elif ranking_strategy == 'hidden_gems':
            # Rank by high quality but low exposure with zero-division protection
            max_votes = max(enriched_df['total_votes'].max(), 1)
            enriched_df['gem_score'] = (
                enriched_df['originality_score'] * 0.8 -
                (enriched_df['total_votes'] / max_votes) * 0.2
            )
            sort_columns = ['gem_score']
            ascending = [False]
            
        else:  # balanced
            # Balanced ranking considering quality, popularity, and freshness with zero-division protection
            max_likes = max(enriched_df['likes'].max(), 1)
            enriched_df['balanced_rank'] = (
                enriched_df['originality_score'] * 0.4 +
                enriched_df['engagement_score'] * 0.3 +
                (enriched_df['likes'] / max_likes) * 0.2 +
                enriched_df['difficulty_adjusted_acceptance'] * 0.1
            )
            sort_columns = ['balanced_rank']
            ascending = [False]
        
        # Sort by ranking
        ranked_df = enriched_df.sort_values(by=sort_columns, ascending=ascending)
        
        logger.info(f"Ranked {len(ranked_df)} problems using '{ranking_strategy}' strategy")
        return ranked_df
    
    def get_recommendation_insights(self) -> Dict[str, Any]:
        """
        Get insights for problem recommendations.
        
        Returns:
            Dictionary with recommendation insights
        """
        if not self.is_ready():
            return {'error': 'Metadata service not ready'}
        
        insights = {
            'hidden_gems': self.processor.find_hidden_gems(limit=10),
            'interview_classics': self.processor.find_interview_classics(limit=10),
            'rising_stars': self.processor.find_rising_stars(limit=10),
            'quality_analysis': self.processor.get_quality_analysis_summary(),
            'difficulty_reality': self.processor.analyze_difficulty_reality()
        }
        
        return insights
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size': len(self._metadata_cache)
        }
    
    def _clear_cache(self):
        """Clear the metadata cache."""
        self._metadata_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        # Clear LRU cache
        self.get_problem_metadata.cache_clear()
        logger.info("Metadata cache cleared")
    
    def reload_metadata(self) -> bool:
        """Reload metadata and clear cache."""
        self._clear_cache()
        return self.processor.reload_metadata()


# Global instance
metadata_lookup_service = MetadataLookupService()