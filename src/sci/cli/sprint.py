"""sci sprint — Sprint lifecycle management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import typer
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from sci.cli.utils import console, err_console, get_state_manager, require_init
from sci.models.local import Sprint, SprintBacklog

app = typer.Typer(no_args_is_help=True)


def _next_sprint_id(state_mgr) -> str:  # noqa: ANN001
    """Generate the next sprint ID by checking the archive."""
    archive_dir = state_mgr.local_dir / "sprints" / "archive"
    if not archive_dir.exists():
        return "SPR-001"
    existing = list(archive_dir.glob("SPR-*.yaml"))
    return f"SPR-{len(existing) + 1:03d}"


@app.command("start")
def start(
    goal: str = typer.Option("", "--goal", "-g", help="Sprint goal"),
    duration: int = typer.Option(None, "--duration", "-d", help="Duration in days"),
) -> None:
    """Start a new sprint."""
    state = get_state_manager()
    require_init(state)

    # Check if there's an active sprint
    current_path = state.local_dir / "sprints" / "current.yaml"
    if current_path.exists():
        err_console.print(
            "[bold red]Error:[/bold red] A sprint is already active. "
            "Run [bold]sci sprint end[/bold] first."
        )
        raise SystemExit(1)

    config = state.load_config()
    sprint_days = duration or config.scrum.sprint_duration_days
    sprint_id = _next_sprint_id(state)

    now = datetime.now(timezone.utc)
    sprint = Sprint(
        id=sprint_id,
        goal=goal,
        start_date=now,
        end_date=now + timedelta(days=sprint_days),
        status="active",
    )

    state.save_current_sprint(sprint)
    state.save_sprint_backlog(SprintBacklog(sprint_id=sprint_id))

    console.print(Panel.fit(
        f"[bold green]🚀 Sprint {sprint_id} Started![/bold green]\n\n"
        f"Goal: {goal or '[dim]No goal set[/dim]'}\n"
        f"Duration: {sprint_days} days\n"
        f"Ends: {sprint.end_date.strftime('%Y-%m-%d')}",
        border_style="green",
    ))


@app.command("status")
def status() -> None:
    """Show current sprint progress."""
    state = get_state_manager()
    require_init(state)

    current_path = state.local_dir / "sprints" / "current.yaml"
    if not current_path.exists():
        console.print("[dim]No active sprint. Run [bold]sci sprint start[/bold] to begin.[/dim]")
        return

    sprint = state.load_current_sprint()
    board = state.load_board()

    now = datetime.now(timezone.utc)
    total_days = (sprint.end_date - sprint.start_date).days
    elapsed_days = min((now - sprint.start_date).days, total_days)

    done_count = 0
    total_count = 0
    for col in board.columns:
        total_count += len(col.cards)
        if col.name == "Done":
            done_count = len(col.cards)

    completion = (done_count / total_count * 100) if total_count > 0 else 0

    console.print(Panel.fit(
        f"[bold]{sprint.id}[/bold] — {sprint.goal or '[dim]No goal[/dim]'}",
        border_style="blue",
    ))

    with Progress(
        TextColumn("[bold]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("{task.percentage:.0f}%"),
        TextColumn("(Day {task.completed}/{task.total})"),
    ) as progress:
        progress.add_task("Time", total=total_days, completed=elapsed_days)

    table = Table(show_header=False, box=None)
    table.add_row("Stories completed:", f"[bold]{done_count}[/bold] / {total_count}")
    table.add_row("Completion:", f"[bold]{completion:.0f}%[/bold]")
    table.add_row("Ends:", sprint.end_date.strftime("%Y-%m-%d"))
    console.print(table)


@app.command("end")
def end() -> None:
    """End the current sprint."""
    state = get_state_manager()
    require_init(state)

    current_path = state.local_dir / "sprints" / "current.yaml"
    if not current_path.exists():
        err_console.print("[bold red]Error:[/bold red] No active sprint to end.")
        raise SystemExit(1)

    sprint = state.load_current_sprint()
    sprint.status = "completed"

    state.archive_sprint(sprint)

    # Remove current sprint file
    current_path.unlink()

    console.print(
        f"[bold green]✓[/bold green] Sprint [bold]{sprint.id}[/bold] completed and archived.\n"
        f"  Run [bold]sci retro[/bold] to start a retrospective."
    )
