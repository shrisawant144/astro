# api_server.py
"""
FastAPI REST server for the Vedic Kundali engine.
Run with: uvicorn api_server:app --reload --port 8000

Install: pip install fastapi uvicorn
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import datetime
import traceback

app = FastAPI(
    title="Vedic Kundali API",
    description="Complete Vedic astrology calculation engine",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class BirthData(BaseModel):
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    place: str
    gender: str = "Male"
    ayanamsa: str = "Lahiri"


class MuhurthaRequest(BaseModel):
    birth_data: BirthData        # used for Tarabala / Chandrabala
    start_date: str              # ISO "2025-01-01"
    end_date: str                # ISO "2025-03-01"
    purpose: str = "general"    # "marriage", "business", "travel", etc.


class MatchRequest(BaseModel):
    person1: BirthData
    person2: BirthData


# ---------------------------------------------------------------------------
# Serializer — convert kundali result dict to JSON-safe form
# ---------------------------------------------------------------------------

def _to_json(obj):
    """Recursively make obj JSON-serialisable."""
    try:
        import numpy as np
        _NP_TYPES = (np.integer, np.floating, np.bool_)
        _NP_ARRAY = np.ndarray
    except ImportError:
        _NP_TYPES = ()
        _NP_ARRAY = None

    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (int, float, str)):
        return obj
    if _NP_TYPES and isinstance(obj, _NP_TYPES):
        return obj.item()
    if _NP_ARRAY is not None and isinstance(obj, _NP_ARRAY):
        return obj.tolist()
    if isinstance(obj, dict):
        return {str(k): _to_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json(i) for i in obj]
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    # Fall-back: try str
    try:
        return str(obj)
    except Exception:
        return None


def _serialize_result(result: dict) -> dict:
    """
    Convert the full kundali result dict to a JSON-serialisable summary.

    Includes:
      - lagna_sign, lagna_deg, moon_sign, moon_nakshatra
      - planets summary (sign, deg, nakshatra, dignity, retro, combust)
      - houses (house → planet list)
      - yogas list (name / description)
      - vimshottari summary (current MD, AD, PD)
      - transits (sign, house_from_moon, effect)
      - muhurtha score
      - tajika summary
      - yogini dasha current
      - birth details
    """
    PLANET_FULL = {
        "Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury",
        "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn",
        "Ra": "Rahu",    "Ke": "Ketu",
    }

    out = {}

    # Basic birth details
    for key in ("name", "birth_date", "birth_time", "birth_place", "gender",
                "ayanamsa", "lagna_sign", "lagna_deg", "moon_sign",
                "moon_nakshatra", "sade_sati", "birth_year", "birth_month",
                "birth_day"):
        out[key] = _to_json(result.get(key))

    # Panchanga
    out["panchanga"] = _to_json(result.get("panchanga", {}))

    # Planets summary
    planets_raw = result.get("planets", {})
    planets_out = {}
    for code, pdata in planets_raw.items():
        if not isinstance(pdata, dict):
            continue
        planets_out[PLANET_FULL.get(code, code)] = {
            "sign":       _to_json(pdata.get("sign")),
            "deg":        _to_json(pdata.get("deg")),
            "nakshatra":  _to_json(pdata.get("nakshatra")),
            "dignity":    _to_json(pdata.get("dignity")),
            "retro":      _to_json(pdata.get("retro")),
            "combust":    _to_json(pdata.get("combust")),
            "navamsa_sign": _to_json(pdata.get("navamsa_sign")),
        }
    out["planets"] = planets_out

    # Houses
    houses_raw = result.get("houses", {})
    out["houses"] = {
        str(h): [PLANET_FULL.get(p, p) for p in pl if p != "Asc"]
        for h, pl in houses_raw.items()
    }

    # Yogas (keep name + description + strength)
    yogas_raw = result.get("yogas", [])
    yogas_out = []
    for y in yogas_raw:
        if isinstance(y, dict):
            yogas_out.append({
                "name":        _to_json(y.get("name",        y.get("yoga", ""))),
                "description": _to_json(y.get("description", y.get("planets", ""))),
                "strength":    _to_json(y.get("strength",    y.get("score", ""))),
            })
        else:
            yogas_out.append({"name": str(y), "description": "", "strength": ""})
    out["yogas"] = yogas_out

    # Vimshottari summary
    vims = result.get("vimshottari", {})
    cur_md = vims.get("current_md", {}) or {}
    cur_ad = vims.get("current_ad", {}) or {}
    vims_pd = result.get("vimshottari_pd", {}) or {}
    cur_pd  = vims_pd.get("current_pd", {}) or {}

    def _period(d):
        if not d:
            return None
        return {
            "lord":  _to_json(d.get("lord", d.get("dasha_lord"))),
            "start": _to_json(d.get("start_date", d.get("start"))),
            "end":   _to_json(d.get("end_date",   d.get("end"))),
        }

    out["vimshottari"] = {
        "starting_lord":           _to_json(vims.get("starting_lord")),
        "balance_at_birth_years":  _to_json(vims.get("balance_at_birth_years")),
        "current_md": _period(cur_md),
        "current_ad": _period(cur_ad),
        "current_pd": _period(cur_pd),
        "mahadasas":  _to_json([
            {k: v for k, v in md.items() if k not in ("antardashas",)}
            for md in (vims.get("mahadasas") or [])
        ]),
    }

    # Transits
    transits_raw = result.get("transits", {})
    out["transits"] = {
        PLANET_FULL.get(code, code): {
            "sign":           _to_json(t.get("sign")),
            "house_from_moon": _to_json(t.get("house_from_moon")),
            "effect":         _to_json(t.get("effect")),
        }
        for code, t in transits_raw.items()
        if isinstance(t, dict)
    }

    # Muhurtha score
    muh = result.get("muhurtha", {})
    if isinstance(muh, dict):
        out["muhurtha_score"] = _to_json(muh.get("score", muh.get("total_score")))
        out["muhurtha_summary"] = _to_json(muh.get("summary", muh.get("verdict", "")))
    else:
        out["muhurtha_score"] = None
        out["muhurtha_summary"] = None

    # Tajika summary
    tajika = result.get("tajika", {})
    if isinstance(tajika, dict):
        out["tajika"] = {
            "solar_return_year": _to_json(tajika.get("solar_return_year")),
            "muntha_sign":       _to_json(tajika.get("muntha_sign")),
            "year_verdict":      _to_json(tajika.get("year_verdict", tajika.get("verdict"))),
        }
    else:
        out["tajika"] = {}

    # Yogini dasha current
    yogini = result.get("yogini_dasha", {})
    if isinstance(yogini, dict):
        out["yogini_current"] = _to_json(yogini.get("current"))
    else:
        out["yogini_current"] = None

    # Neecha bhanga
    out["neecha_bhanga_planets"] = [
        PLANET_FULL.get(p, p) for p in (result.get("neecha_bhanga_planets") or [])
    ]

    # Jaimini Atmakaraka
    jaimini = result.get("jaimini", {})
    if isinstance(jaimini, dict):
        out["atmakaraka"] = _to_json(jaimini.get("atmakaraka"))
        out["karakamsa_lagna"] = _to_json(jaimini.get("karakamsa_lagna"))

    return out


# ---------------------------------------------------------------------------
# Ashtakoot Guna Milan (matching helper)
# ---------------------------------------------------------------------------

# Nakshatra list (index 0-26)
_NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

# Nadi per nakshatra index: 0=Adi, 1=Madhya, 2=Antya
_NADI = [0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2,
         0, 1, 2, 0, 1, 2, 0, 1, 2]
_NADI_NAMES = {0: "Adi", 1: "Madhya", 2: "Antya"}

# Gana per nakshatra index: 0=Deva, 1=Manushya, 2=Rakshasa
_GANA = [0, 2, 0, 0, 1, 2, 0, 0, 2,
         2, 1, 0, 0, 2, 0, 0, 0, 2,
         2, 1, 0, 0, 0, 2, 1, 0, 0]
_GANA_NAMES = {0: "Deva", 1: "Manushya", 2: "Rakshasa"}

# Varna per sign: 0=Brahmin, 1=Kshatriya, 2=Vaishya, 3=Shudra
_VARNA_SIGN = {
    "Cancer": 0,      "Scorpio": 0,     "Pisces": 0,
    "Leo":    1,      "Sagittarius": 1, "Aries": 1,
    "Gemini": 2,      "Libra": 2,       "Aquarius": 2,
    "Taurus": 3,      "Virgo": 3,       "Capricorn": 3,
}

# Sign lords (short codes) for Graha Maitri
_SIGN_LORDS = {
    "Aries": "Ma", "Taurus": "Ve", "Gemini": "Me", "Cancer": "Mo",
    "Leo": "Su", "Virgo": "Me", "Libra": "Ve", "Scorpio": "Ma",
    "Sagittarius": "Ju", "Capricorn": "Sa", "Aquarius": "Sa", "Pisces": "Ju",
}

_NAT_FRIENDS = {
    "Su": {"Mo", "Ma", "Ju"},
    "Mo": {"Su", "Me"},
    "Ma": {"Su", "Mo", "Ju"},
    "Me": {"Su", "Ve"},
    "Ju": {"Su", "Mo", "Ma"},
    "Ve": {"Me", "Sa"},
    "Sa": {"Me", "Ve"},
}
_NAT_ENEMIES = {
    "Su": {"Ve", "Sa"},
    "Mo": set(),
    "Ma": {"Me"},
    "Me": {"Mo"},
    "Ju": {"Me", "Ve"},
    "Ve": {"Su", "Mo"},
    "Sa": {"Su", "Mo", "Ma"},
}

# Vasya groups
_VASYA_GROUPS = [
    {"Aries", "Scorpio"},
    {"Taurus", "Libra", "Capricorn"},
    {"Gemini", "Virgo"},
    {"Cancer"},
    {"Leo"},
    {"Sagittarius", "Pisces"},
    {"Aquarius"},
]

# Yoni per nakshatra
_YONI = [
    "Horse", "Elephant", "Goat", "Serpent", "Serpent", "Dog", "Cat", "Goat",
    "Cat", "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger",
    "Deer", "Deer", "Dog", "Monkey", "Monkey", "Horse", "Lion", "Horse",
    "Lion", "Cow", "Elephant",
]
_YONI_FRIENDS = {
    frozenset({"Horse",   "Horse"}):    4,
    frozenset({"Elephant","Elephant"}): 4,
    frozenset({"Goat",    "Goat"}):     4,
    frozenset({"Serpent", "Serpent"}):  4,
    frozenset({"Dog",     "Dog"}):      4,
    frozenset({"Cat",     "Cat"}):      4,
    frozenset({"Rat",     "Rat"}):      4,
    frozenset({"Cow",     "Cow"}):      4,
    frozenset({"Buffalo", "Buffalo"}):  4,
    frozenset({"Tiger",   "Tiger"}):    4,
    frozenset({"Deer",    "Deer"}):     4,
    frozenset({"Monkey",  "Monkey"}):   4,
    frozenset({"Lion",    "Lion"}):     4,
    frozenset({"Horse",   "Deer"}):     3,
    frozenset({"Elephant","Cow"}):      3,
    frozenset({"Goat",    "Deer"}):     3,
    frozenset({"Monkey",  "Rat"}):      3,
    frozenset({"Cat",     "Rat"}):      0,
    frozenset({"Dog",     "Deer"}):     0,
    frozenset({"Lion",    "Elephant"}): 0,
    frozenset({"Tiger",   "Cow"}):      0,
}

_ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _nak_index(nakshatra: str) -> int:
    """Return 0-based index of nakshatra name, or -1 if not found."""
    nak = nakshatra.strip()
    for i, n in enumerate(_NAKSHATRAS):
        if n.lower() == nak.lower():
            return i
    return -1


def _sign_index(sign: str) -> int:
    for i, s in enumerate(_ZODIAC_SIGNS):
        if s.lower() == sign.lower():
            return i
    return -1


def _calc_ashtakoot(
    nak1: str, sign1: str,
    nak2: str, sign2: str,
) -> dict:
    """
    Calculate all 8 Kutas and return a detailed breakdown dict.

    nak1/sign1  = person1 Moon nakshatra / Moon sign
    nak2/sign2  = person2 Moon nakshatra / Moon sign
    """
    n1 = _nak_index(nak1)
    n2 = _nak_index(nak2)
    s1 = _sign_index(sign1)
    s2 = _sign_index(sign2)

    breakdown = {}
    total = 0

    # 1. Varna (1 pt) ── male's varna >= female's varna for compatibility
    varna1 = _VARNA_SIGN.get(sign1, 2)
    varna2 = _VARNA_SIGN.get(sign2, 2)
    _VARNA_NAMES = {0: "Brahmin", 1: "Kshatriya", 2: "Vaishya", 3: "Shudra"}
    varna_pts = 1 if varna1 <= varna2 else 0
    breakdown["Varna"] = {
        "max": 1,
        "score": varna_pts,
        "detail": f"P1={_VARNA_NAMES.get(varna1,'?')}  P2={_VARNA_NAMES.get(varna2,'?')}",
    }
    total += varna_pts

    # 2. Vasya (2 pts)
    grp1 = next((g for g in _VASYA_GROUPS if sign1 in g), set())
    grp2 = next((g for g in _VASYA_GROUPS if sign2 in g), set())
    vasya_pts = 2 if grp1 == grp2 else (1 if grp1 & grp2 else 0)
    breakdown["Vasya"] = {
        "max": 2,
        "score": vasya_pts,
        "detail": f"P1 group={sorted(grp1)}  P2 group={sorted(grp2)}",
    }
    total += vasya_pts

    # 3. Tara / Dina (3 pts)  — count of nak2 from nak1 divided by 9
    if n1 >= 0 and n2 >= 0:
        tara_count = ((n2 - n1) % 27) + 1
        tara_group = ((tara_count - 1) % 9) + 1
        _GOOD_TARAS = {1, 2, 4, 6, 8}  # Janma, Sampat, Kshema, Sadhana, Mitra
        tara_pts = 3 if tara_group in _GOOD_TARAS else 0
        breakdown["Tara"] = {
            "max": 3,
            "score": tara_pts,
            "detail": f"Tara count={tara_count}  group={tara_group}",
        }
    else:
        tara_pts = 0
        breakdown["Tara"] = {"max": 3, "score": 0, "detail": "Nakshatra not found"}
    total += tara_pts

    # 4. Yoni (4 pts)
    if n1 >= 0 and n2 >= 0:
        y1 = _YONI[n1]
        y2 = _YONI[n2]
        pair = frozenset({y1, y2})
        yoni_pts = _YONI_FRIENDS.get(pair, 2)  # default neutral = 2
        breakdown["Yoni"] = {
            "max": 4,
            "score": yoni_pts,
            "detail": f"P1={y1}  P2={y2}",
        }
    else:
        yoni_pts = 0
        breakdown["Yoni"] = {"max": 4, "score": 0, "detail": "Nakshatra not found"}
    total += yoni_pts

    # 5. Graha Maitri (5 pts) — moon sign lords' friendship
    lord1 = _SIGN_LORDS.get(sign1)
    lord2 = _SIGN_LORDS.get(sign2)
    if lord1 and lord2:
        f1 = lord2 in _NAT_FRIENDS.get(lord1, set())
        e1 = lord2 in _NAT_ENEMIES.get(lord1, set())
        f2 = lord1 in _NAT_FRIENDS.get(lord2, set())
        e2 = lord1 in _NAT_ENEMIES.get(lord2, set())
        if f1 and f2:
            gm_pts = 5
            gm_label = "Mutual friends"
        elif f1 or f2:
            gm_pts = 4 if (f1 and not e2) or (f2 and not e1) else 3
            gm_label = "One-sided friend"
        elif e1 or e2:
            gm_pts = 1
            gm_label = "Enemy"
        else:
            gm_pts = 3
            gm_label = "Neutral"
        breakdown["Graha Maitri"] = {
            "max": 5,
            "score": gm_pts,
            "detail": f"Lord1={lord1}  Lord2={lord2}  {gm_label}",
        }
    else:
        gm_pts = 0
        breakdown["Graha Maitri"] = {"max": 5, "score": 0, "detail": "Lords not found"}
    total += gm_pts

    # 6. Gana (6 pts)
    if n1 >= 0 and n2 >= 0:
        g1 = _GANA[n1]
        g2 = _GANA[n2]
        if g1 == g2:
            gana_pts = 6
        elif {g1, g2} == {0, 1} or {g1, g2} == {0, 2}:
            gana_pts = 0 if 2 in (g1, g2) else 5
        else:
            gana_pts = 0
        # Deva+Deva=6, Deva+Manushya=5, Manushya+Manushya=6,
        # Deva+Rakshasa=0, Manushya+Rakshasa=0, Rakshasa+Rakshasa=6
        gana_map = {
            (0, 0): 6, (1, 1): 6, (2, 2): 6,
            (0, 1): 5, (1, 0): 5,
            (0, 2): 0, (2, 0): 0,
            (1, 2): 0, (2, 1): 0,
        }
        gana_pts = gana_map.get((g1, g2), 0)
        breakdown["Gana"] = {
            "max": 6,
            "score": gana_pts,
            "detail": f"P1={_GANA_NAMES[g1]}  P2={_GANA_NAMES[g2]}",
        }
    else:
        gana_pts = 0
        breakdown["Gana"] = {"max": 6, "score": 0, "detail": "Nakshatra not found"}
    total += gana_pts

    # 7. Bhakoot / Bhakoota (7 pts) — sign relationship
    if s1 >= 0 and s2 >= 0:
        rel = abs(s1 - s2) % 12
        rel = min(rel, 12 - rel)
        # Inauspicious patterns: 6/8 and 2/12 from each other
        diff12 = (s2 - s1) % 12 + 1   # house count of sign2 from sign1 (1-12)
        diff21 = (s1 - s2) % 12 + 1
        bad = {(6, 8), (8, 6), (2, 12), (12, 2)}
        bhak_pts = 0 if (diff12, diff21) in bad else 7
        breakdown["Bhakoot"] = {
            "max": 7,
            "score": bhak_pts,
            "detail": f"P1 sign={sign1}  P2 sign={sign2}  relative diff={diff12}/{diff21}",
        }
    else:
        bhak_pts = 0
        breakdown["Bhakoot"] = {"max": 7, "score": 0, "detail": "Sign not found"}
    total += bhak_pts

    # 8. Nadi (8 pts) — different Nadi = 8 pts; same Nadi = 0 (Nadi Dosha)
    if n1 >= 0 and n2 >= 0:
        nd1 = _NADI[n1]
        nd2 = _NADI[n2]
        nadi_dosha = nd1 == nd2
        nadi_pts = 0 if nadi_dosha else 8
        breakdown["Nadi"] = {
            "max": 8,
            "score": nadi_pts,
            "detail": (
                f"P1={_NADI_NAMES[nd1]}  P2={_NADI_NAMES[nd2]}  "
                + ("NADI DOSHA" if nadi_dosha else "Compatible")
            ),
        }
    else:
        nadi_pts = 0
        breakdown["Nadi"] = {"max": 8, "score": 0, "detail": "Nakshatra not found"}
    total += nadi_pts

    # Verdict
    pct = round(total / 36 * 100, 1)
    if total >= 28:
        verdict = "Excellent match"
    elif total >= 21:
        verdict = "Good match"
    elif total >= 18:
        verdict = "Acceptable match"
    else:
        verdict = "Poor match — consult an astrologer"

    return {
        "total": total,
        "max": 36,
        "percentage": pct,
        "verdict": verdict,
        "breakdown": breakdown,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/calculate")
async def calculate(data: BirthData):
    """Calculate complete kundali. Returns serialised result dict."""
    try:
        from kundali.main import calculate_kundali
        result = calculate_kundali(
            name=data.name,
            year=data.year,
            month=data.month,
            day=data.day,
            hour=data.hour,
            minute=data.minute,
            place=data.place,
            gender=data.gender,
            ayanamsa=data.ayanamsa,
        )
        return _serialize_result(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc) + "\n" + traceback.format_exc())


@app.post("/muhurtha/find")
async def find_muhurtha(req: MuhurthaRequest):
    """
    Find auspicious muhurtha windows between start_date and end_date.

    Scans at 1-hour intervals and scores each window using the muhurtha
    evaluator from the kundali engine.  Returns the top windows sorted
    by score (descending).
    """
    try:
        from kundali.main import calculate_kundali
        from kundali.muhurtha import evaluate_muhurtha, get_panchanga
        import swisseph as swe

        bd = req.birth_data
        natal = calculate_kundali(
            name=bd.name, year=bd.year, month=bd.month, day=bd.day,
            hour=bd.hour, minute=bd.minute, place=bd.place,
            gender=bd.gender, ayanamsa=bd.ayanamsa,
        )

        start_dt = datetime.datetime.fromisoformat(req.start_date)
        end_dt   = datetime.datetime.fromisoformat(req.end_date)

        lat = natal.get("lat", 0.0)
        lon = natal.get("lon", 0.0)

        windows = []
        cur = start_dt
        step = datetime.timedelta(hours=1)

        while cur <= end_dt:
            jd = swe.julday(cur.year, cur.month, cur.day,
                            cur.hour + cur.minute / 60.0)
            try:
                score_info = evaluate_muhurtha(jd, natal, lat, lon)
                score = score_info.get("score", score_info.get("total_score", 0)) if isinstance(score_info, dict) else 0
                panchanga = get_panchanga(jd, lat, lon)
                windows.append({
                    "datetime":  cur.isoformat(),
                    "score":     _to_json(score),
                    "tithi":     panchanga.get("tithi_name"),
                    "vara":      panchanga.get("vara_name"),
                    "nakshatra": panchanga.get("nakshatra"),
                    "yoga":      panchanga.get("yoga_name"),
                })
            except Exception:
                pass
            cur += step

        # Return top 20 windows sorted by score
        windows.sort(key=lambda w: w["score"] or 0, reverse=True)
        return {
            "purpose":      req.purpose,
            "start_date":   req.start_date,
            "end_date":     req.end_date,
            "top_windows":  windows[:20],
            "total_scanned": len(windows),
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc) + "\n" + traceback.format_exc())


@app.post("/match")
async def match_compatibility(req: MatchRequest):
    """
    Calculate Ashtakoot Guna Milan compatibility between two persons.

    Derives Moon nakshatra and Moon sign from the calculated charts of
    both persons, then runs the full 8-kuta (36-point) analysis.
    Also delegates to the kundali_matching module for extra dosha checks
    when available.
    """
    try:
        from kundali.main import calculate_kundali

        def _calc(bd: BirthData):
            return calculate_kundali(
                name=bd.name, year=bd.year, month=bd.month, day=bd.day,
                hour=bd.hour, minute=bd.minute, place=bd.place,
                gender=bd.gender, ayanamsa=bd.ayanamsa,
            )

        r1 = _calc(req.person1)
        r2 = _calc(req.person2)

        nak1  = r1.get("moon_nakshatra", "")
        sign1 = r1.get("moon_sign", "")
        nak2  = r2.get("moon_nakshatra", "")
        sign2 = r2.get("moon_sign", "")

        guna = _calc_ashtakoot(nak1, sign1, nak2, sign2)

        # Try to use the full kundali_matching module for extra doshas
        extra_doshas = {}
        try:
            from kundali.kundali_matching import match_kundalis
            full_report = match_kundalis(r1, r2)
            # Extract dosha flags only (avoid duplicating kuta scores)
            for key in ("nadi_dosha", "rajju_dosha", "vedha_dosha",
                        "kuja_dosha_p1", "kuja_dosha_p2",
                        "mahendra", "stree_deergha"):
                if key in full_report:
                    extra_doshas[key] = _to_json(full_report[key])
        except Exception:
            pass

        return {
            "person1": {
                "name":           req.person1.name,
                "moon_sign":      sign1,
                "moon_nakshatra": nak1,
            },
            "person2": {
                "name":           req.person2.name,
                "moon_sign":      sign2,
                "moon_nakshatra": nak2,
            },
            "ashtakoot": guna,
            "extra_doshas": extra_doshas,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc) + "\n" + traceback.format_exc())


@app.post("/transit_calendar")
async def transit_calendar_endpoint(data: BirthData, months: int = 12):
    """
    Get a transit calendar for a native covering the next `months` months.

    Returns month-by-month gochara data for all planets.
    """
    try:
        from kundali.main import calculate_kundali
        import swisseph as swe
        from kundali.utils import get_sign
        from kundali.constants import gochara_effects, zodiac_signs

        natal = calculate_kundali(
            name=data.name, year=data.year, month=data.month, day=data.day,
            hour=data.hour, minute=data.minute, place=data.place,
            gender=data.gender, ayanamsa=data.ayanamsa,
        )

        moon_sign = natal.get("moon_sign", "")
        moon_sign_idx = zodiac_signs.index(moon_sign) if moon_sign in zodiac_signs else 0

        planet_ids = {
            "Su": swe.SUN, "Mo": swe.MOON, "Ma": swe.MARS,
            "Me": swe.MERCURY, "Ju": swe.JUPITER, "Ve": swe.VENUS,
            "Sa": swe.SATURN, "Ra": swe.MEAN_NODE,
        }
        PLANET_FULL = {
            "Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury",
            "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn",
            "Ra": "Rahu", "Ke": "Ketu",
        }

        calendar = []
        now = datetime.datetime.now()

        for m_offset in range(months):
            # First day of each future month
            target_month = (now.month + m_offset - 1) % 12 + 1
            target_year  = now.year + (now.month + m_offset - 1) // 12
            dt = datetime.datetime(target_year, target_month, 1, 12, 0)
            jd = swe.julday(dt.year, dt.month, dt.day, 12.0)

            month_transits = {}
            for code, pid in planet_ids.items():
                lon = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)[0][0]
                sign = get_sign(lon)
                sign_idx = zodiac_signs.index(sign)
                house_from_moon = ((sign_idx - moon_sign_idx + 12) % 12) + 1
                effect = gochara_effects.get(code, {}).get(house_from_moon, "Neutral")
                month_transits[PLANET_FULL.get(code, code)] = {
                    "sign":            sign,
                    "house_from_moon": house_from_moon,
                    "effect":          _to_json(effect),
                }
            # Ketu
            ra_lon = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
            ke_lon = (ra_lon + 180) % 360
            ke_sign = get_sign(ke_lon)
            ke_idx  = zodiac_signs.index(ke_sign)
            ke_house = ((ke_idx - moon_sign_idx + 12) % 12) + 1
            month_transits["Ketu"] = {
                "sign":            ke_sign,
                "house_from_moon": ke_house,
                "effect":          _to_json(gochara_effects.get("Ke", {}).get(ke_house, "Neutral")),
            }

            calendar.append({
                "month":    dt.strftime("%Y-%m"),
                "transits": month_transits,
            })

        return {
            "native":       data.name,
            "moon_sign":    moon_sign,
            "months":       months,
            "calendar":     calendar,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc) + "\n" + traceback.format_exc())
