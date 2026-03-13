# utils.py

import re
from .constants import (
    ZODIAC_SIGNS, SIGN_LORDS, DIGNITY_TABLE, FULL_TO_SHORT,
    NAKSHATRAS, NAKSHATRA_LORDS, NAKSHATRA_DEITIES, NAKSHATRA_QUALITIES
)

def get_navamsa_sign(deg: float) -> str:
    rasi_idx = int(deg // 30)
    deg_in_rasi = deg % 30
    nav_size = 30.0 / 9
    navamsa_in_rasi = int(deg_in_rasi / nav_size)
    start_nav_idx = [0, 9, 6, 3][rasi_idx % 4]
    nav_sign_idx = (start_nav_idx + navamsa_in_rasi) % 12
    return ZODIAC_SIGNS[nav_sign_idx]

def get_dignity(planet: str, sign: str) -> str:
    if not sign or planet not in DIGNITY_TABLE:
        return "Neutral"
    table = DIGNITY_TABLE[planet]
    if sign == table.get("exalt"):
        return "Exalted"
    if sign in table.get("own", []):
        return "Own"
    if sign == table.get("deb"):
        return "Debilitated"
    lord = SIGN_LORDS.get(sign, "")
    if lord in table.get("friends", []):
        return "Friendly"
    if lord in table.get("enemies", []):
        return "Enemy"
    return "Neutral"

def safe_sign_index(sign: str) -> int:
    return ZODIAC_SIGNS.index(sign) if sign in ZODIAC_SIGNS else 0

def has_aspect(planet_house: int, target_house: int, planet: str) -> bool:
    if planet_house == 0 or target_house == 0:
        return False
    diff = (target_house - planet_house) % 12
    if planet == "Ma":
        return diff in [4, 7, 8]
    if planet == "Ju":
        return diff in [5, 7, 9]
    if planet == "Sa":
        return diff in [3, 7, 10]
    return diff == 7

def get_nakshatra_lord(nakshatra: str) -> str:
    try:
        idx = NAKSHATRAS.index(nakshatra)
        return NAKSHATRA_LORDS[idx]
    except ValueError:
        return ""

def get_nakshatra_deity(nakshatra: str) -> str:
    return NAKSHATRA_DEITIES.get(nakshatra, "Unknown")

def get_nakshatra_meaning(nakshatra: str, planet: str) -> str:
    qualities = NAKSHATRA_QUALITIES.get(nakshatra, {})
    quality_prefix = ""
    if qualities:
        animal = qualities.get("animal", "")
        guna = qualities.get("guna", "")
        temperament = qualities.get("temperament", "")
        quality_prefix = f"[{animal}, {guna} guna, {temperament}] "
    meanings = {
        "Ashwini": "Spouse may be a healer, fast-moving, or involved in medicine.",
        "Bharani": "Spouse could be intense, transformative, or associated with cycles of life.",
        "Krittika": "Spouse may have a sharp intellect, be a provider, or have a fiery nature.",
        "Rohini": "Spouse likely creative, nurturing, and attracted to beauty/luxury.",
        "Mrigashira": "Spouse may be searching, curious, or have a restless energy.",
        "Ardra": "Spouse could be stormy, passionate, or bring sudden changes.",
        "Punarvasu": "Spouse may bring renewal, optimism, and a return to joy.",
        "Pushya": "Spouse likely nurturing, protective, and family-oriented.",
        "Ashlesha": "Spouse may be cunning, wise, or have deep intuitive powers.",
        "Magha": "Spouse could be proud, regal, or connected to ancestry.",
        "Purva Phalguni": "Spouse likely romantic, pleasure-seeking, and socially active.",
        "Uttara Phalguni": "Spouse may be stable, reliable, and focused on long-term growth.",
        "Hasta": "Spouse could be skilled with hands, artistic, or dexterous.",
        "Chitra": "Spouse likely artistic, charismatic, and visually striking.",
        "Swati": "Spouse may be independent, adaptable, and drawn to foreign things.",
        "Vishakha": "Spouse could be determined, competitive, and goal-oriented.",
        "Anuradha": "Spouse likely devoted, friendly, and successful in partnerships.",
        "Jyeshtha": "Spouse may be senior, authoritative, or protective.",
        "Mula": "Spouse could be investigative, rooted, or transformative.",
        "Purva Ashadha": "Spouse likely victorious, influential, and philosophical.",
        "Uttara Ashadha": "Spouse may be enduring, righteous, and universally respected.",
        "Shravana": "Spouse could be learned, listening, and connected to knowledge.",
        "Dhanishta": "Spouse likely musical, wealthy, and fame-oriented.",
        "Shatabhisha": "Spouse may be healing, mysterious, or involved in research.",
        "Purva Bhadrapada": "Spouse could be spiritual, eccentric, or dual-natured.",
        "Uttara Bhadrapada": "Spouse likely grounded, deep, and connected to water.",
        "Revati": "Spouse may be nurturing, boundary-less, and compassionate."
    }
    base_meaning = meanings.get(nakshatra, f"Unique {nakshatra} influence.")
    return quality_prefix + base_meaning



