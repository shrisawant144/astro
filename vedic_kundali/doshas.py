# Dosha Detection Module
# Detect major doshas and problems in the Kundali

from constants import (
    zodiac_signs,
    short_to_full,
    FUNCTIONAL_QUALITY,
    sign_lords,
)


# ────────────────────────────────────────────────
# Helper function for consecutive houses
# ────────────────────────────────────────────────
def _houses_are_consecutive(house_set):
    """Return True if the given set of house numbers form a consecutive sequence."""
    houses = sorted(house_set)
    n = len(houses)
    if n < 2:
        return True
    for start_i in range(n):
        ok = True
        for j in range(1, n):
            diff = (houses[(start_i + j) % n] - houses[(start_i + j - 1) % n]) % 12
            if diff != 1:
                ok = False
                break
        if ok:
            return True
    return False


# ────────────────────────────────────────────────
# Dosha Detection
# ────────────────────────────────────────────────
def detect_problems(result):
    """Detect major problems/doshas in the Kundali"""
    problems = []
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
    
    # 1. Mangal Dosha (Mars in 1,2,4,7,8,12 from Lagna)
    if "Ma" in planet_house and planet_house["Ma"] in [1, 2, 4, 7, 8, 12]:
        house_num = planet_house["Ma"]
        mars_sign = p.get("Ma", {}).get("sign", "")
        mars_dignity = p.get("Ma", {}).get("dignity", "")
        moon_dignity = p.get("Mo", {}).get("dignity", "")
        
        # Calculate cancellation factors
        cancellation_factors = []
        severity_reduction = 0
        
        # Factor 1: Jupiter aspects 7th house
        ju_house = planet_house.get("Ju", 0)
        if ju_house:
            ju_5th_aspect = ((ju_house - 1 + 4) % 12) + 1
            ju_7th_aspect = ((ju_house - 1 + 6) % 12) + 1
            ju_9th_aspect = ((ju_house - 1 + 8) % 12) + 1
            if 7 in [ju_5th_aspect, ju_7th_aspect, ju_9th_aspect]:
                cancellation_factors.append("Jupiter aspects 7th house")
                severity_reduction += 3
        
        # Factor 2: Jupiter aspects Mars directly
        if ju_house and "Ma" in planet_house:
            mars_h = planet_house["Ma"]
            if mars_h in [ju_5th_aspect, ju_7th_aspect, ju_9th_aspect]:
                cancellation_factors.append("Jupiter aspects Mars")
                severity_reduction += 2
        
        # Factor 3: Mars in own sign or exalted
        if mars_dignity in ["Own", "Exalted"]:
            cancellation_factors.append(f"Mars {mars_dignity.lower()} in {mars_sign}")
            severity_reduction += 2
        
        # Factor 4: Mars in Leo or Aquarius
        if mars_sign in ["Leo", "Aquarius"]:
            cancellation_factors.append(f"Mars in {mars_sign} (mitigating sign)")
            severity_reduction += 1
        
        # Factor 5: Strong Moon
        if moon_dignity in ["Exalted", "Own"]:
            cancellation_factors.append(f"Moon {moon_dignity.lower()} (emotional stability)")
            severity_reduction += 2
        
        # Factor 6: D9 Venus dignity
        d9_data = result.get("navamsa", {})
        d9_venus_info = d9_data.get("Ve", {})
        d9_venus_dignity = d9_venus_info.get("dignity", "")
        if d9_venus_dignity in ["Exalted", "Own"]:
            cancellation_factors.append(f"D9 Venus {d9_venus_dignity.lower()}")
            severity_reduction += 2
        
        # Factor 7: D9 Mars dignity
        d9_mars_info = d9_data.get("Ma", {})
        d9_mars_dignity = d9_mars_info.get("dignity", "")
        if d9_mars_dignity in ["Exalted", "Own"]:
            cancellation_factors.append(f"D9 Mars {d9_mars_dignity.lower()}")
            severity_reduction += 1
        
        # Calculate severity
        base_severity = 10
        if house_num in [7, 8]:
            base_severity = 8
        elif house_num in [1, 4]:
            base_severity = 6
        else:
            base_severity = 5
        
        final_severity = max(1, base_severity - severity_reduction)
        
        # Determine severity label
        if final_severity <= 3:
            severity_label = "Mild"
            outcome = "Minor adjustments in marriage; generally manageable with awareness"
        elif final_severity <= 5:
            severity_label = "Moderate"
            outcome = "Some delays or disagreements possible; remedies helpful but not urgent"
        elif final_severity <= 7:
            severity_label = "Significant"
            outcome = "Potential delays/discord in marriage; remedies recommended"
        else:
            severity_label = "Severe"
            outcome = "Possible marital discord, delays in marriage, or heated arguments; remedies like Kumbh Vivah advised"
        
        cancel_text = ""
        if cancellation_factors:
            cancel_text = f" MITIGATING FACTORS: {', '.join(cancellation_factors)}."
        
        summary = f"Mangal Dosha – {severity_label} (Mars in {house_num}H, score {final_severity}/10): {outcome}"
        
        detail = (
            f"- Reason: Mangal Dosha occurs when Mars is in houses 1,2,4,7,8,12 from Lagna. "
            f"Mars in {house_num}H in {mars_sign} creates assertive energy in marriage house themes.\n"
            f"- Severity Assessment: Base severity {base_severity}/10 "
            f"(house {house_num}), reduced by {severity_reduction} points due to mitigating factors.\n"
            f"- Direct Outcome: {outcome}.{cancel_text}"
        )
        
        if final_severity > 3:
            problems.append({"summary": summary, "detail": detail})
        else:
            summary = f"Mangal Dosha – Largely Cancelled (Mars in {house_num}H): {', '.join(cancellation_factors)}"
            detail = (
                f"- Reason: Mars in {house_num}H technically creates Mangal Dosha, but multiple mitigating factors "
                f"({', '.join(cancellation_factors)}) effectively neutralise it.\n"
                f"- Direct Outcome: Marriage is protected; no significant delays or discord expected from this placement."
            )
            problems.append({"summary": summary, "detail": detail})
    
    # 2. Kemdrum Yoga
    if "Mo" in planet_house:
        moon_house = planet_house["Mo"]
        moon_house_planets = [pl for pl in h[moon_house] if pl != "Mo"]
        prev_house = ((moon_house - 2) % 12) + 1
        next_house = ((moon_house) % 12) + 1
        if len(moon_house_planets) == 0 and len(h[prev_house]) == 0 and len(h[next_house]) == 0:
            summary = "Kemdrum Yoga: Moon isolated – Emotional instability, financial fluctuations"
            detail = f"- Reason: Kemdrum Yoga forms when the Moon is alone without planetary support in adjacent houses.\n- Direct Outcome: Loneliness, mood swings, or financial instability."
            problems.append({"summary": summary, "detail": detail})
    
    # 3. Kaal Sarp Yoga
    if "Ra" in planet_house and "Ke" in planet_house:
        ra_house = planet_house["Ra"]
        ke_house = planet_house["Ke"]
        ra_pos = ra_house - 1
        ke_pos = ke_house - 1
        
        arc1 = (ke_pos - ra_pos) % 12
        arc2 = (ra_pos - ke_pos) % 12
        
        if arc1 <= 6:
            start, end = ra_pos, ke_pos
            direction = 1
        elif arc2 <= 6:
            start, end = ke_pos, ra_pos
            direction = 1
        else:
            start = end = None
        
        if start is not None:
            all_planets_between = True
            for pl, ph in planet_house.items():
                if pl in ["Ra", "Ke"]:
                    continue
                pos = ph - 1
                if direction == 1:
                    if start < end:
                        if not (start < pos < end):
                            all_planets_between = False
                            break
                    else:
                        if not (pos > start or pos < end):
                            all_planets_between = False
                            break
            if all_planets_between:
                summary = "Kaal Sarp Yoga: All planets hemmed between Rahu-Ketu – Life obstacles, but potential for sudden rise"
                detail = "- Reason: Kaal Sarp forms when all planets are trapped between Rahu and Ketu's axis.\n- Direct Outcome: Life struggles, delays, but potential breakthroughs after mid-life."
                problems.append({"summary": summary, "detail": detail})
    
    # 4. Debilitated Planets
    deb_planets = [pl for pl, data in p.items() if data["dignity"] == "Debilitated"]
    truly_deb = [pl for pl in deb_planets if not p[pl].get("neecha_bhanga", False)]
    nb_planets = [pl for pl in deb_planets if p[pl].get("neecha_bhanga", False)]
    
    if truly_deb:
        full_names = [short_to_full.get(pl, pl) for pl in truly_deb]
        deb_details = []
        for pl in truly_deb:
            sign = p[pl]["sign"]
            if pl == "Me":
                deb_details.append(f"Mercury in {sign}: Intuitive but scattered thinking.")
            elif pl == "Sa":
                deb_details.append(f"Saturn in {sign}: Initial instability, but builds strength through discipline.")
            elif pl == "Ju":
                deb_details.append(f"Jupiter in {sign}: Wisdom through practical experience.")
            elif pl == "Ve":
                deb_details.append(f"Venus in {sign}: Refined tastes developed through effort.")
            elif pl == "Ma":
                deb_details.append(f"Mars in {sign}: Energy channeled through emotional intelligence.")
            elif pl == "Su":
                deb_details.append(f"Sun in {sign}: Ego refined through service.")
            elif pl == "Mo":
                deb_details.append(f"Moon in {sign}: Emotional depth and transformation.")
        
        summary = f"Debilitated Planets ({', '.join(full_names)}): Areas requiring conscious development"
        detail = f"- Reason: A debilitated planet operates differently from its natural expression.\n- Direct Outcome: {'; '.join(deb_details)}"
        problems.append({"summary": summary, "detail": detail})
    
    # Neecha Bhanga planets
    if nb_planets:
        nb_full_names = [short_to_full.get(pl, pl) for pl in nb_planets]
        nb_details = []
        for pl in nb_planets:
            sign = p[pl]["sign"]
            if pl == "Sa":
                nb_details.append(f"Saturn in {sign} (NB): Delayed but powerful after maturity.")
            elif pl == "Me":
                nb_details.append(f"Mercury in {sign} (NB): Intuitive intelligence.")
            elif pl == "Ju":
                nb_details.append(f"Jupiter in {sign} (NB): Practical wisdom.")
            elif pl == "Ve":
                nb_details.append(f"Venus in {sign} (NB): Analytical approach to love/art.")
            elif pl == "Ma":
                nb_details.append(f"Mars in {sign} (NB): Strategic courage.")
            elif pl == "Su":
                nb_details.append(f"Sun in {sign} (NB): Humility transforms into leadership.")
            elif pl == "Mo":
                nb_details.append(f"Moon in {sign} (NB): Deep emotional wisdom.")
        
        summary = f"Neecha Bhanga Planets ({', '.join(nb_full_names)}): Debilitation cancelled – delayed but powerful"
        detail = f"- Reason: Neecha Bhanga occurs when supportive factors neutralize the weakness.\n- Direct Outcome: {'; '.join(nb_details)}"
        problems.append({"summary": summary, "detail": detail})
    
    # 5. Pitru Dosha
    sun_house = planet_house.get("Su", None)
    afflictions = []
    if "Sa" in planet_house and sun_house is not None:
        h_diff = (planet_house["Sa"] - sun_house + 12) % 12
        if h_diff in (0, 6):
            afflictions.append("Saturn")
    if "Ra" in planet_house and sun_house is not None:
        h_diff = (planet_house["Ra"] - sun_house + 12) % 12
        if h_diff in (0, 6):
            afflictions.append("Rahu")
    if sun_house == 12:
        afflictions.append("in 12H")
    if afflictions:
        summary = f"Pitru Dosha (Sun afflicted by {', '.join(afflictions)}): Ancestral issues, father-related challenges"
        detail = f"- Reason: Pitru Dosha arises from Sun's affliction by malefics.\n- Direct Outcome: Paternal health problems, family disputes, or luck obstacles."
        problems.append({"summary": summary, "detail": detail})
    
    # 6. Graha Malika Yoga
    _classical = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
    _c_house_set = set()
    for _pl in _classical:
        for _hnum, _plist in h.items():
            if _pl in _plist:
                _c_house_set.add(_hnum)
                break
    _n_classical_houses = len(_c_house_set)
    if _n_classical_houses >= 6 and _houses_are_consecutive(_c_house_set):
        summary = f"Graha Malika ({_n_classical_houses} classical planets in consecutive houses): Intense, focused life phases"
        detail = ("- Reason: Classical planets in sequential houses concentrate all life energy into a tight arc.\n"
                  "- Direct Outcome: Extreme highs/lows in the activated house arc.")
        problems.append({"summary": summary, "detail": detail})
    
    if not problems:
        problems.append({"summary": "No major doshas/problems detected – Generally favorable chart", "detail": "", "remedies": []})
        return problems
    
    # Add remedies
    problems = add_remedies(problems, result)
    return problems


# ────────────────────────────────────────────────
# Remedies
# ────────────────────────────────────────────────
def add_remedies(problems, result):
    """Add targeted remedies to each detected problem."""
    REMEDIES = {
        "Mangal_Severe": [
            "Recite Hanuman Chalisa daily, especially on Tuesdays.",
            "Donate red lentils (masoor dal) and red cloth on Tuesdays.",
            "Wear red coral (Moonga) in gold/copper ring on right ring finger.",
            "For marriage: Kumbh Vivah ritual (marrying a Peepal tree) before wedding.",
        ],
        "Mangal_Moderate": [
            "Recite Hanuman Chalisa on Tuesdays (optional).",
            "Donate red lentils (masoor dal) on Tuesdays.",
            "No Kumbh Vivah required – mitigating factors protect marriage.",
        ],
        "Mangal_Mild": [
            "General Mars balance: Light physical exercise and avoid aggression.",
            "Optional: Recite Hanuman Chalisa on Tuesdays if desired.",
            "No specific remedies required – dosha is largely cancelled.",
        ],
        "Kemdrum": [
            "Chant 'Om Som Somaya Namah' or 'Om Chandraya Namah' 108× on Mondays.",
            "Offer white flowers and milk to Shiva on Mondays.",
            "Wear moonstone or pearl in silver ring on right little finger.",
            "Avoid major decisions during waning Moon (Krishna Paksha).",
        ],
        "Kaal Sarp": [
            "Perform Kaal Sarp Dosh puja at Trimbakeshwar (Nasik) or Ujjain.",
            "Recite Maha Mrityunjaya Mantra 108× daily.",
            "Donate silver snake idol at Naga temple on Naga Panchami.",
        ],
        "Pitru": [
            "Perform Pitru Tarpan (water libation to ancestors) on every Amavasya.",
            "Observe Shradh rituals for 16 days (Pitru Paksha) annually.",
            "Donate cooked food (kheer/rice) to Brahmins or the needy.",
            "Plant a Peepal tree; feed crows on Saturdays.",
        ],
        "Graha Malika": [
            "Worship all nine Navagraha together on Saturdays.",
            "Recite Navagraha Stotra regularly.",
            "Balance planetary energies through colour therapy and gemstone consultation.",
        ],
    }
    
    for prob in problems:
        summary = prob["summary"]
        rems = []
        
        if "Mangal" in summary:
            if "Severe" in summary or "Significant" in summary:
                rems = REMEDIES["Mangal_Severe"]
            elif "Moderate" in summary:
                rems = REMEDIES["Mangal_Moderate"]
            else:
                rems = REMEDIES["Mangal_Mild"]
        elif "Kemdrum" in summary:
            rems = REMEDIES["Kemdrum"]
        elif "Kaal Sarp" in summary:
            rems = REMEDIES["Kaal Sarp"]
        elif "Graha Malika" in summary:
            rems = REMEDIES["Graha Malika"]
        elif "Pitru" in summary:
            rems = REMEDIES["Pitru"]
        elif "Debilitated" in summary:
            # Add debilitated planet remedies
            lagna_sign_r = result.get("lagna_sign", "")
            fq_r = FUNCTIONAL_QUALITY.get(lagna_sign_r, {})
            func_malefics = fq_r.get("mal", [])
            
            for ps, pk in [("Mercury", "Me"), ("Saturn", "Sa"), ("Sun", "Su"),
                           ("Moon", "Mo"), ("Mars", "Ma"), ("Jupiter", "Ju"), ("Venus", "Ve")]:
                if ps in summary:
                    is_malefic = pk in func_malefics
                    is_combust = result.get("planets", {}).get(pk, {}).get("combust", False)
                    
                    base_rem = f"Donate related items on {pk}'s day; chant appropriate mantra."
                    if is_malefic:
                        base_rem += f" [⚠ SKIP gem - {pk} is functional malefic]"
                    elif is_combust:
                        base_rem += " [⚠ CAUTION - planet is combust]"
                    
                    rems.append(base_rem)
        
        prob["remedies"] = rems
    
    return problems

