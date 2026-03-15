# nakshatra.py
"""
Nakshatra (lunar mansion) constants and helper functions.
Used for refining spouse descriptions and general nakshatra analysis.
"""

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = [
    "Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me",
    "Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me",
    "Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"
]

NAKSHATRA_DEITIES = {
    "Ashwini": "Ashwini Kumaras (divine physicians)",
    "Bharani": "Yama (god of death)",
    "Krittika": "Agni (fire god)",
    "Rohini": "Brahma (creator) or Prajapati",
    "Mrigashira": "Soma (moon god)",
    "Ardra": "Rudra (storm god)",
    "Punarvasu": "Aditi (mother of gods)",
    "Pushya": "Brihaspati (guru of gods)",
    "Ashlesha": "Nagas (serpents)",
    "Magha": "Pitris (ancestors)",
    "Purva Phalguni": "Bhaga (god of enjoyment)",
    "Uttara Phalguni": "Aryaman (god of contracts)",
    "Hasta": "Savitr (sun god)",
    "Chitra": "Vishvakarma (divine architect)",
    "Swati": "Vayu (wind god)",
    "Vishakha": "Indra-Agni (dual deities)",
    "Anuradha": "Mitra (god of friendship)",
    "Jyeshtha": "Indra (king of gods)",
    "Mula": "Nirriti (goddess of dissolution)",
    "Purva Ashadha": "Apas (water goddesses)",
    "Uttara Ashadha": "Vishvadevas (universal gods)",
    "Shravana": "Vishnu (preserver)",
    "Dhanishta": "Vasus (eight deities)",
    "Shatabhisha": "Varuna (god of cosmic waters)",
    "Purva Bhadrapada": "Aja Ekapada (one-footed serpent)",
    "Uttara Bhadrapada": "Ahir Budhnya (serpent of the deep)",
    "Revati": "Pushan (nourisher)",
}

NAKSHATRA_QUALITIES = {
    "Ashwini": {"animal": "Horse (male)", "guna": "Sattvic", "temperament": "Swift, healing, initiating"},
    "Bharani": {"animal": "Elephant (male)", "guna": "Rajasic", "temperament": "Intense, transformative, creative"},
    "Krittika": {"animal": "Sheep (female)", "guna": "Rajasic", "temperament": "Sharp, fiery, purifying"},
    "Rohini": {"animal": "Serpent (male)", "guna": "Rajasic", "temperament": "Creative, nurturing, fertile"},
    "Mrigashira": {"animal": "Serpent (female)", "guna": "Sattvic", "temperament": "Searching, gentle, curious"},
    "Ardra": {"animal": "Dog (female)", "guna": "Tamasic", "temperament": "Stormy, passionate, transformative"},
    "Punarvasu": {"animal": "Cat (female)", "guna": "Sattvic", "temperament": "Renewal, optimistic, returning"},
    "Pushya": {"animal": "Goat (male)", "guna": "Sattvic", "temperament": "Nourishing, protective, generous"},
    "Ashlesha": {"animal": "Cat (male)", "guna": "Tamasic", "temperament": "Cunning, wise, serpentine"},
    "Magha": {"animal": "Rat (male)", "guna": "Tamasic", "temperament": "Regal, ancestral, proud"},
    "Purva Phalguni": {"animal": "Rat (female)", "guna": "Rajasic", "temperament": "Romantic, creative, pleasure-seeking"},
    "Uttara Phalguni": {"animal": "Cow (male)", "guna": "Rajasic", "temperament": "Stable, contractual, reliable"},
    "Hasta": {"animal": "Buffalo (female)", "guna": "Sattvic", "temperament": "Skillful, dexterous, crafty"},
    "Chitra": {"animal": "Tiger (female)", "guna": "Rajasic", "temperament": "Artistic, brilliant, charismatic"},
    "Swati": {"animal": "Buffalo (male)", "guna": "Sattvic", "temperament": "Independent, flexible, scattered"},
    "Vishakha": {"animal": "Tiger (male)", "guna": "Rajasic", "temperament": "Determined, competitive, goal-driven"},
    "Anuradha": {"animal": "Deer (female)", "guna": "Sattvic", "temperament": "Devoted, friendly, successful"},
    "Jyeshtha": {"animal": "Deer (male)", "guna": "Tamasic", "temperament": "Senior, authoritative, protective"},
    "Mula": {"animal": "Dog (male)", "guna": "Tamasic", "temperament": "Investigative, destructive, rooted"},
    "Purva Ashadha": {"animal": "Monkey (male)", "guna": "Rajasic", "temperament": "Victorious, influential, invigorating"},
    "Uttara Ashadha": {"animal": "Mongoose (male)", "guna": "Sattvic", "temperament": "Enduring, universal, righteous"},
    "Shravana": {"animal": "Monkey (female)", "guna": "Sattvic", "temperament": "Learned, listening, connected"},
    "Dhanishta": {"animal": "Lion (female)", "guna": "Rajasic", "temperament": "Musical, wealthy, ambitious"},
    "Shatabhisha": {"animal": "Horse (female)", "guna": "Tamasic", "temperament": "Healing, secretive, philosophical"},
    "Purva Bhadrapada": {"animal": "Lion (male)", "guna": "Rajasic", "temperament": "Spiritual, eccentric, fiery"},
    "Uttara Bhadrapada": {"animal": "Cow (female)", "guna": "Sattvic", "temperament": "Grounded, deep, watery"},
    "Revati": {"animal": "Elephant (female)", "guna": "Sattvic", "temperament": "Nurturing, compassionate, journeying"},
}

def get_nakshatra_lord(nakshatra):
    """Return the planet code ruling the given nakshatra."""
    try:
        idx = NAKSHATRAS.index(nakshatra)
        return NAKSHATRA_LORDS[idx]
    except ValueError:
        return ""

def get_nakshatra_deity(nakshatra):
    """Return the deity associated with a nakshatra."""
    return NAKSHATRA_DEITIES.get(nakshatra, "Unknown")

def get_nakshatra_meaning(nakshatra, planet):
    """Return spouse-related meaning for a given nakshatra, enriched with animal symbol and guna."""
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
        "Revati": "Spouse may be nurturing, boundary-less, and compassionate.",
    }
    base_meaning = meanings.get(nakshatra, f"Unique {nakshatra} influence.")
    return quality_prefix + base_meaning