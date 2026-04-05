"""
Vedic Kundali — Vedic astrology calculation and prediction engine.

Public API (low-level):
    calculate_kundali(birth_date, birth_time, place, gender="Male")
    AdvancedSpousePredictor(chart_data)

GUI-ready API (recommended for frontends):
    api.calculate(birth_date, birth_time, place, ...)
    api.serialize_result(result)
    api.get_spouse_prediction(chart_data)
    api.get_matching(chart1, chart2)
"""

from .main import calculate_kundali
from .spouse.predictor import AdvancedSpousePredictor
from .pancha_pakshi import calculate_pancha_pakshi
from .sky_chart import generate_sky_chart
from .ai_astrologer import (
    get_ai_interpretation,
    get_marriage_analysis,
    get_career_analysis,
)
from . import api

__all__ = [
    "calculate_kundali",
    "AdvancedSpousePredictor",
    "calculate_pancha_pakshi",
    "generate_sky_chart",
    "get_ai_interpretation",
    "get_marriage_analysis",
    "get_career_analysis",
    "api",
]
