# yoga_detection.py
"""
Detection and strength scoring of Vedic yogas (planetary combinations).
Includes Raja Yoga, Gajakesari, Dhana Yoga, Pancha Mahapurusha, etc.
"""

from constants import short_to_full, zodiac_signs, sign_lords, FUNCTIONAL_QUALITY
from utils import get_dignity


def get_yoga_strength(pl_list, result):
    """Calculate yoga strength from 1-10 based on dignity, house, retro,
    combustion, and Neecha Bhanga status."""
    score = 5  # baseline
    planets_data = result.get("planets", {})
    for pl in pl_list:
        if pl not in planets_data:
            continue
        d = planets_data[pl]
        # Dignity bonus/penalty (Neecha Bhanga softens debilitation from -3 to -1)
        if d["dignity"] == "Exalt":
            score += 3
        elif d["dignity"] == "Own":
            score += 2
        elif d["dignity"] == "Debilitated":
            if d.get("neecha_bhanga", False):
                score -= 1  # debilitation cancelled; minor residual only
            else:
                score -= 3
        # Combust penalty (combustion severely weakens a planet)
        if d.get("combust", False):
            score -= 2
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


def detect_yogas(result):
    """Detect major yogas and calculate their strength (1-10)."""
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
    # Traditional rule: Jupiter must occupy a kendra (1st/4th/7th/10th) from the Moon
    if "Ju" in planet_house and "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        ju_h = planet_house["Ju"]
        houses_from_moon = (ju_h - mo_h) % 12  # 0=1st, 3=4th, 6=7th, 9=10th
        if houses_from_moon in (0, 3, 6, 9):  # Jupiter in kendra from Moon
            stren = get_yoga_strength(["Ju", "Mo"], result)
            yogas.append(
                f"Gajakesari Yoga (Strength {stren}/10) → Fame, wisdom, wealth"
            )

    # 2. Raja Yogas (Kendra-Trikona lords)
    # A Yogakaraka is a single planet that lords both a kendra and a trikona.
    # Two different planets form a Raja Yoga by conjunction (same house) or
    # mutual 7th-house aspect (house difference = 6).
    seen_raja = set()
    yogakarakas_seen = set()
    for k in [1, 4, 7, 10]:
        for t in [1, 5, 9]:
            if k == t:
                continue  # same house — don't check against itself
            kl = lord_of(k)
            tl = lord_of(t)
            if kl not in planet_house or tl not in planet_house:
                continue
            if kl == tl:
                # Same planet lords both a kendra and a trikona → Yogakaraka
                if kl not in yogakarakas_seen:
                    yogakarakas_seen.add(kl)
                    s = get_yoga_strength([kl], result)
                    yogas.append(
                        f"Yogakaraka {short_to_full.get(kl, kl)} (Strength {s}/10) → "
                        f"Most powerful planet for this Lagna; grants both power & grace"
                    )
            else:
                pair = tuple(sorted([kl, tl]))
                if pair in seen_raja:
                    continue
                house_diff = (planet_house[kl] - planet_house[tl] + 12) % 12
                if house_diff in (0, 6):  # conjunction or mutual 7th aspect
                    seen_raja.add(pair)
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
