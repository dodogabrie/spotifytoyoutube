from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from core.adapters.base import TargetAdapter
from core.models import IdempotencyMode

logger = logging.getLogger(__name__)

ResolvedAction = Literal["created", "appended", "replaced", "skipped"]


@dataclass
class TargetResolution:
    playlist_id: str | None
    action: ResolvedAction
    name_used: str


def _next_available_name(target: TargetAdapter, base: str) -> str:
    if target.find_existing_playlist_by_name(base) is None:
        return base
    for i in range(2, 100):
        candidate = f"{base} ({i})"
        if target.find_existing_playlist_by_name(candidate) is None:
            return candidate
    return f"{base} (copy)"


def resolve_target(
    target: TargetAdapter,
    desired_name: str,
    description: str | None,
    public: bool,
    mode: IdempotencyMode,
) -> TargetResolution:
    existing = target.find_existing_playlist_by_name(desired_name)

    if mode == IdempotencyMode.SKIP_IF_EXISTS and existing:
        logger.info("Playlist %r exists on target; skipping per SKIP_IF_EXISTS", desired_name)
        return TargetResolution(playlist_id=existing, action="skipped", name_used=desired_name)

    if mode == IdempotencyMode.APPEND and existing:
        return TargetResolution(playlist_id=existing, action="appended", name_used=desired_name)

    if mode == IdempotencyMode.REPLACE and existing:
        target.clear_playlist(existing)
        return TargetResolution(playlist_id=existing, action="replaced", name_used=desired_name)

    name_to_use = (
        desired_name
        if existing is None
        else _next_available_name(target, desired_name)
    )
    new_id = target.create_playlist(name_to_use, description=description, public=public)
    return TargetResolution(playlist_id=new_id, action="created", name_used=name_to_use)
