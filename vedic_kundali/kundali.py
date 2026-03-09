# Main Vedic Kundali Calculator
# Refactored to use modular components

import re
import swisseph as swe
import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# Import all modules
from constants import (
    zodiac_signs,
    planets,
    sign_lords,
    short_to_full,
    HOUSE_SIGNIFICATIONS,
    LAGNA_REMEDIES,
    SEVENTH_LORD_REMEDIES,
    FUNCTIONAL_QUALITY,
)

from astro_utils import (
    setup_swiss_ephemeris,
    get_sign,
    get_nakshatra,
    get_dignity,
    get_house_from_sign,
    is_retrograde,
    datetime_to_jd,
    check_combustion,
    check_neecha_bhanga,
    get_panchanga,
    get_sade_sati_status,
)

from divisional import (
    get_navamsa_sign_and_deg,
    get_d7_sign_and_deg,
    get_d10_sign_and_deg,
)

from dasha import (
    calculate_vimshottari_dasha,
    calculate_antardashas,
    find_current_dasha,
    get_current_pratyantar,
)

from yogas import (
    detect_yogas,
    get_yoga_strength,
)

from doshas import detect_problems

from timings import generate_timings

from analysis import (
    calculate_functional_strength_index,
    interpret_aspects,
    interpret_navamsa,
    interpret_d7,
    interpret_d10,
)

from ashtakavarga import (
    calculate_ashtakavarga,
    calculate_integrity_index,
)


# ────────────────────────────────────────────────
# Aspects & Transits
# ────────────────────────────────────────────────
def calculate_aspects(houses):
    """Calculate planetary aspects."""
    aspects = {h: [] for h in range(1, 13)}
    planet_houses = {p: h for h, plist in houses.items() for p in plist if p != "Asc"}
    
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
    
    return aspects


def calculate_transits(natal_moon_sign, current_jd):
    """Calculate current transits from Moon."""
    from constants import gochara_effects
    
    transits = {}
    moon_idx = zodiac_signs.index(natal_moon_sign)
    
    for pcode, pid in planets.items():
        lon = swe.calc_ut(current_jd, pid, swe.FLG_SIDEREAL)[0][0]
        sign = get_sign(lon)
        sign_idx = zodiac_signs.index(sign)
        rel_house = ((sign_idx - moon_idx + 12) % 12) + 1
        effect = gochara_effects.get(pcode, {}).get(rel_house, "Neutral")
        transits[pcode] = {"sign": sign, "house_from_moon": rel_house, "effect": effect}
    
    ra_lon = swe.calc_ut(current_jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
    ra_sign = get_sign(ra_lon)
    ra_idx = zodiac_signs.index(ra_sign)
    ra_house = ((ra_idx - moon_idx + 12) % 12) + 1
    transits["Ra"] = {
        "sign": ra_sign,
        "house_from_moon": ra_house,
        "effect": gochara_effects.get("Ra", {}).get(ra_house, "Neutral"),
    }
    
    ke_lon = (ra_lon + 180) % 360
    ke_sign = get_sign(ke_lon)
    ke_idx = zodiac_signs.index(ke_sign)
    ke_house = ((ke_idx - moon_idx + 12) % 12) + 1
    transits["Ke"] = {
        "sign": ke_sign,
        "house_from_moon": ke_house,
        "effect": gochara_effects.get("Ke", {}).get(ke_house, "Neutral"),
    }
    
    return transits


# ────────────────────────────────────────────────
# Generate Final Analysis
# ────────────────────────────────────────────────
def generate_final_analysis(result):
    """Generate final analysis text."""
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

    # Find when current Mahadasha ends
    md_end_year = None
    for md in vim["mahadasas"]:
        if md["lord"] == current_md:
            md_end_year = int(birth_year + (md["end_jd"] - birth_jd) / 365.25)
            break

    # First yoga name
    if yogas and yogas != ["No major classical yogas formed"]:
        first_yoga_name = yogas[0].split(" (")[0]
        yoga_summary = f"Strong benefics create yogas like {first_yoga_name}, indicating potential for success."
    else:
        yoga_summary = "Limited classical yogas; growth through steady effort."

    # Active doshas
    active_doshas = [p["summary"].split(":")[0] for p in problems if p["detail"]]

    # First timing
    first_event = list(timings.keys())[0]
    first_range = "upcoming years"
    for _event, _periods in timings.items():
        if _periods:
            first_event = _event
            _m = re.search(r'\((\d{4}-\d{4})\)', _periods[0])
            first_range = _m.group(1) if _m else "upcoming years"
            break

    # Current dasha
    current_md_full = short_to_full.get(current_md, current_md) if current_md else "Unknown"
    current_ad_full = short_to_full.get(current_ad, current_ad) if current_ad else "Unknown"
    dasha_desc = f"{current_md_full}/{current_ad_full} Antardasha"

    # Planet qualities
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
    md_quality = md_qualities.get(current_md_full, "the dasha lord's significations are active")

    # Build analysis
    analysis = "### Final Analysis: Overall Chart Balance, Active Doshas, and Direct Life Outcomes\n"
    analysis += f"Your Kundali ({lagna} Lagna, {moon_sign} Moon in {moon_nak}) shows a distinctive planetary configuration: "
    analysis += yoga_summary + "\n"
    analysis += "Doshas indicate areas of concentrated planetary energy that require attention, not fixed negative fate.\n"
    analysis += "- Why Present? Natal positions place malefics in sensitive houses/signs, creating lessons in "
    if active_doshas:
        analysis += f"areas ruled by {', '.join(d.split('(')[0].strip() for d in active_doshas)}.\n"
    else:
        analysis += "patience, clarity, and harmony.\n"
    analysis += "- Direct Outcomes: "
    if not active_doshas:
        analysis += "Balanced chart with minimal challenges; leverage positive transits actively. "
    else:
        analysis += "Potential delays in stability and clarity; intense life phases may bring career shifts and emotional highs/lows. "
    analysis += f"Positive: High-strength yogas promise material gains and wisdom; key fructification window for {first_event} is around {first_range}.\n"
    
    if md_end_year:
        analysis += f"- Overall Trajectory: In the current {dasha_desc}, {md_quality}. This Mahadasha runs until ~{md_end_year}, after which the next dasha brings a shift in life theme."
    else:
        analysis += f"- Overall Trajectory: In the current {dasha_desc}, {md_quality}."
    
    return analysis


# ────────────────────────────────────────────────
# Main Kundali Calculation
# ────────────────────────────────────────────────
def calculate_kundali(birth_date_str, birth_time_str, place, gender="Male"):
    """Calculate complete Kundali with all charts and analysis."""
    # Initialize Swiss Ephemeris
    setup_swiss_ephemeris()
    
    # Parse date and time
    y, m, d = map(int, birth_date_str.split("-"))
    hh, mm = map(int, birth_time_str.split(":"))
    
    # Get location
    geo = Nominatim(user_agent="vedic_kundali_cli")
    loc = geo.geocode(place, timeout=15)
    if not loc:
        raise ValueError(f"Location not found: {place}. Try 'Mumbai, Maharashtra, India'")
    lat, lon = loc.latitude, loc.longitude
    
    # Get timezone
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if not tz_name:
        raise ValueError("Timezone could not be determined")
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime.datetime(y, m, d, hh, mm))
    utc_dt = local_dt.astimezone(pytz.utc)
    birth_jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute / 60.0)
    
    # Houses & Lagna
    house_data = swe.houses_ex(birth_jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    cusps, ascmc = house_data
    lagna_deg = ascmc[0]
    lagna_sign = get_sign(lagna_deg)
    lagna_idx = zodiac_signs.index(lagna_sign)
    
    # Initialize house planets
    house_planets = {i + 1: [] for i in range(12)}
    planet_data = {}
    moon_sign = None
    moon_nakshatra = None
    sun_full_lon = None
    
    # Calculate planet positions
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
            "combust": False,
            "neecha_bhanga": False,
            "navamsa_sign": None,
            "navamsa_deg": None,
            "d7_sign": None,
            "d7_deg": None,
            "d10_sign": None,
            "d10_deg": None,
        }
        
        if code == "Mo":
            moon_sign = sign
            moon_nakshatra = nak
        
        p_idx = zodiac_signs.index(sign)
        house = get_house_from_sign(lagna_idx, p_idx)
        house_planets[house].append(code)
    
    # Combustion check
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
    
    for code in list(planet_data.keys()):
        if code in ("Su", "Ra", "Ke"):
            continue
        planet_data[code]["neecha_bhanga"] = check_neecha_bhanga(
            code, planet_data, house_planets, lagna_idx, moon_house_nb
        )
    
    # Ketu
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
        "full_lon": round(ke_lon, 4),
    }
    
    ke_idx = zodiac_signs.index(ke_sign)
    ke_house = get_house_from_sign(lagna_idx, ke_idx)
    house_planets[ke_house].append("Ke")
    house_planets[1].append("Asc")
    
    # 7th Lord
    seventh_idx = (lagna_idx + 6) % 12
    seventh_sign = zodiac_signs[seventh_idx]
    seventh_lord = sign_lords[seventh_sign]
    
    # House Lord Placements
    house_lord_map = {}
    for h_num in range(1, 13):
        h_sign = zodiac_signs[(lagna_idx + h_num - 1) % 12]
        h_lord = sign_lords[h_sign]
        lord_in_house = None
        for ph, plist in house_planets.items():
            if h_lord in plist:
                lord_in_house = ph
                break
        house_lord_map[h_num] = {"lord": h_lord, "placed_in": lord_in_house}
    
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
            p_lon = (zodiac_signs.index(planet_data[code]["sign"]) * 30) + planet_data[code]["deg"]
        
        ns, nd = get_navamsa_sign_and_deg(p_lon)
        d7s, d7d = get_d7_sign_and_deg(p_lon)
        d10s, d10d = get_d10_sign_and_deg(p_lon)
        
        planet_data[code]["navamsa_sign"] = ns
        planet_data[code]["navamsa_deg"] = nd
        planet_data[code]["d7_sign"] = d7s
        planet_data[code]["d7_deg"] = d7d
        planet_data[code]["d10_sign"] = d10s
        planet_data[code]["d10_deg"] = d10d
    
    # Vimshottari
    moon_lon = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    start_lord, balance_y, dashas_raw = calculate_vimshottari_dasha(moon_lon, birth_jd)
    dashas = [calculate_antardashas(md) for md in dashas_raw]
    
    # Current time
    now_utc = datetime.datetime.now(pytz.utc)
    current_jd = datetime_to_jd(now_utc)
    current_md, current_ad = find_current_dasha(birth_jd, current_jd, dashas)
    current_pd, pd_start_jd, pd_end_jd = get_current_pratyantar(
        birth_jd, current_jd, current_md, current_ad, dashas
    )
    
    # Aspects and Transits
    aspects = calculate_aspects(house_planets)
    transits = calculate_transits(moon_sign, current_jd)
    
    # Sade Sati
    sa_transit_sign = transits.get("Sa", {}).get("sign", None)
    sade_sati_status = get_sade_sati_status(moon_sign, sa_transit_sign) if sa_transit_sign else None
    
    # Build result
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
        "sade_sati": sade_sati_status,
        "vimshottari_pd": {
            "current_pd": current_pd,
            "pd_start_jd": pd_start_jd,
            "pd_end_jd": pd_end_jd,
        },
    }
    
    # Add yogas, timings, problems
    result["yogas"] = detect_yogas(result)
    result["timings"] = generate_timings(result, y, birth_jd)
    result["problems"] = detect_problems(result)
    result["final_analysis"] = generate_final_analysis(result)
    result["ashtakavarga"] = calculate_ashtakavarga(result)
    
    return result


# ────────────────────────────────────────────────
# Print Function
# ────────────────────────────────────────────────
def print_kundali(result, file=None):
    """Print Kundali report."""
    lines = []
    gender = result.get("gender", "Male")

    def write(s):
        lines.append(s)

    write("\n" + "═" * 95)
    write(" VEDIC KUNDALI – Whole Sign – Lahiri – D7 + D10 + Marriage Timing")
    write("═" * 95)
    write(f"Name         : {result.get('name', 'Not provided')}")
    write(f"Gender       : {gender}")
    write(f"Birth Date   : {result.get('birth_date', 'N/A')}")
    write(f"Birth Time   : {result.get('birth_time', 'N/A')}")
    write(f"Birth Place  : {result.get('birth_place', 'N/A')}")
    write(f"Lagna        : {result['lagna_sign']} {result['lagna_deg']}°")
    write(f"Moon (Rasi)  : {result['moon_sign']} – {result['moon_nakshatra']}")
    write(f"7th Lord     : {result['seventh_lord']}")
    
    # Panchanga
    pan = result.get("panchanga", {})
    if pan:
        write(f"Tithi        : {pan.get('tithi','?')}")
        write(f"Vara         : {pan.get('vara','?')}")
        write(f"Yoga         : {pan.get('yoga','?')}")
        write(f"Karana       : {pan.get('karana','?')}")
    write("")
    
    # Planets in Rasi
    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    write("Planets in Rasi (D1):")
    write("-" * 85)
    for pl in order:
        if pl in result["planets"]:
            d = result["planets"][pl]
            flags = ""
            if d.get("retro"):
                flags += " R"
            if d.get("combust"):
                flags += " C"
            dig_label = d["dignity"]
            if dig_label == "Debilitated" and d.get("neecha_bhanga", False):
                dig_label = "Debilitated (NB)"
            dig = f" ({dig_label})" if dig_label else ""
            write(f"{pl:>3}: {d['deg']:5.2f}° {d['sign']:11} {d['nakshatra']:18}{dig}{flags}")
    write("  (R = Retrograde, C = Combust)")
    
    # Divisional Charts
    for div, title, interp_fn in [
        ("navamsa", "Navamsa (D9 – Marriage/Spouse/Dharma)", interpret_navamsa),
        ("d7", "Saptamsa (D7 – Children/Progeny)", interpret_d7),
        ("d10", "Dasamsa (D10 – Career/Profession)", interpret_d10),
    ]:
        write(f"\n{title}:")
        write("-" * 85)
        for pl in order:
            if pl in result[div]:
                d = result[div][pl]
                write(f"{pl:>3}: {d['deg']:5.2f}° {d['sign']:11}")
        write(f"\nDetailed {title.split('(')[1].rstrip(')')} Analysis:")
        write("-" * 85)
        for line in interp_fn(result):
            write(line)
    
    # Houses
    write("\nHouses (Whole Sign):")
    write("-" * 85)
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    for h in range(1, 13):
        sidx = (lagna_idx + h - 1) % 12
        sign = zodiac_signs[sidx]
        pls = sorted(result["houses"][h])
        content = " ".join(pls) if pls else "—"
        write(f"House {h:2d} ({sign:11}): {content}")
    
    # Aspects
    write("\nAspects (Drishti) – Full Analysis:")
    write("-" * 85)
    write("Aspect strengths: 7th=100% | Jupiter 5th/9th=75% | Mars 8th=75% | Saturn 10th=75%")
    for line in interpret_aspects(result):
        write(line)
    
    # Ashtakavarga
    write("\nAshtakavarga (Sarvashtakavarga):")
    write("-" * 85)
    ashtak = result.get("ashtakavarga", {})
    if ashtak:
        sav_scores = ashtak.get('sav', [])
        interpretation = ashtak.get('interpretation', {})
        
        lagna_idx_av = zodiac_signs.index(result["lagna_sign"])
        
        write("\nSAV Points by House:")
        for h in range(1, 13):
            house_idx = (h - 1 + lagna_idx_av) % 12
            score = sav_scores[house_idx] if house_idx < len(sav_scores) else 0
            sign = zodiac_signs[(lagna_idx_av + h - 1) % 12]
            bar_length = min(30, score)
            bar = "█" * bar_length + "░" * (30 - bar_length)
            interp_data = interpretation.get(h, {})
            strength = interp_data.get('strength', 'Unknown')
            marker = " ★" if h == 7 else ""
            write(f"  H{h:02d} ({sign:11}): [{bar}] {score:2} - {strength}{marker}")
        
        h7_data = interpretation.get(7, {})
        write(f"\n  ★ 7th House SAV: {h7_data.get('score', 0)} points")
    
    # Functional Strength Index
    write("\nFunctional Classification Strength Index:")
    write("-" * 85)
    fq = FUNCTIONAL_QUALITY.get(result["lagna_sign"], {})
    if fq:
        ben_names = [short_to_full.get(p, p) for p in fq.get("ben", [])]
        mal_names = [short_to_full.get(p, p) for p in fq.get("mal", [])]
        yk = fq.get("yk")
        write(f"  Base Benefics    : {', '.join(ben_names) if ben_names else '—'}")
        write(f"  Base Malefics    : {', '.join(mal_names) if mal_names else '—'}")
        if yk:
            write(f"  Yogakaraka       : {short_to_full.get(yk, yk)}")
        write("")
        write("  FUNCTIONAL STRENGTH INDEX:")
        write("  " + "-" * 80)
        for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
            if pl in result["planets"]:
                fsi = calculate_functional_strength_index(result, pl)
                score = fsi["score"]
                bar = "█" * (score // 5) + "░" * (20 - score // 5)
                pl_full = short_to_full.get(pl, pl)
                write(f"  {pl_full:9} [{bar}] {score:3}/100 | {fsi['effective_class']}")
    
    # Vimshottari Dasha
    write("\nVimshottari Dasha:")
    write("-" * 85)
    vim = result["vimshottari"]
    write(f"Starting MD : {vim['starting_lord']} (balance {vim['balance_at_birth_years']} yrs)")
    if vim["current_md"]:
        pd_info = result.get("vimshottari_pd", {})
        current_pd = pd_info.get("current_pd")
        pd_end_jd = pd_info.get("pd_end_jd")
        if current_pd and pd_end_jd:
            pd_end_yr = int(result["birth_year"] + (pd_end_jd - result["birth_jd"]) / 365.25)
            write(f"Current (MD/AD/PD) : {vim['current_md']} / {vim['current_ad']} / {current_pd} (PD until ~{pd_end_yr})")
    
    # Marriage Timing
    spouse_term = "husband" if gender == "Female" else "wife"
    spouse_karaka = "Jupiter" if gender == "Female" else "Venus"
    write(f"\nMarriage Timing Insights – For {gender}:")
    write("-" * 85)
    write(f"  7th Lord ({spouse_term}): {short_to_full.get(result['seventh_lord'], result['seventh_lord'])}")
    write(f"  {spouse_karaka} ({spouse_term} karaka): {result['planets'].get('Ju' if gender == 'Female' else 'Ve', {}).get('sign', '?')}")
    
    vm = vim["current_md"]
    va = vim["current_ad"]
    spouse_karaka_short = "Ju" if gender == "Female" else "Ve"
    if vm in [spouse_karaka, spouse_karaka_short] or va in [spouse_karaka, spouse_karaka_short] or vm == result["seventh_lord"]:
        write("*** CURRENT DASHA IS HIGHLY FAVOURABLE FOR MARRIAGE ***")
    
    # Current Transits
    write("\nCurrent Gochara (from Moon):")
    write("-" * 85)
    for pl, t in sorted(result["transits"].items()):
        write(f"{pl:>3}: {t['sign']:11} (house {t['house_from_moon']:2d}) – {t['effect']}")
    
    sade = result.get("sade_sati")
    if sade:
        write(f"\n  ⚠ SATURN SPECIAL TRANSIT: {sade}")
    
    # Yogas
    write("\n🔥 YOGAS WITH STRENGTH")
    write("-" * 95)
    for yoga in result.get("yogas", []):
        write(f"• {yoga}")
    
    # Timings
    birth_year = result.get("birth_year", "N/A")
    write(f"\n📅 FRUCTIFICATION PERIODS (Full Life Timeline from {birth_year})")
    write("-" * 95)
    write("  [PAST] = Already occurred | [NOW] = Currently active | [FUTURE] = Upcoming")
    for event, periods in result.get("timings", {}).items():
        write(f"\n{event}:")
        if periods:
            for p in periods:
                write(p)
        else:
            write(" No major period found")
    
    # Problems/Doshas
    write("\n⚠️ PROBLEMS/DOSHAS IN KUNDALI")
    write("-" * 95)
    for prob in result.get("problems", []):
        write(f"• {prob['summary']}")
    write("\nDetailed Explanation of Doshas:")
    write("-" * 95)
    for prob in result.get("problems", []):
        if prob["detail"]:
            write(f"{prob['summary'].split(':')[0]}:")
            write(prob["detail"])
            write("")
    
    # Remedies
    write("\n🔧 TARGETED REMEDIES")
    write("-" * 95)
    has_remedy = False
    for prob in result.get("problems", []):
        rems = prob.get("remedies", [])
        if rems:
            has_remedy = True
            write(f"\n{prob['summary'].split(':')[0]}:")
            for r in rems:
                write(f"  • {r}")
    if not has_remedy:
        write("  No specific remedies needed.")
    
    # Personalized Remedies
    _lagna = result.get("lagna_sign", "")
    _seventh_lord = result.get("seventh_lord", "")
    _seventh_lord_full = short_to_full.get(_seventh_lord, _seventh_lord)
    write(f"\n🛡️ PERSONALIZED REMEDIES (For {_lagna} Lagna)")
    write("-" * 85)
    lagna_rem = LAGNA_REMEDIES.get(_lagna)
    if lagna_rem:
        deity, mantra, day = lagna_rem
        write(f"  Lagna Lord Worship: {deity}")
        write(f"  Primary Mantra: {mantra} (108× on {day}s)")
    seventh_rem = SEVENTH_LORD_REMEDIES.get(_seventh_lord)
    if seventh_rem:
        write(f"  For {_seventh_lord_full} (7th Lord): {seventh_rem}")
    
    write("\n" + result.get("final_analysis", ""))
    write("\n" + "═" * 95)
    
    output = "\n".join(lines) + "\n"
    print(output, end="")
    if file:
        file.write(output)


# ────────────────────────────────────────────────
# Entry Point
# ────────────────────────────────────────────────
def main():
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
        
        try:
            result = calculate_kundali(date_str, time_str, place, gender=gender)
            result["name"] = name
            filename = f"{name}_kundali_report.txt"
            with open(filename, "w", encoding="utf-8") as f:
                print_kundali(result, file=f)
            print(f"\nReport saved as '{filename}'")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Tips: Use place='Mumbai, Maharashtra, India'")
            print(" Make sure Swiss Ephemeris .se1 files are in the same folder")
            print("Please re-enter the details.\n")
    
    swe.close()


if __name__ == "__main__":
    main()
