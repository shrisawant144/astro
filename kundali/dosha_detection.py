# dosha_detection.py
"""
Detection of doshas (afflictions) in a kundali: Mangal Dosha, Kemdrum, Kaal Sarp,
debilitated planets, Pitru Dosha, Graha Malika, etc. Includes targeted remedies.
"""

import re
from constants import (
    short_to_full,
    zodiac_signs,
    FUNCTIONAL_QUALITY,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
    NEECHA_BHANGA_INFO,
)
from utils import houses_are_consecutive, get_dignity

# -------------------------------------------------------------------
# Remedial measures for each dosha
# -------------------------------------------------------------------
REMEDIES = {
    "Mangal_Severe": [
        "Recite Hanuman Chalisa daily, especially on Tuesdays.",
        "Donate red lentils (masoor dal) and red cloth on Tuesdays.",
        "Wear red coral (Moonga) in gold/copper ring on right ring finger (after jyotishi consultation).",
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
        "Wear Navagraha or Kaal Sarp yantra after proper energisation.",
    ],
    "Debilitated_Me": [
        "Donate green cloth, green moong dal, or books on Wednesdays.",
        "Chant 'Om Bum Buddhaya Namah' 108× on Wednesdays.",
        "Wear emerald (Panna) in gold ring on right little finger – "
        "ONLY if Mercury is your functional benefic and not combust (consult jyotishi).",
        "Feed green grass to cows and read/give away books.",
    ],
    "Debilitated_Sa": [
        "Recite Shani Stotra and 'Om Sham Shanicharaya Namah' on Saturdays.",
        "Donate black sesame seeds, mustard oil, and black cloth on Saturdays.",
        "Light sesame oil lamp under Peepal tree on Saturdays.",
        "Wear blue sapphire only after thorough jyotishi trial (powerful and risky) – "
        "ONLY if Saturn is your functional benefic and not combust.",
    ],
    "Debilitated_Su": [
        "Offer water (Arghya) to the rising Sun daily with mantra.",
        "Donate wheat, jaggery, or copper items on Sundays.",
        "Chant 'Om Suryaya Namah' 108× mornings.",
    ],
    "Debilitated_Mo": [
        "Fast on Mondays or eat only once.",
        "Offer raw milk/white rice in flowing water on Mondays.",
        "Wear pearl or moonstone in silver on right little finger.",
    ],
    "Debilitated_Ma": [
        "Donate red lentils and copper items on Tuesdays.",
        "Chant 'Om Ang Angarakaya Namah' 108× on Tuesdays.",
        "Physical exercise and discipline reduce Mars's turbulent energy.",
    ],
    "Debilitated_Ju": [
        "Donate yellow cloth, chickpeas, turmeric on Thursdays.",
        "Chant 'Om Brim Brihaspataye Namah' 108× on Thursdays.",
        "Seek blessings of guru/elders; avoid disrespecting knowledge or teachers.",
    ],
    "Debilitated_Ve": [
        "Donate white sweets, white cloth, perfume on Fridays.",
        "Chant 'Om Shum Shukraya Namah' 108× on Fridays.",
        "Wear diamond or white sapphire (after consultation) on right index finger.",
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


def detect_problems(result):
    """Detect major problems/doshas in the Kundali."""
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

    # 1. Mangal Dosha (Mars in 1,2,4,7,8,12 from Lagna) with CANCELLATION CHECKS
    if "Ma" in planet_house and planet_house["Ma"] in [1, 2, 4, 7, 8, 12]:
        house_num = planet_house["Ma"]
        mars_sign = p.get("Ma", {}).get("sign", "")
        mars_dignity = p.get("Ma", {}).get("dignity", "")
        moon_dignity = p.get("Mo", {}).get("dignity", "")

        # Calculate cancellation factors
        cancellation_factors = []
        severity_reduction = 0

        # Factor 1: Jupiter aspects 7th house (check Jupiter's 5th aspect)
        ju_house = planet_house.get("Ju", 0)
        if ju_house:
            ju_5th_aspect = ((ju_house - 1 + 4) % 12) + 1  # 5th aspect
            ju_7th_aspect = ((ju_house - 1 + 6) % 12) + 1  # 7th aspect
            ju_9th_aspect = ((ju_house - 1 + 8) % 12) + 1  # 9th aspect
            if 7 in [ju_5th_aspect, ju_7th_aspect, ju_9th_aspect]:
                cancellation_factors.append("Jupiter aspects 7th house")
                severity_reduction += 3

        # Factor 2: Jupiter aspects Mars directly
        if ju_house and "Ma" in planet_house:
            mars_h = planet_house["Ma"]
            if mars_h in [ju_5th_aspect, ju_7th_aspect, ju_9th_aspect]:
                cancellation_factors.append("Jupiter aspects Mars")
                severity_reduction += 2

        # Factor 3: Mars in own sign (Aries/Scorpio) or exalted (Capricorn)
        if mars_dignity in ["Own", "Exalt"]:
            cancellation_factors.append(f"Mars {mars_dignity.lower()} in {mars_sign}")
            severity_reduction += 2

        # Factor 4: Mars in Leo or Aquarius (cancellation in some traditions)
        if mars_sign in ["Leo", "Aquarius"]:
            cancellation_factors.append(f"Mars in {mars_sign} (mitigating sign)")
            severity_reduction += 1

        # Factor 5: Strong Moon (exalted/own sign) provides emotional stability
        if moon_dignity in ["Exalt", "Own"]:
            cancellation_factors.append(
                f"Moon {moon_dignity.lower()} (emotional stability)"
            )
            severity_reduction += 2

        # Factor 6: Check D9 Venus dignity from result (if available)
        d9_data = result.get("d9", {})
        d9_venus_info = d9_data.get("Ve", {})
        d9_venus_dignity = d9_venus_info.get("dignity", "")
        if d9_venus_dignity in ["Exalt", "Own"]:
            cancellation_factors.append(f"D9 Venus {d9_venus_dignity.lower()}")
            severity_reduction += 2

        # Factor 7: Check D9 Mars dignity
        d9_mars_info = d9_data.get("Ma", {})
        d9_mars_dignity = d9_mars_info.get("dignity", "")
        if d9_mars_dignity in ["Exalt", "Own"]:
            cancellation_factors.append(f"D9 Mars {d9_mars_dignity.lower()}")
            severity_reduction += 1

        # Calculate severity: base 10, reduce by factors
        base_severity = 10
        # House-specific severity: 7th and 8th are traditionally more impactful
        if house_num in [7, 8]:
            base_severity = 8
        elif house_num in [1, 4]:
            base_severity = 6
        else:  # 2, 12
            base_severity = 5

        final_severity = max(1, base_severity - severity_reduction)

        # Determine severity label
        if final_severity <= 3:
            severity_label = "Mild"
            outcome = (
                "Minor adjustments in marriage; generally manageable with awareness"
            )
        elif final_severity <= 5:
            severity_label = "Moderate"
            outcome = (
                "Some delays or disagreements possible; remedies helpful but not urgent"
            )
        elif final_severity <= 7:
            severity_label = "Significant"
            outcome = "Potential delays/discord in marriage; remedies recommended"
        else:
            severity_label = "Severe"
            outcome = "Possible marital discord, delays in marriage, or heated arguments; remedies like Kumbh Vivah advised"

        # Build summary and detail
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

        # Only add to problems if severity is above mild threshold, or add with reduced emphasis
        if final_severity > 3:
            problems.append({"summary": summary, "detail": detail})
        else:
            # Still note it, but with "largely cancelled" language
            summary = f"Mangal Dosha – Largely Cancelled (Mars in {house_num}H): {', '.join(cancellation_factors)}"
            detail = (
                f"- Reason: Mars in {house_num}H technically creates Mangal Dosha, but multiple mitigating factors "
                f"({', '.join(cancellation_factors)}) effectively neutralise it.\n"
                f"- Direct Outcome: Marriage is protected; no significant delays or discord expected from this placement."
            )
            problems.append({"summary": summary, "detail": detail})

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
            summary = "Kemdrum Yoga: Moon isolated – Emotional instability, financial fluctuations"
            detail = f"- Reason: Kemdrum Yoga forms when the Moon is alone without planetary support in adjacent houses, leading to emotional void.\n- Direct Outcome: Loneliness, mood swings, or financial instability; strengthened by Moon's aspects or remedies like Chandra mantra."
            problems.append({"summary": summary, "detail": detail})

    # 3. Kaal Sarp Yoga (All planets between Rahu and Ketu in the shorter arc)
    if "Ra" in planet_house and "Ke" in planet_house:
        ra_house = planet_house["Ra"]
        ke_house = planet_house["Ke"]
        # Normalize to 0-11 for easier arithmetic
        ra_pos = ra_house - 1
        ke_pos = ke_house - 1

        # Compute both possible arcs (clockwise from Ra to Ke, and clockwise from Ke to Ra)
        arc1 = (ke_pos - ra_pos) % 12  # houses from Ra to Ke moving forward
        arc2 = (ra_pos - ke_pos) % 12  # houses from Ke to Ra moving forward

        # The actual occupied arc is the smaller of the two (should be <=6 for Kaal Sarp)
        if arc1 <= 6:
            start, end = ra_pos, ke_pos
            direction = 1  # forward
        elif arc2 <= 6:
            start, end = ke_pos, ra_pos
            direction = 1
        else:
            start = end = None  # arc too large, not Kaal Sarp

        if start is not None:
            all_planets_between = True
            for pl, ph in planet_house.items():
                if pl in ["Ra", "Ke"]:
                    continue
                pos = ph - 1
                # Check if planet lies within the arc (including start and end? No, nodes are excluded)
                # The arc from start to end moving forward (direction=1) should contain pos.
                if direction == 1:
                    if start < end:
                        if not (start < pos < end):
                            all_planets_between = False
                            break
                    else:  # wrap around
                        if not (pos > start or pos < end):
                            all_planets_between = False
                            break
            if all_planets_between:
                summary = "Kaal Sarp Yoga: All planets hemmed between Rahu-Ketu – Life obstacles, but potential for sudden rise"
                detail = f"- Reason: Kaal Sarp forms when all planets are trapped between Rahu and Ketu's axis, creating karmic restrictions.\n- Direct Outcome: Life struggles, delays in success, but potential breakthroughs after mid-life; remedies include Naga puja."
                problems.append({"summary": summary, "detail": detail})

    # 4. Debilitated Planets (check for Neecha Bhanga cancellation)
    deb_planets = [pl for pl, data in p.items() if data["dignity"] == "Debilitated"]
    # Separate those with Neecha Bhanga from truly debilitated
    truly_deb = [pl for pl in deb_planets if not p[pl].get("neecha_bhanga", False)]
    nb_planets = [pl for pl in deb_planets if p[pl].get("neecha_bhanga", False)]

    if truly_deb:
        full_names = [short_to_full.get(pl, pl) for pl in truly_deb]
        deb_details = []
        for pl in truly_deb:
            sign = p[pl]["sign"]
            if pl == "Me":
                deb_details.append(
                    f"Mercury in {sign}: Intuitive but scattered thinking; communication requires structure."
                )
            elif pl == "Sa":
                deb_details.append(
                    f"Saturn in {sign}: Initial instability, but builds strength through discipline."
                )
            elif pl == "Ju":
                deb_details.append(
                    f"Jupiter in {sign}: Wisdom through practical experience; unconventional growth path."
                )
            elif pl == "Ve":
                deb_details.append(
                    f"Venus in {sign}: Refined tastes developed through effort; love matures with time."
                )
            elif pl == "Ma":
                deb_details.append(
                    f"Mars in {sign}: Energy channeled through emotional intelligence; strategic action."
                )
            elif pl == "Su":
                deb_details.append(
                    f"Sun in {sign}: Ego refined through service; leadership through diplomacy."
                )
            elif pl == "Mo":
                deb_details.append(
                    f"Moon in {sign}: Emotional depth and transformation; intuitive power."
                )
        summary = f"Debilitated Planets ({', '.join(full_names)}): Areas requiring conscious development"
        detail = f"- Reason: A debilitated planet operates differently from its natural expression, requiring adaptation and conscious effort.\n- Direct Outcome: {'; '.join(deb_details)} These placements often produce specialists who master their challenges through sustained effort."
        problems.append({"summary": summary, "detail": detail})

    # Neecha Bhanga planets - different, more positive treatment
    if nb_planets:
        nb_full_names = [short_to_full.get(pl, pl) for pl in nb_planets]
        nb_details = []
        for pl in nb_planets:
            sign = p[pl]["sign"]
            if pl == "Sa":
                nb_details.append(
                    f"Saturn in {sign} (NB): Delayed but powerful after maturity (28-30+); builds exceptional resilience and authority."
                )
            elif pl == "Me":
                nb_details.append(
                    f"Mercury in {sign} (NB): Intuitive intelligence; creative communication style gains recognition over time."
                )
            elif pl == "Ju":
                nb_details.append(
                    f"Jupiter in {sign} (NB): Practical wisdom that proves itself; unconventional dharma path with eventual success."
                )
            elif pl == "Ve":
                nb_details.append(
                    f"Venus in {sign} (NB): Analytical approach to love/art eventually creates refined elegance."
                )
            elif pl == "Ma":
                nb_details.append(
                    f"Mars in {sign} (NB): Strategic courage; emotional intelligence becomes a strength."
                )
            elif pl == "Su":
                nb_details.append(
                    f"Sun in {sign} (NB): Humility transforms into respected leadership; diplomatic authority."
                )
            elif pl == "Mo":
                nb_details.append(
                    f"Moon in {sign} (NB): Deep emotional wisdom; transformative intuition."
                )
        summary = f"Neecha Bhanga Planets ({', '.join(nb_full_names)}): Debilitation cancelled – delayed but powerful"
        detail = f"- Reason: Neecha Bhanga (cancelled debilitation) occurs when supportive factors neutralize the weakness. These planets often give BETTER results than normal planets after initial delays.\n- Direct Outcome: {'; '.join(nb_details)} Key: Results manifest after planet's maturity age; patience and discipline unlock the potential."
        problems.append({"summary": summary, "detail": detail})

    # 5. Pitru Dosha (Sun afflicted by Saturn/Rahu, or Sun in 12th)
    # Affliction = same house (conjunction) OR 7 houses away (mutual opposition/aspect)
    sun_house = planet_house.get("Su", None)
    afflictions = []
    if "Sa" in planet_house and sun_house is not None:
        h_diff = (planet_house["Sa"] - sun_house + 12) % 12
        if h_diff in (0, 6):  # conjunction or direct opposition
            afflictions.append("Saturn")
    if "Ra" in planet_house and sun_house is not None:
        h_diff = (planet_house["Ra"] - sun_house + 12) % 12
        if h_diff in (0, 6):
            afflictions.append("Rahu")
    if sun_house == 12:
        afflictions.append("in 12H")
    if afflictions:
        summary = f"Pitru Dosha (Sun afflicted by {', '.join(afflictions)}): Ancestral issues, father-related challenges"
        detail = f"- Reason: Pitru Dosha arises from Sun's affliction by malefics, indicating unresolved ancestral karma.\n- Direct Outcome: Paternal health problems, family disputes, or luck obstacles; remedies include Shradh rituals."
        problems.append({"summary": summary, "detail": detail})

    # 6. Graha Malika Yoga – All 7 classical planets confined to consecutive houses with no gap.
    _classical = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
    _c_house_set = set()
    for _pl in _classical:
        for _hnum, _plist in h.items():
            if _pl in _plist:
                _c_house_set.add(_hnum)
                break
    _n_classical_houses = len(_c_house_set)
    if _n_classical_houses >= 6 and houses_are_consecutive(_c_house_set):
        summary = (
            f"Graha Malika ({_n_classical_houses} classical planets in consecutive houses): "
            f"Intense, focused life phases, potential imbalances"
        )
        detail = (
            "- Reason: Classical planets in sequential houses concentrate all life energy "
            "into a tight arc – intense achievement in those house themes.\n"
            "- Direct Outcome: Extreme highs/lows in the activated house arc; "
            "strong focus but risk of neglecting opposite-house themes; "
            "balances with simultaneous yogas."
        )
        problems.append({"summary": summary, "detail": detail})

    if not problems:
        problems.append(
            {
                "summary": "No major doshas/problems detected – Generally favorable chart",
                "detail": "",
                "remedies": [],
            }
        )
        return problems

    # ── Attach targeted remedies to each problem ──
    for prob in problems:
        summary = prob["summary"]
        rems = []
        if "Mangal" in summary:
            # Check severity level in summary to assign appropriate remedies
            if "Severe" in summary or "Significant" in summary:
                rems = REMEDIES["Mangal_Severe"]
            elif "Moderate" in summary:
                rems = REMEDIES["Mangal_Moderate"]
            else:  # Mild or Largely Cancelled
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
            # Find which planets are debilitated and add their specific remedies
            for pl_short, key in [
                ("Mercury", "Me"),
                ("Saturn", "Sa"),
                ("Sun", "Su"),
                ("Moon", "Mo"),
                ("Mars", "Ma"),
                ("Jupiter", "Ju"),
                ("Venus", "Ve"),
            ]:
                if pl_short in summary:
                    rems += REMEDIES.get(f"Debilitated_{key}", [])
        # ── Gemstone filter: warn/skip if planet is a functional malefic or combust ──
        # Applied AFTER rems is filled so the full list is available for filtering.
        if "Debilitated" in summary and rems:
            lagna_sign_r = result.get("lagna_sign", "")
            fq_r = FUNCTIONAL_QUALITY.get(lagna_sign_r, {})
            func_malefics = fq_r.get("mal", [])
            # Map each remedy line to the planet it belongs to by tracking which
            # planet's remedy block we are in (remedies appear in the same order
            # as the debilitated planets listed in the summary).
            _deb_order = []
            for ps, pk in [
                ("Mercury", "Me"),
                ("Saturn", "Sa"),
                ("Sun", "Su"),
                ("Moon", "Mo"),
                ("Mars", "Ma"),
                ("Jupiter", "Ju"),
                ("Venus", "Ve"),
            ]:
                if ps in summary:
                    _deb_order.append(pk)
            # Each planet's REMEDIES block has the same length → partition rems
            _block_size = {}
            for pk in _deb_order:
                _block_size[pk] = len(REMEDIES.get(f"Debilitated_{pk}", []))
            filtered = []
            _rem_idx = 0
            for pk in _deb_order:
                _planet_rems = rems[_rem_idx : _rem_idx + _block_size[pk]]
                _rem_idx += _block_size[pk]
                is_malefic = pk in func_malefics
                is_combust = result.get("planets", {}).get(pk, {}).get("combust", False)
                for rem_line in _planet_rems:
                    is_gem_line = any(
                        g in rem_line
                        for g in [
                            "sapphire",
                            "emerald",
                            "pearl",
                            "coral",
                            "ruby",
                            "diamond",
                            "moonstone",
                            "gemstone",
                        ]
                    )
                    if is_gem_line and is_malefic:
                        filtered.append(
                            f"{rem_line} [⚠ SKIP – {pk} is a functional malefic for "
                            f"{lagna_sign_r} lagna; wearing this gem will amplify harm]"
                        )
                    elif is_gem_line and is_combust:
                        filtered.append(
                            f"{rem_line} [⚠ CAUTION – {pk} is currently combust; "
                            f"wait for combustion to clear before using this gemstone]"
                        )
                    else:
                        filtered.append(rem_line)
            rems = filtered
        prob["remedies"] = rems

    return problems
