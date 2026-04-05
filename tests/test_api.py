"""Tests for the kundali.api GUI-ready layer."""

import pytest
import json
from tests.conftest import MUMBAI_BIRTH


class TestApiCalculate:
    """Test kundali.api.calculate()."""

    @pytest.fixture(scope="class")
    def result(self):
        from kundali.api import calculate
        return calculate(
            MUMBAI_BIRTH["date"],
            MUMBAI_BIRTH["time"],
            MUMBAI_BIRTH["place"],
            gender=MUMBAI_BIRTH["gender"],
            name="Test",
        )

    def test_returns_dict(self, result):
        assert isinstance(result, dict)

    def test_name_stored(self, result):
        assert result.get("name") == "Test"

    def test_has_planets(self, result):
        assert "planets" in result


class TestSerializeResult:
    """Test that serialize_result produces JSON-safe output."""

    @pytest.fixture(scope="class")
    def serialized(self):
        from kundali.api import calculate, serialize_result
        raw = calculate(
            MUMBAI_BIRTH["date"],
            MUMBAI_BIRTH["time"],
            MUMBAI_BIRTH["place"],
            gender=MUMBAI_BIRTH["gender"],
        )
        return serialize_result(raw)

    def test_json_serializable(self, serialized):
        """The output must survive json.dumps without error."""
        dumped = json.dumps(serialized)
        assert isinstance(dumped, str)
        assert len(dumped) > 100

    def test_has_planets_full_names(self, serialized):
        planets = serialized["planets"]
        assert "Sun" in planets
        assert "Moon" in planets
        assert "Jupiter" in planets

    def test_planet_fields(self, serialized):
        sun = serialized["planets"]["Sun"]
        assert "sign" in sun
        assert "deg" in sun
        assert "nakshatra" in sun
        assert "retro" in sun

    def test_has_houses(self, serialized):
        assert "houses" in serialized
        assert len(serialized["houses"]) == 12

    def test_has_yogas_list(self, serialized):
        assert isinstance(serialized["yogas"], list)

    def test_has_vimshottari(self, serialized):
        vim = serialized["vimshottari"]
        assert "starting_lord" in vim
        assert "mahadasas" in vim

    def test_has_transits(self, serialized):
        assert isinstance(serialized["transits"], dict)

    def test_has_panchanga(self, serialized):
        assert isinstance(serialized["panchanga"], dict)


class TestToJson:
    """Test the to_json serializer handles edge cases."""

    def test_none(self):
        from kundali.api import to_json
        assert to_json(None) is None

    def test_bool(self):
        from kundali.api import to_json
        assert to_json(True) is True

    def test_nested_dict(self):
        from kundali.api import to_json
        result = to_json({"a": {"b": [1, 2.5, "c"]}})
        assert result == {"a": {"b": [1, 2.5, "c"]}}

    def test_datetime(self):
        from kundali.api import to_json
        import datetime
        dt = datetime.datetime(2024, 1, 15, 10, 30)
        assert to_json(dt) == "2024-01-15T10:30:00"
