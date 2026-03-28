# spouse/report.py
from datetime import datetime
from constants import SHORT_TO_FULL, ZODIAC_SIGNS


def generate_spouse_report(pred):
    """Formatted report from the prediction dictionary."""
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

    # Spouse Profile
    lines.append("\n" + "─" * 90)
    lines.append("👤 SPOUSE PROFILE")
    lines.append("─" * 90)
    profile = pred.get("spouse_profile", {})
    lines.append(f"7th House Sign: {profile.get('7th_house_sign', 'N/A')}")
    lines.append(
        f"7th Lord: {SHORT_TO_FULL.get(profile.get('7th_lord', ''), profile.get('7th_lord', ''))}"
    )
    lines.append(f"Darakaraka: {profile.get('darakaraka', 'N/A')}")
    lines.append(f"Venus Functional Nature: {profile.get('venus_functional', 'N/A')}")
    lines.append(
        f"Jupiter Functional Nature: {profile.get('jupiter_functional', 'N/A')}"
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

    # Venus-Mars
    lines.append("\n" + "─" * 90)
    lines.append("❤️‍🔥 VENUS-MARS DYNAMICS")
    lines.append("─" * 90)
    vm = pred.get("venus_mars", {})
    lines.append(f"Status: {vm.get('status', 'N/A')}")
    lines.append(f"Effect: {vm.get('effect', 'N/A')}")

    # Yogas
    if pred.get("marriage_yogas"):
        lines.append("\n" + "─" * 90)
        lines.append("🔮 MARRIAGE YOGAS")
        lines.append("─" * 90)
        for yoga in pred["marriage_yogas"]:
            lines.append(f"• {yoga['name']}")

    # Meeting & Profession
    lines.append("\n" + "─" * 90)
    lines.append("📍 MEETING CIRCUMSTANCES")
    lines.append("─" * 90)
    meet = pred.get("meeting", {})
    lines.append(f"Most Likely: {meet.get('primary', 'N/A')}")

    lines.append("\n" + "─" * 90)
    lines.append("💼 SPOUSE PROFESSION")
    lines.append("─" * 90)
    prof = pred.get("profession", {})
    lines.append(f"Primary Field: {prof.get('primary', 'N/A')}")
    lines.append(f"Secondary Field: {prof.get('secondary', 'N/A')}")

    # Upapada
    lines.append("\n" + "─" * 90)
    lines.append("🏠 UPAPADA LAGNA (Marriage House)")
    lines.append("─" * 90)
    ul = pred.get("upapada", {})
    lines.append(
        f"Upapada Sign: {ul.get('sign', 'N/A')} (Lord {ul.get('lord', 'N/A')}, Dignity {ul.get('dignity', 'N/A')})"
    )
    lines.append(
        f"Strength: {'Strong - Stable marriage' if ul.get('strong') else 'Moderate - needs effort'}"
    )
    lines.append(f"2nd from UL: {ul.get('2nd_meaning', 'N/A')}")
    lines.append(f"8th from UL: {ul.get('8th_meaning', 'N/A')}")

    # Arudha Lagna relationship
    lines.append("\n" + "─" * 90)
    lines.append("🔶 ARUDHA LAGNA (AL) – Social Image of Marriage")
    lines.append("─" * 90)
    al = pred.get("arudha_lagna", {})
    ul_sign = ul.get("sign", "")
    if al and ul_sign in ZODIAC_SIGNS:
        al_idx = al.get("index", -1)
        ul_idx = ZODIAC_SIGNS.index(ul_sign)
        if al_idx != -1 and ul_idx != -1:
            diff = (ul_idx - al_idx) % 12
            if diff in [1, 11]:
                al_ul_relation = "2/12 from AL – marriage will be expensive, lavish, or involve foreign elements."
            elif diff in [5, 7]:
                al_ul_relation = "6/8 from AL – marriage may face societal opposition, be hidden, or unconventional."
            else:
                al_ul_relation = "Neutral – marriage will be socially accepted."
            lines.append(
                f"AL: {al.get('sign', 'N/A')} | UL: {ul_sign} | Relationship: {al_ul_relation}"
            )
        else:
            lines.append("Unable to compute AL-UL relationship.")
    else:
        lines.append("Unable to compute AL-UL relationship.")

    # D9 7th House
    lines.append("\n" + "─" * 90)
    lines.append("🔷 NAVAMSA (D9) 7TH HOUSE - Soul Marriage Level")
    lines.append("─" * 90)
    d9_7 = pred.get("d9_seventh_house", {})
    lines.append(f"D9 7th House Sign: {d9_7.get('d9_7th_sign', 'N/A')}")
    # Fixed f-string: add missing closing parenthesis after the second get()
    d9_lord_short = d9_7.get("d9_7th_lord", "")
    d9_lord_full = SHORT_TO_FULL.get(d9_lord_short, d9_lord_short)
    lines.append(
        f"D9 7th Lord: {d9_lord_full} in {d9_7.get('d9_7th_lord_sign', 'N/A')} ({d9_7.get('d9_7th_lord_dignity', 'N/A')})"
    )
    if d9_7.get("planets_in_d9_7th"):
        lines.append(
            f"Planets in D9 7th: {', '.join([SHORT_TO_FULL.get(p, p) for p in d9_7['planets_in_d9_7th']])}"
        )
    lines.append(f"Interpretation: {d9_7.get('interpretation', 'N/A')}")

    # Aspects on 7th
    lines.append("\n" + "─" * 90)
    lines.append("👁️ ASPECTS ON 7TH HOUSE")
    lines.append("─" * 90)
    aspects = pred.get("aspects_on_7th", {}).get("aspects", [])
    if aspects:
        for asp in aspects:
            lines.append(f"• {asp['planet']} {asp['type']} on {asp['target']}")
    else:
        lines.append("No significant aspects detected.")

    # House Lord Placements
    lines.append("\n" + "─" * 90)
    lines.append("🏡 HOUSE LORD PLACEMENTS")
    lines.append("─" * 90)
    lords = pred.get("lord_placements", {})
    if lords.get("seventh_house"):
        lines.append(
            f"7th House Lord: {lords['seventh_house'].get('interpretation', 'N/A')}"
        )
    if lords.get("second_house"):
        lines.append(
            f"2nd House Lord: {lords['second_house'].get('interpretation', 'N/A')}"
        )
    if lords.get("fifth_house"):
        lines.append(
            f"5th House Lord: {lords['fifth_house'].get('interpretation', 'N/A')}"
        )

    # Marriage Type
    lines.append("\n" + "─" * 90)
    lines.append("💑 MARRIAGE TYPE PREDICTION")
    lines.append("─" * 90)
    mtype = pred.get("marriage_type", {})
    lines.append(f"Category: {mtype.get('category', 'N/A')}")
    lines.append(f"Probability: {mtype.get('probability', 'N/A')}")
    if mtype.get("indicators"):
        lines.append("Indicators:")
        for ind in mtype["indicators"]:
            lines.append(f"  • {ind}")

    # Manglik Dosha
    lines.append("\n" + "─" * 90)
    lines.append("⚠️ MANGLIK DOSHA ANALYSIS")
    lines.append("─" * 90)
    manglik = pred.get("manglik_dosha", {})
    if manglik.get("present"):
        lines.append(f"Status: PRESENT ({manglik.get('severity', 'N/A')})")
        lines.append(
            f"Mars in {manglik.get('mars_house', '?')}th house ({manglik.get('mars_sign', '?')}) - {manglik.get('mars_dignity', '?')}"
        )
        if manglik.get("cancellations"):
            lines.append("Cancellations:")
            for c in manglik["cancellations"]:
                lines.append(f"  ✓ {c}")
    else:
        lines.append(f"Status: NOT PRESENT - {manglik.get('reason', '')}")

    # Neecha Bhanga
    if pred.get("neecha_bhanga_effects"):
        lines.append("\n" + "─" * 90)
        lines.append("🔄 NEECHA BHANGA EFFECTS")
        lines.append("─" * 90)
        for planet, effect in pred["neecha_bhanga_effects"].items():
            lines.append(f"• {planet}: {effect}")

    # Ashtakavarga
    lines.append("\n" + "─" * 90)
    lines.append("📊 ASHTAKAVARGA 7TH HOUSE")
    lines.append("─" * 90)
    ashtak = pred.get("ashtakavarga", {})
    lines.append(f"Points: {ashtak.get('points', 'N/A')}")
    lines.append(f"Interpretation: {ashtak.get('interpretation', 'N/A')}")

    # Navamsa Vargottama
    lines.append("\n" + "─" * 90)
    lines.append("📈 NAVAMSA VARGOTTAMA")
    lines.append("─" * 90)
    nav = pred.get("navamsa_strength", {})
    lines.append(f"Vargottama Planets: {nav.get('count', 0)}")
    if nav.get("vargottama"):
        lines.append(
            f"  → {', '.join([SHORT_TO_FULL.get(p, p) for p in nav['vargottama']])}"
        )

    # Dasha Timing
    lines.append("\n" + "─" * 90)
    lines.append("⏳ MARRIAGE TIMING (Dasha Windows)")
    lines.append("─" * 90)
    dashas = pred.get("dasha_timing", {})
    if dashas.get("upcoming"):
        lines.append("Upcoming High-Probability Periods:")
        for p in dashas["upcoming"]:
            lines.append(
                f"  • {p['maha']}/{p['antara']} ({p['start']}-{p['end']}) - Score {p['score']}/10"
            )
    else:
        lines.append("No high-score upcoming periods found.")

    lines.append("\n🌍 CURRENT TRANSIT EFFECTS")
    lines.append("─" * 90)
    transits = pred.get("current_transits", {})
    if transits.get("transiting_7th"):
        lines.append(
            f"Planets transiting 7th house: {', '.join(transits['transiting_7th'])}"
        )
    else:
        lines.append("No current transit activation of 7th house.")

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

    return "\n".join(lines)
