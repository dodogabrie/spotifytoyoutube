from __future__ import annotations

import logging
from typing import Any

import spotipy

from core.matching.scoring import score_match
from core.models import MatchResult, NormalizedTrack

logger = logging.getLogger(__name__)


def _candidate_from_item(item: dict[str, Any]) -> NormalizedTrack:
    artists = [a.get("name", "") for a in item.get("artists") or [] if a.get("name")]
    isrc = (item.get("external_ids") or {}).get("isrc")
    return NormalizedTrack(
        source_id=item["id"],
        title=item.get("name", ""),
        artists=artists,
        album=(item.get("album") or {}).get("name"),
        duration_ms=item.get("duration_ms"),
        isrc=isrc,
    )


def _search(sp: spotipy.Spotify, query: str, limit: int = 5) -> list[NormalizedTrack]:
    page = sp.search(q=query, type="track", limit=limit)
    items = ((page or {}).get("tracks") or {}).get("items") or []
    return [_candidate_from_item(it) for it in items if it.get("id")]


def _best(track: NormalizedTrack, candidates: list[NormalizedTrack]) -> tuple[NormalizedTrack, float] | None:
    best: tuple[NormalizedTrack, float] | None = None
    for c in candidates:
        s = score_match(track, c)
        if best is None or s > best[1]:
            best = (c, s)
    return best


def search_track(sp: spotipy.Spotify, track: NormalizedTrack, threshold: float) -> MatchResult:
    """Search Spotify for the best match of a NormalizedTrack."""
    primary_artist = track.artists[0] if track.artists else ""

    candidates: list[NormalizedTrack] = []
    if track.isrc:
        candidates += _search(sp, f"isrc:{track.isrc}", limit=3)
    if not candidates:
        # Most-precise query: explicit field qualifiers
        q1 = f'track:"{track.title}"'
        if primary_artist:
            q1 += f' artist:"{primary_artist}"'
        candidates += _search(sp, q1, limit=5)
    if not candidates:
        # Fallback: free-text
        candidates += _search(sp, f"{track.title} {primary_artist}".strip(), limit=5)

    best = _best(track, candidates)
    if best is None:
        return MatchResult(track=track, target_id=None, result_type="none", score=0.0)

    candidate, score = best
    if score < threshold:
        return MatchResult(
            track=track,
            target_id=None,
            result_type="none",
            score=score,
            candidate_title=candidate.title,
            candidate_artists=candidate.artists,
        )
    return MatchResult(
        track=track,
        target_id=candidate.source_id,
        result_type="track",
        score=score,
        candidate_title=candidate.title,
        candidate_artists=candidate.artists,
    )
