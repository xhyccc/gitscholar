"""sci init — Initialize a GitScholar project."""

from __future__ import annotations

from datetime import UTC, datetime

import typer
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from sci.cli.utils import console, err_console, get_state_manager
from sci.models.local import AgentConfig, ProjectConfig, ProjectInfo, ScrumConfig, ScrumRoles
from sci.models.scholar import ScholarIdentity, ScholarProfile


def init_command(
    name: str = typer.Option(None, "--name", "-n", help="Project name"),
    non_interactive: bool = typer.Option(False, "--yes", "-y", help="Skip interactive prompts"),
) -> None:
    """Initialize a new GitScholar project in the current directory."""
    state = get_state_manager()

    if state.is_initialized and not Confirm.ask(
        "[yellow]GitScholar is already initialized here. Re-initialize?[/yellow]",
        default=False,
    ):
        raise SystemExit(0)

    console.print(Panel.fit(
        "[bold blue]🎓 GitScholar Project Initialization[/bold blue]",
        border_style="blue",
    ))

    if non_interactive:
        project_name = name or "unnamed-project"
        description = ""
        domain = ""
    else:
        project_name = name or Prompt.ask("Project name", default="my-research-project")
        description = Prompt.ask("Project description", default="")
        domain = Prompt.ask("Research domain", default="")

    config = ProjectConfig(
        project=ProjectInfo(
            name=project_name,
            description=description,
            domain=domain,
            created_at=datetime.now(UTC),
        ),
        scrum=ScrumConfig(roles=ScrumRoles()),
        agent=AgentConfig(),
    )

    state.init_local(config)

    # Initialize global profile if it doesn't exist
    if not (state.global_dir / "profile.yaml").exists():
        console.print("\n[dim]Setting up your global scholar profile...[/dim]")
        if non_interactive:
            scholar_name = "Scholar"
            email = ""
        else:
            scholar_name = Prompt.ask("Your name")
            email = Prompt.ask("Email", default="")

        profile = ScholarProfile(
            scholar=ScholarIdentity(
                name=scholar_name,
                email=email,
                joined_at=datetime.now(UTC),
            )
        )
        try:
            state.init_global(profile)
        except OSError as e:
            err_console.print(
                f"[yellow]Warning:[/yellow] Could not initialize global profile: {e}"
            )

    console.print(
        f"\n[bold green]✓[/bold green] GitScholar initialized for "
        f"[bold]{project_name}[/bold]\n"
        f"  Local state: [dim].gitscholar/[/dim]\n"
        f"  Run [bold]sci backlog add[/bold] to add your first research task."
    )
