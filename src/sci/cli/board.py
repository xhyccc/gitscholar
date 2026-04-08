"""sci board — Kanban board display and management."""

from __future__ import annotations

import typer
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text

from sci.cli.utils import console, err_console, get_state_manager, require_init

app = typer.Typer(invoke_without_command=True)


@app.callback()
def board_display(ctx: typer.Context) -> None:
    """Display the Kanban board."""
    if ctx.invoked_subcommand is not None:
        return

    state = get_state_manager()
    require_init(state)

    board = state.load_board()
    backlog = state.load_backlog()

    # Build a lookup of backlog items by ID
    items_by_id = {item.id: item for item in backlog.items}

    panels = []
    for col in board.columns:
        wip_info = f" (WIP: {col.wip_limit})" if col.wip_limit else ""
        cards_text = Text()

        for card_id in col.cards:
            item = items_by_id.get(card_id)
            if item:
                cards_text.append(f"[{card_id}]\n", style="cyan")
                cards_text.append(f"{item.title}\n", style="white")
                if item.assignee:
                    cards_text.append(f"@{item.assignee}\n", style="dim")
                cards_text.append("\n")
            else:
                cards_text.append(f"[{card_id}]\n\n", style="cyan")

        if not col.cards:
            cards_text.append("(empty)\n", style="dim")

        panel = Panel(
            cards_text,
            title=f"[bold]{col.name}{wip_info}[/bold]",
            width=22,
            border_style="blue" if col.name == "In Progress" else "dim",
        )
        panels.append(panel)

    console.print()
    console.print("[bold]📋 Kanban Board[/bold]")
    console.print(Columns(panels, equal=True, expand=True))
    console.print()


@app.command("move")
def move(
    item_id: str = typer.Argument(help="Backlog item ID to move"),
    target_column: str = typer.Argument(help="Target column name"),
) -> None:
    """Move an item to a different column on the board."""
    state = get_state_manager()
    require_init(state)

    board = state.load_board()

    # Find and remove the item from its current column
    found = False
    for col in board.columns:
        if item_id in col.cards:
            col.cards.remove(item_id)
            found = True
            break

    if not found:
        err_console.print(f"[bold red]Error:[/bold red] Item '{item_id}' not found on the board.")
        raise SystemExit(1)

    # Find the target column
    target = None
    for col in board.columns:
        if col.name.lower() == target_column.lower():
            target = col
            break

    if target is None:
        column_names = ", ".join(c.name for c in board.columns)
        err_console.print(
            f"[bold red]Error:[/bold red] Column '{target_column}' not found. "
            f"Available: {column_names}"
        )
        raise SystemExit(1)

    # Check WIP limit
    if target.wip_limit and len(target.cards) >= target.wip_limit:
        err_console.print(
            f"[bold yellow]Warning:[/bold yellow] Column '{target.name}' "
            f"has reached its WIP limit ({target.wip_limit})."
        )

    target.cards.append(item_id)
    state.save_board(board)

    console.print(
        f"[bold green]✓[/bold green] Moved [{item_id}] → {target.name}"
    )
