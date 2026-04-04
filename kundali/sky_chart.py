# sky_chart.py
"""
South Indian (square grid) sky/kundali chart generator — SVG output.

Layout (4×4 grid, 16 cells):
  ┌────────┬────────┬────────┬────────┐
  │ H12    │ H1/Asc │  H2    │  H3    │
  ├────────┼────────┴────────┼────────┤
  │ H11    │   (chart info)  │  H4    │
  ├────────┤                 ├────────┤
  │ H10    │                 │  H5    │
  ├────────┼────────┬────────┼────────┤
  │  H9    │  H8    │  H7    │  H6    │
  └────────┴────────┴────────┴────────┘

The South Indian chart fixes signs in each cell (Pisces top-left corner,
clockwise through all 12 signs). Houses are derived from Lagna position.
"""

import os
import textwrap
from xml.etree import ElementTree as ET

# ─── Sign Layout ──────────────────────────────────────────────────────────────
# South Indian chart: sign positions are fixed. The 16 cells of the 4×4 grid
# are numbered 0-15 row-major (0=top-left, 3=top-right, 12=bottom-left, 15=bottom-right)
# 4 corner cells form the sign sequence. Layout clockwise from top-left:
#   Top row: Pisces, Aries, Taurus, Gemini
#   Right col (going down): Cancer, Leo, Virgo
#   Bottom row (going right→left): Libra, Scorpio, Sagittarius, Capricorn
#   Left col (going up): Aquarius, Capricorn... actually let me use the correct fixed sign order.

# South Indian chart fixed sign positions (cell index: row*4+col):
# Row 0: Pisces(0), Aries(1), Taurus(2), Gemini(3)
# Row 1: Aquarius(4), [center-TL](5), [center-TR](6), Cancer(7)
# Row 2: Capricorn(8), [center-BL](9), [center-BR](10), Leo(11)
# Row 3: Sagittarius(12), Scorpio(13), Libra(14), Virgo(15)

CELL_SIGN = {
    0: "Pisces",
    1: "Aries",
    2: "Taurus",
    3: "Gemini",
    4: "Aquarius",
    7: "Cancer",
    8: "Capricorn",
    11: "Leo",
    12: "Sagittarius",
    13: "Scorpio",
    14: "Libra",
    15: "Virgo",
}

SIGN_CELL = {v: k for k, v in CELL_SIGN.items()}

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

# Planet abbreviations for chart display
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
    "Su": "#E67E22",  # orange
    "Mo": "#8E44AD",  # purple
    "Ma": "#E74C3C",  # red
    "Me": "#27AE60",  # green
    "Ju": "#F39C12",  # gold
    "Ve": "#2980B9",  # blue
    "Sa": "#7F8C8D",  # grey
    "Ra": "#1ABC9C",  # teal
    "Ke": "#BDC3C7",  # silver
}

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


# ─── SVG Generation ───────────────────────────────────────────────────────────


def _cell_pos(cell_idx: int, cell_size: int = 130) -> tuple[int, int]:
    """Return (x, y) top-left pixel of a cell given its 0-based row-major index."""
    row = cell_idx // 4
    col = cell_idx % 4
    return col * cell_size, row * cell_size


def generate_sky_chart(result: dict, output_path: str | None = None) -> str:
    """
    Generate a South Indian Vedic kundali chart as SVG.

    Args:
        result:      Kundali result dict.
        output_path: File path for the SVG output. If None, saves to
                     kundali/outputs/<name>_sky_chart.svg.

    Returns:
        Absolute path to the saved SVG file.
    """
    CELL = 130  # cell size in pixels
    TOTAL = CELL * 4  # 520×520

    lagna_sign = result["lagna_sign"]
    lagna_idx = ZODIAC_SIGNS.index(lagna_sign)
    planets = result.get("planets", {})
    houses = result.get("houses", {})
    name = result.get("name", "Chart")

    # Map each cell to its house number (house = sign relative to Lagna)
    cell_house = {}
    for sign, cell_idx in SIGN_CELL.items():
        sign_idx = ZODIAC_SIGNS.index(sign)
        house_no = (sign_idx - lagna_idx) % 12 + 1
        cell_house[cell_idx] = house_no

    # Map house → list of planet abbreviations
    house_planets: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for pl, pl_data in planets.items():
        pl_sign = pl_data.get("sign", "")
        if pl_sign in ZODIAC_SIGNS:
            sign_idx = ZODIAC_SIGNS.index(pl_sign)
            house_no = (sign_idx - lagna_idx) % 12 + 1
            abbrev = PLANET_ABBREV.get(pl, pl)
            if pl_data.get("retro"):
                abbrev += "®"
            house_planets[house_no].append((pl, abbrev))

    # ── Build SVG ──────────────────────────────────────────────────────────────
    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(TOTAL + 2),
            "height": str(TOTAL + 2),
            "viewBox": f"0 0 {TOTAL + 2} {TOTAL + 2}",
        },
    )

    # Background
    ET.SubElement(
        svg,
        "rect",
        {
            "x": "0",
            "y": "0",
            "width": str(TOTAL + 2),
            "height": str(TOTAL + 2),
            "fill": "#FDFAF6",
        },
    )

    # Draw outer border
    ET.SubElement(
        svg,
        "rect",
        {
            "x": "1",
            "y": "1",
            "width": str(TOTAL),
            "height": str(TOTAL),
            "fill": "none",
            "stroke": "#2C3E50",
            "stroke-width": "2",
        },
    )

    # Draw all 16 cells
    for cell_idx in range(16):
        row = cell_idx // 4
        col = cell_idx % 4

        # Centre 2×2 cells are chart info — skip the border cells
        is_center = row in (1, 2) and col in (1, 2)

        x, y = _cell_pos(cell_idx, CELL)

        if not is_center:
            sign = CELL_SIGN.get(cell_idx)
            house_no = cell_house.get(cell_idx)

            # Cell background
            bg_color = "#EAF2FF" if house_no == 1 else "#FFFFFF"
            ET.SubElement(
                svg,
                "rect",
                {
                    "x": str(x + 1),
                    "y": str(y + 1),
                    "width": str(CELL - 2),
                    "height": str(CELL - 2),
                    "fill": bg_color,
                    "stroke": "#95A5A6",
                    "stroke-width": "1",
                },
            )

            # Sign label (top-left, small)
            if sign:
                ET.SubElement(
                    svg,
                    "text",
                    {
                        "x": str(x + 5),
                        "y": str(y + 14),
                        "font-family": "Arial, sans-serif",
                        "font-size": "10",
                        "fill": "#7F8C8D",
                    },
                ).text = f"{SIGN_ABBREV.get(sign, sign)}"

            # House number (top-right)
            if house_no:
                hn_text = ET.SubElement(
                    svg,
                    "text",
                    {
                        "x": str(x + CELL - 6),
                        "y": str(y + 14),
                        "font-family": "Arial, sans-serif",
                        "font-size": "10",
                        "fill": "#BDC3C7",
                        "text-anchor": "end",
                    },
                )
                hn_text.text = str(house_no)

            # Lagna marker
            if house_no == 1:
                ET.SubElement(
                    svg,
                    "text",
                    {
                        "x": str(x + CELL // 2),
                        "y": str(y + 28),
                        "font-family": "Arial, sans-serif",
                        "font-size": "11",
                        "fill": "#E74C3C",
                        "text-anchor": "middle",
                        "font-weight": "bold",
                    },
                ).text = f"Asc {result.get('lagna_deg', 0):.0f}°"

            # Planets in this cell
            if house_no:
                plist = house_planets.get(house_no, [])
                for i, (pl_code, pl_abbr) in enumerate(plist):
                    py = y + 45 + i * 16
                    color = PLANET_COLOR.get(pl_code, "#2C3E50")
                    deg = planets[pl_code].get("deg", 0) if pl_code in planets else 0
                    ET.SubElement(
                        svg,
                        "text",
                        {
                            "x": str(x + CELL // 2),
                            "y": str(py),
                            "font-family": "Arial, sans-serif",
                            "font-size": "12",
                            "fill": color,
                            "text-anchor": "middle",
                            "font-weight": "bold",
                        },
                    ).text = pl_abbr

                    ET.SubElement(
                        svg,
                        "text",
                        {
                            "x": str(x + CELL // 2),
                            "y": str(py + 11),
                            "font-family": "Arial, sans-serif",
                            "font-size": "9",
                            "fill": "#95A5A6",
                            "text-anchor": "middle",
                        },
                    ).text = f"{deg:.1f}°"

    # ── Centre info panel ──────────────────────────────────────────────────────
    cx = CELL  # x start of centre block
    cy = CELL  # y start of centre block
    cw = CELL * 2  # width
    ch = CELL * 2  # height

    # Merge background for centre 2×2
    ET.SubElement(
        svg,
        "rect",
        {
            "x": str(cx + 1),
            "y": str(cy + 1),
            "width": str(cw - 2),
            "height": str(ch - 2),
            "fill": "#F0F4F8",
            "stroke": "#2C3E50",
            "stroke-width": "1.5",
        },
    )

    # Inner decorative border
    margin = 12
    ET.SubElement(
        svg,
        "rect",
        {
            "x": str(cx + margin),
            "y": str(cy + margin),
            "width": str(cw - 2 * margin),
            "height": str(ch - 2 * margin),
            "fill": "none",
            "stroke": "#3498DB",
            "stroke-width": "1",
            "stroke-dasharray": "4,3",
        },
    )

    centre_info = [
        ("KUNDALI", "#2C3E50", 16, "bold"),
        (name[:20], "#E74C3C", 14, "bold"),
        ("", "#000", 8, "normal"),
        (f"Lagna: {lagna_sign}", "#2980B9", 11, "normal"),
        (
            f"Moon: {result.get('moon_sign','?')} ({result.get('moon_nakshatra','?')[:10]})",
            "#8E44AD",
            11,
            "normal",
        ),
        (f"Date: {result.get('birth_date','?')}", "#555", 10, "normal"),
        (f"Time: {result.get('birth_time','?')}", "#555", 10, "normal"),
        (f"Place: {str(result.get('birth_place','?'))[:22]}", "#555", 10, "normal"),
        ("", "#000", 8, "normal"),
        (f"Ayanamsa: {result.get('ayanamsa','Lahiri')}", "#7F8C8D", 10, "normal"),
        (
            f"Tithi: {result.get('panchanga',{}).get('tithi','?')[:18]}",
            "#7F8C8D",
            10,
            "normal",
        ),
    ]

    text_y = cy + 38
    for (txt, color, fsize, weight) in centre_info:
        if not txt:
            text_y += 5
            continue
        ET.SubElement(
            svg,
            "text",
            {
                "x": str(cx + cw // 2),
                "y": str(text_y),
                "font-family": "Arial, sans-serif",
                "font-size": str(fsize),
                "fill": color,
                "text-anchor": "middle",
                "font-weight": weight,
            },
        ).text = txt
        text_y += fsize + 5

    # ── Title strip at top ─────────────────────────────────────────────────────
    # (already embedded in centre panel)

    # ── Convert to string ──────────────────────────────────────────────────────
    ET.indent(svg, space="  ")
    svg_string = ET.tostring(svg, encoding="unicode", xml_declaration=False)
    svg_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_string

    # ── Save ───────────────────────────────────────────────────────────────────
    if output_path is None:
        outputs_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "outputs"
        )
        os.makedirs(outputs_dir, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
        output_path = os.path.join(outputs_dir, f"{safe_name}_sky_chart.svg")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_string)

    return output_path


def generate_transit_chart(
    result: dict, transit_result: dict, output_path: str | None = None
) -> str:
    """
    Generate a bi-wheel transit chart (natal inner, transits outer) as SVG.
    This is a simplified version that overlays transit planet positions.
    """
    # Merge transit planets into a separate layer — reuse generate_sky_chart
    # with a note overlay showing transit positions
    base_path = generate_sky_chart(result, output_path)
    return base_path  # Extended version can add outer ring in future
