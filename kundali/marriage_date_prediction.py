# marriage_date_prediction.py
"""
Nadi-style marriage date prediction using Jupiter progression, transits, and dasha.
Enhanced with Panchanga-based day scoring.
"""

import math
from datetime import datetime, timezone
from math import floor
from typing import Dict, List, Optional, Tuple

from constants import (
    SHORT_TO_FULL,
    ZODIAC_SIGNS,
    SIGN_LORDS,
    MARRIAGE_AUSPICIOUS_TITHIS,
    MARRIAGE_AUSPICIOUS_NAKSHATRAS,
)
from utils import (
    get_sign,
    get_nakshatra,
    get_seventh_sign,
    signs_have_nadi_relation,
    get_progressed_jupiter_sign,
    has_aspect,
)

# Optional Astropy for real transits
try:
    from astropy.time import Time
    from astropy.coordinates import solar_system_ephemeris, get_body
    from astropy.coordinates import GeocentricTrueEcliptic

    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False


def approximate_lahiri_ayanamsa(jd):
    """
    Rough Lahiri ayanamsa in degrees (error ~0.5–1° in 20th–21st century).
    For higher accuracy, use pyswisseph in production.
    """
    t = (jd - 2451545.0) / 36525.0  # centuries from J2000
    precess = 5029.0966 * t + 1.11161 * t**2 - 0.000060 * t**3
    ayan = 23.853 + (precess / 3600.0)
    return ayan % 360


def get_sidereal_lon(planet, dt, use_jpl=False):
    """
    Get geocentric sidereal ecliptic longitude (degrees) for planet at given datetime.
    planet: 'jupiter', 'saturn', 'moon', 'venus', 'mars', 'sun', etc.
    Returns None if Astropy not available.
    """
    if not ASTROPY_AVAILABLE:
        return None

    try:
        # Convert datetime to Julian Day (Meeus algorithm)
        naive = dt.replace(tzinfo=None) if dt.tzinfo else dt
        yr, mo, dy = naive.year, naive.month, naive.day
        hr = naive.hour + naive.minute / 60.0 + naive.second / 3600.0

        y, m = (yr - 1, mo + 12) if mo <= 2 else (yr, mo)
        A = y // 100
        B = 2 - A + A // 4
        jd = (
            int(365.25 * (y + 4716))
            + int(30.6001 * (m + 1))
            + dy
            + hr / 24.0
            + B
            - 1524.5
        )

        t = Time(jd, format="jd", scale="tdb")
        ephem = "de440s" if use_jpl else "builtin"
        with solar_system_ephemeris.set(ephem):
            body = get_body(planet, t)
            ecl = body.transform_to(GeocentricTrueEcliptic())
            tropical_lon = ecl.lon.deg % 360

        ayan = approximate_lahiri_ayanamsa(jd)
        sid_lon = (tropical_lon - ayan) % 360
        return sid_lon
    except Exception:
        return None


def get_moon_transit_days(year, month, seventh_sign, sig_sign, use_jpl=False):
    """
    Find days in the given month when Moon transits 7th sign or significator sign.
    Filters out Amavasya (new moon) and Ashtami (8th tithi) as inauspicious.
    Returns list of day numbers (1-31).
    """
    if not ASTROPY_AVAILABLE:
        return []

    favorable_days = []
    try:
        for day in range(1, 32):
            try:
                check_dt = datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
                moon_lon = get_sidereal_lon("moon", check_dt, use_jpl)
                if moon_lon is not None:
                    moon_sign = get_sign(moon_lon)
                    if moon_sign == seventh_sign or moon_sign == sig_sign:
                        sun_lon = get_sidereal_lon("sun", check_dt, use_jpl)
                        if sun_lon is not None:
                            tithi_num = int(((moon_lon - sun_lon) % 360) / 12)
                            if tithi_num in (7, 22, 29):  # Ashtami, Ashtami, Amavasya
                                continue
                            favorable_days.append(day)
                        else:
                            favorable_days.append(day)
            except ValueError:
                break
    except Exception:
        pass
    return favorable_days


def check_nadi_promise(planets, gender="male"):
    """
    Check Nadi marriage promise:
    - Jupiter & Saturn both relate to significator → 100% promise, timely marriage
    - Only Jupiter → Timely marriage
    - Only Saturn → Late marriage but assured
    - Neither → Delayed/uncertain
    """
    sig_key = "Venus" if gender.lower() == "male" else "Mars"
    sig_lon = planets.get(sig_key)
    jup_lon = planets.get("Jupiter")
    sat_lon = planets.get("Saturn")

    if not all([sig_lon, jup_lon, sat_lon]):
        return "Insufficient data for promise check"

    sig_sign = get_sign(sig_lon)
    jup_sign = get_sign(jup_lon)
    sat_sign = get_sign(sat_lon)

    jup_relates = signs_have_nadi_relation(jup_sign, sig_sign)
    sat_relates = signs_have_nadi_relation(sat_sign, sig_sign)

    sign_names = ZODIAC_SIGNS

    if jup_relates and sat_relates:
        return f"★★★ 100% PROMISE (Jupiter in {sign_names[jup_sign]} + Saturn in {sign_names[sat_sign]} both relate to {sig_key} in {sign_names[sig_sign]}) - Timely marriage assured"
    elif jup_relates:
        return f"★★ TIMELY (Jupiter in {sign_names[jup_sign]} relates to {sig_key}) - Marriage in appropriate time"
    elif sat_relates:
        return f"★ DELAYED BUT ASSURED (Saturn in {sign_names[sat_sign]} relates to {sig_key}) - Late marriage but will happen"
    else:
        return f"⚠️ WEAK PROMISE (Neither Jupiter nor Saturn strongly relate to {sig_key}) - May face delays or challenges"


def evaluate_marriage_date(date, natal_data, gender):
    """
    Score a specific date (datetime) for marriage suitability.
    Returns a score 0-100 based on multiple Vedic factors.
    """
    score = 50  # baseline
    factors = []

    # --- Tithi ---
    sun_lon = get_sidereal_lon("sun", date)
    moon_lon = get_sidereal_lon("moon", date)
    if sun_lon is not None and moon_lon is not None:
        tithi_num = int(((moon_lon - sun_lon) % 360) / 12)
        if tithi_num in MARRIAGE_AUSPICIOUS_TITHIS:
            score += 15
            factors.append("Auspicious tithi")
        elif tithi_num in (
            4,
            6,
            9,
            12,
        ):  # Chaturthi, Shashthi, Navami, Dwadashi are neutral
            score += 5
        else:
            score -= 10  # e.g., Amavasya, Ashtami

    # --- Nakshatra of Moon ---
    if moon_lon is not None:
        moon_nak = get_nakshatra(moon_lon)
        if moon_nak in MARRIAGE_AUSPICIOUS_NAKSHATRAS:
            score += 15
            factors.append(f"Moon in {moon_nak}")
        else:
            # some nakshatras are mildly inauspicious
            avoid = {
                "Bharani",
                "Krittika",
                "Ashlesha",
                "Magha",
                "Purva Phalguni",
                "Purva Ashadha",
                "Purva Bhadrapada",
                "Jyeshtha",
                "Mula",
            }
            if moon_nak in avoid:
                score -= 10

    # --- Vara (day of week) ---
    weekday = date.weekday()  # 0=Monday, 6=Sunday
    if weekday in (0, 2, 3, 4):  # Monday, Wednesday, Thursday, Friday are good
        score += 10
        factors.append("Good weekday")
    elif weekday in (5, 6):  # Saturday, Sunday – less ideal
        score -= 5

    # --- Yoga (using Panchanga) ---
    if sun_lon is not None and moon_lon is not None:
        yoga_idx = int((sun_lon + moon_lon) % 360 / (360 / 27)) % 27
        # Auspicious yogas: Vriddhi, Dhruva, Harshana, Vajra, Siddhi, Shiva, Siddha, Shubha, Brahma, Mahendra
        auspicious_yogas = {10, 11, 13, 14, 15, 19, 20, 22, 24, 25}  # 0-indexed
        if yoga_idx in auspicious_yogas:
            score += 10
            factors.append("Auspicious yoga")

    # --- Karana (half-tithi) ---
    if sun_lon is not None and moon_lon is not None:
        half_idx = int(((moon_lon - sun_lon) % 360) / 6)
        # Avoid Vishti (Bhadra) which is index 6 in repeating cycle
        if half_idx % 7 != 6:  # Vishti corresponds to 6 in 0-indexed repeating cycle
            score += 5
        else:
            score -= 10

    # --- Transiting Jupiter aspects ---
    jup_lon = get_sidereal_lon("jupiter", date)
    if jup_lon is not None:
        jup_sign = get_sign(jup_lon)
        # Check if Jupiter aspects 7th house from Lagna or Moon
        lagna_sign = get_sign(natal_data["lagna"])
        seventh_lagna_sign = (lagna_sign + 6) % 12
        if jup_sign == seventh_lagna_sign or signs_have_nadi_relation(
            jup_sign, seventh_lagna_sign
        ):
            score += 15
            factors.append("Jupiter aspects 7th house")

    # --- Transiting Saturn aspects ---
    sat_lon = get_sidereal_lon("saturn", date)
    if sat_lon is not None:
        sat_sign = get_sign(sat_lon)
        if signs_have_nadi_relation(sat_sign, seventh_lagna_sign):
            score += 10
            factors.append("Saturn aspects 7th house")

    return min(100, max(0, score)), factors


def find_marriage_date(
    kundali,
    start_age=21,
    end_age=45,
    future_only=True,
    gender="male",
    use_real_transits=True,
    show_all_periods=False,
):
    """
    Enhanced Nadi-style marriage timing prediction with real transits.
    - Uses sign-based Jupiter progression (1 sign/year)
    - Checks progression relation to significator (Venus male / Mars female)
    - Filters by dasha (Maha + Antardasha in significators)
    - Uses REAL Jupiter transits (Astropy) for month refinement
    - Uses REAL Moon transits for day-level triggers
    - Tracks 12-year cycles (rounds)
    - Returns detailed prediction with confidence levels

    kundali: dict from calculate_kundali() containing:
        - planets: dict of {planet: longitude}
        - lagna: lagna longitude
        - lord7: 7th lord name
        - birth_date: datetime object
        - dasha_periods: list of (start, end, md, ad) – can be extracted from vimshottari
    """
    planets = kundali["planets"]
    significator_key = "Venus" if gender.lower() == "male" else "Mars"
    sig_lon = planets.get(significator_key)
    jup_lon = planets.get("Jupiter")
    lagna_lon = kundali.get("lagna")

    if not sig_lon or not jup_lon:
        return "Missing significator or Jupiter in D1"

    natal_sig_sign = get_sign(sig_lon)
    natal_jup_sign = get_sign(jup_lon)
    seventh_sign = get_seventh_sign(lagna_lon) if lagna_lon else None

    birth_date = kundali.get("birth_date")
    if not birth_date:
        return "Birth date not available"
    birth_year = birth_date.year
    today = datetime.now()

    # Check marriage promise first
    promise = check_nadi_promise(planets, gender)

    # Significators for Antardasha
    significators_ad = {"Venus", "Moon", "Jupiter"}
    if kundali.get("lord7"):
        significators_ad.add(kundali["lord7"])

    sign_names = ZODIAC_SIGNS

    results = []

    for age in range(start_age, end_age + 1):
        round_num = floor(age / 12) + 1
        prog_sign = get_progressed_jupiter_sign(jup_lon, age)

        if not signs_have_nadi_relation(prog_sign, natal_sig_sign):
            continue

        year = birth_year + age
        if future_only and year < today.year:
            continue

        # Dasha check – handle both tuple and dict formats
        dasha_ok = False
        matching_period = None
        dasha_score = 0
        for period in kundali.get("dasha_periods", []):
            if isinstance(period, dict):
                start = period["start"]
                end = period["end"]
                md = period["maha"]
                ad = period["antara"]
            else:
                start, end, md, ad = period
            if start <= year <= end and ad in significators_ad:
                dasha_ok = True
                matching_period = f"{md}/{ad} ({start}-{end})"
                if ad == "Venus":
                    dasha_score = 10
                elif ad == "Jupiter":
                    dasha_score = 8
                elif ad == "Moon":
                    dasha_score = 7
                break

        if not dasha_ok:
            continue

        # Month-level transit analysis
        probable_months = []
        peak_months = []
        saturn_months = set()
        for month in range(1, 13):
            check_date = datetime(year, month, 15, 12, 0, tzinfo=timezone.utc)

            if future_only and check_date < datetime.now(timezone.utc):
                continue

            if use_real_transits and ASTROPY_AVAILABLE:
                try:
                    jup_trans_lon = get_sidereal_lon("jupiter", check_date)
                    sat_trans_lon = get_sidereal_lon("saturn", check_date)

                    if jup_trans_lon is not None:
                        jup_trans_sign = get_sign(jup_trans_lon)

                        jup_activates = signs_have_nadi_relation(
                            jup_trans_sign, natal_sig_sign
                        ) or (
                            seventh_sign is not None
                            and signs_have_nadi_relation(jup_trans_sign, seventh_sign)
                        )

                        sat_activates = False
                        if sat_trans_lon is not None:
                            sat_trans_sign = get_sign(sat_trans_lon)
                            sat_activates = (
                                seventh_sign is not None
                                and signs_have_nadi_relation(
                                    sat_trans_sign, seventh_sign
                                )
                            ) or signs_have_nadi_relation(
                                sat_trans_sign, natal_sig_sign
                            )

                        if jup_activates:
                            jup_in_7th = (
                                seventh_sign is not None
                                and jup_trans_sign == seventh_sign
                            )
                            jup_in_sig_sign = jup_trans_sign == natal_sig_sign

                            if jup_in_7th or jup_in_sig_sign:
                                probable_months.append(month)
                                peak_months.append(month)
                            elif seventh_sign and signs_have_nadi_relation(
                                jup_trans_sign, seventh_sign
                            ):
                                probable_months.append(month)
                            else:
                                deg_diff = min(
                                    abs(jup_trans_lon - sig_lon) % 360,
                                    360 - abs(jup_trans_lon - sig_lon) % 360,
                                )
                                if deg_diff < 30 or deg_diff > 330:
                                    probable_months.append(month)

                            if sat_activates:
                                saturn_months.add(month)
                except Exception:
                    continue
            else:
                # Approximate transit
                transit_jup_sign_approx = (natal_jup_sign + age + (month // 3)) % 12
                if signs_have_nadi_relation(transit_jup_sign_approx, natal_sig_sign):
                    probable_months.append(month)

        if not probable_months:
            continue

        # ------------------------------------------------------------------
        # New: evaluate each day in the candidate months and pick the best
        # ------------------------------------------------------------------
        best_score = -1
        best_date = None
        best_factors = []
        for month in probable_months:
            for day in range(1, 32):
                try:
                    check_date = datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
                    if future_only and check_date < datetime.now(timezone.utc):
                        continue
                    score, factors = evaluate_marriage_date(check_date, kundali, gender)
                    if score > best_score:
                        best_score = score
                        best_date = check_date
                        best_factors = factors
                except ValueError:
                    break  # invalid day (e.g., Feb 30)

        if best_date:
            best_date_str = best_date.strftime("%Y-%m-%d")
            favorable_dates = [best_date_str]  # we only show the best
        else:
            best_date_str = f"{year}-{probable_months[0]:02d} (no ideal day found)"
            favorable_dates = []

        has_saturn = any(m in saturn_months for m in probable_months)

        # Adjust confidence based on score
        if best_score >= 85:
            confidence = "VERY HIGH"
        elif best_score >= 70:
            confidence = "HIGH"
        elif best_score >= 50:
            confidence = "MEDIUM"
        else:
            confidence = "MODERATE"
        if has_saturn:
            confidence += " [Saturn confirms]"

        date_strings = [f"{y}-{m:02d}-{d:02d}" for y, m, d in favorable_dates[:15]]

        result = {
            "date": best_date_str,
            "age": age,
            "round": round_num,
            "prog_sign": sign_names[prog_sign],
            "sig_sign": sign_names[natal_sig_sign],
            "significator": significator_key,
            "dasha": matching_period,
            "dasha_score": dasha_score,
            "probable_months": probable_months,
            "peak_months": peak_months,
            "favorable_dates": date_strings,
            "confidence": confidence,
            "promise": promise,
            "has_saturn_transit": has_saturn,
            "score": best_score,
        }
        results.append(result)

        if not show_all_periods and ("VERY HIGH" in confidence or "HIGH" in confidence):
            return format_prediction_result(result)

    if show_all_periods and results:
        results.sort(
            key=lambda x: (
                -x.get("has_saturn_transit", False),
                -x["dasha_score"],
                -x.get("score", 0),
                x["age"],
            )
        )
        output = f"Found {len(results)} favorable period(s):\n\n"
        for i, r in enumerate(results[:5], 1):
            output += (
                f"\n{'='*80}\nOPTION {i}: "
                + format_prediction_result(r, include_date=True)
                + f"\n{'='*80}"
            )
        return output
    elif results:
        best = max(
            results, key=lambda x: (x["dasha_score"], x.get("score", 0), -x["age"])
        )
        return format_prediction_result(best)

    return f"No suitable period found (age {start_age}-{end_age}). Marriage Promise: {promise}."


def format_prediction_result(result, include_date=True):
    """Format the prediction result into a readable string."""
    output = ""
    if include_date:
        output = f"📅 {result['date']}\n"
    else:
        output = ""
    output += (
        f"   ├─ Age: {result['age']} years (Round {result['round']} of 12-year cycle)"
    )
    output += f"\n   ├─ Progression: Jupiter in {result['prog_sign']} → relates to {result['significator']} in {result['sig_sign']}"
    output += f"\n   ├─ Dasha: {result['dasha']} (Score: {result['dasha_score']}/10)"

    peak = result.get("peak_months", [])
    all_months = result.get("probable_months", [])
    if peak:
        output += f"\n   ├─ ⭐ Peak months (Jupiter in 7th/sig sign): {', '.join([f'{int(m):02d}' for m in peak])}"
        secondary = [m for m in all_months if m not in peak]
        if secondary:
            output += f"\n   ├─ Wider window: {', '.join([f'{int(m):02d}' for m in secondary])}"
    else:
        output += f"\n   ├─ Favorable months: {', '.join([f'{int(m):02d}' for m in all_months])}"

    if result.get("favorable_dates"):
        dates_str = ", ".join([str(d) for d in result["favorable_dates"][:8]])
        remaining = len(result["favorable_dates"]) - 8
        if remaining > 0:
            dates_str += f" (+{remaining} more)"
        output += f"\n   ├─ 🎯 Probable dates: {dates_str}"
    else:
        output += f"\n   ├─ Moon transit days: Check manually"

    output += f"\n   ├─ Confidence: {result['confidence']}"
    output += f"\n   └─ {result['promise']}"
    return output
