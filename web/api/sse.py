"""Server-Sent Events helpers."""

from __future__ import annotations

import json
from typing import Any


def format_sse_event(data: dict[str, Any]) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
