# LeetCode Analytics API CLI

This CLI provides comprehensive data loading, processing, validation, and monitoring capabilities for the LeetCode Analytics API.

## Installation

Make sure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

## Usage

The CLI is accessible through the `cli.py` script:

```bash
python cli.py --help
```

## Data Commands

### Load Data

Load and process CSV data from company directories:

```bash
# Basic loading
python cli.py data load

# Load with specific root path
python cli.py data load -r /path/to/csv/files

# Force refresh cache
python cli.py data load --force

# Load with detailed output
python cli.py data load -o detailed

# Load with custom parallel workers
python cli.py data load -w 8
```

### Refresh All Datasets

Refresh all cached datasets (unified, exploded, and statistics):

```bash
# Refresh all datasets
python cli.py data refresh

# Force refresh all datasets
python cli.py data refresh --force
```

### Validate Data

Validate data integrity and report quality issues:

```bash
# Basic validation
python cli.py data validate

# Validate specific company
python cli.py data validate -c "Google"

# Validate with link checking (slower)
python cli.py data validate --check-links

# Get validation results in JSON format
python cli.py data validate -o json
```

### Generate Reports

Generate comprehensive data quality and statistics reports:

```bash
# Basic report
python cli.py data report

# Report without topic analysis (faster)
python cli.py data report --no-include-topics

# Report with top 20 items
python cli.py data report --top-n 20

# JSON format report
python cli.py data report -o json
```

### Process Selective Data

Process specific company or timeframe data:

```bash
# Process specific company
python cli.py data process -c "Amazon"

# Process specific timeframe
python cli.py data process -t "30d"

# Process with JSON output
python cli.py data process -c "Google" -o json
```

### Export Data

Export processed datasets to various formats:

```bash
# Export unified dataset to CSV
python cli.py data export -f output.csv

# Export exploded dataset to JSON
python cli.py data export -f output.json -d exploded

# Export company statistics to Parquet
python cli.py data export -f stats.parquet -d company_stats

# Export filtered data
python cli.py data export -f google_data.csv -c "Google"
python cli.py data export -f recent_data.csv -t "30d"

# Force refresh before export
python cli.py data export -f fresh_data.csv --force-refresh
```

### Check Status

Show data loading status and cache information:

```bash
# Show status in table format
python cli.py data status

# Show status in JSON format
python cli.py data status -o json
```

### Clear Cache

Clear all cached datasets:

```bash
python cli.py data clear-cache
```

## Monitoring Commands

### Health Check

Run health checks and display results:

```bash
# Basic health check
python cli.py monitoring health-check

# Health check in JSON format
python cli.py monitoring health-check --format json
```

### System Information

Display system information and resource usage:

```bash
# System info summary
python cli.py monitoring system-info

# System info in JSON format
python cli.py monitoring system-info --format json
```

### Metrics

Display collected metrics:

```bash
# All metrics
python cli.py monitoring metrics

# Specific category
python cli.py monitoring metrics -c api
python cli.py monitoring metrics -c processing
python cli.py monitoring metrics -c cache
```

### Log Analysis

Analyze log files for patterns and issues:

```bash
# Analyze last 7 days
python cli.py monitoring log-analysis

# Analyze last 30 days
python cli.py monitoring log-analysis -d 30

# Filter by log level
python cli.py monitoring log-analysis -l ERROR
```

## Environment Configuration

You can specify different environments:

```bash
# Development environment (default)
python cli.py data load -e development

# Production environment
python cli.py data load -e production

# Test environment
python cli.py data load -e test
```

## Output Formats

Most commands support multiple output formats:

- `summary`: Human-readable summary (default for most commands)
- `detailed`: Detailed human-readable output
- `json`: Machine-readable JSON format
- `table`: Tabular format (where applicable)

## Examples

### Complete Data Processing Workflow

```bash
# 1. Load data
python cli.py data load -o detailed

# 2. Validate data quality
python cli.py data validate -o detailed

# 3. Generate comprehensive report
python cli.py data report -o detailed

# 4. Export processed data
python cli.py data export -f processed_data.csv

# 5. Check system health
python cli.py monitoring health-check
```

### Data Quality Assessment

```bash
# Validate all data with comprehensive checks
python cli.py data validate --check-duplicates --check-links -o detailed

# Generate quality report
python cli.py data report --include-topics -o detailed

# Check specific company data quality
python cli.py data validate -c "Microsoft" -o detailed
```

### Performance Monitoring

```bash
# Check system resources
python cli.py monitoring system-info

# View metrics
python cli.py monitoring metrics -c all

# Analyze recent logs for errors
python cli.py monitoring log-analysis -l ERROR -d 1
```

## Error Handling

The CLI provides comprehensive error handling and will:

- Display helpful error messages
- Exit with appropriate error codes
- Log detailed error information
- Suggest corrective actions when possible

For debugging, you can set the environment to development mode:

```bash
python cli.py data load -e development
```

This will provide more detailed logging and error information.