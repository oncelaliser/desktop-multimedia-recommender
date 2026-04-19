from __future__ import annotations

import re


def normalize_text(value: str) -> str:
    lowered = value.lower().strip()
    return re.sub(r"\s+", " ", lowered)
