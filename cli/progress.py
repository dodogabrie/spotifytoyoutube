from __future__ import annotations

from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

from core.models import TransferProgressEvent


class CLIProgress:
    """Console progress reporter consuming TransferProgressEvent stream."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self._progress: Progress | None = None
        self._overall_id = None
        self._playlist_id = None

    def __enter__(self):
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[stage]}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("{task.description}"),
            console=self.console,
            transient=False,
        )
        self._progress.__enter__()
        return self

    def __exit__(self, *exc):
        if self._progress:
            self._progress.__exit__(*exc)
            self._progress = None

    def on_event(self, event: TransferProgressEvent) -> None:
        if self._progress is None:
            return
        if event.type == "job_started":
            self._overall_id = self._progress.add_task(
                "Overall",
                stage="job",
                total=event.total or 1,
            )
        elif event.type == "playlist_started":
            if self._playlist_id is not None:
                try:
                    self._progress.remove_task(self._playlist_id)
                except KeyError:
                    pass
            self._playlist_id = self._progress.add_task(
                event.playlist_name or "playlist",
                stage="playlist",
                total=event.total or event.total or 1,
            )
        elif event.type in ("track_matched", "track_unmatched"):
            if self._playlist_id is not None and event.current is not None:
                self._progress.update(
                    self._playlist_id,
                    completed=event.current,
                    total=event.total,
                    description=event.track_title or "",
                )
        elif event.type == "playlist_done":
            if self._overall_id is not None:
                self._progress.advance(self._overall_id)
            if event.message:
                self.console.print(
                    f"[green]✓[/green] {event.playlist_name}: {event.message}"
                )
        elif event.type == "job_done":
            self.console.print(f"[bold green]{event.message}[/bold green]")
        elif event.type == "error":
            self.console.print(f"[bold red]ERROR[/bold red]: {event.message}")
