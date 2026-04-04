"""
Vedic Kundali — Vedic astrology calculation and prediction engine.

Public API:
    calculate_kundali(birth_date, birth_time, place, gender="Male")
    AdvancedSpousePredictor(chart_data)
    calculate_pancha_pakshi(result)
    generate_sky_chart(result)
    get_ai_interpretation(result, question=None)
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

__all__ = [
    "calculate_kundali",
    "AdvancedSpousePredictor",
    "calculate_pancha_pakshi",
    "generate_sky_chart",
    "get_ai_interpretation",
    "get_marriage_analysis",
    "get_career_analysis",
]
