"""Tests for benchmark/backtesting helpers."""

import json

from tests.conftest import MUMBAI_BIRTH


def test_evaluate_benchmark_case_passes_for_valid_expectations():
    from kundali.benchmarking import evaluate_benchmark_case

    case = {
        "id": "sample_pass",
        "birth": {
            "date": MUMBAI_BIRTH["date"],
            "time": MUMBAI_BIRTH["time"],
            "place": MUMBAI_BIRTH["place"],
            "gender": MUMBAI_BIRTH["gender"],
        },
        "expectations": [
            {"path": "chart.birth_place", "equals": MUMBAI_BIRTH["place"]},
            {"path": "input_quality.label", "in": ["Good", "Strong"]},
            {"path": "decisions.career.confidence_score", "min": 20},
            {"path": "confidence_summary.average_score", "min": 20},
        ],
    }

    result = evaluate_benchmark_case(case)

    assert result["status"] == "PASS"
    assert result["score"] == 100


def test_run_benchmark_suite_reports_failures():
    from kundali.benchmarking import run_benchmark_suite

    suite = run_benchmark_suite(
        [
            {
                "id": "sample_fail",
                "birth": {
                    "date": MUMBAI_BIRTH["date"],
                    "time": MUMBAI_BIRTH["time"],
                    "place": MUMBAI_BIRTH["place"],
                    "gender": MUMBAI_BIRTH["gender"],
                },
                "expectations": [
                    {"path": "chart.birth_place", "equals": "Somewhere Else"},
                ],
            }
        ]
    )

    assert suite["status"] == "REVIEW"
    assert suite["cases"][0]["status"] == "FAIL"


def test_load_benchmark_cases_reads_json(tmp_path):
    from kundali.benchmarking import load_benchmark_cases

    benchmark_path = tmp_path / "benchmarks.json"
    benchmark_path.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "json_case",
                        "birth": {"date": "1990-05-15", "time": "08:30", "place": "Mumbai, India"},
                        "expectations": [{"path": "chart.birth_place", "equals": "Mumbai, India"}],
                    }
                ]
            }
        )
    )

    cases = load_benchmark_cases(str(benchmark_path))

    assert len(cases) == 1
    assert cases[0]["id"] == "json_case"
