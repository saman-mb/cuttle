"""CLI entrypoint (stub)."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="cuttle",
    help="Frontier mind. Local hands.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Cuttle coding-agent CLI."""


@app.command("version")
def version() -> None:
    """Print the package version."""
    from cuttle import __version__

    typer.echo(__version__)


if __name__ == "__main__":
    app()
