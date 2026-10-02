"""
Display Claude Code subscription usage (5-hour and 7-day windows).

Create one module instance per Claude account; each points at the directory
holding that account's `.credentials.json` (e.g. ~/.claude, ~/.claude-abc).
The token is only read, never refreshed: Claude Code itself renews it.

Configuration parameters:
    blocks: glyphs used for the chart, lowest to highest (default '_▁▂▃▄▅▆▇█')
    cache_timeout: seconds between usage queries (default 300)
    format: display format (default below)
    format_error: shown until the first successful query (default '{name} ?')
    name: label shown in the bar (default 'Claude')
    path: directory containing .credentials.json (default '~/.claude')
    request_timeout: HTTP timeout in seconds (default 10)
    thresholds: chart colour ranges, optionally per window name, e.g.
        {'hourly_percent': [(0, 'good'), (60, 'degraded'), (85, 'bad')]}
        (default [(0, 'good'), (76, 'degraded'), (90, 'bad')])

Format placeholders:
    {name} label
    {hourly_percent} 5-hour window utilization, 0-100
    {hourly_chart} one-glyph chart of it, coloured by thresholds
    {hourly_time_remain} time until the 5-hour window resets, e.g. 2h13m
    {weekly_percent} {weekly_chart} {weekly_time_remain} same for 7 days

Color options:
    color_good: usage below the degraded threshold
    color_degraded: usage in the middle range
    color_bad: usage in the top range

Example (in i3status.conf):
```
order += "claude_usage personal"

claude_usage personal {
    name = 'Personal'
    path = '~/.claude'
    cache_timeout = 300
}
```

@author Stepan Henek

SAMPLE OUTPUT
{'full_text': 'Personal 49%▄2h13m 77%▆2d11h'}
"""

from py3status_claude_usage import api, render

DEFAULT_FORMAT = (
    "{name} {hourly_percent}{hourly_chart}(…{hourly_time_remain}) "
    "{weekly_percent}{weekly_chart}(…{weekly_time_remain})"
)


class Py3status:
    blocks = render.BLOCKS
    cache_timeout = 300
    format = DEFAULT_FORMAT
    format_error = "{name} ?"
    name = "Claude"
    path = "~/.claude"
    request_timeout = 10
    thresholds = [(0, "good"), (76, "degraded"), (90, "bad")]

    def post_config_hook(self):
        self._usage = None  # last successful api.Usage

    def _window_params(self, prefix, window):
        if window is None:
            return {f"{prefix}_percent": "", f"{prefix}_chart": "", f"{prefix}_time_remain": ""}
        percent = int(round(window.utilization))
        key = f"{prefix}_percent"
        chart = self.py3.composite_create(
            {
                "full_text": render.chart_glyph(window.utilization, self.blocks),
                "color": self.py3.threshold_get_color(percent, key),
            }
        )
        return {
            key: percent,
            f"{prefix}_chart": chart,
            f"{prefix}_time_remain": render.format_remaining(window.resets_at),
        }

    def _render(self):
        if self._usage is None:
            return self.py3.safe_format(self.format_error, {"name": self.name})
        params = {"name": self.name}
        params.update(self._window_params("hourly", self._usage.hourly))
        params.update(self._window_params("weekly", self._usage.weekly))
        return self.py3.safe_format(self.format, params)

    def claude_usage(self):
        try:
            token = api.load_token(self.path)
            self._usage = api.fetch_usage(token, self.request_timeout)
        except api.UsageError as err:
            # keep showing the previous values
            self.py3.log(f"{self.name}: {err}", level=self.py3.LOG_WARNING)
        return {
            "full_text": self._render(),
            "cached_until": self.py3.time_in(self.cache_timeout),
        }


if __name__ == "__main__":
    # One-shot check of credentials + endpoint. (py3status' module_test polls
    # every second, which gets rate limited, so it is not used here.)
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else Py3status.path
    print(api.fetch_usage(api.load_token(path)))
