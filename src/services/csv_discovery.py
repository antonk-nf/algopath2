"""CSV file discovery system for LeetCode analytics data."""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from src.models.data_models import CSVFileInfo, Timeframe


logger = logging.getLogger(__name__)


class CSVDiscovery:
    """Discovers and catalogs CSV files from company directories."""
    
    # Mapping of file patterns to timeframe enums
    TIMEFRAME_PATTERNS = {
        r"1\.\s*Thirty\s*Days\.csv$": Timeframe.THIRTY_DAYS,
        r"2\.\s*Three\s*Months\.csv$": Timeframe.THREE_MONTHS,
        r"3\.\s*Six\s*Months\.csv$": Timeframe.SIX_MONTHS,
        r"4\.\s*More\s*Than\s*Six\s*Months\.csv$": Timeframe.MORE_THAN_SIX_MONTHS,
        r"5\.\s*All\.csv$": Timeframe.ALL,
    }
    
    def __init__(self, root_directory: str):
        """Initialize CSV discovery with root directory path.
        
        Args:
            root_directory: Path to the root directory containing company folders
        """
        self.root_directory = Path(root_directory)
        if not self.root_directory.exists():
            raise ValueError(f"Root directory does not exist: {root_directory}")
        self._empty_file_report: List[Dict[str, str]] = []
    
    def discover_csv_files(self) -> List[CSVFileInfo]:
        """Scan company directories and identify valid CSV files.
        
        Returns:
            List of CSVFileInfo objects for discovered CSV files
        """
        self._empty_file_report = []
        csv_files = []
        
        # Iterate through all subdirectories (company folders)
        for company_dir in self.root_directory.iterdir():
            if not company_dir.is_dir():
                continue
                
            # Skip hidden directories and special directories
            if company_dir.name.startswith('.'):
                continue
                
            company_name = company_dir.name
            company_csv_files = self._discover_company_csv_files(company_dir, company_name)
            csv_files.extend(company_csv_files)
        
        return csv_files
    
    def _discover_company_csv_files(self, company_dir: Path, company_name: str) -> List[CSVFileInfo]:
        """Discover CSV files within a specific company directory.
        
        Args:
            company_dir: Path to the company directory
            company_name: Name of the company
            
        Returns:
            List of CSVFileInfo objects for the company's CSV files
        """
        csv_files = []
        
        # Look for CSV files in the company directory
        for file_path in company_dir.iterdir():
            if not file_path.is_file() or not file_path.suffix.lower() == '.csv':
                continue

            # Try to match the file name to a timeframe pattern
            timeframe = self._extract_timeframe_from_filename(file_path.name)
            if timeframe is None:
                # Log warning for unrecognized CSV files but don't fail
                continue

            # Skip zero-byte files and record for reporting
            try:
                file_size = file_path.stat().st_size
            except OSError:
                file_size = -1

            if file_size == 0:
                logger_name = f"{company_name}:{timeframe.value}"
                self._empty_file_report.append({
                    'company': company_name,
                    'timeframe': timeframe.value,
                    'file_path': str(file_path),
                    'reason': 'zero_bytes'
                })
                logger.warning(f"Skipping empty CSV file ({logger_name}) at {file_path}")
                continue

            # Get file modification time
            try:
                last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            except OSError:
                # If we can't get modification time, use current time
                last_modified = datetime.now()
            
            csv_file_info = CSVFileInfo(
                file_path=str(file_path),
                company=company_name,
                timeframe=timeframe,
                last_modified=last_modified
            )
            csv_files.append(csv_file_info)
        
        return csv_files

    @property
    def empty_file_report(self) -> List[Dict[str, str]]:
        """Get report of zero-byte CSV files discovered."""
        return list(self._empty_file_report)
    
    def _extract_timeframe_from_filename(self, filename: str) -> Optional[Timeframe]:
        """Extract timeframe from CSV filename using pattern matching.
        
        Args:
            filename: Name of the CSV file
            
        Returns:
            Timeframe enum if pattern matches, None otherwise
        """
        for pattern, timeframe in self.TIMEFRAME_PATTERNS.items():
            if re.search(pattern, filename, re.IGNORECASE):
                return timeframe
        
        return None
    
    def get_company_names(self) -> List[str]:
        """Get list of all company names found in the root directory.
        
        Returns:
            List of company names (directory names)
        """
        companies = []
        
        for company_dir in self.root_directory.iterdir():
            if company_dir.is_dir() and not company_dir.name.startswith('.'):
                companies.append(company_dir.name)
        
        return sorted(companies)
    
    def get_csv_files_for_company(self, company_name: str) -> List[CSVFileInfo]:
        """Get CSV files for a specific company.
        
        Args:
            company_name: Name of the company
            
        Returns:
            List of CSVFileInfo objects for the company
        """
        company_dir = self.root_directory / company_name
        if not company_dir.exists() or not company_dir.is_dir():
            return []
        
        return self._discover_company_csv_files(company_dir, company_name)
    
    def validate_directory_structure(self) -> dict:
        """Validate the directory structure and report statistics.
        
        Returns:
            Dictionary with validation statistics
        """
        stats = {
            'total_companies': 0,
            'companies_with_csv': 0,
            'total_csv_files': 0,
            'files_by_timeframe': {tf.value: 0 for tf in Timeframe},
            'companies_missing_files': [],
            'unrecognized_files': []
        }
        
        for company_dir in self.root_directory.iterdir():
            if not company_dir.is_dir() or company_dir.name.startswith('.'):
                continue
                
            stats['total_companies'] += 1
            company_name = company_dir.name
            
            csv_files = self._discover_company_csv_files(company_dir, company_name)
            
            if csv_files:
                stats['companies_with_csv'] += 1
                stats['total_csv_files'] += len(csv_files)
                
                # Count files by timeframe
                for csv_file in csv_files:
                    stats['files_by_timeframe'][csv_file.timeframe.value] += 1
            else:
                stats['companies_missing_files'].append(company_name)
            
            # Check for unrecognized CSV files
            for file_path in company_dir.iterdir():
                if (file_path.is_file() and 
                    file_path.suffix.lower() == '.csv' and 
                    self._extract_timeframe_from_filename(file_path.name) is None):
                    stats['unrecognized_files'].append(str(file_path))
        
        return stats
