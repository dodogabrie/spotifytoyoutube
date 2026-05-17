from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from InquirerPy import inquirer
from rich.console import Console

from cli.progress import CLIProgress
from cli.renderers import print_playlists, print_report_summary
from core.adapters.spotify_adapter import SpotifyAdapter
from core.adapters.ytmusic_adapter import YTMusicAdapter
from core.auth.spotify_auth import build_cli_auth_manager
from core.auth.ytmusic_auth import start_device_flow, wait_for_authorization
from core.config import get_settings
from core.exceptions import AuthError, TransferError
from core.models import IdempotencyMode, Playlist, TransferDirection
from core.spotify.client import get_spotify_client
from core.transfer.direction import build_adapters
from core.transfer.engine import TransferEngine
from core.transfer.reporter import write_report
from core.ytmusic.client import get_ytmusic_client_from_file

logger = logging.getLogger(__name__)
console = Console()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def _spotify_login() -> None:
    settings = get_settings()
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        console.print(
            "[red]Spotify client id/secret missing. Set SPOTIFY_CLIENT_ID and "
            "SPOTIFY_CLIENT_SECRET in your .env (copy from .env.example).[/red]"
        )
        return
    auth_manager = build_cli_auth_manager(settings)
    token_info = auth_manager.get_access_token(as_dict=True)
    if not token_info:
        raise AuthError("Spotify authorization failed")
    console.print("[green]✓[/green] Spotify connected.")


def _ytmusic_login() -> None:
    settings = get_settings()
    if not settings.ytmusic_client_id or not settings.ytmusic_client_secret:
        console.print(
            "[red]YouTube Music OAuth credentials missing. Set YTMUSIC_CLIENT_ID "
            "and YTMUSIC_CLIENT_SECRET in your .env (Google Cloud Console: create "
            "an OAuth client of type 'TVs and Limited Input devices' and enable "
            "YouTube Data API v3).[/red]"
        )
        return
    settings.ensure_dirs()
    flow = start_device_flow(settings.ytmusic_client_id)
    console.print(
        f"Open [bold]{flow.verification_url}[/bold] and enter code: "
        f"[bold yellow]{flow.user_code}[/bold yellow]"
    )
    creds = wait_for_authorization(
        settings.ytmusic_client_id,
        settings.ytmusic_client_secret,
        flow,
    )
    target = settings.ytmusic_oauth_path
    target.write_text(json.dumps(creds, indent=2))
    target.chmod(0o600)
    console.print(f"[green]✓[/green] YouTube Music connected ({target}).")


# ---------------------------------------------------------------------------
# Adapter factory based on current credentials on disk
# ---------------------------------------------------------------------------


def _build_adapters() -> tuple[SpotifyAdapter, YTMusicAdapter]:
    settings = get_settings()
    settings.ensure_dirs()

    if not settings.spotify_cache_path.exists():
        raise AuthError("Spotify is not authenticated yet. Run 'Login Spotify' first.")
    if not settings.ytmusic_oauth_path.exists():
        raise AuthError("YouTube Music is not authenticated yet. Run 'Login YouTube Music' first.")

    auth_manager = build_cli_auth_manager(settings)
    sp = get_spotify_client(auth_manager)
    spotify_adapter = SpotifyAdapter(sp, score_threshold=settings.match_score_threshold)

    yt = get_ytmusic_client_from_file(
        settings.ytmusic_oauth_path,
        settings.ytmusic_client_id,
        settings.ytmusic_client_secret,
    )
    ytmusic_adapter = YTMusicAdapter(yt, score_threshold=settings.match_score_threshold)

    return spotify_adapter, ytmusic_adapter


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


def _pick_direction() -> TransferDirection:
    answer = inquirer.select(
        message="Transfer direction:",
        choices=[
            {"name": "Spotify → YouTube Music", "value": TransferDirection.SPOTIFY_TO_YTMUSIC},
            {"name": "YouTube Music → Spotify", "value": TransferDirection.YTMUSIC_TO_SPOTIFY},
        ],
        default=TransferDirection.SPOTIFY_TO_YTMUSIC,
    ).execute()
    return answer


def _pick_playlists(playlists: list[Playlist]) -> list[Playlist]:
    if not playlists:
        console.print("[yellow]No playlists found on the source account.[/yellow]")
        return []
    print_playlists(playlists, console=console)
    selected: list[Playlist] = inquirer.checkbox(
        message="Select playlists to transfer:",
        choices=[{"name": f"{p.name}  ({p.track_count or '?'} tracks)", "value": p} for p in playlists],
        instruction="(space to toggle, enter to confirm)",
        validate=lambda r: len(r) > 0 or "Pick at least one playlist",
    ).execute()
    return selected


def _pick_idempotency() -> IdempotencyMode:
    return inquirer.select(
        message="If a playlist with the same name already exists on the target, what to do?",
        choices=[
            {"name": "Create new (suffix on collision)", "value": IdempotencyMode.CREATE_NEW},
            {"name": "Append to existing", "value": IdempotencyMode.APPEND},
            {"name": "Replace (wipe + refill)", "value": IdempotencyMode.REPLACE},
            {"name": "Skip if exists", "value": IdempotencyMode.SKIP_IF_EXISTS},
        ],
        default=IdempotencyMode.CREATE_NEW,
    ).execute()


def _do_transfer() -> None:
    direction = _pick_direction()
    spotify_adapter, ytmusic_adapter = _build_adapters()
    source, target = build_adapters(direction, spotify_adapter, ytmusic_adapter)

    console.print(f"Reading playlists from [bold]{source.provider.value}[/bold] ...")
    playlists = source.list_user_playlists(own_only=True)
    selected = _pick_playlists(playlists)
    if not selected:
        return
    mode = _pick_idempotency()

    confirm = inquirer.confirm(
        message=f"Transfer {len(selected)} playlist(s) to {target.provider.value}? "
        f"(idempotency={mode.value})",
        default=True,
    ).execute()
    if not confirm:
        return

    engine_target_ids = [p.id for p in selected]

    with CLIProgress(console=console) as progress:
        engine = TransferEngine(
            source=source,
            target=target,
            direction=direction,
            progress_callback=progress.on_event,
        )
        try:
            report = engine.transfer(engine_target_ids, idempotency=mode)
        except TransferError as exc:
            console.print(f"[bold red]Transfer failed:[/bold red] {exc}")
            return

    report_path = write_report(report)
    print_report_summary(
        report,
        report_path,
        target_url_builder=target.playlist_url,
        console=console,
    )


def _show_last_report() -> None:
    settings = get_settings()
    if not settings.reports_dir.exists():
        console.print("[yellow]No reports yet.[/yellow]")
        return
    reports = sorted(settings.reports_dir.glob("report-*.json"))
    if not reports:
        console.print("[yellow]No reports yet.[/yellow]")
        return
    latest = reports[-1]
    console.print(f"Latest report: [bold]{latest}[/bold]")
    data = json.loads(latest.read_text())
    console.print_json(data=data)


def run_interactive() -> None:
    """Top-level interactive menu loop."""
    while True:
        try:
            choice = inquirer.select(
                message="Spotify ⇄ YouTube Music",
                choices=[
                    {"name": "Login Spotify", "value": "login_spotify"},
                    {"name": "Login YouTube Music", "value": "login_ytmusic"},
                    {"name": "Transfer playlists", "value": "transfer"},
                    {"name": "Show last report", "value": "last_report"},
                    {"name": "Exit", "value": "exit"},
                ],
            ).execute()
        except KeyboardInterrupt:
            return

        try:
            if choice == "login_spotify":
                _spotify_login()
            elif choice == "login_ytmusic":
                _ytmusic_login()
            elif choice == "transfer":
                _do_transfer()
            elif choice == "last_report":
                _show_last_report()
            elif choice == "exit":
                return
        except AuthError as exc:
            console.print(f"[bold red]Auth error:[/bold red] {exc}")
        except TransferError as exc:
            console.print(f"[bold red]Transfer error:[/bold red] {exc}")
        except Exception as exc:  # pragma: no cover - safety net
            logger.exception("Unexpected error")
            console.print(f"[bold red]Unexpected error:[/bold red] {exc}")
