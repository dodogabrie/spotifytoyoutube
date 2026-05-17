import logging
import os
import re

from rich.logging import RichHandler

_TOKEN_RE = re.compile(
    r"(?i)(bearer\s+|access_token\"?\s*[:=]\s*\"?|refresh_token\"?\s*[:=]\s*\"?|"
    r"client_secret\"?\s*[:=]\s*\"?|user_code\"?\s*[:=]\s*\"?)([A-Za-z0-9._\-]+)"
)


class SecretScrubber(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _TOKEN_RE.sub(r"\1<REDACTED>", record.msg)
        return True


def configure_logging(level: str | None = None) -> None:
    level_name = (level or os.environ.get("LOG_LEVEL") or "INFO").upper()
    handler = RichHandler(rich_tracebacks=True, show_path=False)
    handler.addFilter(SecretScrubber())
    logging.basicConfig(
        level=level_name,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler],
        force=True,
    )
