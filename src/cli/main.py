"""Main CLI entry point for LeetCode Analytics API."""

import click

from .data_cli import data
from .monitoring import monitoring
from .analytics_cli import analytics
from .static_export import static


@click.group()
@click.version_option(version='1.0.0', prog_name='LeetCode Analytics CLI')
def cli():
    """LeetCode Analytics API Command Line Interface.

    This CLI provides commands for data loading, processing, validation,
    and system monitoring for the LeetCode Analytics API.
    """
    pass


# Add command groups
cli.add_command(data)
cli.add_command(monitoring)
cli.add_command(analytics)
cli.add_command(static)


if __name__ == '__main__':
    cli()
