"""
Topic analysis system for LeetCode Analytics API.

This module provides topic trend analysis, frequency counting, heatmap generation,
and topic correlation analysis capabilities.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple, Set
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations

from ..models.data_models import FilterCriteria, Timeframe

logger = logging.getLogger(__name__)


class TopicAnalyzer:
    """
    Analyzes topic trends, correlations, and patterns in LeetCode problems.
    
    Features:
    - Topic frequency counting and ranking
    - Topic trend analysis across timeframes
    - Topic correlation and co-occurrence analysis
    - Heatmap data generation for visualization
    - Topic clustering and similarity analysis
    """
    
    def __init__(self):
        """Initialize the topic analyzer."""
        logger.info("TopicAnalyzer initialized")
    
    def get_topic_frequency(self, df: pd.DataFrame, filters: FilterCriteria = None,
                          limit: int = 50) -> pd.DataFrame:
        """
        Get topic frequency counts across the dataset.
        
        Args:
            df: Dataset DataFrame (preferably exploded topics)
            filters: Filter criteria to apply
            limit: Maximum number of topics to return
            
        Returns:
            DataFrame with topic frequencies and statistics
        """
        logger.info(f"Analyzing topic frequencies (limit: {limit})")
        
        # Apply filters if provided
        if filters:
            df = self._apply_filters(df, filters)
        
        if df.empty:
            logger.warning("No data remaining after applying filters")
            return pd.DataFrame()
        
        # Extract all topics
        all_topics = self._extract_all_topics(df)
        
        if not all_topics:
            logger.warning("No topics found in dataset")
            return pd.DataFrame()

        # Count topic frequencies
        topic_counts = Counter(all_topics)

        # Create detailed statistics for each topic
        topic_stats = []
        for topic, count in topic_counts.most_common(limit):
            # Get problems with this topic
            topic_problems = df[df['topics'].str.contains(topic, case=False, na=False)]

            # Ensure frequency column exists and is numeric
            frequency_series = topic_problems['frequency'] if 'frequency' in topic_problems.columns else pd.Series(dtype=float)
            frequency_series = pd.to_numeric(frequency_series, errors='coerce')

            # Accept­­ance rate may not be present in all datasets
            if 'acceptance_rate' in topic_problems.columns:
                acceptance_series = pd.to_numeric(topic_problems['acceptance_rate'], errors='coerce')
                avg_acceptance = float(acceptance_series.mean()) if not acceptance_series.empty else None
            else:
                avg_acceptance = None

            stats = {
                'topic': topic,
                'frequency': count,
                'unique_problems': topic_problems['title'].nunique(),
                'companies': topic_problems['company'].nunique(),
                'avg_problem_frequency': float(frequency_series.mean()) if not frequency_series.empty else 0.0,
                'total_problem_frequency': float(frequency_series.sum()) if not frequency_series.empty else 0.0,
                'avg_acceptance_rate': avg_acceptance,
                'difficulty_distribution': topic_problems['difficulty'].value_counts().to_dict()
            }

            topic_stats.append(stats)

        result_df = pd.DataFrame(topic_stats)
        
        logger.info(f"Analyzed {len(result_df)} topics")
        return result_df
    
    def analyze_topic_trends(self, df: pd.DataFrame, timeframes: List[str] = None) -> pd.DataFrame:
        """
        Analyze topic trends across different timeframes.
        
        Args:
            df: Dataset DataFrame
            timeframes: List of timeframes to analyze (default: all available)
            
        Returns:
            DataFrame with topic trend analysis
        """
        if timeframes is None:
            timeframes = df['timeframe'].unique().tolist()
        
        logger.info(f"Analyzing topic trends across timeframes: {timeframes}")
        
        # Filter to specified timeframes
        df_filtered = df[df['timeframe'].isin(timeframes)]
        
        if df_filtered.empty:
            logger.warning("No data found for specified timeframes")
            return pd.DataFrame()
        
        # Get topic frequencies for each timeframe
        trend_data = []
        
        timeframe_totals: Dict[str, int] = {}

        for timeframe in timeframes:
            timeframe_data = df_filtered[df_filtered['timeframe'] == timeframe]
            topics = self._extract_all_topics(timeframe_data)
            topic_counts = Counter(topics)
            total_count = sum(topic_counts.values())
            timeframe_totals[timeframe] = total_count
            
            for topic, count in topic_counts.items():
                trend_data.append({
                    'topic': topic,
                    'timeframe': timeframe,
                    'frequency': count,
                    'timeframe_total': total_count,
                    'unique_problems': timeframe_data[
                        timeframe_data['topics'].str.contains(topic, case=False, na=False)
                    ]['title'].nunique(),
                    'companies': timeframe_data[
                        timeframe_data['topics'].str.contains(topic, case=False, na=False)
                    ]['company'].nunique()
                })
        
        trend_df = pd.DataFrame(trend_data)
        
        if trend_df.empty:
            return trend_df
        
        # Calculate trend metrics
        trend_analysis = []
        
        timeframe_order = {'30d': 1, '3m': 2, '6m': 3, '6m+': 4, 'all': 5}
        timeframe_duration_days = {'30d': 30, '3m': 90, '6m': 180}
        min_samples_per_bucket = 10
        share_threshold = 0.02

        for topic in trend_df['topic'].unique():
            topic_data = trend_df[trend_df['topic'] == topic]

            topic_data_sorted = topic_data.copy()
            topic_data_sorted['timeframe_order'] = topic_data_sorted['timeframe'].map(timeframe_order)
            topic_data_sorted = topic_data_sorted.sort_values('timeframe_order')

            slope_data = topic_data_sorted[topic_data_sorted['timeframe'].isin(timeframe_duration_days.keys())]
            slope_data = slope_data[slope_data['frequency'] >= min_samples_per_bucket]

            share_by_timeframe = {}
            for _, row in topic_data_sorted.iterrows():
                total_for_tf = max(1, float(row.get('timeframe_total', timeframe_totals.get(row['timeframe'], 0))))
                share_by_timeframe[row['timeframe']] = float(row['frequency']) / total_for_tf

            duration_values: List[float] = []
            share_values: List[float] = []

            for _, row in slope_data.iterrows():
                timeframe = row['timeframe']
                duration = timeframe_duration_days.get(timeframe)
                if duration is None:
                    continue
                duration_values.append(float(duration))
                share_values.append(share_by_timeframe.get(timeframe, 0.0))

            sufficient_data = len(duration_values) >= 2

            raw_slope = None
            share_delta = None
            trend_direction = 'insufficient_data'
            slope_per_day = None

            if sufficient_data:
                share_array = np.array(share_values, dtype=float)
                duration_array = np.array(duration_values, dtype=float)

                slope_per_day = np.polyfit(duration_array, share_array, 1)[0]

                ordered_shares = [share_by_timeframe[row['timeframe']] for _, row in slope_data.iterrows()]
                if len(ordered_shares) >= 2:
                    share_delta = float(ordered_shares[-1] - ordered_shares[0])

                raw_slope = slope_per_day

                if share_delta is not None:
                    if share_delta > share_threshold:
                        trend_direction = 'increasing'
                    elif share_delta < -share_threshold:
                        trend_direction = 'decreasing'
                    else:
                        trend_direction = 'stable'

            analysis = {
                'topic': topic,
                'total_frequency': topic_data['frequency'].sum(),
                'max_frequency': topic_data['frequency'].max(),
                'min_frequency': topic_data['frequency'].min(),
                'trend_slope': raw_slope,
                'trend_slope_per_day': slope_per_day,
                'trend_strength': share_delta,
                'trend_direction': trend_direction,
                'timeframe_count': len(topic_data),
                'valid_timeframe_count': len(duration_values),
                'min_samples_per_bucket': min_samples_per_bucket,
                'avg_companies': topic_data['companies'].mean(),
                'timeframe_data': topic_data.set_index('timeframe')['frequency'].to_dict(),
                'share_by_timeframe': share_by_timeframe,
                'sufficient_data': sufficient_data,
            }

            trend_analysis.append(analysis)
        
        result_df = pd.DataFrame(trend_analysis)
        result_df = result_df.sort_values('total_frequency', ascending=False)
        
        logger.info(f"Analyzed trends for {len(result_df)} topics")
        return result_df
    
    def get_topic_correlations(self, df: pd.DataFrame, min_cooccurrence: int = 5) -> pd.DataFrame:
        """
        Analyze topic correlations and co-occurrence patterns.
        
        Args:
            df: Dataset DataFrame
            min_cooccurrence: Minimum number of co-occurrences to include in results
            
        Returns:
            DataFrame with topic correlation analysis
        """
        logger.info(f"Analyzing topic correlations (min co-occurrence: {min_cooccurrence})")
        
        # Get problems with their topics
        problem_topics = {}
        for _, row in df.iterrows():
            if pd.notna(row['topics']):
                topics = [t.strip() for t in str(row['topics']).split(',') if t.strip()]
                if len(topics) > 1:  # Only consider problems with multiple topics
                    problem_topics[row['title']] = set(topics)
        
        if not problem_topics:
            logger.warning("No problems with multiple topics found")
            return pd.DataFrame()
        
        # Calculate co-occurrence matrix
        all_topics = set()
        for topics in problem_topics.values():
            all_topics.update(topics)
        
        all_topics = sorted(list(all_topics))
        cooccurrence_data = []
        
        for topic1, topic2 in combinations(all_topics, 2):
            # Count co-occurrences
            cooccurrence_count = sum(
                1 for topics in problem_topics.values() 
                if topic1 in topics and topic2 in topics
            )
            
            if cooccurrence_count >= min_cooccurrence:
                # Calculate correlation metrics
                topic1_count = sum(1 for topics in problem_topics.values() if topic1 in topics)
                topic2_count = sum(1 for topics in problem_topics.values() if topic2 in topics)
                total_problems = len(problem_topics)
                
                # Jaccard similarity
                union_count = sum(
                    1 for topics in problem_topics.values() 
                    if topic1 in topics or topic2 in topics
                )
                jaccard_similarity = cooccurrence_count / union_count if union_count > 0 else 0
                
                # Lift (how much more likely they are to appear together)
                expected_cooccurrence = (topic1_count * topic2_count) / total_problems
                lift = cooccurrence_count / expected_cooccurrence if expected_cooccurrence > 0 else 0
                
                cooccurrence_data.append({
                    'topic1': topic1,
                    'topic2': topic2,
                    'cooccurrence_count': cooccurrence_count,
                    'topic1_count': topic1_count,
                    'topic2_count': topic2_count,
                    'jaccard_similarity': jaccard_similarity,
                    'lift': lift,
                    'confidence_1_to_2': cooccurrence_count / topic1_count,
                    'confidence_2_to_1': cooccurrence_count / topic2_count
                })
        
        if not cooccurrence_data:
            logger.warning("No significant topic correlations found")
            return pd.DataFrame()
        
        result_df = pd.DataFrame(cooccurrence_data)
        result_df = result_df.sort_values('lift', ascending=False)
        
        logger.info(f"Found {len(result_df)} topic correlations")
        return result_df
    
    def generate_topic_heatmap_data(self, df: pd.DataFrame,
                                  companies: List[str] = None,
                                  topics: List[str] = None,
                                  top_n: int = 30) -> Dict[str, Any]:
        """
        Generate data for topic-company heatmap visualization.
        
        Args:
            df: Dataset DataFrame
            companies: List of companies to include (default: top companies by problem count)
            topics: List of topics to include (default: top topics by frequency)
            
        Returns:
            Dictionary with heatmap data and metadata
        """
        logger.info("Generating topic heatmap data")

        # Select top companies if not specified
        if companies is None:
            company_counts = df['company'].value_counts()
            companies = company_counts.head(20).index.tolist()

        if not companies:
            logger.warning("No companies available for heatmap generation")
            return {}

        # Select top topics if not specified
        if topics is None:
            all_topics = self._extract_all_topics(df)
            topic_counts = Counter(all_topics)
            topics = [topic for topic, _ in topic_counts.most_common(top_n)]
        else:
            topics = topics[:top_n]

        if not topics:
            logger.warning("No topics available for heatmap generation")
            return {}

        # Filter data
        df_filtered = df[df['company'].isin(companies)]

        if df_filtered.empty:
            logger.warning("No data after filtering for selected companies")
            return {}

        # Pre-compute topic counts per company
        company_topic_counts: Dict[str, Counter] = {}
        company_totals: List[int] = []

        for company in companies:
            company_data = df_filtered[df_filtered['company'] == company]
            company_topics = self._extract_all_topics(company_data)
            topic_counter = Counter(company_topics)
            company_topic_counts[company] = topic_counter
            company_totals.append(int(sum(topic_counter.values())))

        # Build topic-major matrix (topics x companies)
        matrix: List[List[int]] = []
        topic_totals: List[int] = []

        for topic in topics:
            row_values: List[int] = []
            topic_total = 0
            for company in companies:
                count = int(company_topic_counts.get(company, {}).get(topic, 0))
                row_values.append(count)
                topic_total += count
            matrix.append(row_values)
            topic_totals.append(topic_total)

        # Collect metadata
        timeframes_present = sorted(df_filtered['timeframe'].dropna().unique().tolist())

        result = {
            'topics': topics,
            'companies': companies,
            'matrix': matrix,
            'topic_totals': topic_totals,
            'company_totals': company_totals,
            'metadata': {
                'total_companies': len(companies),
                'total_topics': len(topics),
                'max_value': max(topic_totals) if topic_totals else 0,
                'timeframes': timeframes_present,
                'top_n': top_n
            }
        }

        logger.info(f"Generated heatmap data for {len(companies)} companies and {len(topics)} topics")
        return result
    
    def find_emerging_topics(self, df: pd.DataFrame, 
                           comparison_timeframes: Tuple[str, str] = ('6m+', '30d')) -> pd.DataFrame:
        """
        Identify emerging and declining topics by comparing timeframes.
        
        Args:
            df: Dataset DataFrame
            comparison_timeframes: Tuple of (older_timeframe, newer_timeframe)
            
        Returns:
            DataFrame with emerging/declining topic analysis
        """
        older_tf, newer_tf = comparison_timeframes
        logger.info(f"Finding emerging topics: {older_tf} vs {newer_tf}")
        
        # Get topic frequencies for each timeframe
        older_data = df[df['timeframe'] == older_tf]
        newer_data = df[df['timeframe'] == newer_tf]
        
        if older_data.empty or newer_data.empty:
            logger.warning("Insufficient data for timeframe comparison")
            return pd.DataFrame()
        
        older_topics = Counter(self._extract_all_topics(older_data))
        newer_topics = Counter(self._extract_all_topics(newer_data))
        
        # Calculate changes
        all_topics = set(older_topics.keys()) | set(newer_topics.keys())
        topic_changes = []
        
        for topic in all_topics:
            older_count = older_topics.get(topic, 0)
            newer_count = newer_topics.get(topic, 0)
            
            # Calculate change metrics
            if older_count > 0:
                change_ratio = newer_count / older_count
                change_percent = ((newer_count - older_count) / older_count) * 100
            else:
                change_ratio = float('inf') if newer_count > 0 else 0
                change_percent = 100 if newer_count > 0 else 0
            
            change_absolute = newer_count - older_count
            
            # Determine trend
            if change_percent > 50 and newer_count >= 3:
                trend = 'emerging'
            elif change_percent < -30 and older_count >= 3:
                trend = 'declining'
            elif abs(change_percent) <= 20:
                trend = 'stable'
            else:
                trend = 'growing' if change_percent > 0 else 'shrinking'
            
            topic_changes.append({
                'topic': topic,
                f'{older_tf}_count': older_count,
                f'{newer_tf}_count': newer_count,
                'change_absolute': change_absolute,
                'change_percent': change_percent,
                'change_ratio': change_ratio,
                'trend': trend,
                'significance': max(older_count, newer_count)  # For filtering
            })
        
        result_df = pd.DataFrame(topic_changes)
        
        # Filter out topics with very low significance
        result_df = result_df[result_df['significance'] >= 2]
        
        # Sort by change magnitude
        result_df = result_df.sort_values('change_percent', ascending=False)
        
        logger.info(f"Analyzed {len(result_df)} topics for emergence/decline")
        return result_df
    
    def get_topic_difficulty_correlation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze correlation between topics and problem difficulty.
        
        Args:
            df: Dataset DataFrame
            
        Returns:
            DataFrame with topic-difficulty correlation analysis
        """
        logger.info("Analyzing topic-difficulty correlations")
        
        # Extract topics and their associated difficulties
        topic_difficulty_data = []
        
        for _, row in df.iterrows():
            if pd.notna(row['topics']) and pd.notna(row['difficulty']):
                topics = [t.strip() for t in str(row['topics']).split(',') if t.strip()]
                for topic in topics:
                    topic_difficulty_data.append({
                        'topic': topic,
                        'difficulty': row['difficulty'],
                        'frequency': row['frequency']
                    })
        
        if not topic_difficulty_data:
            logger.warning("No topic-difficulty data found")
            return pd.DataFrame()
        
        topic_df = pd.DataFrame(topic_difficulty_data)
        
        # Analyze each topic
        topic_analysis = []
        
        for topic in topic_df['topic'].unique():
            topic_data = topic_df[topic_df['topic'] == topic]
            
            # Calculate difficulty distribution
            difficulty_dist = topic_data['difficulty'].value_counts(normalize=True)
            
            # Calculate weighted difficulty score (Easy=1, Medium=2, Hard=3)
            difficulty_weights = {'EASY': 1, 'MEDIUM': 2, 'HARD': 3}
            weighted_scores = []
            
            for _, row in topic_data.iterrows():
                if row['difficulty'] in difficulty_weights:
                    # Weight by frequency
                    weight = difficulty_weights[row['difficulty']] * row['frequency']
                    weighted_scores.append(weight)
            
            avg_difficulty_score = np.mean(weighted_scores) if weighted_scores else 0
            
            analysis = {
                'topic': topic,
                'total_problems': len(topic_data),
                'avg_difficulty_score': avg_difficulty_score,
                'easy_percentage': difficulty_dist.get('EASY', 0) * 100,
                'medium_percentage': difficulty_dist.get('MEDIUM', 0) * 100,
                'hard_percentage': difficulty_dist.get('HARD', 0) * 100,
                'difficulty_distribution': difficulty_dist.to_dict(),
                'avg_frequency': topic_data['frequency'].mean(),
                'total_frequency': topic_data['frequency'].sum()
            }
            
            # Classify topic difficulty tendency
            if avg_difficulty_score < 1.5:
                analysis['difficulty_tendency'] = 'easy'
            elif avg_difficulty_score > 2.5:
                analysis['difficulty_tendency'] = 'hard'
            else:
                analysis['difficulty_tendency'] = 'medium'
            
            topic_analysis.append(analysis)
        
        result_df = pd.DataFrame(topic_analysis)
        result_df = result_df.sort_values('avg_difficulty_score', ascending=False)
        
        logger.info(f"Analyzed difficulty correlations for {len(result_df)} topics")
        return result_df
    
    def _apply_filters(self, df: pd.DataFrame, filters: FilterCriteria) -> pd.DataFrame:
        """Apply filter criteria to the dataset."""
        filtered_df = df.copy()
        
        if filters.companies:
            filtered_df = filtered_df[filtered_df['company'].isin(filters.companies)]
        
        if filters.timeframes:
            timeframe_values = [tf.value if hasattr(tf, 'value') else tf for tf in filters.timeframes]
            filtered_df = filtered_df[filtered_df['timeframe'].isin(timeframe_values)]
        
        if filters.difficulties:
            difficulty_values = [d.value if hasattr(d, 'value') else d for d in filters.difficulties]
            filtered_df = filtered_df[filtered_df['difficulty'].isin(difficulty_values)]
        
        if filters.topics:
            # Filter by topics (contains any of the specified topics)
            topic_mask = filtered_df['topics'].str.contains(
                '|'.join(filters.topics), case=False, na=False
            )
            filtered_df = filtered_df[topic_mask]
        
        return filtered_df
    
    def _extract_all_topics(self, df: pd.DataFrame) -> List[str]:
        """Extract all individual topics from the dataset."""
        all_topics = []
        
        for topics_str in df['topics'].dropna():
            if isinstance(topics_str, str):
                topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                all_topics.extend(topics)
        
        return all_topics
