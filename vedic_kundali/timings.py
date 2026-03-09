# Timing Predictions Module
# Generate accurate timing predictions from birth to future

import re
import datetime
from constants import (
    zodiac_signs,
    sign_lords,
    short_to_full,
)


# ────────────────────────────────────────────────
# Marriage Score Calculation
# ────────────────────────────────────────────────
def calculate_marriage_score(result, md_lord, ad_lord=None):
    """Calculate marriage probability score (0-10) for a dasha period."""
    score = 0.0
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)
    
    def lord_of(house_no):
        sign_idx = (lagna_idx + house_no - 1) % 12
        return sign_lords[zodiac_signs[sign_idx]]
    
    def house_of(planet):
        for h, plist in result.get("houses", {}).items():
            if planet in plist:
                return h
        return 0
    
    def planet_aspects_house(planet, target_house):
        pl_house = house_of(planet)
        if pl_house == 0:
            return False
        # 7th aspect
        if ((pl_house - 1 + 6) % 12) + 1 == target_house:
            return True
        # Special aspects
        if planet == "Ma":
            if ((pl_house - 1 + 3) % 12) + 1 == target_house:
                return True
            if ((pl_house - 1 + 7) % 12) + 1 == target_house:
                return True
        elif planet == "Ju":
            if ((pl_house - 1 + 4) % 12) + 1 == target_house:
                return True
            if ((pl_house - 1 + 8) % 12) + 1 == target_house:
                return True
        elif planet == "Sa":
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
    first_lord = lord_of(1)
    
    # Get functional quality
    from constants import FUNCTIONAL_QUALITY
    fq = FUNCTIONAL_QUALITY.get(lagna_sign, {})
    func_benefics = fq.get("ben", [])
    func_malefics = fq.get("mal", [])
    yogakaraka = fq.get("yk", None)
    
    # Convert to short form
    md_short = next((k for k, v in short_to_full.items() if v == md_lord), md_lord)
    ad_short = next((k for k, v in short_to_full.items() if v == ad_lord), ad_lord) if ad_lord else None
    
    planets_involved = [md_short]
    if ad_short:
        planets_involved.append(ad_short)
    
    marriage_factors_hit = 0
    
    # PRIMARY FACTORS
    if seventh_lord in planets_involved:
        score += 3
        marriage_factors_hit += 1
    
    if "Ve" in planets_involved:
        score += 2
        marriage_factors_hit += 1
        if yogakaraka == "Ve":
            score += 2
        ve_d1_dig = result.get("planets", {}).get("Ve", {}).get("dignity", "")
        if ve_d1_dig in ("Own", "Exalted"):
            score += 1
    
    if second_lord in planets_involved:
        score += 2
        marriage_factors_hit += 1
    
    # SECONDARY FACTORS
    if fifth_lord in planets_involved:
        score += 1.5
        marriage_factors_hit += 1
    
    if eleventh_lord in planets_involved:
        score += 1
    
    if fourth_lord in planets_involved:
        score += 1
    
    if "Ju" in planets_involved:
        score += 1
        if yogakaraka == "Ju":
            score += 1
    
    if twelfth_lord in planets_involved:
        score += 0.5
    
    # D9 FACTORS
    from astro_utils import get_dignity
    navamsa = result.get("navamsa", {})
    
    if "Ve" in navamsa:
        ve_d9_sign = navamsa["Ve"].get("sign", "")
        ve_d9_dig = get_dignity("Ve", ve_d9_sign)
        if ve_d9_dig == "Exalt":
            score += 2
        elif ve_d9_dig == "Own":
            score += 1
    
    if seventh_lord in navamsa:
        sl_d9_sign = navamsa[seventh_lord].get("sign", "")
        sl_d9_dig = get_dignity(seventh_lord, sl_d9_sign)
        if sl_d9_dig in ("Exalt", "Own"):
            score += 1
    
    for pl in planets_involved:
        if pl in navamsa and pl not in ["Ra", "Ke"]:
            pl_d9_sign = navamsa[pl].get("sign", "")
            pl_d9_dig = get_dignity(pl, pl_d9_sign)
            if pl_d9_dig in ("Exalt", "Own"):
                score += 1
                break
    
    if first_lord in navamsa:
        fl_d9_sign = navamsa[first_lord].get("sign", "")
        fl_d9_dig = get_dignity(first_lord, fl_d9_sign)
        if fl_d9_dig in ("Exalt", "Own"):
            score += 0.5
    
    # PLACEMENT FACTORS
    for pl in planets_involved:
        pl_house = house_of(pl)
        if pl_house in [1, 2, 5, 7, 11]:
            score += 1
            break
    
    for pl in planets_involved:
        if planet_aspects_house(pl, 7):
            score += 1
            break
    
    for pl in planets_involved:
        if pl in result.get("planets", {}):
            pl_dig = result["planets"][pl].get("dignity", "")
            if pl_dig in ("Own", "Exalted"):
                score += 1
                break
    
    # LAGNA FACTORS
    for pl in planets_involved:
        if pl == yogakaraka and pl not in ["Ve", "Ju"]:
            score += 2
            break
    
    for pl in planets_involved:
        if pl in func_benefics:
            score += 1
            break
    
    if md_short in func_malefics:
        score -= 0.5
    
    # SYNERGY
    if marriage_factors_hit >= 2 and ad_short:
        score += 1
    
    # RAHU/KETU
    if "Ra" in planets_involved:
        ra_house = house_of("Ra")
        if ra_house == 7:
            score += 1.5
        elif ra_house == 5:
            score += 0.5
    
    if "Ke" in planets_involved:
        ke_house = house_of("Ke")
        if ke_house == 7:
            score += 0.5
        if ke_house == 12:
            score += 0.5
    
    # MOON
    if "Mo" in planets_involved:
        score += 0.5
        mo_dig = result.get("planets", {}).get("Mo", {}).get("dignity", "")
        if mo_dig in ("Exalted", "Own"):
            score += 0.5
    
    return min(10, max(0, int(round(score))))


# ────────────────────────────────────────────────
# Generate Timings
# ────────────────────────────────────────────────
def generate_timings(result, birth_year, birth_jd):
    """Generate accurate timing predictions from birth to future."""
    dashas = result["vimshottari"]["mahadasas"]
    current_year = datetime.datetime.now().year
    start_year = birth_year
    end_year = current_year + 20
    
    MIN_MARRIAGE_AGE = 21
    MIN_CAREER_AGE = 18
    MIN_CHILDREN_AGE = 22

    def lord_of(house_no):
        lagna_idx = zodiac_signs.index(result["lagna_sign"])
        sign = zodiac_signs[(lagna_idx + house_no - 1) % 12]
        return sign_lords[sign]

    seventh_lord = result["seventh_lord"]
    second_lord = lord_of(2)
    
    events = {
        "Marriage": [
            short_to_full["Ve"],
            short_to_full[seventh_lord],
            short_to_full["Ju"],
            short_to_full["Mo"],
            short_to_full[second_lord],
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
        
        if event == "Marriage":
            min_age = MIN_MARRIAGE_AGE
        elif event == "Children / Progeny":
            min_age = MIN_CHILDREN_AGE
        elif event == "Career Rise / Fame":
            min_age = MIN_CAREER_AGE
        else:
            min_age = 18
        
        min_event_year = birth_year + min_age
        
        for md in dashas:
            md_lord = md["lord"]
            md_start_age = (md["start_jd"] - birth_jd) / 365.25
            md_start_y = int(birth_year + md_start_age)
            md_end_y = int(birth_year + (md["end_jd"] - birth_jd) / 365.25)
            
            if md_end_y < start_year or md_start_y > end_year:
                continue
            
            status = "[PAST]" if md_end_y < current_year else "[NOW]" if md_start_y <= current_year <= md_end_y else "[FUTURE]"
            start_age = md_start_y - birth_year
            age_str = f"(Age {start_age}-{md_end_y - birth_year})"
            
            if md_lord in fav_lords:
                if md_end_y < min_event_year:
                    periods.append(f"• {md_lord} Mahadasha ({md_start_y}-{md_end_y}) {age_str} [KARMIC SEED]")
                else:
                    periods.append(f"• {md_lord} Mahadasha ({md_start_y}-{md_end_y}) {age_str} {status}")
            
            for ad in md.get("antardashas", []):
                if ad["lord"] in fav_lords:
                    ad_start_age = (ad["start_jd"] - birth_jd) / 365.25
                    ad_end_age = (ad["end_jd"] - birth_jd) / 365.25
                    ad_start_y = int(birth_year + ad_start_age)
                    ad_end_y = int(birth_year + ad_end_age)
                    
                    if ad_start_y <= end_year and ad_end_y >= start_year:
                        ad_status = "[PAST]" if ad_end_y < current_year else "[NOW]" if ad_start_y <= current_year <= ad_end_y else "[FUTURE]"
                        ad_age_str = f"Age {ad_start_y - birth_year}-{ad_end_y - birth_year}"
                        
                        if event == "Marriage":
                            score = calculate_marriage_score(result, md_lord, ad["lord"])
                            prob_label = "★★★" if score >= 7 else "★★" if score >= 4 else "★"
                            if ad_end_y < min_event_year:
                                periods.append(f" └─ {md_lord}/{ad['lord']} ({ad_start_y}-{ad_end_y}) ({ad_age_str}) [KARMIC SEED - too young]")
                            else:
                                periods.append(f" └─ {md_lord}/{ad['lord']} ({ad_start_y}-{ad_end_y}) ({ad_age_str}) {prob_label} [{score}/10] {ad_status}")
                        else:
                            if ad_end_y < min_event_year:
                                periods.append(f" └─ {md_lord}/{ad['lord']} ({ad_start_y}-{ad_end_y}) ({ad_age_str}) [FORMATIVE]")
                            else:
                                periods.append(f" └─ {md_lord}/{ad['lord']} Antardasha ({ad_start_y}-{ad_end_y}) ({ad_age_str}) {ad_status}")
        
        output[event] = sorted(periods, key=lambda x: int(re.search(r'\((\d{4})', x).group(1)) if re.search(r'\((\d{4})', x) else 0)[:20] if periods else []
    
    return output

