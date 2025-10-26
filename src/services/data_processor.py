"""Main data processing orchestrator that combines normalization, enrichment, and topic explosion."""

import logging
import pandas as pd
from typing import Tuple, List, Optional, Dict, Any

from src.models.data_models import CSVFileInfo, ValidationResult
from src.services.data_normalizer import DataNormalizer
from src.services.metadata_enricher import MetadataEnricher
from src.services.topic_exploder import TopicExploder


logger = logging.getLogger(__name__)


class DataProcessor:
    """Main data processing orchestrator that combines all processing steps."""
    
    def __init__(self, standardize_topics: bool = True):
        """Initialize the data processor.
        
        Args:
            standardize_topics: Whether to standardize topic names during processing
        """
        self.normalizer = DataNormalizer()
        self.enricher = MetadataEnricher()
        self.exploder = TopicExploder(standardize_topics=standardize_topics)
    
    def process_dataframe(self, df: pd.DataFrame, file_info: CSVFileInfo, 
                         create_exploded_view: bool = True) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], ValidationResult]:
        """Process a single DataFrame through all processing steps.
        
        Args:
            df: Input DataFrame to process
            file_info: Information about the source CSV file
            create_exploded_view: Whether to create an exploded topics view
            
        Returns:
            Tuple of (processed DataFrame, exploded DataFrame or None, validation result)
        """
        if df.empty:
            return df, None, ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["DataFrame is empty"],
                processed_rows=0,
                skipped_rows=0
            )
        
        logger.info(f"Processing DataFrame from {file_info.file_path} with {len(df)} rows")
        
        all_errors = []
        all_warnings = []
        
        try:
            # Step 1: Normalize data
            normalized_df, norm_result = self.normalizer.normalize_data(df)
            all_errors.extend(norm_result.errors)
            all_warnings.extend(norm_result.warnings)
            
            if not norm_result.is_valid:
                logger.error(f"Normalization failed for {file_info.file_path}")
                return df, None, norm_result
            
            # Step 2: Enrich with metadata
            enriched_df, enrich_result = self.enricher.enrich_dataframe(normalized_df, file_info)
            all_errors.extend(enrich_result.errors)
            all_warnings.extend(enrich_result.warnings)
            
            if not enrich_result.is_valid:
                logger.error(f"Metadata enrichment failed for {file_info.file_path}")
                return normalized_df, None, ValidationResult(
                    is_valid=False,
                    errors=all_errors,
                    warnings=all_warnings,
                    processed_rows=len(normalized_df),
                    skipped_rows=0
                )
            
            # Step 3: Create topic views if requested
            exploded_df = None
            if create_exploded_view and 'topics' in enriched_df.columns:
                # Create both views
                final_df, exploded_df, explosion_result = self.exploder.create_both_views(enriched_df)
                all_errors.extend(explosion_result.errors)
                all_warnings.extend(explosion_result.warnings)
                
                if explosion_result.is_valid:
                    enriched_df = final_df  # Use the cleaned non-exploded version
                else:
                    logger.warning(f"Topic explosion had issues for {file_info.file_path}")
            
            logger.info(f"Processing complete for {file_info.file_path}: {len(enriched_df)} main rows" + 
                       (f", {len(exploded_df)} exploded rows" if exploded_df is not None else ""))
            
        except Exception as e:
            error_msg = f"Unexpected error processing {file_info.file_path}: {str(e)}"
            logger.error(error_msg)
            all_errors.append(error_msg)
            return df, None, ValidationResult(
                is_valid=False,
                errors=all_errors,
                warnings=all_warnings,
                processed_rows=0,
                skipped_rows=0
            )
        
        final_result = ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            processed_rows=len(enriched_df),
            skipped_rows=len(df) - len(enriched_df) if len(enriched_df) < len(df) else 0
        )
        
        return enriched_df, exploded_df, final_result
    
    def process_batch(self, dataframes_with_info: List[Tuple[pd.DataFrame, CSVFileInfo]], 
                     create_exploded_view: bool = True) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], ValidationResult]:
        """Process multiple DataFrames and combine them.
        
        Args:
            dataframes_with_info: List of tuples (DataFrame, CSVFileInfo)
            create_exploded_view: Whether to create an exploded topics view
            
        Returns:
            Tuple of (combined processed DataFrame, combined exploded DataFrame or None, validation result)
        """
        if not dataframes_with_info:
            return pd.DataFrame(), None, ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["No DataFrames to process"],
                processed_rows=0,
                skipped_rows=0
            )
        
        logger.info(f"Processing batch of {len(dataframes_with_info)} DataFrames")
        
        processed_dfs = []
        exploded_dfs = []
        all_errors = []
        all_warnings = []
        total_processed = 0
        total_skipped = 0
        
        for df, file_info in dataframes_with_info:
            try:
                processed_df, exploded_df, result = self.process_dataframe(
                    df, file_info, create_exploded_view
                )
                
                if result.is_valid and not processed_df.empty:
                    processed_dfs.append(processed_df)
                    if exploded_df is not None and not exploded_df.empty:
                        exploded_dfs.append(exploded_df)
                
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)
                total_processed += result.processed_rows
                total_skipped += result.skipped_rows
                
            except Exception as e:
                error_msg = f"Failed to process DataFrame from {file_info.file_path}: {str(e)}"
                logger.error(error_msg)
                all_errors.append(error_msg)
        
        # Combine all processed DataFrames
        combined_df = pd.DataFrame()
        combined_exploded_df = None
        
        if processed_dfs:
            try:
                combined_df = pd.concat(processed_dfs, ignore_index=True)
                logger.info(f"Combined {len(processed_dfs)} processed DataFrames into {len(combined_df)} total rows")
            except Exception as e:
                error_msg = f"Error combining processed DataFrames: {str(e)}"
                logger.error(error_msg)
                all_errors.append(error_msg)
        
        if exploded_dfs:
            try:
                combined_exploded_df = pd.concat(exploded_dfs, ignore_index=True)
                logger.info(f"Combined {len(exploded_dfs)} exploded DataFrames into {len(combined_exploded_df)} total rows")
            except Exception as e:
                error_msg = f"Error combining exploded DataFrames: {str(e)}"
                logger.error(error_msg)
                all_errors.append(error_msg)
                combined_exploded_df = None
        
        final_result = ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            processed_rows=total_processed,
            skipped_rows=total_skipped
        )
        
        return combined_df, combined_exploded_df, final_result
    
    def get_processing_summary(self, processed_df: pd.DataFrame, 
                             exploded_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Get a summary of the processing results.
        
        Args:
            processed_df: Main processed DataFrame
            exploded_df: Optional exploded DataFrame
            
        Returns:
            Dictionary with processing summary
        """
        summary = {
            'main_dataset': {
                'total_rows': len(processed_df),
                'total_columns': len(processed_df.columns) if not processed_df.empty else 0
            }
        }
        
        if not processed_df.empty:
            # Add metadata summary
            summary['main_dataset'].update(self.enricher.get_metadata_summary(processed_df))
            
            # Add normalization stats if available
            if 'frequency' in processed_df.columns:
                summary['normalization'] = {
                    'frequency_stats': {
                        'mean': float(processed_df['frequency'].mean()),
                        'median': float(processed_df['frequency'].median()),
                        'zero_values': int((processed_df['frequency'] == 0.0).sum())
                    }
                }
            
            # Add topic stats
            if 'topics' in processed_df.columns:
                summary['topics'] = self.exploder.get_topic_statistics(processed_df)
        
        if exploded_df is not None and not exploded_df.empty:
            summary['exploded_dataset'] = {
                'total_rows': len(exploded_df),
                'total_columns': len(exploded_df.columns),
                'topics': self.exploder.get_topic_statistics(exploded_df)
            }
        
        return summary
    
    def process_csv_data(self, df: pd.DataFrame, file_info: CSVFileInfo) -> Optional[pd.DataFrame]:
        """Wrapper method for DatasetManager compatibility.
        
        Args:
            df: Raw DataFrame from CSV
            file_info: CSV file information
            
        Returns:
            Processed DataFrame or None if processing failed
        """
        try:
            processed_df, _, result = self.process_dataframe(df, file_info, create_exploded_view=False)
            
            if result.is_valid:
                return processed_df
            else:
                logger.error(f"Processing failed for {file_info.file_path}: {result.errors}")
                return None
                
        except Exception as e:
            logger.error(f"Error in process_csv_data for {file_info.file_path}: {e}")
            return None
    
    def explode_topics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Wrapper method to explode topics for DatasetManager compatibility.
        
        Args:
            df: DataFrame with topics to explode
            
        Returns:
            DataFrame with exploded topics
        """
        try:
            if 'topics' not in df.columns:
                logger.warning("No topics column found for explosion")
                return df
            
            _, exploded_df, result = self.exploder.create_both_views(df)
            
            if result.is_valid and exploded_df is not None:
                return exploded_df
            else:
                logger.warning(f"Topic explosion failed or returned no data: {result.errors}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error in explode_topics: {e}")
            return pd.DataFrame()