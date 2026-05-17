from __future__ import annotations

import re
import unicodedata

_PARENS_RE = re.compile(r"\s*[\(\[].*?[\)\]]\s*")
_DASH_TAGS_RE = re.compile(
    r"\s*-\s*(remaster(ed)?(\s*\d{2,4})?|live|radio edit|single version|"
    r"deluxe( edition)?|mono|stereo|version|bonus track)\b.*$",
    flags=re.IGNORECASE,
)
_FEAT_RE = re.compile(r"\s*(\(|\[)?\s*(feat\.?|ft\.?)\s+[^)\]]+(\)|\])?\s*", flags=re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalize_title(title: str) -> str:
    """Aggressively normalize a track title for matching purposes."""
    t = title
    t = _FEAT_RE.sub(" ", t)
    t = _PARENS_RE.sub(" ", t)
    t = _DASH_TAGS_RE.sub(" ", t)
    t = strip_accents(t).lower()
    t = _WHITESPACE_RE.sub(" ", t).strip()
    return t


def normalize_artist(artist: str) -> str:
    a = strip_accents(artist).lower()
    a = _WHITESPACE_RE.sub(" ", a).strip()
    return a
