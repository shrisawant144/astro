# parser.py

import re
from typing import Dict, List
from .constants import FULL_TO_SHORT, ZODIAC_SIGNS

class AdvancedChartParser:
    """Extracts all possible data from the kundali report."""

    def __init__(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            self.content = f.read()
        self.lines = self.content.split("\n")

    def parse(self) -> Dict:
        """Parse complete chart data with all sections."""
        return {
            "basic": self._parse_basic(),
            "planets_d1": self._parse_planets("Planets in Rasi"),
            "d9": self._parse_planets("Navamsa"),
            "d7": self._parse_planets("Saptamsa"),
            "d10": self._parse_planets("Dasamsa"),
            "ashtakavarga": self._parse_ashtakavarga(),
            "functional_nature": self._parse_functional_classification(),
            "integrity": self._parse_integrity_index(),
            "house_lord_placements": self._parse_house_lord_placements(),
            "aspects": self._parse_aspects_full(),
            "dashas": self._parse_dasha_periods(),
            "gochara": self._parse_gochara(),
            "yogas": self._parse_yogas(),
            "neecha_bhanga": self._parse_neecha_bhanga(),
            "marriage_timing_insights": self._parse_marriage_timing_insights(),
            "nakshatras_d1": self._parse_nakshatras_d1(),
        }

    def _parse_basic(self) -> Dict:
        data = {}
        patterns = [
            (r"Gender\s*:\s*(\w+)", "gender"),
            (r"Lagna\s*:\s*(\w+)\s+([\d.]+)°", "lagna"),
            (r"Moon.*?:\s*(\w+)\s+[–-]\s+(\w+)", "moon"),
            (r"7th Lord\s*:\s*(\w+)", "seventh_lord"),
        ]
        for regex, key in patterns:
            if m := re.search(regex, self.content, re.IGNORECASE):
                if key == "lagna":
                    data["lagna"] = m.group(1)
                    data["lagna_deg"] = float(m.group(2))
                elif key == "moon":
                    data[key] = (m.group(1), m.group(2))
                else:
                    data[key] = m.group(1)
        return data

    def _parse_planets(self, section: str) -> Dict:
        planets = {}
        section_match = re.search(
            rf"{section}.*?\n-+\n(.*?)(?=\n[A-Z]|\n\n[A-Z]|\Z)",
            self.content,
            re.DOTALL | re.IGNORECASE,
        )
        if not section_match:
            return planets
        for line in section_match.group(1).split("\n"):
            line = line.strip()
            if not line:
                continue
            m = re.match(r"(\w+)\s*:\s*([\d.]+)\s*°?\s+(\w+)(?:\s+([\w ]+\w))?", line)
            if m:
                planet = m.group(1)
                planets[planet] = {
                    "deg": float(m.group(2)),
                    "sign": m.group(3),
                    "nak": m.group(4) if m.group(4) else "",
                }
        return planets

    def _parse_ashtakavarga(self) -> Dict:
        ashtak = {}
        pattern = r"7th House \(Marriage\) SAV:\s*(\d+)\s*points"
        match = re.search(pattern, self.content, re.IGNORECASE)
        if match:
            ashtak["7th_house_points"] = int(match.group(1))
        return ashtak

    def _parse_nakshatras_d1(self) -> Dict:
        """Extract nakshatra for each planet in D1."""
        nakshatras = {}
        section = re.search(
            r"Planets in Rasi.*?\n-+\n(.*?)(?=\n[A-Z]|\n\n[A-Z]|\Z)",
            self.content,
            re.DOTALL,
        )
        if not section:
            return nakshatras
        for line in section.group(1).split("\n"):
            m = re.match(
                r"\s*(\w+):\s*[\d.]+°\s+(\w+)\s+(.+?)(?:\s+\(|$)", line.strip()
            )
            if m:
                planet = m.group(1)
                nakshatra_full = m.group(3).strip()
                nakshatras[planet] = nakshatra_full
        return nakshatras

    def _parse_functional_classification(self) -> Dict:
        """Extract functional nature of each planet."""
        func = {}
        section = re.search(
            r"FUNCTIONAL STRENGTH INDEX \(Adjusted[^:]*\):\s*\n\s*-+\s*\n(.*?)(?=\n\s*\n|\n\s*Legend:)",
            self.content,
            re.DOTALL,
        )
        if not section:
            return func
        lines = section.group(1).split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith(("Base", "Marakas", "Mixed", "Yogakaraka")):
                continue
            if "|" not in line:
                continue
            left, label = line.split("|", 1)
            label = label.strip()
            parts = left.split("[")
            if len(parts) < 2:
                continue
            planet_part = parts[0].strip()
            planet_full = planet_part.split()[0] if planet_part.split() else ""
            if not planet_full:
                continue
            planet = FULL_TO_SHORT.get(planet_full, planet_full)
            rest = parts[1].split("]")[-1].strip()
            score_match = re.search(r"(\d+)/100", rest)
            score = int(score_match.group(1)) if score_match else 0
            func[planet] = {"score": score, "label": label}
        return func

    def _parse_integrity_index(self) -> Dict:
        """Extract planetary integrity index."""
        integrity = {}
        section = re.search(
            r"Cross-Chart Planetary Integrity Index.*?\n-+\n(.*?)(?=\n\s*\nHouse Lord Placements|\Z)",
            self.content,
            re.DOTALL,
        )
        if not section:
            return integrity
        lines = section.group(1).split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("(Measures"):
                continue
            if "|" not in line:
                continue
            left, label = line.split("|", 1)
            label = label.strip()
            parts = left.split("[")
            if len(parts) < 2:
                continue
            planet_part = parts[0].strip()
            planet_full = planet_part.split()[0] if planet_part.split() else ""
            if not planet_full:
                continue
            planet = FULL_TO_SHORT.get(planet_full, planet_full)
            rest = parts[1].split("]")[-1].strip()
            score_match = re.search(r"(\d+)/100", rest)
            score = int(score_match.group(1)) if score_match else 0
            integrity[planet] = {"score": score, "label": label}
        return integrity

    def _parse_house_lord_placements(self) -> Dict:
        """Parse house lord placements."""
        placements = {}
        section = re.search(
            r"House Lord Placements:\n-+\n(.*?)(?=\n\n(?:Vimshottari Dasha|YOGAS)|\Z)", self.content, re.DOTALL
        )
        if not section:
            return placements
        for line in section.group(1).split("\n"):
            line = line.strip()
            m = re.match(
                r"H(\d+)\s+\((\w+)\s*\)\s+lord\s+(\w+)\s+[-–—→>]+\s+H(\d+)\s+\((\w+)\s*\):\s*(.+)",
                line,
            )
            if m:
                h = int(m.group(1))
                planet_full = m.group(3)
                planet = FULL_TO_SHORT.get(planet_full, planet_full)
                placements[h] = {
                    "sign": m.group(2),
                    "lord": planet,
                    "dest_house": int(m.group(4)),
                    "dest_sign": m.group(5),
                    "interpretation": m.group(6).strip(),
                }
        return placements

    def _parse_aspects_full(self) -> Dict:
        """Parse full aspects for each house."""
        aspects = {}
        section = re.search(
            r"Aspects \(Drishti\) – Full Analysis:.*?\n(House\s+\d+.*?)(?=\n\n(?:YOGAS WITH STRENGTH|Current Gochara)|\Z)",
            self.content,
            re.DOTALL,
        )
        if not section:
            return aspects
        lines = section.group(1).split("\n")
        current_house = None
        for line in lines:
            hm = re.match(r"House\s+(\d+)\s+\((\w+)\)", line)
            if hm:
                current_house = int(hm.group(1))
                aspects[current_house] = {"sign": hm.group(2), "aspects": []}
                continue
            if current_house and "•" in line:
                parts = line.split("•")[1].strip()
                pm = re.match(
                    r"(\w+)\s+\(([^,]+),\s*(\d+)%,\s*([^,]+),\s*(.+)\)", parts
                )
                if pm:
                    planet_full = pm.group(1)
                    planet = FULL_TO_SHORT.get(planet_full, planet_full)
                    aspect_type = pm.group(2).strip()
                    strength = int(pm.group(3)) if pm.group(3).isdigit() else 0
                    nature = pm.group(4).strip()
                    condition = pm.group(5).strip()
                    aspects[current_house]["aspects"].append(
                        {
                            "planet": planet,
                            "aspect_type": aspect_type,
                            "strength": strength,
                            "nature": nature,
                            "condition": condition,
                        }
                    )
        return aspects

    def _parse_dasha_periods(self) -> List[Dict]:
        """Extract dasha periods relevant to marriage."""
        periods = []
        timing_section = re.search(
            r"Marriage Timing Insights.*?\nMarriage:\n(.*?)(?=\n\n(?:Career Rise|Children|Current Gochara|🔥))",
            self.content, re.DOTALL
        )
        if timing_section:
            for line in timing_section.group(1).split("\n"):
                m = re.match(
                    r".*?(\w+)/(\w+)\s+\((\d+)-(\d+)\).*?([★]+).*?\[(\d+)/10\].*?(\[.*?\])",
                    line,
                )
                if m:
                    periods.append(
                        {
                            "maha": m.group(1),
                            "antara": m.group(2),
                            "start": int(m.group(3)),
                            "end": int(m.group(4)),
                            "stars": len(m.group(5)),
                            "score": int(m.group(6)),
                            "status": m.group(7).strip("[]"),
                        }
                    )
        return periods

    def _parse_gochara(self) -> Dict:
        """Parse current transit positions from Moon."""
        gochara = {}
        section = re.search(
            r"Current Gochara \(from Moon\):\n-+\n(.*?)(?=\n\n|\Z)",
            self.content,
            re.DOTALL,
        )
        if not section:
            return gochara
        for line in section.group(1).split("\n"):
            m = re.match(r"\s*(\w+):\s+(\w+)\s+\(house\s+(\d+)\)\s+[–-]\s+(.+)", line)
            if m:
                planet = m.group(1)
                sign = m.group(2)
                house = int(m.group(3))
                effect = m.group(4).strip()
                gochara[planet] = {"sign": sign, "house": house, "effect": effect}
        return gochara

    def _parse_yogas(self) -> List[Dict]:
        """Extract yogas with strength."""
        yogas = []
        section = re.search(
            r"YOGAS WITH STRENGTH.*?\n-+\n(.*?)(?=\n\n|\Z)", self.content, re.DOTALL
        )
        if not section:
            return yogas
        for line in section.group(1).split("\n"):
            m = re.match(r"•\s*(.+?)\s+\(Strength\s+(\d+)/10\)\s*→\s*(.+)", line)
            if m:
                yogas.append(
                    {
                        "name": m.group(1).strip(),
                        "strength": int(m.group(2)),
                        "effect": m.group(3).strip(),
                    }
                )
        return yogas

    def _parse_neecha_bhanga(self) -> List[str]:
        """Extract planets with Neecha Bhanga."""
        nb_planets = []
        section = re.search(r"Neecha Bhanga Planets \((.*?)\):", self.content)
        if section:
            planets_str = section.group(1)
            nb_planets = [p.strip() for p in planets_str.split(",")]
        return nb_planets

    def _parse_marriage_timing_insights(self) -> Dict:
        """Extract the score and next favorable periods."""
        insights = {}
        section = re.search(
            r"Marriage Timing Insights.*?\n(.*?)(?=\n\n)", self.content, re.DOTALL
        )
        if section:
            text = section.group(1)
            score_m = re.search(r"Score legend:\s*(.+)", text)
            if score_m:
                insights["score_legend"] = score_m.group(1).strip()
            next_m = re.search(r"Next favourable periods:\s*(.+)", text)
            if next_m:
                insights["next_periods"] = next_m.group(1).strip()
        return insights
