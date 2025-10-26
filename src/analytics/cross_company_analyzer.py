"""
Cross-company analysis functionality for LeetCode Analytics API.

This module provides analysis capabilities for aggregating problem frequency
data across multiple companies, ranking problems, and filtering by various criteria.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np

from ..models.data_models import FilterCriteria, Difficulty, Timeframe, ProblemStats

logger = logging.getLogger(__name__)


class CrossCompanyAnalyzer:
    """
    Analyzes problem frequency and statistics across multiple companies.
    
    Features:
    - Aggregates frequency data across all companies for each problem
    - Ranks problems by total frequency, company count, and other metrics
    - Supports filtering by difficulty, timeframe, and other criteria
    - Provides detailed statistics for cross-company analysis
    """
    
    def __init__(self):
        """Initialize the cross-company analyzer."""
        logger.info("CrossCompanyAnalyzer initialized")
    
    def get_top_problems(self, df: pd.DataFrame, filters: FilterCriteria, 
                        limit: int = 100, sort_by: str = 'total_frequency') -> pd.DataFrame:
        """
        Get top problems ranked across all companies.
        
        Args:
            df: Unified dataset DataFrame
            filters: Filter criteria to apply
            limit: Maximum number of problems to return
            sort_by: Column to sort by ('total_frequency', 'company_count', 'avg_acceptance_rate')
            
        Returns:
            DataFrame with top problems and their aggregated statistics
        """
        logger.info(f"Getting top {limit} problems sorted by {sort_by}")
        
        # Apply filters
        filtered_df = self._apply_filters(df, filters)
        
        if filtered_df.empty:
            logger.warning("No data remaining after applying filters")
            return pd.DataFrame()
        
        # Aggregate by problem title
        aggregated = self._aggregate_by_problem(filtered_df)
        
        # Sort and limit results
        if sort_by not in aggregated.columns:
            logger.warning(f"Sort column '{sort_by}' not found, using 'total_frequency'")
            sort_by = 'total_frequency'
        
        result = aggregated.sort_values(sort_by, ascending=False).head(limit)
        
        logger.info(f"Returning {len(result)} top problems")
        return result
    
    def get_problem_statistics(self, df: pd.DataFrame, problem_title: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed statistics for a specific problem across companies.
        
        Args:
            df: Unified dataset DataFrame
            problem_title: Title of the problem to analyze
            
        Returns:
            Dictionary with detailed problem statistics or None if not found
        """
        problem_data = df[df['title'] == problem_title]
        
        if problem_data.empty:
            logger.warning(f"Problem '{problem_title}' not found in dataset")
            return None
        
        # Basic statistics
        stats = {
            'title': problem_title,
            'total_frequency': problem_data['frequency'].sum(),
            'avg_frequency': problem_data['frequency'].mean(),
            'max_frequency': problem_data['frequency'].max(),
            'min_frequency': problem_data['frequency'].min(),
            'company_count': problem_data['company'].nunique(),
            'companies': sorted(problem_data['company'].unique().tolist()),
            'avg_acceptance_rate': problem_data['acceptance_rate'].mean(),
            'difficulty': problem_data['difficulty'].iloc[0] if len(problem_data) > 0 else None,
            'link': problem_data['link'].iloc[0] if len(problem_data) > 0 else None,
        }
        
        # Topics analysis
        all_topics = []
        for topics_str in problem_data['topics'].dropna():
            if isinstance(topics_str, str):
                topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                all_topics.extend(topics)
        
        if all_topics:
            topic_counts = pd.Series(all_topics).value_counts()
            stats['primary_topics'] = topic_counts.head(5).to_dict()
            stats['all_topics'] = sorted(list(set(all_topics)))
        else:
            stats['primary_topics'] = {}
            stats['all_topics'] = []
        
        # Timeframe distribution
        timeframe_stats = problem_data.groupby('timeframe').agg({
            'frequency': ['sum', 'mean', 'count'],
            'company': 'nunique'
        }).round(2)
        
        stats['timeframe_distribution'] = {}
        for timeframe in timeframe_stats.index:
            stats['timeframe_distribution'][timeframe] = {
                'total_frequency': timeframe_stats.loc[timeframe, ('frequency', 'sum')],
                'avg_frequency': timeframe_stats.loc[timeframe, ('frequency', 'mean')],
                'occurrences': timeframe_stats.loc[timeframe, ('frequency', 'count')],
                'companies': timeframe_stats.loc[timeframe, ('company', 'nunique')]
            }
        
        logger.info(f"Generated statistics for problem '{problem_title}'")
        return stats
    
    def get_company_rankings(self, df: pd.DataFrame, filters: FilterCriteria) -> pd.DataFrame:
        """
        Get companies ranked by various metrics.
        
        Args:
            df: Unified dataset DataFrame
            filters: Filter criteria to apply
            
        Returns:
            DataFrame with company rankings and statistics
        """
        logger.info("Generating company rankings")
        
        # Apply filters
        filtered_df = self._apply_filters(df, filters)
        
        if filtered_df.empty:
            logger.warning("No data remaining after applying filters")
            return pd.DataFrame()
        
        # Aggregate by company
        company_stats = filtered_df.groupby('company').agg({
            'title': 'nunique',  # unique problems
            'frequency': ['sum', 'mean', 'max'],
            'acceptance_rate': 'mean',
            'difficulty': lambda x: x.value_counts().to_dict()
        }).round(2)
        
        # Flatten column names
        company_stats.columns = [
            'unique_problems', 'total_frequency', 'avg_frequency', 
            'max_frequency', 'avg_acceptance_rate', 'difficulty_distribution'
        ]
        
        # Add company name as column
        company_stats = company_stats.reset_index()
        
        # Calculate additional metrics
        company_stats['problems_per_difficulty'] = company_stats['difficulty_distribution'].apply(
            lambda x: {k: v for k, v in x.items()}
        )
        
        # Sort by total frequency
        company_stats = company_stats.sort_values('total_frequency', ascending=False)
        
        logger.info(f"Generated rankings for {len(company_stats)} companies")
        return company_stats
    
    def find_common_problems(self, df: pd.DataFrame, companies: List[str], 
                           min_companies: int = None) -> pd.DataFrame:
        """
        Find problems that appear across multiple specified companies.
        
        Args:
            df: Unified dataset DataFrame
            companies: List of company names to analyze
            min_companies: Minimum number of companies a problem must appear in
            
        Returns:
            DataFrame with problems common across companies
        """
        if min_companies is None:
            min_companies = max(2, len(companies) // 2)
        
        logger.info(f"Finding problems common to at least {min_companies} companies from {companies}")
        
        # Filter to specified companies
        company_data = df[df['company'].isin(companies)]
        
        if company_data.empty:
            logger.warning("No data found for specified companies")
            return pd.DataFrame()
        
        # Find problems that appear in multiple companies
        problem_companies = company_data.groupby('title')['company'].nunique()
        common_problems = problem_companies[problem_companies >= min_companies].index
        
        if len(common_problems) == 0:
            logger.warning(f"No problems found in at least {min_companies} companies")
            return pd.DataFrame()
        
        # Get detailed stats for common problems
        common_data = company_data[company_data['title'].isin(common_problems)]
        result = self._aggregate_by_problem(common_data)
        
        # Add company list for each problem
        company_lists = common_data.groupby('title')['company'].apply(
            lambda x: sorted(x.unique().tolist())
        )
        result['companies'] = result['title'].map(company_lists)
        
        # Sort by company count and frequency
        result = result.sort_values(['company_count', 'total_frequency'], ascending=False)
        
        logger.info(f"Found {len(result)} problems common across companies")
        return result
    
    def compare_companies(self, df: pd.DataFrame, company1: str, company2: str) -> Dict[str, Any]:
        """
        Compare two companies across various metrics.
        
        Args:
            df: Unified dataset DataFrame
            company1: First company name
            company2: Second company name
            
        Returns:
            Dictionary with comparison statistics
        """
        logger.info(f"Comparing companies: {company1} vs {company2}")
        
        # Get data for each company
        data1 = df[df['company'] == company1]
        data2 = df[df['company'] == company2]
        
        if data1.empty or data2.empty:
            logger.warning("One or both companies not found in dataset")
            return {}
        
        # Basic statistics comparison
        comparison = {
            'company1': company1,
            'company2': company2,
            'statistics': {
                company1: self._get_company_stats(data1),
                company2: self._get_company_stats(data2)
            }
        }
        
        # Find common and unique problems
        problems1 = set(data1['title'].unique())
        problems2 = set(data2['title'].unique())
        
        comparison['problem_overlap'] = {
            'common_problems': len(problems1 & problems2),
            'unique_to_company1': len(problems1 - problems2),
            'unique_to_company2': len(problems2 - problems1),
            'total_unique_problems': len(problems1 | problems2),
            'overlap_percentage': len(problems1 & problems2) / len(problems1 | problems2) * 100
        }
        
        # Common problems with frequency comparison
        common_problems = list(problems1 & problems2)
        if common_problems:
            common_comparison = []
            for problem in common_problems:
                freq1 = data1[data1['title'] == problem]['frequency'].sum()
                freq2 = data2[data2['title'] == problem]['frequency'].sum()
                common_comparison.append({
                    'title': problem,
                    f'{company1}_frequency': freq1,
                    f'{company2}_frequency': freq2,
                    'frequency_ratio': freq1 / freq2 if freq2 > 0 else float('inf')
                })
            
            comparison['common_problems_detail'] = sorted(
                common_comparison, 
                key=lambda x: abs(x['frequency_ratio'] - 1), 
                reverse=True
            )[:10]  # Top 10 most different
        
        logger.info(f"Generated comparison between {company1} and {company2}")
        return comparison
    
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
        
        if filters.min_frequency is not None:
            filtered_df = filtered_df[filtered_df['frequency'] >= filters.min_frequency]
        
        if filters.max_frequency is not None:
            filtered_df = filtered_df[filtered_df['frequency'] <= filters.max_frequency]
        
        if filters.min_acceptance_rate is not None:
            filtered_df = filtered_df[filtered_df['acceptance_rate'] >= filters.min_acceptance_rate]
        
        if filters.max_acceptance_rate is not None:
            filtered_df = filtered_df[filtered_df['acceptance_rate'] <= filters.max_acceptance_rate]
        
        return filtered_df
    
    def _aggregate_by_problem(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate data by problem title."""
        aggregated = df.groupby('title').agg({
            'frequency': 'sum',
            'acceptance_rate': 'mean',
            'company': 'nunique',
            'difficulty': 'first',
            'link': 'first',
            'topics': 'first'
        }).round(2)
        
        # Rename columns
        aggregated.columns = [
            'total_frequency', 'avg_acceptance_rate', 'company_count',
            'difficulty', 'link', 'topics'
        ]
        
        # Reset index to make title a column
        aggregated = aggregated.reset_index()
        
        # Calculate trend score (simple metric based on frequency and company count)
        aggregated['trend_score'] = (
            aggregated['total_frequency'] * 0.7 + 
            aggregated['company_count'] * 10 * 0.3
        ).round(2)
        
        # Parse topics into list
        aggregated['primary_topics'] = aggregated['topics'].apply(
            lambda x: [t.strip() for t in str(x).split(',') if t.strip()] if pd.notna(x) else []
        )
        
        return aggregated
    
    def _get_company_stats(self, company_data: pd.DataFrame) -> Dict[str, Any]:
        """Get basic statistics for a company's data."""
        return {
            'total_problems': len(company_data),
            'unique_problems': company_data['title'].nunique(),
            'avg_frequency': company_data['frequency'].mean(),
            'total_frequency': company_data['frequency'].sum(),
            'avg_acceptance_rate': company_data['acceptance_rate'].mean(),
            'difficulty_distribution': company_data['difficulty'].value_counts().to_dict(),
            'timeframe_distribution': company_data['timeframe'].value_counts().to_dict()
        }