# ashtakavarga.py
"""
Ashtakavarga (Sarvashtakavarga) calculation.
Computes benefic points for each planet and the SAV for all houses.
"""

from constants import ASHTAKAVARGA_REKHAS, zodiac_signs


def calculate_ashtakavarga(result):
    """
    Calculate Ashtakavarga (SAV - Sarvashtakavarga) for all houses.

    Args:
        result (dict): The kundali result dictionary containing:
            - planets: D1 planet data with 'sign'
            - lagna_sign: Lagna sign name

    Returns:
        dict: {
            'individual': {planet: [12 house scores]},
            'sav': [12 house scores for SAV],
            'interpretation': {house: {'score': int, 'strength': str}}
        }
    """
    planets_d1 = result["planets"]
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)

    # Get planet positions (0-11 from zodiac, not from lagna)
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

        # For each reference point (planets + Ascendant)
        for ref_point, ref_pos in planet_positions.items():
            if ref_point not in rekhas:
                continue

            benefic_houses = rekhas[ref_point]

            # Add benefic dots to appropriate houses
            for house_offset in benefic_houses:
                # Calculate actual house (0-11) from reference position
                actual_house = (ref_pos + house_offset) % 12
                house_bindus[actual_house] += 1

        individual_av[target_planet] = house_bindus

    # Calculate SAV (Sarvashtakavarga) - sum of all individual Ashtakavargas
    sav = [0] * 12
    for planet_bindus in individual_av.values():
        for i in range(12):
            sav[i] += planet_bindus[i]

    # Interpret SAV scores
    interpretation = {}
    for house_num in range(1, 13):
        # House index in zodiac order (0-11)
        house_idx = (house_num - 1 + lagna_idx) % 12
        score = sav[house_idx]

        if score >= 28:
            interp = "Excellent (Very strong support)"
        elif score >= 25:
            interp = "Good (Positive support)"
        elif score >= 22:
            interp = "Average (Normal karma)"
        else:
            interp = "Weak (Challenges/delays likely)"

        interpretation[house_num] = {"score": score, "strength": interp}

    return {"individual": individual_av, "sav": sav, "interpretation": interpretation}
