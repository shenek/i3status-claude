import json
import time

import pytest
import requests
import responses

from py3status_claude_usage import api
from conftest import body


@responses.activate
def test_fetch_ok_sends_headers(claude_dir):
    responses.get(api.USAGE_URL, json=body())
    usage = api.fetch_usage(api.load_token(claude_dir))
    assert usage.hourly.utilization == 42
    assert usage.weekly.resets_at.year == 2099
    sent = responses.calls[0].request.headers
    assert sent["Authorization"] == "Bearer tok"
    assert sent["anthropic-beta"] == "oauth-2025-04-20"


@pytest.mark.parametrize("status", [401, 429, 500])
@responses.activate
def test_http_errors(status):
    responses.get(api.USAGE_URL, status=status)
    with pytest.raises(api.ApiError):
        api.fetch_usage("tok")


@responses.activate
def test_network_error():
    responses.get(api.USAGE_URL, body=requests.ConnectionError("boom"))
    with pytest.raises(api.ApiError):
        api.fetch_usage("tok")


@responses.activate
def test_null_window():
    responses.get(api.USAGE_URL, json=body(weekly=None))
    usage = api.fetch_usage("tok")
    assert usage.weekly is None and usage.hourly is not None


@responses.activate
def test_non_json_body():
    responses.get(api.USAGE_URL, body="<html>")
    with pytest.raises(api.ApiError):
        api.fetch_usage("tok")


def test_missing_file(tmp_path):
    with pytest.raises(api.CredentialsError):
        api.load_token(tmp_path)


def test_malformed_json(tmp_path):
    (tmp_path / ".credentials.json").write_text("{nope")
    with pytest.raises(api.CredentialsError):
        api.load_token(tmp_path)


def test_no_oauth_section(tmp_path):
    (tmp_path / ".credentials.json").write_text(json.dumps({"x": 1}))
    with pytest.raises(api.CredentialsError):
        api.load_token(tmp_path)


@responses.activate
def test_expired_token_makes_no_request(make_claude_dir):
    d = make_claude_dir(expires_in=-10)
    with pytest.raises(api.TokenExpired):
        api.load_token(d, now=time.time())
    assert len(responses.calls) == 0
