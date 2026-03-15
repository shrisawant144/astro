# printing.py
"""
Formatted output of the complete kundali report.
"""

import datetime
import re
from constants import (
    short_to_full,
    zodiac_signs,
    sign_lords,
    HOUSE_SIGNIFICATIONS,
    FUNCTIONAL_QUALITY,
    DIGNITY_SIGNS,
    CHART_WEIGHTS,
    LAGNA_REMEDIES,
    SEVENTH_LORD_REMEDIES,
    HOUSE_LORD_IN_HOUSE,
)
from utils import get_dignity
from interpretations import (
    interpret_aspects,
    interpret_navamsa,
    interpret_d7,
    interpret_d10,
    calculate_functional_strength_index,
)


def print_kundali(result, file=None):
    """Print the complete kundali report to console and optionally to a file."""
    lines = []
    gender = result.get("gender", "Male")

    def write(s):
        lines.append(s)

    write("\n" + "═" * 95)
    write(" VEDIC KUNDALI – Whole Sign – Lahiri – D7 + D10 + Marriage Timing")
    write("═" * 95)
    write(f"Name         : {result.get('name', 'Not provided')}")
    write(f"Gender       : {gender}")
    write(f"Birth Date   : {result.get('birth_date', 'N/A')}")
    write(f"Birth Time   : {result.get('birth_time', 'N/A')}")
    write(f"Birth Place  : {result.get('birth_place', 'N/A')}")
    write(f"Lagna        : {result['lagna_sign']} {result['lagna_deg']}°")
    write(f"Moon (Rasi)  : {result['moon_sign']} – {result['moon_nakshatra']}")
    write(f"7th Lord     : {result['seventh_lord']}")
    # Panchanga
    pan = result.get("panchanga", {})
    if pan:
        write(f"Tithi        : {pan.get('tithi','?')}")
        write(f"Vara         : {pan.get('vara','?')}")
        write(f"Yoga         : {pan.get('yoga','?')}")
        write(f"Karana       : {pan.get('karana','?')}")
    write("")

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    write("Planets in Rasi (D1):")
    write("-" * 85)
    for pl in order:
        if pl in result["planets"]:
            d = result["planets"][pl]
            flags = ""
            if d.get("retro"):
                flags += " R"
            if d.get("combust"):
                flags += " C"
            # Dignity label — append NB when neecha bhanga cancels debilitation
            dig_label = d["dignity"]
            if dig_label == "Debilitated" and d.get("neecha_bhanga", False):
                dig_label = "Debilitated (NB)"
            dig = f" ({dig_label})" if dig_label else ""
            write(
                f"{pl:>3}: {d['deg']:5.2f}° {d['sign']:11} {d['nakshatra']:18}{dig}{flags}"
            )
    write(
        "  (R = Retrograde, C = Combust/Astangata – weakened by closeness to Sun, NB = Neecha Bhanga – debilitation cancelled)"
    )

    for div, title, interp_fn in [
        ("navamsa", "Navamsa (D9 – Marriage/Spouse/Dharma)", interpret_navamsa),
        ("d7", "Saptamsa (D7 – Children/Progeny)", interpret_d7),
        ("d10", "Dasamsa (D10 – Career/Profession)", interpret_d10),
    ]:
        write(f"\n{title}:")
        write("-" * 85)
        for pl in order:
            if pl in result[div]:
                d = result[div][pl]
                write(f"{pl:>3}: {d['deg']:5.2f}° {d['sign']:11}")
        write(f"\nDetailed {title.split('(')[1].rstrip(')')} Analysis:")
        write("-" * 85)
        for line in interp_fn(result):
            write(line)

    write("\nHouses (Whole Sign):")
    write("-" * 85)
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    for h in range(1, 13):
        sidx = (lagna_idx + h - 1) % 12
        sign = zodiac_signs[sidx]
        pls = sorted(result["houses"][h])
        content = " ".join(pls) if pls else "—"
        write(f"House {h:2d} ({sign:11}): {content}")

    write("\nAspects (Drishti) – Summary:")
    write("-" * 85)
    for h in range(1, 13):
        if result["aspects"][h]:
            write(f"House {h:2d}: {', '.join(result['aspects'][h])}")

    write("\nAspects (Drishti) – Full Analysis:")
    write("-" * 85)
    write(
        "Aspect strengths: 7th=100% | Jupiter 5th/9th=75% | Mars 8th=75% | Saturn 10th=75% | Mars 4th=50% | Saturn 3rd=25%"
    )
    for line in interpret_aspects(result):
        write(line)

    # Ashtakavarga (SAV)
    write("\nAshtakavarga (Sarvashtakavarga - Marriage & Life Support Index):")
    write("-" * 85)
    write(
        "(SAV measures accumulated benefic points for each house. Marriage astrology heavily relies on 7th house SAV.)"
    )
    ashtak = result.get("ashtakavarga", {})
    if ashtak:
        sav_scores = ashtak.get("sav", [])
        interpretation = ashtak.get("interpretation", {})

        lagna_idx_av = zodiac_signs.index(result["lagna_sign"])

        # Show all house SAV scores
        write("\nSAV Points by House:")
        for h in range(1, 13):
            house_idx = (h - 1 + lagna_idx_av) % 12
            score = sav_scores[house_idx] if house_idx < len(sav_scores) else 0
            sign = zodiac_signs[(lagna_idx_av + h - 1) % 12]

            # Visual bar
            bar_length = min(30, score)
            bar = "█" * bar_length + "░" * (30 - bar_length)

            # Get interpretation
            interp_data = interpretation.get(h, {})
            strength = interp_data.get("strength", "Unknown")

            # Highlight 7th house (marriage)
            marker = " ★ MARRIAGE HOUSE" if h == 7 else ""
            write(f"  H{h:02d} ({sign:11}): [{bar}] {score:2} pts - {strength}{marker}")

        # Special focus on 7th house
        h7_data = interpretation.get(7, {})
        h7_score = h7_data.get("score", 0)
        h7_strength = h7_data.get("strength", "Unknown")

        write(f"\n  ★ 7th House (Marriage) SAV: {h7_score} points - {h7_strength}")

        if h7_score >= 28:
            marriage_interp = (
                "Excellent marriage support! Smooth path, harmonious relationship."
            )
        elif h7_score >= 25:
            marriage_interp = "Good marriage support. Positive relationship with manageable challenges."
        elif h7_score >= 22:
            marriage_interp = "Average marriage karma. Normal ups and downs expected."
        else:
            marriage_interp = "Weak marriage support. Extra effort, patience, or remedies recommended."

        write(f"     Interpretation for Marriage: {marriage_interp}")

        write(
            "\n  SAV Scoring Legend: ≥28 = Excellent | 25-27 = Good | 22-24 = Average | <22 = Weak"
        )
        write(
            "  Note: Low SAV doesn't mean 'no marriage' - it indicates more effort/karma to work through."
        )

    # Functional Benefics/Malefics with Strength Index
    write("\nFunctional Classification Strength Index (by Lagna):")
    write("-" * 85)
    write(
        "(Nuanced scoring: Base functional status + D1 dignity + D9 dignity + House placement)"
    )
    write("")
    fq = FUNCTIONAL_QUALITY.get(result["lagna_sign"], {})
    if fq:
        # Show traditional classifications first
        ben_names = [short_to_full.get(p, p) for p in fq.get("ben", [])]
        mal_names = [short_to_full.get(p, p) for p in fq.get("mal", [])]
        maraka_names = [short_to_full.get(p, p) for p in fq.get("maraka", [])]
        mixed_names = [short_to_full.get(p, p) for p in fq.get("mixed", [])]
        yk = fq.get("yk")
        write(f"  Base Benefics    : {', '.join(ben_names) if ben_names else '—'}")
        write(f"  Base Malefics    : {', '.join(mal_names) if mal_names else '—'}")
        write(
            f"  Marakas (2/7)    : {', '.join(maraka_names) if maraka_names else '—'}"
        )
        write(f"  Mixed Nature     : {', '.join(mixed_names) if mixed_names else '—'}")
        if yk:
            write(f"  Yogakaraka       : {short_to_full.get(yk, yk)}")
        write("")
        write("  FUNCTIONAL STRENGTH INDEX (Adjusted for this chart):")
        write("  " + "-" * 80)
        for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
            if pl in result["planets"]:
                fsi = calculate_functional_strength_index(result, pl)
                score = fsi["score"]
                bar = "█" * (score // 5) + "░" * (20 - score // 5)
                pl_full = short_to_full.get(pl, pl)
                mods = ", ".join(fsi["modifiers"]) if fsi["modifiers"] else "—"
                write(f"  {pl_full:9} [{bar}] {score:3}/100 | {fsi['effective_class']}")
                write(f"             Base: {fsi['base_class']:12} | Modifiers: {mods}")
        write("")
        write(
            "  Legend: ≥80 Strong Benefic | ≥65 Conditional Benefic | ≥50 Neutral-Positive"
        )
        write("          ≥35 Conditional Malefic | <35 Functional Malefic")
        write(
            "  Note: A 'Malefic' planet in own sign/exalted becomes Conditional Benefic."
        )

    # Cross-Chart Planetary Integrity Index
    write("\nCross-Chart Planetary Integrity Index (D1-D9-D10-D7):")
    write("-" * 85)
    write(
        "(Measures each planet's consistency across divisional charts – D9 weighted ×2 for marriage context)"
    )
    write("")

    DIGNITY_SIGNS = {
        "Su": {"exalt": "Aries", "own": ["Leo"], "deb": "Libra"},
        "Mo": {"exalt": "Taurus", "own": ["Cancer"], "deb": "Scorpio"},
        "Ma": {"exalt": "Capricorn", "own": ["Aries", "Scorpio"], "deb": "Cancer"},
        "Me": {"exalt": "Virgo", "own": ["Gemini", "Virgo"], "deb": "Pisces"},
        "Ju": {"exalt": "Cancer", "own": ["Sagittarius", "Pisces"], "deb": "Capricorn"},
        "Ve": {"exalt": "Pisces", "own": ["Taurus", "Libra"], "deb": "Virgo"},
        "Sa": {"exalt": "Libra", "own": ["Capricorn", "Aquarius"], "deb": "Aries"},
    }

    # D9 (Navamsa) gets double weight since it is the primary marriage/dharma divisional chart.
    CHART_WEIGHTS = {"D1": 1.0, "D9": 2.0, "D10": 1.0, "D7": 1.0}

    for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        if pl not in result["planets"]:
            continue

        integrity_score = 50
        positions = {"D1": result["planets"][pl]["sign"]}
        strong_count = 0
        weak_count = 0

        for chart_name, chart_data in [
            ("D9", result.get("navamsa", {})),
            ("D10", result.get("d10", {})),
            ("D7", result.get("d7", {})),
        ]:
            if pl in chart_data:
                positions[chart_name] = chart_data[pl]["sign"]

        dig_info = DIGNITY_SIGNS.get(pl, {})
        for chart, sign in positions.items():
            w = CHART_WEIGHTS.get(chart, 1.0)
            if sign == dig_info.get("exalt"):
                integrity_score += int((15 if chart == "D1" else 10) * w)
                strong_count += 1
            elif sign in dig_info.get("own", []):
                integrity_score += int((12 if chart == "D1" else 8) * w)
                strong_count += 1
            elif sign == dig_info.get("deb"):
                integrity_score -= int((15 if chart == "D1" else 8) * w)
                weak_count += 1

        # Vargottama bonus
        if (
            pl in result.get("navamsa", {})
            and result["planets"][pl]["sign"] == result["navamsa"][pl]["sign"]
        ):
            integrity_score += 15

        # Triple alignment bonus
        if pl in result.get("navamsa", {}) and pl in result.get("d10", {}):
            if (
                result["planets"][pl]["sign"]
                == result["navamsa"][pl]["sign"]
                == result["d10"][pl]["sign"]
            ):
                integrity_score += 20

        integrity_score = max(0, min(100, integrity_score))

        # Classify reliability
        if integrity_score >= 80 and weak_count == 0:
            reliability = "Highly Reliable (Triple Confirmation)"
        elif integrity_score >= 65 and strong_count >= 2:
            reliability = "Reliable (Multi-Chart Support)"
        elif integrity_score >= 50:
            reliability = "Moderate (Needs Activation)"
        elif weak_count >= 2:
            reliability = "Challenged (Karmic Work Required)"
        else:
            reliability = "Variable (Context-Dependent)"

        bar = "█" * (integrity_score // 5) + "░" * (20 - integrity_score // 5)
        pl_full = short_to_full.get(pl, pl)
        pos_str = " | ".join([f"{k}:{v}" for k, v in positions.items()])
        write(f"  {pl_full:9} [{bar}] {integrity_score:3}/100 | {reliability}")
        write(f"             Positions: {pos_str}")
    write("")

    # House Lord Placements
    write("\nHouse Lord Placements:")
    write("-" * 85)
    hl_map = result.get("house_lords", {})
    lagna_idx_p = zodiac_signs.index(result["lagna_sign"])
    for h_num in range(1, 13):
        h_sign = zodiac_signs[(lagna_idx_p + h_num - 1) % 12]
        info = hl_map.get(h_num, {})
        lord = info.get("lord", "?")
        placed = info.get("placed_in")
        lord_full = short_to_full.get(lord, lord)
        placed_sign = zodiac_signs[(lagna_idx_p + placed - 1) % 12] if placed else "?"
        key = (h_num, placed)
        if key in HOUSE_LORD_IN_HOUSE:
            meaning = HOUSE_LORD_IN_HOUSE[key]
        else:
            meaning = (
                f"Lord of House {h_num} ({h_sign}) placed in House {placed} ({placed_sign}): "
                f"House {h_num} themes expressed through the environment of House {placed}."
            )
        write(
            f"  H{h_num:02d} ({h_sign:11}) lord {lord_full:9} → H{placed:02d} ({placed_sign:11}): "
            f"{meaning.split(':')[-1].strip()}"
        )

    write("\nVimshottari Dasha:")
    write("-" * 85)
    vim = result["vimshottari"]
    write(
        f"Starting MD : {vim['starting_lord']} (balance {vim['balance_at_birth_years']} yrs)"
    )
    if vim["current_md"]:
        pd_info = result.get("vimshottari_pd", {})
        current_pd = pd_info.get("current_pd")
        pd_end_jd = pd_info.get("pd_end_jd")
        if current_pd and pd_end_jd:
            pd_end_yr = int(
                result["birth_year"] + (pd_end_jd - result["birth_jd"]) / 365.25
            )
            write(
                f"Current (MD/AD/PD) : {vim['current_md']} / {vim['current_ad']} / {current_pd} (PD until ~{pd_end_yr})"
            )
        else:
            write(f"Current (MD/AD) : {vim['current_md']} / {vim['current_ad']}")

    # Gender-specific marriage analysis
    spouse_term = "husband" if gender == "Female" else "wife"
    spouse_karaka = "Jupiter" if gender == "Female" else "Venus"
    spouse_karaka_short = "Ju" if gender == "Female" else "Ve"

    write(f"\nMarriage Timing Insights (Enhanced Parashari) – For {gender}:")
    write("-" * 85)
    # Calculate key factors
    lagna_idx = zodiac_signs.index(result["lagna_sign"])

    def lord_of_h(h):
        return sign_lords[zodiac_signs[(lagna_idx + h - 1) % 12]]

    seventh_lord = result["seventh_lord"]
    second_lord = lord_of_h(2)

    write(
        f"  7th Lord ({spouse_term}): {short_to_full.get(seventh_lord, seventh_lord)}"
    )
    write(f"  2nd Lord (family)    : {short_to_full.get(second_lord, second_lord)}")
    write(
        f"  {spouse_karaka} ({spouse_term} karaka): {result['planets'].get(spouse_karaka_short, {}).get('sign', '?')}"
    )

    # D9 spouse karaka status (gender-specific)
    karaka_d9 = result.get("navamsa", {}).get(spouse_karaka_short, {})
    if karaka_d9:
        karaka_d9_dig = get_dignity(spouse_karaka_short, karaka_d9.get("sign", ""))
        d9_status = f"{karaka_d9.get('sign', '?')}"
        if karaka_d9_dig:
            d9_status += f" ({karaka_d9_dig})"
        write(f"  D9 {spouse_karaka}          : {d9_status}")

    write(
        f"\n  Probability factors scored: 7th lord (+3), {spouse_karaka} (+3), 2nd lord (+2),"
    )
    write(
        f"  {'Venus' if gender == 'Female' else 'Jupiter'} (+1), D9 {spouse_karaka} dignity (+1), D9 7th lord (+1), house placement (+1)"
    )
    write("  Score legend: ★★★ (7-10) High | ★★ (4-6) Moderate | ★ (1-3) Lower")
    vm = vim["current_md"]
    va = vim["current_ad"]
    if (
        vm in [spouse_karaka, spouse_karaka_short]
        or va in [spouse_karaka, spouse_karaka_short]
        or vm == result["seventh_lord"]
        or va == result["seventh_lord"]
    ):
        write("*** CURRENT DASHA IS HIGHLY FAVOURABLE FOR MARRIAGE ***")
    else:
        write(
            f"Next favourable periods: {spouse_karaka} or 7th-lord Mahadasha/Antardasha (check full list)"
        )

    write("\nCurrent Gochara (from Moon):")
    write("-" * 85)
    for pl, t in sorted(result["transits"].items()):
        write(
            f"{pl:>3}: {t['sign']:11} (house {t['house_from_moon']:2d}) – {t['effect']}"
        )
    sade = result.get("sade_sati")
    if sade:
        write(f"\n  ⚠ SATURN SPECIAL TRANSIT: {sade}")
    else:
        write(
            "  ✓ No active Sade Sati or Dhaiya (Saturn not in critical position from Moon)"
        )

    write("\n🔥 YOGAS WITH STRENGTH (1-10) & ACCURATE TIMINGS")
    write("-" * 95)
    for yoga in result.get("yogas", []):
        write(f"• {yoga}")

    birth_year = result.get("birth_year", "N/A")
    write(f"\n📅 FRUCTIFICATION PERIODS (Full Life Timeline from {birth_year})")
    write("-" * 95)
    write(
        "  [PAST] = Already occurred | [NOW] = Currently active | [FUTURE] = Upcoming"
    )
    for event, periods in result.get("timings", {}).items():
        write(f"\n{event}:")
        if periods:
            for p in periods:
                write(p)
        else:
            write(" No major period found")

    write("\n⚠️ PROBLEMS/DOSHAS IN KUNDALI")
    write("-" * 95)
    for prob in result.get("problems", []):
        write(f"• {prob['summary']}")

    write("\nDetailed Explanation of Doshas:")
    write("-" * 95)
    for prob in result.get("problems", []):
        if prob["detail"]:
            write(f"{prob['summary'].split(':')[0]}:")
            write(prob["detail"])
            write("")

    write("\n🔧 TARGETED REMEDIES (per detected Dosha)")
    write("-" * 95)
    has_remedy = False
    for prob in result.get("problems", []):
        rems = prob.get("remedies", [])
        if rems:
            has_remedy = True
            write(f"\n{prob['summary'].split(':')[0]}:")
            for r in rems:
                write(f"  • {r}")
    if not has_remedy:
        write("  No specific remedies needed – maintain positive practices.")

    # ── Personalized Remedies by Lagna & 7th Lord ──
    _lagna = result.get("lagna_sign", "")
    _seventh_lord = result.get("seventh_lord", "")
    _seventh_lord_full = short_to_full.get(_seventh_lord, _seventh_lord)
    write(f"\n🛡️ PERSONALIZED REMEDIES (For {_lagna} Lagna)")
    write("-" * 85)
    # Lagna-specific mantras and deities
    LAGNA_REMEDIES = {
        "Aries": ("Hanuman/Mars", "Om Ang Angarakaya Namah", "Tuesday"),
        "Taurus": ("Lakshmi/Venus", "Om Shum Shukraya Namah", "Friday"),
        "Gemini": ("Vishnu/Mercury", "Om Bum Buddhaya Namah", "Wednesday"),
        "Cancer": ("Moon/Durga", "Om Som Somaya Namah", "Monday"),
        "Leo": ("Sun/Surya", "Om Suryaya Namah", "Sunday"),
        "Virgo": ("Vishnu/Mercury", "Om Bum Buddhaya Namah", "Wednesday"),
        "Libra": ("Lakshmi/Venus", "Om Shum Shukraya Namah", "Friday"),
        "Scorpio": ("Hanuman/Mars", "Om Ang Angarakaya Namah", "Tuesday"),
        "Sagittarius": ("Brihaspati/Jupiter", "Om Brim Brihaspataye Namah", "Thursday"),
        "Capricorn": ("Shani/Saturn", "Om Sham Shanicharaya Namah", "Saturday"),
        "Aquarius": ("Shani/Saturn", "Om Sham Shanicharaya Namah", "Saturday"),
        "Pisces": ("Brihaspati/Jupiter", "Om Brim Brihaspataye Namah", "Thursday"),
    }
    lagna_rem = LAGNA_REMEDIES.get(_lagna)
    if lagna_rem:
        deity, mantra, day = lagna_rem
        write(f"  Lagna Lord Worship: {deity}")
        write(f"  Primary Mantra: {mantra} (108× on {day}s)")
    # 7th lord specific remedy for marital harmony
    SEVENTH_LORD_REMEDIES = {
        "Su": "Offer water (Arghya) to rising Sun on Sundays; donate wheat/jaggery.",
        "Mo": "Wear pearl/moonstone; offer milk to Shiva on Mondays; stay near water.",
        "Ma": "Recite Hanuman Chalisa on Tuesdays; donate red items; exercise regularly.",
        "Me": "Chant Vishnu Sahasranama on Wednesdays; donate green items/books.",
        "Ju": "Visit temple on Thursdays; donate yellow cloth/turmeric; respect elders/gurus.",
        "Ve": "Offer white sweets on Fridays; donate perfume/white cloth; appreciate art/beauty.",
        "Sa": "Serve the needy on Saturdays; donate black sesame/oil; patience in relationships.",
    }
    seventh_rem = SEVENTH_LORD_REMEDIES.get(_seventh_lord)
    if seventh_rem:
        write(f"  For {_seventh_lord_full} (7th Lord – marital harmony): {seventh_rem}")

    write("\n" + result.get("final_analysis", ""))
    write("\nNote: Highest probability when dasha + transit + gochara align.")
    birth_year = result.get("birth_year", "N/A")
    current_year = datetime.datetime.now().year
    write(
        f"Timings calculated from birth year {birth_year}; current year {current_year}."
    )
    write("Doshas indicate challenges; remedies like mantras/gemstones can mitigate.")
    write("\n" + "═" * 95)

    output = "\n".join(lines) + "\n"
    print(output, end="")
    if file:
        file.write(output)
