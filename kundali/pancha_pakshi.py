# pancha_pakshi.py
"""
Pancha Pakshi Shastra — Five Bird Activity System.

Reference: Tamil Siddha tradition; VedAstro (C#) implementation by VedAstro.org.

The five birds (Vulture, Owl, Crow, Cock, Peacock) cycle through five activities
(Ruling, Eating, Walking, Sleeping, Dying) during five Yamas of the day and night.
The native's birth bird (derived from Moon nakshatra) governs their most auspicious
and inauspicious periods for any undertaking.

Activity Strength Guide:
  Ruling  → 5/5  — Most powerful; undertake important tasks
  Eating  → 4/5  — Good; proceed with confidence
  Walking → 3/5  — Neutral; moderate success expected
  Sleeping → 2/5 — Weak; avoid new initiatives
  Dying   → 1/5  — Avoid; inauspicious for any activity
"""

import datetime
import swisseph as swe

# ─── Constants ────────────────────────────────────────────────────────────────

BIRDS = ["Vulture", "Owl", "Crow", "Cock", "Peacock"]
ACTIVITIES = ["Ruling", "Eating", "Walking", "Sleeping", "Dying"]

ACTIVITY_STRENGTH = {
    "Ruling":   5,
    "Eating":   4,
    "Walking":  3,
    "Sleeping": 2,
    "Dying":    1,
}

ACTIVITY_ADVICE = {
    "Ruling":   "Extremely auspicious. Ideal for important decisions, travel, signing contracts.",
    "Eating":   "Auspicious. Good for constructive work, meetings, and new beginnings.",
    "Walking":  "Neutral. Routine matters are fine; avoid risky ventures.",
    "Sleeping": "Mildly inauspicious. Proceed with caution; avoid new undertakings.",
    "Dying":    "Inauspicious. Best to rest and avoid any important activity.",
}

# Birth bird determined by Moon nakshatra index (0-based, 0=Ashwini … 26=Revati)
# Pattern: Vulture, Owl, Crow, Cock, Peacock cycling through all 27 nakshatras
_BIRD_CYCLE = ["Vulture", "Owl", "Crow", "Cock", "Peacock"]
NAKSHATRA_BIRD = {i: _BIRD_CYCLE[i % 5] for i in range(27)}

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# ─── Activity Tables (Day) ────────────────────────────────────────────────────
# Source: VedAstro PanchaPakshi.cs — TimeOfDay.Day table
# Indexed as: DAY_TABLE[weekday_group][yama_index (0-4)] = {bird: activity}
# weekday_group keys correspond to Python weekday(): Mon=0, Tue=1, ..., Sun=6

_DAY_SUN_TUE = [
    {"Vulture": "Eating",   "Owl": "Walking",  "Crow": "Ruling",   "Cock": "Sleeping", "Peacock": "Dying"},
    {"Peacock": "Eating",   "Vulture": "Walking", "Owl": "Ruling", "Crow": "Sleeping", "Cock": "Dying"},
    {"Cock": "Eating",      "Peacock": "Walking", "Vulture": "Ruling", "Owl": "Sleeping", "Crow": "Dying"},
    {"Crow": "Eating",      "Cock": "Walking", "Peacock": "Ruling", "Vulture": "Sleeping", "Owl": "Dying"},
    {"Owl": "Eating",       "Crow": "Walking", "Cock": "Ruling",   "Peacock": "Sleeping", "Vulture": "Dying"},
]

_DAY_MON_WED = [
    {"Owl": "Eating",      "Crow": "Walking",    "Cock": "Ruling",    "Peacock": "Sleeping", "Vulture": "Dying"},
    {"Vulture": "Eating",  "Owl": "Walking",     "Crow": "Ruling",    "Cock": "Sleeping",    "Peacock": "Dying"},
    {"Peacock": "Eating",  "Vulture": "Walking", "Owl": "Ruling",     "Crow": "Sleeping",    "Cock": "Dying"},
    {"Cock": "Eating",     "Peacock": "Walking", "Vulture": "Ruling", "Owl": "Sleeping",     "Crow": "Dying"},
    {"Crow": "Eating",     "Cock": "Walking",    "Peacock": "Ruling", "Vulture": "Sleeping", "Owl": "Dying"},
]

_DAY_THU = [
    {"Crow": "Eating",    "Cock": "Walking",    "Peacock": "Ruling", "Vulture": "Sleeping", "Owl": "Dying"},
    {"Owl": "Eating",     "Crow": "Walking",    "Cock": "Ruling",    "Peacock": "Sleeping", "Vulture": "Dying"},
    {"Vulture": "Eating", "Owl": "Walking",     "Crow": "Ruling",    "Cock": "Sleeping",    "Peacock": "Dying"},
    {"Peacock": "Eating", "Vulture": "Walking", "Owl": "Ruling",     "Crow": "Sleeping",    "Cock": "Dying"},
    {"Cock": "Eating",    "Peacock": "Walking", "Vulture": "Ruling", "Owl": "Sleeping",     "Crow": "Dying"},
]

_DAY_FRI = [
    {"Cock": "Eating",    "Peacock": "Walking", "Vulture": "Ruling", "Owl": "Sleeping",     "Crow": "Dying"},
    {"Crow": "Eating",    "Cock": "Walking",    "Peacock": "Ruling", "Vulture": "Sleeping", "Owl": "Dying"},
    {"Owl": "Eating",     "Crow": "Walking",    "Cock": "Ruling",    "Peacock": "Sleeping", "Vulture": "Dying"},
    {"Vulture": "Eating", "Owl": "Walking",     "Crow": "Ruling",    "Cock": "Sleeping",    "Peacock": "Dying"},
    {"Peacock": "Eating", "Vulture": "Walking", "Owl": "Ruling",     "Crow": "Sleeping",    "Cock": "Dying"},
]

_DAY_SAT = [
    {"Peacock": "Eating", "Vulture": "Walking", "Owl": "Ruling",     "Crow": "Sleeping",    "Cock": "Dying"},
    {"Cock": "Eating",    "Peacock": "Walking", "Vulture": "Ruling", "Owl": "Sleeping",     "Crow": "Dying"},
    {"Crow": "Eating",    "Cock": "Walking",    "Peacock": "Ruling", "Vulture": "Sleeping", "Owl": "Dying"},
    {"Owl": "Eating",     "Crow": "Walking",    "Cock": "Ruling",    "Peacock": "Sleeping", "Vulture": "Dying"},
    {"Vulture": "Eating", "Owl": "Walking",     "Crow": "Ruling",    "Cock": "Sleeping",    "Peacock": "Dying"},
]

# DAY_TABLE[python_weekday] → list of 5 yama dicts
DAY_TABLE = {
    0: _DAY_MON_WED,   # Monday
    1: _DAY_SUN_TUE,   # Tuesday
    2: _DAY_MON_WED,   # Wednesday
    3: _DAY_THU,       # Thursday
    4: _DAY_FRI,       # Friday
    5: _DAY_SAT,       # Saturday
    6: _DAY_SUN_TUE,   # Sunday
}

# ─── Activity Tables (Night) ──────────────────────────────────────────────────
# Source: VedAstro PanchaPakshi.cs — TimeOfDay.Night table

_NIGHT_SUN_TUE = [
    {"Crow": "Eating",    "Owl": "Ruling",     "Vulture": "Dying",  "Peacock": "Walking", "Cock": "Sleeping"},
    {"Cock": "Eating",    "Crow": "Ruling",    "Owl": "Dying",      "Vulture": "Walking", "Peacock": "Sleeping"},
    {"Peacock": "Eating", "Cock": "Ruling",    "Crow": "Dying",     "Owl": "Walking",     "Vulture": "Sleeping"},
    {"Vulture": "Eating", "Peacock": "Ruling", "Cock": "Dying",     "Crow": "Walking",    "Owl": "Sleeping"},
    {"Owl": "Eating",     "Vulture": "Ruling", "Peacock": "Dying",  "Cock": "Walking",    "Crow": "Sleeping"},
]

_NIGHT_MON_WED = [
    {"Cock": "Eating",    "Crow": "Ruling",    "Owl": "Dying",      "Vulture": "Walking", "Peacock": "Sleeping"},
    {"Peacock": "Eating", "Cock": "Ruling",    "Crow": "Dying",     "Owl": "Walking",     "Vulture": "Sleeping"},
    {"Vulture": "Eating", "Peacock": "Ruling", "Cock": "Dying",     "Crow": "Walking",    "Owl": "Sleeping"},
    {"Owl": "Eating",     "Vulture": "Ruling", "Peacock": "Dying",  "Cock": "Walking",    "Crow": "Sleeping"},
    {"Crow": "Eating",    "Owl": "Ruling",     "Vulture": "Dying",  "Peacock": "Walking", "Cock": "Sleeping"},
]

_NIGHT_THU = [
    {"Peacock": "Eating", "Cock": "Ruling",    "Crow": "Dying",     "Owl": "Walking",     "Vulture": "Sleeping"},
    {"Vulture": "Eating", "Peacock": "Ruling", "Cock": "Dying",     "Crow": "Walking",    "Owl": "Sleeping"},
    {"Owl": "Eating",     "Vulture": "Ruling", "Peacock": "Dying",  "Cock": "Walking",    "Crow": "Sleeping"},
    {"Crow": "Eating",    "Owl": "Ruling",     "Vulture": "Dying",  "Peacock": "Walking", "Cock": "Sleeping"},
    {"Cock": "Eating",    "Crow": "Ruling",    "Owl": "Dying",      "Vulture": "Walking", "Peacock": "Sleeping"},
]

_NIGHT_FRI = [
    {"Vulture": "Eating", "Peacock": "Ruling", "Cock": "Dying",     "Crow": "Walking",    "Owl": "Sleeping"},
    {"Owl": "Eating",     "Vulture": "Ruling", "Peacock": "Dying",  "Cock": "Walking",    "Crow": "Sleeping"},
    {"Crow": "Eating",    "Owl": "Ruling",     "Vulture": "Dying",  "Peacock": "Walking", "Cock": "Sleeping"},
    {"Cock": "Eating",    "Crow": "Ruling",    "Owl": "Dying",      "Vulture": "Walking", "Peacock": "Sleeping"},
    {"Peacock": "Eating", "Cock": "Ruling",    "Crow": "Dying",     "Owl": "Walking",     "Vulture": "Sleeping"},
]

_NIGHT_SAT = [
    {"Owl": "Eating",     "Vulture": "Ruling", "Peacock": "Dying",  "Cock": "Walking",    "Crow": "Sleeping"},
    {"Crow": "Eating",    "Owl": "Ruling",     "Vulture": "Dying",  "Peacock": "Walking", "Cock": "Sleeping"},
    {"Cock": "Eating",    "Crow": "Ruling",    "Owl": "Dying",      "Vulture": "Walking", "Peacock": "Sleeping"},
    {"Peacock": "Eating", "Cock": "Ruling",    "Crow": "Dying",     "Owl": "Walking",     "Vulture": "Sleeping"},
    {"Vulture": "Eating", "Peacock": "Ruling", "Cock": "Dying",     "Crow": "Walking",    "Owl": "Sleeping"},
]

# NIGHT_TABLE[python_weekday] → list of 5 yama dicts
NIGHT_TABLE = {
    0: _NIGHT_MON_WED,
    1: _NIGHT_SUN_TUE,
    2: _NIGHT_MON_WED,
    3: _NIGHT_THU,
    4: _NIGHT_FRI,
    5: _NIGHT_SAT,
    6: _NIGHT_SUN_TUE,
}

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ─── Sunrise/Sunset Helper ────────────────────────────────────────────────────

def _get_sun_rise_set(jd: float, lat: float, lon: float):
    """Return (sunrise_jd, sunset_jd) for the given Julian Day and location."""
    try:
        sr = swe.rise_trans(
            jd - 1.0, swe.SUN, "", swe.CALC_RISE,
            geopos=(lon, lat, 0), atpress=0, attemp=0,
        )
        ss = swe.rise_trans(
            jd - 1.0, swe.SUN, "", swe.CALC_SET,
            geopos=(lon, lat, 0), atpress=0, attemp=0,
        )
        sunrise_jd = sr[1][0] if sr[1] else jd - 0.25
        sunset_jd  = ss[1][0] if ss[1] else jd + 0.25
    except Exception:
        # Fallback: assume 6am sunrise, 6pm sunset
        sunrise_jd = jd - 0.25
        sunset_jd  = jd + 0.25
    return sunrise_jd, sunset_jd


def _jd_to_utc_datetime(jd: float) -> datetime.datetime:
    year, month, day, hour_frac = swe.jdut1_to_utc(jd, swe.GREG_CAL)
    hour = int(hour_frac)
    minute = int((hour_frac - hour) * 60)
    second = int(((hour_frac - hour) * 60 - minute) * 60)
    return datetime.datetime(year, month, day, hour, minute, second, tzinfo=datetime.timezone.utc)


# ─── Core Calculation ─────────────────────────────────────────────────────────

def get_birth_bird(moon_nakshatra: str) -> str:
    """Return the birth bird based on the Moon's nakshatra name."""
    try:
        nak_idx = NAKSHATRA_NAMES.index(moon_nakshatra)
    except ValueError:
        # Try partial match
        for i, n in enumerate(NAKSHATRA_NAMES):
            if moon_nakshatra.lower() in n.lower() or n.lower() in moon_nakshatra.lower():
                nak_idx = i
                break
        else:
            return "Crow"  # default
    return NAKSHATRA_BIRD[nak_idx]


def get_yama_info(query_jd: float, sunrise_jd: float, sunset_jd: float,
                  weekday: int) -> dict:
    """
    Determine which yama the query_jd falls in and return the full activity
    mapping for all 5 birds.

    Returns:
        dict with keys: is_day, yama_number (1-5), yama_activities {bird:activity},
                        yama_start_jd, yama_end_jd, ruling_bird
    """
    is_day = sunrise_jd <= query_jd <= sunset_jd

    if is_day:
        day_duration = sunset_jd - sunrise_jd
        yama_duration = day_duration / 5.0
        elapsed = query_jd - sunrise_jd
        table = DAY_TABLE[weekday]
    else:
        # Night spans from sunset today to sunrise tomorrow
        # Midnight wrap-around: if before sunrise, count from previous sunset
        if query_jd < sunrise_jd:
            # Before today's sunrise → use previous night
            prev_sunset_jd = sunset_jd - 1.0  # approximate; caller should pass correct data
            night_duration = sunrise_jd - prev_sunset_jd
            elapsed = query_jd - prev_sunset_jd
        else:
            night_duration = sunrise_jd + 1.0 - sunset_jd  # sunset to next sunrise
            elapsed = query_jd - sunset_jd
        yama_duration = night_duration / 5.0
        table = NIGHT_TABLE[weekday]

    yama_idx = min(int(elapsed / yama_duration), 4) if yama_duration > 0 else 0
    yama_activities = table[yama_idx]
    ruling_bird = next((b for b, a in yama_activities.items() if a == "Ruling"), None)

    return {
        "is_day":          is_day,
        "yama_number":     yama_idx + 1,
        "yama_activities": dict(yama_activities),
        "ruling_bird":     ruling_bird,
        "yama_duration_minutes": yama_duration * 24 * 60 if yama_duration else 0,
    }


def get_auspicious_yamas(birth_bird: str, weekday: int, is_day: bool) -> list:
    """
    Return a list of yama numbers (1-5) that are auspicious for the birth bird
    (i.e. the birth bird is Ruling or Eating in that yama).
    """
    table = DAY_TABLE[weekday] if is_day else NIGHT_TABLE[weekday]
    result = []
    for i, yama_dict in enumerate(table):
        activity = yama_dict.get(birth_bird, "Sleeping")
        if ACTIVITY_STRENGTH[activity] >= 4:
            result.append(i + 1)
    return result


def get_full_day_forecast(birth_bird: str, weekday: int,
                          sunrise_jd: float, sunset_jd: float) -> list:
    """
    Generate a complete day forecast with time ranges and activity strengths.

    Returns list of dicts: {period, start_jd, end_jd, activity, strength, advice}
    """
    forecast = []
    periods = [
        ("Day Yama 1",   "Day Yama 2",   "Day Yama 3",   "Day Yama 4",   "Day Yama 5"),
        ("Night Yama 1", "Night Yama 2", "Night Yama 3", "Night Yama 4", "Night Yama 5"),
    ]

    day_dur   = (sunset_jd - sunrise_jd) / 5.0
    night_dur = (1.0 + sunrise_jd - sunset_jd) / 5.0  # approximate 24h night

    for idx_yama in range(5):
        # Day yama
        start = sunrise_jd + idx_yama * day_dur
        end   = start + day_dur
        act   = DAY_TABLE[weekday][idx_yama].get(birth_bird, "Sleeping")
        forecast.append({
            "period":   f"Day Yama {idx_yama + 1}",
            "start_jd": start,
            "end_jd":   end,
            "activity": act,
            "strength": ACTIVITY_STRENGTH[act],
            "advice":   ACTIVITY_ADVICE[act],
        })
        # Night yama
        start_n = sunset_jd + idx_yama * night_dur
        end_n   = start_n + night_dur
        act_n   = NIGHT_TABLE[weekday][idx_yama].get(birth_bird, "Sleeping")
        forecast.append({
            "period":   f"Night Yama {idx_yama + 1}",
            "start_jd": start_n,
            "end_jd":   end_n,
            "activity": act_n,
            "strength": ACTIVITY_STRENGTH[act_n],
            "advice":   ACTIVITY_ADVICE[act_n],
        })

    return forecast


# ─── Main Public API ──────────────────────────────────────────────────────────

def calculate_pancha_pakshi(result: dict, query_dt: datetime.datetime | None = None) -> dict:
    """
    Calculate Pancha Pakshi analysis for the native's birth chart.

    Args:
        result:   Kundali result dict (from calculate_kundali).
        query_dt: Query datetime (default: now at birth location).

    Returns:
        dict with birth_bird, current_activity, current_strength, day_forecast, etc.
    """
    moon_nak  = result.get("moon_nakshatra", "")
    birth_jd  = result.get("birth_jd", 0.0)
    lat       = result.get("lat", 0.0)
    lon       = result.get("lon", 0.0)

    birth_bird = get_birth_bird(moon_nak)

    # Query time — default to now
    if query_dt is None:
        query_dt = datetime.datetime.now(datetime.timezone.utc)
    if query_dt.tzinfo is None:
        query_dt = query_dt.replace(tzinfo=datetime.timezone.utc)

    query_jd = swe.julday(
        query_dt.year, query_dt.month, query_dt.day,
        query_dt.hour + query_dt.minute / 60.0 + query_dt.second / 3600.0
    )
    weekday = query_dt.weekday()  # 0=Monday, 6=Sunday

    sunrise_jd, sunset_jd = _get_sun_rise_set(query_jd, lat, lon)

    yama_info = get_yama_info(query_jd, sunrise_jd, sunset_jd, weekday)
    current_activity = yama_info["yama_activities"].get(birth_bird, "Sleeping")
    current_strength = ACTIVITY_STRENGTH[current_activity]

    # Birth-time bird activity
    birth_weekday   = result.get("birth_datetime",
                                  datetime.datetime.utcnow()).weekday() if hasattr(
                                  result.get("birth_datetime", None), "weekday") else 0
    birth_sunrise, birth_sunset = _get_sun_rise_set(birth_jd, lat, lon)
    birth_yama = get_yama_info(birth_jd, birth_sunrise, birth_sunset, birth_weekday)
    birth_activity = birth_yama["yama_activities"].get(birth_bird, "Sleeping")

    # Full forecast for today
    day_forecast = get_full_day_forecast(birth_bird, weekday, sunrise_jd, sunset_jd)

    # Auspicious yamas today
    auspicious_day   = get_auspicious_yamas(birth_bird, weekday, True)
    auspicious_night = get_auspicious_yamas(birth_bird, weekday, False)

    # All five birds' current activities for cross-reference
    all_bird_activities = {
        b: {
            "activity": yama_info["yama_activities"].get(b, "Unknown"),
            "strength": ACTIVITY_STRENGTH.get(yama_info["yama_activities"].get(b, "Sleeping"), 3),
        }
        for b in BIRDS
    }

    return {
        "birth_bird":           birth_bird,
        "moon_nakshatra":       moon_nak,
        "nak_index":            NAKSHATRA_NAMES.index(moon_nak) if moon_nak in NAKSHATRA_NAMES else -1,
        "query_weekday":        WEEKDAY_NAMES[weekday],
        "is_day":               yama_info["is_day"],
        "current_yama":         yama_info["yama_number"],
        "current_activity":     current_activity,
        "current_strength":     current_strength,
        "current_advice":       ACTIVITY_ADVICE[current_activity],
        "ruling_bird_now":      yama_info["ruling_bird"],
        "yama_duration_min":    yama_info["yama_duration_minutes"],
        "all_bird_activities":  all_bird_activities,
        "birth_yama":           birth_yama["yama_number"],
        "birth_activity":       birth_activity,
        "auspicious_day_yamas": auspicious_day,
        "auspicious_night_yamas": auspicious_night,
        "day_forecast":         day_forecast,
        "activity_advice":      ACTIVITY_ADVICE,
        "activity_strength_map": ACTIVITY_STRENGTH,
    }
