# north_indian_chart.py
"""
North Indian (diamond/kite) Vedic kundali chart generator — SVG output.

The authentic North Indian chart uses a diamond/kite layout where 12 triangular
cells radiate from a central square. House positions are FIXED (not signs).

Layout on a 1000×1000 canvas (VedAstro NorthChartFactory coordinates):
  H1:(475,150)  H2:(250,100)  H3:(100,200)
  H4:(250,400)  H5:(100,620)  H6:(250,825)
  H7:(475,600)  H8:(675,825)  H9:(840,620)
  H10:(675,400) H11:(840,200) H12:(675,100)
"""

import os
from xml.etree import ElementTree as ET

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
SIGN_ABBREV = {
    "Aries": "Ar",
    "Taurus": "Ta",
    "Gemini": "Ge",
    "Cancer": "Ca",
    "Leo": "Le",
    "Virgo": "Vi",
    "Libra": "Li",
    "Scorpio": "Sc",
    "Sagittarius": "Sg",
    "Capricorn": "Cp",
    "Aquarius": "Aq",
    "Pisces": "Pi",
}
PLANET_ABBREV = {
    "Su": "Su",
    "Mo": "Mo",
    "Ma": "Ma",
    "Me": "Me",
    "Ju": "Ju",
    "Ve": "Ve",
    "Sa": "Sa",
    "Ra": "Ra",
    "Ke": "Ke",
}
PLANET_COLOR = {
    "Su": "#E67E22",
    "Mo": "#8E44AD",
    "Ma": "#E74C3C",
    "Me": "#27AE60",
    "Ju": "#D4AC0D",
    "Ve": "#2980B9",
    "Sa": "#7F8C8D",
    "Ra": "#1ABC9C",
    "Ke": "#95A5A6",
}

# ── Chart geometry on 1000×1000 canvas ────────────────────────────────────────
# Named vertices of the diamond grid
_V = {
    "TL": (0, 0),
    "T": (500, 0),
    "TR": (1000, 0),
    "L": (0, 500),
    "C": (500, 500),
    "R": (1000, 500),
    "BL": (0, 1000),
    "B": (500, 1000),
    "BR": (1000, 1000),
    "MtL": (250, 250),
    "MtR": (750, 250),
    "MbL": (250, 750),
    "MbR": (750, 750),
}


def _pts(*keys):
    return " ".join(f"{_V[k][0]},{_V[k][1]}" for k in keys)


# Polygon vertices per house (clockwise)
HOUSE_POLYGONS = {
    1: _pts("T", "MtR", "C", "MtL"),  # top triangle      — Lagna
    2: _pts("TL", "T", "MtL"),  # top-left triangle
    3: _pts("TL", "MtL", "L"),  # left-upper triangle
    4: _pts("MtL", "C", "MbL", "L"),  # left diamond
    5: _pts("L", "MbL", "BL"),  # left-lower triangle
    6: _pts("MbL", "B", "BL"),  # bottom-left triangle
    7: _pts("C", "MbR", "B", "MbL"),  # bottom triangle
    8: _pts("B", "BR", "MbR"),  # bottom-right triangle
    9: _pts("MbR", "BR", "R"),  # right-lower triangle
    10: _pts("C", "R", "MbR", "MtR"),  # right diamond  ← corrected winding
    11: _pts("MtR", "TR", "R"),  # right-upper triangle
    12: _pts("T", "TR", "MtR"),  # top-right triangle
}

# Text-anchor centres per house (where sign + planets are drawn)
HOUSE_TEXT_CENTER = {
    1: (500, 195),
    2: (215, 110),
    3: (100, 295),
    4: (215, 500),
    5: (100, 705),
    6: (215, 890),
    7: (500, 805),
    8: (785, 890),
    9: (900, 705),
    10: (785, 500),
    11: (900, 295),
    12: (785, 110),
}


def _house_sign(house_no: int, lagna_sign: str) -> str:
    idx = ZODIAC_SIGNS.index(lagna_sign) if lagna_sign in ZODIAC_SIGNS else 0
    return ZODIAC_SIGNS[(idx + house_no - 1) % 12]


def generate_north_indian_chart(result: dict, output_path=None) -> str:
    """
    Generate an authentic North Indian Vedic kundali chart as SVG.
    Returns the absolute path to the saved SVG file.
    """
    W = H = 1000

    lagna_sign = result.get("lagna_sign", "Aries")
    lagna_deg = result.get("lagna_deg", 0)
    lagna_idx = ZODIAC_SIGNS.index(lagna_sign) if lagna_sign in ZODIAC_SIGNS else 0
    planets = result.get("planets", {})
    name = result.get("name", "Chart")

    # house → [(code, abbrev, degree)]
    house_planets = {h: [] for h in range(1, 13)}
    for pl_code, pl_data in planets.items():
        pl_sign = pl_data.get("sign", "")
        if pl_sign not in ZODIAC_SIGNS:
            continue
        si = ZODIAC_SIGNS.index(pl_sign)
        house_no = (si - lagna_idx) % 12 + 1
        abbrev = PLANET_ABBREV.get(pl_code, pl_code)
        if pl_data.get("retro"):
            abbrev += "(R)"
        house_planets[house_no].append((pl_code, abbrev, pl_data.get("deg", 0)))

    # SVG root
    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": "600",
            "height": "600",
            "viewBox": f"0 0 {W} {H}",
        },
    )

    # Cream background
    ET.SubElement(
        svg,
        "rect",
        {"x": "0", "y": "0", "width": str(W), "height": str(H), "fill": "#FDFAF6"},
    )

    # ── House polygons ────────────────────────────────────────────────────────
    for house_no, pts in HOUSE_POLYGONS.items():
        is_lagna = house_no == 1
        ET.SubElement(
            svg,
            "polygon",
            {
                "points": pts,
                "fill": "#E8F4FD" if is_lagna else "#FFFFFF",
                "stroke": "#2C3E50",
                "stroke-width": "2.5",
            },
        )

    # ── Lagna diagonals (X through H1 triangle) ───────────────────────────────
    for (v1, v2) in [("T", "C"), ("MtL", "MtR")]:
        x1, y1 = _V[v1]
        x2, y2 = _V[v2]
        ET.SubElement(
            svg,
            "line",
            {
                "x1": str(x1),
                "y1": str(y1),
                "x2": str(x2),
                "y2": str(y2),
                "stroke": "#C0392B",
                "stroke-width": "1.8",
                "stroke-opacity": "0.40",
            },
        )

    # ── Labels and planets per house ─────────────────────────────────────────
    for house_no in range(1, 13):
        cx, cy = HOUSE_TEXT_CENTER[house_no]
        sign = _house_sign(house_no, lagna_sign)
        sa = SIGN_ABBREV.get(sign, sign[:2])
        is_lagna = house_no == 1

        # Sign abbreviation
        ET.SubElement(
            svg,
            "text",
            {
                "x": str(cx - 22),
                "y": str(cy - 42),
                "font-family": "Arial, sans-serif",
                "font-size": "26",
                "fill": "#7F8C8D",
                "text-anchor": "middle",
            },
        ).text = sa

        # House number
        ET.SubElement(
            svg,
            "text",
            {
                "x": str(cx + 22),
                "y": str(cy - 42),
                "font-family": "Arial, sans-serif",
                "font-size": "19",
                "fill": "#BDC3C7",
                "text-anchor": "middle",
            },
        ).text = str(house_no)

        # Asc label for lagna
        if is_lagna:
            ET.SubElement(
                svg,
                "text",
                {
                    "x": str(cx),
                    "y": str(cy - 8),
                    "font-family": "Arial, sans-serif",
                    "font-size": "24",
                    "fill": "#C0392B",
                    "text-anchor": "middle",
                    "font-weight": "bold",
                },
            ).text = f"Asc {lagna_deg % 30:.1f}\u00b0"

        # Planets
        plist = house_planets.get(house_no, [])
        py_base = cy + (10 if is_lagna else 0)
        for i, (pl_code, pl_abbr, deg) in enumerate(plist):
            py = py_base + i * 52
            color = PLANET_COLOR.get(pl_code, "#2C3E50")
            ET.SubElement(
                svg,
                "text",
                {
                    "x": str(cx),
                    "y": str(py),
                    "font-family": "Arial, sans-serif",
                    "font-size": "28",
                    "fill": color,
                    "text-anchor": "middle",
                    "font-weight": "bold",
                },
            ).text = pl_abbr
            ET.SubElement(
                svg,
                "text",
                {
                    "x": str(cx),
                    "y": str(py + 22),
                    "font-family": "Arial, sans-serif",
                    "font-size": "19",
                    "fill": "#95A5A6",
                    "text-anchor": "middle",
                },
            ).text = f"{deg:.1f}\u00b0"

    # ── Centre info panel (bounded by MtL/MtR/MbL/MbR square) ───────────────
    px, py = _V["MtL"][0] + 22, _V["MtL"][1] + 22
    pw = _V["MtR"][0] - _V["MtL"][0] - 44
    ph = _V["MbL"][1] - _V["MtL"][1] - 44

    ET.SubElement(
        svg,
        "rect",
        {
            "x": str(px),
            "y": str(py),
            "width": str(pw),
            "height": str(ph),
            "fill": "#F0F4F8",
            "stroke": "#2C3E50",
            "stroke-width": "1.5",
            "rx": "8",
            "ry": "8",
        },
    )
    ET.SubElement(
        svg,
        "rect",
        {
            "x": str(px + 10),
            "y": str(py + 10),
            "width": str(pw - 20),
            "height": str(ph - 20),
            "fill": "none",
            "stroke": "#E67E22",
            "stroke-width": "1",
            "stroke-dasharray": "6,4",
            "rx": "4",
            "ry": "4",
        },
    )

    moon_sign = result.get("moon_sign", "?")
    moon_nak = result.get("moon_nakshatra", "?")
    birth_date = result.get("birth_date", "")
    birth_time = result.get("birth_time", "")
    birth_place = str(result.get("birth_place", ""))[:18]
    ayanamsa = result.get("ayanamsa", "Lahiri")
    panel_cx = 500

    centre_lines = [
        ("KUNDALI", "#2C3E50", 36, "bold"),
        (name[:18], "#C0392B", 28, "bold"),
        ("", "#000", 8, "normal"),
        (f"Lagna: {lagna_sign}", "#2980B9", 22, "normal"),
        (f"Moon:  {moon_sign}", "#8E44AD", 20, "normal"),
        (f"Nak: {moon_nak[:13]}", "#8E44AD", 18, "normal"),
        ("", "#000", 6, "normal"),
        (birth_date, "#555555", 18, "normal"),
        (birth_time, "#555555", 18, "normal"),
        (birth_place, "#555555", 16, "normal"),
        (f"Ayanamsa: {ayanamsa}", "#7F8C8D", 16, "normal"),
    ]

    ty = py + 52
    for txt, color, fsize, weight in centre_lines:
        if not txt:
            ty += fsize
            continue
        ET.SubElement(
            svg,
            "text",
            {
                "x": str(panel_cx),
                "y": str(ty),
                "font-family": "Arial, sans-serif",
                "font-size": str(fsize),
                "fill": color,
                "text-anchor": "middle",
                "font-weight": weight,
            },
        ).text = txt
        ty += fsize + 8

    # ── Serialise ─────────────────────────────────────────────────────────────
    ET.indent(svg, space="  ")
    svg_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        svg, encoding="unicode"
    )

    if output_path is None:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
        os.makedirs(out_dir, exist_ok=True)
        safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
        output_path = os.path.join(out_dir, f"{safe}_north_chart.svg")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_str)

    return output_path
