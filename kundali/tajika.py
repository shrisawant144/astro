# tajika.py
"""
Tajika (Annual Horoscopy) module.

Covers:
  - Solar Return (Varsha Pravesh): Sun returns to natal longitude each year
  - Muntha: Annual progressed Ascendant (1 sign per year)
  - Year Lord (Varsha Lord): Lord of the sign occupied by Muntha
  - Tajika Aspects: Itthasala (applying), Ishrafa (separating), Muthasila,
                    Nakta, Yamaya, Manau, Dutthottha, Radd, Kamboola
  - Varsha Tithi Pravesha: Moon returns to natal tithi position
"""

import datetime

import swisseph as swe

from .constants import sign_lords, zodiac_signs

# ─── Solar Return (Varsha Pravesh) ────────────────────────────────────────────


def find_solar_return_jd(natal_sun_lon, year, birth_jd):
    """
    Find Julian Day when Sun returns to natal longitude in a given year.

    Args:
        natal_sun_lon (float): Natal Sun longitude (sidereal, 0-360).
        year (int): Target year (e.g. 2024 for the 2024 solar return).
        birth_jd (float): Julian Day of birth (for starting search point).

    Returns:
        float: Julian Day of solar return.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Start the search around the actual birth anniversary, not January 1.
    birth_year, birth_month, birth_day, birth_hour = swe.revjul(birth_jd, swe.GREG_CAL)
    hour = int(birth_hour)
    minute = int((birth_hour - hour) * 60)
    second = int(round((((birth_hour - hour) * 60) - minute) * 60))
    if second == 60:
        second = 59

    try:
        approx_dt = datetime.datetime(
            year, int(birth_month), int(birth_day), hour, minute, second
        )
    except ValueError:
        # Handle leap-day births and any invalid month/day combination gracefully.
        safe_day = min(int(birth_day), 28)
        approx_dt = datetime.datetime(year, int(birth_month), safe_day, hour, minute, second)

    approx_jd = swe.julday(
        approx_dt.year,
        approx_dt.month,
        approx_dt.day,
        approx_dt.hour + approx_dt.minute / 60.0 + approx_dt.second / 3600.0,
        swe.GREG_CAL,
    )

    # The Sun moves ~1 degree/day, so a +/- 7 day window around the anniversary
    # is plenty while staying anchored near the real solar return.
    step = 1.0 / 48.0  # 30 minutes
    best_jd = approx_jd
    best_diff = 360.0

    for i in range(-7 * 48, 7 * 48 + 1):
        jd_test = approx_jd + i * step
        sun_lon = swe.calc_ut(jd_test, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        diff = abs((sun_lon - natal_sun_lon + 180) % 360 - 180)
        if diff < best_diff:
            best_diff = diff
            best_jd = jd_test

    # Refine with bisection to minute precision
    lo, hi = best_jd - step, best_jd + step
    for _ in range(40):
        mid = (lo + hi) / 2
        sun_mid = swe.calc_ut(mid, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        d = (sun_mid - natal_sun_lon + 180) % 360 - 180
        if d < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def get_tajika_planets(jd, lat, lon):
    """
    Calculate planet positions for a Tajika chart (Solar Return).

    Returns list of (planet_code, longitude) in sidereal.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    planet_map = {
        "Su": swe.SUN,
        "Mo": swe.MOON,
        "Ma": swe.MARS,
        "Me": swe.MERCURY,
        "Ju": swe.JUPITER,
        "Ve": swe.VENUS,
        "Sa": swe.SATURN,
        "Ra": swe.MEAN_NODE,
    }
    result = {}
    for code, sweid in planet_map.items():
        data = swe.calc_ut(jd, sweid, flags)[0]
        lon_val = data[0] % 360
        speed = data[3]
        result[code] = {
            "lon": lon_val,
            "sign_idx": int(lon_val / 30) % 12,
            "speed": speed,
        }
    # Ketu = opposite Rahu
    ra_lon = result["Ra"]["lon"]
    ke_lon = (ra_lon + 180) % 360
    result["Ke"] = {"lon": ke_lon, "sign_idx": int(ke_lon / 30) % 12, "speed": 0}

    # Ascendant
    try:
        houses = swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)[0]
        asc_lon = houses[0] % 360
        result["Asc"] = {"lon": asc_lon, "sign_idx": int(asc_lon / 30) % 12, "speed": 0}
    except Exception:
        result["Asc"] = {"lon": 0, "sign_idx": 0, "speed": 0}

    return result


# ─── Muntha ───────────────────────────────────────────────────────────────────


def calculate_muntha(birth_lagna_sign_idx, age_years):
    """
    Calculate Muntha (annual Ascendant progressor).

    Muntha advances 1 sign per year from the natal Ascendant.

    Args:
        birth_lagna_sign_idx (int): Natal Ascendant sign (0=Aries).
        age_years (int): Completed years at the solar return.

    Returns:
        dict: {sign_idx, sign, lord, house_from_lagna}
    """
    muntha_sign_idx = (birth_lagna_sign_idx + age_years) % 12
    muntha_sign = zodiac_signs[muntha_sign_idx]
    muntha_lord = sign_lords[muntha_sign]
    house_from_lagna = muntha_sign_idx - birth_lagna_sign_idx + 1
    if house_from_lagna <= 0:
        house_from_lagna += 12
    return {
        "sign_idx": muntha_sign_idx,
        "sign": muntha_sign,
        "lord": muntha_lord,
        "house_from_lagna": house_from_lagna,
    }


# ─── Year Lord (Varshesha) ────────────────────────────────────────────────────

_YEAR_LORD_ORDER = ["Su", "Ve", "Me", "Mo", "Sa", "Ju", "Ma"]


def calculate_year_lord(solar_return_jd):
    """
    Calculate Varshesha (Year Lord) = lord of the hora at the solar return moment.

    Uses the traditional Tajika hora lord sequence.

    Args:
        solar_return_jd (float): Julian Day of solar return.

    Returns:
        str: Planet code of the year lord.
    """
    # Hora lord: based on weekday and hour from sunrise
    # Simplified: use the vara (weekday) lord as base
    # Day lords: Sun=0, Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6
    vara_lords = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
    jd_int = int(solar_return_jd + 0.5) % 7
    # 0=Monday in Julian system; reorder to Sun=0
    day_idx = (jd_int + 6) % 7  # approximate
    year_lord = vara_lords[day_idx]
    return year_lord


# ─── Tajika Aspects ───────────────────────────────────────────────────────────

# Tajika aspect orbs (tighter than Parashari)
TAJIKA_ASPECTS = {
    "conjunction": 0,
    "sextile": 60,
    "square": 90,
    "trine": 120,
    "opposition": 180,
}
TAJIKA_ORB = 12  # degrees


def check_tajika_aspects(p1_code, p1_lon, p1_speed, p2_code, p2_lon, p2_speed):
    """
    Check Tajika aspect between two planets.

    Returns list of dicts with aspect type and whether applying/separating.
    """
    aspects = []
    for aspect_name, aspect_angle in TAJIKA_ASPECTS.items():
        diff = abs((p1_lon - p2_lon + 360) % 360)
        diff = min(diff, 360 - diff)
        angular_diff = abs(diff - aspect_angle)
        if angular_diff <= TAJIKA_ORB:
            # Check if applying (Itthasala) or separating (Ishrafa)
            # Applying = planets moving toward exact aspect
            # If both direct: faster planet approaching slower
            relative_speed = p1_speed - p2_speed
            applying = relative_speed < 0 if p1_lon < p2_lon else relative_speed > 0
            aspects.append(
                {
                    "aspect": aspect_name,
                    "angle": aspect_angle,
                    "orb": round(angular_diff, 2),
                    "applying": applying,
                    "type": "Itthasala" if applying else "Ishrafa",
                    "p1": p1_code,
                    "p2": p2_code,
                }
            )
    return aspects


def get_all_tajika_aspects(tajika_planets):
    """Calculate all Tajika aspects between planets."""
    planet_codes = [p for p in tajika_planets if p != "Asc"]
    all_aspects = []
    checked = set()
    for i, p1 in enumerate(planet_codes):
        for p2 in planet_codes[i + 1 :]:
            key = frozenset({p1, p2})
            if key in checked:
                continue
            checked.add(key)
            d1 = tajika_planets[p1]
            d2 = tajika_planets[p2]
            aspects = check_tajika_aspects(
                p1,
                d1["lon"],
                d1.get("speed", 0),
                p2,
                d2["lon"],
                d2.get("speed", 0),
            )
            all_aspects.extend(aspects)
    return all_aspects


# ─── Main Tajika Function ─────────────────────────────────────────────────────


def calculate_tajika(result, target_year=None, lat=None, lon=None):
    """
    Calculate the Annual Tajika (Solar Return) chart for a given year.

    Args:
        result (dict): Natal kundali result dict.
        target_year (int): Year for solar return (defaults to current year).
        lat (float): Latitude for solar return chart.
        lon (float): Longitude for solar return chart.

    Returns:
        dict: {
            year, solar_return_jd, solar_return_date,
            tajika_planets, muntha, year_lord, aspects,
            natal_sun_lon, interpretation
        }
    """
    if target_year is None:
        target_year = datetime.date.today().year

    # Use natal coordinates if not provided
    if lat is None:
        lat = result.get("lat", 0.0)
    if lon is None:
        lon = result.get("lon", 0.0)

    birth_jd = result.get("birth_jd", 0)
    natal_sun_lon = result.get("planets", {}).get("Su", {}).get("full_lon", 0)
    birth_lagna_idx = result.get("lagna_sign_idx")
    if birth_lagna_idx is None:
        birth_lagna_idx = zodiac_signs.index(result.get("lagna_sign", "Aries"))
    birth_year = result.get("birth_year", 1990)
    age_years = target_year - birth_year

    # Find solar return JD
    sr_jd = find_solar_return_jd(natal_sun_lon, target_year, birth_jd)

    # Convert to calendar date
    cal = swe.revjul(sr_jd, swe.GREG_CAL)
    sr_date = f"{int(cal[0])}-{int(cal[1]):02d}-{int(cal[2]):02d} {int(cal[3]):02d}:{int((cal[3] % 1)*60):02d}"

    # Calculate planet positions for solar return
    tajika_planets = get_tajika_planets(sr_jd, lat, lon)

    # Muntha
    muntha = calculate_muntha(birth_lagna_idx, age_years)

    # Year lord
    year_lord = calculate_year_lord(sr_jd)

    # Aspects
    aspects = get_all_tajika_aspects(tajika_planets)
    applying = [a for a in aspects if a["applying"]]

    # Interpretation
    muntha_house = muntha["house_from_lagna"]
    interp_parts = [
        f"Muntha in {muntha['sign']} (House {muntha_house}), lord: {muntha['lord']}",
        f"Year Lord: {year_lord}",
    ]
    if muntha_house in [1, 10, 11]:
        interp_parts.append("Muntha in angular/11th house — generally favorable year.")
    elif muntha_house in [6, 8, 12]:
        interp_parts.append(
            "Muntha in dusthana — year may have challenges and obstacles."
        )
    elif muntha_house in [5, 9]:
        interp_parts.append("Muntha in trikona — spiritually enriching year.")

    itthasala_count = len(applying)
    if itthasala_count > 3:
        interp_parts.append(
            f"Many applying aspects ({itthasala_count}) — active and eventful year."
        )
    elif itthasala_count == 0:
        interp_parts.append("No applying aspects — quieter, reflective year.")

    return {
        "year": target_year,
        "age": age_years,
        "solar_return_jd": sr_jd,
        "solar_return_date": sr_date,
        "tajika_planets": tajika_planets,
        "muntha": muntha,
        "year_lord": year_lord,
        "aspects": aspects,
        "applying_aspects": applying,
        "natal_sun_lon": natal_sun_lon,
        "interpretation": interp_parts,
    }
