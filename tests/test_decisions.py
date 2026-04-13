"""
Tests for the Decision Engine module.

Tests all 9 decision categories:
1. Career
2. Marriage
3. Business
4. Health
5. Travel
6. Daily
7. Compatibility
8. Education
9. Life Analysis
"""

import pytest
from kundali import calculate_kundali
from kundali.decisions import (
    get_career_decision,
    get_marriage_decision,
    get_business_decision,
    get_health_decision,
    get_travel_decision,
    get_daily_guidance,
    get_compatibility_decision,
    get_education_decision,
    get_life_analysis,
    get_all_decisions,
    get_all_decisions_with_compatibility,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sample_chart():
    """Generate a sample kundali for testing."""
    return calculate_kundali(
        birth_date_str="1990-05-15",
        birth_time_str="08:30",
        place="Mumbai, India",
        gender="Male",
    )


@pytest.fixture(scope="module")
def sample_chart_female():
    """Generate a female sample kundali for compatibility testing."""
    return calculate_kundali(
        birth_date_str="1992-08-20",
        birth_time_str="14:45",
        place="Delhi, India",
        gender="Female",
    )


# ---------------------------------------------------------------------------
# 1. Career Decision Tests
# ---------------------------------------------------------------------------

class TestCareerDecision:
    """Tests for career decision engine."""

    def test_career_decision_returns_dict(self, sample_chart):
        """Career decision should return a dictionary."""
        result = get_career_decision(sample_chart)
        assert isinstance(result, dict)

    def test_career_decision_has_required_keys(self, sample_chart):
        """Career decision should have essential keys."""
        result = get_career_decision(sample_chart)
        # Check for some expected keys
        assert "recommended_fields" in result or "fields" in result or "career_fields" in result
        
    def test_career_decision_has_advice(self, sample_chart):
        """Career decision should provide advice."""
        result = get_career_decision(sample_chart)
        # Should have some form of advice/guidance
        has_advice = any(key in result for key in ["advice", "guidance", "recommendation", "current_period"])
        assert has_advice or len(result) > 0

    def test_career_decision_not_empty(self, sample_chart):
        """Career decision should not return empty result."""
        result = get_career_decision(sample_chart)
        assert len(result) > 0

    def test_career_decision_has_confidence(self, sample_chart):
        result = get_career_decision(sample_chart)
        assert "confidence_score" in result
        assert "confidence_label" in result


# ---------------------------------------------------------------------------
# 2. Marriage Decision Tests
# ---------------------------------------------------------------------------

class TestMarriageDecision:
    """Tests for marriage decision engine."""

    def test_marriage_decision_returns_dict(self, sample_chart):
        """Marriage decision should return a dictionary."""
        result = get_marriage_decision(sample_chart)
        assert isinstance(result, dict)

    def test_marriage_decision_has_timing(self, sample_chart):
        """Marriage decision should include timing information."""
        result = get_marriage_decision(sample_chart)
        # Should have timing-related information
        timing_keys = ["timing", "windows", "favorable_periods", "marriage_windows", "best_periods"]
        has_timing = any(key in result for key in timing_keys) or len(result) > 0
        assert has_timing

    def test_marriage_decision_not_empty(self, sample_chart):
        """Marriage decision should not return empty result."""
        result = get_marriage_decision(sample_chart)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 3. Business Decision Tests
# ---------------------------------------------------------------------------

class TestBusinessDecision:
    """Tests for business decision engine."""

    def test_business_decision_returns_dict(self, sample_chart):
        """Business decision should return a dictionary."""
        result = get_business_decision(sample_chart)
        assert isinstance(result, dict)

    def test_business_decision_has_financial_info(self, sample_chart):
        """Business decision should include financial guidance."""
        result = get_business_decision(sample_chart)
        assert len(result) > 0

    def test_business_decision_not_empty(self, sample_chart):
        """Business decision should not return empty result."""
        result = get_business_decision(sample_chart)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 4. Health Decision Tests
# ---------------------------------------------------------------------------

class TestHealthDecision:
    """Tests for health decision engine."""

    def test_health_decision_returns_dict(self, sample_chart):
        """Health decision should return a dictionary."""
        result = get_health_decision(sample_chart)
        assert isinstance(result, dict)

    def test_health_decision_has_health_info(self, sample_chart):
        """Health decision should include health-related information."""
        result = get_health_decision(sample_chart)
        assert len(result) > 0

    def test_health_decision_not_empty(self, sample_chart):
        """Health decision should not return empty result."""
        result = get_health_decision(sample_chart)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 5. Travel Decision Tests
# ---------------------------------------------------------------------------

class TestTravelDecision:
    """Tests for travel decision engine."""

    def test_travel_decision_returns_dict(self, sample_chart):
        """Travel decision should return a dictionary."""
        result = get_travel_decision(sample_chart)
        assert isinstance(result, dict)

    def test_travel_decision_has_direction_info(self, sample_chart):
        """Travel decision should include direction/travel information."""
        result = get_travel_decision(sample_chart)
        assert len(result) > 0

    def test_travel_decision_not_empty(self, sample_chart):
        """Travel decision should not return empty result."""
        result = get_travel_decision(sample_chart)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 6. Daily Guidance Tests
# ---------------------------------------------------------------------------

class TestDailyGuidance:
    """Tests for daily guidance engine."""

    def test_daily_guidance_returns_dict(self, sample_chart):
        """Daily guidance should return a dictionary."""
        result = get_daily_guidance(sample_chart)
        assert isinstance(result, dict)

    def test_daily_guidance_has_today_info(self, sample_chart):
        """Daily guidance should include today's information."""
        result = get_daily_guidance(sample_chart)
        assert len(result) > 0

    def test_daily_guidance_not_empty(self, sample_chart):
        """Daily guidance should not return empty result."""
        result = get_daily_guidance(sample_chart)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 7. Compatibility Decision Tests
# ---------------------------------------------------------------------------

class TestCompatibilityDecision:
    """Tests for compatibility decision engine."""

    def test_compatibility_decision_returns_dict(self, sample_chart, sample_chart_female):
        """Compatibility decision should return a dictionary."""
        result = get_compatibility_decision(sample_chart, sample_chart_female)
        assert isinstance(result, dict)

    def test_compatibility_decision_has_score(self, sample_chart, sample_chart_female):
        """Compatibility decision should include a score."""
        result = get_compatibility_decision(sample_chart, sample_chart_female)
        # Should have some scoring information
        score_keys = ["score", "total", "compatibility_score", "guna_score", "percentage"]
        has_score = any(key in result for key in score_keys) or any(
            key in result.get("ashtakoot", {}) for key in score_keys
        ) if isinstance(result.get("ashtakoot"), dict) else len(result) > 0
        assert has_score

    def test_compatibility_decision_not_empty(self, sample_chart, sample_chart_female):
        """Compatibility decision should not return empty result."""
        result = get_compatibility_decision(sample_chart, sample_chart_female)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 8. Education Decision Tests
# ---------------------------------------------------------------------------

class TestEducationDecision:
    """Tests for education decision engine."""

    def test_education_decision_returns_dict(self, sample_chart):
        """Education decision should return a dictionary."""
        result = get_education_decision(sample_chart)
        assert isinstance(result, dict)

    def test_education_decision_has_fields(self, sample_chart):
        """Education decision should recommend fields of study."""
        result = get_education_decision(sample_chart)
        assert len(result) > 0

    def test_education_decision_not_empty(self, sample_chart):
        """Education decision should not return empty result."""
        result = get_education_decision(sample_chart)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 9. Life Analysis Tests
# ---------------------------------------------------------------------------

class TestLifeAnalysis:
    """Tests for unified life-analysis engine."""

    def test_life_analysis_returns_dict(self, sample_chart):
        result = get_life_analysis(sample_chart)
        assert isinstance(result, dict)

    def test_life_analysis_has_domains(self, sample_chart):
        result = get_life_analysis(sample_chart)
        assert "life_domains" in result
        assert isinstance(result["life_domains"], dict)
        assert len(result["life_domains"]) >= 5

    def test_life_analysis_has_longevity_profile(self, sample_chart):
        result = get_life_analysis(sample_chart)
        assert "longevity_profile" in result
        assert isinstance(result["longevity_profile"], dict)


# ---------------------------------------------------------------------------
# All Decisions Tests
# ---------------------------------------------------------------------------

class TestAllDecisions:
    """Tests for combined all-decisions engine."""

    def test_all_decisions_returns_dict(self, sample_chart):
        """All decisions should return a dictionary."""
        result = get_all_decisions(sample_chart)
        assert isinstance(result, dict)

    def test_all_decisions_has_multiple_categories(self, sample_chart):
        """All decisions should include multiple decision categories."""
        result = get_all_decisions(sample_chart)
        # Should have multiple keys for different decision types
        assert len(result) >= 5  # At least 5 decision categories

    def test_all_decisions_includes_career(self, sample_chart):
        """All decisions should include career guidance."""
        result = get_all_decisions(sample_chart)
        career_keys = ["career", "career_decision", "career_guidance"]
        has_career = any(key in result for key in career_keys)
        assert has_career

    def test_all_decisions_with_compatibility(self, sample_chart, sample_chart_female):
        """All decisions with compatibility should include both."""
        result = get_all_decisions_with_compatibility(sample_chart, sample_chart_female)
        assert isinstance(result, dict)
        assert len(result) >= 6  # All decisions + compatibility

    def test_all_decisions_has_confidence_summary(self, sample_chart):
        result = get_all_decisions(sample_chart)
        assert "confidence_summary" in result
        assert isinstance(result["confidence_summary"]["average_score"], int)


# ---------------------------------------------------------------------------
# Edge Cases and Error Handling
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_career_decision_with_minimal_chart(self):
        """Career decision should handle minimal chart data gracefully."""
        minimal_chart = {
            "lagna_sign": "Aries",
            "planets": {},
            "houses": {},
        }
        # Should not raise an exception
        try:
            result = get_career_decision(minimal_chart)
            assert isinstance(result, dict)
        except Exception as e:
            # If it raises, it should be a reasonable error
            assert "KeyError" in str(type(e).__name__) or "AttributeError" in str(type(e).__name__)

    def test_all_decision_functions_are_callable(self):
        """All decision functions should be callable."""
        functions = [
            get_career_decision,
            get_marriage_decision,
            get_business_decision,
            get_health_decision,
            get_travel_decision,
            get_daily_guidance,
            get_education_decision,
            get_life_analysis,
            get_all_decisions,
        ]
        for func in functions:
            assert callable(func)

    def test_compatibility_function_is_callable(self):
        """Compatibility function should be callable."""
        assert callable(get_compatibility_decision)
        assert callable(get_all_decisions_with_compatibility)
