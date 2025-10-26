#!/usr/bin/env python3
"""
LeetCode Analytics API Startup Script

This script provides a convenient entry point for starting the API server.
It handles Python path setup and starts the FastAPI server.

Usage:
    python start_api.py
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Now import and run the main application
from main import main

if __name__ == '__main__':
    main()