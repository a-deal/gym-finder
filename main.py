#!/usr/bin/env python3
"""
GymIntel - Main Entry Point
A comprehensive gym discovery platform with confidence scoring.
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from gym_finder import main  # noqa: E402

if __name__ == "__main__":
    main()
