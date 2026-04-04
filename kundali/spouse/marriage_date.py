# spouse/marriage_date.py
"""
Re-export marriage date prediction functions from the original module.
All logic remains in marriage_date_prediction.py.
"""
from ..marriage_date_prediction import (
    find_marriage_date,
    evaluate_marriage_date,
    get_moon_transit_days,
    get_sidereal_lon,
    approximate_lahiri_ayanamsa,
    check_nadi_promise,
    format_prediction_result,
)
