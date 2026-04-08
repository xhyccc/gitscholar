"""sci config — View or update project/global configuration."""

from __future__ import annotations

from typing import Any

import typer
from rich.syntax import Syntax

from sci.cli.utils import console, err_console, get_state_manager, require_init

app = typer.Typer(no_args_is_help=True)


def _dump_yaml(data: dict[str, Any]) -> str:
    """Serialize *data* to a YAML string."""
    from io import StringIO

    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.default_flow_style = False
    stream = StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()


@app.command("show")
def show(
    is_global: bool = typer.Option(False, "--global", "-g", help="Show global settings"),
    resolved: bool = typer.Option(
        False, "--resolved", "-r",
        help="Show effective settings with env-var / git-config defaults applied",
    ),
) -> None:
    """Show the current configuration."""
    state = get_state_manager()

    if is_global:
        settings = state.load_global_settings()
        if resolved:
            from sci.core.config import resolve_settings

            settings = resolve_settings(settings)
        data = settings.model_dump(mode="json")
        # Mask the API key in display output
        if data.get("agent", {}).get("llm", {}).get("api_key"):
            data["agent"]["llm"]["api_key"] = "****"
    else:
        require_init(state)
        config = state.load_config()
        data = config.model_dump(mode="json")

    console.print(Syntax(_dump_yaml(data), "yaml", theme="monokai"))


def _set_nested(data: dict[str, Any], dotted_key: str, value: str) -> None:
    """Set a value in a nested dict using dot-notation (e.g. ``agent.llm.model``)."""
    keys = dotted_key.split(".")
    current = data
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]

    # Attempt to coerce value to the right type
    final_key = keys[-1]
    existing = current.get(final_key)
    if isinstance(existing, bool):
        current[final_key] = value.lower() in ("true", "1", "yes")
    elif isinstance(existing, int):
        current[final_key] = int(value)
    elif isinstance(existing, float):
        current[final_key] = float(value)
    else:
        current[final_key] = value


@app.command("set")
def set_value(
    key: str = typer.Argument(help="Dot-notation key (e.g. agent.llm.api_key)"),
    value: str = typer.Argument(help="Value to set"),
    is_global: bool = typer.Option(False, "--global", "-g", help="Update global settings"),
) -> None:
    """Set a configuration value using dot-notation.

    Examples:
        sci config set agent.llm.model gpt-4o --global
        sci config set agent.llm.api_key sk-... --global
        sci config set git.user_name "Jane Doe" --global
        sci config set scrum.sprint_duration_days 7
    """
    state = get_state_manager()

    if is_global:
        settings = state.load_global_settings()
        data = settings.model_dump(mode="json")
        _set_nested(data, key, value)
        from sci.models.scholar import GlobalSettings

        updated_global = GlobalSettings.model_validate(data)
        state.save_global_settings(updated_global)
        console.print(f"[bold green]✓[/bold green] Global setting [bold]{key}[/bold] updated.")
    else:
        require_init(state)
        config = state.load_config()
        data = config.model_dump(mode="json")
        _set_nested(data, key, value)
        from sci.models.local import ProjectConfig

        updated_local = ProjectConfig.model_validate(data)
        state.save_config(updated_local)
        console.print(f"[bold green]✓[/bold green] Project setting [bold]{key}[/bold] updated.")


@app.command("get")
def get_value(
    key: str = typer.Argument(help="Dot-notation key (e.g. agent.llm.model)"),
    is_global: bool = typer.Option(False, "--global", "-g", help="Read global settings"),
    resolved: bool = typer.Option(
        False, "--resolved", "-r",
        help="Resolve env-var / git-config defaults before reading",
    ),
) -> None:
    """Get a single configuration value by dot-notation key.

    Examples:
        sci config get agent.llm.model --global
        sci config get git.user_email --global --resolved
    """
    state = get_state_manager()

    if is_global:
        settings = state.load_global_settings()
        if resolved:
            from sci.core.config import resolve_settings

            settings = resolve_settings(settings)
        data = settings.model_dump(mode="json")
    else:
        require_init(state)
        config = state.load_config()
        data = config.model_dump(mode="json")

    current: Any = data
    for part in key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            err_console.print(f"[bold red]Error:[/bold red] Key [bold]{key}[/bold] not found.")
            raise SystemExit(1)

    # Mask API keys in output
    if "api_key" in key and isinstance(current, str) and current:
        console.print("****")
    else:
        console.print(str(current))
