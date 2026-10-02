import pytest
import responses

from py3status_claude_usage import api
from conftest import FakePy3, body

FMT = "{name} {hourly_percent}%{hourly_chart}"


@responses.activate
def test_success(make_module, claude_dir):
    responses.get(api.USAGE_URL, json=body(hourly=42))
    m = make_module(claude_dir, name="P", format=FMT)
    out = m.claude_usage()
    assert out["full_text"] == "P 42%▄|GREEN"
    assert out["cached_until"] == ("in", 300)


@responses.activate
def test_failure_keeps_last_output(make_module, claude_dir):
    responses.get(api.USAGE_URL, json=body(hourly=42))
    responses.get(api.USAGE_URL, status=500)
    m = make_module(claude_dir, name="P", format=FMT)
    first = m.claude_usage()["full_text"]
    assert m.claude_usage()["full_text"] == first
    assert m.py3.logs


@responses.activate
def test_never_succeeded_shows_error(make_module, tmp_path):
    m = make_module(tmp_path, name="P")
    assert m.claude_usage()["full_text"] == "P ?"


@pytest.mark.parametrize("pct,color", [(0, "GREEN"), (75, "GREEN"), (76, "YELLOW"), (89, "YELLOW"), (90, "RED"), (100, "RED")])
@responses.activate
def test_chart_colors(make_module, claude_dir, pct, color):
    responses.get(api.USAGE_URL, json=body(hourly=pct))
    m = make_module(claude_dir, format="{hourly_chart}")
    assert m.claude_usage()["full_text"].endswith("|" + color)


@responses.activate
def test_per_window_thresholds(make_module, claude_dir):
    responses.get(api.USAGE_URL, json=body(hourly=65, weekly=65))
    m = make_module(claude_dir, format="{hourly_chart} {weekly_chart}")
    m.py3.thresholds = {"hourly_percent": [(0, "good"), (60, "degraded")], "weekly_percent": [(0, "good")]}
    assert m.claude_usage()["full_text"].split(" ")[0].endswith("YELLOW")
    assert m.claude_usage()["full_text"].split(" ")[1].endswith("GREEN")


@responses.activate
def test_missing_window_is_empty(make_module, claude_dir):
    responses.get(api.USAGE_URL, json=body(weekly=None))
    m = make_module(claude_dir, format="[{weekly_percent}]x")
    assert m.claude_usage()["full_text"] == "[]x"


@responses.activate
def test_two_accounts_use_own_tokens(make_module, make_claude_dir):
    responses.get(api.USAGE_URL, json=body())
    a = make_module(make_claude_dir("a", token="AAA"))
    b = make_module(make_claude_dir("b", token="BBB"))
    a.claude_usage()
    b.claude_usage()
    auth = [c.request.headers["Authorization"] for c in responses.calls]
    assert auth == ["Bearer AAA", "Bearer BBB"]
