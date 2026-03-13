# nadi.py

import re
from datetime import datetime, timezone
from math import floor
from typing import Dict, List

from .constants import ZODIAC_SIGNS, SIGN_LORDS, SHORT_TO_FULL, FULL_TO_SHORT
from .utils import safe_sign_index, get_dignity

# Astropy import (optional)
try:
    from astropy.time import Time
    from astropy.coordinates import solar_system_ephemeris, get_body
    from astropy.coordinates import GeocentricTrueEcliptic
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False

def parse_kundali_for_marriage_date(filepath):
    """
    Parse kundali text file specifically for marriage date prediction.
    Extracts Lagna, planetary positions, 7th lord, birth date, and dasha periods.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Mapping from abbreviated to full names (for consistency)
    abbr_to_full = {
        'Su': 'Sun', 'Mo': 'Moon', 'Ma': 'Mars', 'Me': 'Mercury',
        'Ju': 'Jupiter', 'Ve': 'Venus', 'Sa': 'Saturn', 'Ra': 'Rahu', 'Ke': 'Ketu'
    }

    # Extract birth date from report (format: Birth Date   : YYYY-MM-DD)
    birth_date_match = re.search(r'Birth Date\s*:\s*([\d-]+)', text)
    if birth_date_match:
        birth_date_str = birth_date_match.group(1)
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
        except:
            # Fallback: extract just year if date parsing fails
            year_match = re.search(r'(\d{4})', birth_date_str)
            birth_year = int(year_match.group(1)) if year_match else 1999
            birth_date = datetime(birth_year, 1, 1)
    else:
        # Fallback to January 1 if no birth date found
        birth_date = datetime(1999, 1, 1)

    # Sign offsets (Aries = 0)
    sign_offsets = {
        'Aries': 0, 'Taurus': 30, 'Gemini': 60, 'Cancer': 90,
        'Leo': 120, 'Virgo': 150, 'Libra': 180, 'Scorpio': 210,
        'Sagittarius': 240, 'Capricorn': 270, 'Aquarius': 300, 'Pisces': 330
    }

    # Extract Lagna with sign name + degree → compute absolute longitude
    lagna_match = re.search(r'Lagna\s*:\s*(\w+)\s+([\d.]+)°', text)
    if not lagna_match:
        raise ValueError("Lagna not found in report")
    lagna_sign_str = lagna_match.group(1)
    lagna_deg_in_sign = float(lagna_match.group(2))
    lagna_sign_offset = sign_offsets.get(lagna_sign_str, 0)
    # Check if degree already includes sign offset (absolute) or is degree-in-sign
    if lagna_deg_in_sign >= 30:
        # Already absolute longitude (e.g. 289.14° for Capricorn)
        lagna_lon = lagna_deg_in_sign
    else:
        # Degree within sign, add offset
        lagna_lon = lagna_sign_offset + lagna_deg_in_sign

    # Extract planetary longitudes from D1 section
    planet_long = {}
    # Find the D1 section
    d1_section = re.search(r'Planets in Rasi \(D1\):(.*?)(?=\n\n|\nNavamsa)', text, re.DOTALL)
    if d1_section:
        planet_pattern = r'([A-Z][a-z]):\s*([\d.]+)°\s*(\w+)'
        for match in re.finditer(planet_pattern, d1_section.group(1)):
            planet_abbr = match.group(1)
            planet_full = abbr_to_full.get(planet_abbr, planet_abbr)
            deg = float(match.group(2))
            sign = match.group(3)
            if sign in sign_offsets:
                abs_long = sign_offsets[sign] + deg
                planet_long[planet_full] = abs_long

    # 7th lord - convert to full name if abbreviated
    lord7_match = re.search(r'7th Lord\s*:\s*(\w+)', text)
    lord7 = None
    if lord7_match:
        lord7_abbr = lord7_match.group(1)
        lord7 = abbr_to_full.get(lord7_abbr, lord7_abbr)

    # Parse dasha periods under "Marriage:" section
    dasha_periods = []  # each: (start_year, end_year, md, ad)
    in_marriage = False
    for line in text.split('\n'):
        if line.strip() == 'Marriage:':
            in_marriage = True
            continue
        if in_marriage and line.strip().startswith('└─'):
            # Pattern: └─ Planet/Planet (YYYY-YYYY)
            match = re.search(r'└─\s*(\w+)/(\w+)\s*\((\d{4})-(\d{4})\)', line)
            if match:
                md = match.group(1)
                ad = match.group(2)
                start = int(match.group(3))
                end = int(match.group(4))
                dasha_periods.append((start, end, md, ad))
        elif in_marriage and (line.strip() == '' or 'Career Rise' in line or 'Children' in line):
            # Empty line or next section ends the Marriage section
            in_marriage = False

    return {
        'lagna': lagna_lon,
        'planets': planet_long,
        'lord7': lord7,
        'birth_date': birth_date,
        'dasha_periods': dasha_periods
    }


# ============================================================================
# NADI-STYLE HELPER FUNCTIONS
# ============================================================================

def get_sign(lon_deg):
    """Convert absolute longitude to sign index: 0=Aries ... 11=Pisces"""
    return int(lon_deg // 30) % 12


def get_seventh_sign(lagna_lon):
    """Get 7th house sign index from Lagna longitude (equal house system)."""
    return (get_sign(lagna_lon) + 6) % 12


def signs_have_nadi_relation(s1, s2):
    """
    Nadi-INSPIRED sign relation (Parashari approximation).
    NOT true Nadi astrology (Chandra Kala Nadi etc.) which uses amsa-based
    directional strengths at 1/4° granularity.

    Relation types: same sign (0), 2/12 (1), 3/11 (2), opposition (6)
    Use min diff to handle zodiac circle.
    """
    diff = abs(s1 - s2) % 12
    min_diff = min(diff, 12 - diff)
    return min_diff in (0, 1, 2, 6)


def get_progressed_jupiter_sign(natal_jup_lon, age_floor):
    """
    Degree-based Jupiter progression: natal degree + age * 30°.
    Traditional Bhrigu Nadi uses ~1°/month (~12°/year), but many schools
    simplify to 30°/year (1 sign/year). Starting from the exact natal
    degree preserves sub-sign precision, avoiding 6-12 month errors
    that arise from rounding to whole signs.
    Returns progressed sign index.
    """
    progressed_lon = (natal_jup_lon + age_floor * 30) % 360
    return get_sign(progressed_lon)


def is_jupiter_transit_activating(transit_jup_sign, natal_sig_sign, progressed_sign):
    """
    Basic month-level check: Transit Jupiter in a sign that relates to natal significator or progressed Jupiter.
    Refine with exact degrees later for higher precision.
    """
    return (
        signs_have_nadi_relation(transit_jup_sign, natal_sig_sign) or
        signs_have_nadi_relation(transit_jup_sign, progressed_sign)
    )


# ============================================================================
# ASTROPY TRANSIT FUNCTIONS (REAL EPHEMERIS)
# ============================================================================

def approximate_lahiri_ayanamsa(jd):
    """
    Rough Lahiri ayanamsa in degrees (error ~0.5–1° in 20th–21st century).
    For higher accuracy, use pyswisseph in production.
    """
    t = (jd - 2451545.0) / 36525.0  # centuries from J2000
    precess = 5029.0966 * t + 1.11161 * t**2 - 0.000060 * t**3  # arcsec/century
    ayan = 23.853 + (precess / 3600.0)  # rough base + precession
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
        # Build Time from Julian Date directly to avoid ERFA UTC/TAI warnings.
        # ERFA's leap second table doesn't cover future dates, causing warnings
        # when Astropy internally converts between time scales via UTC.
        # Computing JD ourselves and using format='jd' with scale='tdb' bypasses this.
        if hasattr(dt, 'year'):
            naive = dt.replace(tzinfo=None) if hasattr(dt, 'replace') and dt.tzinfo else dt
            yr, mo, dy = naive.year, naive.month, naive.day
            hr = naive.hour + naive.minute / 60.0 + naive.second / 3600.0
        else:
            raise ValueError(f"Unsupported datetime type: {type(dt)}")
        
        # Meeus JD algorithm
        y, m = (yr - 1, mo + 12) if mo <= 2 else (yr, mo)
        A = y // 100
        B = 2 - A + A // 4
        jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + dy + hr / 24.0 + B - 1524.5
        
        t = Time(jd, format='jd', scale='tdb')
        ephem = 'de440s' if use_jpl else 'builtin'
        with solar_system_ephemeris.set(ephem):
            body = get_body(planet, t)
            ecl = body.transform_to(GeocentricTrueEcliptic())
            tropical_lon = ecl.lon.deg % 360
        
        # JD already computed above for Time creation — reuse for ayanamsa
        ayan = approximate_lahiri_ayanamsa(jd)
        sid_lon = (tropical_lon - ayan) % 360
        return sid_lon
    except Exception as e:
        print(f"⚠️ Transit calculation error for {planet}: {e}")
        return None


def check_nadi_promise(planets, gender='male'):
    """
    Check Nadi marriage promise:
    - Jupiter & Saturn both relate to significator → 100% promise, timely marriage
    - Only Jupiter → Timely marriage
    - Only Saturn → Late marriage but assured
    - Neither → Delayed/uncertain
    """
    sig_key = 'Venus' if gender.lower() == 'male' else 'Mars'
    sig_lon = planets.get(sig_key)
    jup_lon = planets.get('Jupiter')
    sat_lon = planets.get('Saturn')
    
    if not all([sig_lon, jup_lon, sat_lon]):
        return "Insufficient data for promise check"
    
    sig_sign = get_sign(sig_lon)
    jup_sign = get_sign(jup_lon)
    sat_sign = get_sign(sat_lon)
    
    jup_relates = signs_have_nadi_relation(jup_sign, sig_sign)
    sat_relates = signs_have_nadi_relation(sat_sign, sig_sign)
    
    sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    if jup_relates and sat_relates:
        return f"★★★ 100% PROMISE (Jupiter in {sign_names[jup_sign]} + Saturn in {sign_names[sat_sign]} both relate to {sig_key} in {sign_names[sig_sign]}) - Timely marriage assured"
    elif jup_relates:
        return f"★★ TIMELY (Jupiter in {sign_names[jup_sign]} relates to {sig_key}) - Marriage in appropriate time"
    elif sat_relates:
        return f"★ DELAYED BUT ASSURED (Saturn in {sign_names[sat_sign]} relates to {sig_key}) - Late marriage but will happen"
    else:
        return f"⚠️ WEAK PROMISE (Neither Jupiter nor Saturn strongly relate to {sig_key}) - May face delays or challenges"


def get_moon_transit_days(year, month, seventh_sign, sig_sign, use_jpl=False):
    """
    Find days in the given month when Moon transits 7th sign or significator sign.
    Filters out Amavasya (new moon) and Ashtami (8th tithi) as inauspicious
    for marriage muhurta per Muhurta Chintamani.
    Favorable tithis: 2,3,5,7,10,11,13 (classical marriage tithis).
    Returns list of day numbers (1-31).
    """
    if not ASTROPY_AVAILABLE:
        return []
    
    FAVORABLE_TITHIS = {1, 2, 4, 6, 9, 10, 12, 14}  # 0-indexed (tithi 2,3,5,7,10,11,13,Purnima)
    
    favorable_days = []
    try:
        # Check each day of the month
        for day in range(1, 32):
            try:
                check_dt = datetime(year, month, day, 12, 0, tzinfo=timezone.utc)  # Noon UTC
                moon_lon = get_sidereal_lon('moon', check_dt, use_jpl)
                if moon_lon is not None:
                    moon_sign = get_sign(moon_lon)
                    if moon_sign == seventh_sign or moon_sign == sig_sign:
                        # Approximate tithi check: Moon-Sun elongation
                        sun_lon = get_sidereal_lon('sun', check_dt, use_jpl)
                        if sun_lon is not None:
                            tithi_num = int(((moon_lon - sun_lon) % 360) / 12)  # 0-29
                            # Skip Amavasya (29) and Ashtami (7, 22) as inauspicious
                            if tithi_num in (7, 22, 29):
                                continue  # Skip inauspicious tithis
                            favorable_days.append(day)
                        else:
                            # Can't check tithi, include day anyway
                            favorable_days.append(day)
            except ValueError:
                break  # Month doesn't have this many days
    except Exception as e:
        print(f"⚠️ Moon transit calculation error: {e}")
    
    return favorable_days


# NOTE: is_jupiter_transit_activating is defined earlier in this file (~line 2370).
# The duplicate was removed to avoid shadowing.


def find_marriage_date(kundali, start_age=21, end_age=45, future_only=True, gender='male', use_real_transits=True, show_all_periods=False):
    """
    Enhanced Nadi-style marriage timing prediction with real transits.
    - Uses sign-based Jupiter progression (1 sign/year)
    - Checks progression relation to significator (Venus male / Mars female)
    - Filters by dasha (Maha + Antardasha in significators)
    - Uses REAL Jupiter transits (Astropy) for month refinement
    - Uses REAL Moon transits for day-level triggers
    - Tracks 12-year cycles (rounds)
    - Returns detailed prediction with confidence levels
    """
    planets = kundali['planets']
    significator_key = 'Venus' if gender.lower() == 'male' else 'Mars'
    sig_lon = planets.get(significator_key)
    jup_lon = planets.get('Jupiter')
    lagna_lon = kundali.get('lagna')
    
    if not sig_lon or not jup_lon:
        return "Missing significator or Jupiter in D1"

    natal_sig_sign = get_sign(sig_lon)
    natal_jup_sign = get_sign(jup_lon)
    seventh_sign = get_seventh_sign(lagna_lon) if lagna_lon else None
    
    birth_date = kundali.get('birth_date', datetime(1999, 1, 1))
    birth_year = birth_date.year
    today = datetime.now()

    # Check marriage promise first
    promise = check_nadi_promise(planets, gender)
    
    # Significators for Antardasha
    significators_ad = {'Venus', 'Moon', 'Jupiter'}
    if kundali.get('lord7'):
        significators_ad.add(kundali['lord7'])
    
    sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

    results = []  # Collect multiple possibilities
    
    for age in range(start_age, end_age + 1):
        # Calculate which round (12-year cycle)
        round_num = floor(age / 12) + 1
        
        # Nadi progression: +1 sign per year
        prog_sign = get_progressed_jupiter_sign(jup_lon, age)
        
        # Core Nadi timing: progressed sign must relate to natal significator sign
        if not signs_have_nadi_relation(prog_sign, natal_sig_sign):
            continue

        year = birth_year + age
        
        # Skip past years if future_only
        if future_only and year < today.year:
            continue

        # Dasha check: year-level
        dasha_ok = False
        matching_period = None
        dasha_score = 0
        for start, end, md, ad in kundali['dasha_periods']:
            if start <= year <= end and ad in significators_ad:
                dasha_ok = True
                matching_period = f"{md}/{ad} ({start}-{end})"
                # Score based on significator strength
                if ad == 'Venus':
                    dasha_score = 10
                elif ad == 'Jupiter':
                    dasha_score = 8
                elif ad == 'Moon':
                    dasha_score = 7
                break
        
        if not dasha_ok:
            continue

        # Check months in that favorable year (Jupiter + Saturn double transit)
        probable_months = []
        peak_months = []       # Jupiter in 7th sign or sig sign (strongest)
        saturn_months = set()  # Track months where Saturn also confirms
        for month in range(1, 13):
            check_date = datetime(year, month, 15, 12, 0, tzinfo=timezone.utc)
            
            # Skip past months
            if future_only and check_date < datetime.now(timezone.utc):
                continue
            
            if use_real_transits and ASTROPY_AVAILABLE:
                # --- Real transit: Jupiter + Saturn ---
                try:
                    jup_trans_lon = get_sidereal_lon('jupiter', check_date, use_jpl=False)
                    sat_trans_lon = get_sidereal_lon('saturn', check_date, use_jpl=False)
                    
                    if jup_trans_lon is not None:
                        jup_trans_sign = get_sign(jup_trans_lon)
                        
                        # Jupiter must relate to significator OR 7th sign
                        jup_activates = (
                            signs_have_nadi_relation(jup_trans_sign, natal_sig_sign) or
                            (seventh_sign is not None and signs_have_nadi_relation(jup_trans_sign, seventh_sign))
                        )
                        
                        # Saturn double-transit check (boosts confidence, not hard filter)
                        sat_activates = False
                        if sat_trans_lon is not None:
                            sat_trans_sign = get_sign(sat_trans_lon)
                            sat_activates = (
                                (seventh_sign is not None and signs_have_nadi_relation(sat_trans_sign, seventh_sign)) or
                                signs_have_nadi_relation(sat_trans_sign, natal_sig_sign)
                            )
                        
                        if jup_activates:
                            # Classify month strength
                            jup_in_7th = (seventh_sign is not None and jup_trans_sign == seventh_sign)
                            jup_in_sig_sign = (jup_trans_sign == natal_sig_sign)
                            
                            if jup_in_7th or jup_in_sig_sign:
                                # Jupiter directly in 7th house or significator sign → peak
                                probable_months.append(month)
                                peak_months.append(month)
                            elif seventh_sign is not None and signs_have_nadi_relation(jup_trans_sign, seventh_sign):
                                # Jupiter relates to 7th house → secondary
                                probable_months.append(month)
                            else:
                                # Jupiter relates to significator only → degree check
                                deg_diff = min(abs(jup_trans_lon - sig_lon) % 360,
                                              360 - abs(jup_trans_lon - sig_lon) % 360)
                                if deg_diff < 30 or deg_diff > 330:
                                    probable_months.append(month)
                            # Track Saturn confirmation
                            if sat_activates:
                                saturn_months.add(month)
                except Exception as e:
                    print(f"⚠️ Transit calculation error for {year}-{month:02d}: {e}")
            else:
                # Approximate transit (no Astropy)
                transit_jup_sign_approx = (natal_jup_sign + age + (month // 3)) % 12
                if is_jupiter_transit_activating(transit_jup_sign_approx, natal_sig_sign, prog_sign):
                    probable_months.append(month)
        
        if not probable_months:
            continue
        
        # Find favorable Moon transit days for ALL probable months
        all_favorable_dates = []  # List of (year, month, day) tuples
        favorable_days_first_month = []
        for pm in probable_months:
            if use_real_transits and ASTROPY_AVAILABLE and seventh_sign is not None:
                days = get_moon_transit_days(year, pm, seventh_sign, natal_sig_sign)
                for d in days:
                    all_favorable_dates.append((year, pm, d))
                if pm == probable_months[0]:
                    favorable_days_first_month = days
        
        # Pick the best predicted date — prefer peak months with Saturn
        best_date_str = None
        if all_favorable_dates:
            # Priority: peak+saturn > peak > saturn > any
            peak_saturn_dates = [(y, m, d) for y, m, d in all_favorable_dates if m in peak_months and m in saturn_months]
            peak_dates = [(y, m, d) for y, m, d in all_favorable_dates if m in peak_months]
            saturn_dates = [(y, m, d) for y, m, d in all_favorable_dates if m in saturn_months]
            
            if peak_saturn_dates:
                by, bm, bd = peak_saturn_dates[0]
            elif peak_dates:
                by, bm, bd = peak_dates[0]
            elif saturn_dates:
                by, bm, bd = saturn_dates[0]
            else:
                by, bm, bd = all_favorable_dates[0]
            best_date_str = f"{by}-{bm:02d}-{bd:02d}"
        else:
            # No Moon transit days found — use first probable month
            target_month = peak_months[0] if peak_months else probable_months[0]
            best_date_str = f"{year}-{target_month:02d} (exact day needs Moon transit)"
        
        # Build confidence level with Saturn double-transit boost
        has_saturn = any(m in saturn_months for m in probable_months)
        
        if dasha_score >= 8 and has_saturn and len(all_favorable_dates) > 0:
            confidence = "VERY HIGH"  # Jupiter + Saturn + strong dasha + Moon days
        elif dasha_score >= 8 and (has_saturn or len(all_favorable_dates) > 0):
            confidence = "HIGH"       # Strong dasha + at least one transit confirmation
        elif dasha_score >= 7:
            confidence = "MEDIUM"
        else:
            confidence = "MODERATE"
        
        # Collect result
        saturn_note = " [Saturn confirms]" if has_saturn else ""
        # Format all favorable dates as date strings
        date_strings = [f"{y}-{m:02d}-{d:02d}" for y, m, d in all_favorable_dates[:15]]
        result = {
            'date': best_date_str,
            'age': age,
            'round': round_num,
            'prog_sign': sign_names[prog_sign],
            'sig_sign': sign_names[natal_sig_sign],
            'significator': significator_key,
            'dasha': matching_period,
            'dasha_score': dasha_score,
            'probable_months': probable_months,
            'peak_months': peak_months,
            'favorable_dates': date_strings,
            'favorable_days': favorable_days_first_month[:10] if favorable_days_first_month else "Check Moon transits manually",
            'confidence': confidence + saturn_note,
            'promise': promise,
            'has_saturn_transit': has_saturn
        }
        
        results.append(result)
        
        # If not showing all periods, return first high-confidence match
        if not show_all_periods and ("VERY HIGH" in confidence or "HIGH" in confidence):
            return format_prediction_result(result)
    
    # Return results based on mode
    if show_all_periods and results:
        # Sort by: Saturn confirmation first, then dasha score descending, then age ascending
        results.sort(key=lambda x: (-x.get('has_saturn_transit', False), -x['dasha_score'], x['age']))
        
        output = f"Found {len(results)} favorable period(s):\n\n"
        for i, r in enumerate(results[:5], 1):
            output += f"\n{'='*80}\n"
            output += f"OPTION {i}: "
            output += format_prediction_result(r, include_date=True)
            output += f"\n{'='*80}"
        return output
    elif results:
        # Return best available (highest dasha score, then earliest)
        best = max(results, key=lambda x: (x['dasha_score'], -x['age']))
        return format_prediction_result(best)
    
    return f"No suitable period found (age {start_age}-{end_age}). Marriage Promise: {promise}. Consider wider age range or partner compatibility analysis."


def format_prediction_result(result, include_date=True):
    """Format the prediction result into a readable string."""
    output = ""
    if include_date:
        output = f"📅 {result['date']}\n"
    output += f"   ├─ Age: {result['age']} years (Round {result['round']} of 12-year cycle)"
    output += f"\n   ├─ Progression: Jupiter in {result['prog_sign']} → relates to {result['significator']} in {result['sig_sign']}"
    output += f"\n   ├─ Dasha: {result['dasha']} (Score: {result['dasha_score']}/10)"
    
    # Show peak months (strongest) vs wider window
    peak = result.get('peak_months', [])
    all_months = result.get('probable_months', [])
    if peak:
        output += f"\n   ├─ ⭐ Peak months (Jupiter in 7th/sig sign): {', '.join([f'{m:02d}' for m in peak])}"
        secondary = [m for m in all_months if m not in peak]
        if secondary:
            output += f"\n   ├─ Wider window: {', '.join([f'{m:02d}' for m in secondary])}"
    else:
        output += f"\n   ├─ Favorable months: {', '.join([f'{m:02d}' for m in all_months])}"
    
    # Show all favorable dates (year-month-day)
    if result.get('favorable_dates'):
        dates_str = ', '.join(result['favorable_dates'][:8])
        remaining = len(result['favorable_dates']) - 8
        if remaining > 0:
            dates_str += f" (+{remaining} more)"
        output += f"\n   ├─ 🎯 Probable dates: {dates_str}"
    elif result['favorable_days'] and isinstance(result['favorable_days'], list):
        days_str = ', '.join([str(d) for d in result['favorable_days'][:10]])
        if len(result['favorable_days']) > 10:
            days_str += f" (+{len(result['favorable_days'])-10} more)"
        output += f"\n   ├─ Moon transit days: {days_str}"
    else:
        output += f"\n   ├─ Moon transit days: {result['favorable_days']}"
    
    output += f"\n   ├─ Confidence: {result['confidence']}"
    output += f"\n   └─ {result['promise']}"
    
    return output


# ============================================================================
# MAIN
# ============================================================================
