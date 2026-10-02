from datetime import datetime, timedelta, timezone

import pytest

from py3status_claude_usage.render import chart_glyph, format_remaining


@pytest.mark.parametrize("pct,glyph", [(0, "_"), (1, "▁"), (50, "▄"), (100, "█"), (130, "█"), (-5, "_")])
def test_chart_glyph(pct, glyph):
    assert chart_glyph(pct) == glyph


def test_custom_blocks():
    assert chart_glyph(100, "ab") == "b"
    assert chart_glyph(0, "ab") == "a"


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "delta,text",
    [
        (timedelta(hours=2, minutes=13), "2h13m"),
        (timedelta(days=4, hours=3, minutes=20), "4d3h"),
        (timedelta(minutes=45), "45m"),
        (timedelta(minutes=-5), "0m"),
    ],
)
def test_format_remaining(delta, text):
    assert format_remaining(NOW + delta, NOW) == text


def test_format_remaining_none():
    assert format_remaining(None) == ""
