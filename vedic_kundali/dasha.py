# Vimshottari Dasha Module
# Dasha calculations and timing predictions

import datetime
from constants import (
    dasha_lords,
    dasha_periods,
    nakshatra_lord_index,
    zodiac_signs,
    sign_lords,
    short_to_full,
    gochara_effects,
)


# ────────────────────────────────────────────────
# Vimshottari Dasha Calculation
# ────────────────────────────────────────────────
def calculate_vimshottari_dasha(moon_deg, birth_jd):
    """Calculate Vimshottari Mahadashas."""
    nak_span = 360 / 27
    nak_index = int(moon_deg / nak_span) % 27
    lord_idx = nakshatra_lord_index[nak_index]
    start_lord = dasha_lords[lord_idx]
    progress = get_nakshatra_progress(moon_deg)
    full_period = dasha_periods[start_lord]
    balance_years = (1 - progress) * full_period
    
    dashas = []
    current_jd = birth_jd
    current_lord_idx = lord_idx
    
    # Balance
    balance_days = balance_years * 365.25
    end_jd = current_jd + balance_days
    dashas.append({
        "lord": start_lord,
        "start_jd": current_jd,
        "end_jd": end_jd,
        "years": round(balance_years, 3),
        "antardashas": [],
    })
    
    current_jd = end_jd
    total_years = balance_years
    
    while total_years < 130:
        current_lord_idx = (current_lord_idx + 1) % 9
        next_lord = dasha_lords[current_lord_idx]
        period = dasha_periods[next_lord]
        days = period * 365.25
        end_jd = current_jd + days
        dashas.append({
            "lord": next_lord,
            "start_jd": current_jd,
            "end_jd": end_jd,
            "years": period,
            "antardashas": [],
        })
        current_jd = end_jd
        total_years += period
    
    return start_lord, balance_years, dashas


def get_nakshatra_progress(deg):
    """Get nakshatra progress (0-1) from degree."""
    nak_span = 360 / 27
    nak_start = int(deg / nak_span) * nak_span
    progress = (deg - nak_start) / nak_span
    return progress


# ────────────────────────────────────────────────
# Antardasha Calculation
# ────────────────────────────────────────────────
def calculate_antardashas(mdadasha):
    """Calculate Antardashas within a Mahadasha."""
    md_lord = mdadasha["lord"]
    md_days = mdadasha["end_jd"] - mdadasha["start_jd"]
    md_years = md_days / 365.25
    
    antardashas = []
    current_ad_jd = mdadasha["start_jd"]
    md_idx = dasha_lords.index(md_lord)
    
    for i in range(9):
        ad_idx = (md_idx + i) % 9
        ad_lord = dasha_lords[ad_idx]
        ad_full_years = dasha_periods[ad_lord]
        ad_proportion = ad_full_years / 120.0
        ad_years_in_md = md_years * ad_proportion
        ad_days = ad_years_in_md * 365.25
        ad_end_jd = current_ad_jd + ad_days
        antardashas.append({
            "lord": ad_lord,
            "start_jd": current_ad_jd,
            "end_jd": ad_end_jd,
            "years": round(ad_years_in_md, 3),
        })
        current_ad_jd = ad_end_jd
    
    mdadasha["antardashas"] = antardashas
    return mdadasha


# ────────────────────────────────────────────────
# Find Current Dasha
# ────────────────────────────────────────────────
def find_current_dasha(birth_jd, current_jd, dashas):
    """Find current Mahadasha and Antardasha."""
    years_since = (current_jd - birth_jd) / 365.25
    for md in dashas:
        md_start_y = (md["start_jd"] - birth_jd) / 365.25
        md_end_y = (md["end_jd"] - birth_jd) / 365.25
        if md_start_y <= years_since < md_end_y:
            for ad in md["antardashas"]:
                ad_start_y = (ad["start_jd"] - birth_jd) / 365.25
                ad_end_y = (ad["end_jd"] - birth_jd) / 365.25
                if ad_start_y <= years_since < ad_end_y:
                    return md["lord"], ad["lord"]
    return None, None


# ────────────────────────────────────────────────
# Pratyantar Dasha
# ────────────────────────────────────────────────
def get_current_pratyantar(birth_jd, current_jd, current_md, current_ad, dashas):
    """Compute current Pratyantar Dasha (3rd level)."""
    years_since = (current_jd - birth_jd) / 365.25
    for md in dashas:
        if md["lord"] != current_md:
            continue
        for ad in md["antardashas"]:
            if ad["lord"] != current_ad:
                continue
            
            ad_days = ad["end_jd"] - ad["start_jd"]
            ad_years = ad_days / 365.25
            current_pd_jd = ad["start_jd"]
            ad_idx = dasha_lords.index(current_ad)
            
            for i in range(9):
                pd_idx = (ad_idx + i) % 9
                pd_lord = dasha_lords[pd_idx]
                pd_years = ad_years * (dasha_periods[pd_lord] / 120.0)
                pd_end_jd = current_pd_jd + pd_years * 365.25
                pd_start_y = (current_pd_jd - birth_jd) / 365.25
                pd_end_y = (pd_end_jd - birth_jd) / 365.25
                if pd_start_y <= years_since < pd_end_y:
                    return pd_lord, current_pd_jd, pd_end_jd
                current_pd_jd = pd_end_jd
    return None, None, None


# ────────────────────────────────────────────────
# Transits Calculation
# ────────────────────────────────────────────────
def calculate_transits(natal_moon_sign, current_jd, planets):
    """Calculate current planetary transits from Moon."""
    from astro_utils import get_sign
    
    transits = {}
    moon_idx = zodiac_signs.index(natal_moon_sign)
    
    for pcode, pid in planets.items():
        lon = datetime_to_jd_wrapper(current_jd, pid)
        sign = get_sign(lon)
        sign_idx = zodiac_signs.index(sign)
        rel_house = ((sign_idx - moon_idx + 12) % 12) + 1
        effect = gochara_effects.get(pcode, {}).get(rel_house, "Neutral")
        transits[pcode] = {"sign": sign, "house_from_moon": rel_house, "effect": effect}
    
    return transits


def datetime_to_jd_wrapper(current_jd, pid):
    """Wrapper for transit calculation."""
    import swisseph as swe
    return swe.calc_ut(current_jd, pid, swe.FLG_SIDEREAL)[0][0]

