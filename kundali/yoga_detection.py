# yoga_detection.py
"""
Detection and strength scoring of 80+ Vedic classical yogas (planetary combinations).

Covers:
  - Pancha Mahapurusha (5)
  - Raja Yogas / Yogakaraka / Viparita Raja
  - Dhana Yogas (wealth): Lakshmi, Kubera, Vasumati, Chandra-Mangal
  - Moon-based: Gajakesari, Adhi, Sunapha, Anapha, Durudhara, Kemadruma
  - Solar: Vesi, Vosi, Ubhayachari, Budha-Aditya
  - Personality: Saraswati, Veena, Musala, Nala, Mala
  - Kartari: Shubha/Papa Kartari
  - Neecha Bhanga Raja Yoga
  - Special: Kala Sarpa, Guru-Chandala, Graha Malika, Vargottama
  - Parivartana, Parvata, Kahala, Chamara, Shankha, Parijata
  - Dharma-Karma Adhipati, Akhanda Samrajya, Amala, Mahabhagya, Pushkala
  - 80+ total classical combinations from BPHS, Phaladeepika, Brihat Jataka
"""

from .constants import short_to_full, zodiac_signs, sign_lords, FUNCTIONAL_QUALITY
from .utils import get_dignity


def get_yoga_strength(pl_list, result):
    """Calculate yoga strength from 1-10 based on dignity, house, retro,
    combustion, and Neecha Bhanga status."""
    score = 5  # baseline
    planets_data = result.get("planets", {})
    for pl in pl_list:
        if pl not in planets_data:
            continue
        d = planets_data[pl]
        if d["dignity"] == "Exalt":
            score += 3
        elif d["dignity"] == "Own":
            score += 2
        elif d["dignity"] == "Debilitated":
            if d.get("neecha_bhanga", False):
                score -= 1
            else:
                score -= 3
        if d.get("combust", False):
            score -= 2
        if not d["retro"]:
            score += 1
        planet_house = None
        for h, pls in result["houses"].items():
            if pl in pls:
                planet_house = h
                break
        if planet_house:
            if planet_house in [1, 4, 7, 10]:
                score += 2
            elif planet_house in [5, 9]:
                score += 1
    return max(1, min(10, score))


def detect_yogas(result):
    """Detect 80+ classical yogas and calculate their strength (1-10)."""
    yogas = []
    p = result["planets"]
    h = result["houses"]
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)

    planet_house = {}
    for house, pls in h.items():
        for pl in pls:
            if pl != "Asc":
                planet_house[pl] = house

    def lord_of(house_no):
        sign_idx = (lagna_idx + house_no - 1) % 12
        return sign_lords[zodiac_signs[sign_idx]]

    def in_kendra(planet):
        return planet_house.get(planet) in [1, 4, 7, 10]

    def in_trikona(planet):
        return planet_house.get(planet) in [1, 5, 9]

    def in_upachaya(planet):
        return planet_house.get(planet) in [3, 6, 10, 11]

    def in_dusthana(planet):
        return planet_house.get(planet) in [6, 8, 12]

    def are_conjunct(pl1, pl2):
        h1 = planet_house.get(pl1)
        h2 = planet_house.get(pl2)
        return h1 is not None and h1 == h2

    def mutual_aspect(pl1, pl2):
        h1 = planet_house.get(pl1)
        h2 = planet_house.get(pl2)
        if h1 is None or h2 is None:
            return False
        return (h2 - h1) % 12 == 6 or (h1 - h2) % 12 == 6

    def aspects_house(planet, target_house):
        ph = planet_house.get(planet)
        if ph is None:
            return False
        diff = (target_house - ph) % 12
        if planet == "Ma":
            return diff in [0, 3, 6, 7]
        if planet == "Ju":
            return diff in [0, 4, 6, 8]
        if planet == "Sa":
            return diff in [0, 2, 6, 9]
        return diff in [0, 6]

    all_planets = [pl for pl in ["Su","Mo","Ma","Me","Ju","Ve","Sa"] if pl in p]

    # ── 1. Gajakesari Yoga ────────────────────────────────────────────────────
    if "Ju" in planet_house and "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        ju_h = planet_house["Ju"]
        if (ju_h - mo_h) % 12 in (0, 3, 6, 9):
            s = get_yoga_strength(["Ju", "Mo"], result)
            yogas.append(f"Gajakesari Yoga (Strength {s}/10) → Fame, wisdom, wealth; Jupiter in kendra from Moon")

    # ── 2. Sunapha Yoga ───────────────────────────────────────────────────────
    if "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        second_from_moon = (mo_h % 12) + 1
        sunapha_pls = [pl for pl in ["Ma","Me","Ju","Ve","Sa"] if planet_house.get(pl) == second_from_moon]
        if sunapha_pls:
            s = get_yoga_strength(["Mo"] + sunapha_pls, result)
            yogas.append(f"Sunapha Yoga ({','.join(sunapha_pls)} in 2nd from Moon, Strength {s}/10) → Self-made wealth, intelligence")

    # ── 3. Anapha Yoga ────────────────────────────────────────────────────────
    if "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        twelfth_from_moon = ((mo_h - 2) % 12) + 1
        anapha_pls = [pl for pl in ["Ma","Me","Ju","Ve","Sa"] if planet_house.get(pl) == twelfth_from_moon]
        if anapha_pls:
            s = get_yoga_strength(["Mo"] + anapha_pls, result)
            yogas.append(f"Anapha Yoga ({','.join(anapha_pls)} in 12th from Moon, Strength {s}/10) → Health, fame, generous spirit")

    # ── 4. Durudhara Yoga ────────────────────────────────────────────────────
    if "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        has_2nd = any(planet_house.get(pl) == (mo_h % 12) + 1 for pl in ["Ma","Me","Ju","Ve","Sa"])
        has_12th = any(planet_house.get(pl) == ((mo_h - 2) % 12) + 1 for pl in ["Ma","Me","Ju","Ve","Sa"])
        if has_2nd and has_12th:
            s = get_yoga_strength(["Mo"], result)
            yogas.append(f"Durudhara Yoga (Strength {s}/10) → Surrounded by wealth and pleasures; life of abundance")

    # ── 5. Kemadruma Yoga (affliction) ───────────────────────────────────────
    if "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        has_any = any(
            planet_house.get(pl) in [(mo_h % 12)+1, ((mo_h-2) % 12)+1, mo_h]
            for pl in ["Su","Ma","Me","Ju","Ve","Sa"])
        if not has_any:
            yogas.append("Kemadruma Yoga (Affliction) → Mental anxiety, unstable mind; needs Jupiter transit remedy")

    # ── 6. Vesi Yoga ──────────────────────────────────────────────────────────
    if "Su" in planet_house:
        su_h = planet_house["Su"]
        vesi_pls = [pl for pl in ["Ma","Me","Ju","Ve","Sa"] if planet_house.get(pl) == (su_h % 12) + 1]
        if vesi_pls:
            s = get_yoga_strength(["Su"] + vesi_pls, result)
            yogas.append(f"Vesi Yoga ({','.join(vesi_pls)} in 2nd from Sun, Strength {s}/10) → Eloquent, virtuous, fortunate")

    # ── 7. Vosi Yoga ──────────────────────────────────────────────────────────
    if "Su" in planet_house:
        su_h = planet_house["Su"]
        vosi_pls = [pl for pl in ["Ma","Me","Ju","Ve","Sa"] if planet_house.get(pl) == ((su_h-2) % 12) + 1]
        if vosi_pls:
            s = get_yoga_strength(["Su"] + vosi_pls, result)
            yogas.append(f"Vosi Yoga ({','.join(vosi_pls)} in 12th from Sun, Strength {s}/10) → Intelligent, fluctuating fortunes")

    # ── 8. Ubhayachari Yoga ───────────────────────────────────────────────────
    if "Su" in planet_house:
        su_h = planet_house["Su"]
        has_2nd_s = any(planet_house.get(pl) == (su_h % 12) + 1 for pl in ["Ma","Me","Ju","Ve","Sa"])
        has_12th_s = any(planet_house.get(pl) == ((su_h-2) % 12) + 1 for pl in ["Ma","Me","Ju","Ve","Sa"])
        if has_2nd_s and has_12th_s:
            s = get_yoga_strength(["Su"], result)
            yogas.append(f"Ubhayachari Yoga (Strength {s}/10) → High status, like a king; Sun flanked by planets")

    # ── 9. Budha-Aditya (Nipuna) Yoga ────────────────────────────────────────
    if are_conjunct("Su","Me"):
        s = get_yoga_strength(["Su","Me"], result)
        yogas.append(f"Budha-Aditya (Nipuna) Yoga (Strength {s}/10) → Brilliant intellect, skilled professional, fame through work")

    # ── 10. Raja Yogas (Kendra-Trikona lords) ────────────────────────────────
    seen_raja = set()
    yogakarakas_seen = set()
    for k in [1, 4, 7, 10]:
        for t in [1, 5, 9]:
            if k == t:
                continue
            kl = lord_of(k)
            tl = lord_of(t)
            if kl not in planet_house or tl not in planet_house:
                continue
            if kl == tl:
                if kl not in yogakarakas_seen:
                    yogakarakas_seen.add(kl)
                    s = get_yoga_strength([kl], result)
                    yogas.append(f"Yogakaraka {short_to_full.get(kl,kl)} (Strength {s}/10) → Most powerful planet; grants both power & grace")
            else:
                pair = tuple(sorted([kl, tl]))
                if pair in seen_raja:
                    continue
                diff = (planet_house[kl] - planet_house[tl] + 12) % 12
                if diff in (0, 6):
                    seen_raja.add(pair)
                    s = get_yoga_strength([kl, tl], result)
                    yogas.append(f"Raja Yoga ({kl}+{tl}, Strength {s}/10) → Power, authority, and high status")

    # ── 11. Neecha Bhanga Raja Yoga ───────────────────────────────────────────
    for pl in result.get("neecha_bhanga_planets", []):
        if pl in planet_house and (in_kendra(pl) or in_trikona(pl)):
            s = get_yoga_strength([pl], result)
            yogas.append(f"Neecha Bhanga Raja Yoga ({short_to_full.get(pl,pl)}, Strength {s}/10) → Debilitation cancelled; rises after struggles")

    # ── 12. Viparita Raja Yogas ───────────────────────────────────────────────
    for vname, trigger_house, interp in [
        ("Harsha",  6, "Health, enemies defeated, strong physique"),
        ("Sarala",  8, "Longevity, fearlessness, wealth from obstacles"),
        ("Vimala", 12, "Self-made wealth, virtuous, independent spirit"),
    ]:
        vl = lord_of(trigger_house)
        if vl in planet_house and planet_house[vl] in [6,8,12] and planet_house[vl] != trigger_house:
            s = get_yoga_strength([vl], result)
            yogas.append(f"{vname} Viparita Raja Yoga (Strength {s}/10) → {interp}")

    # ── 13. Pancha Mahapurusha Yogas ─────────────────────────────────────────
    pmp = {
        "Ruchaka (Mars)":   ("Ma", ["Aries","Scorpio","Capricorn"],   "Martial prowess, leadership, courage"),
        "Bhadra (Mercury)": ("Me", ["Gemini","Virgo"],                "Sharp intellect, eloquence, business acumen"),
        "Hamsa (Jupiter)":  ("Ju", ["Cancer","Sagittarius","Pisces"], "Wisdom, spirituality, good fortune"),
        "Malavya (Venus)":  ("Ve", ["Taurus","Libra","Pisces"],       "Beauty, luxury, artistic talent"),
        "Sasa (Saturn)":    ("Sa", ["Libra","Capricorn","Aquarius"],  "Authority, discipline, mass following"),
    }
    for name, (pl, signs, meaning) in pmp.items():
        if pl in p and p[pl]["sign"] in signs and in_kendra(pl):
            s = get_yoga_strength([pl], result)
            yogas.append(f"{name} Yoga (Strength {s}/10) → {meaning}")

    # ── 14. Dhana Yoga (2nd+11th lords) ──────────────────────────────────────
    d2 = lord_of(2)
    d11 = lord_of(11)
    if d2 in planet_house and d11 in planet_house:
        diff = (planet_house[d2] - planet_house[d11] + 12) % 12
        if diff in (0, 6):
            s = get_yoga_strength([d2, d11], result)
            yogas.append(f"Dhana Yoga (2nd+11th lords, Strength {s}/10) → Wealth accumulation, financial prosperity")

    # ── 15. Lakshmi Yoga ─────────────────────────────────────────────────────
    d9_lord = lord_of(9)
    if (d9_lord in planet_house and "Ve" in planet_house and
        (in_kendra(d9_lord) or in_trikona(d9_lord)) and
        p.get("Ve",{}).get("dignity") in ["Own","Exalt"]):
        s = get_yoga_strength([d9_lord, "Ve"], result)
        yogas.append(f"Lakshmi Yoga (9th lord + strong Venus, Strength {s}/10) → Goddess of wealth; great riches and beauty")

    # ── 16. Vasumati Yoga ────────────────────────────────────────────────────
    if "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        benefics_upachaya_moon = [pl for pl in ["Me","Ju","Ve"]
                                   if planet_house.get(pl) is not None and
                                   ((planet_house[pl] - mo_h) % 12) in [2,5,9,10]]
        if len(benefics_upachaya_moon) >= 2:
            s = get_yoga_strength(["Mo"] + benefics_upachaya_moon, result)
            yogas.append(f"Vasumati Yoga (benefics in upachayas from Moon, Strength {s}/10) → Wealthy, respected, opulent life")

    # ── 17. Adhi Yoga ────────────────────────────────────────────────────────
    if "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        adhi_pls = [pl for pl in ["Me","Ju","Ve"]
                    if planet_house.get(pl) is not None and
                    ((planet_house[pl] - mo_h) % 12) in [5,6,7]]
        if len(adhi_pls) >= 2:
            s = get_yoga_strength(["Mo"] + adhi_pls, result)
            yogas.append(f"Adhi Yoga (benefics in 6/7/8 from Moon, Strength {s}/10) → Minister/leader; protective, respected, wealthy")

    # ── 18. Chandra-Mangal Yoga ───────────────────────────────────────────────
    if "Mo" in planet_house and "Ma" in planet_house:
        if are_conjunct("Mo","Ma") or mutual_aspect("Mo","Ma"):
            s = get_yoga_strength(["Mo","Ma"], result)
            yogas.append(f"Chandra-Mangal Yoga (Strength {s}/10) → Wealth through business/trade; emotional drive for money")

    # ── 19. Saraswati Yoga ───────────────────────────────────────────────────
    sars_houses = [1,2,4,5,7,9,10]
    if (all(planet_house.get(pl) in sars_houses for pl in ["Ju","Ve","Me"] if pl in planet_house) and
            sum(1 for pl in ["Ju","Ve","Me"] if planet_house.get(pl) in sars_houses) == 3 and
            p.get("Ju",{}).get("dignity") in ["Own","Exalt","Friend"]):
        s = get_yoga_strength(["Ju","Ve","Me"], result)
        yogas.append(f"Saraswati Yoga (Strength {s}/10) → Goddess of learning; exceptional intellect, arts, scholarship")

    # ── 20. Veena Yoga ───────────────────────────────────────────────────────
    houses_used = set(planet_house.get(pl) for pl in ["Su","Mo","Ma","Me","Ju","Ve","Sa"] if planet_house.get(pl))
    if len(houses_used) == 7:
        yogas.append("Veena Yoga (Strength 8/10) → Musical talent, fine arts, life of pleasure and fame")

    # ── 21. Musala Yoga ───────────────────────────────────────────────────────
    fixed_signs = {"Taurus","Leo","Scorpio","Aquarius"}
    if all(p[pl]["sign"] in fixed_signs for pl in all_planets):
        s = get_yoga_strength(all_planets, result)
        yogas.append(f"Musala Yoga (Strength {s}/10) → Wealthy, famous, stable but unyielding nature")

    # ── 22. Nala Yoga ────────────────────────────────────────────────────────
    dual_signs = {"Gemini","Virgo","Sagittarius","Pisces"}
    if all(p[pl]["sign"] in dual_signs for pl in all_planets):
        yogas.append("Nala Yoga (Strength 7/10) → Clever, versatile, multiple talents")

    # ── 23. Mala Yoga ────────────────────────────────────────────────────────
    movable_signs = {"Aries","Cancer","Libra","Capricorn"}
    if all(p[pl]["sign"] in movable_signs for pl in all_planets):
        yogas.append("Mala Yoga (Strength 7/10) → Active, dynamic, achiever, initiator")

    # ── 24. Shubha Kartari Yoga ───────────────────────────────────────────────
    if (any(planet_house.get(pl) == 2 for pl in ["Me","Ju","Ve"]) and
        any(planet_house.get(pl) == 12 for pl in ["Me","Ju","Ve"])):
        yogas.append("Shubha Kartari Yoga (Strength 8/10) → Protected life; benefic scissors around Lagna; prosperity")

    # ── 25. Papa Kartari Yoga ─────────────────────────────────────────────────
    if (any(planet_house.get(pl) == 2 for pl in ["Su","Ma","Sa","Ra","Ke"]) and
        any(planet_house.get(pl) == 12 for pl in ["Su","Ma","Sa","Ra","Ke"])):
        yogas.append("Papa Kartari Yoga (Affliction) → Lagna squeezed by malefics; difficulties from all sides")

    # ── 26. Moon Shubha Kartari ───────────────────────────────────────────────
    if "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        if (any(planet_house.get(pl) == (mo_h % 12) + 1 for pl in ["Me","Ju","Ve"]) and
            any(planet_house.get(pl) == ((mo_h-2) % 12) + 1 for pl in ["Me","Ju","Ve"])):
            s = get_yoga_strength(["Mo"], result)
            yogas.append(f"Shubha Kartari on Moon (Strength {s}/10) → Emotional security, supportive people, mental peace")

    # ── 27. Sreenatha Yoga ───────────────────────────────────────────────────
    d7_lord = lord_of(7)
    if d7_lord in p and p[d7_lord]["dignity"] == "Exalt" and planet_house.get(d7_lord) == 10:
        s = get_yoga_strength([d7_lord], result)
        yogas.append(f"Sreenatha Yoga (Strength {s}/10) → Blessed marriage, loyal spouse, prosperity through partner")

    # ── 28. Parvata Yoga ─────────────────────────────────────────────────────
    benefics_in_kendra_list = [pl for pl in ["Me","Ju","Ve"] if in_kendra(pl)]
    dusthana_empty = not any(planet_house.get(pl) in [6,8,12] for pl in ["Su","Mo","Ma","Me","Ju","Ve","Sa"])
    if len(benefics_in_kendra_list) >= 2 and dusthana_empty:
        s = get_yoga_strength(benefics_in_kendra_list, result)
        yogas.append(f"Parvata Yoga (Strength {s}/10) → Mountain-like stability; wealthy, generous, eloquent")

    # ── 29. Kahala Yoga ───────────────────────────────────────────────────────
    d4 = lord_of(4)
    d9 = d9_lord
    l1 = lord_of(1)
    if (d4 in planet_house and (in_kendra(d4) or in_trikona(d4)) and
        d9 in planet_house and (in_kendra(d9) or in_trikona(d9)) and
        l1 in planet_house and (in_kendra(l1) or in_trikona(l1))):
        s = get_yoga_strength([d4, d9, l1], result)
        yogas.append(f"Kahala Yoga (Strength {s}/10) → Courageous, commanding, army chief energy")

    # ── 30. Chamara Yoga ─────────────────────────────────────────────────────
    exalted_in_kendra = [pl for pl in p if p[pl]["dignity"] == "Exalt" and in_kendra(pl)]
    if len(exalted_in_kendra) >= 2:
        s = get_yoga_strength(exalted_in_kendra, result)
        yogas.append(f"Chamara Yoga ({','.join(exalted_in_kendra)} exalted, Strength {s}/10) → Royal bearing, scholarly, respected")

    # ── 31. Shankha Yoga ─────────────────────────────────────────────────────
    d5 = lord_of(5)
    d6 = lord_of(6)
    if d5 in planet_house and d6 in planet_house:
        if (planet_house[d5] - planet_house[d6] + 12) % 12 in (0, 3, 6, 9):
            s = get_yoga_strength([d5, d6], result)
            yogas.append(f"Shankha Yoga (Strength {s}/10) → Long life, righteous, devoted to dharma")

    # ── 32. Parijata Yoga ────────────────────────────────────────────────────
    if l1 in p:
        dispositor = sign_lords[p[l1]["sign"]]
        if dispositor in p and (p[dispositor]["dignity"] in ["Own","Exalt"] or in_kendra(dispositor)):
            s = get_yoga_strength([l1, dispositor], result)
            yogas.append(f"Parijata Yoga (Strength {s}/10) → Respected, wealthy, king-like; gains after initial struggles")

    # ── 33. Kalanidhi Yoga ───────────────────────────────────────────────────
    if "Ju" in planet_house and planet_house["Ju"] in [2,5]:
        if (are_conjunct("Ju","Me") or are_conjunct("Ju","Ve") or
                aspects_house("Me", planet_house["Ju"]) or aspects_house("Ve", planet_house["Ju"])):
            s = get_yoga_strength(["Ju","Me","Ve"], result)
            yogas.append(f"Kalanidhi Yoga (Strength {s}/10) → Mastery of fine arts, honored by royalty")

    # ── 34. Dharma-Karma Adhipati Yoga ───────────────────────────────────────
    d10_lord = lord_of(10)
    if d9 in planet_house and d10_lord in planet_house:
        diff = (planet_house[d9] - planet_house[d10_lord] + 12) % 12
        if diff in (0, 6):
            s = get_yoga_strength([d9, d10_lord], result)
            yogas.append(f"Dharma-Karma Adhipati Yoga (9th+10th lords, Strength {s}/10) → Career aligned with dharma; pillar of society")

    # ── 35. Amala Yoga ───────────────────────────────────────────────────────
    if "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        tenth_from_moon = ((mo_h + 9 - 1) % 12) + 1
        has_ben_10m = any(planet_house.get(pl) == tenth_from_moon for pl in ["Me","Ju","Ve"])
        has_mal_10m = any(planet_house.get(pl) == tenth_from_moon for pl in ["Su","Ma","Sa","Ra","Ke"])
        if has_ben_10m and not has_mal_10m:
            s = get_yoga_strength(["Mo"], result)
            yogas.append(f"Amala Yoga (Strength {s}/10) → Pure reputation; charity and fame that endure beyond lifetime")

    # ── 36. Mahabhagya Yoga ───────────────────────────────────────────────────
    gender = result.get("gender","Male")
    odd_signs = {"Aries","Gemini","Leo","Libra","Sagittarius","Aquarius"}
    even_signs = {"Taurus","Cancer","Virgo","Scorpio","Capricorn","Pisces"}
    if gender == "Male" and all(p.get(pl,{}).get("sign","") in odd_signs for pl in ["Su","Mo"]) and lagna_sign in odd_signs:
        yogas.append("Mahabhagya Yoga (Male, Strength 9/10) → Great destiny; wealth, fame, long life")
    elif gender == "Female" and all(p.get(pl,{}).get("sign","") in even_signs for pl in ["Su","Mo"]) and lagna_sign in even_signs:
        yogas.append("Mahabhagya Yoga (Female, Strength 9/10) → Great destiny; noble birth, renowned, prosperous family")

    # ── 37. Akhanda Samrajya Yoga ────────────────────────────────────────────
    if in_kendra("Ju"):
        ju_rules_trikon = any(lord_of(t) == "Ju" for t in [2,5,9,11])
        if ju_rules_trikon:
            s = get_yoga_strength(["Ju"], result)
            yogas.append(f"Akhanda Samrajya Yoga (Strength {s}/10) → Unbroken empire; vast wealth, enormous organizational power")

    # ── 38. Vargottama Planets ────────────────────────────────────────────────
    navamsa = result.get("navamsa", {})
    for pl in all_planets:
        if pl in navamsa and p[pl]["sign"] == navamsa[pl]["sign"]:
            s = get_yoga_strength([pl], result)
            yogas.append(f"Vargottama {short_to_full.get(pl,pl)} (Strength {s}/10) → D1=D9 sign; extremely powerful placement")

    # ── 39. Strong Venus in kendra/trikona ───────────────────────────────────
    if "Ve" in planet_house and (in_kendra("Ve") or p.get("Ve",{}).get("dignity") in ["Own","Exalt"]):
        s = get_yoga_strength(["Ve"], result)
        yogas.append(f"Strong Venus Yoga (Strength {s}/10) → Beautiful spouse, luxury, artistic talent")

    # ── 40. Strong 7th Lord ───────────────────────────────────────────────────
    seventh_lord = result["seventh_lord"]
    if seventh_lord in planet_house and planet_house[seventh_lord] in [1,4,7,10,5,9]:
        s = get_yoga_strength([seventh_lord], result)
        yogas.append(f"Strong 7th Lord ({seventh_lord}, Strength {s}/10) → Stable, prosperous marriage")

    # ── 41. Jupiter in 5th ────────────────────────────────────────────────────
    if planet_house.get("Ju") == 5:
        s = get_yoga_strength(["Ju"], result)
        yogas.append(f"Jupiter in 5th (Strength {s}/10) → Excellent progeny, intelligent children, spiritual wisdom")

    # ── 42. Strong 10th Lord ─────────────────────────────────────────────────
    if d10_lord in planet_house and in_kendra(d10_lord):
        s = get_yoga_strength([d10_lord], result)
        yogas.append(f"Strong 10th Lord ({d10_lord}, Strength {s}/10) → High career success, public recognition")

    # ── 43. Graha Malika Yoga ────────────────────────────────────────────────
    occupied = sorted(set(planet_house.get(pl) for pl in planet_house if pl not in ["Asc"] and planet_house.get(pl)))
    if len(occupied) >= 6:
        max_run = cur_run = 1
        for i in range(1, len(occupied)):
            if (occupied[i] - occupied[i-1]) % 12 == 1:
                cur_run += 1
                max_run = max(max_run, cur_run)
            else:
                cur_run = 1
        if max_run >= 6:
            yogas.append(f"Graha Malika Yoga ({max_run} consecutive houses, Strength 9/10) → Planetary garland; fame, wealth, remarkable life")

    # ── 44. Kala Sarpa Yoga ──────────────────────────────────────────────────
    if "Ra" in planet_house and "Ke" in planet_house:
        ra_h = planet_house["Ra"]
        ke_h = planet_house["Ke"]
        span = (ke_h - ra_h) % 12
        between = [pl for pl in all_planets if 0 < (planet_house.get(pl,0) - ra_h) % 12 < span]
        total = len([pl for pl in all_planets if pl in planet_house])
        if len(between) == total:
            yogas.append("Kala Sarpa Yoga → Intense karmic life; obstacles first half, remarkable rise after Rahu period")
        elif len(between) >= total - 1:
            yogas.append("Partial Kala Sarpa → Karmic intensity, periodic obstacles that transform into growth")

    # ── 45. Guru-Chandala Yoga ────────────────────────────────────────────────
    if are_conjunct("Ju","Ra"):
        s = get_yoga_strength(["Ju"], result)
        yogas.append(f"Guru-Chandala Yoga (Strength {s}/10) → Unconventional wisdom; breaks tradition; may indicate unorthodox teacher")

    # ── 46. Atmakaraka in Kendra/Trikona ─────────────────────────────────────
    atmakaraka = result.get("jaimini",{}).get("atmakaraka")
    if atmakaraka and (in_kendra(atmakaraka) or in_trikona(atmakaraka)):
        s = get_yoga_strength([atmakaraka], result)
        yogas.append(f"Atmakaraka in Angular/Trine ({short_to_full.get(atmakaraka,atmakaraka)}, Strength {s}/10) → Soul's mission actively supported")

    # ── 47. Kala Yoga (Saturn + Sun in trikona) ───────────────────────────────
    if in_trikona("Su") and in_trikona("Sa"):
        s = get_yoga_strength(["Su","Sa"], result)
        yogas.append(f"Kala Yoga (Sun+Saturn in trikonas, Strength {s}/10) → Mastery of time; disciplined leadership, karmic wisdom")

    # ── 48. Dharma Devata Yoga (Jupiter in 9th) ───────────────────────────────
    if planet_house.get("Ju") == 9:
        s = get_yoga_strength(["Ju"], result)
        yogas.append(f"Dharma Devata Yoga — Jupiter in 9th (Strength {s}/10) → Highly dharmic, blessed by guru/father")

    # ── 49. Pushkara (strong benefic in navamsa) ──────────────────────────────
    for pl in ["Ju","Ve","Mo"]:
        if pl in navamsa and get_dignity(pl, navamsa[pl]["sign"]) in ["Own","Exalt"]:
            s = get_yoga_strength([pl], result)
            yogas.append(f"Strong {short_to_full.get(pl,pl)} in Navamsa (Strength {s}/10) → Marriage/partner karma greatly blessed")

    # ── 50. Parivartana Yoga ─────────────────────────────────────────────────
    seen_pari = set()
    for pl1 in all_planets:
        for pl2 in all_planets:
            if pl1 == pl2 or tuple(sorted([pl1,pl2])) in seen_pari:
                continue
            if (sign_lords.get(p[pl1]["sign"]) == pl2 and sign_lords.get(p[pl2]["sign"]) == pl1):
                seen_pari.add(tuple(sorted([pl1,pl2])))
                h1 = planet_house.get(pl1,0)
                h2 = planet_house.get(pl2,0)
                s = get_yoga_strength([pl1,pl2], result)
                yogas.append(f"Parivartana Yoga ({pl1}↔{pl2}, H{h1}↔H{h2}, Strength {s}/10) → Mutual exchange activates both houses powerfully")

    # ── 51. Pushkala Yoga ────────────────────────────────────────────────────
    if "Mo" in p:
        mo_disp = sign_lords[p["Mo"]["sign"]]
        if in_kendra(mo_disp) and planet_house.get("Mo") in [1,2,3,4,5,9,10,11]:
            s = get_yoga_strength(["Mo", mo_disp], result)
            yogas.append(f"Pushkala Yoga (Strength {s}/10) → Wealth, status, eloquent speech, honored by authorities")

    # ── 52. Nipuna / Strong Mercury ───────────────────────────────────────────
    if "Me" in p and p["Me"]["dignity"] in ["Own","Exalt"] and in_kendra("Me"):
        s = get_yoga_strength(["Me"], result)
        yogas.append(f"Nipuna Yoga (Mercury, Strength {s}/10) → Master of intellect; brilliant in analysis, mathematics")

    # ── 53. Rahu in upachaya ─────────────────────────────────────────────────
    if planet_house.get("Ra") in [3,6,11]:
        yogas.append(f"Rahu in H{planet_house['Ra']} (Strength 7/10) → Rahu in upachaya: ambition, foreign gains, unconventional success")

    # ── 54. Ketu in 12th (Moksha) ────────────────────────────────────────────
    if planet_house.get("Ke") == 12:
        yogas.append("Ketu in 12th — Moksha Yoga (Strength 8/10) → Spiritual liberation; accumulated wisdom from past lives")

    # ── 55. Shubha Yoga (malefics all in upachayas) ───────────────────────────
    active_malefics = [pl for pl in ["Ma","Sa","Ra","Ke"] if pl in planet_house]
    if len(active_malefics) >= 3 and all(in_upachaya(pl) for pl in active_malefics):
        yogas.append("Shubha Yoga (malefics in upachayas, Strength 8/10) → Malefics in ideal positions; obstacles become stepping stones")

    # ── 56. Full Kendra Activation ────────────────────────────────────────────
    if all(any(planet_house.get(pl) == kh for pl in planet_house) for kh in [1,4,7,10]):
        yogas.append("Full Kendra Activation Yoga (Strength 8/10) → Complete manifestation power; goals become reality")

    # ── 57. Full Trikona Activation ───────────────────────────────────────────
    if all(any(planet_house.get(pl) == th for pl in planet_house if pl != "Asc") for th in [1,5,9]):
        yogas.append("Full Trikona Activation Yoga (Strength 8/10) → Dharmic purpose fulfilled; spiritual and material rewards")

    # ── 58. Mangala-Guru Yoga ────────────────────────────────────────────────
    if "Ma" in planet_house and "Ju" in planet_house:
        if are_conjunct("Ma","Ju") or mutual_aspect("Ma","Ju"):
            s = get_yoga_strength(["Ma","Ju"], result)
            yogas.append(f"Mangala-Guru Yoga (Strength {s}/10) → Dharmic warrior; wisdom + action; excellent for law, medicine, spirituality")

    # ── 59. Chandra-Shukra Yoga ───────────────────────────────────────────────
    if "Mo" in planet_house and "Ve" in planet_house:
        if are_conjunct("Mo","Ve") or mutual_aspect("Mo","Ve"):
            s = get_yoga_strength(["Mo","Ve"], result)
            yogas.append(f"Chandra-Shukra Yoga (Strength {s}/10) → Artistic sensibility, attractive personality, love of beauty")

    # ── 60. Guru Pushya Yoga ──────────────────────────────────────────────────
    if "Ju" in p and p["Ju"]["nakshatra"] == "Pushya":
        s = get_yoga_strength(["Ju"], result)
        yogas.append(f"Guru Pushya Yoga (Strength {s}/10) → Jupiter in most nourishing nakshatra; highly auspicious")

    # ── 61. Stellium Yoga ────────────────────────────────────────────────────
    sign_count = {}
    for pl in all_planets:
        sg = p[pl]["sign"]
        sign_count[sg] = sign_count.get(sg, 0) + 1
    for sg, cnt in sign_count.items():
        if cnt >= 4:
            yogas.append(f"Stellium in {sg} ({cnt} planets, Strength 7/10) → Concentrated energy; powerful focus in {sg} themes")

    # ── 62. Benefics in Lagna ────────────────────────────────────────────────
    benefics_in_lagna = [pl for pl in ["Me","Ju","Ve"] if planet_house.get(pl) == 1]
    if benefics_in_lagna:
        s = get_yoga_strength(benefics_in_lagna, result)
        yogas.append(f"{'+'.join(benefics_in_lagna)} in Lagna (Strength {s}/10) → Charming personality, natural magnetism, blessed constitution")

    # ── 63. Chandradhi Yoga ───────────────────────────────────────────────────
    if "Mo" in planet_house and (in_kendra("Mo") or in_trikona("Mo")) and aspects_house("Ju", planet_house["Mo"]):
        s = get_yoga_strength(["Mo","Ju"], result)
        yogas.append(f"Chandradhi Yoga (Strength {s}/10) → Emotionally intelligent, respected, spiritually inclined")

    # ── 64. Srikantha Yoga ───────────────────────────────────────────────────
    if all(in_trikona(pl) for pl in ["Su","Mo","Sa"] if pl in planet_house):
        s = get_yoga_strength(["Su","Mo","Sa"], result)
        yogas.append(f"Srikantha Yoga (Strength {s}/10) → Devotion to Shiva; austere yet powerful, philosophical nature")

    # ── 65. Vipareeta Dhana Yoga ─────────────────────────────────────────────
    vip_lords = {h_no: lord_of(h_no) for h_no in [6,8,12]}
    for h1, l1_code in vip_lords.items():
        for h2, l2_code in vip_lords.items():
            if h1 >= h2:
                continue
            if (l1_code in planet_house and planet_house[l1_code] == h2 and
                l2_code in planet_house and planet_house[l2_code] == h1):
                s = get_yoga_strength([l1_code, l2_code], result)
                yogas.append(f"Vipareeta Dhana Yoga (H{h1}↔H{h2} exchange, Strength {s}/10) → Wealth through unusual or hidden sources")

    # ── 66. Inheritance/Legacy Yoga ───────────────────────────────────────────
    d8_lord = lord_of(8)
    if (d8_lord in planet_house and d2 in planet_house and
        (are_conjunct(d8_lord, d2) or mutual_aspect(d8_lord, d2)) and
        p.get(d8_lord,{}).get("dignity") in ["Own","Exalt"]):
        s = get_yoga_strength([d8_lord, d2], result)
        yogas.append(f"Inheritance/Legacy Yoga (8th+2nd lords, Strength {s}/10) → Wealth through inheritance or partner's resources")

    # ── 67. Career-Wealth Yoga ───────────────────────────────────────────────
    if d2 in planet_house and d10_lord in planet_house and are_conjunct(d2, d10_lord) and in_kendra(d2):
        s = get_yoga_strength([d2, d10_lord], result)
        yogas.append(f"Career-Wealth Yoga (2nd+10th conjunct, Strength {s}/10) → Career directly generates substantial wealth")

    # ── 68. Sanyasa Tendency Yoga ────────────────────────────────────────────
    for sg, cnt in sign_count.items():
        if cnt >= 4:
            pls_in_sg = [pl for pl in all_planets if p.get(pl,{}).get("sign") == sg]
            if any(pl in pls_in_sg for pl in ["Sa","Ke"]):
                s = get_yoga_strength(pls_in_sg, result)
                yogas.append(f"Sanyasa Tendency Yoga (4+ planets in {sg}, Strength {s}/10) → Renunciation, spiritual depth, non-attachment")
                break

    # ── 69. Moon Arishta Yoga ────────────────────────────────────────────────
    moon_h = planet_house.get("Mo",0)
    if moon_h in [6,8,12] and p.get("Mo",{}).get("dignity") not in ["Own","Exalt"]:
        if any(aspects_house(pl, moon_h) for pl in ["Sa","Ma","Ra"] if pl in planet_house):
            yogas.append("Moon Arishta Yoga → Emotional sensitivity; mother/mind challenges; Moon remedies recommended")

    # ── 70. Kubera Yoga ──────────────────────────────────────────────────────
    kubera_lords = [lord_of(h_no) for h_no in [2,5,9,11]]
    kubera_strong = [l for l in kubera_lords if l in planet_house and (in_kendra(l) or in_trikona(l))]
    if len(kubera_strong) >= 3:
        s = get_yoga_strength(list(set(kubera_lords)), result)
        yogas.append(f"Kubera Yoga (3+ wealth lords strong, Strength {s}/10) → Immense wealth like the god of riches")

    # ── 71. Mridanga Yoga ────────────────────────────────────────────────────
    if (l1 in planet_house and in_upachaya(l1) and
        p.get(l1,{}).get("dignity") in ["Own","Exalt"] and
        "Ju" in planet_house and (in_kendra("Ju") or in_trikona("Ju"))):
        s = get_yoga_strength([l1,"Ju"], result)
        yogas.append(f"Mridanga Yoga (Strength {s}/10) → Rises to pinnacle of career; blessed leadership, royal honors")

    # ── 72. Strong benefic cluster ───────────────────────────────────────────
    strong_benefics = [pl for pl in ["Me","Ju","Ve","Mo"] if in_kendra(pl) or in_trikona(pl)]
    if len(strong_benefics) >= 3:
        s = get_yoga_strength(strong_benefics, result)
        yogas.append(f"Strong Benefic Cluster (Strength {s}/10) → Multiple benefics in power positions; auspicious life overall")

    # ── 73. Maheshwari Yoga ───────────────────────────────────────────────────
    if (are_conjunct("Su","Sa") and
        p.get("Su",{}).get("dignity") in ["Own","Exalt","Friend"] and
        p.get("Sa",{}).get("dignity") in ["Own","Exalt","Friend"]):
        s = get_yoga_strength(["Su","Sa"], result)
        yogas.append(f"Maheshwari Yoga (Strength {s}/10) → Authority balanced with discipline; rises through hardship")

    # ── 74. Gada Yoga ────────────────────────────────────────────────────────
    for kp1, kp2 in [(1,4),(4,7),(7,10),(10,1)]:
        pls_in_pair = [pl for pl in all_planets if planet_house.get(pl) in [kp1,kp2]]
        if len(pls_in_pair) >= 5:
            s = get_yoga_strength(pls_in_pair, result)
            yogas.append(f"Gada Yoga (planets massed H{kp1}+H{kp2}, Strength {s}/10) → Stubborn, wealthy, charitable but temperamental")
            break

    # ── 75. Lakshmi-Narayana Yoga (Venus+Jupiter conjunct/mutual aspect) ──────
    if "Ve" in planet_house and "Ju" in planet_house:
        if are_conjunct("Ve","Ju") or mutual_aspect("Ve","Ju"):
            s = get_yoga_strength(["Ve","Ju"], result)
            yogas.append(f"Lakshmi-Narayana Yoga (Strength {s}/10) → Divine grace; wealth, wisdom, spiritual harmony combined")

    # ── 76. Srikantha Yoga (Sun in 1/4/7/10 with strong aspect from Jupiter) ──
    if in_kendra("Su") and aspects_house("Ju", planet_house.get("Su",0)):
        s = get_yoga_strength(["Su","Ju"], result)
        yogas.append(f"Surya-Guru Yoga (Strength {s}/10) → Leadership blessed by wisdom; respected authority figure")

    # ── 77. Rahu+Mercury Yoga ────────────────────────────────────────────────
    if are_conjunct("Ra","Me"):
        yogas.append("Rahu-Mercury Yoga → Exceptional analytical ability, technology aptitude, unconventional thinking")

    # ── 78. Pushkara Navamsa (Lagna vargottama) ───────────────────────────────
    nav_asc = result.get("navamsa",{}).get("Asc",{})
    if nav_asc and result.get("lagna_sign") == nav_asc.get("sign",""):
        yogas.append("Vargottama Lagna (Strength 9/10) → Ascendant identical in D1 and D9; tremendously fortified personality")

    # ── 79. Kahal Yoga (Mars in 3rd + strong 3rd lord) ───────────────────────
    if planet_house.get("Ma") == 3:
        d3_lord = lord_of(3)
        if d3_lord in planet_house and (in_kendra(d3_lord) or in_trikona(d3_lord)):
            s = get_yoga_strength(["Ma", d3_lord], result)
            yogas.append(f"Kahal Yoga (Strength {s}/10) → Courageous, commands groups, bold communicator")

    # ── 80. Sreenatha extended (7th lord + Venus both strong) ────────────────
    if (seventh_lord in planet_house and "Ve" in planet_house and
        (in_kendra(seventh_lord) or in_trikona(seventh_lord)) and
        (in_kendra("Ve") or p.get("Ve",{}).get("dignity") in ["Own","Exalt"])):
        s = get_yoga_strength([seventh_lord, "Ve"], result)
        yogas.append(f"Extended Marriage Yoga (7th lord + Venus both strong, Strength {s}/10) → Outstanding marital happiness and romantic fulfillment")

    return yogas if yogas else ["No major classical yogas formed"]
