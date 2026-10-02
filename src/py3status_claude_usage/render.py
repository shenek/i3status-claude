"""Pure formatting helpers (no py3status dependency)."""

import math
from datetime import datetime, timezone

BLOCKS = "_▁▂▃▄▅▆▇█"


def chart_glyph(percent, blocks=BLOCKS):
    """Pick a glyph the same way py3status' battery_level does."""
    top = len(blocks) - 1
    index = int(math.ceil(percent / 100 * top))
    return blocks[max(0, min(top, index))]


def format_remaining(resets_at, now=None):
    """'2h13m', '4d3h', '45m'; '0m' once the reset time has passed."""
    if resets_at is None:
        return ""
    now = now or datetime.now(timezone.utc)
    minutes = max(0, int((resets_at - now).total_seconds() // 60))
    days, rest = divmod(minutes, 1440)
    hours, mins = divmod(rest, 60)
    if days:
        return f"{days}d{hours}h"
    if hours:
        return f"{hours}h{mins:02d}m"
    return f"{mins}m"
