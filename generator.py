from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from profile import load_profile

load_dotenv()

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY ist nicht gesetzt. "
                "Bitte .env Datei prüfen."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def _get_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o")


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def _build_system_prompt(profile: dict[str, Any]) -> str:
    identity = profile["identity"]
    persona  = profile["persona"]

    avoid = ", ".join(identity["must_avoid"])
    rules = "\n".join(f"- {r}" for r in profile["writing_rules"])
    roles = ", ".join(persona.get("political_roles", []))
    volunteering = ", ".join(persona.get("voluntary_work", []))
    expertise_items = profile.get("expertise", [])
    expertise_block = (
        "\n\nPERSÖNLICHE ERFAHRUNGEN (bei thematischer Relevanz einmal kurz und natürlich einbringen – nicht erzwingen):\n"
        + "\n".join(f"- {e}" for e in expertise_items)
        if expertise_items else ""
    )

    return f"""Du schreibst politische Texte im Namen von {persona['name']}.

ÜBER {persona['name'].upper()}:
- {persona['age']}-jährig, {persona['profession']}
- Wohnhaft in {persona['location']}
- Kandidiert für: {persona['candidacy']}
- Partei: {persona['party']}
- Politische Ämter: {roles}
- Ehrenamtliches Engagement: {volunteering}
- Slogan: «{persona['slogan']}»{expertise_block}

POLITISCHES PROFIL: {identity['political_profile']}

SCHREIBSTIL-ANWEISUNG: {identity.get('tone_instruction', 'Klar positioniert, sachlich, konstruktiv.')}

STRIKT VERMEIDEN: {avoid}

SCHREIBREGELN:
{rules}

Schreibe ausschliesslich auf Deutsch (Schweizer Hochdeutsch, kein «ß»).
Erfinde keine Fakten, Statistiken oder Zitate, die nicht im Artikel stehen.
Der Text soll authentisch nach {persona['name']} klingen – bodenständig, juristisch präzise, lokal verwurzelt."""


def _build_themes_block(matches: list[dict[str, Any]]) -> str:
    if not matches:
        return ""
    lines = ["SEINE POSITIONEN ZU DEN RELEVANTEN THEMEN (nach Wichtigkeit geordnet – bei Zielkonflikten hat das erstgenannte Thema Vorrang):"]
    for m in matches:
        lines.append(
            f"- {m['theme']} (Treffer: {', '.join(m['hits'])}): {m['position']}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Comment generator (≤ 1500 characters)
# ---------------------------------------------------------------------------

def generate_comment(article: dict[str, Any], matches: list[dict[str, Any]]) -> str:
    """
    Online comment: direct, position clear from line 1, ≤ 1500 chars.
    Posted directly under an existing article — context is known to readers.
    """
    profile = load_profile()
    themes_block = _build_themes_block(matches)

    user_prompt = f"""Schreibe einen Online-Kommentar zu folgendem Artikel.

ARTIKEL-TITEL: {article['title']}
ARTIKEL-INHALT: {article['summary'] or '(kein Volltext verfügbar)'}

{themes_block}

ANFORDERUNGEN:
- Maximal 1500 Zeichen inklusive Leerzeichen – halte diese Grenze strikt ein
- KLARE HALTUNG ab dem ersten Satz – der Leser soll sofort wissen, wo du stehst
- Kein «einerseits/andererseits» – du vertrittst eine Position, du moderierst nicht
- Reaktiv: beziehe dich konkret auf diesen Artikel
- Kontext ist dem Leser bekannt – nicht nochmals zusammenfassen
- Kein Angriff auf Personen, aber Kritik an Zuständen und Entscheiden ist erwünscht
- Schluss mit einer konkreten Forderung oder einem klaren Appell
- Ich-Perspektive
- Bringe einmal kurz und natürlich eine persönliche Erfahrung ein, aus der du sprichst – nur wenn sie zum Thema passt, nie erzwungen

Schreibe nur den Kommentartext, ohne Titel oder Überschrift."""

    response = _get_client().chat.completions.create(
        model=_get_model(),
        messages=[
            {"role": "system", "content": _build_system_prompt(profile)},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.7,
        max_completion_tokens=600,
    )

    text = response.choices[0].message.content.strip()
    if len(text) > 1500:
        text = text[:1497].rsplit(" ", 1)[0] + "..."
    return text


# ---------------------------------------------------------------------------
# Letter-to-editor generator (≤ 2000 characters)
# ---------------------------------------------------------------------------

def generate_letter(article: dict[str, Any], matches: list[dict[str, Any]]) -> str:
    """
    Letter to editor: rounded, contextual, builds to position, ≤ 2000 chars.
    Standalone submission — readers may not have seen the original article.
    """
    profile = load_profile()
    themes_block = _build_themes_block(matches)

    user_prompt = f"""Schreibe einen Leserbrief zu folgendem Artikel.

ARTIKEL-TITEL: {article['title']}
ARTIKEL-INHALT: {article['summary'] or '(kein Volltext verfügbar)'}

{themes_block}

ANFORDERUNGEN:
- Maximal 2000 Zeichen inklusive Leerzeichen – halte diese Grenze strikt ein
- Beginne mit einer kurzen, fairen Einordnung des Artikels (1–2 Sätze) – dann sofort zur Position
- KLARE HALTUNG: Der Leserbrief muss erkennbar machen, wofür du stehst und was du forderst
- Kein «auf der einen Seite... auf der anderen Seite» – du vertrittst einen Standpunkt
- «Fair» bedeutet: sachlich korrekt, nicht: ausgewogen oder neutral
- Eigenständiger Text – auch ohne Kenntnis des Artikels verständlich
- Schluss mit einer konkreten politischen Forderung oder einem klaren Appell
- Ich-Perspektive, kein Absender oder Grussformel
- Bringe einmal kurz und natürlich eine persönliche Erfahrung ein, aus der du sprichst – nur wenn sie zum Thema passt, nie erzwungen

Schreibe nur den Leserbrieftext, ohne Titel oder Betreffzeile."""

    response = _get_client().chat.completions.create(
        model=_get_model(),
        messages=[
            {"role": "system", "content": _build_system_prompt(profile)},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.7,
        max_completion_tokens=800,
    )

    text = response.choices[0].message.content.strip()
    if len(text) > 2000:
        text = text[:1997].rsplit(" ", 1)[0] + "..."
    return text
