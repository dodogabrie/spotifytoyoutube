from unittest.mock import MagicMock

from core.models import IdempotencyMode
from core.transfer.idempotency import resolve_target


def _target(existing=None, created="new-id"):
    t = MagicMock()
    t.find_existing_playlist_by_name.side_effect = lambda name: existing.get(name) if existing else None
    t.create_playlist.return_value = created
    return t


def test_create_new_when_no_collision():
    t = _target(existing={})
    res = resolve_target(t, "My Mix", None, False, IdempotencyMode.CREATE_NEW)
    assert res.action == "created"
    assert res.name_used == "My Mix"
    assert res.playlist_id == "new-id"


def test_create_new_uses_suffix_on_collision():
    t = _target(existing={"My Mix": "old"})
    t.create_playlist.return_value = "fresh"
    res = resolve_target(t, "My Mix", None, False, IdempotencyMode.CREATE_NEW)
    assert res.action == "created"
    assert res.name_used == "My Mix (2)"
    assert res.playlist_id == "fresh"


def test_append_reuses_existing():
    t = _target(existing={"My Mix": "old"})
    res = resolve_target(t, "My Mix", None, False, IdempotencyMode.APPEND)
    assert res.action == "appended"
    assert res.playlist_id == "old"
    t.create_playlist.assert_not_called()


def test_replace_clears_then_reuses():
    t = _target(existing={"My Mix": "old"})
    res = resolve_target(t, "My Mix", None, False, IdempotencyMode.REPLACE)
    assert res.action == "replaced"
    assert res.playlist_id == "old"
    t.clear_playlist.assert_called_once_with("old")


def test_skip_if_exists():
    t = _target(existing={"My Mix": "old"})
    res = resolve_target(t, "My Mix", None, False, IdempotencyMode.SKIP_IF_EXISTS)
    assert res.action == "skipped"
    assert res.playlist_id == "old"
    t.create_playlist.assert_not_called()
