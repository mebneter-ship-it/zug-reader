from __future__ import annotations

import json
from typing import Any

from settings import PROFILE_PATH


def load_profile() -> dict[str, Any]:
    """Load the campaign profile from profile.json."""
    with open(PROFILE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_profile(profile: dict[str, Any]) -> None:
    """Write the campaign profile back to profile.json."""
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def get_active_feeds() -> list[dict[str, Any]]:
    """Return only feeds that are enabled."""
    return [f for f in load_profile()["feeds"] if f.get("enabled", True)]
