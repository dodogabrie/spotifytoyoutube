from __future__ import annotations

from rapidfuzz import fuzz

from core.matching.normalize import normalize_artist, normalize_title
from core.models import NormalizedTrack

W_TITLE = 0.5
W_ARTIST = 0.3
W_DURATION = 0.15
ISRC_BONUS = 0.10


def _title_sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return fuzz.token_set_ratio(normalize_title(a), normalize_title(b)) / 100.0


def _artist_sim(a_list: list[str], b_list: list[str]) -> float:
    if not a_list or not b_list:
        return 0.0
    best = 0.0
    for a in a_list:
        na = normalize_artist(a)
        for b in b_list:
            nb = normalize_artist(b)
            sim = fuzz.token_set_ratio(na, nb) / 100.0
            if sim > best:
                best = sim
    return best


def _duration_sim(a_ms: int | None, b_ms: int | None, tolerance_ms: int = 15000) -> float:
    if a_ms is None or b_ms is None:
        return 0.5  # neutral when unknown
    delta = abs(a_ms - b_ms)
    return max(0.0, 1.0 - delta / tolerance_ms)


def score_match(query: NormalizedTrack, candidate: NormalizedTrack) -> float:
    title = _title_sim(query.title, candidate.title)
    artist = _artist_sim(query.artists, candidate.artists)
    duration = _duration_sim(query.duration_ms, candidate.duration_ms)

    score = W_TITLE * title + W_ARTIST * artist + W_DURATION * duration
    if query.isrc and candidate.isrc and query.isrc.upper() == candidate.isrc.upper():
        score = min(1.0, score + ISRC_BONUS)
    return round(score, 4)
