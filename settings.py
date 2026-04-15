from __future__ import annotations
from pathlib import Path

# ---------------------------------------------------------------------------
# App-level constants — edit here, not via the UI
# ---------------------------------------------------------------------------

# Path to the user-editable campaign profile
PROFILE_PATH: Path = Path(__file__).parent / "profile.json"

# Score display thresholds
SCORE_HIGH: int = 20   # green badge
SCORE_MED:  int = 8    # orange badge
# below SCORE_MED → grey badge

# Feed fetching
REQUEST_TIMEOUT: int = 15   # seconds per HTTP request

# ---------------------------------------------------------------------------
# Geographic filter — Kanton Zug municipalities and canton keywords
# ---------------------------------------------------------------------------

ZUG_GEO_KEYWORDS: list[str] = [
    # Canton
    "kanton zug", "kt. zug", "kt zug",
    # City / Hauptort
    "zug",
    # All municipalities (Gemeinden)
    "baar", "cham", "hünenberg", "menzingen", "neuheim",
    "oberägeri", "risch", "rotkreuz", "steinhausen",
    "unterägeri", "walchwil",
    # Common local references
    "zuger", "zugerinnen", "zuger kantonsrat",
    "zuger regierung", "stadtrat zug", "gemeinderat zug",
]
