"""
Temporal trend analysis for LeetCode Analytics API.

This module provides time-based comparison capabilities, frequency change detection
across timeframes, and emerging/declining topic identification.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime

from ..models.data_models import FilterCriteria, Timeframe

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Analyzes temporal trends and changes in LeetCode problem patterns.
    
    Features:
    - Time-based frequency comparisons across different timeframes
    - Trend detection for problems and topics
    - Emerging and declining pattern identification
    - Seasonal and temporal pattern analysis
    - Change magnitude and significance calculation
    """
    
    def __init__(self):
        """Initialize the trend analyzer."""
        self.timeframe_order = {
            '30d': 1,
            '3m': 2, 
            '6m': 3,
            '6m+': 4,
            'all': 5
        }
        logger.info("TrendAnalyzer initialized")
    
    def analyze_problem_trends(self, df: pd.DataFrame, 
                             comparison_timeframes: List[str] = None,
                             min_frequency: float = 1.0) -> pd.DataFrame:
        """
        Analyze trends for individual problems across timeframes.
        
        Args:
            df: Dataset DataFrame
            comparison_timeframes: List of timeframes to compare (default: all available)
            min_frequency: Minimum frequency threshold to include problems
            
        Returns:
            DataFrame with problem trend analysis
        """
        if comparison_timeframes is None:
            comparison_timeframes = sorted(df['timeframe'].unique(), 
                                         key=lambda x: self.timeframe_order.get(x, 999))
        
        logger.info(f"Analyzing problem trends across timeframes: {comparison_timeframes}")
        
        # Filter to specified timeframes
        df_filtered = df[df['timeframe'].isin(comparison_timeframes)]
        
        if df_filtered.empty:
            logger.warning("No data found for specified timeframes")
            return pd.DataFrame()
        
        # Get problems that appear in multiple timeframes
        problem_timeframe_data = df_filtered.groupby(['title', 'timeframe']).agg({
            'frequency': 'sum',
            'company': 'nunique',
            'acceptance_rate': 'mean',
            'difficulty': 'first',
            'link': 'first'
        }).reset_index()
        
        # Analyze trends for each problem
        trend_analysis = []
        
        for problem in problem_timeframe_data['title'].unique():
            problem_data = problem_timeframe_data[
                problem_timeframe_data['title'] == problem
            ].copy()
            
            # Skip problems with very low frequency
            if problem_data['frequency'].max() < min_frequency:
                continue
            
            # Sort by timeframe order
            problem_data['timeframe_order'] = problem_data['timeframe'].map(self.timeframe_order)
            problem_data = problem_data.sort_values('timeframe_order')
            
            # Calculate trend metrics
            frequencies = problem_data['frequency'].values
            timeframes = problem_data['timeframe'].tolist()
            
            # Linear trend calculation
            if len(frequencies) > 1:
                x = np.arange(len(frequencies))
                trend_slope, trend_intercept = np.polyfit(x, frequencies, 1)
                trend_r_squared = np.corrcoef(x, frequencies)[0, 1] ** 2
            else:
                trend_slope = 0
                trend_intercept = frequencies[0] if len(frequencies) > 0 else 0
                trend_r_squared = 0
            
            # Calculate change metrics
            if len(frequencies) >= 2:
                first_freq = frequencies[0]
                last_freq = frequencies[-1]
                
                if first_freq > 0:
                    change_percent = ((last_freq - first_freq) / first_freq) * 100
                else:
                    change_percent = 100 if last_freq > 0 else 0
                
                change_absolute = last_freq - first_freq
            else:
                change_percent = 0
                change_absolute = 0
            
            # Determine trend direction and significance
            trend_direction = self._classify_trend(trend_slope, change_percent, frequencies)
            trend_significance = self._calculate_trend_significance(frequencies, trend_r_squared)
            
            analysis = {
                'title': problem,
                'difficulty': problem_data['difficulty'].iloc[0],
                'link': problem_data['link'].iloc[0],
                'timeframes_present': len(problem_data),
                'total_frequency': problem_data['frequency'].sum(),
                'max_frequency': problem_data['frequency'].max(),
                'min_frequency': problem_data['frequency'].min(),
                'avg_frequency': problem_data['frequency'].mean(),
                'trend_slope': trend_slope,
                'trend_intercept': trend_intercept,
                'trend_r_squared': trend_r_squared,
                'change_percent': change_percent,
                'change_absolute': change_absolute,
                'trend_direction': trend_direction,
                'trend_significance': trend_significance,
                'max_companies': problem_data['company'].max(),
                'avg_acceptance_rate': problem_data['acceptance_rate'].mean(),
                'timeframe_data': dict(zip(timeframes, frequencies))
            }
            
            trend_analysis.append(analysis)
        
        if not trend_analysis:
            logger.warning("No problems met the criteria for trend analysis")
            return pd.DataFrame()
        
        result_df = pd.DataFrame(trend_analysis)
        result_df = result_df.sort_values(['trend_significance', 'total_frequency'], 
                                        ascending=[False, False])
        
        logger.info(f"Analyzed trends for {len(result_df)} problems")
        return result_df
    
    def analyze_company_trends(self, df: pd.DataFrame, 
                             companies: List[str] = None,
                             comparison_timeframes: List[str] = None) -> pd.DataFrame:
        """
        Analyze trends in company hiring patterns across timeframes.
        
        Args:
            df: Dataset DataFrame
            companies: List of companies to analyze (default: top companies)
            comparison_timeframes: List of timeframes to compare
            
        Returns:
            DataFrame with company trend analysis
        """
        if companies is None:
            # Select top companies by total problems
            company_counts = df.groupby('company')['title'].nunique()
            companies = company_counts.nlargest(20).index.tolist()
        
        if comparison_timeframes is None:
            comparison_timeframes = sorted(df['timeframe'].unique(),
                                         key=lambda x: self.timeframe_order.get(x, 999))
        
        logger.info(f"Analyzing company trends for {len(companies)} companies")
        
        # Filter data
        df_filtered = df[
            (df['company'].isin(companies)) & 
            (df['timeframe'].isin(comparison_timeframes))
        ]
        
        if df_filtered.empty:
            logger.warning("No data found for specified companies and timeframes")
            return pd.DataFrame()
        
        # Analyze trends for each company
        company_trends = []
        
        for company in companies:
            company_data = df_filtered[df_filtered['company'] == company]
            
            if company_data.empty:
                continue
            
            # Aggregate by timeframe
            timeframe_stats = company_data.groupby('timeframe').agg({
                'title': 'nunique',
                'frequency': ['sum', 'mean'],
                'acceptance_rate': 'mean'
            }).round(2)
            
            # Flatten column names
            timeframe_stats.columns = [
                'unique_problems', 'total_frequency', 'avg_frequency', 'avg_acceptance_rate'
            ]
            timeframe_stats = timeframe_stats.reset_index()
            
            # Sort by timeframe order
            timeframe_stats['timeframe_order'] = timeframe_stats['timeframe'].map(self.timeframe_order)
            timeframe_stats = timeframe_stats.sort_values('timeframe_order')
            
            # Calculate trends
            frequencies = timeframe_stats['total_frequency'].values
            problem_counts = timeframe_stats['unique_problems'].values
            
            if len(frequencies) > 1:
                # Frequency trend
                x = np.arange(len(frequencies))
                freq_slope = np.polyfit(x, frequencies, 1)[0]
                
                # Problem count trend
                prob_slope = np.polyfit(x, problem_counts, 1)[0]
                
                # Change metrics
                freq_change = ((frequencies[-1] - frequencies[0]) / frequencies[0] * 100) if frequencies[0] > 0 else 0
                prob_change = ((problem_counts[-1] - problem_counts[0]) / problem_counts[0] * 100) if problem_counts[0] > 0 else 0
            else:
                freq_slope = prob_slope = freq_change = prob_change = 0
            
            # Difficulty trend analysis
            difficulty_trends = self._analyze_difficulty_trends(company_data, comparison_timeframes)
            
            # Topic trend analysis
            topic_trends = self._analyze_company_topic_trends(company_data, comparison_timeframes)
            
            trend_data = {
                'company': company,
                'timeframes_present': len(timeframe_stats),
                'total_problems': company_data['title'].nunique(),
                'total_frequency': company_data['frequency'].sum(),
                'frequency_trend_slope': freq_slope,
                'problem_count_trend_slope': prob_slope,
                'frequency_change_percent': freq_change,
                'problem_count_change_percent': prob_change,
                'avg_acceptance_rate': company_data['acceptance_rate'].mean(),
                'difficulty_trends': difficulty_trends,
                'top_trending_topics': topic_trends,
                'timeframe_data': timeframe_stats.set_index('timeframe').to_dict('index')
            }
            
            company_trends.append(trend_data)
        
        if not company_trends:
            logger.warning("No company trends could be calculated")
            return pd.DataFrame()
        
        result_df = pd.DataFrame(company_trends)
        result_df = result_df.sort_values('frequency_trend_slope', ascending=False)
        
        logger.info(f"Analyzed trends for {len(result_df)} companies")
        return result_df
    
    def detect_seasonal_patterns(self, df: pd.DataFrame, 
                               pattern_type: str = 'problems') -> Dict[str, Any]:
        """
        Detect seasonal or cyclical patterns in the data.
        
        Args:
            df: Dataset DataFrame
            pattern_type: Type of pattern to analyze ('problems', 'topics', 'companies')
            
        Returns:
            Dictionary with seasonal pattern analysis
        """
        logger.info(f"Detecting seasonal patterns for {pattern_type}")
        
        # Map timeframes to approximate months for seasonal analysis
        timeframe_to_months = {
            '30d': 1,
            '3m': 3,
            '6m': 6,
            '6m+': 12,
            'all': 24  # Approximate for "all time"
        }
        
        patterns = {}
        
        if pattern_type == 'problems':
            patterns = self._detect_problem_seasonal_patterns(df, timeframe_to_months)
        elif pattern_type == 'topics':
            patterns = self._detect_topic_seasonal_patterns(df, timeframe_to_months)
        elif pattern_type == 'companies':
            patterns = self._detect_company_seasonal_patterns(df, timeframe_to_months)
        
        logger.info(f"Detected seasonal patterns for {pattern_type}")
        return patterns
    
    def compare_timeframe_distributions(self, df: pd.DataFrame, 
                                      metric: str = 'frequency') -> pd.DataFrame:
        """
        Compare distributions of metrics across different timeframes.
        
        Args:
            df: Dataset DataFrame
            metric: Metric to compare ('frequency', 'acceptance_rate', 'difficulty')
            
        Returns:
            DataFrame with distribution comparison statistics
        """
        logger.info(f"Comparing {metric} distributions across timeframes")
        
        if metric not in df.columns:
            logger.error(f"Metric '{metric}' not found in dataset")
            return pd.DataFrame()
        
        # Calculate distribution statistics for each timeframe
        distribution_stats = []
        
        for timeframe in df['timeframe'].unique():
            timeframe_data = df[df['timeframe'] == timeframe]
            
            if metric in ['frequency', 'acceptance_rate']:
                # Numerical metrics
                stats = {
                    'timeframe': timeframe,
                    'count': len(timeframe_data),
                    'mean': timeframe_data[metric].mean(),
                    'median': timeframe_data[metric].median(),
                    'std': timeframe_data[metric].std(),
                    'min': timeframe_data[metric].min(),
                    'max': timeframe_data[metric].max(),
                    'q25': timeframe_data[metric].quantile(0.25),
                    'q75': timeframe_data[metric].quantile(0.75),
                    'skewness': timeframe_data[metric].skew(),
                    'kurtosis': timeframe_data[metric].kurtosis()
                }
            else:
                # Categorical metrics (like difficulty)
                value_counts = timeframe_data[metric].value_counts(normalize=True)
                stats = {
                    'timeframe': timeframe,
                    'count': len(timeframe_data),
                    'unique_values': timeframe_data[metric].nunique(),
                    'most_common': timeframe_data[metric].mode().iloc[0] if not timeframe_data[metric].mode().empty else None,
                    'distribution': value_counts.to_dict()
                }
            
            distribution_stats.append(stats)
        
        result_df = pd.DataFrame(distribution_stats)
        
        # Sort by timeframe order
        result_df['timeframe_order'] = result_df['timeframe'].map(self.timeframe_order)
        result_df = result_df.sort_values('timeframe_order').drop('timeframe_order', axis=1)
        
        logger.info(f"Compared {metric} distributions across {len(result_df)} timeframes")
        return result_df
    
    def identify_momentum_changes(self, df: pd.DataFrame, 
                                window_size: int = 2) -> pd.DataFrame:
        """
        Identify problems or topics with significant momentum changes.
        
        Args:
            df: Dataset DataFrame
            window_size: Number of timeframes to consider for momentum calculation
            
        Returns:
            DataFrame with momentum change analysis
        """
        logger.info(f"Identifying momentum changes (window size: {window_size})")
        
        # Get problems with data across multiple timeframes
        problem_timeframes = df.groupby('title')['timeframe'].nunique()
        multi_timeframe_problems = problem_timeframes[problem_timeframes >= window_size].index
        
        if len(multi_timeframe_problems) == 0:
            logger.warning("No problems found with sufficient timeframe data")
            return pd.DataFrame()
        
        momentum_analysis = []
        
        for problem in multi_timeframe_problems:
            problem_data = df[df['title'] == problem].copy()
            
            # Sort by timeframe order
            problem_data['timeframe_order'] = problem_data['timeframe'].map(self.timeframe_order)
            problem_data = problem_data.sort_values('timeframe_order')
            
            frequencies = problem_data['frequency'].values
            
            if len(frequencies) < window_size:
                continue
            
            # Calculate momentum (rate of change)
            momentum_changes = []
            for i in range(len(frequencies) - window_size + 1):
                window_data = frequencies[i:i + window_size]
                if len(window_data) >= 2:
                    # Simple momentum: (current - previous) / previous
                    momentum = (window_data[-1] - window_data[0]) / window_data[0] if window_data[0] > 0 else 0
                    momentum_changes.append(momentum)
            
            if not momentum_changes:
                continue
            
            # Detect significant momentum changes
            momentum_std = np.std(momentum_changes) if len(momentum_changes) > 1 else 0
            momentum_mean = np.mean(momentum_changes)
            
            # Find the most significant momentum change
            max_momentum_change = max(momentum_changes, key=abs) if momentum_changes else 0
            
            # Classify momentum pattern
            if momentum_std > 0.5:  # High volatility
                momentum_pattern = 'volatile'
            elif momentum_mean > 0.3:
                momentum_pattern = 'accelerating'
            elif momentum_mean < -0.3:
                momentum_pattern = 'decelerating'
            else:
                momentum_pattern = 'stable'
            
            analysis = {
                'title': problem,
                'difficulty': problem_data['difficulty'].iloc[0],
                'timeframes_analyzed': len(frequencies),
                'avg_momentum': momentum_mean,
                'momentum_volatility': momentum_std,
                'max_momentum_change': max_momentum_change,
                'momentum_pattern': momentum_pattern,
                'total_frequency': problem_data['frequency'].sum(),
                'frequency_range': problem_data['frequency'].max() - problem_data['frequency'].min(),
                'companies': problem_data['company'].nunique()
            }
            
            momentum_analysis.append(analysis)
        
        if not momentum_analysis:
            logger.warning("No momentum changes could be calculated")
            return pd.DataFrame()
        
        result_df = pd.DataFrame(momentum_analysis)
        result_df = result_df.sort_values('momentum_volatility', ascending=False)
        
        logger.info(f"Analyzed momentum changes for {len(result_df)} problems")
        return result_df
    
    def _classify_trend(self, slope: float, change_percent: float, frequencies: np.ndarray) -> str:
        """Classify trend direction based on slope and change metrics."""
        if abs(change_percent) < 10 and abs(slope) < 0.5:
            return 'stable'
        elif slope > 0.5 and change_percent > 20:
            return 'strongly_increasing'
        elif slope > 0 and change_percent > 0:
            return 'increasing'
        elif slope < -0.5 and change_percent < -20:
            return 'strongly_decreasing'
        elif slope < 0 and change_percent < 0:
            return 'decreasing'
        else:
            return 'mixed'
    
    def _calculate_trend_significance(self, frequencies: np.ndarray, r_squared: float) -> str:
        """Calculate trend significance based on R-squared and data quality."""
        if len(frequencies) < 3:
            return 'insufficient_data'
        elif r_squared > 0.8 and np.std(frequencies) > 1:
            return 'highly_significant'
        elif r_squared > 0.6:
            return 'significant'
        elif r_squared > 0.3:
            return 'moderate'
        else:
            return 'not_significant'
    
    def _analyze_difficulty_trends(self, company_data: pd.DataFrame, 
                                 timeframes: List[str]) -> Dict[str, Any]:
        """Analyze difficulty distribution trends for a company."""
        difficulty_trends = {}
        
        for timeframe in timeframes:
            tf_data = company_data[company_data['timeframe'] == timeframe]
            if not tf_data.empty:
                difficulty_dist = tf_data['difficulty'].value_counts(normalize=True)
                difficulty_trends[timeframe] = difficulty_dist.to_dict()
        
        return difficulty_trends
    
    def _analyze_company_topic_trends(self, company_data: pd.DataFrame, 
                                    timeframes: List[str]) -> List[Dict[str, Any]]:
        """Analyze topic trends for a company."""
        topic_trends = []
        
        # Get topics for each timeframe
        timeframe_topics = {}
        for timeframe in timeframes:
            tf_data = company_data[company_data['timeframe'] == timeframe]
            topics = []
            for topics_str in tf_data['topics'].dropna():
                if isinstance(topics_str, str):
                    topics.extend([t.strip() for t in topics_str.split(',') if t.strip()])
            
            if topics:
                topic_counts = Counter(topics)
                timeframe_topics[timeframe] = topic_counts
        
        # Find trending topics
        if len(timeframe_topics) >= 2:
            all_topics = set()
            for topics in timeframe_topics.values():
                all_topics.update(topics.keys())
            
            for topic in all_topics:
                topic_data = []
                for tf in sorted(timeframes, key=lambda x: self.timeframe_order.get(x, 999)):
                    count = timeframe_topics.get(tf, {}).get(topic, 0)
                    topic_data.append(count)
                
                if len(topic_data) >= 2 and max(topic_data) > 0:
                    # Calculate simple trend
                    if topic_data[0] > 0:
                        change = (topic_data[-1] - topic_data[0]) / topic_data[0] * 100
                    else:
                        change = 100 if topic_data[-1] > 0 else 0
                    
                    topic_trends.append({
                        'topic': topic,
                        'change_percent': change,
                        'max_count': max(topic_data)
                    })
        
        # Return top trending topics
        return sorted(topic_trends, key=lambda x: abs(x['change_percent']), reverse=True)[:5]
    
    def _detect_problem_seasonal_patterns(self, df: pd.DataFrame, 
                                        timeframe_to_months: Dict[str, int]) -> Dict[str, Any]:
        """Detect seasonal patterns in problem frequency."""
        # This is a simplified seasonal analysis
        # In a real implementation, you might use more sophisticated time series analysis
        
        patterns = {
            'pattern_type': 'problems',
            'timeframe_preferences': {},
            'seasonal_problems': []
        }
        
        # Analyze which problems are more common in certain timeframes
        for timeframe, months in timeframe_to_months.items():
            tf_data = df[df['timeframe'] == timeframe]
            if not tf_data.empty:
                top_problems = tf_data.nlargest(10, 'frequency')[['title', 'frequency']]
                patterns['timeframe_preferences'][timeframe] = {
                    'months_represented': months,
                    'total_problems': len(tf_data),
                    'avg_frequency': tf_data['frequency'].mean(),
                    'top_problems': top_problems.to_dict('records')
                }
        
        return patterns
    
    def _detect_topic_seasonal_patterns(self, df: pd.DataFrame, 
                                      timeframe_to_months: Dict[str, int]) -> Dict[str, Any]:
        """Detect seasonal patterns in topic popularity."""
        patterns = {
            'pattern_type': 'topics',
            'timeframe_topic_trends': {},
            'seasonal_topics': []
        }
        
        for timeframe, months in timeframe_to_months.items():
            tf_data = df[df['timeframe'] == timeframe]
            if not tf_data.empty:
                # Extract topics
                all_topics = []
                for topics_str in tf_data['topics'].dropna():
                    if isinstance(topics_str, str):
                        topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                        all_topics.extend(topics)
                
                if all_topics:
                    topic_counts = Counter(all_topics)
                    patterns['timeframe_topic_trends'][timeframe] = {
                        'months_represented': months,
                        'total_topic_mentions': len(all_topics),
                        'unique_topics': len(topic_counts),
                        'top_topics': dict(topic_counts.most_common(10))
                    }
        
        return patterns
    
    def _detect_company_seasonal_patterns(self, df: pd.DataFrame, 
                                        timeframe_to_months: Dict[str, int]) -> Dict[str, Any]:
        """Detect seasonal patterns in company hiring."""
        patterns = {
            'pattern_type': 'companies',
            'timeframe_company_activity': {},
            'seasonal_companies': []
        }
        
        for timeframe, months in timeframe_to_months.items():
            tf_data = df[df['timeframe'] == timeframe]
            if not tf_data.empty:
                company_stats = tf_data.groupby('company').agg({
                    'title': 'nunique',
                    'frequency': 'sum'
                }).sort_values('frequency', ascending=False)
                
                patterns['timeframe_company_activity'][timeframe] = {
                    'months_represented': months,
                    'active_companies': len(company_stats),
                    'avg_problems_per_company': company_stats['title'].mean(),
                    'top_companies': company_stats.head(10).to_dict('index')
                }
        
        return patterns