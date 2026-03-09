# Divisional Charts Module
# D9 (Navamsa), D7 (Saptamsa), D10 (Dasamsa) calculations

from constants import zodiac_signs


# ────────────────────────────────────────────────
# Navamsa (D9) Calculation
# ────────────────────────────────────────────────
def get_navamsa_sign_and_deg(full_lon):
    """Calculate Navamsa (D9) sign and degree."""
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    nav_size = 30.0 / 9
    navamsa_in_rasi = int(deg_in_rasi / nav_size)
    start_nav_idx = [0, 9, 6, 3][rasi_idx % 4]  # Fire/Earth/Air/Water
    nav_sign_idx = (start_nav_idx + navamsa_in_rasi) % 12
    remainder = deg_in_rasi % nav_size
    deg_in_nav = remainder * 9
    return zodiac_signs[nav_sign_idx], round(deg_in_nav, 2)


# ────────────────────────────────────────────────
# Saptamsa (D7) Calculation
# ────────────────────────────────────────────────
def get_d7_sign_and_deg(full_lon):
    """Calculate Saptamsa (D7) sign and degree."""
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    sapt_size = 30.0 / 7
    sapt_idx = int(deg_in_rasi / sapt_size)
    if rasi_idx % 2 == 0:  # Odd signs
        start_idx = rasi_idx
    else:
        start_idx = (rasi_idx + 6) % 12
    new_idx = (start_idx + sapt_idx) % 12
    frac = (deg_in_rasi % sapt_size) / sapt_size
    deg_in_d7 = frac * 30
    return zodiac_signs[new_idx], round(deg_in_d7, 2)


# ────────────────────────────────────────────────
# Dasamsa (D10) Calculation
# ────────────────────────────────────────────────
def get_d10_sign_and_deg(full_lon):
    """Calculate Dasamsa (D10) sign and degree."""
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    dasa_size = 3.0
    dasa_idx = int(deg_in_rasi / dasa_size)
    if rasi_idx % 2 == 0:  # Odd signs
        start_idx = rasi_idx
    else:
        start_idx = (rasi_idx + 8) % 12
    new_idx = (start_idx + dasa_idx) % 12
    frac = (deg_in_rasi % dasa_size) / dasa_size
    deg_in_d10 = frac * 30
    return zodiac_signs[new_idx], round(deg_in_d10, 2)


# ────────────────────────────────────────────────
# Calculate all divisional charts for a planet
# ────────────────────────────────────────────────
def calculate_divisional(planet_code, planet_full_lon, ra_lon=None, ke_lon=None):
    """Calculate all divisional chart positions for a planet."""
    if planet_code == "Ra":
        p_lon = ra_lon
    elif planet_code == "Ke":
        p_lon = ke_lon
    else:
        p_lon = planet_full_lon
    
    ns, nd = get_navamsa_sign_and_deg(p_lon)
    d7s, d7d = get_d7_sign_and_deg(p_lon)
    d10s, d10d = get_d10_sign_and_deg(p_lon)
    
    return {
        "navamsa_sign": ns,
        "navamsa_deg": nd,
        "d7_sign": d7s,
        "d7_deg": d7d,
        "d10_sign": d10s,
        "d10_deg": d10d,
    }

