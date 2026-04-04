# printing.py
"""
Formatted output of the complete kundali report.
"""

import datetime
import re
from .constants import (
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
from .utils import get_dignity
from .interpretations import (
    interpret_aspects,
    interpret_navamsa,
    interpret_d7,
    interpret_d10,
    interpret_d60,
    calculate_functional_strength_index,
    get_aspect_quality_score,
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
    write(f"Ayanamsa    : {result.get('ayanamsa', 'Lahiri')}")
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
        ("d60", "Shashtiamsa (D60 – Past Life Karma)", interpret_d60),
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

    # ...existing code...

    # D9 (Navamsa) gets double weight since it is the primary marriage/dharma divisional chart.
    # CHART_WEIGHTS is now imported from constants

    for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        if pl not in result["planets"]:
            continue

        integrity_score = 50
        positions = {"D1": result["planets"][pl]["sign"]}
        strong_count = 0
        weak_count = 0

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

    # Jaimini Charakaraka
    write("\nJaimini Charakaraka (The Seven Significators):")
    write("-" * 85)
    write("(Based on highest planetary longitude – nodes excluded)")
    jai = result.get("jaimini", {})
    karakas = jai.get("charakaraka", {})
    if karakas:
        for role, planet in karakas.items():
            write(f"  {role:14} : {short_to_full.get(planet, planet)}")
        atm = jai.get("atmakaraka")
        kl = jai.get("karakamsa_lagna")
        if atm and kl:
            write(f"\n  Karakamsa Lagna (Atmakaraka in D9) : {kl}")
            write(
                f"    → The soul's ultimate direction; planets conjunct or aspecting {kl} in D9 gain immense power."
            )
    else:
        write("  Could not determine karakas.")

    write("\nVimshottari Dasha:")
    write("-" * 85)
    vim = result["vimshottari"]

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
    lagna_rem = LAGNA_REMEDIES.get(_lagna)
    if lagna_rem:
        deity, mantra, day = lagna_rem
        write(f"  Lagna Lord Worship: {deity}")
        write(f"  Primary Mantra: {mantra} (108× on {day}s)")
    # 7th lord specific remedy for marital harmony
    seventh_rem = SEVENTH_LORD_REMEDIES.get(_seventh_lord)
    if seventh_rem:
        write(f"  For {_seventh_lord_full} (7th Lord – marital harmony): {seventh_rem}")

    # ── Ashtottari Dasha ─────────────────────────────────────────────────────
    ashto = result.get("ashtottari", {})
    if ashto and ashto.get("current_md"):
        write("\nAshtottari Dasha (108-year system — alternate method):")
        write("-" * 85)
        write(
            f"Starting MD : {ashto['starting_lord']} (balance {ashto['balance_at_birth_years']} yrs)"
        )
        write(f"Current MD/AD : {ashto['current_md']} / {ashto['current_ad']}")

    # ── Sookshma Dasha (4th level) ────────────────────────────────────────────
    sd_info = result.get("vimshottari_sd", {})
    current_sd = sd_info.get("current_sd")
    if current_sd:
        sd_end = sd_info.get("sd_end_jd")
        sd_end_yr = (
            int(result["birth_year"] + (sd_end - result["birth_jd"]) / 365.25)
            if sd_end
            else "?"
        )
        vim = result.get("vimshottari", {})
        pd_info = result.get("vimshottari_pd", {})
        write(
            f"  Sookshma (4th level): {vim.get('current_md','?')} / "
            f"{vim.get('current_ad','?')} / {pd_info.get('current_pd','?')} / "
            f"{current_sd} (until ~{sd_end_yr})"
        )

    # ── Upagrahas ─────────────────────────────────────────────────────────────
    upagrahas = result.get("upagrahas", {})
    if upagrahas:
        write("\nUpagrahas (Shadow / Sub-Planets):")
        write("-" * 85)
        for name, data in upagrahas.items():
            write(f"  {name:14}: {data['sign']:12} {data['deg']:5.2f}°")

    # ── Arudha Lagna ──────────────────────────────────────────────────────────
    al = result.get("arudha_lagna", {})
    if al:
        write(
            f"\nArudha Lagna (AL1) : {al.get('sign','?')} (House {al.get('house','?')})"
        )
        write("  (Reflects worldly image/perception — the 'mask' shown to society)")

    # ── Avasthas ──────────────────────────────────────────────────────────────
    avasthas = result.get("avasthas", {})
    if avasthas:
        write("\nPlanetary Avasthas (States):")
        write("-" * 85)
        write("(Qualitative states that modify how each planet delivers its results)")
        for pl in order:
            if pl in avasthas:
                av = avasthas[pl]
                pl_full = short_to_full.get(pl, pl)
                state_str = ", ".join(av["avasthas"])
                write(f"  {pl_full:9}: {state_str}")
                for desc in av["description"]:
                    write(f"             → {desc}")

    # ── Shadbala ──────────────────────────────────────────────────────────────
    shadbala = result.get("shadbala", {})
    if shadbala:
        write("\nShadbala — Six Sources of Planetary Strength:")
        write("-" * 85)
        write(
            "(Total strength in Rupas. Minimum for strength: Su≥5, Mo≥6, Ma≥5, Me≥7, Ju≥6.5, Ve≥5.5, Sa≥5)"
        )
        write(
            f"{'Planet':<10} {'Rupas':>6} {'Min':>5} {'Status':<10} "
            f"{'Sthana':>7} {'Dig':>5} {'Kala':>6} {'Chesta':>7} "
            f"{'Naisarg':>8} {'Drik':>6} {'Ishta':>6} {'Kashta':>7}"
        )
        write("-" * 85)
        for pl in order:
            if pl in shadbala:
                sb = shadbala[pl]
                c = sb["components"]
                status = "STRONG" if sb["strong"] else "weak"
                bar = "█" * int(sb["rupas"]) + "░" * max(0, 8 - int(sb["rupas"]))
                write(
                    f"  {short_to_full.get(pl,pl):<9} {sb['rupas']:>6.2f} "
                    f"{sb['min_rupas']:>5.1f} {status:<10} "
                    f"{c['sthana_bala']:>7.1f} {c['dig_bala']:>5.1f} "
                    f"{c['kala_bala']:>6.1f} {c['chesta_bala']:>7.1f} "
                    f"{c['naisargika_bala']:>8.1f} {c['drik_bala']:>6.1f} "
                    f"{sb['ishta']:>6.1f} {sb['kashta']:>7.1f}"
                )
        write(
            "  Ishta = benefic potential (higher=better); Kashta = malefic tendency (lower=better)"
        )

    # ── Bhinnashtakavarga ─────────────────────────────────────────────────────
    ashtak = result.get("ashtakavarga", {})
    by_house = ashtak.get("by_house", {})
    if by_house:
        write("\nBhinnashtakavarga — Per-Planet Bindus per House:")
        write("-" * 85)
        write("(Number of benefic dots each planet contributes to each house)")
        header = (
            f"{'House':<8} {'Sign':<12}"
            + "".join(
                f"{short_to_full.get(pl,pl):>8}"
                for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
            )
            + f"{'SAV':>6} {'Strength':<10}"
        )
        write(header)
        write("-" * 85)
        for h in range(1, 13):
            hd = by_house[h]
            planet_cols = "".join(
                f"{hd['planets'].get(pl, 0):>8}"
                for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
            )
            write(
                f"  H{h:02d} ({hd['sign']:<10}) {planet_cols}  {hd['sav']:>3}  {hd['strength']}"
            )

    # ── Additional Divisional Charts ──────────────────────────────────────────
    extra_vargas = [
        ("d3", "Drekkana (D3 – Siblings/Courage/Vitality)"),
        ("d4", "Chaturthamsha (D4 – Property/Fortune)"),
        ("d12", "Dwadashamsha (D12 – Parents/Ancestral Karma)"),
        ("d16", "Shodasha (D16 – Vehicles/Comforts)"),
        ("d20", "Vimsha (D20 – Spiritual Practice)"),
        ("d24", "Chaturvimsha (D24 – Education/Learning)"),
        ("d27", "Bhamsha (D27 – Strengths/Weaknesses)"),
        ("d30", "Trimsha (D30 – Evils/Misfortune Mitigation)"),
        ("d40", "Khavedamsha (D40 – Auspicious/Inauspicious Effects)"),
        ("d45", "Akshavedamsha (D45 – All-round Strength)"),
    ]
    write("\nAdditional Divisional Charts:")
    write("-" * 85)
    for chart_key, chart_title in extra_vargas:
        chart_data = result.get(chart_key, {})
        if not chart_data:
            continue
        write(f"\n{chart_title}:")
        write("-" * 50)
        for pl in order:
            if pl in chart_data:
                d = chart_data[pl]
                write(f"  {pl:>3}: {d.get('deg', 0):5.2f}° {d.get('sign','?'):<12}")

    # ── Numerology ────────────────────────────────────────────────────────────
    num = result.get("numerology", {})
    if num:
        write("\nVedic Numerology:")
        write("-" * 85)
        write(
            f"  Birth Number   : {num['birth_number']} ({num['birth_planet']}) — {num['birth_meaning']}"
        )
        write(
            f"  Destiny Number : {num['destiny_number']} ({num['destiny_planet']}) — {num['destiny_meaning']}"
        )
        if num.get("name_number"):
            write(
                f"  Name Number    : {num['name_number']} ({num.get('name_planet','')}) — {num.get('name_meaning','')}"
            )
        write(f"  Lucky Days     : {num['lucky_days']}")
        write(f"  Lucky Color    : {num['lucky_color']}")
        write(f"  Lucky Gem      : {num['lucky_gem']}")
        write(f"  Compatibility  : {num['compatibility']}")

    # ── Yogini Dasha ──────────────────────────────────────────────────────────
    yd = result.get("yogini_dasha", {})
    if yd:
        write("\nYogini Dasha (36-Year Cycle):")
        write("-" * 85)
        write(
            f"  Birth Yogini   : {yd.get('start_yogini','?')} | Balance: {yd.get('balance_years',0):.2f} years"
        )
        cur = yd.get("current", {})
        if cur:
            write(
                f"  Current Yogini : {cur.get('yogini','?')} (Lord: {cur.get('lord','?')})"
            )
            ad_info = cur.get("antardasha")
            if ad_info:
                write(
                    f"  Current AD     : {ad_info.get('yogini','?')} (Lord: {ad_info.get('lord','?')})"
                )
        write("")
        write(f"  {'Yogini':<14} {'Lord':<10} {'Years':<6}  Period")
        write("  " + "-" * 60)
        for md in yd.get("dashas", [])[:12]:
            start_yr = md.get("start_jd", 0)
            end_yr = md.get("end_jd", 0)
            try:
                by = result.get("birth_year", 2000)
                bjd = result.get("birth_jd", 0)
                s_yr = int(by + (md["start_jd"] - bjd) / 365.25)
                e_yr = int(by + (md["end_jd"] - bjd) / 365.25)
                period_str = f"{s_yr}–{e_yr}"
            except Exception:
                period_str = ""
            write(
                f"  {md['yogini']:<14} {md['lord']:<10} {md['years']:<6.1f}  {period_str}"
            )

    # ── Tajika / Solar Return ─────────────────────────────────────────────────
    taj = result.get("tajika", {})
    if taj:
        write("\nTajika Solar Return Analysis:")
        write("-" * 85)
        write(f"  Year          : {taj.get('year','?')} (Age {taj.get('age','?')})")
        write(f"  Solar Return  : {taj.get('solar_return_date','?')}")
        write(f"  Year Lord     : {taj.get('year_lord','?')}")
        mun = taj.get("muntha", {})
        if mun:
            write(
                f"  Muntha Sign   : {mun.get('sign','?')} (House {mun.get('house_from_lagna','?')}, Lord: {mun.get('lord','?')})"
            )
        for line in taj.get("interpretation", [])[:6]:
            write(f"  • {line}")
        applying = taj.get("applying_aspects", [])
        if applying:
            write(f"  Applying Aspects ({len(applying)}):")
            for a in applying:
                write(
                    f"    {a.get('p1', a.get('planet1','?'))} → {a.get('p2', a.get('planet2','?'))} : {a.get('aspect','?')} (orb {a.get('orb','?')}°)"
                )

    # ── Muhurtha (Birth Moment Quality) ───────────────────────────────────────
    muh = result.get("muhurtha", {})
    if muh:
        write("\nMuhurtha — Birth Moment Quality:")
        write("-" * 85)
        score = muh.get("total_score", muh.get("overall_score", "?"))
        grade = muh.get("grade", "?")
        write(f"  Overall Score : {score}/{muh.get('max_score',100)}")
        write(f"  Grade         : {grade}")
        if muh.get("tarabala"):
            tb = muh["tarabala"]
            write(
                f"  Tarabala      : {tb.get('tara_name','?')} (Score {tb.get('score','?')}/5)"
            )
        if muh.get("chandrabala"):
            cb = muh["chandrabala"]
            write(
                f"  Chandrabala   : H{cb.get('count','?')} from Moon — Score {cb.get('score','?')}/5"
            )
        if muh.get("panchanga"):
            mp = muh["panchanga"]
            write(f"  Tithi         : {mp.get('tithi_name', mp.get('tithi','?'))}")
            write(f"  Yoga          : {mp.get('yoga_name', mp.get('yoga','?'))}")
        for w in muh.get("warnings", [])[:5]:
            write(f"  ⚠  {w}")

    # ── Pancha Pakshi ─────────────────────────────────────────────────────────
    pp = result.get("pancha_pakshi", {})
    if pp:
        write("\nPancha Pakshi — Five Bird Activity System:")
        write("-" * 85)
        write(
            f"  Birth Bird     : {pp.get('birth_bird','?')} (Moon in {pp.get('moon_nakshatra','?')})"
        )
        write(f"  Today ({pp.get('query_weekday','?')}):")
        write(
            f"    Period       : {'Day' if pp.get('is_day') else 'Night'} Yama {pp.get('current_yama','?')}"
        )
        write(
            f"    Activity     : {pp.get('current_activity','?')} (Strength {pp.get('current_strength','?')}/5)"
        )
        write(f"    Advice       : {pp.get('current_advice','')}")
        write(f"  Ruling Bird Now: {pp.get('ruling_bird_now','?')}")
        day_yamas = pp.get("auspicious_day_yamas", [])
        night_yamas = pp.get("auspicious_night_yamas", [])
        if day_yamas:
            write(f"  Best Day Yamas : {', '.join(f'Yama {y}' for y in day_yamas)}")
        if night_yamas:
            write(f"  Best Night Yamas: {', '.join(f'Yama {y}' for y in night_yamas)}")
        write("")
        write("  All Birds — Current Activity:")
        for bird, info in pp.get("all_bird_activities", {}).items():
            write(f"    {bird:<10}: {info['activity']:<10} ({info['strength']}/5)")
        write("")
        write("  Today's Full Forecast (Birth Bird activities):")
        write(f"  {'Period':<18} {'Activity':<12} {'Str':<4} Advice (short)")
        write("  " + "-" * 70)
        for slot in pp.get("day_forecast", []):
            advice_short = slot["advice"].split(";")[0][:38]
            strength_bar = "★" * slot["strength"] + "☆" * (5 - slot["strength"])
            write(
                f"  {slot['period']:<18} {slot['activity']:<12} {strength_bar}  {advice_short}"
            )

    # ── Sky Chart SVG ─────────────────────────────────────────────────────────
    sky_path = result.get("sky_chart_path", "")
    if sky_path:
        write("\nSky Chart (SVG):")
        write("-" * 85)
        write(f"  South Indian chart saved to: {sky_path}")
        write("  Open the SVG file in any browser or vector graphics editor.")

    # ── Chara Dasha ───────────────────────────────────────────────────────────
    cd = result.get("chara_dasha", {})
    if cd and cd.get("dashas"):
        write("\nJaimini Chara Dasha (Sign-Based):")
        write("-" * 85)
        cur_cd = cd.get("current") or {}
        if cur_cd:
            write(
                f"  Current : {cur_cd.get('current_sign','?')} "
                f"(Lord: {cur_cd.get('current_lord','?')}) — "
                f"{cur_cd.get('years_remaining',0):.1f} yrs remaining"
            )
        write(f"  {'Sign':<14} {'Lord':<8} {'Yrs':<5}  Period")
        write("  " + "-" * 55)
        for md in cd.get("dashas", []):
            by = result.get("birth_year", 2000)
            bjd = result.get("birth_jd", 0)
            try:
                s_yr = int(by + (md["start_jd"] - bjd) / 365.25)
                e_yr = int(by + (md["end_jd"] - bjd) / 365.25)
                period_str = f"{s_yr}–{e_yr}"
            except Exception:
                period_str = ""
            write(
                f"  {md['sign']:<14} {md['lord']:<8} {md['years']:<5.1f}  {period_str}"
            )

    # ── Pada Lagnas (Arudha) ──────────────────────────────────────────────────
    pada = result.get("pada_lagnas", {})
    if pada:
        write("\nPada Lagnas (Arudha A1–A12):")
        write("-" * 85)
        write("  (Each Pada = worldly reflection of that house in the outer world)")
        for key in [f"A{i}" for i in range(1, 13)]:
            info = pada.get(key, {})
            if info:
                write(
                    f"  {key}: {info.get('sign','?'):13} (House {info.get('house','?')})"
                )
        ul = result.get("upapadha_lagna", {})
        if ul:
            write(
                f"\n  Upapadha Lagna (UL / A12 of H12): {ul.get('sign','?')} (House {ul.get('house','?')})"
            )
            interp = ul.get("interpretation", "")
            if interp:
                write(f"  → {interp}")

    # ── Vimshopak Bala ────────────────────────────────────────────────────────
    vb = result.get("vimshopak_bala", {})
    if vb:
        write("\nVimshopak Bala — 20-Point Strength Across 16 Vargas:")
        write("-" * 85)
        write("  (Score /20. Strong ≥ 15. Key weights: D60=4, D1=3.5, D9=3, D16=2)")
        write(f"  {'Planet':<10} {'Score':>6} {'Status':<8}  Bar")
        write("  " + "-" * 60)
        for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]:
            if pl in vb:
                pv = vb[pl]
                score = pv.get("score", 0)
                strong = pv.get("strong", False)
                bar = "█" * int(score) + "░" * max(0, 20 - int(score))
                status = "STRONG" if strong else "weak"
                pl_full = short_to_full.get(pl, pl)
                write(f"  {pl_full:<10} {score:>6.2f} {status:<8}  {bar}")

    # ── Graha Yuddha ──────────────────────────────────────────────────────────
    gy = result.get("graha_yuddha", [])
    if gy:
        write("\nGraha Yuddha (Planetary War):")
        write("-" * 85)
        write("  (Planets within 1° of each other — lower degree planet wins)")
        for war in gy:
            write(
                f"  {war.get('planet1','?')} vs {war.get('planet2','?')} "
                f"in {war.get('sign','?')} (orb {war.get('orb',0):.2f}°) "
                f"— Winner: {war.get('winner','?')}"
            )
            interp = war.get("interpretation", "")
            if interp:
                write(f"    → {interp}")

    # ── Transit Calendar ──────────────────────────────────────────────────────
    tc = result.get("transit_calendar", {})
    if tc:
        write("\nTransit Calendar — Next 30 Days:")
        write("-" * 85)
        summary = tc.get("summary_next_30_days", [])
        if summary:
            for evt in summary[:15]:
                evt_type = evt.get("type", evt.get("event_type", "event")).upper()
                desc = evt.get("description", evt.get("planet", ""))
                write(f"  {evt.get('date','?')}  {evt_type:<18} {desc}")
        ingresses = tc.get("ingresses", [])
        if ingresses:
            write(f"\n  Upcoming Sign Ingresses (next {min(8,len(ingresses))}):")
            for ing in ingresses[:8]:
                write(
                    f"    {ing.get('date','?')}: {ing.get('planet','?')} "
                    f"→ {ing.get('to_sign','?')} (from {ing.get('from_sign','?')})"
                )
        retros = tc.get("retrogrades", [])
        if retros:
            write(f"\n  Retrograde Stations (next {min(6,len(retros))}):")
            for r in retros[:6]:
                write(
                    f"    {r.get('date','?')}: {r.get('planet','?')} "
                    f"{r.get('type','').replace('_',' ')} in {r.get('sign','?')}"
                )
        eclipses = tc.get("eclipses", [])
        if eclipses:
            write(f"\n  Eclipses (next {min(4,len(eclipses))}):")
            for ec in eclipses[:4]:
                write(
                    f"    {ec.get('date','?')}: {ec.get('type','?').upper()} "
                    f"Eclipse ({ec.get('subtype','?')})"
                )

    # ── North Indian Chart ────────────────────────────────────────────────────
    north_path = result.get("north_chart_path", "")
    if north_path:
        write("\nNorth Indian Chart (SVG):")
        write("-" * 85)
        write(f"  Chart saved to: {north_path}")

    # ── PDF Report ────────────────────────────────────────────────────────────
    pdf_path = result.get("pdf_report_path", "")
    if pdf_path:
        write("\nPDF Report:")
        write("-" * 85)
        write(f"  Full report saved to: {pdf_path}")

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
