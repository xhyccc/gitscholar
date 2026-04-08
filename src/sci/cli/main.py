"""Main CLI entry point for GitScholar (sci)."""

from __future__ import annotations

import typer

from sci.cli.backlog import app as backlog_app
from sci.cli.board import app as board_app
from sci.cli.config import app as config_app
from sci.cli.daily import app as daily_app
from sci.cli.hypothesis import app as hypothesis_app
from sci.cli.init import init_command
from sci.cli.scholar import app as scholar_app
from sci.cli.sprint import app as sprint_app

app = typer.Typer(
    name="sci",
    help="GitScholar CLI — A command-line collaboration and growth tool for academic research.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register sub-commands
app.command("init")(init_command)
app.add_typer(config_app, name="config", help="View or update configuration.")
app.add_typer(backlog_app, name="backlog", help="Manage the product backlog.")
app.add_typer(sprint_app, name="sprint", help="Sprint lifecycle management.")
app.add_typer(board_app, name="board", help="Display and manage the Kanban board.")
app.add_typer(daily_app, name="daily", help="Daily standup management.")
app.add_typer(hypothesis_app, name="hypothesis", help="Research hypothesis tracking.")
app.add_typer(scholar_app, name="scholar", help="Scholar profile and ISP dashboard.")


@app.command()
def version() -> None:
    """Show the GitScholar CLI version."""
    from sci import __version__

    from rich.console import Console

    console = Console()
    console.print(f"[bold]GitScholar CLI (sci)[/bold] v{__version__}")


if __name__ == "__main__":
    app()
