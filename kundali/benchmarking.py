"""
Benchmarking and backtesting helpers for the kundali engine.

This module lets you score the engine against real cases with explicit
expectations so future rule changes can be measured instead of guessed.
"""

import json

from .decisions import get_all_decisions
from .main import calculate_kundali


def _get_by_path(payload, path):
    current = payload
    for part in str(path or "").split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _evaluate_expectation(actual, expectation):
    if "equals" in expectation:
        expected = expectation["equals"]
        passed = actual == expected
        detail = f"expected {expected!r}, got {actual!r}"
    elif "in" in expectation:
        expected = list(expectation.get("in", []))
        passed = actual in expected
        detail = f"expected one of {expected!r}, got {actual!r}"
    elif "contains" in expectation:
        expected = expectation["contains"]
        if isinstance(actual, (list, tuple, set)):
            passed = expected in actual
        else:
            passed = str(expected) in str(actual or "")
        detail = f"expected {expected!r} to be present in {actual!r}"
    elif "contains_any" in expectation:
        expected = list(expectation.get("contains_any", []))
        if isinstance(actual, (list, tuple, set)):
            passed = any(item in actual for item in expected)
        else:
            actual_text = str(actual or "")
            passed = any(str(item) in actual_text for item in expected)
        detail = f"expected one of {expected!r} inside {actual!r}"
    elif "min" in expectation:
        expected = expectation["min"]
        passed = actual is not None and actual >= expected
        detail = f"expected >= {expected!r}, got {actual!r}"
    elif "max" in expectation:
        expected = expectation["max"]
        passed = actual is not None and actual <= expected
        detail = f"expected <= {expected!r}, got {actual!r}"
    elif "len_at_least" in expectation:
        expected = int(expectation["len_at_least"])
        actual_len = len(actual) if actual is not None and hasattr(actual, "__len__") else 0
        passed = actual is not None and hasattr(actual, "__len__") and actual_len >= expected
        detail = f"expected length >= {expected}, got {actual_len}"
    elif "len_at_most" in expectation:
        expected = int(expectation["len_at_most"])
        actual_len = len(actual) if actual is not None and hasattr(actual, "__len__") else 0
        passed = actual is not None and hasattr(actual, "__len__") and actual_len <= expected
        detail = f"expected length <= {expected}, got {actual_len}"
    elif expectation.get("truthy") is True:
        passed = bool(actual)
        detail = f"expected truthy value, got {actual!r}"
    elif expectation.get("truthy") is False:
        passed = not bool(actual)
        detail = f"expected falsy value, got {actual!r}"
    else:
        raise ValueError(
            "Expectation must include one of: equals, in, contains, contains_any, min, max, len_at_least, len_at_most, truthy"
        )

    return {
        "passed": passed,
        "actual": actual,
        "rule": {
            key: value
            for key, value in expectation.items()
            if key not in {"path", "label"}
        },
        "detail": detail,
    }


def evaluate_benchmark_case(case):
    """Run a single benchmark case and return scored results."""
    birth = dict(case.get("birth", {}))
    expectations = list(case.get("expectations", []))
    if not expectations:
        raise ValueError("Benchmark case must include at least one expectation.")

    chart = calculate_kundali(
        birth.get("date"),
        birth.get("time"),
        birth.get("place", ""),
        gender=birth.get("gender", "Male"),
        ayanamsa_name=birth.get("ayanamsa", "Lahiri"),
        name=birth.get("name", "benchmark"),
        rectification_events=birth.get("rectification_events"),
        apply_rectification=birth.get("apply_rectification", False),
        rectification_min_confidence=birth.get("rectification_min_confidence", 75),
        latitude=birth.get("latitude"),
        longitude=birth.get("longitude"),
        timezone_name=birth.get("timezone"),
    )
    decisions_bundle = get_all_decisions(chart)
    payload = {
        "chart": chart,
        "result": chart,
        "decisions": decisions_bundle,
        "confidence_summary": decisions_bundle.get("confidence_summary", {}),
        "input_quality": chart.get("input_quality", {}),
        "rectification": chart.get("birth_time_rectification", {}),
    }

    evaluations = []
    passed = 0
    for expectation in expectations:
        path = expectation.get("path")
        if not path:
            raise ValueError("Each expectation requires a 'path'.")
        actual = _get_by_path(payload, path)
        evaluation = _evaluate_expectation(actual, expectation)
        evaluation["path"] = path
        evaluation["label"] = expectation.get("label") or path
        evaluations.append(evaluation)
        if evaluation["passed"]:
            passed += 1

    total = len(evaluations)
    score = int(round((passed / total) * 100)) if total else 0
    return {
        "case_id": case.get("id", "unnamed_case"),
        "title": case.get("title", case.get("id", "Unnamed Case")),
        "passed_expectations": passed,
        "total_expectations": total,
        "score": score,
        "status": "PASS" if passed == total else "PARTIAL" if passed > 0 else "FAIL",
        "evaluations": evaluations,
        "input_quality": chart.get("input_quality", {}),
        "decision_confidence": decisions_bundle.get("confidence_summary", {}),
    }


def run_benchmark_suite(cases):
    """Run multiple benchmark cases and return an aggregate summary."""
    case_results = [evaluate_benchmark_case(case) for case in cases]
    total_cases = len(case_results)
    average_score = (
        int(round(sum(item["score"] for item in case_results) / total_cases))
        if total_cases
        else 0
    )
    passed_cases = sum(1 for item in case_results if item["status"] == "PASS")

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "average_score": average_score,
        "status": "PASS" if total_cases and passed_cases == total_cases else "REVIEW",
        "cases": case_results,
    }


def load_benchmark_cases(path):
    """Load benchmark cases from a JSON file."""
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        return list(payload.get("cases", []))
    return list(payload)
