"""Metadata enrichment system for adding company and timeframe information."""

import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from src.models.data_models import CSVFileInfo, Timeframe, ValidationResult


logger = logging.getLogger(__name__)


class MetadataEnricher:
    """Enriches DataFrames with metadata extracted from file paths and other sources."""
    
    # Mapping from file patterns to timeframe enums
    TIMEFRAME_PATTERNS = {
        '1. thirty days': Timeframe.THIRTY_DAYS,
        '1. thirty days.csv': Timeframe.THIRTY_DAYS,
        '2. three months': Timeframe.THREE_MONTHS,
        '2. three months.csv': Timeframe.THREE_MONTHS,
        '3. six months': Timeframe.SIX_MONTHS,
        '3. six months.csv': Timeframe.SIX_MONTHS,
        '4. more than six months': Timeframe.MORE_THAN_SIX_MONTHS,
        '4. more than six months.csv': Timeframe.MORE_THAN_SIX_MONTHS,
        '5. all': Timeframe.ALL,
        '5. all.csv': Timeframe.ALL,
    }
    
    def __init__(self):
        """Initialize the metadata enricher."""
        pass
    
    def enrich_dataframe(self, df: pd.DataFrame, file_info: CSVFileInfo) -> Tuple[pd.DataFrame, ValidationResult]:
        """Add metadata columns to a DataFrame based on file information.
        
        Args:
            df: Input DataFrame to enrich
            file_info: Information about the source CSV file
            
        Returns:
            Tuple of (enriched DataFrame, validation result)
        """
        if df.empty:
            return df, ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["DataFrame is empty"],
                processed_rows=0,
                skipped_rows=0
            )
        
        logger.debug(f"Enriching DataFrame with metadata from {file_info.file_path}")
        
        # Create a copy to avoid modifying the original
        enriched_df = df.copy()
        errors = []
        warnings = []
        
        try:
            # Add basic metadata from file_info
            enriched_df['company'] = file_info.company
            enriched_df['timeframe'] = file_info.timeframe.value
            enriched_df['source_file'] = file_info.file_path
            enriched_df['last_updated'] = file_info.last_modified
            
            # Add derived metadata
            enriched_df = self._add_derived_metadata(enriched_df, file_info)
            
            # Validate metadata consistency
            validation_warnings = self._validate_metadata_consistency(enriched_df, file_info)
            warnings.extend(validation_warnings)
            
        except Exception as e:
            error_msg = f"Error during metadata enrichment: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        logger.debug(f"Metadata enrichment complete for {len(enriched_df)} rows")
        
        validation_result = ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            processed_rows=len(enriched_df),
            skipped_rows=0
        )
        
        return enriched_df, validation_result
    
    def enrich_batch(self, dataframes_with_info: list) -> Tuple[pd.DataFrame, ValidationResult]:
        """Enrich multiple DataFrames and combine them.
        
        Args:
            dataframes_with_info: List of tuples (DataFrame, CSVFileInfo)
            
        Returns:
            Tuple of (combined enriched DataFrame, validation result)
        """
        if not dataframes_with_info:
            return pd.DataFrame(), ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["No DataFrames to process"],
                processed_rows=0,
                skipped_rows=0
            )
        
        enriched_dataframes = []
        all_errors = []
        all_warnings = []
        total_processed = 0
        total_skipped = 0
        
        for df, file_info in dataframes_with_info:
            try:
                enriched_df, validation_result = self.enrich_dataframe(df, file_info)
                
                if not enriched_df.empty:
                    enriched_dataframes.append(enriched_df)
                
                all_errors.extend(validation_result.errors)
                all_warnings.extend(validation_result.warnings)
                total_processed += validation_result.processed_rows
                total_skipped += validation_result.skipped_rows
                
            except Exception as e:
                error_msg = f"Failed to enrich DataFrame from {file_info.file_path}: {str(e)}"
                logger.error(error_msg)
                all_errors.append(error_msg)
        
        # Combine all enriched DataFrames
        if enriched_dataframes:
            try:
                combined_df = pd.concat(enriched_dataframes, ignore_index=True)
                logger.info(f"Combined {len(enriched_dataframes)} enriched DataFrames into {len(combined_df)} total rows")
            except Exception as e:
                error_msg = f"Error combining enriched DataFrames: {str(e)}"
                logger.error(error_msg)
                all_errors.append(error_msg)
                combined_df = pd.DataFrame()
        else:
            combined_df = pd.DataFrame()
            all_warnings.append("No DataFrames were successfully enriched")
        
        validation_result = ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            processed_rows=total_processed,
            skipped_rows=total_skipped
        )
        
        return combined_df, validation_result
    
    def extract_metadata_from_path(self, file_path: str) -> Tuple[str, Timeframe]:
        """Extract company name and timeframe from file path.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Tuple of (company name, timeframe)
        """
        path = Path(file_path)
        
        # Extract company name from parent directory
        company = path.parent.name
        
        # Extract timeframe from filename
        filename_lower = path.name.lower()
        timeframe = Timeframe.ALL  # Default fallback
        
        for pattern, tf in self.TIMEFRAME_PATTERNS.items():
            if pattern in filename_lower:
                timeframe = tf
                break
        
        return company, timeframe
    
    def _add_derived_metadata(self, df: pd.DataFrame, file_info: CSVFileInfo) -> pd.DataFrame:
        """Add derived metadata columns.
        
        Args:
            df: DataFrame to enrich
            file_info: Source file information
            
        Returns:
            DataFrame with additional metadata columns
        """
        # Add file size and modification time info
        try:
            file_path = Path(file_info.file_path)
            if file_path.exists():
                df['file_size_bytes'] = file_path.stat().st_size
            else:
                df['file_size_bytes'] = None
        except Exception as e:
            logger.debug(f"Could not get file size for {file_info.file_path}: {str(e)}")
            df['file_size_bytes'] = None
        
        # Add timeframe category for easier filtering
        df['timeframe_category'] = self._get_timeframe_category(file_info.timeframe)
        
        # Add company category (could be extended with company classification)
        df['company_category'] = self._get_company_category(file_info.company)
        
        # Add data freshness indicator
        df['data_age_days'] = self._calculate_data_age_days(file_info.last_modified)
        
        return df
    
    def _get_timeframe_category(self, timeframe: Timeframe) -> str:
        """Get a broader category for the timeframe.
        
        Args:
            timeframe: Timeframe enum value
            
        Returns:
            Timeframe category string
        """
        if timeframe == Timeframe.THIRTY_DAYS:
            return 'recent'
        elif timeframe in [Timeframe.THREE_MONTHS, Timeframe.SIX_MONTHS]:
            return 'medium_term'
        elif timeframe == Timeframe.MORE_THAN_SIX_MONTHS:
            return 'long_term'
        else:  # ALL
            return 'comprehensive'
    
    def _get_company_category(self, company: str) -> str:
        """Get a category for the company (can be extended with more sophisticated classification).
        
        Args:
            company: Company name
            
        Returns:
            Company category string
        """
        # This is a basic implementation - could be extended with more sophisticated
        # company classification based on industry, size, etc.
        company_lower = company.lower()
        
        # FAANG companies
        faang = ['google', 'apple', 'facebook', 'meta', 'amazon', 'netflix']
        if any(f in company_lower for f in faang):
            return 'faang'
        
        # Major tech companies
        major_tech = ['microsoft', 'uber', 'airbnb', 'spotify', 'twitter', 'x', 'linkedin', 
                     'salesforce', 'oracle', 'adobe', 'nvidia', 'intel', 'cisco']
        if any(tech in company_lower for tech in major_tech):
            return 'major_tech'
        
        # Financial services
        financial = ['goldman sachs', 'morgan stanley', 'jpmorgan', 'j.p. morgan', 'blackrock',
                    'citadel', 'two sigma', 'jane street', 'bridgewater']
        if any(fin in company_lower for fin in financial):
            return 'financial'
        
        # Consulting
        consulting = ['mckinsey', 'deloitte', 'accenture', 'pwc']
        if any(cons in company_lower for cons in consulting):
            return 'consulting'
        
        # Default category
        return 'other'
    
    def _calculate_data_age_days(self, last_modified: datetime) -> int:
        """Calculate how many days old the data is.
        
        Args:
            last_modified: Last modification timestamp
            
        Returns:
            Number of days since last modification
        """
        try:
            now = datetime.now()
            if last_modified.tzinfo is not None:
                # If last_modified has timezone info, make now timezone-aware
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            
            delta = now - last_modified
            return delta.days
        except Exception as e:
            logger.debug(f"Could not calculate data age: {str(e)}")
            return 0
    
    def _validate_metadata_consistency(self, df: pd.DataFrame, file_info: CSVFileInfo) -> list:
        """Validate that metadata is consistent across the DataFrame.
        
        Args:
            df: DataFrame with metadata
            file_info: Original file information
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check that all rows have the same company
        if 'company' in df.columns:
            unique_companies = df['company'].nunique()
            if unique_companies > 1:
                warnings.append(f"Found {unique_companies} different companies in single file")
        
        # Check that all rows have the same timeframe
        if 'timeframe' in df.columns:
            unique_timeframes = df['timeframe'].nunique()
            if unique_timeframes > 1:
                warnings.append(f"Found {unique_timeframes} different timeframes in single file")
        
        # Check that source_file is consistent
        if 'source_file' in df.columns:
            unique_files = df['source_file'].nunique()
            if unique_files > 1:
                warnings.append(f"Found {unique_files} different source files in single DataFrame")
        
        return warnings
    
    def get_metadata_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get a summary of metadata in the DataFrame.
        
        Args:
            df: DataFrame with metadata
            
        Returns:
            Dictionary with metadata summary
        """
        summary = {}
        
        if df.empty:
            return {'total_rows': 0, 'message': 'DataFrame is empty'}
        
        summary['total_rows'] = len(df)
        
        # Company distribution
        if 'company' in df.columns:
            summary['companies'] = {
                'unique_count': df['company'].nunique(),
                'top_companies': df['company'].value_counts().head(10).to_dict()
            }
        
        # Timeframe distribution
        if 'timeframe' in df.columns:
            summary['timeframes'] = df['timeframe'].value_counts().to_dict()
        
        # Company category distribution
        if 'company_category' in df.columns:
            summary['company_categories'] = df['company_category'].value_counts().to_dict()
        
        # Timeframe category distribution
        if 'timeframe_category' in df.columns:
            summary['timeframe_categories'] = df['timeframe_category'].value_counts().to_dict()
        
        # Data freshness
        if 'data_age_days' in df.columns:
            summary['data_freshness'] = {
                'avg_age_days': float(df['data_age_days'].mean()),
                'oldest_data_days': int(df['data_age_days'].max()),
                'newest_data_days': int(df['data_age_days'].min())
            }
        
        # Source file count
        if 'source_file' in df.columns:
            summary['source_files'] = {
                'unique_count': df['source_file'].nunique(),
                'files': df['source_file'].unique().tolist()
            }
        
        return summary
    
    def create_file_info_from_path(self, file_path: str, last_modified: Optional[datetime] = None) -> CSVFileInfo:
        """Create a CSVFileInfo object from a file path.
        
        Args:
            file_path: Path to the CSV file
            last_modified: Optional last modification time (will be detected if not provided)
            
        Returns:
            CSVFileInfo object
        """
        company, timeframe = self.extract_metadata_from_path(file_path)
        
        if last_modified is None:
            try:
                path = Path(file_path)
                if path.exists():
                    last_modified = datetime.fromtimestamp(path.stat().st_mtime)
                else:
                    last_modified = datetime.now()
            except Exception:
                last_modified = datetime.now()
        
        return CSVFileInfo(
            file_path=file_path,
            company=company,
            timeframe=timeframe,
            last_modified=last_modified
        )