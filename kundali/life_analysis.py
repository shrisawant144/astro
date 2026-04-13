"""
Advanced life analysis synthesis layer.

Builds a broad life-domain view from a calculated chart and the existing
decision-engine outputs. This module intentionally avoids deterministic death
prediction; it models vitality, risk concentration, resilience, and timing
windows instead.
"""

import datetime
import re

from .constants import zodiac_signs, sign_lords, short_to_full

_NATURAL_BENEFICS = {"Ju", "Ve", "Mo", "Me"}
_NATURAL_MALEFICS = {"Sa", "Ma", "Ra", "Ke", "Su"}

_PHASE_THEMES = {
    "Sun": "identity, visibility, leadership, and decisive self-expression",
    "Moon": "emotions, family, adaptability, and public responsiveness",
    "Mars": "drive, conflict, courage, and action under pressure",
    "Mercury": "learning, trade, writing, networking, and skill-building",
    "Jupiter": "wisdom, teaching, expansion, ethics, and long-term growth",
    "Venus": "relationships, beauty, comfort, values, and social ease",
    "Saturn": "discipline, karmic dues, endurance, structure, and slow mastery",
    "Rahu": "ambition, foreign links, unconventional change, and obsession",
    "Ketu": "detachment, spirituality, hidden work, research, and inner pruning",
}


def _planet_full_name(value):
    text = str(value or "").strip()
    return short_to_full.get(text, text)


def _extract_dasha_lord(value):
    if isinstance(value, dict):
        value = value.get("lord", value.get("dasha_lord", ""))
    return _planet_full_name(value)


def _lord_of(house_no, lagna_sign):
    if lagna_sign not in zodiac_signs:
        lagna_sign = "Aries"
    idx = zodiac_signs.index(lagna_sign)
    sign = zodiac_signs[(idx + house_no - 1) % 12]
    return sign_lords[sign]


def _planets_in_house(houses, house_no):
    values = houses.get(house_no)
    if values is None:
        values = houses.get(str(house_no), [])
    return list(values or [])


def _planet_strength_label(planet, planets_data):
    p = planets_data.get(planet, {})
    dig = p.get("dignity", "")
    score = 0
    if dig in ("Exalt", "Own"):
        score += 3
    elif dig == "Friend":
        score += 2
    elif dig in ("Neutral", ""):
        score += 1
    elif dig in ("Enemy", "Debilitated"):
        score -= 1
    if p.get("combust"):
        score -= 2
    if p.get("retro") and planet not in ("Ra", "Ke"):
        score -= 1
    if p.get("neecha_bhanga"):
        score += 1
    if score >= 3:
        return "strong"
    if score >= 1:
        return "moderate"
    return "weak"


def _strength_points(label):
    return {"strong": 18, "moderate": 8, "weak": -12}.get(str(label).lower(), 0)


def _clamp_score(score):
    return max(0, min(100, int(round(score))))


def _score_label(score):
    score = _clamp_score(score)
    if score >= 78:
        return "Strong"
    if score >= 63:
        return "Promising"
    if score >= 48:
        return "Mixed"
    return "Needs Attention"


def _clean_list(items, limit=6):
    seen = set()
    cleaned = []
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _domain_entry(label, score, summary, drivers=None, advice=""):
    score = _clamp_score(score)
    return {
        "label": label,
        "score": score,
        "status": _score_label(score),
        "summary": summary,
        "drivers": _clean_list(drivers or [], limit=6),
        "advice": str(advice or "").strip(),
    }


def _event_periods(result, event_name, limit=2):
    periods = []
    for line in result.get("timings", {}).get(event_name, []):
        lower = str(line).lower()
        if "karmic seed" in lower or "formative" in lower or "[past]" in lower:
            continue
        periods.append(str(line).strip())
        if len(periods) >= limit:
            break
    return periods


def _extract_start_year(text):
    match = re.search(r"\((\d{4})-(\d{4})\)", str(text))
    return int(match.group(1)) if match else 9999


def _timing_status(text):
    if "[now]" in str(text).lower():
        return "Current"
    return "Upcoming"


def _build_timing_overview(result):
    entries = []
    timing_map = [
        ("Relationships", "Marriage"),
        ("Career", "Career Rise / Fame"),
        ("Wealth", "Major Wealth / Property"),
        ("Family", "Children / Progeny"),
    ]
    for domain, event_name in timing_map:
        for line in _event_periods(result, event_name, limit=2):
            entries.append(
                {
                    "domain": domain,
                    "event": event_name,
                    "period": line,
                    "status": _timing_status(line),
                    "sort_year": _extract_start_year(line),
                }
            )
    entries.sort(key=lambda item: (0 if item["status"] == "Current" else 1, item["sort_year"], item["domain"]))
    return [
        {
            "domain": item["domain"],
            "event": item["event"],
            "period": item["period"],
            "status": item["status"],
        }
        for item in entries[:8]
    ]


def _future_sensitive_dashas(result, lords_full, limit=3):
    birth_year = result.get("birth_year")
    birth_jd = result.get("birth_jd")
    if birth_year is None or birth_jd is None:
        return []

    current_year = datetime.datetime.now().year
    target = {str(name) for name in lords_full}
    windows = []
    for md in result.get("vimshottari", {}).get("mahadasas", []):
        lord = _planet_full_name(md.get("lord", ""))
        if lord not in target:
            continue
        try:
            start_year = int(birth_year + (md["start_jd"] - birth_jd) / 365.25)
            end_year = int(birth_year + (md["end_jd"] - birth_jd) / 365.25)
        except Exception:
            continue
        if end_year < current_year:
            continue
        windows.append(f"{lord} Mahadasha ({start_year}-{end_year})")
        if len(windows) >= limit:
            break
    return windows


def _format_ranked_domains(items):
    return [
        {"domain": item["label"], "score": item["score"], "status": item["status"]}
        for item in items
    ]


def build_life_analysis(result, decisions_bundle=None):
    """Return a high-level life synthesis from chart data and decision outputs."""
    decisions_bundle = decisions_bundle or {}
    lagna = result.get("lagna_sign", "Aries")
    moon_sign = result.get("moon_sign", "")
    planets = result.get("planets", {})
    houses = result.get("houses", {})

    current_md = _extract_dasha_lord(result.get("vimshottari", {}).get("current_md"))
    current_ad = _extract_dasha_lord(result.get("vimshottari", {}).get("current_ad"))
    phase_theme = _PHASE_THEMES.get(
        current_md,
        "the dasha lord's significations are shaping the present life chapter",
    )

    lord1 = _lord_of(1, lagna)
    lord4 = _lord_of(4, lagna)
    lord5 = _lord_of(5, lagna)
    lord7 = _lord_of(7, lagna)
    lord8 = _lord_of(8, lagna)
    lord9 = _lord_of(9, lagna)
    lord10 = _lord_of(10, lagna)
    lord12 = _lord_of(12, lagna)

    lagna_strength = _planet_strength_label(lord1, planets)
    moon_strength = _planet_strength_label("Mo", planets)
    sun_strength = _planet_strength_label("Su", planets)
    lord4_strength = _planet_strength_label(lord4, planets)
    lord5_strength = _planet_strength_label(lord5, planets)
    lord8_strength = _planet_strength_label(lord8, planets)
    lord9_strength = _planet_strength_label(lord9, planets)
    lord12_strength = _planet_strength_label(lord12, planets)
    saturn_strength = _planet_strength_label("Sa", planets)
    jupiter_strength = _planet_strength_label("Ju", planets)

    career = decisions_bundle.get("career", {})
    marriage = decisions_bundle.get("marriage", {})
    business = decisions_bundle.get("business", {})
    health = decisions_bundle.get("health", {})
    travel = decisions_bundle.get("travel", {})
    education = decisions_bundle.get("education", {})

    first_house = _planets_in_house(houses, 1)
    fourth_house = _planets_in_house(houses, 4)
    fifth_house = _planets_in_house(houses, 5)
    eighth_house = _planets_in_house(houses, 8)
    twelfth_house = _planets_in_house(houses, 12)

    identity_score = 52
    identity_score += _strength_points(lagna_strength)
    identity_score += int(_strength_points(moon_strength) * 0.5)
    identity_score += int(_strength_points(sun_strength) * 0.4)
    identity_score += min(10, 5 * len([p for p in first_house if p in _NATURAL_BENEFICS]))
    identity_score -= min(10, 5 * len([p for p in first_house if p in {"Sa", "Ra", "Ke"}]))

    career_bindus = career.get("tenth_house_ashtakavarga_bindus", 0)
    career_score = 50
    career_score += _strength_points(career.get("tenth_lord_strength"))
    career_score += 12 if career.get("good_period_for_career_change") else -4
    career_score += min(8, len(career.get("recommended_fields", [])))
    if isinstance(career_bindus, (int, float)):
        if career_bindus >= 28:
            career_score += 10
        elif career_bindus <= 20:
            career_score -= 8

    wealth_score = 50
    wealth_score += min(18, len(business.get("wealth_yogas", [])) * 6)
    wealth_score += _strength_points(business.get("fifth_lord_strength"))
    wealth_score += 12 if business.get("good_period_for_business") else -5
    jupiter_transit = business.get("jupiter_transit_house")
    if isinstance(jupiter_transit, int):
        if jupiter_transit in (2, 5, 9, 11):
            wealth_score += 8
        elif jupiter_transit in (6, 8, 12):
            wealth_score -= 8

    relationship_score = 50
    relationship_score += _strength_points(marriage.get("seventh_lord_strength"))
    relationship_score += _strength_points(marriage.get("venus_strength"))
    relationship_score += 10 if marriage.get("favorable_dasha_for_marriage") else -4
    relationship_score += 6 if marriage.get("favorable_periods") else 0
    relationship_score -= min(18, len(marriage.get("marriage_blockers", [])) * 6)

    family_score = 50
    family_score += _strength_points(lord4_strength)
    family_score += _strength_points(lord5_strength)
    family_score += int(_strength_points(moon_strength) * 0.4)
    family_score += int(_strength_points(jupiter_strength) * 0.5)
    family_score += 6 if any(p in _NATURAL_BENEFICS for p in fourth_house) else 0
    family_score -= 6 if any(p in {"Sa", "Ra", "Ke"} for p in fourth_house) else 0
    family_score += 6 if any(p in _NATURAL_BENEFICS for p in fifth_house) else 0
    family_score -= 4 if any(p in {"Sa", "Ra", "Ke"} for p in fifth_house) else 0

    health_score = 58
    health_score += _strength_points(health.get("overall_vitality", health.get("lagna_lord_strength")))
    health_score -= min(20, len(health.get("vulnerable_planets", [])) * 6)
    health_score -= 10 if health.get("risky_health_period") else 0
    health_score -= 8 if health.get("sade_sati_active") else 0
    health_score -= 4 if health.get("health_risk_areas_8th") else 0

    learning_score = education.get("academic_ability_score", 50)
    learning_score += 8 if education.get("good_period_for_education") else -2
    learning_score += int(_strength_points(lord9_strength) * 0.4)

    travel_score = 42
    travel_score += int(travel.get("foreign_indicators_score", 0)) * 8
    travel_score += int(_strength_points(lord9_strength) * 0.4)
    travel_score += int(_strength_points(lord12_strength) * 0.4)
    travel_score += 10 if travel.get("good_period_for_travel") else -2
    travel_score += 6 if any(p in {"Ju", "Ke"} for p in twelfth_house) else 0

    family_windows = _event_periods(result, "Children / Progeny", limit=1)
    timing_overview = _build_timing_overview(result)

    domains = {
        "self_and_identity": _domain_entry(
            "Self & Identity",
            identity_score,
            (
                f"{lagna} lagna with {moon_sign or 'unknown'} Moon makes self-definition a major life theme. "
                f"{_planet_full_name(lord1)} is {lagna_strength}, and the current {current_md or '-'} period emphasizes "
                f"{phase_theme}."
            ),
            drivers=[
                f"Lagna lord: {_planet_full_name(lord1)} ({lagna_strength})",
                f"Moon strength: {moon_strength}",
                f"Sun strength: {sun_strength}",
                f"1st-house planets: {', '.join(_planet_full_name(p) for p in first_house) or 'none'}",
            ],
            advice="Protect your energy, routines, and decision quality; identity gains compound when your body and mind are steady.",
        ),
        "career_and_public_life": _domain_entry(
            "Career & Public Life",
            career_score,
            (
                f"{career.get('tenth_lord', _planet_full_name(lord10))} is {career.get('tenth_lord_strength', 'moderate')}, "
                f"pointing toward {', '.join(career.get('recommended_fields', [])[:3]) or 'practical career growth'}. "
                f"The current period is {'supportive' if career.get('good_period_for_career_change') else 'better for consolidation'} for career change."
            ),
            drivers=[
                f"10th lord strength: {career.get('tenth_lord_strength', 'moderate')}",
                f"Top fields: {', '.join(career.get('recommended_fields', [])[:4]) or 'not enough data'}",
                f"Ashtakavarga bindus: {career_bindus or 'n/a'}",
            ],
            advice=career.get("advice", ""),
        ),
        "wealth_and_assets": _domain_entry(
            "Wealth & Assets",
            wealth_score,
            (
                f"Financial promise is {'active' if business.get('good_period_for_business') else 'developing slowly'}. "
                f"Wealth signatures include {', '.join(business.get('wealth_yogas', [])[:2]) or 'steady effort rather than sudden luck'}, "
                f"with speculation strength marked as {business.get('fifth_lord_strength', 'moderate')}."
            ),
            drivers=[
                f"2nd lord: {business.get('second_lord', '')}",
                f"11th lord: {business.get('eleventh_lord', '')}",
                f"5th lord strength: {business.get('fifth_lord_strength', 'moderate')}",
                f"Jupiter transit from Moon: {jupiter_transit if jupiter_transit != '' else 'n/a'}",
            ],
            advice=business.get("advice", ""),
        ),
        "relationships_and_marriage": _domain_entry(
            "Relationships & Marriage",
            relationship_score,
            (
                f"{marriage.get('seventh_lord', _planet_full_name(lord7))} and Venus are "
                f"{marriage.get('seventh_lord_strength', 'moderate')} / {marriage.get('venus_strength', 'moderate')} in strength. "
                f"The chart currently {'supports active relationship movement' if marriage.get('favorable_dasha_for_marriage') else 'needs patience and timing'}."
            ),
            drivers=[
                f"7th lord strength: {marriage.get('seventh_lord_strength', 'moderate')}",
                f"Venus strength: {marriage.get('venus_strength', 'moderate')}",
                f"Blockers: {', '.join(marriage.get('marriage_blockers', [])[:3]) or 'none major'}",
                f"Best windows: {', '.join(marriage.get('favorable_periods', [])[:2]) or 'await stronger triggers'}",
            ],
            advice=marriage.get("advice", ""),
        ),
        "family_home_and_children": _domain_entry(
            "Family, Home & Children",
            family_score,
            (
                f"Home stability and family legacy depend on {_planet_full_name(lord4)} ({lord4_strength}) and "
                f"{_planet_full_name(lord5)} ({lord5_strength}). "
                f"{'A child/progeny window is visible around ' + family_windows[0] + '.' if family_windows else 'Children and creative legacy may need longer timing confirmation.'}"
            ),
            drivers=[
                f"4th lord: {_planet_full_name(lord4)} ({lord4_strength})",
                f"5th lord: {_planet_full_name(lord5)} ({lord5_strength})",
                f"4th-house planets: {', '.join(_planet_full_name(p) for p in fourth_house) or 'none'}",
                f"5th-house planets: {', '.join(_planet_full_name(p) for p in fifth_house) or 'none'}",
            ],
            advice="Build emotional safety and long-range family plans slowly; stability at home improves every other domain.",
        ),
        "health_and_longevity": _domain_entry(
            "Health & Longevity",
            health_score,
            (
                f"Vitality is currently rated as {health.get('overall_vitality', health.get('lagna_lord_strength', 'moderate'))}. "
                f"The chart highlights {', '.join(health.get('health_risk_areas_6th', [])[:3] + health.get('health_risk_areas_8th', [])[:2]) or 'general preventive care'} "
                f"as areas to watch."
            ),
            drivers=[
                f"Lagna lord strength: {health.get('lagna_lord_strength', lagna_strength)}",
                f"6th lord: {health.get('sixth_lord', '')}",
                f"8th lord: {health.get('eighth_lord', '')}",
                f"Risk period active: {'yes' if health.get('risky_health_period') else 'no'}",
            ],
            advice=health.get("advice", ""),
        ),
        "learning_creativity_and_dharma": _domain_entry(
            "Learning, Creativity & Dharma",
            learning_score,
            (
                f"Learning and meaning-making are supported at {education.get('academic_ability_score', 50)}/100, "
                f"with stronger signals toward {', '.join(education.get('recommended_fields', [])[:3]) or 'skill-based development'}. "
                f"{'This is a good phase to study deeply.' if education.get('good_period_for_education') else 'Practical application may work better than formal study right now.'}"
            ),
            drivers=[
                f"Mercury strength: {education.get('mercury_strength', _planet_strength_label('Me', planets))}",
                f"Jupiter strength: {education.get('jupiter_strength', jupiter_strength)}",
                f"9th lord: {_planet_full_name(lord9)} ({lord9_strength})",
            ],
            advice=education.get("advice", ""),
        ),
        "travel_change_and_spirituality": _domain_entry(
            "Travel, Change & Spirituality",
            travel_score,
            (
                f"Change, relocation, and spiritual expansion are marked as {travel.get('foreign_settlement_likelihood', 'moderate').lower()} likelihood. "
                f"{travel.get('best_travel_direction', 'East')} is favored for movement, and 12th-house themes show "
                f"{'meaningful spiritual growth' if any(p in {'Ju', 'Ke'} for p in twelfth_house) else 'change through practical relocation or detachment'}."
            ),
            drivers=[
                f"Foreign indicators: {travel.get('foreign_indicators_score', 0)}",
                f"9th lord: {_planet_full_name(lord9)} ({lord9_strength})",
                f"12th lord: {_planet_full_name(lord12)} ({lord12_strength})",
                f"12th-house planets: {', '.join(_planet_full_name(p) for p in twelfth_house) or 'none'}",
            ],
            advice=travel.get("advice", ""),
        ),
    }

    ranked_desc = sorted(domains.values(), key=lambda item: item["score"], reverse=True)
    ranked_asc = sorted(domains.values(), key=lambda item: item["score"])

    protective_factors = []
    risk_factors = []
    if lagna_strength == "strong":
        protective_factors.append("Lagna lord is strong, supporting recovery capacity and baseline resilience.")
    elif lagna_strength == "weak":
        risk_factors.append("Lagna lord is weak, so routine, sleep, and discipline matter more.")
    if lord8_strength == "strong":
        protective_factors.append("8th lord is strong, helping the chart handle transformation and crises better.")
    elif lord8_strength == "weak":
        risk_factors.append("8th lord is weak, increasing sensitivity to sudden disruptions.")
    if saturn_strength == "strong":
        protective_factors.append("Saturn is strong; longevity improves when life is structured and disciplined.")
    elif saturn_strength == "weak":
        risk_factors.append("Saturn is strained, so chronic stress and neglect can accumulate faster.")
    if any(p in _NATURAL_BENEFICS for p in eighth_house):
        protective_factors.append("Benefic influence on the 8th house offers protection during difficult phases.")
    if any(p in _NATURAL_MALEFICS for p in eighth_house):
        risk_factors.append("Malefic pressure in the 8th house increases the intensity of sudden events.")
    if health.get("risky_health_period"):
        risk_factors.append("Current dasha activates 6th/8th-house themes; prevention matters right now.")
    if health.get("sade_sati_active"):
        risk_factors.append("Sade Sati raises stress load on body and mind.")
    if len(health.get("vulnerable_planets", [])) >= 2:
        risk_factors.append("Multiple vulnerable planets point to areas that should be monitored early, not ignored.")

    resilience_score = 54
    resilience_score += _strength_points(lagna_strength)
    resilience_score += int(_strength_points(lord8_strength) * 0.7)
    resilience_score += int(_strength_points(saturn_strength) * 0.4)
    resilience_score += min(12, len(protective_factors) * 4)
    resilience_score -= min(20, len(risk_factors) * 5)
    resilience_score = _clamp_score(resilience_score)
    if resilience_score >= 75:
        resilience_label = "High"
    elif resilience_score >= 58:
        resilience_label = "Moderate"
    else:
        resilience_label = "Sensitive"

    sensitive_periods = []
    if health.get("risky_health_period") and current_md:
        sensitive_periods.append(
            f"The current {current_md} Mahadasha needs extra care because health-risk themes are active."
        )
    sensitive_periods.extend(
        _future_sensitive_dashas(
            result,
            {
                _planet_full_name(lord8),
                health.get("sixth_lord", _planet_full_name(_lord_of(6, lagna))),
                health.get("eighth_lord", _planet_full_name(lord8)),
            },
            limit=3,
        )
    )
    sensitive_periods = _clean_list(sensitive_periods, limit=4)

    strongest = _format_ranked_domains(ranked_desc[:3])
    attention = _format_ranked_domains(ranked_asc[:3])

    top_names = ", ".join(item["domain"] for item in strongest[:2]) or "your strongest domains"
    focus_names = ", ".join(item["domain"] for item in attention[:2]) or "the most sensitive domains"
    next_window = timing_overview[0]["period"] if timing_overview else "the next supportive dasha trigger"

    return {
        "version": "1.0",
        "current_life_phase": {
            "mahadasha": current_md or "-",
            "antardasha": current_ad or "-",
            "theme": phase_theme,
        },
        "life_domains": domains,
        "strongest_domains": strongest,
        "attention_domains": attention,
        "timing_overview": timing_overview,
        "longevity_profile": {
            "overall_resilience_score": resilience_score,
            "overall_resilience": resilience_label,
            "protective_factors": _clean_list(protective_factors, limit=5),
            "risk_factors": _clean_list(risk_factors, limit=5),
            "sensitive_periods": sensitive_periods,
            "guidance": (
                "Treat longevity as a resilience and prevention lens: strengthen habits, do routine health checks, "
                "avoid reckless periods, and act early on chronic stress or symptoms."
            ),
            "note": "This is a longevity-risk model, not an exact death predictor.",
        },
        "master_advice": (
            f"Use the current {current_md or '-'} / {current_ad or '-'} phase to lean into {top_names}, while actively "
            f"stabilizing {focus_names}. The next visible activation window is {next_window}; use it for intentional action, "
            f"not fatalistic waiting."
        ),
    }
