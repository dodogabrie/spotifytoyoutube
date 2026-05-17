from core.matching.scoring import score_match
from core.models import NormalizedTrack


def _track(title, artists, duration_ms=None, isrc=None):
    return NormalizedTrack(
        source_id="x",
        title=title,
        artists=artists,
        duration_ms=duration_ms,
        isrc=isrc,
    )


def test_identical_tracks_score_near_one():
    a = _track("Wonderwall", ["Oasis"], 258_000)
    b = _track("Wonderwall", ["Oasis"], 258_000)
    assert score_match(a, b) >= 0.95


def test_isrc_match_adds_bonus():
    a = _track("Wonderwall", ["Oasis"], 258_000, isrc="GBARL9500001")
    b = _track("Wonderwall - Remaster", ["Oasis"], 257_500, isrc="GBARL9500001")
    assert score_match(a, b) > 0.9


def test_different_artists_score_low():
    a = _track("Wonderwall", ["Oasis"], 258_000)
    b = _track("Wonderwall", ["Random Cover Artist"], 258_000)
    assert score_match(a, b) < 0.85


def test_unknown_duration_is_neutral():
    a = _track("Hello", ["Adele"], None)
    b = _track("Hello", ["Adele"], None)
    s = score_match(a, b)
    assert 0.85 <= s <= 1.0
