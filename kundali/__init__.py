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

Decision Engines:
    decisions.get_career_decision(result)
    decisions.get_marriage_decision(result)
    decisions.get_business_decision(result)
    decisions.get_health_decision(result)
    decisions.get_travel_decision(result)
    decisions.get_daily_guidance(result)
    decisions.get_compatibility_decision(result1, result2)
    decisions.get_education_decision(result)
    decisions.get_all_decisions(result)
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
from . import decisions
from .decisions import (
    get_career_decision,
    get_marriage_decision,
    get_business_decision,
    get_health_decision,
    get_travel_decision,
    get_daily_guidance,
    get_compatibility_decision,
    get_education_decision,
    get_all_decisions,
    get_all_decisions_with_compatibility,
)

__all__ = [
    "calculate_kundali",
    "AdvancedSpousePredictor",
    "calculate_pancha_pakshi",
    "generate_sky_chart",
    "get_ai_interpretation",
    "get_marriage_analysis",
    "get_career_analysis",
    "api",
    "decisions",
    # Decision engine functions
    "get_career_decision",
    "get_marriage_decision",
    "get_business_decision",
    "get_health_decision",
    "get_travel_decision",
    "get_daily_guidance",
    "get_compatibility_decision",
    "get_education_decision",
    "get_all_decisions",
    "get_all_decisions_with_compatibility",
]
