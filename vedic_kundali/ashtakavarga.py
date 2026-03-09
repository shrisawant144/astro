# Ashtakavarga Module
# Sarvashtakavarga calculation and interpretation

from constants import (
    zodiac_signs,
    ASHTAKAVARGA_REKHAS,
    sign_lords,
)


# ────────────────────────────────────────────────
# Ashtakavarga Calculation
# ────────────────────────────────────────────────
def calculate_ashtakavarga(result):
    """
    Calculate Ashtakavarga (SAV - Sarvashtakavarga) for all houses.
    
    Returns:
        dict: {
            'individual': {planet: [12 house scores]},
            'sav': [12 house scores for SAV],
            'interpretation': {house: text}
        }
    """
    planets_d1 = result["planets"]
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)
    
    # Get planet positions (0-11 from lagna)
    planet_positions = {}
    for pl in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        if pl in planets_d1:
            pl_sign = planets_d1[pl]["sign"]
            pl_idx = zodiac_signs.index(pl_sign)
            planet_positions[pl] = pl_idx
    
    planet_positions["As"] = lagna_idx  # Ascendant
    
    # Calculate individual Ashtakavarga for each planet
    individual_av = {}
    
    for target_planet in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        if target_planet not in planet_positions:
            continue
        
        house_bindus = [0] * 12  # Initialize 12 houses with 0 benefic dots
        
        rekhas = ASHTAKAVARGA_REKHAS.get(target_planet, {})
        
        # For each reference point
        for ref_point, ref_pos in planet_positions.items():
            if ref_point not in rekhas:
                continue
            
            benefic_houses = rekhas[ref_point]
            
            # Add benefic dots to appropriate houses
            for house_offset in benefic_houses:
                actual_house = (ref_pos + house_offset) % 12
                house_bindus[actual_house] += 1
        
        individual_av[target_planet] = house_bindus
    
    # Calculate SAV (Sarvashtakavarga) - sum of all individual
    sav = [0] * 12
    for planet_bindus in individual_av.values():
        for i in range(12):
            sav[i] += planet_bindus[i]
    
    # Interpret SAV scores
    interpretation = {}
    for house_num in range(1, 13):
        house_idx = (house_num - 1 + lagna_idx) % 12
        score = sav[house_idx] if house_idx < len(sav) else 0
        
        if score >= 28:
            interp = "Excellent (Very strong support)"
        elif score >= 25:
            interp = "Good (Positive support)"
        elif score >= 22:
            interp = "Average (Normal karma)"
        else:
            interp = "Weak (Challenges/delays likely)"
        
        interpretation[house_num] = {
            'score': score,
            'strength': interp
        }
    
    return {
        'individual': individual_av,
        'sav': sav,
        'interpretation': interpretation
    }


# ────────────────────────────────────────────────
# Cross-Chart Planetary Integrity
# ────────────────────────────────────────────────
def calculate_integrity_index(result):
    """Calculate Cross-Chart Planetary Integrity Index (D1-D9-D10-D7)."""
    DIGNITY_SIGNS = {
        "Su": {"exalt": "Aries", "own": ["Leo"], "deb": "Libra"},
        "Mo": {"exalt": "Taurus", "own": ["Cancer"], "deb": "Scorpio"},
        "Ma": {"exalt": "Capricorn", "own": ["Aries", "Scorpio"], "deb": "Cancer"},
        "Me": {"exalt": "Virgo", "own": ["Gemini", "Virgo"], "deb": "Pisces"},
        "Ju": {"exalt": "Cancer", "own": ["Sagittarius", "Pisces"], "deb": "Capricorn"},
        "Ve": {"exalt": "Pisces", "own": ["Taurus", "Libra"], "deb": "Virgo"},
        "Sa": {"exalt": "Libra", "own": ["Capricorn", "Aquarius"], "deb": "Aries"},
    }
    
    # D9 gets double weight for marriage context
    CHART_WEIGHTS = {"D1": 1.0, "D9": 2.0, "D10": 1.0, "D7": 1.0}
    
    integrity_results = []
    
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
            ("D7", result.get("d7", {}))
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
        if pl in result.get("navamsa", {}) and result["planets"][pl]["sign"] == result["navamsa"][pl]["sign"]:
            integrity_score += 15
        
        # Triple alignment bonus
        if pl in result.get("navamsa", {}) and pl in result.get("d10", {}):
            if (result["planets"][pl]["sign"] == result["navamsa"][pl]["sign"] == result["d10"][pl]["sign"]):
                integrity_score += 20
        
        integrity_score = max(0, min(100, integrity_score))
        
        # Reliability classification
        if integrity_score >= 80 and weak_count == 0:
            reliability = "Highly Reliable"
        elif integrity_score >= 65 and strong_count >= 2:
            reliability = "Reliable"
        elif integrity_score >= 50:
            reliability = "Moderate"
        elif weak_count >= 2:
            reliability = "Challenged"
        else:
            reliability = "Variable"
        
        integrity_results.append({
            "planet": pl,
            "score": integrity_score,
            "reliability": reliability,
            "positions": positions,
            "strong_count": strong_count,
            "weak_count": weak_count,
        })
    
    return integrity_results

