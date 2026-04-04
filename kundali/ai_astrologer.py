# ai_astrologer.py
"""
AI Astrologer — Claude API integration for Vedic Kundali interpretation.

Builds a rich structured prompt from the kundali result dict and returns
a detailed AI-generated interpretation using Anthropic's Claude models.

Usage:
    from kundali.ai_astrologer import get_ai_interpretation

    interpretation = get_ai_interpretation(result, question="When will I get married?")

Requirements:
    pip install anthropic
    Set environment variable ANTHROPIC_API_KEY.
"""

import os
import json
import textwrap

try:
    import anthropic

    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

# Default model — can override via env var VEDIC_AI_MODEL
DEFAULT_MODEL = os.environ.get("VEDIC_AI_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.environ.get("VEDIC_AI_MAX_TOKENS", "2048"))
SYSTEM_PROMPT = textwrap.dedent(
    """\
    You are an expert Vedic astrologer with deep knowledge of:
    - Parashari system (BPHS), Jaimini system, Nadi astrology
    - Planetary dignities, yogas, dashas, divisional charts
    - Muhurtha, Tajika Solar Return, Pancha Pakshi, Nakshatra analysis
    - Classical Sanskrit texts: Brihat Parashara Hora Shastra, Phaladeepika,
      Saravali, Brihat Jataka, Uttara Kalamrita, and Dasadhyayi

    When analyzing a kundali:
    1. Start with the Lagna (Ascendant) — the body, self, and overall life path
    2. Examine Moon sign and nakshatra — emotional temperament and mental nature
    3. Assess planetary dignities, strengths (Shadbala), and aspects
    4. Identify major yogas and their fructification potential
    5. Analyse current Vimshottari dasha for timing of events
    6. Consider divisional charts (especially D9 for marriage, D10 for career)
    7. Provide practical, compassionate guidance without fatalistic predictions

    Always speak in a warm, insightful tone. Provide specific, actionable insights.
    When uncertain, state possibilities rather than absolute predictions.
    Mention relevant remedies (mantras, gemstones, fasting, charity) where appropriate.
"""
)


# ─── Prompt Builders ──────────────────────────────────────────────────────────


def _format_planet_summary(result: dict) -> str:
    """Build a compact planet summary string for the prompt."""
    planets = result.get("planets", {})
    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    lines = []
    for pl in order:
        if pl not in planets:
            continue
        d = planets[pl]
        flags = []
        if d.get("retro"):
            flags.append("R")
        if d.get("combust"):
            flags.append("C")
        nb = " (Neecha Bhanga)" if d.get("neecha_bhanga") else ""
        flag_str = f" [{','.join(flags)}]" if flags else ""
        lines.append(
            f"  {pl}: {d['sign']:12} {d.get('deg',0):5.1f}° | {d['nakshatra'][:14]:14} "
            f"| {d.get('dignity','?'):12}{nb}{flag_str}"
        )
    return "\n".join(lines)


def _format_houses(result: dict) -> str:
    """Build a compact house occupancy string."""
    houses = result.get("houses", {})
    lagna = result.get("lagna_sign", "")
    signs = [
        "Aries",
        "Taurus",
        "Gemini",
        "Cancer",
        "Leo",
        "Virgo",
        "Libra",
        "Scorpio",
        "Sagittarius",
        "Capricorn",
        "Aquarius",
        "Pisces",
    ]
    lagna_idx = signs.index(lagna) if lagna in signs else 0
    lines = []
    for h in range(1, 13):
        sign_idx = (lagna_idx + h - 1) % 12
        sign = signs[sign_idx]
        occupants = [p for p in houses.get(h, []) if p != "Asc"]
        content = " ".join(occupants) if occupants else "—"
        lines.append(f"  H{h:02d} ({sign:12}): {content}")
    return "\n".join(lines)


def _format_yogas(result: dict, max_yogas: int = 15) -> str:
    yogas = result.get("yogas", [])
    if isinstance(yogas, list):
        return "\n".join(f"  • {y}" for y in yogas[:max_yogas])
    return "  No yogas detected."


def _format_dasha(result: dict) -> str:
    vim = result.get("vimshottari", {})
    if not vim:
        return "  Dasha data unavailable."
    md = vim.get("current_md", "?")
    ad = vim.get("current_ad", "?")
    pd = result.get("vimshottari_pd", {}).get("current_pd", "?")
    lines = [f"  Current Mahadasha : {md}"]
    lines.append(f"  Current Antardasha: {ad}")
    lines.append(f"  Current Pratyantar: {pd}")
    # Upcoming dashas
    birth_jd = result.get("birth_jd", 0)
    birth_yr = result.get("birth_year", 2000)
    mds = vim.get("mahadasas", [])[:5]
    if mds:
        lines.append("  Upcoming Mahadashas:")
        for m in mds:
            try:
                s_yr = int(birth_yr + (m["start_jd"] - birth_jd) / 365.25)
                e_yr = int(birth_yr + (m["end_jd"] - birth_jd) / 365.25)
                lines.append(f"    {m['lord']:8} ({s_yr}–{e_yr})")
            except Exception:
                lines.append(f"    {m.get('lord','?')}")
    return "\n".join(lines)


def _format_navamsa(result: dict) -> str:
    nav = result.get("navamsa", {})
    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    lines = []
    for pl in order:
        if pl in nav:
            lines.append(f"  {pl}: {nav[pl].get('sign','?')}")
    return "\n".join(lines) if lines else "  Navamsa data unavailable."


def _format_shadbala(result: dict) -> str:
    sb_data = result.get("shadbala", {})
    if not sb_data:
        return "  Shadbala data unavailable."
    rows = []
    for pl, data in sb_data.items():
        if isinstance(data, dict):
            rupas = data.get("rupas", data.get("total_rupas", data.get("total", 0)))
            strong = "STRONG" if data.get("strong") else "weak"
            rows.append(f"  {pl}: {rupas:.2f} Rupas ({strong})")
    return "\n".join(rows) if rows else "  Shadbala unavailable."


def _format_pancha_pakshi(result: dict) -> str:
    pp = result.get("pancha_pakshi", {})
    if not pp:
        return "  Pancha Pakshi data unavailable."
    lines = [
        f"  Birth Bird    : {pp.get('birth_bird','?')}",
        f"  Moon Nakshatra: {pp.get('moon_nakshatra','?')}",
        f"  Current Yama  : {pp.get('current_yama','?')} ({'Day' if pp.get('is_day') else 'Night'})",
        f"  Activity Now  : {pp.get('current_activity','?')} (Strength {pp.get('current_strength','?')}/5)",
        f"  Advice        : {pp.get('current_advice','')}",
    ]
    return "\n".join(lines)


def _format_problems(result: dict) -> str:
    problems = result.get("problems", [])
    if not problems:
        return "  No major doshas detected."
    lines = []
    for p in problems[:8]:
        summary = p.get("summary", "")
        if summary:
            lines.append(f"  • {summary}")
    return "\n".join(lines) if lines else "  No major doshas."


def build_kundali_prompt(result: dict, question: str | None = None) -> str:
    """
    Build a comprehensive Vedic astrology prompt from the kundali result dict.
    """
    name = result.get("name", "the native")
    gender = result.get("gender", "Unknown")
    birth_date = result.get("birth_date", "?")
    birth_time = result.get("birth_time", "?")
    birth_place = result.get("birth_place", "?")
    lagna = result.get("lagna_sign", "?")
    lagna_deg = result.get("lagna_deg", 0)
    moon_sign = result.get("moon_sign", "?")
    moon_nak = result.get("moon_nakshatra", "?")
    ayanamsa = result.get("ayanamsa", "Lahiri")
    pan = result.get("panchanga", {})

    prompt = textwrap.dedent(
        f"""\
        ════════════════════════════════════════════════════════════════
        VEDIC KUNDALI — Full Analysis Request
        ════════════════════════════════════════════════════════════════

        NATIVE DETAILS
        ──────────────
        Name        : {name}
        Gender      : {gender}
        Birth Date  : {birth_date}
        Birth Time  : {birth_time}
        Birth Place : {birth_place}
        Ayanamsa    : {ayanamsa}

        PANCHANGA
        ─────────
        Tithi  : {pan.get('tithi','?')}
        Vara   : {pan.get('vara','?')}
        Yoga   : {pan.get('yoga','?')}
        Karana : {pan.get('karana','?')}
        Nakshatra (Moon): {moon_nak}

        LAGNA & MOON
        ────────────
        Ascendant   : {lagna} {lagna_deg:.2f}°
        Moon Sign   : {moon_sign}
        Moon Nak    : {moon_nak}
        7th Lord    : {result.get('seventh_lord','?')}

        PLANETARY POSITIONS (D1 — Rasi Chart)
        ──────────────────────────────────────
        [Planet: Sign | Degree | Nakshatra | Dignity | Flags]
    """
    )
    prompt += _format_planet_summary(result) + "\n\n"

    prompt += textwrap.dedent(
        """\
        HOUSES (Whole Sign)
        ───────────────────
    """
    )
    prompt += _format_houses(result) + "\n\n"

    prompt += textwrap.dedent(
        """\
        NAVAMSA (D9) — Marriage/Dharma
        ───────────────────────────────
    """
    )
    prompt += _format_navamsa(result) + "\n\n"

    prompt += textwrap.dedent(
        """\
        MAJOR YOGAS DETECTED
        ─────────────────────
    """
    )
    prompt += _format_yogas(result) + "\n\n"

    prompt += textwrap.dedent(
        """\
        VIMSHOTTARI DASHA
        ─────────────────
    """
    )
    prompt += _format_dasha(result) + "\n\n"

    prompt += textwrap.dedent(
        """\
        SHADBALA (Planetary Strength)
        ──────────────────────────────
    """
    )
    prompt += _format_shadbala(result) + "\n\n"

    prompt += textwrap.dedent(
        """\
        PANCHA PAKSHI (Bird Activity System)
        ─────────────────────────────────────
    """
    )
    prompt += _format_pancha_pakshi(result) + "\n\n"

    prompt += textwrap.dedent(
        """\
        DOSHAS & CHALLENGES
        ────────────────────
    """
    )
    prompt += _format_problems(result) + "\n\n"

    # Optional tajika / muhurtha
    tajika = result.get("tajika", {})
    if tajika:
        year_lord = tajika.get("year_lord", "?")
        muntha = tajika.get("muntha", {}).get("sign", "?")
        mun_house = tajika.get("muntha", {}).get("house_from_lagna", "?")
        prompt += "TAJIKA SOLAR RETURN\n───────────────────\n"
        prompt += f"  Year : {tajika.get('year','?')} | Year Lord: {year_lord}\n"
        prompt += f"  Muntha: {muntha} (House {mun_house})\n\n"

    muhurtha = result.get("muhurtha", {})
    if muhurtha:
        score = muhurtha.get("total_score", muhurtha.get("overall_score", "?"))
        grade = muhurtha.get("grade", "?")
        prompt += "MUHURTHA (Birth Moment Quality)\n─────────────────────────────────\n"
        prompt += f"  Score: {score}/100 ({grade})\n\n"

    prompt += "════════════════════════════════════════════════════════════════\n"

    # Specific question
    if question:
        prompt += textwrap.dedent(
            f"""\
            SPECIFIC QUESTION FROM NATIVE
            ──────────────────────────────
            {question}

            Please provide a thorough Vedic astrological analysis addressing:
            1. The answer to the specific question above
            2. Key planetary combinations supporting or challenging this area
            3. Timing via current Vimshottari dasha
            4. Remedies or practical recommendations
            5. Overall life potential summary (brief)
        """
        )
    else:
        prompt += textwrap.dedent(
            """\
            Please provide a comprehensive Vedic astrological interpretation covering:
            1. Overall personality and life path (Lagna + Moon analysis)
            2. Career and wealth potential (2nd, 10th, 11th house lords + yogas)
            3. Marriage and relationships (7th house, Navamsa, Venus)
            4. Health and longevity (1st, 6th, 8th houses)
            5. Spiritual inclination and dharma (9th house, Jupiter)
            6. Current life phase based on Vimshottari dasha
            7. Key opportunities in the next 3–5 years
            8. Suggested remedies for planetary afflictions
        """
        )

    return prompt


# ─── Main API ─────────────────────────────────────────────────────────────────


def get_ai_interpretation(
    result: dict,
    question: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> str:
    """
    Get an AI-generated Vedic astrological interpretation of the kundali.

    Args:
        result:   Kundali result dict (from calculate_kundali).
        question: Optional specific question (e.g. "When will I marry?").
        model:    Anthropic model ID (default: claude-sonnet-4-6).
        api_key:  Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.

    Returns:
        String interpretation from Claude, or an error/fallback message.
    """
    if not _ANTHROPIC_AVAILABLE:
        return (
            "⚠️  AI Astrologer requires the 'anthropic' package.\n"
            "Install it with: pip install anthropic\n"
            "Then set the ANTHROPIC_API_KEY environment variable."
        )

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return (
            "⚠️  ANTHROPIC_API_KEY not set.\n"
            "Please set the environment variable:\n"
            "  export ANTHROPIC_API_KEY='your-key-here'\n\n"
            "--- Offline Fallback Analysis ---\n" + _offline_fallback(result, question)
        )

    model = model or DEFAULT_MODEL
    prompt = build_kundali_prompt(result, question)

    try:
        client = anthropic.Anthropic(api_key=key)
        message = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = message.content[0].text if message.content else ""
        return response_text

    except Exception as e:
        return (
            f"⚠️  Claude API error: {e}\n\n"
            "--- Offline Fallback Analysis ---\n" + _offline_fallback(result, question)
        )


def _offline_fallback(result: dict, question: str | None = None) -> str:
    """Generate a basic text analysis without the AI API."""
    lagna = result.get("lagna_sign", "?")
    moon_s = result.get("moon_sign", "?")
    moon_n = result.get("moon_nakshatra", "?")
    name = result.get("name", "the native")
    yogas = result.get("yogas", [])
    vim = result.get("vimshottari", {})
    md = vim.get("current_md", "?")
    ad = vim.get("current_ad", "?")
    problems = result.get("problems", [])

    lines = [
        f"Vedic Kundali Analysis for {name}",
        "=" * 50,
        f"Ascendant   : {lagna}",
        f"Moon Sign   : {moon_s} in {moon_n}",
        "",
        "Active Yogas:",
    ]
    for y in yogas[:8]:
        lines.append(f"  • {y}")

    lines += [
        "",
        f"Current Dasha: {md}/{ad}",
        "",
        "Key Challenges:",
    ]
    for p in problems[:5]:
        s = p.get("summary", "")
        if s:
            lines.append(f"  • {s}")

    if question:
        lines += [
            "",
            f"Question: {question}",
            "(Set ANTHROPIC_API_KEY for AI analysis)",
        ]

    return "\n".join(lines)


# ─── Convenience Helpers ──────────────────────────────────────────────────────


def get_marriage_analysis(result: dict) -> str:
    """Focused marriage / relationship analysis."""
    return get_ai_interpretation(
        result,
        question=(
            "Please analyse the marriage and relationship potential in detail. "
            "Include: 7th house and its lord, Venus placement, Navamsa (D9) analysis, "
            "Upapada Lagna, timing of marriage via Vimshottari dasha, and any yoga "
            "supporting or delaying marriage. Provide gemstone and mantra remedies."
        ),
    )


def get_career_analysis(result: dict) -> str:
    """Focused career / profession analysis."""
    return get_ai_interpretation(
        result,
        question=(
            "Please analyse the career, profession, and financial potential. "
            "Cover: 10th house and its lord, 2nd and 11th lords, Dasamsa (D10), "
            "current dasha for career peaks, and best career fields for this chart. "
            "Provide specific timing for career breakthroughs."
        ),
    )


def get_spiritual_analysis(result: dict) -> str:
    """Focused spiritual path analysis."""
    return get_ai_interpretation(
        result,
        question=(
            "Please analyse the spiritual inclination and dharmic path. "
            "Cover: 9th house, Jupiter, Ketu, D20 (Vimsha), any Sanyasa or "
            "Moksha yogas, and the soul's evolutionary purpose from this chart."
        ),
    )
