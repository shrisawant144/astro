# spouse/predictor.py
"""
Main predictor class that orchestrates all analysis modules.
"""

from . import analysis
from . import report
from ..utils import get_navamsa_sign_and_deg
from ..constants import SHORT_TO_FULL, ZODIAC_SIGNS, SIGN_LORDS


class AdvancedSpousePredictor:
    def __init__(self, chart_data):
        self.data = chart_data
        self.gender = chart_data.get("gender", "Male")
        self.lagna_sign = chart_data.get("lagna_sign", "Aries")
        self.lagna_idx = ZODIAC_SIGNS.index(self.lagna_sign)
        self.d9_lagna_sign = get_navamsa_sign_and_deg(chart_data["lagna_deg"])[0]
        self.d9_lagna_idx = ZODIAC_SIGNS.index(self.d9_lagna_sign)
        self.spouse_karaka = "Ju" if self.gender == "Female" else "Ve"
        self.spouse_term = "husband" if self.gender == "Female" else "wife"
        self.jaimini = chart_data.get("jaimini", {})
        self.atmakaraka = self.jaimini.get("atmakaraka")
        self.karakamsa_lagna = self.jaimini.get("karakamsa_lagna")

        self.confidence_factors = []

        # Precompute derived values
        self.arudha_lagna = analysis._calculate_arudha_lagna(self.data, self.lagna_idx)

        # Build the full prediction dictionary
        self.prediction = self._build_prediction()

    def _build_prediction(self):
        """Call all analysis functions and assemble result."""
        pred = {}

        # Basic info
        pred["gender"] = self.gender
        pred["lagna_sign"] = self.lagna_sign
        pred["spouse_karaka"] = self.spouse_karaka

        # Core analyses
        pred["spouse_profile"] = analysis.consolidate_profile(
            self.data, self.lagna_idx, self.gender
        )
        pred["darakaraka_details"] = analysis.analyze_darakaraka(
            self.data, self.lagna_idx, self.d9_lagna_idx, self.gender
        )
        pred["atmakaraka_analysis"] = analysis.analyze_atmakaraka_for_spouse(self.data)
        pred["karakamsa_analysis"] = analysis.analyze_karakamsa_lagna(self.data)
        pred["personality"] = analysis.consolidate_personality(
            self.data, self.lagna_idx
        )
        pred["appearance"] = analysis.predict_appearance(
            self.data, self.lagna_idx, self.gender
        )
        pred["venus_mars"] = analysis.analyze_venus_mars(self.data, self.lagna_idx)
        pred["marriage_yogas"] = analysis.analyze_marriage_yogas(self.data)
        pred["meeting"] = analysis.predict_meeting(self.data, self.lagna_idx)
        pred["profession"] = analysis.predict_profession(self.data, self.lagna_idx)
        pred["upapada"] = analysis.analyze_upapada(self.data, self.lagna_idx)
        pred["arudha_lagna"] = self.arudha_lagna
        pred["d9_seventh_house"] = analysis.analyze_d9_seventh_house(
            self.data, self.d9_lagna_idx
        )
        pred["aspects_on_7th"] = analysis.analyze_aspects_on_7th(
            self.data, self.lagna_idx
        )
        pred["lord_placements"] = analysis.analyze_house_lord_placements(self.data)
        pred["marriage_type"] = analysis.classify_marriage_type(
            self.data, self.lagna_idx, self.gender
        )
        pred["manglik_dosha"] = analysis.check_manglik_dosha(self.data, self.lagna_idx)
        pred["neecha_bhanga_effects"] = analysis.analyze_neecha_bhanga_effects(
            self.data, self.lagna_idx
        )
        pred["ashtakavarga"] = analysis.analyze_ashtakavarga(self.data)
        pred["navamsa_strength"] = analysis.analyze_navamsa_strength(self.data)
        # Always include high-score marriage periods from main report if available
        dasha_timing = analysis.analyze_marriage_dashas(
            self.data,
            self.lagna_idx,
            self.data["birth_jd"],
            self.data["birth_year"],
        )
        # If high-score periods missing but present in timings, add them
        if not dasha_timing.get("high_score_periods") and self.data.get(
            "timings", {{}}
        ).get("Marriage"):
            timings = self.data["timings"]["Marriage"]
            import re

            for line in timings:
                m = re.search(r"─\s*(\w+)/(\w+)\s*\((\d{4})-(\d{4})\)", line)
                if m:
                    dasha_timing.setdefault("high_score_periods", []).append(
                        {
                            "maha": m.group(1),
                            "antara": m.group(2),
                            "start": int(m.group(3)),
                            "end": int(m.group(4)),
                            "score": 8,
                        }
                    )
        pred["dasha_timing"] = dasha_timing
        pred["current_transits"] = analysis.analyze_current_transits(
            self.data, self.lagna_idx
        )
        pred["double_transit"] = analysis.check_double_transit(
            self.data, self.lagna_idx
        )
        pred["tara_analysis"] = analysis.analyze_nakshatra_tara(
            self.data, self.lagna_idx
        )
        pred["d2_analysis"] = analysis.analyze_d2_financial_integration(
            self.data, self.lagna_idx
        )
        pred["d60_analysis"] = analysis.analyze_d60_karma(self.data, self.lagna_idx)
        pred["nakshatra_insights"] = analysis.analyze_nakshatra_for_spouse(
            self.data, self.lagna_idx
        )
        pred["a7_darapada"] = analysis.calculate_a7_darapada(
            self.data, self.lagna_idx
        )
        pred["graha_yuddha"] = analysis.detect_planetary_war(self.data)
        pred["integrity_summary"] = analysis.summarize_integrity(
            self.data, self.lagna_idx
        )
        # Add functional_karaka for confidence
        pred["functional_karaka"] = analysis.analyze_functional_venus_jupiter(
            self.data, self.lagna_idx
        )

        # Confidence factors collected from analysis functions
        self._collect_confidence(pred)
        pred["confidence_factors"] = self.confidence_factors
        pred["confidence_score"] = analysis.calculate_confidence(
            self.confidence_factors
        )

        return pred

    def _collect_confidence(self, pred):
        """Extract confidence factors from analysis results."""
        # 7th lord strong
        h7 = pred.get("spouse_profile", {})
        h7_lord = h7.get("7th_lord")
        if h7_lord and self.data.get("planets", {}).get(h7_lord, {}).get("dignity") in (
            "Exalted",
            "Own",
        ):
            self.confidence_factors.append(
                f"7th lord {SHORT_TO_FULL[h7_lord]} strong in D1"
            )

        # Functional benefic of Venus/Jupiter
        karaka = pred.get("functional_karaka", {})
        if karaka.get("venus", {}).get("label") in [
            "Strong Benefic",
            "Conditional Benefic",
        ]:
            self.confidence_factors.append(
                "Venus functionally benefic - excellent spouse karaka"
            )
        if karaka.get("jupiter", {}).get("label") in [
            "Strong Benefic",
            "Conditional Benefic",
        ]:
            self.confidence_factors.append(
                "Jupiter functionally benefic - blessed marriage"
            )

        # Darakaraka integrity
        dk = pred.get("darakaraka_details", {})
        if dk.get("integrity", 0) >= 70:
            self.confidence_factors.append(
                f"Darakaraka high integrity ({dk['integrity']}%)"
            )

        # Ashtakavarga strong
        ashtak = pred.get("ashtakavarga", {})
        if ashtak.get("points") and ashtak["points"] >= 28:
            self.confidence_factors.append(
                f"Ashtakavarga 7th house {ashtak['points']} points - excellent support"
            )

        # Venus-Mars conjunction
        vm = pred.get("venus_mars", {})
        if vm.get("status") == "Conjunction":
            self.confidence_factors.append("Venus-Mars conjunction - intense passion")

        # Upapada strong
        ul = pred.get("upapada", {})
        if ul.get("strong"):
            self.confidence_factors.append("Upapada Lagna strong - stable marriage")

        # D9 7th lord strong
        d9_7 = pred.get("d9_seventh_house", {})
        if d9_7.get("strong"):
            self.confidence_factors.append(
                "D9 7th lord strong - blessed marriage karma"
            )

        # Dasha near sandhi
        dashas = pred.get("dasha_timing", {})
        if dashas.get("sandhi_periods"):
            for p in dashas["sandhi_periods"]:
                self.confidence_factors.append(
                    f"{p['maha']}/{p['antara']} near Dasha Sandhi - high probability"
                )

        # Double transit active
        dt = pred.get("double_transit", {})
        if dt.get("active"):
            self.confidence_factors.append("Double Transit active – marriage imminent")

        # Nakshatra Tara beneficial
        tara = pred.get("tara_analysis", {})
        for planet, tdata in tara.items():
            if tdata.get("tara") in (2, 4, 6, 8, 9):
                self.confidence_factors.append(
                    f"{SHORT_TO_FULL[planet]}-Moon Tara {tdata['name']}: Excellent compatibility"
                )

    def predict(self):
        return self.prediction

    def generate_report(self):
        return report.generate_spouse_report(self.prediction)
