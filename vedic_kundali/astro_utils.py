# Astronomical Utility Functions
# Helper functions for Vedic astrology calculations

import swisseph as swe
import os
import warnings

# Import constants
from constants import (
    zodiac_signs,
    nakshatras,
    planets,
    dignity_table,
    sign_lords,
    COMBUSTION_ORBS,
    NEECHA_BHANGA_INFO,
    EXALT_SIGNS,
    NATURAL_FRIENDS,
    NATURAL_ENEMIES,
)


# ────────────────────────────────────────────────
# Swiss Ephemeris Setup
# ────────────────────────────────────────────────
def setup_swiss_ephemeris():
    """Initialize Swiss Ephemeris and validate data files."""
    EPHE_DIR = os.path.dirname(os.path.abspath(__file__)) or "."
    swe.set_ephe_path(EPHE_DIR)
    
    # Validate that at least one essential ephemeris file exists
    REQUIRED_FILES = ["sepl_18.se1", "semo_18.se1"]
    missing = [f for f in REQUIRED_FILES if not os.path.isfile(os.path.join(EPHE_DIR, f))]
    if missing:
        warnings.warn(
            f"Swiss Ephemeris data files missing from '{EPHE_DIR}': {', '.join(missing)}. "
            "Swiss Ephemeris will fall back to less accurate Moshier mode. "
            "Download .se1 files from https://www.astro.com/ftp/swisseph/ephe/"
        )
    
    # Set Lahiri ayanamsa
    swe.set_sid_mode(swe.SIDM_LAHIRI)


# ────────────────────────────────────────────────
# Sign and Nakshatra Functions
# ────────────────────────────────────────────────
def get_sign(deg):
    """Get zodiac sign from degree."""
    return zodiac_signs[int(deg / 30) % 12]


def get_nakshatra(deg):
    """Get nakshatra from degree."""
    nak_index = int(deg / (360 / 27)) % 27
    return nakshatras[nak_index]


def get_nakshatra_progress(deg):
    """Get nakshatra progress (0-1) from degree."""
    nak_span = 360 / 27
    nak_start = int(deg / nak_span) * nak_span
    progress = (deg - nak_start) / nak_span
    return progress


# ────────────────────────────────────────────────
# Dignity Functions
# ────────────────────────────────────────────────
def get_dignity(planet, sign):
    """Get dignity of a planet in a given sign."""
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
    
    # Friend / Enemy classification
    if planet in ("Ra", "Ke") or sign not in sign_lords:
        return ""
    
    sign_lord = sign_lords[sign]
    if sign_lord == planet:
        return ""
    
    friends = NATURAL_FRIENDS.get(planet, set())
    enemies = NATURAL_ENEMIES.get(planet, set())
    
    if sign_lord in friends:
        return "Friend"
    elif sign_lord in enemies:
        return "Enemy"
    else:
        return "Neutral"


# ────────────────────────────────────────────────
# House Functions
# ────────────────────────────────────────────────
def get_house_from_sign(asc_sign_idx, planet_sign_idx):
    """Get house number from ascendant and planet sign indices."""
    return ((planet_sign_idx - asc_sign_idx) % 12) + 1


def is_retrograde(speed):
    """Check if planet is retrograde based on speed."""
    return speed < 0


# ────────────────────────────────────────────────
# Time Functions
# ────────────────────────────────────────────────
def datetime_to_jd(dt):
    """Convert datetime to Julian Day."""
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)


# ────────────────────────────────────────────────
# Combustion Check
# ────────────────────────────────────────────────
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


# ────────────────────────────────────────────────
# Neecha Bhanga Check
# ────────────────────────────────────────────────
def _houses_are_consecutive(house_set):
    """Return True if the given set of house numbers (1-12) form a
    gapless consecutive sequence, accounting for zodiac wrap-around."""
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


def check_neecha_bhanga(planet_code, planet_data, house_planets, lagna_idx, moon_house):
    """Return True if the debilitated planet's debilitation is cancelled
    (Neecha Bhanga Raja Yoga)."""
    if planet_code not in NEECHA_BHANGA_INFO:
        return False
    if planet_code not in planet_data:
        return False
    if planet_data[planet_code]["dignity"] != "Debilitated":
        return False

    kendra_from_lagna = {1, 4, 7, 10}
    if moon_house is not None:
        kendra_from_moon = {((moon_house - 1 + offset) % 12) + 1 for offset in (0, 3, 6, 9)}
    else:
        kendra_from_moon = set()

    def planet_in_kendra(pl_code):
        for h, plist in house_planets.items():
            if pl_code in plist:
                return h in kendra_from_lagna or h in kendra_from_moon
        return False

    def get_planet_house(pl_code):
        for h, plist in house_planets.items():
            if pl_code in plist:
                return h
        return None

    def planets_in_mutual_aspect(pl1_house, pl2_house):
        if pl1_house is None or pl2_house is None:
            return False
        return abs(pl1_house - pl2_house) % 12 == 6

    def planet_aspects_house(aspecting_code, aspecting_house, target_house):
        if aspecting_house is None or target_house is None:
            return False
        diff = ((target_house - aspecting_house) % 12)
        aspect_offsets = {6}
        if aspecting_code == "Ma":
            aspect_offsets.update({3, 7})
        elif aspecting_code == "Ju":
            aspect_offsets.update({4, 8})
        elif aspecting_code == "Sa":
            aspect_offsets.update({2, 9})
        return diff in aspect_offsets

    deb_lord, exalt_planet = NEECHA_BHANGA_INFO[planet_code]
    exalt_sign = EXALT_SIGNS.get(planet_code)
    exalt_sign_lord = sign_lords.get(exalt_sign) if exalt_sign else None

    # Rule A
    if deb_lord and planet_in_kendra(deb_lord):
        return True
    # Rule B
    if exalt_planet and exalt_planet != deb_lord and planet_in_kendra(exalt_planet):
        return True
    # Rule C
    if planet_in_kendra(planet_code):
        return True
    # Rule D
    if exalt_sign_lord and exalt_sign_lord != deb_lord and planet_in_kendra(exalt_sign_lord):
        return True
    # Rule E
    deb_lord_house = get_planet_house(deb_lord) if deb_lord else None
    planet_house = get_planet_house(planet_code)
    if deb_lord and deb_lord_house is not None and planet_house is not None:
        if planet_aspects_house(deb_lord, deb_lord_house, planet_house):
            return True
    # Rule F
    if deb_lord and deb_lord in planet_data:
        if planet_data[deb_lord].get("dignity") == "Exalt":
            return True
    # Rule G
    if exalt_sign_lord and exalt_sign_lord != planet_code:
        exalt_lord_house = get_planet_house(exalt_sign_lord)
        if planets_in_mutual_aspect(planet_house, exalt_lord_house):
            return True
    
    return False


# ────────────────────────────────────────────────
# Panchanga Functions
# ────────────────────────────────────────────────
def get_panchanga(birth_jd, sun_lon, moon_lon):
    """Return birth Panchanga: Tithi, Vara, Yoga, Karana."""
    from constants import TITHI_NAMES, YOGA_NAMES, KARANA_REPEATING, VARA_NAMES
    
    # Tithi
    tithi_num = int((moon_lon - sun_lon) % 360 / 12)
    tithi = TITHI_NAMES[tithi_num]
    
    # Vara (day of week)
    vara_idx = int(birth_jd + 1.5) % 7
    vara = VARA_NAMES[vara_idx]
    
    # Yoga
    yoga_idx = int((sun_lon + moon_lon) % 360 / (360 / 27)) % 27
    yoga = YOGA_NAMES[yoga_idx]
    
    # Karana
    half_idx = int((moon_lon - sun_lon) % 360 / 6)
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


# ────────────────────────────────────────────────
# Sade Sati Status
# ────────────────────────────────────────────────
def get_sade_sati_status(natal_moon_sign, current_sa_sign):
    """Return Sade Sati / Dhaiya status from natal Moon and transiting Saturn sign."""
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


# Initialize on import
setup_swiss_ephemeris()

