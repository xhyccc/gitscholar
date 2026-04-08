"""sci config — View or update project/global configuration."""

from __future__ import annotations

import typer
from rich.syntax import Syntax

from sci.cli.utils import console, get_state_manager, require_init

app = typer.Typer(no_args_is_help=True)


@app.command("show")
def show(
    is_global: bool = typer.Option(False, "--global", "-g", help="Show global settings"),
) -> None:
    """Show the current configuration."""
    from io import StringIO

    from ruamel.yaml import YAML

    state = get_state_manager()
    yaml = YAML()
    yaml.default_flow_style = False
    stream = StringIO()

    if is_global:
        settings = state.load_global_settings()
        yaml.dump(settings.model_dump(mode="json"), stream)
    else:
        require_init(state)
        config = state.load_config()
        yaml.dump(config.model_dump(mode="json"), stream)

    console.print(Syntax(stream.getvalue(), "yaml", theme="monokai"))
