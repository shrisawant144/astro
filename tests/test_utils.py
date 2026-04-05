"""Tests for kundali.utils — pure calculation functions (no network)."""

import pytest
from kundali.utils import (
    get_sign,
    get_nakshatra,
    get_nakshatra_progress,
    get_dignity,
    is_retrograde,
    get_house_from_sign,
    get_navamsa_sign_and_deg,
    get_d7_sign_and_deg,
    get_d10_sign_and_deg,
    get_d2_sign_and_deg,
    get_d60_sign_and_deg,
    has_aspect,
    check_combustion,
)


# ---------------------------------------------------------------------------
# get_sign
# ---------------------------------------------------------------------------

class TestGetSign:
    def test_aries_start(self):
        assert get_sign(0.0) == "Aries"

    def test_aries_end(self):
        assert get_sign(29.99) == "Aries"

    def test_taurus(self):
        assert get_sign(30.0) == "Taurus"

    def test_pisces(self):
        assert get_sign(350.0) == "Pisces"

    def test_wrap_360(self):
        assert get_sign(360.0) == "Aries"

    def test_mid_sign(self):
        assert get_sign(135.0) == "Leo"  # 135/30 = 4.5 → index 4 = Leo


# ---------------------------------------------------------------------------
# get_nakshatra
# ---------------------------------------------------------------------------

class TestGetNakshatra:
    def test_ashwini(self):
        assert get_nakshatra(0.0) == "Ashwini"

    def test_bharani(self):
        # Each nakshatra spans 360/27 ≈ 13.333°
        assert get_nakshatra(14.0) == "Bharani"

    def test_revati(self):
        assert get_nakshatra(359.0) == "Revati"


# ---------------------------------------------------------------------------
# get_nakshatra_progress
# ---------------------------------------------------------------------------

class TestGetNakshatraProgress:
    def test_start(self):
        assert get_nakshatra_progress(0.0) == pytest.approx(0.0, abs=0.01)

    def test_mid(self):
        nak_span = 360 / 27
        assert get_nakshatra_progress(nak_span / 2) == pytest.approx(0.5, abs=0.01)


# ---------------------------------------------------------------------------
# get_dignity
# ---------------------------------------------------------------------------

class TestGetDignity:
    def test_sun_exalted_aries(self):
        assert get_dignity("Su", "Aries") == "Exalt"

    def test_sun_own_leo(self):
        assert get_dignity("Su", "Leo") == "Own"

    def test_sun_debilitated_libra(self):
        assert get_dignity("Su", "Libra") == "Debilitated"

    def test_jupiter_friend_aries(self):
        # Aries lord is Mars, Mars is friend of Jupiter
        assert get_dignity("Ju", "Aries") == "Friend"

    def test_rahu_empty(self):
        assert get_dignity("Ra", "Aries") == ""


# ---------------------------------------------------------------------------
# is_retrograde
# ---------------------------------------------------------------------------

class TestIsRetrograde:
    def test_negative_speed(self):
        assert is_retrograde(-0.5) is True

    def test_positive_speed(self):
        assert is_retrograde(1.2) is False

    def test_zero_speed(self):
        assert is_retrograde(0.0) is False


# ---------------------------------------------------------------------------
# get_house_from_sign
# ---------------------------------------------------------------------------

class TestGetHouseFromSign:
    def test_same_sign_house_1(self):
        assert get_house_from_sign(0, 0) == 1

    def test_opposite_house_7(self):
        assert get_house_from_sign(0, 6) == 7

    def test_wrap_around(self):
        assert get_house_from_sign(10, 2) == 5  # (2-10+12)%12+1 = 5


# ---------------------------------------------------------------------------
# Divisional charts
# ---------------------------------------------------------------------------

class TestDivisionalCharts:
    def test_navamsa_aries_start(self):
        sign, deg = get_navamsa_sign_and_deg(0.0)
        assert sign == "Aries"

    def test_navamsa_returns_tuple(self):
        result = get_navamsa_sign_and_deg(45.0)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_d7_returns_tuple(self):
        result = get_d7_sign_and_deg(100.0)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_d10_returns_tuple(self):
        result = get_d10_sign_and_deg(200.0)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_d2_hora(self):
        sign, deg = get_d2_sign_and_deg(10.0)
        assert sign in [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]

    def test_d60_returns_valid_sign(self):
        sign, deg = get_d60_sign_and_deg(123.456)
        assert sign in [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]


# ---------------------------------------------------------------------------
# Aspects
# ---------------------------------------------------------------------------

class TestHasAspect:
    def test_all_planets_7th_aspect(self):
        # diff = (8-1)%12 = 7 → Sun aspects 7th house
        assert has_aspect(1, 8, "Su") is True

    def test_mars_4th_aspect(self):
        assert has_aspect(1, 5, "Ma") is True  # diff=(5-1)%12=4

    def test_mars_8th_aspect(self):
        assert has_aspect(1, 9, "Ma") is True  # diff=(9-1)%12=8

    def test_jupiter_5th_aspect(self):
        assert has_aspect(1, 6, "Ju") is True  # diff=5

    def test_jupiter_9th_aspect(self):
        assert has_aspect(1, 10, "Ju") is True  # diff=9

    def test_saturn_3rd_aspect(self):
        assert has_aspect(1, 4, "Sa") is True  # diff=3

    def test_saturn_10th_aspect(self):
        assert has_aspect(1, 11, "Sa") is True  # diff=10


# ---------------------------------------------------------------------------
# Combustion
# ---------------------------------------------------------------------------

class TestCheckCombustion:
    def test_mercury_combust_direct(self):
        # Mercury combust within 14° direct
        assert check_combustion("Me", 100.0, 105.0, False) is True

    def test_mercury_not_combust(self):
        assert check_combustion("Me", 100.0, 120.0, False) is False

    def test_sun_not_combustible(self):
        assert check_combustion("Su", 100.0, 100.0, False) is False

    def test_rahu_not_combustible(self):
        assert check_combustion("Ra", 100.0, 100.0, False) is False
