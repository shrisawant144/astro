# neecha_bhanga.py
"""
Neecha Bhanga (cancellation of debilitation) detection.
Based on Brihat Parashara Hora Shastra, Chapter 28.
"""

from constants import NEECHA_BHANGA_INFO, sign_lords, zodiac_signs


def check_neecha_bhanga(planet_code, planet_data, house_planets, lagna_idx, moon_house):
    """Return True if the debilitated planet's debilitation is cancelled
    (Neecha Bhanga Raja Yoga).

    Seven Parashari rules are checked:
      A – The lord of the debilitation sign is in a kendra from Lagna or Moon.
      B – The planet that is exalted in the debilitation sign is in a kendra
          from Lagna or Moon.
      C – The debilitated planet itself is in a kendra from Lagna or Moon.
      D – The lord of the sign where the debilitated planet would be exalted
          is in a kendra from Lagna or Moon.
      E – The debilitated planet is aspected by its debilitation sign lord.
      F – The sign dispositor (lord of deb sign) is itself exalted.
      G – The debilitated planet is in mutual aspect with its exaltation sign lord.
    Any one rule satisfied cancels the debilitation.
    """
    if planet_code not in NEECHA_BHANGA_INFO:
        return False
    if planet_code not in planet_data:
        return False
    if planet_data[planet_code]["dignity"] != "Debilitated":
        return False  # not debilitated, no cancellation needed

    kendra_from_lagna = {1, 4, 7, 10}
    # Kendras from Moon (houses 1,4,7,10 counted from Moon's house)
    if moon_house is not None:
        kendra_from_moon = {
            ((moon_house - 1 + offset) % 12) + 1 for offset in (0, 3, 6, 9)
        }
    else:
        kendra_from_moon = set()

    def planet_in_kendra(pl_code):
        """Return True if pl_code is found in a kendra from Lagna or Moon."""
        for h, plist in house_planets.items():
            if pl_code in plist:
                return h in kendra_from_lagna or h in kendra_from_moon
        return False

    def get_planet_house(pl_code):
        """Return house number (1-12) where planet is placed, or None."""
        for h, plist in house_planets.items():
            if pl_code in plist:
                return h
        return None

    def planets_in_mutual_aspect(pl1_house, pl2_house):
        """Return True if two house positions are exactly 7 houses apart (7th aspect)."""
        if pl1_house is None or pl2_house is None:
            return False
        return (
            abs(pl1_house - pl2_house) % 12 == 6
        )  # 7th house = 6 positions apart in 0-indexed

    def planet_aspects_house(aspecting_code, aspecting_house, target_house):
        """Return True if aspecting planet (from its house) aspects the target house.
        All planets have 7th aspect. Mars also 4th & 8th. Jupiter 5th & 9th. Saturn 3rd & 10th."""
        if aspecting_house is None or target_house is None:
            return False
        diff = (target_house - aspecting_house) % 12
        # 7th aspect = 6 houses ahead (all planets)
        aspect_offsets = {6}
        if aspecting_code == "Ma":
            aspect_offsets.update({3, 7})  # 4th and 8th
        elif aspecting_code == "Ju":
            aspect_offsets.update({4, 8})  # 5th and 9th
        elif aspecting_code == "Sa":
            aspect_offsets.update({2, 9})  # 3rd and 10th
        return diff in aspect_offsets

    deb_lord, exalt_planet = NEECHA_BHANGA_INFO[planet_code]

    # Exaltation sign lords (lord of sign where planet would be exalted)
    EXALT_SIGNS = {
        "Su": "Aries",
        "Mo": "Taurus",
        "Ma": "Capricorn",
        "Me": "Virgo",
        "Ju": "Cancer",
        "Ve": "Pisces",
        "Sa": "Libra",
    }
    exalt_sign = EXALT_SIGNS.get(planet_code)
    exalt_sign_lord = sign_lords.get(exalt_sign) if exalt_sign else None

    # Rule A – Debilitation lord in kendra
    if deb_lord and planet_in_kendra(deb_lord):
        return True
    # Rule B – Planet exalted in deb sign, in kendra
    if exalt_planet and exalt_planet != deb_lord and planet_in_kendra(exalt_planet):
        return True
    # Rule C – Debilitated planet itself in kendra
    if planet_in_kendra(planet_code):
        return True
    # Rule D – Lord of exaltation sign of the deb planet is in kendra
    if (
        exalt_sign_lord
        and exalt_sign_lord != deb_lord
        and planet_in_kendra(exalt_sign_lord)
    ):
        return True
    # Rule E – Debilitated planet is aspected by its deb sign lord
    deb_lord_house = get_planet_house(deb_lord) if deb_lord else None
    planet_house = get_planet_house(planet_code)
    if deb_lord and deb_lord_house is not None and planet_house is not None:
        if planet_aspects_house(deb_lord, deb_lord_house, planet_house):
            return True
    # Rule F – The sign dispositor (deb lord) is itself exalted
    if deb_lord and deb_lord in planet_data:
        if planet_data[deb_lord].get("dignity") == "Exalt":
            return True
    # Rule G – Debilitated planet in mutual aspect with its exaltation sign lord
    if exalt_sign_lord and exalt_sign_lord != planet_code:
        exalt_lord_house = get_planet_house(exalt_sign_lord)
        if planets_in_mutual_aspect(planet_house, exalt_lord_house):
            return True
    return False
