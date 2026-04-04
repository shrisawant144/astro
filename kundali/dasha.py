# dasha.py
"""
Dasha calculations:
  - Vimshottari: Mahadasha → Antardasha → Pratyantar → Sookshma (4 levels)
  - Ashtottari : alternate 108-year dasha system (Rahu-based)
"""

import swisseph as swe
from .constants import dasha_lords, dasha_periods, nakshatra_lord_index
from .utils import get_nakshatra_progress

# ─── Ashtottari constants ────────────────────────────────────────────────────
# Order: Su, Mo, Ma, Me, Ve, Sa, Ju, Ra  (8 planets, total 108 years)
_ASHTO_LORDS = ["Su", "Mo", "Ma", "Me", "Ve", "Sa", "Ju", "Ra"]
_ASHTO_PERIODS = {
    "Su": 6,
    "Mo": 15,
    "Ma": 8,
    "Me": 17,
    "Ve": 21,
    "Sa": 10,
    "Ju": 19,
    "Ra": 12,
}  # total = 108 years
_ASHTO_NAK_LORD = {
    # Nakshatra index (0-26) → Ashtottari starting lord index
    # Lord of each nakshatra in Ashtottari (different from Vimshottari)
    0: 1,
    1: 2,
    2: 3,
    3: 4,
    4: 5,
    5: 6,
    6: 7,
    7: 0,
    8: 1,
    9: 2,
    10: 3,
    11: 4,
    12: 5,
    13: 6,
    14: 7,
    15: 0,
    16: 1,
    17: 2,
    18: 3,
    19: 4,
    20: 5,
    21: 6,
    22: 7,
    23: 0,
    24: 1,
    25: 2,
    26: 3,
}


def calculate_vimshottari_dasha(moon_deg, birth_jd):
    """
    Calculate Vimshottari Mahadashas from birth.

    Args:
        moon_deg (float): Moon's longitude at birth (0-360).
        birth_jd (float): Julian Day of birth (UT).

    Returns:
        tuple: (starting_lord, balance_years, list_of_mahadashas)
            Each mahadasha dict contains:
            - lord (str): planet code
            - start_jd (float)
            - end_jd (float)
            - years (float)
            - antardashas (list, initially empty)
    """
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

    # Balance period
    balance_days = balance_years * 365.25
    end_jd = current_jd + balance_days
    dashas.append(
        {
            "lord": start_lord,
            "start_jd": current_jd,
            "end_jd": end_jd,
            "years": round(balance_years, 3),
            "antardashas": [],
        }
    )
    current_jd = end_jd
    total_years = balance_years

    # Subsequent full dashas (up to ~130 years)
    while total_years < 130:
        current_lord_idx = (current_lord_idx + 1) % 9
        next_lord = dasha_lords[current_lord_idx]
        period = dasha_periods[next_lord]
        days = period * 365.25
        end_jd = current_jd + days
        dashas.append(
            {
                "lord": next_lord,
                "start_jd": current_jd,
                "end_jd": end_jd,
                "years": period,
                "antardashas": [],
            }
        )
        current_jd = end_jd
        total_years += period

    return start_lord, balance_years, dashas


def calculate_antardashas(md_dasha):
    """
    Calculate antardashas (sub-periods) within a mahadasha.
    Modifies the dasha dict in-place and returns it.

    Args:
        md_dasha (dict): Mahadasha dict with 'lord', 'start_jd', 'end_jd'.

    Returns:
        dict: The same dict with 'antardashas' list populated.
    """
    md_lord = md_dasha["lord"]
    md_days = md_dasha["end_jd"] - md_dasha["start_jd"]
    md_years = md_days / 365.25
    antardashas = []
    current_ad_jd = md_dasha["start_jd"]
    md_idx = dasha_lords.index(md_lord)

    for i in range(9):
        ad_idx = (md_idx + i) % 9
        ad_lord = dasha_lords[ad_idx]
        ad_full_years = dasha_periods[ad_lord]
        ad_proportion = ad_full_years / 120.0
        ad_years_in_md = md_years * ad_proportion
        ad_days = ad_years_in_md * 365.25
        ad_end_jd = current_ad_jd + ad_days
        antardashas.append(
            {
                "lord": ad_lord,
                "start_jd": current_ad_jd,
                "end_jd": ad_end_jd,
                "years": round(ad_years_in_md, 3),
            }
        )
        current_ad_jd = ad_end_jd

    md_dasha["antardashas"] = antardashas
    return md_dasha


def find_current_dasha(birth_jd, current_jd, dashas):
    """
    Find current Mahadasha and Antardasha at given current_jd.

    Args:
        birth_jd (float): Birth Julian Day.
        current_jd (float): Current Julian Day.
        dashas (list): List of mahadasha dicts (with antardashas).

    Returns:
        tuple: (md_lord, ad_lord) or (None, None) if not found.
    """
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


def get_current_pratyantar(birth_jd, current_jd, current_md, current_ad, dashas):
    """
    Compute current Pratyantar Dasha (3rd level) lord and its start/end JDs.

    Args:
        birth_jd (float): Birth Julian Day.
        current_jd (float): Current Julian Day.
        current_md (str): Current Mahadasha lord.
        current_ad (str): Current Antardasha lord.
        dashas (list): List of mahadasha dicts.

    Returns:
        tuple: (pd_lord, pd_start_jd, pd_end_jd) or (None, None, None).
    """
    years_since = (current_jd - birth_jd) / 365.25
    for md in dashas:
        if md["lord"] != current_md:
            continue
        for ad in md["antardashas"]:
            if ad["lord"] != current_ad:
                continue
            # Compute pratyantars for this AD on the fly
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


def get_current_sookshma(
    birth_jd, current_jd, current_md, current_ad, current_pd, dashas
):
    """
    Compute current Sookshma Dasha (4th level, ~days precision).

    Returns (sd_lord, sd_start_jd, sd_end_jd) or (None, None, None).
    """
    years_since = (current_jd - birth_jd) / 365.25
    for md in dashas:
        if md["lord"] != current_md:
            continue
        for ad in md["antardashas"]:
            if ad["lord"] != current_ad:
                continue
            ad_years = (ad["end_jd"] - ad["start_jd"]) / 365.25
            ad_idx = dasha_lords.index(current_ad)
            pd_jd = ad["start_jd"]
            for i in range(9):
                pd_idx = (ad_idx + i) % 9
                pd_lord_name = dasha_lords[pd_idx]
                pd_years = ad_years * (dasha_periods[pd_lord_name] / 120.0)
                pd_end_jd = pd_jd + pd_years * 365.25
                if pd_lord_name != current_pd:
                    pd_jd = pd_end_jd
                    continue
                # Now iterate Sookshma within this PD
                sd_jd = pd_jd
                pd_idx2 = dasha_lords.index(current_pd)
                for j in range(9):
                    sd_idx = (pd_idx2 + j) % 9
                    sd_lord_name = dasha_lords[sd_idx]
                    sd_years = pd_years * (dasha_periods[sd_lord_name] / 120.0)
                    sd_end = sd_jd + sd_years * 365.25
                    sd_start_y = (sd_jd - birth_jd) / 365.25
                    sd_end_y = (sd_end - birth_jd) / 365.25
                    if sd_start_y <= years_since < sd_end_y:
                        return sd_lord_name, sd_jd, sd_end
                    sd_jd = sd_end
    return None, None, None


# ─────────────────────────────────────────────────────────────────────────────
# Ashtottari Dasha (108-year system)
# ─────────────────────────────────────────────────────────────────────────────


def calculate_ashtottari_dasha(moon_deg, birth_jd):
    """
    Calculate Ashtottari Mahadashas from birth.

    Returns: (starting_lord, balance_years, list_of_mahadashas)
    """
    nak_span = 360 / 27
    nak_index = int(moon_deg / nak_span) % 27
    lord_idx = _ASHTO_NAK_LORD.get(nak_index, 0)
    start_lord = _ASHTO_LORDS[lord_idx]

    progress = get_nakshatra_progress(moon_deg)
    full_period = _ASHTO_PERIODS[start_lord]
    balance_years = (1 - progress) * full_period

    dashas = []
    current_jd = birth_jd
    current_idx = lord_idx

    # Balance period
    balance_days = balance_years * 365.25
    dashas.append(
        {
            "lord": start_lord,
            "start_jd": current_jd,
            "end_jd": current_jd + balance_days,
            "years": round(balance_years, 3),
            "antardashas": [],
        }
    )
    current_jd += balance_days
    total_years = balance_years

    while total_years < 108:
        current_idx = (current_idx + 1) % 8
        lord = _ASHTO_LORDS[current_idx]
        period = _ASHTO_PERIODS[lord]
        days = period * 365.25
        dashas.append(
            {
                "lord": lord,
                "start_jd": current_jd,
                "end_jd": current_jd + days,
                "years": period,
                "antardashas": [],
            }
        )
        current_jd += days
        total_years += period

    return start_lord, balance_years, dashas


def calculate_ashtottari_antardashas(md_dasha):
    """Calculate Ashtottari sub-periods within a Mahadasha."""
    md_lord = md_dasha["lord"]
    md_years = (md_dasha["end_jd"] - md_dasha["start_jd"]) / 365.25
    antardashas = []
    current_jd = md_dasha["start_jd"]
    md_idx = _ASHTO_LORDS.index(md_lord)

    for i in range(8):
        ad_idx = (md_idx + i) % 8
        ad_lord = _ASHTO_LORDS[ad_idx]
        ad_full = _ASHTO_PERIODS[ad_lord]
        ad_prop = ad_full / 108.0
        ad_years = md_years * ad_prop
        ad_end = current_jd + ad_years * 365.25
        antardashas.append(
            {
                "lord": ad_lord,
                "start_jd": current_jd,
                "end_jd": ad_end,
                "years": round(ad_years, 3),
            }
        )
        current_jd = ad_end

    md_dasha["antardashas"] = antardashas
    return md_dasha


def find_current_ashtottari(birth_jd, current_jd, dashas):
    """Find current Ashtottari MD and AD."""
    years_since = (current_jd - birth_jd) / 365.25
    for md in dashas:
        ms = (md["start_jd"] - birth_jd) / 365.25
        me = (md["end_jd"] - birth_jd) / 365.25
        if ms <= years_since < me:
            for ad in md["antardashas"]:
                as_ = (ad["start_jd"] - birth_jd) / 365.25
                ae = (ad["end_jd"] - birth_jd) / 365.25
                if as_ <= years_since < ae:
                    return md["lord"], ad["lord"]
    return None, None


# ─────────────────────────────────────────────────────────────────────────────
# Yogini Dasha (36-year cycle)
# ─────────────────────────────────────────────────────────────────────────────
# 8 Yoginis with their ruling planets and durations (total = 36 years)
_YOGINI_LORDS = ["Mo", "Su", "Ju", "Ma", "Me", "Sa", "Ve", "Ra"]
_YOGINI_NAMES = [
    "Mangala",
    "Pingala",
    "Dhanya",
    "Bhramari",
    "Bhadrika",
    "Ulka",
    "Siddha",
    "Sankata",
]
_YOGINI_PERIODS = {
    "Mangala": 1,  # Moon
    "Pingala": 2,  # Sun
    "Dhanya": 3,  # Jupiter
    "Bhramari": 4,  # Mars
    "Bhadrika": 5,  # Mercury
    "Ulka": 6,  # Saturn
    "Siddha": 7,  # Venus
    "Sankata": 8,  # Rahu
}  # total = 36 years

# Nakshatra → starting Yogini index (0-7) for Yogini Dasha
# Maps nak_index % 8 → Yogini sequence start
_YOGINI_NAK_MAP = {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 0,
    9: 1,
    10: 2,
    11: 3,
    12: 4,
    13: 5,
    14: 6,
    15: 7,
    16: 0,
    17: 1,
    18: 2,
    19: 3,
    20: 4,
    21: 5,
    22: 6,
    23: 7,
    24: 0,
    25: 1,
    26: 2,
}


def calculate_yogini_dasha(moon_deg, birth_jd):
    """
    Calculate Yogini Dasha from birth.

    Yogini Dasha is a 36-year cycle of 8 Yoginis.
    Each Yogini has a ruling planet and a period of 1-8 years.

    Args:
        moon_deg (float): Moon's longitude at birth (sidereal, 0-360).
        birth_jd (float): Julian Day of birth.

    Returns:
        tuple: (starting_yogini, balance_years, list_of_dashas)
    """
    nak_span = 360 / 27
    nak_index = int(moon_deg / nak_span) % 27
    yogini_idx = _YOGINI_NAK_MAP.get(nak_index, 0)
    start_yogini = _YOGINI_NAMES[yogini_idx]

    # Progress within nakshatra
    progress = (moon_deg % nak_span) / nak_span
    full_period = _YOGINI_PERIODS[start_yogini]
    balance_years = (1 - progress) * full_period

    dashas = []
    current_jd = birth_jd
    current_idx = yogini_idx

    # Balance period
    balance_days = balance_years * 365.25
    dashas.append(
        {
            "yogini": start_yogini,
            "lord": _YOGINI_LORDS[current_idx],
            "start_jd": current_jd,
            "end_jd": current_jd + balance_days,
            "years": round(balance_years, 3),
            "antardashas": [],
        }
    )
    current_jd += balance_days
    total_years = balance_years

    while total_years < 72:  # 2 cycles of 36 years
        current_idx = (current_idx + 1) % 8
        yogini = _YOGINI_NAMES[current_idx]
        period = _YOGINI_PERIODS[yogini]
        days = period * 365.25
        dashas.append(
            {
                "yogini": yogini,
                "lord": _YOGINI_LORDS[current_idx],
                "start_jd": current_jd,
                "end_jd": current_jd + days,
                "years": period,
                "antardashas": [],
            }
        )
        current_jd += days
        total_years += period

    return start_yogini, balance_years, dashas


def calculate_yogini_antardashas(md_dasha):
    """
    Calculate Yogini sub-periods (Antardashas) within a Yogini Mahadasha.

    Sub-period duration = (MD_years × sub_years) / 36
    """
    md_yogini = md_dasha["yogini"]
    md_years = (md_dasha["end_jd"] - md_dasha["start_jd"]) / 365.25
    total_cycle = 36.0
    md_idx = _YOGINI_NAMES.index(md_yogini)
    antardashas = []
    current_jd = md_dasha["start_jd"]

    for i in range(8):
        ad_idx = (md_idx + i) % 8
        ad_yogini = _YOGINI_NAMES[ad_idx]
        ad_full = _YOGINI_PERIODS[ad_yogini]
        ad_prop = ad_full / total_cycle
        ad_years = md_years * ad_prop
        ad_end = current_jd + ad_years * 365.25
        antardashas.append(
            {
                "yogini": ad_yogini,
                "lord": _YOGINI_LORDS[ad_idx],
                "start_jd": current_jd,
                "end_jd": ad_end,
                "years": round(ad_years, 3),
            }
        )
        current_jd = ad_end

    md_dasha["antardashas"] = antardashas
    return md_dasha


def find_current_yogini(birth_jd, current_jd, dashas):
    """Find current Yogini MD and AD at current_jd."""
    years_since = (current_jd - birth_jd) / 365.25
    for md in dashas:
        ms = (md["start_jd"] - birth_jd) / 365.25
        me = (md["end_jd"] - birth_jd) / 365.25
        if ms <= years_since < me:
            for ad in md.get("antardashas", []):
                as_ = (ad["start_jd"] - birth_jd) / 365.25
                ae = (ad["end_jd"] - birth_jd) / 365.25
                if as_ <= years_since < ae:
                    return md["yogini"], md["lord"], ad["yogini"], ad["lord"]
    return None, None, None, None
