"""
Advanced spouse predictor using 25+ Vedic techniques.
Requires result dict from calculate_kundali().
"""

from marriage_date_prediction import find_marriage_date, ASTROPY_AVAILABLE

from datetime import datetime
from typing import Dict, List, Optional, Any

from constants import (
    ZODIAC_SIGNS,
    SIGN_LORDS,
    SHORT_TO_FULL,
    FULL_TO_SHORT,
    PLANET_SPOUSE_TRAITS,
    SIGN_APPEARANCE,
    MEETING_CIRCUMSTANCES,
    PROFESSION_BY_HOUSE,
    FUNCTIONAL_LABELS,
)
from utils import (
    get_dignity,
    get_navamsa_sign,
    get_sign,
    has_aspect,
    get_house_from_sign,
    get_seventh_sign,
)
from nakshatra import get_nakshatra_lord, get_nakshatra_deity, get_nakshatra_meaning

# Sign offsets for longitude calculation (Aries=0°)
SIGN_OFFSETS = {
    "Aries": 0,
    "Taurus": 30,
    "Gemini": 60,
    "Cancer": 90,
    "Leo": 120,
    "Virgo": 150,
    "Libra": 180,
    "Scorpio": 210,
    "Sagittarius": 240,
    "Capricorn": 270,
    "Aquarius": 300,
    "Pisces": 330,
}


def extract_marriage_data(result):
    """
    Extract marriage date prediction data from main.py result dict.
    Returns format compatible with find_marriage_date().
    """
    from datetime import datetime

    # Lagna longitude
    lagna_sign = result.get("lagna_sign", "Aries")
    lagna_deg = result.get("lagna_deg", 0.0)
    lagna_offset = SIGN_OFFSETS.get(lagna_sign, 0)
    lagna_lon = lagna_offset + lagna_deg

    # Planets: already have full_lon! Map short → full names
    SHORT_TO_FULL = {
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
    planets_long = {}
    for short, data in result["planets"].items():
        if "full_lon" in data:
            full_name = SHORT_TO_FULL.get(short, short)
            planets_long[full_name] = data["full_lon"]

    # 7th lord (already short code like "Mo")
    lord7 = result.get("seventh_lord")

    # Birth date
    birth_date = result.get("birth_datetime") or datetime.now()

    # Parse dasha periods from timings["Marriage"]
    dasha_periods = []
    marriage_lines = result.get("timings", {}).get("Marriage", [])
    import re

    for line in marriage_lines:
        m = re.search(r"─\s*(\w+)/(\w+)\s*\((\d{4})-(\d{4})\)", line)
        if m:
            start, end = int(m.group(3)), int(m.group(4))
            md, ad = m.group(1), m.group(2)
            dasha_periods.append((start, end, md, ad))

    return {
        "lagna": lagna_lon,
        "planets": planets_long,
        "lord7": lord7,
        "birth_date": birth_date,
        "dasha_periods": dasha_periods,
    }


# ============================================================================
# MARRIAGE DATE PREDICTION FUNCTIONS (copied/adapted from outer)
# ============================================================================


def get_sign(lon_deg):
    """Convert absolute longitude to sign index: 0=Aries ... 11=Pisces"""
    return int(lon_deg // 30) % 12


def get_seventh_sign(lagna_lon):
    """Get 7th house sign index from Lagna longitude (equal house system)."""
    return (get_sign(lagna_lon) + 6) % 12


def signs_have_nadi_relation(s1, s2):
    """
    Nadi-inspired sign relation: same (0), 2/12 (1), 3/11 (2), opposition (6).
    """
    diff = abs(s1 - s2) % 12
    min_diff = min(diff, 12 - diff)
    return min_diff in (0, 1, 2, 6)


def get_progressed_jupiter_sign(natal_jup_lon, age_floor):
    """Jupiter progression: natal degree + age * 30° (1 sign/year)."""
    progressed_lon = (natal_jup_lon + age_floor * 30) % 360
    return get_sign(progressed_lon)


def check_nadi_promise(planets, gender="male"):
    """Nadi marriage promise check."""
    sig_key = "Venus" if gender.lower() == "male" else "Mars"
    sig_lon = planets.get(sig_key)
    jup_lon = planets.get("Jupiter")
    sat_lon = planets.get("Saturn")

    if not all([sig_lon, jup_lon, sat_lon]):
        return "Insufficient data"

    sig_sign = get_sign(sig_lon)
    jup_sign = get_sign(jup_lon)
    sat_sign = get_sign(sat_lon)

    jup_rel = signs_have_nadi_relation(jup_sign, sig_sign)
    sat_rel = signs_have_nadi_relation(sat_sign, sig_sign)

    sign_names = [
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

    if jup_rel and sat_rel:
        return f"★★★ 100% PROMISE (Ju+Sa relate to {sig_key})"
    elif jup_rel:
        return f"★★ TIMELY (Jupiter relates to {sig_key})"
    elif sat_rel:
        return f"★ DELAYED BUT ASSURED (Saturn relates to {sig_key})"
    return f"⚠️ WEAK PROMISE (No strong relation to {sig_key})"


def is_jupiter_transit_activating(transit_jup_sign, natal_sig_sign, progressed_sign):
    return signs_have_nadi_relation(
        transit_jup_sign, natal_sig_sign
    ) or signs_have_nadi_relation(transit_jup_sign, progressed_sign)


# Astropy imports (optional, graceful fallback)
try:
    from astropy.time import Time
    from astropy.coordinates import (
        solar_system_ephemeris,
        get_body,
        GeocentricTrueEcliptic,
    )

    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False


def approximate_lahiri_ayanamsa(jd):
    """Rough Lahiri ayanamsa approximation."""
    t = (jd - 2451545.0) / 36525.0
    precess = 5029.0966 * t + 1.11161 * t ** 2
    return (23.853 + precess / 3600.0) % 360


def get_sidereal_lon(planet, dt, use_jpl=False):
    """Get sidereal longitude (Astropy or None)."""
    if not ASTROPY_AVAILABLE:
        return None
    try:
        # JD calculation (Meeus algorithm)
        yr, mo, dy = dt.year, dt.month, dt.day
        hr = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        if mo <= 2:
            yr -= 1
            mo += 12
        A = yr // 100
        B = 2 - A + A // 4
        jd = (
            int(365.25 * (yr + 4716))
            + int(30.6001 * (mo + 1))
            + dy
            + B
            - 1524.5
            + hr / 24.0
        )

        t = Time(jd, format="jd", scale="tdb")
        with solar_system_ephemeris.set("builtin"):
            body = get_body(planet.lower(), t)
            ecl = body.transform_to(GeocentricTrueEcliptic())
            trop_lon = ecl.lon.deg % 360
        ayan = approximate_lahiri_ayanamsa(jd)
        return (trop_lon - ayan) % 360
    except:
        return None


def get_moon_transit_days(year, month, seventh_sign, sig_sign):
    """Days Moon transits 7th/sign (skip inauspicious tithis)."""
    if not ASTROPY_AVAILABLE:
        return []
    FAVORABLE_TITHIS = {
        1,
        2,
        4,
        6,
        9,
        10,
        12,
        14,
    }  # 0-indexed classical marriage tithis
    days = []
    for day in range(1, 32):
        try:
            dt = datetime(year, month, day, 12, tzinfo=timezone.utc)
            moon_lon = get_sidereal_lon("moon", dt)
            if moon_lon is not None and (
                get_sign(moon_lon) in (seventh_sign, sig_sign)
            ):
                sun_lon = get_sidereal_lon("sun", dt)
                if sun_lon:
                    tithi = int(((moon_lon - sun_lon) % 360) / 12)
                    if tithi not in (7, 22, 29):  # Skip Ashtami/Amavasya
                        days.append(day)
        except:
            break
    return days


def find_marriage_date(
    kundali,
    start_age=21,
    end_age=45,
    future_only=True,
    gender="male",
    use_real_transits=True,
    show_all_periods=False,
):
    """Core Nadi marriage timing prediction."""
    planets = kundali["planets"]
    sig_key = "Venus" if gender.lower() == "male" else "Mars"
    sig_lon = planets.get(sig_key)
    jup_lon = planets.get("Jupiter")
    if not sig_lon or not jup_lon:
        return "Missing data"

    natal_sig_sign = get_sign(sig_lon)
    lagna_lon = kundali.get("lagna", 0)
    seventh_sign = get_seventh_sign(lagna_lon)
    birth_year = kundali["birth_date"].year
    today = datetime.now()

    promise = check_nadi_promise(planets, gender)
    significators_ad = {"Venus", "Moon", "Jupiter", kundali.get("lord7", "")}

    sign_names = [
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
    results = []

    for age in range(start_age, end_age + 1):
        round_num = (age // 12) + 1
        prog_sign = get_progressed_jupiter_sign(jup_lon, age)

        if not signs_have_nadi_relation(prog_sign, natal_sig_sign):
            continue

        year = birth_year + age
        if future_only and year < today.year:
            continue

        # Dasha match
        dasha_ok = False
        matching_period, dasha_score = None, 0
        for period in kundali["dasha_periods"]:
            if isinstance(period, dict):
                start = period["start"]
                end = period["end"]
                md = period["maha"]
                ad = period["antara"]
            else:
                start, end, md, ad = period
            if start <= year <= end and ad in significators_ad:
                dasha_ok = True
                matching_period = f"{md}/{ad} ({start}-{end})"
                dasha_score = 10 if ad == "Venus" else 8 if ad == "Jupiter" else 7
                break
        if not dasha_ok:
            continue

        # Jupiter transit months
        probable_months, peak_months, saturn_months = [], [], set()
        for month in range(1, 13):
            if future_only:
                check_date = datetime(year, month, 15)
                if check_date < today:
                    continue

            jup_trans = (
                get_sidereal_lon("jupiter", check_date) if use_real_transits else None
            )
            if jup_trans is not None:
                jup_sign_t = get_sign(jup_trans)
                jup_act = signs_have_nadi_relation(
                    jup_sign_t, natal_sig_sign
                ) or signs_have_nadi_relation(jup_sign_t, seventh_sign)
                if jup_act:
                    if jup_sign_t in (seventh_sign, natal_sig_sign):
                        peak_months.append(month)
                    probable_months.append(month)

                    sat_trans = get_sidereal_lon("saturn", check_date)
                    if sat_trans and signs_have_nadi_relation(
                        get_sign(sat_trans), seventh_sign
                    ):
                        saturn_months.add(month)
            else:
                # Fallback approx
                trans_jup = (get_sign(jup_lon) + age + month // 3) % 12
                if is_jupiter_transit_activating(trans_jup, natal_sig_sign, prog_sign):
                    probable_months.append(month)

        if not probable_months:
            continue

        # Moon favorable days (first peak month)
        all_dates = []
        fav_days_first = get_moon_transit_days(
            year, probable_months[0], seventh_sign, natal_sig_sign
        )
        for day in fav_days_first:
            all_dates.append((year, probable_months[0], day))

        # Best date
        best_date = f"{year}-{probable_months[0]:02d}-{fav_days_first[0] if fav_days_first else 15}"

        # Confidence
        has_sat = bool(saturn_months & set(probable_months))
        conf = (
            "VERY HIGH"
            if dasha_score >= 8 and has_sat
            else "HIGH"
            if dasha_score >= 8
            else "MEDIUM"
        )

        results.append(
            {
                "date": best_date,
                "age": age,
                "round": round_num,
                "prog_sign": sign_names[prog_sign],
                "dasha": matching_period,
                "dasha_score": dasha_score,
                "probable_months": probable_months,
                "peak_months": peak_months,
                "favorable_dates": [
                    f"{year}-{m:02d}-{d:02d}" for m, d in all_dates[:15]
                ],
                "confidence": conf + (" [Saturn confirms]" if has_sat else ""),
                "promise": promise,
            }
        )

        if not show_all_periods and "HIGH" in conf:
            return format_prediction_result(results[0])

    if results:
        results.sort(key=lambda x: (-x["dasha_score"], x["age"]))
        output = f"Found {len(results)} periods:\n\n"
        for i, r in enumerate(results[:5], 1):
            output += f"\n{'='*60}\n{i}. " + format_prediction_result(r)
        return output
    return f"No periods found. Promise: {promise}"


def format_prediction_result(result):
    """Format single prediction nicely."""
    out = f"📅 {result['date']}\n"
    out += f"Age {result['age']} (Round {result['round']})\n"
    out += f"Ju progressed: {result['prog_sign']}\n"
    out += f"Dasha: {result['dasha']} (score {result['dasha_score']})\n"
    out += f"Peak months: {', '.join(map(str,result['peak_months']))}\n"
    out += f"Confidence: {result['confidence']}\n"
    out += f"Promise: {result['promise']}"
    return out


class AdvancedSpousePredictor:

    """
    Ultra-detailed spouse prediction using 25+ Vedic techniques.
    """

    def _calculate_arudha_lagna(self) -> Dict:
        """Compute Arudha Lagna (AL) – the image of the ascendant."""
        d1 = self.data["planets"]
        lagna_lord = SIGN_LORDS[self.lagna_sign]
        if lagna_lord not in d1:
            return {"sign": "Unknown", "index": 0}
        lagna_lord_sign = d1[lagna_lord]["sign"]
        lagna_lord_idx = ZODIAC_SIGNS.index(lagna_lord_sign)
        lagna_idx = self.lagna_idx
        distance = (lagna_lord_idx - lagna_idx) % 12
        al_idx = (lagna_lord_idx + distance) % 12
        # Exception: if AL falls in the same sign as lagna or 7th from lagna, move it to the 10th from that sign
        if al_idx == lagna_idx or al_idx == (lagna_idx + 6) % 12:
            al_idx = (al_idx + 9) % 12
        al_sign = ZODIAC_SIGNS[al_idx]
        return {"sign": al_sign, "index": al_idx}

    def __init__(self, chart_data: Dict):
        self.data = chart_data
        self.gender = chart_data.get("gender", "Male")
        self.spouse_karaka = "Ju" if self.gender == "Female" else "Ve"
        self.spouse_term = "husband" if self.gender == "Female" else "wife"

        # D1 Lagna
        self.lagna_sign = chart_data.get("lagna_sign", "Aries")
        self.lagna_idx = ZODIAC_SIGNS.index(self.lagna_sign)
        self.lagna_deg = chart_data.get("lagna_deg", 0.0)

        # D9 Lagna (calculated from lagna degree)
        self.d9_lagna_sign = get_navamsa_sign(self.lagna_deg)
        self.d9_lagna_idx = (
            ZODIAC_SIGNS.index(self.d9_lagna_sign)
            if self.d9_lagna_sign in ZODIAC_SIGNS
            else 0
        )

        # Jaimini data (if available)
        self.jaimini = self.data.get("jaimini", {})
        self.atmakaraka = self.jaimini.get("atmakaraka")
        self.karakamsa_lagna = self.jaimini.get("karakamsa_lagna")

        # Confidence tracking
        self.confidence_factors = []

    # ------------------------------------------------------------------------
    # Core House Analysis
    # ------------------------------------------------------------------------
    def _analyze_atmakaraka_for_spouse(self) -> Dict:
        """Analyze Atmakaraka (soul's significator) and its D9 position."""
        if not self.atmakaraka:
            return {"error": "Atmakaraka not available"}

        d9 = self.data.get("navamsa", {})
        ak = self.atmakaraka
        ak_full = SHORT_TO_FULL.get(ak, ak)

        # D9 sign of Atmakaraka
        ak_d9_sign = d9.get(ak, {}).get("sign", "Unknown") if ak in d9 else "Unknown"
        ak_d9_dignity = get_dignity(ak, ak_d9_sign) if ak_d9_sign != "Unknown" else ""

        # Relationship to 7th house in D9
        d9_7th_house_idx = (self.d9_lagna_idx + 6) % 12
        d9_7th_sign = ZODIAC_SIGNS[d9_7th_house_idx]
        ak_in_7th_d9 = ak_d9_sign == d9_7th_sign

        interpretation = []
        if ak_in_7th_d9:
            interpretation.append(
                f"Your Atmakaraka {ak_full} is in the 7th house of D9 – your spouse is deeply connected to your soul's purpose. Marriage is karmic and transformative."
            )
            self.confidence_factors.append("Atmakaraka in D9 7th – soulmate connection")
        else:
            interpretation.append(
                f"Your Atmakaraka {ak_full} resides in {ak_d9_sign} in D9. Your spouse will help you grow in areas ruled by this sign."
            )

        # Dignity remark
        if ak_d9_dignity in ("Exalt", "Own"):
            interpretation.append(
                f"Atmakaraka is {ak_d9_dignity} in D9 – your soul's strength is well‑supported; marriage will be a source of spiritual growth."
            )
            self.confidence_factors.append(f"Atmakaraka {ak_d9_dignity} in D9")
        elif ak_d9_dignity == "Debilitated":
            interpretation.append(
                f"Atmakaraka is debilitated in D9 – you may need to work through karmic challenges in marriage, but overcoming them brings great wisdom."
            )

        return {
            "atmakaraka": ak,
            "atmakaraka_full": ak_full,
            "d9_sign": ak_d9_sign,
            "d9_dignity": ak_d9_dignity,
            "in_7th_d9": ak_in_7th_d9,
            "interpretation": " ".join(interpretation),
        }

    def _analyze_karakamsa_lagna(self) -> Dict:
        """Analyze Karakamsa Lagna (sign of Atmakaraka in D9)."""
        if not self.karakamsa_lagna:
            return {"error": "Karakamsa Lagna not available"}

        kl = self.karakamsa_lagna
        kl_idx = ZODIAC_SIGNS.index(kl) if kl in ZODIAC_SIGNS else -1
        d9 = self.data.get("navamsa", {})

        # 7th house from Karakamsa Lagna in D9
        if kl_idx != -1:
            kl_7th_idx = (kl_idx + 6) % 12
            kl_7th_sign = ZODIAC_SIGNS[kl_7th_idx]
        else:
            kl_7th_sign = "Unknown"

        # Planets in Karakamsa Lagna or its 7th in D9
        planets_in_kl = []
        planets_in_kl_7th = []
        for pl, data in d9.items():
            sign = data.get("sign", "")
            if sign == kl:
                planets_in_kl.append(pl)
            if sign == kl_7th_sign:
                planets_in_kl_7th.append(pl)

        # Interpretation
        lines = []
        lines.append(
            f"Karakamsa Lagna = {kl} – the sign of your soul's ultimate focus."
        )
        lines.append(
            f"Its 7th house (spouse) in D9 is {kl_7th_sign}. Planets here colour the spouse's role in your spiritual evolution."
        )
        if planets_in_kl_7th:
            pl_names = [SHORT_TO_FULL.get(p, p) for p in planets_in_kl_7th]
            lines.append(
                f"✨ Planets in Karakamsa 7th: {', '.join(pl_names)} – they strongly influence your marriage at the soul level."
            )
            self.confidence_factors.append(
                f"Planets in Karakamsa 7th: {', '.join(pl_names)}"
            )
        if planets_in_kl:
            pl_names = [SHORT_TO_FULL.get(p, p) for p in planets_in_kl]
            lines.append(
                f"Planets conjunct Karakamsa Lagna: {', '.join(pl_names)} – they amplify the soul's mission and may manifest through the spouse."
            )

        return {
            "karakamsa_lagna": kl,
            "kl_7th_sign": kl_7th_sign,
            "planets_in_kl": planets_in_kl,
            "planets_in_kl_7th": planets_in_kl_7th,
            "interpretation": "\n      ".join(lines),
        }

    def _analyze_7th_house_multilevel(self) -> Dict:
        h7_idx = (self.lagna_idx + 6) % 12
        h7_sign = ZODIAC_SIGNS[h7_idx]
        h7_lord = SIGN_LORDS[h7_sign]

        d1 = self.data["planets"]
        h7_lord_data = d1.get(h7_lord, {})
        h7_lord_sign = h7_lord_data.get("sign", "")
        h7_lord_dignity = get_dignity(h7_lord, h7_lord_sign)
        h7_lord_house = self._get_house(h7_lord)

        # Functional nature of 7th lord
        func_nature = self.data.get("functional_nature", {}).get(h7_lord, {})
        func_label = func_nature.get("label", "Unknown")

        # Integrity of 7th lord
        integrity = self.data.get("integrity", {}).get(h7_lord, {})
        integrity_score = integrity.get("score", 50)

        analysis = {
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

        if h7_lord_dignity in ["Exalted", "Own"]:
            self.confidence_factors.append(
                f"7th lord {SHORT_TO_FULL[h7_lord]} strong in D1"
            )
        if func_label in ["Strong Benefic", "Conditional Benefic"]:
            self.confidence_factors.append("7th lord functionally benefic")
        if integrity_score >= 70:
            self.confidence_factors.append(
                f"7th lord high integrity ({integrity_score}%)"
            )

        return analysis

    # ------------------------------------------------------------------------
    # Functional Venus-Jupiter Analysis
    # ------------------------------------------------------------------------
    def _analyze_functional_venus_jupiter(self) -> Dict:
        """Analyze functional status of Venus and Jupiter, including mutual aspect/conjunction."""
        func = self.data.get("functional_nature", {})
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

        if venus.get("label") in ["Strong Benefic", "Conditional Benefic"]:
            self.confidence_factors.append(
                "Venus functionally benefic - excellent spouse karaka"
            )
        if jupiter.get("label") in ["Strong Benefic", "Conditional Benefic"]:
            self.confidence_factors.append(
                "Jupiter functionally benefic - blessed marriage"
            )

        # Venus-Jupiter mutual aspect/conjunction
        d1 = self.data["planets"]
        ve_data = d1.get("Ve", {})
        ju_data = d1.get("Ju", {})
        ve_deg = ve_data.get("deg", 0)
        ju_deg = ju_data.get("deg", 0)
        ve_sign = ve_data.get("sign", "")
        ju_sign = ju_data.get("sign", "")
        ve_house = self._get_house("Ve")
        ju_house = self._get_house("Ju")

        vj_relationship = "No direct connection"
        if ve_sign and ju_sign:
            if ve_sign == ju_sign:
                deg_diff = abs(ve_deg - ju_deg)
                if deg_diff < 10:
                    vj_relationship = f"Conjunction within {deg_diff:.1f}° – harmonious union, spouse is wise and beautiful"
                    self.confidence_factors.append(
                        "Venus-Jupiter conjunction – strong marriage indicator"
                    )
                else:
                    vj_relationship = (
                        f"Same sign but wide orb ({deg_diff:.1f}°) – mild positive"
                    )
            elif has_aspect(ve_house, ju_house, "Ve") or has_aspect(
                ju_house, ve_house, "Ju"
            ):
                vj_relationship = "Mutual aspect – harmonious spouse, balanced marriage"
                self.confidence_factors.append(
                    "Venus-Jupiter mutual aspect – positive marriage karma"
                )

        result["venus_jupiter_relationship"] = vj_relationship
        return result

    # ------------------------------------------------------------------------
    # Aspects on 7th House & Lord
    # ------------------------------------------------------------------------
    def _analyze_aspects_on_7th(self) -> Dict:
        aspects_data = self.data.get("aspects", {})
        h7_house_num = ((self.lagna_idx + 6) % 12) + 1

        # Aspects to 7th house
        h7_aspects = aspects_data.get(
            h7_house_num, []
        )  # aspects_data is dict house->list of aspect strings

        # Convert to structured list (simplified)
        combined = []
        for asp in h7_aspects:
            # asp is string like "Ju-7th" or "Ma-4"
            parts = asp.split("-")
            planet = parts[0]
            asp_type = parts[1] if len(parts) > 1 else "7th"
            combined.append({"target": "7th house", "planet": planet, "type": asp_type})

        # Add confidence for benefic aspects
        benefic_planets = ["Ju", "Ve", "Mo", "Me"]
        for asp in combined:
            if asp["planet"] in benefic_planets:
                self.confidence_factors.append(
                    f"Benefic {asp['planet']} aspect on 7th house"
                )

        return {"aspects": combined}

    # ------------------------------------------------------------------------
    # House Lord Placements
    # ------------------------------------------------------------------------
    def _analyze_house_lord_placements(self) -> Dict:
        placements = self.data.get("house_lords", {})
        return {
            "seventh_house": placements.get(7, {}),
            "second_house": placements.get(2, {}),
            "fifth_house": placements.get(5, {}),
        }

    # ------------------------------------------------------------------------
    # Dasha Timing Analysis
    # ------------------------------------------------------------------------
    def _analyze_marriage_dashas(self) -> Dict:
        # Use pre-parsed periods from main.py or fallback to timings lines
        periods = self.data.get("dasha_periods_for_marriage", [])
        if not periods:  # Fallback parse if no pre-parsed
            timings = self.data.get("timings", {}).get("Marriage", [])
            import re

            for line in timings:
                m = re.search(r"─\s*(\w+)/(\w+)\s*\((\d{4})-(\d{4})\)", line)
                if m:
                    periods.append(
                        {
                            "maha": m.group(1),
                            "antara": m.group(2),
                            "start": int(m.group(3)),
                            "end": int(m.group(4)),
                            "score": 8,  # Default
                        }
                    )
        high_score = [p for p in periods if p.get("score", 0) >= 8]
        return {
            "high_score_periods": high_score,
            "upcoming": [
                p for p in high_score if p.get("start", 0) > datetime.now().year
            ],
            "count": len(high_score),
        }

    # ------------------------------------------------------------------------
    # Current Transit Effects
    # ------------------------------------------------------------------------
    def _analyze_current_transits(self) -> Dict:
        transits = self.data.get("transits", {})
        h7_house_num = ((self.lagna_idx + 6) % 12) + 1

        transiting_7th = []
        for planet, data in transits.items():
            if data.get("house_from_moon") == h7_house_num:
                transiting_7th.append(planet)

        return {
            "transiting_7th": transiting_7th,
            "gochara": transits,
        }

    # ------------------------------------------------------------------------
    # Yogas for Marriage
    # ------------------------------------------------------------------------
    def _analyze_marriage_yogas_from_list(self) -> List[Dict]:
        all_yogas = self.data.get("yogas", [])
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
                relevant.append(
                    {"name": yoga, "strength": 5}
                )  # strength not in string, approximate
                self.confidence_factors.append(f"Marriage yoga: {yoga}")
        return relevant

    # ------------------------------------------------------------------------
    # Neecha Bhanga Effects
    # ------------------------------------------------------------------------
    def _analyze_neecha_bhanga_effects(self) -> Dict:
        nb_planets = self.data.get("neecha_bhanga_planets", [])
        h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(self.lagna_idx + 6) % 12]]
        dk = self._find_darakaraka_planet()

        effects = {}
        if h7_lord in nb_planets:
            effects[
                "seventh_lord"
            ] = "Neecha Bhanga - debilitation cancelled, becomes powerful after maturity"
            self.confidence_factors.append(
                "7th lord has Neecha Bhanga - delayed but strong marriage"
            )
        if dk in nb_planets:
            effects[
                "darakaraka"
            ] = "Neecha Bhanga - spouse-related planet gains strength over time"
        if "Ve" in nb_planets:
            effects[
                "venus"
            ] = "Neecha Bhanga - Venus strengthens with age, spouse quality improves"
        return effects

    # ------------------------------------------------------------------------
    # Darakaraka Analysis
    # ------------------------------------------------------------------------
    def _find_darakaraka_planet(self) -> str:
        d1 = self.data["planets"]
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

    def _analyze_darakaraka_advanced(self) -> Dict:
        dk_planet = self._find_darakaraka_planet()
        d1 = self.data["planets"]
        d9 = self.data.get("navamsa", {})

        dk_sign_d1 = d1[dk_planet]["sign"]
        dk_dignity_d1 = get_dignity(dk_planet, dk_sign_d1)
        min_deg = float(d1[dk_planet]["deg"]) % 30

        dk_sign_d9 = d9.get(dk_planet, {}).get("sign", "")
        dk_dignity_d9 = get_dignity(dk_planet, dk_sign_d9)

        # DK house in D9
        dk_d9_house = self._get_house_d9(dk_planet) if dk_planet in d9 else 0
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

        # Integrity and functional nature
        integrity = self.data.get("integrity", {}).get(dk_planet, {})
        func = self.data.get("functional_nature", {}).get(dk_planet, {})

        if dk_dignity_d1 in ["Exalted", "Own"]:
            self.confidence_factors.append(
                f"Darakaraka {SHORT_TO_FULL[dk_planet]} strong in D1"
            )
        if integrity.get("score", 0) >= 70:
            self.confidence_factors.append(
                f'Darakaraka high integrity ({integrity["score"]}%)'
            )

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

    # ------------------------------------------------------------------------
    # D9 7th House Analysis
    # ------------------------------------------------------------------------
    def _analyze_d9_seventh_house_advanced(self) -> Dict:
        d9 = self.data.get("navamsa", {})
        d9_h7_idx = (self.d9_lagna_idx + 6) % 12
        d9_h7_sign = ZODIAC_SIGNS[d9_h7_idx]
        d9_h7_lord = SIGN_LORDS[d9_h7_sign]

        # Lord position
        d9_h7_lord_sign = d9.get(d9_h7_lord, {}).get("sign", "")
        d9_h7_lord_dignity = (
            get_dignity(d9_h7_lord, d9_h7_lord_sign) if d9_h7_lord_sign else "Unknown"
        )

        # Planets in D9 7th
        planets_in = [
            p for p, data in d9.items() if ZODIAC_SIGNS.index(data["sign"]) == d9_h7_idx
        ]

        # Functional nature (from D1 proxy)
        func = self.data.get("functional_nature", {}).get(d9_h7_lord, {})
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
                f'Planets in D9 7th: {", ".join([SHORT_TO_FULL[p] for p in planets_in])}'
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
            "interpretation": (
                " | ".join(interpretation) if interpretation else "Average D9 7th house"
            ),
        }

    # ------------------------------------------------------------------------
    # House Helpers
    # ------------------------------------------------------------------------
    def _get_house(self, planet: str) -> int:
        d1 = self.data["planets"]
        if planet not in d1:
            return 0
        planet_sign = d1[planet]["sign"]
        planet_idx = ZODIAC_SIGNS.index(planet_sign)
        return ((planet_idx - self.lagna_idx) % 12) + 1

    def _get_house_d9(self, planet: str) -> int:
        d9 = self.data.get("navamsa", {})
        if planet not in d9:
            return 0
        planet_sign = d9[planet]["sign"]
        planet_idx = ZODIAC_SIGNS.index(planet_sign)
        return ((planet_idx - self.d9_lagna_idx) % 12) + 1

    # ------------------------------------------------------------------------
    # Base methods (Upapada, Manglik, Marriage type, etc.)
    # ------------------------------------------------------------------------
    def _analyze_upapada_enhanced(self) -> Dict:
        h12_idx = (self.lagna_idx + 11) % 12
        h12_sign = ZODIAC_SIGNS[h12_idx]
        h12_lord = SIGN_LORDS[h12_sign]
        d1 = self.data["planets"]
        if h12_lord not in d1:
            return {"sign": "", "strong": False}
        h12_lord_sign = d1[h12_lord]["sign"]
        h12_lord_idx = ZODIAC_SIGNS.index(h12_lord_sign)
        distance = (h12_lord_idx - h12_idx) % 12
        ul_idx = (h12_lord_idx + distance) % 12
        if ul_idx == h12_idx:
            ul_idx = (h12_idx + 9) % 12
        elif ul_idx == (h12_idx + 6) % 12:
            ul_idx = ((h12_idx + 6) + 9) % 12
        ul_sign = ZODIAC_SIGNS[ul_idx]
        ul_lord = SIGN_LORDS[ul_sign]
        ul_lord_sign = d1.get(ul_lord, {}).get("sign", "")
        ul_dignity = get_dignity(ul_lord, ul_lord_sign)
        strong = ul_dignity in ["Exalted", "Own", "Friendly"]
        if strong:
            self.confidence_factors.append("Upapada Lagna strong - stable marriage")

        ul_2nd_idx = (ul_idx + 1) % 12
        ul_2nd_sign = ZODIAC_SIGNS[ul_2nd_idx]
        planets_in_2nd = [
            p
            for p, data in d1.items()
            if ZODIAC_SIGNS.index(data["sign"]) == ul_2nd_idx
        ]
        has_malefic_2nd = any(p in ["Ma", "Sa", "Ra", "Ke"] for p in planets_in_2nd)
        meaning_2nd = (
            "Challenges in family harmony, possible financial strain"
            if has_malefic_2nd
            else "Supportive family after marriage, good sustenance, happiness"
        )

        ul_8th_idx = (ul_idx + 7) % 12
        ul_8th_sign = ZODIAC_SIGNS[ul_8th_idx]
        planets_in_8th = [
            p
            for p, data in d1.items()
            if ZODIAC_SIGNS.index(data["sign"]) == ul_8th_idx
        ]
        has_malefic_8th = any(p in ["Ma", "Sa", "Ra", "Ke"] for p in planets_in_8th)
        meaning_8th = (
            "Possible transformations, in-law issues, or obstacles"
            if has_malefic_8th
            else "Stable long-term marriage, good in-laws relations"
        )

        return {
            "sign": ul_sign,
            "lord": ul_lord,
            "dignity": ul_dignity,
            "strong": strong,
            "2nd_sign": ul_2nd_sign,
            "2nd_meaning": meaning_2nd,
            "8th_sign": ul_8th_sign,
            "8th_meaning": meaning_8th,
        }

    def _analyze_navamsa_strength(self) -> Dict:
        d1 = self.data["planets"]
        d9 = self.data.get("navamsa", {})
        vargottama = []
        for p in d1:
            if p in d9 and d1[p]["sign"] == d9[p]["sign"]:
                vargottama.append(p)
        if vargottama:
            self.confidence_factors.append(
                f'Vargottama: {", ".join([SHORT_TO_FULL[p] for p in vargottama])}'
            )
        return {"vargottama": vargottama, "count": len(vargottama)}

    def _analyze_venus_mars(self) -> Dict:
        d1 = self.data["planets"]
        if "Ve" not in d1 or "Ma" not in d1:
            return {"status": "No connection", "effect": "Neutral passion level"}
        ve_house = self._get_house("Ve")
        ma_house = self._get_house("Ma")
        if ve_house == ma_house:
            self.confidence_factors.append("Venus-Mars conjunction - intense passion")
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

    def _analyze_ashtakavarga(self) -> Dict:
        ashtak = self.data.get("ashtakavarga", {})
        h7_points = ashtak.get("interpretation", {}).get(7, {}).get("score")
        if h7_points is None:
            return {"points": "Data not available", "interpretation": "SAV not found"}
        if h7_points >= 28:
            interp = "Excellent - Very strong marriage yoga, smooth path"
            self.confidence_factors.append(
                f"Ashtakavarga 7th house {h7_points} points - excellent support"
            )
            strength = "Very Strong"
        elif h7_points >= 25:
            interp = "Good - Positive support for marriage"
            self.confidence_factors.append(
                f"Ashtakavarga 7th house {h7_points} points - good"
            )
            strength = "Strong"
        elif h7_points >= 22:
            interp = "Average - Normal marriage karma"
            strength = "Average"
        else:
            interp = "Weak - Possible delays, obstacles, or need for remedies"
            strength = "Weak"
        return {"points": h7_points, "strength": strength, "interpretation": interp}

    def _check_manglik_dosha(self) -> Dict:
        d1 = self.data["planets"]
        if "Ma" not in d1:
            return {"present": False, "reason": "Mars position unknown"}
        mars_house = self._get_house("Ma")
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
        ju_house = self._get_house("Ju")
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
        }

    def _classify_marriage_type(self) -> Dict:
        d1 = self.data["planets"]
        love_score = 0
        arranged_score = 0
        indicators = []
        ve_house = self._get_house("Ve")
        mo_house = self._get_house("Mo")
        if ve_house == mo_house:
            love_score += 3
            indicators.append("Venus-Moon conjunction (romantic nature)")
        h5_lord = SIGN_LORDS[ZODIAC_SIGNS[(self.lagna_idx + 4) % 12]]
        h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(self.lagna_idx + 6) % 12]]
        if self._get_house(h5_lord) == 7 or self._get_house(h7_lord) == 5:
            love_score += 3
            indicators.append("5th-7th house connection (love marriage yoga)")
        planets_in_5 = [p for p in d1 if self._get_house(p) == 5]
        planets_in_7 = [p for p in d1 if self._get_house(p) == 7]
        if "Ra" in planets_in_5 or "Ra" in planets_in_7 or "Ke" in planets_in_5:
            love_score += 2
            indicators.append("Rahu/Ketu influence (unconventional/love)")
        if ve_house == 5:
            love_score += 2
            indicators.append("Venus in 5th house (romance)")
        if "Ju" in planets_in_7:
            arranged_score += 2
            indicators.append("Jupiter in 7th (traditional/arranged)")
        h7_lord_house = self._get_house(h7_lord)
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

    def _predict_appearance_enhanced(self) -> Dict:
        h7_idx = (self.lagna_idx + 6) % 12
        h7_sign = ZODIAC_SIGNS[h7_idx]
        appearance = SIGN_APPEARANCE.get(h7_sign, {}).copy()
        appearance["primary_source"] = f"7th house in {h7_sign}"
        dk_planet = self._find_darakaraka_planet()
        d1 = self.data["planets"]
        d9 = self.data.get("navamsa", {})
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

    def _predict_meeting(self) -> Dict:
        h7_idx = (self.lagna_idx + 6) % 12
        h7_lord = SIGN_LORDS[ZODIAC_SIGNS[h7_idx]]
        h7_lord_house = self._get_house(h7_lord)
        circumstance = MEETING_CIRCUMSTANCES.get(h7_lord_house, "Various circumstances")
        return {"primary": circumstance, "7th_lord_house": h7_lord_house}

    def _predict_profession(self) -> Dict:
        dk_planet = self._find_darakaraka_planet()
        profession = {}
        if dk_planet:
            profession["primary"] = PLANET_SPOUSE_TRAITS.get(dk_planet, {}).get(
                "profession", ""
            )
        h7_idx = (self.lagna_idx + 6) % 12
        h7_lord = SIGN_LORDS[ZODIAC_SIGNS[h7_idx]]
        h7_lord_house = self._get_house(h7_lord)
        profession["secondary"] = PROFESSION_BY_HOUSE.get(h7_lord_house, "")
        return profession

    def _consolidate_profile(self, h7: Dict, karaka: Dict, dk: Dict) -> Dict:
        return {
            "7th_house_sign": h7["d1"]["sign"],
            "7th_lord": h7["d1"]["lord"],
            "darakaraka": dk["name"],
            "venus_functional": karaka["venus"]["label"],
            "jupiter_functional": karaka["jupiter"]["label"],
        }

    def _consolidate_personality(self, h7: Dict, dk: Dict) -> Dict:
        h7_sign = h7["d1"]["sign"]
        h7_traits = SIGN_APPEARANCE.get(h7_sign, {}).get("personality", "")
        dk_traits = dk["traits"].get("personality", "")
        return {"7th_house_influence": h7_traits, "darakaraka_influence": dk_traits}

    def _calculate_confidence(self) -> str:
        count = len(self.confidence_factors)
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

    # ------------------------------------------------------------------------
    # Nakshatra Analysis
    # ------------------------------------------------------------------------
    def _analyze_nakshatra_for_spouse(self) -> Dict:
        nakshatras = self.data.get("nakshatras_d1", {})
        if not nakshatras:
            return {}

        h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(self.lagna_idx + 6) % 12]]
        dk_planet = self._find_darakaraka_planet()
        key_planets = ["Ve", h7_lord, dk_planet]
        seen = set()
        key_planets = [p for p in key_planets if not (p in seen or seen.add(p))]

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
        if insights:
            self.confidence_factors.append("Nakshatra-level spouse refinement applied")
        return insights

    # ------------------------------------------------------------------------
    # Planetary War Detection
    # ------------------------------------------------------------------------
    def _detect_planetary_war(self) -> List[Dict]:
        d1 = self.data["planets"]
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
                            "description": f"{SHORT_TO_FULL[winner]} wins over {SHORT_TO_FULL[loser]}, {SHORT_TO_FULL[loser]}'s results are weakened.",
                        }
                    )
        return wars

    def _summarize_integrity(self) -> Dict:
        integrity = self.data.get("integrity", {})
        key_planets = ["Ve", "Ju", self._find_darakaraka_planet()]
        h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(self.lagna_idx + 6) % 12]]
        if h7_lord not in key_planets:
            key_planets.append(h7_lord)
        summary = {}
        for p in key_planets:
            if p in integrity:
                summary[p] = integrity[p]
        return summary

    # ------------------------------------------------------------------------
    # Main prediction method
    # ------------------------------------------------------------------------
    def predict(self) -> Dict:
        try:
            h7 = self._analyze_7th_house_multilevel()
        except Exception:
            h7 = {
                "d1": {"sign": "Unknown", "lord": "Unknown", "lord_dignity": "Unknown"}
            }
        try:
            karaka = self._analyze_functional_venus_jupiter()
        except Exception:
            karaka = {"venus": {"label": "Unknown"}, "jupiter": {"label": "Unknown"}}
        try:
            dk = self._analyze_darakaraka_advanced()
        except Exception:
            dk = {"name": "Unknown", "dignity_d1": "Unknown"}
        ul = self._analyze_upapada_enhanced()
        navamsa = self._analyze_navamsa_strength()
        d9_7th = self._analyze_d9_seventh_house_advanced()
        venus_mars = self._analyze_venus_mars()
        ashtak = self._analyze_ashtakavarga()
        manglik = self._check_manglik_dosha()
        marriage_type = self._classify_marriage_type()
        appearance = self._predict_appearance_enhanced()
        meeting = self._predict_meeting()
        profession = self._predict_profession()
        aspects_7th = self._analyze_aspects_on_7th()
        lord_placements = self._analyze_house_lord_placements()
        dashas = self._analyze_marriage_dashas()
        transits = self._analyze_current_transits()
        marriage_yogas = self._analyze_marriage_yogas_from_list()
        neecha = self._analyze_neecha_bhanga_effects()
        nakshatra = self._analyze_nakshatra_for_spouse()
        graha_yuddha = self._detect_planetary_war()
        integrity_summary = self._summarize_integrity()

        # NEW: Atmakaraka & Karakamsa
        atmakaraka_analysis = self._analyze_atmakaraka_for_spouse()
        karakamsa_analysis = self._analyze_karakamsa_lagna()

        return {
            "spouse_profile": self._consolidate_profile(h7, karaka, dk),
            "appearance": appearance,
            "personality": self._consolidate_personality(h7, dk),
            "profession": profession,
            "meeting": meeting,
            "marriage_type": marriage_type,
            "upapada": ul,
            "venus_mars": venus_mars,
            "ashtakavarga": ashtak,
            "navamsa_strength": navamsa,
            "d9_seventh_house": d9_7th,
            "manglik_dosha": manglik,
            "darakaraka_details": dk,
            "functional_karaka": karaka,
            "aspects_on_7th": aspects_7th,
            "lord_placements": lord_placements,
            "dasha_timing": dashas,
            "current_transits": transits,
            "marriage_yogas": marriage_yogas,
            "neecha_bhanga_effects": neecha,
            "integrity_summary": integrity_summary,
            "nakshatra_insights": nakshatra,
            "graha_yuddha": graha_yuddha,
            "atmakaraka_analysis": atmakaraka_analysis,  # new
            "karakamsa_analysis": karakamsa_analysis,  # new
            "confidence_factors": self.confidence_factors,
            "confidence_score": self._calculate_confidence(),
        }

    def generate_report(self) -> str:
        pred = self.predict()
        lines = []
        # Nadi marriage date prediction integration
        nadi_result = ""
        try:
            nadi_kundali = {
                "planets": self.data.get("planets_full_long", {}),
                "lagna": self.data.get("lagna_deg", 0.0),
                "lord7": self.data.get("lord7_full", ""),
                "birth_date": self.data.get("birth_datetime"),
                "dasha_periods": self.data.get("dasha_periods_for_marriage", []),
            }
            date_pred = find_marriage_date(
                nadi_kundali,
                start_age=21,
                end_age=45,
                future_only=True,
                gender=self.gender,
                use_real_transits=ASTROPY_AVAILABLE,
                show_all_periods=True,
            )
            nadi_result = f"\n\n📅 NADI MARRIAGE DATE PREDICTION:\n{date_pred}"
        except Exception as e:
            nadi_result = f"\n\n⚠️ Nadi prediction failed: {e}"
        lines.append("=" * 90)
        lines.append(
            "  ADVANCED FUTURE SPOUSE PREDICTION - PROFESSIONAL 2025-26 EDITION"
        )
        lines.append(
            "  (25+ Vedic Layers: Functional Nature + Integrity + Aspects + Dashas + Transits)"
        )
        lines.append("=" * 90)
        lines.append(f"\nGender: {self.gender} | Lagna: {self.lagna_sign}")
        lines.append(f"Spouse Karaka: {SHORT_TO_FULL[self.spouse_karaka]}")
        lines.append(f"\nOverall Confidence Score: {pred['confidence_score']}")

        # Spouse Profile
        lines.append("\n" + "─" * 90)
        lines.append("👤 SPOUSE PROFILE")
        lines.append("─" * 90)
        profile = pred["spouse_profile"]
        lines.append(f"7th House Sign: {profile['7th_house_sign']}")
        lines.append(f"7th Lord: {SHORT_TO_FULL[profile['7th_lord']]}")
        lines.append(f"Darakaraka: {profile['darakaraka']}")
        lines.append(f"Venus Functional Nature: {profile['venus_functional']}")
        lines.append(f"Jupiter Functional Nature: {profile['jupiter_functional']}")

        # Darakaraka Details
        lines.append("\n" + "─" * 90)
        lines.append("🌟 DARAKARAKA DETAILS (Jaimini)")
        lines.append("─" * 90)
        dk = pred["darakaraka_details"]
        lines.append(f"Planet: {dk['name']} at {dk['degree']:.2f}° within sign")
        lines.append(f"Sign in D1: {dk['sign_d1']} ({dk['dignity_d1']})")
        lines.append(f"Sign in D9: {dk['sign_d9']} ({dk['dignity_d9']})")
        lines.append(f"DK in D9 {dk['d9_house']}th house: {dk['d9_house_meaning']}")
        lines.append(f"Integrity Score: {dk['integrity']}%")
        lines.append(f"Functional Nature: {dk['functional']}")

        # NEW: Atmakaraka Analysis
        lines.append("\n" + "─" * 90)
        lines.append("🔮 ATMAKARAKA FOR SPOUSE (Soul Connection)")
        lines.append("─" * 90)
        ak_analysis = pred["atmakaraka_analysis"]
        if "error" not in ak_analysis:
            lines.append(ak_analysis["interpretation"])
        else:
            lines.append(f"Note: {ak_analysis.get('error', 'Data unavailable')}")

        # NEW: Karakamsa Lagna
        lines.append("\n" + "─" * 90)
        lines.append("🌌 KARAKAMSA LAGNA (Soul Marriage)")
        lines.append("─" * 90)
        kl_analysis = pred["karakamsa_analysis"]
        if "error" not in kl_analysis:
            lines.append(kl_analysis["interpretation"])
        else:
            lines.append(f"Note: {kl_analysis.get('error', 'Data unavailable')}")

        # Personality & Appearance
        lines.append("\n" + "─" * 90)
        lines.append("💫 SPOUSE PERSONALITY")
        lines.append("─" * 90)
        personality = pred["personality"]
        lines.append(f"7th House Influence: {personality['7th_house_influence']}")
        lines.append(f"Darakaraka Influence: {personality['darakaraka_influence']}")

        lines.append("\n" + "─" * 90)
        lines.append("✨ PHYSICAL APPEARANCE (Multi-Layer)")
        lines.append("─" * 90)
        appearance = pred["appearance"]
        lines.append(f"Primary Source: {appearance.get('primary_source', 'N/A')}")
        lines.append(f"Build: {appearance.get('build', 'N/A')}")
        lines.append(f"Face: {appearance.get('face', 'N/A')}")
        lines.append(f"Complexion: {appearance.get('complexion', 'N/A')}")
        if "dk_planet" in appearance:
            lines.append(
                f"Darakaraka {appearance['dk_planet']} adds: {appearance.get('dk_influence', '')}"
            )
            lines.append(f"DK sign modifier: {appearance.get('dk_sign_adds', '')}")
            lines.append(f"D9 refinement: {appearance.get('d9_refinement', '')}")

        # Venus-Mars
        lines.append("\n" + "─" * 90)
        lines.append("❤️‍🔥 VENUS-MARS DYNAMICS")
        lines.append("─" * 90)
        vm = pred["venus_mars"]
        lines.append(f"Status: {vm['status']}")
        lines.append(f"Effect: {vm['effect']}")

        # Yogas
        if pred["marriage_yogas"]:
            lines.append("\n" + "─" * 90)
            lines.append("🔮 MARRIAGE YOGAS")
            lines.append("─" * 90)
            for yoga in pred["marriage_yogas"]:
                lines.append(f"• {yoga['name']}")

        # Meeting & Profession
        lines.append("\n" + "─" * 90)
        lines.append("📍 MEETING CIRCUMSTANCES")
        lines.append("─" * 90)
        meeting = pred["meeting"]
        lines.append(f"Most Likely: {meeting['primary']}")

        lines.append("\n" + "─" * 90)
        lines.append("💼 SPOUSE PROFESSION")
        lines.append("─" * 90)
        profession = pred["profession"]
        lines.append(f"Primary Field: {profession.get('primary', 'N/A')}")
        lines.append(f"Secondary Field: {profession.get('secondary', 'N/A')}")

        # Upapada
        lines.append("\n" + "─" * 90)
        lines.append("🏠 UPAPADA LAGNA (Marriage House)")
        lines.append("─" * 90)
        ul = pred["upapada"]
        lines.append(
            f"Upapada Sign: {ul['sign']} (Lord {ul['lord']}, Dignity {ul['dignity']})"
        )
        lines.append(
            f"Strength: {'Strong - Stable marriage' if ul['strong'] else 'Moderate - needs effort'}"
        )
        lines.append(f"2nd from UL: {ul['2nd_meaning']}")
        lines.append(f"8th from UL: {ul['8th_meaning']}")

        # AL-UL Relationship
        lines.append("\n" + "─" * 90)
        lines.append("🔶 ARUDHA LAGNA (AL) – Social Image of Marriage")
        lines.append("─" * 90)
        al = self._calculate_arudha_lagna()
        ul_idx = ZODIAC_SIGNS.index(ul["sign"]) if ul["sign"] in ZODIAC_SIGNS else -1
        al_idx = al["index"]
        if al_idx != -1 and ul_idx != -1:
            diff = (ul_idx - al_idx) % 12
            if diff in [1, 11]:
                al_ul_relation = "2/12 from AL – marriage will be expensive, lavish, or involve foreign elements."
            elif diff in [5, 7]:
                al_ul_relation = "6/8 from AL – marriage may face societal opposition, be hidden, or unconventional."
            else:
                al_ul_relation = "Neutral – marriage will be socially accepted."
            lines.append(
                f"AL: {al['sign']} | UL: {ul['sign']} | Relationship: {al_ul_relation}"
            )
        else:
            lines.append("Unable to compute AL-UL relationship.")

        # D9 7th House
        lines.append("\n" + "─" * 90)
        lines.append("🔷 NAVAMSA (D9) 7TH HOUSE - Soul Marriage Level")
        lines.append("─" * 90)
        d9_7 = pred["d9_seventh_house"]
        lines.append(f"D9 7th House Sign: {d9_7['d9_7th_sign']}")
        lines.append(
            f"D9 7th Lord: {SHORT_TO_FULL[d9_7['d9_7th_lord']]} in {d9_7['d9_7th_lord_sign']} ({d9_7['d9_7th_lord_dignity']})"
        )
        if d9_7["planets_in_d9_7th"]:
            lines.append(
                f"Planets in D9 7th: {', '.join([SHORT_TO_FULL[p] for p in d9_7['planets_in_d9_7th']])}"
            )
        lines.append(f"Interpretation: {d9_7['interpretation']}")

        # Aspects on 7th
        lines.append("\n" + "─" * 90)
        lines.append("👁️ ASPECTS ON 7TH HOUSE")
        lines.append("─" * 90)
        if pred["aspects_on_7th"]["aspects"]:
            for asp in pred["aspects_on_7th"]["aspects"]:
                lines.append(f"• {asp['planet']} {asp['type']} on {asp['target']}")
        else:
            lines.append("No significant aspects detected.")

        # House Lord Placements
        lines.append("\n" + "─" * 90)
        lines.append("🏡 HOUSE LORD PLACEMENTS")
        lines.append("─" * 90)
        lords = pred["lord_placements"]
        if lords["seventh_house"]:
            lines.append(
                f"7th House Lord: {lords['seventh_house'].get('interpretation', 'N/A')}"
            )
        if lords["second_house"]:
            lines.append(
                f"2nd House Lord: {lords['second_house'].get('interpretation', 'N/A')}"
            )
        if lords["fifth_house"]:
            lines.append(
                f"5th House Lord: {lords['fifth_house'].get('interpretation', 'N/A')}"
            )

        # Marriage Type
        lines.append("\n" + "─" * 90)
        lines.append("💑 MARRIAGE TYPE PREDICTION")
        lines.append("─" * 90)
        mtype = pred["marriage_type"]
        lines.append(f"Category: {mtype['category']}")
        lines.append(f"Probability: {mtype['probability']}")
        if mtype["indicators"]:
            lines.append("Indicators:")
            for ind in mtype["indicators"]:
                lines.append(f"  • {ind}")

        # Manglik Dosha
        lines.append("\n" + "─" * 90)
        lines.append("⚠️ MANGLIK DOSHA ANALYSIS")
        lines.append("─" * 90)
        manglik = pred["manglik_dosha"]
        if manglik["present"]:
            lines.append(f"Status: PRESENT ({manglik['severity']})")
            lines.append(
                f"Mars in {manglik['mars_house']}th house ({manglik['mars_sign']}) - {manglik['mars_dignity']}"
            )
            if manglik["cancellations"]:
                lines.append("Cancellations:")
                for c in manglik["cancellations"]:
                    lines.append(f"  ✓ {c}")
        else:
            lines.append(f"Status: NOT PRESENT - {manglik.get('reason', '')}")

        # Neecha Bhanga
        if pred["neecha_bhanga_effects"]:
            lines.append("\n" + "─" * 90)
            lines.append("🔄 NEECHA BHANGA EFFECTS")
            lines.append("─" * 90)
            for planet, effect in pred["neecha_bhanga_effects"].items():
                lines.append(f"• {planet}: {effect}")

        # Ashtakavarga
        lines.append("\n" + "─" * 90)
        lines.append("📊 ASHTAKAVARGA 7TH HOUSE")
        lines.append("─" * 90)
        ashtak = pred["ashtakavarga"]
        lines.append(f"Points: {ashtak['points']}")
        lines.append(f"Interpretation: {ashtak['interpretation']}")

        # Navamsa Vargottama
        lines.append("\n" + "─" * 90)
        lines.append("📈 NAVAMSA VARGOTTAMA")
        lines.append("─" * 90)
        nav = pred["navamsa_strength"]
        lines.append(f"Vargottama Planets: {nav['count']}")
        if nav["vargottama"]:
            lines.append(
                f"  → {', '.join([SHORT_TO_FULL[p] for p in nav['vargottama']])}"
            )

        # Dasha Timing
        lines.append("\n" + "─" * 90)
        lines.append("⏳ MARRIAGE TIMING (Dasha Windows)")
        lines.append("─" * 90)
        dashas = pred["dasha_timing"]
        if dashas["upcoming"]:
            lines.append("Upcoming High-Probability Periods:")
            for p in dashas["upcoming"]:
                lines.append(
                    f"  • {p['maha']}/{p['antara']} ({p['start']}-{p['end']}) - Score {p['score']}/10"
                )
        else:
            lines.append("No high-score upcoming periods found.")

        lines.append("🌍 CURRENT TRANSIT EFFECTS")
        lines.append("─" * 90)
        transits = pred["current_transits"]
        if transits["transiting_7th"]:
            lines.append(
                f"Planets transiting 7th house: {', '.join(transits['transiting_7th'])}"
            )
        else:
            lines.append("No current transit activation of 7th house.")

        # Nakshatra Insights
        if pred["nakshatra_insights"]:
            lines.append("\n" + "─" * 90)
            lines.append("🌙 NAKSHATRA INSIGHTS")
            lines.append("─" * 90)
            for p, info in pred["nakshatra_insights"].items():
                lines.append(
                    f"• {SHORT_TO_FULL[p]} in {info['nakshatra']} (ruled by {info['lord']}, deity {info['deity']})"
                )
                lines.append(f"  → {info['meaning']}")

        # Planetary War
        if pred["graha_yuddha"]:
            lines.append("\n" + "─" * 90)
            lines.append("⚔️ GRAHA YUDDHA (Planetary War)")
            lines.append("─" * 90)
            for war in pred["graha_yuddha"]:
                lines.append(f"• {war['description']}")

        # Integrity Summary
        lines.append("\n" + "─" * 90)
        lines.append("🔒 PLANETARY INTEGRITY")
        lines.append("─" * 90)
        for p, data in pred["integrity_summary"].items():
            lines.append(f"• {SHORT_TO_FULL[p]}: {data['score']}% - {data['label']}")

        # Confidence Factors
        lines.append("\n" + "─" * 90)
        lines.append(f"✅ CONFIRMING FACTORS ({len(pred['confidence_factors'])})")
        lines.append("─" * 90)
        for factor in pred["confidence_factors"]:
            lines.append(f"• {factor}")

        lines.append("\n" + "=" * 90)
        lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 90)

        return "\n".join(lines) + nadi_result
