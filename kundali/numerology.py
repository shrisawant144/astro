# numerology.py
"""
Vedic Numerology — Birth Number, Destiny Number, Name Number.

Systems used:
  Birth Number   : sum of birth day digits, reduced to 1–9
  Destiny Number : sum of ALL birth date digits (DD+MM+YYYY), reduced to 1–9
  Name Number    : Chaldean system (letter values 1–8), reduced to 1–9

References: B.V. Raman "Numerology and Your Destiny".
"""

# ─────────────────────────────────────────────────────────────────────────────
# Chaldean letter values (1-8; no 9 assigned directly)
# ─────────────────────────────────────────────────────────────────────────────
_CHALDEAN = {
    "A": 1, "I": 1, "J": 1, "Q": 1, "Y": 1,
    "B": 2, "K": 2, "R": 2,
    "C": 3, "G": 3, "L": 3, "S": 3,
    "D": 4, "M": 4, "T": 4,
    "E": 5, "H": 5, "N": 5, "X": 5,
    "U": 6, "V": 6, "W": 6,
    "O": 7, "Z": 7,
    "F": 8, "P": 8,
}

# Number meanings (1-9)
_MEANINGS = {
    1: ("Sun", "Leadership, independence, originality, courage, strong will."),
    2: ("Moon", "Cooperation, diplomacy, sensitivity, intuition, receptivity."),
    3: ("Jupiter", "Creativity, joy, self-expression, optimism, social charm."),
    4: ("Rahu/Uranus", "Hard work, discipline, practicality, stability, endurance."),
    5: ("Mercury", "Freedom, adaptability, communication, travel, versatility."),
    6: ("Venus", "Harmony, love, responsibility, beauty, domestic warmth."),
    7: ("Ketu/Neptune", "Introspection, spirituality, wisdom, analysis, solitude."),
    8: ("Saturn", "Ambition, power, authority, material mastery, karmic justice."),
    9: ("Mars", "Humanitarianism, completion, courage, generosity, global outlook."),
}

# Lucky days, colors, gems per number
_LUCKY = {
    1: {"days": "Sunday", "color": "Gold/Orange", "gem": "Ruby"},
    2: {"days": "Monday", "color": "White/Silver", "gem": "Pearl/Moonstone"},
    3: {"days": "Thursday", "color": "Yellow", "gem": "Yellow Sapphire"},
    4: {"days": "Saturday/Sunday", "color": "Electric Blue", "gem": "Gomed (Hessonite)"},
    5: {"days": "Wednesday", "color": "Green", "gem": "Emerald"},
    6: {"days": "Friday", "color": "Pink/Blue", "gem": "Diamond/Opal"},
    7: {"days": "Monday", "color": "Violet/White", "gem": "Cat's Eye"},
    8: {"days": "Saturday", "color": "Black/Dark Blue", "gem": "Blue Sapphire"},
    9: {"days": "Tuesday", "color": "Red/Coral", "gem": "Red Coral"},
}


def _digital_root(n):
    """Reduce a positive integer to its digital root (1–9)."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def birth_number(birth_day: int) -> int:
    """
    Birth Number = digital root of the day of birth (1–31).
    Reflects the personality and natural tendencies.
    """
    return _digital_root(birth_day)


def destiny_number(birth_year: int, birth_month: int, birth_day: int) -> int:
    """
    Destiny Number = digital root of (DD + MM + YYYY).
    Reflects the life path and overall karmic purpose.
    """
    total = sum(int(d) for d in f"{birth_day:02d}{birth_month:02d}{birth_year:04d}")
    return _digital_root(total)


def name_number(name: str) -> int:
    """
    Name Number (Chaldean) = digital root of letter values in the name.
    Use full name at birth for best accuracy.
    """
    total = 0
    for ch in name.upper():
        total += _CHALDEAN.get(ch, 0)
    return _digital_root(total) if total > 0 else 0


def calculate_numerology(result, name: str = "") -> dict:
    """
    Calculate all three numerology numbers and their interpretations.

    Parameters
    ----------
    result : dict — kundali result dict
    name   : str  — full birth name (optional, for Name Number)

    Returns
    -------
    dict {
      'birth_number'   : int,
      'destiny_number' : int,
      'name_number'    : int or None,
      'birth_planet'   : str,
      'destiny_planet' : str,
      'birth_meaning'  : str,
      'destiny_meaning': str,
      'name_meaning'   : str or None,
      'lucky_days'     : str,
      'lucky_color'    : str,
      'lucky_gem'      : str,
      'compatibility'  : str,  # birth + destiny number interaction
    }
    """
    y = result.get("birth_year", 2000)
    m = result.get("birth_month", 1)
    d = result.get("birth_day", 1)

    bn = birth_number(d)
    dn = destiny_number(y, m, d)
    nn = name_number(name) if name.strip() else None

    bn_planet, bn_meaning = _MEANINGS.get(bn, ("Unknown", ""))
    dn_planet, dn_meaning = _MEANINGS.get(dn, ("Unknown", ""))
    nn_planet, nn_meaning = _MEANINGS.get(nn, ("Unknown", "")) if nn else (None, None)

    # Compatibility between birth and destiny numbers
    compat_table = {
        frozenset({1, 1}): "Powerful but may need to share control.",
        frozenset({1, 2}): "Leader and diplomat — complementary.",
        frozenset({1, 9}): "Both independent; strong humanitarian streak.",
        frozenset({3, 6}): "Creatively and harmoniously compatible.",
        frozenset({4, 8}): "Practical pair; great material achievement.",
        frozenset({5, 9}): "Freedom-loving adventurers — highly compatible.",
        frozenset({2, 7}): "Intuitive and spiritual duo.",
    }
    compat = compat_table.get(
        frozenset({bn, dn}),
        f"Birth {bn} ({bn_planet}) and Destiny {dn} ({dn_planet}): "
        "work consciously to balance their energies.",
    )

    lucky = _LUCKY.get(bn, {})

    return {
        "birth_number":    bn,
        "destiny_number":  dn,
        "name_number":     nn,
        "birth_planet":    bn_planet,
        "destiny_planet":  dn_planet,
        "name_planet":     nn_planet,
        "birth_meaning":   bn_meaning,
        "destiny_meaning": dn_meaning,
        "name_meaning":    nn_meaning,
        "lucky_days":      lucky.get("days", ""),
        "lucky_color":     lucky.get("color", ""),
        "lucky_gem":       lucky.get("gem", ""),
        "compatibility":   compat,
    }
