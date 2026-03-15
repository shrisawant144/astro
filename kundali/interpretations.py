# interpretations.py
"""
Interpretation functions for divisional charts (D9, D7, D10) and aspects.
Provides detailed textual analysis of planetary placements and their implications.
"""

from constants import (
    short_to_full,
    zodiac_signs,
    sign_lords,
    HOUSE_SIGNIFICATIONS,
    PLANET_ASPECT_THEMES,
    FUNCTIONAL_QUALITY,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
)
from utils import get_dignity


def get_aspect_quality_score(
    planet, lagna_sign, dignity, is_combust=False, is_retro=False
):
    """Calculate aspect quality score for a planet.
    Returns: (score, nature_label)
      score > 0 = beneficial influence
      score < 0 = challenging influence
      score = 0 = neutral
    nature_label describes the functional classification.
    """
    fq = FUNCTIONAL_QUALITY.get(lagna_sign, {})

    # Base score from functional nature
    if planet in fq.get("ben", []):
        base = 2
        nature_label = "func. benefic"
    elif planet == fq.get("yk"):
        base = 3
        nature_label = "Yogakaraka"
    elif planet in fq.get("mal", []):
        base = -2
        nature_label = "func. malefic"
    elif planet in fq.get("maraka", []):
        base = -1
        nature_label = "Maraka"
    elif planet in fq.get("mixed", []):
        base = 0
        nature_label = "mixed"
    else:
        # Default to natural classification
        if planet in NATURAL_BENEFICS:
            base = 1
            nature_label = "nat. benefic"
        else:
            base = -1
            nature_label = "nat. malefic"

    # Dignity modifier (strength override)
    if dignity == "Exalt":
        base += 2  # Exaltation significantly improves results
    elif dignity == "Own":
        base += 1  # Own sign is stable and positive
    elif dignity == "Friend":
        pass  # Friendly sign: no modifier (slight positive, but not counted)
    elif dignity == "Enemy":
        base -= 1  # Enemy sign weakens planet's delivery
    elif dignity == "Debilitated":
        base -= 1  # Debilitation weakens (but doesn't fully negate functional nature)

    # Combustion weakens significantly
    if is_combust:
        base -= 1

    return base, nature_label


def interpret_aspects(result):
    """Full Drishti analysis per house with strength, nature, and life outcomes.
    Uses functional nature + dignity for balanced assessment instead of just natural benefic/malefic."""
    aspects = result["aspects"]
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)
    planets_data = result["planets"]
    out = []

    strength_labels = {
        "7th": "100%",
        "4": "50%",
        "8": "75%",
        "5": "75%",
        "9": "75%",
        "3": "25%",
        "10": "75%",
        "5/9": "75%",
    }

    for h in range(1, 13):
        if not aspects[h]:
            continue
        house_sign = zodiac_signs[(lagna_idx + h - 1) % 12]
        signif = HOUSE_SIGNIFICATIONS[h]
        out.append(f"\nHouse {h:2d} ({house_sign}) – {signif.split(',')[0]}:")
        out.append(f"  Significations: {signif}")

        total_score = 0
        aspect_details = []

        for asp in aspects[h]:
            parts = asp.split("-")
            pl = parts[0]
            asp_type = parts[1] if len(parts) > 1 else "7th"

            pl_data = planets_data.get(pl, {})
            dig = pl_data.get("dignity", "") if pl_data else ""
            retro = pl_data.get("retro", False) if pl_data else False
            combust = pl_data.get("combust", False) if pl_data else False

            # Strength description
            if dig == "Exalt":
                strength_note = "Exalted – very strong"
            elif dig == "Own":
                strength_note = "Own sign – strong"
            elif dig == "Debilitated":
                # Check for Neecha Bhanga - if cancelled, use different wording
                if pl_data and pl_data.get("neecha_bhanga", False):
                    strength_note = (
                        "Debilitated (NB) – delayed but powerful after maturity"
                    )
                else:
                    strength_note = "Debilitated – requires conscious development"
            elif combust:
                strength_note = "Combust – weakened by Sun"
            elif retro:
                strength_note = "Retrograde – intensified"
            else:
                strength_note = "Normal strength"

            # Get functional nature score
            score, nature_label = get_aspect_quality_score(
                pl, lagna_sign, dig, combust, retro
            )
            total_score += score

            asp_pct = strength_labels.get(asp_type, "100%")
            pl_full = short_to_full.get(pl, pl)

            theme = PLANET_ASPECT_THEMES.get(pl, {}).get(
                asp_type,
                f"{pl_full} brings its significations into this house.",
            )

            out.append(
                f"  • {pl_full:8} ({asp_type} aspect, {asp_pct}, {nature_label}, {strength_note})"
            )
            out.append(f"    → {theme}")

        # Net summary based on total score
        h_area = signif.split(",")[0]
        if total_score >= 3:
            out.append(
                f"  ✓ Net: Strongly positive influences – {h_area} is well-supported; results come naturally."
            )
        elif total_score >= 1:
            out.append(
                f"  ✓ Net: Positive overall – {h_area} benefits from supportive planetary energy."
            )
        elif total_score >= -1:
            out.append(
                f"  ~ Net: Mixed influences – {h_area} has balanced energies; results depend on dasha periods."
            )
        elif total_score >= -3:
            out.append(
                f"  ~ Net: Multiple planetary influences – {h_area} has strong but complex energy; "
                f"conscious direction during benefic dashas brings best results."
            )
        else:
            out.append(
                f"  ~ Net: Concentrated planetary energy in {h_area}; active management and benefic "
                f"dashas recommended for optimal outcomes."
            )

    return out


def interpret_navamsa(result):
    """Full D9 Navamsa analysis – marriage, spouse, dharma, inner soul."""
    navamsa = result["navamsa"]
    planets_data = result["planets"]
    gender = result.get("gender", "Male")
    spouse_term = "husband" if gender == "Female" else "wife"
    spouse_karaka = "Jupiter" if gender == "Female" else "Venus"
    spouse_karaka_short = "Ju" if gender == "Female" else "Ve"

    out = []
    out.append(
        f"(D9 reveals {spouse_term} character, marriage quality, dharmic path, and "
        "the soul's evolutionary direction. D1 shows the promise; D9 confirms or modifies it. "
        "Strong D1 + strong D9 = highly reliable results; strong D1 + weak D9 = fluctuating results; "
        f"weak D1 + strong D9 = gradual improvement over time. For {gender}, {spouse_karaka} is the primary karaka for {spouse_term}.)"
    )

    # Gender-specific planet meanings
    planet_d9_meanings_male = {
        "Su": "Soul authority: wife may have Sun-like qualities (leadership, pride). Dharma path involves service, governance, or father-like responsibility.",
        "Mo": "Emotional soul: deep emotional bond with wife; marriage is nurturing. Inner self driven by security, mother, and public approval.",
        "Ma": "Passionate soul: wife is energetic, ambitious, possibly athletic or bold. Marriage has intense passion; conflicts must be managed consciously.",
        "Me": "Intellectual soul: wife is communicative, witty, analytical. Marriage thrives on mental connection; dharma through teaching or trade.",
        "Ju": "Wisdom soul: wife is wise, spiritual, generous. Jupiter's D9 dignity determines dharmic blessings; strong = growth, weak = obstacles.",
        "Ve": "Artistic soul (WIFE KARAKA): wife is beautiful, artistic, loving, comfort-seeking. Venus's D9 dignity is crucial for marital harmony and satisfaction.",
        "Sa": "Karmic soul: wife may be older, serious, disciplined, or from a different background. Marriage has karmic weight; deep loyalty over time.",
        "Ra": "Unconventional soul: wife may be foreign, unconventional, or connected by past-life karma. Marriage outside norms; obsessive at times.",
        "Ke": "Spiritual soul: previous-life karmic bond with wife; partner may be deeply spiritual, detached, or intuitive. Marriage is meaningful but impersonal.",
    }

    planet_d9_meanings_female = {
        "Su": "Soul authority: husband may have Sun-like qualities (leadership, pride, authority). Dharma path involves service, governance, or father-like responsibility.",
        "Mo": "Emotional soul: deep emotional bond with husband; marriage is nurturing. Inner self driven by security, mother, and public approval.",
        "Ma": "Passionate soul: husband is energetic, ambitious, athletic or bold. Mars indicates husband's courage and vitality.",
        "Me": "Intellectual soul: husband is communicative, witty, analytical. Marriage thrives on mental connection; dharma through teaching or trade.",
        "Ju": "Wisdom soul (HUSBAND KARAKA): husband is wise, spiritual, generous. Jupiter's D9 dignity is crucial for marital harmony and husband's qualities.",
        "Ve": "Artistic soul: husband appreciates beauty, arts, and comfort. Strong Venus gives loving marriage and material comforts.",
        "Sa": "Karmic soul: husband may be older, serious, disciplined, or from a different background. Marriage has karmic weight; deep loyalty over time.",
        "Ra": "Unconventional soul: husband may be foreign, unconventional, or connected by past-life karma. Marriage outside norms; obsessive at times.",
        "Ke": "Spiritual soul: previous-life karmic bond with husband; partner may be deeply spiritual, detached, or intuitive. Marriage is meaningful but impersonal.",
    }

    planet_d9_meanings = (
        planet_d9_meanings_female if gender == "Female" else planet_d9_meanings_male
    )

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    for pl in order:
        if pl not in navamsa:
            continue
        d = navamsa[pl]
        nav_sign = d["sign"]
        nav_dig = get_dignity(pl, nav_sign)
        dig_note = f" [{nav_dig}]" if nav_dig else ""
        pl_full = short_to_full.get(pl, pl)
        out.append(f"  {pl_full:9} in {nav_sign:12} {d['deg']:5.2f}°{dig_note}")
        out.append(f"    → {planet_d9_meanings[pl]}")
        if nav_dig == "Debilitated":
            # Softer, more nuanced language for D9 debilitation
            if pl == "Ju":
                out.append(
                    f"    ⚠ Debilitated in D9: Jupiter's marriage/dharma significations require "
                    f"spiritual growth and conscious effort; wisdom develops through challenges."
                )
            elif pl == "Ve":
                out.append(
                    f"    ⚠ Debilitated in D9: Venus's marriage significations require refinement; "
                    f"love matures through service and practical effort."
                )
            elif pl == "Mo":
                out.append(
                    f"    ⚠ Debilitated in D9: Emotional fulfillment in marriage requires "
                    f"transformation; deep bonding develops over time."
                )
            else:
                out.append(
                    f"    ⚠ Debilitated in D9: {pl_full}'s marriage/dharma significations require "
                    f"conscious development; strengthen through D1 placement or remedies."
                )
        elif nav_dig in ("Exalt", "Own"):
            out.append(
                f"    ✓ {nav_dig} in D9: {pl_full}'s significations are powerfully reliable "
                f"in marriage and dharmic areas."
            )

    # Vargottama check
    vargottama = [
        short_to_full.get(pl, pl)
        for pl in order
        if pl in planets_data
        and pl in navamsa
        and planets_data[pl]["sign"] == navamsa[pl]["sign"]
    ]
    out.append("\n  Vargottama (same sign in D1 and D9 – doubled strength):")
    if vargottama:
        out.append(
            f"  → {', '.join(vargottama)}: These planets are extremely stable and reliable "
            f"in their results; their placement in D1 is fully confirmed by D9."
        )
    else:
        out.append("  → No Vargottama planets.")

    # Best and worst D9 placements
    exalt_d9 = [
        short_to_full.get(pl, pl)
        for pl in order
        if pl in navamsa and get_dignity(pl, navamsa[pl]["sign"]) == "Exalt"
    ]
    deb_d9 = [
        short_to_full.get(pl, pl)
        for pl in order
        if pl in navamsa and get_dignity(pl, navamsa[pl]["sign"]) == "Debilitated"
    ]
    if exalt_d9:
        out.append(
            f"  ✓ Exalted in D9: {', '.join(exalt_d9)} – Marriage/dharma blessings are magnified."
        )
    if deb_d9:
        out.append(
            f"  ⚠ Debilitated in D9: {', '.join(deb_d9)} – D1 promise may fluctuate; conscious effort helps stabilise results."
        )

    # Gender-specific spouse karaka analysis
    if gender == "Female":
        # Jupiter is the primary husband karaka for females
        if "Ju" in navamsa:
            ju_d9_sign = navamsa["Ju"]["sign"]
            ju_d9_dig = get_dignity("Ju", ju_d9_sign)
            if ju_d9_dig in ("Exalt", "Own"):
                ju_note = (
                    "Excellent – husband will be wise, prosperous, and supportive."
                )
            elif ju_d9_dig == "Debilitated":
                ju_note = "Debilitated – husband's qualities may require patience; Jupiter remedies can help."
            else:
                ju_note = "Moderate – good husband qualities but may need conscious nurturing."
            dig_tag = f", {ju_d9_dig}" if ju_d9_dig else ""
            out.append(
                f"\n  Jupiter in D9 ({ju_d9_sign}{dig_tag}) [HUSBAND KARAKA]: {ju_note}"
            )
        # Also check Venus for marital harmony
        if "Ve" in navamsa:
            ve_d9_sign = navamsa["Ve"]["sign"]
            ve_d9_dig = get_dignity("Ve", ve_d9_sign)
            if ve_d9_dig in ("Exalt", "Own"):
                ve_note = "Excellent – beauty, love, and harmony in marriage."
            elif ve_d9_dig == "Debilitated":
                ve_note = "Debilitated – marital romance may require extra effort."
            else:
                ve_note = "Moderate – marriage has affection but may need conscious nurturing."
            dig_tag = f", {ve_d9_dig}" if ve_d9_dig else ""
            out.append(
                f"  Venus in D9 ({ve_d9_sign}{dig_tag}) [Marital Harmony]: {ve_note}"
            )
    else:
        # Venus is the primary wife karaka for males
        if "Ve" in navamsa:
            ve_d9_sign = navamsa["Ve"]["sign"]
            ve_d9_dig = get_dignity("Ve", ve_d9_sign)
            if ve_d9_dig in ("Exalt", "Own"):
                ve_note = (
                    "Excellent – wife will be beautiful, loving, and harmony-loving."
                )
            elif ve_d9_dig == "Debilitated":
                ve_note = "Debilitated – wife's qualities may require patience; Venus remedies can help."
            else:
                ve_note = "Moderate – marriage has affection but may need conscious nurturing."
            dig_tag = f", {ve_d9_dig}" if ve_d9_dig else ""
            out.append(
                f"\n  Venus in D9 ({ve_d9_sign}{dig_tag}) [WIFE KARAKA]: {ve_note}"
            )
    return out


def interpret_d7(result):
    """Full D7 Saptamsa analysis – children, progeny, generative energy."""
    d7 = result["d7"]
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    fifth_sign = zodiac_signs[(lagna_idx + 4) % 12]
    fifth_lord = sign_lords[fifth_sign]
    out = []
    out.append(
        "(D7 reveals potential for children, timing of progeny, their "
        "nature and quality. Jupiter and 5th lord are the primary karakas.)"
    )

    planet_d7_meanings = {
        "Su": "Progeny will have leadership, pride, and authority – strongly willed, possibly in government or power roles. Father's legacy passed to children.",
        "Mo": "Nurturing, sensitive children with strong emotional intelligence. Close mother-child bond. Children may work in public, nurturing, or creative fields.",
        "Ma": "Energetic, bold, athletic children – courageous and competitive. Possibly more sons. Active and passionate generative force.",
        "Me": "Intelligent, communicative, analytical children. Academic excellence likely. Children suited to communication, IT, trade, or education careers.",
        "Ju": "Wise, fortunate, well-educated children – the most auspicious D7 planet. Abundant blessings for progeny; children bring joy and prosperity.",
        "Ve": "Artistic, beautiful, socially gifted children. Strong aesthetic sensibility. Children may excel in arts, design, fashion, or diplomacy.",
        "Sa": "Fewer children or delays; disciplined and serious progeny. Children may face early hardships but build strong characters. Karmic parent-child bond.",
        "Ra": "Unconventional, innovative children – possibly gifted in technology, foreign fields. Unusual conception circumstances or unexpected arrival.",
        "Ke": "Spiritually oriented or intuitive children; past-life karmic connection. Children may show detachment from worldly life or mystical inclinations.",
    }

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    for pl in order:
        if pl not in d7:
            continue
        d = d7[pl]
        d7_sign = d["sign"]
        d7_dig = get_dignity(pl, d7_sign)
        dig_note = f" [{d7_dig}]" if d7_dig else ""
        pl_full = short_to_full.get(pl, pl)
        out.append(f"  {pl_full:9} in {d7_sign:12} {d['deg']:5.2f}°{dig_note}")
        out.append(f"    → {planet_d7_meanings[pl]}")
        if d7_dig == "Debilitated":
            out.append(
                f"    ⚠ Debilitated in D7: challenges to above; remedies (Jupiter mantra, charity) advised."
            )
        elif d7_dig in ("Exalt", "Own"):
            out.append(
                f"    ✓ {d7_dig} in D7: above significations fully activated and reliable."
            )

    # Jupiter in D7 summary
    out.append(
        f"\n  Key Karakas: Jupiter (natural) + 5th lord {short_to_full.get(fifth_lord, fifth_lord)} (functional)"
    )
    if "Ju" in d7:
        ju_sign = d7["Ju"]["sign"]
        ju_dig = get_dignity("Ju", ju_sign)
        if ju_dig == "Exalt":
            out.append(
                f"  ✓ Jupiter Exalted in D7 ({ju_sign}) – Excellent, abundant, and wise progeny strongly indicated."
            )
        elif ju_dig == "Own":
            out.append(
                f"  ✓ Jupiter in Own sign in D7 ({ju_sign}) – Good number of children; wise and fortunate progeny."
            )
        elif ju_dig == "Debilitated":
            out.append(
                f"  ⚠ Jupiter Debilitated in D7 ({ju_sign}) – Progeny challenges; possible delays or health issues for children; remedies essential."
            )
        else:
            out.append(
                f"  Jupiter in {ju_sign} in D7 – Moderate progeny; timing through Jupiter/5th lord Dasha is key."
            )
    return out


def interpret_d10(result):
    """Full D10 Dasamsa analysis – career, profession, public life."""
    d10 = result["d10"]
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    tenth_sign = zodiac_signs[(lagna_idx + 9) % 12]
    tenth_lord = sign_lords[tenth_sign]
    out = []
    out.append(
        "(D10 reveals true professional destiny, career field, authority level, "
        "and the quality of public life. Sun, Saturn, and 10th lord are primary karakas.)"
    )

    planet_d10_meanings = {
        "Su": "Government, administration, politics, leadership roles, father's career influence. Sun strong in D10 = fame, authority, and recognition.",
        "Mo": "Public-facing work, healthcare, hospitality, food, real estate, business involving masses. Fluctuating but popular career.",
        "Ma": "Engineering, military, surgery, real estate, sports, competitive and technical fields. Mars strong = decisive, results-driven professional.",
        "Me": "Communication, writing, IT, education, trade, accounts, media, analysis. Mercury strong = skilled, versatile professional.",
        "Ju": "Teaching, law, counseling, finance, philosophy, management, spiritual guidance. Jupiter strong in D10 = respected, morally driven career.",
        "Ve": "Arts, entertainment, fashion, luxury goods, beauty industry, hospitality, diplomacy. Venus strong = glamorous or aesthetics-driven profession.",
        "Sa": "Service sector, labor, judiciary, mining, research, long-term technical work, social welfare. Saturn strong = career builder who earns through sustained effort.",
        "Ra": "Foreign companies, cutting-edge technology, unconventional professions, film, mass politics, import/export. Rahu = career outside traditional norms.",
        "Ke": "Research, spirituality, healing arts, behind-the-scenes work, mathematics, programming. Ketu = expertise in niche or hidden fields.",
    }

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    for pl in order:
        if pl not in d10:
            continue
        d = d10[pl]
        d10_sign = d["sign"]
        d10_dig = get_dignity(pl, d10_sign)
        dig_note = f" [{d10_dig}]" if d10_dig else ""
        pl_full = short_to_full.get(pl, pl)
        out.append(f"  {pl_full:9} in {d10_sign:12} {d['deg']:5.2f}°{dig_note}")
        out.append(f"    → {planet_d10_meanings[pl]}")
        if d10_dig == "Debilitated":
            out.append(
                f"    ⚠ Debilitated in D10: professional obstacles in this area; choose field aligned with planet's strength elsewhere."
            )
        elif d10_dig in ("Exalt", "Own"):
            out.append(
                f"    ✓ {d10_dig} in D10: career success in this domain is strongly supported."
            )

    # 10th lord summary
    out.append(
        f"\n  Primary Karaka: Sun (fame/authority) | Functional 10th Lord: {short_to_full.get(tenth_lord, tenth_lord)}"
    )
    if tenth_lord in d10:
        tl_sign = d10[tenth_lord]["sign"]
        tl_dig = get_dignity(tenth_lord, tl_sign)
        if tl_dig in ("Exalt", "Own"):
            out.append(
                f"  ✓ 10th lord ({short_to_full.get(tenth_lord, tenth_lord)}) {tl_dig} in D10 ({tl_sign}) – Peak career success; prominence and rise to authority highly indicated."
            )
        elif tl_dig == "Debilitated":
            out.append(
                f"  ⚠ 10th lord Debilitated in D10 ({tl_sign}) – Career hurdles; switching to the planet's natural field (see above) and remedies help significantly."
            )
        else:
            out.append(
                f"  10th lord in {tl_sign} in D10 – Career grows steadily through hard work; major rise during 10th lord's Mahadasha."
            )

    # D10 10th lord house placement analysis (which D10 house does the 10th lord occupy?)
    if tenth_lord in d10:
        tl_d10_sign = d10[tenth_lord]["sign"]
        # In D10 whole-sign: find what house the 10th lord lands in relative to D1 lagna
        tl_d10_sign_idx = zodiac_signs.index(tl_d10_sign)
        tl_d10_house = ((tl_d10_sign_idx - lagna_idx) % 12) + 1
        D10_HOUSE_MEANINGS = {
            1: "Career strongly tied to personal identity; self-made professional; entrepreneurship.",
            2: "Career involves wealth management, family business, speech/teaching, banking, food industry.",
            3: "Career in communication, media, writing, short-distance travel, sales, publishing.",
            4: "Career in real estate, vehicles, education, homeland-related fields; comfort-oriented work.",
            5: "Career in creative fields, education, children-related, speculation, entertainment, politics.",
            6: "Career in service, healthcare, law, defence, competition; daily routines define growth.",
            7: "Career through partnerships, business, consulting, diplomacy, foreign trade.",
            8: "Career involves research, insurance, occult, transformative work; ups and downs in profession.",
            9: "Career in teaching, religion, law, philosophy, long-distance travel, publishing; father's influence.",
            10: "Strongest placement – 10th lord in 10th house of D10: Raj Yoga for career; fame and authority.",
            11: "Career brings large gains, social network; fulfillment of professional aspirations.",
            12: "Career in foreign lands, hospitals, spiritual institutions, charity; behind-the-scenes roles.",
        }
        house_meaning = D10_HOUSE_MEANINGS.get(
            tl_d10_house, f"10th lord in House {tl_d10_house} of D10."
        )
        out.append(f"  10th lord in D10 House {tl_d10_house}: {house_meaning}")

    # Sun in D10
    if "Su" in d10:
        su_dig = get_dignity("Su", d10["Su"]["sign"])
        if su_dig in ("Exalt", "Own"):
            out.append(
                f"  ✓ Sun ({su_dig}) in D10 – Strong public image, authority, and social recognition."
            )
        elif su_dig == "Debilitated":
            out.append(
                f"  ⚠ Sun Debilitated in D10 – Ego conflicts with authority; avoid confrontations with superiors; build reputation quietly."
            )

    # Exalted/debilitated summary
    exalt_d10 = [
        short_to_full.get(pl, pl)
        for pl in order
        if pl in d10 and get_dignity(pl, d10[pl]["sign"]) == "Exalt"
    ]
    deb_d10 = [
        short_to_full.get(pl, pl)
        for pl in order
        if pl in d10 and get_dignity(pl, d10[pl]["sign"]) == "Debilitated"
    ]
    if exalt_d10:
        out.append(
            f"  ✓ Exalted in D10: {', '.join(exalt_d10)} – Career domains of these planets thrive."
        )
    if deb_d10:
        out.append(
            f"  ⚠ Debilitated in D10: {', '.join(deb_d10)} – Avoid career fields solely dependent on these planets."
        )
    return out


def calculate_functional_strength_index(result, planet):
    """
    Calculate a nuanced Functional Classification Strength Index (0-100) for a planet.

    Instead of binary benefic/malefic labels, this provides a weighted score:
    - Base functional status (benefic=70, malefic=30, mixed=50)
    - D1 dignity adjustment (exalt +20, own +15, debilitated -15)
    - D9 dignity adjustment (exalt +10, own +8, debilitated -8)
    - House placement (+/- based on kendra/trikona/dusthana)
    - Benefic aspects received (+5 each)
    - Malefic aspects received (-5 each)

    Returns: dict with score, classification, and modifying factors
    """
    lagna_sign = result["lagna_sign"]
    fq = FUNCTIONAL_QUALITY.get(lagna_sign, {})
    planets_data = result.get("planets", {})
    navamsa = result.get("navamsa", {})
    houses = result.get("houses", {})
    aspects = result.get("aspects", {})

    # Base score based on functional classification
    if planet in fq.get("ben", []):
        base = 70
        base_class = "Benefic"
    elif planet in fq.get("mal", []):
        base = 30
        base_class = "Malefic"
    elif planet in fq.get("maraka", []):
        base = 35
        base_class = "Maraka"
    elif planet in fq.get("mixed", []):
        base = 50
        base_class = "Mixed"
    else:
        base = 50
        base_class = "Neutral"

    # Yogakaraka bonus
    yk_bonus = 0
    if fq.get("yk") == planet:
        yk_bonus = 20
        base_class = "Yogakaraka"

    # D1 dignity adjustment
    d1_adj = 0
    d1_reason = ""
    if planet in planets_data:
        dignity = planets_data[planet].get("dignity", "")
        if dignity == "Exalt":
            d1_adj = 20
            d1_reason = "D1 Exalted"
        elif dignity == "Own":
            d1_adj = 15
            d1_reason = "D1 Own Sign"
        elif dignity == "Debilitated":
            d1_adj = -15
            d1_reason = "D1 Debilitated"
            # Check for neecha bhanga
            if planets_data[planet].get("neecha_bhanga", False):
                d1_adj = -5  # Reduced penalty
                d1_reason = "D1 Debilitated (NB)"
        elif dignity == "Friend":
            d1_adj = 5
            d1_reason = "D1 Friendly Sign"
        elif dignity == "Enemy":
            d1_adj = -5
            d1_reason = "D1 Enemy Sign"

    # D9 dignity adjustment
    d9_adj = 0
    d9_reason = ""
    if planet in navamsa:
        d9_sign = navamsa[planet].get("sign", "")
        d9_dignity = get_dignity(planet, d9_sign)
        if d9_dignity == "Exalt":
            d9_adj = 10
            d9_reason = "D9 Exalted"
        elif d9_dignity == "Own":
            d9_adj = 8
            d9_reason = "D9 Own"
        elif d9_dignity == "Debilitated":
            d9_adj = -8
            d9_reason = "D9 Debilitated"
        elif d9_dignity == "Friend":
            d9_adj = 3
            d9_reason = "D9 Friendly Sign"
        elif d9_dignity == "Enemy":
            d9_adj = -3
            d9_reason = "D9 Enemy Sign"

    # House placement adjustment
    house_adj = 0
    house_reason = ""
    for h, plist in houses.items():
        if planet in plist:
            if h in [1, 4, 7, 10]:  # Kendras - good for all planets
                house_adj = 5
                house_reason = f"H{h} Kendra"
            elif h in [5, 9]:  # Trikonas - great for benefics
                house_adj = 8 if base >= 50 else 3
                house_reason = f"H{h} Trikona"
            elif h in [6, 8, 12]:  # Dusthanas - challenging
                house_adj = -5 if base >= 50 else 3  # Malefics do okay in dusthanas
                house_reason = f"H{h} Dusthana"
            elif h in [2, 11]:  # Wealth houses
                house_adj = 4
                house_reason = f"H{h} Wealth"
            elif h == 3:  # Upachaya
                house_adj = 2
                house_reason = f"H{h} Upachaya"
            break

    # Calculate final score
    final_score = base + yk_bonus + d1_adj + d9_adj + house_adj
    final_score = max(0, min(100, final_score))

    # Determine effective classification
    if final_score >= 80:
        effective_class = "Strong Benefic"
    elif final_score >= 65:
        effective_class = "Conditional Benefic"
    elif final_score >= 50:
        effective_class = "Neutral-Positive"
    elif final_score >= 35:
        effective_class = "Conditional Malefic"
    else:
        effective_class = "Functional Malefic"

    # Build modifiers list
    modifiers = []
    if yk_bonus:
        modifiers.append("Yogakaraka")
    if d1_reason:
        modifiers.append(d1_reason)
    if d9_reason:
        modifiers.append(d9_reason)
    if house_reason:
        modifiers.append(house_reason)

    return {
        "score": final_score,
        "base_class": base_class,
        "effective_class": effective_class,
        "modifiers": modifiers,
    }
