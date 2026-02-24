import swisseph as swe
import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# ────────────────────────────────────────────────
# Swiss Ephemeris Setup
# ────────────────────────────────────────────────
swe.set_ephe_path(".")  # Put seas_18.se1, sepl_18.se1, semo_18.se1 etc. in this folder
swe.set_sid_mode(swe.SIDM_LAHIRI)

zodiac_signs = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

nakshatras = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

dasha_lords = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

dasha_periods = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

nakshatra_lord_index = [0, 1, 2, 3, 4, 5, 6, 7, 8] * 3

planets = {
    "Su": swe.SUN,
    "Mo": swe.MOON,
    "Ma": swe.MARS,
    "Me": swe.MERCURY,
    "Ju": swe.JUPITER,
    "Ve": swe.VENUS,
    "Sa": swe.SATURN,
    "Ra": swe.MEAN_NODE,
}

dignity_table = {
    "Su": {"own": "Leo", "exalt": "Aries", "deb": "Libra"},
    "Mo": {"own": "Cancer", "exalt": "Taurus", "deb": "Scorpio"},
    "Ma": {"own": ["Aries", "Scorpio"], "exalt": "Capricorn", "deb": "Cancer"},
    "Me": {"own": ["Gemini", "Virgo"], "exalt": "Virgo", "deb": "Pisces"},
    "Ju": {"own": ["Sagittarius", "Pisces"], "exalt": "Cancer", "deb": "Capricorn"},
    "Ve": {"own": ["Taurus", "Libra"], "exalt": "Pisces", "deb": "Virgo"},
    "Sa": {"own": ["Capricorn", "Aquarius"], "exalt": "Libra", "deb": "Aries"},
    "Ra": {"exalt": "Taurus/Gemini", "deb": "Scorpio/Sagittarius"},
    "Ke": {"exalt": "Scorpio/Sagittarius", "deb": "Taurus/Gemini"},
}

gochara_effects = {
    "Su": {
        1: "Good for health",
        2: "Expenses",
        3: "Short travels",
        4: "Home happiness",
        5: "Children luck",
        6: "Enemies/defeat",
        7: "Marriage/partners",
        8: "Obstacles",
        9: "Luck",
        10: "Career",
        11: "Gains",
        12: "Losses",
    },
    "Mo": {
        1: "Peace",
        2: "Family issues",
        3: "Communication",
        4: "Mother/home",
        5: "Creativity",
        6: "Health issues",
        7: "Relations",
        8: "Secrets",
        9: "Travel",
        10: "Status",
        11: "Friends",
        12: "Isolation",
    },
    "Ma": {
        1: "Energy",
        2: "Arguments",
        3: "Courage",
        4: "Property",
        5: "Speculation",
        6: "Victory",
        7: "Conflicts",
        8: "Accidents",
        9: "Father",
        10: "Authority",
        11: "Ambition",
        12: "Hidden enemies",
    },
    "Me": {
        1: "Intellect",
        2: "Learning",
        3: "Siblings",
        4: "Education",
        5: "Wit",
        6: "Debts",
        7: "Trade",
        8: "Research",
        9: "Philosophy",
        10: "Communication",
        11: "Networks",
        12: "Imagination",
    },
    "Ju": {
        1: "Growth",
        2: "Wealth",
        3: "Knowledge",
        4: "Comfort",
        5: "Wisdom",
        6: "Service",
        7: "Harmony",
        8: "Occult",
        9: "Guru",
        10: "Success",
        11: "Prosperity",
        12: "Charity",
    },
    "Ve": {
        1: "Charm",
        2: "Luxury",
        3: "Arts",
        4: "Vehicles",
        5: "Romance",
        6: "Pleasures",
        7: "Love",
        8: "Intimacy",
        9: "Beauty",
        10: "Fame",
        11: "Income",
        12: "Expenses on fun",
    },
    "Sa": {
        1: "Discipline",
        2: "Stability",
        3: "Hard work",
        4: "Roots",
        5: "Karma",
        6: "Delays",
        7: "Commitments",
        8: "Transformation",
        9: "Dharma",
        10: "Career hurdles",
        11: "Long-term gains",
        12: "Isolation",
    },
    "Ra": {
        1: "Ambition",
        2: "Unusual gains",
        3: "Adventures",
        4: "Foreign home",
        5: "Innovation",
        6: "Obsession",
        7: "Unconventional partners",
        8: "Sudden changes",
        9: "Spiritual quests",
        10: "Power struggles",
        11: "Mass gains",
        12: "Karmic losses",
    },
    "Ke": {
        1: "Detachment",
        2: "Mysticism",
        3: "Intuition",
        4: "Spiritual home",
        5: "Past karma",
        6: "Healing",
        7: "Karmic ties",
        8: "Release",
        9: "Moksha",
        10: "Hidden talents",
        11: "Sudden losses",
        12: "Enlightenment",
    },
}

sign_lords = {
    "Aries": "Ma",
    "Taurus": "Ve",
    "Gemini": "Me",
    "Cancer": "Mo",
    "Leo": "Su",
    "Virgo": "Me",
    "Libra": "Ve",
    "Scorpio": "Ma",
    "Sagittarius": "Ju",
    "Capricorn": "Sa",
    "Aquarius": "Sa",
    "Pisces": "Ju",
}


# ────────────────────────────────────────────────
# Helper Functions
# ────────────────────────────────────────────────
def get_sign(deg):
    return zodiac_signs[int(deg / 30) % 12]


def get_nakshatra(deg):
    nak_index = int(deg / (360 / 27)) % 27
    return nakshatras[nak_index]


def get_nakshatra_progress(deg):
    nak_span = 360 / 27
    nak_start = int(deg / nak_span) * nak_span
    progress = (deg - nak_start) / nak_span
    return progress


def get_dignity(planet, sign):
    if planet not in dignity_table:
        return ""
    d = dignity_table[planet]
    own_signs = d.get("own", [])
    if isinstance(own_signs, str):
        own_signs = [own_signs]
    if sign in own_signs:
        return "Own"
    exalt_str = d.get("exalt", "")
    if exalt_str:
        exalt_signs = [s.strip() for s in exalt_str.split("/") if s.strip()]
        if sign in exalt_signs:
            return "Exalt"
    deb_str = d.get("deb", "")
    if deb_str:
        deb_signs = [s.strip() for s in deb_str.split("/") if s.strip()]
        if sign in deb_signs:
            return "Debilitated"
    return ""


def get_lat_lon(place):
    geo = Nominatim(user_agent="vedic_kundali_cli")
    loc = geo.geocode(place, timeout=15)
    if not loc:
        raise ValueError(
            f"Location not found: {place}. Try 'Mumbai, Maharashtra, India'"
        )
    return loc.latitude, loc.longitude


def is_retrograde(speed):
    return speed < 0


def get_house_from_sign(asc_sign_idx, planet_sign_idx):
    return ((planet_sign_idx - asc_sign_idx) % 12) + 1


def datetime_to_jd(dt):
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)


# ────────────────────────────────────────────────
# Divisional Charts (Traditional Parashari)
# ────────────────────────────────────────────────
def get_navamsa_sign_and_deg(full_lon):
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    nav_size = 30.0 / 9
    navamsa_in_rasi = int(deg_in_rasi / nav_size)
    start_nav_idx = [0, 9, 6, 3][rasi_idx % 4]  # Fire/Earth/Air/Water
    nav_sign_idx = (start_nav_idx + navamsa_in_rasi) % 12
    remainder = deg_in_rasi % nav_size
    deg_in_nav = remainder * 9
    return zodiac_signs[nav_sign_idx], round(deg_in_nav, 2)


def get_d7_sign_and_deg(full_lon):
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    sapt_size = 30.0 / 7
    sapt_idx = int(deg_in_rasi / sapt_size)
    if rasi_idx % 2 == 0:  # Odd signs (Aries, Gemini...)
        start_idx = rasi_idx
    else:
        start_idx = (rasi_idx + 6) % 12
    new_idx = (start_idx + sapt_idx) % 12
    frac = (deg_in_rasi % sapt_size) / sapt_size
    deg_in_d7 = frac * 30
    return zodiac_signs[new_idx], round(deg_in_d7, 2)


def get_d10_sign_and_deg(full_lon):
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    dasa_size = 3.0
    dasa_idx = int(deg_in_rasi / dasa_size)
    if rasi_idx % 2 == 0:  # Odd signs
        start_idx = rasi_idx
    else:
        start_idx = (rasi_idx + 8) % 12
    new_idx = (start_idx + dasa_idx) % 12
    frac = (deg_in_rasi % dasa_size) / dasa_size
    deg_in_d10 = frac * 30
    return zodiac_signs[new_idx], round(deg_in_d10, 2)


# ────────────────────────────────────────────────
# Vimshottari Dasha
# ────────────────────────────────────────────────
def calculate_vimshottari_dasha(moon_deg, birth_jd):
    nak_span = 360 / 27
    nak_index = int(moon_deg / nak_span) % 27
    lord_idx = nakshatra_lord_index[nak_index]
    start_lord = dasha_lords[lord_idx]
    progress = get_nakshatra_progress(moon_deg)
    full_period = dasha_periods[start_lord]
    balance_years = (1 - progress) * full_period

    dashas = []
    current_jd = birth_jd
    current_lord_idx = lord_idx

    # Balance
    balance_days = balance_years * 365.25
    end_jd = current_jd + balance_days
    dashas.append(
        {
            "lord": start_lord,
            "start_jd": current_jd,
            "end_jd": end_jd,
            "years": round(balance_years, 3),
            "antardashas": [],
        }
    )
    current_jd = end_jd

    total_years = balance_years
    while total_years < 130:
        current_lord_idx = (current_lord_idx + 1) % 9
        next_lord = dasha_lords[current_lord_idx]
        period = dasha_periods[next_lord]
        days = period * 365.25
        end_jd = current_jd + days
        dashas.append(
            {
                "lord": next_lord,
                "start_jd": current_jd,
                "end_jd": end_jd,
                "years": period,
                "antardashas": [],
            }
        )
        current_jd = end_jd
        total_years += period
    return start_lord, balance_years, dashas


def calculate_antardashas(mdadasha):
    md_lord = mdadasha["lord"]
    md_days = mdadasha["end_jd"] - mdadasha["start_jd"]
    md_years = md_days / 365.25
    antardashas = []
    current_ad_jd = mdadasha["start_jd"]
    md_idx = dasha_lords.index(md_lord)
    for i in range(9):
        ad_idx = (md_idx + i) % 9
        ad_lord = dasha_lords[ad_idx]
        ad_full_years = dasha_periods[ad_lord]
        ad_proportion = ad_full_years / 120.0
        ad_years_in_md = md_years * ad_proportion
        ad_days = ad_years_in_md * 365.25
        ad_end_jd = current_ad_jd + ad_days
        antardashas.append(
            {
                "lord": ad_lord,
                "start_jd": current_ad_jd,
                "end_jd": ad_end_jd,
                "years": round(ad_years_in_md, 3),
            }
        )
        current_ad_jd = ad_end_jd
    mdadasha["antardashas"] = antardashas
    return mdadasha


def find_current_dasha(birth_jd, current_jd, dashas):
    years_since = (current_jd - birth_jd) / 365.25
    for md in dashas:
        md_start_y = (md["start_jd"] - birth_jd) / 365.25
        md_end_y = (md["end_jd"] - birth_jd) / 365.25
        if md_start_y <= years_since < md_end_y:
            for ad in md["antardashas"]:
                ad_start_y = (ad["start_jd"] - birth_jd) / 365.25
                ad_end_y = (ad["end_jd"] - birth_jd) / 365.25
                if ad_start_y <= years_since < ad_end_y:
                    return md["lord"], ad["lord"]
    return None, None


# ────────────────────────────────────────────────
# Aspects & Transits
# ────────────────────────────────────────────────
def calculate_aspects(houses):
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
# Main Kundali Calculation
# ────────────────────────────────────────────────
def calculate_kundali(birth_date_str, birth_time_str, place):
    y, m, d = map(int, birth_date_str.split("-"))
    hh, mm = map(int, birth_time_str.split(":"))

    lat, lon = get_lat_lon(place)
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

    for code, pid in planets.items():
        pos_speed = swe.calc_ut(birth_jd, pid, swe.FLG_SIDEREAL)[0]
        lon = pos_speed[0]
        speed = pos_speed[3]
        sign = get_sign(lon)
        deg_in_sign = round(lon % 30, 2)
        nak = get_nakshatra(lon)
        dignity = get_dignity(code, sign)
        retro = is_retrograde(speed)

        planet_data[code] = {
            "deg": deg_in_sign,
            "sign": sign,
            "nakshatra": nak,
            "dignity": dignity,
            "retro": retro,
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

    # Ketu + Ra lon for later
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
        "navamsa_sign": None,
        "navamsa_deg": None,
        "d7_sign": None,
        "d7_deg": None,
        "d10_sign": None,
        "d10_deg": None,
    }
    ke_idx = zodiac_signs.index(ke_sign)
    ke_house = get_house_from_sign(lagna_idx, ke_idx)
    house_planets[ke_house].append("Ke")

    house_planets[1].append("Asc")  # Ascendant in 1st house

    # 7th Lord
    seventh_idx = (lagna_idx + 6) % 12
    seventh_sign = zodiac_signs[seventh_idx]
    seventh_lord = sign_lords[seventh_sign]

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

    # Current time (UTC)
    now_utc = datetime.datetime.now(pytz.utc)
    current_jd = datetime_to_jd(now_utc)
    current_md, current_ad = find_current_dasha(birth_jd, current_jd, dashas)

    aspects = calculate_aspects(house_planets)
    transits = calculate_transits(moon_sign, current_jd)

    return {
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
    }


# ────────────────────────────────────────────────
# Print Function
# ────────────────────────────────────────────────
def print_kundali(result):
    print("\n" + "═" * 95)
    print("          VEDIC KUNDALI – Whole Sign – Lahiri – D7 + D10 + Marriage Timing")
    print("═" * 95)

    print(f"Lagna          : {result['lagna_sign']} {result['lagna_deg']}°")
    print(f"Moon (Rasi)    : {result['moon_sign']} – {result['moon_nakshatra']}")
    print(f"7th Lord       : {result['seventh_lord']}\n")

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    print("Planets in Rasi (D1):")
    print("-" * 85)
    for pl in order:
        if pl in result["planets"]:
            d = result["planets"][pl]
            r = " R" if d["retro"] else ""
            dig = f" ({d['dignity']})" if d["dignity"] else ""
            print(
                f"{pl:>3}: {d['deg']:5.2f}° {d['sign']:11} {d['nakshatra']:18}{dig}{r}"
            )

    for div, title in [
        ("navamsa", "Navamsa (D9 – Marriage/Spouse)"),
        ("d7", "Saptamsa (D7 – Children/Progeny)"),
        ("d10", "Dasamsa (D10 – Career/Profession)"),
    ]:
        print(f"\n{title}:")
        print("-" * 85)
        for pl in order:
            if pl in result[div]:
                d = result[div][pl]
                print(f"{pl:>3}: {d['deg']:5.2f}° {d['sign']:11}")

    print("\nHouses (Whole Sign):")
    print("-" * 85)
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    for h in range(1, 13):
        sidx = (lagna_idx + h - 1) % 12
        sign = zodiac_signs[sidx]
        pls = sorted(result["houses"][h])
        content = " ".join(pls) if pls else "—"
        print(f"House {h:2d} ({sign:11}): {content}")

    print("\nAspects (Drishti):")
    print("-" * 85)
    for h in range(1, 13):
        if result["aspects"][h]:
            print(f"House {h:2d}: {', '.join(result['aspects'][h])}")

    print("\nVimshottari Dasha:")
    print("-" * 85)
    vim = result["vimshottari"]
    print(
        f"Starting MD     : {vim['starting_lord']} (balance {vim['balance_at_birth_years']} yrs)"
    )
    if vim["current_md"]:
        print(f"Current         : {vim['current_md']} → {vim['current_ad']}")

    print("\nMarriage Timing Insights (Basic Parashari):")
    print("-" * 85)
    print(f"7th Lord        : {result['seventh_lord']}")
    print("Key Triggers    : Venus MD/AD  OR  7th-lord MD/AD")
    print(
        "Also favourable : Jupiter transit over 7th/2nd from Moon, strong D9 Venus/7th"
    )
    vm = vim["current_md"]
    va = vim["current_ad"]
    if (
        vm in ["Venus", "Ve"]
        or va in ["Venus", "Ve"]
        or vm == result["seventh_lord"]
        or va == result["seventh_lord"]
    ):
        print("*** CURRENT DASHA IS HIGHLY FAVOURABLE FOR MARRIAGE ***")
    else:
        print(
            "Next favourable periods: Venus or 7th-lord Mahadasha/Antardasha (check full list)"
        )

    print("\nCurrent Gochara (from Moon):")
    print("-" * 85)
    for pl, t in sorted(result["transits"].items()):
        print(
            f"{pl:>3}: {t['sign']:11} (house {t['house_from_moon']:2d}) – {t['effect']}"
        )

    print("\n" + "═" * 95)


# ────────────────────────────────────────────────
# Entry Point
# ────────────────────────────────────────────────
def main():
    print("Vedic Kundali Generator – Full Version with D7, D10 & Marriage Timing")
    print("─────────────────────────────────────────────────────────────────────\n")

    date_str = input("Birth Date (YYYY-MM-DD)     : ").strip()
    time_str = input("Birth Time (HH:MM 24h)      : ").strip()
    place = input("Birth Place (City, Country) : ").strip()

    try:
        result = calculate_kundali(date_str, time_str, place)
        print_kundali(result)
    except Exception as e:
        print(f"\nError: {e}")
        print("Tips: Use place='Mumbai, Maharashtra, India'")
        print("      Make sure Swiss Ephemeris .se1 files are in the same folder")


if __name__ == "__main__":
    main()
