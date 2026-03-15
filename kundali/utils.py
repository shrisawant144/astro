# utils.py
"""
Utility functions for Vedic astrology calculations: sign, nakshatra, dignity,
location, time conversion, divisional charts, and Panchanga.
"""

import re
import swisseph as swe
import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from constants import (
    zodiac_signs,
    nakshatras,
    sign_lords,
    dignity_table,
    TITHI_NAMES,
    VARA_NAMES,
    YOGA_NAMES,
    KARANA_REPEATING,
    COMBUSTION_ORBS,
)


def get_sign(deg):
    """Return zodiac sign name for a given ecliptic longitude (0-360)."""
    return zodiac_signs[int(deg / 30) % 12]


def get_nakshatra(deg):
    """Return nakshatra name for a given longitude."""
    nak_index = int(deg / (360 / 27)) % 27
    return nakshatras[nak_index]


def get_nakshatra_progress(deg):
    """Return progress (0-1) through the current nakshatra."""
    nak_span = 360 / 27
    nak_start = int(deg / nak_span) * nak_span
    return (deg - nak_start) / nak_span


def get_dignity(planet, sign):
    """Determine the dignity of a planet in a sign (Exalt, Own, Deb, Friend, Enemy, Neutral)."""
    if planet not in dignity_table:
        return ""
    d = dignity_table[planet]
    own_signs = d.get("own", [])
    if isinstance(own_signs, str):
        own_signs = [own_signs]
    if sign in own_signs:
        return "Own"
    exalt_str = d.get("exalt", "")
    if exalt_str:
        exalt_signs = [s.strip() for s in exalt_str.split("/") if s.strip()]
        if sign in exalt_signs:
            return "Exalt"
    deb_str = d.get("deb", "")
    if deb_str:
        deb_signs = [s.strip() for s in deb_str.split("/") if s.strip()]
        if sign in deb_signs:
            return "Debilitated"

    # Natural friendship
    NATURAL_FRIENDS = {
        "Su": {"Mo", "Ma", "Ju"},
        "Mo": {"Su", "Me"},
        "Ma": {"Su", "Mo", "Ju"},
        "Me": {"Su", "Ve"},
        "Ju": {"Su", "Mo", "Ma"},
        "Ve": {"Me", "Sa"},
        "Sa": {"Me", "Ve"},
    }
    NATURAL_ENEMIES = {
        "Su": {"Ve", "Sa"},
        "Mo": set(),
        "Ma": {"Me"},
        "Me": {"Mo"},
        "Ju": {"Me", "Ve"},
        "Ve": {"Su", "Mo"},
        "Sa": {"Su", "Mo", "Ma"},
    }
    if planet in ("Ra", "Ke") or sign not in sign_lords:
        return ""
    sign_lord = sign_lords[sign]
    if sign_lord == planet:
        return ""  # should have been caught by "Own", but safety
    friends = NATURAL_FRIENDS.get(planet, set())
    enemies = NATURAL_ENEMIES.get(planet, set())
    if sign_lord in friends:
        return "Friend"
    elif sign_lord in enemies:
        return "Enemy"
    else:
        return "Neutral"


def get_lat_lon(place):
    """Return (latitude, longitude) for a place string using Nominatim."""
    geo = Nominatim(user_agent="vedic_kundali_cli")
    loc = geo.geocode(place, timeout=15)
    if not loc:
        raise ValueError(
            f"Location not found: {place}. Try 'Mumbai, Maharashtra, India'"
        )
    return loc.latitude, loc.longitude


def is_retrograde(speed):
    """Return True if planetary speed indicates retrograde motion."""
    return speed < 0


def get_house_from_sign(asc_sign_idx, planet_sign_idx):
    """Calculate house number (1-12) of a planet given Lagna index and planet sign index."""
    return ((planet_sign_idx - asc_sign_idx) % 12) + 1


def datetime_to_jd(dt):
    """Convert a datetime object to Julian Day (UT)."""
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)


def check_combustion(planet_code, planet_full_lon, sun_full_lon, is_retro):
    """Return True if planet is combust (within orb of Sun)."""
    if planet_code not in COMBUSTION_ORBS:
        return False
    orb_direct, orb_retro = COMBUSTION_ORBS[planet_code]
    orb = orb_retro if is_retro else orb_direct
    diff = abs((planet_full_lon - sun_full_lon + 360) % 360)
    if diff > 180:
        diff = 360 - diff
    return diff <= orb


def houses_are_consecutive(house_set):
    """Return True if the given set of house numbers (1-12) form a gapless consecutive sequence,
    accounting for zodiac wrap-around."""
    houses = sorted(house_set)
    n = len(houses)
    if n < 2:
        return True
    for start_i in range(n):
        ok = True
        for j in range(1, n):
            diff = (houses[(start_i + j) % n] - houses[(start_i + j - 1) % n]) % 12
            if diff != 1:
                ok = False
                break
        if ok:
            return True
    return False


def get_panchanga(birth_jd, sun_lon, moon_lon):
    """Return birth Panchanga: Tithi, Vara, Yoga, Karana."""
    # Tithi
    tithi_num = int((moon_lon - sun_lon) % 360 / 12)  # 0-29
    tithi = TITHI_NAMES[tithi_num]
    # Vara (day of week)
    vara_idx = int(birth_jd + 1.5) % 7  # 0=Sun,1=Mon,...,6=Sat
    vara = VARA_NAMES[vara_idx]
    # Yoga (27 Nithya Yogas)
    yoga_idx = int((sun_lon + moon_lon) % 360 / (360 / 27)) % 27
    yoga = YOGA_NAMES[yoga_idx]
    # Karana (half-tithi)
    half_idx = int((moon_lon - sun_lon) % 360 / 6)  # 0-59
    if half_idx == 0:
        karana = "Kimstughna"
    elif half_idx <= 56:
        karana = KARANA_REPEATING[(half_idx - 1) % 7]
    elif half_idx == 57:
        karana = "Shakuni"
    elif half_idx == 58:
        karana = "Chatushpada"
    else:
        karana = "Naga"
    return {"tithi": tithi, "vara": vara, "yoga": yoga, "karana": karana}


def get_sade_sati_status(natal_moon_sign, current_sa_sign):
    """Return Sade Sati / Dhaiya status from natal Moon and transiting Saturn sign."""
    if current_sa_sign is None:
        return None
    moon_idx = zodiac_signs.index(natal_moon_sign)
    sa_idx = zodiac_signs.index(current_sa_sign)
    diff = (sa_idx - moon_idx + 12) % 12
    if diff == 11:
        return "Sade Sati – Rising Phase (Saturn in 12th from Moon): increased expenses, inner unrest, foreign journeys"
    elif diff == 0:
        return "Sade Sati – Peak Phase (Saturn on Moon sign): maximum pressure on mind, health, and finances"
    elif diff == 1:
        return "Sade Sati – Setting Phase (Saturn in 2nd from Moon): family friction, financial stress, speech issues"
    elif diff == 3:
        return "Kantaka Shani / Dhaiya (Saturn in 4th from Moon): troubles at home, property, vehicles, mother's health"
    elif diff == 7:
        return "Ashtama Shani / Dhaiya (Saturn in 8th from Moon): health challenges, obstacles, financial losses; intense karmic period"
    else:
        return None


# -------------------------------------------------------------------
# Divisional Charts (Vargas)
# -------------------------------------------------------------------
def get_navamsa_sign_and_deg(full_lon):
    """Return (sign, degree) in D9 Navamsa for a given full longitude."""
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    nav_size = 30.0 / 9
    navamsa_in_rasi = int(deg_in_rasi / nav_size)
    start_nav_idx = [0, 9, 6, 3][rasi_idx % 4]  # Fire/Earth/Air/Water
    nav_sign_idx = (start_nav_idx + navamsa_in_rasi) % 12
    remainder = deg_in_rasi % nav_size
    deg_in_nav = remainder * 9
    return zodiac_signs[nav_sign_idx], round(deg_in_nav, 2)


def get_d7_sign_and_deg(full_lon):
    """Return (sign, degree) in D7 Saptamsa."""
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    sapt_size = 30.0 / 7
    sapt_idx = int(deg_in_rasi / sapt_size)
    if rasi_idx % 2 == 0:  # Odd signs (Aries, Gemini...)
        start_idx = rasi_idx
    else:
        start_idx = (rasi_idx + 6) % 12
    new_idx = (start_idx + sapt_idx) % 12
    frac = (deg_in_rasi % sapt_size) / sapt_size
    deg_in_d7 = frac * 30
    return zodiac_signs[new_idx], round(deg_in_d7, 2)


def get_d10_sign_and_deg(full_lon):
    """Return (sign, degree) in D10 Dasamsa."""
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    dasa_size = 3.0
    dasa_idx = int(deg_in_rasi / dasa_size)
    if rasi_idx % 2 == 0:  # Odd signs
        start_idx = rasi_idx
    else:
        start_idx = (rasi_idx + 8) % 12
    new_idx = (start_idx + dasa_idx) % 12
    frac = (deg_in_rasi % dasa_size) / dasa_size
    deg_in_d10 = frac * 30
    return zodiac_signs[new_idx], round(deg_in_d10, 2)

# Add to utils.py

def get_navamsa_sign(deg):
    """Return D9 sign for a given longitude."""
    from constants import zodiac_signs
    rasi_idx = int(deg // 30)
    deg_in_rasi = deg % 30
    nav_size = 30.0 / 9
    navamsa_in_rasi = int(deg_in_rasi / nav_size)
    start_nav_idx = [0, 9, 6, 3][rasi_idx % 4]
    nav_sign_idx = (start_nav_idx + navamsa_in_rasi) % 12
    return zodiac_signs[nav_sign_idx]


def has_aspect(planet_house, target_house, planet):
    """Check if planet aspects target house (1-based houses)."""
    if planet_house == 0 or target_house == 0:
        return False
    diff = (target_house - planet_house) % 12
    if planet == "Ma":
        return diff in [4, 7, 8]
    if planet == "Ju":
        return diff in [5, 7, 9]
    if planet == "Sa":
        return diff in [3, 7, 10]
    return diff == 7


def get_seventh_sign(lagna_lon):
    """Get 7th house sign index (0-11) from Lagna longitude."""
    from utils import get_sign
    return (get_sign(lagna_lon) + 6) % 12


def signs_have_nadi_relation(s1, s2):
    """
    Nadi-INSPIRED sign relation (Parashari approximation).
    Relation types: same sign (0), 2/12 (1), 3/11 (2), opposition (6)
    """
    diff = abs(s1 - s2) % 12
    min_diff = min(diff, 12 - diff)
    return min_diff in (0, 1, 2, 6)


def get_progressed_jupiter_sign(natal_jup_lon, age_floor):
    """
    Degree-based Jupiter progression: natal degree + age * 30°.
    Returns progressed sign index (0-11).
    """
    progressed_lon = (natal_jup_lon + age_floor * 30) % 360
    return get_sign(progressed_lon)