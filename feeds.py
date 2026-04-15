from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import feedparser
import requests
from bs4 import BeautifulSoup

from profile import get_active_feeds
from settings import REQUEST_TIMEOUT

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_struct_time(t) -> datetime | None:
    if t is None:
        return None
    try:
        return datetime(*t[:6], tzinfo=timezone.utc)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# RSS fetcher
# ---------------------------------------------------------------------------

def fetch_rss(feed_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    articles: list[dict[str, Any]] = []
    try:
        # Use requests to fetch so macOS SSL certificates are handled correctly,
        # then pass raw content to feedparser (avoids CERTIFICATE_VERIFY_FAILED)
        resp = requests.get(feed_cfg["url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except Exception as exc:
        print(f"[feeds] RSS error ({feed_cfg['name']}): {exc}")
        return articles

    for entry in parsed.entries:
        url = entry.get("link", "")
        if not url:
            continue

        pub_dt = _parse_struct_time(
            entry.get("published_parsed") or entry.get("updated_parsed")
        )

        summary = ""
        if hasattr(entry, "summary"):
            summary = BeautifulSoup(entry.summary, "html.parser").get_text(" ", strip=True)
        elif hasattr(entry, "description"):
            summary = BeautifulSoup(entry.description, "html.parser").get_text(" ", strip=True)

        articles.append(
            {
                "id": _make_id(url),
                "title": entry.get("title", "").strip(),
                "url": url,
                "source": feed_cfg["source"],
                "feed_name": feed_cfg["name"],
                "published": pub_dt,
                "summary": summary,
                "full_text": summary,
            }
        )

    return articles


# ---------------------------------------------------------------------------
# zentralplus scraper
# ---------------------------------------------------------------------------

def fetch_zentralplus(feed_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    articles: list[dict[str, Any]] = []
    try:
        resp = requests.get(feed_cfg["url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[feeds] Scrape error ({feed_cfg['name']}): {exc}")
        return articles

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates = soup.find_all("article")
    if not candidates:
        candidates = soup.select("a[href*='/zug/']")

    seen_urls: set[str] = set()

    for item in candidates:
        link_tag = item.find("a", href=True) if item.name != "a" else item
        if not link_tag:
            continue
        href = link_tag["href"]
        if not href.startswith("http"):
            href = "https://www.zentralplus.ch" + href
        if href in seen_urls or "/zug/" not in href:
            continue
        if href.rstrip("/") == "https://www.zentralplus.ch/zug":
            continue
        seen_urls.add(href)

        title_tag = item.find(["h1", "h2", "h3", "h4"]) or (
            link_tag if link_tag.get_text(strip=True) else None
        )
        title = title_tag.get_text(" ", strip=True) if title_tag else ""
        if not title:
            continue

        summary_tag = item.find("p")
        summary = summary_tag.get_text(" ", strip=True) if summary_tag else ""

        pub_dt: datetime | None = None
        time_tag = item.find("time")
        if time_tag:
            dt_str = time_tag.get("datetime", "")
            try:
                pub_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except Exception:
                pass
        if pub_dt is None:
            pub_dt = _now_utc()

        articles.append(
            {
                "id": _make_id(href),
                "title": title,
                "url": href,
                "source": feed_cfg["source"],
                "feed_name": feed_cfg["name"],
                "published": pub_dt,
                "summary": summary,
                "full_text": summary,
            }
        )

    return articles


# ---------------------------------------------------------------------------
# Generic scraper fallback (for future feeds of type "basic")
# ---------------------------------------------------------------------------

def fetch_basic(feed_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Route 'basic' feeds to the appropriate scraper by source name,
    or use a generic fallback.
    """
    source = feed_cfg.get("source", "")
    if source == "zentralplus":
        return fetch_zentralplus(feed_cfg)

    # Generic fallback: grab <article> or <h2><a> patterns
    articles: list[dict[str, Any]] = []
    try:
        resp = requests.get(feed_cfg["url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[feeds] Generic scrape error ({feed_cfg['name']}): {exc}")
        return articles

    soup = BeautifulSoup(resp.text, "html.parser")
    seen: set[str] = set()

    for tag in soup.find_all(["article", "h2", "h3"]):
        link = tag.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            base = feed_cfg["url"].rstrip("/")
            href = base + "/" + href.lstrip("/")
        if href in seen:
            continue
        seen.add(href)
        title = link.get_text(" ", strip=True)
        if not title:
            continue
        articles.append(
            {
                "id": _make_id(href),
                "title": title,
                "url": href,
                "source": feed_cfg["source"],
                "feed_name": feed_cfg["name"],
                "published": _now_utc(),
                "summary": "",
                "full_text": "",
            }
        )

    return articles


# ---------------------------------------------------------------------------
# Full feed aggregator
# ---------------------------------------------------------------------------

def fetch_all_feeds() -> list[dict[str, Any]]:
    """
    Fetch all enabled feeds from profile.json and return a deduplicated,
    combined list of article dicts.
    """
    all_articles: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for feed_cfg in get_active_feeds():
        feed_type = feed_cfg.get("type", "rss")
        if feed_type == "rss":
            articles = fetch_rss(feed_cfg)
        elif feed_type == "basic":
            articles = fetch_basic(feed_cfg)
        else:
            print(f"[feeds] Unknown type '{feed_type}' for {feed_cfg['name']} – skipping.")
            continue

        for art in articles:
            if art["id"] not in seen_ids:
                seen_ids.add(art["id"])
                art["score_text"] = f"{art['title']} {art['summary']}"
                all_articles.append(art)

    return all_articles
