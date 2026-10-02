"""Credentials loading and the Claude OAuth usage endpoint."""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from . import __version__

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CREDENTIALS_FILE = ".credentials.json"


class UsageError(Exception):
    """Base class for all errors raised by this module."""


class CredentialsError(UsageError):
    """Credentials file missing or malformed."""


class TokenExpired(UsageError):
    """Access token is expired; Claude Code has to refresh it."""


class ApiError(UsageError):
    """The usage request failed."""


@dataclass
class Window:
    utilization: float  # 0-100
    resets_at: Optional[datetime]


@dataclass
class Usage:
    hourly: Optional[Window]
    weekly: Optional[Window]


def load_token(path, now=None):
    """Return the OAuth access token stored in ``<path>/.credentials.json``."""
    file = Path(path).expanduser() / CREDENTIALS_FILE
    try:
        data = json.loads(file.read_text())
        oauth = data["claudeAiOauth"]
        token = oauth["accessToken"]
        expires_at = oauth.get("expiresAt")
    except OSError as err:
        raise CredentialsError(f"cannot read {file}: {err.strerror}") from None
    except (ValueError, KeyError, TypeError):
        raise CredentialsError(f"{file} has no claudeAiOauth.accessToken") from None
    if not token:
        raise CredentialsError(f"{file} has an empty accessToken")
    now = time.time() if now is None else now
    if isinstance(expires_at, (int, float)) and expires_at / 1000 <= now:
        raise TokenExpired(f"token in {file} expired")
    return token


def _parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _parse_window(raw):
    if not isinstance(raw, dict):
        return None
    try:
        utilization = float(raw["utilization"])
    except (KeyError, TypeError, ValueError):
        return None
    return Window(utilization, _parse_time(raw.get("resets_at")))


def parse_usage(body):
    if not isinstance(body, dict):
        raise ApiError("unexpected response body")
    return Usage(_parse_window(body.get("five_hour")), _parse_window(body.get("seven_day")))


def fetch_usage(token, timeout=10):
    headers = {
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
        "User-Agent": f"py3status-claude-usage/{__version__}",
    }
    try:
        resp = requests.get(USAGE_URL, headers=headers, timeout=timeout)
    except requests.RequestException as err:
        raise ApiError(f"request failed: {type(err).__name__}") from None
    if resp.status_code != 200:
        raise ApiError(f"HTTP {resp.status_code}")
    try:
        return parse_usage(resp.json())
    except ValueError:
        raise ApiError("response is not JSON") from None
