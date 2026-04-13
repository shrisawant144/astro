"""Targeted tests for the PDF report generator."""

import warnings

import pytest

from tests.conftest import MUMBAI_BIRTH


@pytest.fixture
def chart():
    from kundali.main import calculate_kundali

    result = calculate_kundali(
        MUMBAI_BIRTH["date"],
        MUMBAI_BIRTH["time"],
        MUMBAI_BIRTH["place"],
        gender=MUMBAI_BIRTH["gender"],
    )
    result["name"] = "QA PDF"
    return result


def _pdf_bytes(builder):
    from kundali.report_pdf import KundaliPDF

    pdf = KundaliPDF(native_name="QA PDF")
    pdf.set_compression(False)
    builder(pdf)
    return bytes(pdf.output())


def test_safe_filename_strips_unsafe_characters():
    from kundali.report_pdf import _safe_filename

    assert _safe_filename(" Jane / Doe?? ") == "jane_doe"


def test_generate_pdf_report_creates_custom_output_path(chart, tmp_path):
    from kundali.report_pdf import generate_pdf_report

    output_path = tmp_path / "nested" / "pdf" / "report.pdf"
    created = generate_pdf_report(chart, output_path=str(output_path))

    assert created == str(output_path.resolve())
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_chara_dasha_page_uses_runtime_dashas_shape(chart):
    from kundali.report_pdf import _page_chara_dasha

    pdf_bytes = _pdf_bytes(lambda pdf: _page_chara_dasha(pdf, chart))

    assert b"Current Chara Dasha" in pdf_bytes
    assert b"Chara Mahadasha Sequence" in pdf_bytes
    assert chart["chara_dasha"]["current"]["current_sign"].encode("latin-1") in pdf_bytes


def test_decision_pages_render_runtime_payload_keys(chart):
    from kundali.report_pdf import _page_decisions

    pdf_bytes = _pdf_bytes(lambda pdf: _page_decisions(pdf, chart))

    expected_titles = [
        b"Prediction Confidence & Data Quality",
        b"Current Career Dasha",
        b"Favorable Marriage Periods",
        b"Financial Advice",
        b"Foreign Settlement Likelihood",
        b"Academic Ability Score",
        b"Daily Tips",
    ]
    for title in expected_titles:
        assert title in pdf_bytes


def test_shadbala_page_flattens_nested_component_dicts(chart):
    from kundali.report_pdf import _page_shadbala

    pdf_bytes = _pdf_bytes(lambda pdf: _page_shadbala(pdf, chart))

    assert b"Shadbala" in pdf_bytes
    assert b"Sthana" in pdf_bytes
    assert b"{'sthana_bala'" not in pdf_bytes
    assert b"'components'" not in pdf_bytes


def test_vimshopak_page_flattens_breakdown_dicts(chart):
    from kundali.report_pdf import _page_vimshopak

    pdf_bytes = _pdf_bytes(lambda pdf: _page_vimshopak(pdf, chart))

    assert b"Vimshopak Bala" in pdf_bytes
    assert b"D60" in pdf_bytes
    assert b"{'d1':" not in pdf_bytes
    assert b"'breakdown'" not in pdf_bytes


def test_generate_pdf_report_emits_no_ln_deprecation(chart, tmp_path):
    from kundali.report_pdf import generate_pdf_report

    output_path = tmp_path / "warnings.pdf"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        generate_pdf_report(chart, output_path=str(output_path))

    ln_warnings = [
        warning
        for warning in caught
        if issubclass(warning.category, DeprecationWarning)
        and '"ln"' in str(warning.message)
    ]
    assert not ln_warnings
