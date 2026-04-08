"""sci scholar — Scholar profile and ISP dashboard."""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from sci.cli.utils import console, err_console

app = typer.Typer(invoke_without_command=True)


def _load_global_state():
    """Load global state, handling missing profile gracefully."""
    from sci.persistence.state import StateManager
    state = StateManager()

    if not (state.global_dir / "profile.yaml").exists():
        err_console.print(
            "[bold red]Error:[/bold red] No scholar profile found.\n"
            "Run [bold]sci init[/bold] in a project to set up your profile."
        )
        raise SystemExit(1)

    return state


@app.callback()
def scholar_dashboard(ctx: typer.Context) -> None:
    """Show the scholar dashboard."""
    if ctx.invoked_subcommand is not None:
        return

    state = _load_global_state()
    profile = state.load_scholar_profile()
    scholar = profile.scholar

    level_stars = {
        "novice": "⭐",
        "explorer": "⭐⭐",
        "contributor": "⭐⭐⭐",
        "scholar": "⭐⭐⭐⭐",
        "master": "⭐⭐⭐⭐⭐",
    }

    dashboard = (
        f"[bold]Name:[/bold]  {scholar.name}\n"
        f"[bold]Level:[/bold] {scholar.isp_level.value.title()} "
        f"{level_stars.get(scholar.isp_level.value, '')}\n"
    )

    if scholar.orcid:
        dashboard += f"[bold]ORCID:[/bold] {scholar.orcid}\n"
    if scholar.institution:
        dashboard += f"[bold]Institution:[/bold] {scholar.institution}\n"
    if scholar.research_interests:
        dashboard += f"[bold]Interests:[/bold] {', '.join(scholar.research_interests)}\n"

    console.print(Panel.fit(
        dashboard,
        title="[bold]🎓 Scholar Profile[/bold]",
        border_style="blue",
    ))

    # Show milestones summary
    try:
        milestones = state.load_milestones()
        if milestones.milestones:
            achieved = sum(1 for m in milestones.milestones if m.achieved)
            total = len(milestones.milestones)
            console.print(f"\n[bold]Milestones:[/bold] {achieved}/{total} achieved")
    except Exception:
        pass

    # Show skills summary
    try:
        skills = state.load_skills()
        all_skills = (
            skills.technical + skills.research + skills.collaboration + skills.writing
        )
        if all_skills:
            console.print("\n[bold]Skill Highlights:[/bold]")
            with Progress(
                TextColumn("  {task.description:<20}"),
                BarColumn(bar_width=15),
                TextColumn("{task.completed}/5"),
            ) as progress:
                for skill in sorted(all_skills, key=lambda s: s.level, reverse=True)[:5]:
                    progress.add_task(skill.name, total=5, completed=skill.level)
    except Exception:
        pass


@app.command("milestones")
def milestones() -> None:
    """List all ISP milestones and progress."""
    state = _load_global_state()
    tracker = state.load_milestones()

    if not tracker.milestones:
        console.print("[dim]No milestones defined yet.[/dim]")
        return

    table = Table(title="ISP Milestones", show_lines=True)
    table.add_column("", width=2)
    table.add_column("Milestone", style="white")
    table.add_column("Category", style="blue")
    table.add_column("Achieved", style="green")
    table.add_column("Project")

    for m in tracker.milestones:
        icon = "✓" if m.achieved else "○"
        style = "green" if m.achieved else "dim"
        achieved_str = m.achieved_at.strftime("%Y-%m-%d") if m.achieved_at else "-"
        table.add_row(
            f"[{style}]{icon}[/{style}]",
            m.name,
            m.category.value,
            achieved_str,
            m.project or "-",
        )

    console.print(table)


@app.command("skills")
def skills() -> None:
    """Show the skill tree."""
    state = _load_global_state()
    skill_tree = state.load_skills()

    categories = [
        ("Technical", skill_tree.technical),
        ("Research", skill_tree.research),
        ("Collaboration", skill_tree.collaboration),
        ("Writing", skill_tree.writing),
    ]

    for category_name, category_skills in categories:
        if not category_skills:
            continue

        console.print(f"\n[bold]{category_name}[/bold]")
        with Progress(
            TextColumn("  {task.description:<25}"),
            BarColumn(bar_width=15),
            TextColumn("{task.completed}/5"),
        ) as progress:
            for skill in sorted(category_skills, key=lambda s: s.level, reverse=True):
                progress.add_task(skill.name, total=5, completed=skill.level)

    all_skills = (
        skill_tree.technical + skill_tree.research
        + skill_tree.collaboration + skill_tree.writing
    )
    if not all_skills:
        console.print("[dim]No skills tracked yet. Skills are updated as you use sci.[/dim]")
