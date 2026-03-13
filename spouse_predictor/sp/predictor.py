# predictor.py

from datetime import datetime
from typing import Dict, List
from .constants import (
    ZODIAC_SIGNS, SIGN_LORDS, SHORT_TO_FULL, FULL_TO_SHORT,
    SIGN_APPEARANCE, PLANET_SPOUSE_TRAITS, MEETING_CIRCUMSTANCES,
    PROFESSION_BY_HOUSE
)
from .utils import (
    get_navamsa_sign, get_dignity, safe_sign_index, has_aspect,
    get_nakshatra_lord, get_nakshatra_deity, get_nakshatra_meaning
)

class AdvancedSpousePredictor:
    """
    Ultra-detailed spouse prediction using 25+ Vedic techniques.
    """

    def __init__(self, chart_data: Dict):
        self.data = chart_data
        self.gender = chart_data["basic"].get("gender", "Male")
        self.spouse_karaka = "Ju" if self.gender == "Female" else "Ve"
        self.spouse_term = "husband" if self.gender == "Female" else "wife"

        # D1 Lagna
        self.lagna_sign = chart_data["basic"].get("lagna", "Aries")
        self.lagna_idx = safe_sign_index(self.lagna_sign)
        self.lagna_deg = chart_data["basic"].get("lagna_deg", 0.0)

        # D9 Lagna
        self.d9_lagna_sign = get_navamsa_sign(self.lagna_deg)
        self.d9_lagna_idx = safe_sign_index(self.d9_lagna_sign)

        # Confidence tracking
        self.confidence_factors = []
        self.all_indicators = []  # store all findings for cross-verification

    # ------------------------------------------------------------------------
    # Core House Analysis (enhanced)
    # ------------------------------------------------------------------------
    def _analyze_7th_house_multilevel(self) -> Dict:
        h7_idx = (self.lagna_idx + 6) % 12
        h7_sign = ZODIAC_SIGNS[h7_idx]
        h7_lord = SIGN_LORDS[h7_sign]

        d1 = self.data["planets_d1"]
        h7_lord_data = d1.get(h7_lord, {})
        h7_lord_sign = h7_lord_data.get("sign", "")
        h7_lord_dignity = get_dignity(h7_lord, h7_lord_sign)
        h7_lord_house = self._get_house(h7_lord)

        # Functional nature of 7th lord
        func_nature = self.data.get("functional_nature", {}).get(h7_lord, {})
        func_label = func_nature.get("label", "Unknown")

        # Integrity of 7th lord
        integrity = self.data.get("integrity", {}).get(h7_lord, {})
        integrity_score = integrity.get("score", 50)

        analysis = {
            "d1": {
                "sign": h7_sign,
                "lord": h7_lord,
                "lord_sign": h7_lord_sign,
                "lord_dignity": h7_lord_dignity,
                "lord_house": h7_lord_house,
                "functional_nature": func_label,
                "integrity": integrity_score,
            }
        }

        if h7_lord_dignity in ["Exalted", "Own"]:
            self.confidence_factors.append(
                f"7th lord {SHORT_TO_FULL[h7_lord]} strong in D1"
            )
        if func_label in ["Strong Benefic", "Conditional Benefic"]:
            self.confidence_factors.append(f"7th lord functionally benefic")
        if integrity_score >= 70:
            self.confidence_factors.append(
                f"7th lord high integrity ({integrity_score}%)"
            )

        return analysis

    # ------------------------------------------------------------------------
    # New: Functional Nature Integration
    # ------------------------------------------------------------------------
    def _analyze_functional_venus_jupiter(self) -> Dict:
        """Analyze functional status of Venus and Jupiter, including mutual
        aspect/conjunction (BPHS Ch. 25: mutual aspect indicates harmonious spouse)."""
        func = self.data.get("functional_nature", {})
        venus = func.get("Ve", {})
        jupiter = func.get("Ju", {})

        result = {
            "venus": {
                "label": venus.get("label", "Unknown"),
                "score": venus.get("score", 0),
            },
            "jupiter": {
                "label": jupiter.get("label", "Unknown"),
                "score": jupiter.get("score", 0),
            },
        }

        if venus.get("label") in ["Strong Benefic", "Conditional Benefic"]:
            self.confidence_factors.append(
                f"Venus functionally benefic - excellent spouse karaka"
            )
        if jupiter.get("label") in ["Strong Benefic", "Conditional Benefic"]:
            self.confidence_factors.append(
                f"Jupiter functionally benefic - blessed marriage"
            )

        # Venus-Jupiter mutual aspect/conjunction check (BPHS Ch. 25)
        d1 = self.data["planets_d1"]
        ve_data = d1.get("Ve", {})
        ju_data = d1.get("Ju", {})
        ve_deg = ve_data.get("deg", 0)
        ju_deg = ju_data.get("deg", 0)
        ve_sign = ve_data.get("sign", "")
        ju_sign = ju_data.get("sign", "")
        ve_house = self._get_house("Ve")
        ju_house = self._get_house("Ju")

        vj_relationship = "No direct connection"
        if ve_sign and ju_sign:
            if ve_sign == ju_sign:
                # Conjunction – check orb (<10° for benefics)
                deg_diff = abs(ve_deg - ju_deg)
                if deg_diff < 10:
                    vj_relationship = f"Conjunction within {deg_diff:.1f}° – harmonious union, spouse is wise and beautiful"
                    self.confidence_factors.append("Venus-Jupiter conjunction – strong marriage indicator")
                else:
                    vj_relationship = f"Same sign but wide orb ({deg_diff:.1f}°) – mild positive"
            elif has_aspect(ve_house, ju_house, "Ve") or has_aspect(ju_house, ve_house, "Ju"):
                vj_relationship = "Mutual aspect – harmonious spouse, balanced marriage"
                self.confidence_factors.append("Venus-Jupiter mutual aspect – positive marriage karma")

        result["venus_jupiter_relationship"] = vj_relationship
        return result

    # ------------------------------------------------------------------------
    # New: Aspects to 7th House & 7th Lord
    # ------------------------------------------------------------------------
    def _analyze_aspects_on_7th(self) -> Dict:
        """Collect all aspects on 7th house and 7th lord."""
        aspects_data = self.data.get("aspects", {})
        h7_idx = (self.lagna_idx + 6) % 12
        h7_house_num = h7_idx + 1  # 1-based

        # Aspects to 7th house
        h7_aspects = aspects_data.get(h7_house_num, {}).get("aspects", [])

        # Also find aspects to 7th lord's position
        h7_lord = SIGN_LORDS[ZODIAC_SIGNS[h7_idx]]
        h7_lord_house = self._get_house(h7_lord)
        lord_aspects = aspects_data.get(h7_lord_house, {}).get("aspects", [])

        # Combine and annotate with functional nature
        combined = []
        for asp in h7_aspects:
            combined.append(
                {
                    "target": "7th house",
                    "planet": asp["planet"],
                    "type": asp["aspect_type"],
                    "strength": asp["strength"],
                    "nature": asp["nature"],
                    "condition": asp["condition"],
                }
            )
        for asp in lord_aspects:
            combined.append(
                {
                    "target": "7th lord",
                    "planet": asp["planet"],
                    "type": asp["aspect_type"],
                    "strength": asp["strength"],
                    "nature": asp["nature"],
                    "condition": asp["condition"],
                }
            )

        # Add confidence for benefic aspects
        benefic_planets = ["Ju", "Ve", "Mo", "Me"]  # generally benefic
        for asp in combined:
            if asp["planet"] in benefic_planets and asp["strength"] >= 75:
                self.confidence_factors.append(
                    f'Strong {asp["planet"]} aspect on {asp["target"]}'
                )

        return {"aspects": combined}

    # ------------------------------------------------------------------------
    # New: House Lord Placement Interpretations
    # ------------------------------------------------------------------------
    def _analyze_house_lord_placements(self) -> Dict:
        """Extract interpretations for spouse-related houses."""
        placements = self.data.get("house_lord_placements", {})

        # 7th lord placement (house 7 is always 7, regardless of lagna)
        seventh_lord_info = placements.get(7, {})
        # 2nd lord (family wealth)
        second_lord_info = placements.get(2, {})
        # 5th lord (romance)
        fifth_lord_info = placements.get(5, {})

        return {
            "seventh_house": seventh_lord_info,
            "second_house": second_lord_info,
            "fifth_house": fifth_lord_info,
        }

    # ------------------------------------------------------------------------
    # New: Dasha Timing Analysis
    # ------------------------------------------------------------------------
    def _analyze_marriage_dashas(self) -> Dict:
        """Identify high-probability marriage periods from dashas."""
        periods = self.data.get("dashas", [])
        high_score_periods = [p for p in periods if p.get("score", 0) >= 8]
        moderate_score_periods = [p for p in periods if 4 <= p.get("score", 0) < 8]
        
        # If no high score periods, use moderate score periods instead
        if not high_score_periods and moderate_score_periods:
            display_periods = moderate_score_periods
        else:
            display_periods = high_score_periods
        
        upcoming = [p for p in display_periods if p.get("status") == "FUTURE"]

        return {
            "high_score_periods": display_periods,
            "upcoming": upcoming,
            "count": len(display_periods),
        }

    # ------------------------------------------------------------------------
    # New: Current Transit Effects
    # ------------------------------------------------------------------------
    def _analyze_current_transits(self) -> Dict:
        """See how current transits affect marriage house."""
        gochara = self.data.get("gochara", {})
        h7_idx = (self.lagna_idx + 6) % 12
        h7_house_num = h7_idx + 1

        # Find planets transiting 7th house or aspecting it
        transiting_7th = []
        for planet, data in gochara.items():
            if data.get("house") == h7_house_num:
                transiting_7th.append(planet)

        # Also check if any planet aspects 7th from its transit position
        # (simplified: only full aspect considered)
        aspecting_7th = []
        for planet, data in gochara.items():
            planet_house = data.get("house", 0)
            if has_aspect(planet_house, h7_house_num, planet):
                aspecting_7th.append(planet)

        return {
            "transiting_7th": transiting_7th,
            "aspecting_7th": aspecting_7th,
            "gochara": gochara,
        }

    # ------------------------------------------------------------------------
    # New: Yogas for Marriage
    # ------------------------------------------------------------------------
    def _analyze_marriage_yogas_from_list(self) -> List[Dict]:
        """Extract yogas specifically related to marriage from the list."""
        all_yogas = self.data.get("yogas", [])
        marriage_keywords = [
            "marriage",
            "spouse",
            "wife",
            "husband",
            "venus",
            "7th",
            "darakaraka",
        ]
        relevant = []
        for yoga in all_yogas:
            name = yoga["name"].lower()
            if any(k in name for k in marriage_keywords):
                relevant.append(yoga)
                self.confidence_factors.append(
                    f"Marriage yoga: {yoga['name']} (strength {yoga['strength']}/10)"
                )
        return relevant

    # ------------------------------------------------------------------------
    # New: Neecha Bhanga Effects
    # ------------------------------------------------------------------------
    def _analyze_neecha_bhanga_effects(self) -> Dict:
        """See if any spouse-related planets have Neecha Bhanga."""
        nb_planets = self.data.get("neecha_bhanga", [])
        h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(self.lagna_idx + 6) % 12]]
        dk = self._find_darakaraka_planet()

        effects = {}
        if h7_lord in nb_planets:
            effects["seventh_lord"] = (
                "Neecha Bhanga - debilitation cancelled, becomes powerful after maturity"
            )
            self.confidence_factors.append(
                "7th lord has Neecha Bhanga - delayed but strong marriage"
            )
        if dk in nb_planets:
            effects["darakaraka"] = (
                "Neecha Bhanga - spouse-related planet gains strength over time"
            )
        if "Ve" in nb_planets:
            effects["venus"] = (
                "Neecha Bhanga - Venus strengthens with age, spouse quality improves"
            )
        return effects

    # ------------------------------------------------------------------------
    # Enhanced Darakaraka Analysis
    # ------------------------------------------------------------------------
    def _find_darakaraka_planet(self) -> str:
        d1 = self.data["planets_d1"]
        min_deg = 30
        dk = "Ve"
        for p, data in d1.items():
            if p in ["Ra", "Ke"]:
                continue
            deg = float(data["deg"]) % 30
            if deg < min_deg:
                min_deg = deg
                dk = p
        return dk

    def _analyze_darakaraka_advanced(self) -> Dict:
        dk_planet = self._find_darakaraka_planet()
        d1 = self.data["planets_d1"]
        d9 = self.data["d9"]
        d10 = self.data.get("d10", {})
        d7 = self.data.get("d7", {})

        dk_sign_d1 = d1[dk_planet]["sign"]
        dk_dignity_d1 = get_dignity(dk_planet, dk_sign_d1)
        min_deg = float(d1[dk_planet]["deg"]) % 30

        dk_sign_d9 = d9.get(dk_planet, {}).get("sign", "")
        dk_dignity_d9 = get_dignity(dk_planet, dk_sign_d9)

        # DK house in D9
        dk_d9_house = self._get_house_d9(dk_planet) if dk_planet in d9 else 0
        d9_house_meaning = {
            1: "Spouse strongly influences your identity",
            2: "Marriage brings wealth, family values central",
            3: "Communicative spouse, sibling-like bond",
            4: "Domestic harmony, spouse connected to home",
            5: "Creative partnership, children bring joy",
            6: "Service-oriented spouse, health matters",
            7: "Perfect partnership, strong marriage",
            8: "Transformative marriage, deep intimacy",
            9: "Philosophical spouse, dharmic marriage",
            10: "Career-oriented spouse, public recognition",
            11: "Social spouse, gains through marriage",
            12: "Spiritual union, foreign connections",
        }.get(dk_d9_house, "Unique placement")

        # Integrity and functional nature
        integrity = self.data.get("integrity", {}).get(dk_planet, {})
        func = self.data.get("functional_nature", {}).get(dk_planet, {})

        if dk_dignity_d1 in ["Exalted", "Own"]:
            self.confidence_factors.append(
                f"Darakaraka {SHORT_TO_FULL[dk_planet]} strong in D1"
            )
        if integrity.get("score", 0) >= 70:
            self.confidence_factors.append(
                f'Darakaraka high integrity ({integrity["score"]}%)'
            )

        return {
            "planet": dk_planet,
            "name": SHORT_TO_FULL[dk_planet],
            "degree": min_deg,
            "sign_d1": dk_sign_d1,
            "dignity_d1": dk_dignity_d1,
            "sign_d9": dk_sign_d9,
            "dignity_d9": dk_dignity_d9,
            "d9_house": dk_d9_house,
            "d9_house_meaning": d9_house_meaning,
            "traits": PLANET_SPOUSE_TRAITS.get(dk_planet, {}),
            "integrity": integrity.get("score", 50),
            "functional": func.get("label", "Unknown"),
        }

    # ------------------------------------------------------------------------
    # Enhanced D9 7th House Analysis with Aspects
    # ------------------------------------------------------------------------
    def _analyze_d9_seventh_house_advanced(self) -> Dict:
        d9 = self.data["d9"]
        d9_h7_idx = (self.d9_lagna_idx + 6) % 12
        d9_h7_sign = ZODIAC_SIGNS[d9_h7_idx]
        d9_h7_lord = SIGN_LORDS[d9_h7_sign]

        # Lord position
        d9_h7_lord_sign = d9.get(d9_h7_lord, {}).get("sign", "")
        d9_h7_lord_dignity = (
            get_dignity(d9_h7_lord, d9_h7_lord_sign) if d9_h7_lord_sign else "Unknown"
        )

        # Planets in D9 7th
        planets_in = [
            p for p, data in d9.items() if safe_sign_index(data["sign"]) == d9_h7_idx
        ]

        # Aspects on D9 7th house (using D9 chart)
        # Since we don't have D9 aspects in report, we'll infer from D9 planet positions
        # but for simplicity, we'll note that we lack that data.

        # Check if any planet aspects D9 7th lord in D9
        lord_house = self._get_house_d9(d9_h7_lord) if d9_h7_lord in d9 else 0

        # Strength
        strong = d9_h7_lord_dignity in ["Exalted", "Own"]

        # Also check D9 7th lord's functional nature (if available in D1? Not directly)
        # We'll use D1 functional as proxy
        func = self.data.get("functional_nature", {}).get(d9_h7_lord, {})
        func_label = func.get("label", "Unknown")

        interpretation = []
        if d9_h7_lord_dignity == "Exalted":
            interpretation.append("Excellent marriage karma at soul level")
        elif d9_h7_lord_dignity == "Own":
            interpretation.append("Strong marriage foundation")
        elif d9_h7_lord_dignity == "Debilitated":
            interpretation.append("Challenges in marriage at deeper level")
        if planets_in:
            interpretation.append(
                f'Planets in D9 7th: {", ".join([SHORT_TO_FULL[p] for p in planets_in])}'
            )
        if func_label in ["Strong Benefic", "Conditional Benefic"]:
            interpretation.append("D9 7th lord functionally benefic - blessed")

        return {
            "d9_7th_sign": d9_h7_sign,
            "d9_7th_lord": d9_h7_lord,
            "d9_7th_lord_sign": d9_h7_lord_sign,
            "d9_7th_lord_dignity": d9_h7_lord_dignity,
            "planets_in_d9_7th": planets_in,
            "strong": strong,
            "functional_lord": func_label,
            "interpretation": (
                " | ".join(interpretation) if interpretation else "Average D9 7th house"
            ),
        }

    # ------------------------------------------------------------------------
    # Helper to get house number in D1
    # ------------------------------------------------------------------------
    def _get_house(self, planet: str) -> int:
        d1 = self.data["planets_d1"]
        if planet not in d1:
            return 0
        planet_sign = d1[planet]["sign"]
        planet_idx = safe_sign_index(planet_sign)
        return ((planet_idx - self.lagna_idx) % 12) + 1

    def _get_house_d9(self, planet: str) -> int:
        d9 = self.data["d9"]
        if planet not in d9:
            return 0
        planet_sign = d9[planet]["sign"]
        planet_idx = safe_sign_index(planet_sign)
        return ((planet_idx - self.d9_lagna_idx) % 12) + 1

    # ------------------------------------------------------------------------
    # Main prediction orchestration
    # ------------------------------------------------------------------------
    def predict(self) -> Dict:
        """Run all analysis layers and consolidate."""
        # Layer 1-2: Basic 7th + Karaka
        h7 = self._analyze_7th_house_multilevel()
        karaka = self._analyze_functional_venus_jupiter()  # replaces old karaka

        # Layer 3: Darakaraka advanced
        dk = self._analyze_darakaraka_advanced()

        # Layer 4: Upapada (using base method but enhanced with parsed data)
        ul = self._analyze_upapada_enhanced()

        # Layer 5: A7 Darapada (base)
        a7 = calculate_a7_darapada(self.lagna_idx, self.data["planets_d1"])

        # Layer 6: Navamsa strength (base)
        navamsa = self._analyze_navamsa_strength()

        # Layer 7: D9 7th advanced
        d9_7th = self._analyze_d9_seventh_house_advanced()

        # Layer 8: Venus-Mars (base)
        venus_mars = self._analyze_venus_mars()

        # Layer 9: Ashtakavarga (base)
        ashtak = self._analyze_ashtakavarga()

        # Layer 10: Manglik (base but enhanced with functional)
        manglik = self._check_manglik_dosha()

        # Layer 11: Love vs Arranged (base)
        marriage_type = self._classify_marriage_type()

        # Layer 12: Appearance (base)
        appearance = self._predict_appearance_enhanced()

        # Layer 13: Meeting (base)
        meeting = self._predict_meeting()

        # Layer 14: Profession (base)
        profession = self._predict_profession()

        # NEW LAYERS:
        # Layer 15: Aspects on 7th
        aspects_7th = self._analyze_aspects_on_7th()

        # Layer 16: House lord placements
        lord_placements = self._analyze_house_lord_placements()

        # Layer 17: Dasha timing
        dashas = self._analyze_marriage_dashas()

        # Layer 18: Current transits
        transits = self._analyze_current_transits()

        # Layer 19: Yogas from list
        marriage_yogas = self._analyze_marriage_yogas_from_list()

        # Layer 20: Neecha Bhanga effects
        neecha = self._analyze_neecha_bhanga_effects()

        # NEW LAYERS (Nakshatra & Graha Yuddha)
        nakshatra = self._analyze_nakshatra_for_spouse()
        graha_yuddha = self._detect_planetary_war()

        # Layer 21: Integrity of key planets
        integrity_summary = self._summarize_integrity()

        # Compile all
        return {
            "spouse_profile": self._consolidate_profile(h7, karaka, dk),
            "appearance": appearance,
            "personality": self._consolidate_personality(h7, dk),
            "profession": profession,
            "meeting": meeting,
            "marriage_type": marriage_type,
            "upapada": ul,
            "a7_darapada": a7,
            "venus_mars": venus_mars,
            "ashtakavarga": ashtak,
            "navamsa_strength": navamsa,
            "d9_seventh_house": d9_7th,
            "manglik_dosha": manglik,
            "darakaraka_details": dk,
            "functional_karaka": karaka,
            "aspects_on_7th": aspects_7th,
            "lord_placements": lord_placements,
            "dasha_timing": dashas,
            "current_transits": transits,
            "marriage_yogas": marriage_yogas,
            "neecha_bhanga_effects": neecha,
            "integrity_summary": integrity_summary,
            "nakshatra_insights": nakshatra,
            "graha_yuddha": graha_yuddha,
            "confidence_factors": self.confidence_factors,
            "confidence_score": self._calculate_confidence(),
        }

    def _summarize_integrity(self) -> Dict:
        """Summarize integrity of key spouse planets."""
        integrity = self.data.get("integrity", {}) or {}
        key_planets = ["Ve", "Ju", self._find_darakaraka_planet()]
        h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(self.lagna_idx + 6) % 12]]
        if h7_lord not in key_planets:
            key_planets.append(h7_lord)

        summary = {}
        for p in key_planets:
            if p in integrity:
                summary[p] = integrity[p]
        return summary

    # ------------------------------------------------------------------------
    # New: Nakshatra Analysis for Spouse
    # ------------------------------------------------------------------------
    def _analyze_nakshatra_for_spouse(self) -> Dict:
        """Provide nakshatra-level description for spouse-related planets."""
        nakshatras = self.data.get("nakshatras_d1", {})
        if not nakshatras:
            return {}

        h7_lord = SIGN_LORDS[ZODIAC_SIGNS[(self.lagna_idx + 6) % 12]]
        dk_planet = self._find_darakaraka_planet()
        key_planets = ["Ve", h7_lord, dk_planet]
        # Remove duplicates while preserving order
        seen = set()
        key_planets = [p for p in key_planets if not (p in seen or seen.add(p))]

        insights = {}
        for p in key_planets:
            if p not in nakshatras:
                continue
            nak = nakshatras[p]
            lord = get_nakshatra_lord(nak)
            deity = get_nakshatra_deity(nak)
            meaning = get_nakshatra_meaning(nak, p)
            insights[p] = {
                "nakshatra": nak,
                "lord": SHORT_TO_FULL[lord] if lord else "Unknown",
                "deity": deity,
                "meaning": meaning,
            }

        if insights:
            self.confidence_factors.append("Nakshatra-level spouse refinement applied")

        return insights

    # ------------------------------------------------------------------------
    # New: Graha Yuddha (Planetary War) Detection
    # ------------------------------------------------------------------------
    def _detect_planetary_war(self) -> List[Dict]:
        """Find planets within 1° in D1 – they are in war, modifying results."""
        d1 = self.data["planets_d1"]
        planets = list(d1.keys())
        wars = []
        for i in range(len(planets)):
            for j in range(i + 1, len(planets)):
                p1 = planets[i]
                p2 = planets[j]
                if p1 in ["Ra", "Ke"] or p2 in ["Ra", "Ke"]:
                    continue  # nodes not considered in war
                deg1 = d1[p1]["deg"]
                deg2 = d1[p2]["deg"]
                if abs(deg1 - deg2) <= 1.0:  # within 1 degree
                    # Determine winner: planet with lower degree (more combustive?)
                    # Classical rule: the one with lower longitude wins.
                    winner = p1 if deg1 < deg2 else p2
                    loser = p2 if winner == p1 else p1
                    wars.append(
                        {
                            "planets": [p1, p2],
                            "winner": winner,
                            "loser": loser,
                            "description": f"{SHORT_TO_FULL[winner]} wins over {SHORT_TO_FULL[loser]}, {SHORT_TO_FULL[loser]}'s results are weakened.",
                        }
                    )
        return wars

    # ------------------------------------------------------------------------
    # Base methods reused with minor enhancements
    # (copied from original but can be left as is, or enhanced with new data)
    # ------------------------------------------------------------------------
    def _analyze_navamsa_strength(self) -> Dict:
        d1 = self.data["planets_d1"]
        d9 = self.data["d9"]
        vargottama = []
        for p in d1:
            if p in d9 and d1[p]["sign"] == d9[p]["sign"]:
                vargottama.append(p)
        if vargottama:
            self.confidence_factors.append(
                f'Vargottama: {", ".join([SHORT_TO_FULL[p] for p in vargottama])}'
            )
        return {"vargottama": vargottama, "count": len(vargottama)}

    def _analyze_venus_mars(self) -> Dict:
        d1 = self.data["planets_d1"]
        if "Ve" not in d1 or "Ma" not in d1:
            return {"status": "No connection", "effect": "Neutral passion level"}
        ve_house = self._get_house("Ve")
        ma_house = self._get_house("Ma")
        if ve_house == ma_house:
            self.confidence_factors.append("Venus-Mars conjunction - intense passion")
            return {
                "status": "Conjunction",
                "effect": "Intense passion, strong attraction, high energy in intimacy. Possible conflicts but strong chemistry.",
            }
        if has_aspect(ve_house, ma_house, "Ve") or has_aspect(ma_house, ve_house, "Ma"):
            return {
                "status": "Mutual Aspect",
                "effect": "Mutual attraction with some tension. Balanced passion, manageable conflicts.",
            }
        return {
            "status": "No direct connection",
            "effect": "Standard or mild passion levels. Romance without excessive intensity.",
        }

    def _analyze_ashtakavarga(self) -> Dict:
        ashtak_data = self.data.get("ashtakavarga", {})
        h7_points = ashtak_data.get("7th_house_points", None)
        if h7_points is None:
            return {
                "points": "Data not available",
                "guidance": "Add SAV parsing to chart4.py output",
                "interpretation": "Sarvashtakavarga (SAV) scoring: ≥28 = Excellent (Uttara Kalamrita), 25-27 = Good, 22-24 = Average, <22 = Weak (delays/obstacles)",
            }
        if h7_points >= 28:
            interp = "Excellent - Very strong marriage yoga, smooth path (classical threshold: 28+ per Uttara Kalamrita)"
            self.confidence_factors.append(
                f"Ashtakavarga 7th house {h7_points} points - excellent support"
            )
            strength = "Very Strong"
        elif h7_points >= 25:
            interp = "Good - Positive support for marriage"
            self.confidence_factors.append(
                f"Ashtakavarga 7th house {h7_points} points - good"
            )
            strength = "Strong"
        elif h7_points >= 22:
            interp = "Average - Normal marriage karma"
            strength = "Average"
        else:
            interp = "Weak - Possible delays, obstacles, or need for remedies"
            strength = "Weak"
        return {"points": h7_points, "strength": strength, "interpretation": interp}

    def _analyze_upapada_enhanced(self) -> Dict:
        # Reusing original method, but we could enhance with parsed house lord placements
        h12_idx = (self.lagna_idx + 11) % 12
        h12_sign = ZODIAC_SIGNS[h12_idx]
        h12_lord = SIGN_LORDS[h12_sign]
        d1 = self.data["planets_d1"]
        h12_lord_sign = d1.get(h12_lord, {}).get("sign", "")
        if not h12_lord_sign:
            return {
                "sign": "",
                "strong": False,
                "2nd_meaning": "Unknown",
                "8th_meaning": "Unknown",
            }
        h12_lord_idx = safe_sign_index(h12_lord_sign)
        distance = (h12_lord_idx - h12_idx) % 12
        ul_idx = (h12_lord_idx + distance) % 12
        if ul_idx == h12_idx:
            ul_idx = (h12_idx + 9) % 12
        elif ul_idx == (h12_idx + 6) % 12:
            ul_idx = ((h12_idx + 6) + 9) % 12
        ul_sign = ZODIAC_SIGNS[ul_idx]
        ul_lord = SIGN_LORDS[ul_sign]
        ul_lord_sign = d1.get(ul_lord, {}).get("sign", "")
        ul_dignity = get_dignity(ul_lord, ul_lord_sign)
        strong = ul_dignity in ["Exalted", "Own", "Friendly"]
        if strong:
            self.confidence_factors.append("Upapada Lagna strong - stable marriage")
        ul_2nd_idx = (ul_idx + 1) % 12
        ul_2nd_sign = ZODIAC_SIGNS[ul_2nd_idx]
        planets_in_2nd = [
            p for p, data in d1.items() if safe_sign_index(data["sign"]) == ul_2nd_idx
        ]
        has_malefic_2nd = any(p in ["Ma", "Sa", "Ra", "Ke"] for p in planets_in_2nd)
        meaning_2nd = (
            "Challenges in family harmony, possible financial strain"
            if has_malefic_2nd
            else "Supportive family after marriage, good sustenance, happiness"
        )
        ul_8th_idx = (ul_idx + 7) % 12
        ul_8th_sign = ZODIAC_SIGNS[ul_8th_idx]
        planets_in_8th = [
            p for p, data in d1.items() if safe_sign_index(data["sign"]) == ul_8th_idx
        ]
        has_malefic_8th = any(p in ["Ma", "Sa", "Ra", "Ke"] for p in planets_in_8th)
        meaning_8th = (
            "Possible transformations, in-law issues, or obstacles"
            if has_malefic_8th
            else "Stable long-term marriage, good in-laws relations"
        )
        return {
            "sign": ul_sign,
            "lord": ul_lord,
            "dignity": ul_dignity,
            "strong": strong,
            "2nd_sign": ul_2nd_sign,
            "2nd_meaning": meaning_2nd,
            "8th_sign": ul_8th_sign,
            "8th_meaning": meaning_8th,
        }

    def _check_manglik_dosha(self) -> Dict:
        d1 = self.data["planets_d1"]
        if "Ma" not in d1:
            return {"present": False, "reason": "Mars position unknown"}
        mars_house = self._get_house("Ma")
        mars_sign = d1["Ma"]["sign"]
        mars_dignity = get_dignity("Ma", mars_sign)
        is_manglik = mars_house in [1, 2, 4, 7, 8, 12]
        if not is_manglik:
            return {
                "present": False,
                "mars_house": mars_house,
                "reason": "Mars not in Manglik houses (1,2,4,7,8,12)",
            }
        cancellations = []
        if mars_dignity in ["Exalted", "Own"]:
            cancellations.append("Mars in own/exalted sign (strength cancels dosha)")
        ju_house = self._get_house("Ju")
        if has_aspect(ju_house, mars_house, "Ju"):
            cancellations.append("Jupiter aspects Mars (benefic protection)")
        if mars_house == 1 and mars_sign in ["Aries", "Scorpio"]:
            cancellations.append("Mars in 1st in own sign (reduces intensity)")
        if mars_house == 4 and mars_sign == "Capricorn":
            cancellations.append("Mars exalted in 4th (cancellation)")
        if mars_house == 7 and mars_sign in ["Capricorn", "Aries", "Scorpio"]:
            cancellations.append("Mars in 7th in strong position")
        if mars_house == 8 and mars_sign == "Capricorn":
            cancellations.append("Mars exalted in 8th (cancellation)")
        if "Ve" in d1:
            ve_dignity = get_dignity("Ve", d1["Ve"]["sign"])
            if ve_dignity in ["Exalted", "Own"]:
                cancellations.append("Venus very strong (mitigates Mars dosha)")
        severity = "Cancelled" if cancellations else "Present"
        if not cancellations:
            severity = (
                "Mild"
                if mars_house in [2, 12]
                else "Moderate" if mars_house in [1, 4] else "Strong"
            )
        result = {
            "present": True,
            "severity": severity,
            "mars_house": mars_house,
            "mars_sign": mars_sign,
            "mars_dignity": mars_dignity,
            "cancellations": cancellations,
            "recommendation": self._get_manglik_recommendation(severity, cancellations),
        }
        return result

    def _get_manglik_recommendation(
        self, severity: str, cancellations: List[str]
    ) -> str:
        if cancellations:
            return "Dosha is cancelled - no major concern. Normal compatibility check sufficient."
        if severity == "Mild":
            return "Mild dosha - prefer partner with similar Mars placement or perform simple remedies."
        if severity == "Moderate":
            return "Moderate dosha - partner should also be Manglik or have strong Venus/Jupiter. Consider remedies."
        return "Strong dosha - Important: Partner should be Manglik or have strong cancellations. Consult astrologer for remedies."

    def _classify_marriage_type(self) -> Dict:
        d1 = self.data["planets_d1"]
        love_score = 0
        arranged_score = 0
        indicators = []
        ve_house = self._get_house("Ve")
        mo_house = self._get_house("Mo")
        if ve_house == mo_house:
            love_score += 3
            indicators.append("Venus-Moon conjunction (romantic nature)")
        h5_sign = ZODIAC_SIGNS[(self.lagna_idx + 4) % 12]
        h5_lord = SIGN_LORDS[h5_sign]
        h7_sign = ZODIAC_SIGNS[(self.lagna_idx + 6) % 12]
        h7_lord = SIGN_LORDS[h7_sign]
        if self._get_house(h5_lord) == 7 or self._get_house(h7_lord) == 5:
            love_score += 3
            indicators.append("5th-7th house connection (love marriage yoga)")
        planets_in_5 = [p for p, data in d1.items() if self._get_house(p) == 5]
        planets_in_7 = [p for p, data in d1.items() if self._get_house(p) == 7]
        if "Ra" in planets_in_5 or "Ra" in planets_in_7 or "Ke" in planets_in_5:
            love_score += 2
            indicators.append("Rahu/Ketu influence (unconventional/love)")
        if ve_house == 5:
            love_score += 2
            indicators.append("Venus in 5th house (romance)")
        if "Ju" in planets_in_7:
            arranged_score += 2
            indicators.append("Jupiter in 7th (traditional/arranged)")
        h7_lord_house = self._get_house(h7_lord)
        if h7_lord_house in [2, 4, 10]:
            arranged_score += 2
            h7_ordinal = (
                "2nd" if h7_lord_house == 2 else "4th" if h7_lord_house == 4 else "10th"
            )
            indicators.append(f"7th lord in {h7_ordinal} (family involvement)")
        if ve_house in [2, 4, 10]:
            arranged_score += 1
            indicators.append("Venus in family house (arranged tendency)")
        if "Sa" in planets_in_7:
            arranged_score += 1
            indicators.append("Saturn in 7th (traditional approach)")
        if love_score == 0 and arranged_score == 0:
            category = "Neutral"
            probability = "Cannot determine clearly - could be either"
        elif love_score > arranged_score + 2:
            category = "Love Marriage"
            probability = "High probability of love/self-choice marriage"
            confidence = "High" if love_score >= 5 else "Moderate"
        elif arranged_score > love_score + 2:
            category = "Arranged Marriage"
            probability = "High probability of arranged/family-introduced marriage"
            confidence = "High" if arranged_score >= 4 else "Moderate"
        else:
            category = "Mixed/Love-cum-Arranged"
            probability = "Mixed indicators - modern love-cum-arranged very likely"
            confidence = "Moderate"
        return {
            "category": category,
            "probability": probability,
            "confidence": confidence if "confidence" in locals() else "Low",
            "love_score": love_score,
            "arranged_score": arranged_score,
            "indicators": indicators,
        }

    def _predict_appearance_enhanced(self) -> Dict:
        h7_idx = (self.lagna_idx + 6) % 12
        h7_sign = ZODIAC_SIGNS[h7_idx]
        appearance = SIGN_APPEARANCE.get(h7_sign, {}).copy()
        appearance["primary_source"] = f"7th house in {h7_sign}"
        dk_planet = self._find_darakaraka_planet()
        d1 = self.data["planets_d1"]
        d9 = self.data["d9"]
        if dk_planet:
            dk_traits = PLANET_SPOUSE_TRAITS.get(dk_planet, {})
            appearance["dk_planet"] = SHORT_TO_FULL[dk_planet]
            appearance["dk_influence"] = dk_traits.get("appearance", "")
            dk_sign = d1[dk_planet]["sign"]
            dk_sign_traits = SIGN_APPEARANCE.get(dk_sign, {})
            appearance["dk_sign_adds"] = dk_sign_traits.get("build", "")
            if dk_planet in d9:
                dk_d9_sign = d9[dk_planet]["sign"]
                d9_traits = SIGN_APPEARANCE.get(dk_d9_sign, {})
                appearance["d9_refinement"] = d9_traits.get("face", "")
        return appearance

    def _predict_meeting(self) -> Dict:
        h7_idx = (self.lagna_idx + 6) % 12
        h7_sign = ZODIAC_SIGNS[h7_idx]
        h7_lord = SIGN_LORDS[h7_sign]
        h7_lord_house = self._get_house(h7_lord)
        circumstance = MEETING_CIRCUMSTANCES.get(h7_lord_house, "Various circumstances")
        return {"primary": circumstance, "7th_lord_house": h7_lord_house}

    def _predict_profession(self) -> Dict:
        dk_planet = self._find_darakaraka_planet()
        profession = {}
        if dk_planet:
            profession["primary"] = PLANET_SPOUSE_TRAITS.get(dk_planet, {}).get(
                "profession", ""
            )
        h7_idx = (self.lagna_idx + 6) % 12
        h7_sign = ZODIAC_SIGNS[h7_idx]
        h7_lord = SIGN_LORDS[h7_sign]
        h7_lord_house = self._get_house(h7_lord)
        profession["secondary"] = PROFESSION_BY_HOUSE.get(h7_lord_house, "")
        return profession

    def _consolidate_profile(self, h7: Dict, karaka: Dict, dk: Dict) -> Dict:
        return {
            "7th_house_sign": h7["d1"]["sign"],
            "7th_lord": h7["d1"]["lord"],
            "darakaraka": dk["name"],
            "venus_functional": karaka["venus"]["label"],
            "jupiter_functional": karaka["jupiter"]["label"],
        }

    def _consolidate_personality(self, h7: Dict, dk: Dict) -> Dict:
        h7_sign = h7["d1"]["sign"]
        h7_traits = SIGN_APPEARANCE.get(h7_sign, {}).get("personality", "")
        dk_traits = dk["traits"].get("personality", "")
        return {"7th_house_influence": h7_traits, "darakaraka_influence": dk_traits}

    def _calculate_confidence(self) -> str:
        """Qualitative confidence based on confirming factor count.
        These are NOT statistical probabilities – they reflect the number
        of classical correlations aligning, per BPHS/Jaimini/Phaladeepika."""
        count = len(self.confidence_factors)
        if count >= 10:
            return "Very High (10+ confirming factors)"
        elif count >= 7:
            return "High (7-9 confirming factors)"
        elif count >= 5:
            return "Moderate-High (5-6 confirming factors)"
        elif count >= 3:
            return "Moderate (3-4 confirming factors)"
        else:
            return "Low (<3 confirming factors)"

    # ------------------------------------------------------------------------
    # Report Generation
    # ------------------------------------------------------------------------
    def generate_report(self) -> str:
        pred = self.predict()
        lines = []
        lines.append("=" * 90)
        lines.append(
            "  ADVANCED FUTURE SPOUSE PREDICTION - PROFESSIONAL 2025-26 EDITION"
        )
        lines.append(
            "  (25+ Vedic Layers: Functional Nature + Integrity + Aspects + Dashas + Transits)"
        )
        lines.append("=" * 90)
        lines.append(f"\nGender: {self.gender} | Lagna: {self.lagna_sign}")
        lines.append(f"Spouse Karaka: {SHORT_TO_FULL[self.spouse_karaka]}")
        lines.append(f"\nOverall Confidence Score: {pred['confidence_score']}")

        # ====================================================================
        # SPOUSE PROFILE
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("👤 SPOUSE PROFILE")
        lines.append("─" * 90)
        profile = pred["spouse_profile"]
        lines.append(f"7th House Sign: {profile['7th_house_sign']}")
        lines.append(f"7th Lord: {SHORT_TO_FULL[profile['7th_lord']]}")
        lines.append(f"Darakaraka: {profile['darakaraka']}")
        lines.append(f"Venus Functional Nature: {profile['venus_functional']}")
        lines.append(f"Jupiter Functional Nature: {profile['jupiter_functional']}")

        # ====================================================================
        # DARAKARAKA DETAILS
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("🌟 DARAKARAKA DETAILS (Jaimini)")
        lines.append("─" * 90)
        dk = pred["darakaraka_details"]
        lines.append(f"Planet: {dk['name']} at {dk['degree']:.2f}° within sign")
        lines.append(f"Sign in D1: {dk['sign_d1']} ({dk['dignity_d1']})")
        lines.append(f"Sign in D9: {dk['sign_d9']} ({dk['dignity_d9']})")
        lines.append(f"DK in D9 {dk['d9_house']}th house: {dk['d9_house_meaning']}")
        lines.append(
            f"Integrity Score: {dk['integrity']}% - {self.data['integrity'].get(dk['planet'], {}).get('label', 'N/A')}"
        )
        lines.append(f"Functional Nature: {dk['functional']}")

        # ====================================================================
        # PERSONALITY & APPEARANCE
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("💫 SPOUSE PERSONALITY")
        lines.append("─" * 90)
        personality = pred["personality"]
        lines.append(f"7th House Influence: {personality['7th_house_influence']}")
        lines.append(f"Darakaraka Influence: {personality['darakaraka_influence']}")

        lines.append("\n" + "─" * 90)
        lines.append("✨ PHYSICAL APPEARANCE (Multi-Layer)")
        lines.append("─" * 90)
        appearance = pred["appearance"]
        lines.append(f"Primary Source: {appearance.get('primary_source', 'N/A')}")
        lines.append(f"Build: {appearance.get('build', 'N/A')}")
        lines.append(f"Face: {appearance.get('face', 'N/A')}")
        lines.append(f"Complexion: {appearance.get('complexion', 'N/A')}")
        if "dk_planet" in appearance:
            lines.append(
                f"Darakaraka {appearance['dk_planet']} adds: {appearance.get('dk_influence', '')}"
            )
            lines.append(f"DK sign modifier: {appearance.get('dk_sign_adds', '')}")
            lines.append(f"D9 refinement: {appearance.get('d9_refinement', '')}")

        # ====================================================================
        # VENUS-MARS & YOGAS
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("❤️‍🔥 VENUS-MARS DYNAMICS")
        lines.append("─" * 90)
        vm = pred["venus_mars"]
        lines.append(f"Status: {vm['status']}")
        lines.append(f"Effect: {vm['effect']}")

        if pred["marriage_yogas"]:
            lines.append("\n" + "─" * 90)
            lines.append("🔮 MARRIAGE YOGAS (from report)")
            lines.append("─" * 90)
            for yoga in pred["marriage_yogas"]:
                lines.append(
                    f"• {yoga['name']} (Strength {yoga['strength']}/10) → {yoga['effect']}"
                )

        # ====================================================================
        # MEETING & PROFESSION
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("📍 MEETING CIRCUMSTANCES")
        lines.append("─" * 90)
        meeting = pred["meeting"]
        h7_lord_house = meeting["7th_lord_house"]
        ordinal = f"{h7_lord_house}th"
        if h7_lord_house == 1:
            ordinal = "1st"
        elif h7_lord_house == 2:
            ordinal = "2nd"
        elif h7_lord_house == 3:
            ordinal = "3rd"
        lines.append(f"Most Likely: {meeting['primary']}")
        lines.append(f"(7th lord in {ordinal} house)")

        lines.append("\n" + "─" * 90)
        lines.append("💼 SPOUSE PROFESSION")
        lines.append("─" * 90)
        profession = pred["profession"]
        lines.append(f"Primary Field: {profession.get('primary', 'N/A')}")
        lines.append(f"Secondary Field: {profession.get('secondary', 'N/A')}")

        # ====================================================================
        # UPAPADA, A7, D9 7TH
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("🏠 UPAPADA LAGNA (Marriage House) - ENHANCED")
        lines.append("─" * 90)
        ul = pred["upapada"]
        lines.append(
            f"Upapada Sign: {ul['sign']} (Lord {ul['lord']}, Dignity {ul['dignity']})"
        )
        lines.append(
            f"Strength: {'Strong - Stable marriage' if ul['strong'] else 'Moderate - needs effort'}"
        )
        lines.append(f"2nd from UL ({ul['2nd_sign']}): {ul['2nd_meaning']}")
        lines.append(f"8th from UL ({ul['8th_sign']}): {ul['8th_meaning']}")

        lines.append("\n" + "─" * 90)
        lines.append("🎭 A7 DARAPADA (Public Image of Marriage)")
        lines.append("─" * 90)
        a7 = pred["a7_darapada"]
        lines.append(f"A7 Sign: {a7['sign']} (Lord {a7['lord']})")
        lines.append(f"Status: {a7['status'].capitalize()}")
        lines.append(f"Meaning: {a7['meaning']}")

        lines.append("\n" + "─" * 90)
        lines.append("🔷 NAVAMSA (D9) 7TH HOUSE - Soul Marriage Level")
        lines.append("─" * 90)
        d9_7 = pred["d9_seventh_house"]
        lines.append(f"D9 7th House Sign: {d9_7['d9_7th_sign']}")
        lines.append(
            f"D9 7th Lord: {SHORT_TO_FULL[d9_7['d9_7th_lord']]} in {d9_7['d9_7th_lord_sign']} ({d9_7['d9_7th_lord_dignity']})"
        )
        lines.append(f"Functional Nature (D1 proxy): {d9_7['functional_lord']}")
        if d9_7["planets_in_d9_7th"]:
            lines.append(
                f"Planets in D9 7th: {', '.join([SHORT_TO_FULL[p] for p in d9_7['planets_in_d9_7th']])}"
            )
        lines.append(f"Interpretation: {d9_7['interpretation']}")

        # ====================================================================
        # ASPECTS ON 7TH
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("👁️ ASPECTS ON 7TH HOUSE & 7TH LORD")
        lines.append("─" * 90)
        aspects = pred["aspects_on_7th"]["aspects"]
        if aspects:
            for asp in aspects:
                lines.append(
                    f"• {asp['planet']} {asp['type']} on {asp['target']} ({asp['strength']}%, {asp['nature']}, {asp['condition']})"
                )
        else:
            lines.append("No significant aspects detected.")

        # ====================================================================
        # HOUSE LORD PLACEMENTS
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("🏡 HOUSE LORD PLACEMENTS (Spouse-Related)")
        lines.append("─" * 90)
        lords = pred["lord_placements"]
        if lords["seventh_house"]:
            lines.append(
                f"7th House Lord: {lords['seventh_house'].get('interpretation', 'N/A')}"
            )
        if lords["second_house"]:
            lines.append(
                f"2nd House Lord (Family Wealth): {lords['second_house'].get('interpretation', 'N/A')}"
            )
        if lords["fifth_house"]:
            lines.append(
                f"5th House Lord (Romance): {lords['fifth_house'].get('interpretation', 'N/A')}"
            )

        # ====================================================================
        # MARRIAGE TYPE
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("💑 MARRIAGE TYPE PREDICTION")
        lines.append("─" * 90)
        mtype = pred["marriage_type"]
        lines.append(f"Category: {mtype['category']}")
        lines.append(f"Probability: {mtype['probability']}")
        lines.append(f"Confidence: {mtype['confidence']}")
        lines.append(
            f"Love Score: {mtype['love_score']} | Arranged Score: {mtype['arranged_score']}"
        )
        if mtype["indicators"]:
            lines.append("Indicators:")
            for ind in mtype["indicators"]:
                lines.append(f"  • {ind}")

        # ====================================================================
        # MANGLIK DOSHA
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("⚠️ MANGLIK (KUJA) DOSHA ANALYSIS")
        lines.append("─" * 90)
        manglik = pred["manglik_dosha"]
        if manglik["present"]:
            lines.append(f"Status: PRESENT ({manglik['severity']})")
            lines.append(
                f"Mars in {manglik['mars_house']}th house ({manglik['mars_sign']}) - {manglik['mars_dignity']}"
            )
            if manglik["cancellations"]:
                lines.append("🟢 Cancellations Present:")
                for cancel in manglik["cancellations"]:
                    lines.append(f"  ✓ {cancel}")
            lines.append(f"Recommendation: {manglik['recommendation']}")
        else:
            lines.append(f"Status: NOT PRESENT - {manglik['reason']}")

        # ====================================================================
        # Neecha Bhanga Effects
        # ====================================================================
        if pred["neecha_bhanga_effects"]:
            lines.append("\n" + "─" * 90)
            lines.append("🔄 NEECHA BHANGA EFFECTS")
            lines.append("─" * 90)
            for planet, effect in pred["neecha_bhanga_effects"].items():
                lines.append(f"• {planet}: {effect}")

        # ====================================================================
        # ASHTAKAVARGA & NAVAMSA
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("📊 ASHTAKAVARGA 7TH HOUSE")
        lines.append("─" * 90)
        ashtak = pred["ashtakavarga"]
        lines.append(f"Points: {ashtak['points']}")
        if "strength" in ashtak:
            lines.append(f"Strength: {ashtak['strength']}")
        lines.append(f"Interpretation: {ashtak['interpretation']}")

        lines.append("\n" + "─" * 90)
        lines.append("📈 NAVAMSA VARGOTTAMA")
        lines.append("─" * 90)
        navamsa = pred["navamsa_strength"]
        lines.append(f"Vargottama Planets: {navamsa['count']}")
        if navamsa["vargottama"]:
            lines.append(
                f"  → {', '.join([SHORT_TO_FULL[p] for p in navamsa['vargottama']])}"
            )

        # ====================================================================
        # MARRIAGE TIMING (DASHA)
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("⏳ MARRIAGE TIMING (Dasha Windows)")
        lines.append("─" * 90)
        dashas = pred["dasha_timing"]
        if dashas["upcoming"]:
            lines.append("Upcoming High-Probability Periods:")
            for p in dashas["upcoming"]:
                lines.append(
                    f"  • {p['maha']}/{p['antara']} ({p['start']}-{p['end']}) - Score {p['score']}/10"
                )
        else:
            lines.append("No high-score upcoming periods found in report data.")

        # ====================================================================
        # CURRENT TRANSITS
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("🌍 CURRENT TRANSIT EFFECTS ON MARRIAGE")
        lines.append("─" * 90)
        transits = pred["current_transits"]
        if transits["transiting_7th"]:
            lines.append(
                f"Planets transiting 7th house: {', '.join(transits['transiting_7th'])}"
            )
        if transits["aspecting_7th"]:
            lines.append(
                f"Planets aspecting 7th house from transit: {', '.join(transits['aspecting_7th'])}"
            )
        if not transits["transiting_7th"] and not transits["aspecting_7th"]:
            lines.append("No current transit activation of 7th house.")

        # ====================================================================
        # NAKSHATRA INSIGHTS
        # ====================================================================
        if pred["nakshatra_insights"]:
            lines.append("\n" + "─" * 90)
            lines.append("🌙 NAKSHATRA INSIGHTS (Refined Spouse Description)")
            lines.append("─" * 90)
            for p, info in pred["nakshatra_insights"].items():
                lines.append(
                    f"• {SHORT_TO_FULL[p]} in {info['nakshatra']} (ruled by {info['lord']}, deity {info['deity']})"
                )
                lines.append(f"  → {info['meaning']}")

        # ====================================================================
        # GRAHA YUDDHA (Planetary War)
        # ====================================================================
        if pred["graha_yuddha"]:
            lines.append("\n" + "─" * 90)
            lines.append("⚔️ GRAHA YUDDHA (Planetary War)")
            lines.append("─" * 90)
            for war in pred["graha_yuddha"]:
                lines.append(f"• {war['description']}")

        # ====================================================================
        # INTEGRITY SUMMARY
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append("🔒 PLANETARY INTEGRITY (Reliability)")
        lines.append("─" * 90)
        for p, data in pred["integrity_summary"].items():
            lines.append(f"• {SHORT_TO_FULL[p]}: {data['score']}% - {data['label']}")

        # ====================================================================
        # CONFIDENCE FACTORS
        # ====================================================================
        lines.append("\n" + "─" * 90)
        lines.append(f"✅ CONFIRMING FACTORS ({len(pred['confidence_factors'])})")
        lines.append("─" * 90)
        for factor in pred["confidence_factors"]:
            lines.append(f"• {factor}")

        lines.append("\n" + "=" * 90)
        lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(
            "Classical Sources: BPHS, Jaimini Sutras, Phaladeepika, Saravali, Jataka Tattva"
        )
        lines.append("Note: Confidence levels are qualitative (based on classical correlations), not statistically validated.")
        lines.append("=" * 90)

        return "\n".join(lines)




def calculate_a7_darapada(lagna_idx: int, planets_d1: Dict) -> Dict:
    h7_idx = (lagna_idx + 6) % 12
    h7_sign = ZODIAC_SIGNS[h7_idx]
    h7_lord = SIGN_LORDS[h7_sign]
    if h7_lord not in planets_d1:
        return {"sign": "Unknown", "status": "neutral", "meaning": "Data insufficient"}
    lord_sign = planets_d1[h7_lord]["sign"]
    lord_idx = safe_sign_index(lord_sign)
    distance = (lord_idx - h7_idx) % 12
    a7_idx = (lord_idx + distance) % 12
    if a7_idx == h7_idx:
        a7_idx = (h7_idx + 9) % 12
    elif a7_idx == (h7_idx + 6) % 12:
        a7_idx = ((h7_idx + 6) + 9) % 12
    a7_sign = ZODIAC_SIGNS[a7_idx]
    a7_lord = SIGN_LORDS[a7_sign]
    a7_lord_sign = planets_d1.get(a7_lord, {}).get("sign", "")
    a7_dignity = get_dignity(a7_lord, a7_lord_sign)
    status = (
        "strong"
        if a7_dignity in ["Exalted", "Own"]
        else "afflicted" if a7_dignity == "Debilitated" else "neutral"
    )
    meaning = {
        "strong": "Attractive spouse image, harmonious public perception of marriage",
        "afflicted": "Challenges in public perception, possible delays/conflicts",
        "neutral": "Average public image of marriage",
    }.get(status, "")
    return {"sign": a7_sign, "lord": a7_lord, "status": status, "meaning": meaning}


