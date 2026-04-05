# report_pdf.py
"""
PDF report generator for Vedic Kundali using fpdf2.
Install: pip install fpdf2
"""

try:
    from fpdf import FPDF

    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

import os
import datetime

from . import decisions


# ---------------------------------------------------------------------------
# Colour palette (R, G, B)
# ---------------------------------------------------------------------------
DARK_BLUE = (26, 58, 92)  # #1a3a5c
MID_BLUE = (41, 98, 155)  # section sub-header
LIGHT_GRAY = (240, 244, 248)  # #f0f4f8 – alternating row bg
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (60, 60, 60)
TEXT_COLOR = (30, 30, 30)

PLANET_FULL = {
    "Su": "Sun",
    "Mo": "Moon",
    "Ma": "Mars",
    "Me": "Mercury",
    "Ju": "Jupiter",
    "Ve": "Venus",
    "Sa": "Saturn",
    "Ra": "Rahu",
    "Ke": "Ketu",
}

_FPDFBase = FPDF if FPDF_AVAILABLE else object


class KundaliPDF(_FPDFBase):
    """Custom FPDF subclass with branded header/footer on every page."""

    def __init__(self, native_name="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.native_name = native_name
        self.set_auto_page_break(auto=True, margin=15)

    # ------------------------------------------------------------------
    def header(self):
        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, self.w, 10, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.set_xy(0, 1)
        title = f"Vedic Kundali Report  |  {self.native_name}"
        self.cell(self.w, 8, title, align="C")
        self.set_text_color(*TEXT_COLOR)
        self.ln(6)

    # ------------------------------------------------------------------
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")
        self.set_text_color(*TEXT_COLOR)

    def normalize_text(self, text):
        """Auto-sanitize unicode before fpdf2 encodes to latin-1."""
        _MAP = {
            "\u2013": "-",
            "\u2014": "--",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2022": "*",
            "\u2026": "...",
            "\u00b0": "deg",
            "\u00ae": "(R)",
            "\u2605": "*",
            "\u2606": "o",
            "\u2588": "#",
            "\u2591": ".",
            "\u25a0": "#",
            "\u25a1": ".",
            "\u00e2": "a",
            "\u20ac": "EUR",
            "\u2192": "->",
            "\u2190": "<-",
            "\u25b6": ">",
            "\u25c0": "<",
        }
        for ch, rep in _MAP.items():
            text = text.replace(ch, rep)
        text = text.encode("latin-1", errors="replace").decode("latin-1")
        return super().normalize_text(text)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def section_title(self, text):
        """Draw a full-width dark-blue band with white section title."""
        self.ln(4)
        self.set_fill_color(*DARK_BLUE)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*WHITE)
        self.cell(0, 9, f"  {text}", ln=True, fill=True)
        self.set_text_color(*TEXT_COLOR)
        self.ln(2)

    def sub_section(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*MID_BLUE)
        self.cell(0, 7, text, ln=True)
        self.set_text_color(*TEXT_COLOR)

    def kv_row(self, key, value, row_idx=0):
        """Two-column key-value row with light alternating background."""
        if row_idx % 2 == 0:
            self.set_fill_color(*LIGHT_GRAY)
        else:
            self.set_fill_color(*WHITE)
        key_w = 55
        val_w = self.epw - key_w
        val_str = str(value)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*DARK_BLUE)
        # For multi-line values, use multi_cell with a saved x
        if len(val_str) > 90:
            cur_y = self.get_y()
            self.cell(key_w, 7, str(key), fill=True)
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*TEXT_COLOR)
            self.multi_cell(val_w, 7, val_str, fill=True)
        else:
            self.cell(key_w, 7, str(key), fill=True)
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*TEXT_COLOR)
            self.cell(val_w, 7, val_str, fill=True, ln=True)

    def table_header(self, cols, widths):
        """Draw a table header row."""
        self.set_fill_color(*DARK_BLUE)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        for col, w in zip(cols, widths):
            self.cell(w, 7, col, border=0, fill=True, align="C")
        self.ln()
        self.set_text_color(*TEXT_COLOR)

    def table_row(self, values, widths, row_idx=0, aligns=None):
        """Draw a single data row with alternating shading."""
        if row_idx % 2 == 0:
            self.set_fill_color(*LIGHT_GRAY)
        else:
            self.set_fill_color(*WHITE)
        self.set_font("Helvetica", "", 9)
        if aligns is None:
            aligns = ["L"] * len(values)
        for val, w, align in zip(values, widths, aligns):
            self.cell(
                w, 6, str(val) if val is not None else "-", fill=True, align=align
            )
        self.ln()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_UNICODE_MAP = {
    "\u2013": "-",
    "\u2014": "--",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2022": "*",
    "\u2026": "...",
    "\u00b0": "deg",
    "\u00ae": "(R)",
    "\u2122": "(TM)",
    "\u2103": "C",
    "\u2605": "*",
    "\u2606": "o",
    "\u2588": "#",
    "\u2591": ".",
    "\u25a0": "#",
    "\u25a1": ".",
    "\u2192": "->",
    "\u2190": "<-",
    "\u25b2": "^",
    "\u25bc": "v",
    "\u00d7": "x",
    "\u00f7": "/",
    "\u2248": "~",
    "\u2260": "!=",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u00e9": "e",
    "\u00e0": "a",
    "\u00e8": "e",
    "\u00ea": "e",
    "\u0101": "a",
    "\u012b": "i",
    "\u016b": "u",
    "\u015b": "s",
    "\u1e25": "h",
    "\u1e47": "n",
    "\u1e63": "s",
    "\u1e6d": "t",
}


def _safe(text):
    """Strip/replace characters outside latin-1 so core FPDF fonts don't crash."""
    if not isinstance(text, str):
        text = str(text)
    for ch, rep in _UNICODE_MAP.items():
        text = text.replace(ch, rep)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _sf(v, decimals=2):
    try:
        return round(float(v), decimals)
    except (TypeError, ValueError):
        return v


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def generate_pdf_report(result, output_path=None):
    """
    Generate a complete kundali PDF report.

    Args:
        result : Full kundali result dict from calculate_kundali().
        output_path : Optional file path.  Defaults to
                      kundali/outputs/<name>_report.pdf

    Returns:
        Absolute path to the generated PDF, or None if fpdf2 is not installed.
    """
    if not FPDF_AVAILABLE:
        print("[report_pdf] fpdf2 is not installed. Run: pip install fpdf2")
        return None

    name = result.get("name", "Native")

    # ---- resolve output path -----------------------------------------------
    if output_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(here, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        safe_name = name.lower().replace(" ", "_")
        output_path = os.path.join(out_dir, f"{safe_name}_report.pdf")

    pdf = KundaliPDF(native_name=name, orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=12, top=14, right=12)

    # ================================================================
    # Page 1 – Cover
    # ================================================================
    _page_cover(pdf, result, name)

    # ================================================================
    # Page 2 – Planetary Positions
    # ================================================================
    _page_planets(pdf, result)

    # ================================================================
    # Page 3 – House Overview
    # ================================================================
    _page_houses(pdf, result)

    # ================================================================
    # Page 4 – Divisional Charts D1-D9
    # ================================================================
    _page_divisional(pdf, result)

    # ================================================================
    # Page 5 – Dasha Timeline
    # ================================================================
    _page_dasha(pdf, result)

    # ================================================================
    # Page 6 – Yogas
    # ================================================================
    _page_yogas(pdf, result)

    # ================================================================
    # Page 7 – Transit Summary
    # ================================================================
    _page_transits(pdf, result)

    # ================================================================
    # Page 8 – Remedies
    # ================================================================
    _page_remedies(pdf, result)

    # ================================================================
    # Page 9 – Shadbala
    # ================================================================
    _page_shadbala(pdf, result)

    # ================================================================
    # Page 10 – Ashtakavarga
    # ================================================================
    _page_ashtakavarga(pdf, result)

    # ================================================================
    # Page 11 – Vimshopak Bala
    # ================================================================
    _page_vimshopak(pdf, result)

    # ================================================================
    # Page 12 – Chara Dasha
    # ================================================================
    _page_chara_dasha(pdf, result)

    # ================================================================
    # Page 13 – Life Guidance (Decision Engines)
    # ================================================================
    _page_decisions(pdf, result)

    pdf.output(output_path)
    return os.path.abspath(output_path)


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------


def _page_cover(pdf, result, name):
    pdf.add_page()

    # Big title banner
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(0, 14, pdf.w, 38, "F")
    pdf.set_y(18)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 12, "Vedic Kundali", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Astrological Birth Chart Report", ln=True, align="C")
    pdf.set_text_color(*TEXT_COLOR)
    pdf.ln(20)

    # Native name
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 12, name, ln=True, align="C")
    pdf.set_text_color(*TEXT_COLOR)
    pdf.ln(6)

    # Birth details card
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.rect(20, pdf.get_y(), pdf.w - 40, 56, "F")
    pdf.set_x(24)

    birth_date = result.get("birth_date", "")
    birth_time = result.get("birth_time", "")
    birth_place = result.get("birth_place", "")
    gender = result.get("gender", "")
    lagna_sign = result.get("lagna_sign", "")
    lagna_deg_raw = result.get("lagna_deg", 0)
    lagna_deg = f"{lagna_deg_raw % 30:.2f}"  # degree within sign, not full longitude
    moon_sign = result.get("moon_sign", "")
    moon_nak = result.get("moon_nakshatra", "")
    ayanamsa = result.get("ayanamsa", "Lahiri")

    details = [
        ("Date of Birth", birth_date),
        ("Time of Birth", birth_time),
        ("Place of Birth", birth_place),
        ("Gender", gender),
        ("Ascendant (Lagna)", f"{lagna_sign}  {_sf(lagna_deg, 2)}°"),
        ("Moon Sign", moon_sign),
        ("Moon Nakshatra", moon_nak),
        ("Ayanamsa", ayanamsa),
    ]
    for i, (k, v) in enumerate(details):
        pdf.set_x(24)
        pdf.kv_row(k, v, row_idx=i)

    pdf.ln(8)

    # Panchanga strip
    panchanga = result.get("panchanga", {})
    if panchanga:
        pdf.section_title("Panchanga at Birth")
        items = [
            ("Tithi", panchanga.get("tithi", "-")),
            ("Vara", panchanga.get("vara", "-")),
            ("Yoga", panchanga.get("yoga", "-")),
            ("Karana", panchanga.get("karana", "-")),
        ]
        for i, (k, v) in enumerate(items):
            pdf.kv_row(k, v, row_idx=i)

    # Report generation timestamp
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(130, 130, 130)
    now = datetime.datetime.now().strftime("%d %b %Y  %H:%M")
    pdf.cell(0, 6, f"Report generated: {now}", ln=True, align="R")
    pdf.set_text_color(*TEXT_COLOR)


def _page_planets(pdf, result):
    planets_data = result.get("planets", {})
    if not planets_data:
        return

    pdf.add_page()
    pdf.section_title("Planetary Positions")

    cols = ["Planet", "Sign", "Degree", "Nakshatra", "Dignity", "Retro"]
    widths = [28, 30, 20, 38, 28, 18]
    pdf.table_header(cols, widths)

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    for idx, code in enumerate(order):
        if code not in planets_data:
            continue
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.table_header(cols, widths)
        p = planets_data[code]
        row = [
            PLANET_FULL.get(code, code),
            p.get("sign", "-"),
            f"{_sf(p.get('deg', 0), 2)}°",
            p.get("nakshatra", "-"),
            p.get("dignity", "-") or "-",
            "R" if p.get("retro") else "",
        ]
        aligns = ["L", "L", "R", "L", "L", "C"]
        pdf.table_row(row, widths, row_idx=idx, aligns=aligns)

    # Neecha Bhanga note
    nb = result.get("neecha_bhanga_planets", [])
    if nb:
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MID_BLUE)
        names = [PLANET_FULL.get(p, p) for p in nb]
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(
            pdf.epw, 6, f"Neecha Bhanga (debility cancellation): {', '.join(names)}"
        )
        pdf.set_text_color(*TEXT_COLOR)

    # Sade Sati
    sade = result.get("sade_sati")
    if sade:
        pdf.ln(4)
        pdf.section_title("Sade Sati / Dhaiya Status")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 6, sade)


def _page_houses(pdf, result):
    houses = result.get("houses", {})
    if not houses:
        return

    lagna_sign = result.get("lagna_sign", "")
    from .constants import zodiac_signs

    pdf.add_page()
    pdf.section_title("House Overview")

    cols = ["House", "Sign", "Planets / Occupants"]
    widths = [20, 35, 125]
    pdf.table_header(cols, widths)

    lagna_idx = zodiac_signs.index(lagna_sign) if lagna_sign in zodiac_signs else 0

    for house_num in range(1, 13):
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.table_header(cols, widths)
        sign = zodiac_signs[(lagna_idx + house_num - 1) % 12]
        occ = houses.get(house_num, [])
        planets_in_house = [p for p in occ if p != "Asc"]
        planet_str = ", ".join(PLANET_FULL.get(p, p) for p in planets_in_house) or "—"
        row = [str(house_num), sign, planet_str]
        pdf.table_row(row, widths, row_idx=house_num - 1, aligns=["C", "L", "L"])

    # House lords
    house_lords = result.get("house_lords", {})
    if house_lords:
        pdf.ln(4)
        pdf.section_title("House Lords")
        lord_cols = ["House", "Sign", "Lord", "Lord Placed In House"]
        lord_widths = [20, 38, 28, 94]
        pdf.table_header(lord_cols, lord_widths)
        for h in range(1, 13):
            if h not in house_lords:
                continue
            if pdf.get_y() > pdf.h - 25:
                pdf.add_page()
                pdf.table_header(lord_cols, lord_widths)
            info = house_lords[h]
            if isinstance(info, dict):
                lord_code = info.get("lord", "-")
                lord_house = info.get("placed_in", "-")
            elif isinstance(info, (list, tuple)):
                lord_code = info[0]
                lord_house = info[1] if len(info) > 1 else "-"
            else:
                lord_code, lord_house = str(info), "-"
            sign = zodiac_signs[(lagna_idx + h - 1) % 12]
            pdf.table_row(
                [str(h), sign, PLANET_FULL.get(lord_code, lord_code), str(lord_house)],
                lord_widths,
                row_idx=h - 1,
                aligns=["C", "L", "L", "C"],
            )


def _page_divisional(pdf, result):
    planets_data = result.get("planets", {})
    if not planets_data:
        return

    pdf.add_page()
    pdf.section_title("Divisional Charts — D1 through D9 (Navamsa)")

    div_charts = [
        ("D1 (Rasi)", "sign", "deg"),
        ("D2 (Hora)", "d2_sign", "d2_deg"),
        ("D3 (Drekkana)", "d3_sign", "d3_deg"),
        ("D4 (Chaturth)", "d4_sign", "d4_deg"),
        ("D7 (Saptamsa)", "d7_sign", "d7_deg"),
        ("D9 (Navamsa)", "navamsa_sign", "navamsa_deg"),
    ]

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]

    # Build header
    header_cols = ["Planet"] + [d[0] for d in div_charts]
    col_w_planet = 24
    col_w_each = round((pdf.w - 24 - col_w_planet) / len(div_charts), 1)
    widths = [col_w_planet] + [col_w_each] * len(div_charts)

    pdf.table_header(header_cols, widths)

    for idx, code in enumerate(order):
        if code not in planets_data:
            continue
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.table_header(header_cols, widths)
        p = planets_data[code]
        row = [PLANET_FULL.get(code, code)]
        for _, sign_key, deg_key in div_charts:
            s = p.get(sign_key) or "-"
            d = p.get(deg_key)
            cell = f"{s[:3]} {_sf(d, 1)}°" if d is not None else (s[:6] if s else "-")
            row.append(cell)
        pdf.table_row(row, widths, row_idx=idx, aligns=["L"] + ["C"] * len(div_charts))

    # Navamsa extended table (full sign names)
    navamsa = result.get("navamsa", {})
    if navamsa:
        pdf.ln(6)
        pdf.section_title("D9 Navamsa — Full Detail")
        nav_cols = ["Planet", "D1 Sign", "Navamsa Sign", "Nav Degree"]
        nav_widths = [30, 42, 42, 36]
        pdf.table_header(nav_cols, nav_widths)
        for idx, code in enumerate(order):
            if code not in planets_data:
                continue
            d1_sign = planets_data[code].get("sign", "-")
            nav_info = navamsa.get(code, {})
            nav_sign = nav_info.get("sign") or "-"
            nav_deg = nav_info.get("deg")
            pdf.table_row(
                [
                    PLANET_FULL.get(code, code),
                    d1_sign,
                    nav_sign,
                    f"{_sf(nav_deg, 2)}°" if nav_deg is not None else "-",
                ],
                nav_widths,
                row_idx=idx,
                aligns=["L", "L", "L", "R"],
            )


def _page_dasha(pdf, result):
    vims = result.get("vimshottari", {})
    if not vims:
        return

    pdf.add_page()
    pdf.section_title("Vimshottari Dasha Timeline")

    # Current MD / AD / PD
    cur_md = vims.get("current_md", {})
    cur_ad = vims.get("current_ad", {})
    pd_info = result.get("vimshottari_pd", {})
    cur_pd = pd_info.get("current_pd", {})

    pdf.sub_section("Current Dasha Periods")

    def _lord_str(d):
        """Extract lord name from either a string or a dasha dict."""
        if not d:
            return "-"
        if isinstance(d, str):
            return PLANET_FULL.get(d, d)
        if isinstance(d, dict):
            lord = d.get("lord", d.get("dasha_lord", "-"))
            return PLANET_FULL.get(lord, lord)
        return str(d)

    info_rows = [
        ("Mahadasha (MD)", _lord_str(cur_md)),
        ("Antardasha (AD)", _lord_str(cur_ad)),
        ("Pratyantardasha", _lord_str(cur_pd)),
        ("Starting Lord", _lord_str(vims.get("starting_lord", "-"))),
        ("Balance at Birth", f"{vims.get('balance_at_birth_years', '-')} yrs"),
    ]
    for i, (k, v) in enumerate(info_rows):
        pdf.kv_row(k, v, row_idx=i)

    # Upcoming Mahadashas
    mahadashas = vims.get("mahadasas", [])
    if mahadashas:
        pdf.ln(6)
        pdf.section_title("Mahadasha Sequence")
        md_cols = ["#", "Lord", "Start", "End", "Duration (yrs)"]
        md_widths = [10, 30, 38, 38, 34]
        pdf.table_header(md_cols, md_widths)
        birth_jd_v = result.get("birth_jd", 0)
        birth_year_v = result.get("birth_year", 2000)
        for i, md in enumerate(mahadashas[:18]):
            if pdf.get_y() > pdf.h - 25:
                pdf.add_page()
                pdf.table_header(md_cols, md_widths)
            lord = PLANET_FULL.get(
                md.get("lord", md.get("dasha_lord", "-")), md.get("lord", "-")
            )
            dur = md.get("years", md.get("duration", "-"))
            try:
                s_yr = int(birth_year_v + (md["start_jd"] - birth_jd_v) / 365.25)
                e_yr = int(birth_year_v + (md["end_jd"] - birth_jd_v) / 365.25)
                start, end = str(s_yr), str(e_yr)
            except Exception:
                start, end = "-", "-"
            pdf.table_row(
                [str(i + 1), lord, start, end, str(dur)],
                md_widths,
                row_idx=i,
                aligns=["C", "L", "C", "C", "C"],
            )

    # Ashtottari
    ashto = result.get("ashtottari", {})
    if ashto:
        pdf.ln(6)
        pdf.section_title("Ashtottari Dasha — Current")
        ashto_info = [
            ("Current MD", _lord_str(ashto.get("current_md", "-"))),
            ("Current AD", _lord_str(ashto.get("current_ad", "-"))),
        ]
        for i, (k, v) in enumerate(ashto_info):
            pdf.kv_row(k, v, row_idx=i)

    # Yogini dasha
    yogini = result.get("yogini_dasha", {})
    if yogini:
        cur_y = yogini.get("current", {})
        if cur_y:
            pdf.ln(6)
            pdf.section_title("Yogini Dasha — Current")
            yogini_str = (
                f"{cur_y.get('yogini','-')} (Lord: {cur_y.get('lord','-')})"
                if isinstance(cur_y, dict)
                else str(cur_y)
            )
            pdf.kv_row("Current Yogini MD", yogini_str)


def _page_yogas(pdf, result):
    yogas = result.get("yogas", [])
    if not yogas:
        return

    pdf.add_page()
    pdf.section_title(f"Detected Yogas  ({len(yogas)} found)")

    # Yogas are plain strings: "Name (details) -> Meaning"
    # Layout: two columns — Yoga (name+detail) and Effect
    cols = ["#", "Yoga", "Effect / Meaning"]
    widths = [10, 105, 75]

    pdf.table_header(cols, widths)
    for i, yoga in enumerate(yogas):
        if isinstance(yoga, dict):
            raw = yoga.get("name", str(yoga))
        else:
            raw = str(yoga)

        # Split on arrow separator (may be → unicode or -> ascii after sanitize)
        raw_safe = raw.replace("\u2192", "->")
        if "->" in raw_safe:
            name_part, effect_part = raw_safe.split("->", 1)
        else:
            name_part, effect_part = raw_safe, ""

        name_part = name_part.strip()[:103]
        effect_part = effect_part.strip()[:73]

        pdf.table_row(
            [str(i + 1), name_part, effect_part],
            widths,
            row_idx=i,
            aligns=["C", "L", "L"],
        )
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.table_header(cols, widths)


def _page_transits(pdf, result):
    transits = result.get("transits", {})
    if not transits:
        return

    pdf.add_page()
    pdf.section_title("Current Gochara (Transit) Summary")

    moon_sign = result.get("moon_sign", "")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, f"Houses counted from natal Moon sign: {moon_sign}", ln=True)
    pdf.set_text_color(*TEXT_COLOR)
    pdf.ln(2)

    cols = ["Planet", "Transit Sign", "House from Moon", "Effect"]
    widths = [28, 35, 30, 87]
    pdf.table_header(cols, widths)

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    for idx, code in enumerate(order):
        if code not in transits:
            continue
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.table_header(cols, widths)
        t = transits[code]
        effect = str(t.get("effect", "-"))
        if len(effect) > 50:
            effect = effect[:47] + "..."
        pdf.table_row(
            [
                PLANET_FULL.get(code, code),
                t.get("sign", "-"),
                str(t.get("house_from_moon", "-")),
                effect,
            ],
            widths,
            row_idx=idx,
            aligns=["L", "L", "C", "L"],
        )

    # Sade Sati (if present)
    sade = result.get("sade_sati")
    if sade:
        pdf.ln(6)
        pdf.section_title("Sade Sati / Dhaiya")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 6, sade)


def _page_remedies(pdf, result):
    problems = result.get("problems", {})
    if not problems:
        return

    pdf.add_page()
    pdf.section_title("Doshas, Problems & Remedies")

    row_idx = 0
    # problems is a list of {summary, detail, remedies} dicts
    if isinstance(problems, list):
        problems_iter = [
            (p.get("summary", f"Issue {i+1}"), p) for i, p in enumerate(problems)
        ]
    else:
        problems_iter = problems.items()

    for dosha_key, dosha_info in problems_iter:
        if not dosha_info:
            continue

        # Header for each dosha group
        pdf.ln(3)
        pdf.sub_section(str(dosha_key).split(":")[0][:60])
        pdf.set_font("Helvetica", "", 9)

        if isinstance(dosha_info, dict):
            present = dosha_info.get("present", dosha_info.get("detected", True))
            desc = dosha_info.get(
                "detail", dosha_info.get("description", dosha_info.get("details", ""))
            )
            remedies = dosha_info.get("remedies", [])

            if not present:
                pdf.set_text_color(60, 130, 60)
                pdf.cell(0, 6, "Not detected.", ln=True)
                pdf.set_text_color(*TEXT_COLOR)
                continue

            if desc:
                pdf.set_text_color(*TEXT_COLOR)
                # Format multi-line descriptions (strip leading "- " bullets)
                for line in str(desc)[:500].split("\n"):
                    line = line.strip().lstrip("- ").strip()
                    if line:
                        pdf.set_x(pdf.l_margin)
                        pdf.multi_cell(pdf.epw, 6, line)

            if remedies:
                pdf.ln(1)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_x(pdf.l_margin)
                pdf.cell(pdf.epw, 6, "Suggested Remedies:", ln=True)
                pdf.set_font("Helvetica", "", 9)
                if isinstance(remedies, list):
                    for rem in remedies:
                        pdf.set_fill_color(
                            *LIGHT_GRAY
                        ) if row_idx % 2 == 0 else pdf.set_fill_color(*WHITE)
                        pdf.set_x(pdf.l_margin)
                        pdf.cell(
                            pdf.epw, 6, f"  * {str(rem)[:100]}", fill=True, ln=True
                        )
                        row_idx += 1
                else:
                    pdf.set_x(pdf.l_margin)
                    pdf.cell(pdf.epw, 6, f"  * {str(remedies)[:100]}", ln=True)

        elif isinstance(dosha_info, (list, tuple)):
            for item in dosha_info:
                pdf.set_fill_color(
                    *LIGHT_GRAY
                ) if row_idx % 2 == 0 else pdf.set_fill_color(*WHITE)
                pdf.set_x(pdf.l_margin)
                pdf.cell(pdf.epw, 6, f"  * {str(item)[:100]}", fill=True, ln=True)
                row_idx += 1
        else:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 6, str(dosha_info)[:300])

        row_idx += 1

        if pdf.get_y() > pdf.h - 20:
            pdf.add_page()
            pdf.section_title("Doshas, Problems & Remedies (cont.)")


# ---------------------------------------------------------------------------
# New sections: Shadbala, Ashtakavarga, Vimshopak Bala, Chara Dasha
# ---------------------------------------------------------------------------


def _page_shadbala(pdf, result):
    shadbala = result.get("shadbala", {})
    if not shadbala:
        return

    pdf.add_page()
    pdf.section_title("Shadbala — Six Sources of Planetary Strength")

    # Determine available component keys from first entry
    sample = next(iter(shadbala.values()), {})
    if isinstance(sample, dict):
        comp_keys = [
            k
            for k in sample.keys()
            if k not in ("total", "total_rupas", "strength", "label")
        ]
    else:
        comp_keys = []

    short_labels = {
        "sthana": "Sthana",
        "dig": "Dig",
        "kala": "Kala",
        "chesta": "Chesta",
        "naisargika": "Naisar",
        "drik": "Drik",
        "sthana_bala": "Sthana",
        "dig_bala": "Dig",
        "kala_bala": "Kala",
        "chesta_bala": "Chesta",
        "naisargika_bala": "Naisar",
        "drik_bala": "Drik",
    }

    display_keys = comp_keys[:6]  # cap at 6 component columns
    col_labels = [short_labels.get(k, k[:6]) for k in display_keys]

    cols = ["Planet", "Total Rupas"] + col_labels + ["Grade"]
    # Distribute widths across page
    epw = pdf.epw
    w_pl = 28
    w_tot = 22
    w_gr = 20
    n_comp = len(display_keys)
    w_comp = round((epw - w_pl - w_tot - w_gr) / max(n_comp, 1), 1) if n_comp else 0
    widths = [w_pl, w_tot] + [w_comp] * n_comp + [w_gr]

    pdf.table_header(cols, widths)

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
    for idx, code in enumerate(order):
        if code not in shadbala:
            continue
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.table_header(cols, widths)
        data = shadbala[code]
        if isinstance(data, dict):
            total = data.get("total_rupas", data.get("total", "-"))
            grade = data.get("strength", data.get("label", "-"))
            comps = [str(_sf(data.get(k, "-"), 2)) for k in display_keys]
        else:
            total, grade, comps = str(data), "-", ["-"] * n_comp
        row = (
            [PLANET_FULL.get(code, code), str(_sf(total, 2))] + comps + [str(grade)[:8]]
        )
        aligns = ["L", "R"] + ["R"] * n_comp + ["C"]
        pdf.table_row(row, widths, row_idx=idx, aligns=aligns)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        pdf.epw,
        5,
        "Shadbala measures planetary strength from six sources: Sthana (positional), "
        "Dig (directional), Kala (temporal), Chesta (motional), Naisargika (natural), "
        "Drik (aspectual). Higher Rupas = stronger planet.",
    )
    pdf.set_text_color(*TEXT_COLOR)


def _page_ashtakavarga(pdf, result):
    ashta = result.get("ashtakavarga", {})
    if not ashta:
        return

    pdf.add_page()
    pdf.section_title("Ashtakavarga — Bindu (Benefic Point) Scores")

    # ── SAV (Sarvashtakavarga) by house ──────────────────────────────────────
    sav_by_house = None
    by_house = ashta.get("by_house", {})
    sav_list = ashta.get("sav", [])

    if by_house:
        pdf.sub_section("Sarvashtakavarga (SAV) by House")
        h_cols = ["House", "Sign", "SAV Score", "Strength"]
        h_widths = [20, 40, 30, 90]
        pdf.table_header(h_cols, h_widths)
        for h in range(1, 13):
            if pdf.get_y() > pdf.h - 25:
                pdf.add_page()
                pdf.table_header(h_cols, h_widths)
            info = by_house.get(h, by_house.get(str(h), {}))
            sign = info.get("sign", "-") if isinstance(info, dict) else "-"
            sav = info.get("sav", "-") if isinstance(info, dict) else "-"
            strength = info.get("strength", "-") if isinstance(info, dict) else "-"
            pdf.table_row(
                [str(h), sign, str(sav), str(strength)],
                h_widths,
                row_idx=h - 1,
                aligns=["C", "L", "C", "L"],
            )
    elif sav_list:
        pdf.sub_section("Sarvashtakavarga (SAV) — 12-House Scores")
        h_cols = ["House"] + [str(i) for i in range(1, 13)]
        h_widths = [30] + [round(pdf.epw - 30) // 12] * 12
        pdf.table_header(h_cols, h_widths)
        pdf.table_row(
            ["SAV"] + [str(v) for v in sav_list[:12]],
            h_widths,
            row_idx=0,
            aligns=["L"] + ["C"] * 12,
        )

    # ── Individual planet bindus ──────────────────────────────────────────────
    individual = ashta.get("individual", {})
    if individual:
        pdf.ln(5)
        pdf.sub_section("Individual Planet Bindus per House")
        order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
        pl_cols = ["Planet"] + [str(i) for i in range(1, 13)] + ["Total"]
        cw = round((pdf.epw - 30) / 13, 1)
        pl_widths = [30] + [cw] * 13
        pdf.table_header(pl_cols, pl_widths)
        for idx, code in enumerate(order):
            if code not in individual:
                continue
            if pdf.get_y() > pdf.h - 25:
                pdf.add_page()
                pdf.table_header(pl_cols, pl_widths)
            bindus = individual[code]
            if isinstance(bindus, (list, tuple)):
                total = sum(int(b) for b in bindus[:12] if str(b).isdigit())
                row = (
                    [PLANET_FULL.get(code, code)]
                    + [str(b) for b in bindus[:12]]
                    + [str(total)]
                )
            else:
                row = [PLANET_FULL.get(code, code)] + ["-"] * 12 + ["-"]
            pdf.table_row(row, pl_widths, row_idx=idx, aligns=["L"] + ["C"] * 13)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        pdf.epw,
        5,
        "Ashtakavarga: Each planet casts benefic bindus (0 or 1) into each house. "
        "28+ bindus in a house indicates excellent results. SAV (sum of all planets) "
        "above 28 per house is generally favourable.",
    )
    pdf.set_text_color(*TEXT_COLOR)


def _page_vimshopak(pdf, result):
    vimshopak = result.get("vimshopak_bala", {})
    if not vimshopak:
        return

    pdf.add_page()
    pdf.section_title("Vimshopak Bala — Divisional Chart Strength")

    # vimshopak_bala can be {planet: {total, d1, d9, ...}} or {planet: float}
    sample = next(iter(vimshopak.values()), {})
    if isinstance(sample, dict):
        div_keys = [k for k in sample.keys() if k not in ("total", "grade", "label")]
        short = {
            "d1": "D1",
            "d2": "D2",
            "d3": "D3",
            "d4": "D4",
            "d7": "D7",
            "d9": "D9",
            "d10": "D10",
            "d12": "D12",
            "d16": "D16",
            "d20": "D20",
            "d24": "D24",
            "d27": "D27",
            "d30": "D30",
            "d40": "D40",
            "d45": "D45",
            "d60": "D60",
        }
        show_divs = div_keys[:8]  # cap columns
        div_labels = [short.get(k, k[:4]) for k in show_divs]
        cw = round((pdf.epw - 28 - 22) / max(len(show_divs) + 1, 1), 1)
        cols = ["Planet", "Total"] + div_labels
        widths = [28, 22] + [cw] * len(show_divs)
    else:
        cols = ["Planet", "Vimshopak Score", "Grade"]
        widths = [35, 60, 85]
        show_divs = []

    pdf.table_header(cols, widths)

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    for idx, code in enumerate(order):
        if code not in vimshopak:
            continue
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.table_header(cols, widths)
        data = vimshopak[code]
        if isinstance(data, dict):
            total = _sf(data.get("total", "-"), 2)
            comps = [str(_sf(data.get(k, "-"), 2)) for k in show_divs]
            row = [PLANET_FULL.get(code, code), str(total)] + comps
            aligns = ["L", "R"] + ["R"] * len(show_divs)
        else:
            grade = "-"
            row = [PLANET_FULL.get(code, code), str(_sf(data, 2)), grade]
            aligns = ["L", "R", "C"]
        pdf.table_row(row, widths, row_idx=idx, aligns=aligns)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        pdf.epw,
        5,
        "Vimshopak Bala: Composite strength derived from all 16 divisional charts. "
        "Maximum = 20 points. Score above 15 is very strong; below 5 is weak.",
    )
    pdf.set_text_color(*TEXT_COLOR)


def _page_chara_dasha(pdf, result):
    chara = result.get("chara_dasha", {})
    if not chara:
        return

    pdf.add_page()
    pdf.section_title("Chara Dasha (Jaimini) — Sign-Based Dasha")

    # Current period info
    cur = chara.get("current", {})
    if cur:
        pdf.sub_section("Current Chara Dasha")
        rows = []
        if isinstance(cur, dict):
            for k, v in cur.items():
                rows.append((str(k).replace("_", " ").title(), str(v)))
        for i, (k, v) in enumerate(rows[:6]):
            pdf.kv_row(k, v, row_idx=i)

    # Full sequence
    sequence = chara.get("sequence", chara.get("mahadashas", chara.get("periods", [])))
    if not sequence and isinstance(chara, list):
        sequence = chara

    if sequence:
        pdf.ln(5)
        pdf.sub_section("Chara Mahadasha Sequence")
        cols = ["#", "Sign (Rasi)", "Start", "End", "Duration (yrs)"]
        widths = [10, 45, 38, 38, 34]
        # fill remaining width
        widths[1] += round(pdf.epw - sum(widths), 1)
        pdf.table_header(cols, widths)
        for i, period in enumerate(sequence[:24]):
            if pdf.get_y() > pdf.h - 25:
                pdf.add_page()
                pdf.table_header(cols, widths)
            if isinstance(period, dict):
                sign = period.get("sign", period.get("rasi", period.get("lord", "-")))
                start = period.get("start", period.get("start_year", "-"))
                end = period.get("end", period.get("end_year", "-"))
                dur = period.get("years", period.get("duration", "-"))
            elif isinstance(period, (list, tuple)) and len(period) >= 2:
                sign, start, end, dur = (list(period) + ["-", "-", "-"])[:4]
            else:
                sign, start, end, dur = str(period), "-", "-", "-"
            pdf.table_row(
                [str(i + 1), str(sign), str(start), str(end), str(dur)],
                widths,
                row_idx=i,
                aligns=["C", "L", "C", "C", "C"],
            )

    if not cur and not sequence:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 8, "Chara Dasha data not available in this chart.", ln=True)
        pdf.set_text_color(*TEXT_COLOR)


# ---------------------------------------------------------------------------
# Life Guidance / Decision Engines
# ---------------------------------------------------------------------------

def _page_decisions(pdf, result):
    """Generate pages for all 7 decision engine outputs."""
    
    # Get all decisions at once
    try:
        all_decisions = decisions.get_all_decisions(result)
    except Exception:
        return  # Skip if decisions module fails
    
    if not all_decisions:
        return

    # ========== CAREER GUIDANCE ==========
    career = all_decisions.get("career", {})
    if career:
        pdf.add_page()
        pdf.section_title("Career Guidance")
        
        # Recommended Fields
        fields = career.get("recommended_fields", [])
        if fields:
            pdf.sub_section("Recommended Career Fields")
            for i, field in enumerate(fields[:10]):
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(8, 6, f"{i+1}.", align="R")
                pdf.cell(0, 6, f"  {field}", ln=True)
        
        # Current Period
        period = career.get("current_period", {})
        if period:
            pdf.ln(3)
            pdf.sub_section("Current Career Period")
            items = [
                ("Mahadasha", period.get("mahadasha", "-")),
                ("Antardasha", period.get("antardasha", "-")),
                ("Good for Career", "Yes" if period.get("good_for_career") else "No"),
            ]
            for i, (k, v) in enumerate(items):
                pdf.kv_row(k, str(v), row_idx=i)
        
        # Advice
        advice = career.get("advice", "")
        if advice:
            pdf.ln(3)
            pdf.sub_section("Career Advice")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(advice)))
        
        # D10 Insights
        d10 = career.get("d10_insights", [])
        if d10:
            pdf.ln(3)
            pdf.sub_section("Dasamsa (D10) Insights")
            for insight in d10[:5]:
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(pdf.epw, 5, f"• {pdf.normalize_text(str(insight))}")

    # ========== MARRIAGE GUIDANCE ==========
    marriage = all_decisions.get("marriage", {})
    if marriage:
        pdf.add_page()
        pdf.section_title("Marriage & Relationships")
        
        # Readiness
        readiness = marriage.get("readiness", "")
        if readiness:
            pdf.sub_section("Marriage Readiness")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(readiness)))
        
        # Favorable Windows
        windows = marriage.get("favorable_windows", [])
        if windows:
            pdf.ln(3)
            pdf.sub_section("Favorable Marriage Windows")
            for i, window in enumerate(windows[:6]):
                pdf.set_font("Helvetica", "", 10)
                if isinstance(window, dict):
                    period = window.get("period", window.get("window", str(window)))
                    pdf.cell(0, 6, f"{i+1}. {period}", ln=True)
                else:
                    pdf.cell(0, 6, f"{i+1}. {window}", ln=True)
        
        # Spouse Characteristics
        spouse = marriage.get("spouse_characteristics", {})
        if spouse:
            pdf.ln(3)
            pdf.sub_section("Spouse Characteristics")
            for i, (k, v) in enumerate(list(spouse.items())[:8]):
                pdf.kv_row(str(k).replace("_", " ").title(), str(v), row_idx=i)
        
        # Advice
        advice = marriage.get("advice", "")
        if advice:
            pdf.ln(3)
            pdf.sub_section("Marriage Advice")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(advice)))

    # ========== BUSINESS & FINANCE ==========
    business = all_decisions.get("business", {})
    if business:
        pdf.add_page()
        pdf.section_title("Business & Finance Guidance")
        
        # Business Aptitude
        aptitude = business.get("aptitude", business.get("business_aptitude", ""))
        if aptitude:
            pdf.sub_section("Business Aptitude")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(aptitude)))
        
        # Recommended Sectors
        sectors = business.get("recommended_sectors", business.get("sectors", []))
        if sectors:
            pdf.ln(3)
            pdf.sub_section("Recommended Business Sectors")
            for i, sector in enumerate(sectors[:8]):
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, f"{i+1}. {sector}", ln=True)
        
        # Financial Periods
        fin_period = business.get("financial_period", business.get("current_period", {}))
        if fin_period and isinstance(fin_period, dict):
            pdf.ln(3)
            pdf.sub_section("Current Financial Period")
            for i, (k, v) in enumerate(list(fin_period.items())[:6]):
                pdf.kv_row(str(k).replace("_", " ").title(), str(v), row_idx=i)
        
        # Investment Advice
        invest = business.get("investment_advice", business.get("advice", ""))
        if invest:
            pdf.ln(3)
            pdf.sub_section("Financial Advice")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(invest)))

    # ========== HEALTH GUIDANCE ==========
    health = all_decisions.get("health", {})
    if health:
        pdf.add_page()
        pdf.section_title("Health Guidance")
        
        # Constitution
        constitution = health.get("constitution", health.get("body_type", ""))
        if constitution:
            pdf.sub_section("Constitution & Body Type")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(constitution)))
        
        # Vulnerable Areas
        areas = health.get("vulnerable_areas", health.get("health_concerns", []))
        if areas:
            pdf.ln(3)
            pdf.sub_section("Areas Requiring Attention")
            for i, area in enumerate(areas[:8]):
                pdf.set_font("Helvetica", "", 10)
                if isinstance(area, dict):
                    name = area.get("area", area.get("name", str(area)))
                    pdf.cell(0, 6, f"• {name}", ln=True)
                else:
                    pdf.cell(0, 6, f"• {area}", ln=True)
        
        # Favorable Practices
        practices = health.get("favorable_practices", health.get("recommendations", []))
        if practices:
            pdf.ln(3)
            pdf.sub_section("Recommended Health Practices")
            for i, practice in enumerate(practices[:8]):
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, f"• {practice}", ln=True)
        
        # Health Advice
        advice = health.get("advice", "")
        if advice:
            pdf.ln(3)
            pdf.sub_section("Health Advice")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(advice)))

    # ========== TRAVEL GUIDANCE ==========
    travel = all_decisions.get("travel", {})
    if travel:
        pdf.add_page()
        pdf.section_title("Travel & Relocation Guidance")
        
        # Favorable Directions
        directions = travel.get("favorable_directions", travel.get("directions", []))
        if directions:
            pdf.sub_section("Favorable Directions")
            for i, direction in enumerate(directions[:8]):
                pdf.set_font("Helvetica", "", 10)
                if isinstance(direction, dict):
                    dir_name = direction.get("direction", str(direction))
                    reason = direction.get("reason", "")
                    text = f"• {dir_name}" + (f" — {reason}" if reason else "")
                else:
                    text = f"• {direction}"
                pdf.cell(0, 6, text, ln=True)
        
        # Foreign Settlement
        foreign = travel.get("foreign_settlement", travel.get("foreign", {}))
        if foreign:
            pdf.ln(3)
            pdf.sub_section("Foreign Settlement Potential")
            if isinstance(foreign, dict):
                for i, (k, v) in enumerate(list(foreign.items())[:6]):
                    pdf.kv_row(str(k).replace("_", " ").title(), str(v), row_idx=i)
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(foreign)))
        
        # Travel Timing
        timing = travel.get("favorable_periods", travel.get("timing", []))
        if timing:
            pdf.ln(3)
            pdf.sub_section("Favorable Travel Periods")
            for i, period in enumerate(timing[:5]):
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, f"• {period}", ln=True)
        
        # Travel Advice
        advice = travel.get("advice", "")
        if advice:
            pdf.ln(3)
            pdf.sub_section("Travel Advice")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(advice)))

    # ========== EDUCATION GUIDANCE ==========
    education = all_decisions.get("education", {})
    if education:
        pdf.add_page()
        pdf.section_title("Education Guidance")
        
        # Learning Style
        style = education.get("learning_style", "")
        if style:
            pdf.sub_section("Learning Style")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(style)))
        
        # Recommended Fields
        fields = education.get("recommended_fields", education.get("fields", []))
        if fields:
            pdf.ln(3)
            pdf.sub_section("Recommended Fields of Study")
            for i, field in enumerate(fields[:10]):
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, f"{i+1}. {field}", ln=True)
        
        # Academic Periods
        periods = education.get("favorable_periods", education.get("academic_periods", []))
        if periods:
            pdf.ln(3)
            pdf.sub_section("Favorable Academic Periods")
            for i, period in enumerate(periods[:5]):
                pdf.set_font("Helvetica", "", 10)
                if isinstance(period, dict):
                    pdf.cell(0, 6, f"• {period.get('period', str(period))}", ln=True)
                else:
                    pdf.cell(0, 6, f"• {period}", ln=True)
        
        # Education Advice
        advice = education.get("advice", "")
        if advice:
            pdf.ln(3)
            pdf.sub_section("Education Advice")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(advice)))

    # ========== DAILY GUIDANCE ==========
    daily = all_decisions.get("daily_guidance", {})
    if daily:
        pdf.add_page()
        pdf.section_title("Daily Guidance & Muhurtha")
        
        # Today's Overview
        overview = daily.get("overview", daily.get("today", ""))
        if overview:
            pdf.sub_section("Today's Overview")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(overview)))
        
        # Auspicious Activities
        auspicious = daily.get("auspicious_activities", daily.get("favorable", []))
        if auspicious:
            pdf.ln(3)
            pdf.sub_section("Auspicious Activities for Today")
            for activity in auspicious[:8]:
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, f"• {activity}", ln=True)
        
        # Activities to Avoid
        avoid = daily.get("activities_to_avoid", daily.get("unfavorable", []))
        if avoid:
            pdf.ln(3)
            pdf.sub_section("Activities to Avoid")
            for activity in avoid[:8]:
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, f"• {activity}", ln=True)
        
        # Lucky Elements
        lucky = daily.get("lucky_elements", {})
        if lucky:
            pdf.ln(3)
            pdf.sub_section("Lucky Elements")
            items = []
            if lucky.get("color"):
                items.append(("Lucky Color", lucky["color"]))
            if lucky.get("number"):
                items.append(("Lucky Number", str(lucky["number"])))
            if lucky.get("direction"):
                items.append(("Lucky Direction", lucky["direction"]))
            if lucky.get("gemstone"):
                items.append(("Lucky Gemstone", lucky["gemstone"]))
            for i, (k, v) in enumerate(items):
                pdf.kv_row(k, v, row_idx=i)
        
        # Daily Advice
        advice = daily.get("advice", daily.get("general_advice", ""))
        if advice:
            pdf.ln(3)
            pdf.sub_section("Daily Advice")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(advice)))
