"""sci backlog — Product backlog management commands."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime

import typer
from rich.table import Table

from sci.cli.utils import console, get_state_manager, require_init
from sci.models.local import BacklogItem, BacklogItemType, BacklogStatus, Priority

app = typer.Typer(no_args_is_help=True)


def _next_id(prefix: str, existing_ids: list[str]) -> str:
    """Generate the next sequential ID."""
    max_num = 0
    for item_id in existing_ids:
        parts = item_id.split("-")
        if len(parts) == 2:
            with contextlib.suppress(ValueError):
                max_num = max(max_num, int(parts[1]))
    return f"{prefix}-{max_num + 1:03d}"


@app.command("list")
def list_items(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    priority: str = typer.Option(None, "--priority", "-p", help="Filter by priority"),
) -> None:
    """List all product backlog items."""
    state = get_state_manager()
    require_init(state)

    backlog = state.load_backlog()

    items = backlog.items
    if status:
        items = [i for i in items if i.status.value == status]
    if priority:
        items = [i for i in items if i.priority.value == priority]

    if not items:
        console.print("[dim]No backlog items found.[/dim]")
        return

    table = Table(title="Product Backlog", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Type", style="blue")
    table.add_column("Priority", style="yellow")
    table.add_column("Points", justify="right")
    table.add_column("Status", style="green")
    table.add_column("Assignee")

    priority_colors = {
        "critical": "red",
        "high": "yellow",
        "medium": "white",
        "low": "dim",
    }

    for item in items:
        color = priority_colors.get(item.priority.value, "white")
        table.add_row(
            item.id,
            item.title,
            item.type.value,
            f"[{color}]{item.priority.value}[/{color}]",
            str(item.story_points or "-"),
            item.status.value,
            item.assignee or "-",
        )

    console.print(table)


@app.command("add")
def add_item(
    title: str = typer.Option(..., "--title", "-t", prompt="Title"),
    description: str = typer.Option("", "--description", "-d"),
    item_type: str = typer.Option("research_task", "--type"),
    priority: str = typer.Option("medium", "--priority", "-p"),
    points: int = typer.Option(None, "--points"),
    assignee: str = typer.Option(None, "--assignee", "-a"),
) -> None:
    """Add a new item to the product backlog."""
    state = get_state_manager()
    require_init(state)

    backlog = state.load_backlog()
    item_id = _next_id("PBI", [i.id for i in backlog.items])

    now = datetime.now(UTC)
    item = BacklogItem(
        id=item_id,
        title=title,
        description=description,
        type=BacklogItemType(item_type),
        priority=Priority(priority),
        story_points=points,
        status=BacklogStatus.DRAFT,
        assignee=assignee,
        created_at=now,
        updated_at=now,
    )

    backlog.items.append(item)
    state.save_backlog(backlog)

    console.print(
        f"[bold green]✓[/bold green] Added [{item_id}] {title}"
    )
