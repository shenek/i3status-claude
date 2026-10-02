# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A py3status module (`claude_usage`) that shows Claude Code subscription usage (5-hour and 7-day windows) in the i3 bar. One module instance per Claude account; py3status itself parses `i3status.conf` and injects config keys as attributes, so the module never reads the config file. `README.md` documents user-facing config/placeholders; `PLAN.md` holds the original design (note: it is partly outdated, e.g. it mentions hatchling and `load_credentials`, whereas the code uses `uv_build` and `api.load_token`).

## Commands

```
uv sync                                                          # .venv with pytest + responses
uv run pytest                                                    # all tests
uv run pytest tests/test_module.py::test_name                    # single test
uv run python -m py3status_claude_usage.claude_usage ~/.claude   # one live API query
```

Do not use py3status' `module_test` against the live API: it polls every second and gets rate limited.

## Architecture

Three layers in `src/py3status_claude_usage/`:
- `api.py`: reads `<path>/.credentials.json` (`load_token`) and calls `GET https://api.anthropic.com/api/oauth/usage` (`fetch_usage`) returning a `Usage` with `hourly` (`five_hour`) and `weekly` (`seven_day`) windows. All failures raise `api.UsageError`.
- `render.py`: pure helpers (`chart_glyph`, `format_remaining`, `BLOCKS`).
- `claude_usage.py`: thin py3status glue (`class Py3status`). The module docstring is parsed by py3status for docs/config params, so keep its format (Configuration parameters / Format placeholders / Color options / SAMPLE OUTPUT).

Key behaviours to preserve:
- The token is re-read on every poll and **never refreshed**: refreshing would rotate the refresh token and log the real Claude Code session out. An expired token is treated as a failure.
- On any `UsageError` the last successful `Usage` is kept and re-rendered (warning logged); `format_error` shows only if there has never been a success.
- The chart glyph is returned as a py3status composite with its own colour from `threshold_get_color(percent, "<window>_percent")`, so thresholds can be global or per window.
- Missing/null windows render as empty strings so py3status optional blocks `(...)` hide them.

## Packaging / install

The `py3status` entry point `claude_usage` is declared in `pyproject.toml`. `contrib/py3status_shim.py` is an alternative loader copied into `~/.config/py3status/modules/` (its `sys.path` line must be edited for the repo location).

## Testing

`tests/conftest.py` provides `make_claude_dir` (temp dir with fake `.credentials.json`), `body()` (fake API JSON), `FakePy3` (stand-in for the `self.py3` helper) and `make_module`. HTTP is mocked with `responses`; py3status itself is not needed to run tests.

## Commits and changelog

Commit messages follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`; `!` or a `BREAKING CHANGE:` footer for breaking changes). User-visible changes are also recorded in `CHANGELOG.md` ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format) under `[Unreleased]`.
