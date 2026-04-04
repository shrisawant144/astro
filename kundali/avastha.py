# avastha.py
"""
Planetary Avasthas (States) — Six qualitative states of a planet.

1. Lajjita  (Shamed)    — Jupiter/Venus in 5H with Rahu, Ketu, or Saturn
2. Garvita  (Proud)     — Planet in exaltation or Moolatrikona
3. Kshudita (Starved)   — In enemy sign, aspected by enemy, no friendly aspect
4. Trishita (Thirsty)   — In watery sign aspected by a malefic
5. Mudita   (Delighted) — In friendly sign OR aspected by Jupiter/benefic
6. Kshobita (Agitated)  — Combust AND aspected by a malefic

A planet can hold multiple avasthas simultaneously.
Reference: Phaladeepika Ch. 4, BPHS Ch. 45.
"""

from .constants import zodiac_signs, sign_lords, NATURAL_BENEFICS, NATURAL_MALEFICS

_MOOLATRIKONA = {
    "Su": "Leo",
    "Mo": "Taurus",
    "Ma": "Aries",
    "Me": "Virgo",
    "Ju": "Sagittarius",
    "Ve": "Libra",
    "Sa": "Aquarius",
}

_EXALT_SIGNS = {
    "Su": "Aries",
    "Mo": "Taurus",
    "Ma": "Capricorn",
    "Me": "Virgo",
    "Ju": "Cancer",
    "Ve": "Pisces",
    "Sa": "Libra",
}

_DEB_SIGNS = {
    "Su": "Libra",
    "Mo": "Scorpio",
    "Ma": "Cancer",
    "Me": "Pisces",
    "Ju": "Capricorn",
    "Ve": "Virgo",
    "Sa": "Aries",
}

_OWN_SIGNS = {
    "Su": ["Leo"],
    "Mo": ["Cancer"],
    "Ma": ["Aries", "Scorpio"],
    "Me": ["Gemini", "Virgo"],
    "Ju": ["Sagittarius", "Pisces"],
    "Ve": ["Taurus", "Libra"],
    "Sa": ["Capricorn", "Aquarius"],
}

_WATERY_SIGNS = {"Cancer", "Scorpio", "Pisces"}

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


def _gets_aspect(aspector_house, target_house, aspector_planet):
    """Return True if aspector_planet in aspector_house aspects target_house."""
    diff = (target_house - aspector_house) % 12
    if aspector_planet == "Ma":
        return diff in {3, 6, 7}
    if aspector_planet == "Ju":
        return diff in {4, 6, 7}
    if aspector_planet == "Sa":
        return diff in {2, 6, 7, 9}
    return diff == 7


def _is_aspected_by(planet_house, all_planet_houses, aspectors):
    """Return True if any planet in `aspectors` aspects planet_house."""
    for asp, asp_h in all_planet_houses.items():
        if asp in aspectors and _gets_aspect(asp_h, planet_house, asp):
            return True
    return False


def calculate_avasthas(result):
    """
    Determine avasthas for all 7 classical planets.

    Parameters
    ----------
    result : dict — kundali result dict

    Returns
    -------
    dict  {planet: {
        'avasthas'    : [list of avastha names],
        'description' : [list of short meanings],
        'primary'     : str  (most significant avastha),
    }}
    """
    planet_data = result["planets"]
    houses = result["houses"]

    # house_map: planet → house number (1-12)
    house_map = {}
    for h, plist in houses.items():
        for p in plist:
            if p != "Asc":
                house_map[p] = h

    malefics = NATURAL_MALEFICS  # {"Sa","Ma","Su","Ra","Ke"}
    benefics = NATURAL_BENEFICS  # {"Ju","Ve","Mo"}

    avasthas_all = {}

    for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        if pl not in planet_data:
            continue
        pd = planet_data[pl]
        sign = pd["sign"]
        house = house_map.get(pl, 1)
        states = []
        descs = []

        # ── 1. Lajjita (Shamed) ─────────────────────────────────────────
        if pl in ("Ju", "Ve") and house == 5:
            co_5h = [
                p
                for p in house_map
                if house_map[p] == 5 and p not in ("Ju", "Ve", "Asc")
            ]
            if any(p in {"Ra", "Ke", "Sa"} for p in co_5h):
                states.append("Lajjita")
                descs.append(
                    "Shamed: 5th-house conjunction with Rahu/Ketu/Saturn "
                    "weakens the planet's creative and child significations"
                )

        # ── 2. Garvita (Proud) ──────────────────────────────────────────
        if sign == _EXALT_SIGNS.get(pl) or sign == _MOOLATRIKONA.get(pl):
            states.append("Garvita")
            descs.append(
                "Proud: exaltation / Moolatrikona — full expression of strength"
            )

        # ── 3. Kshudita (Starved) ───────────────────────────────────────
        # In enemy sign with enemy aspect and no friendly aspect
        in_enemy = sign_lords.get(sign) in _NAT_ENEMIES.get(pl, set())
        enemy_asp = _is_aspected_by(house, house_map, _NAT_ENEMIES.get(pl, set()))
        friend_asp = _is_aspected_by(house, house_map, _NAT_FRIENDS.get(pl, set()))
        if in_enemy and enemy_asp and not friend_asp:
            states.append("Kshudita")
            descs.append(
                "Starved: enemy sign + enemy aspect + no friend — severely weakened"
            )

        # ── 4. Trishita (Thirsty) ───────────────────────────────────────
        if sign in _WATERY_SIGNS:
            mal_asp = _is_aspected_by(house, house_map, malefics - {"Su"})
            if mal_asp:
                states.append("Trishita")
                descs.append(
                    "Thirsty: watery sign + malefic aspect — emotionally depleted"
                )

        # ── 5. Mudita (Delighted) ───────────────────────────────────────
        own_list = _OWN_SIGNS.get(pl, [])
        in_friend = sign_lords.get(sign) in _NAT_FRIENDS.get(pl, set())
        ju_asp = _is_aspected_by(house, house_map, {"Ju"})
        if sign in own_list or in_friend or ju_asp:
            states.append("Mudita")
            descs.append(
                "Delighted: own/friendly sign or Jupiter aspect — content and productive"
            )

        # ── 6. Kshobita (Agitated) ──────────────────────────────────────
        if pd.get("combust", False):
            mal_asp = _is_aspected_by(house, house_map, malefics)
            if mal_asp:
                states.append("Kshobita")
                descs.append(
                    "Agitated: combust + malefic aspect — severely disturbed results"
                )

        # Default if no state detected
        if not states:
            d1_sign_lord = sign_lords.get(sign, "")
            if d1_sign_lord == pl or sign in own_list:
                states.append("Mudita")
                descs.append("Delighted: in own sign — comfortable and effective")
            else:
                states.append("Neutral")
                descs.append("No dominant avastha — context-dependent results")

        # Primary = first (most severe / significant)
        avasthas_all[pl] = {
            "avasthas": states,
            "description": descs,
            "primary": states[0],
        }

    return avasthas_all


# Arudha Lagna calculation (Jaimini)
def calculate_arudha_lagna(result):
    """
    Arudha Lagna = the sign as far from the 1st-lord's position
                   as the 1st-lord is from Lagna.

    Returns (sign_str, house_number).
    """
    from .constants import sign_lords as sl

    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)
    lagna_lord = sl[lagna_sign]  # e.g. "Sa" for Capricorn

    pd = result["planets"]
    if lagna_lord not in pd:
        return lagna_sign, 1

    lord_sign = pd[lagna_lord]["sign"]
    lord_idx = zodiac_signs.index(lord_sign)

    # Distance from lagna to lord (in signs, 1-indexed)
    dist = (lord_idx - lagna_idx) % 12  # 0-11
    if dist == 0:
        dist = 12

    # Arudha = same distance from lord
    arudha_idx = (lord_idx + dist) % 12

    # Special rule: if Arudha falls on Lagna or 7th from Lagna, move 10 signs
    seventh_idx = (lagna_idx + 6) % 12
    if arudha_idx == lagna_idx or arudha_idx == seventh_idx:
        arudha_idx = (arudha_idx + 9) % 12  # +10 signs (−2 from same)

    arudha_sign = zodiac_signs[arudha_idx]
    arudha_house = (arudha_idx - lagna_idx) % 12 + 1
    return arudha_sign, arudha_house
