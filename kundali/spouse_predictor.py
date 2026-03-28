import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# spouse_predictor.py
"""
Legacy entry point. Re-exports the main class and functions from the new modular package.
"""
from spouse.predictor import AdvancedSpousePredictor
from spouse.marriage_date import find_marriage_date

__all__ = ["AdvancedSpousePredictor", "find_marriage_date"]
