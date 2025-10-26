"""Analytics-focused CLI commands for debugging correlations and insights."""

from __future__ import annotations

import json
from typing import Dict, Iterable, List, Tuple

import click

from ..analytics.analytics_engine import AnalyticsEngine
from ..config.settings import config
from ..services.cache_manager import CacheManager
from ..services.csv_discovery import CSVDiscovery
from ..services.csv_loader import CSVLoader
from ..services.data_processor import DataProcessor
from ..services.dataset_manager import DatasetManager


def _build_dataset_manager() -> DatasetManager:
    """Create a dataset manager matching the API dependency wiring."""
    cache_dir = config.get_config("CACHE_DIR", ".cache")
    root_path = config.get_config("DATA_ROOT_PATH", ".")
    max_workers = config.get_config("PARALLEL_WORKERS", 4)

    cache_manager = CacheManager(cache_dir=cache_dir)
    data_processor = DataProcessor(standardize_topics=True)
    csv_discovery = CSVDiscovery(root_directory=root_path)
    csv_loader = CSVLoader(max_workers=max_workers)

    return DatasetManager(cache_manager, data_processor, csv_discovery, csv_loader)


def _format_top_features(features: Dict[str, float], limit: int = 5) -> List[Tuple[str, float]]:
    """Return the features sorted by absolute contribution."""
    return sorted(features.items(), key=lambda item: abs(item[1]), reverse=True)[:limit]


@click.group()
def analytics():
    """Analytics debugging utilities."""


@analytics.command(name="inspect-correlations")
@click.option(
    "--company",
    "companies",
    multiple=True,
    required=True,
    help="Company to include in the analysis. Provide at least two; repeat flag for multiple companies."
)
@click.option(
    "--metric",
    default="composite",
    show_default=True,
    help="Correlation metric to use (composite, frequency, difficulty, topics, acceptance_rate)."
)
@click.option(
    "--top",
    default=5,
    show_default=True,
    help="Number of strongest correlations to print."
)
@click.option(
    "--force-refresh",
    is_flag=True,
    help="Force dataset refresh instead of using cached parquet." 
)
@click.option(
    "--as-json",
    is_flag=True,
    help="Output raw JSON for further processing."
)
def inspect_correlations(companies: Iterable[str], metric: str, top: int, force_refresh: bool, as_json: bool) -> None:
    """Inspect correlation scores and contributing feature blocks for selected companies."""
    selected_companies = list(dict.fromkeys([c.strip() for c in companies if c and c.strip()]))

    if len(selected_companies) < 2:
        raise click.UsageError("Please provide at least two distinct companies using --company.")

    dataset_manager = _build_dataset_manager()
    dataset = dataset_manager.get_unified_dataset(force_refresh=force_refresh)

    if dataset is None or dataset.empty:
        raise click.ClickException("Unified dataset is empty. Run the data refresh command first.")

    missing = sorted(set(selected_companies) - set(dataset['company'].unique()))
    if missing:
        raise click.ClickException(f"Unknown companies: {', '.join(missing)}")

    engine = AnalyticsEngine()
    correlation_result = engine.get_company_correlations(
        dataset,
        metric=metric,
        include_features=True,
        companies_filter=selected_companies
    )

    if as_json:
        click.echo(json.dumps(correlation_result, indent=2, sort_keys=True, default=str))
        return

    click.echo(click.style("Correlation Debug Report", fg="cyan", bold=True))
    click.echo(f"Metric: {metric} | Companies: {', '.join(selected_companies)}")

    correlations = correlation_result.get('top_correlations', [])
    if not correlations:
        click.echo("No correlations available for the selected companies.")
        return

    click.echo()
    click.echo(click.style("Top Pair Similarities", fg="green", bold=True))
    for entry in correlations[:top]:
        comp1 = entry['company1']
        comp2 = entry['company2']
        score = entry['correlation']
        strength = entry.get('strength', 'unknown')
        components = entry.get('components', {})
        click.echo(f"• {comp1} ↔ {comp2}: {score:+.3f} ({strength})")
        if components:
            comp_summary = ', '.join(f"{name}={value:+.3f}" for name, value in components.items())
            click.echo(f"    breakdown: {comp_summary}")

    debug_info = correlation_result.get('debug', {})
    block_vectors = debug_info.get('feature_blocks', {})

    if block_vectors:
        click.echo()
        click.echo(click.style("Company Feature Deviations (standardized)", fg="yellow", bold=True))
        for company in selected_companies:
            click.echo(click.style(f"{company}", fg="white", bold=True))
            for block_name, block_data in block_vectors.items():
                company_vector = block_data.get(company)
                if not company_vector:
                    continue
                top_features = _format_top_features(company_vector)
                formatted = ', '.join(f"{feat}={value:+.3f}" for feat, value in top_features)
                click.echo(f"  {block_name}: {formatted}")
            click.echo()

    standardized = debug_info.get('standardized_features')
    if standardized:
        click.echo(click.style("Raw Standardized Feature Vector", fg="magenta"))
        for company, vector in standardized.items():
            trimmed = _format_top_features(vector)
            formatted = ', '.join(f"{feat}={value:+.3f}" for feat, value in trimmed)
            click.echo(f"  {company}: {formatted}")


@analytics.command(name="export-correlation-pairs")
@click.option(
    "--min-problems",
    default=100,
    show_default=True,
    type=int,
    help="Minimum number of problems per company to include in the export."
)
@click.option(
    "--metric",
    default="composite",
    show_default=True,
    type=click.Choice(["composite", "frequency", "difficulty", "topics", "acceptance_rate"], case_sensitive=False),
    help="Correlation metric to use when computing similarities."
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, writable=True, path_type=str),
    help="Optional file path to write the correlation pairs. Prints to stdout when omitted."
)
@click.option(
    "--force-refresh",
    is_flag=True,
    help="Force dataset refresh instead of using cached parquet."
)
def export_correlation_pairs(min_problems: int, metric: str, output: str | None, force_refresh: bool) -> None:
    """Export pairwise correlation scores for companies meeting a problem-count threshold."""

    dataset_manager = _build_dataset_manager()
    dataset = dataset_manager.get_unified_dataset(force_refresh=force_refresh)

    if dataset is None or dataset.empty:
        raise click.ClickException("Unified dataset is empty. Run the data refresh command first.")

    company_counts = dataset.groupby('company').size()
    eligible_companies = sorted(company_counts[company_counts >= min_problems].index.tolist())

    if len(eligible_companies) < 2:
        raise click.ClickException(
            f"Found only {len(eligible_companies)} companies with >= {min_problems} problems; need at least two."
        )

    engine = AnalyticsEngine()
    correlation_result = engine.get_company_correlations(
        dataset,
        metric=metric,
        include_features=False,
        companies_filter=eligible_companies
    )

    correlations = correlation_result.get('top_correlations', []) if correlation_result else []
    if not correlations:
        raise click.ClickException("No correlations available for the selected companies.")

    lines = [
        f"{entry['company1']},{entry['company2']},{entry['correlation']:.6f}"
        for entry in correlations
    ]

    header = f"# metric={metric} min_problems={min_problems} companies={len(eligible_companies)}"

    if output:
        try:
            with open(output, 'w', encoding='utf-8') as file_obj:
                file_obj.write(header + '\n')
                file_obj.write('\n'.join(lines))
        except OSError as exc:
            raise click.ClickException(f"Failed to write output file: {exc}") from exc
        click.echo(
            click.style(
                f"Wrote {len(lines)} correlation pairs for {len(eligible_companies)} companies to {output}",
                fg="green"
            )
        )
    else:
        click.echo(header)
        for line in lines:
            click.echo(line)
