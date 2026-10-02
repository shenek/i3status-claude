# Copy to ~/.config/py3status/modules/claude_usage.py and fix the path.
import sys

sys.path.insert(0, "<path>/i3status-claude/src")
from py3status_claude_usage.claude_usage import Py3status  # noqa: E402,F401
