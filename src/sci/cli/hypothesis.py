"""sci hypothesis — Research hypothesis tracking."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime

import typer
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from sci.cli.utils import console, err_console, get_state_manager, require_init
from sci.models.local import Hypothesis, HypothesisStatus

app = typer.Typer(no_args_is_help=True)


def _next_hyp_id(existing_ids: list[str]) -> str:
    """Generate the next hypothesis ID."""
    max_num = 0
    for hyp_id in existing_ids:
        parts = hyp_id.split("-")
        if len(parts) == 2:
            with contextlib.suppress(ValueError):
                max_num = max(max_num, int(parts[1]))
    return f"HYP-{max_num + 1:03d}"


@app.command("list")
def list_hypotheses() -> None:
    """List all research hypotheses."""
    state = get_state_manager()
    require_init(state)

    tracker = state.load_hypotheses()

    if not tracker.hypotheses:
        console.print(
            "[dim]No hypotheses found. Run [bold]sci hypothesis add[/bold] to create one.[/dim]"
        )
        return

    table = Table(title="Research Hypotheses", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Statement", style="white")
    table.add_column("Status", style="green")
    table.add_column("Evidence", justify="right")

    status_styles = {
        "proposed": "yellow",
        "testing": "blue",
        "supported": "green",
        "refuted": "red",
        "revised": "magenta",
    }

    for hyp in tracker.hypotheses:
        style = status_styles.get(hyp.status.value, "white")
        table.add_row(
            hyp.id,
            hyp.statement,
            f"[{style}]{hyp.status.value}[/{style}]",
            str(len(hyp.evidence)),
        )

    console.print(table)


@app.command("add")
def add(
    statement: str = typer.Option(None, "--statement", "-s", help="Hypothesis statement"),
) -> None:
    """Propose a new research hypothesis."""
    state = get_state_manager()
    require_init(state)

    if not statement:
        statement = Prompt.ask("Hypothesis statement")

    tracker = state.load_hypotheses()
    hyp_id = _next_hyp_id([h.id for h in tracker.hypotheses])

    hypothesis = Hypothesis(
        id=hyp_id,
        statement=statement,
        status=HypothesisStatus.PROPOSED,
        created_at=datetime.now(UTC),
    )

    tracker.hypotheses.append(hypothesis)
    state.save_hypotheses(tracker)

    console.print(Panel.fit(
        f"[bold green]✓ Hypothesis {hyp_id} Proposed[/bold green]\n\n"
        f"[italic]{statement}[/italic]",
        border_style="green",
    ))


@app.command("status")
def show_status(
    hyp_id: str = typer.Argument(help="Hypothesis ID"),
) -> None:
    """Show detailed status of a hypothesis."""
    state = get_state_manager()
    require_init(state)

    tracker = state.load_hypotheses()
    hypothesis = next((h for h in tracker.hypotheses if h.id == hyp_id), None)

    if hypothesis is None:
        err_console.print(f"[bold red]Error:[/bold red] Hypothesis '{hyp_id}' not found.")
        raise SystemExit(1)

    console.print(Panel.fit(
        f"[bold]{hypothesis.id}[/bold]\n\n"
        f"[italic]{hypothesis.statement}[/italic]\n\n"
        f"Status: [bold]{hypothesis.status.value}[/bold]\n"
        f"Evidence items: {len(hypothesis.evidence)}\n"
        f"Linked tasks: {', '.join(hypothesis.linked_tasks) or 'None'}",
        title="Hypothesis Details",
        border_style="blue",
    ))

    if hypothesis.evidence:
        table = Table(title="Evidence")
        table.add_column("Type")
        table.add_column("Ref")
        table.add_column("Outcome")
        table.add_column("Notes")

        for ev in hypothesis.evidence:
            table.add_row(ev.type, ev.ref, ev.outcome.value, ev.notes)

        console.print(table)
