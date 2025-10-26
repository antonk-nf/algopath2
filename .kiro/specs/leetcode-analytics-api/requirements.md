# Requirements Document

## Introduction

This feature will create a comprehensive LeetCode interview data analysis system that loads CSV data from 470+ company directories, processes it into a unified format, and exposes analytics capabilities through REST endpoints. The system will enable cross-company analysis, temporal trend tracking, topic clustering, and difficulty correlation analysis to help candidates optimize their interview preparation.

## Requirements

### Requirement 1

**User Story:** As a data analyst, I want to load and normalize CSV data from all company directories, so that I can perform consistent analysis across different companies and timeframes.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL scan all company directories and identify CSV files matching the five timeframe patterns (Thirty Days, Three Months, Six Months, More Than Six Months, All)
2. WHEN loading CSV files THEN the system SHALL normalize column names and data types (Frequency to numeric, Acceptance Rate to percentage, Topics as comma-separated strings)
3. WHEN processing each CSV THEN the system SHALL add metadata columns for company name and timeframe window extracted from file paths
4. WHEN data loading completes THEN the system SHALL validate that all expected columns are present and properly formatted
5. WHEN encountering malformed CSV data THEN the system SHALL log errors and continue processing other files

### Requirement 2

**User Story:** As a developer, I want the processed data to be cached in an efficient format, so that repeated analytics operations are fast and don't require re-reading hundreds of CSV files.

#### Acceptance Criteria

1. WHEN data processing completes THEN the system SHALL save the unified dataset in Parquet format for fast loading
2. WHEN the cache exists and is newer than source CSV files THEN the system SHALL load from cache instead of re-processing
3. WHEN source CSV files are modified THEN the system SHALL detect changes and invalidate the cache
4. WHEN caching data THEN the system SHALL preserve all original columns plus added metadata
5. IF database persistence is enabled THEN the system SHALL also store data in a SQL database with proper indexing

### Requirement 3

**User Story:** As a candidate preparing for interviews, I want to query the most frequently asked problems across companies, so that I can prioritize my study time on high-impact questions.

#### Acceptance Criteria

1. WHEN requesting cross-company leaderboards THEN the system SHALL aggregate frequency data across all companies for each problem
2. WHEN filtering by timeframe THEN the system SHALL allow querying specific windows (30 days, 3 months, etc.) or combinations
3. WHEN requesting top problems THEN the system SHALL return ranked lists with problem title, aggregated frequency, difficulty, and company count
4. WHEN querying by difficulty THEN the system SHALL support filtering results by Easy, Medium, or Hard problems
5. WHEN requesting problem details THEN the system SHALL include LeetCode links and acceptance rates

### Requirement 4

**User Story:** As a researcher, I want to analyze topic trends and correlations, so that I can understand which skill areas are emphasized by different companies or time periods.

#### Acceptance Criteria

1. WHEN processing topics data THEN the system SHALL explode comma-separated topics into individual records for analysis
2. WHEN requesting topic heatmaps THEN the system SHALL count topic occurrences across companies and timeframes
3. WHEN analyzing topic trends THEN the system SHALL support comparing topic frequency between different time windows
4. WHEN filtering by company type THEN the system SHALL allow grouping companies by categories (FAANG, fintech, startups, etc.)
5. WHEN correlating topics with difficulty THEN the system SHALL provide statistics on topic-difficulty distributions

### Requirement 5

**User Story:** As an API consumer, I want to access all analytics through REST endpoints, so that I can integrate the data into web applications, dashboards, or other tools.

#### Acceptance Criteria

1. WHEN the API server starts THEN it SHALL expose endpoints for all major analytics operations
2. WHEN requesting data THEN the API SHALL support pagination for large result sets
3. WHEN filtering data THEN the API SHALL accept query parameters for company, timeframe, difficulty, and topics
4. WHEN returning results THEN the API SHALL provide data in JSON format with consistent schema
5. WHEN handling errors THEN the API SHALL return appropriate HTTP status codes and error messages

### Requirement 6

**User Story:** As a system administrator, I want the system to be configurable and maintainable, so that I can deploy it in different environments and monitor its performance.

#### Acceptance Criteria

1. WHEN deploying the system THEN it SHALL support configuration via environment variables or config files
2. WHEN running in production THEN the system SHALL provide health check endpoints and logging
3. WHEN processing large datasets THEN the system SHALL handle memory efficiently and provide progress indicators
4. WHEN errors occur THEN the system SHALL log detailed error information for debugging
5. IF using Docker THEN the system SHALL include containerization with proper resource limits