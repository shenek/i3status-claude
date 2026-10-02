# PLAN: py3status module showing Claude Code usage

## 1. Goal
A pip-installable Python project providing the py3status module `claude_usage`
that, per configured account, periodically calls
`GET https://api.anthropic.com/api/oauth/usage` with that account's OAuth token
and renders a user-formattable status-bar segment.

## 2. How configuration works (key design decision)
py3status already parses `~/.config/i3/i3status.conf` and injects each module
block's keys as attributes. Multiple accounts = multiple **module instances**,
so the module never parses the file itself:

```
claude_usage personal {
    name = 'Personal'
    path = '~/.claude'
    cache_timeout = 300
    format = '{name} {hourly_percent}%{hourly_chart}{hourly_time_remain} {weekly_percent}%{weekly_chart}{weekly_time_remain}'
}
claude_usage company {
    name = 'Company'
    path = '~/.claude-company'
    cache_timeout = 600
}
order += "claude_usage personal"
order += "claude_usage company"
```

Config parameters (attribute defaults on the class):
| param | default | meaning |
|---|---|---|
| `name` | `'Claude'` | label, `{name}` placeholder |
| `path` | `'~/.claude'` | dir containing `.credentials.json` (`~` expanded) |
| `cache_timeout` | `300` | seconds between API queries ("timeout" in the request) |
| `format` | `'{name} {hourly_percent}%{hourly_chart}{hourly_time_remain} {weekly_percent}%{weekly_chart}{weekly_time_remain}'` | optional |
| `request_timeout` | `10` | HTTP timeout, seconds |
| `blocks` | `'_▁▂▃▄▅▆▇█'` | chart glyphs, same as `battery_level` |
| `thresholds` | `[(0,'good'),(76,'degraded'),(90,'bad')]` | chart colour ranges: 0–75 green, 76–89 yellow, 90–100 red |
| `color_good` / `color_degraded` / `color_bad` | i3status general colours | override actual colours per instance (e.g. `'#00FF00'`, `'#FFFF00'`, `'#FF0000'`) |
| `format_error` | `'{name} ?'` | shown only if no successful fetch yet |

## 3. Placeholders
- `{name}`
- `{hourly_percent}` – `five_hour.utilization`, int 0–100
- `{hourly_chart}` – **single glyph, rendered like `battery_level`'s icon**:
  `blocks[ceil(pct / 100 * (len(blocks) - 1))]` clamped to the last index,
  so 0% → `_`, 50% → `▄`, 100% → `█`. The glyph is returned as a py3status
  composite `{'full_text': glyph, 'color': self.py3.threshold_get_color(pct, '<window>_percent')}`,
  so it is coloured automatically wherever `{hourly_chart}` appears in
  `format` – no colour markup needed in the user's format string. The rest of
  the text keeps the default bar colour.
- `{hourly_time_remain}` – time until `five_hour.resets_at`, e.g. `2h13m`
- `{weekly_percent}`, `{weekly_chart}`, `{weekly_time_remain}` – same from `seven_day` (`4d3h`)

Thresholds are configurable either globally or per window, using py3status'
standard `thresholds` syntax:
```
thresholds = [(0, 'good'), (76, 'degraded'), (90, 'bad')]          # both charts
thresholds = {'hourly_percent': [(0,'good'),(60,'degraded'),(85,'bad')],
              'weekly_percent': [(0,'good'),(76,'degraded'),(90,'bad')]}
```
Users may additionally colour the percent text via `\?color=hourly_percent`.

Missing/null windows in the response render as empty strings (py3status
`[...]` optional blocks then hide them).

## 4. Behaviour
1. `claude_usage()` is called by py3status every `cache_timeout` (or on click).
2. Re-read `<path>/.credentials.json` on every poll (Claude Code rotates the
   token; re-reading picks up fresh ones). No caching of the token.
3. If `expiresAt` (ms epoch) is in the past → skip request, keep last output,
   mark stale. **No token refresh** by the module: refreshing rotates the
   refresh token and would log the real Claude Code session out. Token is
   refreshed next time Claude Code is used.
4. Request: `requests.get(URL, headers={"Authorization": f"Bearer {token}",
   "anthropic-beta": "oauth-2025-04-20", "User-Agent": "py3status-claude-usage/<ver>"},
   timeout=request_timeout)`.
5. On success → parse, store as `self._last`, render, return
   `{"full_text": ..., "cached_until": self.py3.time_in(self.cache_timeout)}`.
6. On any failure (missing file, bad JSON, HTTP ≠ 200, network) → **status bar
   is not changed**: return the last successful output (time-remaining
   recomputed from stored `resets_at`), log via `self.py3.log`, retry after
   `cache_timeout`. If there was never a success → `format_error`.
7. Between polls, the remaining-time strings are only refreshed at poll time
   (acceptable; optional: `cached_until = min(cache_timeout, 60)` with a
   cheap re-render that does not hit the API — decide during implementation).

## 5. Project layout
```
i3status-claude/
├── PLAN.md
├── README.md                    # install + config example
├── pyproject.toml               # hatchling; deps: requests; entry point below
├── examples/i3status.conf       # snippet with two accounts
├── src/py3status_claude_usage/
│   ├── __init__.py
│   ├── claude_usage.py          # class Py3status (thin py3status glue + docstring in py3status style)
│   ├── api.py                   # load_credentials(path), fetch_usage(token, timeout) -> Usage dataclass
│   └── render.py                # chart_glyph(pct, blocks), format_remaining(resets_at, now)
├── contrib/py3status_shim.py    # 3-line loader for ~/.config/py3status/modules/ (see §6)
└── tests/
    ├── conftest.py              # tmp claude dir fixture with .credentials.json, FakePy3
    ├── test_api.py
    ├── test_render.py
    └── test_module.py
```
`pyproject.toml`: `dependencies = ["requests"]`,
`[project.optional-dependencies] test = ["pytest", "responses"]`, and the
py3status entry point (see §6).

## 6. Integration with py3status (goes into README.md too)
py3status (3.64 here, `/usr/lib/python3/dist-packages`) finds third-party
modules in two ways; both are documented, **B is the recommended one on this
Debian system** because the system Python is PEP 668 "externally managed".

**A. Entry point (pip-installed package).** py3status scans the
`py3status` entry-point group (`core.py: ENTRY_POINT_NAME = "py3status"`):
```toml
[project.entry-points.py3status]
claude_usage = "py3status_claude_usage.claude_usage"
```
Install into the *same* interpreter that runs py3status:
- distro py3status: `pip install --user --break-system-packages -e .`
- py3status in pipx: `pipx inject py3status /path/to/i3status-claude`
- py3status in a venv: `<venv>/bin/pip install -e .`

**B. Include path (no install).** py3status loads any `*.py` from
`~/.config/py3status/modules/` (default include path, or `-i <dir>`). Because
the code is a package, a shim is copied there:
```python
# ~/.config/py3status/modules/claude_usage.py
import sys; sys.path.insert(0, "<path>/i3status-claude/src")
from py3status_claude_usage.claude_usage import Py3status  # noqa: E402,F401
```
(`contrib/py3status_shim.py`; README gives a `sed`/`cp` one-liner. Only
dependency is `requests`, already provided by `python3-requests`.)

**Then, for either way:**
1. Add the instance blocks + `order += "claude_usage <instance>"` lines (§2)
   to `~/.config/i3/i3status.conf`.
2. Check discovery: `py3status modules list | grep claude_usage` and
   `py3status modules details claude_usage` (shows the docstring).
3. Reload: `i3-msg restart` (or `killall -USR1 py3status`); force a single
   refresh with `py3-cmd refresh "claude_usage personal"`.
4. Debug: run bar with `py3status -c ~/.config/i3/i3status.conf -l ~/py3status.log -d`
   and read the module's `self.py3.log` output.

## 7. Tests (pytest + `responses`)
No network; `responses` intercepts `requests`. `conftest.py` provides a
`claude_dir` fixture (tmp dir with a valid `.credentials.json`, `expiresAt`
in the future) and a minimal `FakePy3` (`time_in`, `log`, `safe_format`
delegating to `str.format` on plain values, `composite_create`,
`threshold_get_color` implementing the threshold list/dict lookup) so tests
don't need a running py3status.

`test_api.py`
- `@responses.activate` 200 with sample body → `Usage` parsed
  (`five_hour.utilization == 42`, `resets_at` datetime); assert request
  carried `Authorization: Bearer <token>` and `anthropic-beta` header.
- 401 / 500 → `ApiError`; `responses.ConnectionError` body → `ApiError`.
- body with `"seven_day": null` → `weekly` window is `None`.
- missing file / malformed JSON / no `claudeAiOauth` → `CredentialsError`.
- `expiresAt` in the past → `TokenExpired` and **no HTTP call made**
  (`len(responses.calls) == 0`).

`test_render.py`
- `chart_glyph`: 0→`_`, 50→`▄`, 100→`█`, 130 clamped to `█`, −5 → `_`;
  custom `blocks` string honoured.
- `format_remaining`: 2h13m, 4d3h, 45m, past timestamp → `0m`.

`test_module.py` (instantiate `Py3status`, set attrs, inject `FakePy3`)
- success → output contains `name`, `42`, `2h…`; `cached_until` set.
- success, then mocked 500 → second call returns the same `full_text`
  (bar not changed on failure).
- no success ever → `format_error`.
- chart colour: 75→good, 76→degraded, 90→bad; per-window dict thresholds.
- two instances with different `path`s hit the API with their own tokens.

Run: `python3 -m venv --system-site-packages .venv && .venv/bin/pip install -e '.[test]' && .venv/bin/pytest`
(`--system-site-packages` so the distro py3status is importable for the
`module_test` smoke run).

## 8. Implementation steps
1. `pyproject.toml`, package skeleton, `examples/i3status.conf`, `contrib/py3status_shim.py`.
2. `api.py`: `Credentials` + `Usage`/`Window(utilization, resets_at)` dataclasses,
   typed exceptions (`CredentialsError`, `TokenExpired`, `ApiError`).
3. `render.py`: chart + duration formatting (pure functions, no py3status import).
4. `claude_usage.py`: `Py3status` class, `post_config_hook` (expand path,
   validate), `claude_usage()` method, `__main__` block using
   `py3status.module_test.module_test(Py3status, config={...})`.
5. Tests (§7), README with the integration guide (§6).
6. Wire into `~/.config/i3/i3status.conf` via shim, reload i3.

## 9. Verification
- `.venv/bin/pytest` – all tests green, no network.
- `python -m py3status_claude_usage.claude_usage` – module_test prints live
  output for `~/.claude`.
- `py3-cmd refresh claude_usage` / restart i3 bar; check both
  `claude_usage personal` and `claude_usage company` appear, values match
  `/usage` in Claude Code, and disconnecting network keeps the last values.

## 10. Risks / open notes
- `/api/oauth/usage` is undocumented; response shape
  (`five_hour`, `seven_day`, `seven_day_opus`, `utilization`, `resets_at`) may
  change → parse defensively.
- Rate limiting: keep `cache_timeout` ≥ 60s; document it.
- Never log the token.
