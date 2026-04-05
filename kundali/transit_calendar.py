# transit_calendar.py
"""
Transit Calendar — upcoming planetary ingresses, retrogrades, eclipses, and key conjunctions.
Uses Swiss Ephemeris for precise event timing.
"""

import datetime
import swisseph as swe

PLANET_IDS = {
    "Su": swe.SUN,
    "Mo": swe.MOON,
    "Ma": swe.MARS,
    "Me": swe.MERCURY,
    "Ju": swe.JUPITER,
    "Ve": swe.VENUS,
    "Sa": swe.SATURN,
    "Ra": swe.MEAN_NODE,
}

ZODIAC_SIGNS = [
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

# Scan step sizes in days per planet (coarse scan)
_PLANET_STEP = {
    "Su": 1,
    "Ma": 1,
    "Me": 1,
    "Ve": 1,
    "Ju": 7,
    "Sa": 7,
    "Ra": 7,
}

# Planets that can go retrograde
_RETROGRADE_PLANETS = {"Ma", "Me", "Ju", "Ve", "Sa"}

# Eclipse type bit masks used by swisseph
_LUN_ECLIPSE_TYPES = {
    swe.ECL_TOTAL: "total",
    swe.ECL_PARTIAL: "partial",
    swe.ECL_PENUMBRAL: "penumbral",
}
_SOL_ECLIPSE_TYPES = {
    swe.ECL_TOTAL: "total",
    swe.ECL_ANNULAR: "annular",
    swe.ECL_PARTIAL: "partial",
    swe.ECL_ANNULAR_TOTAL: "hybrid",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _jd_to_date(jd):
    """Convert Julian Day to ISO date string (YYYY-MM-DD)."""
    y, mo, d, h = swe.revjul(jd)
    return f"{int(y)}-{int(mo):02d}-{int(d):02d}"


def _get_lon(planet_id, jd):
    """Return (sidereal longitude, speed) for a planet at the given JD."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    result = swe.calc_ut(jd, planet_id, flags)
    return result[0][0], result[0][3]  # lon, speed


def _sign_index(lon):
    """Return sign index (0-11) for an ecliptic longitude."""
    return int(lon / 30) % 12


def _bisect_ingress(planet_id, jd_before, jd_after, tolerance=0.001):
    """
    Binary-search for the exact JD when planet crosses a sign boundary.
    jd_before  → planet still in the 'old' sign
    jd_after   → planet already in the 'new' sign
    """
    sign_before = _sign_index(_get_lon(planet_id, jd_before)[0])
    for _ in range(50):  # max iterations
        jd_mid = (jd_before + jd_after) / 2.0
        if jd_after - jd_before < tolerance:
            break
        lon_mid, _ = _get_lon(planet_id, jd_mid)
        if _sign_index(lon_mid) == sign_before:
            jd_before = jd_mid
        else:
            jd_after = jd_mid
    return (jd_before + jd_after) / 2.0


def _bisect_station(planet_id, jd_before, jd_after, tolerance=0.001):
    """
    Binary-search for the exact JD when planet's speed crosses zero.
    Returns the JD of the station.
    """
    spd_before = _get_lon(planet_id, jd_before)[1]
    for _ in range(50):
        jd_mid = (jd_before + jd_after) / 2.0
        if jd_after - jd_before < tolerance:
            break
        spd_mid = _get_lon(planet_id, jd_mid)[1]
        if (spd_before >= 0) == (spd_mid >= 0):
            jd_before = jd_mid
            spd_before = spd_mid
        else:
            jd_after = jd_mid
    return (jd_before + jd_after) / 2.0


def _months_to_jd(current_jd, months):
    """Return JD approximately `months` months ahead of current_jd."""
    return current_jd + months * 30.4375


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_upcoming_ingresses(current_jd, months=24):
    """
    Find sign ingress dates for all planets (except Moon) over the next `months` months.

    For Rahu (Ra) the motion is retrograde by default (mean node), so ingresses
    move backwards through the zodiac.

    Returns a list of dicts sorted by date:
        {planet, from_sign, to_sign, date, jd}
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    end_jd = _months_to_jd(current_jd, months)
    ingresses = []

    for planet_name, planet_id in PLANET_IDS.items():
        if planet_name == "Mo":
            continue  # Moon moves too fast; skip

        step = _PLANET_STEP.get(planet_name, 1)
        jd = current_jd
        lon_prev, _ = _get_lon(planet_id, jd)
        sign_prev = _sign_index(lon_prev)

        while jd < end_jd:
            jd_next = min(jd + step, end_jd)
            lon_next, _ = _get_lon(planet_id, jd_next)
            sign_next = _sign_index(lon_next)

            if sign_next != sign_prev:
                # Refine with bisection
                exact_jd = _bisect_ingress(planet_id, jd, jd_next)
                lon_exact, _ = _get_lon(planet_id, exact_jd)
                from_sign = ZODIAC_SIGNS[sign_prev]
                to_sign = ZODIAC_SIGNS[_sign_index(lon_exact)]
                ingresses.append(
                    {
                        "planet": planet_name,
                        "from_sign": from_sign,
                        "to_sign": to_sign,
                        "date": _jd_to_date(exact_jd),
                        "jd": round(exact_jd, 4),
                    }
                )
                sign_prev = _sign_index(lon_exact)
            else:
                sign_prev = sign_next

            jd = jd_next

    ingresses.sort(key=lambda e: e["jd"])
    return ingresses


def get_retrograde_windows(current_jd, months=24):
    """
    Find retrograde station dates for Ma, Me, Ju, Ve, Sa over the next `months` months.

    A station retrograde (SR) is when speed goes from positive to negative.
    A station direct (SD) is when speed goes from negative to positive.

    Returns a list of dicts sorted by date:
        {planet, type: "station_retrograde"|"station_direct", date, jd, sign}
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    end_jd = _months_to_jd(current_jd, months)
    stations = []

    for planet_name in _RETROGRADE_PLANETS:
        planet_id = PLANET_IDS[planet_name]
        step = 1  # daily scan
        jd = current_jd
        _, spd_prev = _get_lon(planet_id, jd)

        while jd < end_jd:
            jd_next = min(jd + step, end_jd)
            lon_next, spd_next = _get_lon(planet_id, jd_next)

            if spd_prev >= 0 and spd_next < 0:
                # Station retrograde
                exact_jd = _bisect_station(planet_id, jd, jd_next)
                lon_exact, _ = _get_lon(planet_id, exact_jd)
                stations.append(
                    {
                        "planet": planet_name,
                        "type": "station_retrograde",
                        "date": _jd_to_date(exact_jd),
                        "jd": round(exact_jd, 4),
                        "sign": ZODIAC_SIGNS[_sign_index(lon_exact)],
                    }
                )
            elif spd_prev < 0 and spd_next >= 0:
                # Station direct
                exact_jd = _bisect_station(planet_id, jd, jd_next)
                lon_exact, _ = _get_lon(planet_id, exact_jd)
                stations.append(
                    {
                        "planet": planet_name,
                        "type": "station_direct",
                        "date": _jd_to_date(exact_jd),
                        "jd": round(exact_jd, 4),
                        "sign": ZODIAC_SIGNS[_sign_index(lon_exact)],
                    }
                )

            spd_prev = spd_next
            jd = jd_next

    stations.sort(key=lambda e: e["jd"])
    return stations


def get_eclipse_dates(current_jd, months=24):
    """
    Find solar and lunar eclipse dates within the next `months` months.

    Uses swe.lun_eclipse_when and swe.sol_eclipse_when_glob.

    Returns a list of dicts sorted by date:
        {type: "lunar"|"solar", subtype: "total"|"partial"|..., date, jd}
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    end_jd = _months_to_jd(current_jd, months)
    eclipses = []

    # --- Lunar eclipses ---
    jd_search = current_jd
    while True:
        try:
            ret = swe.lun_eclipse_when(jd_search, ifl=0, itype=0)
        except Exception:
            break

        # ret is (retval, tret) where tret[0] is the eclipse JD
        retval = ret[0]
        tret = ret[1]
        eclipse_jd = tret[0]

        if eclipse_jd > end_jd or eclipse_jd <= 0:
            break

        # Determine subtype from retval bitmask
        subtype = "partial"
        if retval & swe.ECL_TOTAL:
            subtype = "total"
        elif retval & swe.ECL_PENUMBRAL:
            subtype = "penumbral"
        elif retval & swe.ECL_PARTIAL:
            subtype = "partial"

        eclipses.append(
            {
                "type": "lunar",
                "subtype": subtype,
                "date": _jd_to_date(eclipse_jd),
                "jd": round(eclipse_jd, 4),
            }
        )

        jd_search = eclipse_jd + 25  # lunar eclipses at least ~29 days apart

    # --- Solar eclipses ---
    jd_search = current_jd
    while True:
        try:
            ret = swe.sol_eclipse_when_glob(jd_search, ifl=0, itype=0)
        except Exception:
            break

        retval = ret[0]
        tret = ret[1]
        eclipse_jd = tret[0]

        if eclipse_jd > end_jd or eclipse_jd <= 0:
            break

        subtype = "partial"
        if retval & swe.ECL_TOTAL:
            subtype = "total"
        elif retval & swe.ECL_ANNULAR_TOTAL:
            subtype = "hybrid"
        elif retval & swe.ECL_ANNULAR:
            subtype = "annular"
        elif retval & swe.ECL_PARTIAL:
            subtype = "partial"

        eclipses.append(
            {
                "type": "solar",
                "subtype": subtype,
                "date": _jd_to_date(eclipse_jd),
                "jd": round(eclipse_jd, 4),
            }
        )

        jd_search = eclipse_jd + 25

    eclipses.sort(key=lambda e: e["jd"])
    return eclipses


def get_key_conjunctions(current_jd, months=24):
    """
    Find rare planetary conjunctions (within 1° orb) over the next `months` months.

    Pairs checked: Ju-Sa, Ju-Ra, Sa-Ra, Ma-Sa.
    Scans weekly; refines exact conjunction with bisection.

    Returns a list of dicts sorted by date:
        {p1, p2, date, jd, sign, orb}
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    end_jd = _months_to_jd(current_jd, months)

    PAIRS = [
        ("Ju", "Sa"),
        ("Ju", "Ra"),
        ("Sa", "Ra"),
        ("Ma", "Sa"),
    ]
    STEP = 7  # weekly scan
    ORB_THRESHOLD = 1.0  # degrees
    conjunctions = []

    def _angular_diff(lon1, lon2):
        diff = abs(lon1 - lon2) % 360
        return diff if diff <= 180 else 360 - diff

    def _refine_conjunction(id1, id2, jd_a, jd_b):
        """Bisect to find the JD of minimum angular separation."""
        for _ in range(40):
            if jd_b - jd_a < 0.01:
                break
            jd_m = (jd_a + jd_b) / 2.0
            lon_a1, _ = _get_lon(id1, jd_a)
            lon_a2, _ = _get_lon(id2, jd_a)
            lon_m1, _ = _get_lon(id1, jd_m)
            lon_m2, _ = _get_lon(id2, jd_m)
            lon_b1, _ = _get_lon(id1, jd_b)
            lon_b2, _ = _get_lon(id2, jd_b)
            diff_a = _angular_diff(lon_a1, lon_a2)
            diff_m = _angular_diff(lon_m1, lon_m2)
            diff_b = _angular_diff(lon_b1, lon_b2)
            if diff_a < diff_b:
                jd_b = jd_m
            else:
                jd_a = jd_m
        return (jd_a + jd_b) / 2.0

    # Track which conjunctions we've already recorded to avoid duplicates
    recorded = {}  # (p1, p2) -> last jd recorded

    for p1, p2 in PAIRS:
        id1 = PLANET_IDS[p1]
        id2 = PLANET_IDS[p2]
        jd = current_jd
        lon1_prev, _ = _get_lon(id1, jd)
        lon2_prev, _ = _get_lon(id2, jd)
        orb_prev = _angular_diff(lon1_prev, lon2_prev)
        in_conjunction = orb_prev <= ORB_THRESHOLD

        # Reset per pair
        recorded[(p1, p2)] = None

        while jd < end_jd:
            jd_next = min(jd + STEP, end_jd)
            lon1, _ = _get_lon(id1, jd_next)
            lon2, _ = _get_lon(id2, jd_next)
            orb = _angular_diff(lon1, lon2)

            if orb <= ORB_THRESHOLD and not in_conjunction:
                # Entered conjunction window; find the closest approach
                # Search around [jd - STEP, jd_next + STEP] for minimum
                exact_jd = _refine_conjunction(
                    id1, id2, max(current_jd, jd - STEP), min(end_jd, jd_next + STEP)
                )
                exact_lon1, _ = _get_lon(id1, exact_jd)
                exact_lon2, _ = _get_lon(id2, exact_jd)
                exact_orb = _angular_diff(exact_lon1, exact_lon2)

                last = recorded[(p1, p2)]
                if last is None or exact_jd - last > 30:
                    conjunctions.append(
                        {
                            "p1": p1,
                            "p2": p2,
                            "date": _jd_to_date(exact_jd),
                            "jd": round(exact_jd, 4),
                            "sign": ZODIAC_SIGNS[_sign_index(exact_lon1)],
                            "orb": round(exact_orb, 3),
                        }
                    )
                    recorded[(p1, p2)] = exact_jd
                in_conjunction = True
            elif orb > ORB_THRESHOLD:
                in_conjunction = False

            orb_prev = orb
            jd = jd_next

    conjunctions.sort(key=lambda e: e["jd"])
    return conjunctions


# ---------------------------------------------------------------------------
# Natal triggers helper
# ---------------------------------------------------------------------------


def _get_natal_triggers(current_jd, months, natal_positions):
    """
    Find when transiting outer planets (Ju, Sa, Ra) conjunct natal planet positions
    within 2° orb.

    natal_positions: dict of {planet_code: longitude}
    Returns list of dicts: {transit_planet, natal_planet, date, jd, sign, orb}
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    end_jd = _months_to_jd(current_jd, months)

    TRANSIT_PLANETS = ["Ju", "Sa", "Ra"]
    NATAL_TARGET_PLANETS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
    STEP = 3  # days
    ORB = 2.0  # degrees

    triggers = []

    def _angular_diff(lon1, lon2):
        diff = abs(lon1 - lon2) % 360
        return diff if diff <= 180 else 360 - diff

    for tp in TRANSIT_PLANETS:
        tp_id = PLANET_IDS[tp]
        for np_code in NATAL_TARGET_PLANETS:
            if np_code not in natal_positions:
                continue
            natal_lon = natal_positions[np_code]

            jd = current_jd
            lon_prev, _ = _get_lon(tp_id, jd)
            orb_prev = _angular_diff(lon_prev, natal_lon)
            in_trigger = orb_prev <= ORB
            last_recorded = None

            while jd < end_jd:
                jd_next = min(jd + STEP, end_jd)
                lon_next, _ = _get_lon(tp_id, jd_next)
                orb_next = _angular_diff(lon_next, natal_lon)

                if orb_next <= ORB and not in_trigger:
                    # Find closest approach by scanning at 0.5-day resolution in window
                    best_jd = jd
                    best_orb = orb_prev
                    scan = jd
                    while scan <= jd_next + STEP and scan <= end_jd:
                        lo, _ = _get_lon(tp_id, scan)
                        ob = _angular_diff(lo, natal_lon)
                        if ob < best_orb:
                            best_orb = ob
                            best_jd = scan
                        scan += 0.5

                    if last_recorded is None or best_jd - last_recorded > 30:
                        lon_at, _ = _get_lon(tp_id, best_jd)
                        triggers.append(
                            {
                                "transit_planet": tp,
                                "natal_planet": np_code,
                                "date": _jd_to_date(best_jd),
                                "jd": round(best_jd, 4),
                                "sign": ZODIAC_SIGNS[_sign_index(lon_at)],
                                "orb": round(best_orb, 3),
                            }
                        )
                        last_recorded = best_jd
                    in_trigger = True
                elif orb_next > ORB:
                    in_trigger = False

                orb_prev = orb_next
                jd = jd_next

    triggers.sort(key=lambda e: e["jd"])
    return triggers


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------


def generate_transit_calendar(result, months=24):
    """
    Generate a complete Vedic transit calendar for a native.

    Args:
        result: kundali result dict; expected keys used:
                  - birth_jd     : Julian day of birth (used for natal positions)
                  - planets      : dict of planet dicts, each with 'longitude' key
        months : number of months ahead to scan (default 24)

    Returns:
        {
            ingresses          : list of sign ingress events,
            retrogrades        : list of station retrograde/direct events,
            eclipses           : list of eclipse events,
            conjunctions       : list of key planetary conjunctions,
            natal_triggers     : list of transits over natal positions,
            summary_next_30_days: most important events in the next 30 days,
        }
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Always use current date for transit calendar (not birth date)
    now = datetime.datetime.utcnow()
    current_jd = swe.julday(
        now.year, now.month, now.day, now.hour + now.minute / 60.0
    )

    # Compute all event lists
    ingresses = get_upcoming_ingresses(current_jd, months)
    retrogrades = get_retrograde_windows(current_jd, months)
    eclipses = get_eclipse_dates(current_jd, months)
    conjunctions = get_key_conjunctions(current_jd, months)

    # Natal triggers — gracefully skipped if planets not available
    natal_triggers = []
    if result and "planets" in result and result["planets"]:
        natal_positions = {}
        for planet_code, pdata in result["planets"].items():
            if isinstance(pdata, dict) and "longitude" in pdata:
                natal_positions[planet_code] = pdata["longitude"]
            elif isinstance(pdata, (int, float)):
                natal_positions[planet_code] = pdata
        if natal_positions:
            natal_triggers = _get_natal_triggers(current_jd, months, natal_positions)

    # Summary: events in the next 30 days
    cutoff_jd = current_jd + 30.0

    def _within_30(event):
        return event.get("jd", 0) <= cutoff_jd

    all_events = []
    for e in ingresses:
        if _within_30(e):
            all_events.append({**e, "event_type": "ingress"})
    for e in retrogrades:
        if _within_30(e):
            all_events.append({**e, "event_type": "retrograde_station"})
    for e in eclipses:
        if _within_30(e):
            all_events.append({**e, "event_type": "eclipse"})
    for e in conjunctions:
        if _within_30(e):
            all_events.append({**e, "event_type": "conjunction"})
    for e in natal_triggers:
        if _within_30(e):
            all_events.append({**e, "event_type": "natal_trigger"})

    all_events.sort(key=lambda e: e.get("jd", 0))

    return {
        "ingresses": ingresses,
        "retrogrades": retrogrades,
        "eclipses": eclipses,
        "conjunctions": conjunctions,
        "natal_triggers": natal_triggers,
        "summary_next_30_days": all_events,
    }
