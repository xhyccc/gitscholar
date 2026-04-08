"""sci daily — Daily standup management."""

from __future__ import annotations

from datetime import date

import typer
from rich.panel import Panel
from rich.prompt import Prompt

from sci.cli.utils import console, get_state_manager, require_init
from sci.models.local import DailyEntry

app = typer.Typer(invoke_without_command=True)


@app.callback()
def daily_standup(
    ctx: typer.Context,
    non_interactive: bool = typer.Option(False, "--yes", "-y", help="Skip prompts"),
) -> None:
    """Record a daily standup."""
    if ctx.invoked_subcommand is not None:
        return

    state = get_state_manager()
    require_init(state)

    today = date.today().isoformat()

    console.print(Panel.fit(
        f"[bold blue]📝 Daily Standup — {today}[/bold blue]",
        border_style="blue",
    ))

    if non_interactive:
        console.print("[dim]Use interactive mode for standup entries.[/dim]")
        return

    participant = Prompt.ask("Your name")
    yesterday = Prompt.ask("What did you accomplish yesterday?")
    today_plan = Prompt.ask("What will you work on today?")
    blockers = Prompt.ask("Any blockers?", default="None")

    entry = DailyEntry(
        date=today,
        participant=participant,
        yesterday=yesterday,
        today=today_plan,
        blockers=blockers if blockers != "None" else "",
    )

    log = state.load_daily(today)
    log.entries.append(entry)
    state.save_daily(today, log)

    console.print(f"\n[bold green]✓[/bold green] Standup recorded for {participant}.")
