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


def _maybe_update_isp_level(state) -> None:  # type: ignore[no-untyped-def]
    """Recompute and persist the scholar's ISP level if it changed."""
    from sci.core.isp import compute_isp_level

    try:
        tracker = state.load_milestones()
        skills = state.load_skills()
        computed = compute_isp_level(tracker, skills)
        profile = state.load_scholar_profile()
        if computed != profile.scholar.isp_level:
            profile.scholar.isp_level = computed
            state.save_scholar_profile(profile)
            console.print(
                f"[bold green]🎉 ISP level advanced to "
                f"{computed.value.title()}![/bold green]"
            )
    except Exception:
        pass


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

    # Auto-update ISP level and show milestones summary
    milestones = None
    skills_data = None
    try:
        from sci.core.isp import compute_isp_level

        milestones = state.load_milestones()
        skills_data = state.load_skills()
        computed_level = compute_isp_level(milestones, skills_data)

        if computed_level != scholar.isp_level:
            scholar.isp_level = computed_level
            profile.scholar = scholar
            state.save_scholar_profile(profile)
            console.print(
                f"[bold green]🎉 ISP level updated to "
                f"{computed_level.value.title()}![/bold green]"
            )

        if milestones.milestones:
            achieved = sum(1 for m in milestones.milestones if m.achieved)
            total = len(milestones.milestones)
            console.print(f"\n[bold]Milestones:[/bold] {achieved}/{total} achieved")
    except (OSError, KeyError, ValueError):
        pass

    # Show skills summary
    try:
        skills = skills_data if skills_data is not None else state.load_skills()
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
