"""
Difficulty and acceptance rate correlation analysis for LeetCode Analytics API.

This module provides difficulty-based statistics, acceptance rate outlier detection,
and difficulty-topic correlation analysis capabilities.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from collections import Counter
from scipy import stats

from ..models.data_models import FilterCriteria, Difficulty

logger = logging.getLogger(__name__)


class DifficultyAnalyzer:
    """
    Analyzes difficulty patterns, acceptance rate correlations, and outlier detection.
    
    Features:
    - Difficulty-based statistics and distributions
    - Acceptance rate outlier detection and analysis
    - Difficulty-topic correlation analysis
    - Company difficulty preferences analysis
    - Acceptance rate vs frequency correlations
    """
    
    def __init__(self):
        """Initialize the difficulty analyzer."""
        self.difficulty_weights = {
            'EASY': 1,
            'MEDIUM': 2, 
            'HARD': 3,
            'UNKNOWN': 0
        }
        logger.info("DifficultyAnalyzer initialized")
    
    def analyze_difficulty_distribution(self, df: pd.DataFrame, 
                                      group_by: str = None,
                                      filters: FilterCriteria = None) -> pd.DataFrame:
        """
        Analyze difficulty distribution across the dataset.
        
        Args:
            df: Dataset DataFrame
            group_by: Column to group by ('company', 'timeframe', 'topics')
            filters: Filter criteria to apply
            
        Returns:
            DataFrame with difficulty distribution analysis
        """
        logger.info(f"Analyzing difficulty distribution (group by: {group_by})")
        
        # Apply filters if provided
        if filters:
            df = self._apply_filters(df, filters)
        
        if df.empty:
            logger.warning("No data remaining after applying filters")
            return pd.DataFrame()
        
        if group_by is None:
            # Overall distribution
            return self._calculate_overall_difficulty_stats(df)
        elif group_by == 'company':
            return self._calculate_company_difficulty_stats(df)
        elif group_by == 'timeframe':
            return self._calculate_timeframe_difficulty_stats(df)
        elif group_by == 'topics':
            return self._calculate_topic_difficulty_stats(df)
        else:
            logger.error(f"Unsupported group_by parameter: {group_by}")
            return pd.DataFrame()
    
    def detect_acceptance_rate_outliers(self, df: pd.DataFrame, 
                                      method: str = 'iqr',
                                      group_by: str = 'difficulty') -> pd.DataFrame:
        """
        Detect problems with unusual acceptance rates.
        
        Args:
            df: Dataset DataFrame
            method: Outlier detection method ('iqr', 'zscore', 'isolation')
            group_by: Group outlier detection by ('difficulty', 'company', 'overall')
            
        Returns:
            DataFrame with outlier analysis
        """
        logger.info(f"Detecting acceptance rate outliers using {method} method (group by: {group_by})")
        
        if df.empty or 'acceptance_rate' not in df.columns:
            logger.warning("No acceptance rate data available")
            return pd.DataFrame()
        
        outliers = []
        
        if group_by == 'overall':
            outliers.extend(self._detect_outliers_in_group(df, method, 'overall'))
        elif group_by == 'difficulty':
            for difficulty in df['difficulty'].unique():
                if pd.notna(difficulty):
                    group_data = df[df['difficulty'] == difficulty]
                    outliers.extend(self._detect_outliers_in_group(group_data, method, difficulty))
        elif group_by == 'company':
            for company in df['company'].unique():
                if pd.notna(company):
                    group_data = df[df['company'] == company]
                    outliers.extend(self._detect_outliers_in_group(group_data, method, company))
        
        if not outliers:
            logger.info("No outliers detected")
            return pd.DataFrame()
        
        outliers_df = pd.DataFrame(outliers)
        outliers_df = outliers_df.sort_values('outlier_score', ascending=False)
        
        logger.info(f"Detected {len(outliers_df)} acceptance rate outliers")
        return outliers_df
    
    def analyze_difficulty_topic_correlation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze correlation between topics and problem difficulty.
        
        Args:
            df: Dataset DataFrame
            
        Returns:
            DataFrame with topic-difficulty correlation analysis
        """
        logger.info("Analyzing difficulty-topic correlations")
        
        if df.empty or 'topics' not in df.columns:
            logger.warning("No topic data available")
            return pd.DataFrame()
        
        # Extract topic-difficulty pairs
        topic_difficulty_data = []
        
        for _, row in df.iterrows():
            if pd.notna(row['topics']) and pd.notna(row['difficulty']):
                topics = [t.strip() for t in str(row['topics']).split(',') if t.strip()]
                for topic in topics:
                    topic_difficulty_data.append({
                        'topic': topic,
                        'difficulty': row['difficulty'],
                        'difficulty_weight': self.difficulty_weights.get(row['difficulty'], 0),
                        'frequency': row['frequency'],
                        'acceptance_rate': row['acceptance_rate']
                    })
        
        if not topic_difficulty_data:
            logger.warning("No topic-difficulty pairs found")
            return pd.DataFrame()
        
        topic_df = pd.DataFrame(topic_difficulty_data)
        
        # Analyze each topic
        topic_analysis = []
        
        for topic in topic_df['topic'].unique():
            topic_data = topic_df[topic_df['topic'] == topic]
            
            if len(topic_data) < 3:  # Skip topics with too few data points
                continue
            
            # Calculate difficulty statistics
            difficulty_dist = topic_data['difficulty'].value_counts(normalize=True)
            weighted_difficulty = np.average(
                topic_data['difficulty_weight'], 
                weights=topic_data['frequency']
            )
            
            # Calculate correlations
            if len(topic_data) > 1:
                # Correlation between difficulty weight and acceptance rate
                difficulty_acceptance_corr = topic_data['difficulty_weight'].corr(
                    topic_data['acceptance_rate']
                )
                
                # Correlation between difficulty weight and frequency
                difficulty_frequency_corr = topic_data['difficulty_weight'].corr(
                    topic_data['frequency']
                )
            else:
                difficulty_acceptance_corr = 0
                difficulty_frequency_corr = 0
            
            # Statistical tests
            easy_data = topic_data[topic_data['difficulty'] == 'EASY']['acceptance_rate']
            hard_data = topic_data[topic_data['difficulty'] == 'HARD']['acceptance_rate']
            
            if len(easy_data) > 0 and len(hard_data) > 0:
                # T-test between easy and hard problems
                t_stat, p_value = stats.ttest_ind(easy_data, hard_data)
            else:
                t_stat, p_value = 0, 1
            
            analysis = {
                'topic': topic,
                'total_problems': len(topic_data),
                'weighted_avg_difficulty': weighted_difficulty,
                'difficulty_acceptance_correlation': difficulty_acceptance_corr,
                'difficulty_frequency_correlation': difficulty_frequency_corr,
                'easy_percentage': difficulty_dist.get('EASY', 0) * 100,
                'medium_percentage': difficulty_dist.get('MEDIUM', 0) * 100,
                'hard_percentage': difficulty_dist.get('HARD', 0) * 100,
                'avg_acceptance_rate': topic_data['acceptance_rate'].mean(),
                'avg_frequency': topic_data['frequency'].mean(),
                'easy_hard_ttest_pvalue': p_value,
                'difficulty_preference': self._classify_difficulty_preference(difficulty_dist),
                'acceptance_rate_by_difficulty': {
                    diff: topic_data[topic_data['difficulty'] == diff]['acceptance_rate'].mean()
                    for diff in topic_data['difficulty'].unique()
                }
            }
            
            topic_analysis.append(analysis)
        
        if not topic_analysis:
            logger.warning("No topic correlations could be calculated")
            return pd.DataFrame()
        
        result_df = pd.DataFrame(topic_analysis)
        result_df = result_df.sort_values('weighted_avg_difficulty', ascending=False)
        
        logger.info(f"Analyzed difficulty correlations for {len(result_df)} topics")
        return result_df
    
    def analyze_company_difficulty_preferences(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze company preferences for different difficulty levels.
        
        Args:
            df: Dataset DataFrame
            
        Returns:
            DataFrame with company difficulty preference analysis
        """
        logger.info("Analyzing company difficulty preferences")
        
        if df.empty:
            logger.warning("No data available")
            return pd.DataFrame()
        
        company_analysis = []
        
        for company in df['company'].unique():
            company_data = df[df['company'] == company]
            
            if company_data.empty:
                continue
            
            # Calculate difficulty distribution
            difficulty_dist = company_data['difficulty'].value_counts(normalize=True)
            
            # Calculate weighted difficulty score
            weighted_difficulty = np.average(
                [self.difficulty_weights.get(d, 0) for d in company_data['difficulty']],
                weights=company_data['frequency']
            )
            
            # Calculate acceptance rate by difficulty
            acceptance_by_difficulty = company_data.groupby('difficulty')['acceptance_rate'].agg([
                'mean', 'std', 'count'
            ]).round(3)
            
            # Calculate frequency by difficulty
            frequency_by_difficulty = company_data.groupby('difficulty')['frequency'].agg([
                'sum', 'mean', 'count'
            ]).round(2)
            
            # Determine difficulty preference
            difficulty_preference = self._classify_difficulty_preference(difficulty_dist)
            
            # Calculate difficulty diversity (entropy)
            difficulty_entropy = self._calculate_entropy(difficulty_dist.values)
            
            analysis = {
                'company': company,
                'total_problems': len(company_data),
                'unique_problems': company_data['title'].nunique(),
                'weighted_avg_difficulty': weighted_difficulty,
                'difficulty_preference': difficulty_preference,
                'difficulty_diversity': difficulty_entropy,
                'easy_percentage': difficulty_dist.get('EASY', 0) * 100,
                'medium_percentage': difficulty_dist.get('MEDIUM', 0) * 100,
                'hard_percentage': difficulty_dist.get('HARD', 0) * 100,
                'avg_acceptance_rate': company_data['acceptance_rate'].mean(),
                'total_frequency': company_data['frequency'].sum(),
                'acceptance_rate_by_difficulty': acceptance_by_difficulty.to_dict('index'),
                'frequency_by_difficulty': frequency_by_difficulty.to_dict('index')
            }
            
            company_analysis.append(analysis)
        
        if not company_analysis:
            logger.warning("No company analysis could be performed")
            return pd.DataFrame()
        
        result_df = pd.DataFrame(company_analysis)
        result_df = result_df.sort_values('weighted_avg_difficulty', ascending=False)
        
        logger.info(f"Analyzed difficulty preferences for {len(result_df)} companies")
        return result_df
    
    def analyze_acceptance_frequency_correlation(self, df: pd.DataFrame, 
                                               group_by: str = 'difficulty') -> Dict[str, Any]:
        """
        Analyze correlation between acceptance rate and problem frequency.
        
        Args:
            df: Dataset DataFrame
            group_by: Group analysis by ('difficulty', 'company', 'overall')
            
        Returns:
            Dictionary with correlation analysis results
        """
        logger.info(f"Analyzing acceptance rate vs frequency correlation (group by: {group_by})")
        
        if df.empty or 'acceptance_rate' not in df.columns or 'frequency' not in df.columns:
            logger.warning("Insufficient data for correlation analysis")
            return {}
        
        correlation_results = {
            'group_by': group_by,
            'correlations': {},
            'scatter_data': {},
            'summary_statistics': {}
        }
        
        if group_by == 'overall':
            correlation_results.update(self._calculate_acceptance_frequency_correlation(df, 'overall'))
        elif group_by == 'difficulty':
            for difficulty in df['difficulty'].unique():
                if pd.notna(difficulty):
                    group_data = df[df['difficulty'] == difficulty]
                    if len(group_data) > 1:
                        group_results = self._calculate_acceptance_frequency_correlation(group_data, difficulty)
                        correlation_results['correlations'][difficulty] = group_results['correlation']
                        correlation_results['scatter_data'][difficulty] = group_results['scatter_data']
                        correlation_results['summary_statistics'][difficulty] = group_results['summary_stats']
        elif group_by == 'company':
            # Analyze top companies only (to avoid too much data)
            top_companies = df['company'].value_counts().head(10).index
            for company in top_companies:
                company_data = df[df['company'] == company]
                if len(company_data) > 1:
                    group_results = self._calculate_acceptance_frequency_correlation(company_data, company)
                    correlation_results['correlations'][company] = group_results['correlation']
                    correlation_results['scatter_data'][company] = group_results['scatter_data']
                    correlation_results['summary_statistics'][company] = group_results['summary_stats']
        
        logger.info(f"Completed acceptance rate vs frequency correlation analysis")
        return correlation_results
    
    def find_difficulty_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Find problems with difficulty ratings that don't match their acceptance rates.
        
        Args:
            df: Dataset DataFrame
            
        Returns:
            DataFrame with difficulty anomaly analysis
        """
        logger.info("Finding difficulty anomalies")
        
        if df.empty or 'acceptance_rate' not in df.columns or 'difficulty' not in df.columns:
            logger.warning("Insufficient data for anomaly detection")
            return pd.DataFrame()
        
        # Calculate expected acceptance rate ranges for each difficulty
        difficulty_acceptance_stats = df.groupby('difficulty')['acceptance_rate'].agg([
            'mean', 'std', 'median', 'count'
        ]).round(3)
        
        anomalies = []
        
        for _, row in df.iterrows():
            difficulty = row['difficulty']
            acceptance_rate = row['acceptance_rate']
            
            if pd.isna(difficulty) or pd.isna(acceptance_rate):
                continue
            
            if difficulty not in difficulty_acceptance_stats.index:
                continue
            
            stats = difficulty_acceptance_stats.loc[difficulty]
            
            if stats['count'] < 5:  # Skip difficulties with too few samples
                continue
            
            # Calculate z-score
            if stats['std'] > 0:
                z_score = (acceptance_rate - stats['mean']) / stats['std']
            else:
                z_score = 0
            
            # Determine if it's an anomaly
            is_anomaly = abs(z_score) > 2  # More than 2 standard deviations
            
            if is_anomaly:
                # Classify type of anomaly
                if difficulty == 'EASY' and acceptance_rate < 0.3:
                    anomaly_type = 'unexpectedly_hard_easy'
                elif difficulty == 'HARD' and acceptance_rate > 0.7:
                    anomaly_type = 'unexpectedly_easy_hard'
                elif difficulty == 'MEDIUM' and acceptance_rate < 0.2:
                    anomaly_type = 'unexpectedly_hard_medium'
                elif difficulty == 'MEDIUM' and acceptance_rate > 0.8:
                    anomaly_type = 'unexpectedly_easy_medium'
                else:
                    anomaly_type = 'general_anomaly'
                
                anomalies.append({
                    'title': row['title'],
                    'company': row['company'],
                    'difficulty': difficulty,
                    'acceptance_rate': acceptance_rate,
                    'expected_acceptance_rate': stats['mean'],
                    'z_score': z_score,
                    'anomaly_type': anomaly_type,
                    'frequency': row['frequency'],
                    'link': row.get('link', ''),
                    'topics': row.get('topics', '')
                })
        
        if not anomalies:
            logger.info("No difficulty anomalies detected")
            return pd.DataFrame()
        
        anomalies_df = pd.DataFrame(anomalies)
        anomalies_df = anomalies_df.sort_values('z_score', key=abs, ascending=False)
        
        logger.info(f"Found {len(anomalies_df)} difficulty anomalies")
        return anomalies_df
    
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
        
        return filtered_df
    
    def _calculate_overall_difficulty_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate overall difficulty distribution statistics."""
        difficulty_stats = df.groupby('difficulty').agg({
            'title': 'nunique',
            'frequency': ['sum', 'mean', 'std'],
            'acceptance_rate': ['mean', 'std', 'median'],
            'company': 'nunique'
        }).round(3)
        
        # Flatten column names
        difficulty_stats.columns = [
            'unique_problems', 'total_frequency', 'avg_frequency', 'freq_std',
            'avg_acceptance_rate', 'acceptance_std', 'median_acceptance_rate', 'companies'
        ]
        
        difficulty_stats = difficulty_stats.reset_index()
        
        # Add percentage distribution
        total_problems = difficulty_stats['unique_problems'].sum()
        difficulty_stats['percentage'] = (difficulty_stats['unique_problems'] / total_problems * 100).round(2)
        
        return difficulty_stats
    
    def _calculate_company_difficulty_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate difficulty statistics grouped by company."""
        company_difficulty = df.groupby(['company', 'difficulty']).agg({
            'title': 'nunique',
            'frequency': 'sum',
            'acceptance_rate': 'mean'
        }).round(3)
        
        # Pivot to get difficulties as columns
        company_stats = company_difficulty.pivot_table(
            index='company',
            columns='difficulty',
            values=['title', 'frequency', 'acceptance_rate'],
            fill_value=0
        )
        
        # Flatten column names
        company_stats.columns = [f'{col[1]}_{col[0]}' for col in company_stats.columns]
        company_stats = company_stats.reset_index()
        
        return company_stats
    
    def _calculate_timeframe_difficulty_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate difficulty statistics grouped by timeframe."""
        timeframe_difficulty = df.groupby(['timeframe', 'difficulty']).agg({
            'title': 'nunique',
            'frequency': 'sum',
            'acceptance_rate': 'mean'
        }).round(3)
        
        # Pivot to get difficulties as columns
        timeframe_stats = timeframe_difficulty.pivot_table(
            index='timeframe',
            columns='difficulty',
            values=['title', 'frequency', 'acceptance_rate'],
            fill_value=0
        )
        
        # Flatten column names
        timeframe_stats.columns = [f'{col[1]}_{col[0]}' for col in timeframe_stats.columns]
        timeframe_stats = timeframe_stats.reset_index()
        
        return timeframe_stats
    
    def _calculate_topic_difficulty_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate difficulty statistics for topics."""
        # This requires exploded topics data
        topic_difficulty_data = []
        
        for _, row in df.iterrows():
            if pd.notna(row['topics']):
                topics = [t.strip() for t in str(row['topics']).split(',') if t.strip()]
                for topic in topics:
                    topic_difficulty_data.append({
                        'topic': topic,
                        'difficulty': row['difficulty'],
                        'frequency': row['frequency'],
                        'acceptance_rate': row['acceptance_rate']
                    })
        
        if not topic_difficulty_data:
            return pd.DataFrame()
        
        topic_df = pd.DataFrame(topic_difficulty_data)
        
        topic_stats = topic_df.groupby(['topic', 'difficulty']).agg({
            'frequency': 'sum',
            'acceptance_rate': 'mean'
        }).round(3)
        
        # Pivot to get difficulties as columns
        topic_difficulty_stats = topic_stats.pivot_table(
            index='topic',
            columns='difficulty',
            values=['frequency', 'acceptance_rate'],
            fill_value=0
        )
        
        # Flatten column names
        topic_difficulty_stats.columns = [f'{col[1]}_{col[0]}' for col in topic_difficulty_stats.columns]
        topic_difficulty_stats = topic_difficulty_stats.reset_index()
        
        return topic_difficulty_stats
    
    def _detect_outliers_in_group(self, group_data: pd.DataFrame, 
                                method: str, group_name: str) -> List[Dict[str, Any]]:
        """Detect outliers in a specific group."""
        if len(group_data) < 4:  # Need minimum data points
            return []
        
        acceptance_rates = group_data['acceptance_rate'].dropna()
        
        if len(acceptance_rates) < 4:
            return []
        
        outliers = []
        
        if method == 'iqr':
            Q1 = acceptance_rates.quantile(0.25)
            Q3 = acceptance_rates.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_mask = (acceptance_rates < lower_bound) | (acceptance_rates > upper_bound)
            
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(acceptance_rates))
            outlier_mask = z_scores > 2
            
        else:  # Default to IQR
            Q1 = acceptance_rates.quantile(0.25)
            Q3 = acceptance_rates.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_mask = (acceptance_rates < lower_bound) | (acceptance_rates > upper_bound)
        
        outlier_indices = acceptance_rates[outlier_mask].index
        
        for idx in outlier_indices:
            row = group_data.loc[idx]
            
            if method == 'zscore':
                outlier_score = abs(stats.zscore(acceptance_rates)[acceptance_rates.index.get_loc(idx)])
            else:
                # Calculate distance from median as score
                median_rate = acceptance_rates.median()
                outlier_score = abs(row['acceptance_rate'] - median_rate)
            
            outliers.append({
                'title': row['title'],
                'company': row['company'],
                'difficulty': row['difficulty'],
                'acceptance_rate': row['acceptance_rate'],
                'frequency': row['frequency'],
                'group': group_name,
                'outlier_score': outlier_score,
                'method': method,
                'link': row.get('link', ''),
                'topics': row.get('topics', '')
            })
        
        return outliers
    
    def _classify_difficulty_preference(self, difficulty_dist: pd.Series) -> str:
        """Classify difficulty preference based on distribution."""
        easy_pct = difficulty_dist.get('EASY', 0)
        medium_pct = difficulty_dist.get('MEDIUM', 0)
        hard_pct = difficulty_dist.get('HARD', 0)
        
        if easy_pct > 0.6:
            return 'easy_focused'
        elif hard_pct > 0.5:
            return 'hard_focused'
        elif medium_pct > 0.5:
            return 'medium_focused'
        elif abs(easy_pct - medium_pct) < 0.1 and abs(medium_pct - hard_pct) < 0.1:
            return 'balanced'
        elif easy_pct + medium_pct > 0.8:
            return 'easy_medium_focused'
        elif medium_pct + hard_pct > 0.8:
            return 'medium_hard_focused'
        else:
            return 'mixed'
    
    def _calculate_entropy(self, probabilities: np.ndarray) -> float:
        """Calculate entropy for diversity measurement."""
        probabilities = probabilities[probabilities > 0]  # Remove zeros
        if len(probabilities) <= 1:
            return 0
        return -np.sum(probabilities * np.log2(probabilities))
    
    def _calculate_acceptance_frequency_correlation(self, df: pd.DataFrame, 
                                                  group_name: str) -> Dict[str, Any]:
        """Calculate correlation between acceptance rate and frequency for a group."""
        if len(df) < 3:
            return {
                'correlation': 0,
                'p_value': 1,
                'scatter_data': [],
                'summary_stats': {}
            }
        
        # Calculate correlation
        correlation = df['acceptance_rate'].corr(df['frequency'])
        
        # Statistical significance test
        _, p_value = stats.pearsonr(df['acceptance_rate'], df['frequency'])
        
        # Prepare scatter plot data
        scatter_data = df[['title', 'acceptance_rate', 'frequency', 'difficulty']].to_dict('records')
        
        # Summary statistics
        summary_stats = {
            'count': len(df),
            'acceptance_rate_mean': df['acceptance_rate'].mean(),
            'acceptance_rate_std': df['acceptance_rate'].std(),
            'frequency_mean': df['frequency'].mean(),
            'frequency_std': df['frequency'].std(),
            'correlation_strength': self._classify_correlation_strength(abs(correlation))
        }
        
        return {
            'correlation': correlation,
            'p_value': p_value,
            'scatter_data': scatter_data,
            'summary_stats': summary_stats
        }
    
    def _classify_correlation_strength(self, abs_correlation: float) -> str:
        """Classify correlation strength."""
        if abs_correlation < 0.1:
            return 'negligible'
        elif abs_correlation < 0.3:
            return 'weak'
        elif abs_correlation < 0.5:
            return 'moderate'
        elif abs_correlation < 0.7:
            return 'strong'
        else:
            return 'very_strong'