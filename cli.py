#!/usr/bin/env python3
"""
LeetCode Analytics API CLI Entry Point

This script provides a convenient entry point for the CLI commands.
You can run it directly or use it as a module.

Usage:
    python cli.py data load --help
    python cli.py monitoring health-check
    python cli.py --help
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.cli.main import cli

if __name__ == '__main__':
    cli()