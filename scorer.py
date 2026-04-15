from __future__ import annotations
from profile import load_profile


def score_article(text: str, title: str = "") -> dict:
    """
    Score an article against the campaign profile themes.

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
    haystack = f"{title} {text}".lower()
    matches = []
    total_score = 0

    for theme in profile["themes"]:
        hits = [kw for kw in theme["keywords"] if kw.lower() in haystack]
        if hits:
            theme_score = len(hits) * max(1, 8 - theme["priority"])
            total_score += theme_score
            matches.append(
                {
                    "theme": theme["name"],
                    "hits": hits,
                    "priority": theme["priority"],
                    "score": theme_score,
                    "position": theme["position"],
                }
            )

    matches.sort(key=lambda x: (-x["score"], x["priority"]))
    return {"score": total_score, "matches": matches}
