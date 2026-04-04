# kundali_matching.py
"""
Kundali Matching — Ashtakuta (8 Kuta) compatibility system.

Checks implemented (max points shown):
  1.  Varna        (1)   — spiritual evolution grade
  2.  Vasya        (2)   — dominance/attraction
  3.  Tara / Dina  (3)   — birth star compatibility
  4.  Yoni         (4)   — sexual / temperament compatibility
  5.  Graha Maitri (5)   — Moon sign lord friendship
  6.  Gana         (6)   — temperament (Deva/Manushya/Rakshasa)
  7.  Bhakoota     (7)   — Moon sign relative position
  8.  Nadi         (8)   — physiological / elemental dosha
  ── Total: 36 points ──

Additional checks (no points, dosha/flag):
  9.  Rajju Dosha     — spine-compatibility rule
  10. Vedha Dosha     — obstacle pairs among nakshatras
  11. Mahendra        — auspiciousness check
  12. Stree Deergha   — husband's star ≥ 9 nakshatras ahead of wife
  13. Kuja Dosha      — Mars affliction in 1/2/4/7/8/12
  14. Nadi Dosha      — same Nadi = severe dosha

Usage
-----
  from kundali.kundali_matching import match_kundalis
  report = match_kundalis(result_male, result_female)
"""

from .constants import zodiac_signs, sign_lords
from .nakshatra import NAKSHATRAS          # list of 27 nakshatra names


# ─────────────────────────────────────────────────────────────────────────────
# Static tables
# ─────────────────────────────────────────────────────────────────────────────

# Varna (0=Brahmin, 1=Kshatriya, 2=Vaishya, 3=Shudra)
_VARNA = {
    "Cancer":      0, "Scorpio":    0, "Pisces":     0,   # Brahmin (water)
    "Leo":         1, "Sagittarius":1, "Aries":      1,   # Kshatriya (fire)
    "Gemini":      2, "Libra":      2, "Aquarius":   2,   # Vaishya (air)
    "Taurus":      3, "Virgo":      3, "Capricorn":  3,   # Shudra (earth)
}

# Vasya groups: each sign is attracted to / compatible with its vasya group
_VASYA_GROUPS = [
    {"Aries", "Scorpio"},
    {"Taurus", "Libra", "Capricorn"},
    {"Gemini", "Virgo"},
    {"Cancer"},
    {"Leo"},
    {"Sagittarius", "Pisces"},
    {"Aquarius"},
]

# Yoni (animal symbol) for each nakshatra
_YONI = [
    "Horse",    # 0 Ashwini
    "Elephant", # 1 Bharani
    "Goat",     # 2 Krittika
    "Serpent",  # 3 Rohini
    "Serpent",  # 4 Mrigashira
    "Dog",      # 5 Ardra
    "Cat",      # 6 Punarvasu
    "Goat",     # 7 Pushya
    "Cat",      # 8 Ashlesha
    "Rat",      # 9 Magha
    "Rat",      # 10 Purva Phalguni
    "Cow",      # 11 Uttara Phalguni
    "Buffalo",  # 12 Hasta
    "Tiger",    # 13 Chitra
    "Buffalo",  # 14 Swati
    "Tiger",    # 15 Vishakha
    "Deer",     # 16 Anuradha
    "Deer",     # 17 Jyeshtha
    "Dog",      # 18 Mula
    "Monkey",   # 19 Purva Ashadha
    "Monkey",   # 20 Uttara Ashadha
    "Horse",    # 21 Shravana
    "Lion",     # 22 Dhanishta
    "Horse",    # 23 Shatabhisha   (some texts: Elephant; using Horse)
    "Lion",     # 24 Purva Bhadrapada
    "Cow",      # 25 Uttara Bhadrapada
    "Elephant", # 26 Revati
]

# Yoni compatibility: 4=same+friendly, 3=friendly, 2=neutral, 1=unfriendly, 0=enemy
_YONI_FRIENDS = {
    frozenset({"Horse",   "Horse"}):    4,
    frozenset({"Elephant","Elephant"}): 4,
    frozenset({"Goat",    "Goat"}):     4,
    frozenset({"Serpent", "Serpent"}):  4,
    frozenset({"Dog",     "Dog"}):      4,
    frozenset({"Cat",     "Cat"}):      4,
    frozenset({"Rat",     "Rat"}):      4,
    frozenset({"Cow",     "Cow"}):      4,
    frozenset({"Buffalo", "Buffalo"}):  4,
    frozenset({"Tiger",   "Tiger"}):    4,
    frozenset({"Deer",    "Deer"}):     4,
    frozenset({"Monkey",  "Monkey"}):   4,
    frozenset({"Lion",    "Lion"}):     4,
    # Natural pairs (friends – 3 pts)
    frozenset({"Horse",   "Deer"}):     3,
    frozenset({"Elephant","Cow"}):      3,
    frozenset({"Goat",    "Deer"}):     3,
    frozenset({"Monkey",  "Rat"}):      3,
    # Enemy pairs (0 pts)
    frozenset({"Cat",     "Rat"}):      0,
    frozenset({"Dog",     "Deer"}):     0,
    frozenset({"Serpent", "Mongoose"}): 0,
    frozenset({"Lion",    "Elephant"}): 0,
    frozenset({"Tiger",   "Cow"}):      0,
}

# Gana (temperament): 0=Deva, 1=Manushya, 2=Rakshasa
_GANA = [
    0, 2, 0, 0, 1, 2, 0, 0, 2,  # 0-8
    2, 1, 0, 0, 2, 0, 0, 0, 2,  # 9-17
    2, 1, 0, 0, 0, 2, 1, 0, 0,  # 18-26
]

# Nadi (physiological): 0=Adi (Vata), 1=Madhya (Pitta), 2=Antya (Kapha)
_NADI = [
    0, 1, 2, 0, 1, 2, 0, 1, 2,  # 0-8
    0, 1, 2, 0, 1, 2, 0, 1, 2,  # 9-17
    0, 1, 2, 0, 1, 2, 0, 1, 2,  # 18-26
]

# Rajju groups (5 groups by nakshatra triplets)
_RAJJU = [
    1, 2, 3, 4, 5, 4, 3, 2, 1,  # 0-8
    1, 2, 3, 4, 5, 4, 3, 2, 1,  # 9-17
    1, 2, 3, 4, 5, 4, 3, 2, 1,  # 18-26
]

# Vedha (obstacle pairs — nakshatra indices)
_VEDHA_PAIRS = [
    (0, 18), (1, 16), (2, 17), (3, 15), (4, 14),
    (5, 13), (6, 12), (7, 24), (8, 20), (9, 25),
    (10, 11), (19, 21), (22, 26), (23, 25),
]
_VEDHA_SET = {frozenset(p) for p in _VEDHA_PAIRS}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _nak_index(nak_name):
    try:
        return NAKSHATRAS.index(nak_name)
    except ValueError:
        return 0


def _moon_sign(result):
    return result.get("moon_sign", "Aries")


def _moon_nak(result):
    return result.get("moon_nakshatra", "Ashwini")


def _sign_lord(sign):
    return sign_lords.get(sign, "Su")


_NAT_FRIENDS_MATCH = {
    "Su": {"Mo", "Ma", "Ju"},  "Mo": {"Su", "Me"},
    "Ma": {"Su", "Mo", "Ju"},  "Me": {"Su", "Ve"},
    "Ju": {"Su", "Mo", "Ma"},  "Ve": {"Me", "Sa"},
    "Sa": {"Me", "Ve"},
}
_NAT_ENEMIES_MATCH = {
    "Su": {"Ve", "Sa"},  "Mo": set(),   "Ma": {"Me"},
    "Me": {"Mo"},        "Ju": {"Me", "Ve"}, "Ve": {"Su", "Mo"},
    "Sa": {"Su", "Mo", "Ma"},
}


def _planet_relation(p1, p2):
    """'Friend', 'Neutral', or 'Enemy'."""
    if p1 == p2:
        return "Friend"
    if p2 in _NAT_FRIENDS_MATCH.get(p1, set()):
        return "Friend"
    if p2 in _NAT_ENEMIES_MATCH.get(p1, set()):
        return "Enemy"
    return "Neutral"


# ─────────────────────────────────────────────────────────────────────────────
# Individual Kuta checks
# ─────────────────────────────────────────────────────────────────────────────

def _varna(sign_m, sign_f):
    """1 pt if male ≥ female varna grade (male must not be lower grade)."""
    vm = _VARNA.get(sign_m, 3)
    vf = _VARNA.get(sign_f, 3)
    score = 1 if vm <= vf else 0   # lower index = higher varna
    return score, 1, f"Male Varna: {['Brahmin','Kshatriya','Vaishya','Shudra'][vm]}, Female: {['Brahmin','Kshatriya','Vaishya','Shudra'][vf]}"


def _vasya(sign_m, sign_f):
    """2 pts mutual, 1 pt one-way, 0 pt none."""
    def in_same(s1, s2):
        for grp in _VASYA_GROUPS:
            if s1 in grp and s2 in grp:
                return True
        return False
    mf = in_same(sign_m, sign_f)
    if mf:
        return 2, 2, "Mutual Vasya attraction"
    return 0, 2, "No Vasya relationship"


def _tara(nak_m, nak_f):
    """
    3 pts both stars auspicious for each other, 1.5 pt one-way, 0 both inauspicious.
    Tara number = (nak_f - nak_m) % 9 + 1 (from male); same for female.
    Good taras: 1(Janma), 2(Sampat), 4(Kshema), 6(Sadhana) — 1-indexed.
    Bad taras: 3(Vipat), 5(Pratyak), 7(Naidhana).
    """
    _GOOD = {1, 2, 4, 6}
    def tara_ok(from_nak, to_nak):
        t = ((_nak_index(to_nak) - _nak_index(from_nak)) % 27) % 9 + 1
        return t in _GOOD
    m_ok = tara_ok(nak_m, nak_f)
    f_ok = tara_ok(nak_f, nak_m)
    if m_ok and f_ok:
        return 3, 3, "Both stars mutually auspicious (Tara)"
    if m_ok or f_ok:
        return 1, 3, "One-way Tara auspiciousness"
    return 0, 3, "Inauspicious Tara for both"


def _yoni(nak_m, nak_f):
    """0–4 points based on animal compatibility."""
    yi_m = _YONI[_nak_index(nak_m)]
    yi_f = _YONI[_nak_index(nak_f)]
    key = frozenset({yi_m, yi_f})
    score = _YONI_FRIENDS.get(key, 2)   # default neutral
    return score, 4, f"Male Yoni: {yi_m}, Female Yoni: {yi_f}"


def _graha_maitri(sign_m, sign_f):
    """5 pts mutual friend, 4 one friend, 3 neutral, 1 one enemy, 0 mutual enemy."""
    lm = _sign_lord(sign_m)
    lf = _sign_lord(sign_f)
    r_mf = _planet_relation(lm, lf)
    r_fm = _planet_relation(lf, lm)
    if r_mf == "Friend" and r_fm == "Friend":
        return 5, 5, f"{lm}↔{lf}: mutual friends"
    if r_mf == "Friend" or r_fm == "Friend":
        return 4, 5, f"{lm}↔{lf}: one-way friendly"
    if r_mf == "Neutral" and r_fm == "Neutral":
        return 3, 5, f"{lm}↔{lf}: neutral"
    if r_mf == "Enemy" or r_fm == "Enemy":
        return 1, 5, f"{lm}↔{lf}: one is enemy"
    return 0, 5, f"{lm}↔{lf}: mutual enemies"


def _gana(nak_m, nak_f):
    """6 pts same gana, 5 Deva+Manushya, 1 if one Rakshasa, 0 Rakshasa pair."""
    gm = _GANA[_nak_index(nak_m)]
    gf = _GANA[_nak_index(nak_f)]
    gana_names = ["Deva", "Manushya", "Rakshasa"]
    label = f"Male: {gana_names[gm]}, Female: {gana_names[gf]}"
    if gm == gf:
        return 6, 6, f"Same Gana ({gana_names[gm]}): excellent compatibility — {label}"
    if {gm, gf} == {0, 1}:   # Deva + Manushya
        return 5, 6, f"Deva+Manushya: good compatibility — {label}"
    if gm == 2 or gf == 2:
        return 0, 6, f"Rakshasa present: challenging temperament — {label}"
    return 3, 6, f"Moderate Gana match — {label}"


def _bhakoota(sign_m, sign_f):
    """7 pts compatible, 0 inauspicious. Based on Moon sign relative positions."""
    idx_m = zodiac_signs.index(sign_m)
    idx_f = zodiac_signs.index(sign_f)
    diff_mf = (idx_f - idx_m) % 12 + 1   # 1-12 (from male to female)
    diff_fm = (idx_m - idx_f) % 12 + 1   # from female to male
    # Bad Bhakoota: 6/8 (shadashtak), 2/12 (dwirdwadash), 5/9 (navapancham)
    bad_pairs = {(2, 12), (12, 2), (6, 8), (8, 6), (5, 9), (9, 5)}
    pair = (diff_mf, diff_fm)
    if pair in bad_pairs:
        return 0, 7, f"Inauspicious Bhakoota ({diff_mf}/{diff_fm}) — relationship friction"
    return 7, 7, f"Auspicious Bhakoota ({diff_mf}/{diff_fm}) — harmonious Moon signs"


def _nadi(nak_m, nak_f):
    """8 pts different Nadi, 0 pts same Nadi (Nadi Dosha)."""
    nm = _NADI[_nak_index(nak_m)]
    nf = _NADI[_nak_index(nak_f)]
    nadi_names = ["Adi (Vata)", "Madhya (Pitta)", "Antya (Kapha)"]
    if nm == nf:
        return 0, 8, f"Same Nadi ({nadi_names[nm]}) — Nadi Dosha: health/progeny concerns"
    return 8, 8, f"Different Nadis ({nadi_names[nm]} & {nadi_names[nf]}) — excellent"


# ─────────────────────────────────────────────────────────────────────────────
# Additional dosha checks
# ─────────────────────────────────────────────────────────────────────────────

def _rajju(nak_m, nak_f):
    rj_m = _RAJJU[_nak_index(nak_m)]
    rj_f = _RAJJU[_nak_index(nak_f)]
    dosha = rj_m == rj_f
    groups = {1: "Siro (head)", 2: "Kantha (neck)", 3: "Udara (belly)",
              4: "Kati (waist)", 5: "Pada (feet)"}
    if dosha:
        return True, f"Rajju Dosha: both in {groups.get(rj_m,'?')} — longevity concern"
    return False, "No Rajju Dosha"


def _vedha(nak_m, nak_f):
    pair = frozenset({_nak_index(nak_m), _nak_index(nak_f)})
    if pair in _VEDHA_SET:
        return True, f"Vedha Dosha: {nak_m} & {nak_f} obstruct each other"
    return False, "No Vedha Dosha"


def _mahendra(nak_m, nak_f):
    """Auspicious if male star is 4th, 7th, 10th, 13th, 16th, 19th, 22nd, 25th from female."""
    diff = (_nak_index(nak_m) - _nak_index(nak_f)) % 27 + 1
    auspicious = diff in {4, 7, 10, 13, 16, 19, 22, 25}
    if auspicious:
        return True, f"Mahendra: male star is {diff}th from female star — auspicious"
    return False, "Mahendra not formed"


def _stree_deergha(nak_m, nak_f):
    """Good if male star is ≥ 9 nakshatras ahead of female's."""
    diff = (_nak_index(nak_m) - _nak_index(nak_f)) % 27
    if diff >= 9:
        return True, f"Stree Deergha: male star {diff} nakshatras ahead — husband lives long"
    return False, f"Stree Deergha not satisfied (diff={diff}): longevity concern for husband"


def _kuja_dosha(result):
    """Check Mars in houses 1, 2, 4, 7, 8, 12."""
    houses = result["houses"]
    for h, plist in houses.items():
        if "Ma" in plist and h in {1, 2, 4, 7, 8, 12}:
            return True, f"Mangal Dosha: Mars in H{h}"
    return False, "No Mangal Dosha"


# ─────────────────────────────────────────────────────────────────────────────
# Overall rating
# ─────────────────────────────────────────────────────────────────────────────

def _overall_grade(score, has_major_dosha):
    if has_major_dosha and score < 18:
        return "Poor — not recommended without remedies"
    if score >= 28:
        return "Excellent match"
    if score >= 24:
        return "Good match"
    if score >= 18:
        return "Average match — workable with effort"
    return "Below average — challenges expected"


# ─────────────────────────────────────────────────────────────────────────────
# Main function
# ─────────────────────────────────────────────────────────────────────────────

def match_kundalis(result_male, result_female):
    """
    Compare two kundali results and return full compatibility report.

    Returns
    -------
    dict {
      'kutas'        : {kuta_name: {'score', 'max', 'detail'}},
      'total_score'  : int,
      'max_score'    : 36,
      'doshas'       : {dosha_name: {'present': bool, 'detail': str}},
      'grade'        : str,
      'summary'      : str,
    }
    """
    sign_m = _moon_sign(result_male)
    sign_f = _moon_sign(result_female)
    nak_m  = _moon_nak(result_male)
    nak_f  = _moon_nak(result_female)

    kutas = {}
    total = 0

    for name, fn, args in [
        ("Varna",        _varna,        (sign_m, sign_f)),
        ("Vasya",        _vasya,        (sign_m, sign_f)),
        ("Tara",         _tara,         (nak_m, nak_f)),
        ("Yoni",         _yoni,         (nak_m, nak_f)),
        ("Graha Maitri", _graha_maitri, (sign_m, sign_f)),
        ("Gana",         _gana,         (nak_m, nak_f)),
        ("Bhakoota",     _bhakoota,     (sign_m, sign_f)),
        ("Nadi",         _nadi,         (nak_m, nak_f)),
    ]:
        score, max_pts, detail = fn(*args)
        kutas[name] = {"score": score, "max": max_pts, "detail": detail}
        total += score

    # Doshas
    doshas = {}
    rj, rj_d = _rajju(nak_m, nak_f)
    doshas["Rajju"]       = {"present": rj, "detail": rj_d}
    ve, ve_d = _vedha(nak_m, nak_f)
    doshas["Vedha"]       = {"present": ve, "detail": ve_d}
    ma_ok, ma_d = _mahendra(nak_m, nak_f)
    doshas["Mahendra"]    = {"present": not ma_ok, "detail": ma_d}
    sd, sd_d = _stree_deergha(nak_m, nak_f)
    doshas["Stree Deergha"] = {"present": not sd, "detail": sd_d}
    km, km_d = _kuja_dosha(result_male)
    doshas["Kuja (Male)"] = {"present": km, "detail": km_d}
    kf, kf_d = _kuja_dosha(result_female)
    doshas["Kuja (Female)"] = {"present": kf, "detail": kf_d}

    nadi_dosha = kutas["Nadi"]["score"] == 0
    doshas["Nadi Dosha"] = {
        "present": nadi_dosha,
        "detail": "Same Nadi — Nadi Dosha present" if nadi_dosha else "Different Nadi — no Nadi Dosha",
    }

    major_dosha = any(
        doshas[d]["present"]
        for d in ("Rajju", "Vedha", "Nadi Dosha", "Kuja (Male)", "Kuja (Female)")
    )

    grade = _overall_grade(total, major_dosha)

    summary = (
        f"Compatibility Score: {total}/36 — {grade}. "
        f"Male Moon: {sign_m} ({nak_m}), Female Moon: {sign_f} ({nak_f}). "
    )
    active_doshas = [d for d, v in doshas.items() if v["present"]]
    if active_doshas:
        summary += f"Doshas present: {', '.join(active_doshas)}. Remedies advised."
    else:
        summary += "No major doshas. Highly compatible."

    return {
        "kutas":       kutas,
        "total_score": total,
        "max_score":   36,
        "doshas":      doshas,
        "grade":       grade,
        "summary":     summary,
        "male_sign":   sign_m,
        "female_sign": sign_f,
        "male_nak":    nak_m,
        "female_nak":  nak_f,
    }
