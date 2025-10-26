"""Data normalization system for standardizing CSV data formats."""

import logging
import pandas as pd
import re
from typing import Optional, Tuple, List
from urllib.parse import urlparse

from src.models.data_models import Difficulty, ValidationResult


logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalizes and standardizes CSV data formats."""
    
    # Regex patterns for data cleaning
    FREQUENCY_PATTERN = re.compile(r'(\d+(?:\.\d+)?)')
    ACCEPTANCE_RATE_PATTERN = re.compile(r'(\d+(?:\.\d+)?)%?')
    LEETCODE_URL_PATTERN = re.compile(r'https?://leetcode\.com/problems/[\w-]+/?')
    
    # Difficulty mapping variations
    DIFFICULTY_MAPPING = {
        'easy': Difficulty.EASY,
        'e': Difficulty.EASY,
        '1': Difficulty.EASY,
        'medium': Difficulty.MEDIUM,
        'med': Difficulty.MEDIUM,
        'm': Difficulty.MEDIUM,
        '2': Difficulty.MEDIUM,
        'hard': Difficulty.HARD,
        'h': Difficulty.HARD,
        '3': Difficulty.HARD,
        'difficult': Difficulty.HARD,
    }
    
    def __init__(self):
        """Initialize the data normalizer."""
        pass
    
    def normalize_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, ValidationResult]:
        """Normalize all data in the DataFrame.
        
        Args:
            df: Input DataFrame to normalize
            
        Returns:
            Tuple of (normalized DataFrame, validation result)
        """
        if df.empty:
            return df, ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["DataFrame is empty"],
                processed_rows=0,
                skipped_rows=0
            )
        
        logger.info(f"Starting normalization of {len(df)} rows")
        
        # Create a copy to avoid modifying the original
        normalized_df = df.copy()
        errors = []
        warnings = []
        initial_rows = len(normalized_df)
        
        # Normalize each column type
        try:
            normalized_df, freq_warnings = self._normalize_frequency(normalized_df)
            warnings.extend(freq_warnings)
            
            normalized_df, rate_warnings = self._normalize_acceptance_rate(normalized_df)
            warnings.extend(rate_warnings)
            
            normalized_df, diff_warnings = self._normalize_difficulty(normalized_df)
            warnings.extend(diff_warnings)
            
            normalized_df, title_warnings = self._normalize_titles(normalized_df)
            warnings.extend(title_warnings)
            
            normalized_df, link_warnings = self._normalize_links(normalized_df)
            warnings.extend(link_warnings)
            
            normalized_df, topic_warnings = self._normalize_topics(normalized_df)
            warnings.extend(topic_warnings)
            
        except Exception as e:
            error_msg = f"Error during normalization: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Remove rows with critical missing data
        before_cleanup = len(normalized_df)
        normalized_df = self._remove_invalid_rows(normalized_df)
        after_cleanup = len(normalized_df)
        skipped_rows = before_cleanup - after_cleanup
        
        if skipped_rows > 0:
            warnings.append(f"Removed {skipped_rows} rows with critical missing data")
        
        logger.info(f"Normalization complete: {len(normalized_df)} rows processed, {skipped_rows} rows skipped")
        
        validation_result = ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            processed_rows=len(normalized_df),
            skipped_rows=skipped_rows
        )
        
        return normalized_df, validation_result
    
    def _normalize_frequency(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Normalize frequency column to float64.
        
        Args:
            df: DataFrame with frequency column
            
        Returns:
            Tuple of (DataFrame with normalized frequency, warnings)
        """
        warnings = []
        
        if 'frequency' not in df.columns:
            warnings.append("No frequency column found")
            return df, warnings
        
        original_count = len(df)
        
        # Convert to string first to handle mixed types
        freq_series = df['frequency'].astype(str)
        
        # Extract numeric values using regex
        numeric_values = []
        for value in freq_series:
            if pd.isna(value) or value.lower() in ['nan', 'none', 'null', '']:
                numeric_values.append(0.0)
            else:
                match = self.FREQUENCY_PATTERN.search(str(value))
                if match:
                    try:
                        numeric_values.append(float(match.group(1)))
                    except ValueError:
                        numeric_values.append(0.0)
                else:
                    numeric_values.append(0.0)
        
        df['frequency'] = numeric_values
        
        # Ensure frequency is non-negative
        negative_count = (df['frequency'] < 0).sum()
        if negative_count > 0:
            df.loc[df['frequency'] < 0, 'frequency'] = 0.0
            warnings.append(f"Set {negative_count} negative frequency values to 0.0")
        
        # Check for values that seem too high (likely percentage instead of count)
        high_freq_count = (df['frequency'] > 100).sum()
        if high_freq_count > 0:
            warnings.append(f"Found {high_freq_count} frequency values > 100, may need manual review")
        
        zero_count = (df['frequency'] == 0.0).sum()
        if zero_count > 0:
            warnings.append(f"Set {zero_count} invalid/missing frequency values to 0.0")
        
        return df, warnings
    
    def _normalize_acceptance_rate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Normalize acceptance rate to percentage (0.0-1.0).
        
        Args:
            df: DataFrame with acceptance_rate column
            
        Returns:
            Tuple of (DataFrame with normalized acceptance rate, warnings)
        """
        warnings = []
        
        if 'acceptance_rate' not in df.columns:
            warnings.append("No acceptance_rate column found")
            return df, warnings
        
        # Convert to string first to handle mixed types
        rate_series = df['acceptance_rate'].astype(str)
        
        # Extract numeric values and convert to 0.0-1.0 range
        normalized_rates = []
        for value in rate_series:
            if pd.isna(value) or value.lower() in ['nan', 'none', 'null', '']:
                normalized_rates.append(None)  # Keep as None for missing data
            else:
                match = self.ACCEPTANCE_RATE_PATTERN.search(str(value))
                if match:
                    try:
                        rate_value = float(match.group(1))
                        # If value is > 1, assume it's a percentage and convert
                        if rate_value > 1:
                            rate_value = rate_value / 100.0
                        # Clamp to valid range
                        rate_value = max(0.0, min(1.0, rate_value))
                        normalized_rates.append(rate_value)
                    except ValueError:
                        normalized_rates.append(None)
                else:
                    normalized_rates.append(None)
        
        df['acceptance_rate'] = normalized_rates
        
        # Count missing values
        missing_count = df['acceptance_rate'].isna().sum()
        if missing_count > 0:
            warnings.append(f"Found {missing_count} missing/invalid acceptance rate values")
        
        return df, warnings
    
    def _normalize_difficulty(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Normalize difficulty to standard enum values.
        
        Args:
            df: DataFrame with difficulty column
            
        Returns:
            Tuple of (DataFrame with normalized difficulty, warnings)
        """
        warnings = []
        
        if 'difficulty' not in df.columns:
            warnings.append("No difficulty column found")
            return df, warnings
        
        # Normalize difficulty values
        normalized_difficulties = []
        unknown_count = 0
        
        for value in df['difficulty']:
            if pd.isna(value):
                normalized_difficulties.append(Difficulty.UNKNOWN.value)
                unknown_count += 1
            else:
                value_clean = str(value).lower().strip()
                if value_clean in self.DIFFICULTY_MAPPING:
                    normalized_difficulties.append(self.DIFFICULTY_MAPPING[value_clean].value)
                else:
                    normalized_difficulties.append(Difficulty.UNKNOWN.value)
                    unknown_count += 1
        
        df['difficulty'] = normalized_difficulties
        
        if unknown_count > 0:
            warnings.append(f"Set {unknown_count} unknown/missing difficulty values to UNKNOWN")
        
        return df, warnings
    
    def _normalize_titles(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Clean and validate problem titles.
        
        Args:
            df: DataFrame with title column
            
        Returns:
            Tuple of (DataFrame with cleaned titles, warnings)
        """
        warnings = []
        
        if 'title' not in df.columns:
            warnings.append("No title column found")
            return df, warnings
        
        # Clean titles
        cleaned_titles = []
        empty_count = 0
        
        for title in df['title']:
            if pd.isna(title) or str(title).strip() == '':
                cleaned_titles.append(None)
                empty_count += 1
            else:
                # Clean the title: strip whitespace, normalize spaces
                clean_title = re.sub(r'\s+', ' ', str(title).strip())
                # Remove common prefixes like problem numbers
                clean_title = re.sub(r'^\d+\.\s*', '', clean_title)
                cleaned_titles.append(clean_title)
        
        df['title'] = cleaned_titles
        
        if empty_count > 0:
            warnings.append(f"Found {empty_count} empty/missing titles")
        
        # Check for very short titles (likely invalid)
        short_titles = df['title'].str.len() < 3
        short_count = short_titles.sum()
        if short_count > 0:
            warnings.append(f"Found {short_count} very short titles (< 3 characters)")
        
        return df, warnings
    
    def _normalize_links(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Clean and validate LeetCode links.
        
        Args:
            df: DataFrame with link column
            
        Returns:
            Tuple of (DataFrame with cleaned links, warnings)
        """
        warnings = []
        
        if 'link' not in df.columns:
            warnings.append("No link column found")
            return df, warnings
        
        # Clean and validate links
        cleaned_links = []
        invalid_count = 0
        missing_count = 0
        
        for link in df['link']:
            if pd.isna(link) or str(link).strip() == '':
                cleaned_links.append(None)
                missing_count += 1
            else:
                link_str = str(link).strip()
                
                # Try to fix common issues
                if not link_str.startswith('http'):
                    if link_str.startswith('leetcode.com'):
                        link_str = 'https://' + link_str
                    elif link_str.startswith('www.leetcode.com'):
                        link_str = 'https://' + link_str
                    elif link_str.startswith('/problems/'):
                        link_str = 'https://leetcode.com' + link_str
                
                # Validate URL format
                try:
                    parsed = urlparse(link_str)
                    if parsed.netloc and 'leetcode.com' in parsed.netloc:
                        cleaned_links.append(link_str)
                    else:
                        cleaned_links.append(link_str)  # Keep original but mark as potentially invalid
                        invalid_count += 1
                except Exception:
                    cleaned_links.append(link_str)  # Keep original but mark as invalid
                    invalid_count += 1
        
        df['link'] = cleaned_links
        
        if missing_count > 0:
            warnings.append(f"Found {missing_count} missing links")
        
        if invalid_count > 0:
            warnings.append(f"Found {invalid_count} potentially invalid links")
        
        return df, warnings
    
    def _normalize_topics(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Clean and normalize topics column.
        
        Args:
            df: DataFrame with topics column
            
        Returns:
            Tuple of (DataFrame with cleaned topics, warnings)
        """
        warnings = []
        
        if 'topics' not in df.columns:
            warnings.append("No topics column found")
            return df, warnings
        
        # Clean topics
        cleaned_topics = []
        empty_count = 0
        
        for topics in df['topics']:
            if pd.isna(topics) or str(topics).strip() == '':
                cleaned_topics.append('')
                empty_count += 1
            else:
                # Clean topics: normalize spaces, remove extra commas
                topics_str = str(topics).strip()
                # Split by comma, clean each topic, and rejoin
                topic_list = [topic.strip() for topic in topics_str.split(',') if topic.strip()]
                cleaned_topics.append(', '.join(topic_list))
        
        df['topics'] = cleaned_topics
        
        if empty_count > 0:
            warnings.append(f"Found {empty_count} empty/missing topics")
        
        return df, warnings
    
    def _remove_invalid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows with critical missing data.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            DataFrame with invalid rows removed
        """
        # Remove rows without titles (critical field)
        if 'title' in df.columns:
            df = df.dropna(subset=['title'])
            df = df[df['title'].str.strip() != '']
        
        return df
    
    def get_normalization_stats(self, original_df: pd.DataFrame, normalized_df: pd.DataFrame) -> dict:
        """Get statistics about the normalization process.
        
        Args:
            original_df: Original DataFrame before normalization
            normalized_df: DataFrame after normalization
            
        Returns:
            Dictionary with normalization statistics
        """
        stats = {
            'original_rows': len(original_df),
            'normalized_rows': len(normalized_df),
            'rows_removed': len(original_df) - len(normalized_df),
            'columns_processed': []
        }
        
        # Check which columns were processed
        for col in ['frequency', 'acceptance_rate', 'difficulty', 'title', 'link', 'topics']:
            if col in normalized_df.columns:
                stats['columns_processed'].append(col)
        
        # Add column-specific stats
        if 'frequency' in normalized_df.columns:
            stats['frequency_stats'] = {
                'mean': float(normalized_df['frequency'].mean()),
                'median': float(normalized_df['frequency'].median()),
                'zero_values': int((normalized_df['frequency'] == 0.0).sum())
            }
        
        if 'acceptance_rate' in normalized_df.columns:
            stats['acceptance_rate_stats'] = {
                'mean': float(normalized_df['acceptance_rate'].mean()) if not normalized_df['acceptance_rate'].isna().all() else 0.0,
                'median': float(normalized_df['acceptance_rate'].median()) if not normalized_df['acceptance_rate'].isna().all() else 0.0,
                'missing_values': int(normalized_df['acceptance_rate'].isna().sum())
            }
        
        if 'difficulty' in normalized_df.columns:
            stats['difficulty_distribution'] = normalized_df['difficulty'].value_counts().to_dict()
        
        return stats