"""CSV loading system with robust error handling and parallel processing."""

import logging
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Union
from datetime import datetime
import chardet

from src.models.data_models import CSVFileInfo, ValidationResult


logger = logging.getLogger(__name__)


class CSVLoader:
    """Loads CSV files with robust error handling and parallel processing."""
    
    # Common encodings to try when loading CSV files
    ENCODINGS_TO_TRY = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    # Expected column names (case-insensitive)
    EXPECTED_COLUMNS = {
        'difficulty': ['difficulty', 'level'],
        'title': ['title', 'problem', 'problem_title', 'name'],
        'frequency': ['frequency', 'freq', 'count'],
        'acceptance_rate': ['acceptance_rate', 'acceptance rate', 'acceptance', 'accept_rate', 'rate'],
        'link': ['link', 'url', 'leetcode_link', 'problem_link'],
        'topics': ['topics', 'tags', 'categories', 'topic']
    }
    
    def __init__(self, max_workers: int = 4):
        """Initialize CSV loader.
        
        Args:
            max_workers: Maximum number of threads for parallel loading
        """
        self.max_workers = max_workers
    
    def load_csv_batch(self, file_infos: List[CSVFileInfo]) -> Tuple[pd.DataFrame, List[str]]:
        """Load multiple CSV files in parallel and combine into single DataFrame.
        
        Args:
            file_infos: List of CSV file information objects
            
        Returns:
            Tuple of (combined DataFrame, list of error messages)
        """
        if not file_infos:
            return pd.DataFrame(), []
        
        dataframes = []
        errors = []
        
        # Use ThreadPoolExecutor for parallel loading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all loading tasks
            future_to_file = {
                executor.submit(self._load_single_csv, file_info): file_info 
                for file_info in file_infos
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_info = future_to_file[future]
                try:
                    df, file_errors = future.result()
                    if df is not None and not df.empty:
                        dataframes.append(df)
                    if file_errors:
                        errors.extend(file_errors)
                except Exception as e:
                    error_msg = f"Unexpected error loading {file_info.file_path}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        # Combine all successfully loaded DataFrames
        if dataframes:
            try:
                combined_df = pd.concat(dataframes, ignore_index=True)
                logger.info(f"Successfully loaded {len(dataframes)} CSV files with {len(combined_df)} total rows")
                return combined_df, errors
            except Exception as e:
                error_msg = f"Error combining DataFrames: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                return pd.DataFrame(), errors
        else:
            logger.warning("No CSV files were successfully loaded")
            return pd.DataFrame(), errors
    
    def _load_single_csv(self, file_info: CSVFileInfo) -> Tuple[Optional[pd.DataFrame], List[str]]:
        """Load a single CSV file with error handling.
        
        Args:
            file_info: Information about the CSV file to load
            
        Returns:
            Tuple of (DataFrame or None, list of error messages)
        """
        errors = []
        file_path = Path(file_info.file_path)
        
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return None, [error_msg]
        
        # Try different encodings
        for encoding in self.ENCODINGS_TO_TRY:
            try:
                df = self._read_csv_with_encoding(file_path, encoding)
                if df is not None:
                    # Add metadata columns
                    df['company'] = file_info.company
                    df['timeframe'] = file_info.timeframe.value
                    df['source_file'] = str(file_path)
                    df['last_updated'] = file_info.last_modified
                    
                    logger.debug(f"Successfully loaded {file_path} with encoding {encoding}")
                    return df, errors
            except Exception as e:
                logger.debug(f"Failed to load {file_path} with encoding {encoding}: {str(e)}")
                continue
        
        # If all encodings failed, try to detect encoding
        try:
            detected_encoding = self._detect_encoding(file_path)
            if detected_encoding and detected_encoding not in self.ENCODINGS_TO_TRY:
                df = self._read_csv_with_encoding(file_path, detected_encoding)
                if df is not None:
                    df['company'] = file_info.company
                    df['timeframe'] = file_info.timeframe.value
                    df['source_file'] = str(file_path)
                    df['last_updated'] = file_info.last_modified
                    
                    logger.info(f"Successfully loaded {file_path} with detected encoding {detected_encoding}")
                    return df, errors
        except Exception as e:
            logger.debug(f"Encoding detection failed for {file_path}: {str(e)}")
        
        error_msg = f"Failed to load CSV file with any encoding: {file_path}"
        logger.error(error_msg)
        return None, [error_msg]
    
    def _read_csv_with_encoding(self, file_path: Path, encoding: str) -> Optional[pd.DataFrame]:
        """Read CSV file with specific encoding and handle common issues.
        
        Args:
            file_path: Path to the CSV file
            encoding: Encoding to use
            
        Returns:
            DataFrame if successful, None otherwise
        """
        try:
            # Read CSV with various options to handle malformed data
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                on_bad_lines='skip',  # Skip bad lines instead of failing
                dtype=str,  # Read everything as string initially
                na_values=['', 'N/A', 'NULL', 'null', 'None'],
                keep_default_na=True
            )
            
            # Check if DataFrame is empty
            if df.empty:
                logger.warning(f"CSV file is empty: {file_path}")
                return None
            
            # Normalize column names and map to expected columns
            df = self._normalize_columns(df, file_path)
            
            return df
            
        except pd.errors.EmptyDataError:
            logger.warning(f"CSV file is empty: {file_path}")
            return None
        except pd.errors.ParserError as e:
            logger.error(f"Parser error reading {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading {file_path} with encoding {encoding}: {str(e)}")
            return None
    
    def _normalize_columns(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        """Normalize column names to standard format.
        
        Args:
            df: Input DataFrame
            file_path: Path to the source file (for logging)
            
        Returns:
            DataFrame with normalized column names
        """
        # Create a mapping from current columns to standard names
        column_mapping = {}
        original_columns = [col.lower().strip() for col in df.columns]
        
        for standard_name, possible_names in self.EXPECTED_COLUMNS.items():
            for col in df.columns:
                col_lower = col.lower().strip()
                if col_lower in [name.lower() for name in possible_names]:
                    column_mapping[col] = standard_name
                    break
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Log missing columns
        missing_columns = set(self.EXPECTED_COLUMNS.keys()) - set(df.columns)
        if missing_columns:
            logger.warning(f"Missing columns in {file_path}: {missing_columns}")
        
        return df
    
    def _detect_encoding(self, file_path: Path) -> Optional[str]:
        """Detect file encoding using chardet.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected encoding or None
        """
        try:
            with open(file_path, 'rb') as f:
                # Read first 10KB for encoding detection
                raw_data = f.read(10240)
                result = chardet.detect(raw_data)
                if result and result['confidence'] > 0.7:
                    return result['encoding']
        except Exception as e:
            logger.debug(f"Encoding detection failed for {file_path}: {str(e)}")
        
        return None
    
    def validate_csv_structure(self, df: pd.DataFrame) -> ValidationResult:
        """Validate the structure and content of a loaded DataFrame.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        processed_rows = len(df)
        skipped_rows = 0
        
        # Check for required columns
        required_columns = ['title', 'difficulty']  # Minimum required
        missing_required = [col for col in required_columns if col not in df.columns]
        if missing_required:
            errors.append(f"Missing required columns: {missing_required}")
        
        # Check for empty title column
        if 'title' in df.columns:
            empty_titles = df['title'].isna().sum()
            if empty_titles > 0:
                warnings.append(f"Found {empty_titles} rows with empty titles")
        
        # Validate frequency column if present
        if 'frequency' in df.columns:
            try:
                # Try to convert to numeric
                numeric_freq = pd.to_numeric(df['frequency'], errors='coerce')
                invalid_freq = numeric_freq.isna().sum() - df['frequency'].isna().sum()
                if invalid_freq > 0:
                    warnings.append(f"Found {invalid_freq} rows with invalid frequency values")
            except Exception:
                warnings.append("Could not validate frequency column")
        
        # Validate acceptance_rate column if present
        if 'acceptance_rate' in df.columns:
            try:
                # Try to convert to numeric
                numeric_rate = pd.to_numeric(df['acceptance_rate'], errors='coerce')
                invalid_rate = numeric_rate.isna().sum() - df['acceptance_rate'].isna().sum()
                if invalid_rate > 0:
                    warnings.append(f"Found {invalid_rate} rows with invalid acceptance rate values")
            except Exception:
                warnings.append("Could not validate acceptance_rate column")
        
        # Check for duplicate titles within the same company/timeframe
        if all(col in df.columns for col in ['title', 'company', 'timeframe']):
            duplicates = df.duplicated(subset=['title', 'company', 'timeframe']).sum()
            if duplicates > 0:
                warnings.append(f"Found {duplicates} duplicate problem entries")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            processed_rows=processed_rows,
            skipped_rows=skipped_rows
        )
    
    def load_single_file(self, file_info: CSVFileInfo) -> Tuple[Optional[pd.DataFrame], ValidationResult]:
        """Load and validate a single CSV file.
        
        Args:
            file_info: Information about the CSV file to load
            
        Returns:
            Tuple of (DataFrame or None, ValidationResult)
        """
        df, errors = self._load_single_csv(file_info)
        
        if df is not None:
            validation_result = self.validate_csv_structure(df)
            # Add loading errors to validation result
            if errors:
                validation_result.errors.extend(errors)
                validation_result.is_valid = False
        else:
            validation_result = ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=[],
                processed_rows=0,
                skipped_rows=0
            )
        
        return df, validation_result
    
    def load_csv(self, file_input: Union[str, CSVFileInfo]) -> Optional[pd.DataFrame]:
        """Load a CSV file from a path or pre-built file info.

        Args:
            file_input: File path or CSVFileInfo describing the file

        Returns:
            DataFrame if successful, None otherwise
        """
        try:
            file_info: CSVFileInfo
            if isinstance(file_input, CSVFileInfo):
                file_info = file_input
            else:
                from src.models.data_models import Timeframe
                import os

                file_path = str(file_input)
                path_obj = Path(file_path)

                # Derive basic metadata; fall back to safe defaults if parsing fails
                company = path_obj.parent.name if path_obj.parent.name else "unknown"
                timeframe = Timeframe.ALL

                file_info = CSVFileInfo(
                    file_path=file_path,
                    company=company,
                    timeframe=timeframe,
                    last_modified=datetime.fromtimestamp(os.path.getmtime(file_path)) if os.path.exists(file_path) else datetime.now()
                )

            df, _ = self._load_single_csv(file_info)
            return df

        except Exception as e:
            file_path = getattr(file_input, "file_path", file_input)
            logger.error(f"Error in load_csv for {file_path}: {e}")
            return None
