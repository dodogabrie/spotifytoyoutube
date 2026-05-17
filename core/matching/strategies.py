from __future__ import annotations

from core.matching.normalize import normalize_title
from core.models import NormalizedTrack


def ytmusic_queries(track: NormalizedTrack) -> list[str]:
    """Ordered list of search queries to try against YouTube Music."""
    primary_artist = track.artists[0] if track.artists else ""
    queries: list[str] = []

    if track.isrc:
        queries.append(track.isrc)

    queries.append(f"{track.title} {primary_artist}".strip())

    normalized = normalize_title(track.title)
    if normalized and normalized != track.title.lower():
        queries.append(f"{normalized} {primary_artist}".strip())

    seen: set[str] = set()
    deduped: list[str] = []
    for q in queries:
        q_clean = q.strip()
        if q_clean and q_clean.lower() not in seen:
            seen.add(q_clean.lower())
            deduped.append(q_clean)
    return deduped
