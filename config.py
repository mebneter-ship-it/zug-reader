from __future__ import annotations

# ---------------------------------------------------------------------------
# RSS / Scraping Sources
# ---------------------------------------------------------------------------

RSS_FEEDS = [
    {
        "name": "Zuger Zeitung – Zug",
        "url": "https://www.zugerzeitung.ch/zentralschweiz/zug.rss",
        "source": "zugerzeitung",
        "type": "rss",
    },
    {
        "name": "Zuger Zeitung – Zentralschweiz",
        "url": "https://www.zugerzeitung.ch/zentralschweiz.rss",
        "source": "zugerzeitung",
        "type": "rss",
    },
    {
        "name": "Zuger Zeitung – Leserbriefe",
        "url": "https://www.zugerzeitung.ch/meinung/leserbriefe.rss",
        "source": "zugerzeitung",
        "type": "rss",
    },
    {
        "name": "zentralplus – Zug",
        "url": "https://www.zentralplus.ch/zug/",
        "source": "zentralplus",
        "type": "basic",
    },
]

# ---------------------------------------------------------------------------
# Campaign Profile
# ---------------------------------------------------------------------------

CAMPAIGN_PROFILE = {
    "identity": {
        "political_profile": (
            "linksbürgerlich, sachlich, konstruktiv, lokal verankert, juristisch sauber"
        ),
        "must_have_tone": [
            "sachlich",
            "konstruktiv",
            "bürgernah",
            "lokal verankert",
            "plausibel",
            "ruhig",
        ],
        "must_avoid": [
            "unbelegte Tatsachenbehauptungen",
            "erfundene Zahlen",
            "persönliche Angriffe",
            "Polemik",
            "Parteisprech",
            "rechtlich unsaubere Zuspitzungen",
        ],
    },
    "themes": [
        {
            "name": "Wohnraum",
            "priority": 1,
            "keywords": [
                "wohnraum", "miete", "mieten", "wohnen", "überbauung", "verdichtung",
                "raumplanung", "familienwohnungen", "bezahlbar", "wohnungsmarkt",
            ],
            "position": (
                "Zug braucht mehr Wohnraum, der bezahlbar, nachhaltig und gut "
                "in die Gemeinden integriert ist."
            ),
        },
        {
            "name": "Wirtschaft mit Verantwortung",
            "priority": 2,
            "keywords": [
                "wirtschaft", "unternehmen", "innovation", "arbeitsplätze", "standort",
                "fachkräfte", "ausbildung", "ansiedlung", "kmu",
            ],
            "position": (
                "Zug soll wirtschaftlich stark bleiben, aber Wachstum muss Verantwortung "
                "für Ausbildung, Wohnraum und Lebensqualität mittragen."
            ),
        },
        {
            "name": "Lebensqualität und Zusammenhalt",
            "priority": 3,
            "keywords": [
                "lebensqualität", "gemeinde", "nachbarschaft", "familien", "ältere menschen",
                "freiwilligenarbeit", "zusammenhalt", "kiss", "betreuung",
            ],
            "position": (
                "Ein erfolgreicher Kanton braucht nicht nur Wohlstand, sondern auch "
                "gesellschaftlichen Zusammenhalt und starke lokale Strukturen."
            ),
        },
        {
            "name": "Gesundheit und Prämien",
            "priority": 4,
            "keywords": [
                "krankenkasse", "prämien", "gesundheit", "pflege", "versorgung",
                "prävention", "betreuung", "kosten",
            ],
            "position": (
                "Ein gutes Gesundheitssystem muss zugänglich, bezahlbar und "
                "alltagstauglich bleiben."
            ),
        },
        {
            "name": "Sicherheit und Rechtsstaat",
            "priority": 5,
            "keywords": [
                "sicherheit", "kriminalität", "rechtsstaat", "gericht", "justiz", "ordnung",
            ],
            "position": (
                "Sicherheit und Rechtsstaat müssen konsequent, glaubwürdig und ohne "
                "populistische Zuspitzung gewährleistet werden."
            ),
        },
        {
            "name": "Integration, Ausbildung, Infrastruktur",
            "priority": 6,
            "keywords": [
                "integration", "schule", "schulraum", "infrastruktur", "verkehr",
                "zuwanderung", "berufsbildung", "ausbildungsplätze",
            ],
            "position": (
                "Wachstum und Zuwanderung müssen mit funktionierender Infrastruktur, "
                "Integration und Ausbildungsqualität Schritt halten."
            ),
        },
    ],
    "writing_rules": [
        "Immer fair in der Einordnung des Ausgangsbeitrags.",
        "Wenn möglich mit Bezug zu Zug, Risch oder einer Zuger Gemeinde.",
        "Konkretes Problem benennen und konstruktive Perspektive formulieren.",
        "Nur Fakten aus Artikel oder freigegebenem Profil verwenden.",
        "Keine zusätzlichen Statistiken oder Zitate erfinden.",
    ],
}

# ---------------------------------------------------------------------------
# Scoring thresholds (adjust to taste)
# ---------------------------------------------------------------------------

SCORE_HIGH = 20   # shown in green
SCORE_MED  = 8    # shown in orange
# below SCORE_MED  → shown in grey
