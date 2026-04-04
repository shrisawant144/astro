# spouse/report.py
def generate_spouse_report(pred):
    from datetime import datetime
    from ..constants import SHORT_TO_FULL, ZODIAC_SIGNS

    lines = []
    lines.append("=" * 90)
    lines.append("  ADVANCED FUTURE SPOUSE PREDICTION - PROFESSIONAL 2025-26 EDITION")
    lines.append(
        "  (25+ Vedic Layers: Functional Nature + Integrity + Aspects + Dashas + Transits)"
    )
    lines.append("=" * 90)
    lines.append(
        f"\nGender: {pred.get('gender', 'Male')} | Lagna: {pred.get('lagna_sign', 'N/A')}"
    )
    lines.append(
        f"Spouse Karaka: {SHORT_TO_FULL.get(pred.get('spouse_karaka', 'Ve'), 'Venus')}"
    )
    lines.append(
        f"\nOverall Confidence Score: {pred.get('confidence_score', 'Unknown')}"
    )

    # Darakaraka Details
    lines.append("\n" + "─" * 90)
    lines.append("🌟 DARAKARAKA DETAILS (Jaimini)")
    lines.append("─" * 90)
    dk = pred.get("darakaraka_details", {})
    lines.append(
        f"Planet: {dk.get('name', 'N/A')} at {dk.get('degree', 0):.2f}° within sign"
    )
    lines.append(
        f"Sign in D1: {dk.get('sign_d1', 'N/A')} ({dk.get('dignity_d1', 'N/A')})"
    )
    lines.append(
        f"Sign in D9: {dk.get('sign_d9', 'N/A')} ({dk.get('dignity_d9', 'N/A')})"
    )
    lines.append(
        f"DK in D9 {dk.get('d9_house', '?')}th house: {dk.get('d9_house_meaning', '')}"
    )
    lines.append(f"Integrity Score: {dk.get('integrity', 50)}%")
    lines.append(f"Functional Nature: {dk.get('functional', 'Unknown')}")

    # Atmakaraka
    lines.append("\n" + "─" * 90)
    lines.append("🔮 ATMAKARAKA FOR SPOUSE (Soul Connection)")
    lines.append("─" * 90)
    ak = pred.get("atmakaraka_analysis", {})
    if "error" not in ak:
        lines.append(ak.get("interpretation", ""))
    else:
        lines.append(f"Note: {ak.get('error', 'Data unavailable')}")

    # Karakamsa Lagna
    lines.append("\n" + "─" * 90)
    lines.append("🌌 KARAKAMSA LAGNA (Soul Marriage)")
    lines.append("─" * 90)
    kl = pred.get("karakamsa_analysis", {})
    if "error" not in kl:
        lines.append(kl.get("interpretation", ""))
    else:
        lines.append(f"Note: {kl.get('error', 'Data unavailable')}")

    # Personality & Appearance
    lines.append("\n" + "─" * 90)
    lines.append("💫 SPOUSE PERSONALITY")
    lines.append("─" * 90)
    pers = pred.get("personality", {})
    lines.append(f"7th House Influence: {pers.get('7th_house_influence', 'N/A')}")
    lines.append(f"Darakaraka Influence: {pers.get('darakaraka_influence', 'N/A')}")

    lines.append("\n" + "─" * 90)
    lines.append("✨ PHYSICAL APPEARANCE (Multi-Layer)")
    lines.append("─" * 90)
    app = pred.get("appearance", {})
    lines.append(f"Primary Source: {app.get('primary_source', 'N/A')}")
    lines.append(f"Build: {app.get('build', 'N/A')}")
    lines.append(f"Face: {app.get('face', 'N/A')}")
    lines.append(f"Complexion: {app.get('complexion', 'N/A')}")
    if "dk_planet" in app:
        lines.append(
            f"Darakaraka {app['dk_planet']} adds: {app.get('dk_influence', '')}"
        )
        lines.append(f"DK sign modifier: {app.get('dk_sign_adds', '')}")
        lines.append(f"D9 refinement: {app.get('d9_refinement', '')}")

    # --- EXPANDED SECTIONS: All available computed details ---
    # Full 7th House Analysis
    if pred.get("spouse_profile"):
        lines.append("\n" + "─" * 90)
        lines.append("🏠 FULL 7TH HOUSE ANALYSIS")
        lines.append("─" * 90)
        h7 = pred.get("spouse_profile", {})
        for k, v in h7.items():
            # If value is a dict, format nicely
            if isinstance(v, dict):
                for subk, subv in v.items():
                    lines.append(f"{k} - {subk}: {subv}")
            else:
                lines.append(f"{k.replace('_', ' ').capitalize()}: {v}")

    # House Lord Placements (2nd, 5th, 7th)
    if pred.get("lord_placements"):
        lines.append("\n" + "─" * 90)
        lines.append("🏡 HOUSE LORD PLACEMENTS (Full)")
        lines.append("─" * 90)
        for house, data in pred["lord_placements"].items():
            if isinstance(data, dict):
                lines.append(f"{house.replace('_', ' ').capitalize()} Lord: {data.get('lord', '?')}, placed in {data.get('placed_in', '?')} house.")
                lines.append(f"Interpretation: {data.get('interpretation', '')}")
            else:
                lines.append(f"{house.replace('_', ' ').capitalize()}: {data}")

    # Vargottama Planets (D1=D9)
    if pred.get("navamsa_strength"):
        lines.append("\n" + "─" * 90)
        lines.append("📈 VARGOTTAMA PLANETS (D1=D9)")
        lines.append("─" * 90)
        nav = pred["navamsa_strength"]
        count = nav.get('count', 0)
        lines.append(f"Number of Vargottama Planets: {count}")
        if nav.get("vargottama"):
            full_names = [SHORT_TO_FULL.get(p, p) for p in nav["vargottama"]]
            lines.append(f"Vargottama Planets: {', '.join(full_names)}")
        if count == 0:
            lines.append("No planets are Vargottama (in the same sign in both D1 and D9 charts).")

    # Integrity Scores for Key Planets
    if pred.get("integrity_summary"):
        lines.append("\n" + "─" * 90)
        lines.append("🔒 INTEGRITY SCORES (All Key Planets)")
        lines.append("─" * 90)
        for p, data in pred["integrity_summary"].items():
            if isinstance(data, dict):
                lines.append(f"{SHORT_TO_FULL.get(p, p)}: {data.get('score', '?')}% - {data.get('label', 'Unknown')}")
            else:
                lines.append(f"{SHORT_TO_FULL.get(p, p)}: {data}")

    # Graha Yuddha (Planetary War)
    if pred.get("graha_yuddha"):
        lines.append("\n" + "─" * 90)
        lines.append("⚔️ GRAHA YUDDHA (Planetary War)")
        lines.append("─" * 90)
        for war in pred["graha_yuddha"]:
            lines.append(f"• {war['description']}")

    # Functional Karaka (Venus/Jupiter)
    if pred.get("functional_karaka"):
        lines.append("\n" + "─" * 90)
        lines.append("🌟 FUNCTIONAL KARAKA (Venus/Jupiter)")
        lines.append("─" * 90)
        for k, v in pred["functional_karaka"].items():
            if isinstance(v, dict):
                lines.append(f"{k.capitalize()}: {v.get('label', '')} (Score: {v.get('score', '?')})")
            else:
                lines.append(f"{k.capitalize()}: {v}")

    # Nakshatra Insights (All)
    if pred.get("nakshatra_insights"):
        lines.append("\n" + "─" * 90)
        lines.append("🌙 NAKSHATRA INSIGHTS (All)")
        lines.append("─" * 90)
        for p, info in pred["nakshatra_insights"].items():
            if isinstance(info, dict):
                lines.append(f"• {SHORT_TO_FULL.get(p, p)} in {info.get('nakshatra', '?')} (ruled by {info.get('lord', '?')}, deity {info.get('deity', '?')})")
                lines.append(f"  → {info.get('meaning', '')}")
            else:
                lines.append(f"• {SHORT_TO_FULL.get(p, p)}: {info}")

    # Current Transits (Full)
    if pred.get("current_transits"):
        lines.append("\n" + "─" * 90)
        lines.append("🌍 CURRENT TRANSITS (Full)")
        lines.append("─" * 90)
        transits = pred["current_transits"]
        # Transiting 7th house
        if "transiting_7th" in transits:
            if transits["transiting_7th"]:
                lines.append("Planets currently transiting the 7th house:")
                lines.append(
                    "  • " + ", ".join([SHORT_TO_FULL.get(p, p) for p in transits["transiting_7th"]])
                )
            else:
                lines.append("No planets are currently transiting the 7th house.")
        # Gochara (planetary transits from Moon)
        if "gochara" in transits and isinstance(transits["gochara"], dict):
            lines.append("")
            lines.append("Gochara (Planetary Transits from Moon):")
            for planet, info in transits["gochara"].items():
                pname = SHORT_TO_FULL.get(planet, planet)
                sign = info.get("sign", "?")
                house = info.get("house_from_moon", "?")
                effect = info.get("effect", "")
                lines.append(f"• {pname} in {sign} ({house}th from Moon): {effect}")

    # Marriage Type (All Indicators)
    if pred.get("marriage_type"):
        lines.append("\n" + "─" * 90)
        lines.append("💑 MARRIAGE TYPE (All Indicators)")
        lines.append("─" * 90)
        mt = pred["marriage_type"]
        if isinstance(mt, dict):
            for k, v in mt.items():
                lines.append(f"{k}: {v}")
        else:
            lines.append(str(mt))

    # Ashtakavarga (Full)
    if pred.get("ashtakavarga"):
        lines.append("\n" + "─" * 90)
        lines.append("📊 ASHTAKAVARGA (Full)")
        lines.append("─" * 90)
        ashtak = pred["ashtakavarga"]
        if 'points' in ashtak:
            lines.append(f"Total Points in 7th House: {ashtak['points']}")
        if 'planetary_points' in ashtak:
            lines.append("Breakdown by Planet:")
            for planet, pts in ashtak['planetary_points'].items():
                lines.append(f"  • {SHORT_TO_FULL.get(planet, planet)}: {pts} points")
        if 'interpretation' in ashtak:
            lines.append(f"Summary: {ashtak['interpretation']}")
        else:
            for k, v in ashtak.items():
                if k not in ('points', 'planetary_points', 'interpretation'):
                    lines.append(f"{k.replace('_', ' ').capitalize()}: {v}")

    # D2 Analysis (Full)
    if pred.get("d2_analysis"):
        lines.append("\n" + "─" * 90)
        lines.append("💰 D2 HORA (Full)")
        lines.append("─" * 90)
        d2 = pred["d2_analysis"]
        if d2.get('available'):
            if 'h7_lord_d2_sign' in d2 and 'h7_lord_d2_dignity' in d2:
                lines.append(f"7th Lord in D2: {d2['h7_lord_d2_sign']} ({d2['h7_lord_d2_dignity']})")
            if 'financial_strength' in d2:
                lines.append(f"Family Financial Strength: {d2['financial_strength']}")
            if 'family_note' in d2:
                lines.append(f"Summary: {d2['family_note']}")
        else:
            for k, v in d2.items():
                if k not in ('available', 'h7_lord_d2_sign', 'h7_lord_d2_dignity', 'financial_strength', 'family_note'):
                    lines.append(f"{k.replace('_', ' ').capitalize()}: {v}")

    # D60 Analysis (Full)
    if pred.get("d60_analysis"):
        lines.append("\n" + "─" * 90)
        lines.append("🔮 D60 SHASHTIAMSA (Full)")
        lines.append("─" * 90)
        d60 = pred["d60_analysis"]
        if d60.get('available'):
            if 'h7_lord_d60' in d60:
                lines.append(f"7th Lord in D60: {d60['h7_lord_d60']}")
            if 'venus_d60' in d60:
                lines.append(f"Venus in D60: {d60['venus_d60']}")
            if 'karma_notes' in d60:
                lines.append("Karmic Insights:")
                for note in d60['karma_notes']:
                    lines.append(f"  • {note}")
            if d60.get('severe_karma'):
                lines.append(f"⚠️ Severe Karma: {d60['remedy_note']}")
            elif 'remedy_note' in d60:
                lines.append(f"Remedy: {d60['remedy_note']}")
        else:
            for k, v in d60.items():
                if k not in ('available', 'h7_lord_d60', 'venus_d60', 'karma_notes', 'severe_karma', 'remedy_note'):
                    lines.append(f"{k.replace('_', ' ').capitalize()}: {v}")

    # Confidence Factors (Full)
    if pred.get("confidence_factors"):
        lines.append("\n" + "─" * 90)
        lines.append(f"✅ CONFIDENCE FACTORS (Full List, {len(pred['confidence_factors'])})")
        lines.append("─" * 90)
        for i, factor in enumerate(pred["confidence_factors"], 1):
            lines.append(f"{i}. {factor}")

    # Manglik Dosha
    lines.append("\n" + "─" * 90)
    lines.append("⚠️ MANGLIK DOSHA ANALYSIS")
    lines.append("─" * 90)
    manglik = pred.get("manglik_dosha", {})
    if manglik.get("present"):
        lines.append(f"Manglik Dosha is PRESENT (Severity: {manglik.get('severity', 'N/A')})")
        lines.append(f"Mars is placed in the {manglik.get('mars_house', '?')}th house ({manglik.get('mars_sign', '?')}), dignity: {manglik.get('mars_dignity', '?')}")
        if manglik.get("cancellations"):
            lines.append("Cancellations (protective factors):")
            for c in manglik["cancellations"]:
                lines.append(f"  ✓ {c}")
        if manglik.get("recommendation"):
            lines.append(f"Recommendation: {manglik['recommendation']}")
    else:
        lines.append(f"Manglik Dosha is NOT present. {manglik.get('reason', '')}")

    # A7 Darapada
    a7 = pred.get("a7_darapada", {})
    if a7.get("sign") and a7["sign"] != "Unknown":
        lines.append("\n" + "─" * 90)
        lines.append("🎭 A7 DARAPADA (Public Image of Marriage)")
        lines.append("─" * 90)
        lines.append(f"A7 Sign: {a7['sign']} (Lord {a7.get('lord', 'N/A')})")
        lines.append(f"Status: {a7.get('status', 'neutral').title()}")
        lines.append(f"Meaning: {a7.get('meaning', '')}")

    # Neecha Bhanga
    if pred.get("neecha_bhanga_effects"):
        lines.append("\n" + "─" * 90)
        lines.append("🔄 NEECHA BHANGA EFFECTS")
        lines.append("─" * 90)
        for planet, effect in pred["neecha_bhanga_effects"].items():
            lines.append(f"• {SHORT_TO_FULL.get(planet, planet)}: {effect}")

    # Ashtakavarga (Summary)
    lines.append("\n" + "─" * 90)
    lines.append("📊 ASHTAKAVARGA 7TH HOUSE (Summary)")
    lines.append("─" * 90)
    ashtak = pred.get("ashtakavarga", {})
    if 'points' in ashtak:
        lines.append(f"Points: {ashtak.get('points', 'N/A')}")
    if 'interpretation' in ashtak:
        lines.append(f"Interpretation: {ashtak.get('interpretation', 'N/A')}")

    # (Removed duplicate NAVAMSA VARGOTTAMA section)

    # Dasha Timing
    lines.append("\n" + "─" * 90)
    lines.append("⏳ MARRIAGE TIMING (Dasha Windows)")
    lines.append("─" * 90)
    dashas = pred.get("dasha_timing", {})
    if dashas.get("upcoming"):
        lines.append("Upcoming High-Probability Periods:")
        for p in dashas["upcoming"]:
            lines.append(f"  • {p['maha']} / {p['antara']} ({p['start']} to {p['end']}) — Score: {p['score']}/10")
    elif dashas.get("high_score_periods"):
        lines.append("High-Probability Periods (past or present):")
        for p in dashas["high_score_periods"]:
            lines.append(f"  • {p['maha']} / {p['antara']} ({p['start']} to {p['end']}) — Score: {p['score']}/10")
    else:
        lines.append("No high-score upcoming periods found.")

    lines.append("\n🌍 CURRENT TRANSIT EFFECTS")
    lines.append("─" * 90)
    transits = pred.get("current_transits", {})
    if transits.get("transiting_7th"):
        lines.append(f"Planets currently transiting the 7th house: {', '.join([SHORT_TO_FULL.get(p, p) for p in transits['transiting_7th']])}")
    else:
        lines.append("No current transit activation of the 7th house.")

    # Double Transit
    lines.append("\n" + "─" * 90)
    lines.append("⚡ DOUBLE TRANSIT (Ju+Sa Marriage Window)")
    lines.append("─" * 90)
    dt = pred.get("double_transit", {})
    if dt.get("active"):
        lines.append(
            "✅ **HIGHLY ACTIVE** - Jupiter + Saturn both aspecting marriage houses"
        )
        lines.append(
            f"Ju House {dt.get('ju_house', '?')}, Sa House {dt.get('sa_house', '?')}"
        )
        lines.append("Marriage **imminent** in this window!")
    else:
        if dt.get("reason"):
            lines.append(f"Not active: {dt['reason']}")
        else:
            lines.append("⏳ Not currently active")

    # Nakshatra Tara
    lines.append("\n" + "─" * 90)
    lines.append("🌙 NAKSHATRA TARA COMPATIBILITY")
    lines.append("─" * 90)
    tara = pred.get("tara_analysis", {})
    if "error" not in tara:
        for planet, tdata in tara.items():
            lines.append(
                f"{SHORT_TO_FULL.get(planet, planet)}-Moon: {tdata['name']} (#{tdata['tara']})"
            )
            lines.append(f"  {tdata['description']}")
    else:
        lines.append(f"⚠️ {tara.get('error')}")

    # D2 Financial
    lines.append("\n" + "─" * 90)
    lines.append("💰 D2 HORA - SPOUSE FAMILY FINANCES")
    lines.append("─" * 90)
    d2 = pred.get("d2_analysis", {})
    if d2.get("available"):
        lines.append(f"7L D2: {d2['h7_lord_d2_sign']} ({d2['h7_lord_d2_dignity']})")
        lines.append(f"UL-2nd D2 Strength: **{d2['financial_strength']}**")
        lines.append(f"Family Note: {d2['family_note']}")
    else:
        lines.append("D2 data unavailable")

    # D60 Karma
    lines.append("\n" + "─" * 90)
    lines.append("🔮 D60 SHASH TIAMSA - MARRIAGE KARMA")
    lines.append("─" * 90)
    d60 = pred.get("d60_analysis", {})
    if d60.get("available"):
        lines.append(f"7L D60: {d60['h7_lord_d60']}")
        lines.append(f"Venus D60: {d60['venus_d60']}")
        for note in d60["karma_notes"]:
            lines.append(f"• {note}")
        if d60.get("severe_karma"):
            lines.append(f"⚠️ **Severe**: {d60['remedy_note']}")
        else:
            lines.append(f"✅ {d60['remedy_note']}")
    else:
        lines.append("D60 data unavailable")

    # Nakshatra Insights
    if pred.get("nakshatra_insights"):
        lines.append("\n" + "─" * 90)
        lines.append("🌙 NAKSHATRA INSIGHTS")
        lines.append("─" * 90)
        for p, info in pred["nakshatra_insights"].items():
            lines.append(
                f"• {SHORT_TO_FULL.get(p, p)} in {info['nakshatra']} (ruled by {info['lord']}, deity {info['deity']})"
            )
            lines.append(f"  → {info['meaning']}")

    # Planetary War
    if pred.get("graha_yuddha"):
        lines.append("\n" + "─" * 90)
        lines.append("⚔️ GRAHA YUDDHA (Planetary War)")
        lines.append("─" * 90)
        for war in pred["graha_yuddha"]:
            lines.append(f"• {war['description']}")

    # Integrity Summary
    lines.append("\n" + "─" * 90)
    lines.append("🔒 PLANETARY INTEGRITY")
    lines.append("─" * 90)
    for p, data in pred.get("integrity_summary", {}).items():
        lines.append(
            f"• {SHORT_TO_FULL.get(p, p)}: {data.get('score', '?')}% - {data.get('label', 'Unknown')}"
        )

    # Confidence Factors
    lines.append("\n" + "─" * 90)
    lines.append(f"✅ CONFIRMING FACTORS ({len(pred.get('confidence_factors', []))})")
    lines.append("─" * 90)
    for factor in pred.get("confidence_factors", []):
        lines.append(f"• {factor}")

    lines.append("\n" + "=" * 90)
    lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 90)

    # Glossary/Legend
    lines.append("\nGLOSSARY / LEGEND")
    lines.append("─" * 40)
    lines.append("Darakaraka: Planet with the lowest degree in the chart, represents the spouse.")
    lines.append("Atmakaraka: Planet with the highest degree, represents the soul's desire.")
    lines.append("Karakamsa: The sign occupied by Atmakaraka in the D9 (Navamsa) chart.")
    lines.append("Vargottama: A planet occupying the same sign in both D1 and D9 charts.")
    lines.append("Ashtakavarga: A point-based system to assess house/planet strength.")
    lines.append("D2 Hora: Divisional chart for wealth and family finances.")
    lines.append("D60 Shashtiamsa: Divisional chart for deep karma and past life influences.")
    lines.append("Manglik Dosha: Affliction caused by Mars in certain houses, affecting marriage.")
    lines.append("Neecha Bhanga: Cancellation of planetary debilitation.")
    lines.append("Double Transit: Simultaneous influence of Jupiter and Saturn on marriage houses.")
    lines.append("Tara: Nakshatra-based compatibility system.")
    lines.append("Upapada Lagna: Special ascendant for marriage and spouse analysis.")
    lines.append("Dasha: Planetary period system for timing events.")
    lines.append("Navamsa: D9 divisional chart, key for marriage and spiritual growth.")
    lines.append("Graha Yuddha: Planetary war, when two planets are close together.")
    lines.append("Functional Karaka: Key planet for marriage (Venus for men, Jupiter for women).")

    lines.append("\nFor more details, consult a professional Vedic astrologer.")
    return "\n".join(lines)

