"""CLI commands for exporting static JSON data for frontend deployment."""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import click
import pandas as pd

from src.config.settings import create_config
from src.services.csv_discovery import CSVDiscovery
from src.services.csv_loader import CSVLoader
from src.services.data_processor import DataProcessor
from src.services.cache_manager import CacheManager
from src.services.dataset_manager import DatasetManager
from src.analytics.analytics_engine import AnalyticsEngine
from src.analytics.topic_analyzer import TopicAnalyzer


def _build_services(environment: Optional[str], root_path: Optional[str]):
    """Build and return all required services."""
    config = create_config(environment)

    if root_path is None:
        root_path = config.get_config("DATA_ROOT_PATH", ".")

    csv_discovery = CSVDiscovery(root_path)
    csv_loader = CSVLoader(max_workers=config.get_config("PARALLEL_WORKERS", 4))
    data_processor = DataProcessor()
    cache_manager = CacheManager(config.get_config("CACHE_DIR", ".cache"))
    dataset_manager = DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)
    analytics_engine = AnalyticsEngine()
    topic_analyzer = TopicAnalyzer()

    return {
        'config': config,
        'root_path': root_path,
        'dataset_manager': dataset_manager,
        'analytics_engine': analytics_engine,
        'topic_analyzer': topic_analyzer,
    }


def _slugify(name: str) -> str:
    """Convert a name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


def _normalize_topics(topics_val) -> List[str]:
    """Normalize topics value to a list of strings."""
    if pd.isna(topics_val):
        return []
    if isinstance(topics_val, list):
        return [str(t).strip() for t in topics_val if t]
    if isinstance(topics_val, str):
        return [t.strip() for t in topics_val.split(',') if t.strip()]
    return []


def _safe_json_value(val):
    """Convert a value to a JSON-safe format."""
    if pd.isna(val):
        return None
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.isoformat()
    if isinstance(val, (int, float, str, bool, list, dict)):
        return val
    return str(val)


def _write_json(path: Path, data: Any):
    """Write data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=_safe_json_value)


@click.group()
def static():
    """Static site data export commands."""
    pass


@static.command('export')
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--root-path', '-r', default=None, help='Root directory containing company CSV files')
@click.option('--output', '-o', default='frontend/public/data', help='Output directory for JSON files')
@click.option('--force', '-f', is_flag=True, help='Force refresh datasets before export')
def export_static(environment: Optional[str], root_path: Optional[str], output: str, force: bool):
    """Export all data as static JSON files for frontend deployment."""
    try:
        start_time = time.time()
        output_path = Path(output)

        click.echo(f"Exporting static data to: {output_path}")

        # Build services
        services = _build_services(environment, root_path)
        dataset_manager = services['dataset_manager']
        analytics_engine = services['analytics_engine']
        topic_analyzer = services['topic_analyzer']
        root = services['root_path']

        # Load unified dataset
        click.echo("Loading unified dataset...")
        unified_df = dataset_manager.create_unified_dataset(root, force_refresh=force)

        if unified_df is None or unified_df.empty:
            click.echo("No data available. Run 'python cli.py data refresh' first.", err=True)
            sys.exit(1)

        click.echo(f"  Loaded {len(unified_df):,} records from {unified_df['company'].nunique()} companies")

        # Export company statistics
        click.echo("Exporting company statistics...")
        _export_company_stats(dataset_manager, root, output_path, force)

        # Export per-company problem data
        click.echo("Exporting per-company problem data...")
        _export_company_problems(unified_df, output_path)

        # Export topic data
        click.echo("Exporting topic data...")
        _export_topic_data(topic_analyzer, unified_df, output_path)

        # Export analytics summary
        click.echo("Exporting analytics summary...")
        _export_analytics(analytics_engine, unified_df, output_path)

        # Export all problems (for client-side filtering)
        click.echo("Exporting all problems...")
        _export_all_problems(unified_df, output_path)

        # Export problem previews from LeetCode metadata
        click.echo("Exporting problem previews...")
        _export_problem_previews(output_path)

        # Export pre-generated study plans
        click.echo("Exporting pre-generated study plans...")
        _export_study_plans(unified_df, output_path)

        # Write manifest
        click.echo("Writing manifest...")
        manifest = {
            'version': '1.0.0',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'total_companies': int(unified_df['company'].nunique()),
            'total_problems': int(unified_df['title'].nunique()),
            'total_records': len(unified_df),
        }
        _write_json(output_path / 'index.json', manifest)

        processing_time = time.time() - start_time
        click.echo(f"\n✅ Static export complete!")
        click.echo(f"   Output directory: {output_path}")
        click.echo(f"   Processing time: {processing_time:.2f} seconds")

    except Exception as e:
        click.echo(f"Error during static export: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _export_company_stats(dataset_manager: DatasetManager, root_path: str,
                          output_path: Path, force: bool):
    """Export company statistics to JSON."""
    company_stats_df = dataset_manager.create_company_statistics(root_path=root_path, force_refresh=force)

    if company_stats_df is None or company_stats_df.empty:
        click.echo("  Warning: No company statistics available", err=True)
        return

    # Convert to list of company objects matching frontend CompanyData type
    companies = []
    for idx, row in company_stats_df.iterrows():
        company_name = row.get('company', idx)

        # Parse difficulty distribution
        difficulty_dist = {
            'EASY': int(row.get('easy_count', 0) or 0),
            'MEDIUM': int(row.get('medium_count', 0) or 0),
            'HARD': int(row.get('hard_count', 0) or 0),
            'UNKNOWN': int(row.get('unknown_count', 0) or 0),
        }

        # Parse top topics
        top_topics = row.get('top_topics', {})
        if isinstance(top_topics, str):
            try:
                top_topics = json.loads(top_topics)
            except:
                top_topics = {}
        if isinstance(top_topics, dict):
            top_topics_list = sorted(top_topics.keys(), key=lambda k: top_topics[k], reverse=True)[:10]
        else:
            top_topics_list = []

        # Parse timeframe coverage
        timeframe_coverage = []
        for tf in ['30d', '3m', '6m', '6m+', 'all']:
            col = f'timeframe_{tf.replace("+", "_plus")}'
            if row.get(col, 0) > 0:
                timeframe_coverage.append(tf)

        company_data = {
            'company': str(company_name),
            'totalProblems': int(row.get('total_problems', 0) or 0),
            'uniqueProblems': int(row.get('unique_problems', 0) or 0),
            'avgFrequency': float(row.get('avg_frequency', 0) or 0),
            'avgAcceptanceRate': float(row.get('avg_acceptance_rate', 0) or 0),
            'difficultyDistribution': difficulty_dist,
            'topTopics': top_topics_list,
            'timeframeCoverage': timeframe_coverage,
        }
        companies.append(company_data)

    # Sort by total problems descending
    companies.sort(key=lambda x: x['totalProblems'], reverse=True)

    # Add rank
    for i, company in enumerate(companies):
        company['rank'] = i + 1

    _write_json(output_path / 'companies' / 'stats.json', companies)
    click.echo(f"  Exported {len(companies)} companies")


def _export_company_problems(unified_df: pd.DataFrame, output_path: Path):
    """Export per-company problem data."""
    companies_path = output_path / 'companies'
    companies_path.mkdir(parents=True, exist_ok=True)

    company_groups = unified_df.groupby('company')
    exported_count = 0

    for company_name, group in company_groups:
        slug = _slugify(str(company_name))

        # Deduplicate problems by title
        problems = []
        seen_titles = {}

        for _, row in group.iterrows():
            title = row.get('title', '')
            if not title:
                continue

            if title in seen_titles:
                # Update existing with additional timeframe
                existing = seen_titles[title]
                timeframe = row.get('timeframe', '')
                if timeframe and timeframe not in existing['timeframes']:
                    existing['timeframes'].append(timeframe)
                continue

            topics = _normalize_topics(row.get('topics'))
            timeframe = row.get('timeframe', '')

            problem = {
                'title': str(title),
                'titleSlug': _slugify(str(title)),
                'difficulty': str(row.get('difficulty', 'UNKNOWN')).upper(),
                'frequency': float(row['frequency']) if pd.notna(row.get('frequency')) else None,
                'acceptanceRate': float(row['acceptance_rate']) if pd.notna(row.get('acceptance_rate')) else None,
                'link': row.get('leetcode_link') or row.get('link') or row.get('url'),
                'topics': topics,
                'timeframe': timeframe,
                'timeframes': [timeframe] if timeframe else [],
            }

            problems.append(problem)
            seen_titles[title] = problem

        # Sort by frequency descending
        problems.sort(key=lambda x: x.get('frequency') or 0, reverse=True)

        # Calculate company stats
        difficulty_counts = group['difficulty'].value_counts().to_dict()
        top_topics = {}
        for topics_val in group['topics'].dropna():
            for topic in _normalize_topics(topics_val):
                top_topics[topic] = top_topics.get(topic, 0) + 1

        top_topics_list = sorted(top_topics.keys(), key=lambda k: top_topics[k], reverse=True)[:15]

        company_data = {
            'company': str(company_name),
            'stats': {
                'totalProblems': len(problems),
                'uniqueProblems': len(problems),
                'avgFrequency': group['frequency'].mean() if 'frequency' in group.columns else 0,
                'avgAcceptanceRate': group['acceptance_rate'].mean() if 'acceptance_rate' in group.columns else 0,
                'difficultyDistribution': {
                    'EASY': int(difficulty_counts.get('EASY', difficulty_counts.get('Easy', 0))),
                    'MEDIUM': int(difficulty_counts.get('MEDIUM', difficulty_counts.get('Medium', 0))),
                    'HARD': int(difficulty_counts.get('HARD', difficulty_counts.get('Hard', 0))),
                    'UNKNOWN': int(difficulty_counts.get('UNKNOWN', difficulty_counts.get('Unknown', 0))),
                },
            },
            'problems': problems,
            'topTopics': top_topics_list,
        }

        _write_json(companies_path / f'{slug}.json', company_data)
        exported_count += 1

    click.echo(f"  Exported {exported_count} company files")


def _export_topic_data(topic_analyzer: TopicAnalyzer, unified_df: pd.DataFrame,
                       output_path: Path):
    """Export topic analysis data."""
    topics_path = output_path / 'topics'
    topics_path.mkdir(parents=True, exist_ok=True)

    # Topic trends
    try:
        trends_df = topic_analyzer.analyze_topic_trends(unified_df)
        if trends_df is not None and not trends_df.empty:
            trends = []
            for _, row in trends_df.iterrows():
                trend = {
                    'topic': str(row.get('topic', '')),
                    'trendDirection': str(row.get('trend_direction', 'stable')),
                    'trendStrength': float(row.get('trend_strength', 0)) if pd.notna(row.get('trend_strength')) else 0,
                    'trendStrengthAbs': abs(float(row.get('trend_strength', 0))) if pd.notna(row.get('trend_strength')) else 0,
                    'totalFrequency': int(row.get('total_frequency', 0)) if pd.notna(row.get('total_frequency')) else 0,
                }

                # Add timeframe frequencies if available
                timeframe_cols = [c for c in trends_df.columns if c.startswith('freq_')]
                if timeframe_cols:
                    timeframe_freqs = {}
                    for col in timeframe_cols:
                        tf_name = col.replace('freq_', '')
                        timeframe_freqs[tf_name] = int(row.get(col, 0)) if pd.notna(row.get(col)) else 0
                    trend['timeframeFrequencies'] = timeframe_freqs

                trends.append(trend)

            _write_json(topics_path / 'trends.json', trends)
            click.echo(f"  Exported {len(trends)} topic trends")
    except Exception as e:
        click.echo(f"  Warning: Could not export topic trends: {e}", err=True)

    # Topic frequency
    try:
        freq_df = topic_analyzer.get_topic_frequency(unified_df, limit=100)
        if freq_df is not None and not freq_df.empty:
            frequencies = []
            for _, row in freq_df.iterrows():
                freq = {
                    'topic': str(row.get('topic', '')),
                    'frequency': int(row.get('frequency', 0)) if pd.notna(row.get('frequency')) else 0,
                    'uniqueProblems': int(row.get('unique_problems', 0)) if pd.notna(row.get('unique_problems')) else 0,
                    'companies': int(row.get('companies', 0)) if pd.notna(row.get('companies')) else 0,
                    'avgAcceptanceRate': float(row.get('avg_acceptance_rate', 0)) if pd.notna(row.get('avg_acceptance_rate')) else 0,
                }
                frequencies.append(freq)

            _write_json(topics_path / 'frequency.json', frequencies)
            click.echo(f"  Exported {len(frequencies)} topic frequencies")
    except Exception as e:
        click.echo(f"  Warning: Could not export topic frequency: {e}", err=True)

    # Topic heatmap
    try:
        heatmap_data = topic_analyzer.generate_topic_heatmap_data(unified_df, top_n=30)
        if heatmap_data:
            _write_json(topics_path / 'heatmap.json', heatmap_data)
            click.echo(f"  Exported topic heatmap ({len(heatmap_data.get('topics', []))} topics x {len(heatmap_data.get('companies', []))} companies)")
    except Exception as e:
        click.echo(f"  Warning: Could not export topic heatmap: {e}", err=True)


def _export_analytics(analytics_engine: AnalyticsEngine, unified_df: pd.DataFrame,
                      output_path: Path):
    """Export analytics summary."""
    analytics_path = output_path / 'analytics'
    analytics_path.mkdir(parents=True, exist_ok=True)

    try:
        summary = analytics_engine.get_analytics_summary(unified_df)
        if summary:
            _write_json(analytics_path / 'summary.json', summary)
            click.echo(f"  Exported analytics summary")
    except Exception as e:
        click.echo(f"  Warning: Could not export analytics summary: {e}", err=True)


def _export_all_problems(unified_df: pd.DataFrame, output_path: Path):
    """Export all problems for client-side search/filtering."""
    problems_path = output_path / 'problems'
    problems_path.mkdir(parents=True, exist_ok=True)

    # Deduplicate by title
    problems = {}

    for _, row in unified_df.iterrows():
        title = row.get('title', '')
        if not title:
            continue

        if title in problems:
            # Aggregate: add company if not already present
            existing = problems[title]
            company = row.get('company', '')
            if company and company not in existing['companies']:
                existing['companies'].append(company)
            # Add timeframe
            timeframe = row.get('timeframe', '')
            if timeframe and timeframe not in existing['timeframes']:
                existing['timeframes'].append(timeframe)
            continue

        topics = _normalize_topics(row.get('topics'))
        company = row.get('company', '')
        timeframe = row.get('timeframe', '')

        problems[title] = {
            'title': str(title),
            'titleSlug': _slugify(str(title)),
            'difficulty': str(row.get('difficulty', 'UNKNOWN')).upper(),
            'frequency': float(row['frequency']) if pd.notna(row.get('frequency')) else None,
            'acceptanceRate': float(row['acceptance_rate']) if pd.notna(row.get('acceptance_rate')) else None,
            'link': row.get('leetcode_link') or row.get('link') or row.get('url'),
            'topics': topics,
            'companies': [company] if company else [],
            'companyCount': 1,
            'timeframes': [timeframe] if timeframe else [],
        }

    # Update company counts
    all_problems = list(problems.values())
    for problem in all_problems:
        problem['companyCount'] = len(problem['companies'])

    # Sort by company count (most popular first)
    all_problems.sort(key=lambda x: x['companyCount'], reverse=True)

    _write_json(problems_path / 'all.json', all_problems)
    click.echo(f"  Exported {len(all_problems)} unique problems")


def _export_study_plans(unified_df: pd.DataFrame, output_path: Path):
    """Export pre-generated study plans."""
    plans_path = output_path / 'study-plans'
    plans_path.mkdir(parents=True, exist_ok=True)

    # Get problem data with company counts
    problem_data = {}
    for _, row in unified_df.iterrows():
        title = row.get('title', '')
        if not title:
            continue

        if title not in problem_data:
            problem_data[title] = {
                'title': str(title),
                'titleSlug': _slugify(str(title)),
                'difficulty': str(row.get('difficulty', 'UNKNOWN')).upper(),
                'frequency': float(row['frequency']) if pd.notna(row.get('frequency')) else 0,
                'acceptanceRate': float(row['acceptance_rate']) if pd.notna(row.get('acceptance_rate')) else None,
                'link': row.get('leetcode_link') or row.get('link') or row.get('url'),
                'topics': _normalize_topics(row.get('topics')),
                'companies': set(),
            }
        problem_data[title]['companies'].add(row.get('company', ''))

    # Convert to list and add company count
    problems = list(problem_data.values())
    for p in problems:
        p['companyCount'] = len(p['companies'])
        p['companies'] = list(p['companies'])

    # Sort by popularity (company count * frequency)
    problems.sort(key=lambda x: x['companyCount'] * (x.get('frequency') or 0), reverse=True)

    # FAANG problems
    faang_companies = {'facebook', 'amazon', 'apple', 'netflix', 'google', 'meta', 'microsoft'}
    faang_problems = [p for p in problems if any(c.lower() in faang_companies for c in p['companies'])]

    # Generate study plans

    # 1. FAANG 4-week plan (top 80 problems, 4 per day)
    faang_plan = _create_study_plan(
        name="FAANG Interview Prep",
        description="Top interview problems from FAANG companies",
        duration_weeks=4,
        problems_per_day=4,
        problems=faang_problems[:112],  # 4 weeks * 7 days * 4 problems
        target_audience="intermediate"
    )
    _write_json(plans_path / 'faang-4-weeks.json', faang_plan)

    # 2. Beginner 2-week plan (Easy problems, 3 per day)
    easy_problems = [p for p in problems if p['difficulty'] == 'EASY']
    beginner_plan = _create_study_plan(
        name="Beginner Fundamentals",
        description="Easy problems to build a strong foundation",
        duration_weeks=2,
        problems_per_day=3,
        problems=easy_problems[:42],  # 2 weeks * 7 days * 3 problems
        target_audience="beginner"
    )
    _write_json(plans_path / 'beginner-2-weeks.json', beginner_plan)

    # 3. Advanced 3-week plan (Hard problems, 3 per day)
    hard_problems = [p for p in problems if p['difficulty'] == 'HARD']
    advanced_plan = _create_study_plan(
        name="Advanced Algorithms",
        description="Challenging problems for experienced engineers",
        duration_weeks=3,
        problems_per_day=3,
        problems=hard_problems[:63],  # 3 weeks * 7 days * 3 problems
        target_audience="advanced"
    )
    _write_json(plans_path / 'advanced-3-weeks.json', advanced_plan)

    # 4. Top 100 must-do problems
    top_100_plan = _create_study_plan(
        name="Top 100 Must-Do Problems",
        description="The most frequently asked problems across all companies",
        duration_weeks=4,
        problems_per_day=4,
        problems=problems[:100],
        target_audience="intermediate"
    )
    _write_json(plans_path / 'top-100-must-do.json', top_100_plan)

    click.echo(f"  Exported 4 study plans")


def _export_problem_previews(output_path: Path):
    """Export problem previews from LeetCode metadata."""
    problems_path = output_path / 'problems'
    problems_path.mkdir(parents=True, exist_ok=True)

    # Try to load leetcode_metadata.parquet
    metadata_path = Path('leetcode_metadata.parquet')
    if not metadata_path.exists():
        click.echo("  Warning: leetcode_metadata.parquet not found, skipping problem previews", err=True)
        click.echo("  Run 'python cli.py data fetch-leetcode-metadata' to fetch problem metadata", err=True)
        return

    try:
        df = pd.read_parquet(metadata_path)

        # Build a dictionary keyed by titleslug
        previews = {}
        for _, row in df.iterrows():
            slug = row.get('titleslug', '')
            if not slug:
                continue

            # Parse topic tags
            topic_tags = []
            raw_tags = row.get('topictags')
            if raw_tags is not None:
                if isinstance(raw_tags, (list, tuple)):
                    for tag in raw_tags:
                        if isinstance(tag, dict):
                            topic_tags.append({
                                'name': tag.get('name', ''),
                                'slug': tag.get('slug', '')
                            })
                        elif isinstance(tag, str):
                            topic_tags.append({'name': tag, 'slug': _slugify(tag)})

            preview = {
                'title': row.get('title', ''),
                'titleSlug': slug,
                'questionId': row.get('questionfrontendid'),
                'difficulty': str(row.get('difficulty', 'Unknown')),
                'content_html': row.get('content_html'),
                'content_text': row.get('content_text'),
                'topic_tags': topic_tags,
                'ac_rate': float(row['acrate']) if pd.notna(row.get('acrate')) else None,
                'likes': int(row['likes']) if pd.notna(row.get('likes')) else None,
                'dislikes': int(row['dislikes']) if pd.notna(row.get('dislikes')) else None,
                'is_paid_only': bool(row.get('ispaidonly', False)),
                'has_solution': bool(row.get('hassolution', False)),
                'has_video_solution': bool(row.get('hasvideosolution', False)),
            }
            previews[slug] = preview

        _write_json(problems_path / 'previews.json', previews)
        click.echo(f"  Exported {len(previews)} problem previews")

    except Exception as e:
        click.echo(f"  Warning: Could not export problem previews: {e}", err=True)


def _create_study_plan(name: str, description: str, duration_weeks: int,
                       problems_per_day: int, problems: List[Dict],
                       target_audience: str) -> Dict:
    """Create a structured study plan."""
    days = []
    problem_idx = 0

    for week in range(duration_weeks):
        for day in range(7):
            day_problems = []
            for _ in range(problems_per_day):
                if problem_idx < len(problems):
                    p = problems[problem_idx]
                    day_problems.append({
                        'title': p['title'],
                        'titleSlug': p['titleSlug'],
                        'difficulty': p['difficulty'],
                        'topics': p['topics'][:3] if p['topics'] else [],
                        'link': p.get('link'),
                    })
                    problem_idx += 1

            if day_problems:
                days.append({
                    'week': week + 1,
                    'day': day + 1,
                    'dayNumber': week * 7 + day + 1,
                    'problems': day_problems,
                })

    return {
        'id': _slugify(name),
        'name': name,
        'description': description,
        'durationWeeks': duration_weeks,
        'problemsPerDay': problems_per_day,
        'totalProblems': problem_idx,
        'targetAudience': target_audience,
        'createdAt': datetime.utcnow().isoformat() + 'Z',
        'days': days,
    }


if __name__ == '__main__':
    static()
