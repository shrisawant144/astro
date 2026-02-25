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

short_to_full = {
    "Su": "Sun",
    "Mo": "Moon",
    "Ma": "Mars",
    "Me": "Mercury",
    "Ju": "Jupiter",
    "Ve": "Venus",
    "Sa": "Saturn",
    "Ra": "Rahu",
    "Ke": "Ketu",
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
# Yoga Strength Calculation (1-10)
# ────────────────────────────────────────────────
def get_yoga_strength(pl_list, result):
    """Calculate yoga strength from 1-10 based on dignity, house, retro, etc."""
    score = 5  # baseline
    for pl in pl_list:
        if pl not in result["planets"]:
            continue
        d = result["planets"][pl]

        # Dignity bonus/penalty
        if d["dignity"] == "Exalt":
            score += 3
        elif d["dignity"] == "Own":
            score += 2
        elif d["dignity"] == "Debilitated":
            score -= 3

        # Direct motion bonus
        if not d["retro"]:
            score += 1

        # House placement bonus
        planet_house = None
        for h, pls in result["houses"].items():
            if pl in pls:
                planet_house = h
                break

        if planet_house:
            if planet_house in [1, 4, 7, 10]:  # Kendras
                score += 2
            elif planet_house in [5, 9]:  # Trikonas
                score += 1

    return max(1, min(10, score))


# ────────────────────────────────────────────────
# Detect Problems/Doshas
# ────────────────────────────────────────────────
def detect_problems(result):
    """Detect major problems/doshas in the Kundali"""
    problems = []
    p = result["planets"]
    h = result["houses"]
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)

    # Create planet to house mapping (excluding Asc)
    planet_house = {}
    for house, pls in h.items():
        for pl in pls:
            if pl != "Asc":
                planet_house[pl] = house

    # 1. Mangal Dosha (Mars in 1,2,4,7,8,12 from Lagna)
    if "Ma" in planet_house and planet_house["Ma"] in [1, 2, 4, 7, 8, 12]:
        house_num = planet_house["Ma"]
        problems.append(
            f"Mangal Dosha (Mars in {house_num}H): Potential delays/discord in marriage"
        )

    # 2. Kemdrum Yoga (Moon with no planets in 2nd/12th from it, and alone in its house)
    if "Mo" in planet_house:
        moon_house = planet_house["Mo"]
        moon_house_planets = [pl for pl in h[moon_house] if pl != "Mo"]
        prev_house = ((moon_house - 2) % 12) + 1
        next_house = ((moon_house) % 12) + 1
        if (
            len(moon_house_planets) == 0
            and len(h[prev_house]) == 0
            and len(h[next_house]) == 0
        ):
            problems.append(
                "Kemdrum Yoga: Moon isolated – Emotional instability, financial fluctuations"
            )

    # 3. Kaal Sarp Yoga (Basic: All planets between Rahu and Ketu in one arc)
    if "Ra" in planet_house and "Ke" in planet_house:
        ra_house = planet_house["Ra"]
        ke_house = planet_house["Ke"]
        # Normalize houses: assume houses are 1-12
        # Check if all other planets are between ra_house and ke_house (clockwise or anticlockwise)
        all_planets_between = True
        direction1 = (ke_house - ra_house + 12) % 12  # From Ra to Ke clockwise
        direction2 = (ra_house - ke_house + 12) % 12  # From Ke to Ra clockwise
        if (
            direction1 <= 6 or direction2 <= 6
        ):  # Only if span is half or less (simplified)
            for pl_house in planet_house.values():
                if pl_house not in [ra_house, ke_house]:
                    pos_from_ra = (pl_house - ra_house + 12) % 12
                    if not (0 < pos_from_ra < direction1):
                        all_planets_between = False
                        break
            if all_planets_between:
                problems.append(
                    "Kaal Sarp Yoga: All planets hemmed between Rahu-Ketu – Life obstacles, but potential for sudden rise"
                )

    # 4. Debilitated Planets
    deb_planets = [pl for pl, data in p.items() if data["dignity"] == "Debilitated"]
    if deb_planets:
        full_names = [short_to_full.get(pl, pl) for pl in deb_planets]
        problems.append(
            f"Debilitated Planets ({', '.join(full_names)}): Weakened vitality/effects in respective areas"
        )

    # 5. Pitru Dosha (Sun afflicted by Saturn/Rahu, or Sun in 12th)
    sun_house = planet_house.get("Su", None)
    afflictions = []
    if "Sa" in planet_house and abs(planet_house["Sa"] - sun_house) in [
        0,
        1,
        6,
        7,
    ]:  # Conjunction or opposition
        afflictions.append("Saturn")
    if "Ra" in planet_house and abs(planet_house["Ra"] - sun_house) in [0, 1, 6, 7]:
        afflictions.append("Rahu")
    if sun_house == 12:
        afflictions.append("in 12H")
    if afflictions:
        problems.append(
            f"Pitru Dosha (Sun afflicted by {', '.join(afflictions)}): Ancestral issues, father-related challenges"
        )

    # 6. Graha Malika Yoga (Planets in consecutive houses – can be problematic if malefic heavy)
    # Simplified: Check if 5+ planets in 5 consecutive houses
    consecutive_count = 1
    max_consec = 1
    for i in range(1, 13):
        if len(h[i]) > 0:
            consecutive_count += 1
            max_consec = max(max_consec, consecutive_count)
        else:
            consecutive_count = 0
    if max_consec >= 5:
        problems.append(
            "Graha Malika (5+ planets consecutive): Intense life phases, potential imbalances"
        )

    return (
        problems
        if problems
        else ["No major doshas/problems detected – Generally favorable chart"]
    )


# ────────────────────────────────────────────────
# Accurate Fructification Timings (2026-2046)
# ────────────────────────────────────────────────
def generate_timings(result, birth_year, birth_jd):
    """Generate accurate timing predictions for next 20 years"""
    dashas = result["vimshottari"]["mahadasas"]
    current_year = 2026

    def lord_of(house_no):
        lagna_idx = zodiac_signs.index(result["lagna_sign"])
        sign = zodiac_signs[(lagna_idx + house_no - 1) % 12]
        return sign_lords[sign]

    # Event → favorable lords (expanded list)
    seventh_lord = result["seventh_lord"]
    events = {
        "Marriage": [
            short_to_full["Ve"],
            short_to_full[seventh_lord],
            short_to_full["Ju"],
            short_to_full["Mo"],
        ],
        "Career Rise / Fame": [
            short_to_full["Sa"],
            short_to_full[lord_of(10)],
            short_to_full["Ju"],
            short_to_full["Su"],
            short_to_full["Ma"],
        ],
        "Children / Progeny": [
            short_to_full["Ju"],
            short_to_full[lord_of(5)],
            short_to_full["Mo"],
            short_to_full["Ve"],
        ],
        "Major Wealth / Property": [
            short_to_full["Ju"],
            short_to_full["Ve"],
            short_to_full[lord_of(2)],
            short_to_full[lord_of(11)],
            short_to_full["Me"],
        ],
    }

    output = {}
    for event, fav_lords in events.items():
        periods = []

        for md in dashas:
            md_lord = md["lord"]
            md_start_age = (md["start_jd"] - birth_jd) / 365.25
            md_start_y = int(birth_year + md_start_age)
            md_end_y = int(birth_year + (md["end_jd"] - birth_jd) / 365.25)

            # Skip if MD is completely outside our window
            if md_end_y < current_year or md_start_y > current_year + 20:
                continue

            # Include if MD lord is favorable
            if md_lord in fav_lords:
                periods.append(f"• {md_lord} Mahadasha ({md_start_y}-{md_end_y})")

            # Check antardashas within the 2026-2046 window
            for ad in md.get("antardashas", []):
                if ad["lord"] in fav_lords:
                    ad_start_age = (ad["start_jd"] - birth_jd) / 365.25
                    ad_end_age = (ad["end_jd"] - birth_jd) / 365.25
                    ad_start_y = int(birth_year + ad_start_age)
                    ad_end_y = int(birth_year + ad_end_age)

                    # Include if AD starts or overlaps within 2026-2046
                    if ad_start_y <= current_year + 20 and ad_end_y >= current_year:
                        periods.append(
                            f"  └─ {md_lord}/{ad['lord']} Antardasha ({ad_start_y}-{ad_end_y})"
                        )

        output[event] = periods[:10] if periods else []

    return output


# ────────────────────────────────────────────────
# Detect Yogas with Strength
# ────────────────────────────────────────────────
def detect_yogas(result):
    """Detect major yogas and calculate their strength (1-10)"""
    yogas = []
    p = result["planets"]
    h = result["houses"]
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)

    # Create planet to house mapping
    planet_house = {}
    for house, pls in h.items():
        for pl in pls:
            if pl != "Asc":
                planet_house[pl] = house

    def lord_of(house_no):
        sign_idx = (lagna_idx + house_no - 1) % 12
        return sign_lords[zodiac_signs[sign_idx]]

    # 1. Gajakesari Yoga (Jupiter-Moon)
    if "Ju" in planet_house and "Mo" in planet_house:
        stren = get_yoga_strength(["Ju", "Mo"], result)
        yogas.append(f"Gajakesari Yoga (Strength {stren}/10) → Fame, wisdom, wealth")

    # 2. Raja Yogas (Kendra-Trikona lords)
    for k in [1, 4, 7, 10]:
        for t in [1, 5, 9]:
            kl = lord_of(k)
            tl = lord_of(t)
            if kl in planet_house and tl in planet_house:
                if kl == tl or abs(planet_house[kl] - planet_house[tl]) % 12 in (0, 6):
                    s = get_yoga_strength([kl, tl], result)
                    yogas.append(
                        f"Raja Yoga ({kl}-{tl}) (Strength {s}/10) → Power & status"
                    )

    # 3. Strong Venus Yoga
    if "Ve" in planet_house:
        ve_h = planet_house["Ve"]
        if ve_h in [1, 4, 7, 10] or p["Ve"]["dignity"] in ["Own", "Exalt"]:
            s = get_yoga_strength(["Ve"], result)
            yogas.append(
                f"Strong Venus Yoga (Strength {s}/10) → Beautiful spouse, luxury"
            )

    # 4. Strong 7th Lord
    seventh_lord = result["seventh_lord"]
    if seventh_lord in planet_house and planet_house[seventh_lord] in [
        1,
        4,
        7,
        10,
        5,
        9,
    ]:
        s = get_yoga_strength([seventh_lord], result)
        yogas.append(
            f"Strong 7th Lord ({seventh_lord}) (Strength {s}/10) → Stable marriage"
        )

    # 5. Jupiter in 5th house
    if "Ju" in planet_house and planet_house["Ju"] == 5:
        s = get_yoga_strength(["Ju"], result)
        yogas.append(
            f"Jupiter in 5th (Strength {s}/10) → Excellent progeny, intelligent children"
        )

    # 6. Strong 10th Lord
    tenth_lord = lord_of(10)
    if tenth_lord in planet_house and planet_house[tenth_lord] in [1, 4, 7, 10]:
        s = get_yoga_strength([tenth_lord], result)
        yogas.append(
            f"Strong 10th Lord ({tenth_lord}) (Strength {s}/10) → High career success"
        )

    # 7. Dhana Yoga (2nd + 11th lords)
    d2 = lord_of(2)
    d11 = lord_of(11)
    if d2 in planet_house and d11 in planet_house:
        s = get_yoga_strength([d2, d11], result)
        yogas.append(f"Dhana Yoga (2nd+11th) (Strength {s}/10) → Wealth through effort")

    # 8. Pancha Mahapurusha Yogas
    pmp = {
        "Ruchaka (Mars)": ("Ma", ["Aries", "Scorpio", "Capricorn"]),
        "Bhadra (Mercury)": ("Me", ["Gemini", "Virgo"]),
        "Hamsa (Jupiter)": ("Ju", ["Cancer", "Sagittarius", "Pisces"]),
        "Malavya (Venus)": ("Ve", ["Taurus", "Libra", "Pisces"]),
        "Sasa (Saturn)": ("Sa", ["Libra", "Capricorn", "Aquarius"]),
    }
    for name, (pl, signs) in pmp.items():
        if pl in p and p[pl]["sign"] in signs and planet_house.get(pl) in [1, 4, 7, 10]:
            s = get_yoga_strength([pl], result)
            yogas.append(f"{name} Yoga (Strength {s}/10) → Great personality & success")

    return yogas if yogas else ["No major classical yogas formed"]


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

    result = {
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
        "birth_jd": birth_jd,
    }

    # Add yogas, timings, and problems
    result["yogas"] = detect_yogas(result)
    result["timings"] = generate_timings(result, y, birth_jd)
    result["problems"] = detect_problems(result)

    return result


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

    print("\n🔥 YOGAS WITH STRENGTH (1-10) & ACCURATE TIMINGS (2026–2046)")
    print("-" * 95)
    for y in result.get("yogas", []):
        print(f"• {y}")

    print("\n📅 POSSIBLE FRUCTIFICATION PERIODS (Next 20 years)")
    print("-" * 95)
    for event, periods in result.get("timings", {}).items():
        print(f"\n{event}:")
        if periods:
            for p in periods:
                print(p)
        else:
            print("   No major period in next 20 years")

    print("\n⚠️  PROBLEMS/DOSHAS IN KUNDALI")
    print("-" * 95)
    for prob in result.get("problems", []):
        print(f"• {prob}")

    print("\nNote: Highest probability when dasha + transit + gochara align.")
    print(
        "For 1999-04-14 Mumbai chart (age 27 in 2026): timings calculated from birth JD."
    )
    print("Doshas indicate challenges; remedies like mantras/gemstones can mitigate.")

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
