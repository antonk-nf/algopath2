"""
Main analytics engine for LeetCode Analytics API.

This module provides a unified interface to all analytics capabilities,
coordinating between different analyzers and providing high-level analytics operations.
"""

import logging
from collections import Counter
from typing import List, Optional, Dict, Any, Union
import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype

from .cross_company_analyzer import CrossCompanyAnalyzer
from .topic_analyzer import TopicAnalyzer
from .trend_analyzer import TrendAnalyzer
from .difficulty_analyzer import DifficultyAnalyzer
from ..models.data_models import FilterCriteria, ProblemStats

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Main analytics engine that coordinates all analysis capabilities.
    
    Features:
    - Unified interface to all analytics modules
    - Cross-company problem analysis
    - Topic trend and correlation analysis
    - Temporal trend detection
    - Difficulty and acceptance rate analysis
    - Comprehensive filtering and aggregation
    """
    
    def __init__(self):
        """Initialize the analytics engine with all analyzer components."""
        self.cross_company_analyzer = CrossCompanyAnalyzer()
        self.topic_analyzer = TopicAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.difficulty_analyzer = DifficultyAnalyzer()
        
        logger.info("AnalyticsEngine initialized with all analyzer components")
    
    def get_top_problems(self, df: pd.DataFrame, filters: FilterCriteria = None,
                        limit: int = 100, sort_by: str = 'total_frequency') -> pd.DataFrame:
        """
        Get top problems ranked across all companies.
        
        Args:
            df: Unified dataset DataFrame
            filters: Filter criteria to apply
            limit: Maximum number of problems to return
            sort_by: Column to sort by
            
        Returns:
            DataFrame with top problems and their aggregated statistics
        """
        if filters is None:
            filters = FilterCriteria()
        
        return self.cross_company_analyzer.get_top_problems(df, filters, limit, sort_by)
    
    def analyze_topic_trends(self, df: pd.DataFrame, timeframes: List[str] = None) -> pd.DataFrame:
        """
        Analyze topic trends across different timeframes.
        
        Args:
            df: Dataset DataFrame
            timeframes: List of timeframes to analyze
            
        Returns:
            DataFrame with topic trend analysis
        """
        return self.topic_analyzer.analyze_topic_trends(df, timeframes)

    def generate_topic_heatmap(self, df: pd.DataFrame,
                               companies: Optional[List[str]] = None,
                               topics: Optional[List[str]] = None,
                               top_n: int = 30) -> Dict[str, Any]:
        """Generate topic-company heatmap data."""
        return self.topic_analyzer.generate_topic_heatmap_data(
            df,
            companies=companies,
            topics=topics,
            top_n=top_n
        )
    
    def get_company_correlations(
        self,
        df: pd.DataFrame,
        metric: str = 'composite',
        include_features: bool = False,
        companies_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get correlations between companies based on specified metric.

        Args:
            df: Dataset DataFrame
            metric: Metric to analyze correlations for
            include_features: Whether to include feature vectors in the response (debugging)
            companies_filter: Optional subset of companies to include in correlation output

        Returns:
            Dictionary with correlation analysis results
        """
        metric = metric or 'composite'
        logger.info("Analyzing company correlations", extra={"metric": metric})

        if metric == 'frequency':
            return self._analyze_company_frequency_correlations(df if not companies_filter else df[df['company'].isin(companies_filter)])
        if metric == 'difficulty':
            return self._analyze_company_difficulty_correlations(df if not companies_filter else df[df['company'].isin(companies_filter)])
        if metric == 'topics':
            return self._analyze_company_topic_correlations(df if not companies_filter else df[df['company'].isin(companies_filter)])
        if metric == 'acceptance_rate':
            # Acceptance rate similarity just delegates to composite for now since it incorporates rate
            logger.info("Acceptance rate correlation delegated to composite blend")
            return self._analyze_company_composite_correlations(
                df,
                include_features=include_features,
                companies_filter=companies_filter
            )

        # Default to composite blended similarity
        return self._analyze_company_composite_correlations(
            df,
            include_features=include_features,
            companies_filter=companies_filter
        )
    
    def calculate_difficulty_stats(self, df: pd.DataFrame, groupby: str = 'overall') -> pd.DataFrame:
        """
        Calculate difficulty-based statistics.
        
        Args:
            df: Dataset DataFrame
            groupby: How to group the analysis ('overall', 'company', 'timeframe', 'topics')
            
        Returns:
            DataFrame with difficulty statistics
        """
        # Map 'overall' to None for the difficulty analyzer
        group_param = None if groupby == 'overall' else groupby
        return self.difficulty_analyzer.analyze_difficulty_distribution(df, group_param)
    
    def get_comprehensive_analysis(self, df: pd.DataFrame, 
                                 filters: FilterCriteria = None) -> Dict[str, Any]:
        """
        Get a comprehensive analysis report covering all major analytics.
        
        Args:
            df: Dataset DataFrame
            filters: Filter criteria to apply
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        logger.info("Generating comprehensive analysis report")
        
        if filters is None:
            filters = FilterCriteria()
        
        # Apply filters to dataset
        filtered_df = self._apply_filters(df, filters)
        
        if filtered_df.empty:
            logger.warning("No data remaining after applying filters")
            return {}
        
        analysis_report = {
            'dataset_summary': self._generate_dataset_summary(filtered_df),
            'top_problems': self.get_top_problems(filtered_df, limit=20),
            'topic_analysis': {
                'frequency': self.topic_analyzer.get_topic_frequency(filtered_df, limit=20),
                'trends': self.topic_analyzer.analyze_topic_trends(filtered_df),
                'correlations': self.topic_analyzer.get_topic_correlations(filtered_df)
            },
            'difficulty_analysis': {
                'overall_distribution': self.difficulty_analyzer.analyze_difficulty_distribution(filtered_df),
                'company_preferences': self.difficulty_analyzer.analyze_company_difficulty_preferences(filtered_df),
                'topic_correlations': self.difficulty_analyzer.analyze_difficulty_topic_correlation(filtered_df),
                'outliers': self.difficulty_analyzer.detect_acceptance_rate_outliers(filtered_df)
            },
            'trend_analysis': {
                'problem_trends': self.trend_analyzer.analyze_problem_trends(filtered_df),
                'company_trends': self.trend_analyzer.analyze_company_trends(filtered_df),
                'momentum_changes': self.trend_analyzer.identify_momentum_changes(filtered_df)
            },
            'company_analysis': {
                'rankings': self.cross_company_analyzer.get_company_rankings(filtered_df, filters),
                'difficulty_preferences': self.difficulty_analyzer.analyze_company_difficulty_preferences(filtered_df)
            }
        }
        
        logger.info("Comprehensive analysis report generated successfully")
        return analysis_report
    
    def search_problems(self, df: pd.DataFrame, search_criteria: Dict[str, Any]) -> pd.DataFrame:
        """
        Search problems with flexible criteria.
        
        Args:
            df: Dataset DataFrame
            search_criteria: Dictionary with search parameters
            
        Returns:
            DataFrame with matching problems
        """
        logger.info("Searching problems with custom criteria")
        
        filtered_df = df.copy()
        
        # Apply search filters
        if 'title_contains' in search_criteria:
            title_pattern = search_criteria['title_contains']
            filtered_df = filtered_df[
                filtered_df['title'].str.contains(title_pattern, case=False, na=False)
            ]
        
        if 'companies' in search_criteria and search_criteria['companies'] is not None:
            filtered_df = filtered_df[filtered_df['company'].isin(search_criteria['companies'])]
        
        if 'difficulties' in search_criteria and search_criteria['difficulties'] is not None:
            filtered_df = filtered_df[filtered_df['difficulty'].isin(search_criteria['difficulties'])]
        
        if 'topics' in search_criteria and search_criteria['topics'] is not None:
            topic_pattern = '|'.join(search_criteria['topics'])
            filtered_df = filtered_df[
                filtered_df['topics'].str.contains(topic_pattern, case=False, na=False)
            ]
        
        if 'min_frequency' in search_criteria:
            filtered_df = filtered_df[filtered_df['frequency'] >= search_criteria['min_frequency']]
        
        if 'max_frequency' in search_criteria:
            filtered_df = filtered_df[filtered_df['frequency'] <= search_criteria['max_frequency']]
        
        if 'min_acceptance_rate' in search_criteria:
            filtered_df = filtered_df[filtered_df['acceptance_rate'] >= search_criteria['min_acceptance_rate']]
        
        if 'max_acceptance_rate' in search_criteria:
            filtered_df = filtered_df[filtered_df['acceptance_rate'] <= search_criteria['max_acceptance_rate']]
        
        # Sort results
        sort_by = search_criteria.get('sort_by', 'frequency')
        ascending = search_criteria.get('ascending', False)
        
        if sort_by in filtered_df.columns:
            filtered_df = filtered_df.sort_values(sort_by, ascending=ascending)
        
        # Limit results
        limit = search_criteria.get('limit', 100)
        filtered_df = filtered_df.head(limit)
        
        logger.info(f"Found {len(filtered_df)} problems matching search criteria")
        return filtered_df
    
    def get_analytics_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get a high-level summary of analytics capabilities and dataset statistics.
        
        Args:
            df: Dataset DataFrame
            
        Returns:
            Dictionary with analytics summary
        """
        logger.info("Generating analytics summary")
        
        summary = {
            'dataset_stats': {
                'total_records': len(df),
                'unique_problems': df['title'].nunique(),
                'unique_companies': df['company'].nunique(),
                'timeframes': sorted(df['timeframe'].unique().tolist()),
                'difficulties': df['difficulty'].value_counts().to_dict(),
                'date_range': {
                    'earliest': df['last_updated'].min() if 'last_updated' in df.columns else None,
                    'latest': df['last_updated'].max() if 'last_updated' in df.columns else None
                }
            },
            'top_metrics': {
                'most_frequent_problem': df.loc[df['frequency'].idxmax(), 'title'] if not df.empty else None,
                'highest_acceptance_rate': df.loc[df['acceptance_rate'].idxmax(), 'title'] if not df.empty else None,
                'most_active_company': df['company'].value_counts().index[0] if not df.empty else None,
                'most_common_topic': self._get_most_common_topic(df)
            },
            'analytics_capabilities': {
                'cross_company_analysis': [
                    'Top problems ranking',
                    'Company comparisons',
                    'Common problems identification',
                    'Company rankings'
                ],
                'topic_analysis': [
                    'Topic frequency analysis',
                    'Topic trend detection',
                    'Topic correlations',
                    'Heatmap generation'
                ],
                'trend_analysis': [
                    'Problem trend analysis',
                    'Company trend analysis',
                    'Seasonal pattern detection',
                    'Momentum change identification'
                ],
                'difficulty_analysis': [
                    'Difficulty distribution analysis',
                    'Acceptance rate outlier detection',
                    'Difficulty-topic correlations',
                    'Company difficulty preferences'
                ]
            }
        }

        # Company breakdown (top companies by problem count)
        if not df.empty:
            company_group = (
                df.groupby('company')
                  .agg(
                      total_problems=('title', 'count'),
                      unique_problems=('title', 'nunique'),
                      avg_frequency=('frequency', 'mean')
                  )
                  .sort_values('total_problems', ascending=False)
                  .head(50)
            )

            summary['company_breakdown'] = [
                {
                    'company': company,
                    'total_problems': int(row.total_problems),
                    'unique_problems': int(row.unique_problems),
                    'avg_frequency': float(row.avg_frequency) if pd.notna(row.avg_frequency) else 0.0
                }
                for company, row in company_group.iterrows()
            ]

            # Topic analysis
            topic_counts: Dict[str, Dict[str, Any]] = {}
            for _, record in df[['topics', 'company']].dropna(subset=['topics']).iterrows():
                topics = [t.strip() for t in str(record['topics']).split(',') if t.strip()]
                for topic in topics:
                    if topic not in topic_counts:
                        topic_counts[topic] = {
                            'frequency': 0,
                            'companies': set()
                        }
                    topic_counts[topic]['frequency'] += 1
                    topic_counts[topic]['companies'].add(record['company'])

            summary['topic_analysis'] = {
                'total_topics': len(topic_counts),
                'top_topics': [
                    {
                        'topic': topic,
                        'frequency': topic_data['frequency'],
                        'companies': len(topic_data['companies'])
                    }
                    for topic, topic_data in sorted(
                        topic_counts.items(),
                        key=lambda item: item[1]['frequency'],
                        reverse=True
                    )[:50]
                ]
            }
        else:
            summary['company_breakdown'] = []
            summary['topic_analysis'] = {
                'total_topics': 0,
                'top_topics': []
            }

        logger.info("Analytics summary generated successfully")
        return summary
    
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
            topic_pattern = '|'.join(filters.topics)
            filtered_df = filtered_df[
                filtered_df['topics'].str.contains(topic_pattern, case=False, na=False)
            ]
        
        if filters.min_frequency is not None:
            filtered_df = filtered_df[filtered_df['frequency'] >= filters.min_frequency]
        
        if filters.max_frequency is not None:
            filtered_df = filtered_df[filtered_df['frequency'] <= filters.max_frequency]
        
        if filters.min_acceptance_rate is not None:
            filtered_df = filtered_df[filtered_df['acceptance_rate'] >= filters.min_acceptance_rate]
        
        if filters.max_acceptance_rate is not None:
            filtered_df = filtered_df[filtered_df['acceptance_rate'] <= filters.max_acceptance_rate]
        
        return filtered_df
    
    def _generate_dataset_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate a summary of the dataset."""
        return {
            'total_records': len(df),
            'unique_problems': df['title'].nunique(),
            'unique_companies': df['company'].nunique(),
            'avg_frequency': df['frequency'].mean(),
            'avg_acceptance_rate': df['acceptance_rate'].mean(),
            'difficulty_distribution': df['difficulty'].value_counts(normalize=True).to_dict(),
            'timeframe_distribution': df['timeframe'].value_counts().to_dict()
        }

    def _analyze_company_composite_correlations(
        self,
        df: pd.DataFrame,
        include_features: bool = False,
        companies_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze composite correlations between companies using blended interview signals."""
        if df.empty:
            logger.warning("Composite correlation requested on empty dataset")
            return {}

        if 'company' not in df.columns:
            logger.warning("Dataset missing 'company' column for composite correlation analysis")
            return {}

        dataset = df.copy()
        dataset = dataset[dataset['company'].notna()]

        available_companies = sorted(dataset['company'].unique().tolist())
        if len(available_companies) < 2:
            logger.warning("Composite correlation requires at least two companies to compare")
            return {}

        if companies_filter:
            companies = sorted([c for c in companies_filter if c in available_companies])
            if len(companies) < 2:
                logger.warning("Company filter yielded fewer than two companies; returning empty result")
                return {}
        else:
            companies = available_companies

        dataset = dataset[dataset['company'].isin(companies)].copy()
        if dataset.empty:
            logger.warning("No records available for selected companies")
            return {}

        def _coerce_numeric(series: pd.Series) -> pd.Series:
            if series is None:
                return pd.Series(dtype=float)
            if is_numeric_dtype(series):
                numeric = pd.to_numeric(series, errors='coerce')
            else:
                cleaned = series.astype(str).str.replace(r'[^0-9eE+\-\.]+', '', regex=True)
                numeric = pd.to_numeric(cleaned, errors='coerce')
            return numeric.fillna(0.0)

        alias_map = {
            'acceptance_rate': ['acceptance_rate', 'leetcode_acrate', 'leetcode_acceptance_rate'],
            'likes': ['likes', 'leetcode_likes'],
            'dislikes': ['dislikes', 'leetcode_dislikes'],
            'frequency': ['frequency']
        }

        for target, candidates in alias_map.items():
            source_series = None
            for candidate in candidates:
                if candidate in dataset.columns:
                    source_series = dataset[candidate]
                    break
            if source_series is None:
                dataset[target] = 0.0
            else:
                dataset[target] = _coerce_numeric(source_series)

        dataset['reaction_sum'] = dataset['likes'] + dataset['dislikes']

        def _max_scale(frame: pd.DataFrame) -> pd.DataFrame:
            if frame is None or frame.empty:
                return frame
            scaled = frame.copy()
            maxima = frame.max(axis=0)
            nonzero = maxima > 1e-9
            if nonzero.any():
                scaled.loc[:, nonzero] = scaled.loc[:, nonzero].div(maxima[nonzero], axis=1)
            scaled.loc[:, ~nonzero] = 0.0
            return scaled.fillna(0.0)

        def _extract_topics(value: Any) -> List[str]:
            if isinstance(value, str):
                return [topic.strip() for topic in value.split(',') if topic.strip()]
            if isinstance(value, (list, tuple, set)):
                return [str(topic).strip() for topic in value if str(topic).strip()]
            return []

        topic_counter: Counter[str] = Counter()
        company_topic_counters: Dict[str, Counter] = {company: Counter() for company in companies}

        for _, row in dataset[['company', 'topics']].iterrows():
            topics = _extract_topics(row['topics'])
            if not topics:
                continue
            topic_counter.update(topics)
            company_topic_counters[row['company']].update(topics)

        sorted_topics = [topic for topic, _ in topic_counter.most_common()]
        trimmed_topics = sorted_topics[5:-5] if len(sorted_topics) > 10 else sorted_topics
        if not trimmed_topics:
            trimmed_topics = sorted_topics
        topic_selection = trimmed_topics[:10]

        topic_columns = [f"topic::{topic}" for topic in topic_selection]
        topic_features = pd.DataFrame(0.0, index=companies, columns=topic_columns)
        for company, counter in company_topic_counters.items():
            total_topics = sum(counter.values())
            if total_topics == 0:
                continue
            for topic in topic_selection:
                topic_features.at[company, f"topic::{topic}"] = counter.get(topic, 0) / total_topics
        topic_block = topic_features

        difficulty_counts = dataset.groupby(['company', 'difficulty']).size().unstack(fill_value=0)
        expected_difficulties = ['EASY', 'MEDIUM', 'HARD', 'UNKNOWN']
        for difficulty in expected_difficulties:
            if difficulty not in difficulty_counts.columns:
                difficulty_counts[difficulty] = 0
        difficulty_counts = difficulty_counts[expected_difficulties]
        difficulty_pct = difficulty_counts.div(difficulty_counts.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
        difficulty_pct = difficulty_pct.reindex(companies, fill_value=0.0)
        difficulty_pct.columns = [f"difficulty::{col}" for col in difficulty_pct.columns]
        difficulty_block = difficulty_pct

        acceptance_stats = dataset.groupby('company')['acceptance_rate'].mean().reindex(companies).fillna(0.0)
        acceptance_stats = acceptance_stats.to_frame(name='continuous::acceptance_rate')
        if acceptance_stats['continuous::acceptance_rate'].max() > 1.5:
            acceptance_stats['continuous::acceptance_rate'] = acceptance_stats['continuous::acceptance_rate'] / 100.0
        acceptance_block = acceptance_stats

        # Row-level engagement metrics to capture per-problem behaviour
        dataset['row_votes'] = dataset['likes'] + dataset['dislikes']
        dataset['row_like_ratio'] = np.where(
            dataset['row_votes'] > 0,
            dataset['likes'] / dataset['row_votes'],
            np.nan
        )

        feedback_totals = dataset.groupby('company').agg(
            like_ratio=('row_like_ratio', 'mean'),
            likes_per_problem=('likes', 'mean'),
            votes_per_problem=('row_votes', 'mean'),
            avg_frequency=('frequency', 'mean')
        ).reindex(companies).fillna(0.0)

        feedback_features = feedback_totals.rename(columns={
            'like_ratio': 'feedback::like_ratio',
            'likes_per_problem': 'feedback::likes_per_problem',
            'votes_per_problem': 'feedback::votes_per_problem',
            'avg_frequency': 'feedback::avg_frequency'
        })

        topic_scaled = _max_scale(topic_block)
        difficulty_scaled = _max_scale(difficulty_block)
        acceptance_scaled = _max_scale(acceptance_block)
        feedback_scaled = _max_scale(feedback_features)

        def _filter_informative_columns(frame: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
            if frame is None or frame.empty:
                return None
            variances = frame.var(axis=0, ddof=0)
            informative_cols = variances[variances > 1e-12].index.tolist()
            if not informative_cols:
                return None
            return frame[informative_cols]

        topic_scaled = _filter_informative_columns(topic_scaled)
        difficulty_scaled = _filter_informative_columns(difficulty_scaled)
        acceptance_scaled = _filter_informative_columns(acceptance_scaled)
        feedback_scaled = _filter_informative_columns(feedback_scaled)

        def _classify_strength(value: float) -> str:
            magnitude = abs(value)
            if magnitude >= 0.75:
                return 'strong'
            if magnitude >= 0.4:
                return 'moderate'
            return 'weak'

        def _component_similarity(frame: pd.DataFrame, company_a: str, company_b: str) -> Optional[float]:
            if frame is None or frame.empty:
                return None
            if company_a not in frame.index or company_b not in frame.index:
                return None
            if frame.shape[1] == 1:
                values = frame.iloc[:, 0].to_numpy(dtype=float)
                idx_a = frame.index.get_loc(company_a)
                idx_b = frame.index.get_loc(company_b)
                difference = abs(values[idx_a] - values[idx_b])
                return float(np.clip(1.0 - difference, -1.0, 1.0))
            vector_a = frame.loc[company_a].to_numpy(dtype=float)
            vector_b = frame.loc[company_b].to_numpy(dtype=float)
            norm_a = np.linalg.norm(vector_a)
            norm_b = np.linalg.norm(vector_b)
            if norm_a == 0 or norm_b == 0:
                return None
            cosine = float(np.dot(vector_a, vector_b) / (norm_a * norm_b))
            return float(np.clip(cosine, -1.0, 1.0))

        component_blocks = {
            'topics': topic_scaled if topic_scaled is not None and not topic_scaled.empty else None,
            'difficulty': difficulty_scaled if difficulty_scaled is not None and not difficulty_scaled.empty else None,
            'acceptance_rate': acceptance_scaled if acceptance_scaled is not None and not acceptance_scaled.empty else None,
            'feedback': feedback_scaled if feedback_scaled is not None and not feedback_scaled.empty else None
        }

        component_weights = {
            'topics': 0.5,
            'difficulty': 0.2,
            'acceptance_rate': 0.15,
            'feedback': 0.15
        }

        available_blocks = {
            name: block for name, block in component_blocks.items()
            if block is not None and not block.empty
        }

        if not available_blocks:
            logger.warning("Composite correlation failed: all component blocks were empty")
            return {}

        raw_weights = {
            name: component_weights.get(name, 0.0)
            for name in available_blocks.keys()
        }
        weight_sum = sum(raw_weights.values())
        if weight_sum <= 0:
            normalized_weights = {
                name: 1.0 / len(available_blocks)
                for name in available_blocks.keys()
            }
        else:
            normalized_weights = {
                name: raw_weights[name] / weight_sum
                for name in available_blocks.keys()
            }

        weighted_blocks: List[pd.DataFrame] = []
        for name, block in available_blocks.items():
            weight = normalized_weights.get(name, 0.0)
            if weight <= 0:
                continue
            weighted_blocks.append(block * np.sqrt(weight))

        if not weighted_blocks:
            logger.warning("Composite correlation failed: no weighted feature blocks available")
            return {}

        combined_features = pd.concat(weighted_blocks, axis=1).reindex(companies).fillna(0.0)
        variances = combined_features.var(axis=0, ddof=0)
        informative_columns = variances[variances > 1e-12].index.tolist()
        if not informative_columns:
            logger.warning("Composite correlation failed: all derived features are constant")
            return {}

        informative_features = combined_features[informative_columns]

        feature_matrix = informative_features.to_numpy(dtype=float)
        norms = np.linalg.norm(feature_matrix, axis=1, keepdims=True)
        normalized_matrix = np.zeros_like(feature_matrix)
        nonzero_rows = norms.squeeze() > 0
        if nonzero_rows.any():
            normalized_matrix[nonzero_rows] = feature_matrix[nonzero_rows] / norms[nonzero_rows]

        similarity_matrix = normalized_matrix @ normalized_matrix.T
        similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)
        np.fill_diagonal(similarity_matrix, 1.0)

        correlations: List[Dict[str, Any]] = []
        for idx, company_a in enumerate(companies):
            for jdx in range(idx + 1, len(companies)):
                company_b = companies[jdx]
                value = float(similarity_matrix[idx, jdx])
                if np.isnan(value):
                    continue
                component_breakdown = {}
                for name, block in component_blocks.items():
                    score = _component_similarity(block, company_a, company_b)
                    if score is not None:
                        component_breakdown[name] = score
                correlations.append({
                    'company1': company_a,
                    'company2': company_b,
                    'correlation': value,
                    'metric': 'composite',
                    'strength': _classify_strength(value),
                    'components': component_breakdown
                })

        correlations.sort(key=lambda item: item['correlation'], reverse=True)

        correlation_dict = {
            company: {
                other: float(similarity_matrix[i, j])
                for j, other in enumerate(companies)
            }
            for i, company in enumerate(companies)
        }

        feature_metadata = {
            'topic_features': topic_selection,
            'difficulty_features': expected_difficulties,
            'acceptance_features': ['continuous::acceptance_rate'],
            'feedback_features': ['like_ratio', 'likes_per_problem', 'votes_per_problem', 'avg_frequency']
        }

        result = {
            'analysis_type': 'composite_correlation',
            'top_correlations': correlations,
            'correlation_matrix': correlation_dict,
            'feature_overview': feature_metadata,
            'component_weights': normalized_weights,
            'companies_analyzed': companies,
            'feature_count': len(informative_columns)
        }

        if include_features:
            debug_blocks: Dict[str, Any] = {}
            debug_blocks['topics_raw'] = topic_block.to_dict('index') if topic_block is not None else {}
            debug_blocks['topics_scaled'] = topic_scaled.to_dict('index') if topic_scaled is not None else {}
            debug_blocks['difficulty_raw'] = difficulty_block.to_dict('index') if difficulty_block is not None else {}
            debug_blocks['difficulty_scaled'] = difficulty_scaled.to_dict('index') if difficulty_scaled is not None else {}
            debug_blocks['acceptance_raw'] = acceptance_block.to_dict('index') if acceptance_block is not None else {}
            debug_blocks['acceptance_scaled'] = acceptance_scaled.to_dict('index') if acceptance_scaled is not None else {}
            debug_blocks['feedback_raw'] = feedback_features.to_dict('index') if not feedback_features.empty else {}
            debug_blocks['feedback_scaled'] = feedback_scaled.to_dict('index') if feedback_scaled is not None else {}

            result['debug'] = {
                'combined_features': informative_features.to_dict('index'),
                'feature_blocks': debug_blocks
            }

        return result


    def _analyze_company_difficulty_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations between companies based on difficulty preferences."""
        # Calculate difficulty distribution for each company
        company_difficulty = df.groupby(['company', 'difficulty']).size().unstack(fill_value=0)
        
        # Normalize to get percentages
        company_difficulty_pct = company_difficulty.div(company_difficulty.sum(axis=1), axis=0)
        
        # Calculate correlation matrix
        correlation_matrix = company_difficulty_pct.T.corr()
        
        # Find most correlated company pairs
        correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                company1 = correlation_matrix.columns[i]
                company2 = correlation_matrix.columns[j]
                correlation = correlation_matrix.iloc[i, j]
                
                if not pd.isna(correlation):
                    correlations.append({
                        'company1': company1,
                        'company2': company2,
                        'correlation': correlation
                    })
        
        correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return {
            'correlation_matrix': correlation_matrix.to_dict(),
            'top_correlations': correlations[:20],
            'difficulty_distributions': company_difficulty_pct.to_dict(),
            'analysis_type': 'difficulty_correlation'
        }
    
    def _analyze_company_topic_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations between companies based on topic preferences."""
        # Extract topics for each company
        company_topics = {}
        
        for company in df['company'].unique():
            company_data = df[df['company'] == company]
            topics = []
            
            for topics_str in company_data['topics'].dropna():
                if isinstance(topics_str, str):
                    topics.extend([t.strip() for t in topics_str.split(',') if t.strip()])
            
            if topics:
                from collections import Counter
                topic_counts = Counter(topics)
                company_topics[company] = topic_counts
        
        # Create company-topic matrix
        all_topics = set()
        for topics in company_topics.values():
            all_topics.update(topics.keys())
        
        company_topic_matrix = pd.DataFrame(0, 
                                          index=list(company_topics.keys()),
                                          columns=sorted(list(all_topics)))
        
        for company, topics in company_topics.items():
            for topic, count in topics.items():
                company_topic_matrix.loc[company, topic] = count
        
        # Normalize to get percentages
        company_topic_pct = company_topic_matrix.div(company_topic_matrix.sum(axis=1), axis=0)
        
        # Calculate correlation matrix
        correlation_matrix = company_topic_pct.corr()
        
        # Find most correlated company pairs
        correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                company1 = correlation_matrix.columns[i]
                company2 = correlation_matrix.columns[j]
                correlation = correlation_matrix.iloc[i, j]
                
                if not pd.isna(correlation):
                    correlations.append({
                        'company1': company1,
                        'company2': company2,
                        'correlation': correlation
                    })
        
        correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return {
            'correlation_matrix': correlation_matrix.to_dict(),
            'top_correlations': correlations[:20],
            'topic_distributions': company_topic_pct.to_dict(),
            'analysis_type': 'topic_correlation'
        }
    
    def _get_most_common_topic(self, df: pd.DataFrame) -> Optional[str]:
        """Get the most common topic across all problems."""
        all_topics = []
        
        for topics_str in df['topics'].dropna():
            if isinstance(topics_str, str):
                topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                all_topics.extend(topics)
        
        if all_topics:
            from collections import Counter
            topic_counts = Counter(all_topics)
            return topic_counts.most_common(1)[0][0]
        
        return None
