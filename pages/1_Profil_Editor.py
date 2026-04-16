from __future__ import annotations

import copy
import sys
from pathlib import Path

import streamlit as st

# Make sure parent directory is on the path so we can import profile/settings
sys.path.insert(0, str(Path(__file__).parent.parent))

from profile import load_profile, save_profile

try:
    from streamlit_sortables import sort_items
    HAS_SORTABLES = True
except ImportError:
    HAS_SORTABLES = False

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Profil-Editor",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ Profil-Editor")
st.caption("Bearbeite hier dein Kampagnenprofil, deine Themen und deine Feeds.")

# ---------------------------------------------------------------------------
# Load current profile into session state (once per session)
# ---------------------------------------------------------------------------

if "editor_profile" not in st.session_state:
    st.session_state.editor_profile = load_profile()

profile = st.session_state.editor_profile

# ---------------------------------------------------------------------------
# Helper: tag list editor (comma-separated input → list)
# ---------------------------------------------------------------------------

def _list_editor(label: str, items: list[str], key: str) -> list[str]:
    raw = st.text_area(
        label,
        value="\n".join(items),
        height=120,
        key=key,
        help="Ein Eintrag pro Zeile.",
    )
    return [line.strip() for line in raw.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_persona, tab_identity, tab_themes, tab_rules, tab_feeds = st.tabs(
    ["👤 Persona", "🎭 Identität & Ton", "🏷 Themen", "✍️ Schreibregeln", "📡 Feeds"]
)

# ============================================================
# TAB 1 – PERSONA
# ============================================================

with tab_persona:
    st.subheader("Persönliche Angaben")
    st.info(
        "Diese Angaben werden in die LLM-Prompts eingebettet, damit die generierten Texte "
        "authentisch nach dir klingen.",
        icon="ℹ️",
    )

    p = profile["persona"]
    col1, col2 = st.columns(2)

    with col1:
        p["name"]       = st.text_input("Name",        value=p.get("name", ""), key="p_name")
        p["age"]        = st.text_input("Alter",        value=p.get("age", ""), key="p_age")
        p["profession"] = st.text_input("Beruf",        value=p.get("profession", ""), key="p_prof")
        p["location"]   = st.text_input("Wohnort",      value=p.get("location", ""), key="p_loc")
        p["party"]      = st.text_input("Partei",       value=p.get("party", ""), key="p_party")

    with col2:
        p["candidacy"]  = st.text_input("Kandidatur",   value=p.get("candidacy", ""), key="p_cand")
        p["slogan"]     = st.text_input("Slogan",        value=p.get("slogan", ""), key="p_slogan")
        p["adjectives"] = [
            a.strip()
            for a in st.text_input(
                "Adjektive (kommagetrennt)",
                value=", ".join(p.get("adjectives", [])),
                key="p_adj",
            ).split(",")
            if a.strip()
        ]

    p["political_roles"] = _list_editor(
        "Politische Ämter (ein Amt pro Zeile)",
        p.get("political_roles", []),
        key="p_roles",
    )
    p["voluntary_work"] = _list_editor(
        "Ehrenamtliches Engagement (ein Engagement pro Zeile)",
        p.get("voluntary_work", []),
        key="p_vol",
    )

    st.markdown("---")
    st.markdown("**Persönliche Erfahrungen**")
    st.caption(
        "Aus welcher Erfahrung sprichst du? Das Modell wählt jeweils die thematisch passende Erfahrung aus "
        "und bringt sie kurz und natürlich in Kommentare und Leserbriefe ein. Ein Eintrag pro Zeile."
    )
    profile["expertise"] = _list_editor(
        "",
        profile.get("expertise", []),
        key="p_expertise",
    )

# ============================================================
# TAB 2 – IDENTITY & TONE
# ============================================================

with tab_identity:
    st.subheader("Politische Identität")

    ident = profile["identity"]
    ident["political_profile"] = st.text_area(
        "Politisches Profil (Kurzcharakteristik)",
        value=ident.get("political_profile", ""),
        height=80,
        key="id_profile",
    )

    ident["tone_instruction"] = st.text_area(
        "Schreibstil-Anweisung (fliesst direkt in den LLM-Prompt ein)",
        value=ident.get("tone_instruction", ""),
        height=100,
        key="id_tone_instr",
        help="Beschreibe hier in eigenen Worten, wie die Texte klingen sollen. "
             "Diese Anweisung wird dem Modell wortwörtlich übergeben.",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        ident["must_have_tone"] = _list_editor(
            "Gewünschter Ton (ein Begriff pro Zeile)",
            ident.get("must_have_tone", []),
            key="id_tone",
        )
    with col_b:
        ident["must_avoid"] = _list_editor(
            "Strikt vermeiden (ein Begriff pro Zeile)",
            ident.get("must_avoid", []),
            key="id_avoid",
        )

# ============================================================
# TAB 3 – THEMES
# ============================================================

with tab_themes:
    st.subheader("Kampagnenthemen")
    st.caption(
        "Reihenfolge = Priorität. Ziehe Themen per Drag & Drop in die gewünschte Reihenfolge, "
        "dann **Profil speichern**. Priorität 1 gewinnt bei Zielkonflikten im LLM-Prompt."
    )

    themes = sorted(profile["themes"], key=lambda t: t["priority"])
    theme_map = {t["name"]: t for t in themes}

    # --- Drag & drop reorder (or ↑/↓ fallback) ---
    if HAS_SORTABLES:
        sorted_names = sort_items(
            [t["name"] for t in themes],
            direction="vertical",
            key="theme_sort",
        )
        themes = [theme_map[name] for name in sorted_names if name in theme_map]
    else:
        st.caption("💡 Für Drag & Drop: `pip3 install streamlit-sortables` ausführen und neu starten.")
        move_up, move_down = None, None
        for idx, theme in enumerate(themes):
            col_u, col_d, col_lbl = st.columns([1, 1, 8])
            with col_u:
                if idx > 0 and st.button("↑", key=f"up_{idx}"):
                    move_up = idx
            with col_d:
                if idx < len(themes) - 1 and st.button("↓", key=f"dn_{idx}"):
                    move_down = idx
            with col_lbl:
                st.markdown(f"**#{idx+1}** {theme['name']}")
        if move_up is not None:
            themes[move_up], themes[move_up-1] = themes[move_up-1], themes[move_up]
            st.rerun()
        if move_down is not None:
            themes[move_down], themes[move_down+1] = themes[move_down+1], themes[move_down]
            st.rerun()

    # Reassign priority by position
    for i, t in enumerate(themes):
        t["priority"] = i + 1

    st.markdown("---")

    # --- Edit / delete each theme ---
    to_delete = None
    for idx, theme in enumerate(themes):
        icons = "🥇" if idx == 0 else ("🥈" if idx == 1 else ("🥉" if idx == 2 else "📌"))
        with st.expander(f"{icons} #{idx + 1} · {theme['name']}"):
            col_name, col_del = st.columns([5, 1])
            with col_name:
                theme["name"] = st.text_input("Name", value=theme["name"], key=f"t_name_{idx}")
            with col_del:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑", key=f"del_t_{idx}", help="Thema löschen"):
                    to_delete = idx

            theme["keywords"] = [
                k.strip()
                for k in st.text_area(
                    "Keywords (ein Keyword pro Zeile)",
                    value="\n".join(theme.get("keywords", [])),
                    height=120,
                    key=f"t_kw_{idx}",
                ).splitlines()
                if k.strip()
            ]
            theme["position"] = st.text_area(
                "Position / Standpunkt",
                value=theme.get("position", ""),
                height=80,
                key=f"t_pos_{idx}",
            )

    if to_delete is not None:
        deleted_name = themes[to_delete]["name"]
        themes.pop(to_delete)
        st.success(f"Thema «{deleted_name}» gelöscht.")
        st.rerun()

    # --- Add new theme ---
    st.markdown("---")
    with st.expander("➕ Neues Thema hinzufügen"):
        new_name = st.text_input("Themenname", key="new_t_name")
        new_kws  = st.text_area("Keywords (ein Keyword pro Zeile)", height=100, key="new_t_kw")
        new_pos  = st.text_area("Position / Standpunkt", height=80, key="new_t_pos")
        if st.button("Thema hinzufügen", key="add_theme_btn"):
            if new_name.strip():
                themes.append({
                    "name":     new_name.strip(),
                    "priority": len(themes) + 1,
                    "keywords": [k.strip() for k in new_kws.splitlines() if k.strip()],
                    "position": new_pos.strip(),
                })
                st.success(f"Thema «{new_name.strip()}» hinzugefügt.")
                st.rerun()
            else:
                st.warning("Bitte einen Themenname angeben.")

    profile["themes"] = themes

# ============================================================
# TAB 4 – WRITING RULES
# ============================================================

with tab_rules:
    st.subheader("Schreibregeln")
    st.caption("Diese Regeln werden in jeden LLM-Prompt eingebettet.")

    rules = profile.get("writing_rules", [])

    # Edit existing
    to_delete_r = None
    for idx, rule in enumerate(rules):
        col_r, col_del = st.columns([5, 1])
        with col_r:
            rules[idx] = st.text_input(
                f"Regel {idx + 1}", value=rule, key=f"rule_{idx}", label_visibility="collapsed"
            )
        with col_del:
            if st.button("🗑", key=f"del_r_{idx}", help="Löschen"):
                to_delete_r = idx

    if to_delete_r is not None:
        rules.pop(to_delete_r)
        st.rerun()

    # Add new rule
    st.markdown("---")
    new_rule = st.text_input("Neue Regel hinzufügen", key="new_rule_input")
    if st.button("➕ Regel hinzufügen", key="add_rule_btn"):
        if new_rule.strip():
            rules.append(new_rule.strip())
            st.success("Regel hinzugefügt.")
            st.rerun()

    profile["writing_rules"] = [r for r in rules if r.strip()]

# ============================================================
# TAB 5 – FEEDS
# ============================================================

with tab_feeds:
    st.subheader("Quellen / Feeds")
    st.caption(
        "RSS-Feeds werden automatisch geparst. "
        "Quellen vom Typ «basic» werden gescrapt. "
        "Deaktivierte Feeds werden beim Laden ignoriert."
    )

    feeds = profile.get("feeds", [])
    FEED_TYPES = ["rss", "basic"]

    # --- Add new feed ---
    with st.expander("➕ Neuen Feed hinzufügen"):
        nf_name    = st.text_input("Anzeigename",    key="nf_name")
        nf_url     = st.text_input("URL",            key="nf_url")
        nf_source  = st.text_input(
            "Source-Kürzel (für internen Gebrauch, z.B. 'zugerzeitung')", key="nf_source"
        )
        nf_type    = st.selectbox("Typ", FEED_TYPES, key="nf_type")
        nf_enabled = st.toggle("Aktiviert", value=True, key="nf_enabled")

        if st.button("Feed hinzufügen", key="add_feed_btn"):
            if nf_name.strip() and nf_url.strip():
                feeds.append(
                    {
                        "name":    nf_name.strip(),
                        "url":     nf_url.strip(),
                        "source":  nf_source.strip() or nf_name.strip().lower().replace(" ", "_"),
                        "type":    nf_type,
                        "enabled": nf_enabled,
                    }
                )
                st.success(f"Feed «{nf_name.strip()}» hinzugefügt.")
                st.rerun()
            else:
                st.warning("Bitte mindestens Name und URL angeben.")

    # --- Edit / delete existing feeds ---
    to_delete_f = None
    for idx, feed in enumerate(feeds):
        icon = "✅" if feed.get("enabled", True) else "⏸️"
        with st.expander(f"{icon} {feed['name']} ({feed['type'].upper()})"):
            col_fa, col_fb = st.columns([3, 1])
            with col_fa:
                feed["name"] = st.text_input("Name", value=feed["name"], key=f"f_name_{idx}")
                feed["url"]  = st.text_input("URL",  value=feed["url"],  key=f"f_url_{idx}")
            with col_fb:
                feed["source"]  = st.text_input(
                    "Source", value=feed.get("source", ""), key=f"f_src_{idx}"
                )
                feed["type"]    = st.selectbox(
                    "Typ", FEED_TYPES,
                    index=FEED_TYPES.index(feed.get("type", "rss")),
                    key=f"f_type_{idx}",
                )
                feed["enabled"] = st.toggle(
                    "Aktiviert", value=feed.get("enabled", True), key=f"f_en_{idx}"
                )

            if st.button(f"🗑 Feed «{feed['name']}» löschen", key=f"del_f_{idx}"):
                to_delete_f = idx

    if to_delete_f is not None:
        deleted_feed = feeds[to_delete_f]["name"]
        feeds.pop(to_delete_f)
        st.success(f"Feed «{deleted_feed}» gelöscht.")
        st.rerun()

    profile["feeds"] = feeds

# ============================================================
# SAVE BUTTON (sticky at the bottom)
# ============================================================

st.divider()
col_save, col_reset, col_spacer = st.columns([1, 1, 3])

with col_save:
    if st.button("💾 Profil speichern", type="primary", use_container_width=True):
        save_profile(profile)
        st.session_state.editor_profile = load_profile()  # reload to confirm write
        st.success("✅ Profil gespeichert. Änderungen sind beim nächsten Feed-Laden aktiv.")

with col_reset:
    if st.button("↩️ Änderungen verwerfen", use_container_width=True):
        st.session_state.editor_profile = load_profile()
        st.rerun()
