# report_pdf.py
"""
PDF report generator for Vedic Kundali using fpdf2.
Install: pip install fpdf2
"""

try:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    XPos = YPos = None

import os
import io
import datetime
import math
import re
import contextlib

from . import decisions
from . import printing


# ---------------------------------------------------------------------------
# Colour palette (R, G, B)
# ---------------------------------------------------------------------------
DARK_BLUE = (24, 46, 71)
MID_BLUE = (56, 91, 128)
LIGHT_GRAY = (238, 242, 247)
PAGE_BG = (248, 245, 238)
CARD_BG = (255, 255, 255)
SOFT_BLUE = (231, 238, 246)
ACCENT_GOLD = (186, 149, 92)
ACCENT_GOLD_LIGHT = (228, 214, 188)
BORDER_COLOR = (214, 220, 228)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (68, 68, 68)
MUTED_TEXT = (112, 112, 112)
TEXT_COLOR = (34, 34, 34)

HEADER_BAR_HEIGHT = 12.0
HEADER_ACCENT_HEIGHT = 1.0
CONTENT_TOP_Y = 24.0
SECTION_BAR_HEIGHT = 10.0
SECTION_GAP_AFTER = 3.0
CONTINUATION_GAP_AFTER = 3.0

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
        self._pending_page_style = "standard"
        self._page_styles = {}
        self.current_part_title = ""
        self.set_auto_page_break(auto=True, margin=15)

    def add_styled_page(self, style="standard"):
        self._pending_page_style = style
        self.add_page()

    def start_content_flow(self):
        self.set_y(CONTENT_TOP_Y)

    def start_new_standard_page(self, continuation_title=None):
        self.add_styled_page("standard")
        self.start_content_flow()
        if continuation_title:
            self.continuation_heading(continuation_title)

    def _current_page_style(self):
        page_no = self.page_no()
        style = self._page_styles.get(page_no)
        if style is None:
            style = getattr(self, "_pending_page_style", "standard") or "standard"
            self._page_styles[page_no] = style
            self._pending_page_style = "standard"
        return style

    def cell(self, *args, **kwargs):
        """Back-compat shim for fpdf2's deprecated ln= API."""
        ln = kwargs.pop("ln", None)
        if ln is not None and "new_x" not in kwargs and "new_y" not in kwargs and XPos:
            if ln:
                kwargs["new_x"] = XPos.LMARGIN
                kwargs["new_y"] = YPos.NEXT
            else:
                kwargs["new_x"] = XPos.RIGHT
                kwargs["new_y"] = YPos.TOP
        return super().cell(*args, **kwargs)

    # ------------------------------------------------------------------
    def header(self):
        style = self._current_page_style()

        self.set_fill_color(*PAGE_BG)
        self.rect(0, 0, self.w, self.h, "F")

        if style == "cover":
            self.set_y(14)
            return

        if style == "divider":
            self.set_y(CONTENT_TOP_Y)
            return

        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, self.w, HEADER_BAR_HEIGHT, "F")
        self.set_fill_color(*ACCENT_GOLD)
        self.rect(0, HEADER_BAR_HEIGHT, self.w, HEADER_ACCENT_HEIGHT, "F")

        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 8.5)
        self.set_xy(self.l_margin, 2.2)
        self.cell(0, 4.5, self.normalize_text("Vedic Kundali Report"))

        if self.current_part_title:
            self.set_font("Helvetica", "", 7.5)
            self.set_xy(self.l_margin, 6.8)
            self.cell(0, 3.2, self.normalize_text(self.current_part_title[:58]))

        self.set_font("Helvetica", "B", 8.5)
        self.set_xy(0, 2.2)
        self.cell(
            self.w - self.r_margin,
            4.5,
            self.normalize_text(self.native_name),
            align="R",
        )

        self.set_text_color(*TEXT_COLOR)
        self.set_y(CONTENT_TOP_Y)

    # ------------------------------------------------------------------
    def footer(self):
        if self._page_styles.get(self.page_no(), "standard") != "standard":
            return

        self.set_draw_color(*ACCENT_GOLD_LIGHT)
        self.line(self.l_margin, self.h - 15, self.w - self.r_margin, self.h - 15)
        self.set_y(-11)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*MUTED_TEXT)
        self.cell(0, 7, f"Page {self.page_no()}", align="C")
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
            "\u2191": "^",
            "\u2193": "v",
            "\u25b6": ">",
            "\u25c0": "<",
            "\u2122": "(TM)",
            "\u2103": "C",
            "\u2713": "v",
            "\u2714": "v",
            "\u2717": "x",
            "\u2718": "x",
            "\u26a0": "!",
            "\u00d7": "x",
            "\u00f7": "/",
            "\u2248": "~",
            "\u2260": "!=",
            "\u2264": "<=",
            "\u2265": ">=",
        }
        for ch, rep in _MAP.items():
            text = text.replace(ch, rep)
        text = text.encode("latin-1", errors="replace").decode("latin-1")
        return super().normalize_text(text)

    def ensure_space(self, height):
        """Start a new page when a block would run into the footer."""
        if self.get_y() + height > self.page_break_trigger:
            self.start_new_standard_page()

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def section_title(self, text):
        """Draw a premium section band with accent marker and spacing."""
        self.ensure_space(SECTION_BAR_HEIGHT + 12)
        if self.get_y() < CONTENT_TOP_Y:
            self.set_y(CONTENT_TOP_Y)
        elif self.get_y() > CONTENT_TOP_Y + 1:
            self.ln(2.5)

        y = self.get_y()
        self.set_fill_color(*DARK_BLUE)
        self.rect(self.l_margin, y, self.epw, SECTION_BAR_HEIGHT, "F")
        self.set_fill_color(*ACCENT_GOLD)
        self.rect(self.l_margin, y, 5.5, SECTION_BAR_HEIGHT, "F")
        self.set_xy(self.l_margin + 8, y + 1.3)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*WHITE)
        self.cell(self.epw - 10, 7, self.normalize_text(text))
        self.set_text_color(*TEXT_COLOR)
        self.set_y(y + SECTION_BAR_HEIGHT + SECTION_GAP_AFTER)

    def continuation_heading(self, text):
        self.set_y(CONTENT_TOP_Y)
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(*MID_BLUE)
        self.cell(0, 5.5, self.normalize_text(f"{text} (cont.)"), ln=True)
        self.set_draw_color(*ACCENT_GOLD_LIGHT)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_text_color(*TEXT_COLOR)
        self.ln(CONTINUATION_GAP_AFTER)

    def sub_section(self, text):
        self.ensure_space(10)
        if self.get_y() > CONTENT_TOP_Y + 1:
            self.ln(1.5)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*MID_BLUE)
        self.cell(0, 6, self.normalize_text(text), ln=True)
        self.set_draw_color(*ACCENT_GOLD)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.l_margin + 34, self.get_y())
        self.set_line_width(0.2)
        self.ln(1.4)
        self.set_text_color(*TEXT_COLOR)

    def kv_row(self, key, value, row_idx=0):
        """Two-column key-value row with light alternating background."""
        if row_idx % 2 == 0:
            self.set_fill_color(*SOFT_BLUE)
        else:
            self.set_fill_color(*CARD_BG)
        self.set_draw_color(*BORDER_COLOR)
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

    def table_header(self, cols, widths, font_size=9, row_height=7):
        """Draw a table header row."""
        self.set_fill_color(*DARK_BLUE)
        self.set_font("Helvetica", "B", font_size)
        self.set_text_color(*WHITE)
        for col, w in zip(cols, widths):
            self.cell(w, row_height, col, border=0, fill=True, align="C")
        self.ln()
        self.set_text_color(*TEXT_COLOR)

    def table_row(
        self, values, widths, row_idx=0, aligns=None, font_size=9, row_height=6
    ):
        """Draw a single data row with alternating shading."""
        if row_idx % 2 == 0:
            self.set_fill_color(*LIGHT_GRAY)
        else:
            self.set_fill_color(*WHITE)
        self.set_font("Helvetica", "", font_size)
        if aligns is None:
            aligns = ["L"] * len(values)
        for val, w, align in zip(values, widths, aligns):
            self.cell(
                w,
                row_height,
                str(val) if val is not None else "-",
                fill=True,
                align=align,
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
    "\u2500": "-",
    "\u2501": "-",
    "\u2502": "|",
    "\u2503": "|",
    "\u250c": "+",
    "\u2510": "+",
    "\u2514": "+",
    "\u2518": "+",
    "\u251c": "+",
    "\u2524": "+",
    "\u252c": "+",
    "\u2534": "+",
    "\u253c": "+",
    "\u2550": "=",
    "\u2551": "|",
    "\u2554": "+",
    "\u2557": "+",
    "\u255a": "+",
    "\u255d": "+",
    "\u2550": "=",
    "\u2713": "v",
    "\u2717": "x",
    "\u2714": "v",
    "\u2718": "x",
    "\u26a0": "!",
    "\u2605": "*",
    "\u2606": "o",
    "\u00b0": "deg",
}


def _safe(text):
    """Strip/replace characters outside latin-1 so core FPDF fonts don't crash."""
    if not isinstance(text, str):
        text = str(text)
    for ch, rep in _UNICODE_MAP.items():
        text = text.replace(ch, rep)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _has_content(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _display_value(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(v) for v in value if _has_content(v)) or "-"
    if isinstance(value, dict):
        parts = [f"{k}: {v}" for k, v in value.items() if _has_content(v)]
        return ", ".join(parts) or "-"
    return str(value)


def _as_list(value):
    if not _has_content(value):
        return []
    if isinstance(value, (list, tuple, set)):
        return [item for item in value if _has_content(item)]
    return [value]


def _safe_filename(value, default="native"):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip().lower()).strip("._")
    return cleaned or default


def _current_dasha_rows(dasha, extras=None):
    if not isinstance(dasha, dict):
        return []
    rows = [
        ("Mahadasha", dasha.get("mahadasha", "-")),
        ("Antardasha", dasha.get("antardasha", "-")),
    ]
    if extras:
        rows.extend(extras)
    return rows


def _render_kv_rows(pdf, rows):
    filtered = [(label, _display_value(value)) for label, value in rows if _has_content(value)]
    for idx, (label, value) in enumerate(filtered):
        pdf.ensure_space(8)
        pdf.kv_row(label, value, row_idx=idx)


def _render_named_rows(pdf, title, rows):
    rows = [(label, value) for label, value in rows if _has_content(value)]
    if not rows:
        return
    pdf.ensure_space(14)
    pdf.ln(3)
    pdf.sub_section(title)
    _render_kv_rows(pdf, rows)


def _render_list(pdf, title, items, numbered=False, limit=None):
    lines = []
    for item in _as_list(items):
        text = _display_value(item)
        if _has_content(text):
            lines.append(str(text))
    if limit is not None:
        lines = lines[:limit]
    if not lines:
        return
    pdf.ensure_space(14)
    pdf.ln(3)
    pdf.sub_section(title)
    pdf.set_font("Helvetica", "", 10)
    for idx, line in enumerate(lines):
        pdf.ensure_space(7)
        prefix = f"{idx + 1}. " if numbered else "* "
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 5, f"{prefix}{pdf.normalize_text(line)}")


def _render_text_block(pdf, title, text):
    if not _has_content(text):
        return
    pdf.ensure_space(14)
    pdf.ln(3)
    pdf.sub_section(title)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 5, pdf.normalize_text(str(text)))


def _render_confidence_panel(pdf, payload, title="Prediction Confidence"):
    if not isinstance(payload, dict):
        return
    rows = [
        ("Confidence Score", payload.get("confidence_score")),
        ("Confidence Label", payload.get("confidence_label")),
    ]
    if not any(_has_content(value) for _, value in rows):
        return
    _render_named_rows(pdf, title, rows)
    _render_list(pdf, "Confidence Factors", payload.get("confidence_factors"), limit=5)
    _render_list(pdf, "Confidence Limiters", payload.get("confidence_limiters"), limit=4)


def _format_vulnerable_planet(item):
    if not isinstance(item, dict):
        return _display_value(item)
    body_parts = ", ".join(item.get("body_parts", [])[:4])
    details = []
    if _has_content(item.get("reason")):
        details.append(str(item["reason"]))
    if body_parts:
        details.append(body_parts)
    suffix = f" - {' | '.join(details)}" if details else ""
    return f"{item.get('planet', 'Planet')}{suffix}"


def _format_transit_effect(code, info):
    if not isinstance(info, dict):
        return None
    house = info.get("house_from_moon", "-")
    effect = info.get("effect", "-")
    planet = PLANET_FULL.get(code, code)
    return f"{planet} in house {house}: {effect}"


def _shadbala_summary(data):
    if not isinstance(data, dict):
        return None

    components = data.get("components", {})
    if components:
        return {
            "rupas": data.get("rupas"),
            "min_rupas": data.get("min_rupas"),
            "strong": data.get("strong"),
            "sthana_bala": components.get("sthana_bala"),
            "dig_bala": components.get("dig_bala"),
            "kala_bala": components.get("kala_bala"),
            "chesta_bala": components.get("chesta_bala"),
            "naisargika_bala": components.get("naisargika_bala"),
            "drik_bala": components.get("drik_bala"),
            "ishta": data.get("ishta"),
            "kashta": data.get("kashta"),
        }

    return {
        "rupas": data.get("total_rupas", data.get("total")),
        "min_rupas": data.get("min_rupas"),
        "strong": data.get("strong", data.get("strength")),
        "sthana_bala": data.get("sthana_bala", data.get("sthana")),
        "dig_bala": data.get("dig_bala", data.get("dig")),
        "kala_bala": data.get("kala_bala", data.get("kala")),
        "chesta_bala": data.get("chesta_bala", data.get("chesta")),
        "naisargika_bala": data.get("naisargika_bala", data.get("naisargika")),
        "drik_bala": data.get("drik_bala", data.get("drik")),
        "ishta": data.get("ishta"),
        "kashta": data.get("kashta"),
    }


def _vimshopak_summary(data):
    if isinstance(data, dict):
        breakdown = data.get("breakdown")
        if isinstance(breakdown, dict):
            return {
                "score": data.get("score"),
                "strong": data.get("strong"),
                "breakdown": breakdown,
            }

        div_keys = {
            key: value
            for key, value in data.items()
            if key
            not in {
                "score",
                "total",
                "grade",
                "label",
                "strong",
                "status",
                "breakdown",
            }
            and not isinstance(value, dict)
        }
        return {
            "score": data.get("score", data.get("total")),
            "strong": data.get("strong"),
            "breakdown": div_keys,
        }

    return {"score": data, "strong": None, "breakdown": {}}


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

    name = result.get("name") or "Native"

    # ---- resolve output path -----------------------------------------------
    if output_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(here, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        safe_name = _safe_filename(name)
        output_path = os.path.join(out_dir, f"{safe_name}_report.pdf")
    else:
        output_path = os.path.abspath(output_path)
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    pdf = KundaliPDF(native_name=name, orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=12, top=14, right=12)
    pdf.set_title(f"Vedic Kundali Report - {name}")
    pdf.set_author("vedic-kundali")
    pdf.set_creator("vedic-kundali")
    pdf.set_subject("Astrological Birth Chart Report")

    # Capture the authoritative text report (single source of truth)
    buf = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()):
        printing.print_kundali(result, file=buf)
    txt = buf.getvalue()

    sections = _parse_txt_sections(txt)
    parts = _group_sections_into_parts(sections)

    _render_cover_page(pdf, result, name)

    for idx, (part_title, part_subtitle, part_sections) in enumerate(parts, start=1):
        pdf.current_part_title = (
            part_title.split("—", 1)[-1].strip() if "—" in part_title else part_title
        )
        _render_part_divider(pdf, idx, part_title, part_subtitle, part_sections)
        pdf.start_new_standard_page()
        for sec in part_sections:
            _render_section(pdf, sec)

    pdf.current_part_title = ""
    pdf.output(output_path)
    return os.path.abspath(output_path)


# ---------------------------------------------------------------------------
# Text-driven rendering (mirrors print_kundali output verbatim)
# ---------------------------------------------------------------------------

_RULE_RE = re.compile(r"^[-=─═]{5,}\s*$")
_BANNER_RE = re.compile(r"^[═=]{20,}\s*$")


def _parse_txt_sections(txt):
    """Split the txt report into (kind, title, body_lines) sections.

    kind is one of:
      'header'  — top-of-file banner block (name/birth/panchanga)
      'banner'  — major ═══ banner (e.g. LIFE GUIDANCE)
      'section' — title line followed by a --- rule
      'free'    — trailing prose (Final Analysis etc.)
    """
    lines = txt.splitlines()
    # Drop leading blank lines so the banner lands at index 0
    while lines and not lines[0].strip():
        lines.pop(0)
    n = len(lines)
    sections = []
    i = 0

    # 1) Leading banner: ═══ / VEDIC KUNDALI / ═══ + key-value lines up to first blank
    if i < n and _BANNER_RE.match(lines[i] or ""):
        header_body = []
        header_body.append(lines[i]); i += 1
        while i < n and lines[i].strip():
            header_body.append(lines[i]); i += 1
        sections.append(("header", "Birth Details & Panchanga", header_body))

    while i < n:
        line = lines[i]
        # Skip blanks between sections
        if not line.strip():
            i += 1
            continue

        # Major banner: ═══ / TITLE / ═══
        if _BANNER_RE.match(line):
            if i + 2 < n and _BANNER_RE.match(lines[i + 2] or ""):
                title = lines[i + 1].strip()
                i += 3
                sections.append(("banner", title, []))
                continue
            # Lone banner (end of file) — skip
            i += 1
            continue

        # Titled section: "Some Title:" followed by a rule line
        if i + 1 < n and _RULE_RE.match(lines[i + 1] or ""):
            title = _strip_leading_symbols(line.rstrip(": ").strip()).strip()
            i += 2
            body = []
            while i < n:
                if not lines[i].strip():
                    # Lookahead: blank + new titled section → end
                    j = i + 1
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and (
                        _BANNER_RE.match(lines[j] or "")
                        or (j + 1 < n and _RULE_RE.match(lines[j + 1] or ""))
                    ):
                        break
                    body.append(lines[i])
                    i += 1
                    continue
                body.append(lines[i])
                i += 1
            sections.append(("section", title, body))
            continue

        # Free prose block (e.g. Final Analysis after LIFE GUIDANCE banner)
        body = []
        while i < n and not _BANNER_RE.match(lines[i] or ""):
            if i + 1 < n and _RULE_RE.match(lines[i + 1] or ""):
                break
            body.append(lines[i])
            i += 1
        if any(b.strip() for b in body):
            sections.append(("free", "", body))

    return sections


# Map of section title → (part_index, part_title)
_PART_DEFS = [
    ("I",    "Foundations",              "Birth, Panchanga & Planetary Positions"),
    ("II",   "Houses & Aspects",         "Bhavas, Drishti and House Lords"),
    ("III",  "Divisional Charts",        "Vargas — D1 through D60"),
    ("IV",   "Strength & Balance",       "Shadbala, Ashtakavarga & Vimshopak"),
    ("V",    "Timing & Dasha",           "Vimshottari, Gochara & Transit"),
    ("VI",   "Doshas & Subtle Factors",  "Neecha Bhanga, Upagrahas, Avasthas"),
    ("VII",  "Specialised Systems",      "Numerology, Muhurtha, Pancha Pakshi, Jaimini"),
    ("VIII", "Life Guidance",            "Decision Engines & Final Analysis"),
]

_TITLE_TO_PART = {
    # Part I — Foundations
    "Birth Details & Panchanga": 0,
    "Planets in Rasi (D1)": 0,
    # Part II — Houses & Aspects
    "Houses (Whole Sign)": 1,
    "Aspects (Drishti) – Summary": 1,
    "Aspects (Drishti) – Full Analysis": 1,
    "House Lord Placements": 1,
    "Functional Classification Strength Index (by Lagna)": 1,
    # Part III — Divisional Charts
    "Navamsa (D9 – Marriage/Spouse/Dharma)": 2,
    "Detailed D9 – Marriage/Spouse/Dharma Analysis": 2,
    "Saptamsa (D7 – Children/Progeny)": 2,
    "Detailed D7 – Children/Progeny Analysis": 2,
    "Dasamsa (D10 – Career/Profession)": 2,
    "Detailed D10 – Career/Profession Analysis": 2,
    "Shashtiamsa (D60 – Past Life Karma)": 2,
    "Detailed D60 – Past Life Karma Analysis": 2,
    "Additional Divisional Charts": 2,
    "Drekkana (D3 – Siblings/Courage/Vitality)": 2,
    "Chaturthamsha (D4 – Property/Fortune)": 2,
    "Dwadashamsha (D12 – Parents/Ancestral Karma)": 2,
    "Shodasha (D16 – Vehicles/Comforts)": 2,
    "Vimsha (D20 – Spiritual Practice)": 2,
    "Chaturvimsha (D24 – Education/Learning)": 2,
    "Bhamsha (D27 – Strengths/Weaknesses)": 2,
    "Trimsha (D30 – Evils/Misfortune Mitigation)": 2,
    "Khavedamsha (D40 – Auspicious/Inauspicious Effects)": 2,
    "Akshavedamsha (D45 – All-round Strength)": 2,
    # Part IV — Strength & Balance
    "Ashtakavarga (Sarvashtakavarga - Marriage & Life Support Index)": 3,
    "SAV Points by House": 3,
    "Bhinnashtakavarga — Per-Planet Bindus per House": 3,
    "Shadbala — Six Sources of Planetary Strength": 3,
    "Vimshopak Bala — 20-Point Strength Across 16 Vargas": 3,
    "Cross-Chart Planetary Integrity Index (D1-D9-D10-D7)": 3,
    # Part V — Timing & Dasha
    "Vimshottari Dasha": 4,
    "Marriage Timing Insights (Enhanced Parashari) – For Male": 4,
    "Marriage Timing Insights (Enhanced Parashari) – For Female": 4,
    "Current Gochara (from Moon)": 4,
    "Ashtottari Dasha (108-year system — alternate method)": 4,
    "Yogini Dasha (36-Year Cycle)": 4,
    "Jaimini Chara Dasha (Sign-Based)": 4,
    "Tajika Solar Return Analysis": 4,
    "Transit Calendar — Next 30 Days": 4,
    # Part VI — Doshas & Subtle Factors
    "Detailed Explanation of Doshas": 5,
    "Neecha Bhanga Planets (Mercury, Saturn)": 5,
    "Upagrahas (Shadow / Sub-Planets)": 5,
    "Planetary Avasthas (States)": 5,
    # Part VII — Specialised Systems
    "Vedic Numerology": 6,
    "Muhurtha — Birth Moment Quality": 6,
    "Pancha Pakshi — Five Bird Activity System": 6,
    "Jaimini Charakaraka (The Seven Significators)": 6,
    "Pada Lagnas (Arudha A1–A12)": 6,
    "Sky Chart (SVG)": 6,
    "North Indian Chart (SVG)": 6,
    "PDF Report": 6,
    # Yogas / remedies / fructification (titles have emoji prefixes in txt)
    "YOGAS WITH STRENGTH (1-10) & ACCURATE TIMINGS": 0,
    "FRUCTIFICATION PERIODS (Full Life Timeline from 1999)": 4,
    "TARGETED REMEDIES (per detected Dosha)": 5,
    "PERSONALIZED REMEDIES (For Capricorn Lagna)": 5,
    # Part VIII — Life Guidance
}


def _strip_leading_symbols(s):
    """Drop leading emoji / symbols / whitespace from a section title."""
    i = 0
    while i < len(s) and not (s[i].isalnum() or s[i] in "(["):
        i += 1
    return s[i:]


def _normalise_title(title):
    """Strip trailing punctuation/case quirks for lookup."""
    t = title.strip().rstrip(":").strip()
    t = _strip_leading_symbols(t).strip()
    return t


def _group_sections_into_parts(sections):
    """Return [(part_title, part_subtitle, [section,...]), ...] for every part
    that has at least one section assigned.
    """
    buckets = [[] for _ in _PART_DEFS]
    in_life_guidance = False

    for sec in sections:
        kind, title, body = sec
        if kind == "banner":
            if "LIFE GUIDANCE" in title.upper():
                in_life_guidance = True
            continue

        if kind == "free":
            # Trailing prose → Life Guidance part (VIII)
            buckets[7].append(sec)
            continue

        if in_life_guidance:
            buckets[7].append(sec)
            continue

        key = _normalise_title(title)
        idx = _TITLE_TO_PART.get(key)
        if idx is None:
            # Fallback heuristics
            low = key.lower()
            if "dasha" in low or "gochara" in low or "transit" in low or "tajika" in low:
                idx = 4
            elif "divisional" in low or low.startswith(("d9", "d7", "d10", "d60", "d3", "d4", "d12", "d16", "d20", "d24", "d27", "d30", "d40", "d45")):
                idx = 2
            elif "house" in low or "aspect" in low:
                idx = 1
            elif "shadbala" in low or "ashtakavarga" in low or "vimshopak" in low:
                idx = 3
            elif "dosha" in low or "upagraha" in low or "avastha" in low or "remed" in low:
                idx = 5
            elif "yoga" in low or "fructification" in low:
                idx = 0 if "yoga" in low else 4
            elif "numerology" in low or "muhurtha" in low or "pancha pakshi" in low or "arudha" in low or "charakaraka" in low:
                idx = 6
            else:
                idx = 0
        buckets[idx].append(sec)

    parts = []
    for (roman, title, subtitle), bucket in zip(_PART_DEFS, buckets):
        if bucket:
            parts.append((f"Part {roman} — {title}", subtitle, bucket))
    return parts


# ---------------------------------------------------------------------------
# Page renderers for the txt-driven layout
# ---------------------------------------------------------------------------

_SHORT_PLANET_LINE_RE = re.compile(r"^\s*(Su|Mo|Ma|Me|Ju|Ve|Sa|Ra|Ke):\s+.+$")
_LONG_PLANET_LINE_RE = re.compile(
    r"^\s*(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\s+in\s+.+$"
)
_KV_LINE_RE = re.compile(r"^\s*([A-Za-z0-9()/'&.+ \-]{2,42})\s*:\s*(.+)\s*$")
_BULLET_LINE_RE = re.compile(r"^\s*(\d+\.)\s+(.+)$|^\s*([*•\-~✓⚠!]|->|=>|→)\s*(.+)$")
_BOX_TITLE_RE = re.compile(r"^\s*[┌├]\s*[-─]*\s*(.+?)\s*[-─]*[┐┤]\s*$")
_BOX_BORDER_RE = re.compile(r"^\s*[└┘┌┐├┤][─-]{8,}[└┘┌┐├┤]?\s*$")


def _collapse_inline_spaces(text):
    return re.sub(r"\s{2,}", " ", text.strip())


def _estimate_wrapped_lines(pdf, text, width):
    safe_width = max(width, 1)
    total = 0
    for segment in str(text).split("\n"):
        normalized = pdf.normalize_text(segment.strip())
        if not normalized:
            total += 1
            continue
        total += max(1, int(math.ceil(pdf.get_string_width(normalized) / safe_width)))
    return total


def _ensure_content_space(pdf, height, section_title=None):
    if pdf.get_y() + height <= pdf.page_break_trigger:
        return
    pdf.start_new_standard_page()
    if section_title:
        pdf.continuation_heading(section_title)


def _looks_note_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("(") and stripped.endswith(")"):
        return True
    lowered = stripped.lower()
    return lowered.startswith(("note:", "legend:", "aspect strengths:"))


def _looks_preformatted_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    if _SHORT_PLANET_LINE_RE.match(stripped) or _LONG_PLANET_LINE_RE.match(stripped):
        return True
    if re.match(r"^H\d{2}\s+\(", stripped):
        return True
    if "████" in stripped or "░" in stripped:
        return True
    if "[" in stripped and "]" in stripped and " | " in stripped:
        return True
    if re.match(
        r"^(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\s+\[",
        stripped,
    ):
        return True
    return False


def _parse_kv_line(line):
    if _looks_preformatted_line(line):
        return None
    match = _KV_LINE_RE.match(line)
    if not match:
        return None
    key, value = match.groups()
    return _collapse_inline_spaces(key), _collapse_inline_spaces(value)


def _parse_bullet_line(line):
    stripped = line.strip()
    match = _BULLET_LINE_RE.match(stripped)
    if not match:
        return None
    if match.group(1):
        return match.group(1), match.group(2).strip()
    return match.group(3), match.group(4).strip()


def _bullet_marker(prefix):
    prefix = (prefix or "*").strip()
    if prefix.endswith("."):
        return prefix
    return {
        "✓": "+",
        "✔": "+",
        "⚠": "!",
        "→": "-",
        "->": "-",
        "=>": "-",
        "•": "*",
        "-": "-",
        "~": "~",
        "!": "!",
        "*": "*",
    }.get(prefix, "*")


def _parse_box_title(line):
    stripped = line.strip()
    match = _BOX_TITLE_RE.match(stripped)
    if not match:
        return None
    title = re.sub(r"\s{2,}", " ", match.group(1)).strip(" -─")
    return title or None


def _is_inline_subheading(line):
    stripped = line.strip()
    if not stripped or len(stripped) > 72 or not stripped.endswith(":"):
        return False
    if _parse_bullet_line(stripped) is not None:
        return False
    kv = _parse_kv_line(stripped)
    return kv is None


def _render_paragraph_block(pdf, lines, section_title=None):
    text = " ".join(_collapse_inline_spaces(line) for line in lines if line.strip())
    if not text:
        return
    pdf.set_font("Times", "", 10.5)
    est_height = _estimate_wrapped_lines(pdf, text, pdf.epw) * 4.9 + 2
    _ensure_content_space(pdf, est_height, section_title=section_title)
    pdf.set_text_color(*TEXT_COLOR)
    pdf.multi_cell(pdf.epw, 4.9, pdf.normalize_text(text))
    pdf.ln(1.2)


def _render_note_block(pdf, lines, section_title=None):
    text = " ".join(_collapse_inline_spaces(line) for line in lines if line.strip())
    if not text:
        return
    pdf.set_font("Times", "I", 10)
    text_width = pdf.epw - 6
    box_height = _estimate_wrapped_lines(pdf, text, text_width) * 4.6 + 4
    _ensure_content_space(pdf, box_height + 1.5, section_title=section_title)
    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_fill_color(*SOFT_BLUE)
    pdf.set_draw_color(*ACCENT_GOLD_LIGHT)
    pdf.rect(x, y, pdf.epw, box_height, "DF")
    pdf.set_xy(x + 3, y + 2)
    pdf.set_text_color(*DARK_GRAY)
    pdf.multi_cell(text_width, 4.6, pdf.normalize_text(text))
    pdf.set_text_color(*TEXT_COLOR)
    pdf.set_y(y + box_height + 1.5)


def _render_bullet_block(pdf, items, section_title=None):
    for prefix, text in items:
        if not text:
            continue
        pdf.set_font("Times", "", 10.4)
        marker = _bullet_marker(prefix)
        text_width = pdf.epw - 7
        est_height = _estimate_wrapped_lines(pdf, text, text_width) * 4.8 + 1
        _ensure_content_space(pdf, est_height + 1, section_title=section_title)
        y = pdf.get_y()
        pdf.set_xy(pdf.l_margin, y + 0.2)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*ACCENT_GOLD)
        pdf.cell(6, 4.5, pdf.normalize_text(marker))
        pdf.set_xy(pdf.l_margin + 6.5, y)
        pdf.set_font("Times", "", 10.4)
        pdf.set_text_color(*TEXT_COLOR)
        pdf.multi_cell(text_width, 4.8, pdf.normalize_text(text))
        pdf.ln(0.2)


def _render_preformatted_block(pdf, lines, section_title=None):
    rendered = [_safe(line.rstrip()) for line in lines if line.strip()]
    if not rendered:
        return

    pdf.set_font("Courier", "", 8.3)
    line_height = 4.0

    if len(rendered) <= 10:
        box_height = len(rendered) * line_height + 4
        _ensure_content_space(pdf, box_height + 1.5, section_title=section_title)
        x = pdf.l_margin
        y = pdf.get_y()
        pdf.set_fill_color(*CARD_BG)
        pdf.set_draw_color(*BORDER_COLOR)
        pdf.rect(x, y, pdf.epw, box_height, "DF")
        pdf.set_xy(x + 3, y + 2)
        pdf.set_text_color(*DARK_GRAY)
        for raw in rendered:
            pdf.set_x(x + 3)
            pdf.cell(pdf.epw - 6, line_height, raw, ln=True)
        pdf.set_text_color(*TEXT_COLOR)
        pdf.set_y(y + box_height + 1.5)
        return

    _ensure_content_space(pdf, 10, section_title=section_title)
    pdf.set_text_color(*DARK_GRAY)
    for raw in rendered:
        if pdf.get_y() + line_height > pdf.page_break_trigger:
            pdf.start_new_standard_page()
            if section_title:
                pdf.continuation_heading(section_title)
            pdf.set_font("Courier", "", 8.4)
            pdf.set_text_color(*DARK_GRAY)
        pdf.set_x(pdf.l_margin + 2)
        pdf.cell(pdf.epw - 4, line_height, raw, ln=True)
    pdf.set_text_color(*TEXT_COLOR)
    pdf.ln(1.2)


def _render_cover_page(pdf, result, name):
    pdf.add_styled_page("cover")

    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(0, 0, pdf.w, 108, "F")
    pdf.set_fill_color(*ACCENT_GOLD)
    pdf.rect(0, 17, pdf.w, 1.2, "F")

    pdf.set_y(26)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(223, 229, 236)
    pdf.cell(0, 6, "PERSONAL BIRTH CHART REPORT", ln=True, align="C")

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 14, "VEDIC KUNDALI", ln=True, align="C")
    pdf.set_font("Times", "I", 13)
    pdf.cell(0, 7, "Planetary positions, yogas, dashas and life guidance", ln=True, align="C")

    pdf.ln(8)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(215, 223, 233)
    pdf.cell(
        0,
        6,
        "Whole Sign System | Lahiri Ayanamsa | D7, D9, D10, D60 | Marriage Timing",
        ln=True,
        align="C",
    )

    card_x = 18
    card_y = 127
    card_w = pdf.w - 36
    card_h = 86
    pdf.set_fill_color(*CARD_BG)
    pdf.set_draw_color(*BORDER_COLOR)
    pdf.rect(card_x, card_y, card_w, card_h, "DF")

    pdf.set_xy(card_x, card_y + 8)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MID_BLUE)
    pdf.cell(card_w, 5, "PREPARED FOR", ln=True, align="C")

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(card_w, 11, _safe(name), ln=True, align="C")

    meta = [
        ("Birth Date", result.get("birth_date", "N/A")),
        ("Birth Time", result.get("birth_time", "N/A")),
        ("Birth Place", result.get("birth_place", "N/A")),
        ("Gender", result.get("gender", "N/A")),
        ("Lagna", f"{result.get('lagna_sign', '?')} {result.get('lagna_deg', '?')} deg"),
        ("Moon Rasi", f"{result.get('moon_sign', '?')} - {result.get('moon_nakshatra', '?')}"),
        ("Ayanamsa", result.get("ayanamsa", "Lahiri")),
    ]

    label_color = MID_BLUE
    value_color = TEXT_COLOR
    left_x = card_x + 12
    right_x = card_x + card_w / 2 + 4
    base_y = card_y + 30
    row_gap = 11

    for idx, (label, value) in enumerate(meta[:4]):
        y = base_y + idx * row_gap
        pdf.set_xy(left_x, y)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*label_color)
        pdf.cell(0, 4.2, _safe(label))
        pdf.set_xy(left_x, y + 4.4)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*value_color)
        pdf.cell(0, 4.5, _safe(str(value)))

    for idx, (label, value) in enumerate(meta[4:]):
        y = base_y + idx * row_gap
        pdf.set_xy(right_x, y)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*label_color)
        pdf.cell(0, 4.2, _safe(label))
        pdf.set_xy(right_x, y + 4.4)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*value_color)
        pdf.cell(0, 4.5, _safe(str(value)))

    pdf.set_xy(18, 232)
    pdf.set_font("Times", "I", 10.5)
    pdf.set_text_color(*DARK_GRAY)
    pdf.multi_cell(
        pdf.w - 36,
        5,
        "This report blends foundational chart data with interpretive analysis, timing windows, and practical guidance across relationships, career, and life direction.",
        align="C",
    )

    pdf.set_y(-22)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*MUTED_TEXT)
    pdf.cell(
        0,
        6,
        f"Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ln=True,
        align="C",
    )
    pdf.set_text_color(*TEXT_COLOR)


def _render_part_divider(pdf, number, part_title, subtitle, sections):
    pdf.add_styled_page("divider")
    pdf.set_fill_color(*PAGE_BG)
    pdf.rect(0, 0, pdf.w, pdf.h, "F")

    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(0, 0, pdf.w, 22, "F")
    pdf.set_fill_color(*ACCENT_GOLD)
    pdf.rect(0, 22, pdf.w, 1.2, "F")

    title_body = part_title.split("—", 1)[-1].strip() if "—" in part_title else part_title
    section_titles = [title for _, title, _ in sections if title]

    pdf.set_xy(pdf.l_margin, 7)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 5, pdf.normalize_text("Vedic Kundali Report"))
    pdf.set_xy(0, 7)
    pdf.cell(
        pdf.w - pdf.r_margin,
        5,
        pdf.normalize_text(pdf.native_name),
        align="R",
    )

    pdf.set_y(40)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*MID_BLUE)
    pdf.cell(
        0,
        6,
        _safe(f"PART {['I','II','III','IV','V','VI','VII','VIII','IX','X'][number-1]}"),
        ln=True,
        align="C",
    )

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 27)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 12, _safe(title_body), ln=True, align="C")

    pdf.set_font("Times", "I", 13)
    pdf.set_text_color(*DARK_GRAY)
    pdf.cell(0, 7, _safe(subtitle), ln=True, align="C")

    line_y = pdf.get_y() + 4
    line_w = pdf.w * 0.22
    pdf.set_draw_color(*ACCENT_GOLD)
    pdf.line((pdf.w - line_w) / 2, line_y, (pdf.w + line_w) / 2, line_y)

    panel_x = 22
    panel_y = line_y + 10
    panel_w = pdf.w - 44
    line_height = 6.2
    panel_h = min(145, 22 + max(len(section_titles), 1) * line_height)
    pdf.set_fill_color(*CARD_BG)
    pdf.set_draw_color(*BORDER_COLOR)
    pdf.rect(panel_x, panel_y, panel_w, panel_h, "DF")

    pdf.set_xy(panel_x, panel_y + 9)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*MID_BLUE)
    pdf.cell(panel_w, 6, "Included in this section", ln=True, align="C")

    y = panel_y + 20
    pdf.set_font("Helvetica", "", 9.4 if len(section_titles) <= 10 else 8.8)
    pdf.set_text_color(*TEXT_COLOR)
    for idx, title in enumerate(section_titles, start=1):
        pdf.set_xy(panel_x + 12, y)
        pdf.cell(panel_w - 24, 5.4, _safe(f"{idx}. {title}"))
        y += line_height

    pdf.set_y(panel_y + panel_h + 14)
    pdf.set_font("Times", "I", 10.5)
    pdf.set_text_color(*MUTED_TEXT)
    pdf.cell(
        0,
        6,
        "The detailed analysis for this part begins on the following page.",
        ln=True,
        align="C",
    )
    pdf.set_text_color(*TEXT_COLOR)


def _render_section(pdf, sec):
    kind, title, body = sec

    body = [
        line
        for line in body
        if not _RULE_RE.match(line or "") and not _BOX_BORDER_RE.match((line or "").strip())
    ]

    if pdf.get_y() + 25 > pdf.page_break_trigger:
        pdf.start_new_standard_page()

    if title:
        pdf.section_title(title)

    while body and not body[0].strip():
        body = body[1:]
    while body and not body[-1].strip():
        body = body[:-1]

    section_name = title or "Guidance"
    idx = 0
    while idx < len(body):
        raw = body[idx]
        stripped = raw.strip()

        if not stripped:
            pdf.ln(1.2)
            idx += 1
            continue

        box_title = _parse_box_title(stripped)
        if box_title:
            pdf.section_title(box_title.title())
            idx += 1
            continue

        if _is_inline_subheading(stripped):
            _ensure_content_space(pdf, 10, section_title=section_name)
            pdf.sub_section(stripped.rstrip(":"))
            idx += 1
            continue

        if _looks_note_line(stripped):
            end = idx + 1
            while end < len(body) and body[end].strip() and _looks_note_line(body[end].strip()):
                end += 1
            _render_note_block(pdf, body[idx:end], section_title=section_name)
            idx = end
            continue

        bullet = _parse_bullet_line(stripped)
        if bullet is not None:
            items = []
            end = idx
            while end < len(body):
                current = body[end].strip()
                parsed = _parse_bullet_line(current)
                if not current or parsed is None:
                    break
                items.append(parsed)
                end += 1
            _render_bullet_block(pdf, items, section_title=section_name)
            idx = end
            continue

        kv = _parse_kv_line(stripped)
        if kv is not None:
            rows = []
            end = idx
            while end < len(body):
                current = body[end].strip()
                parsed = _parse_kv_line(current)
                if not current or parsed is None:
                    break
                rows.append(parsed)
                end += 1
            _ensure_content_space(pdf, len(rows) * 8 + 2, section_title=section_name)
            for row_idx, (label, value) in enumerate(rows):
                pdf.kv_row(label, value, row_idx=row_idx)
            pdf.ln(1.2)
            idx = end
            continue

        if _looks_preformatted_line(stripped):
            lines = []
            end = idx
            while end < len(body):
                current = body[end].strip()
                if not current or not _looks_preformatted_line(current):
                    break
                lines.append(body[end])
                end += 1
            _render_preformatted_block(pdf, lines, section_title=section_name)
            idx = end
            continue

        lines = []
        end = idx
        while end < len(body):
            current = body[end].strip()
            if not current:
                break
            if (
                _is_inline_subheading(current)
                or _looks_note_line(current)
                or _parse_bullet_line(current) is not None
                or _parse_kv_line(current) is not None
                or _looks_preformatted_line(current)
            ):
                break
            lines.append(body[end])
            end += 1
        _render_paragraph_block(pdf, lines, section_title=section_name)
        idx = end
    pdf.ln(1.5)


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
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        pdf.epw,
        4.5,
        "Total strength in Rupas. Classical minimums: Sun 5.0, Moon 6.0, Mars 5.0, "
        "Mercury 7.0, Jupiter 6.5, Venus 5.5, Saturn 5.0.",
    )
    pdf.set_text_color(*TEXT_COLOR)
    pdf.ln(1)

    cols = [
        "Planet",
        "Rupas",
        "Min",
        "Status",
        "Sthana",
        "Dig",
        "Kala",
        "Chesta",
        "Naisar",
        "Drik",
        "Ishta",
        "Kashta",
    ]
    widths = [22, 14, 11, 16, 18, 14, 14, 15, 17, 14, 14, 17]
    pdf.table_header(cols, widths, font_size=7.4, row_height=6)

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
    for idx, code in enumerate(order):
        if code not in shadbala:
            continue
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.table_header(cols, widths, font_size=7.4, row_height=6)
        summary = _shadbala_summary(shadbala[code]) or {}
        status = "STRONG" if summary.get("strong") else "Weak"
        row = [
            PLANET_FULL.get(code, code),
            str(_sf(summary.get("rupas", "-"), 2)),
            str(_sf(summary.get("min_rupas", "-"), 1)),
            status,
            str(_sf(summary.get("sthana_bala", "-"), 1)),
            str(_sf(summary.get("dig_bala", "-"), 1)),
            str(_sf(summary.get("kala_bala", "-"), 1)),
            str(_sf(summary.get("chesta_bala", "-"), 1)),
            str(_sf(summary.get("naisargika_bala", "-"), 1)),
            str(_sf(summary.get("drik_bala", "-"), 1)),
            str(_sf(summary.get("ishta", "-"), 1)),
            str(_sf(summary.get("kashta", "-"), 1)),
        ]
        aligns = ["L", "R", "R", "C", "R", "R", "R", "R", "R", "R", "R", "R"]
        pdf.table_row(
            row,
            widths,
            row_idx=idx,
            aligns=aligns,
            font_size=7.2,
            row_height=5.6,
        )

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        pdf.epw,
        5,
        "Shadbala measures planetary strength from six sources: Sthana (positional), "
        "Dig (directional), Kala (temporal), Chesta (motional), Naisargika (natural), "
        "Drik (aspectual). Higher Rupas = stronger planet. Higher Ishta is beneficial; "
        "lower Kashta is preferable.",
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
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        pdf.epw,
        4.5,
        "Composite score out of 20 across 16 divisional charts. The strongest weighted "
        "contributors are D1, D9, D16, and D60.",
    )
    pdf.set_text_color(*TEXT_COLOR)
    pdf.ln(1)

    cols = ["Planet", "Score", "D1", "D9", "D10", "D16", "D20", "D60", "Status"]
    widths = [24, 18, 16, 16, 18, 18, 18, 18, 24]
    pdf.table_header(cols, widths, font_size=8, row_height=6)

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    for idx, code in enumerate(order):
        if code not in vimshopak:
            continue
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.table_header(cols, widths, font_size=8, row_height=6)
        summary = _vimshopak_summary(vimshopak[code])
        breakdown = summary.get("breakdown", {})
        row = [
            PLANET_FULL.get(code, code),
            str(_sf(summary.get("score", "-"), 2)),
            str(_sf(breakdown.get("d1", "-"), 2)),
            str(_sf(breakdown.get("navamsa", breakdown.get("d9", "-")), 2)),
            str(_sf(breakdown.get("d10", "-"), 2)),
            str(_sf(breakdown.get("d16", "-"), 2)),
            str(_sf(breakdown.get("d20", "-"), 2)),
            str(_sf(breakdown.get("d60", "-"), 2)),
            "STRONG" if summary.get("strong") else "Weak",
        ]
        aligns = ["L", "R", "R", "R", "R", "R", "R", "R", "C"]
        pdf.table_row(
            row,
            widths,
            row_idx=idx,
            aligns=aligns,
            font_size=8,
            row_height=5.8,
        )

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        pdf.epw,
        5,
        "Vimshopak Bala: Maximum = 20 points. Score above 15 is very strong; below 5 "
        "is weak. D1 = Rasi, D9 = Navamsa, D10 = Dasamsa, D16 = Shodashamsa, "
        "D20 = Vimsamsa, D60 = Shashtiamsa.",
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
                if k == "current_lord":
                    v = PLANET_FULL.get(v, v)
                rows.append((str(k).replace("_", " ").title(), str(v)))
        for i, (k, v) in enumerate(rows[:6]):
            pdf.kv_row(k, v, row_idx=i)

    # Full sequence
    sequence = chara.get(
        "dashas",
        chara.get("sequence", chara.get("mahadashas", chara.get("periods", []))),
    )
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
                lord = PLANET_FULL.get(period.get("lord", "-"), period.get("lord", "-"))
                if start == "-" and end == "-":
                    by = result.get("birth_year", 2000)
                    bjd = result.get("birth_jd", 0)
                    try:
                        start = int(by + (period["start_jd"] - bjd) / 365.25)
                        end = int(by + (period["end_jd"] - bjd) / 365.25)
                    except Exception:
                        pass
                sign = f"{sign} ({lord})" if lord and lord != "-" else sign
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
    """Generate pages for all decision engine outputs."""

    try:
        all_decisions = decisions.get_all_decisions(result)
    except Exception:
        return

    if not all_decisions:
        return

    _page_prediction_quality(pdf, result, all_decisions)
    _page_life_analysis(pdf, all_decisions.get("life_analysis", {}))
    _page_career_guidance(pdf, all_decisions.get("career", {}))
    _page_marriage_guidance(pdf, all_decisions.get("marriage", {}))
    _page_business_guidance(pdf, all_decisions.get("business", {}))
    _page_health_guidance(pdf, all_decisions.get("health", {}))
    _page_travel_guidance(pdf, all_decisions.get("travel", {}))
    _page_education_guidance(pdf, all_decisions.get("education", {}))
    _page_daily_guidance(pdf, all_decisions.get("daily_guidance", {}))


def _page_prediction_quality(pdf, result, all_decisions):
    pdf.add_page()
    pdf.section_title("Prediction Confidence & Data Quality")

    input_quality = result.get("input_quality", {}) or {}
    _render_named_rows(
        pdf,
        "Input Quality",
        [
            ("Quality Score", input_quality.get("score")),
            ("Quality Label", input_quality.get("label")),
            ("Birth Place Specificity", input_quality.get("birth_place_specificity")),
            ("Location Source", result.get("location_source", input_quality.get("location_source"))),
            ("Timezone", result.get("timezone", input_quality.get("timezone"))),
            ("Timezone Source", result.get("timezone_source", input_quality.get("timezone_source"))),
        ],
    )
    _render_list(pdf, "Input Warnings", input_quality.get("warnings"), limit=5)

    rectification = result.get("birth_time_rectification", {}) or {}
    _render_named_rows(
        pdf,
        "Birth Time Rectification",
        [
            ("Applied", rectification.get("applied")),
            ("Corrected Birth Time", rectification.get("corrected_birth_time")),
            ("Offset Minutes", rectification.get("offset_minutes")),
            ("Confidence Score", rectification.get("confidence_score")),
            ("Confidence Label", rectification.get("confidence_label")),
            ("Events Used", rectification.get("events_used")),
        ],
    )
    _render_text_block(pdf, "Rectification Note", rectification.get("applied_reason"))

    confidence_summary = all_decisions.get("confidence_summary", {}) or {}
    _render_named_rows(
        pdf,
        "Overall Prediction Confidence",
        [
            ("Average Score", confidence_summary.get("average_score")),
            ("Confidence Label", confidence_summary.get("label")),
        ],
    )
    category_lines = [
        f"{str(name).replace('_', ' ').title()}: {score}/100"
        for name, score in (confidence_summary.get("categories", {}) or {}).items()
    ]
    _render_list(pdf, "Category Confidence", category_lines, limit=10)


def _format_domain_rank(item):
    if not isinstance(item, dict):
        return _display_value(item)
    return f"{item.get('domain', '')}: {item.get('score', '-')}/100 ({item.get('status', '')})"


def _format_timing_item(item):
    if not isinstance(item, dict):
        return _display_value(item)
    label = item.get("domain") or item.get("event") or "Timing"
    period = item.get("period", "")
    status = item.get("status", "")
    status_prefix = f"[{status}] " if status else ""
    return f"{label}: {status_prefix}{period}"


def _page_life_analysis(pdf, life):
    if not life:
        return

    pdf.add_page()
    pdf.section_title("Advanced Life Analysis")

    phase = life.get("current_life_phase", {})
    _render_named_rows(
        pdf,
        "Current Life Phase",
        [
            ("Mahadasha", phase.get("mahadasha")),
            ("Antardasha", phase.get("antardasha")),
            ("Theme", phase.get("theme")),
        ],
    )

    longevity = life.get("longevity_profile", {})
    _render_named_rows(
        pdf,
        "Longevity & Risk Profile",
        [
            ("Overall Resilience", longevity.get("overall_resilience")),
            ("Resilience Score", longevity.get("overall_resilience_score")),
            ("Note", longevity.get("note")),
        ],
    )
    _render_confidence_panel(pdf, life)
    _render_list(
        pdf,
        "Strongest Domains",
        [_format_domain_rank(item) for item in _as_list(life.get("strongest_domains"))],
        limit=3,
    )
    _render_list(
        pdf,
        "Domains Needing Attention",
        [_format_domain_rank(item) for item in _as_list(life.get("attention_domains"))],
        limit=3,
    )
    _render_list(pdf, "Protective Factors", longevity.get("protective_factors"), limit=5)
    _render_list(pdf, "Risk Factors", longevity.get("risk_factors"), limit=5)
    _render_list(pdf, "Sensitive Periods", longevity.get("sensitive_periods"), limit=4)
    _render_list(
        pdf,
        "Timing Overview",
        [_format_timing_item(item) for item in _as_list(life.get("timing_overview"))],
        limit=8,
    )
    _render_text_block(pdf, "Life Strategy", life.get("master_advice"))


def _page_career_guidance(pdf, career):
    if not career:
        return

    pdf.add_page()
    pdf.section_title("Career Guidance")

    _render_kv_rows(
        pdf,
        [
            ("10th House Sign", career.get("tenth_house_sign")),
            ("10th Lord", career.get("tenth_lord")),
            ("10th Lord Sign", career.get("tenth_lord_sign")),
            ("10th Lord Strength", career.get("tenth_lord_strength")),
            ("Atmakaraka", career.get("atmakaraka")),
            ("Career-Supportive Period", career.get("good_period_for_career_change")),
            (
                "10th House Ashtakavarga Bindus",
                career.get("tenth_house_ashtakavarga_bindus"),
            ),
        ],
    )
    _render_confidence_panel(pdf, career)
    _render_list(pdf, "Planets in 10th House", career.get("planets_in_10th"))
    _render_list(pdf, "Recommended Career Fields", career.get("recommended_fields"), numbered=True, limit=10)
    _render_list(pdf, "Atmakaraka Career Themes", career.get("atmakaraka_fields"), limit=5)
    _render_named_rows(
        pdf,
        "Current Career Dasha",
        _current_dasha_rows(
            career.get("current_dasha"),
            [("Good for Career Change", career.get("good_period_for_career_change"))],
        ),
    )
    _render_list(pdf, "Current Dasha Career Affinity", career.get("dasha_career_affinity"), limit=5)
    _render_list(pdf, "Dasamsa (D10) Insights", career.get("d10_insights"), limit=6)
    _render_text_block(pdf, "Career Advice", career.get("advice"))


def _page_marriage_guidance(pdf, marriage):
    if not marriage:
        return

    pdf.add_page()
    pdf.section_title("Marriage & Relationships")

    _render_kv_rows(
        pdf,
        [
            ("7th House Sign", marriage.get("seventh_house_sign")),
            ("7th Lord", marriage.get("seventh_lord")),
            ("7th Lord Sign", marriage.get("seventh_lord_sign")),
            ("7th Lord Strength", marriage.get("seventh_lord_strength")),
            ("Venus Strength", marriage.get("venus_strength")),
            ("Upapadha Lagna", marriage.get("upapadha_lagna")),
            ("Marriage-Supportive Dasha", marriage.get("favorable_dasha_for_marriage")),
            ("Sade Sati Active", marriage.get("sade_sati_active")),
        ],
    )
    _render_confidence_panel(pdf, marriage)
    _render_list(pdf, "Planets in 7th House", marriage.get("planets_in_7th"))
    _render_named_rows(
        pdf,
        "Navamsa Venus",
        [
            ("Navamsa Sign", marriage.get("navamsa_venus", {}).get("sign")),
            ("Navamsa Dignity", marriage.get("navamsa_venus", {}).get("dignity")),
        ],
    )
    _render_named_rows(
        pdf,
        "Current Marriage Dasha",
        _current_dasha_rows(
            marriage.get("current_dasha"),
            [("Favorable for Marriage", marriage.get("favorable_dasha_for_marriage"))],
        ),
    )
    _render_list(pdf, "Marriage Yogas", marriage.get("marriage_yogas"), limit=8)
    _render_list(pdf, "Marriage Blockers", marriage.get("marriage_blockers"), limit=8)
    _render_list(pdf, "Favorable Marriage Periods", marriage.get("favorable_periods"), numbered=True, limit=8)
    _render_text_block(pdf, "Marriage Advice", marriage.get("advice"))


def _page_business_guidance(pdf, business):
    if not business:
        return

    pdf.add_page()
    pdf.section_title("Business & Finance Guidance")

    _render_kv_rows(
        pdf,
        [
            ("2nd Lord", business.get("second_lord")),
            ("11th Lord", business.get("eleventh_lord")),
            ("9th Lord", business.get("ninth_lord")),
            ("5th Lord for Speculation", business.get("fifth_lord_speculation")),
            ("5th Lord Strength", business.get("fifth_lord_strength")),
            ("Business-Supportive Period", business.get("good_period_for_business")),
            ("Jupiter Transit from Moon", business.get("jupiter_transit_house")),
            ("Muhurtha Score", business.get("muhurtha_score")),
        ],
    )
    _render_confidence_panel(pdf, business)
    _render_named_rows(
        pdf,
        "Current Financial Dasha",
        _current_dasha_rows(
            business.get("current_dasha"),
            [("Good for Business", business.get("good_period_for_business"))],
        ),
    )
    _render_list(pdf, "Wealth Yogas", business.get("wealth_yogas"), limit=8)
    _render_list(pdf, "Wealth Periods", business.get("wealth_periods"), numbered=True, limit=8)
    _render_list(pdf, "Upcoming Transit Highlights", business.get("upcoming_transits_30_days"), limit=10)
    _render_text_block(pdf, "Financial Advice", business.get("advice"))


def _page_health_guidance(pdf, health):
    if not health:
        return

    pdf.add_page()
    pdf.section_title("Health Guidance")

    _render_kv_rows(
        pdf,
        [
            ("Lagna Lord", health.get("lagna_lord")),
            ("Lagna Lord Strength", health.get("lagna_lord_strength")),
            ("6th Lord", health.get("sixth_lord")),
            ("8th Lord", health.get("eighth_lord")),
            ("Overall Vitality", health.get("overall_vitality")),
            ("Risky Health Period", health.get("risky_health_period")),
            ("Sade Sati Active", health.get("sade_sati_active")),
        ],
    )
    _render_confidence_panel(pdf, health)
    _render_named_rows(pdf, "Current Health Dasha", _current_dasha_rows(health.get("current_dasha")))
    _render_list(pdf, "Planets in 6th House", health.get("planets_in_6th"))
    _render_list(pdf, "Planets in 8th House", health.get("planets_in_8th"))
    _render_list(pdf, "6th-House Risk Areas", health.get("health_risk_areas_6th"), limit=10)
    _render_list(pdf, "8th-House Risk Areas", health.get("health_risk_areas_8th"), limit=10)
    _render_list(
        pdf,
        "Vulnerable Planets",
        [_format_vulnerable_planet(item) for item in _as_list(health.get("vulnerable_planets"))],
        limit=8,
    )
    _render_text_block(pdf, "Health Advice", health.get("advice"))


def _page_travel_guidance(pdf, travel):
    if not travel:
        return

    pdf.add_page()
    pdf.section_title("Travel & Relocation Guidance")

    _render_kv_rows(
        pdf,
        [
            ("4th Lord (Home)", travel.get("fourth_lord_home")),
            ("3rd Lord (Short Travel)", travel.get("third_lord_short_travel")),
            ("9th Lord (Long Travel)", travel.get("ninth_lord_travel")),
            ("12th Lord (Foreign)", travel.get("twelfth_lord_foreign")),
            ("Best Travel Direction", travel.get("best_travel_direction")),
            ("Home Direction", travel.get("home_direction")),
            ("Foreign Settlement Likelihood", travel.get("foreign_settlement_likelihood")),
            ("Foreign Indicators Score", travel.get("foreign_indicators_score")),
            ("Travel-Supportive Period", travel.get("good_period_for_travel")),
            ("Rahu House", travel.get("rahu_house")),
        ],
    )
    _render_confidence_panel(pdf, travel)
    _render_named_rows(
        pdf,
        "Current Travel Dasha",
        _current_dasha_rows(
            travel.get("current_dasha"),
            [("Good for Travel", travel.get("good_period_for_travel"))],
        ),
    )
    _render_list(pdf, "Planets in 4th House", travel.get("planets_in_4th"))
    _render_list(pdf, "Planets in 9th House", travel.get("planets_in_9th"))
    _render_list(pdf, "Planets in 12th House", travel.get("planets_in_12th"))
    _render_text_block(pdf, "Travel Advice", travel.get("advice"))


def _page_education_guidance(pdf, education):
    if not education:
        return

    pdf.add_page()
    pdf.section_title("Education Guidance")

    _render_kv_rows(
        pdf,
        [
            ("4th House Sign", education.get("fourth_house_sign")),
            ("5th House Sign", education.get("fifth_house_sign")),
            ("4th Lord", education.get("fourth_lord")),
            ("5th Lord", education.get("fifth_lord")),
            ("9th Lord (Higher Education)", education.get("ninth_lord_higher_edu")),
            ("Mercury Strength", education.get("mercury_strength")),
            ("Jupiter Strength", education.get("jupiter_strength")),
            ("Academic Ability Score", education.get("academic_ability_score")),
            ("Education-Supportive Period", education.get("good_period_for_education")),
        ],
    )
    _render_confidence_panel(pdf, education)
    _render_named_rows(
        pdf,
        "Current Education Dasha",
        _current_dasha_rows(
            education.get("current_dasha"),
            [("Good for Education", education.get("good_period_for_education"))],
        ),
    )
    _render_list(pdf, "Planets in 4th House", education.get("planets_in_4th"))
    _render_list(pdf, "Planets in 5th House", education.get("planets_in_5th"))
    _render_list(pdf, "Recommended Fields of Study", education.get("recommended_fields"), numbered=True, limit=12)
    _render_list(pdf, "D24 Insights", education.get("d24_insights"), limit=6)
    _render_text_block(pdf, "Education Advice", education.get("advice"))


def _page_daily_guidance(pdf, daily):
    if not daily:
        return

    pdf.add_page()
    pdf.section_title("Daily Guidance & Muhurtha")

    _render_kv_rows(
        pdf,
        [
            ("Day Rating", daily.get("day_rating")),
            ("Day Score", daily.get("day_score")),
            ("Muhurtha Score", daily.get("muhurtha_score")),
            ("Muhurtha Grade", daily.get("muhurtha_grade")),
        ],
    )
    _render_confidence_panel(pdf, daily)
    _render_named_rows(pdf, "Current Dasha", _current_dasha_rows(daily.get("current_dasha")))
    _render_named_rows(
        pdf,
        "Panchanga Snapshot",
        [
            ("Tithi", daily.get("panchanga", {}).get("tithi")),
            ("Vara", daily.get("panchanga", {}).get("vara")),
            ("Yoga", daily.get("panchanga", {}).get("yoga")),
            ("Karana", daily.get("panchanga", {}).get("karana")),
            ("Nakshatra", daily.get("panchanga", {}).get("nakshatra")),
        ],
    )
    _render_named_rows(
        pdf,
        "Pancha Pakshi Snapshot",
        [
            ("Birth Bird", daily.get("pancha_pakshi", {}).get("bird")),
            ("Current Activity", daily.get("pancha_pakshi", {}).get("current_activity")),
            ("Ruling Bird", daily.get("pancha_pakshi", {}).get("ruling_bird")),
        ],
    )
    _render_list(pdf, "Favorable Transits", daily.get("favorable_transits"), limit=5)
    _render_list(pdf, "Challenging Transits", daily.get("challenging_transits"), limit=5)
    transit_notes = [
        _format_transit_effect(code, info)
        for code, info in (daily.get("transit_effects", {}) or {}).items()
    ]
    _render_list(pdf, "Transit Notes", [note for note in transit_notes if note], limit=8)
    _render_list(pdf, "Daily Tips", daily.get("daily_tips"), limit=8)
