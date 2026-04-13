"""
GUI-ready API layer for the Vedic Kundali engine.

All functions accept plain Python types and return JSON-serializable dicts.
No file I/O, no print statements — suitable for any frontend:
  - CLI (run.py)
  - Web (FastAPI / Flask)
  - Desktop GUI (Tkinter / PyQt / Electron)
  - Mobile (via JSON-RPC or REST)

Usage:
    from kundali.api import calculate, get_spouse_prediction, serialize_result

    result = calculate("1990-05-15", "08:30", "Mumbai, India")
    json_safe = serialize_result(result)
"""

import datetime


# ---------------------------------------------------------------------------
# JSON serializer — handles numpy, datetime, and other non-JSON types
# ---------------------------------------------------------------------------

def to_json(obj):
    """Recursively make *obj* JSON-serialisable."""
    try:
        import numpy as np
        _NP_TYPES = (np.integer, np.floating, np.bool_)
        _NP_ARRAY = np.ndarray
    except ImportError:
        _NP_TYPES = ()
        _NP_ARRAY = None

    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (int, float, str)):
        return obj
    if _NP_TYPES and isinstance(obj, _NP_TYPES):
        return obj.item()
    if _NP_ARRAY is not None and isinstance(obj, _NP_ARRAY):
        return obj.tolist()
    if isinstance(obj, dict):
        return {str(k): to_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_json(i) for i in obj]
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    try:
        return str(obj)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Planet name mapping
# ---------------------------------------------------------------------------

PLANET_FULL = {
    "Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury",
    "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn",
    "Ra": "Rahu", "Ke": "Ketu",
}


# ---------------------------------------------------------------------------
# Core API functions
# ---------------------------------------------------------------------------

def calculate(
    birth_date,
    birth_time,
    place,
    gender="Male",
    ayanamsa="Lahiri",
    name="",
    rectification_events=None,
    apply_rectification=False,
    rectification_min_confidence=75,
    latitude=None,
    longitude=None,
    timezone_name=None,
):
    """
    Calculate a complete Vedic kundali.

    Args:
        birth_date: "YYYY-MM-DD"
        birth_time: "HH:MM" (24-hour)
        place: "City, Country"
        gender: "Male" or "Female"
        ayanamsa: Ayanamsa name (default "Lahiri")
        name: Native's name (optional, stored in result)
        rectification_events: optional life events for birth-time rectification
        apply_rectification: auto-apply strong rectification before returning
        rectification_min_confidence: minimum confidence score required for auto-apply
        latitude: optional exact birth latitude
        longitude: optional exact birth longitude
        timezone_name: optional IANA timezone like Asia/Kolkata

    Returns:
        dict: Raw kundali result (pass to serialize_result() for JSON-safe output).
    """
    from .main import calculate_kundali
    result = calculate_kundali(
        birth_date,
        birth_time,
        place,
        gender=gender,
        ayanamsa_name=ayanamsa,
        name=name or "native",
        rectification_events=rectification_events,
        apply_rectification=apply_rectification,
        rectification_min_confidence=rectification_min_confidence,
        latitude=latitude,
        longitude=longitude,
        timezone_name=timezone_name,
    )
    return result


def get_spouse_prediction(chart_data):
    """
    Run the advanced spouse predictor on a calculated chart.

    Args:
        chart_data: dict returned by calculate()

    Returns:
        dict: Spouse prediction result with keys like
              'appearance', 'personality', 'timing', 'manglik', etc.
    """
    from .spouse.predictor import AdvancedSpousePredictor
    predictor = AdvancedSpousePredictor(chart_data)
    return {
        "prediction": predictor.prediction,
        "report_text": predictor.generate_report(),
    }


def get_matching(chart1, chart2):
    """
    Compute Ashtakoot Guna Milan + extra dosha checks between two charts.

    Args:
        chart1, chart2: dicts returned by calculate()

    Returns:
        dict with keys: person1, person2, ashtakoot, extra_doshas
    """
    from .kundali_matching import match_kundalis
    from .constants import zodiac_signs

    nak1 = chart1.get("moon_nakshatra", "")
    sign1 = chart1.get("moon_sign", "")
    nak2 = chart2.get("moon_nakshatra", "")
    sign2 = chart2.get("moon_sign", "")

    # Use the full matching module
    try:
        full_report = match_kundalis(chart1, chart2)
    except Exception:
        full_report = {}

    return {
        "person1": {"moon_sign": sign1, "moon_nakshatra": nak1},
        "person2": {"moon_sign": sign2, "moon_nakshatra": nak2},
        "full_report": to_json(full_report),
    }


# ---------------------------------------------------------------------------
# Serializer — convert raw kundali result to JSON-safe summary
# ---------------------------------------------------------------------------

def serialize_result(result):
    """
    Convert the full kundali result dict to a JSON-serialisable summary.

    Suitable for sending over HTTP, storing in a database, or rendering in a GUI.
    """
    out = {}

    # Basic birth details
    for key in ("name", "birth_date", "birth_time", "birth_place", "birth_place_normalized",
                "birth_place_input", "birth_time_original_input", "gender",
                "ayanamsa", "lagna_sign", "lagna_deg", "moon_sign",
                "moon_nakshatra", "sade_sati", "birth_year", "birth_month",
                "birth_day", "lat", "lon", "timezone", "location_source", "timezone_source"):
        out[key] = to_json(result.get(key))

    # Panchanga
    out["panchanga"] = to_json(result.get("panchanga", {}))

    # Planets summary
    planets_raw = result.get("planets", {})
    planets_out = {}
    for code, pdata in planets_raw.items():
        if not isinstance(pdata, dict):
            continue
        planets_out[PLANET_FULL.get(code, code)] = {
            "sign":       to_json(pdata.get("sign")),
            "deg":        to_json(pdata.get("deg")),
            "full_lon":   to_json(pdata.get("full_lon")),
            "nakshatra":  to_json(pdata.get("nakshatra")),
            "dignity":    to_json(pdata.get("dignity")),
            "retro":      to_json(pdata.get("retro")),
            "combust":    to_json(pdata.get("combust")),
            "navamsa_sign": to_json(pdata.get("navamsa_sign")),
        }
    out["planets"] = planets_out

    # Houses
    houses_raw = result.get("houses", {})
    out["houses"] = {
        str(h): [PLANET_FULL.get(p, p) for p in pl if p != "Asc"]
        for h, pl in houses_raw.items()
    }

    # Yogas
    yogas_raw = result.get("yogas", [])
    yogas_out = []
    for y in yogas_raw:
        if isinstance(y, dict):
            yogas_out.append({
                "name":        to_json(y.get("name", y.get("yoga", ""))),
                "description": to_json(y.get("description", y.get("planets", ""))),
                "strength":    to_json(y.get("strength", y.get("score", ""))),
            })
        else:
            yogas_out.append({"name": str(y), "description": "", "strength": ""})
    out["yogas"] = yogas_out

    # Vimshottari dasha summary
    vims = result.get("vimshottari", {})
    cur_md = vims.get("current_md")
    cur_ad = vims.get("current_ad")
    vims_pd = result.get("vimshottari_pd", {}) or {}
    cur_pd = vims_pd.get("current_pd")

    def _period(d):
        if not d:
            return None
        # current_md / current_ad may be plain strings (lord name) rather than dicts
        if isinstance(d, str):
            return {"lord": d, "start": None, "end": None}
        return {
            "lord":  to_json(d.get("lord", d.get("dasha_lord"))),
            "start": to_json(d.get("start_date", d.get("start"))),
            "end":   to_json(d.get("end_date", d.get("end"))),
        }

    out["vimshottari"] = {
        "starting_lord":          to_json(vims.get("starting_lord")),
        "balance_at_birth_years": to_json(vims.get("balance_at_birth_years")),
        "current_md": _period(cur_md),
        "current_ad": _period(cur_ad),
        "current_pd": _period(cur_pd),
        "mahadasas":  to_json([
            {k: v for k, v in md.items() if k != "antardashas"}
            for md in (vims.get("mahadasas") or [])
        ]),
    }

    # Transits
    transits_raw = result.get("transits", {})
    out["transits"] = {
        PLANET_FULL.get(code, code): {
            "sign":            to_json(t.get("sign")),
            "house_from_moon": to_json(t.get("house_from_moon")),
            "effect":          to_json(t.get("effect")),
        }
        for code, t in transits_raw.items()
        if isinstance(t, dict)
    }

    # Muhurtha
    muh = result.get("muhurtha", {})
    if isinstance(muh, dict):
        out["muhurtha_score"] = to_json(muh.get("score", muh.get("total_score")))
        out["muhurtha_summary"] = to_json(muh.get("summary", muh.get("verdict", "")))
    else:
        out["muhurtha_score"] = None
        out["muhurtha_summary"] = None

    # Tajika
    tajika = result.get("tajika", {})
    if isinstance(tajika, dict):
        out["tajika"] = {
            "solar_return_year": to_json(tajika.get("solar_return_year")),
            "muntha_sign":       to_json(tajika.get("muntha_sign")),
            "year_verdict":      to_json(tajika.get("year_verdict", tajika.get("verdict"))),
        }
    else:
        out["tajika"] = {}

    # Yogini dasha
    yogini = result.get("yogini_dasha", {})
    out["yogini_current"] = to_json(yogini.get("current")) if isinstance(yogini, dict) else None

    # Neecha bhanga
    out["neecha_bhanga_planets"] = [
        PLANET_FULL.get(p, p) for p in (result.get("neecha_bhanga_planets") or [])
    ]

    # Jaimini
    jaimini = result.get("jaimini", {})
    if isinstance(jaimini, dict):
        out["atmakaraka"] = to_json(jaimini.get("atmakaraka"))
        out["karakamsa_lagna"] = to_json(jaimini.get("karakamsa_lagna"))

    # Problems / Doshas
    out["problems"] = to_json(result.get("problems", []))

    # Accuracy metadata
    out["birth_time_rectification"] = to_json(result.get("birth_time_rectification", {}))
    out["input_quality"] = to_json(result.get("input_quality", {}))

    # Unified life analysis
    try:
        life_analysis = get_life_analysis(result)
        out["life_analysis"] = life_analysis
    except Exception:
        life_analysis = {}
        out["life_analysis"] = {}

    try:
        from .decisions import get_all_decisions

        out["decision_confidence_summary"] = to_json(
            get_all_decisions(result).get("confidence_summary", {})
        )
    except Exception:
        out["decision_confidence_summary"] = {}

    # Final analysis text
    out["final_analysis"] = to_json(result.get("final_analysis", ""))

    # Chart file paths (GUI can use these to display)
    out["north_chart_path"] = to_json(result.get("north_chart_path", ""))
    out["sky_chart_path"] = to_json(result.get("sky_chart_path", ""))
    out["pdf_report_path"] = to_json(result.get("pdf_report_path", ""))

    return out


# ---------------------------------------------------------------------------
# Decision Engine API — actionable life guidance
# ---------------------------------------------------------------------------

def get_career_decision(chart_data):
    """Career guidance from the chart (10th house, D10, Atmakaraka)."""
    from .decisions import get_career_decision as _career
    return to_json(_career(chart_data))


def get_marriage_decision(chart_data):
    """Marriage timing and readiness analysis."""
    from .decisions import get_marriage_decision as _marriage
    return to_json(_marriage(chart_data))


def get_business_decision(chart_data):
    """Business, investment, and financial timing guidance."""
    from .decisions import get_business_decision as _business
    return to_json(_business(chart_data))


def get_health_decision(chart_data):
    """Health vulnerabilities and risky periods."""
    from .decisions import get_health_decision as _health
    return to_json(_health(chart_data))


def get_travel_decision(chart_data):
    """Travel and relocation guidance (directions, foreign settlement)."""
    from .decisions import get_travel_decision as _travel
    return to_json(_travel(chart_data))


def get_daily_guidance(chart_data):
    """Daily/weekly guidance from transits, dasha, and panchanga."""
    from .decisions import get_daily_guidance as _daily
    return to_json(_daily(chart_data))


def run_benchmark(cases=None, benchmark_path=None):
    """Run benchmark cases from a list or a JSON file path."""
    from .benchmarking import load_benchmark_cases, run_benchmark_suite

    if benchmark_path:
        cases = load_benchmark_cases(benchmark_path)
    return to_json(run_benchmark_suite(cases or []))


def get_compatibility_decision(chart1, chart2):
    """Compatibility analysis between two charts."""
    from .decisions import get_compatibility_decision as _compat
    return to_json(_compat(chart1, chart2))


def get_education_decision(chart_data):
    """Education field recommendations and timing."""
    from .decisions import get_education_decision as _edu
    return to_json(_edu(chart_data))


def get_life_analysis(chart_data):
    """Unified life-domain synthesis with timing and longevity-risk overview."""
    from .decisions import get_life_analysis as _life
    return to_json(_life(chart_data))


def get_all_decisions(chart_data):
    """All single-chart decision categories at once."""
    from .decisions import get_all_decisions as _all
    return to_json(_all(chart_data))


def get_all_decisions_with_compatibility(chart1, chart2):
    """All decision categories including compatibility."""
    from .decisions import get_all_decisions_with_compatibility as _all_compat
    return to_json(_all_compat(chart1, chart2))
