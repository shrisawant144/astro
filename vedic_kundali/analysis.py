# Analysis Module
# Interpretation functions for aspects, navamsa, d7, d10

from constants import (
    zodiac_signs,
    short_to_full,
    FUNCTIONAL_QUALITY,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
    HOUSE_SIGNIFICATIONS,
    sign_lords,
)
from astro_utils import get_dignity


# ────────────────────────────────────────────────
# Functional Strength Index
# ────────────────────────────────────────────────
def calculate_functional_strength_index(result, planet):
    """Calculate a nuanced Functional Classification Strength Index (0-100)."""
    lagna_sign = result["lagna_sign"]
    fq = FUNCTIONAL_QUALITY.get(lagna_sign, {})
    planets_data = result.get("planets", {})
    navamsa = result.get("navamsa", {})
    houses = result.get("houses", {})
    
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
            if planets_data[planet].get("neecha_bhanga", False):
                d1_adj = -5
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
            if h in [1, 4, 7, 10]:
                house_adj = 5
                house_reason = f"H{h} Kendra"
            elif h in [5, 9]:
                house_adj = 8 if base >= 50 else 3
                house_reason = f"H{h} Trikona"
            elif h in [6, 8, 12]:
                house_adj = -5 if base >= 50 else 3
                house_reason = f"H{h} Dusthana"
            elif h in [2, 11]:
                house_adj = 4
                house_reason = f"H{h} Wealth"
            elif h == 3:
                house_adj = 2
                house_reason = f"H{h} Upachaya"
            break
    
    # Final score
    final_score = base + yk_bonus + d1_adj + d9_adj + house_adj
    final_score = max(0, min(100, final_score))
    
    # Effective classification
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
    
    # Modifiers list
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
        "modifiers": modifiers
    }


# ────────────────────────────────────────────────
# Aspect Quality Score
# ────────────────────────────────────────────────
def get_aspect_quality_score(planet, lagna_sign, dignity, is_combust=False, is_retro=False):
    """Calculate aspect quality score for a planet."""
    fq = FUNCTIONAL_QUALITY.get(lagna_sign, {})
    
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
        if planet in NATURAL_BENEFICS:
            base = 1
            nature_label = "nat. benefic"
        else:
            base = -1
            nature_label = "nat. malefic"
    
    if dignity == "Exalt":
        base += 2
    elif dignity == "Own":
        base += 1
    elif dignity == "Enemy":
        base -= 1
    elif dignity == "Debilitated":
        base -= 1
    
    if is_combust:
        base -= 1
    
    return base, nature_label


# ────────────────────────────────────────────────
# Planet Aspect Themes
# ────────────────────────────────────────────────
PLANET_ASPECT_THEMES = {
    "Su": {
        "7th": "Sun casts its authority and ego here – leadership potential; father-figures and government influence; pride may cause friction.",
    },
    "Mo": {
        "7th": "Moon's reflective, nurturing energy touches this house – strong emotional sensitivity; fluctuating results; public and maternal influence.",
    },
    "Ma": {
        "7th": "Mars fires this house with energy, ambition, and aggression – disputes possible but also bold initiative and protection.",
        "4": "Mars' 4th aspect energises home/property themes – real estate gains possible; family arguments; drive in educational pursuits.",
        "8": "Mars' full 8th aspect (75%) activates transformation and risk – sudden events, occult interest, accidents; surgery or research fields.",
    },
    "Me": {
        "7th": "Mercury brings intellect and communication to this house – business acumen, analytical energy, youthful and witty expression.",
    },
    "Ju": {
        "7th": "Jupiter's powerful full aspect (100%) blesses and expands this house – wisdom, prosperity, dharmic protection, and divine grace.",
        "5": "Jupiter's 5th aspect (75%) is deeply auspicious – wisdom, children, creativity, intelligence, and past-karma resolution richly blessed.",
        "9": "Jupiter's 9th aspect (75%) bestows dharma, luck, and spiritual blessings – father, guru, and long-distance good fortune.",
    },
    "Ve": {
        "7th": "Venus pours beauty, harmony, love, and material comforts into this house – artistic gifts, refined partnerships.",
    },
    "Sa": {
        "7th": "Saturn's disciplining aspect (100%) creates karmic tests and delays here – slow but lasting results; serious, dutiful outcomes.",
        "3": "Saturn's 3rd aspect (25%) adds persistent caution to communication and courage – methodical, hard-working energy; slow siblings/journeys.",
        "10": "Saturn's powerful 10th aspect (75%) enforces discipline in career and authority – delays early but eventual recognition and structured success.",
    },
    "Ra": {
        "7th": "Rahu amplifies desires and brings unconventional, foreign influences to this house – obsession, illusion, sudden twists.",
        "5/9": "Rahu's 5th/9th axis activates karmic obsessions – unusual circumstances in children, creativity, luck, and dharma themes.",
    },
    "Ke": {
        "7th": "Ketu brings detachment, past-karma, and spiritual insights to this house – dissolution of illusions; mystical or karmic events.",
        "5/9": "Ketu's 5th/9th axis awakens past-life karma – spiritual lessons in children, creativity, luck, dharma, and higher learning.",
    },
}


# ────────────────────────────────────────────────
# Interpret Aspects
# ────────────────────────────────────────────────
def interpret_aspects(result):
    """Full Drishti analysis per house."""
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
                if pl_data and pl_data.get("neecha_bhanga", False):
                    strength_note = "Debilitated (NB) – delayed but powerful"
                else:
                    strength_note = "Debilitated – requires development"
            elif combust:
                strength_note = "Combust – weakened by Sun"
            elif retro:
                strength_note = "Retrograde – intensified"
            else:
                strength_note = "Normal strength"

            score, nature_label = get_aspect_quality_score(pl, lagna_sign, dig, combust, retro)
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

        h_area = signif.split(",")[0]
        if total_score >= 3:
            out.append(f"  ✓ Net: Strongly positive influences – {h_area} is well-supported.")
        elif total_score >= 1:
            out.append(f"  ✓ Net: Positive overall – {h_area} benefits from supportive energy.")
        elif total_score >= -1:
            out.append(f"  ~ Net: Mixed influences – {h_area} has balanced energies.")
        elif total_score >= -3:
            out.append(f"  ~ Net: Multiple influences – {h_area} has strong but complex energy.")
        else:
            out.append(f"  ~ Net: Concentrated energy in {h_area}; active management recommended.")

    return out


# ────────────────────────────────────────────────
# Interpret Navamsa (D9)
# ────────────────────────────────────────────────
def interpret_navamsa(result):
    """Full D9 Navamsa analysis – marriage, spouse, dharma."""
    navamsa = result["navamsa"]
    planets_data = result["planets"]
    gender = result.get("gender", "Male")
    
    spouse_term = "husband" if gender == "Female" else "wife"
    spouse_karaka = "Jupiter" if gender == "Female" else "Venus"
    spouse_karaka_short = "Ju" if gender == "Female" else "Ve"
    
    out = []
    out.append(f"(D9 reveals {spouse_term} character, marriage quality, dharmic path. "
               "D1 shows the promise; D9 confirms or modifies it.)")

    planet_d9_meanings_male = {
        "Su": "Soul authority: wife may have Sun-like qualities.",
        "Mo": "Emotional soul: deep emotional bond with wife.",
        "Ma": "Passionate soul: wife is energetic, ambitious.",
        "Me": "Intellectual soul: wife is communicative, witty.",
        "Ju": "Wisdom soul: wife is wise, spiritual, generous. Jupiter's D9 dignity crucial.",
        "Ve": "Artistic soul (WIFE KARAKA): wife is beautiful, artistic, loving.",
        "Sa": "Karmic soul: wife may be older, serious, disciplined.",
        "Ra": "Unconventional soul: wife may be foreign or unconventional.",
        "Ke": "Spiritual soul: past-life karmic bond with wife.",
    }
    
    planet_d9_meanings_female = {
        "Su": "Soul authority: husband may have Sun-like qualities.",
        "Mo": "Emotional soul: deep emotional bond with husband.",
        "Ma": "Passionate soul: husband is energetic, ambitious.",
        "Me": "Intellectual soul: husband is communicative, witty.",
        "Ju": "Wisdom soul (HUSBAND KARAKA): husband is wise, spiritual, generous.",
        "Ve": "Artistic soul: husband appreciates beauty, arts.",
        "Sa": "Karmic soul: husband may be older, serious.",
        "Ra": "Unconventional soul: husband may be foreign.",
        "Ke": "Spiritual soul: past-life karmic bond with husband.",
    }
    
    planet_d9_meanings = planet_d9_meanings_female if gender == "Female" else planet_d9_meanings_male

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
            out.append(f"    ⚠ Debilitated in D9: {pl_full}'s marriage/dharma significations require conscious development.")
        elif nav_dig in ("Exalt", "Own"):
            out.append(f"    ✓ {nav_dig} in D9: {pl_full}'s significations are powerful in marriage.")

    # Vargottama
    vargottama = [
        short_to_full.get(pl, pl)
        for pl in order
        if pl in planets_data and pl in navamsa
        and planets_data[pl]["sign"] == navamsa[pl]["sign"]
    ]
    out.append("\n  Vargottama (same sign in D1 and D9):")
    if vargottama:
        out.append(f"  → {', '.join(vargottama)}: These planets are extremely stable.")
    else:
        out.append("  → No Vargottama planets.")

    return out


# ────────────────────────────────────────────────
# Interpret D7
# ────────────────────────────────────────────────
def interpret_d7(result):
    """Full D7 Saptamsa analysis – children, progeny."""
    d7 = result["d7"]
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    fifth_sign = zodiac_signs[(lagna_idx + 4) % 12]
    fifth_lord = sign_lords[fifth_sign]
    out = []
    out.append("(D7 reveals potential for children, timing of progeny, their nature.)")

    planet_d7_meanings = {
        "Su": "Progeny will have leadership, pride, authority.",
        "Mo": "Nurturing, sensitive children with emotional intelligence.",
        "Ma": "Energetic, bold, athletic children.",
        "Me": "Intelligent, communicative, analytical children.",
        "Ju": "Wise, fortunate, well-educated children – most auspicious.",
        "Ve": "Artistic, beautiful, socially gifted children.",
        "Sa": "Disciplined and serious progeny; fewer children or delays.",
        "Ra": "Unconventional, innovative children.",
        "Ke": "Spiritually oriented or intuitive children.",
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
            out.append(f"    ⚠ Debilitated in D7: challenges to progeny.")
        elif d7_dig in ("Exalt", "Own"):
            out.append(f"    ✓ {d7_dig} in D7: above significations fully activated.")

    out.append(f"\n  Key Karakas: Jupiter + 5th lord {short_to_full.get(fifth_lord, fifth_lord)}")
    return out


# ────────────────────────────────────────────────
# Interpret D10
# ────────────────────────────────────────────────
def interpret_d10(result):
    """Full D10 Dasamsa analysis – career, profession."""
    d10 = result["d10"]
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    tenth_sign = zodiac_signs[(lagna_idx + 9) % 12]
    tenth_lord = sign_lords[tenth_sign]
    out = []
    out.append("(D10 reveals true professional destiny, career, authority level.)")

    planet_d10_meanings = {
        "Su": "Government, administration, politics, leadership roles.",
        "Mo": "Public-facing work, healthcare, hospitality, real estate.",
        "Ma": "Engineering, military, surgery, real estate, sports.",
        "Me": "Communication, writing, IT, education, trade, media.",
        "Ju": "Teaching, law, counseling, finance, philosophy.",
        "Ve": "Arts, entertainment, fashion, luxury, diplomacy.",
        "Sa": "Service, labor, judiciary, mining, research.",
        "Ra": "Foreign companies, technology, film, mass politics.",
        "Ke": "Research, spirituality, healing, mathematics.",
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

    out.append(f"\n  Primary Karaka: Sun | Functional 10th Lord: {short_to_full.get(tenth_lord, tenth_lord)}")
    return out


# ────────────────────────────────────────────────
# House Lord Placement Interpretation
# ────────────────────────────────────────────────
HOUSE_LORD_IN_HOUSE = {
    (1, 1): "Strong, self-reliant personality; health and vitality prominent.",
    (1, 2): "Wealth and family shape identity; skilled in speech.",
    (1, 3): "Courageous and communicative; siblings define life greatly.",
    (1, 4): "Deeply rooted in home and mother; domestic comfort is priority.",
    (1, 5): "Creative, intelligent, child-oriented life; fame possible.",
    (1, 6): "Life centred on service, health, competition.",
    (1, 7): "Partnerships central to identity; marriage-oriented.",
    (1, 8): "Transformative, occult-drawn life; longevity issues possible.",
    (1, 9): "Highly fortunate; life guided by dharma and luck.",
    (1, 10): "Career and authority powerfully expressed; public recognition strong.",
    (1, 11): "Gains and social networks prosper naturally.",
    (1, 12): "Spiritual, isolated, or foreign-oriented life.",
    # Additional house lord placements would go here
}


def interpret_house_lords(result):
    """Interpret house lord placements."""
    out = []
    hl_map = result.get("house_lords", {})
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    
    for h_num in range(1, 13):
        h_sign = zodiac_signs[(lagna_idx + h_num - 1) % 12]
        info = hl_map.get(h_num, {})
        lord = info.get("lord", "?")
        placed = info.get("placed_in")
        lord_full = short_to_full.get(lord, lord)
        placed_sign = zodiac_signs[(lagna_idx + placed - 1) % 12] if placed else "?"
        
        key = (h_num, placed)
        if key in HOUSE_LORD_IN_HOUSE:
            meaning = HOUSE_LORD_IN_HOUSE[key]
        else:
            meaning = f"Lord of House {h_num} placed in House {placed}."
        
        out.append(f"  H{h_num:02d} ({h_sign:11}) lord {lord_full:9} → H{placed:02d} ({placed_sign:11}): {meaning}")
    
    return out

