#!/usr/bin/env python3
"""
GymIntel - Main Entry Point
Comprehensive Gym Discovery CLI Tool
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gym_finder import main

if __name__ == "__main__":
    main()