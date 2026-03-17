"""
Birth time rectification using KP (Krishnamurti Paddhati) and prenatal epoch.
Requires the full kundali result and a list of life events with dates.
"""

import swisseph as swe
from datetime import datetime, timedelta
from math import floor
from constants import ZODIAC_SIGNS, nakshatras, nakshatra_lord_index, dasha_lords, AYANAMSA_OPTIONS
from utils import get_sign, get_nakshatra, datetime_to_jd


# -------------------------------------------------------------------
# KP Helper: Sub-lords (9 divisions per nakshatra)
# -------------------------------------------------------------------
def get_nakshatra_sub_lord(lon):
    """
    Return the sub-lord for a given longitude (0-360).
    Each nakshatra (13°20′) divided into 9 parts ruled by Vimshottari dasha order.
    """
    nak_span = 360 / 27  # 13°20′
    sub_span = nak_span / 9  # ~1°28′
    nak_index = int(lon / nak_span) % 27
    sub_index = int((lon % nak_span) / sub_span) % 9
    print(f"Longitude {lon:.2f}: Nakshatra index {nak_index}, Sub-lord index {sub_index}, Sub-lord {dasha_lords[sub_index]}")
    return dasha_lords[sub_index]


def get_house_sub_lord(jd, lat, lon, house_num, ayanamsa_name="Lahiri"):
    """
    Compute sub-lord of house cusp longitude (KP method: cusp star sub-lord rules house).
    """
    ayanamsa_code = AYANAMSA_OPTIONS.get(ayanamsa_name, swe.SIDM_LAHIRI)
    swe.set_sid_mode(ayanamsa_code)
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', swe.FLG_SIDEREAL)
    house_cusp_lon = cusps[house_num - 1]  # 1-based to 0-index
    print(f"House {house_num}: Cusp longitude {house_cusp_lon:.2f}")
    return get_nakshatra_sub_lord(house_cusp_lon)


# -------------------------------------------------------------------
# Prenatal Epoch (simplified)
# -------------------------------------------------------------------
def get_prenatal_epoch_jd(birth_jd):
    """Approx conception: 273 days before birth (full-term gestation)."""
    return birth_jd - 273.0


def check_prenatal_epoch(birth_jd, birth_lat, birth_lon, ayanamsa_name="Lahiri"):
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
    print(f"Prenatal epoch: Moon longitude {moon_lon:.2f}, sign {moon_sign}, nakshatra index {moon_nak_idx}, nakshatra lord {moon_nak_lord_idx}")
    # Asc at birth
    cusps, ascmc = swe.houses_ex(birth_jd, birth_lat, birth_lon, b'W', swe.FLG_SIDEREAL)
    asc_lon = ascmc[0]
    asc_sign = get_sign(asc_lon)
    asc_nak_idx = int(asc_lon / (360 / 27)) % 27
    asc_nak_lord_idx = nakshatra_lord_index[asc_nak_idx]
    print(f"Birth: Asc longitude {asc_lon:.2f}, sign {asc_sign}, nakshatra index {asc_nak_idx}, nakshatra lord {asc_nak_lord_idx}")
    score = 0
    if moon_sign == asc_sign:
        print("Moon sign matches Asc sign: +2")
        score += 2
    if moon_nak_lord_idx == asc_nak_lord_idx:
        print("Moon nakshatra lord matches Asc nakshatra lord: +1")
        score += 1
    print(f"Prenatal epoch score: {score}")
    return score


# -------------------------------------------------------------------
# Main rectification
# -------------------------------------------------------------------
def rectify_birth_time(original_result, events):
    """
    Rectify birth time iterating ±1h in 2min steps.
    original_result: from calculate_kundali()
    events: [{'date': datetime, 'house': int, 'description': str, 'planets': list}]
    """
    orig_birth_dt = original_result['birth_datetime']
    orig_jd = original_result['birth_jd']
    lat = original_result.get('lat', 0.0)
    lon = original_result.get('lon', 0.0)
    ayanamsa = original_result.get('ayanamsa', 'Lahiri')
    print(f"Starting rectification: birth JD {orig_jd}, lat {lat}, lon {lon}, ayanamsa {ayanamsa}")
    step_minutes = 2
    step_days = step_minutes / (24 * 60)
    best_score = -1
    best_jd = orig_jd
    best_offset = 0
    for offset_minutes in range(-60, 61, step_minutes):
        test_jd = orig_jd + (offset_minutes / (24 * 60))
        score = 0
        print(f"\nTesting offset {offset_minutes} min (JD {test_jd:.5f})")
        # Prenatal epoch (weighted heavily)
        epoch_score = check_prenatal_epoch(test_jd, lat, lon, ayanamsa)
        score += epoch_score * 5
        print(f"Epoch score (x5): {epoch_score * 5}")
        # Life events: house sub-lord at birth time matches event planets?
        for event in events:
            house = event['house']
            sub_lord = get_house_sub_lord(test_jd, lat, lon, house, ayanamsa)
            expected_planets = event.get('planets', [])
            print(f"Event: house {house}, expected planets {expected_planets}, sub-lord {sub_lord}")
            if sub_lord in expected_planets:
                print(f"Sub-lord {sub_lord} matches event planets: +10")
                score += 10
        print(f"Total score for offset {offset_minutes}: {score}")
        if score > best_score:
            print(f"New best score: {score} at offset {offset_minutes}")
            best_score = score
            best_jd = test_jd
            best_offset = offset_minutes
    # Convert back
    best_dt = jd_to_datetime(best_jd)
    print(f"\nBest offset: {best_offset} min, corrected birth time: {best_dt}")
    return {
        'original_birth_time': orig_birth_dt.strftime('%Y-%m-%d %H:%M'),
        'corrected_birth_time': best_dt.strftime('%Y-%m-%d %H:%M'),
        'offset_minutes': best_offset,
        'confidence_score': best_score,
        'events_used': len(events)
    }


def jd_to_datetime(jd):
    """Julian Day to datetime (UT)."""
    y, m, d, h = swe.revjul(jd)
    hour = int(h)
    minute = int((h - hour) * 60)
    second = int(((h - hour) * 60 - minute) * 60)
    return datetime(y, m, d, hour, minute, second)


def datetime_from_jd(jd):
    """Alias for jd_to_datetime."""
    return jd_to_datetime(jd)

