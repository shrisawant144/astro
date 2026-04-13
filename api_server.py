# api_server.py
"""
FastAPI REST server for the Vedic Kundali engine.
Run with: uvicorn api_server:app --reload --port 8000

Install: pip install fastapi uvicorn

Thin HTTP layer — all heavy logic lives in kundali.api.
"""

from fastapi import FastAPI, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import datetime
import traceback

from kundali.api import (
    calculate as api_calculate,
    serialize_result,
    to_json,
    PLANET_FULL,
    get_career_decision,
    get_marriage_decision,
    get_business_decision,
    get_health_decision,
    get_travel_decision,
    get_daily_guidance,
    get_compatibility_decision,
    get_education_decision,
    get_life_analysis,
    get_all_decisions,
)

app = FastAPI(
    title="Vedic Kundali API",
    description="""
## 🌟 Complete Vedic Astrology Calculation Engine

This API provides comprehensive Vedic astrology calculations including:

- **Kundali (Birth Chart)** - Complete planetary positions and house placements
- **Dasha Predictions** - Vimshottari, Yogini, Ashtottari dashas
- **Yoga Detection** - Classical yoga formations
- **Marriage Compatibility** - Ashtakoot Guna Milan (36-point matching)
- **Muhurtha** - Auspicious time selection
- **Transit Calendar** - Monthly planetary transits

### 🚀 Quick Start

**Option 1: Use the Web Form**
Visit the [Home Page](/) for an easy-to-use form interface.

**Option 2: Use Query Parameters**
```
GET /calculate/simple?name=John&date=1990-05-15&time=08:30&place=Mumbai,India
```

**Option 3: Use JSON API**
```json
POST /calculate
{
    "name": "John",
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 8,
    "minute": 30,
    "place": "Mumbai, India"
}
```
    """,
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
    """Birth details for kundali calculation."""
    name: str = Field(..., description="Name of the person")
    year: int = Field(..., description="Birth year (e.g., 1990)", ge=1900, le=2100)
    month: int = Field(..., description="Birth month (1-12)", ge=1, le=12)
    day: int = Field(..., description="Birth day (1-31)", ge=1, le=31)
    hour: int = Field(..., description="Birth hour in 24h format (0-23)", ge=0, le=23)
    minute: int = Field(..., description="Birth minute (0-59)", ge=0, le=59)
    place: str = Field(..., description="Birth place (City, State, Country)")
    gender: str = Field("Male", description="Gender: 'Male' or 'Female'")
    ayanamsa: str = Field("Lahiri", description="Ayanamsa system: Lahiri, Raman, KP, True Chitra, Yukteshwar, Djwhal Khul")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "Rahul Sharma",
                "year": 1990,
                "month": 5,
                "day": 15,
                "hour": 8,
                "minute": 30,
                "place": "Mumbai, Maharashtra, India",
                "gender": "Male",
                "ayanamsa": "Lahiri"
            }]
        }
    }


# Simplified input model that accepts date/time as strings
class SimpleBirthData(BaseModel):
    """Simplified birth details - accepts date and time as strings."""
    name: str = Field(..., description="Name of the person")
    date: str = Field(..., description="Birth date in YYYY-MM-DD format")
    time: str = Field(..., description="Birth time in HH:MM (24h) format")
    place: str = Field(..., description="Birth place (City, State, Country)")
    gender: str = Field("Male", description="Gender: 'Male' or 'Female'")
    ayanamsa: str = Field("Lahiri", description="Ayanamsa system")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "Rahul Sharma",
                "date": "1990-05-15",
                "time": "08:30",
                "place": "Mumbai, Maharashtra, India",
                "gender": "Male",
                "ayanamsa": "Lahiri"
            }]
        }
    }


class MuhurthaRequest(BaseModel):
    birth_data: BirthData        # used for Tarabala / Chandrabala
    start_date: str              # ISO "2025-01-01"
    end_date: str                # ISO "2025-03-01"
    purpose: str = "general"    # "marriage", "business", "travel", etc.


class MatchRequest(BaseModel):
    person1: BirthData
    person2: BirthData


# Serialization is now in kundali.api — imported at the top


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
# HTML Form Interface
# ---------------------------------------------------------------------------

HTML_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌟 Vedic Kundali Generator</title>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --border: #334155;
            --success: #22c55e;
            --warning: #f59e0b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 0.5rem;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #f59e0b, #ef4444, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle {
            text-align: center;
            color: var(--text-muted);
            margin-bottom: 2rem;
        }
        .tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        .tab {
            padding: 0.75rem 1.5rem;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            color: var(--text-muted);
            transition: all 0.2s;
        }
        .tab.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        .tab:hover:not(.active) {
            background: var(--border);
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 0 12px 12px 12px;
            padding: 2rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3);
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
        }
        .form-group {
            display: flex;
            flex-direction: column;
        }
        .form-group.full-width {
            grid-column: 1 / -1;
        }
        label {
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text);
        }
        label .hint {
            font-weight: normal;
            color: var(--text-muted);
            font-size: 0.875rem;
        }
        input, select {
            padding: 0.75rem 1rem;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-size: 1rem;
            transition: border-color 0.2s;
        }
        input:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        input::placeholder {
            color: var(--text-muted);
        }
        .btn {
            padding: 1rem 2rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        .btn:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
        }
        .btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }
        .result-container {
            margin-top: 2rem;
            display: none;
        }
        .result-container.show {
            display: block;
        }
        .result {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            overflow-x: auto;
        }
        .result pre {
            margin: 0;
            white-space: pre-wrap;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 0.875rem;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .summary-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        .summary-card .label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .summary-card .value {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--primary);
            margin-top: 0.25rem;
        }
        .error {
            background: #7f1d1d;
            border-color: #dc2626;
            color: #fecaca;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid transparent;
            border-top-color: currentColor;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .api-info {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            margin-top: 1.5rem;
        }
        .api-info h3 {
            margin-bottom: 1rem;
            color: var(--warning);
        }
        .api-info code {
            background: var(--card-bg);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-family: 'Fira Code', 'Consolas', monospace;
        }
        .api-info pre {
            background: var(--card-bg);
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 0.5rem 0;
        }
        footer {
            text-align: center;
            margin-top: 3rem;
            color: var(--text-muted);
            font-size: 0.875rem;
        }
        footer a {
            color: var(--primary);
            text-decoration: none;
        }
        footer a:hover {
            text-decoration: underline;
        }
        
        /* Kundali Report Styles */
        .kundali-report, .match-report {
            color: var(--text);
        }
        .kundali-report h2, .match-report h2 {
            color: var(--warning);
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
        }
        .section {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .section h3 {
            color: var(--primary);
            margin-bottom: 1rem;
            font-size: 1.1rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        }
        .info-item {
            display: flex;
            flex-direction: column;
        }
        .info-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }
        .info-value {
            font-size: 1rem;
            color: var(--text);
            margin-top: 0.25rem;
        }
        .highlight-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        .highlight-card {
            background: linear-gradient(135deg, var(--card-bg), var(--bg));
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
        }
        .highlight-card.lagna { border-left: 4px solid #f59e0b; }
        .highlight-card.moon { border-left: 4px solid #8b5cf6; }
        .highlight-card.dasha { border-left: 4px solid #22c55e; }
        .highlight-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
        .highlight-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }
        .highlight-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text);
            margin: 0.25rem 0;
        }
        .highlight-sub {
            font-size: 0.875rem;
            color: var(--text-muted);
        }
        .sade-sati-alert {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid #ef4444;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
            color: #fca5a5;
            font-size: 0.9rem;
        }
        .panchanga-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem;
        }
        .panchanga-item {
            text-align: center;
            padding: 0.75rem;
            background: var(--card-bg);
            border-radius: 8px;
        }
        .panchanga-label {
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            display: block;
        }
        .panchanga-value {
            font-size: 0.95rem;
            color: var(--text);
            margin-top: 0.25rem;
            display: block;
        }
        .table-wrapper { overflow-x: auto; }
        .planets-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        .planets-table th, .planets-table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        .planets-table th {
            background: var(--card-bg);
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
        }
        .planets-table tr:hover { background: rgba(99, 102, 241, 0.1); }
        .dignity-exalted { color: #22c55e; font-weight: 600; }
        .dignity-own { color: #3b82f6; font-weight: 600; }
        .dignity-debilitated { color: #ef4444; font-weight: 600; }
        .legend {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.75rem;
            text-align: right;
        }
        .houses-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 0.5rem;
        }
        .house-box {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem 0.5rem;
            text-align: center;
        }
        .house-num {
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
        }
        .house-planets {
            font-size: 0.8rem;
            color: var(--primary);
            font-weight: 500;
        }
        .yogas-list {
            list-style: none;
            padding: 0;
        }
        .yogas-list li {
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: var(--card-bg);
            border-radius: 8px;
            border-left: 3px solid var(--border);
            font-size: 0.9rem;
        }
        .yogas-list li.yoga-strong { border-left-color: #22c55e; }
        .yogas-list li.yoga-medium { border-left-color: #f59e0b; }
        .yogas-list li.yoga-weak { border-left-color: #ef4444; }
        .yogas-list li.yoga-more { 
            color: var(--text-muted);
            font-style: italic;
            border-left-color: var(--border);
        }
        .transits-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 0.75rem;
        }
        .transit-item {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 0.75rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        .transit-item.transit-good { border: 1px solid #22c55e; }
        .transit-item.transit-bad { border: 1px solid #ef4444; }
        .transit-planet { font-weight: 600; color: var(--text); }
        .transit-sign { font-size: 0.85rem; color: var(--text-muted); }
        .transit-effect { font-size: 0.75rem; margin-top: 0.25rem; color: var(--primary); }
        .problems-list { display: flex; flex-direction: column; gap: 1rem; }
        .problem-item {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            padding: 1rem;
        }
        .problem-summary {
            font-weight: 600;
            color: #fca5a5;
            margin-bottom: 0.5rem;
        }
        .problem-detail {
            font-size: 0.875rem;
            color: var(--text-muted);
            line-height: 1.6;
        }
        .analysis-text {
            font-size: 0.95rem;
            line-height: 1.8;
            color: var(--text);
        }
        .error-message {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid #ef4444;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
        }
        .error-message h3 { color: #fca5a5; margin-bottom: 0.5rem; }
        .error-message p { color: var(--text-muted); }
        
        /* Match Report Styles */
        .match-persons {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 2rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        .person-card {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem 2rem;
            text-align: center;
            min-width: 150px;
        }
        .person-name {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 0.5rem;
        }
        .person-detail {
            font-size: 0.875rem;
            color: var(--text-muted);
        }
        .match-heart { font-size: 2rem; }
        .match-score {
            text-align: center;
            padding: 2rem;
            background: var(--bg);
            border-radius: 16px;
            margin-bottom: 2rem;
        }
        .match-score.excellent { border: 2px solid #22c55e; }
        .match-score.good { border: 2px solid #3b82f6; }
        .match-score.acceptable { border: 2px solid #f59e0b; }
        .match-score.poor { border: 2px solid #ef4444; }
        .score-circle {
            display: inline-flex;
            align-items: baseline;
            margin-bottom: 0.5rem;
        }
        .score-number {
            font-size: 3rem;
            font-weight: 700;
            color: var(--primary);
        }
        .score-max {
            font-size: 1.5rem;
            color: var(--text-muted);
        }
        .score-percent {
            font-size: 1.25rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }
        .score-verdict {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text);
        }
        .kutas-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        .kuta-item {
            display: grid;
            grid-template-columns: 120px 1fr 60px;
            gap: 1rem;
            align-items: center;
        }
        .kuta-name {
            font-weight: 500;
            color: var(--text);
        }
        .kuta-bar {
            height: 8px;
            background: var(--border);
            border-radius: 4px;
            overflow: hidden;
        }
        .kuta-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), #22c55e);
            border-radius: 4px;
        }
        .kuta-score {
            text-align: right;
            color: var(--text-muted);
            font-size: 0.875rem;
        }
        
        @media (max-width: 600px) {
            .houses-grid { grid-template-columns: repeat(4, 1fr); }
            .kuta-item { grid-template-columns: 100px 1fr 50px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌟 Vedic Kundali</h1>
        <p class="subtitle">Complete Vedic Astrology Calculation Engine</p>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('kundali')">📜 Kundali</div>
            <div class="tab" onclick="switchTab('match')">💑 Match</div>
            <div class="tab" onclick="switchTab('api')">🔌 API</div>
        </div>
        
        <div class="card">
            <!-- Kundali Form -->
            <div id="kundali-tab" class="tab-content active">
                <form id="kundali-form">
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="name">Name</label>
                            <input type="text" id="name" name="name" placeholder="Enter your name" required>
                        </div>
                        <div class="form-group">
                            <label for="gender">Gender</label>
                            <select id="gender" name="gender">
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="date">Birth Date</label>
                            <input type="date" id="date" name="date" required>
                        </div>
                        <div class="form-group">
                            <label for="time">Birth Time <span class="hint">(24hr)</span></label>
                            <input type="time" id="time" name="time" required>
                        </div>
                        <div class="form-group full-width">
                            <label for="place">Birth Place <span class="hint">(City, State, Country)</span></label>
                            <input type="text" id="place" name="place" placeholder="e.g., Mumbai, Maharashtra, India" required>
                        </div>
                        <div class="form-group">
                            <label for="ayanamsa">Ayanamsa</label>
                            <select id="ayanamsa" name="ayanamsa">
                                <option value="Lahiri" selected>Lahiri (Default)</option>
                                <option value="Raman">Raman</option>
                                <option value="KP">KP (Krishnamurti)</option>
                                <option value="True Chitra">True Chitra</option>
                                <option value="Yukteshwar">Yukteshwar</option>
                                <option value="Djwhal Khul">Djwhal Khul</option>
                            </select>
                        </div>
                        <div class="form-group" style="justify-content: flex-end;">
                            <button type="submit" class="btn" id="submit-btn">
                                ✨ Generate Kundali
                            </button>
                        </div>
                    </div>
                </form>
                
                <div id="result-container" class="result-container">
                    <div id="kundali-results"></div>
                </div>
            </div>
            
            <!-- Match Form -->
            <div id="match-tab" class="tab-content">
                <form id="match-form">
                    <h3 style="margin-bottom: 1.5rem; color: var(--warning);">👤 Person 1 (Groom)</h3>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Name</label>
                            <input type="text" name="name1" placeholder="Groom's name" required>
                        </div>
                        <div class="form-group">
                            <label>Birth Date</label>
                            <input type="date" name="date1" required>
                        </div>
                        <div class="form-group">
                            <label>Birth Time</label>
                            <input type="time" name="time1" required>
                        </div>
                        <div class="form-group full-width">
                            <label>Birth Place</label>
                            <input type="text" name="place1" placeholder="City, State, Country" required>
                        </div>
                    </div>
                    
                    <h3 style="margin: 2rem 0 1.5rem; color: var(--warning);">👤 Person 2 (Bride)</h3>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Name</label>
                            <input type="text" name="name2" placeholder="Bride's name" required>
                        </div>
                        <div class="form-group">
                            <label>Birth Date</label>
                            <input type="date" name="date2" required>
                        </div>
                        <div class="form-group">
                            <label>Birth Time</label>
                            <input type="time" name="time2" required>
                        </div>
                        <div class="form-group full-width">
                            <label>Birth Place</label>
                            <input type="text" name="place2" placeholder="City, State, Country" required>
                        </div>
                    </div>
                    
                    <div style="margin-top: 1.5rem;">
                        <button type="submit" class="btn" id="match-btn">
                            💕 Check Compatibility
                        </button>
                    </div>
                </form>
                
                <div id="match-result-container" class="result-container">
                    <div id="match-results"></div>
                </div>
            </div>
            
            <!-- API Info -->
            <div id="api-tab" class="tab-content">
                <div class="api-info">
                    <h3>📚 API Documentation</h3>
                    <p>Full interactive API docs are available at <a href="/docs" style="color: var(--primary);">/docs</a></p>
                    
                    <h4 style="margin-top: 1.5rem; margin-bottom: 0.5rem;">🔗 Simple URL-based Request</h4>
                    <p>No JSON needed! Just use query parameters:</p>
                    <pre><code>GET /calculate/simple?name=Rahul&date=1990-05-15&time=08:30&place=Mumbai,India</code></pre>
                    
                    <h4 style="margin-top: 1.5rem; margin-bottom: 0.5rem;">📝 Form-style POST Request</h4>
                    <pre><code>POST /calculate/form
Content-Type: application/x-www-form-urlencoded

name=Rahul&date=1990-05-15&time=08:30&place=Mumbai,India</code></pre>
                    
                    <h4 style="margin-top: 1.5rem; margin-bottom: 0.5rem;">📦 JSON POST Request</h4>
                    <pre><code>POST /calculate
Content-Type: application/json

{
    "name": "Rahul Sharma",
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 8,
    "minute": 30,
    "place": "Mumbai, Maharashtra, India",
    "gender": "Male",
    "ayanamsa": "Lahiri"
}</code></pre>
                    
                    <h4 style="margin-top: 1.5rem; margin-bottom: 0.5rem;">🔄 Available Endpoints</h4>
                    <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                        <li><code>GET /</code> - This page</li>
                        <li><code>GET /health</code> - API health check</li>
                        <li><code>GET /calculate/simple</code> - Calculate using URL params</li>
                        <li><code>POST /calculate/form</code> - Calculate using form data</li>
                        <li><code>POST /calculate</code> - Calculate using JSON</li>
                        <li><code>POST /match</code> - Marriage compatibility</li>
                        <li><code>POST /match/simple</code> - Match using form data</li>
                        <li><code>POST /muhurtha/find</code> - Find auspicious times</li>
                        <li><code>POST /transit_calendar</code> - Monthly transits</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <footer>
            <p>Powered by Swiss Ephemeris | <a href="/docs">API Documentation</a></p>
        </footer>
    </div>
    
    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tabName + '-tab').classList.add('active');
        }
        
        function renderKundaliResults(data) {
            const planets = data.planets || {};
            const yogas = data.yogas || [];
            const houses = data.houses || {};
            const panchanga = data.panchanga || {};
            const vimshottari = data.vimshottari || {};
            const transits = data.transits || {};
            const problems = data.problems || [];
            
            // Build planets table
            let planetsRows = '';
            for (const [planet, info] of Object.entries(planets)) {
                const dignityClass = info.dignity === 'Exalted' ? 'dignity-exalted' : 
                                    info.dignity === 'Own' ? 'dignity-own' :
                                    info.dignity === 'Debilitated' ? 'dignity-debilitated' : '';
                const retroIcon = info.retro ? ' ℞' : '';
                const combustIcon = info.combust ? ' 🔥' : '';
                planetsRows += `
                    <tr>
                        <td><strong>${planet}</strong>${retroIcon}${combustIcon}</td>
                        <td>${info.sign || '-'}</td>
                        <td>${info.deg?.toFixed(1) || '-'}°</td>
                        <td>${info.nakshatra || '-'}</td>
                        <td class="${dignityClass}">${info.dignity || 'Neutral'}</td>
                        <td>${info.navamsa_sign || '-'}</td>
                    </tr>
                `;
            }
            
            // Build yogas list
            let yogasList = '';
            for (const yoga of yogas.slice(0, 10)) {
                const name = yoga.name || yoga;
                const match = name.match(/Strength (\\d+)\\/10/);
                const strength = match ? parseInt(match[1]) : 5;
                const strengthClass = strength >= 8 ? 'yoga-strong' : strength >= 6 ? 'yoga-medium' : 'yoga-weak';
                yogasList += `<li class="${strengthClass}">${name}</li>`;
            }
            if (yogas.length > 10) {
                yogasList += `<li class="yoga-more">... and ${yogas.length - 10} more yogas</li>`;
            }
            
            // Build houses display
            let housesHtml = '';
            for (let h = 1; h <= 12; h++) {
                const planets = houses[h] || houses[String(h)] || [];
                const planetsList = planets.length > 0 ? planets.join(', ') : '-';
                housesHtml += `
                    <div class="house-box">
                        <div class="house-num">${h}</div>
                        <div class="house-planets">${planetsList}</div>
                    </div>
                `;
            }
            
            // Build transits
            let transitsHtml = '';
            for (const [planet, info] of Object.entries(transits)) {
                const effectClass = info.effect === 'Good' || info.effect === 'Wisdom' || info.effect === 'Gains' ? 'transit-good' :
                                   info.effect === 'Bad' || info.effect === 'Expenses' || info.effect === 'Arguments' ? 'transit-bad' : '';
                transitsHtml += `
                    <div class="transit-item ${effectClass}">
                        <span class="transit-planet">${planet}</span>
                        <span class="transit-sign">${info.sign}</span>
                        <span class="transit-effect">${info.effect}</span>
                    </div>
                `;
            }
            
            // Build problems/doshas
            let problemsHtml = '';
            for (const problem of problems) {
                problemsHtml += `
                    <div class="problem-item">
                        <div class="problem-summary">${problem.summary || ''}</div>
                        <div class="problem-detail">${(problem.detail || '').replace(/\\n/g, '<br>')}</div>
                    </div>
                `;
            }
            
            return `
                <div class="kundali-report">
                    <h2>🌟 Kundali Report for ${data.name || 'Native'}</h2>
                    
                    <div class="section">
                        <h3>📋 Birth Details</h3>
                        <div class="info-grid">
                            <div class="info-item"><span class="info-label">Date</span><span class="info-value">${data.birth_date || '-'}</span></div>
                            <div class="info-item"><span class="info-label">Time</span><span class="info-value">${data.birth_time || '-'}</span></div>
                            <div class="info-item"><span class="info-label">Place</span><span class="info-value">${data.birth_place || '-'}</span></div>
                            <div class="info-item"><span class="info-label">Gender</span><span class="info-value">${data.gender || '-'}</span></div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>🔮 Ascendant & Moon</h3>
                        <div class="highlight-grid">
                            <div class="highlight-card lagna">
                                <div class="highlight-icon">⬆️</div>
                                <div class="highlight-label">Lagna (Ascendant)</div>
                                <div class="highlight-value">${data.lagna_sign || '-'}</div>
                                <div class="highlight-sub">${data.lagna_deg?.toFixed(1) || '-'}°</div>
                            </div>
                            <div class="highlight-card moon">
                                <div class="highlight-icon">🌙</div>
                                <div class="highlight-label">Moon Sign (Rashi)</div>
                                <div class="highlight-value">${data.moon_sign || '-'}</div>
                                <div class="highlight-sub">${data.moon_nakshatra || '-'}</div>
                            </div>
                            <div class="highlight-card dasha">
                                <div class="highlight-icon">⏱️</div>
                                <div class="highlight-label">Current Dasha</div>
                                <div class="highlight-value">${vimshottari.current_md?.lord || '-'}</div>
                                <div class="highlight-sub">Antardasha: ${vimshottari.current_ad?.lord || '-'}</div>
                            </div>
                        </div>
                        ${data.sade_sati ? `<div class="sade-sati-alert">⚠️ ${data.sade_sati}</div>` : ''}
                    </div>
                    
                    <div class="section">
                        <h3>📅 Panchanga</h3>
                        <div class="panchanga-grid">
                            <div class="panchanga-item"><span class="panchanga-label">Tithi</span><span class="panchanga-value">${panchanga.tithi || '-'}</span></div>
                            <div class="panchanga-item"><span class="panchanga-label">Vara (Day)</span><span class="panchanga-value">${panchanga.vara || '-'}</span></div>
                            <div class="panchanga-item"><span class="panchanga-label">Yoga</span><span class="panchanga-value">${panchanga.yoga || '-'}</span></div>
                            <div class="panchanga-item"><span class="panchanga-label">Karana</span><span class="panchanga-value">${panchanga.karana || '-'}</span></div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>🪐 Planetary Positions</h3>
                        <div class="table-wrapper">
                            <table class="planets-table">
                                <thead>
                                    <tr>
                                        <th>Planet</th>
                                        <th>Sign</th>
                                        <th>Degree</th>
                                        <th>Nakshatra</th>
                                        <th>Dignity</th>
                                        <th>Navamsa</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${planetsRows}
                                </tbody>
                            </table>
                        </div>
                        <div class="legend">℞ = Retrograde | 🔥 = Combust</div>
                    </div>
                    
                    <div class="section">
                        <h3>🏠 House Placements</h3>
                        <div class="houses-grid">
                            ${housesHtml}
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3>✨ Yogas (${yogas.length} found)</h3>
                        <ul class="yogas-list">
                            ${yogasList || '<li>No major yogas detected</li>'}
                        </ul>
                    </div>
                    
                    <div class="section">
                        <h3>🌍 Current Transits</h3>
                        <div class="transits-grid">
                            ${transitsHtml}
                        </div>
                    </div>
                    
                    ${problems.length > 0 ? `
                    <div class="section">
                        <h3>⚠️ Doshas & Considerations</h3>
                        <div class="problems-list">
                            ${problemsHtml}
                        </div>
                    </div>
                    ` : ''}
                    
                    ${data.final_analysis ? `
                    <div class="section">
                        <h3>📖 Analysis Summary</h3>
                        <div class="analysis-text">${data.final_analysis.replace(/\\n/g, '<br>').replace(/###/g, '')}</div>
                    </div>
                    ` : ''}
                </div>
            `;
        }
        
        document.getElementById('kundali-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submit-btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading"></span> Calculating...';
            btn.disabled = true;
            
            const formData = new FormData(e.target);
            const params = new URLSearchParams();
            for (const [key, value] of formData.entries()) {
                params.append(key, value);
            }
            
            try {
                const response = await fetch('/calculate/simple?' + params.toString());
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('kundali-results').innerHTML = renderKundaliResults(data);
                } else {
                    document.getElementById('kundali-results').innerHTML = `
                        <div class="error-message">
                            <h3>❌ Error</h3>
                            <p>${data.detail || JSON.stringify(data)}</p>
                        </div>
                    `;
                }
                document.getElementById('result-container').classList.add('show');
            } catch (err) {
                document.getElementById('kundali-results').innerHTML = `
                    <div class="error-message">
                        <h3>❌ Network Error</h3>
                        <p>${err.message}</p>
                    </div>
                `;
                document.getElementById('result-container').classList.add('show');
            }
            
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
        
        function renderMatchResults(data) {
            const ak = data.ashtakoot || {};
            const breakdown = ak.breakdown || {};
            
            let kutasHtml = '';
            for (const [kuta, info] of Object.entries(breakdown)) {
                const pct = (info.score / info.max * 100).toFixed(0);
                kutasHtml += `
                    <div class="kuta-item">
                        <div class="kuta-name">${kuta}</div>
                        <div class="kuta-bar">
                            <div class="kuta-fill" style="width: ${pct}%"></div>
                        </div>
                        <div class="kuta-score">${info.score}/${info.max}</div>
                    </div>
                `;
            }
            
            const verdictClass = ak.total >= 28 ? 'excellent' : ak.total >= 21 ? 'good' : ak.total >= 18 ? 'acceptable' : 'poor';
            
            return `
                <div class="match-report">
                    <h2>💑 Compatibility Report</h2>
                    
                    <div class="match-persons">
                        <div class="person-card">
                            <div class="person-name">${data.person1?.name || 'Person 1'}</div>
                            <div class="person-detail">🌙 ${data.person1?.moon_sign || '-'}</div>
                            <div class="person-detail">⭐ ${data.person1?.moon_nakshatra || '-'}</div>
                        </div>
                        <div class="match-heart">❤️</div>
                        <div class="person-card">
                            <div class="person-name">${data.person2?.name || 'Person 2'}</div>
                            <div class="person-detail">🌙 ${data.person2?.moon_sign || '-'}</div>
                            <div class="person-detail">⭐ ${data.person2?.moon_nakshatra || '-'}</div>
                        </div>
                    </div>
                    
                    <div class="match-score ${verdictClass}">
                        <div class="score-circle">
                            <div class="score-number">${ak.total || 0}</div>
                            <div class="score-max">/36</div>
                        </div>
                        <div class="score-percent">${ak.percentage || 0}%</div>
                        <div class="score-verdict">${ak.verdict || '-'}</div>
                    </div>
                    
                    <div class="section">
                        <h3>📊 Ashtakoot Breakdown</h3>
                        <div class="kutas-list">
                            ${kutasHtml}
                        </div>
                    </div>
                </div>
            `;
        }
        
        document.getElementById('match-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('match-btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading"></span> Checking...';
            btn.disabled = true;
            
            const formData = new FormData(e.target);
            const params = new URLSearchParams();
            for (const [key, value] of formData.entries()) {
                params.append(key, value);
            }
            
            try {
                const response = await fetch('/match/simple', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: params.toString()
                });
                const data = await response.json();
                
                if (response.ok && data.ashtakoot) {
                    document.getElementById('match-results').innerHTML = renderMatchResults(data);
                } else {
                    document.getElementById('match-results').innerHTML = `
                        <div class="error-message">
                            <h3>❌ Error</h3>
                            <p>${data.detail || JSON.stringify(data)}</p>
                        </div>
                    `;
                }
                document.getElementById('match-result-container').classList.add('show');
            } catch (err) {
                document.getElementById('match-results').innerHTML = `
                    <div class="error-message">
                        <h3>❌ Network Error</h3>
                        <p>${err.message}</p>
                    </div>
                `;
                document.getElementById('match-result-container').classList.add('show');
            }
            
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home():
    """User-friendly HTML form interface for the API."""
    return HTML_FORM


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/calculate")
async def calculate(data: BirthData):
    """
    Calculate complete kundali using JSON input.
    
    Returns a comprehensive Vedic astrology analysis including:
    - Planetary positions and dignities
    - House placements
    - Yoga formations
    - Dasha periods (Vimshottari, Yogini)
    - Doshas and problems
    - And much more...
    """
    try:
        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        result = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return serialize_result(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc) + "\n" + traceback.format_exc())


@app.get("/calculate/simple")
async def calculate_simple(
    name: str = Query(..., description="Name of the person"),
    date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Query(..., description="Birth time (HH:MM in 24h format)"),
    place: str = Query(..., description="Birth place (City, Country)"),
    gender: str = Query("Male", description="Gender: Male or Female"),
    ayanamsa: str = Query("Lahiri", description="Ayanamsa system"),
):
    """
    🌟 **Simple Kundali Calculation** - No JSON needed!
    
    Just pass the birth details as URL query parameters.
    
    **Example:**
    ```
    /calculate/simple?name=Rahul&date=1990-05-15&time=08:30&place=Mumbai,India
    ```
    """
    try:
        # Parse date and time
        date_parts = date.split("-")
        if len(date_parts) != 3:
            raise ValueError("Date must be in YYYY-MM-DD format")
        
        time_parts = time.replace(":", "-").split("-")
        if len(time_parts) < 2:
            raise ValueError("Time must be in HH:MM format")
        
        result = api_calculate(
            date, time, place,
            gender=gender, ayanamsa=ayanamsa, name=name,
        )
        return serialize_result(result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/calculate/form")
async def calculate_form(
    name: str = Form(..., description="Name of the person"),
    date: str = Form(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Form(..., description="Birth time (HH:MM)"),
    place: str = Form(..., description="Birth place"),
    gender: str = Form("Male"),
    ayanamsa: str = Form("Lahiri"),
):
    """
    Calculate kundali using form data (x-www-form-urlencoded).
    
    Perfect for HTML form submissions!
    """
    try:
        result = api_calculate(
            date, time, place,
            gender=gender, ayanamsa=ayanamsa, name=name,
        )
        return serialize_result(result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/calculate/json")
async def calculate_json(data: SimpleBirthData):
    """
    Calculate kundali using simplified JSON format.
    
    Uses human-friendly date and time strings instead of separate year/month/day fields.
    
    **Example:**
    ```json
    {
        "name": "Rahul",
        "date": "1990-05-15",
        "time": "08:30",
        "place": "Mumbai, India"
    }
    ```
    """
    try:
        result = api_calculate(
            data.date, data.time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return serialize_result(result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/muhurtha/find")
async def find_muhurtha(req: MuhurthaRequest):
    """
    Find auspicious muhurtha windows between start_date and end_date.

    Scans at 1-hour intervals and scores each window using the muhurtha
    evaluator from the kundali engine.  Returns the top windows sorted
    by score (descending).
    """
    try:
        from kundali.muhurtha import evaluate_muhurtha, get_panchanga
        import swisseph as swe

        bd = req.birth_data
        birth_date = f"{bd.year:04d}-{bd.month:02d}-{bd.day:02d}"
        birth_time = f"{bd.hour:02d}:{bd.minute:02d}"
        natal = api_calculate(
            birth_date, birth_time, bd.place,
            gender=bd.gender, ayanamsa=bd.ayanamsa, name=bd.name,
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
                    "score":     to_json(score),
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
        def _calc(bd: BirthData):
            birth_date = f"{bd.year:04d}-{bd.month:02d}-{bd.day:02d}"
            birth_time = f"{bd.hour:02d}:{bd.minute:02d}"
            return api_calculate(
                birth_date, birth_time, bd.place,
                gender=bd.gender, ayanamsa=bd.ayanamsa, name=bd.name,
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
                    extra_doshas[key] = to_json(full_report[key])
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


@app.post("/match/simple")
async def match_simple(
    name1: str = Form(..., description="Person 1 name"),
    date1: str = Form(..., description="Person 1 birth date (YYYY-MM-DD)"),
    time1: str = Form(..., description="Person 1 birth time (HH:MM)"),
    place1: str = Form(..., description="Person 1 birth place"),
    name2: str = Form(..., description="Person 2 name"),
    date2: str = Form(..., description="Person 2 birth date (YYYY-MM-DD)"),
    time2: str = Form(..., description="Person 2 birth time (HH:MM)"),
    place2: str = Form(..., description="Person 2 birth place"),
    ayanamsa: str = Form("Lahiri"),
):
    """
    💑 **Simple Marriage Compatibility Check** - Using form data!
    
    Calculate Ashtakoot Guna Milan (36-point compatibility) between two people.
    """
    try:
        r1 = api_calculate(date1, time1, place1, gender="Male", ayanamsa=ayanamsa, name=name1)
        r2 = api_calculate(date2, time2, place2, gender="Female", ayanamsa=ayanamsa, name=name2)

        nak1 = r1.get("moon_nakshatra", "")
        sign1 = r1.get("moon_sign", "")
        nak2 = r2.get("moon_nakshatra", "")
        sign2 = r2.get("moon_sign", "")

        guna = _calc_ashtakoot(nak1, sign1, nak2, sign2)

        # Try extra doshas
        extra_doshas = {}
        try:
            from kundali.kundali_matching import match_kundalis
            full_report = match_kundalis(r1, r2)
            for key in ("nadi_dosha", "rajju_dosha", "vedha_dosha",
                        "kuja_dosha_p1", "kuja_dosha_p2",
                        "mahendra", "stree_deergha"):
                if key in full_report:
                    extra_doshas[key] = to_json(full_report[key])
        except Exception:
            pass

        return {
            "person1": {"name": name1, "moon_sign": sign1, "moon_nakshatra": nak1},
            "person2": {"name": name2, "moon_sign": sign2, "moon_nakshatra": nak2},
            "ashtakoot": guna,
            "extra_doshas": extra_doshas,
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/transit_calendar")
async def transit_calendar_endpoint(data: BirthData, months: int = 12):
    """
    Get a transit calendar for a native covering the next `months` months.

    Returns month-by-month gochara data for all planets.
    """
    try:
        import swisseph as swe
        from kundali.utils import get_sign
        from kundali.constants import gochara_effects, zodiac_signs

        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        natal = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
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
                    "effect":          to_json(effect),
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
                "effect":          to_json(gochara_effects.get("Ke", {}).get(ke_house, "Neutral")),
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


# ---------------------------------------------------------------------------
# Decision Engine Endpoints
# ---------------------------------------------------------------------------

@app.post("/decisions/career")
async def career_decision(data: BirthData):
    """
    🎯 **Career Decision Engine**
    
    Analyze the chart for career guidance based on:
    - 10th house lord and planets
    - D10 (Dasamsa) chart analysis
    - Atmakaraka placement
    - Current dasha period
    - Ashtakavarga strength
    
    Returns recommended career fields, current period analysis, and actionable advice.
    """
    try:
        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        result = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return to_json(get_career_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/decisions/career/simple")
async def career_decision_simple(
    name: str = Query(..., description="Name of the person"),
    date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Query(..., description="Birth time (HH:MM)"),
    place: str = Query(..., description="Birth place"),
    gender: str = Query("Male"),
    ayanamsa: str = Query("Lahiri"),
):
    """🎯 Career guidance via URL parameters."""
    try:
        result = api_calculate(date, time, place, gender=gender, ayanamsa=ayanamsa, name=name)
        return to_json(get_career_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/decisions/marriage")
async def marriage_decision(data: BirthData):
    """
    💍 **Marriage Decision Engine**
    
    Analyze optimal marriage timing based on:
    - 7th house lord and Venus condition
    - Dasha periods favorable for marriage
    - Transit triggers (Jupiter, Venus over 7th)
    - Manglik/Kuja dosha assessment
    
    Returns marriage windows, favorable periods, and relationship advice.
    """
    try:
        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        result = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return to_json(get_marriage_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/decisions/marriage/simple")
async def marriage_decision_simple(
    name: str = Query(..., description="Name of the person"),
    date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Query(..., description="Birth time (HH:MM)"),
    place: str = Query(..., description="Birth place"),
    gender: str = Query("Male"),
    ayanamsa: str = Query("Lahiri"),
):
    """💍 Marriage timing guidance via URL parameters."""
    try:
        result = api_calculate(date, time, place, gender=gender, ayanamsa=ayanamsa, name=name)
        return to_json(get_marriage_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/decisions/business")
async def business_decision(data: BirthData):
    """
    💼 **Business Decision Engine**
    
    Analyze business and investment timing based on:
    - 2nd, 10th, 11th house analysis (wealth houses)
    - Current dasha for financial gains/losses
    - Saturn and Jupiter transit effects
    - Ashtakavarga strength in wealth houses
    
    Returns business timing advice, investment windows, and risk periods.
    """
    try:
        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        result = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return to_json(get_business_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/decisions/business/simple")
async def business_decision_simple(
    name: str = Query(..., description="Name of the person"),
    date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Query(..., description="Birth time (HH:MM)"),
    place: str = Query(..., description="Birth place"),
    gender: str = Query("Male"),
    ayanamsa: str = Query("Lahiri"),
):
    """💼 Business & investment guidance via URL parameters."""
    try:
        result = api_calculate(date, time, place, gender=gender, ayanamsa=ayanamsa, name=name)
        return to_json(get_business_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/decisions/health")
async def health_decision(data: BirthData):
    """
    🏥 **Health Decision Engine**
    
    Analyze health vulnerabilities based on:
    - 6th house (disease), 8th house (chronic), 12th house (hospitalization)
    - Weak/afflicted planets and their body parts
    - Current dasha health implications
    - Vulnerable periods to watch
    
    Returns health focus areas, vulnerable periods, and preventive advice.
    """
    try:
        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        result = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return to_json(get_health_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/decisions/health/simple")
async def health_decision_simple(
    name: str = Query(..., description="Name of the person"),
    date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Query(..., description="Birth time (HH:MM)"),
    place: str = Query(..., description="Birth place"),
    gender: str = Query("Male"),
    ayanamsa: str = Query("Lahiri"),
):
    """🏥 Health guidance via URL parameters."""
    try:
        result = api_calculate(date, time, place, gender=gender, ayanamsa=ayanamsa, name=name)
        return to_json(get_health_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/decisions/travel")
async def travel_decision(data: BirthData):
    """
    ✈️ **Travel Decision Engine**
    
    Analyze travel and relocation guidance based on:
    - 3rd house (short travel), 9th house (long travel), 12th house (foreign)
    - Rahu/Ketu axis for foreign connections
    - Best directions based on planetary strengths
    - Current dasha for travel timing
    
    Returns favorable directions, travel timing, and relocation advice.
    """
    try:
        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        result = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return to_json(get_travel_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/decisions/travel/simple")
async def travel_decision_simple(
    name: str = Query(..., description="Name of the person"),
    date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Query(..., description="Birth time (HH:MM)"),
    place: str = Query(..., description="Birth place"),
    gender: str = Query("Male"),
    ayanamsa: str = Query("Lahiri"),
):
    """✈️ Travel & relocation guidance via URL parameters."""
    try:
        result = api_calculate(date, time, place, gender=gender, ayanamsa=ayanamsa, name=name)
        return to_json(get_travel_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/decisions/daily")
async def daily_guidance(data: BirthData):
    """
    📅 **Daily Guidance Engine**
    
    Get personalized guidance for today based on:
    - Current transits over natal chart
    - Pancha Pakshi system (5-bird activity)
    - Moon transit and Tarabala
    - Hora (planetary hour) recommendations
    
    Returns today's favorable/unfavorable activities and timing.
    """
    try:
        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        result = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return to_json(get_daily_guidance(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/decisions/daily/simple")
async def daily_guidance_simple(
    name: str = Query(..., description="Name of the person"),
    date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Query(..., description="Birth time (HH:MM)"),
    place: str = Query(..., description="Birth place"),
    gender: str = Query("Male"),
    ayanamsa: str = Query("Lahiri"),
):
    """📅 Daily guidance via URL parameters."""
    try:
        result = api_calculate(date, time, place, gender=gender, ayanamsa=ayanamsa, name=name)
        return to_json(get_daily_guidance(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/decisions/education")
async def education_decision(data: BirthData):
    """
    📚 **Education Decision Engine**
    
    Analyze best fields of study based on:
    - 4th house (basic education), 5th house (higher learning)
    - D24 (Siddhamsa) chart for educational specialization
    - Mercury and Jupiter strength
    - Current dasha for learning periods
    
    Returns recommended fields, learning style, and academic timing.
    """
    try:
        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        result = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return to_json(get_education_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/decisions/education/simple")
async def education_decision_simple(
    name: str = Query(..., description="Name of the person"),
    date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Query(..., description="Birth time (HH:MM)"),
    place: str = Query(..., description="Birth place"),
    gender: str = Query("Male"),
    ayanamsa: str = Query("Lahiri"),
):
    """📚 Education guidance via URL parameters."""
    try:
        result = api_calculate(date, time, place, gender=gender, ayanamsa=ayanamsa, name=name)
        return to_json(get_education_decision(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/decisions/life-analysis")
async def life_analysis_decision(data: BirthData):
    """
    🔭 **Advanced Life Analysis Engine**

    Unified synthesis across major life domains:
    - Identity, career, wealth, relationships, family
    - Health/longevity risk profile
    - Learning, travel, spirituality, and timing windows

    Returns a broad life map with strongest domains, pressure points, and
    a non-fatalistic longevity profile.
    """
    try:
        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        result = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return to_json(get_life_analysis(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/decisions/life-analysis/simple")
async def life_analysis_decision_simple(
    name: str = Query(..., description="Name of the person"),
    date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Query(..., description="Birth time (HH:MM)"),
    place: str = Query(..., description="Birth place"),
    gender: str = Query("Male"),
    ayanamsa: str = Query("Lahiri"),
):
    """🔭 Advanced life analysis via URL parameters."""
    try:
        result = api_calculate(date, time, place, gender=gender, ayanamsa=ayanamsa, name=name)
        return to_json(get_life_analysis(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/decisions/compatibility")
async def compatibility_decision(req: MatchRequest):
    """
    💑 **Compatibility Decision Engine**
    
    Deep compatibility analysis between two people:
    - Ashtakoot Guna Milan (36 points)
    - Manglik dosha comparison
    - Nakshatra compatibility
    - Dasha synchronization
    
    Returns compatibility score, detailed breakdown, and relationship advice.
    """
    try:
        def _calc(bd: BirthData):
            birth_date = f"{bd.year:04d}-{bd.month:02d}-{bd.day:02d}"
            birth_time = f"{bd.hour:02d}:{bd.minute:02d}"
            return api_calculate(
                birth_date, birth_time, bd.place,
                gender=bd.gender, ayanamsa=bd.ayanamsa, name=bd.name,
            )

        r1 = _calc(req.person1)
        r2 = _calc(req.person2)
        return to_json(get_compatibility_decision(r1, r2))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/decisions/all")
async def all_decisions(data: BirthData):
    """
    🌟 **All Decisions Engine**
    
    Get comprehensive life guidance across all 9 decision areas:
    - Career, Marriage, Business, Health
    - Travel, Daily, Education, Life Analysis
    
    Returns a complete decision report for holistic life planning.
    """
    try:
        birth_date = f"{data.year:04d}-{data.month:02d}-{data.day:02d}"
        birth_time = f"{data.hour:02d}:{data.minute:02d}"
        result = api_calculate(
            birth_date, birth_time, data.place,
            gender=data.gender, ayanamsa=data.ayanamsa, name=data.name,
        )
        return to_json(get_all_decisions(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/decisions/all/simple")
async def all_decisions_simple(
    name: str = Query(..., description="Name of the person"),
    date: str = Query(..., description="Birth date (YYYY-MM-DD)"),
    time: str = Query(..., description="Birth time (HH:MM)"),
    place: str = Query(..., description="Birth place"),
    gender: str = Query("Male"),
    ayanamsa: str = Query("Lahiri"),
):
    """🌟 All decisions via URL parameters."""
    try:
        result = api_calculate(date, time, place, gender=gender, ayanamsa=ayanamsa, name=name)
        return to_json(get_all_decisions(result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
