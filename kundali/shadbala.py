# shadbala.py
"""
Shadbala — Six Sources of Planetary Strength.

Components (all in Virupas; 60 Virupas = 1 Rupa):
  1. Sthana Bala   — positional strength (Uchcha + Sapta Varga + Kendra + Ojha/Yugma + Drekkana)
  2. Dig Bala      — directional strength
  3. Kala Bala     — temporal strength (Paksha + Natonnatha + Tribhaga + Vara/Hora lords)
  4. Chesta Bala   — motional strength (speed relative to mean)
  5. Naisargika    — natural/permanent strength (fixed)
  6. Drik Bala     — aspectual strength

Also computes Ishta / Kashta Phala per planet.

References: B.V. Raman "A Manual of Hindu Astrology", Mantreswara "Phaladeepika".
"""

import math
import swisseph as swe

from .constants import zodiac_signs, sign_lords, NATURAL_BENEFICS, NATURAL_MALEFICS

# ---------------------------------------------------------------------------
# Exaltation/Debilitation degrees (full longitude 0-360)
# ---------------------------------------------------------------------------
_EXALT_DEG = {
    "Su": 10.0,  # Aries 10°
    "Mo": 33.0,  # Taurus  3°
    "Ma": 298.0,  # Capricorn 28°
    "Me": 165.0,  # Virgo 15°
    "Ju": 95.0,  # Cancer  5°
    "Ve": 357.0,  # Pisces 27°
    "Sa": 200.0,  # Libra  20°
}
_DEB_DEG = {pl: (_EXALT_DEG[pl] + 180) % 360 for pl in _EXALT_DEG}

# Natural strength (Naisargika Bala) in Virupas
_NAISARGIKA = {
    "Su": 60.0,
    "Mo": 51.43,
    "Ve": 45.0,
    "Ju": 34.29,
    "Me": 25.71,
    "Ma": 17.14,
    "Sa": 8.57,
}

# Minimum Shadbala Pinda (in Rupas = Virupas/60) for "strong" classification
_MIN_RUPAS = {
    "Su": 5.0,
    "Mo": 6.0,
    "Ma": 5.0,
    "Me": 7.0,
    "Ju": 6.5,
    "Ve": 5.5,
    "Sa": 5.0,
}

# Planets that prefer odd signs (masculine)
_ODD_SIGN_PLANETS = {"Su", "Ma", "Ju", "Me", "Sa"}
# Planets that prefer even signs (feminine)
_EVEN_SIGN_PLANETS = {"Mo", "Ve"}

# Direction of maximum Dig Bala strength (house number, 1-based)
_DIG_BALA_HOUSE = {
    "Su": 10,
    "Ju": 10,  # strongest in 10th
    "Mo": 4,
    "Ve": 4,  # strongest in 4th
    "Ma": 1,
    "Sa": 1,  # strongest in 1st
    "Me": 1,  # strongest in 1st
}

# Mean daily motions (degrees/day) for Chesta Bala
_MEAN_MOTION = {
    "Su": 0.9856,
    "Mo": 13.1764,
    "Ma": 0.5240,
    "Me": 1.3833,
    "Ju": 0.0831,
    "Ve": 1.2000,
    "Sa": 0.0335,
}

# Sapta-Varga dignity score table (Virupas per varga)
_VARGA_SCORES = {
    "Exalt": 20.0,
    "Moolatrikona": 45.0,
    "Own": 30.0,
    "Great Friend": 22.5,
    "Friend": 15.0,
    "Neutral": 7.5,
    "Enemy": 3.75,
    "Great Enemy": 1.875,
    "Debilitated": 0.0,
}

# Moolatrikona signs
_MOOLATRIKONA = {
    "Su": "Leo",
    "Mo": "Taurus",
    "Ma": "Aries",
    "Me": "Virgo",
    "Ju": "Sagittarius",
    "Ve": "Libra",
    "Sa": "Aquarius",
}

# Natural friendships (for Sapta Varga dignity)
_NAT_FRIENDS = {
    "Su": {"Mo", "Ma", "Ju"},
    "Mo": {"Su", "Me"},
    "Ma": {"Su", "Mo", "Ju"},
    "Me": {"Su", "Ve"},
    "Ju": {"Su", "Mo", "Ma"},
    "Ve": {"Me", "Sa"},
    "Sa": {"Me", "Ve"},
}
_NAT_ENEMIES = {
    "Su": {"Ve", "Sa"},
    "Mo": set(),
    "Ma": {"Me"},
    "Me": {"Mo"},
    "Ju": {"Me", "Ve"},
    "Ve": {"Su", "Mo"},
    "Sa": {"Su", "Mo", "Ma"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _angular_distance(lon_a, lon_b):
    """Shortest arc between two longitudes (0-180)."""
    d = abs(lon_a - lon_b) % 360
    return d if d <= 180 else 360 - d


def _sign_of(full_lon):
    return zodiac_signs[int(full_lon % 360 // 30)]


def _dignity_label(planet, sign):
    """Return dignity category string for Sapta Varga scoring."""
    from .constants import dignity_table

    if planet not in dignity_table:
        return "Neutral"
    d = dignity_table[planet]
    own = d.get("own", [])
    if isinstance(own, str):
        own = [own]
    exalt = d.get("exalt", "")
    deb = d.get("deb", "")

    if exalt and sign == exalt:
        return "Exalt"
    if deb and sign == deb:
        return "Debilitated"
    if sign == _MOOLATRIKONA.get(planet):
        return "Moolatrikona"
    if sign in own:
        return "Own"
    lord = sign_lords.get(sign)
    if lord == planet:
        return "Own"
    friends = _NAT_FRIENDS.get(planet, set())
    enemies = _NAT_ENEMIES.get(planet, set())
    if lord in friends:
        return "Friend"
    if lord in enemies:
        return "Enemy"
    return "Neutral"


# ---------------------------------------------------------------------------
# 1. Sthana Bala
# ---------------------------------------------------------------------------


def _uchcha_bala(planet, full_lon):
    """0–60 Virupas. Max at exaltation point, 0 at debilitation point."""
    if planet not in _EXALT_DEG:
        return 0.0
    exalt = _EXALT_DEG[planet]
    deb = _DEB_DEG[planet]
    dist_from_deb = _angular_distance(full_lon, deb)
    # 180° from deb = exalt → 60 Virupas; 0° from deb → 0
    return round((dist_from_deb / 180.0) * 60.0, 2)


def _sapta_varga_bala(planet, planet_signs):
    """
    Sum dignity scores across 7 divisional charts.
    planet_signs: dict {chart: sign_str}  e.g. {'D1':'Aries','D2':'Leo',...}
    """
    total = 0.0
    for sign in planet_signs.values():
        label = _dignity_label(planet, sign)
        total += _VARGA_SCORES.get(label, 7.5)
    return round(total, 2)


def _ojha_yugma_bala(planet, d1_sign):
    """15 Virupas if planet is in its preferred odd/even sign type."""
    sign_idx = zodiac_signs.index(d1_sign)
    is_odd = sign_idx % 2 == 0  # Aries=0 (odd), Taurus=1 (even) …
    if planet in _ODD_SIGN_PLANETS and is_odd:
        return 15.0
    if planet in _EVEN_SIGN_PLANETS and not is_odd:
        return 15.0
    return 0.0


def _kendra_bala(house):
    """60 for kendras, 30 for panapharas, 15 for apoklimas."""
    if house in (1, 4, 7, 10):
        return 60.0
    if house in (2, 5, 8, 11):
        return 30.0
    return 15.0


def _drekkana_bala(planet, full_lon):
    """15 Virupas for correct decan affinity."""
    deg_in_sign = full_lon % 30
    decan = int(deg_in_sign / 10)  # 0=1st, 1=2nd, 2=3rd
    male = {"Su", "Ma", "Ju"}
    female = {"Mo", "Ve"}
    if planet in male and decan == 0:
        return 15.0
    if planet == "Me" and decan == 1:
        return 15.0
    if planet in female and decan == 2:
        return 15.0
    return 0.0


def sthana_bala(planet, full_lon, d1_sign, house, planet_signs):
    """Total Sthana Bala in Virupas."""
    ub = _uchcha_bala(planet, full_lon)
    svb = _sapta_varga_bala(planet, planet_signs)
    ojb = _ojha_yugma_bala(planet, d1_sign)
    kb = _kendra_bala(house)
    db = _drekkana_bala(planet, full_lon)
    total = ub + svb + ojb + kb + db
    return round(total, 2), {
        "uchcha": ub,
        "sapta_varga": svb,
        "ojha_yugma": ojb,
        "kendra": kb,
        "drekkana": db,
    }


# ---------------------------------------------------------------------------
# 2. Dig Bala
# ---------------------------------------------------------------------------


def dig_bala(planet, house):
    """0–60 Virupas. Max at direction house, 0 at opposite house."""
    if planet not in _DIG_BALA_HOUSE:
        return 0.0
    best_h = _DIG_BALA_HOUSE[planet]
    worst_h = ((best_h - 1 + 6) % 12) + 1  # opposite house
    dist_from_worst = abs(house - worst_h)
    if dist_from_worst > 6:
        dist_from_worst = 12 - dist_from_worst
    return round((dist_from_worst / 6.0) * 60.0, 2)


# ---------------------------------------------------------------------------
# 3. Kala Bala
# ---------------------------------------------------------------------------

# Day planets get 60 during day, night planets 60 at night, Me always 60
_DAY_PLANETS = {"Su", "Ju", "Ve"}
_NIGHT_PLANETS = {"Mo", "Ma", "Sa"}


def _natonnatha_bala(planet, is_day_birth):
    if planet == "Me":
        return 60.0
    if planet in _DAY_PLANETS:
        return 60.0 if is_day_birth else 0.0
    if planet in _NIGHT_PLANETS:
        return 0.0 if is_day_birth else 60.0
    return 30.0


def _paksha_bala(planet, moon_phase_fraction):
    """
    moon_phase_fraction: 0=new moon, 1=full moon.
    Benefics gain strength in Shukla (waxing), malefics in Krishna (waning).
    Returns 0–60 Virupas.
    """
    benefics = {"Mo", "Me", "Ju", "Ve"}
    malefics = {"Su", "Ma", "Sa"}
    if planet in benefics:
        return round(moon_phase_fraction * 60.0, 2)
    if planet in malefics:
        return round((1 - moon_phase_fraction) * 60.0, 2)
    return 30.0


_TRIBHAGA_DAY = [["Me", "Su", "Sa"], ["Mo", "Ve", "Ma"], ["Ju", "Me", "Su"]]
_TRIBHAGA_NIGHT = [["Ju", "Ve", "Sa"], ["Mo", "Ma", "Me"], ["Su", "Ju", "Ve"]]


def _tribhaga_bala(planet, birth_jd, sunrise_jd, sunset_jd):
    """30 Virupas if planet lords the current 1/3 of day/night."""
    try:
        day_len = sunset_jd - sunrise_jd
        night_len = 1.0 - day_len  # as fraction of a day (approx)
        elapsed = birth_jd - sunrise_jd
        if 0 <= elapsed <= day_len:
            part = int(elapsed / day_len * 3)
            part = min(part, 2)
            lords = _TRIBHAGA_DAY[part]
        else:
            next_sunrise = sunrise_jd + 1.0
            elapsed_night = birth_jd - sunset_jd
            if elapsed_night < 0:
                elapsed_night += 1.0
            n_len = next_sunrise - sunset_jd
            part = int(elapsed_night / n_len * 3) if n_len > 0 else 0
            part = min(part, 2)
            lords = _TRIBHAGA_NIGHT[part]
        if planet in lords:
            return 30.0
    except Exception:
        pass
    return 0.0


def kala_bala(planet, birth_jd, sun_lon, moon_lon, sunrise_jd, sunset_jd):
    """Total Kala Bala in Virupas."""
    is_day = sunrise_jd <= birth_jd <= sunset_jd
    moon_phase = ((moon_lon - sun_lon) % 360) / 360.0

    nath = _natonnatha_bala(planet, is_day)
    paksha = _paksha_bala(planet, moon_phase)
    trib = _tribhaga_bala(planet, birth_jd, sunrise_jd, sunset_jd)

    total = nath + paksha + trib
    return round(total, 2), {
        "natonnatha": nath,
        "paksha": paksha,
        "tribhaga": trib,
    }


# ---------------------------------------------------------------------------
# 4. Chesta Bala
# ---------------------------------------------------------------------------


def chesta_bala(planet, speed):
    """
    0–60 Virupas based on speed relative to mean daily motion.
    Retrograde planets get a flat 60 (maximum exertion).
    Direct planets: min(|speed|/mean_speed, 1) × 60.
    Sun & Moon: based on speed deviation.
    """
    if planet not in _MEAN_MOTION:
        return 0.0
    mean = _MEAN_MOTION[planet]
    if speed < 0:  # retrograde → maximum chesta
        return 60.0
    ratio = abs(speed) / mean if mean > 0 else 0
    return round(min(ratio, 1.0) * 60.0, 2)


# ---------------------------------------------------------------------------
# 5. Naisargika Bala (fixed)
# ---------------------------------------------------------------------------


def naisargika_bala(planet):
    return _NAISARGIKA.get(planet, 0.0)


# ---------------------------------------------------------------------------
# 6. Drik Bala (aspectual)
# ---------------------------------------------------------------------------


def _aspect_strength(planet_house, aspector_house, aspector):
    """Return aspect fraction (0-1) for classical Vedic aspects."""
    diff = (aspector_house - planet_house) % 12
    if aspector == "Ma":
        return {3: 0.5, 6: 0.75, 7: 1.0}.get(diff, 1.0 if diff == 0 else 0.0)
    if aspector == "Ju":
        return {4: 0.75, 6: 0.75, 7: 1.0}.get(diff, 1.0 if diff == 0 else 0.0)
    if aspector == "Sa":
        return {2: 0.25, 6: 0.75, 7: 1.0, 9: 0.75}.get(diff, 1.0 if diff == 0 else 0.0)
    return 1.0 if diff == 7 else (1.0 if diff == 0 else 0.0)


def drik_bala(planet, planet_house, all_houses):
    """
    Positive from benefic aspects, negative from malefic aspects.
    all_houses: dict {planet_code: house_num}.
    Returns a value in Virupas (can be negative).
    """
    score = 0.0
    for asp, asp_house in all_houses.items():
        if asp == planet or asp == "Asc":
            continue
        frac = _aspect_strength(planet_house, asp_house, asp)
        if frac == 0:
            continue
        if asp in NATURAL_BENEFICS:
            score += frac * 30.0
        elif asp in NATURAL_MALEFICS:
            score -= frac * 15.0
    return round(score, 2)


# ---------------------------------------------------------------------------
# Ishta / Kashta Phala
# ---------------------------------------------------------------------------


def ishta_kashta_phala(uchcha_virupas, chesta_virupas):
    """
    Ishta  = sqrt(Uchcha × Chesta) / 60  × 60  (range 0-60)
    Kashta = sqrt((60-Uchcha) × (60-Chesta)) / 60  × 60
    """
    ub = max(0, min(60, uchcha_virupas))
    cb = max(0, min(60, chesta_virupas))
    ishta = round(math.sqrt(ub * cb), 2)
    kashta = round(math.sqrt((60 - ub) * (60 - cb)), 2)
    return ishta, kashta


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def calculate_shadbala(result):
    """
    Calculate Shadbala for all 7 planets.

    Parameters
    ----------
    result : dict
        The kundali result dict from calculate_kundali().

    Returns
    -------
    dict  {planet: {
        'virupas': float,          # total Shadbala Pinda
        'rupas': float,            # virupas / 60
        'min_rupas': float,        # classical minimum for strength
        'strong': bool,
        'components': {...},
        'ishta': float,
        'kashta': float,
    }}
    """
    planet_data = result["planets"]
    birth_jd = result["birth_jd"]
    lagna_idx = zodiac_signs.index(result["lagna_sign"])

    # House number for each planet
    house_map = {}
    for h, plist in result["houses"].items():
        for p in plist:
            if p != "Asc":
                house_map[p] = h

    # Sunrise / sunset at birth location
    lat = result.get("lat", 0.0)
    lon_geo = result.get("lon", 0.0)
    try:
        sunrise_res, sunrise_tret = swe.rise_trans(
            birth_jd - 1,
            swe.SUN,
            swe.CALC_RISE,
            (lon_geo, lat, 0),
            0,
            0,
            swe.FLG_SWIEPH,
        )
        sunrise_jd = (
            sunrise_tret[0] if sunrise_res == 0 and sunrise_tret else birth_jd - 0.25
        )
        sunset_res, sunset_tret = swe.rise_trans(
            birth_jd - 1,
            swe.SUN,
            swe.CALC_SET,
            (lon_geo, lat, 0),
            0,
            0,
            swe.FLG_SWIEPH,
        )
        sunset_jd = (
            sunset_tret[0] if sunset_res == 0 and sunset_tret else birth_jd + 0.25
        )
    except Exception:
        sunrise_jd = birth_jd - 0.25
        sunset_jd = birth_jd + 0.25

    sun_lon = planet_data["Su"]["full_lon"]
    moon_lon = planet_data["Mo"]["full_lon"]

    shadbala = {}

    for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        if pl not in planet_data:
            continue
        pd = planet_data[pl]
        full_lon = pd["full_lon"]
        d1_sign = pd["sign"]
        house = house_map.get(pl, 1)
        speed = 0.0  # default; use planet speed if stored
        # Re-fetch speed from result if available (stored by main.py as 'speed')
        speed = pd.get("speed", 0.5)

        # Build planet signs across 7 vargas for Sapta Varga Bala
        planet_signs = {
            "D1": d1_sign,
            "D2": pd.get("d2_sign", d1_sign),
            "D3": pd.get("d3_sign", d1_sign),
            "D9": pd.get("navamsa_sign", d1_sign),
            "D12": pd.get("d12_sign", d1_sign),
            "D30": pd.get("d30_sign", d1_sign),
            "D7": pd.get("d7_sign", d1_sign),
        }

        stb, stb_parts = sthana_bala(pl, full_lon, d1_sign, house, planet_signs)
        dgb = dig_bala(pl, house)
        klb, klb_parts = kala_bala(
            pl, birth_jd, sun_lon, moon_lon, sunrise_jd, sunset_jd
        )
        chb = chesta_bala(pl, speed)
        nab = naisargika_bala(pl)
        drb = drik_bala(pl, house, house_map)

        total_virupas = stb + dgb + klb + chb + nab + drb
        total_rupas = round(total_virupas / 60.0, 3)
        min_rupas = _MIN_RUPAS.get(pl, 5.0)
        ishta, kashta = ishta_kashta_phala(stb_parts["uchcha"], chb)

        shadbala[pl] = {
            "virupas": round(total_virupas, 2),
            "rupas": total_rupas,
            "min_rupas": min_rupas,
            "strong": total_rupas >= min_rupas,
            "components": {
                "sthana_bala": stb,
                "sthana_detail": stb_parts,
                "dig_bala": dgb,
                "kala_bala": klb,
                "kala_detail": klb_parts,
                "chesta_bala": chb,
                "naisargika_bala": nab,
                "drik_bala": drb,
            },
            "ishta": ishta,
            "kashta": kashta,
        }

    return shadbala
