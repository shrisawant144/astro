"""Tests for the text report renderer."""

import contextlib
import io

from tests.conftest import MUMBAI_BIRTH


def test_print_kundali_renders_core_sections():
    from kundali.main import calculate_kundali
    from kundali.printing import print_kundali

    chart = calculate_kundali(
        MUMBAI_BIRTH["date"],
        MUMBAI_BIRTH["time"],
        MUMBAI_BIRTH["place"],
        gender=MUMBAI_BIRTH["gender"],
    )

    buf = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()):
        print_kundali(chart, file=buf)

    output = buf.getvalue()
    assert "VEDIC KUNDALI" in output
    assert "Moon (Rasi)" in output
    assert "Highest probability when dasha + transit + gochara align." in output
