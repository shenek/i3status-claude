import json
import time

import pytest

from py3status_claude_usage import claude_usage


@pytest.fixture
def make_claude_dir(tmp_path):
    def make(name="claude", token="tok", expires_in=3600):
        d = tmp_path / name
        d.mkdir()
        creds = {"claudeAiOauth": {"accessToken": token, "expiresAt": int((time.time() + expires_in) * 1000)}}
        (d / ".credentials.json").write_text(json.dumps(creds))
        return d

    return make


@pytest.fixture
def claude_dir(make_claude_dir):
    return make_claude_dir()


def body(hourly=42.0, weekly=77.0):
    def win(v):
        return None if v is None else {"utilization": v, "resets_at": "2099-01-01T00:00:00+00:00"}

    return {"five_hour": win(hourly), "seven_day": win(weekly)}


class FakePy3:
    LOG_WARNING = "warning"

    def __init__(self, module, thresholds=None):
        self.module = module
        self.logs = []
        self.thresholds = thresholds if thresholds is not None else module.thresholds
        self.colors = {"good": "GREEN", "degraded": "YELLOW", "bad": "RED"}

    def time_in(self, seconds):
        return ("in", seconds)

    def log(self, msg, level=None):
        self.logs.append(msg)

    def composite_create(self, data):
        return data

    def threshold_get_color(self, value, name=None):
        th = self.thresholds
        if isinstance(th, dict):
            th = th.get(name, [])
        color = None
        for limit, c in th:
            if value >= limit:
                color = c
        return self.colors.get(color)

    def safe_format(self, fmt, params):
        flat = {k: (v["full_text"] + "|" + str(v["color"]) if isinstance(v, dict) else v) for k, v in params.items()}
        return fmt.format(**flat)


@pytest.fixture
def make_module():
    def make(path, **attrs):
        m = claude_usage.Py3status()
        m.path = str(path)
        for k, v in attrs.items():
            setattr(m, k, v)
        m.py3 = FakePy3(m)
        m.post_config_hook()
        return m

    return make
