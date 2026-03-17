# main.py (updated with spouse prediction support)
"""
Main orchestration module for Vedic kundali generation.
Coordinates all calculations and provides the primary API.
"""

import os
import sys
import datetime
import warnings
import swisseph as swe
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# Import all modules
from constants import (
    zodiac_signs,
    planets,
    sign_lords,
    short_to_full,
    dasha_lords,
    dasha_periods,
    nakshatra_lord_index,
    COMBUSTION_ORBS,
    NEECHA_BHANGA_INFO,
    FUNCTIONAL_QUALITY,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
    HOUSE_SIGNIFICATIONS,
    ASHTAKAVARGA_REKHAS,
    DIGNITY_SIGNS,
    CHART_WEIGHTS,
    AYANAMSA_OPTIONS,
    DEFAULT_AYANAMSA,
)
from utils import (
    get_sign,
    get_nakshatra,
    get_nakshatra_progress,
    get_dignity,
    get_lat_lon,
    is_retrograde,
    get_house_from_sign,
    datetime_to_jd,
    check_combustion,
    get_panchanga,
    get_sade_sati_status,
    get_navamsa_sign_and_deg,
    get_d7_sign_and_deg,
    get_d10_sign_and_deg,
    get_d60_sign_and_deg,
)
from neecha_bhanga import check_neecha_bhanga
from yoga_detection import detect_yogas
from dosha_detection import detect_problems
from dasha import (
    calculate_vimshottari_dasha,
    calculate_antardashas,
    find_current_dasha,
    get_current_pratyantar,
)
from marriage_scoring import calculate_marriage_score
from timings import generate_timings
from ashtakavarga import calculate_ashtakavarga
from interpretations import (
    interpret_aspects,
    interpret_navamsa,
    interpret_d7,
    interpret_d10,
    calculate_functional_strength_index,
    get_aspect_quality_score,
)
from printing import print_kundali
from rectification import rectify_birth_time


# -------------------------------------------------------------------
# Swiss Ephemeris Setup
# -------------------------------------------------------------------
_EPHE_DIR = os.path.dirname(os.path.abspath(__file__)) or "."
swe.set_ephe_path(_EPHE_DIR)
_REQUIRED_FILES = ["sepl_18.se1", "semo_18.se1"]
_missing = [
    f for f in _REQUIRED_FILES if not os.path.isfile(os.path.join(_EPHE_DIR, f))
]
if _missing:
    warnings.warn(
        f"Swiss Ephemeris data files missing from '{_EPHE_DIR}': {', '.join(_missing)}. "
        "Swiss Ephemeris will fall back to less accurate Moshier mode. "
        "Download .se1 files from https://www.astro.com/ftp/swisseph/ephe/"
    )
swe.set_sid_mode(swe.SIDM_LAHIRI)


def calculate_functional_nature(result):
    """Calculate functional nature for all planets and return dict of {planet: {score, label}}."""
    functional = {}
    for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        if pl in result["planets"]:
            fsi = calculate_functional_strength_index(result, pl)
            functional[pl] = {"score": fsi["score"], "label": fsi["effective_class"]}
    return functional


def calculate_integrity_index(result):
    """
    Cross-Chart Planetary Integrity Index (D1-D9-D10-D7).
    Returns dict of {planet: {score, label}}.
    """
    integrity = {}
    planets_data = result["planets"]
    navamsa = result.get("navamsa", {})
    d10 = result.get("d10", {})
    d7 = result.get("d7", {})

    DIGNITY_SIGNS = {
        "Su": {"exalt": "Aries", "own": ["Leo"], "deb": "Libra"},
        "Mo": {"exalt": "Taurus", "own": ["Cancer"], "deb": "Scorpio"},
        "Ma": {"exalt": "Capricorn", "own": ["Aries", "Scorpio"], "deb": "Cancer"},
        "Me": {"exalt": "Virgo", "own": ["Gemini", "Virgo"], "deb": "Pisces"},
        "Ju": {"exalt": "Cancer", "own": ["Sagittarius", "Pisces"], "deb": "Capricorn"},
        "Ve": {"exalt": "Pisces", "own": ["Taurus", "Libra"], "deb": "Virgo"},
        "Sa": {"exalt": "Libra", "own": ["Capricorn", "Aquarius"], "deb": "Aries"},
    }
    CHART_WEIGHTS = {"D1": 1.0, "D9": 2.0, "D10": 1.0, "D7": 1.0}

    for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        if pl not in planets_data:
            continue

        integrity_score = 50
        positions = {"D1": planets_data[pl]["sign"]}
        strong_count = 0
        weak_count = 0

        for chart_name, chart_data in [("D9", navamsa), ("D10", d10), ("D7", d7)]:
            if pl in chart_data:
                positions[chart_name] = chart_data[pl]["sign"]

        dig_info = DIGNITY_SIGNS.get(pl, {})
        for chart, sign in positions.items():
            w = CHART_WEIGHTS.get(chart, 1.0)
            if sign == dig_info.get("exalt"):
                integrity_score += int((15 if chart == "D1" else 10) * w)
                strong_count += 1
            elif sign in dig_info.get("own", []):
                integrity_score += int((12 if chart == "D1" else 8) * w)
                strong_count += 1
            elif sign == dig_info.get("deb"):
                integrity_score -= int((15 if chart == "D1" else 8) * w)
                weak_count += 1

        # Vargottama bonus
        if pl in navamsa and planets_data[pl]["sign"] == navamsa[pl]["sign"]:
            integrity_score += 15

        # Triple alignment bonus
        if pl in navamsa and pl in d10:
            if planets_data[pl]["sign"] == navamsa[pl]["sign"] == d10[pl]["sign"]:
                integrity_score += 20

        integrity_score = max(0, min(100, integrity_score))

        # Classify reliability
        if integrity_score >= 80 and weak_count == 0:
            label = "Highly Reliable (Triple Confirmation)"
        elif integrity_score >= 65 and strong_count >= 2:
            label = "Reliable (Multi-Chart Support)"
        elif integrity_score >= 50:
            label = "Moderate (Needs Activation)"
        elif weak_count >= 2:
            label = "Challenged (Karmic Work Required)"
        else:
            label = "Variable (Context-Dependent)"

        integrity[pl] = {"score": integrity_score, "label": label}

    return integrity


def extract_dasha_periods_for_marriage(timings):
    """Parse marriage timing lines into list of (start_year, end_year, md, ad)."""
    periods = []
    marriage_lines = timings.get("Marriage", [])
    for line in marriage_lines:
        import re

        m = re.search(r"─\s*(\w+)/(\w+)\s*\((\d{4})-(\d{4})\)", line)
        if m:
            md = m.group(1)
            ad = m.group(2)
            start = int(m.group(3))
            end = int(m.group(4))
            periods.append(
                {"maha": md, "antara": ad, "start": start, "end": end, "score": 8}
            )  # Default score for predictor
    return periods


def calculate_kundali(
    birth_date_str, birth_time_str, place, gender="Male", ayanamsa_name=DEFAULT_AYANAMSA
):
    """
    Calculate the complete Vedic kundali for given birth details.

    Args:
        birth_date_str (str): Date in YYYY-MM-DD format.
        birth_time_str (str): Time in HH:MM 24-hour format.
        place (str): Birth place (city, country).
        gender (str): "Male" or "Female".
        ayanamsa_name (str): Ayanamsa choice like "Lahiri", "Raman" etc. (default DEFAULT_AYANAMSA).

    Returns:
        dict: Complete kundali result with all calculated data.
    """
    y, m, d = map(int, birth_date_str.split("-"))
    hh, mm = map(int, birth_time_str.split(":"))
    lat, lon = get_lat_lon(place)
    result = {}
    result["lat"] = lat
    result["lon"] = lon
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if not tz_name:
        raise ValueError("Timezone could not be determined")
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime.datetime(y, m, d, hh, mm))
    utc_dt = local_dt.astimezone(pytz.utc)
    birth_jd = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute / 60.0
    )

    # Set ayanamsa
    ayanamsa_code = AYANAMSA_OPTIONS.get(ayanamsa_name, swe.SIDM_LAHIRI)
    swe.set_sid_mode(ayanamsa_code)

    # Houses & Lagna
    house_data = swe.houses_ex(birth_jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    cusps, ascmc = house_data
    lagna_deg = ascmc[0]
    lagna_sign = get_sign(lagna_deg)
    lagna_idx = zodiac_signs.index(lagna_sign)
    house_planets = {i + 1: [] for i in range(12)}
    planet_data = {}
    moon_sign = None
    moon_nakshatra = None
    sun_full_lon = None

    # Store nakshatras for later
    nakshatras_d1 = {}

    for code, pid in planets.items():
        pos_speed = swe.calc_ut(birth_jd, pid, swe.FLG_SIDEREAL)[0]
        lon = pos_speed[0]
        speed = pos_speed[3]
        sign = get_sign(lon)
        deg_in_sign = round(lon % 30, 2)
        nak = get_nakshatra(lon)
        dignity = get_dignity(code, sign)
        retro = is_retrograde(speed)
        if code == "Su":
            sun_full_lon = lon
        planet_data[code] = {
            "deg": deg_in_sign,
            "full_lon": round(lon, 4),
            "sign": sign,
            "nakshatra": nak,
            "dignity": dignity,
            "retro": retro,
            "combust": False,  # filled after Sun lon is known
            "neecha_bhanga": False,  # filled after all planets are placed
            "navamsa_sign": None,
            "navamsa_deg": None,
            "d7_sign": None,
            "d7_deg": None,
            "d10_sign": None,
            "d10_deg": None,
        }
        nakshatras_d1[code] = nak
        if code == "Mo":
            moon_sign = sign
            moon_nakshatra = nak
        p_idx = zodiac_signs.index(sign)
        house = get_house_from_sign(lagna_idx, p_idx)
        house_planets[house].append(code)

    # Combustion check (requires Sun longitude computed first)
    if sun_full_lon is not None:
        for code in planet_data:
            if code == "Su":
                continue
            planet_data[code]["combust"] = check_combustion(
                code,
                planet_data[code]["full_lon"],
                sun_full_lon,
                planet_data[code]["retro"],
            )

    # Neecha Bhanga
    moon_house_nb = None
    for _h, _plist in house_planets.items():
        if "Mo" in _plist:
            moon_house_nb = _h
            break
    neecha_bhanga_planets = []
    for code in list(planet_data.keys()):
        if code in ("Su", "Ra", "Ke"):
            continue
        nb = check_neecha_bhanga(
            code, planet_data, house_planets, lagna_idx, moon_house_nb
        )
        planet_data[code]["neecha_bhanga"] = nb
        if nb:
            neecha_bhanga_planets.append(code)

    # Ketu (from Rahu)
    ra_lon = swe.calc_ut(birth_jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
    ke_lon = (ra_lon + 180) % 360
    ke_sign = get_sign(ke_lon)
    ke_deg = round(ke_lon % 30, 2)
    ke_nak = get_nakshatra(ke_lon)
    ke_dignity = get_dignity("Ke", ke_sign)
    planet_data["Ke"] = {
        "deg": ke_deg,
        "sign": ke_sign,
        "nakshatra": ke_nak,
        "dignity": ke_dignity,
        "retro": True,
        "combust": False,
        "neecha_bhanga": False,
        "navamsa_sign": None,
        "navamsa_deg": None,
        "d7_sign": None,
        "d7_deg": None,
        "d10_sign": None,
        "d10_deg": None,
    }
    nakshatras_d1["Ke"] = ke_nak
    ke_idx = zodiac_signs.index(ke_sign)
    ke_house = get_house_from_sign(lagna_idx, ke_idx)
    house_planets[ke_house].append("Ke")
    house_planets[1].append("Asc")  # Ascendant in 1st house
    planet_data["Ke"]["full_lon"] = round(ke_lon, 4)

    # 7th Lord
    seventh_idx = (lagna_idx + 6) % 12
    seventh_sign = zodiac_signs[seventh_idx]
    seventh_lord = sign_lords[seventh_sign]

    # House Lord Placements
    house_lord_map = {}  # house_num → (lord_code, lord_in_house)
    for h_num in range(1, 13):
        h_sign = zodiac_signs[(lagna_idx + h_num - 1) % 12]
        h_lord = sign_lords[h_sign]
        # Find which house the lord is placed in
        lord_in_house = None
        for ph, plist in house_planets.items():
            if h_lord in plist:
                lord_in_house = ph
                break
        house_lord_map[h_num] = {"lord": h_lord, "placed_in": lord_in_house}

    # Add interpretations for key marriage houses 2,5,7 used by spouse_predictor
    from constants import HOUSE_LORD_IN_HOUSE

    for h_num in range(1, 13):
        info = house_lord_map[h_num]
        if info["placed_in"]:
            key = (h_num, info["placed_in"])
            interp = HOUSE_LORD_IN_HOUSE.get(
                key,
                f"Lord of House {h_num} ({zodiac_signs[(lagna_idx + h_num - 1) % 12]}) placed in House {info['placed_in']}: "
                f"House {h_num} themes expressed through House {info['placed_in']} environment.",
            )
            house_lord_map[h_num]["interpretation"] = interp
        else:
            interp_sign = zodiac_signs[(lagna_idx + h_num - 1) % 12]
            house_lord_map[h_num][
                "interpretation"
            ] = f"Lord of House {h_num} ({interp_sign}) position undetermined - themes delayed or indirect."

    # Birth Panchanga
    sun_lon_birth = planet_data["Su"]["full_lon"]
    moon_lon_birth = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    panchanga = get_panchanga(birth_jd, sun_lon_birth, moon_lon_birth)

    # Divisional Charts
    for code in planet_data:
        if code == "Ra":
            p_lon = ra_lon
        elif code == "Ke":
            p_lon = ke_lon
        else:
            p_lon = (zodiac_signs.index(planet_data[code]["sign"]) * 30) + planet_data[
                code
            ]["deg"]
        ns, nd = get_navamsa_sign_and_deg(p_lon)
        d7s, d7d = get_d7_sign_and_deg(p_lon)
        d10s, d10d = get_d10_sign_and_deg(p_lon)
        d60s, d60d = get_d60_sign_and_deg(p_lon)
        planet_data[code]["navamsa_sign"] = ns
        planet_data[code]["navamsa_deg"] = nd
        planet_data[code]["d7_sign"] = d7s
        planet_data[code]["d7_deg"] = d7d
        planet_data[code]["d10_sign"] = d10s
        planet_data[code]["d10_deg"] = d10d
        planet_data[code]["d60_sign"] = d60s
        planet_data[code]["d60_deg"] = d60d

    # Vimshottari
    moon_lon = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    start_lord, balance_y, dashas_raw = calculate_vimshottari_dasha(moon_lon, birth_jd)
    dashas = [calculate_antardashas(md) for md in dashas_raw]

    # Current time (UTC)
    now_utc = datetime.datetime.now(pytz.utc)
    current_jd = datetime_to_jd(now_utc)
    current_md, current_ad = find_current_dasha(birth_jd, current_jd, dashas)
    current_pd, pd_start_jd, pd_end_jd = get_current_pratyantar(
        birth_jd, current_jd, current_md, current_ad, dashas
    )

    # Aspects
    aspects = {h: [] for h in range(1, 13)}
    planet_houses = {
        p: h for h, plist in house_planets.items() for p in plist if p != "Asc"
    }
    for planet, ph in planet_houses.items():
        aspect_h = ((ph - 1 + 6) % 12) + 1
        aspects[aspect_h].append(f"{planet}-7th")
    special = {"Ma": [3, 7], "Ju": [4, 8], "Sa": [2, 9]}
    for planet, offsets in special.items():
        if planet in planet_houses:
            ph = planet_houses[planet]
            for offset in offsets:
                ah = ((ph - 1 + offset) % 12) + 1
                aspects[ah].append(f"{planet}-{offset + 1}")
    for node in ["Ra", "Ke"]:
        if node in planet_houses:
            nh = planet_houses[node]
            for offset in [4, 8]:
                ah = ((nh - 1 + offset) % 12) + 1
                aspects[ah].append(f"{node}-5/9")

    # Transits
    from constants import gochara_effects

    transits = {}
    for pcode, pid in planets.items():
        lon = swe.calc_ut(current_jd, pid, swe.FLG_SIDEREAL)[0][0]
        sign = get_sign(lon)
        sign_idx = zodiac_signs.index(sign)
        rel_house = ((sign_idx - zodiac_signs.index(moon_sign) + 12) % 12) + 1
        effect = gochara_effects.get(pcode, {}).get(rel_house, "Neutral")
        transits[pcode] = {"sign": sign, "house_from_moon": rel_house, "effect": effect}
    # Add Rahu/Ketu transits
    ra_lon = swe.calc_ut(current_jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
    ra_sign = get_sign(ra_lon)
    ra_idx = zodiac_signs.index(ra_sign)
    ra_house = ((ra_idx - zodiac_signs.index(moon_sign) + 12) % 12) + 1
    transits["Ra"] = {
        "sign": ra_sign,
        "house_from_moon": ra_house,
        "effect": gochara_effects.get("Ra", {}).get(ra_house, "Neutral"),
    }
    ke_lon = (ra_lon + 180) % 360
    ke_sign = get_sign(ke_lon)
    ke_idx = zodiac_signs.index(ke_sign)
    ke_house = ((ke_idx - zodiac_signs.index(moon_sign) + 12) % 12) + 1
    transits["Ke"] = {
        "sign": ke_sign,
        "house_from_moon": ke_house,
        "effect": gochara_effects.get("Ke", {}).get(ke_house, "Neutral"),
    }

    # Sade Sati / Dhaiya
    sa_transit_sign = transits.get("Sa", {}).get("sign", None)
    sade_sati_status = (
        get_sade_sati_status(moon_sign, sa_transit_sign) if sa_transit_sign else None
    )

    # Build result dictionary
    result = {
        "gender": gender,
        "lagna_deg": round(lagna_deg, 2),
        "lagna_sign": lagna_sign,
        "seventh_lord": seventh_lord,
        "planets": planet_data,
        "houses": house_planets,
        "moon_sign": moon_sign,
        "moon_nakshatra": moon_nakshatra,
        "vimshottari": {
            "starting_lord": start_lord,
            "balance_at_birth_years": round(balance_y, 2),
            "mahadasas": dashas,
            "current_md": current_md,
            "current_ad": current_ad,
        },
        "aspects": aspects,
        "navamsa": {
            p: {"sign": d["navamsa_sign"], "deg": d["navamsa_deg"]}
            for p, d in planet_data.items()
        },
        "d7": {
            p: {"sign": d["d7_sign"], "deg": d["d7_deg"]}
            for p, d in planet_data.items()
        },
        "d10": {
            p: {"sign": d["d10_sign"], "deg": d["d10_deg"]}
            for p, d in planet_data.items()
        },
        "d60": {
            p: {"sign": d["d60_sign"], "deg": d["d60_deg"]}
            for p, d in planet_data.items()
            if "d60_sign" in d
        },
        "transits": transits,
        "birth_year": y,
        "birth_month": m,
        "birth_day": d,
        "birth_date": birth_date_str,
        "birth_time": birth_time_str,
        "birth_place": place,
        "birth_jd": birth_jd,
        "panchanga": panchanga,
        "house_lords": house_lord_map,
        "ayanamsa": ayanamsa_name,
        "sade_sati": sade_sati_status,
        "vimshottari_pd": {
            "current_pd": current_pd,
            "pd_start_jd": pd_start_jd,
            "pd_end_jd": pd_end_jd,
        },
        "nakshatras_d1": nakshatras_d1,
        "neecha_bhanga_planets": neecha_bhanga_planets,
    }

    # Jaimini Charakaraka (moved here after result dict exists)
    from jaimini import calculate_charakaraka, get_karakamsa_lagna

    charakaraka = calculate_charakaraka(planet_data, result["navamsa"])
    atmakaraka = charakaraka.get("Atmakaraka")
    karakamsa_lagna = (
        get_karakamsa_lagna(atmakaraka, result["navamsa"]) if atmakaraka else None
    )

    result["jaimini"] = {
        "charakaraka": charakaraka,
        "atmakaraka": atmakaraka,
        "karakamsa_lagna": karakamsa_lagna,
    }

    # Add yogas, timings, problems, and ashtakavarga
    result["yogas"] = detect_yogas(result)
    result["timings"] = generate_timings(result, y, birth_jd)
    result["problems"] = detect_problems(result)
    result["ashtakavarga"] = calculate_ashtakavarga(result)

    # Additional fields for spouse predictor
    result["functional_nature"] = calculate_functional_nature(result)
    result["integrity"] = calculate_integrity_index(result)
    result["dasha_periods_for_marriage"] = extract_dasha_periods_for_marriage(
        result["timings"]
    )
    result["lord7_full"] = short_to_full.get(seventh_lord, seventh_lord)
    # Planets with full names and longitudes for marriage date prediction
    result["planets_full_long"] = {}
    for code, data in planet_data.items():
        full = short_to_full.get(code, code)
        result["planets_full_long"][full] = data["full_lon"]
    # Birth date as datetime object
    result["birth_datetime"] = local_dt

    result["final_analysis"] = generate_final_analysis(result)

    return result


def generate_final_analysis(result):
    """Generate a final summary analysis of the kundali."""
    yogas = result["yogas"]
    problems = result["problems"]
    timings = result["timings"]
    lagna = result["lagna_sign"]
    moon_sign = result["moon_sign"]
    moon_nak = result["moon_nakshatra"]
    vim = result["vimshottari"]
    current_md = vim["current_md"]
    current_ad = vim["current_ad"]
    birth_year = result["birth_year"]
    birth_jd = result["birth_jd"]

    # --- Dynamic: find when current Mahadasha ends ---
    md_end_year = None
    for md in vim["mahadasas"]:
        if md["lord"] == current_md:
            md_end_year = int(birth_year + (md["end_jd"] - birth_jd) / 365.25)
            break

    # --- Dynamic: first yoga name ---
    if yogas and yogas != ["No major classical yogas formed"]:
        first_yoga_name = yogas[0].split(" (")[0]
        yoga_summary = (
            f"Strong benefics create yogas like {first_yoga_name}, indicating potential "
            f"for success in wisdom- and Jupiter/Venus-driven fields."
        )
    else:
        yoga_summary = "Limited classical yogas; growth through steady effort."

    # --- Dynamic: primary doshas ---
    active_doshas = [p["summary"].split(":")[0] for p in problems if p.get("detail")]

    # --- Dynamic: first timing period ---
    first_event = list(timings.keys())[0]
    first_range = "upcoming years"
    for _event, _periods in timings.items():
        if _periods:
            first_event = _event
            import re

            _m = re.search(r"\((\d{4}-\d{4})\)", _periods[0])
            first_range = _m.group(1) if _m else "upcoming years"
            break

    # --- Dynamic: current dasha description ---
    current_md_full = (
        short_to_full.get(current_md, current_md) if current_md else "Unknown"
    )
    current_ad_full = (
        short_to_full.get(current_ad, current_ad) if current_ad else "Unknown"
    )
    dasha_desc = f"{current_md_full}/{current_ad_full} Antardasha"

    # --- Dynamic: planet qualities for current MD ---
    md_qualities = {
        "Mercury": "analytical thinking and communication are heightened",
        "Jupiter": "wisdom, expansion, and spiritual growth dominate",
        "Venus": "relationships, beauty, and material comforts take center stage",
        "Saturn": "discipline, hard work, and karmic dues come to the fore",
        "Mars": "energy, ambition, and assertiveness are activated",
        "Sun": "leadership, fame, and self-expression are in focus",
        "Moon": "emotions, family, and mental sensitivity are heightened",
        "Rahu": "ambition, foreign exposure, and unconventional paths open",
        "Ketu": "detachment, spirituality, and past-karma resolution dominate",
    }
    md_quality = md_qualities.get(
        current_md_full, "the dasha lord's significations are active"
    )

    # --- Build analysis ---
    analysis = "### Final Analysis: Overall Chart Balance, Active Doshas, and Direct Life Outcomes\n"
    analysis += f"Your Kundali ({lagna} Lagna, {moon_sign} Moon in {moon_nak}) shows a distinctive planetary configuration: "
    analysis += yoga_summary + "\n"
    analysis += (
        f"Doshas indicate areas of concentrated planetary energy that require attention, "
        f"not fixed negative fate. They reflect learning opportunities and growth areas.\n"
    )
    analysis += "- Why Present? Natal positions place malefics in sensitive houses/signs, creating lessons in "
    if active_doshas:
        analysis += f"areas ruled by {', '.join(d.split('(')[0].strip() for d in active_doshas)}.\n"
    else:
        analysis += "patience, clarity, and harmony.\n"
    analysis += "- Direct Outcomes: "
    if not active_doshas:
        analysis += "Balanced chart with minimal challenges; leverage positive transits actively. "
    else:
        analysis += (
            "Potential delays in stability and clarity in decisions; intense life phases may bring "
            "career shifts and emotional highs/lows as karmic debts resolve. "
        )
    analysis += (
        f"Positive: High-strength yogas promise material gains and wisdom; "
        f"key fructification window for {first_event} is around {first_range}.\n"
    )
    if md_end_year:
        analysis += (
            f"- Overall Trajectory: In the current {dasha_desc}, {md_quality}. "
            f"This Mahadasha runs until ~{md_end_year}, after which the next dasha brings a shift in life theme. "
            f"Focus remedies now to mitigate active doshas and capitalise on strong yoga periods."
        )
    else:
        analysis += (
            f"- Overall Trajectory: In the current {dasha_desc}, {md_quality}. "
            f"Focus remedies to mitigate active doshas and capitalise on strong yoga periods."
        )
    return analysis


def main():
    """Command-line entry point."""
    print("Vedic Kundali Generator – Full Version with D7, D10 & Marriage Timing")
    print("─────────────────────────────────────────────────────────────────────\n")
    while True:
        name = input("Enter Name : ").strip()
        gender_input = input("Gender (M/F) : ").strip().upper()
        while gender_input not in ("M", "F"):
            print("Please enter M for Male or F for Female")
            gender_input = input("Gender (M/F) : ").strip().upper()
        gender = "Male" if gender_input == "M" else "Female"
        date_str = input("Birth Date (YYYY-MM-DD) : ").strip()
        time_str = input("Birth Time (HH:MM 24h) : ").strip()
        place = input("Birth Place (City, Country) : ").strip()

        print(
            "\nAyanamsa options: Lahiri, Raman, KP (Krishnamurti), True Chitra, Yukteshwar, Djwhal Khul"
        )
        ayanamsa_choice = input("Choose ayanamsa (default Lahiri): ").strip()
        if not ayanamsa_choice:
            ayanamsa_choice = "Lahiri"
        # validate (optional)
        if ayanamsa_choice not in AYANAMSA_OPTIONS:
            print("Invalid choice, using Lahiri.")
            ayanamsa_choice = "Lahiri"
        try:
            result = calculate_kundali(
                date_str, time_str, place, gender=gender, ayanamsa_name=ayanamsa_choice
            )
            result["name"] = name  # Store name in result
            import os

            outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")
            os.makedirs(outputs_dir, exist_ok=True)
            filename = os.path.join(outputs_dir, f"{name}_kundali_report.txt")
            with open(filename, "w", encoding="utf-8") as f:
                print_kundali(result, file=f)
            print(f"\nReport saved as '{filename}'")

            # Full spouse + marriage date prediction
            from datetime import datetime as dt

            try:
                from spouse_predictor import AdvancedSpousePredictor

                # Spouse analysis
                predictor = AdvancedSpousePredictor(result)
                spouse_report = predictor.generate_report()

                # Match outer filename pattern: input_basename.replace(".txt", "_spouse_prediction.txt")
                report_base = f"{name}_kundali_report"
                spouse_filename = os.path.join(
                    outputs_dir, f"{report_base}_spouse_prediction.txt"
                )

                with open(spouse_filename, "w", encoding="utf-8") as f:
                    f.write(spouse_report)
                print(f"Full spouse + marriage prediction saved as '{spouse_filename}'")

            except Exception as e:
                print(f"Spouse predictor error: {e}")
                import traceback

                traceback.print_exc()
                print("Continuing with basic kundali report...")

            # Optional: Birth Time Rectification
            rectify_choice = input("\nWould you like to rectify birth time using life events? (y/n): ").strip().lower()
            if rectify_choice == 'y':
                print("\nEnter 3+ major life events.")
                events = []
                while len(events) < 10:  # Max 10
                    event_date = input(f"Event {len(events)+1} date (YYYY-MM-DD) [enter to finish]: ").strip()
                    if not event_date:
                        break
                    try:
                        ev_dt = datetime.datetime.strptime(event_date, "%Y-%m-%d")
                    except ValueError:
                        print("Invalid date. Skipping.")
                        continue
                    event_desc = input("Description (e.g. 'marriage'): ").strip()
                    event_house = input("House (1-12): ").strip()
                    try:
                        house_num = int(event_house)
                        if not 1 <= house_num <= 12:
                            raise ValueError
                    except ValueError:
                        print("Invalid house. Skipping.")
                        continue
                    planets_input = input("Planets (e.g. Ve,Ju,Mo) [skip]: ").strip()
                    planets = [p.strip().upper() for p in planets_input.split(',') if p.strip()] if planets_input else []
                    events.append({
                        'date': ev_dt,
                        'house': house_num,
                        'description': event_desc,
                        'planets': planets
                    })
                    print(f"Added event {len(events)}.")
                if len(events) >= 3:
                    rect_result = rectify_birth_time(result, events)
                    print("\n" + "="*60)
                    print("BIRTH TIME RECTIFICATION RESULT (KP + Prenatal Epoch)")
                    print("="*60)
                    print(f"Original: {rect_result['original_birth_time']}")
                    print(f"Corrected: {rect_result['corrected_birth_time']}")
                    print(f"Offset: {rect_result['offset_minutes']:+d} minutes")
                    print(f"Confidence: {rect_result['confidence_score']} (based on {rect_result['events_used']} events)")
                    regen = input("\nRegenerate kundali with corrected time? (y/n): ").strip().lower()
                    if regen == 'y':
                        corr_dt = datetime.datetime.strptime(rect_result['corrected_birth_time'], '%Y-%m-%d %H:%M')
                        corr_date_str = corr_dt.strftime("%Y-%m-%d")
                        corr_time_str = corr_dt.strftime("%H:%M")
                        result = calculate_kundali(corr_date_str, corr_time_str, place, gender=gender, ayanamsa_name=ayanamsa_choice)
                        result["name"] = name
                        rect_filename = os.path.join(outputs_dir, f"{name}_kundali_rectified.txt")
                        with open(rect_filename, "w", encoding="utf-8") as f:
                            print_kundali(result, file=f)
                        print(f"Rectified report: '{rect_filename}'")
                else:
                    print("Need 3+ events for rectification.")

            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Tips: Use place='Mumbai, Maharashtra, India'")
            print(" Make sure Swiss Ephemeris .se1 files are in the same folder")
            print("Please re-enter the details.\n")

    swe.close()


if __name__ == "__main__":
    main()
