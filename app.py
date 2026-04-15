from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from settings import SCORE_HIGH, SCORE_MED, ZUG_GEO_KEYWORDS
from feeds import fetch_all_feeds
from generator import generate_comment, generate_letter
from scorer import score_article

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="FeedReader – Kampagnen-Tool",
    page_icon="🗞️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
.block-container { padding-top: 1.2rem; }

.score-high { background:#d4edda; color:#155724;
              padding:2px 9px; border-radius:10px;
              font-weight:700; font-size:0.82rem; }
.score-med  { background:#fff3cd; color:#856404;
              padding:2px 9px; border-radius:10px;
              font-weight:700; font-size:0.82rem; }
.score-low  { background:#f0f0f0; color:#555;
              padding:2px 9px; border-radius:10px;
              font-weight:700; font-size:0.82rem; }

.theme-tag  { display:inline-block; background:#e8f0fe; color:#1a56d6;
              padding:2px 8px; border-radius:9px;
              font-size:0.76rem; margin:2px 3px 2px 0; }

.detail-title { font-size:1.1rem; font-weight:700; line-height:1.4; }
.detail-meta  { color:#888; font-size:0.82rem; margin-bottom:8px; }

.generated-box {
    background:#1e1e1e;
    border-left:4px solid #4a7fff;
    padding:14px 16px;
    border-radius:4px;
    white-space:pre-wrap;
    font-size:0.91rem;
    line-height:1.65;
    max-height:420px;
    overflow-y:auto;
    color:#f0f0f0 !important;
}
.char-ok   { color:#155724; font-size:0.8rem; font-weight:600; }
.char-warn { color:#856404; font-size:0.8rem; font-weight:600; }
.used-dot  { color:#28a745; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

defaults = {
    "articles":       [],
    "last_fetch":     None,
    "selected_idx":   None,
    "generated":      {},   # article_id → {type, text, limit}
    "used_articles":  set(),
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _cutoff(days: int) -> datetime:
    if days == 0:
        return _now_utc().replace(hour=0, minute=0, second=0, microsecond=0)
    return _now_utc() - timedelta(days=days)

def _fmt_date(dt: datetime | None) -> str:
    if not dt:
        return "–"
    return dt.astimezone().strftime("%-d.%-m.%Y")

def _score_badge(score: int) -> str:
    css = "score-high" if score >= SCORE_HIGH else ("score-med" if score >= SCORE_MED else "score-low")
    return f'<span class="{css}">▲ {score}</span>'

def _load_and_score() -> list[dict[str, Any]]:
    raw = fetch_all_feeds()
    scored = []
    for art in raw:
        r = score_article(art["full_text"], art["title"])
        if r["score"] > 0:
            art["score"]   = r["score"]
            art["matches"] = r["matches"]
            scored.append(art)
    scored.sort(key=lambda a: -a["score"])
    return scored

def _copy_button(text: str, key: str) -> None:
    safe = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    components.html(f"""
        <button id="btn_{key}" onclick="
            navigator.clipboard.writeText(`{safe}`)
            .then(() => {{
                document.getElementById('btn_{key}').innerText = '✓ Kopiert!';
                document.getElementById('btn_{key}').style.background = '#28a745';
                setTimeout(() => {{
                    document.getElementById('btn_{key}').innerText = '📋 In Zwischenablage kopieren';
                    document.getElementById('btn_{key}').style.background = '#1a56d6';
                }}, 2500);
            }});
        " style="background:#1a56d6;color:#fff;border:none;padding:8px 18px;
                 border-radius:6px;cursor:pointer;font-size:0.87rem;font-weight:600;
                 margin-top:8px;">
            📋 In Zwischenablage kopieren
        </button>""", height=50)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🗞️ FeedReader")
    st.caption("Kampagnen-Tool Kanton Zug")
    st.divider()

    st.subheader("📅 Aktualität")
    actuality = st.radio("", ["Heute", "3 Tage", "7 Tage"], index=1, label_visibility="collapsed")
    actuality_days = {"Heute": 0, "3 Tage": 3, "7 Tage": 7}[actuality]

    st.divider()
    st.subheader("🎯 Mindest-Score")
    min_score = st.slider("", 1, 50, 5, label_visibility="collapsed")

    st.divider()
    st.subheader("🏷 Themen")
    from profile import load_profile as _lp
    all_themes = [t["name"] for t in _lp()["themes"]]
    selected_themes = st.multiselect("", options=all_themes, default=all_themes, label_visibility="collapsed")

    st.divider()
    st.subheader("📍 Geografie")
    geo_filter = st.toggle("Nur Kanton Zug & Gemeinden", value=True)

    st.divider()
    if st.button("🔄 Feeds laden / aktualisieren", use_container_width=True):
        st.session_state.articles   = _load_and_score()
        st.session_state.last_fetch = _now_utc()
        st.session_state.selected_idx = None
        st.toast(f"✅ {len(st.session_state.articles)} relevante Artikel geladen.", icon="📰")

    if st.session_state.last_fetch:
        st.caption(f"Geladen: {_fmt_date(st.session_state.last_fetch)}")
    st.caption(f"Session: {len(st.session_state.used_articles)} Artikel bearbeitet")

# ---------------------------------------------------------------------------
# Auto-load on first run
# ---------------------------------------------------------------------------

if not st.session_state.articles and not st.session_state.last_fetch:
    with st.spinner("Feeds werden geladen…"):
        st.session_state.articles   = _load_and_score()
        st.session_state.last_fetch = _now_utc()

# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------

def _is_zug_related(art: dict) -> bool:
    haystack = f"{art['title']} {art['summary']}".lower()
    return any(kw in haystack for kw in ZUG_GEO_KEYWORDS)

cutoff_dt = _cutoff(actuality_days)
articles = [
    a for a in st.session_state.articles
    if a["published"] and a["published"] >= cutoff_dt
    and a["score"] >= min_score
    and any(m["theme"] in selected_themes for m in a["matches"])
    and (not geo_filter or _is_zug_related(a))
]

# ---------------------------------------------------------------------------
# Main layout: table (left) | detail panel (right)
# ---------------------------------------------------------------------------

st.title("🗞️ FeedReader – Kampagnen-Tool")
col_table, col_detail = st.columns([5, 4], gap="large")

# ── LEFT: Article table ───────────────────────────────────────────────────

with col_table:
    st.markdown(f"**{len(articles)} Artikel** · {actuality}, Score ≥ {min_score}")

    if not articles:
        st.info("Keine Artikel gefunden. Filter lockern oder Feeds neu laden.", icon="🔍")
    else:
        # Build display dataframe
        rows = []
        for a in articles:
            used_mark = "✓ " if a["id"] in st.session_state.used_articles else ""
            themes_short = ", ".join(
                m["theme"].split(" ")[0] for m in a["matches"]
                if m["theme"] in selected_themes
            )[:30]
            summary_short = (a["summary"][:90] + "…") if len(a["summary"]) > 90 else a["summary"]
            rows.append({
                "▲": a["score"],
                "Titel": used_mark + a["title"],
                "Quelle": a["feed_name"].replace("Zuger Zeitung – ", "ZZ·").replace("zentralplus – ", "ZP·"),
                "Datum": _fmt_date(a["published"]),
                "Themen": themes_short,
                "Vorschau": summary_short,
            })

        df = pd.DataFrame(rows)

        event = st.dataframe(
            df,
            on_select="rerun",
            selection_mode="single-row",
            use_container_width=True,
            hide_index=True,
            height=620,
            column_config={
                "▲":       st.column_config.NumberColumn(width=50),
                "Titel":   st.column_config.TextColumn(width="large"),
                "Quelle":  st.column_config.TextColumn(width="small"),
                "Datum":   st.column_config.TextColumn(width="small"),
                "Themen":  st.column_config.TextColumn(width="medium"),
                "Vorschau":st.column_config.TextColumn(width="large"),
            },
        )

        # Update selected article on row click
        if event.selection.rows:
            st.session_state.selected_idx = event.selection.rows[0]

# ── RIGHT: Detail + Generate panel ───────────────────────────────────────

with col_detail:
    idx = st.session_state.selected_idx

    if idx is None or idx >= len(articles):
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("← Artikel in der Tabelle anklicken, um Kommentar oder Leserbrief zu generieren.", icon="👈")
    else:
        art = articles[idx]
        art_id = art["id"]

        # --- Article header ---
        score_html = _score_badge(art["score"])
        used_html  = '<span class="used-dot"> ✓ bearbeitet</span>' if art_id in st.session_state.used_articles else ""

        st.markdown(
            f'{score_html}{used_html}<br>'
            f'<span class="detail-title"><a href="{art["url"]}" target="_blank">{art["title"]}</a></span><br>'
            f'<span class="detail-meta">{art["feed_name"]} · {_fmt_date(art["published"])}</span>',
            unsafe_allow_html=True,
        )

        # Theme tags
        visible_matches = [m for m in art["matches"] if m["theme"] in selected_themes]
        if visible_matches:
            tags = " ".join(f'<span class="theme-tag">🏷 {m["theme"]}</span>' for m in visible_matches)
            st.markdown(tags, unsafe_allow_html=True)

        # Summary
        if art["summary"]:
            st.markdown("---")
            st.markdown(f"*{art['summary']}*")

        # Matched positions
        if visible_matches:
            with st.expander("Positionen anzeigen"):
                for m in visible_matches:
                    st.markdown(f"**{m['theme']}** *(Treffer: {', '.join(m['hits'])})*  \n→ {m['position']}")

        st.markdown("---")

        # Generate buttons
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            gen_comment = st.button("✍️ Kommentar (1500)", key=f"c_{art_id}", use_container_width=True)
        with col_btn2:
            gen_letter  = st.button("📝 Leserbrief (2000)", key=f"l_{art_id}", use_container_width=True)

        if gen_comment or gen_letter:
            gen_type = "comment" if gen_comment else "letter"
            limit    = 1500 if gen_comment else 2000
            label    = "Kommentar" if gen_comment else "Leserbrief"
            with st.spinner(f"{label} wird generiert…"):
                try:
                    fn = generate_comment if gen_comment else generate_letter
                    text = fn(art, visible_matches or art["matches"])
                    st.session_state.generated[art_id] = {"type": gen_type, "text": text, "limit": limit}
                    st.session_state.used_articles.add(art_id)
                except Exception as exc:
                    st.error(f"Fehler: {exc}")

        # Display generated text
        if art_id in st.session_state.generated:
            gen   = st.session_state.generated[art_id]
            text  = gen["text"]
            limit = gen["limit"]
            chars = len(text)
            label = "Kommentar" if gen["type"] == "comment" else "Leserbrief"
            css   = "char-ok" if chars <= limit else "char-warn"

            st.markdown(f"**Generierter {label}**")
            st.markdown(f'<p class="{css}">Zeichen: {chars} / {limit}</p>', unsafe_allow_html=True)
            st.markdown(f'<div class="generated-box">{text}</div>', unsafe_allow_html=True)
            _copy_button(text, key=f"cp_{art_id}_{gen['type']}")
