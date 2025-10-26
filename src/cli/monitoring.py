"""CLI commands for monitoring and logging management."""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click

from src.config.settings import create_config
from src.monitoring import HealthMonitor, MetricsCollector, SystemMonitor


@click.group()
def monitoring():
    """Monitoring and logging management commands."""
    pass


@monitoring.command()
@click.option('--environment', '-e', default=None, help='Environment to use (development, production, test)')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'table']), help='Output format')
def health_check(environment: Optional[str], output_format: str):
    """Run health checks and display results."""
    try:
        config = create_config(environment)
        health_monitor = HealthMonitor(config)
        
        # Run health checks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            health_report = loop.run_until_complete(health_monitor.run_all_checks())
        finally:
            loop.close()
        
        if output_format == 'json':
            click.echo(json.dumps(health_report, indent=2))
        else:
            # Table format
            click.echo(f"Health Status: {health_report['status'].upper()}")
            click.echo(f"Timestamp: {health_report['timestamp']}")
            click.echo(f"Duration: {health_report['duration_ms']:.2f}ms")
            click.echo(f"Checks: {health_report['checks']['healthy']}/{health_report['checks']['total']} healthy")
            
            if health_report['details']['unhealthy']:
                click.echo("\nFailed Checks:")
                for check in health_report['details']['unhealthy']:
                    click.echo(f"  ❌ {check['name']}: {check['message']}")
            
            if health_report['details']['healthy']:
                click.echo("\nPassed Checks:")
                for check in health_report['details']['healthy']:
                    click.echo(f"  ✅ {check['name']}: {check['message']}")
        
        # Exit with error code if unhealthy
        if health_report['status'] != 'healthy':
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error running health checks: {e}", err=True)
        sys.exit(1)


@monitoring.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'summary']), help='Output format')
def system_info(environment: Optional[str], output_format: str):
    """Display system information and resource usage."""
    try:
        config = create_config(environment)
        metrics_collector = MetricsCollector(config)
        system_monitor = SystemMonitor(config, metrics_collector)
        
        system_info = system_monitor.get_system_info()
        
        if output_format == 'json':
            click.echo(json.dumps(system_info, indent=2))
        else:
            # Summary format
            click.echo("System Information")
            click.echo("=" * 50)
            
            if 'error' in system_info:
                click.echo(f"Error: {system_info['error']}")
                return
            
            # System resources
            sys_info = system_info['system']
            click.echo(f"CPU Usage: {sys_info['cpu']['percent']:.1f}%")
            click.echo(f"CPU Cores: {sys_info['cpu']['count']}")
            click.echo(f"Memory Usage: {sys_info['memory']['percent']:.1f}%")
            click.echo(f"Memory Available: {sys_info['memory']['available_gb']:.2f} GB")
            click.echo(f"Disk Usage: {sys_info['disk']['percent']:.1f}%")
            click.echo(f"Disk Free: {sys_info['disk']['free_gb']:.2f} GB")
            
            # Process info
            proc_info = system_info['process']
            click.echo(f"\nProcess Information")
            click.echo("-" * 30)
            click.echo(f"PID: {proc_info['pid']}")
            click.echo(f"CPU Usage: {proc_info['cpu_percent']:.1f}%")
            click.echo(f"Memory RSS: {proc_info['memory_info']['rss_mb']:.2f} MB")
            click.echo(f"Threads: {proc_info['num_threads']}")
            
            # Uptime
            uptime_seconds = system_info['uptime_seconds']
            uptime_str = str(timedelta(seconds=int(uptime_seconds)))
            click.echo(f"Uptime: {uptime_str}")
            
    except Exception as e:
        click.echo(f"Error getting system info: {e}", err=True)
        sys.exit(1)


@monitoring.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--category', '-c', type=click.Choice(['all', 'api', 'processing', 'cache']), 
              default='all', help='Metrics category to display')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'summary']), 
              help='Output format')
def metrics(environment: Optional[str], category: str, output_format: str):
    """Display collected metrics."""
    try:
        config = create_config(environment)
        metrics_collector = MetricsCollector(config)
        
        if category == 'all':
            metrics_data = metrics_collector.get_metrics_summary()
        elif category == 'api':
            metrics_data = metrics_collector.get_api_metrics()
        elif category == 'processing':
            metrics_data = metrics_collector.get_data_processing_metrics()
        elif category == 'cache':
            metrics_data = metrics_collector.get_cache_metrics()
        
        if output_format == 'json':
            click.echo(json.dumps(metrics_data, indent=2))
        else:
            # Summary format
            if not metrics_data.get('enabled', True):
                click.echo("Metrics collection is disabled")
                return
            
            click.echo(f"Metrics Summary - {category.title()}")
            click.echo("=" * 50)
            
            if 'counters' in metrics_data:
                click.echo("Counters:")
                for name, value in metrics_data['counters'].items():
                    click.echo(f"  {name}: {value}")
            
            if 'gauges' in metrics_data:
                click.echo("\nGauges:")
                for name, value in metrics_data['gauges'].items():
                    click.echo(f"  {name}: {value}")
            
            if 'timers' in metrics_data:
                click.echo("\nTimers:")
                for name, stats in metrics_data['timers'].items():
                    click.echo(f"  {name}:")
                    click.echo(f"    Count: {stats['count']}")
                    click.echo(f"    Avg: {stats['avg']:.2f}ms")
                    click.echo(f"    P95: {stats['p95']:.2f}ms")
            
    except Exception as e:
        click.echo(f"Error getting metrics: {e}", err=True)
        sys.exit(1)


@monitoring.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.option('--days', '-d', default=7, help='Number of days of logs to analyze')
@click.option('--level', '-l', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']), 
              help='Filter by log level')
def log_analysis(environment: Optional[str], days: int, level: Optional[str]):
    """Analyze log files for patterns and issues."""
    try:
        config = create_config(environment)
        log_config = config.get_logging_config()
        
        if not log_config['file']:
            click.echo("No log file configured")
            return
        
        log_file = Path(log_config['file'])
        if not log_file.exists():
            click.echo(f"Log file not found: {log_file}")
            return
        
        # Simple log analysis (in production, you'd want more sophisticated analysis)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        error_count = 0
        warning_count = 0
        info_count = 0
        total_lines = 0
        
        with open(log_file, 'r') as f:
            for line in f:
                total_lines += 1
                
                if level and level not in line:
                    continue
                
                if 'ERROR' in line:
                    error_count += 1
                elif 'WARNING' in line:
                    warning_count += 1
                elif 'INFO' in line:
                    info_count += 1
        
        click.echo(f"Log Analysis - Last {days} days")
        click.echo("=" * 40)
        click.echo(f"Total lines: {total_lines}")
        click.echo(f"Errors: {error_count}")
        click.echo(f"Warnings: {warning_count}")
        click.echo(f"Info: {info_count}")
        
        if error_count > 0:
            click.echo(f"\n⚠️  Found {error_count} errors in logs")
        
        if warning_count > 0:
            click.echo(f"⚠️  Found {warning_count} warnings in logs")
        
    except Exception as e:
        click.echo(f"Error analyzing logs: {e}", err=True)
        sys.exit(1)


@monitoring.command()
@click.option('--environment', '-e', default=None, help='Environment to use')
@click.confirmation_option(prompt='Are you sure you want to reset all metrics?')
def reset_metrics(environment: Optional[str]):
    """Reset all collected metrics."""
    try:
        config = create_config(environment)
        metrics_collector = MetricsCollector(config)
        
        metrics_collector.reset_metrics()
        click.echo("All metrics have been reset")
        
    except Exception as e:
        click.echo(f"Error resetting metrics: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    monitoring()