from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.config import get_settings
from core.models import TransferReport


def write_report(report: TransferReport, reports_dir: Path | None = None) -> Path:
    settings = get_settings()
    target_dir = reports_dir or settings.reports_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = target_dir / f"report-{stamp}.json"
    path.write_text(report.model_dump_json(indent=2))
    return path
