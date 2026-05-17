from __future__ import annotations

from typing import Iterable

from core.adapters.base import SourceAdapter, TargetAdapter
from core.models import (
    IdempotencyMode,
    MatchResult,
    NormalizedTrack,
    Playlist,
    Provider,
    TransferDirection,
    TransferProgressEvent,
)
from core.transfer.engine import TransferEngine


class FakeSource(SourceAdapter):
    provider = Provider.SPOTIFY

    def __init__(self, playlists, tracks_by_id):
        self._playlists = playlists
        self._tracks = tracks_by_id

    def list_user_playlists(self, own_only=True):
        return list(self._playlists)

    def fetch_playlist_tracks(self, playlist_id):
        return list(self._tracks.get(playlist_id, []))


class FakeTarget(TargetAdapter):
    provider = Provider.YTMUSIC

    def __init__(self, existing_names=None, mismatch_titles=()):
        self.existing = dict(existing_names or {})
        self.created = []
        self.added = {}
        self.cleared = []
        self.next_id_counter = 0
        self._mismatch = set(mismatch_titles)

    def search_track(self, track: NormalizedTrack) -> MatchResult:
        if track.title in self._mismatch:
            return MatchResult(track=track, target_id=None, result_type="none", score=0.0)
        # echo back a deterministic target id derived from the source id
        return MatchResult(
            track=track,
            target_id=f"tgt-{track.source_id}",
            result_type="song",
            score=0.95,
            candidate_title=track.title,
            candidate_artists=track.artists,
        )

    def find_existing_playlist_by_name(self, name):
        return self.existing.get(name)

    def create_playlist(self, name, description=None, public=False):
        self.next_id_counter += 1
        new_id = f"new-{self.next_id_counter}"
        self.created.append((new_id, name, public))
        self.existing[name] = new_id
        return new_id

    def add_tracks(self, playlist_id, target_ids: Iterable[str]):
        self.added.setdefault(playlist_id, []).extend(list(target_ids))

    def clear_playlist(self, playlist_id):
        self.cleared.append(playlist_id)

    def playlist_url(self, playlist_id):
        return f"https://example.test/{playlist_id}"


def _track(i):
    return NormalizedTrack(
        source_id=f"t{i}",
        title=f"Song {i}",
        artists=["Artist"],
        duration_ms=200_000,
    )


def test_engine_transfers_two_playlists_create_new():
    p1 = Playlist(id="p1", name="Mix A", track_count=2)
    p2 = Playlist(id="p2", name="Mix B", track_count=1)
    source = FakeSource(
        playlists=[p1, p2],
        tracks_by_id={
            "p1": [_track(1), _track(2)],
            "p2": [_track(3)],
        },
    )
    target = FakeTarget()
    events: list[TransferProgressEvent] = []
    engine = TransferEngine(
        source=source,
        target=target,
        direction=TransferDirection.SPOTIFY_TO_YTMUSIC,
        progress_callback=events.append,
    )
    report = engine.transfer(["p1", "p2"], idempotency=IdempotencyMode.CREATE_NEW)

    assert report.total_matched == 3
    assert report.total_unmatched == 0
    assert report.direction is TransferDirection.SPOTIFY_TO_YTMUSIC
    assert {n for _, n, _ in target.created} == {"Mix A", "Mix B"}
    assert any(e.type == "job_done" for e in events)
    assert sum(1 for e in events if e.type == "track_matched") == 3


def test_engine_records_unmatched_tracks():
    p = Playlist(id="p1", name="Mix")
    source = FakeSource(
        playlists=[p],
        tracks_by_id={"p1": [_track(1), _track(2)]},
    )
    target = FakeTarget(mismatch_titles={"Song 2"})
    engine = TransferEngine(
        source=source,
        target=target,
        direction=TransferDirection.SPOTIFY_TO_YTMUSIC,
    )
    report = engine.transfer(["p1"])

    assert report.total_matched == 1
    assert report.total_unmatched == 1
    outcome = report.playlists[0]
    assert outcome.unmatched[0].track.title == "Song 2"


def test_engine_works_in_reverse_direction():
    p = Playlist(id="ytp1", name="From YT")
    source = FakeSource(
        playlists=[p],
        tracks_by_id={"ytp1": [_track(10)]},
    )
    target = FakeTarget()
    engine = TransferEngine(
        source=source,
        target=target,
        direction=TransferDirection.YTMUSIC_TO_SPOTIFY,
    )
    report = engine.transfer(["ytp1"])
    assert report.direction is TransferDirection.YTMUSIC_TO_SPOTIFY
    assert report.total_matched == 1


def test_engine_append_mode_uses_existing_playlist():
    p = Playlist(id="p1", name="Mix")
    source = FakeSource(
        playlists=[p],
        tracks_by_id={"p1": [_track(1)]},
    )
    target = FakeTarget(existing_names={"Mix": "already-there"})
    engine = TransferEngine(
        source=source,
        target=target,
        direction=TransferDirection.SPOTIFY_TO_YTMUSIC,
    )
    report = engine.transfer(["p1"], idempotency=IdempotencyMode.APPEND)
    assert target.created == []
    assert target.added == {"already-there": ["tgt-t1"]}
    assert report.playlists[0].action == "appended"


def test_engine_skip_if_exists():
    p = Playlist(id="p1", name="Mix")
    source = FakeSource(
        playlists=[p],
        tracks_by_id={"p1": [_track(1)]},
    )
    target = FakeTarget(existing_names={"Mix": "already-there"})
    engine = TransferEngine(
        source=source,
        target=target,
        direction=TransferDirection.SPOTIFY_TO_YTMUSIC,
    )
    report = engine.transfer(["p1"], idempotency=IdempotencyMode.SKIP_IF_EXISTS)
    assert target.created == []
    assert target.added == {}
    assert report.playlists[0].action == "skipped"
    assert report.playlists[0].skipped_count == 1
