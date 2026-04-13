# decisions.py
"""
Decision Engine — actionable life guidance from kundali data.

Nine decision categories synthesized from the full chart:
  1. Career     — best career path (10th house, D10, Atmakaraka)
  2. Marriage   — when to marry (dasha windows, transit triggers)
  3. Business   — good/bad periods for investments & ventures
  4. Health     — vulnerable periods (6th/8th lords, dasha)
  5. Travel     — best directions & relocation guidance
  6. Daily      — what to do today (transit + pancha pakshi)
  7. Compatibility — partner matching (Ashtakoot + dosha)
  8. Education  — best fields of study (4th/5th house, D24)
  9. Life Analysis — unified synthesis across all major domains

All functions accept the raw dict from calculate_kundali() and return
JSON-serializable dicts.
"""

import datetime

from .constants import (
    zodiac_signs,
    sign_lords,
    short_to_full,
    FUNCTIONAL_QUALITY,
)
from .utils import get_dignity, get_house_from_sign


# ===================================================================
# Helpers
# ===================================================================

def _lord_of(house_no, lagna_sign):
    """Return the short-code lord of *house_no* (1-12) for a given lagna."""
    idx = zodiac_signs.index(lagna_sign)
    sign = zodiac_signs[(idx + house_no - 1) % 12]
    return sign_lords[sign]


def _house_of_planet(planet, houses):
    """Return the house number (1-12) where *planet* is placed, or 0."""
    for h, plist in houses.items():
        if planet in plist:
            return int(h)
    return 0


def _planet_strength_label(planet, planets_data):
    """Return 'strong', 'moderate', or 'weak' based on dignity + retro + combust."""
    p = planets_data.get(planet, {})
    dig = p.get("dignity", "")
    score = 0
    if dig in ("Exalt", "Own"):
        score += 3
    elif dig == "Friend":
        score += 2
    elif dig in ("Neutral", ""):
        score += 1
    elif dig in ("Enemy", "Debilitated"):
        score -= 1
    if p.get("combust"):
        score -= 2
    if p.get("retro") and planet not in ("Ra", "Ke"):
        score -= 1
    if p.get("neecha_bhanga"):
        score += 1
    if score >= 3:
        return "strong"
    elif score >= 1:
        return "moderate"
    return "weak"


def _current_dasha_info(result):
    """Extract current mahadasha / antardasha as a dict."""
    vim = result.get("vimshottari", {})
    md = vim.get("current_md", "")
    ad = vim.get("current_ad", "")
    if isinstance(md, dict):
        md = md.get("lord", md.get("dasha_lord", str(md)))
    if isinstance(ad, dict):
        ad = ad.get("lord", ad.get("dasha_lord", str(ad)))
    return {"mahadasha": str(md), "antardasha": str(ad)}


def _sign_element(sign):
    """Return the element (Fire/Earth/Air/Water) for a zodiac sign."""
    fire = {"Aries", "Leo", "Sagittarius"}
    earth = {"Taurus", "Virgo", "Capricorn"}
    air = {"Gemini", "Libra", "Aquarius"}
    if sign in fire:
        return "Fire"
    if sign in earth:
        return "Earth"
    if sign in air:
        return "Air"
    return "Water"


def _ordinal(n):
    """Return a compact ordinal like 1st, 2nd, 3rd."""
    if 10 <= (n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _clean_items(items, limit=6):
    seen = set()
    cleaned = []
    for item in items or []:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _confidence_label(score):
    if score >= 85:
        return "High"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Moderate"
    return "Low"


def _attach_confidence(payload, supporting=None, limiting=None, base=48, result=None):
    supporting = _clean_items(supporting, limit=6)
    limiting = _clean_items(limiting, limit=4)

    score = base + min(28, len(supporting) * 8) - min(24, len(limiting) * 5)
    if not supporting:
        score -= 10

    if isinstance(result, dict):
        input_quality = result.get("input_quality", {}) or {}
        input_score = input_quality.get("score")
        if isinstance(input_score, (int, float)):
            if input_score >= 85:
                score += 4
            elif input_score >= 70:
                score += 1
            elif input_score < 55:
                score -= 8
            else:
                score -= 3

        rectification = result.get("birth_time_rectification", {}) or {}
        if rectification.get("applied"):
            supporting = _clean_items(
                supporting + ["Birth time rectification has been applied"], limit=6
            )
            score += 3
        elif rectification.get("confidence_score", 0) >= 75:
            limiting = _clean_items(
                limiting + ["Strong rectification signal is available but not applied"],
                limit=4,
            )
            score -= 4

    score = max(20, min(95, score))

    payload["confidence_score"] = score
    payload["confidence_label"] = _confidence_label(score)
    payload["confidence_factors"] = supporting
    if limiting:
        payload["confidence_limiters"] = limiting
    return payload


# ===================================================================
# 1. CAREER DECISIONS
# ===================================================================

_CAREER_MAP = {
    "Su": ["Government", "Administration", "Politics", "Leadership", "Medicine"],
    "Mo": ["Hospitality", "Nursing", "Public Relations", "Dairy", "Travel & Tourism"],
    "Ma": ["Military", "Engineering", "Surgery", "Sports", "Real Estate", "Police"],
    "Me": ["IT & Software", "Accounting", "Writing", "Teaching", "Commerce", "Media"],
    "Ju": ["Law", "Banking", "Education", "Consulting", "Philosophy", "Priesthood"],
    "Ve": ["Arts", "Fashion", "Entertainment", "Luxury Goods", "Beauty", "Music", "Film"],
    "Sa": ["Mining", "Agriculture", "Labour Management", "Oil & Gas", "Iron & Steel"],
    "Ra": ["Foreign Trade", "Aviation", "Technology", "Research", "Pharmaceuticals"],
    "Ke": ["Spiritual Work", "Alternative Medicine", "Occult", "IT (backend)", "Research"],
}

_SIGN_CAREER = {
    "Aries": ["Entrepreneurship", "Military", "Sports"],
    "Taurus": ["Finance", "Agriculture", "Luxury Goods", "Art"],
    "Gemini": ["Journalism", "Marketing", "Teaching", "IT"],
    "Cancer": ["Nursing", "Hospitality", "Real Estate", "Food"],
    "Leo": ["Government", "Entertainment", "Management"],
    "Virgo": ["Healthcare", "Accounting", "Quality Assurance", "Data Analysis"],
    "Libra": ["Law", "Diplomacy", "Fashion", "HR"],
    "Scorpio": ["Research", "Investigation", "Surgery", "Occult"],
    "Sagittarius": ["Education", "Travel", "Publishing", "Law"],
    "Capricorn": ["Corporate", "Engineering", "Government", "Mining"],
    "Aquarius": ["Technology", "Social Work", "Innovation", "Science"],
    "Pisces": ["Arts", "Healing", "Spirituality", "Marine", "Film"],
}


def get_career_decision(result):
    """Analyse the chart for career guidance.

    Examines 10th house lord, planets in 10th, D10, Atmakaraka,
    current dasha, and Ashtakavarga bindus.
    """
    lagna = result.get("lagna_sign", "Aries")
    planets = result.get("planets", {})
    houses = result.get("houses", {})
    d10 = result.get("d10", {})
    jaimini = result.get("jaimini", {})

    lord10 = _lord_of(10, lagna)
    lord10_sign = planets.get(lord10, {}).get("sign", "")
    lord10_strength = _planet_strength_label(lord10, planets)
    tenth_sign = zodiac_signs[(zodiac_signs.index(lagna) + 9) % 12]
    planets_in_10 = houses.get(10, [])

    fields = list(_CAREER_MAP.get(lord10, []))
    fields += _SIGN_CAREER.get(tenth_sign, [])
    for p in planets_in_10:
        fields += _CAREER_MAP.get(p, [])

    d10_insights = []
    if d10:
        d10_lord10_sign = d10.get(lord10, {}).get("sign", "")
        if d10_lord10_sign:
            d10_insights.append(
                f"10th lord {short_to_full.get(lord10, lord10)} in {d10_lord10_sign} in D10"
            )
        d10_su = d10.get("Su", {}).get("sign", "")
        if d10_su:
            d10_insights.append(f"Sun in {d10_su} in D10 -- public authority/visibility")

    ak = jaimini.get("atmakaraka", "")
    ak_fields = _CAREER_MAP.get(ak, [])

    dasha = _current_dasha_info(result)
    md_lord = dasha["mahadasha"]
    md_short = next((k for k, v in short_to_full.items() if v == md_lord), md_lord)
    dasha_career = _CAREER_MAP.get(md_short, [])

    akv = result.get("ashtakavarga", {})
    tenth_bindus = 0
    # Handle nested structure: ashtakavarga may have 'individual' or 'sav'
    individual = akv.get("individual", akv) if isinstance(akv, dict) else {}
    if isinstance(individual, dict):
        for p_name, p_data in individual.items():
            if isinstance(p_data, list) and len(p_data) >= 10:
                tenth_bindus += p_data[9]  # 10th house is index 9
            elif isinstance(p_data, dict) and isinstance(p_data.get(10), (int, float)):
                tenth_bindus += p_data.get(10, 0)

    seen = set()
    ranked_fields = []
    for f in fields:
        if f not in seen:
            seen.add(f)
            ranked_fields.append(f)

    career_lords = {lord10, _lord_of(1, lagna), "Su", "Sa"}
    career_lords_full = {short_to_full.get(c, c) for c in career_lords}
    good_period = md_lord in career_lords_full

    full10 = short_to_full.get(lord10, lord10)
    if lord10_strength == "strong":
        advice = f"Your 10th lord {full10} is strong -- you will naturally rise in your chosen field."
    elif lord10_strength == "moderate":
        advice = f"Your 10th lord {full10} has moderate strength -- steady growth with effort."
    else:
        advice = f"Your 10th lord {full10} is weak -- career success requires extra persistence."

    extras = []
    if "Sa" in planets_in_10:
        extras.append("Saturn in 10th gives long-lasting career but slow start.")
    if "Su" in planets_in_10:
        extras.append("Sun in 10th favours government or leadership roles.")
    if "Ju" in planets_in_10:
        extras.append("Jupiter in 10th blesses career with ethics and expansion.")
    if "Ra" in planets_in_10:
        extras.append("Rahu in 10th drives unconventional or foreign career paths.")
    if good_period:
        extras.append("Current dasha supports career changes -- act on opportunities.")
    else:
        extras.append("Current dasha is not primarily career-focused -- consolidate rather than switch.")
    advice = advice + " " + " ".join(extras)

    payload = {
        "tenth_house_sign": tenth_sign,
        "tenth_lord": full10,
        "tenth_lord_sign": lord10_sign,
        "tenth_lord_strength": lord10_strength,
        "planets_in_10th": [short_to_full.get(p, p) for p in planets_in_10],
        "recommended_fields": ranked_fields[:10],
        "atmakaraka": short_to_full.get(ak, ak),
        "atmakaraka_fields": ak_fields[:5],
        "d10_insights": d10_insights,
        "current_dasha": dasha,
        "dasha_career_affinity": dasha_career[:5],
        "good_period_for_career_change": good_period,
        "tenth_house_ashtakavarga_bindus": tenth_bindus,
        "advice": advice,
    }
    supporting = []
    limiting = []
    if lord10_sign:
        supporting.append(f"10th lord is placed in {lord10_sign}")
    if lord10_strength in ("strong", "moderate"):
        supporting.append(f"10th lord strength is {lord10_strength}")
    else:
        limiting.append("10th lord is weak")
    if d10_insights:
        supporting.append("D10 confirms career themes")
    else:
        limiting.append("D10 confirmation is limited")
    if dasha_career:
        supporting.append("Current dasha supports career themes")
    if isinstance(tenth_bindus, (int, float)) and tenth_bindus > 0:
        supporting.append(f"Ashtakavarga bindus available for 10th house ({tenth_bindus})")
    if not good_period:
        limiting.append("Current dasha favors consolidation over major career shifts")
    return _attach_confidence(payload, supporting, limiting, base=50, result=result)


# ===================================================================
# 2. MARRIAGE TIMING
# ===================================================================

def get_marriage_decision(result):
    """Analyse the chart for marriage timing and readiness."""
    lagna = result.get("lagna_sign", "Aries")
    planets = result.get("planets", {})
    houses = result.get("houses", {})
    navamsa = result.get("navamsa", {})

    lord7 = _lord_of(7, lagna)
    lord7_sign = planets.get(lord7, {}).get("sign", "")
    lord7_strength = _planet_strength_label(lord7, planets)
    venus_strength = _planet_strength_label("Ve", planets)
    planets_in_7 = houses.get(7, [])

    marriage_yogas = []
    for y in result.get("yogas", []):
        name = y.get("name", "") if isinstance(y, dict) else str(y)
        lower = name.lower()
        if any(w in lower for w in ("marriage", "spouse", "partner", "venus", "7th")):
            marriage_yogas.append(name)

    blockers = []
    for p in result.get("problems", []):
        name = (p.get("summary", "") or p.get("name", "")) if isinstance(p, dict) else str(p)
        lower = name.lower()
        if any(w in lower for w in ("mangal", "manglik", "kaal sarp", "kemdrum")):
            blockers.append(name)

    ve_d9 = navamsa.get("Ve", {})
    ve_d9_sign = ve_d9.get("sign", "")
    ve_d9_dignity = get_dignity("Ve", ve_d9_sign) if ve_d9_sign else ""

    timings = result.get("timings", {})
    marriage_periods_raw = timings.get("Marriage", [])
    marriage_periods = []
    for line in marriage_periods_raw:
        lower = line.lower()
        if "too young" in lower or "karmic seed" in lower or "formative" in lower:
            continue
        if "[past]" in lower:
            continue
        if "/" in line or "[future]" in lower or "[now]" in lower:
            marriage_periods.append(line)

    sade_sati = result.get("sade_sati", {})
    sade_sati_active = False
    if isinstance(sade_sati, dict):
        sade_sati_active = sade_sati.get("active", False) or sade_sati.get("running", False)
    elif isinstance(sade_sati, str):
        sade_sati_active = "active" in sade_sati.lower() or "running" in sade_sati.lower()

    dasha = _current_dasha_info(result)
    marriage_lords = {short_to_full.get(lord7, lord7), "Venus", "Jupiter", "Moon"}
    favorable_dasha = dasha["mahadasha"] in marriage_lords

    upapadha = result.get("upapadha_lagna", "")

    # Build advice
    parts = []
    if lord7_strength == "strong" and venus_strength == "strong":
        parts.append("Strong 7th lord and Venus indicate a happy and timely marriage.")
    elif lord7_strength == "weak" or venus_strength == "weak":
        parts.append("Weakness in 7th lord or Venus may cause delays -- remedies recommended.")
    else:
        parts.append("Moderate marriage indicators -- timing through dasha will be the key trigger.")
    if blockers:
        parts.append(f"Doshas detected ({', '.join(blockers[:3])}) -- consult remedies section.")
    if sade_sati_active:
        parts.append("Sade Sati is active -- marriage may face delays or require extra patience.")
    if favorable_dasha:
        parts.append("Current dasha is favorable for marriage -- actively pursue alliances.")
    else:
        parts.append("Current dasha is not primarily marriage-oriented -- wait for a favorable window.")

    payload = {
        "seventh_house_sign": zodiac_signs[(zodiac_signs.index(lagna) + 6) % 12],
        "seventh_lord": short_to_full.get(lord7, lord7),
        "seventh_lord_sign": lord7_sign,
        "seventh_lord_strength": lord7_strength,
        "venus_strength": venus_strength,
        "planets_in_7th": [short_to_full.get(p, p) for p in planets_in_7],
        "navamsa_venus": {"sign": ve_d9_sign, "dignity": ve_d9_dignity},
        "marriage_yogas": marriage_yogas,
        "marriage_blockers": blockers,
        "favorable_periods": marriage_periods[:8],
        "current_dasha": dasha,
        "favorable_dasha_for_marriage": favorable_dasha,
        "sade_sati_active": sade_sati_active,
        "upapadha_lagna": upapadha if isinstance(upapadha, str) else str(upapadha),
        "advice": " ".join(parts),
    }
    supporting = []
    limiting = []
    if lord7_sign:
        supporting.append(f"7th lord is placed in {lord7_sign}")
    if lord7_strength in ("strong", "moderate"):
        supporting.append(f"7th lord strength is {lord7_strength}")
    else:
        limiting.append("7th lord is weak")
    if venus_strength in ("strong", "moderate"):
        supporting.append(f"Venus strength is {venus_strength}")
    else:
        limiting.append("Venus is weak")
    if marriage_periods:
        supporting.append("Marriage timing windows are available")
    else:
        limiting.append("Marriage timing windows are thin")
    if favorable_dasha:
        supporting.append("Current dasha supports marriage")
    if ve_d9_sign:
        supporting.append("Navamsa Venus is available for confirmation")
    if blockers:
        limiting.append(f"Blocking factors present ({len(blockers)})")
    if sade_sati_active:
        limiting.append("Sade Sati may delay marriage decisions")
    return _attach_confidence(payload, supporting, limiting, base=50, result=result)


# ===================================================================
# 3. BUSINESS DECISIONS
# ===================================================================

def get_business_decision(result):
    """Analyse chart for business, investment, and financial timing."""
    lagna = result.get("lagna_sign", "Aries")
    planets = result.get("planets", {})
    houses = result.get("houses", {})

    lord2 = _lord_of(2, lagna)
    lord11 = _lord_of(11, lagna)
    lord9 = _lord_of(9, lagna)
    lord10 = _lord_of(10, lagna)
    lord5 = _lord_of(5, lagna)

    wealth_yogas = []
    for y in result.get("yogas", []):
        name = y.get("name", "") if isinstance(y, dict) else str(y)
        lower = name.lower()
        if any(w in lower for w in ("dhana", "lakshmi", "wealth", "kubera", "vasumati")):
            wealth_yogas.append(name)

    timings = result.get("timings", {})
    wealth_periods = timings.get("Major Wealth / Property", [])

    dasha = _current_dasha_info(result)
    md = dasha["mahadasha"]
    wealth_lords_full = {
        short_to_full.get(lord2, lord2),
        short_to_full.get(lord11, lord11),
        short_to_full.get(lord9, lord9),
        "Jupiter", "Venus", "Mercury",
    }
    good_for_business = md in wealth_lords_full

    transit_cal = result.get("transit_calendar", {})
    upcoming = transit_cal.get("summary_next_30_days", [])

    transits = result.get("transits", {})
    jup_transit = transits.get("Ju", transits.get("Jupiter", {}))
    jup_house = ""
    if isinstance(jup_transit, dict):
        jup_house = jup_transit.get("house_from_moon", "")

    muhurtha = result.get("muhurtha", {})
    muhurtha_score = 0
    if isinstance(muhurtha, dict):
        muhurtha_score = muhurtha.get("total_score", 0)

    spec_strength = _planet_strength_label(lord5, planets)

    # Build advice
    parts = []
    if wealth_yogas:
        parts.append(f"Wealth yogas present ({', '.join(wealth_yogas[:2])}) -- financial potential is strong.")
    else:
        parts.append("No major wealth yogas detected -- build wealth through steady effort.")
    if good_for_business:
        parts.append("Current dasha supports financial growth -- good time for investments.")
    else:
        parts.append("Current dasha is not primarily wealth-oriented -- avoid large risks.")
    if spec_strength == "strong":
        parts.append("5th lord is strong -- speculative investments may bring gains.")
    elif spec_strength == "weak":
        parts.append("5th lord is weak -- avoid speculative investments and gambling.")
    if isinstance(jup_house, int):
        if jup_house in (2, 5, 9, 11):
            parts.append(f"Jupiter transiting {jup_house}th from Moon -- expansion and gains likely.")
        elif jup_house in (6, 8, 12):
            parts.append(f"Jupiter transiting {jup_house}th from Moon -- be cautious with finances.")

    payload = {
        "second_lord": short_to_full.get(lord2, lord2),
        "eleventh_lord": short_to_full.get(lord11, lord11),
        "ninth_lord": short_to_full.get(lord9, lord9),
        "fifth_lord_speculation": short_to_full.get(lord5, lord5),
        "fifth_lord_strength": spec_strength,
        "wealth_yogas": wealth_yogas,
        "wealth_periods": wealth_periods[:8],
        "current_dasha": dasha,
        "good_period_for_business": good_for_business,
        "jupiter_transit_house": jup_house,
        "muhurtha_score": muhurtha_score,
        "upcoming_transits_30_days": upcoming[:10] if isinstance(upcoming, list) else [],
        "advice": " ".join(parts),
    }
    supporting = []
    limiting = []
    if wealth_yogas:
        supporting.append(f"Wealth yogas detected ({len(wealth_yogas)})")
    else:
        limiting.append("No major wealth yogas were detected")
    if good_for_business:
        supporting.append("Current dasha supports business growth")
    else:
        limiting.append("Current dasha is not wealth-oriented")
    if spec_strength in ("strong", "moderate"):
        supporting.append(f"5th lord speculation strength is {spec_strength}")
    else:
        limiting.append("5th lord is weak for speculative moves")
    if isinstance(jup_house, int) and jup_house in (2, 5, 9, 11):
        supporting.append(f"Jupiter transit from Moon is supportive ({jup_house}th)")
    elif isinstance(jup_house, int) and jup_house in (6, 8, 12):
        limiting.append(f"Jupiter transit from Moon is cautionary ({jup_house}th)")
    if isinstance(muhurtha_score, (int, float)) and muhurtha_score > 0:
        supporting.append("Muhurtha score is available")
    return _attach_confidence(payload, supporting, limiting, base=48, result=result)


# ===================================================================
# 4. HEALTH ALERTS
# ===================================================================

_HEALTH_PLANET = {
    "Su": ["Heart", "Eyes", "Bones", "Vitality", "Head"],
    "Mo": ["Mind", "Stomach", "Blood", "Lungs", "Sleep"],
    "Ma": ["Blood Pressure", "Muscles", "Surgery", "Accidents", "Inflammation"],
    "Me": ["Nerves", "Skin", "Speech", "Respiratory", "Digestive"],
    "Ju": ["Liver", "Fat/Obesity", "Diabetes", "Ears", "Thighs"],
    "Ve": ["Kidneys", "Reproductive", "Throat", "Hormones", "Diabetes"],
    "Sa": ["Joints", "Teeth", "Chronic Illness", "Depression", "Bones"],
    "Ra": ["Allergies", "Poisoning", "Mysterious Illness", "Phobias", "Infections"],
    "Ke": ["Nerve Disorders", "Spiritual Crisis", "Fever", "Wounds", "Skin"],
}


def get_health_decision(result):
    """Identify health vulnerabilities and risky periods."""
    lagna = result.get("lagna_sign", "Aries")
    planets = result.get("planets", {})
    houses = result.get("houses", {})

    lord6 = _lord_of(6, lagna)
    lord8 = _lord_of(8, lagna)
    lord1 = _lord_of(1, lagna)

    planets_in_6 = houses.get(6, [])
    planets_in_8 = houses.get(8, [])

    vulnerabilities = []
    for p_code, p_data in planets.items():
        if p_code in ("Ra", "Ke"):
            continue
        if p_data.get("dignity") in ("Debilitated", "Enemy") or p_data.get("combust"):
            bp = _HEALTH_PLANET.get(p_code, [])
            full = short_to_full.get(p_code, p_code)
            reasons = []
            if p_data.get("dignity") == "Debilitated":
                reasons.append("debilitated")
            elif p_data.get("dignity") == "Enemy":
                reasons.append("in enemy sign")
            if p_data.get("combust"):
                reasons.append("combust")
            vulnerabilities.append({
                "planet": full,
                "reason": ", ".join(reasons),
                "body_parts": bp,
            })

    health_areas_6 = []
    for p in planets_in_6:
        health_areas_6.extend(_HEALTH_PLANET.get(p, []))
    health_areas_8 = []
    for p in planets_in_8:
        health_areas_8.extend(_HEALTH_PLANET.get(p, []))

    dasha = _current_dasha_info(result)
    md = dasha["mahadasha"]
    risky_lords = {short_to_full.get(lord6, lord6), short_to_full.get(lord8, lord8)}
    risky_dasha = md in risky_lords

    sade_sati = result.get("sade_sati", {})
    sade_sati_active = False
    if isinstance(sade_sati, dict):
        sade_sati_active = sade_sati.get("active", False) or sade_sati.get("running", False)
    elif isinstance(sade_sati, str):
        sade_sati_active = "active" in sade_sati.lower()

    vitality = _planet_strength_label(lord1, planets)

    # Build advice
    parts = []
    if vitality == "strong":
        parts.append("Lagna lord is strong -- good constitution and recovery ability.")
    elif vitality == "weak":
        parts.append("Lagna lord is weak -- take extra care of health, maintain routine checkups.")
    else:
        parts.append("Moderate vitality -- maintain a balanced lifestyle for best health.")
    if vulnerabilities:
        areas = []
        for v in vulnerabilities[:3]:
            areas.extend(v["body_parts"][:2])
        parts.append(f"Pay attention to: {', '.join(set(areas))}.")
    if risky_dasha:
        parts.append("Current dasha activates disease houses -- prioritize health.")
    if sade_sati_active:
        parts.append("Sade Sati period -- mental and physical stress likely; practice meditation.")

    payload = {
        "lagna_lord": short_to_full.get(lord1, lord1),
        "lagna_lord_strength": vitality,
        "sixth_lord": short_to_full.get(lord6, lord6),
        "eighth_lord": short_to_full.get(lord8, lord8),
        "planets_in_6th": [short_to_full.get(p, p) for p in planets_in_6],
        "planets_in_8th": [short_to_full.get(p, p) for p in planets_in_8],
        "health_risk_areas_6th": list(set(health_areas_6)),
        "health_risk_areas_8th": list(set(health_areas_8)),
        "vulnerable_planets": vulnerabilities,
        "current_dasha": dasha,
        "risky_health_period": risky_dasha,
        "sade_sati_active": sade_sati_active,
        "overall_vitality": vitality,
        "advice": " ".join(parts),
    }
    supporting = []
    limiting = []
    if vitality in ("strong", "moderate"):
        supporting.append(f"Lagna lord vitality is {vitality}")
    else:
        limiting.append("Lagna lord is weak")
    if not vulnerabilities:
        supporting.append("No major debilitated or combust health triggers were found")
    else:
        limiting.append(f"Health vulnerabilities detected ({len(vulnerabilities)})")
    if not risky_dasha:
        supporting.append("Current dasha is not focused on disease houses")
    else:
        limiting.append("Current dasha activates disease houses")
    if sade_sati_active:
        limiting.append("Sade Sati can amplify stress load")
    return _attach_confidence(payload, supporting, limiting, base=50, result=result)


# ===================================================================
# 5. TRAVEL / RELOCATION
# ===================================================================

_SIGN_DIRECTION = {
    "Aries": "East", "Taurus": "South", "Gemini": "West",
    "Cancer": "North", "Leo": "East", "Virgo": "South",
    "Libra": "West", "Scorpio": "North", "Sagittarius": "East",
    "Capricorn": "South", "Aquarius": "West", "Pisces": "North",
}


def get_travel_decision(result):
    """Analyse chart for travel and relocation guidance."""
    lagna = result.get("lagna_sign", "Aries")
    planets = result.get("planets", {})
    houses = result.get("houses", {})

    lord4 = _lord_of(4, lagna)
    lord9 = _lord_of(9, lagna)
    lord12 = _lord_of(12, lagna)
    lord3 = _lord_of(3, lagna)

    planets_in_4 = houses.get(4, [])
    planets_in_9 = houses.get(9, [])
    planets_in_12 = houses.get(12, [])

    foreign_indicators = 0
    rahu_house = _house_of_planet("Ra", houses)
    if rahu_house in (1, 4, 7, 9, 12):
        foreign_indicators += 1
    if "Ra" in planets_in_4 or "Ra" in planets_in_9 or "Ra" in planets_in_12:
        foreign_indicators += 1
    lord4_house = _house_of_planet(lord4, houses)
    if lord4_house in (6, 8, 12):
        foreign_indicators += 1
    lord12_sign = planets.get(lord12, {}).get("sign", "")
    if lord12_sign and lord12 not in ("Ra", "Ke"):
        lord12_dig = get_dignity(lord12, lord12_sign)
        if lord12_dig in ("Exalt", "Own"):
            foreign_indicators += 1

    ninth_sign = zodiac_signs[(zodiac_signs.index(lagna) + 8) % 12]
    best_direction = _SIGN_DIRECTION.get(ninth_sign, "East")
    fourth_sign = zodiac_signs[(zodiac_signs.index(lagna) + 3) % 12]
    home_direction = _SIGN_DIRECTION.get(fourth_sign, "North")

    dasha = _current_dasha_info(result)
    md = dasha["mahadasha"]
    travel_lords_full = {
        short_to_full.get(lord3, lord3),
        short_to_full.get(lord9, lord9),
        short_to_full.get(lord12, lord12),
        "Rahu", "Moon",
    }
    good_for_travel = md in travel_lords_full

    if foreign_indicators >= 3:
        foreign_likelihood = "High"
    elif foreign_indicators >= 2:
        foreign_likelihood = "Moderate"
    elif foreign_indicators >= 1:
        foreign_likelihood = "Low"
    else:
        foreign_likelihood = "Very Low"

    # Build advice
    parts = []
    if foreign_likelihood in ("High", "Moderate"):
        parts.append(f"Foreign settlement potential is {foreign_likelihood.lower()} -- opportunities abroad are indicated.")
    else:
        parts.append("Chart indicates stronger ties to homeland -- foreign stays may be short-term.")
    parts.append(f"Best direction for travel/relocation: {best_direction}.")
    if rahu_house in (9, 12):
        parts.append("Rahu's placement strongly supports foreign connections.")
    elif rahu_house == 4:
        parts.append("Rahu in 4th may create restlessness at home -- frequent moves likely.")
    if good_for_travel:
        parts.append("Current dasha supports travel and relocation -- good time to plan moves.")
    else:
        parts.append("Current dasha is not travel-focused -- prefer stability for now.")

    payload = {
        "fourth_lord_home": short_to_full.get(lord4, lord4),
        "ninth_lord_travel": short_to_full.get(lord9, lord9),
        "twelfth_lord_foreign": short_to_full.get(lord12, lord12),
        "third_lord_short_travel": short_to_full.get(lord3, lord3),
        "planets_in_4th": [short_to_full.get(p, p) for p in planets_in_4],
        "planets_in_9th": [short_to_full.get(p, p) for p in planets_in_9],
        "planets_in_12th": [short_to_full.get(p, p) for p in planets_in_12],
        "rahu_house": rahu_house,
        "best_travel_direction": best_direction,
        "home_direction": home_direction,
        "foreign_settlement_likelihood": foreign_likelihood,
        "foreign_indicators_score": foreign_indicators,
        "current_dasha": dasha,
        "good_period_for_travel": good_for_travel,
        "advice": " ".join(parts),
    }
    supporting = []
    limiting = []
    if foreign_indicators > 0:
        supporting.append(f"Foreign-travel indicators present ({foreign_indicators})")
    else:
        limiting.append("Foreign-travel indicators are minimal")
    if rahu_house in (4, 9, 12):
        supporting.append(f"Rahu supports relocation themes from the {rahu_house}th house")
    if good_for_travel:
        supporting.append("Current dasha supports travel and relocation")
    else:
        limiting.append("Current dasha is not travel-focused")
    if planets_in_12:
        supporting.append("12th-house placements reinforce foreign links")
    return _attach_confidence(payload, supporting, limiting, base=46, result=result)


# ===================================================================
# 6. DAILY / WEEKLY GUIDANCE
# ===================================================================

def get_daily_guidance(result):
    """Generate daily/weekly guidance from current transits, dasha, panchanga."""
    transits = result.get("transits", {})
    panchanga = result.get("current_panchanga") or result.get("panchanga", {})
    pakshi = result.get("pancha_pakshi", {})
    muhurtha = result.get("current_muhurtha") or result.get("muhurtha", {})
    dasha = _current_dasha_info(result)

    transit_effects = {}
    for planet, data in transits.items():
        if isinstance(data, dict):
            house = data.get("house_from_moon", "")
            effect = data.get("effect", "")
            transit_effects[planet] = {"house_from_moon": house, "effect": effect}

    favorable = []
    challenging = []
    for planet, data in transit_effects.items():
        h = data.get("house_from_moon", 0)
        if isinstance(h, int):
            if h in (1, 2, 5, 9, 11):
                favorable.append(f"{planet} in {_ordinal(h)}: {data.get('effect', '')}")
            elif h in (6, 8, 12):
                challenging.append(f"{planet} in {_ordinal(h)}: {data.get('effect', '')}")

    panchanga_info = {}
    if isinstance(panchanga, dict):
        panchanga_info = {
            "tithi": panchanga.get("tithi_name", panchanga.get("tithi", "")),
            "vara": panchanga.get("vara_name", panchanga.get("vara", "")),
            "yoga": panchanga.get("yoga_name", panchanga.get("yoga", "")),
            "karana": panchanga.get("karana_name", panchanga.get("karana", "")),
            "nakshatra": panchanga.get("nakshatra", ""),
        }

    pakshi_info = {}
    if isinstance(pakshi, dict):
        pakshi_info = {
            "bird": pakshi.get("birth_bird", pakshi.get("bird", "")),
            "current_activity": pakshi.get("current_activity", ""),
            "ruling_bird": pakshi.get("ruling_bird_now", pakshi.get("ruling_bird", "")),
        }

    muhurtha_score = 0
    muhurtha_grade = ""
    if isinstance(muhurtha, dict):
        muhurtha_score = muhurtha.get("total_score", 0)
        muhurtha_grade = muhurtha.get("grade", "")

    score = 50
    score += len(favorable) * 5
    score -= len(challenging) * 5
    if muhurtha_score:
        score = int((score + muhurtha_score) / 2)
    score = max(0, min(100, score))

    if score >= 75:
        day_rating = "Excellent"
    elif score >= 60:
        day_rating = "Good"
    elif score >= 40:
        day_rating = "Average"
    elif score >= 25:
        day_rating = "Challenging"
    else:
        day_rating = "Difficult"

    tips = []
    if favorable:
        tips.append("Leverage positive transits for important decisions and meetings.")
    if challenging:
        tips.append("Be cautious in areas affected by challenging transits -- avoid confrontation.")
    md = dasha["mahadasha"]
    md_short = next((k for k, v in short_to_full.items() if v == md), md)
    if md_short in ("Ju", "Ve"):
        tips.append("Benefic dasha lord supports social activities and creative work.")
    elif md_short in ("Sa", "Ra"):
        tips.append("Current dasha requires discipline and patience -- focus on long-term goals.")
    elif md_short == "Su":
        tips.append("Sun dasha -- good for leadership initiatives and dealing with authorities.")
    if not tips:
        tips.append("Follow your regular routine and remain mindful of opportunities.")

    payload = {
        "day_rating": day_rating,
        "day_score": score,
        "current_dasha": dasha,
        "transit_effects": transit_effects,
        "favorable_transits": favorable[:5],
        "challenging_transits": challenging[:5],
        "panchanga": panchanga_info,
        "pancha_pakshi": pakshi_info,
        "muhurtha_score": muhurtha_score,
        "muhurtha_grade": muhurtha_grade,
        "daily_tips": tips,
    }
    supporting = []
    limiting = []
    if favorable:
        supporting.append(f"Supportive transits detected ({len(favorable)})")
    if challenging:
        limiting.append(f"Challenging transits detected ({len(challenging)})")
    if panchanga_info:
        supporting.append("Panchanga data is available")
    if pakshi_info:
        supporting.append("Pancha Pakshi data is available")
    if muhurtha_score:
        supporting.append(f"Muhurtha score available ({muhurtha_score})")
    return _attach_confidence(payload, supporting, limiting, base=52, result=result)


# ===================================================================
# 7. COMPATIBILITY DECISIONS
# ===================================================================

def get_compatibility_decision(result1, result2):
    """Compare two charts for relationship compatibility."""
    moon1 = result1.get("moon_sign", "")
    moon2 = result2.get("moon_sign", "")
    nak1 = result1.get("moon_nakshatra", "")
    nak2 = result2.get("moon_nakshatra", "")
    lagna1 = result1.get("lagna_sign", "Aries")
    lagna2 = result2.get("lagna_sign", "Aries")
    planets1 = result1.get("planets", {})
    planets2 = result2.get("planets", {})

    lagna_idx1 = zodiac_signs.index(lagna1) if lagna1 in zodiac_signs else 0
    lagna_idx2 = zodiac_signs.index(lagna2) if lagna2 in zodiac_signs else 0
    lagna_diff = abs(lagna_idx1 - lagna_idx2) % 12
    lagna_diff = min(lagna_diff, 12 - lagna_diff)
    lagna_compatible = lagna_diff in (0, 4, 5, 6, 8)

    ve1_sign = planets1.get("Ve", {}).get("sign", "")
    ve2_sign = planets2.get("Ve", {}).get("sign", "")
    ve1_elem = _sign_element(ve1_sign) if ve1_sign else ""
    ve2_elem = _sign_element(ve2_sign) if ve2_sign else ""
    venus_harmony = ve1_elem == ve2_elem and ve1_elem != ""

    def has_mangal_dosha(res):
        for p in res.get("problems", []):
            name = p.get("name", "") if isinstance(p, dict) else str(p)
            if "mangal" in name.lower() or "manglik" in name.lower():
                return True
        return False

    mangal1 = has_mangal_dosha(result1)
    mangal2 = has_mangal_dosha(result2)
    mangal_match = mangal1 == mangal2

    lord7_1 = _lord_of(7, lagna1)
    lord7_2 = _lord_of(7, lagna2)

    score = 50
    if lagna_compatible:
        score += 10
    if venus_harmony:
        score += 10
    if mangal_match:
        score += 15
    else:
        score -= 15
    if moon1 and moon2 and moon1 == moon2:
        score += 5

    if score >= 75:
        verdict = "Excellent compatibility"
    elif score >= 60:
        verdict = "Good compatibility"
    elif score >= 45:
        verdict = "Average compatibility -- some adjustments needed"
    else:
        verdict = "Challenging compatibility -- consult an astrologer"

    # Build advice
    parts = []
    if lagna_compatible:
        parts.append("Ascendant signs are harmonious -- good foundation for understanding.")
    else:
        parts.append("Ascendant signs create friction -- conscious effort needed for harmony.")
    if venus_harmony:
        parts.append("Venus placements share the same element -- romantic compatibility is natural.")
    else:
        parts.append("Venus placements differ in element -- different love languages; communicate openly.")
    if mangal_match:
        parts.append("Mangal Dosha status is matched -- no extra remedial needed.")
    else:
        parts.append("Mangal Dosha mismatch detected -- perform recommended remedies before marriage.")

    payload = {
        "person1": {
            "lagna": lagna1,
            "moon_sign": moon1,
            "moon_nakshatra": nak1,
            "venus_sign": ve1_sign,
            "mangal_dosha": mangal1,
        },
        "person2": {
            "lagna": lagna2,
            "moon_sign": moon2,
            "moon_nakshatra": nak2,
            "venus_sign": ve2_sign,
            "mangal_dosha": mangal2,
        },
        "lagna_compatible": lagna_compatible,
        "venus_element_harmony": venus_harmony,
        "mangal_dosha_matched": mangal_match,
        "seventh_lord_1": short_to_full.get(lord7_1, lord7_1),
        "seventh_lord_2": short_to_full.get(lord7_2, lord7_2),
        "compatibility_score": min(100, max(0, score)),
        "verdict": verdict,
        "advice": " ".join(parts),
    }
    supporting = []
    limiting = []
    if moon1 and moon2:
        supporting.append("Both Moon signs are available")
    else:
        limiting.append("Moon-sign comparison is incomplete")
    if nak1 and nak2:
        supporting.append("Both nakshatras are available")
    if ve1_sign and ve2_sign:
        supporting.append("Both Venus placements are available")
    else:
        limiting.append("Venus comparison is incomplete")
    if mangal_match:
        supporting.append("Mangal Dosha status is matched")
    else:
        limiting.append("Mangal Dosha mismatch is present")
    if lagna_compatible:
        supporting.append("Ascendant compatibility is supportive")
    return _attach_confidence(payload, supporting, limiting, base=50, result=result1)


# ===================================================================
# 8. EDUCATION DECISIONS
# ===================================================================

_EDUCATION_PLANET = {
    "Su": ["Political Science", "Medicine", "Public Administration"],
    "Mo": ["Psychology", "Nursing", "Hospitality Management", "Home Science"],
    "Ma": ["Engineering", "Military Science", "Sports Science", "Surgery"],
    "Me": ["Computer Science", "Mathematics", "Commerce", "Journalism", "Linguistics"],
    "Ju": ["Law", "Philosophy", "Theology", "Management", "Banking & Finance"],
    "Ve": ["Fine Arts", "Music", "Film Studies", "Fashion Design", "Architecture"],
    "Sa": ["Agriculture", "Geology", "Archaeology", "Labor Studies", "Civil Engineering"],
    "Ra": ["Foreign Languages", "Aeronautical Engineering", "Biotechnology", "AI/ML"],
    "Ke": ["Metaphysics", "Ayurveda", "Computer Science (Research)", "Quantum Physics"],
}

_SIGN_EDUCATION = {
    "Aries": ["Leadership courses", "Sports", "Military training"],
    "Taurus": ["Commerce", "Agriculture", "Fine Arts"],
    "Gemini": ["Communication", "IT", "Teaching", "Journalism"],
    "Cancer": ["Psychology", "Nursing", "History"],
    "Leo": ["Performing Arts", "Political Science", "Management"],
    "Virgo": ["Medicine", "Data Science", "Accounting"],
    "Libra": ["Law", "Design", "Diplomacy"],
    "Scorpio": ["Research", "Forensics", "Surgery", "Occult Science"],
    "Sagittarius": ["Philosophy", "Law", "International Studies"],
    "Capricorn": ["Engineering", "MBA", "Public Administration"],
    "Aquarius": ["Technology", "Social Sciences", "Astronomy"],
    "Pisces": ["Music", "Marine Science", "Spirituality", "Film"],
}


def get_education_decision(result):
    """Analyse chart for best educational fields and timing."""
    lagna = result.get("lagna_sign", "Aries")
    planets = result.get("planets", {})
    houses = result.get("houses", {})
    d24 = result.get("d24", {})

    lord4 = _lord_of(4, lagna)
    lord5 = _lord_of(5, lagna)
    lord9 = _lord_of(9, lagna)

    planets_in_4 = houses.get(4, [])
    planets_in_5 = houses.get(5, [])

    mercury_strength = _planet_strength_label("Me", planets)
    jupiter_strength = _planet_strength_label("Ju", planets)

    fields = []
    fields += _EDUCATION_PLANET.get(lord4, [])
    fields += _EDUCATION_PLANET.get(lord5, [])
    fourth_sign = zodiac_signs[(zodiac_signs.index(lagna) + 3) % 12]
    fifth_sign = zodiac_signs[(zodiac_signs.index(lagna) + 4) % 12]
    fields += _SIGN_EDUCATION.get(fourth_sign, [])
    fields += _SIGN_EDUCATION.get(fifth_sign, [])
    for p in planets_in_4 + planets_in_5:
        fields += _EDUCATION_PLANET.get(p, [])

    d24_insights = []
    if d24:
        me_d24 = d24.get("Me", {}).get("sign", "")
        if me_d24:
            d24_insights.append(f"Mercury in {me_d24} in D24 -- intellectual focus area")
            fields += _SIGN_EDUCATION.get(me_d24, [])
        ju_d24 = d24.get("Ju", {}).get("sign", "")
        if ju_d24:
            d24_insights.append(f"Jupiter in {ju_d24} in D24 -- wisdom and teaching")

    seen = set()
    ranked = []
    for f in fields:
        if f not in seen:
            seen.add(f)
            ranked.append(f)

    dasha = _current_dasha_info(result)
    md = dasha["mahadasha"]
    edu_lords_full = {
        short_to_full.get(lord4, lord4),
        short_to_full.get(lord5, lord5),
        "Mercury", "Jupiter",
    }
    good_for_education = md in edu_lords_full

    ability_score = 50
    if mercury_strength == "strong":
        ability_score += 15
    elif mercury_strength == "weak":
        ability_score -= 10
    if jupiter_strength == "strong":
        ability_score += 15
    elif jupiter_strength == "weak":
        ability_score -= 10
    if planets_in_5:
        for p in planets_in_5:
            if p in ("Me", "Ju", "Ve"):
                ability_score += 10
            elif p in ("Sa", "Ra"):
                ability_score -= 5
    ability_score = max(0, min(100, ability_score))

    # Build advice
    parts = []
    if ability_score >= 75:
        parts.append("Strong academic indicators -- higher education and research are well supported.")
    elif ability_score >= 50:
        parts.append("Moderate academic ability -- focused effort will yield good results.")
    else:
        parts.append("Academic challenges indicated -- practical/vocational education may suit better.")
    if mercury_strength == "strong":
        parts.append("Strong Mercury favors analytical, communication, and technical fields.")
    if jupiter_strength == "strong":
        parts.append("Strong Jupiter supports law, philosophy, management, and teaching.")
    if good_for_education:
        parts.append("Current dasha supports learning -- enrol in courses or pursue certifications.")
    else:
        parts.append("Current dasha is not education-focused -- apply existing knowledge.")

    payload = {
        "fourth_house_sign": fourth_sign,
        "fifth_house_sign": fifth_sign,
        "fourth_lord": short_to_full.get(lord4, lord4),
        "fifth_lord": short_to_full.get(lord5, lord5),
        "ninth_lord_higher_edu": short_to_full.get(lord9, lord9),
        "planets_in_4th": [short_to_full.get(p, p) for p in planets_in_4],
        "planets_in_5th": [short_to_full.get(p, p) for p in planets_in_5],
        "mercury_strength": mercury_strength,
        "jupiter_strength": jupiter_strength,
        "recommended_fields": ranked[:12],
        "d24_insights": d24_insights,
        "current_dasha": dasha,
        "good_period_for_education": good_for_education,
        "academic_ability_score": ability_score,
        "advice": " ".join(parts),
    }
    supporting = []
    limiting = []
    if mercury_strength in ("strong", "moderate"):
        supporting.append(f"Mercury strength is {mercury_strength}")
    else:
        limiting.append("Mercury is weak")
    if jupiter_strength in ("strong", "moderate"):
        supporting.append(f"Jupiter strength is {jupiter_strength}")
    else:
        limiting.append("Jupiter is weak")
    if d24_insights:
        supporting.append("D24 provides educational confirmation")
    else:
        limiting.append("D24 educational confirmation is limited")
    if good_for_education:
        supporting.append("Current dasha supports study and certifications")
    if ranked:
        supporting.append("Multiple education fields are supported")
    return _attach_confidence(payload, supporting, limiting, base=50, result=result)


# ===================================================================
# 9. ADVANCED LIFE ANALYSIS
# ===================================================================

def get_life_analysis(result):
    """Return a unified life-domain synthesis from chart data."""
    from .life_analysis import build_life_analysis

    decision_bundle = {
        "career": get_career_decision(result),
        "marriage": get_marriage_decision(result),
        "business": get_business_decision(result),
        "health": get_health_decision(result),
        "travel": get_travel_decision(result),
        "education": get_education_decision(result),
    }
    analysis = build_life_analysis(result, decision_bundle)
    supporting = []
    limiting = []
    domains = analysis.get("life_domains", {})
    if domains:
        supporting.append(f"Life-domain synthesis covers {len(domains)} domains")
    else:
        limiting.append("Life-domain synthesis is incomplete")
    if analysis.get("timing_overview"):
        supporting.append("Timing overview is available")
    else:
        limiting.append("Timing overview is limited")
    longevity = analysis.get("longevity_profile", {})
    if longevity.get("protective_factors"):
        supporting.append("Protective longevity factors were identified")
    if longevity.get("risk_factors"):
        supporting.append("Risk concentration factors were identified")
    return _attach_confidence(analysis, supporting, limiting, base=55, result=result)


# ===================================================================
# Master functions
# ===================================================================

def get_all_decisions(result):
    """Return all single-chart decision categories including life analysis."""
    decisions = {
        "career": get_career_decision(result),
        "marriage": get_marriage_decision(result),
        "business": get_business_decision(result),
        "health": get_health_decision(result),
        "travel": get_travel_decision(result),
        "daily_guidance": get_daily_guidance(result),
        "education": get_education_decision(result),
        "life_analysis": get_life_analysis(result),
    }
    confidence_scores = {
        key: value.get("confidence_score")
        for key, value in decisions.items()
        if isinstance(value, dict) and isinstance(value.get("confidence_score"), (int, float))
    }
    if confidence_scores:
        average_score = int(round(sum(confidence_scores.values()) / len(confidence_scores)))
        decisions["confidence_summary"] = {
            "average_score": average_score,
            "label": _confidence_label(average_score),
            "categories": confidence_scores,
        }
    return decisions


def get_all_decisions_with_compatibility(result1, result2):
    """Return all categories including compatibility (needs two charts)."""
    decisions = get_all_decisions(result1)
    decisions["compatibility"] = get_compatibility_decision(result1, result2)
    confidence_scores = {
        key: value.get("confidence_score")
        for key, value in decisions.items()
        if isinstance(value, dict) and isinstance(value.get("confidence_score"), (int, float))
    }
    if confidence_scores:
        average_score = int(round(sum(confidence_scores.values()) / len(confidence_scores)))
        decisions["confidence_summary"] = {
            "average_score": average_score,
            "label": _confidence_label(average_score),
            "categories": confidence_scores,
        }
    return decisions
