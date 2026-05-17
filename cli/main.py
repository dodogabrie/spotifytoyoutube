from __future__ import annotations

import typer

from cli.interactive import _spotify_login, _ytmusic_login, run_interactive
from core.logging_setup import configure_logging

app = typer.Typer(
    help="Bidirectional playlist transfer between Spotify and YouTube Music.",
    no_args_is_help=False,
    pretty_exceptions_show_locals=False,
)


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context, log_level: str = typer.Option("INFO", help="Logging level")):
    configure_logging(log_level)
    if ctx.invoked_subcommand is None:
        run_interactive()


@app.command("login-spotify", help="Authenticate with Spotify (writes cache under ./secrets/)")
def cmd_login_spotify():
    _spotify_login()


@app.command("login-ytmusic", help="Authenticate with YouTube Music via device code flow")
def cmd_login_ytmusic():
    _ytmusic_login()


@app.command("interactive", help="Launch the interactive menu (default)")
def cmd_interactive():
    run_interactive()


if __name__ == "__main__":
    app()
