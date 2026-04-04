# jaimini.py
"""
Jaimini Charakaraka (7 significators) and Karakamsa Lagna.
Based on the Jaimini Sutras, using the highest degrees (or lowest for nodes) to determine the karakas.
"""

from .constants import short_to_full, zodiac_signs
from .utils import get_navamsa_sign


def calculate_charakaraka(planet_data, navamsa_data):
    """
    Determine the 7 Jaimini karakas (Atmakaraka to Gnatikaraka).
    Returns a dict with planet codes and their roles.
    """
    # Exclude nodes from karaka calculation (some schools include Rahu, but classical excludes)
    planets = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
    degrees = []
    for p in planets:
        if p in planet_data:
            # Use the full longitude (0-360) – the planet with the highest longitude is Atmakaraka
            lon = planet_data[p]["full_lon"] % 360
            degrees.append((lon, p))
    # Sort by longitude descending (highest = Atmakaraka)
    degrees.sort(reverse=True)
    karaka_order = [
        "Atmakaraka",
        "Amatyakaraka",
        "Bhratrukaraka",
        "Matrukaraka",
        "Pitrukaraka",
        "Putrakaraka",
        "Gnatikaraka",
    ]
    karakas = {}
    for i, (_, planet) in enumerate(degrees):
        if i < len(karaka_order):
            karakas[karaka_order[i]] = planet
    return karakas


def get_karakamsa_lagna(atmakaraka, navamsa_data):
    """
    Karakamsa Lagna = the sign occupied by Atmakaraka in D9 Navamsa.
    This is the lagna of the soul in the navamsa chart.
    """
    if atmakaraka not in navamsa_data:
        return None
    return navamsa_data[atmakaraka]["sign"]


# -------------------------------------------------------------------
# Jaimini Chara Dasha, Argala, Pada Lagnas
# -------------------------------------------------------------------

SIGN_TYPES = {
    "Aries": "movable",
    "Taurus": "fixed",
    "Gemini": "dual",
    "Cancer": "movable",
    "Leo": "fixed",
    "Virgo": "dual",
    "Libra": "movable",
    "Scorpio": "fixed",
    "Sagittarius": "dual",
    "Capricorn": "movable",
    "Aquarius": "fixed",
    "Pisces": "dual",
}

SIGN_LORDS = {
    "Aries": "Ma",
    "Taurus": "Ve",
    "Gemini": "Me",
    "Cancer": "Mo",
    "Leo": "Su",
    "Virgo": "Me",
    "Libra": "Ve",
    "Scorpio": "Ma",
    "Sagittarius": "Ju",
    "Capricorn": "Sa",
    "Aquarius": "Sa",
    "Pisces": "Ju",
}


def calculate_chara_dasha(result):
    """
    Jaimini Chara Dasha (sign-based).

    result: kundali result dict with keys:
      - lagna_sign (str)
      - planets (dict pl -> {sign: str, ...})
      - birth_jd (float)

    Returns list of 12 dicts: {sign, lord, years, start_jd, end_jd}
    """
    lagna_sign = result.get("lagna_sign", "Aries")
    planets = result.get("planets", {})
    birth_jd = result.get("birth_jd", 0.0)

    lagna_idx = zodiac_signs.index(lagna_sign) if lagna_sign in zodiac_signs else 0

    # Map sign -> list of planets in that sign
    planets_in_sign = {sign: [] for sign in zodiac_signs}
    for pl, pdata in planets.items():
        psign = pdata.get("sign")
        if psign in planets_in_sign:
            planets_in_sign[psign].append(pl)

    JD_PER_YEAR = 365.25

    dashas = []
    current_jd = birth_jd

    for i in range(12):
        sign_idx = (lagna_idx + i) % 12
        sign = zodiac_signs[sign_idx]
        lord = SIGN_LORDS[sign]
        sign_type = SIGN_TYPES[sign]

        # Find lord's sign
        lord_sign = None
        for pl, pdata in planets.items():
            if pl == lord:
                lord_sign = pdata.get("sign")
                break

        if lord_sign is None or lord_sign == sign:
            # Lord in same sign or not found → 12 years
            years = 12
        else:
            lord_sign_idx = (
                zodiac_signs.index(lord_sign) if lord_sign in zodiac_signs else sign_idx
            )

            if sign_type in ("movable", "dual"):
                # Count forward from sign to lord's sign
                count = (lord_sign_idx - sign_idx) % 12
            else:
                # Fixed: count backward from sign to lord's sign
                count = (sign_idx - lord_sign_idx) % 12

            years = max(1, count)

        # Special: Rahu in this sign adds 1 year (cap at 12)
        rahu_sign = None
        for pl, pdata in planets.items():
            if pl == "Ra":
                rahu_sign = pdata.get("sign")
                break
        if rahu_sign == sign:
            years = min(12, years + 1)

        end_jd = current_jd + years * JD_PER_YEAR
        dashas.append(
            {
                "sign": sign,
                "lord": lord,
                "years": years,
                "start_jd": current_jd,
                "end_jd": end_jd,
            }
        )
        current_jd = end_jd

    return dashas


def find_current_chara_dasha(birth_jd, current_jd, dashas):
    """
    Find which Chara Dasha sign is currently active.

    Returns dict: {current_sign, current_lord, years_elapsed, years_remaining}
    or None if current_jd is before birth or after all dashas.
    """
    JD_PER_YEAR = 365.25

    if current_jd < birth_jd:
        return None

    for dasha in dashas:
        if dasha["start_jd"] <= current_jd < dasha["end_jd"]:
            years_elapsed = (current_jd - dasha["start_jd"]) / JD_PER_YEAR
            years_remaining = (dasha["end_jd"] - current_jd) / JD_PER_YEAR
            return {
                "current_sign": dasha["sign"],
                "current_lord": dasha["lord"],
                "years_elapsed": round(years_elapsed, 2),
                "years_remaining": round(years_remaining, 2),
            }

    return None


def calculate_argala(result):
    """
    Argala = houses that support (intervene in) a given house/planet.

    For each house 1-12:
      - Argala from: 2nd, 4th, 11th relative to that house
      - Virodha (cancellation): 12th cancels 2nd, 10th cancels 4th, 3rd cancels 11th
      - Virodha cancels only if virodha house has >= planets as argala house

    result must have result["houses"] as a dict or list of house planet counts.
    Expects result["houses"][h] = list of planets in house h (1-indexed).

    Returns: {house_num: {argala: [(argala_house, planets, virodha_house, virodha_planets, net_effect), ...],
                          summary: str}}
    """
    houses_data = result.get("houses", {})

    def planet_count(h):
        """Return number of planets in house h (1-indexed)."""
        entry = houses_data.get(h, [])
        if isinstance(entry, (list, tuple)):
            return len(entry)
        if isinstance(entry, dict):
            return len(entry)
        return int(entry)

    argala_offsets = {
        2: 12,  # 2nd argala is cancelled by 12th
        4: 10,  # 4th argala is cancelled by 10th
        11: 3,  # 11th argala is cancelled by 3rd
    }

    output = {}
    for ref_house in range(1, 13):
        argala_list = []
        summary_parts = []

        for argala_offset, virodha_offset in argala_offsets.items():
            argala_h = ((ref_house - 1 + argala_offset - 1) % 12) + 1
            virodha_h = ((ref_house - 1 + virodha_offset - 1) % 12) + 1

            argala_count = planet_count(argala_h)
            virodha_count = planet_count(virodha_h)

            # Virodha cancels if virodha_count >= argala_count AND argala_count > 0
            if argala_count > 0 and virodha_count >= argala_count:
                net_effect = "cancelled"
            elif argala_count > 0:
                net_effect = "active"
            else:
                net_effect = "none"

            argala_list.append(
                (
                    argala_h,
                    argala_count,
                    virodha_h,
                    virodha_count,
                    net_effect,
                )
            )

            if net_effect == "active":
                summary_parts.append(f"H{argala_h}(+{argala_count})")
            elif net_effect == "cancelled":
                summary_parts.append(f"H{argala_h}(cancelled by H{virodha_h})")

        summary = "; ".join(summary_parts) if summary_parts else "No active argala"
        output[ref_house] = {"argala": argala_list, "summary": summary}

    return output


def calculate_pada_lagnas(result):
    """
    Arudha Padas A1 through A12.

    Formula for Pada of house N:
      1. Find lord L of house N (using SIGN_LORDS and lagna sign)
      2. Find which house L is placed in
      3. Count distance from house N to L's house (forward)
      4. Pada = same distance further from L's house
      5. If Pada == house N → add 10 (mod 12, 1-indexed)
      6. If Pada == 7th from house N → add 10 (mod 12, 1-indexed)

    Returns dict: {"A1": {sign, house}, "A2": {...}, ..., "A12": {...}}
    """
    lagna_sign = result.get("lagna_sign", "Aries")
    planets = result.get("planets", {})
    lagna_idx = zodiac_signs.index(lagna_sign) if lagna_sign in zodiac_signs else 0

    def get_house_sign(house_num):
        """Return sign name for house number (1-indexed)."""
        return zodiac_signs[(lagna_idx + house_num - 1) % 12]

    def sign_to_house(sign):
        """Return house number (1-indexed) for a given sign."""
        if sign not in zodiac_signs:
            return 1
        sign_idx = zodiac_signs.index(sign)
        return ((sign_idx - lagna_idx) % 12) + 1

    def get_lord_house(lord):
        """Return house number where lord planet is placed."""
        for pl, pdata in planets.items():
            if pl == lord:
                psign = pdata.get("sign")
                if psign:
                    return sign_to_house(psign)
        return None

    output = {}
    for n in range(1, 13):
        house_sign = get_house_sign(n)
        lord = SIGN_LORDS.get(house_sign)
        if lord is None:
            output[f"A{n}"] = {"sign": house_sign, "house": n}
            continue

        lord_house = get_lord_house(lord)
        if lord_house is None:
            output[f"A{n}"] = {"sign": house_sign, "house": n}
            continue

        # Distance from house N to lord's house (forward)
        count = (lord_house - n) % 12
        if count == 0:
            count = 12  # Same house → lord in house N

        # Pada = same distance further from lord's house
        pada_house = ((lord_house - 1 + count) % 12) + 1

        # Special rule: if Pada falls on house N itself
        if pada_house == n:
            pada_house = ((pada_house - 1 + 10) % 12) + 1

        # Special rule: if Pada falls on the 7th from house N
        seventh_from_n = ((n - 1 + 6) % 12) + 1
        if pada_house == seventh_from_n:
            pada_house = ((pada_house - 1 + 10) % 12) + 1

        pada_sign = get_house_sign(pada_house)
        output[f"A{n}"] = {"sign": pada_sign, "house": pada_house}

    return output


def get_upapadha_lagna(result):
    """
    Upapadha Lagna (UL) = Arudha of the 12th house (A12).

    Returns: {sign, house, interpretation}
    """
    padas = calculate_pada_lagnas(result)
    a12 = padas.get("A12", {})
    sign = a12.get("sign", "Unknown")
    house = a12.get("house", 0)

    # Build a brief interpretation based on the sign
    interp_map = {
        "Aries": "Spouse likely from an independent, pioneering background; early marriage possible.",
        "Taurus": "Spouse from a stable, wealthy family; focus on material comforts in marriage.",
        "Gemini": "Intellectual companionship; spouse may be communicative or in a dual career.",
        "Cancer": "Nurturing spouse; strong emotional bond; family-oriented marriage.",
        "Leo": "Spouse from a noble or prominent family; strong personality in marriage.",
        "Virgo": "Spouse detail-oriented or in health/service field; practical union.",
        "Libra": "Balanced, harmonious marriage; spouse may be artistic or in legal field.",
        "Scorpio": "Intense karmic bond; transformation through marriage; secretive spouse.",
        "Sagittarius": "Spouse from a philosophical or foreign background; freedom in marriage.",
        "Capricorn": "Late or practical marriage; spouse disciplined and career-focused.",
        "Aquarius": "Unconventional marriage; spouse humanitarian or socially minded.",
        "Pisces": "Spiritual or artistic spouse; sacrificial themes possible in marriage.",
    }
    interpretation = interp_map.get(
        sign, "Marriage and long-term partnership are indicated by this sign."
    )

    return {"sign": sign, "house": house, "interpretation": interpretation}
