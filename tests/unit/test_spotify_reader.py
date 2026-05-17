from unittest.mock import MagicMock

from core.spotify.reader import fetch_playlist_tracks, list_user_playlists


def _make_sp(user_id="me"):
    sp = MagicMock()
    sp.current_user.return_value = {"id": user_id}
    return sp


def test_list_user_playlists_filters_own_when_requested():
    sp = _make_sp("me")
    sp.current_user_playlists.return_value = {
        "items": [
            {"id": "p1", "name": "Mine", "owner": {"id": "me"}, "tracks": {"total": 3}},
            {"id": "p2", "name": "Friend's", "owner": {"id": "someone-else"}, "tracks": {"total": 1}},
        ],
        "next": None,
    }
    out = list_user_playlists(sp, own_only=True)
    assert [p.id for p in out] == ["p1"]


def test_list_user_playlists_paginates():
    sp = _make_sp("me")
    sp.current_user_playlists.side_effect = [
        {"items": [{"id": "p1", "name": "A", "owner": {"id": "me"}, "tracks": {"total": 1}}], "next": "url"},
        {"items": [{"id": "p2", "name": "B", "owner": {"id": "me"}, "tracks": {"total": 1}}], "next": None},
    ]
    out = list_user_playlists(sp, own_only=True)
    assert [p.id for p in out] == ["p1", "p2"]


def test_fetch_playlist_tracks_skips_local_and_episodes():
    sp = _make_sp()
    sp.playlist_items.return_value = {
        "items": [
            {"track": {"id": "t1", "name": "Real", "artists": [{"name": "A"}], "duration_ms": 1000, "type": "track", "external_ids": {"isrc": "ABC"}}},
            {"track": {"id": "t2", "name": "Local", "artists": [], "is_local": True, "type": "track"}},
            {"track": {"id": "t3", "name": "Podcast", "type": "episode"}},
            {"track": None},
        ],
        "next": None,
    }
    tracks = fetch_playlist_tracks(sp, "p1")
    assert [t.source_id for t in tracks] == ["t1"]
    assert tracks[0].isrc == "ABC"
