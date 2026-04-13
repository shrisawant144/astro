"""
Integration tests for the full kundali calculation pipeline.

Uses seeded geocache (conftest.py) so no network calls are made.
"""

import pytest
from tests.conftest import MUMBAI_BIRTH


class TestCalculateKundali:
    """Test the main calculate_kundali function end-to-end."""

    @pytest.fixture(scope="class")
    def chart(self):
        from kundali.main import calculate_kundali
        return calculate_kundali(
            MUMBAI_BIRTH["date"],
            MUMBAI_BIRTH["time"],
            MUMBAI_BIRTH["place"],
            gender=MUMBAI_BIRTH["gender"],
        )

    def test_returns_dict(self, chart):
        assert isinstance(chart, dict)

    def test_has_lagna(self, chart):
        assert "lagna_sign" in chart
        assert chart["lagna_sign"] in [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]

    def test_has_all_planets(self, chart):
        expected = {"Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"}
        assert expected.issubset(set(chart["planets"].keys()))

    def test_planet_has_required_keys(self, chart):
        for code, pdata in chart["planets"].items():
            assert "sign" in pdata, f"{code} missing 'sign'"
            assert "deg" in pdata, f"{code} missing 'deg'"
            assert "nakshatra" in pdata, f"{code} missing 'nakshatra'"
            assert "full_lon" in pdata, f"{code} missing 'full_lon'"
            assert "retro" in pdata, f"{code} missing 'retro'"

    def test_has_12_houses(self, chart):
        assert len(chart["houses"]) == 12
        for h in range(1, 13):
            assert h in chart["houses"]

    def test_has_moon_data(self, chart):
        assert chart["moon_sign"] is not None
        assert chart["moon_nakshatra"] is not None

    def test_has_vimshottari(self, chart):
        vim = chart["vimshottari"]
        assert "starting_lord" in vim
        assert "mahadasas" in vim
        assert len(vim["mahadasas"]) >= 9  # 9 lords + possible balance period

    def test_has_panchanga(self, chart):
        p = chart["panchanga"]
        assert "tithi" in p
        assert "vara" in p
        assert "yoga" in p
        assert "karana" in p

    def test_has_navamsa(self, chart):
        assert "navamsa" in chart
        assert "Su" in chart["navamsa"]

    def test_has_yogas(self, chart):
        assert "yogas" in chart
        assert isinstance(chart["yogas"], list)

    def test_has_problems(self, chart):
        assert "problems" in chart
        assert isinstance(chart["problems"], list)

    def test_has_transits(self, chart):
        assert "transits" in chart
        assert len(chart["transits"]) >= 7  # At least 7 planets

    def test_has_jaimini(self, chart):
        assert "jaimini" in chart
        assert "atmakaraka" in chart["jaimini"]

    def test_has_final_analysis(self, chart):
        assert "final_analysis" in chart
        assert isinstance(chart["final_analysis"], str)
        assert len(chart["final_analysis"]) > 50

    def test_birth_info_preserved(self, chart):
        assert chart["birth_date"] == MUMBAI_BIRTH["date"]
        assert chart["birth_time"] == MUMBAI_BIRTH["time"]
        assert chart["birth_place"] == MUMBAI_BIRTH["place"]
        assert chart["gender"] == MUMBAI_BIRTH["gender"]

    def test_has_input_quality_metadata(self, chart):
        assert isinstance(chart.get("input_quality"), dict)
        assert chart["input_quality"]["label"] in {"Strong", "Good", "Moderate", "Needs Review"}
        assert isinstance(chart["input_quality"]["warnings"], list)

    def test_has_rectification_metadata_placeholder(self, chart):
        assert "birth_time_rectification" in chart
        assert isinstance(chart["birth_time_rectification"], dict)

    def test_supports_precise_coordinates_and_timezone(self):
        from kundali.main import calculate_kundali

        chart = calculate_kundali(
            "1990-05-15",
            "08:30",
            "",
            gender="Male",
            latitude=19.0760,
            longitude=72.8777,
            timezone_name="Asia/Kolkata",
        )
        assert chart["location_source"] == "coordinates"
        assert chart["timezone_source"] == "manual"
        assert chart["timezone"] == "Asia/Kolkata"
        assert chart["input_quality"]["birth_place_specificity"] == "coordinates"


class TestInputValidation:
    """Test that calculate_kundali rejects bad inputs clearly."""

    def test_bad_date_format(self):
        from kundali.main import calculate_kundali
        with pytest.raises(ValueError, match="Invalid date format"):
            calculate_kundali("15-05-1990", "08:30", "Mumbai, India")

    def test_bad_time_format(self):
        from kundali.main import calculate_kundali
        with pytest.raises(ValueError, match="Invalid time format"):
            calculate_kundali("1990-05-15", "8.30am", "Mumbai, India")

    def test_empty_place(self):
        from kundali.main import calculate_kundali
        with pytest.raises(ValueError, match="Birth place cannot be empty"):
            calculate_kundali("1990-05-15", "08:30", "")

    def test_bad_gender(self):
        from kundali.main import calculate_kundali
        with pytest.raises(ValueError, match="Gender must be"):
            calculate_kundali("1990-05-15", "08:30", "Mumbai, India", gender="Other")

    def test_bad_ayanamsa(self):
        from kundali.main import calculate_kundali
        with pytest.raises(ValueError, match="Unknown ayanamsa"):
            calculate_kundali("1990-05-15", "08:30", "Mumbai, India", ayanamsa_name="Foobar")

    def test_month_out_of_range(self):
        from kundali.main import calculate_kundali
        with pytest.raises(ValueError, match="Month"):
            calculate_kundali("1990-13-15", "08:30", "Mumbai, India")

    def test_hour_out_of_range(self):
        from kundali.main import calculate_kundali
        with pytest.raises(ValueError, match="Hour"):
            calculate_kundali("1990-05-15", "25:30", "Mumbai, India")


class TestRectificationIntegration:
    """Test optional rectification wiring in the main calculator."""

    @staticmethod
    def _fake_rectification(result, events, **kwargs):
        return {
            "original_birth_time": "1990-05-15 08:30",
            "corrected_birth_time": "1990-05-15 08:34",
            "corrected_birth_time_input": "08:34",
            "corrected_birth_datetime_local": "1990-05-15T08:34:00+05:30",
            "corrected_birth_datetime_utc": "1990-05-15T03:04:00+00:00",
            "offset_minutes": 4,
            "raw_score": 28,
            "confidence_score": 82,
            "confidence_label": "High",
            "score_margin": 10,
            "events_used": len(events),
            "search_window_minutes": 60,
            "step_minutes": 2,
            "applied": False,
            "applied_reason": "",
        }

    def test_rectification_analysis_attached(self, monkeypatch):
        import kundali.main as main_mod

        monkeypatch.setattr(main_mod, "rectify_birth_time", TestRectificationIntegration._fake_rectification)
        result = main_mod.calculate_kundali(
            MUMBAI_BIRTH["date"],
            MUMBAI_BIRTH["time"],
            MUMBAI_BIRTH["place"],
            gender=MUMBAI_BIRTH["gender"],
            rectification_events=[{"house": 10, "planets": ["Saturn"]}],
            apply_rectification=False,
        )

        assert result["birth_time"] == MUMBAI_BIRTH["time"]
        assert result["birth_time_rectification"]["confidence_score"] == 82
        assert result["birth_time_rectification"]["applied"] is False

    def test_rectification_can_auto_apply(self, monkeypatch):
        import kundali.main as main_mod

        monkeypatch.setattr(main_mod, "rectify_birth_time", TestRectificationIntegration._fake_rectification)
        result = main_mod.calculate_kundali(
            MUMBAI_BIRTH["date"],
            MUMBAI_BIRTH["time"],
            MUMBAI_BIRTH["place"],
            gender=MUMBAI_BIRTH["gender"],
            rectification_events=[{"house": 10, "planets": ["Saturn"]}],
            apply_rectification=True,
            rectification_min_confidence=70,
        )

        assert result["birth_time"] == "08:34"
        assert result["birth_time_original_input"] == MUMBAI_BIRTH["time"]
        assert result["birth_time_rectification"]["applied"] is True
