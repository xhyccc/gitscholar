"""Shared CLI utilities and helpers."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from sci.persistence.state import StateManager

console = Console()
err_console = Console(stderr=True)


def get_state_manager() -> StateManager:
    """Get a StateManager instance rooted at the current working directory."""
    return StateManager(repo_root=Path.cwd())


def require_init(state: StateManager) -> None:
    """Exit with an error if the project is not initialized."""
    if not state.is_initialized:
        err_console.print(
            "[bold red]Error:[/bold red] This directory is not a GitScholar project.\n"
            "Run [bold]sci init[/bold] to initialize."
        )
        raise SystemExit(1)
