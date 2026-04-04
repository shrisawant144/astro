# marriage_scoring.py
"""
Marriage probability scoring based on Parashari principles.
Computes a score (0-10) for a given dasha period indicating likelihood of marriage.
"""

from .constants import short_to_full, sign_lords, zodiac_signs, FUNCTIONAL_QUALITY
from .utils import get_dignity, get_house_from_sign


def calculate_marriage_score(result, md_lord, ad_lord=None):
    """Calculate marriage probability score (0-10) for a dasha period.

    Comprehensive scoring for ALL lagnas:

    PRIMARY FACTORS (high weight):
    1. 7th lord involvement (+3) - Direct marriage significator
    2. Venus involvement (+2 base) - Natural marriage karaka
       - Yogakaraka bonus (+2)
       - D1 dignity bonus (+1)
    3. 2nd lord involvement (+2) - Family/kutumb

    SECONDARY FACTORS (medium weight):
    4. 5th lord involvement (+1.5) - Romance, love
    5. 11th lord involvement (+1) - Fulfillment of desires
    6. 4th lord involvement (+1) - Domestic happiness
    7. Jupiter involvement (+1) - Natural benefic, dharma
    8. 12th lord involvement (+0.5) - Bed pleasures (minor)

    D9 FACTORS (marriage-specific):
    9. D9 Venus exalt (+2) / own (+1)
    10. D9 7th lord strong (+1)
    11. D9 dasha lord strong (+1)
    12. D9 lagna lord strong (+0.5)

    PLACEMENT & DIGNITY FACTORS:
    13. Dasha lord in house 1/2/5/7/11 (+1)
    14. Dasha lord aspects 7th house (+1)
    15. Dasha lord D1 dignity own/exalt (+1)

    LAGNA-SPECIFIC FACTORS:
    16. Yogakaraka dasha lord (+2)
    17. Functional benefic (+1)

    SYNERGY BONUS:
    18. Both MD and AD marriage-related (+1)

    RAHU/KETU HANDLING:
    19. Rahu in 7th or with 7th lord (+1) - unconventional marriage
    20. Ketu special - can delay but also give spiritual spouse
    """
    score = 0.0
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)

    def lord_of(house_no):
        sign_idx = (lagna_idx + house_no - 1) % 12
        return sign_lords[zodiac_signs[sign_idx]]

    def house_of(planet):
        """Get house number where planet is placed"""
        for h, plist in result.get("houses", {}).items():
            if planet in plist:
                return h
        return 0

    def planet_aspects_house(planet, target_house):
        """Check if planet aspects a specific house"""
        pl_house = house_of(planet)
        if pl_house == 0:
            return False
        # 7th aspect (all planets)
        if ((pl_house - 1 + 6) % 12) + 1 == target_house:
            return True
        # Special aspects
        if planet == "Ma":  # Mars: 4th and 8th
            if ((pl_house - 1 + 3) % 12) + 1 == target_house:
                return True
            if ((pl_house - 1 + 7) % 12) + 1 == target_house:
                return True
        elif planet == "Ju":  # Jupiter: 5th and 9th
            if ((pl_house - 1 + 4) % 12) + 1 == target_house:
                return True
            if ((pl_house - 1 + 8) % 12) + 1 == target_house:
                return True
        elif planet == "Sa":  # Saturn: 3rd and 10th
            if ((pl_house - 1 + 2) % 12) + 1 == target_house:
                return True
            if ((pl_house - 1 + 9) % 12) + 1 == target_house:
                return True
        return False

    # Get house lords
    seventh_lord = result.get("seventh_lord", lord_of(7))
    second_lord = lord_of(2)
    fifth_lord = lord_of(5)
    fourth_lord = lord_of(4)
    eleventh_lord = lord_of(11)
    twelfth_lord = lord_of(12)
    first_lord = lord_of(1)  # Lagna lord

    # Get functional quality for this lagna
    fq = FUNCTIONAL_QUALITY.get(lagna_sign, {})
    func_benefics = fq.get("ben", [])
    func_malefics = fq.get("mal", [])
    yogakaraka = fq.get("yk", None)

    # Convert to short form for comparison
    md_short = next((k for k, v in short_to_full.items() if v == md_lord), md_lord)
    ad_short = (
        next((k for k, v in short_to_full.items() if v == ad_lord), ad_lord)
        if ad_lord
        else None
    )

    planets_involved = [md_short]
    if ad_short:
        planets_involved.append(ad_short)

    # Track what marriage factors are activated for synergy bonus
    marriage_factors_hit = 0

    # ═══════════════════════════════════════════════════════════════
    # PRIMARY FACTORS
    # ═══════════════════════════════════════════════════════════════

    # 1. 7th lord involvement (+3)
    if seventh_lord in planets_involved:
        score += 3
        marriage_factors_hit += 1

    # 2. Venus involvement (+2 base)
    if "Ve" in planets_involved:
        score += 2
        marriage_factors_hit += 1
        # Yogakaraka bonus (+2)
        if yogakaraka == "Ve":
            score += 2
        # D1 dignity bonus (+1)
        ve_d1_dig = result.get("planets", {}).get("Ve", {}).get("dignity", "")
        if ve_d1_dig in ("Own", "Exalt"):
            score += 1

    # 3. 2nd lord involvement (+2)
    if second_lord in planets_involved:
        score += 2
        marriage_factors_hit += 1

    # ═══════════════════════════════════════════════════════════════
    # SECONDARY FACTORS
    # ═══════════════════════════════════════════════════════════════

    # 4. 5th lord involvement (+1.5) - romance
    if fifth_lord in planets_involved:
        score += 1.5
        marriage_factors_hit += 1

    # 5. 11th lord involvement (+1) - fulfillment of desires
    if eleventh_lord in planets_involved:
        score += 1

    # 6. 4th lord involvement (+1) - domestic happiness
    if fourth_lord in planets_involved:
        score += 1

    # 7. Jupiter involvement (+1) - natural benefic
    if "Ju" in planets_involved:
        score += 1
        # Extra if Jupiter is Yogakaraka
        if yogakaraka == "Ju":
            score += 1

    # 8. 12th lord involvement (+0.5) - bed pleasures
    if twelfth_lord in planets_involved:
        score += 0.5

    # ═══════════════════════════════════════════════════════════════
    # D9 (NAVAMSA) FACTORS - Critical for marriage
    # ═══════════════════════════════════════════════════════════════
    navamsa = result.get("navamsa", {})

    # 9. D9 Venus strength
    if "Ve" in navamsa:
        ve_d9_sign = navamsa["Ve"].get("sign", "")
        ve_d9_dig = get_dignity("Ve", ve_d9_sign)
        if ve_d9_dig == "Exalt":
            score += 2
        elif ve_d9_dig == "Own":
            score += 1

    # 10. D9 7th lord strength
    if seventh_lord in navamsa:
        sl_d9_sign = navamsa[seventh_lord].get("sign", "")
        sl_d9_dig = get_dignity(seventh_lord, sl_d9_sign)
        if sl_d9_dig in ("Exalt", "Own"):
            score += 1

    # 11. D9 dasha lord strength
    for pl in planets_involved:
        if pl in navamsa and pl not in ["Ra", "Ke"]:
            pl_d9_sign = navamsa[pl].get("sign", "")
            pl_d9_dig = get_dignity(pl, pl_d9_sign)
            if pl_d9_dig in ("Exalt", "Own"):
                score += 1
                break  # Count once

    # 12. D9 lagna lord strength (+0.5)
    if first_lord in navamsa:
        fl_d9_sign = navamsa[first_lord].get("sign", "")
        fl_d9_dig = get_dignity(first_lord, fl_d9_sign)
        if fl_d9_dig in ("Exalt", "Own"):
            score += 0.5

    # ═══════════════════════════════════════════════════════════════
    # PLACEMENT & DIGNITY FACTORS
    # ═══════════════════════════════════════════════════════════════

    # 13. Dasha lord in marriage-relevant houses (1, 2, 5, 7, 11)
    for pl in planets_involved:
        pl_house = house_of(pl)
        if pl_house in [1, 2, 5, 7, 11]:
            score += 1
            break

    # 14. Dasha lord aspects 7th house (+1)
    for pl in planets_involved:
        if planet_aspects_house(pl, 7):
            score += 1
            break

    # 15. Dasha lord D1 dignity bonus (+1)
    for pl in planets_involved:
        if pl in result.get("planets", {}):
            pl_dig = result["planets"][pl].get("dignity", "")
            if pl_dig in ("Own", "Exalt"):
                score += 1
                break

    # ═══════════════════════════════════════════════════════════════
    # LAGNA-SPECIFIC FACTORS
    # ═══════════════════════════════════════════════════════════════

    # 16. Yogakaraka dasha lord (+2) - already handled above for Ve/Ju
    for pl in planets_involved:
        if pl == yogakaraka and pl not in ["Ve", "Ju"]:  # Avoid double counting
            score += 2
            break

    # 17. Functional benefic (+1)
    for pl in planets_involved:
        if pl in func_benefics:
            score += 1
            break

    # Penalty for functional malefic mahadasha lord (-0.5)
    if md_short in func_malefics:
        score -= 0.5

    # ═══════════════════════════════════════════════════════════════
    # SYNERGY BONUS
    # ═══════════════════════════════════════════════════════════════

    # 18. Both MD and AD are marriage-related (+1)
    if marriage_factors_hit >= 2 and ad_short:
        score += 1

    # ═══════════════════════════════════════════════════════════════
    # RAHU/KETU SPECIAL HANDLING
    # ═══════════════════════════════════════════════════════════════

    # 19. Rahu in 7th or aspecting 7th - unconventional but can give marriage
    if "Ra" in planets_involved:
        ra_house = house_of("Ra")
        if ra_house == 7:
            score += 1.5  # Strong indicator of marriage (unconventional)
        elif ra_house == 5:  # Rahu in 5th aspects 11th (desires)
            score += 0.5
        # Rahu with 7th lord
        seventh_lord_house = house_of(seventh_lord)
        if ra_house == seventh_lord_house:
            score += 1

    # 20. Ketu special handling
    if "Ke" in planets_involved:
        ke_house = house_of("Ke")
        if ke_house == 7:
            score += 0.5  # Can give marriage but spiritual/karmic spouse
        # Ketu in 12th - moksha but also bed pleasures
        if ke_house == 12:
            score += 0.5

    # ═══════════════════════════════════════════════════════════════
    # MOON FACTOR (for males especially, Moon = wife's mind)
    # ═══════════════════════════════════════════════════════════════
    if "Mo" in planets_involved:
        score += 0.5
        # Moon as 7th lord already counted above
        # Moon in good dignity
        mo_dig = result.get("planets", {}).get("Mo", {}).get("dignity", "")
        if mo_dig in ("Exalt", "Own"):
            score += 0.5

    # ═══════════════════════════════════════════════════════════════
    # FINAL ADJUSTMENTS
    # ═══════════════════════════════════════════════════════════════

    # Ensure score stays in 0-10 range
    return min(10, max(0, int(round(score))))
