"""
Vedic Kundali — Vedic astrology calculation and prediction engine.

Public API:
    calculate_kundali(birth_date, birth_time, place, gender="Male")
    AdvancedSpousePredictor(chart_data)
"""

from .main import calculate_kundali
from .spouse.predictor import AdvancedSpousePredictor

__all__ = ["calculate_kundali", "AdvancedSpousePredictor"]
