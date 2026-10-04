# py3status-claude-usage

py3status module that shows Claude Code subscription usage (5-hour and 7-day
windows) in the i3 bar. One module instance per Claude account.

```
Personal 49%▄2h13m 77%▆2d11h
```

Data comes from `https://api.anthropic.com/api/oauth/usage`, authenticated with
the OAuth token in `<path>/.credentials.json`. The module never refreshes the
token (that would rotate the refresh token and log Claude Code out); if the
token is expired the bar keeps its last values until Claude Code renews it.

No Claude Code session has to stay open, but only Claude Code renews the token,
and it does so when it is used. For an account you have not used for a while
(for example a second `CLAUDE_CONFIG_DIR`), run `claude` once with that config
dir, e.g. `CLAUDE_CONFIG_DIR=~/.claude-work claude -p hi`, to get up-to-date
data. The module picks up the renewed token on its next poll.

## Configuration

```
claude_usage personal {
    name = 'Personal'          # label, {name}
    path = '~/.claude'         # dir with .credentials.json
    cache_timeout = 300        # seconds between queries (keep >= 60)
    # format is optional:
    format = '{name} {hourly_percent}%{hourly_chart}{hourly_time_remain} {weekly_percent}%{weekly_chart}{weekly_time_remain}'
}
claude_usage abc {
    name = 'ABC'
    path = '~/.claude-abc'
}
order += "claude_usage personal"
order += "claude_usage abc"
```

Placeholders: `{name} {hourly_percent} {hourly_chart} {hourly_time_remain}
{weekly_percent} {weekly_chart} {weekly_time_remain}`.

The chart is one glyph from `blocks` (default `_▁▂▃▄▅▆▇█`, as in
`battery_level`), coloured green 0-75, yellow 76-89, red 90-100. Change with
`thresholds` (a list, or a dict keyed by `hourly_percent` / `weekly_percent`)
and `color_good` / `color_degraded` / `color_bad`. See `examples/i3status.conf`.

## Installing into py3status

py3status finds third-party modules in two ways.

**A. Include path (no pip, recommended on Debian with distro py3status).**
```
mkdir -p ~/.config/py3status/modules
cp contrib/py3status_shim.py ~/.config/py3status/modules/claude_usage.py
# edit the sys.path line if the repo is not in ~/projects/i3status-claude
```
Needs only `requests` (`python3-requests`).

**B. Entry point (pip).** Install into the interpreter that runs py3status:
```
pip install py3status-claude-usage                      # from PyPI
uv tool install py3status --with py3status-claude-usage # uv tool, from PyPI
uv pip install --system --break-system-packages -e .   # from a checkout, distro py3status
uv tool install py3status --with /path/to/i3status-claude   # from a checkout
```

Then:
1. Add the blocks and `order +=` lines to `~/.config/i3/i3status.conf`.
2. Check: `py3status modules list | grep claude_usage`
3. Reload: `i3-msg restart`; refresh one instance: `py3-cmd refresh "claude_usage personal"`
4. Debug: `py3status -c ~/.config/i3/i3status.conf -l ~/py3status.log -d`

## Development

```
uv sync                      # creates .venv with pytest + responses
uv run pytest
uv run python -m py3status_claude_usage.claude_usage ~/.claude   # one live query
```

## Releasing

1. Move the `[Unreleased]` changelog entries under a new version heading and bump `version` in `pyproject.toml`.
2. `uv run pytest && uv build`
3. Tag: `git tag vX.Y.Z && git push --tags`
4. Publish: `uv publish` (with a PyPI API token via `UV_PUBLISH_TOKEN`), or let the `Publish` GitHub workflow do it on a published release (PyPI trusted publishing).
