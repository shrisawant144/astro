# dasha.py
"""
Vimshottari Dasha calculations: Mahadasha, Antardasha, Pratyantar Dasha.
"""

import swisseph as swe
from .constants import dasha_lords, dasha_periods, nakshatra_lord_index
from .utils import get_nakshatra_progress


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
