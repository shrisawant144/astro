# muhurtha.py
"""
Muhurtha (electional astrology) module.

Covers:
  - Tarabala   : Auspiciousness based on count of current nakshatra from birth nakshatra
  - Chandrabala: Moon sign count from natal Moon sign (1-12)
  - Panchaka   : 5 inauspicious combinations based on Panchanga elements
  - Panchanga  : Tithi, Vara, Nakshatra, Yoga, Karana for any JD
  - Muhurtha evaluator: Score a time window for overall auspiciousness
"""

import swisseph as swe
from .nakshatra import NAKSHATRAS, TARA_NAMES

# ─── Panchanga constants ──────────────────────────────────────────────────────

VARA_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
VARA_LORDS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya",
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]

KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja",
    "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna",
]

# Auspicious/inauspicious tithis for Muhurtha
INAUSPICIOUS_TITHIS = {4, 8, 9, 12, 14}   # Chaturthi, Ashtami, Navami, Dwadashi, Chaturdashi
AUSPICIOUS_TITHIS   = {2, 3, 5, 7, 10, 11, 13}

# Inauspicious varas (days)
INAUSPICIOUS_VARAS  = {"Tuesday", "Saturday"}  # for general auspicious events

# Auspicious yogas (index 0-based → yoga number 1-27)
INAUSPICIOUS_YOGAS  = {"Vishkambha", "Atiganda", "Shula", "Ganda", "Vyaghata",
                        "Vajra", "Vyatipata", "Parigha", "Vaidhriti"}
AUSPICIOUS_YOGAS    = {"Priti", "Ayushman", "Saubhagya", "Shobhana", "Sukarma",
                       "Dhriti", "Siddhi", "Harshana", "Vriddhi", "Dhruva",
                       "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra"}

# Inauspicious karana
INAUSPICIOUS_KARANAS = {"Vishti"}  # Bhadra / Vishti karana is most inauspicious

# Auspicious nakshatras for general events
AUSPICIOUS_NAKSHATRAS = {
    "Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Revati",
}
INAUSPICIOUS_NAKSHATRAS = {
    "Bharani", "Ardra", "Ashlesha", "Magha", "Vishakha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Purva Bhadrapada",
}

# ─── Panchanga calculation ────────────────────────────────────────────────────

def get_panchanga(jd, lat=0.0, lon=0.0):
    """
    Calculate Panchanga (five elements) for a given Julian Day.

    Returns dict with:
      tithi, tithi_name, vara, vara_name, vara_lord,
      nakshatra, nakshatra_idx, yoga, yoga_name, karana, karana_name,
      moon_lon, sun_lon
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    sun_lon  = swe.calc_ut(jd, swe.SUN,  flags)[0][0]
    moon_lon = swe.calc_ut(jd, swe.MOON, flags)[0][0]

    # Tithi: each tithi = 12° of Moon-Sun longitude difference
    diff = (moon_lon - sun_lon) % 360
    tithi = int(diff / 12) + 1  # 1-30

    # Vara (day of week): 0=Sun, 1=Mon ... 6=Sat
    jd_int = int(jd + 0.5)
    vara = int(jd_int % 7)  # Rough; corrected via weekday offset
    # Swiss ephemeris gives Julian Day; day of week formula:
    vara_day = int((jd + 1.5) % 7)  # 0=Mon ... 6=Sun
    # Convert to Sun=0 standard
    vara_day_sun = (vara_day + 1) % 7

    # Nakshatra: 27 nakshatras, each 13°20'
    nak_span = 360 / 27
    nak_idx  = int(moon_lon / nak_span) % 27
    nakshatra = NAKSHATRAS[nak_idx]

    # Yoga: (Sun + Moon) / (360/27)
    yoga_lon = (sun_lon + moon_lon) % 360
    yoga_idx = int(yoga_lon / (360 / 27)) % 27
    yoga_name = YOGA_NAMES[yoga_idx]

    # Karana: half-tithi (each 6°)
    karana_idx = int(diff / 6) % 11
    karana_name = KARANA_NAMES[karana_idx]

    return {
        "tithi":        tithi,
        "tithi_name":   TITHI_NAMES[(tithi - 1) % 15],
        "vara":         vara_day_sun,
        "vara_name":    VARA_NAMES[vara_day_sun],
        "vara_lord":    VARA_LORDS[vara_day_sun],
        "nakshatra":    nakshatra,
        "nakshatra_idx": nak_idx,
        "yoga":         yoga_idx + 1,
        "yoga_name":    yoga_name,
        "karana":       karana_idx,
        "karana_name":  karana_name,
        "moon_lon":     moon_lon,
        "sun_lon":      sun_lon,
    }


# ─── Tarabala ─────────────────────────────────────────────────────────────────

TARABALA_SCORES = {
    1: (3, "Janma – Powerful but intense; caution for new ventures"),
    2: (5, "Sampat – Wealth and prosperity; excellent"),
    3: (1, "Vipat – Danger; avoid important work"),
    4: (4, "Kshema – Well-being; good for health and family"),
    5: (2, "Pratyak – Obstacles; avoid travel and new starts"),
    6: (5, "Sadhana – Achievement; success through effort"),
    7: (1, "Naidhana – Death-like; avoid all important events"),
    8: (4, "Mitra – Friendly; good for social activities"),
    9: (5, "Parama Mitra – Best friend; ideal for all purposes"),
}

def calculate_tarabala(birth_nak_idx, current_nak_idx):
    """
    Calculate Tarabala (star strength) for the current nakshatra.

    Args:
        birth_nak_idx (int): Nakshatra index at birth (0-26).
        current_nak_idx (int): Current nakshatra index (0-26).

    Returns:
        dict: {tara, tara_name, score, description}
    """
    diff = (current_nak_idx - birth_nak_idx) % 27
    tara = diff % 9 + 1
    tara_name = TARA_NAMES[tara]
    score, description = TARABALA_SCORES[tara]
    return {
        "tara":        tara,
        "tara_name":   tara_name,
        "score":       score,   # 1-5
        "description": description,
    }


# ─── Chandrabala ──────────────────────────────────────────────────────────────

CHANDRABALA_SCORES = {
    1:  (1, "Same sign as natal Moon — very intense, avoid major decisions"),
    2:  (3, "2nd from natal Moon — moderate"),
    3:  (5, "3rd from natal Moon — auspicious"),
    4:  (3, "4th from natal Moon — moderate"),
    5:  (5, "5th from natal Moon — auspicious"),
    6:  (1, "6th from natal Moon — inauspicious, avoid"),
    7:  (5, "7th from natal Moon — auspicious"),
    8:  (1, "8th from natal Moon — highly inauspicious"),
    9:  (5, "9th from natal Moon — most auspicious"),
    10: (3, "10th from natal Moon — moderate"),
    11: (5, "11th from natal Moon — gain and success"),
    12: (1, "12th from natal Moon — loss and obstacles"),
}

def calculate_chandrabala(natal_moon_sign_idx, current_moon_sign_idx):
    """
    Calculate Chandrabala (Moon strength) for an event.

    Args:
        natal_moon_sign_idx (int): Moon sign at birth (0-11, Aries=0).
        current_moon_sign_idx (int): Current Moon sign index (0-11).

    Returns:
        dict: {count, score, description}
    """
    count = (current_moon_sign_idx - natal_moon_sign_idx) % 12 + 1
    score, description = CHANDRABALA_SCORES.get(count, (3, "Neutral"))
    return {
        "count":       count,
        "score":       score,   # 1-5
        "description": description,
    }


# ─── Panchaka ─────────────────────────────────────────────────────────────────

PANCHAKA_TYPES = {
    0: ("Mrityu Panchaka",  "Death-like; very inauspicious"),
    2: ("Agni Panchaka",    "Fire accidents; avoid fire-related activities"),
    4: ("Raja Panchaka",    "Obstacles from authority; avoid government dealings"),
    6: ("Chora Panchaka",   "Theft and deception; protect valuables"),
    8: ("Roga Panchaka",    "Illness; avoid health-related risks"),
}

def calculate_panchaka(tithi, vara, nakshatra_idx, lagna_sign_idx, moon_sign_idx):
    """
    Check if current moment has Panchaka dosha.

    Panchaka = remainder when (Vara + Tithi + Nakshatra + Lagna + Moon sign) / 9

    Args:
        tithi (int): Current tithi (1-30).
        vara (int): Day of week (0=Sun ... 6=Sat).
        nakshatra_idx (int): Current Moon nakshatra (0-26).
        lagna_sign_idx (int): Ascendant sign index (0-11).
        moon_sign_idx (int): Current Moon sign (0-11).

    Returns:
        dict: {has_panchaka, type, description} or {has_panchaka: False}
    """
    total = (vara + 1) + tithi + (nakshatra_idx + 1) + (lagna_sign_idx + 1) + (moon_sign_idx + 1)
    remainder = total % 9

    if remainder in PANCHAKA_TYPES:
        ptype, description = PANCHAKA_TYPES[remainder]
        return {
            "has_panchaka": True,
            "remainder":    remainder,
            "type":         ptype,
            "description":  description,
        }
    return {"has_panchaka": False, "remainder": remainder, "type": None, "description": "No Panchaka"}


# ─── Muhurtha Evaluator ───────────────────────────────────────────────────────

def evaluate_muhurtha(jd, birth_result, lat=0.0, lon=0.0, purpose="general"):
    """
    Evaluate a specific time moment for Muhurtha (auspiciousness).

    Args:
        jd (float): Julian Day of the proposed time.
        birth_result (dict): Kundali result dict (for natal Moon sign/nakshatra).
        lat (float): Latitude (for ascendant calc, optional).
        lon (float): Longitude (for ascendant calc, optional).
        purpose (str): Purpose type — 'general', 'marriage', 'business', 'travel',
                       'medical', 'property', 'education'.

    Returns:
        dict: {
            panchanga, tarabala, chandrabala, panchaka,
            total_score, max_score, grade, summary, warnings
        }
    """
    panchanga = get_panchanga(jd, lat, lon)
    warnings  = []
    score     = 0
    max_score = 100

    # --- Panchanga element scores (each 0-10) ---

    # 1. Vara (day) — 10 pts
    vara_name = panchanga["vara_name"]
    if vara_name in INAUSPICIOUS_VARAS:
        vara_score = 3
        warnings.append(f"Inauspicious vara: {vara_name}")
    elif vara_name in ("Monday", "Wednesday", "Thursday", "Friday"):
        vara_score = 9
    else:
        vara_score = 7  # Sunday
    score += vara_score

    # 2. Tithi — 15 pts
    tithi_no = panchanga["tithi"]
    tithi_base = ((tithi_no - 1) % 15) + 1
    if tithi_base in INAUSPICIOUS_TITHIS:
        tithi_score = 3
        warnings.append(f"Inauspicious tithi: {panchanga['tithi_name']} ({tithi_no})")
    elif tithi_base in AUSPICIOUS_TITHIS:
        tithi_score = 14
    else:
        tithi_score = 8
    score += tithi_score

    # 3. Nakshatra — 20 pts
    nak = panchanga["nakshatra"]
    if nak in INAUSPICIOUS_NAKSHATRAS:
        nak_score = 4
        warnings.append(f"Inauspicious nakshatra: {nak}")
    elif nak in AUSPICIOUS_NAKSHATRAS:
        nak_score = 19
    else:
        nak_score = 12
    score += nak_score

    # 4. Yoga — 15 pts
    yoga_name = panchanga["yoga_name"]
    if yoga_name in INAUSPICIOUS_YOGAS:
        yoga_score = 2
        warnings.append(f"Inauspicious yoga: {yoga_name}")
    elif yoga_name in AUSPICIOUS_YOGAS:
        yoga_score = 14
    else:
        yoga_score = 8
    score += yoga_score

    # 5. Karana — 10 pts
    karana_name = panchanga["karana_name"]
    if karana_name in INAUSPICIOUS_KARANAS:
        karana_score = 2
        warnings.append(f"Inauspicious karana: Vishti (Bhadra)")
    else:
        karana_score = 9
    score += karana_score

    # --- Personal factors ---

    # 6. Tarabala — 15 pts
    birth_nak_idx = 0
    birth_planets = birth_result.get("planets", {})
    if "Mo" in birth_planets:
        mo_lon = birth_planets["Mo"].get("full_lon", 0)
        birth_nak_idx = int(mo_lon / (360 / 27)) % 27
    natal_moon_sign_idx = int(birth_planets.get("Mo", {}).get("full_lon", 0) / 30) % 12

    tara_data = calculate_tarabala(birth_nak_idx, panchanga["nakshatra_idx"])
    tara_score = tara_data["score"] * 3  # scale 1-5 → 3-15
    if tara_data["score"] <= 1:
        warnings.append(f"Poor Tarabala: {tara_data['tara_name']}")
    score += tara_score

    # 7. Chandrabala — 15 pts
    current_moon_sign_idx = int(panchanga["moon_lon"] / 30) % 12
    chandra_data = calculate_chandrabala(natal_moon_sign_idx, current_moon_sign_idx)
    chandra_score = chandra_data["score"] * 3  # scale 1-5 → 3-15
    if chandra_data["score"] <= 1:
        warnings.append(f"Poor Chandrabala: {chandra_data['description']}")
    score += chandra_score

    # 8. Panchaka check — can reduce score
    lagna_sign_idx = int(birth_result.get("lagna_full_lon", 0) / 30) % 12
    panchaka_data = calculate_panchaka(
        panchanga["tithi"], panchanga["vara"],
        panchanga["nakshatra_idx"], lagna_sign_idx, current_moon_sign_idx
    )
    if panchaka_data["has_panchaka"]:
        score = max(0, score - 15)
        warnings.append(f"Panchaka Dosha: {panchaka_data['type']} — {panchaka_data['description']}")

    # --- Purpose-specific adjustments ---
    purpose_adjustments = {
        "marriage":   {"good_vara": {"Wednesday", "Thursday", "Friday"},
                       "bad_vara":  {"Tuesday", "Saturday", "Sunday"}},
        "business":   {"good_vara": {"Wednesday", "Thursday"},
                       "bad_vara":  {"Tuesday", "Saturday"}},
        "travel":     {"good_vara": {"Wednesday", "Thursday", "Friday"},
                       "bad_vara":  {"Tuesday"}},
        "medical":    {"good_vara": {"Monday", "Wednesday", "Thursday"},
                       "bad_vara":  {"Tuesday", "Saturday"}},
        "education":  {"good_vara": {"Wednesday", "Thursday"},
                       "bad_vara":  set()},
        "property":   {"good_vara": {"Wednesday", "Thursday", "Friday"},
                       "bad_vara":  {"Tuesday", "Saturday"}},
    }
    if purpose in purpose_adjustments:
        adj = purpose_adjustments[purpose]
        if vara_name in adj["good_vara"]:
            score = min(max_score, score + 5)
        elif vara_name in adj["bad_vara"]:
            score = max(0, score - 5)
            warnings.append(f"Vara unfavorable for {purpose}: {vara_name}")

    # Clamp to max
    score = min(max_score, score)

    # Grade
    if score >= 80:
        grade = "Excellent"
    elif score >= 65:
        grade = "Good"
    elif score >= 50:
        grade = "Average"
    elif score >= 35:
        grade = "Below Average"
    else:
        grade = "Inauspicious"

    # Summary
    summary_parts = [
        f"Vara: {vara_name} ({panchanga['vara_lord']})",
        f"Tithi: {panchanga['tithi_name']} ({tithi_no})",
        f"Nakshatra: {nak}",
        f"Yoga: {yoga_name}",
        f"Karana: {karana_name}",
        f"Tarabala: {tara_data['tara_name']} ({tara_data['score']}/5)",
        f"Chandrabala: {chandra_data['count']}th ({chandra_data['score']}/5)",
    ]
    if panchaka_data["has_panchaka"]:
        summary_parts.append(f"⚠ {panchaka_data['type']}")

    return {
        "panchanga":    panchanga,
        "tarabala":     tara_data,
        "chandrabala":  chandra_data,
        "panchaka":     panchaka_data,
        "total_score":  score,
        "max_score":    max_score,
        "grade":        grade,
        "purpose":      purpose,
        "summary":      " | ".join(summary_parts),
        "warnings":     warnings,
    }


def find_best_muhurtha(birth_result, start_jd, days=7, purpose="general",
                       lat=0.0, lon=0.0, min_score=65):
    """
    Search for the best Muhurtha windows over a range of days.

    Scans every 2 hours and returns windows scoring above min_score.

    Args:
        birth_result (dict): Kundali result for the native.
        start_jd (float): Start Julian Day.
        days (int): Number of days to search.
        purpose (str): Event purpose.
        lat, lon (float): Location for calculations.
        min_score (int): Minimum score threshold.

    Returns:
        list of dicts sorted by score descending.
    """
    results = []
    step = 2 / 24.0  # 2-hour steps
    total_steps = int(days * 24 / 2)

    for i in range(total_steps):
        jd_check = start_jd + i * step
        try:
            m = evaluate_muhurtha(jd_check, birth_result, lat, lon, purpose)
            if m["total_score"] >= min_score:
                # Convert JD to calendar date
                cal = swe.revjul(jd_check, swe.GREG_CAL)
                m["datetime_str"] = (
                    f"{int(cal[0])}-{int(cal[1]):02d}-{int(cal[2]):02d} "
                    f"{int(cal[3]):02d}:{int((cal[3] % 1) * 60):02d}"
                )
                m["jd"] = jd_check
                results.append(m)
        except Exception:
            continue

    results.sort(key=lambda x: x["total_score"], reverse=True)
    return results[:20]  # Top 20 windows
