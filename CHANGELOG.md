# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- py3status module `claude_usage` showing Claude Code subscription usage for
  the 5-hour and 7-day windows, one module instance per Claude account.
- Usage API client reading the OAuth token from `<path>/.credentials.json`.
  The token is re-read on every poll and never refreshed, so the real Claude
  Code session is not logged out.
- One-glyph usage chart with its own colour, driven by global or per-window
  `thresholds`.
- Last successful result is kept and re-rendered when a poll fails;
  `format_error` is shown only until the first success.
- Missing or null windows render as empty strings, so optional format blocks
  `(...)` hide them.
- Packaging with a `py3status` entry point, a `contrib/py3status_shim.py`
  loader and an example `i3status.conf`.
- Test suite for the API client, rendering helpers and module glue.

### Changed

- Default format no longer prints a literal `%` and wraps the time remaining
  in an optional block, so it disappears when a window is unavailable.
