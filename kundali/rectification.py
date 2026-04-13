"""
Birth time rectification using KP (Krishnamurti Paddhati) and prenatal epoch.
Requires the full kundali result and a list of life events with dates.
"""

import swisseph as swe
from datetime import datetime, timedelta, timezone
import pytz
from .constants import (
    nakshatra_lord_index,
    dasha_lords,
    AYANAMSA_OPTIONS,
    short_to_full,
)
from .utils import get_sign


_PLANET_LOOKUP = {code.lower(): code for code in short_to_full}
_PLANET_LOOKUP.update({name.lower(): code for code, name in short_to_full.items()})


def _log(verbose, message):
    if verbose:
        print(message)


def _normalize_expected_planets(values):
    normalized = []
    for value in values or []:
        code = _PLANET_LOOKUP.get(str(value or "").strip().lower())
        if code:
            normalized.append(code)
    return normalized


def _confidence_label(score, events_used):
    if events_used <= 0 or score <= 0:
        return "Insufficient Data"
    if events_used < 3:
        if score >= 75:
            return "Moderate"
        if score >= 50:
            return "Tentative"
        return "Low"
    if score >= 85:
        return "High"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Moderate"
    return "Low"


# -------------------------------------------------------------------
# KP Helper: Sub-lords (9 divisions per nakshatra)
# -------------------------------------------------------------------
def get_nakshatra_sub_lord(lon, verbose=False):
    """
    Return the sub-lord for a given longitude (0-360).
    Each nakshatra (13°20′) divided into 9 parts ruled by Vimshottari dasha order.
    """
    nak_span = 360 / 27  # 13°20′
    sub_span = nak_span / 9  # ~1°28′
    nak_index = int(lon / nak_span) % 27
    sub_index = int((lon % nak_span) / sub_span) % 9
    _log(
        verbose,
        f"Longitude {lon:.2f}: Nakshatra index {nak_index}, Sub-lord index {sub_index}, Sub-lord {dasha_lords[sub_index]}"
    )
    return dasha_lords[sub_index]


def get_house_sub_lord(jd, lat, lon, house_num, ayanamsa_name="Lahiri", verbose=False):
    """
    Compute sub-lord of house cusp longitude (KP method: cusp star sub-lord rules house).
    """
    ayanamsa_code = AYANAMSA_OPTIONS.get(ayanamsa_name, swe.SIDM_LAHIRI)
    swe.set_sid_mode(ayanamsa_code)
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    house_cusp_lon = cusps[house_num - 1]  # 1-based to 0-index
    _log(verbose, f"House {house_num}: Cusp longitude {house_cusp_lon:.2f}")
    return get_nakshatra_sub_lord(house_cusp_lon, verbose=verbose)


# -------------------------------------------------------------------
# Prenatal Epoch (simplified)
# -------------------------------------------------------------------
def get_prenatal_epoch_jd(birth_jd):
    """Approx conception: 273 days before birth (full-term gestation)."""
    return birth_jd - 273.0


def check_prenatal_epoch(birth_jd, birth_lat, birth_lon, ayanamsa_name="Lahiri", verbose=False):
    """
    Score prenatal epoch: Moon at conception ~ Asc at birth (sign/nakshatra lord).
    """
    conception_jd = get_prenatal_epoch_jd(birth_jd)
    ayanamsa_code = AYANAMSA_OPTIONS.get(ayanamsa_name, swe.SIDM_LAHIRI)
    swe.set_sid_mode(ayanamsa_code)
    # Moon at conception
    moon_lon = swe.calc_ut(conception_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    moon_sign = get_sign(moon_lon)
    moon_nak_idx = int(moon_lon / (360 / 27)) % 27
    moon_nak_lord_idx = nakshatra_lord_index[moon_nak_idx]
    _log(
        verbose,
        f"Prenatal epoch: Moon longitude {moon_lon:.2f}, sign {moon_sign}, nakshatra index {moon_nak_idx}, nakshatra lord {moon_nak_lord_idx}"
    )
    # Asc at birth
    cusps, ascmc = swe.houses_ex(birth_jd, birth_lat, birth_lon, b"W", swe.FLG_SIDEREAL)
    asc_lon = ascmc[0]
    asc_sign = get_sign(asc_lon)
    asc_nak_idx = int(asc_lon / (360 / 27)) % 27
    asc_nak_lord_idx = nakshatra_lord_index[asc_nak_idx]
    _log(
        verbose,
        f"Birth: Asc longitude {asc_lon:.2f}, sign {asc_sign}, nakshatra index {asc_nak_idx}, nakshatra lord {asc_nak_lord_idx}"
    )
    score = 0
    if moon_sign == asc_sign:
        _log(verbose, "Moon sign matches Asc sign: +2")
        score += 2
    if moon_nak_lord_idx == asc_nak_lord_idx:
        _log(verbose, "Moon nakshatra lord matches Asc nakshatra lord: +1")
        score += 1
    _log(verbose, f"Prenatal epoch score: {score}")
    return score


# -------------------------------------------------------------------
# Main rectification
# -------------------------------------------------------------------
def rectify_birth_time(
    original_result,
    events,
    *,
    step_minutes=2,
    search_window_minutes=60,
    verbose=False,
):
    """
    Rectify birth time iterating ±1h in 2min steps.
    original_result: from calculate_kundali()
    events: [{'date': datetime, 'house': int, 'description': str, 'planets': list}]
    """
    orig_birth_dt = original_result["birth_datetime"]
    orig_jd = original_result["birth_jd"]
    lat = original_result.get("lat", 0.0)
    lon = original_result.get("lon", 0.0)
    ayanamsa = original_result.get("ayanamsa", "Lahiri")
    tz_name = original_result.get("timezone")
    parsed_events = []
    for event in events or []:
        try:
            house = int(event.get("house"))
        except (TypeError, ValueError, AttributeError):
            continue
        if not 1 <= house <= 12:
            continue
        expected_planets = _normalize_expected_planets(event.get("planets", []))
        parsed_events.append(
            {
                "house": house,
                "description": str(event.get("description", "")).strip(),
                "expected_planets": expected_planets,
            }
        )

    if not parsed_events:
        return {
            "original_birth_time": orig_birth_dt.strftime("%Y-%m-%d %H:%M"),
            "corrected_birth_time": orig_birth_dt.strftime("%Y-%m-%d %H:%M"),
            "corrected_birth_time_input": orig_birth_dt.strftime("%H:%M"),
            "corrected_birth_datetime_local": orig_birth_dt.isoformat(),
            "corrected_birth_datetime_utc": orig_birth_dt.astimezone(pytz.utc).isoformat(),
            "offset_minutes": 0,
            "raw_score": 0,
            "confidence_score": 0,
            "confidence_label": "Insufficient Data",
            "score_margin": 0,
            "events_used": 0,
            "search_window_minutes": search_window_minutes,
            "step_minutes": step_minutes,
            "applied": False,
            "applied_reason": "No valid life events were provided for rectification.",
        }

    _log(
        verbose,
        f"Starting rectification: birth JD {orig_jd}, lat {lat}, lon {lon}, ayanamsa {ayanamsa}"
    )
    best_score = -1
    best_jd = orig_jd
    best_offset = 0
    runner_up_score = None
    for offset_minutes in range(-search_window_minutes, search_window_minutes + 1, step_minutes):
        test_jd = orig_jd + (offset_minutes / (24 * 60))
        score = 0
        _log(verbose, f"\nTesting offset {offset_minutes} min (JD {test_jd:.5f})")
        # Prenatal epoch (weighted heavily)
        epoch_score = check_prenatal_epoch(test_jd, lat, lon, ayanamsa, verbose=verbose)
        score += epoch_score * 5
        _log(verbose, f"Epoch score (x5): {epoch_score * 5}")
        # Life events: house sub-lord at birth time matches event planets?
        for event in parsed_events:
            house = event["house"]
            sub_lord = get_house_sub_lord(
                test_jd, lat, lon, house, ayanamsa, verbose=verbose
            )
            expected_planets = event["expected_planets"]
            _log(
                verbose,
                f"Event: house {house}, expected planets {expected_planets}, sub-lord {sub_lord}"
            )
            if sub_lord in expected_planets:
                _log(verbose, f"Sub-lord {sub_lord} matches event planets: +10")
                score += 10
        _log(verbose, f"Total score for offset {offset_minutes}: {score}")
        if score > best_score:
            if best_score >= 0:
                runner_up_score = best_score if runner_up_score is None else max(runner_up_score, best_score)
            _log(verbose, f"New best score: {score} at offset {offset_minutes}")
            best_score = score
            best_jd = test_jd
            best_offset = offset_minutes
        elif runner_up_score is None or score > runner_up_score:
            runner_up_score = score
    # Convert back
    best_dt = jd_to_datetime(best_jd, tz_name=tz_name)
    max_score = 15 + (len(parsed_events) * 10)
    confidence_score = int(round((best_score / max_score) * 100)) if max_score > 0 else 0
    if len(parsed_events) < 3:
        confidence_score = min(confidence_score, 60)
    score_margin = max(0, best_score - (runner_up_score if runner_up_score is not None else 0))
    _log(verbose, f"\nBest offset: {best_offset} min, corrected birth time: {best_dt}")
    return {
        "original_birth_time": orig_birth_dt.strftime("%Y-%m-%d %H:%M"),
        "corrected_birth_time": best_dt.strftime("%Y-%m-%d %H:%M"),
        "corrected_birth_time_input": best_dt.strftime("%H:%M"),
        "corrected_birth_datetime_local": best_dt.isoformat(),
        "corrected_birth_datetime_utc": best_dt.astimezone(pytz.utc).isoformat(),
        "offset_minutes": best_offset,
        "raw_score": best_score,
        "confidence_score": confidence_score,
        "confidence_label": _confidence_label(confidence_score, len(parsed_events)),
        "score_margin": score_margin,
        "events_used": len(parsed_events),
        "search_window_minutes": search_window_minutes,
        "step_minutes": step_minutes,
        "applied": False,
        "applied_reason": "",
    }


def jd_to_datetime(jd, tz_name=None):
    """Julian Day to timezone-aware datetime."""
    y, m, d, hh, mm, sec = swe.jdut1_to_utc(jd, swe.GREG_CAL)
    microseconds = int(round((sec % 1) * 1_000_000))
    dt_utc = datetime(y, m, d, hh, mm, int(sec), microseconds, tzinfo=timezone.utc)
    if tz_name:
        try:
            return dt_utc.astimezone(pytz.timezone(tz_name))
        except Exception:
            pass
    return dt_utc


def datetime_from_jd(jd):
    """Alias for jd_to_datetime."""
    return jd_to_datetime(jd)
