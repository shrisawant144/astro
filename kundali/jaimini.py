# jaimini.py
"""
Jaimini Charakaraka (7 significators) and Karakamsa Lagna.
Based on the Jaimini Sutras, using the highest degrees (or lowest for nodes) to determine the karakas.
"""

from constants import short_to_full, zodiac_signs
from utils import get_navamsa_sign


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
