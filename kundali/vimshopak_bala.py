# vimshopak_bala.py
"""
Vimshopak Bala — 20-point strength system across 16 Shodasavarga charts.
Graha Yuddha — planetary war detection.
"""

from .constants import zodiac_signs
from .utils import get_dignity

VIMSHOPAK_WEIGHTS = {
    "d1": 3.5,
    "d2": 0.5,
    "d3": 1.0,
    "d4": 1.0,
    "d7": 0.5,
    "navamsa": 3.0,
    "d10": 0.5,
    "d12": 0.5,
    "d16": 2.0,
    "d20": 0.5,
    "d24": 0.5,
    "d27": 0.5,
    "d30": 1.0,
    "d40": 0.5,
    "d45": 0.5,
    "d60": 4.0,
}
# Total weight = 20.0

DIGNITY_SCORE = {
    "Exalted": 1.0,
    "Exalt": 1.0,  # alternate spelling from get_dignity
    "Own": 1.0,
    "Moolatrikona": 0.75,
    "Friendly": 0.5,
    "Friend": 0.5,  # alternate spelling from get_dignity
    "Neutral": 0.375,
    "Enemy": 0.25,
    "Debilitated": 0.0,
}

# Planets eligible for vimshopak calculation
VIMSHOPAK_PLANETS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]

# Mapping from varga key to result dict key for planet sign lookup
_VARGA_RESULT_KEY = {
    "d1": ("planets", "sign"),
    "d2": ("d2", "sign"),
    "d3": ("d3", "sign"),
    "d4": ("d4", "sign"),
    "d7": ("d7", "sign"),
    "navamsa": ("navamsa", "sign"),
    "d10": ("d10", "sign"),
    "d12": ("d12", "sign"),
    "d16": ("d16", "sign"),
    "d20": ("d20", "sign"),
    "d24": ("d24", "sign"),
    "d27": ("d27", "sign"),
    "d30": ("d30", "sign"),
    "d40": ("d40", "sign"),
    "d45": ("d45", "sign"),
    "d60": ("d60", "sign"),
}


def _get_planet_sign_in_varga(result, varga_key, planet):
    """
    Extract a planet's sign from result for a given varga.
    Returns sign string or None if not found.
    """
    result_key, sign_key = _VARGA_RESULT_KEY[varga_key]
    varga_data = result.get(result_key)
    if not varga_data:
        return None
    planet_data = varga_data.get(planet)
    if not planet_data:
        return None
    if isinstance(planet_data, dict):
        return planet_data.get(sign_key)
    return None


def calculate_vimshopak_bala(result):
    """
    Calculate Vimshopak Bala for each planet across all 16 vargas.

    result dict has:
      - result["planets"][pl]["sign"]       for D1
      - result["navamsa"][pl]["sign"]       for D9
      - result["d2"][pl]["sign"], etc.      for other vargas

    Returns dict:
      {planet: {score: float (0-20), breakdown: {varga: score}, strong: bool}}
    """
    output = {}

    for planet in VIMSHOPAK_PLANETS:
        breakdown = {}
        total_score = 0.0

        for varga_key, weight in VIMSHOPAK_WEIGHTS.items():
            try:
                sign = _get_planet_sign_in_varga(result, varga_key, planet)
                if sign is None:
                    breakdown[varga_key] = 0.0
                    continue

                dignity = get_dignity(planet, sign)
                dig_score = DIGNITY_SCORE.get(dignity, 0.375)  # default Neutral
                varga_score = round(dig_score * weight, 4)
                breakdown[varga_key] = varga_score
                total_score += varga_score
            except Exception:
                breakdown[varga_key] = 0.0

        total_score = round(total_score, 4)
        output[planet] = {
            "score": total_score,
            "breakdown": breakdown,
            "strong": total_score >= 15.0,
        }

    return output


def detect_graha_yuddha(result):
    """
    Detect Graha Yuddha (planetary war) — when two planets are within 1° of each other
    in the same sign. Excludes Sun, Moon, Rahu, Ketu.

    The planet with the lower degree within its sign WINS
    (closer to 0° = brighter/faster-rising).

    Uses result["planets"][pl]["deg"]  (degree within sign, 0-30)
    and    result["planets"][pl]["sign"].

    Returns list of dicts:
      {planet1, planet2, winner, loser, orb, sign, interpretation}
    """
    planets_data = result.get("planets", {})
    excluded = {"Su", "Mo", "Ra", "Ke"}

    # Collect eligible planets with their sign and degree
    eligible = {}
    for pl, pdata in planets_data.items():
        if pl in excluded:
            continue
        sign = pdata.get("sign")
        deg = pdata.get("deg")
        if sign is None or deg is None:
            continue
        try:
            deg = float(deg)
        except (TypeError, ValueError):
            continue
        eligible[pl] = {"sign": sign, "deg": deg}

    planet_list = list(eligible.keys())
    wars = []

    for i in range(len(planet_list)):
        for j in range(i + 1, len(planet_list)):
            pl1 = planet_list[i]
            pl2 = planet_list[j]

            try:
                d1 = eligible[pl1]
                d2 = eligible[pl2]

                # Must be in the same sign
                if d1["sign"] != d2["sign"]:
                    continue

                orb = abs(d1["deg"] - d2["deg"])
                if orb > 1.0:
                    continue

                # Winner = lower degree (closer to 0° in sign)
                if d1["deg"] <= d2["deg"]:
                    winner, loser = pl1, pl2
                else:
                    winner, loser = pl2, pl1

                sign = d1["sign"]
                interpretation = (
                    f"{winner} wins the planetary war over {loser} in {sign}; "
                    f"{loser}'s significations are weakened."
                )

                wars.append(
                    {
                        "planet1": pl1,
                        "planet2": pl2,
                        "winner": winner,
                        "loser": loser,
                        "orb": round(orb, 4),
                        "sign": sign,
                        "interpretation": interpretation,
                    }
                )
            except Exception:
                continue

    return wars
