from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from core.models import Playlist, TransferReport


def print_playlists(playlists: list[Playlist], console: Console | None = None) -> None:
    console = console or Console()
    table = Table(title="Source playlists", show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Tracks", justify="right")
    table.add_column("Visibility")
    for i, p in enumerate(playlists, start=1):
        visibility = (
            "collaborative"
            if p.collaborative
            else ("public" if p.public else "private" if p.public is False else "—")
        )
        table.add_row(str(i), p.name, str(p.track_count or "?"), visibility)
    console.print(table)


def print_report_summary(
    report: TransferReport,
    report_path: Path,
    target_url_builder=None,
    console: Console | None = None,
) -> None:
    console = console or Console()
    console.rule("[bold]Transfer summary")
    console.print(f"Direction:   [bold]{report.direction.value}[/bold]")
    console.print(f"Started:     {report.started_at.isoformat()}")
    console.print(f"Finished:    {report.finished_at.isoformat()}")
    console.print(f"Idempotency: {report.idempotency.value}")
    console.print(
        f"Totals:      matched={report.total_matched}  "
        f"unmatched={report.total_unmatched}  skipped={report.total_skipped}"
    )

    table = Table(show_lines=False)
    table.add_column("Source playlist", style="bold")
    table.add_column("Target", style="cyan")
    table.add_column("Action")
    table.add_column("Matched", justify="right")
    table.add_column("Unmatched", justify="right")
    for outcome in report.playlists:
        target_label = outcome.target_playlist_name
        if target_url_builder and outcome.target_playlist_id:
            target_label = target_url_builder(outcome.target_playlist_id)
        table.add_row(
            outcome.source_playlist.name,
            target_label,
            outcome.action,
            str(outcome.matched_count),
            str(outcome.unmatched_count),
        )
    console.print(table)
    console.print(f"Report saved to: [italic]{report_path}[/italic]")
