# ashtakavarga.py
"""
Ashtakavarga calculations:
  - Bhinnashtakavarga  : individual planet charts (7 planets × 12 houses)
  - Sarvashtakavarga   : total SAV (sum of all 7)
  - Prastaraka display : per-planet bindus per house in sign order
"""

from .constants import ASHTAKAVARGA_REKHAS, zodiac_signs


def _planet_positions(result):
    """Return dict of {planet/As: zodiac_index 0-11}."""
    pd = result["planets"]
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    pos = {"As": lagna_idx}
    for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        if pl in pd:
            pos[pl] = zodiac_signs.index(pd[pl]["sign"])
    return pos


def _compute_bindus(target_planet, planet_positions):
    """Return list of 12 bindu counts (zodiac order) for one planet."""
    house_bindus = [0] * 12
    rekhas = ASHTAKAVARGA_REKHAS.get(target_planet, {})
    for ref_point, ref_pos in planet_positions.items():
        if ref_point not in rekhas:
            continue
        for house_offset in rekhas[ref_point]:
            actual_house = (ref_pos + house_offset) % 12
            house_bindus[actual_house] += 1
    return house_bindus


def calculate_ashtakavarga(result):
    """
    Calculate Bhinnashtakavarga (per-planet) and Sarvashtakavarga (SAV).

    Returns
    -------
    dict with keys:
      'individual'     : {planet: [12 bindus in zodiac order]}
      'sav'            : [12 SAV bindus in zodiac order]
      'by_house'       : {house_num 1-12: {'sign':str, 'sav':int,
                           'planets':{pl:int}, 'strength':str}}
      'interpretation' : {house_num: {'score':int, 'strength':str}}
    """
    planet_positions = _planet_positions(result)
    lagna_idx = zodiac_signs.index(result["lagna_sign"])

    # --- Bhinnashtakavarga ---
    individual_av = {}
    for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        if pl in planet_positions:
            individual_av[pl] = _compute_bindus(pl, planet_positions)

    # --- SAV ---
    sav = [0] * 12
    for bindus in individual_av.values():
        for i in range(12):
            sav[i] += bindus[i]

    # --- Per-house summary (house 1–12, each mapped to its zodiac sign) ---
    by_house = {}
    for h in range(1, 13):
        z_idx = (lagna_idx + h - 1) % 12
        sign = zodiac_signs[z_idx]
        sav_score = sav[z_idx]
        planet_bindus = {pl: individual_av[pl][z_idx] for pl in individual_av}

        if sav_score >= 28:
            strength = "Excellent"
        elif sav_score >= 25:
            strength = "Good"
        elif sav_score >= 22:
            strength = "Average"
        else:
            strength = "Weak"

        by_house[h] = {
            "sign": sign,
            "sav": sav_score,
            "planets": planet_bindus,
            "strength": strength,
        }

    # Legacy key kept for backward-compat with printing.py
    interpretation = {
        h: {"score": by_house[h]["sav"], "strength": by_house[h]["strength"]}
        for h in range(1, 13)
    }

    return {
        "individual": individual_av,
        "sav": sav,
        "by_house": by_house,
        "interpretation": interpretation,
    }
