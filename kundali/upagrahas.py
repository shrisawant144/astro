# upagrahas.py
"""
Upagrahas (shadow / sub-planets) for Vedic astrology.

Implemented:
  Gulika (Mandi)   — Saturn's day portion (most important)
  Yamghantaka      — Jupiter's portion
  Ardhaprahara     — Mars portion  (some texts call it Kala)
  Kaala            — Saturn-related
  Dhuma            — Sun + 133°20' (4s13°20')
  Vyatipata        — 360° − (Sun + Moon)
  Parivesha        — Vyatipata + 180°
  Indrachapa       — 360° − Parivesha   (same as Dhuma + 180° − 6°40')
  Upaketu          — Dhuma + 180°

All shadow planets that use day-portion math (Gulika etc.) require:
  birth_jd, lat, lon, vara_idx (weekday 0=Sun…6=Sat).
"""

import math
import swisseph as swe
from .constants import zodiac_signs
from .utils import get_sign


# ---------------------------------------------------------------------------
# Day-portion helpers
# ---------------------------------------------------------------------------

# Gulika day-part number (1-indexed) for each vara (0=Sun…6=Sat)
_GULIKA_DAY_PART = {0: 6, 1: 4, 2: 2, 3: 7, 4: 5, 5: 3, 6: 1}
# Yamghantaka day-part
_YAMGHANTAKA_DAY_PART = {0: 4, 1: 2, 2: 7, 3: 5, 4: 3, 5: 1, 6: 6}
# Ardhaprahara (Kala) day-part
_ARDHAPRAHARA_DAY_PART = {0: 1, 1: 6, 2: 4, 3: 2, 4: 7, 5: 5, 6: 3}
# Kaala day-part
_KAALA_DAY_PART = {0: 2, 1: 7, 2: 5, 3: 3, 4: 1, 5: 6, 6: 4}


def _get_sunrise_sunset(birth_jd, lat, lon_geo):
    """Return (sunrise_jd, sunset_jd) for the birth date."""
    try:
        sr_res, sr_tret = swe.rise_trans(
            birth_jd - 1,
            swe.SUN,
            swe.CALC_RISE,
            (lon_geo, lat, 0),
            0,
            0,
            swe.FLG_SWIEPH,
        )
        ss_res, ss_tret = swe.rise_trans(
            birth_jd - 1,
            swe.SUN,
            swe.CALC_SET,
            (lon_geo, lat, 0),
            0,
            0,
            swe.FLG_SWIEPH,
        )
        sunrise_jd = sr_tret[0] if sr_res == 0 and sr_tret else birth_jd - 0.25
        sunset_jd = ss_tret[0] if ss_res == 0 and ss_tret else birth_jd + 0.25
    except Exception:
        sunrise_jd = birth_jd - 0.25
        sunset_jd = birth_jd + 0.25
    return sunrise_jd, sunset_jd


def _lagna_at_jd(jd, lat, lon_geo):
    """Return Ascendant longitude at a given JD and geographic location."""
    try:
        house_data = swe.houses_ex(jd, lat, lon_geo, b"W", swe.FLG_SIDEREAL)
        return house_data[1][0]  # ascmc[0] = Lagna
    except Exception:
        return 0.0


def _day_portion_jd(sunrise_jd, sunset_jd, part_num):
    """JD at the *start* of the given day portion (1-indexed, 8 parts)."""
    day_len = sunset_jd - sunrise_jd
    portion_len = day_len / 8.0
    return sunrise_jd + (part_num - 1) * portion_len


def _upagraha_from_day_part(part_map, birth_jd, lat, lon_geo, vara_idx=None):
    """
    Generic: find which day part this upagraha occupies, compute its Lagna.
    Returns (sign_str, deg_in_sign_float).
    """
    sunrise_jd, sunset_jd = _get_sunrise_sunset(birth_jd, lat, lon_geo)
    weekday = vara_idx if vara_idx is not None else int((birth_jd + 0.5) % 7)
    part = part_map.get(weekday, 1)
    portion_jd = _day_portion_jd(sunrise_jd, sunset_jd, part)
    asc_lon = _lagna_at_jd(portion_jd, lat, lon_geo)
    sign = get_sign(asc_lon)
    deg = round(asc_lon % 30, 2)
    return sign, deg, round(asc_lon, 4)


# ---------------------------------------------------------------------------
# Sun-based shadow planets (simple longitude arithmetic)
# ---------------------------------------------------------------------------


def _dhuma(sun_lon):
    """Dhuma = Sun + 133°20'."""
    return (sun_lon + 133.333) % 360


def _vyatipata(sun_lon, moon_lon):
    """Vyatipata = 360° − (Sun + Moon)."""
    return (360 - (sun_lon + moon_lon)) % 360


def _parivesha(sun_lon, moon_lon):
    """Parivesha = Vyatipata + 180°."""
    return (_vyatipata(sun_lon, moon_lon) + 180) % 360


def _indrachapa(sun_lon, moon_lon):
    """Indrachapa = Parivesha + 180° (= Vyatipata)... actually = 360 − Parivesha."""
    return (360 - _parivesha(sun_lon, moon_lon)) % 360


def _upaketu(sun_lon):
    """Upaketu = Dhuma + 180°."""
    return (_dhuma(sun_lon) + 180) % 360


def _lon_to_sign_deg(lon):
    sign = get_sign(lon)
    deg = round(lon % 30, 2)
    return sign, deg


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------


def calculate_upagrahas(result):
    """
    Calculate all upagrahas.

    Parameters
    ----------
    result : dict  — kundali result dict

    Returns
    -------
    dict {
      'Gulika'      : {'sign':str, 'deg':float, 'full_lon':float},
      'Yamghantaka' : {...},
      'Ardhaprahara': {...},
      'Kaala'       : {...},
      'Dhuma'       : {'sign':str, 'deg':float, 'full_lon':float},
      'Vyatipata'   : {...},
      'Parivesha'   : {...},
      'Indrachapa'  : {...},
      'Upaketu'     : {...},
    }
    """
    birth_jd = result["birth_jd"]
    lat = result.get("lat", 0.0)
    lon_geo = result.get("lon", 0.0)
    vara_idx = result.get("birth_vara_idx")
    sun_lon = result["planets"]["Su"]["full_lon"]
    moon_lon = result["planets"]["Mo"]["full_lon"]

    out = {}

    # Day-portion upagrahas
    for name, part_map in [
        ("Gulika", _GULIKA_DAY_PART),
        ("Yamghantaka", _YAMGHANTAKA_DAY_PART),
        ("Ardhaprahara", _ARDHAPRAHARA_DAY_PART),
        ("Kaala", _KAALA_DAY_PART),
    ]:
        sign, deg, full_lon = _upagraha_from_day_part(
            part_map, birth_jd, lat, lon_geo, vara_idx
        )
        out[name] = {"sign": sign, "deg": deg, "full_lon": full_lon}

    # Sun/Moon arithmetic upagrahas
    for name, lon in [
        ("Dhuma", _dhuma(sun_lon)),
        ("Vyatipata", _vyatipata(sun_lon, moon_lon)),
        ("Parivesha", _parivesha(sun_lon, moon_lon)),
        ("Indrachapa", _indrachapa(sun_lon, moon_lon)),
        ("Upaketu", _upaketu(sun_lon)),
    ]:
        sign, deg = _lon_to_sign_deg(lon)
        out[name] = {"sign": sign, "deg": deg, "full_lon": round(lon, 4)}

    return out
