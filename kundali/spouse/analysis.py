import re
from datetime import datetime
import pytz

from ..constants import (
    ZODIAC_SIGNS,
    SIGN_LORDS,
    SHORT_TO_FULL,
    PLANET_SPOUSE_TRAITS,
    SIGN_APPEARANCE,
    MEETING_CIRCUMSTANCES,
    PROFESSION_BY_HOUSE,
)
from ..utils import (
    get_dignity,
    get_navamsa_sign,
    has_aspect,
    datetime_to_jd,
)
from ..nakshatra import (
    get_nakshatra_lord,
    get_nakshatra_deity,
    get_nakshatra_meaning,
    get_tara_relation,
    get_tara_description,
    NAKSHATRAS,
)

# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------
def _get_house(chart_data, planet, lagna_idx):
    """Return house number (1-12) where planet is placed in D1."""
    d1 = chart_data["planets"]
    if planet not in d1:
        return 0
    planet_sign = d1[planet]["sign"]
    planet_idx = ZODIAC_SIGNS.index(planet_sign)
    return ((planet_idx - lagna_idx) % 12) + 1


def _get_house_d9(chart_data, planet, d9_lagna_idx):
    """Return house number (1-12) where planet is placed in D9."""
    d9 = chart_data.get("navamsa", {})
    if planet not in d9:
        return 0
    planet_sign = d9[planet]["sign"]
    planet_idx = ZODIAC_SIGNS.index(planet_sign)
    return ((planet_idx - d9_lagna_idx) % 12) + 1


def _find_darakaraka_planet(chart_data):
    """Lowest degree among classical planets (excluding nodes)."""
    d1 = chart_data["planets"]
    min_deg = 30
    dk = "Ve"
    for p, data in d1.items():
        if p in ["Ra", "Ke"]:
            continue
        deg = float(data["deg"]) % 30
        if deg < min_deg:
            min_deg = deg
            dk = p
    return dk


def _calculate_arudha_lagna(chart_data, lagna_idx):
    """Compute Arudha Lagna (AL)."""
    d1 = chart_data["planets"]
    lagna_sign = ZODIAC_SIGNS[lagna_idx]
    lagna_lord = SIGN_LORDS[lagna_sign]
    if lagna_lord not in d1:
        return {"sign": "Unknown", "index": 0}
    lagna_lord_sign = d1[lagna_lord]["sign"]
    lagna_lord_idx = ZODIAC_SIGNS.index(lagna_lord_sign)
    distance = (lagna_lord_idx - lagna_idx) % 12
    al_idx = (lagna_lord_idx + distance) % 12
    # Apavada: if AL falls in Lagna or 7th from Lagna, move to 10th from there
    if al_idx == lagna_idx or al_idx == (lagna_idx + 6) % 12:
        al_idx = (al_idx + 9) % 12
    al_sign = ZODIAC_SIGNS[al_idx]
    return {"sign": al_sign, "index": al_idx}


# ------------------------------------------------------------------------
# Analysis functions
# ------------------------------------------------------------------------
def analyze_7th_house(chart_data, lagna_idx):
    """Return 7th house D1 details."""
    h7_idx = (lagna_idx + 6) % 12
    h7_sign = ZODIAC_SIGNS[h7_idx]
    h7_lord = SIGN_LORDS[h7_sign]

    d1 = chart_data["planets"]
    h7_lord_data = d1.get(h7_lord, {})
    h7_lord_sign = h7_lord_data.get("sign", "")
    h7_lord_dignity = get_dignity(h7_lord, h7_lord_sign)
    h7_lord_house = _get_house(chart_data, h7_lord, lagna_idx)

    func_nature = chart_data.get("functional_nature", {}).get(h7_lord, {})
    func_label = func_nature.get("label", "Unknown")
    integrity = chart_data.get("integrity", {}).get(h7_lord, {})
    integrity_score = integrity.get("score", 50)

    return {
        "d1": {
            "sign": h7_sign,
            "lord": h7_lord,
            "lord_sign": h7_lord_sign,
            "lord_dignity": h7_lord_dignity,
            "lord_house": h7_lord_house,
            "functional_nature": func_label,
            "integrity": integrity_score,
        }
    }


def analyze_darakaraka(chart_data, lagna_idx, d9_lagna_idx, gender):
    """Detailed Darakaraka analysis."""
    dk_planet = _find_darakaraka_planet(chart_data)
    d1 = chart_data["planets"]
    d9 = chart_data.get("navamsa", {})

    dk_sign_d1 = d1[dk_planet]["sign"]
    dk_dignity_d1 = get_dignity(dk_planet, dk_sign_d1)
    min_deg = float(d1[dk_planet]["deg"]) % 30

    dk_sign_d9 = d9.get(dk_planet, {}).get("sign", "")
    dk_dignity_d9 = get_dignity(dk_planet, dk_sign_d9)
    dk_d9_house = _get_house_d9(chart_data, dk_planet, d9_lagna_idx)

    d9_house_meaning = {
        1: "Spouse strongly influences your identity",
        2: "Marriage brings wealth, family values central",
        3: "Communicative spouse, sibling-like bond",
        4: "Domestic harmony, spouse connected to home",
        5: "Creative partnership, children bring joy",
        6: "Service-oriented spouse, health matters",
        7: "Perfect partnership, strong marriage",
        8: "Transformative marriage, deep intimacy",
        9: "Philosophical spouse, dharmic marriage",
        10: "Career-oriented spouse, public recognition",
        11: "Social spouse, gains through marriage",
        12: "Spiritual union, foreign connections",
    }.get(dk_d9_house, "Unique placement")

    integrity = chart_data.get("integrity", {}).get(dk_planet, {})
    func = chart_data.get("functional_nature", {}).get(dk_planet, {})

    return {
        "planet": dk_planet,
        "name": SHORT_TO_FULL[dk_planet],
        "degree": min_deg,
        "sign_d1": dk_sign_d1,
        "dignity_d1": dk_dignity_d1,
        "sign_d9": dk_sign_d9,
        "dignity_d9": dk_dignity_d9,
        "d9_house": dk_d9_house,
        "d9_house_meaning": d9_house_meaning,
        "traits": PLANET_SPOUSE_TRAITS.get(dk_planet, {}),
        "integrity": integrity.get("score", 50),
        "functional": func.get("label", "Unknown"),
    }


def analyze_upapada(chart_data, lagna_idx):
    """Complete Upapada Lagna with BPHS exception rules."""
    h12_idx = (lagna_idx + 11) % 12
    h12_sign = ZODIAC_SIGNS[h12_idx]
    h12_lord = SIGN_LORDS[h12_sign]
    d1 = chart_data["planets"]
    if h12_lord not in d1:
        return {"sign": "", "strong": False, "method": "Data missing"}

    h12_lord_sign = d1[h12_lord]["sign"]
    h12_lord_house = _get_house(chart_data, h12_lord, lagna_idx)
    h12_lord_idx = ZODIAC_SIGNS.index(h12_lord_sign)
    distance = (h12_lord_idx - h12_idx) % 12

    # Standard UL
    ul_idx = (h12_lord_idx + distance) % 12
    method = "Standard (equal distance from 12L)"

    # Apavada rules
    if h12_lord_idx == h12_idx:
        ul_idx = (h12_lord_idx + 9) % 12
        method = "12L in 12H → UL=10th from there"
    elif h12_lord_house == ((h12_idx + 6) % 12) + 1:
        ul_idx = (h12_lord_idx + 9) % 12
        method = "12L in 7th from 12H → UL=10th from there"

    ul_sign = ZODIAC_SIGNS[ul_idx]
    ul_lord = SIGN_LORDS[ul_sign]
    ul_lord_sign = d1.get(ul_lord, {}).get("sign", "")
    ul_dignity = get_dignity(ul_lord, ul_lord_sign)
    strong = ul_dignity in ["Exalted", "Own", "Friendly"]

    # 2nd from UL
    ul_2nd_idx = (ul_idx + 1) % 12
    ul_2nd_sign = ZODIAC_SIGNS[ul_2nd_idx]
    planets_in_2nd = [
        p for p, data in d1.items() if ZODIAC_SIGNS.index(data["sign"]) == ul_2nd_idx
    ]
    has_malefic_2nd = any(p in ["Ma", "Sa", "Ra", "Ke"] for p in planets_in_2nd)
    meaning_2nd = (
        "Challenges in family harmony/finances"
        if has_malefic_2nd
        else "Supportive family, good sustenance"
    )

    # 8th from UL
    ul_8th_idx = (ul_idx + 7) % 12
    ul_8th_sign = ZODIAC_SIGNS[ul_8th_idx]
    planets_in_8th = [
        p for p, data in d1.items() if ZODIAC_SIGNS.index(data["sign"]) == ul_8th_idx
    ]
    has_malefic_8th = any(p in ["Ma", "Sa", "Ra", "Ke"] for p in planets_in_8th)
    meaning_8th = (
        "Transformations/in-law issues"
        if has_malefic_8th
        else "Stable long-term marriage"
    )

    return {
        "sign": ul_sign,
        "lord": ul_lord,
        "dignity": ul_dignity,
        "strong": strong,
        "calculation_method": method,
        "2nd_sign": ul_2nd_sign,
        "2nd_meaning": meaning_2nd,
        "8th_sign": ul_8th_sign,
        "8th_meaning": meaning_8th,
    }


def analyze_functional_venus_jupiter(chart_data, lagna_idx):
    """Functional status of Venus and Jupiter, plus mutual connection."""
    func = chart_data.get("functional_nature", {})
    venus = func.get("Ve", {})
    jupiter = func.get("Ju", {})

    result = {
        "venus": {
            "label": venus.get("label", "Unknown"),
            "score": venus.get("score", 0),
        },
        "jupiter": {
            "label": jupiter.get("label", "Unknown"),
            "score": jupiter.get("score", 0),
        },
    }

    # Venus-Jupiter relationship in D1
    d1 = chart_data["planets"]
    ve_data = d1.get("Ve", {})
    ju_data = d1.get("Ju", {})
    ve_deg = ve_data.get("deg", 0)
    ju_deg = ju_data.get("deg", 0)
    ve_sign = ve_data.get("sign", "")
    ju_sign = ju_data.get("sign", "")
    ve_house = _get_house(chart_data, "Ve", lagna_idx)
    ju_house = _get_house(chart_data, "Ju", lagna_idx)

    vj_relationship = "No direct connection"
    if ve_sign and ju_sign:
        if ve_sign == ju_sign:
            deg_diff = abs(ve_deg - ju_deg)
            if deg_diff < 10:
                vj_relationship = f"Conjunction within {deg_diff:.1f}° – harmonious union, spouse is wise and beautiful"
            else:
                vj_relationship = (
                    f"Same sign but wide orb ({deg_diff:.1f}°) – mild positive"
                )
        elif has_aspect(ve_house, ju_house, "Ve") or has_aspect(
            ju_house, ve_house, "Ju"
        ):
            vj_relationship = "Mutual aspect – harmonious spouse, balanced marriage"

    result["venus_jupiter_relationship"] = vj_relationship
    return result


def analyze_aspects_on_7th(chart_data, lagna_idx):
    """Aspects to 7th house."""
    aspects_data = chart_data.get("aspects", {})
    h7_house_num = ((lagna_idx + 6) % 12) + 1
    h7_aspects = aspects_data.get(h7_house_num, [])

    combined = []
    for asp in h7_aspects:
        parts = asp.split("-")
        planet = parts[0]
        asp_type = parts[1] if len(parts) > 1 else "7th"
        combined.append({"target": "7th house", "planet": planet, "type": asp_type})
    return {"aspects": combined}


def analyze_house_lord_placements(chart_data):
    """Return placements of 2nd, 5th, 7th house lords."""
    return {
        "seventh_house": chart_data.get("house_lords", {}).get(7, {}),
        "second_house": chart_data.get("house_lords", {}).get(2, {}),
        "fifth_house": chart_data.get("house_lords", {}).get(5, {}),
    }


def analyze_marriage_dashas(chart_data, lagna_idx, birth_jd, birth_year):
    """Dasha windows with scores, sandhi detection."""
    periods = chart_data.get("dasha_periods_for_marriage", [])
    if not periods:
        timings = chart_data.get("timings", {}).get("Marriage", [])
        for line in timings:
            m = re.search(r"─\s*(\w+)/(\w+)\s*\((\d{4})-(\d{4})\)", line)
            if m:
                periods.append(
                    {
                        "maha": m.group(1),
                        "antara": m.group(2),
                        "start": int(m.group(3)),
                        "end": int(m.group(4)),
                        "score": 8,
                    }
                )

    # Dasha Sandhi boundaries
    vim = chart_data.get("vimshottari", {})
    mahadashas = vim.get("mahadasas", [])
    md_boundaries = []
    for md in mahadashas:
        md_start = int(birth_year + (md.get("start_jd", birth_jd) - birth_jd) / 365.25)
        md_end = int(birth_year + (md.get("end_jd", birth_jd) - birth_jd) / 365.25)
        md_boundaries.append({"start": md_start, "end": md_end})

    high_score = []
    for p in periods:
        p_score = p.get("score", 0)
        is_sandhi = False
        for boundary in md_boundaries:
            if (
                abs(p["start"] - boundary["start"]) <= 1
                or abs(p["end"] - boundary["end"]) <= 1
                or abs(p["start"] - boundary["end"]) <= 1
            ):
                is_sandhi = True
                break
        if is_sandhi:
            p_score = min(10, p_score + 2)
            p["sandhi"] = True
        else:
            p["sandhi"] = False
        p["score"] = p_score
        if p_score >= 8:
            high_score.append(p)

    from kundali.utils import datetime_to_jd
    import pytz

    current_jd = datetime_to_jd(datetime.now(pytz.utc))
    # Always include all high-score periods as 'upcoming' if their end year is >= current year
    current_year = datetime.now(pytz.utc).year
    upcoming = [p for p in high_score if p.get("end", 0) >= current_year]
    return {
        "high_score_periods": high_score,
        "upcoming": upcoming,
        "count": len(high_score),
        "sandhi_periods": [p for p in high_score if p.get("sandhi", False)],
    }


def analyze_current_transits(chart_data, lagna_idx):
    """Transiting planets in 7th from Moon, and double transit activation."""
    transits = chart_data.get("transits", {})
    h7_house_num = ((lagna_idx + 6) % 12) + 1
    transiting_7th = []
    for planet, data in transits.items():
        if data.get("house_from_moon") == h7_house_num:
            transiting_7th.append(planet)
    return {"transiting_7th": transiting_7th, "gochara": transits}


def check_double_transit(chart_data, lagna_idx):
    """Jupiter and Saturn both aspecting marriage‑related houses."""
    transits = chart_data.get("transits", {})
    if not transits.get("Ju") or not transits.get("Sa"):
        return {"active": False, "reason": "Missing transit data"}

    ju_sign = transits["Ju"]["sign"]
    sa_sign = transits["Sa"]["sign"]
    ju_house = ((ZODIAC_SIGNS.index(ju_sign) - lagna_idx) % 12) + 1
    sa_house = ((ZODIAC_SIGNS.index(sa_sign) - lagna_idx) % 12) + 1

    h7_num = 7
    h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(lagna_idx + 6) % 12]]
    h7_lord_house = _get_house(chart_data, h7_lord, lagna_idx)
    ul = analyze_upapada(chart_data, lagna_idx)
    ul_sign_idx = ZODIAC_SIGNS.index(ul["sign"]) if ul["sign"] else -1
    ul_house = ((ul_sign_idx - lagna_idx) % 12) + 1 if ul_sign_idx >= 0 else 0

    targets = [h7_num, h7_lord_house]
    if ul_house > 0:
        targets.append(ul_house)

    jup_activates = any(has_aspect(ju_house, target, "Ju") for target in targets)
    sat_activates = any(has_aspect(sa_house, target, "Sa") for target in targets)

    return {
        "active": jup_activates and sat_activates,
        "jupiter_activates": jup_activates,
        "saturn_activates": sat_activates,
        "ju_house": ju_house,
        "sa_house": sa_house,
        "targets": targets,
    }


def analyze_marriage_yogas(chart_data):
    """Yogas that mention marriage keywords."""
    all_yogas = chart_data.get("yogas", [])
    marriage_keywords = [
        "marriage",
        "spouse",
        "wife",
        "husband",
        "venus",
        "7th",
        "darakaraka",
    ]
    relevant = []
    for yoga in all_yogas:
        if any(k in yoga.lower() for k in marriage_keywords):
            relevant.append({"name": yoga, "strength": 5})
    return relevant


def analyze_neecha_bhanga_effects(chart_data, lagna_idx):
    """Check if 7th lord or Darakaraka or Venus have Neecha Bhanga."""
    nb_planets = chart_data.get("neecha_bhanga_planets", [])
    h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(lagna_idx + 6) % 12]]
    dk = _find_darakaraka_planet(chart_data)

    effects = {}
    if h7_lord in nb_planets:
        effects[
            "seventh_lord"
        ] = "Neecha Bhanga - debilitation cancelled, becomes powerful after maturity"
    if dk in nb_planets:
        effects[
            "darakaraka"
        ] = "Neecha Bhanga - spouse-related planet gains strength over time"
    if "Ve" in nb_planets:
        effects[
            "venus"
        ] = "Neecha Bhanga - Venus strengthens with age, spouse quality improves"
    return effects


def analyze_d9_seventh_house(chart_data, d9_lagna_idx):
    """D9 7th house analysis."""
    d9 = chart_data.get("navamsa", {})
    d9_h7_idx = (d9_lagna_idx + 6) % 12
    d9_h7_sign = ZODIAC_SIGNS[d9_h7_idx]
    d9_h7_lord = SIGN_LORDS[d9_h7_sign]

    d9_h7_lord_sign = d9.get(d9_h7_lord, {}).get("sign", "")
    d9_h7_lord_dignity = (
        get_dignity(d9_h7_lord, d9_h7_lord_sign) if d9_h7_lord_sign else "Unknown"
    )

    planets_in = [
        p for p, data in d9.items() if ZODIAC_SIGNS.index(data["sign"]) == d9_h7_idx
    ]

    func = chart_data.get("functional_nature", {}).get(d9_h7_lord, {})
    func_label = func.get("label", "Unknown")

    interpretation = []
    if d9_h7_lord_dignity == "Exalted":
        interpretation.append("Excellent marriage karma at soul level")
    elif d9_h7_lord_dignity == "Own":
        interpretation.append("Strong marriage foundation")
    elif d9_h7_lord_dignity == "Debilitated":
        interpretation.append("Challenges in marriage at deeper level")
    if planets_in:
        interpretation.append(
            f"Planets in D9 7th: {', '.join([SHORT_TO_FULL[p] for p in planets_in])}"
        )
    if func_label in ["Strong Benefic", "Conditional Benefic"]:
        interpretation.append("D9 7th lord functionally benefic - blessed")

    return {
        "d9_7th_sign": d9_h7_sign,
        "d9_7th_lord": d9_h7_lord,
        "d9_7th_lord_sign": d9_h7_lord_sign,
        "d9_7th_lord_dignity": d9_h7_lord_dignity,
        "planets_in_d9_7th": planets_in,
        "strong": d9_h7_lord_dignity in ["Exalted", "Own"],
        "functional_lord": func_label,
        "interpretation": " | ".join(interpretation)
        if interpretation
        else "Average D9 7th house",
    }


def analyze_d2_financial_integration(chart_data, lagna_idx):
    """D2 Hora analysis for spouse family financial support."""
    d2 = chart_data.get("d2", {})
    if not d2:
        return {"available": False}

    h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(lagna_idx + 6) % 12]]
    h7_lord_d2_data = d2.get(h7_lord, {})
    h7_lord_d2_sign = h7_lord_d2_data.get("sign", "Unknown")
    h7_lord_d2_dignity = get_dignity(h7_lord, h7_lord_d2_sign)

    ul = analyze_upapada(chart_data, lagna_idx)
    ul_sign = ul.get("sign", "")
    ul2_d2_sign = "Unknown"
    financial_strength = "Unknown"
    family_note = "UL unavailable for D2 analysis"
    if ul_sign in ZODIAC_SIGNS:
        ul_idx = ZODIAC_SIGNS.index(ul_sign)
        ul2_idx = (ul_idx + 1) % 12
        ul2_d2_sign = ZODIAC_SIGNS[ul2_idx]
        planets_ul2_d2 = [
            p for p, data in d2.items() if data.get("sign") == ul2_d2_sign
        ]
        malefics = {"Ma", "Sa", "Ra", "Ke"}
        has_malefic_ul2 = any(p in malefics for p in planets_ul2_d2)
        financial_strength = (
            "Weak (malefics in UL-2nd D2)" if has_malefic_ul2 else "Strong"
        )
        family_note = (
            "Spouse family financial support limited; self-earned wealth primary"
            if has_malefic_ul2
            else "Excellent family support post-marriage; joint wealth accumulation"
        )

    return {
        "available": True,
        "h7_lord_d2_sign": h7_lord_d2_sign,
        "h7_lord_d2_dignity": h7_lord_d2_dignity,
        "ul2_d2_sign": ul2_d2_sign,
        "financial_strength": financial_strength,
        "family_note": family_note,
    }


def analyze_d60_karma(chart_data, lagna_idx):
    """D60 Shashtiamsa for deep marriage karma."""
    d60 = chart_data.get("d60", {})
    if not d60:
        return {"available": False}

    h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(lagna_idx + 6) % 12]]
    h7_lord_d60_data = d60.get(h7_lord, {})
    h7_lord_d60_sign = h7_lord_d60_data.get("sign", "Unknown")
    h7_lord_d60_dignity = get_dignity(h7_lord, h7_lord_d60_sign)

    ve_d60_data = d60.get("Ve", {})
    ve_d60_sign = ve_d60_data.get("sign", "Unknown")
    ve_d60_dignity = get_dignity("Ve", ve_d60_sign)

    dk = _find_darakaraka_planet(chart_data)
    dk_d60_data = d60.get(dk, {})
    dk_d60_sign = dk_d60_data.get("sign", "Unknown")

    karma_notes = []
    # Relative dusthana houses 6,8,12 from D60 lagna (proxy since no D60 lagna)
    dk_house_proxy = 6  # simplistic
    if h7_lord_d60_dignity in ["Debilitated", "Enemy"]:
        karma_notes.append("7L weak in D60: Karmic marriage obstacles")
    if ve_d60_dignity in ["Debilitated", "Enemy"]:
        karma_notes.append("Venus afflicted D60: Relationship karma needs work")
    if dk_d60_sign in ["Virgo", "Scorpio", "Pisces"]:  # keep proxy but note
        karma_notes.append("DK in proxy dusthana signs: Soul-level marriage lessons")
    if not karma_notes:
        karma_notes.append("Clean D60 marriage karma - minimal past life baggage")

    severe_karma = len(karma_notes) >= 2
    return {
        "available": True,
        "h7_lord_d60": h7_lord_d60_sign,
        "venus_d60": ve_d60_sign,
        "dk_d60": dk_d60_sign,
        "karma_notes": karma_notes,
        "severe_karma": severe_karma,
        "remedy_note": "D60 remedies advised" if severe_karma else "Karma manageable",
    }


def analyze_navamsa_strength(chart_data):
    """Vargottama planets."""
    d1 = chart_data["planets"]
    d9 = chart_data.get("navamsa", {})
    vargottama = []
    for p in d1:
        if p in d9 and d1[p]["sign"] == d9[p]["sign"]:
            vargottama.append(p)
    return {"vargottama": vargottama, "count": len(vargottama)}


def analyze_venus_mars(chart_data, lagna_idx):
    """Venus-Mars relationship in D1."""
    d1 = chart_data["planets"]
    if "Ve" not in d1 or "Ma" not in d1:
        return {"status": "No connection", "effect": "Neutral passion level"}
    ve_house = _get_house(chart_data, "Ve", lagna_idx)
    ma_house = _get_house(chart_data, "Ma", lagna_idx)
    if ve_house == ma_house:
        return {
            "status": "Conjunction",
            "effect": "Intense passion, strong attraction, high energy in intimacy. Possible conflicts but strong chemistry.",
        }
    if has_aspect(ve_house, ma_house, "Ve") or has_aspect(ma_house, ve_house, "Ma"):
        return {
            "status": "Mutual Aspect",
            "effect": "Mutual attraction with some tension. Balanced passion, manageable conflicts.",
        }
    return {
        "status": "No direct connection",
        "effect": "Standard or mild passion levels.",
    }


def analyze_ashtakavarga(chart_data):
    """Ashtakavarga points for 7th house."""
    ashtak = chart_data.get("ashtakavarga", {})
    h7_points = ashtak.get("interpretation", {}).get(7, {}).get("score")
    if h7_points is None:
        return {"points": "Data not available", "interpretation": "SAV not found"}
    if h7_points >= 28:
        interp = "Excellent - Very strong marriage yoga, smooth path"
        strength = "Very Strong"
    elif h7_points >= 25:
        interp = "Good - Positive support for marriage"
        strength = "Strong"
    elif h7_points >= 22:
        interp = "Average - Normal marriage karma"
        strength = "Average"
    else:
        interp = "Weak - Possible delays, obstacles, or need for remedies"
        strength = "Weak"
    return {"points": h7_points, "strength": strength, "interpretation": interp}


def check_manglik_dosha(chart_data, lagna_idx):
    """Mangal Dosha detection with cancellations."""
    d1 = chart_data["planets"]
    if "Ma" not in d1:
        return {"present": False, "reason": "Mars position unknown"}
    mars_house = _get_house(chart_data, "Ma", lagna_idx)
    mars_sign = d1["Ma"]["sign"]
    mars_dignity = get_dignity("Ma", mars_sign)
    is_manglik = mars_house in [1, 2, 4, 7, 8, 12]
    if not is_manglik:
        return {
            "present": False,
            "mars_house": mars_house,
            "reason": "Mars not in Manglik houses",
        }

    cancellations = []
    if mars_dignity in ["Exalted", "Own"]:
        cancellations.append("Mars in own/exalted sign (strength cancels dosha)")
    ju_house = _get_house(chart_data, "Ju", lagna_idx)
    if has_aspect(ju_house, mars_house, "Ju"):
        cancellations.append("Jupiter aspects Mars (benefic protection)")
    if mars_house == 1 and mars_sign in ["Aries", "Scorpio"]:
        cancellations.append("Mars in 1st in own sign (reduces intensity)")
    if mars_house == 4 and mars_sign == "Capricorn":
        cancellations.append("Mars exalted in 4th (cancellation)")
    if mars_house == 7 and mars_sign in ["Capricorn", "Aries", "Scorpio"]:
        cancellations.append("Mars in 7th in strong position")
    if mars_house == 8 and mars_sign == "Capricorn":
        cancellations.append("Mars exalted in 8th (cancellation)")
    if "Ve" in d1:
        ve_dignity = get_dignity("Ve", d1["Ve"]["sign"])
        if ve_dignity in ["Exalted", "Own"]:
            cancellations.append("Venus very strong (mitigates Mars dosha)")

    severity = "Cancelled" if cancellations else "Present"
    if not cancellations:
        severity = (
            "Mild"
            if mars_house in [2, 12]
            else "Moderate"
            if mars_house in [1, 4]
            else "Strong"
        )

    return {
        "present": True,
        "severity": severity,
        "mars_house": mars_house,
        "mars_sign": mars_sign,
        "mars_dignity": mars_dignity,
        "cancellations": cancellations,
        "recommendation": get_manglik_recommendation(severity, cancellations),
    }


def classify_marriage_type(chart_data, lagna_idx, gender):
    """Love vs arranged vs mixed."""
    d1 = chart_data["planets"]
    love_score = 0
    arranged_score = 0
    indicators = []

    ve_house = _get_house(chart_data, "Ve", lagna_idx)
    mo_house = _get_house(chart_data, "Mo", lagna_idx)
    if ve_house == mo_house:
        love_score += 3
        indicators.append("Venus-Moon conjunction (romantic nature)")

    h5_lord = SIGN_LORDS[ZODIAC_SIGNS[(lagna_idx + 4) % 12]]
    h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(lagna_idx + 6) % 12]]
    if (
        _get_house(chart_data, h5_lord, lagna_idx) == 7
        or _get_house(chart_data, h7_lord, lagna_idx) == 5
    ):
        love_score += 3
        indicators.append("5th-7th house connection (love marriage yoga)")

    planets_in_5 = [p for p in d1 if _get_house(chart_data, p, lagna_idx) == 5]
    planets_in_7 = [p for p in d1 if _get_house(chart_data, p, lagna_idx) == 7]
    if "Ra" in planets_in_5 or "Ra" in planets_in_7 or "Ke" in planets_in_5:
        love_score += 2
        indicators.append("Rahu/Ketu influence (unconventional/love)")

    if ve_house == 5:
        love_score += 2
        indicators.append("Venus in 5th house (romance)")

    if "Ju" in planets_in_7:
        arranged_score += 2
        indicators.append("Jupiter in 7th (traditional/arranged)")

    h7_lord_house = _get_house(chart_data, h7_lord, lagna_idx)
    if h7_lord_house in [2, 4, 10]:
        arranged_score += 2
        indicators.append(f"7th lord in {h7_lord_house}th (family involvement)")

    if ve_house in [2, 4, 10]:
        arranged_score += 1
        indicators.append("Venus in family house (arranged tendency)")

    if "Sa" in planets_in_7:
        arranged_score += 1
        indicators.append("Saturn in 7th (traditional approach)")

    if love_score == 0 and arranged_score == 0:
        category = "Neutral"
        probability = "Cannot determine clearly - could be either"
    elif love_score > arranged_score + 2:
        category = "Love Marriage"
        probability = "High probability of love/self-choice marriage"
    elif arranged_score > love_score + 2:
        category = "Arranged Marriage"
        probability = "High probability of arranged/family-introduced marriage"
    else:
        category = "Mixed/Love-cum-Arranged"
        probability = "Mixed indicators - modern love-cum-arranged very likely"

    return {
        "category": category,
        "probability": probability,
        "love_score": love_score,
        "arranged_score": arranged_score,
        "indicators": indicators,
    }


def predict_appearance(chart_data, lagna_idx, gender):
    """Spouse appearance from 7th house, Darakaraka, D9."""
    h7_idx = (lagna_idx + 6) % 12
    h7_sign = ZODIAC_SIGNS[h7_idx]
    appearance = SIGN_APPEARANCE.get(h7_sign, {}).copy()
    appearance["primary_source"] = f"7th house in {h7_sign}"

    dk_planet = _find_darakaraka_planet(chart_data)
    d1 = chart_data["planets"]
    d9 = chart_data.get("navamsa", {})
    if dk_planet:
        dk_traits = PLANET_SPOUSE_TRAITS.get(dk_planet, {})
        appearance["dk_planet"] = SHORT_TO_FULL[dk_planet]
        appearance["dk_influence"] = dk_traits.get("appearance", "")
        dk_sign = d1[dk_planet]["sign"]
        dk_sign_traits = SIGN_APPEARANCE.get(dk_sign, {})
        appearance["dk_sign_adds"] = dk_sign_traits.get("build", "")
        if dk_planet in d9:
            dk_d9_sign = d9[dk_planet]["sign"]
            d9_traits = SIGN_APPEARANCE.get(dk_d9_sign, {})
            appearance["d9_refinement"] = d9_traits.get("face", "")
    return appearance


def predict_meeting(chart_data, lagna_idx):
    """Meeting circumstances based on 7th lord's house and Rahu."""
    h7_idx = (lagna_idx + 6) % 12
    h7_lord = SIGN_LORDS[ZODIAC_SIGNS[h7_idx]]
    h7_lord_house = _get_house(chart_data, h7_lord, lagna_idx)
    circumstance = MEETING_CIRCUMSTANCES.get(h7_lord_house, "Various circumstances")

    rahu_house = _get_house(chart_data, "Ra", lagna_idx)
    rahu_modifier = ""
    rahu_conditions = {
        7: " (unconventional: online, foreign, sudden)",
        5: " (romance through unconventional networks)",
        3: " (through communication/tech/media)",
        12: " (foreign land/spiritual place)",
        11: " (social networks/large groups)",
        9: " (travel/pilgrimage/long distance)",
    }
    if rahu_house in rahu_conditions:
        rahu_modifier = rahu_conditions[rahu_house]
    elif has_aspect(rahu_house, h7_lord_house, "Ra"):
        rahu_modifier = " (Rahu influences 7L: unexpected circumstances)"

    return {
        "primary": circumstance + rahu_modifier,
        "7th_lord_house": h7_lord_house,
        "rahu_house": rahu_house,
        "rahu_modifier": rahu_modifier.strip(),
    }


def predict_profession(chart_data, lagna_idx):
    """Spouse profession from Darakaraka and 7th lord's house."""
    dk_planet = _find_darakaraka_planet(chart_data)
    profession = {}
    if dk_planet:
        profession["primary"] = PLANET_SPOUSE_TRAITS.get(dk_planet, {}).get(
            "profession", ""
        )
    h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(lagna_idx + 6) % 12]]
    h7_lord_house = _get_house(chart_data, h7_lord, lagna_idx)
    profession["secondary"] = PROFESSION_BY_HOUSE.get(h7_lord_house, "")
    return profession


def consolidate_profile(chart_data, lagna_idx, gender):
    """Basic profile summary."""
    h7 = analyze_7th_house(chart_data, lagna_idx)
    karaka = analyze_functional_venus_jupiter(chart_data, lagna_idx)
    dk = analyze_darakaraka(
        chart_data, lagna_idx, 0, gender
    )  # d9_lagna_idx placeholder; will be overridden later
    return {
        "7th_house_sign": h7["d1"]["sign"],
        "7th_lord": h7["d1"]["lord"],
        "darakaraka": dk["name"],
        "venus_functional": karaka["venus"]["label"],
        "jupiter_functional": karaka["jupiter"]["label"],
    }


def consolidate_personality(chart_data, lagna_idx):
    """Personality traits from 7th house and Darakaraka."""
    h7 = analyze_7th_house(chart_data, lagna_idx)
    dk = analyze_darakaraka(
        chart_data, lagna_idx, 0, "Male"
    )  # gender not needed for traits
    h7_sign = h7["d1"]["sign"]
    h7_traits = SIGN_APPEARANCE.get(h7_sign, {}).get("personality", "")
    dk_traits = dk["traits"].get("personality", "")
    return {"7th_house_influence": h7_traits, "darakaraka_influence": dk_traits}


def calculate_confidence(factors):
    """Confidence string based on number of confirming factors."""
    count = len(factors)
    if count >= 10:
        return "Very High (10+ confirming factors)"
    elif count >= 7:
        return "High (7-9 confirming factors)"
    elif count >= 5:
        return "Moderate-High (5-6 confirming factors)"
    elif count >= 3:
        return "Moderate (3-4 confirming factors)"
    else:
        return "Low (<3 confirming factors)"


def analyze_atmakaraka_for_spouse(chart_data):
    """Atmakaraka analysis for spouse."""
    jaimini = chart_data.get("jaimini", {})
    atmakaraka = jaimini.get("atmakaraka")
    if not atmakaraka:
        return {"error": "Atmakaraka not available"}
    d9 = chart_data.get("navamsa", {})
    ak_full = SHORT_TO_FULL.get(atmakaraka, atmakaraka)

    ak_d9_sign = (
        d9.get(atmakaraka, {}).get("sign", "Unknown") if atmakaraka in d9 else "Unknown"
    )
    ak_d9_dignity = (
        get_dignity(atmakaraka, ak_d9_sign) if ak_d9_sign != "Unknown" else ""
    )

    d9_lagna_idx = chart_data.get("d9_lagna_idx", 0)
    d9_7th_house_idx = (d9_lagna_idx + 6) % 12
    d9_7th_sign = ZODIAC_SIGNS[d9_7th_house_idx]
    ak_in_7th_d9 = ak_d9_sign == d9_7th_sign

    interpretation = []
    if ak_in_7th_d9:
        interpretation.append(
            f"Your Atmakaraka {ak_full} is in the 7th house of D9 – your spouse is deeply connected to your soul"
            "s purpose. Marriage is karmic and transformative."
        )
    else:
        interpretation.append(
            f"Your Atmakaraka {ak_full} resides in {ak_d9_sign} in D9. Your spouse will help you grow in areas ruled by this sign."
        )
    if ak_d9_dignity in ("Exalt", "Own"):
        interpretation.append(
            f"Atmakaraka is {ak_d9_dignity} in D9 – your soul"
            "s strength is well‑supported; marriage will be a source of spiritual growth."
        )
    elif ak_d9_dignity == "Debilitated":
        interpretation.append(
            f"Atmakaraka is debilitated in D9 – you may need to work through karmic challenges in marriage, but overcoming them brings great wisdom."
        )

    return {
        "atmakaraka": atmakaraka,
        "atmakaraka_full": ak_full,
        "d9_sign": ak_d9_sign,
        "d9_dignity": ak_d9_dignity,
        "in_7th_d9": ak_in_7th_d9,
        "interpretation": " ".join(interpretation),
    }


def analyze_karakamsa_lagna(chart_data):
    """Karakamsa Lagna analysis."""
    jaimini = chart_data.get("jaimini", {})
    karakamsa_lagna = jaimini.get("karakamsa_lagna")
    if not karakamsa_lagna:
        return {"error": "Karakamsa Lagna not available"}

    kl = karakamsa_lagna
    kl_idx = ZODIAC_SIGNS.index(kl) if kl in ZODIAC_SIGNS else -1
    d9 = chart_data.get("navamsa", {})

    kl_7th_sign = "Unknown"
    if kl_idx != -1:
        kl_7th_idx = (kl_idx + 6) % 12
        kl_7th_sign = ZODIAC_SIGNS[kl_7th_idx]

    planets_in_kl = []
    planets_in_kl_7th = []
    for pl, data in d9.items():
        sign = data.get("sign", "")
        if sign == kl:
            planets_in_kl.append(pl)
        if sign == kl_7th_sign:
            planets_in_kl_7th.append(pl)

    lines = [f"Karakamsa Lagna = {kl} – the sign of your soul" "s ultimate focus."]
    lines.append(
        f"Its 7th house (spouse) in D9 is {kl_7th_sign}. Planets here colour the spouse"
        "s role in your spiritual evolution."
    )
    if planets_in_kl_7th:
        pl_names = [SHORT_TO_FULL.get(p, p) for p in planets_in_kl_7th]
        lines.append(
            f'✨ Planets in Karakamsa 7th: {", ".join(pl_names)} – they strongly influence your marriage at the soul level.'
        )
    if planets_in_kl:
        pl_names = [SHORT_TO_FULL.get(p, p) for p in planets_in_kl]
        lines.append(
            f'Planets conjunct Karakamsa Lagna: {", ".join(pl_names)} – they amplify the soul'
            "s mission and may manifest through the spouse."
        )

    return {
        "karakamsa_lagna": kl,
        "kl_7th_sign": kl_7th_sign,
        "planets_in_kl": planets_in_kl,
        "planets_in_kl_7th": planets_in_kl_7th,
        "interpretation": "\n      ".join(lines),
    }


def analyze_nakshatra_for_spouse(chart_data, lagna_idx):
    """Nakshatra insights for spouse karakas."""
    nakshatras = chart_data.get("nakshatras_d1", {})
    if not nakshatras:
        return {}

    h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(lagna_idx + 6) % 12]]
    dk_planet = _find_darakaraka_planet(chart_data)
    key_planets = ["Ve", h7_lord, dk_planet]
    seen = set()
    key_planets = [p for p in key_planets if p and p not in seen and not seen.add(p)]

    insights = {}
    for p in key_planets:
        if p not in nakshatras:
            continue
        nak = nakshatras[p]
        lord = get_nakshatra_lord(nak)
        deity = get_nakshatra_deity(nak)
        meaning = get_nakshatra_meaning(nak, p)
        insights[p] = {
            "nakshatra": nak,
            "lord": SHORT_TO_FULL[lord] if lord else "Unknown",
            "deity": deity,
            "meaning": meaning,
        }
    return insights


def analyze_nakshatra_tara(chart_data, lagna_idx):
    """Nakshatra Tara compatibility between native Moon and spouse karakas."""
    nakshatras = chart_data.get("nakshatras_d1", {})
    if "Mo" not in nakshatras:
        return {"error": "Moon nakshatra unavailable"}

    nak_to_idx = {nak: idx for idx, nak in enumerate(NAKSHATRAS)}
    moon_nak = nakshatras["Mo"]
    moon_idx = nak_to_idx.get(moon_nak, -1)
    if moon_idx == -1:
        return {"error": f"Unknown Moon nakshatra: {moon_nak}"}

    h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(lagna_idx + 6) % 12]]
    dk_planet = _find_darakaraka_planet(chart_data)
    karakas = ["Ve", h7_lord, dk_planet]
    seen = set()
    karakas = [p for p in karakas if p and p not in seen and not seen.add(p)]

    tara_results = {}
    beneficial_taras = [2, 4, 6, 8, 9]  # Sampat, Kshema, Sadhana, Mitra, Parama Mitra

    for planet in karakas:
        if planet not in nakshatras:
            continue
        karaka_nak = nakshatras[planet]
        karaka_idx = nak_to_idx.get(karaka_nak, -1)
        if karaka_idx == -1:
            continue
        tara_num, tara_name = get_tara_relation(moon_idx, karaka_idx)
        desc = get_tara_description(tara_num)
        tara_results[planet] = {
            "nakshatra": karaka_nak,
            "tara": tara_num,
            "name": tara_name,
            "description": desc,
        }
    return tara_results


def detect_planetary_war(chart_data):
    """Graha Yuddha detection (conjunction within 1°)."""
    d1 = chart_data["planets"]
    planets = list(d1.keys())
    wars = []
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1 = planets[i]
            p2 = planets[j]
            if p1 in ["Ra", "Ke"] or p2 in ["Ra", "Ke"]:
                continue
            deg1 = d1[p1]["deg"]
            deg2 = d1[p2]["deg"]
            if abs(deg1 - deg2) <= 1.0:
                winner = p1 if deg1 < deg2 else p2
                loser = p2 if winner == p1 else p1
                wars.append(
                    {
                        "planets": [p1, p2],
                        "winner": winner,
                        "loser": loser,
                        "description": f"{SHORT_TO_FULL[winner]} wins over {SHORT_TO_FULL[loser]}, {SHORT_TO_FULL[loser]}"
                        "s results are weakened.",
                    }
                )
    return wars


def summarize_integrity(chart_data, lagna_idx):
    """Integrity summary for key marriage planets."""
    integrity = chart_data.get("integrity", {})
    key_planets = ["Ve", "Ju", _find_darakaraka_planet(chart_data)]
    h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(lagna_idx + 6) % 12]]
    if h7_lord not in key_planets:
        key_planets.append(h7_lord)
    summary = {}
    for p in key_planets:
        if p in integrity:
            summary[p] = integrity[p]
    return summary


def calculate_a7_darapada(chart_data, lagna_idx):
    """Calculate A7 Darapada — public image of marriage (Jaimini)."""
    d1 = chart_data["planets"]
    h7_idx = (lagna_idx + 6) % 12
    h7_sign = ZODIAC_SIGNS[h7_idx]
    h7_lord = SIGN_LORDS[h7_sign]
    if h7_lord not in d1:
        return {"sign": "Unknown", "status": "neutral", "meaning": "Data insufficient"}
    lord_sign = d1[h7_lord]["sign"]
    lord_idx = ZODIAC_SIGNS.index(lord_sign) if lord_sign in ZODIAC_SIGNS else 0
    distance = (lord_idx - h7_idx) % 12
    a7_idx = (lord_idx + distance) % 12
    if a7_idx == h7_idx:
        a7_idx = (h7_idx + 9) % 12
    elif a7_idx == (h7_idx + 6) % 12:
        a7_idx = ((h7_idx + 6) + 9) % 12
    a7_sign = ZODIAC_SIGNS[a7_idx]
    a7_lord = SIGN_LORDS[a7_sign]
    a7_lord_sign = d1.get(a7_lord, {}).get("sign", "")
    a7_dignity = get_dignity(a7_lord, a7_lord_sign)
    status = (
        "strong"
        if a7_dignity in ["Exalted", "Own"]
        else "afflicted" if a7_dignity == "Debilitated" else "neutral"
    )
    meaning = {
        "strong": "Attractive spouse image, harmonious public perception of marriage",
        "afflicted": "Challenges in public perception, possible delays/conflicts",
        "neutral": "Average public image of marriage",
    }.get(status, "")
    return {"sign": a7_sign, "lord": a7_lord, "status": status, "meaning": meaning}


def get_manglik_recommendation(severity, cancellations):
    """Provide recommendation text based on Manglik severity and cancellations."""
    if cancellations:
        return "Dosha is cancelled - no major concern. Normal compatibility check sufficient."
    if severity == "Mild":
        return "Mild dosha - prefer partner with similar Mars placement or perform simple remedies."
    if severity == "Moderate":
        return "Moderate dosha - partner should also be Manglik or have strong Venus/Jupiter. Consider remedies."
    return "Strong dosha - Important: Partner should be Manglik or have strong cancellations. Consult astrologer for remedies."
