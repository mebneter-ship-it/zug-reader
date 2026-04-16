from __future__ import annotations

import re
from profile import load_profile


def _make_pattern(keyword: str) -> re.Pattern:
    """
    Compile a case-insensitive word-boundary regex for a keyword.

    Uses a *leading* boundary only so that German compound words are matched:
      e.g. 'miete' matches 'Miete', 'Mietpreise', 'Mietzinsbelastung'
           'wirtschaft' matches 'Wirtschaft', 'Wirtschaftsstandort'
    This avoids the substring-false-positive problem (no match inside a word
    like 'Abkommen') while still surfacing compound forms.

    Multi-word keywords (e.g. 'künstliche intelligenz') are matched as a phrase
    with a leading boundary on the first word only.
    """
    escaped = re.escape(keyword)
    return re.compile(rf"\b{escaped}", re.IGNORECASE)


def score_article(text: str, title: str = "") -> dict:
    """
    Score an article against the campaign profile themes using whole-word matching.

    Returns:
        {
            "score": int,
            "matches": [
                {
                    "theme": str,
                    "hits": list[str],
                    "priority": int,
                    "score": int,
                    "position": str,
                },
                ...
            ]
        }
    """
    profile = load_profile()
    haystack = f"{title} {text}"   # preserve case for regex; pattern is IGNORECASE

    matches = []
    total_score = 0

    for theme in profile["themes"]:
        hits = [
            kw for kw in theme["keywords"]
            if _make_pattern(kw).search(haystack)
        ]
        if hits:
            theme_score = len(hits) * max(1, 8 - theme["priority"])
            total_score += theme_score
            matches.append(
                {
                    "theme":    theme["name"],
                    "hits":     hits,
                    "priority": theme["priority"],
                    "score":    theme_score,
                    "position": theme["position"],
                }
            )

    matches.sort(key=lambda x: (-x["score"], x["priority"]))
    return {"score": total_score, "matches": matches}
