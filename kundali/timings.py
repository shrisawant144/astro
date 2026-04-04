# timings.py
"""
Fructification timings for major life events (marriage, career, children, wealth)
based on Vimshottari Dasha periods and planetary significations.
"""

import re
import datetime
from .constants import short_to_full, sign_lords, zodiac_signs
from .marriage_scoring import calculate_marriage_score


def lord_of(house_no, lagna_sign):
    """Return the lord of a given house (1-12) for the given Lagna sign."""
    lagna_idx = zodiac_signs.index(lagna_sign)
    sign = zodiac_signs[(lagna_idx + house_no - 1) % 12]
    return sign_lords[sign]


def generate_timings(result, birth_year, birth_jd):
    """Generate accurate timing predictions from birth to future with probability scores and age awareness."""
    dashas = result["vimshottari"]["mahadasas"]
    current_year = datetime.datetime.now().year
    # Cover from birth to 20 years in future
    start_year = birth_year
    end_year = current_year + 20

    # Age thresholds for realistic predictions
    MIN_MARRIAGE_AGE = 21
    MIN_CAREER_AGE = 18
    MIN_CHILDREN_AGE = 22

    lagna_sign = result["lagna_sign"]
    seventh_lord = result["seventh_lord"]
    second_lord = lord_of(2, lagna_sign)

    # Event → favorable lords (expanded list)
    events = {
        "Marriage": [
            short_to_full["Ve"],
            short_to_full[seventh_lord],
            short_to_full["Ju"],
            short_to_full["Mo"],
            short_to_full[second_lord],  # 2nd lord for family/marriage
        ],
        "Career Rise / Fame": [
            short_to_full["Sa"],
            short_to_full[lord_of(10, lagna_sign)],
            short_to_full["Ju"],
            short_to_full["Su"],
            short_to_full["Ma"],
        ],
        "Children / Progeny": [
            short_to_full["Ju"],
            short_to_full[lord_of(5, lagna_sign)],
            short_to_full["Mo"],
            short_to_full["Ve"],
        ],
        "Major Wealth / Property": [
            short_to_full["Ju"],
            short_to_full["Ve"],
            short_to_full[lord_of(2, lagna_sign)],
            short_to_full[lord_of(11, lagna_sign)],
            short_to_full["Me"],
        ],
    }

    output = {}
    for event, fav_lords in events.items():
        periods = []
        # Set minimum age based on event type
        if event == "Marriage":
            min_age = MIN_MARRIAGE_AGE
        elif event == "Children / Progeny":
            min_age = MIN_CHILDREN_AGE
        elif event == "Career Rise / Fame":
            min_age = MIN_CAREER_AGE
        else:
            min_age = 18  # Default minimum for most life events

        min_event_year = birth_year + min_age

        for md in dashas:
            md_lord = md["lord"]
            md_start_age = (md["start_jd"] - birth_jd) / 365.25
            md_start_y = int(birth_year + md_start_age)
            md_end_y = int(birth_year + (md["end_jd"] - birth_jd) / 365.25)
            # Skip if MD is completely outside our window (birth to future)
            if md_end_y < start_year or md_start_y > end_year:
                continue
            # Determine status (Past/Current/Future)
            status = (
                "[PAST]"
                if md_end_y < current_year
                else "[NOW]"
                if md_start_y <= current_year <= md_end_y
                else "[FUTURE]"
            )
            # Calculate age at period start
            start_age = md_start_y - birth_year
            age_str = f"(Age {start_age}-{md_end_y - birth_year})"

            # Include if MD lord is favorable
            if md_lord in fav_lords:
                # Mark periods before minimum age as "Karmic Seed"
                if md_end_y < min_event_year:
                    periods.append(
                        f"• {md_lord} Mahadasha ({md_start_y}-{md_end_y}) {age_str} [KARMIC SEED]"
                    )
                else:
                    periods.append(
                        f"• {md_lord} Mahadasha ({md_start_y}-{md_end_y}) {age_str} {status}"
                    )
            # Check antardashas within our full timeline
            for ad in md.get("antardashas", []):
                if ad["lord"] in fav_lords:
                    ad_start_age = (ad["start_jd"] - birth_jd) / 365.25
                    ad_end_age = (ad["end_jd"] - birth_jd) / 365.25
                    ad_start_y = int(birth_year + ad_start_age)
                    ad_end_y = int(birth_year + ad_end_age)
                    # Include if AD starts or overlaps within our full timeline
                    if ad_start_y <= end_year and ad_end_y >= start_year:
                        # Determine AD status
                        ad_status = (
                            "[PAST]"
                            if ad_end_y < current_year
                            else (
                                "[NOW]"
                                if ad_start_y <= current_year <= ad_end_y
                                else "[FUTURE]"
                            )
                        )
                        # Calculate age for this period
                        ad_age_str = (
                            f"Age {ad_start_y - birth_year}-{ad_end_y - birth_year}"
                        )

                        # For marriage, add probability score and age filtering
                        if event == "Marriage":
                            score = calculate_marriage_score(
                                result, md_lord, ad["lord"]
                            )
                            prob_label = (
                                "★★★" if score >= 7 else "★★" if score >= 4 else "★"
                            )
                            # Mark pre-21 as karmic seed for marriage
                            if ad_end_y < min_event_year:
                                periods.append(
                                    f" └─ {md_lord}/{ad['lord']} ({ad_start_y}-{ad_end_y}) ({ad_age_str}) [KARMIC SEED - too young]"
                                )
                            else:
                                periods.append(
                                    f" └─ {md_lord}/{ad['lord']} ({ad_start_y}-{ad_end_y}) ({ad_age_str}) {prob_label} [{score}/10] {ad_status}"
                                )
                        else:
                            # For other events, mark appropriately
                            if ad_end_y < min_event_year:
                                periods.append(
                                    f" └─ {md_lord}/{ad['lord']} ({ad_start_y}-{ad_end_y}) ({ad_age_str}) [FORMATIVE]"
                                )
                            else:
                                periods.append(
                                    f" └─ {md_lord}/{ad['lord']} Antardasha ({ad_start_y}-{ad_end_y}) ({ad_age_str}) {ad_status}"
                                )
        # Sort by year and include up to 20 periods
        output[event] = (
            sorted(
                periods,
                key=lambda x: (
                    int(re.search(r"\((\d{4})", x).group(1))
                    if re.search(r"\((\d{4})", x)
                    else 0
                ),
            )[:20]
            if periods
            else []
        )

    return output
