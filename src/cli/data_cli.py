"""CLI commands for data loading and processing operations."""

import asyncio
import json
import sys
import time
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterable

import click
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup

from src.config.settings import create_config
from src.services.csv_discovery import CSVDiscovery
from src.services.csv_loader import CSVLoader
from src.services.data_processor import DataProcessor
from src.services.cache_manager import CacheManager
from src.services.dataset_manager import DatasetManager

logger = logging.getLogger(__name__)

@click.group()
def data():
    """Data loading and processing commands."""
    pass


@data.command()
@click.option('--environment', '-e', default=None, help='Environment to use (development, production, test)')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--force', '-f', is_flag=True, help='Force refresh even if cache is valid')
@click.option('--parallel-workers', '-w', default=None, type=int, help='Number of parallel workers for loading')
@click.option('--progress/--no-progress', default=True, help='Show progress bars')
@click.option('--output', '-o', type=click.Choice(['json', 'summary', 'detailed']), default='summary', 
              help='Output format')
def load(environment: Optional[str], root_path: Optional[str], force: bool, 
         parallel_workers: Optional[int], progress: bool, output: str):
    """Load and process CSV data from company directories."""
    try:
        # Initialize configuration
        config = create_config(environment)
        
        # Use configured root path if not provided
        if root_path is None:
            root_path = config.get_config("DATA_ROOT_PATH", ".")
        
        # Validate root path exists
        root_path_obj = Path(root_path)
        if not root_path_obj.exists():
            click.echo(f"Error: Root path does not exist: {root_path}", err=True)
            sys.exit(1)
        
        if not root_path_obj.is_dir():
            click.echo(f"Error: Root path is not a directory: {root_path}", err=True)
            sys.exit(1)
        
        # Initialize services
        csv_discovery = CSVDiscovery(root_path)
        csv_loader = CSVLoader(max_workers=parallel_workers or config.get_config("PARALLEL_WORKERS", 4))
        data_processor = DataProcessor()
        cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
        dataset_manager = DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)
        
        start_time = time.time()
        
        # Progress tracking
        def progress_callback(current: int, total: int):
            if progress:
                # This will be handled by tqdm in dataset_manager
                pass
        
        click.echo(f"Loading data from: {root_path}")
        if force:
            click.echo("Force refresh enabled - ignoring cache")
        
        # Create unified dataset
        unified_df = dataset_manager.create_unified_dataset(
            root_path, 
            force_refresh=force,
            progress_callback=progress_callback if progress else None
        )
        
        if unified_df.empty:
            click.echo("No data was loaded. Check your CSV files and try again.", err=True)
            sys.exit(1)
        
        processing_time = time.time() - start_time
        
        # Generate output based on format
        if output == 'json':
            result = {
                'status': 'success',
                'processing_time_seconds': round(processing_time, 2),
                'total_records': len(unified_df),
                'companies': unified_df['company'].nunique(),
                'unique_problems': unified_df['title'].nunique(),
                'timeframes': unified_df['timeframe'].unique().tolist(),
                'cache_used': not force
            }
            click.echo(json.dumps(result, indent=2))
        
        elif output == 'detailed':
            click.echo("Data Loading Complete")
            click.echo("=" * 50)
            click.echo(f"Processing time: {processing_time:.2f} seconds")
            click.echo(f"Total records: {len(unified_df):,}")
            click.echo(f"Companies: {unified_df['company'].nunique()}")
            click.echo(f"Unique problems: {unified_df['title'].nunique()}")
            click.echo(f"Cache used: {'No (forced refresh)' if force else 'Yes'}")
            
            # Show company breakdown
            click.echo("\nCompany Breakdown:")
            company_counts = unified_df['company'].value_counts().head(10)
            for company, count in company_counts.items():
                click.echo(f"  {company}: {count:,} records")
            
            if len(unified_df['company'].unique()) > 10:
                click.echo(f"  ... and {len(unified_df['company'].unique()) - 10} more companies")
            
            # Show timeframe breakdown
            click.echo("\nTimeframe Breakdown:")
            timeframe_counts = unified_df['timeframe'].value_counts()
            for timeframe, count in timeframe_counts.items():
                click.echo(f"  {timeframe}: {count:,} records")
            
            # Show difficulty breakdown
            if 'difficulty' in unified_df.columns:
                click.echo("\nDifficulty Breakdown:")
                difficulty_counts = unified_df['difficulty'].value_counts()
                for difficulty, count in difficulty_counts.items():
                    click.echo(f"  {difficulty}: {count:,} records")
        
        else:  # summary
            click.echo(f"✅ Successfully loaded {len(unified_df):,} records from {unified_df['company'].nunique()} companies")
            click.echo(f"   Processing time: {processing_time:.2f} seconds")
            click.echo(f"   Unique problems: {unified_df['title'].nunique():,}")
            click.echo(f"   Cache: {'Refreshed' if force else 'Used'}")
        
    except Exception as e:
        click.echo(f"Error loading data: {e}", err=True)
        sys.exit(1)


@data.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--force', '-f', is_flag=True, help='Force refresh all datasets')
@click.option('--progress/--no-progress', default=True, help='Show progress bars')
def refresh(environment: Optional[str], root_path: Optional[str], force: bool, progress: bool):
    """Refresh all cached datasets (unified, exploded, and statistics)."""
    try:
        # Initialize configuration and services
        config = create_config(environment)
        
        if root_path is None:
            root_path = config.get_config("DATA_ROOT_PATH", ".")
        
        # Validate root path
        root_path_obj = Path(root_path)
        if not root_path_obj.exists():
            click.echo(f"Error: Root path does not exist: {root_path}", err=True)
            sys.exit(1)
        
        # Initialize services
        csv_discovery = CSVDiscovery(root_path)
        csv_loader = CSVLoader(max_workers=config.get_config("PARALLEL_WORKERS", 4))
        data_processor = DataProcessor()
        cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
        dataset_manager = DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)
        
        start_time = time.time()
        
        # Progress tracking
        current_stage = ""
        progress_bar = None
        stage_labels = {
            "unified": "Discovering CSV files",
            "exploded": "Building exploded dataset",
            "statistics": "Computing company statistics",
            "complete": "All stages complete"
        }

        def progress_callback(stage: str, current: int, total: int):
            nonlocal current_stage, progress_bar

            if not progress:
                return

            if stage != current_stage:
                # Close any active progress bar when leaving the stage
                if current_stage == "unified_processing" and progress_bar is not None:
                    progress_bar.close()
                    progress_bar = None

                current_stage = stage

                if stage not in {"unified_processing", "complete"}:
                    label = stage_labels.get(stage, stage.replace('_', ' ').title())
                    click.echo(label)

            if stage == "unified_processing":
                if progress_bar is None:
                    progress_bar = tqdm(total=total, desc="Processing CSV files", unit="file")
                progress_bar.n = current
                progress_bar.refresh()
            elif stage == "complete":
                if progress_bar is not None:
                    progress_bar.close()
                    progress_bar = None
                click.echo("Finished refreshing datasets.\n")
        

        click.echo(f"Refreshing all datasets from: {root_path}")
        logger.warn("lol")
        if force:
            click.echo("Force refresh enabled")

        # Refresh all datasets with logging silenced so only the progress bar is shown
        previous_disable_level = logging.root.manager.disable
        logging.disable(logging.CRITICAL)
        try:
            datasets = dataset_manager.refresh_all_datasets(
                root_path,
                progress_callback=progress_callback if progress else None
            )
        finally:
            logging.disable(previous_disable_level if previous_disable_level else logging.NOTSET)

        processing_time = time.time() - start_time
        
        # Show results
        click.echo(f"\n✅ All datasets refreshed successfully!")
        click.echo(f"   Processing time: {processing_time:.2f} seconds")
        click.echo(f"   Unified dataset: {len(datasets['unified']):,} records")
        click.echo(f"   Exploded dataset: {len(datasets['exploded']):,} records")
        click.echo(f"   Company statistics: {len(datasets['company_stats'])} companies")
        
    except Exception as e:
        click.echo(f"Error refreshing datasets: {e}", err=True)
        sys.exit(1)


@data.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--company', '-c', help='Process only specific company')
@click.option('--timeframe', '-t', type=click.Choice(['30d', '3m', '6m', '6m+', 'all']), 
              help='Process only specific timeframe')
@click.option('--force', '-f', is_flag=True, help='Force processing even if cache is valid')
@click.option('--output', '-o', type=click.Choice(['json', 'summary']), default='summary', 
              help='Output format')
def process(environment: Optional[str], root_path: Optional[str], company: Optional[str], 
           timeframe: Optional[str], force: bool, output: str):
    """Process specific company or timeframe data selectively."""
    try:
        # Initialize configuration and services
        config = create_config(environment)
        
        if root_path is None:
            root_path = config.get_config("DATA_ROOT_PATH", ".")
        
        # Initialize services
        csv_discovery = CSVDiscovery(root_path)
        csv_loader = CSVLoader(max_workers=config.get_config("PARALLEL_WORKERS", 4))
        data_processor = DataProcessor()
        
        # Discover CSV files
        all_csv_files = csv_discovery.discover_csv_files()
        
        # Filter files based on criteria
        filtered_files = all_csv_files
        
        if company:
            filtered_files = [f for f in filtered_files if f.company.lower() == company.lower()]
            if not filtered_files:
                click.echo(f"No CSV files found for company: {company}", err=True)
                sys.exit(1)
        
        if timeframe:
            # Map timeframe to enum value
            timeframe_map = {
                '30d': 'thirty_days',
                '3m': 'three_months', 
                '6m': 'six_months',
                '6m+': 'more_than_six_months',
                'all': 'all'
            }
            target_timeframe = timeframe_map.get(timeframe)
            filtered_files = [f for f in filtered_files if f.timeframe.value == target_timeframe]
            if not filtered_files:
                click.echo(f"No CSV files found for timeframe: {timeframe}", err=True)
                sys.exit(1)
        
        click.echo(f"Processing {len(filtered_files)} CSV files...")
        if company:
            click.echo(f"Company filter: {company}")
        if timeframe:
            click.echo(f"Timeframe filter: {timeframe}")
        
        start_time = time.time()
        
        # Load and process files
        combined_df, errors = csv_loader.load_csv_batch(filtered_files)
        
        if combined_df.empty:
            click.echo("No data was loaded from the selected files.", err=True)
            if errors:
                click.echo("Errors encountered:")
                for error in errors:
                    click.echo(f"  - {error}")
            sys.exit(1)
        
        processing_time = time.time() - start_time
        
        # Generate output
        if output == 'json':
            result = {
                'status': 'success',
                'processing_time_seconds': round(processing_time, 2),
                'files_processed': len(filtered_files),
                'total_records': len(combined_df),
                'companies': combined_df['company'].nunique(),
                'unique_problems': combined_df['title'].nunique(),
                'errors': errors
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"✅ Successfully processed {len(filtered_files)} files")
            click.echo(f"   Total records: {len(combined_df):,}")
            click.echo(f"   Companies: {combined_df['company'].nunique()}")
            click.echo(f"   Unique problems: {combined_df['title'].nunique()}")
            click.echo(f"   Processing time: {processing_time:.2f} seconds")
            
            if errors:
                click.echo(f"   Errors: {len(errors)}")
                if len(errors) <= 5:
                    for error in errors:
                        click.echo(f"     - {error}")
                else:
                    for error in errors[:3]:
                        click.echo(f"     - {error}")
                    click.echo(f"     ... and {len(errors) - 3} more errors")
        
    except Exception as e:
        click.echo(f"Error processing data: {e}", err=True)
        sys.exit(1)


def _extract_title_slug_from_link(link: str) -> Optional[str]:
    if not isinstance(link, str) or not link:
        return None
    match = re.search(r"/problems/([\w-]+)/?", link)
    if match:
        return match.group(1).strip()
    return None


def _collect_unique_slugs(dataset: pd.DataFrame) -> List[str]:
    slug_columns = [col for col in dataset.columns if col.lower() in {"title_slug", "titleslug", "slug"}]

    slugs: set[str] = set()
    if slug_columns:
        for col in slug_columns:
            series = dataset[col].dropna().astype(str).str.strip().str.lower()
            slugs.update(value for value in series if value)

    if 'link' in dataset.columns:
        for link in dataset['link'].dropna().astype(str):
            slug = _extract_title_slug_from_link(link)
            if slug:
                slugs.add(slug.lower())

    if not slugs and 'title' in dataset.columns:
        for title in dataset['title'].dropna().astype(str):
            candidate = re.sub(r"[^a-z0-9-]", "-", title.strip().lower())
            candidate = re.sub(r"-+", "-", candidate).strip('-')
            if candidate:
                slugs.add(candidate)

    return sorted(slugs)


def _normalize_columns(columns: Iterable[str]) -> List[str]:
    normalized = []
    seen: Dict[str, int] = {}
    for col in columns:
        clean = col.replace('question.', '')
        clean = clean.replace('[', '.').replace(']', '')
        clean = clean.replace('..', '.')
        clean = clean.strip('.').lower()
        clean = clean.replace('.', '_')
        clean = re.sub(r'[^a-z0-9_]', '_', clean)
        if not clean:
            clean = 'value'
        count = seen.get(clean, 0)
        if count:
            new_name = f"{clean}_{count}"
            seen[clean] = count + 1
            normalized.append(new_name)
        else:
            seen[clean] = 1
            normalized.append(clean)
    return normalized


def _jsonl_to_parquet(jsonl_path: Path, parquet_path: Path) -> int:
    records: List[Dict[str, Any]] = []
    with jsonl_path.open('r', encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))

    if not records:
        return 0

    df = pd.json_normalize(records)
    df.columns = _normalize_columns(df.columns)
    if 'fetched_at' in df.columns:
        df['fetched_at'] = pd.to_datetime(df['fetched_at'], errors='coerce')
    if 'title_slug' in df.columns:
        df['title_slug'] = df['title_slug'].astype(str).str.strip().str.lower()

    if 'content' in df.columns:
        df = df.rename(columns={'content': 'content_raw'})
        df['content_html'] = df['content_raw'].apply(_sanitize_html)
        df['content_text'] = df['content_html'].apply(_extract_plain_text)

    df.to_parquet(parquet_path, index=False)
    return len(df)


def _sanitize_html(html: Any) -> Optional[str]:
    if not isinstance(html, str) or not html.strip():
        return None
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
    for a_tag in soup.find_all('a'):
        a_tag['rel'] = 'noopener noreferrer'
        a_tag['target'] = '_blank'
    for img_tag in soup.find_all('img'):
        img_tag.attrs.pop('width', None)
        img_tag.attrs.pop('height', None)
        img_tag['loading'] = 'lazy'
    sanitized = soup.decode()
    return sanitized.strip()


def _extract_plain_text(html: Any) -> Optional[str]:
    if not isinstance(html, str) or not html.strip():
        return None
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text('\n')
    return text.strip()


@data.command('export-title-slugs')
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--output', '-o', default='leetcode_title_slugs.json', show_default=True,
              help='Output file to write the slug list to')
@click.option('--format', '-f', type=click.Choice(['json', 'text'], case_sensitive=False),
              default='json', show_default=True, help='Output format (JSON array or newline text)')
def export_title_slugs(environment: Optional[str], root_path: Optional[str], output: str, format: str):
    """Export unique LeetCode title slugs from the unified dataset."""

    try:
        config = create_config(environment)
        if root_path is None:
            root_path = config.get_config("DATA_ROOT_PATH", ".")

        csv_discovery = CSVDiscovery(root_path)
        csv_loader = CSVLoader(max_workers=config.get_config("PARALLEL_WORKERS", 4))
        data_processor = DataProcessor()
        cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
        dataset_manager = DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)

        dataset = dataset_manager.get_unified_dataset(root_path)
        if dataset is None or dataset.empty:
            click.echo('No data available in unified dataset. Run "python cli.py data refresh" first.', err=True)
            sys.exit(1)

        slugs = _collect_unique_slugs(dataset)
        if not slugs:
            click.echo('Could not identify any title slugs in the dataset.', err=True)
            sys.exit(1)

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == 'json':
            payload = {
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'count': len(slugs),
                'slugs': slugs,
            }
            output_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        else:
            output_path.write_text('\n'.join(slugs) + '\n', encoding='utf-8')

        click.echo(f"Exported {len(slugs)} unique title slugs to {output_path}")

    except Exception as exc:
        click.echo(f"Error exporting title slugs: {exc}", err=True)
        sys.exit(1)


@data.command('fetch-leetcode-metadata')
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--slugs-file', '-s', type=click.Path(exists=True, dir_okay=False),
              help='File containing title slugs (JSON array or newline-delimited). If omitted, slugs are read from the dataset.')
@click.option('--output', '-o', default='leetcode_metadata.jsonl', show_default=True,
              help='Output JSONL file for fetched metadata')
@click.option('--limit', '-l', type=int, help='Maximum number of slugs to process')
@click.option('--rate-limit', '-p', default=5, show_default=True, type=float,
              help='Maximum number of requests per second')
@click.option('--timeout', '-t', default=20, show_default=True, type=int,
              help='HTTP request timeout in seconds')
@click.option('--csrf-token', default=None, help='Optional CSRF token header value')
@click.option('--referer', default='https://leetcode.com', show_default=True, help='Referer header for requests')
def fetch_leetcode_metadata(environment: Optional[str], root_path: Optional[str], slugs_file: Optional[str],
                           output: str, limit: Optional[int], rate_limit: float, timeout: int,
                           csrf_token: Optional[str], referer: str):
    """Fetch enriched problem metadata from LeetCode GraphQL and store it locally."""

    try:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError('The "requests" library is required for this command. Install it via pip.') from exc

        if rate_limit <= 0:
            click.echo('Rate limit must be positive.', err=True)
            sys.exit(1)

        if slugs_file:
            path = Path(slugs_file)
            contents = path.read_text(encoding='utf-8')
            try:
                parsed = json.loads(contents)
                if isinstance(parsed, dict) and 'slugs' in parsed and isinstance(parsed['slugs'], list):
                    slugs = [str(s).strip() for s in parsed['slugs'] if str(s).strip()]
                elif isinstance(parsed, list):
                    slugs = [str(s).strip() for s in parsed if str(s).strip()]
                else:
                    raise ValueError
            except ValueError:
                slugs = [line.strip() for line in contents.splitlines() if line.strip()]
        else:
            config = create_config(environment)
            if root_path is None:
                root_path = config.get_config("DATA_ROOT_PATH", ".")

            csv_discovery = CSVDiscovery(root_path)
            csv_loader = CSVLoader(max_workers=config.get_config("PARALLEL_WORKERS", 4))
            data_processor = DataProcessor()
            cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
            dataset_manager = DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)

            dataset = dataset_manager.get_unified_dataset(root_path)
            if dataset is None or dataset.empty:
                click.echo('No data available in unified dataset. Run "python cli.py data refresh" first.', err=True)
                sys.exit(1)

            slugs = _collect_unique_slugs(dataset)

        if not slugs:
            click.echo('No title slugs available to fetch.', err=True)
            sys.exit(1)

        if limit is not None:
            slugs = slugs[:max(0, limit)]

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'Referer': referer,
        })
        if csrf_token:
            session.headers['X-CSRFToken'] = csrf_token
            session.headers['X-Requested-With'] = 'XMLHttpRequest'
            session.headers['Origin'] = referer
            session.cookies.set('csrftoken', csrf_token)

        query = (
            "query questionData($titleSlug:String!){question(titleSlug:$titleSlug){"
            "title titleSlug questionFrontendId difficulty likes dislikes acRate isPaidOnly "
            "content topicTags{name id slug} hasSolution hasVideoSolution freqBar}}"
        )

        delay = 1.0 / rate_limit
        fetched = 0
        failures = 0
        start_time = time.time()

        jsonl_path = output_path.with_suffix('.jsonl')
        parquet_path = output_path.with_suffix('.parquet')

        with jsonl_path.open('w', encoding='utf-8') as handle:
            for idx, slug in enumerate(slugs, start=1):
                if idx > 1:
                    elapsed = time.time() - start_time
                    expected_elapsed = (idx - 1) * delay
                    if expected_elapsed > elapsed:
                        time.sleep(expected_elapsed - elapsed)

                payload = {
                    'operationName': 'questionData',
                    'variables': {'titleSlug': slug},
                    'query': query,
                }

                try:
                    response = session.post('https://leetcode.com/graphql/', json=payload, timeout=timeout)
                except requests.RequestException as req_exc:
                    failures += 1
                    click.echo(f"[{idx}/{len(slugs)}] {slug} -> network error: {req_exc}", err=True)
                    continue

                if response.status_code != 200:
                    failures += 1
                    click.echo(f"[{idx}/{len(slugs)}] {slug} -> HTTP {response.status_code}", err=True)
                    continue

                try:
                    data = response.json()
                except ValueError as parse_exc:
                    failures += 1
                    click.echo(f"[{idx}/{len(slugs)}] {slug} -> invalid JSON: {parse_exc}", err=True)
                    continue

                if 'errors' in data:
                    failures += 1
                    click.echo(f"[{idx}/{len(slugs)}] {slug} -> GraphQL errors: {data['errors']}", err=True)
                    continue

                question = data.get('data', {}).get('question')
                if question is None:
                    failures += 1
                    click.echo(f"[{idx}/{len(slugs)}] {slug} -> no question data", err=True)
                    continue

                record = {
                    'titleSlug': slug,
                    'fetched_at': datetime.utcnow().isoformat() + 'Z',
                    'question': question,
                }
                handle.write(json.dumps(record) + '\n')
                fetched += 1

                if idx % 50 == 0 or idx == len(slugs):
                    click.echo(f"Processed {idx}/{len(slugs)} slugs (fetched={fetched}, failed={failures})")

        click.echo(f"Completed fetching metadata for {fetched} problems. Failures: {failures}. JSONL: {jsonl_path}")

        if fetched == 0:
            click.echo('No successful records to convert to Parquet.', err=True)
            return

        try:
            converted = _jsonl_to_parquet(jsonl_path, parquet_path)
            if converted:
                click.echo(f"Parquet written to {parquet_path} ({converted} records)")
            else:
                click.echo('No records available for Parquet conversion.', err=True)
        except Exception as convert_exc:
            click.echo(f"Warning: failed to convert JSONL to Parquet ({convert_exc}).", err=True)

    except Exception as exc:
        click.echo(f"Error fetching LeetCode metadata: {exc}", err=True)
        sys.exit(1)


@data.command('convert-metadata-parquet')
@click.argument('jsonl_file', type=click.Path(exists=True, dir_okay=False))
@click.option('--output', '-o', default=None, help='Output Parquet file path (defaults to input with .parquet extension)')
def convert_metadata_parquet(jsonl_file: str, output: Optional[str]):
    """Convert an existing LeetCode metadata JSONL file to Parquet."""

    try:
        jsonl_path = Path(jsonl_file)
        if output:
            parquet_path = Path(output)
        else:
            parquet_path = jsonl_path.with_suffix('.parquet')

        converted = _jsonl_to_parquet(jsonl_path, parquet_path)
        if converted == 0:
            click.echo('No records found to convert.', err=True)
        else:
            click.echo(f'Converted {converted} records to {parquet_path}')

    except Exception as exc:
        click.echo(f"Error converting metadata: {exc}", err=True)
        sys.exit(1)


@data.command('inspect-problem')
@click.argument('title_slug')
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
def inspect_problem(title_slug: str, environment: Optional[str], root_path: Optional[str]):
    """Inspect a problem record in the unified dataset (metadata debug helper)."""

    try:
        config = create_config(environment)
        if root_path is None:
            root_path = config.get_config("DATA_ROOT_PATH", ".")

        csv_discovery = CSVDiscovery(root_path)
        csv_loader = CSVLoader(max_workers=config.get_config("PARALLEL_WORKERS", 4))
        data_processor = DataProcessor()
        cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
        dataset_manager = DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)

        dataset = dataset_manager.get_unified_dataset(root_path)
        if dataset is None or dataset.empty:
            click.echo('Unified dataset is empty. Run refresh first.', err=True)
            sys.exit(1)

        dataset = dataset_manager._ensure_title_slug_column(dataset)

        slug = title_slug.strip().lower()
        match = dataset[dataset['title_slug'].astype('string').str.lower() == slug]

        if match.empty:
            click.echo(f'No record found for slug "{slug}".', err=True)
            sys.exit(1)

        record = match.iloc[0]
        click.echo(f"Found record for slug: {slug}")

        columns_of_interest = [
            'title', 'title_slug', 'company', 'difficulty',
            'leetcode_content_html', 'leetcode_content_text',
            'leetcode_likes', 'leetcode_dislikes', 'leetcode_acrate',
            'leetcode_topic_tags', 'leetcode_fetched_at'
        ]

        for column in columns_of_interest:
            if column in record:
                click.echo(f"{column}: {record[column]}")

        extra_columns = [col for col in record.index if col.startswith('leetcode_') and col not in columns_of_interest]
        if extra_columns:
            click.echo('\nAdditional metadata columns:')
            for col in extra_columns:
                click.echo(f"{col}: {record[col]}")

    except Exception as exc:
        click.echo(f"Error inspecting problem: {exc}", err=True)
        sys.exit(1)
@data.command('topic-acceptance')
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--difficulty', '-d', type=click.Choice(['EASY', 'MEDIUM', 'HARD'], case_sensitive=False),
              default=None, help='Filter to a specific difficulty')
@click.option('--top', '-t', default=10, show_default=True, help='Number of topics to display per difficulty')
@click.option('--min-count', '-m', default=5, show_default=True,
              help='Minimum number of problems per topic/difficulty pair')
@click.option('--sort-by', '-s', type=click.Choice(['avg_acceptance', 'problem_count']), default='avg_acceptance',
              show_default=True, help='Field to sort by')
def topic_acceptance(environment: Optional[str], root_path: Optional[str], difficulty: Optional[str],
                     top: int, min_count: int, sort_by: str):
    """Report average acceptance rate per topic and difficulty."""
    try:
        config = create_config(environment)
        if root_path is None:
            root_path = config.get_config("DATA_ROOT_PATH", ".")

        csv_discovery = CSVDiscovery(root_path)
        csv_loader = CSVLoader(max_workers=config.get_config("PARALLEL_WORKERS", 4))
        data_processor = DataProcessor()
        cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
        dataset_manager = DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)

        dataset = dataset_manager.get_unified_dataset(root_path)
        if dataset is None or dataset.empty:
            click.echo("No data available. Run 'python cli.py data load' first.", err=True)
            sys.exit(1)

        def resolve_column(df: pd.DataFrame, candidates: List[str], friendly: str) -> str:
            for candidate in candidates:
                if candidate in df.columns:
                    return candidate
            raise KeyError(friendly)

        try:
            topics_col = resolve_column(
                dataset,
                ['topics', 'normalized_topics', 'topic_list', 'topic_tags', 'topic_names', 'topic_labels'],
                'topics'
            )
            acceptance_col = resolve_column(
                dataset,
                [
                    'acceptance_rate', 'acceptanceRate', 'avg_acceptance', 'acceptRate',
                    'acceptance rate', 'Acceptance Rate', 'acceptance', 'avg_acceptance_rate'
                ],
                'acceptance_rate'
            )
            difficulty_col = resolve_column(
                dataset,
                ['difficulty', 'level', 'Difficulty', 'problem_difficulty', 'difficulty_level'],
                'difficulty'
            )
        except KeyError as missing:
            click.echo(f"Dataset is missing required column: {missing.args[0]}.", err=True)
            sys.exit(1)

        working_df = dataset[[topics_col, acceptance_col, difficulty_col]].dropna(subset=[topics_col]).copy()
        working_df.rename(columns={
            topics_col: 'topics',
            acceptance_col: 'acceptance_rate',
            difficulty_col: 'difficulty'
        }, inplace=True)

        working_df['acceptance_rate'] = pd.to_numeric(working_df['acceptance_rate'], errors='coerce')
        working_df = working_df.dropna(subset=['acceptance_rate'])

        if working_df.empty:
            click.echo("No records with acceptance rate data available.", err=True)
            sys.exit(1)

        exploded = working_df.assign(
            topics=working_df['topics'].astype(str).str.split(',')
        ).explode('topics')

        exploded['topic'] = exploded['topics'].astype(str).str.strip()
        exploded = exploded.drop(columns=['topics'])
        exploded = exploded[exploded['topic'] != '']
        exploded['difficulty'] = exploded['difficulty'].astype(str).str.upper()

        if exploded.empty:
            click.echo("No topic entries found after exploding the dataset.", err=True)
            sys.exit(1)

        grouped = (
            exploded.groupby(['difficulty', 'topic'])
            .agg(
                problem_count=('topic', 'size'),
                avg_acceptance=('acceptance_rate', 'mean'),
                median_acceptance=('acceptance_rate', 'median')
            )
            .reset_index()
        )

        grouped = grouped[grouped['problem_count'] >= max(1, min_count)]
        if grouped.empty:
            click.echo("No topic/difficulty combinations met the minimum count threshold.", err=True)
            sys.exit(1)

        grouped['avg_acceptance'] = grouped['avg_acceptance'] * 100
        grouped['median_acceptance'] = grouped['median_acceptance'] * 100

        difficulties = ['EASY', 'MEDIUM', 'HARD']
        if difficulty:
            difficulties = [difficulty.upper()]

        for diff in difficulties:
            subset = grouped[grouped['difficulty'] == diff]
            if subset.empty:
                continue

            if sort_by == 'avg_acceptance':
                subset = subset.sort_values(by='avg_acceptance', ascending=False)
            else:
                subset = subset.sort_values(by='problem_count', ascending=False)
            display_df = subset.head(top)

            click.echo(f"\n{diff} topics (min problems per topic: {min_count})")
            click.echo("-" * (len(diff) + 30))
            click.echo(
                display_df[['topic', 'problem_count', 'avg_acceptance', 'median_acceptance']]
                .rename(columns={
                    'topic': 'Topic',
                    'problem_count': 'Problems',
                    'avg_acceptance': 'Avg Acceptance %',
                    'median_acceptance': 'Median Acceptance %'
                })
                .to_string(index=False, formatters={
                    'Avg Acceptance %': lambda x: f"{x:6.2f}",
                    'Median Acceptance %': lambda x: f"{x:6.2f}"
                })
            )

        click.echo("\nDone.")

    except Exception as exc:
        click.echo(f"Error generating topic acceptance report: {exc}", err=True)
        sys.exit(1)


@data.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', 
              help='Output format')
def status(environment: Optional[str], root_path: Optional[str], output: str):
    """Show data loading status and cache information."""
    try:
        # Initialize configuration and services
        config = create_config(environment)
        
        if root_path is None:
            root_path = config.get_config("DATA_ROOT_PATH", ".")
        
        # Initialize services
        csv_discovery = CSVDiscovery(root_path)
        csv_loader = CSVLoader()
        data_processor = DataProcessor()
        cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
        dataset_manager = DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)
        
        # Get dataset information
        info = dataset_manager.get_dataset_info(root_path)
        
        if output == 'json':
            click.echo(json.dumps(info, indent=2, default=str))
        else:
            # Table format
            click.echo("Data Loading Status")
            click.echo("=" * 50)
            
            # Source files info
            source_info = info['source_files']
            click.echo(f"CSV Files: {source_info['total_csv_files']}")
            click.echo(f"Companies: {source_info['companies']}")
            click.echo(f"Timeframes: {', '.join(source_info['timeframes'])}")
            
            # Cache status
            click.echo("\nCache Status:")
            cache_status = info['cache_status']
            
            for dataset_name, status_info in cache_status.items():
                status_icon = "✅" if status_info['cached'] else "❌"
                dataset_display = dataset_name.replace('_', ' ').title()
                click.echo(f"  {status_icon} {dataset_display}: {'Cached' if status_info['cached'] else 'Not cached'}")
            
            # Cache statistics
            cache_stats = info['cache_stats']
            click.echo(f"\nCache Statistics:")
            total_files = sum(ct['file_count'] for ct in cache_stats['cache_types'].values())
            total_size_mb = sum(ct['total_size_mb'] for ct in cache_stats['cache_types'].values())
            click.echo(f"  Total files: {total_files}")
            click.echo(f"  Total size: {total_size_mb:.2f} MB")
            click.echo(f"  Cache directory: {cache_stats['cache_dir']}")
        
    except Exception as e:
        click.echo(f"Error getting status: {e}", err=True)
        sys.exit(1)


@data.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.confirmation_option(prompt='Are you sure you want to clear all cached data?')
def clear_cache(environment: Optional[str]):
    """Clear all cached datasets."""
    try:
        config = create_config(environment)
        cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
        
        # Clear cache
        cache_manager.clear_cache()
        
        click.echo("✅ All cached data has been cleared")
        
    except Exception as e:
        click.echo(f"Error clearing cache: {e}", err=True)
        sys.exit(1)


@data.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--company', '-c', help='Validate only specific company')
@click.option('--output', '-o', type=click.Choice(['json', 'detailed', 'summary']), default='detailed', 
              help='Output format')
@click.option('--check-duplicates/--no-check-duplicates', default=True, help='Check for duplicate problems')
@click.option('--check-links/--no-check-links', default=False, help='Validate LeetCode links (slower)')
def validate(environment: Optional[str], root_path: Optional[str], company: Optional[str], 
            output: str, check_duplicates: bool, check_links: bool):
    """Validate data integrity and report quality issues."""
    try:
        # Initialize configuration and services
        config = create_config(environment)
        
        if root_path is None:
            root_path = config.get_config("DATA_ROOT_PATH", ".")
        
        # Initialize services
        csv_discovery = CSVDiscovery(root_path)
        csv_loader = CSVLoader(max_workers=config.get_config("PARALLEL_WORKERS", 4))
        
        # Discover CSV files
        all_csv_files = csv_discovery.discover_csv_files()
        
        # Filter by company if specified
        if company:
            all_csv_files = [f for f in all_csv_files if f.company.lower() == company.lower()]
            if not all_csv_files:
                click.echo(f"No CSV files found for company: {company}", err=True)
                sys.exit(1)
        
        click.echo(f"Validating {len(all_csv_files)} CSV files...")
        if company:
            click.echo(f"Company filter: {company}")
        
        start_time = time.time()
        
        # Validation results
        validation_results = {
            'total_files': len(all_csv_files),
            'valid_files': 0,
            'invalid_files': 0,
            'total_records': 0,
            'valid_records': 0,
            'issues': {
                'missing_columns': [],
                'empty_titles': [],
                'invalid_frequencies': [],
                'invalid_acceptance_rates': [],
                'duplicate_problems': [],
                'invalid_links': [],
                'encoding_issues': [],
                'parsing_errors': []
            },
            'company_stats': {},
            'file_details': []
        }
        
        # Process each file
        with tqdm(total=len(all_csv_files), desc="Validating files") as pbar:
            for csv_file in all_csv_files:
                file_result = {
                    'file_path': csv_file.file_path,
                    'company': csv_file.company,
                    'timeframe': csv_file.timeframe.value,
                    'is_valid': True,
                    'errors': [],
                    'warnings': [],
                    'record_count': 0
                }
                
                try:
                    # Load and validate single file
                    df, validation_result = csv_loader.load_single_file(csv_file)
                    
                    if df is not None:
                        file_result['record_count'] = len(df)
                        validation_results['total_records'] += len(df)
                        
                        if validation_result.is_valid:
                            validation_results['valid_files'] += 1
                            validation_results['valid_records'] += validation_result.processed_rows
                        else:
                            validation_results['invalid_files'] += 1
                            file_result['is_valid'] = False
                        
                        file_result['errors'] = validation_result.errors
                        file_result['warnings'] = validation_result.warnings
                        
                        # Collect specific issues
                        _collect_validation_issues(df, validation_results, csv_file, check_duplicates, check_links)
                        
                        # Update company stats
                        if csv_file.company not in validation_results['company_stats']:
                            validation_results['company_stats'][csv_file.company] = {
                                'files': 0,
                                'records': 0,
                                'valid_files': 0,
                                'issues': 0
                            }
                        
                        company_stats = validation_results['company_stats'][csv_file.company]
                        company_stats['files'] += 1
                        company_stats['records'] += len(df)
                        if validation_result.is_valid:
                            company_stats['valid_files'] += 1
                        company_stats['issues'] += len(validation_result.errors) + len(validation_result.warnings)
                    
                    else:
                        validation_results['invalid_files'] += 1
                        file_result['is_valid'] = False
                        file_result['errors'] = ['Failed to load CSV file']
                        validation_results['issues']['parsing_errors'].append({
                            'file': csv_file.file_path,
                            'company': csv_file.company,
                            'error': 'Failed to load CSV file'
                        })
                
                except Exception as e:
                    validation_results['invalid_files'] += 1
                    file_result['is_valid'] = False
                    file_result['errors'] = [str(e)]
                    validation_results['issues']['parsing_errors'].append({
                        'file': csv_file.file_path,
                        'company': csv_file.company,
                        'error': str(e)
                    })
                
                validation_results['file_details'].append(file_result)
                pbar.update(1)
        
        processing_time = time.time() - start_time
        validation_results['processing_time_seconds'] = round(processing_time, 2)
        
        # Generate output
        if output == 'json':
            click.echo(json.dumps(validation_results, indent=2, default=str))
        
        elif output == 'summary':
            _print_validation_summary(validation_results)
        
        else:  # detailed
            _print_detailed_validation_report(validation_results)
        
        # Exit with error code if validation failed
        if validation_results['invalid_files'] > 0:
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error during validation: {e}", err=True)
        sys.exit(1)


@data.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--output', '-o', type=click.Choice(['json', 'detailed', 'summary']), default='detailed', 
              help='Output format')
@click.option('--include-topics/--no-include-topics', default=True, help='Include topic analysis')
@click.option('--top-n', default=10, type=int, help='Number of top items to show in rankings')
def report(environment: Optional[str], root_path: Optional[str], output: str, 
          include_topics: bool, top_n: int):
    """Generate comprehensive data quality and statistics report."""
    try:
        # Initialize configuration and services
        config = create_config(environment)
        
        if root_path is None:
            root_path = config.get_config("DATA_ROOT_PATH", ".")
        
        # Initialize services
        csv_discovery = CSVDiscovery(root_path)
        csv_loader = CSVLoader(max_workers=config.get_config("PARALLEL_WORKERS", 4))
        data_processor = DataProcessor()
        cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
        dataset_manager = DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)
        
        click.echo("Generating data quality report...")
        start_time = time.time()
        
        # Get or create unified dataset
        unified_df = dataset_manager.get_unified_dataset(root_path)
        
        if unified_df is None or unified_df.empty:
            click.echo("No data available for reporting. Run 'data load' first.", err=True)
            sys.exit(1)
        
        # Generate comprehensive report
        report_data = _generate_data_report(unified_df, include_topics, top_n)
        report_data['processing_time_seconds'] = round(time.time() - start_time, 2)
        
        # Generate output
        if output == 'json':
            click.echo(json.dumps(report_data, indent=2, default=str))
        
        elif output == 'summary':
            _print_report_summary(report_data)
        
        else:  # detailed
            _print_detailed_report(report_data, top_n)
        
    except Exception as e:
        click.echo(f"Error generating report: {e}", err=True)
        sys.exit(1)


@data.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--output-file', '-f', required=True, help='Output file path (supports .csv, .json, .parquet)')
@click.option('--format', 'export_format', type=click.Choice(['csv', 'json', 'parquet']), 
              help='Export format (auto-detected from file extension if not specified)')
@click.option('--dataset', '-d', type=click.Choice(['unified', 'exploded', 'company_stats']), 
              default='unified', help='Dataset to export')
@click.option('--company', '-c', help='Export only specific company data')
@click.option('--timeframe', '-t', type=click.Choice(['30d', '3m', '6m', '6m+', 'all']), 
              help='Export only specific timeframe')
@click.option('--force-refresh', '--force', is_flag=True, help='Force refresh dataset before export')
def export(environment: Optional[str], root_path: Optional[str], output_file: str, 
          export_format: Optional[str], dataset: str, company: Optional[str], 
          timeframe: Optional[str], force_refresh: bool):
    """Export processed datasets to various formats."""
    try:
        # Initialize configuration and services
        config = create_config(environment)
        
        if root_path is None:
            root_path = config.get_config("DATA_ROOT_PATH", ".")
        
        # Auto-detect format from file extension if not specified
        if export_format is None:
            file_ext = Path(output_file).suffix.lower()
            format_map = {'.csv': 'csv', '.json': 'json', '.parquet': 'parquet'}
            export_format = format_map.get(file_ext)
            if export_format is None:
                click.echo(f"Cannot auto-detect format from extension: {file_ext}", err=True)
                click.echo("Please specify --format explicitly", err=True)
                sys.exit(1)
        
        # Initialize services
        csv_discovery = CSVDiscovery(root_path)
        csv_loader = CSVLoader(max_workers=config.get_config("PARALLEL_WORKERS", 4))
        data_processor = DataProcessor()
        cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
        dataset_manager = DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)
        
        click.echo(f"Exporting {dataset} dataset to {output_file} ({export_format} format)")
        
        start_time = time.time()
        
        # Get the requested dataset
        if dataset == 'unified':
            df = dataset_manager.get_unified_dataset(root_path, force_refresh)
        elif dataset == 'exploded':
            df = dataset_manager.create_exploded_dataset(root_path=root_path, force_refresh=force_refresh)
        elif dataset == 'company_stats':
            df = dataset_manager.create_company_statistics(root_path=root_path, force_refresh=force_refresh)
        else:
            click.echo(f"Unknown dataset: {dataset}", err=True)
            sys.exit(1)
        
        if df is None or df.empty:
            click.echo(f"No data available for {dataset} dataset", err=True)
            sys.exit(1)
        
        # Apply filters
        original_count = len(df)
        
        if company and 'company' in df.columns:
            df = df[df['company'].str.lower() == company.lower()]
            if df.empty:
                click.echo(f"No data found for company: {company}", err=True)
                sys.exit(1)
        
        if timeframe and 'timeframe' in df.columns:
            # Map timeframe to the actual values in the data
            timeframe_map = {
                '30d': 'thirty_days',
                '3m': 'three_months', 
                '6m': 'six_months',
                '6m+': 'more_than_six_months',
                'all': 'all'
            }
            target_timeframe = timeframe_map.get(timeframe, timeframe)
            df = df[df['timeframe'] == target_timeframe]
            if df.empty:
                click.echo(f"No data found for timeframe: {timeframe}", err=True)
                sys.exit(1)
        
        # Export data
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if export_format == 'csv':
            df.to_csv(output_path, index=False)
        elif export_format == 'json':
            df.to_json(output_path, orient='records', indent=2, date_format='iso')
        elif export_format == 'parquet':
            df.to_parquet(output_path, index=False)
        
        processing_time = time.time() - start_time
        
        click.echo(f"✅ Successfully exported {len(df):,} records")
        click.echo(f"   Original dataset: {original_count:,} records")
        click.echo(f"   Filtered dataset: {len(df):,} records")
        click.echo(f"   Output file: {output_path}")
        click.echo(f"   File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        click.echo(f"   Processing time: {processing_time:.2f} seconds")
        
    except Exception as e:
        click.echo(f"Error exporting data: {e}", err=True)
        sys.exit(1)


def _collect_validation_issues(df: pd.DataFrame, validation_results: Dict[str, Any], 
                             csv_file, check_duplicates: bool, check_links: bool):
    """Collect specific validation issues from a DataFrame."""
    # Check for missing required columns
    required_columns = ['title', 'difficulty']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        validation_results['issues']['missing_columns'].append({
            'file': csv_file.file_path,
            'company': csv_file.company,
            'missing_columns': missing_cols
        })
    
    # Check for empty titles
    if 'title' in df.columns:
        empty_titles = df['title'].isna().sum()
        if empty_titles > 0:
            validation_results['issues']['empty_titles'].append({
                'file': csv_file.file_path,
                'company': csv_file.company,
                'count': empty_titles
            })
    
    # Check frequency values
    if 'frequency' in df.columns:
        try:
            numeric_freq = pd.to_numeric(df['frequency'], errors='coerce')
            invalid_freq = numeric_freq.isna().sum() - df['frequency'].isna().sum()
            if invalid_freq > 0:
                validation_results['issues']['invalid_frequencies'].append({
                    'file': csv_file.file_path,
                    'company': csv_file.company,
                    'count': invalid_freq
                })
        except Exception:
            pass
    
    # Check acceptance rates
    if 'acceptance_rate' in df.columns:
        try:
            numeric_rate = pd.to_numeric(df['acceptance_rate'], errors='coerce')
            invalid_rate = numeric_rate.isna().sum() - df['acceptance_rate'].isna().sum()
            if invalid_rate > 0:
                validation_results['issues']['invalid_acceptance_rates'].append({
                    'file': csv_file.file_path,
                    'company': csv_file.company,
                    'count': invalid_rate
                })
        except Exception:
            pass
    
    # Check for duplicates
    if check_duplicates and 'title' in df.columns:
        duplicates = df.duplicated(subset=['title']).sum()
        if duplicates > 0:
            validation_results['issues']['duplicate_problems'].append({
                'file': csv_file.file_path,
                'company': csv_file.company,
                'count': duplicates
            })
    
    # Check links (basic validation)
    if check_links and 'link' in df.columns:
        invalid_links = 0
        for link in df['link'].dropna():
            if not str(link).startswith(('http://', 'https://')):
                invalid_links += 1
        
        if invalid_links > 0:
            validation_results['issues']['invalid_links'].append({
                'file': csv_file.file_path,
                'company': csv_file.company,
                'count': invalid_links
            })


def _print_validation_summary(validation_results: Dict[str, Any]):
    """Print a summary of validation results."""
    click.echo("Data Validation Summary")
    click.echo("=" * 50)
    click.echo(f"Files processed: {validation_results['total_files']}")
    click.echo(f"Valid files: {validation_results['valid_files']}")
    click.echo(f"Invalid files: {validation_results['invalid_files']}")
    click.echo(f"Total records: {validation_results['total_records']:,}")
    click.echo(f"Processing time: {validation_results['processing_time_seconds']:.2f} seconds")
    
    # Issue summary
    issues = validation_results['issues']
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    
    if total_issues > 0:
        click.echo(f"\n⚠️  Found {total_issues} issue types:")
        for issue_type, issue_list in issues.items():
            if issue_list:
                issue_name = issue_type.replace('_', ' ').title()
                click.echo(f"  - {issue_name}: {len(issue_list)} files affected")
    else:
        click.echo("\n✅ No validation issues found")


def _print_detailed_validation_report(validation_results: Dict[str, Any]):
    """Print detailed validation report."""
    _print_validation_summary(validation_results)
    
    # Detailed issues
    issues = validation_results['issues']
    
    for issue_type, issue_list in issues.items():
        if issue_list:
            issue_name = issue_type.replace('_', ' ').title()
            click.echo(f"\n{issue_name}:")
            for issue in issue_list[:10]:  # Show first 10
                if 'count' in issue:
                    click.echo(f"  - {issue['company']}: {issue['count']} issues")
                else:
                    click.echo(f"  - {issue['company']}: {issue.get('error', 'Unknown error')}")
            
            if len(issue_list) > 10:
                click.echo(f"  ... and {len(issue_list) - 10} more")
    
    # Company statistics
    if validation_results['company_stats']:
        click.echo(f"\nCompany Statistics:")
        for company, stats in list(validation_results['company_stats'].items())[:10]:
            success_rate = (stats['valid_files'] / stats['files'] * 100) if stats['files'] > 0 else 0
            click.echo(f"  {company}: {stats['valid_files']}/{stats['files']} files valid ({success_rate:.1f}%)")


def _generate_data_report(df: pd.DataFrame, include_topics: bool, top_n: int) -> Dict[str, Any]:
    """Generate comprehensive data quality report."""
    report = {
        'overview': {
            'total_records': len(df),
            'companies': df['company'].nunique(),
            'unique_problems': df['title'].nunique() if 'title' in df.columns else 0,
            'timeframes': df['timeframe'].unique().tolist() if 'timeframe' in df.columns else [],
            'date_range': {
                'earliest': df['last_updated'].min() if 'last_updated' in df.columns else None,
                'latest': df['last_updated'].max() if 'last_updated' in df.columns else None
            }
        }
    }
    
    # Company analysis
    if 'company' in df.columns:
        agg_dict = {'title': 'count'}
        if 'frequency' in df.columns:
            agg_dict['frequency'] = ['mean', 'max']
        if 'acceptance_rate' in df.columns:
            agg_dict['acceptance_rate'] = 'mean'
        
        company_stats = df.groupby('company').agg(agg_dict).round(2)
        
        report['companies'] = {
            'top_by_problems': company_stats.head(top_n).to_dict(),
            'total_companies': len(company_stats)
        }
    
    # Difficulty analysis
    if 'difficulty' in df.columns:
        difficulty_counts = df['difficulty'].value_counts()
        report['difficulty_distribution'] = difficulty_counts.to_dict()
    
    # Frequency analysis
    if 'frequency' in df.columns:
        freq_stats = df['frequency'].describe()
        report['frequency_stats'] = {
            'mean': round(freq_stats['mean'], 2),
            'median': round(freq_stats['50%'], 2),
            'std': round(freq_stats['std'], 2),
            'min': round(freq_stats['min'], 2),
            'max': round(freq_stats['max'], 2),
            'zero_values': int((df['frequency'] == 0).sum())
        }
    
    # Topic analysis
    if include_topics and 'topics' in df.columns:
        all_topics = []
        for topics_str in df['topics'].dropna():
            if isinstance(topics_str, str):
                topics = [t.strip() for t in topics_str.split(',') if t.strip()]
                all_topics.extend(topics)
        
        if all_topics:
            topic_counts = pd.Series(all_topics).value_counts()
            report['topics'] = {
                'total_unique_topics': len(topic_counts),
                'top_topics': topic_counts.head(top_n).to_dict(),
                'avg_topics_per_problem': round(len(all_topics) / len(df), 2)
            }
    
    # Data quality metrics
    report['data_quality'] = {
        'completeness': {},
        'duplicates': {}
    }
    
    # Check completeness for each column
    for col in df.columns:
        if col not in ['company', 'timeframe', 'source_file', 'last_updated']:
            missing_pct = (df[col].isna().sum() / len(df)) * 100
            report['data_quality']['completeness'][col] = round(missing_pct, 2)
    
    # Check for duplicates
    if 'title' in df.columns:
        total_duplicates = df.duplicated(subset=['title']).sum()
        report['data_quality']['duplicates']['total'] = total_duplicates
        report['data_quality']['duplicates']['percentage'] = round((total_duplicates / len(df)) * 100, 2)
    
    return report


def _print_report_summary(report_data: Dict[str, Any]):
    """Print summary of data report."""
    overview = report_data['overview']
    
    click.echo("Data Quality Report Summary")
    click.echo("=" * 50)
    click.echo(f"Total records: {overview['total_records']:,}")
    click.echo(f"Companies: {overview['companies']}")
    click.echo(f"Unique problems: {overview['unique_problems']:,}")
    click.echo(f"Processing time: {report_data['processing_time_seconds']:.2f} seconds")
    
    # Data quality summary
    if 'data_quality' in report_data:
        quality = report_data['data_quality']
        if 'completeness' in quality:
            avg_completeness = 100 - sum(quality['completeness'].values()) / len(quality['completeness'])
            click.echo(f"Average completeness: {avg_completeness:.1f}%")
        
        if 'duplicates' in quality and 'percentage' in quality['duplicates']:
            click.echo(f"Duplicate problems: {quality['duplicates']['percentage']:.1f}%")


def _print_detailed_report(report_data: Dict[str, Any], top_n: int):
    """Print detailed data report."""
    _print_report_summary(report_data)
    
    # Company details
    if 'companies' in report_data:
        click.echo(f"\nTop {top_n} Companies by Problem Count:")
        companies = report_data['companies']['top_by_problems']
        if 'title' in companies:
            for company, count in list(companies['title'].items())[:top_n]:
                click.echo(f"  {company}: {count:,} problems")
    
    # Difficulty distribution
    if 'difficulty_distribution' in report_data:
        click.echo("\nDifficulty Distribution:")
        for difficulty, count in report_data['difficulty_distribution'].items():
            percentage = (count / report_data['overview']['total_records']) * 100
            click.echo(f"  {difficulty}: {count:,} ({percentage:.1f}%)")
    
    # Frequency statistics
    if 'frequency_stats' in report_data:
        stats = report_data['frequency_stats']
        click.echo(f"\nFrequency Statistics:")
        click.echo(f"  Mean: {stats['mean']}")
        click.echo(f"  Median: {stats['median']}")
        click.echo(f"  Standard deviation: {stats['std']}")
        click.echo(f"  Range: {stats['min']} - {stats['max']}")
        click.echo(f"  Zero frequency problems: {stats['zero_values']:,}")
    
    # Topic analysis
    if 'topics' in report_data:
        topics = report_data['topics']
        click.echo(f"\nTopic Analysis:")
        click.echo(f"  Total unique topics: {topics['total_unique_topics']:,}")
        click.echo(f"  Average topics per problem: {topics['avg_topics_per_problem']}")
        click.echo(f"  Top {top_n} topics:")
        for topic, count in list(topics['top_topics'].items())[:top_n]:
            click.echo(f"    {topic}: {count:,}")
    
    # Data quality details
    if 'data_quality' in report_data:
        quality = report_data['data_quality']
        
        if 'completeness' in quality:
            click.echo(f"\nData Completeness (% missing):")
            for col, missing_pct in quality['completeness'].items():
                status = "✅" if missing_pct < 5 else "⚠️" if missing_pct < 20 else "❌"
                click.echo(f"  {status} {col}: {missing_pct:.1f}%")
        
        if 'duplicates' in quality:
            dup_info = quality['duplicates']
            if dup_info['total'] > 0:
                click.echo(f"\n⚠️  Duplicate Problems: {dup_info['total']:,} ({dup_info['percentage']:.1f}%)")
            else:
                click.echo(f"\n✅ No duplicate problems found")


if __name__ == '__main__':
    data()
