from __future__ import annotations

"""
Dataset management system for LeetCode Analytics API.

This module handles unified dataset creation, merging processed CSV data,
and managing the caching of large datasets with progress tracking.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Tuple
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup

from .cache_manager import CacheManager
from .data_processor import DataProcessor
from .csv_discovery import CSVDiscovery
from .csv_loader import CSVLoader

logger = logging.getLogger(__name__)


class DatasetManager:
    """
    Manages unified dataset creation and caching for the LeetCode Analytics system.
    
    Features:
    - Merges all processed CSV data into unified datasets
    - Handles both exploded and non-exploded topic views
    - Progress tracking for large dataset processing
    - Automatic caching with Parquet compression
    """
    
    def __init__(self, cache_manager: CacheManager, data_processor: DataProcessor,
                 csv_discovery: CSVDiscovery, csv_loader: CSVLoader):
        """
        Initialize the dataset manager.
        
        Args:
            cache_manager: Cache manager instance
            data_processor: Data processor instance
            csv_discovery: CSV discovery service
            csv_loader: CSV loader service
        """
        self.cache_manager = cache_manager
        self.data_processor = data_processor
        self.csv_discovery = csv_discovery
        self.csv_loader = csv_loader

        # Cache keys for different dataset types
        self.UNIFIED_DATASET_KEY = "unified_dataset"
        self.EXPLODED_DATASET_KEY = "exploded_dataset"
        self.COMPANY_STATS_KEY = "company_stats"

        logger.info("DatasetManager initialized")
        self._last_empty_file_report: List[Dict[str, Any]] = []
        self._leetcode_metadata_df: Optional[pd.DataFrame] = None

    def _ensure_discovery_root(self, root_path: Optional[str]) -> None:
        """Ensure the CSV discovery service is pointing at the desired root."""
        if root_path is None:
            return

        current_root = getattr(self.csv_discovery, 'root_directory', None)
        try:
            if current_root is None or Path(current_root) != Path(root_path):
                from .csv_discovery import CSVDiscovery
                self.csv_discovery = CSVDiscovery(root_path)
        except Exception as exc:
            logger.error(f"Failed to initialize CSV discovery for '{root_path}': {exc}")
            raise

    def _impute_acceptance_rates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing acceptance rates and flag incomplete records."""
        if df.empty or 'acceptance_rate' not in df.columns:
            return df

        # Work on a copy to avoid mutating caller data
        imputed_df = df.copy()
        imputed_df['acceptance_rate'] = pd.to_numeric(
            imputed_df['acceptance_rate'], errors='coerce'
        )

        initial_missing = imputed_df['acceptance_rate'].isna()
        imputed_df['acceptance_rate_imputed'] = False
        imputed_df['acceptance_rate_imputation_method'] = 'original'

        if not initial_missing.any():
            imputed_df['acceptance_rate_missing'] = False
            return imputed_df

        available = imputed_df.loc[~initial_missing, ['title', 'timeframe', 'acceptance_rate']]
        title_time_dict = {}
        title_dict = {}
        overall_mean = None

        if not available.empty:
            title_time_dict = (
                available.groupby(['title', 'timeframe'])['acceptance_rate']
                .mean()
                .to_dict()
            )
            title_dict = (
                available.groupby('title')['acceptance_rate']
                .mean()
                .to_dict()
            )
            overall_mean = available['acceptance_rate'].mean()

        imputed_indices: List[int] = []
        imputation_methods: List[str] = []

        for idx, row in imputed_df.loc[initial_missing, ['title', 'timeframe']].iterrows():
            imputed_value = None
            method = None

            key = (row.get('title'), row.get('timeframe'))
            if key in title_time_dict:
                imputed_value = title_time_dict[key]
                method = 'title_timeframe'
            elif row.get('title') in title_dict:
                imputed_value = title_dict[row.get('title')]
                method = 'title_average'
            elif overall_mean is not None and not pd.isna(overall_mean):
                imputed_value = overall_mean
                method = 'global_average'

            if imputed_value is not None:
                imputed_df.at[idx, 'acceptance_rate'] = imputed_value
                imputed_indices.append(idx)
                imputation_methods.append(method)

        if imputed_indices:
            imputed_df.loc[imputed_indices, 'acceptance_rate_imputed'] = True
            imputed_df.loc[imputed_indices, 'acceptance_rate_imputation_method'] = imputation_methods

        # Flag any remaining missing values explicitly
        final_missing = imputed_df['acceptance_rate'].isna()
        if final_missing.any():
            imputed_df['acceptance_rate_imputation_method'] = imputed_df['acceptance_rate_imputation_method'].where(
                ~final_missing, 'missing'
            )
            logger.warning(
                "Acceptance rate imputation could not resolve %d records; they remain flagged as missing.",
                final_missing.sum()
            )

        imputed_df['acceptance_rate_missing'] = final_missing

        if imputed_indices:
            method_breakdown = {}
            for method in imputation_methods:
                method_breakdown[method] = method_breakdown.get(method, 0) + 1
            logger.info(
                "Imputed acceptance rates for %d records (methods: %s)",
                len(imputed_indices),
                ', '.join(f"{k}={v}" for k, v in method_breakdown.items())
            )

        return imputed_df

    def _log_empty_file_report(self, processing_reports: List[Dict[str, Any]]) -> None:
        """Merge discovery and processing reports for empty CSV files and log summary."""
        discovery_reports = []
        if hasattr(self.csv_discovery, 'empty_file_report'):
            discovery_reports = self.csv_discovery.empty_file_report

        combined_reports: List[Dict[str, Any]] = []
        if discovery_reports:
            combined_reports.extend(discovery_reports)
        if processing_reports:
            combined_reports.extend(processing_reports)

        self._last_empty_file_report = combined_reports

        if not combined_reports:
            return

        summary_lines = []
        for report in combined_reports:
            company = report.get('company', 'unknown')
            timeframe = report.get('timeframe', 'unknown')
            file_path = report.get('file_path') or 'unknown'
            reason = report.get('reason', 'unspecified')
            summary_lines.append(f"- {company} [{timeframe}] -> {file_path} ({reason})")

        logger.warning(
            "Skipped %d CSV files due to being empty or unreadable:\n%s",
            len(combined_reports),
            '\n'.join(summary_lines)
        )

    def get_last_empty_file_report(self) -> List[Dict[str, Any]]:
        """Expose the most recent empty CSV file report."""
        return list(self._last_empty_file_report)

    def _deduplicate_dataset(self, df: pd.DataFrame, key_columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Remove duplicate rows based on the specified key columns.

        Args:
            df: DataFrame to deduplicate
            key_columns: Columns to use for duplicate detection; defaults to
                title/company/timeframe if available

        Returns:
            Tuple of (deduplicated DataFrame, stats dictionary)
        """
        if df.empty:
            return df, {'removed_duplicates': 0, 'total_rows': 0, 'key_columns': key_columns or []}

        available_columns = set(df.columns)
        if not key_columns:
            default_keys = ['title', 'company', 'timeframe']
            key_columns = [col for col in default_keys if col in available_columns]

        if not key_columns:
            logger.warning("Deduplication skipped: none of the key columns are present")
            return df, {'removed_duplicates': 0, 'total_rows': len(df), 'key_columns': []}

        # Flag duplicates while keeping the first occurrence
        duplicate_mask = df.duplicated(subset=key_columns, keep='first')
        duplicates_count = duplicate_mask.sum()

        if duplicates_count == 0:
            return df, {
                'removed_duplicates': 0,
                'total_rows': len(df),
                'key_columns': key_columns
            }

        deduped_df = df.loc[~duplicate_mask].reset_index(drop=True)

        stats = {
            'removed_duplicates': int(duplicates_count),
            'total_rows': len(df),
            'remaining_rows': len(deduped_df),
            'key_columns': key_columns
        }

        logger.info(
            "Deduplicated dataset using keys %s: removed %d of %d rows",
            key_columns,
            duplicates_count,
            len(df)
        )

        return deduped_df, stats

    @staticmethod
    def _extract_title_slug_from_link(link: Any) -> Optional[str]:
        if not isinstance(link, str) or not link:
            return None
        match = re.search(r"https?://leetcode\.com/problems/([\w-]+)/?", link)
        if match:
            return match.group(1).strip().lower()
        return None

    @staticmethod
    def _slugify_title(title: Any) -> Optional[str]:
        if not isinstance(title, str) or not title.strip():
            return None
        slug = re.sub(r'[^a-z0-9]+', '-', title.strip().lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug or None

    def _ensure_title_slug_column(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'title_slug' not in df.columns:
            df['title_slug'] = pd.NA

        df['title_slug'] = df['title_slug'].astype('string')
        df['title_slug'] = df['title_slug'].str.strip().str.lower()

        if 'link' in df.columns:
            missing_mask = df['title_slug'].isna() | (df['title_slug'] == '')
            df.loc[missing_mask, 'title_slug'] = df.loc[missing_mask, 'link'].apply(self._extract_title_slug_from_link)

        if 'title' in df.columns:
            missing_mask = df['title_slug'].isna() | (df['title_slug'] == '')
            df.loc[missing_mask, 'title_slug'] = df.loc[missing_mask, 'title'].apply(self._slugify_title)

        df['title_slug'] = df['title_slug'].fillna('').astype(str)
        df.loc[df['title_slug'] == '', 'title_slug'] = pd.NA
        return df

    def _load_external_metadata(self) -> Optional[pd.DataFrame]:
        if self._leetcode_metadata_df is not None:
            return self._leetcode_metadata_df

        try:
            from ..config.settings import config
        except Exception:
            logger.warning('Unable to access configuration for metadata enrichment')
            return None

        metadata_path: Optional[str] = None

        if hasattr(config, 'get_config'):
            metadata_path = config.get_config('LEETCODE_METADATA_PATH')
            logger.warning(metadata_path)
            logger.warning('1')

        if not metadata_path and hasattr(config, 'settings'):
            metadata_path = getattr(config.settings, 'LEETCODE_METADATA_PATH', None)
            logger.warning(metadata_path)
        if not metadata_path:
            logger.warning('LEETCODE_METADATA_PATH not set; skipping metadata enrichment')
            return None

        metadata_file = Path(metadata_path)
        if not metadata_file.exists():
            logger.warning('LeetCode metadata file not found at %s', metadata_file)
            return None

        try:
            metadata_df = pd.read_parquet(metadata_file)
            logger.info('Loaded metadata parquet: %s rows, columns=%s', len(metadata_df), list(metadata_df.columns))
        except Exception as exc:
            logger.error('Failed to read LeetCode metadata parquet: %s', exc)
            return None

        slug_column = None
        for candidate in ['title_slug', 'titleslug', 'titleslug_1']:
            if candidate in metadata_df.columns:
                slug_column = candidate
                break

        if slug_column is None:
            logger.warning('Metadata file lacks a usable title slug column')
            return None

        metadata_df['title_slug'] = metadata_df[slug_column].astype(str).str.strip().str.lower()
        metadata_df = metadata_df.dropna(subset=['title_slug'])

        if metadata_df.empty:
            logger.warning('Metadata file at %s contains zero rows after slug normalization', metadata_file)
            return None

        first_row = metadata_df.iloc[0]
        logger.info(
            'Metadata sample: slug=%s, has_html=%s, has_text=%s',
            first_row.get('title_slug'),
            bool(first_row.get('content_html')), 
            bool(first_row.get('content_text'))
        )

        column_map = {}
        for column in metadata_df.columns:
            if column == 'title_slug':
                continue
            normalized = column
            if normalized.startswith('question_'):
                normalized = normalized[len('question_'):]
            if normalized.startswith('leetcode_'):
                normalized = normalized[len('leetcode_'):]
            if normalized == 'fetched_at':
                target_name = 'leetcode_fetched_at'
            else:
                target_name = f'leetcode_{normalized}'
            column_map[column] = target_name

        metadata_df = metadata_df.rename(columns=column_map)
        columns = ['title_slug'] + [col for col in metadata_df.columns if col != 'title_slug']
        self._leetcode_metadata_df = metadata_df[columns]
        logger.info('Loaded LeetCode metadata with %d records from %s', len(self._leetcode_metadata_df), metadata_file)
        return self._leetcode_metadata_df

    def _enrich_with_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        metadata_df = self._load_external_metadata()
        if metadata_df is None or metadata_df.empty:
            return df

        if 'title_slug' not in df.columns:
            return df

        return df.merge(metadata_df, on='title_slug', how='left')

    def create_unified_dataset(self, root_path: str, force_refresh: bool = False,
                             progress_callback: Optional[Callable[[int, int], None]] = None) -> pd.DataFrame:
        """
        Create unified dataset from all CSV files.
        
        Args:
            root_path: Root directory containing company CSV files
            force_refresh: Force recreation even if cache is valid
            progress_callback: Optional callback for progress updates (current, total)
            
        Returns:
            Unified DataFrame with all processed data
        """
        self._ensure_discovery_root(root_path)
        # Discover all CSV files
        csv_files = self.csv_discovery.discover_csv_files()
        source_file_paths = [str(csv_file.file_path) for csv_file in csv_files]
        
        # Generate cache key
        cache_key = self.cache_manager.generate_cache_key(
            self.UNIFIED_DATASET_KEY, 
            source_file_paths
        )
        
        # Check if we can use cached data
        if not force_refresh and self.cache_manager.is_cache_valid(cache_key, source_file_paths):
            logger.info("Loading unified dataset from cache")
            cached_data = self.cache_manager.load_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        logger.info(f"Creating unified dataset from {len(csv_files)} CSV files")
        
        # Process all CSV files with progress tracking
        all_dataframes = []
        total_files = len(csv_files)
        
        # Use tqdm for progress bar if no custom callback provided
        pbar = None
        if progress_callback is None:
            pbar = tqdm(total=total_files, desc="Processing CSV files")
            def default_callback(current: int, total: int):
                pbar.update(1)
            progress_callback = default_callback

        try:
            empty_dataset_reports: List[Dict[str, Any]] = []
            for i, csv_file in enumerate(csv_files):
                try:
                    # Load CSV data
                    raw_df, validation = self.csv_loader.load_single_file(csv_file)
                    if validation and not validation.is_valid:
                        logger.warning(
                            "Validation failed for %s: %s", csv_file.file_path, validation.errors
                        )
                        continue
                    if raw_df is None:
                        empty_dataset_reports.append({
                            'company': csv_file.company,
                            'timeframe': csv_file.timeframe.value,
                            'file_path': csv_file.file_path,
                            'reason': 'load_failed',
                            'details': validation.errors if validation else []
                        })
                        logger.warning(f"Skipping unreadable CSV file: {csv_file.file_path}")
                        continue

                    if raw_df.empty:
                        empty_dataset_reports.append({
                            'company': csv_file.company,
                            'timeframe': csv_file.timeframe.value,
                            'file_path': csv_file.file_path,
                            'reason': 'no_data_rows',
                            'details': validation.warnings if validation else []
                        })
                        logger.warning(f"Skipping CSV with no data rows: {csv_file.file_path}")
                        continue

                    # Process the data
                    processed_df = self.data_processor.process_csv_data(raw_df, csv_file)
                    if processed_df is not None and not processed_df.empty:
                        all_dataframes.append(processed_df)
                        logger.debug(f"Processed {len(processed_df)} records from {csv_file.file_path}")
                    
                except Exception as e:
                    logger.error(f"Error processing {csv_file.file_path}: {e}")
                    continue
                
                # Update progress
                progress_callback(i + 1, total_files)
            
            if pbar is not None:
                pbar.close()

        except Exception as e:
            if pbar is not None:
                pbar.close()
            raise e
        
        if not all_dataframes:
            logger.error("No valid data found in any CSV files")
            self._log_empty_file_report(empty_dataset_reports)
            return pd.DataFrame()

        # Merge all dataframes
        logger.info(f"Merging {len(all_dataframes)} processed dataframes")
        unified_df = pd.concat(all_dataframes, ignore_index=True)

        # Rescue missing acceptance rates before adding metadata
        unified_df = self._impute_acceptance_rates(unified_df)
        unified_df = self._ensure_title_slug_column(unified_df)

        # Deduplicate rows before adding metadata columns
        unified_df, dedupe_stats = self._deduplicate_dataset(unified_df)
        unified_df = self._enrich_with_metadata(unified_df)

        # Add dataset metadata
        unified_df['dataset_created_at'] = datetime.now()
        unified_df['total_companies'] = unified_df['company'].nunique()
        unified_df['total_problems'] = unified_df['title'].nunique()

        logger.info(f"Created unified dataset with {len(unified_df)} records from {unified_df['company'].nunique()} companies")

        # Log summary of empty/invalid CSV files encountered
        self._log_empty_file_report(empty_dataset_reports)

        # Log deduplication summary
        if dedupe_stats.get('removed_duplicates', 0) > 0:
            logger.info(
                "Removed %d duplicate rows (keys=%s). Remaining rows: %d",
                dedupe_stats['removed_duplicates'],
                dedupe_stats['key_columns'],
                dedupe_stats['remaining_rows']
            )
        else:
            logger.info("No duplicate rows detected with keys %s", dedupe_stats.get('key_columns', []))

        # Cache the unified dataset
        if self.cache_manager.save_to_cache(unified_df, cache_key, source_file_paths):
            logger.info("Unified dataset cached successfully")
        else:
            logger.warning("Failed to cache unified dataset")

        return unified_df
    
    def get_unified_dataset(self, root_path: str = None, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        Get the unified dataset, loading from cache or creating if needed.
        
        Args:
            root_path: Root directory containing CSV files (uses config default if not provided)
            force_refresh: Force recreation even if cache is valid
            
        Returns:
            Unified DataFrame or None if no data available
        """
        if root_path is None:
            from ..config.settings import config
            root_path = config.get_config("DATA_ROOT_PATH", ".")
        
        try:
            return self.create_unified_dataset(root_path, force_refresh)
        except Exception as e:
            logger.error(f"Failed to get unified dataset: {e}")
            return None
    
    def create_exploded_dataset(self, unified_df: Optional[pd.DataFrame] = None,
                              root_path: str = None, force_refresh: bool = False) -> pd.DataFrame:
        """
        Create exploded dataset with topics split into separate rows.
        
        Args:
            unified_df: Pre-loaded unified dataset (optional)
            root_path: Root directory for CSV files (required if unified_df not provided)
            force_refresh: Force recreation even if cache is valid
            
        Returns:
            DataFrame with exploded topics
        """
        # Generate cache key for exploded dataset
        if unified_df is not None:
            # Use a hash of the unified dataset for cache key
            cache_key = self.cache_manager.generate_cache_key(
                self.EXPLODED_DATASET_KEY + "_from_memory"
            )
        else:
            # Update CSV discovery root path if different
            self._ensure_discovery_root(root_path)
            # Use source files for cache key
            csv_files = self.csv_discovery.discover_csv_files()
            source_file_paths = [str(csv_file.file_path) for csv_file in csv_files]
            cache_key = self.cache_manager.generate_cache_key(
                self.EXPLODED_DATASET_KEY,
                source_file_paths
            )
        
        # Check cache
        if not force_refresh and self.cache_manager.is_cache_valid(cache_key):
            logger.info("Loading exploded dataset from cache")
            cached_data = self.cache_manager.load_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Get unified dataset if not provided
        if unified_df is None:
            if root_path is None:
                raise ValueError("Either unified_df or root_path must be provided")
            unified_df = self.create_unified_dataset(root_path, force_refresh)
        
        logger.info("Creating exploded dataset from unified data")
        
        # Create exploded dataset using the data processor
        exploded_df = self.data_processor.explode_topics(unified_df)
        
        logger.info(f"Created exploded dataset with {len(exploded_df)} records")
        
        # Cache the exploded dataset
        source_files = [] if unified_df is not None else None
        if self.cache_manager.save_to_cache(exploded_df, cache_key, source_files):
            logger.info("Exploded dataset cached successfully")
        else:
            logger.warning("Failed to cache exploded dataset")
        
        return exploded_df
    
    def create_company_statistics(self, unified_df: Optional[pd.DataFrame] = None,
                                root_path: str = None, force_refresh: bool = False) -> pd.DataFrame:
        """
        Create pre-computed company statistics for faster queries.
        
        Args:
            unified_df: Pre-loaded unified dataset (optional)
            root_path: Root directory for CSV files (required if unified_df not provided)
            force_refresh: Force recreation even if cache is valid
            
        Returns:
            DataFrame with company-level statistics
        """
        # Generate cache key
        cache_key = self.cache_manager.generate_cache_key(self.COMPANY_STATS_KEY)
        
        # Check cache
        if not force_refresh and self.cache_manager.is_cache_valid(cache_key):
            logger.info("Loading company statistics from cache")
            cached_data = self.cache_manager.load_from_cache(cache_key, "analytics")
            if cached_data is not None:
                return cached_data
        
        # Get unified dataset if not provided
        if unified_df is None:
            if root_path is None:
                raise ValueError("Either unified_df or root_path must be provided")
            unified_df = self.create_unified_dataset(root_path, force_refresh)
        
        logger.info("Creating company statistics")
        
        # Calculate company-level statistics
        company_stats = []
        
        for company in unified_df['company'].unique():
            company_data = unified_df[unified_df['company'] == company]
            
            # Basic statistics
            stats = {
                'company': company,
                'total_problems': len(company_data),
                'unique_problems': company_data['title'].nunique(),
                'avg_frequency': company_data['frequency'].mean(),
                'max_frequency': company_data['frequency'].max(),
                'min_frequency': company_data['frequency'].min(),
            }
            
            # Add acceptance rate if available
            if 'acceptance_rate' in company_data.columns:
                stats['avg_acceptance_rate'] = company_data['acceptance_rate'].mean()
            else:
                stats['avg_acceptance_rate'] = None
            
            # Difficulty distribution
            difficulty_counts = company_data['difficulty'].value_counts()
            stats.update({
                'easy_count': difficulty_counts.get('EASY', 0),
                'medium_count': difficulty_counts.get('MEDIUM', 0),
                'hard_count': difficulty_counts.get('HARD', 0),
            })
            
            # Timeframe distribution
            timeframe_counts = company_data['timeframe'].value_counts()
            stats.update({
                'timeframe_30d': timeframe_counts.get('30d', 0),
                'timeframe_3m': timeframe_counts.get('3m', 0),
                'timeframe_6m': timeframe_counts.get('6m', 0),
                'timeframe_6m_plus': timeframe_counts.get('6m+', 0),
                'timeframe_all': timeframe_counts.get('all', 0),
            })
            
            # Top topics (most common)
            if 'topics' in company_data.columns:
                all_topics = []
                for topics_str in company_data['topics'].dropna():
                    if isinstance(topics_str, str):
                        topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                        all_topics.extend(topics)
                
                if all_topics:
                    topic_counts = pd.Series(all_topics).value_counts()
                    stats['top_topics'] = topic_counts.head(5).to_dict()
                    stats['total_unique_topics'] = len(topic_counts)
                else:
                    stats['top_topics'] = {}
                    stats['total_unique_topics'] = 0
            
            company_stats.append(stats)
        
        # Convert to DataFrame
        stats_df = pd.DataFrame(company_stats)
        stats_df['created_at'] = datetime.now()
        
        logger.info(f"Created statistics for {len(stats_df)} companies")
        
        # Cache the statistics
        if self.cache_manager.save_to_cache(stats_df, cache_key, cache_type="analytics"):
            logger.info("Company statistics cached successfully")
        else:
            logger.warning("Failed to cache company statistics")
        
        return stats_df
    
    def get_dataset_info(self, root_path: str) -> Dict[str, Any]:
        """
        Get information about available datasets and cache status.
        
        Args:
            root_path: Root directory containing CSV files
            
        Returns:
            Dictionary with dataset information
        """
        # Update CSV discovery root path if different
        self._ensure_discovery_root(root_path)
        
        # Discover CSV files
        csv_files = self.csv_discovery.discover_csv_files()
        source_file_paths = [str(csv_file.file_path) for csv_file in csv_files]
        
        # Check cache status for different datasets
        unified_key = self.cache_manager.generate_cache_key(
            self.UNIFIED_DATASET_KEY, source_file_paths
        )
        exploded_key = self.cache_manager.generate_cache_key(
            self.EXPLODED_DATASET_KEY, source_file_paths
        )
        stats_key = self.cache_manager.generate_cache_key(self.COMPANY_STATS_KEY)
        
        info = {
            'source_files': {
                'total_csv_files': len(csv_files),
                'companies': len(set(csv_file.company for csv_file in csv_files)),
                'timeframes': list(set(csv_file.timeframe for csv_file in csv_files)),
            },
            'cache_status': {
                'unified_dataset': {
                    'cached': self.cache_manager.is_cache_valid(unified_key, source_file_paths),
                    'cache_key': unified_key
                },
                'exploded_dataset': {
                    'cached': self.cache_manager.is_cache_valid(exploded_key, source_file_paths),
                    'cache_key': exploded_key
                },
                'company_stats': {
                    'cached': self.cache_manager.is_cache_valid(stats_key),
                    'cache_key': stats_key
                }
            },
            'cache_stats': self.cache_manager.get_cache_stats()
        }
        
        return info
    
    def refresh_all_datasets(self, root_path: str, 
                           progress_callback: Optional[Callable[[str, int, int], None]] = None) -> Dict[str, pd.DataFrame]:
        """
        Refresh all datasets (unified, exploded, and company stats).
        
        Args:
            root_path: Root directory containing CSV files
            progress_callback: Optional callback for progress updates (stage, current, total)
            
        Returns:
            Dictionary containing all refreshed datasets
        """
        logger.info("Refreshing all datasets")

        def update_progress(stage: str, current: int, total: int):
            if progress_callback:
                progress_callback(stage, current, total)
        
        # Create unified dataset
        update_progress("unified", 0, 3)
        unified_df = self.create_unified_dataset(
            root_path, 
            force_refresh=True,
            progress_callback=lambda c, t: update_progress("unified_processing", c, t)
        )
        
        # Create exploded dataset
        update_progress("exploded", 1, 3)
        exploded_df = self.create_exploded_dataset(unified_df, force_refresh=True)
        
        # Create company statistics
        update_progress("statistics", 2, 3)
        stats_df = self.create_company_statistics(unified_df, force_refresh=True)
        
        update_progress("complete", 3, 3)
        
        logger.info("All datasets refreshed successfully")
        
        return {
            'unified': unified_df,
            'exploded': exploded_df,
            'company_stats': stats_df
        }
