"""Agent engine interface — wraps claw-code as a headless LLM engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sci.core.tools import Tool, ToolRegistry


@dataclass
class AgentResponse:
    """Structured response from the Agent engine."""

    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentEngine:
    """Wraps claw-code as a headless LLM Agent engine.

    This class provides the interface between the sci orchestration layer
    and the underlying Agent engine. It manages prompt injection, tool
    registration, and response parsing.

    Note: The actual claw-code integration will be implemented when
    the claw-code package is available. Currently provides a stub
    interface for development.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4",
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._tool_registry = ToolRegistry

    def register_tool(self, tool: Tool) -> None:
        """Register a tool for the Agent to use."""
        self._tool_registry._tools[tool.name] = tool

    def execute(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Tool] | None = None,
    ) -> AgentResponse:
        """Execute an Agent interaction.

        Args:
            system_prompt: Context-rich system prompt from PromptBuilder.
            user_message: The user's message or query.
            tools: Optional list of tools available for this interaction.
                   If None, all registered tools are available.

        Returns:
            AgentResponse with content and any tool call results.

        Raises:
            NotImplementedError: Until claw-code integration is complete.
        """
        raise NotImplementedError(
            "Agent engine requires claw-code integration. "
            "Install with: pip install gitscholar[agent]"
        )

    def is_available(self) -> bool:
        """Check if the Agent engine is available and configured."""
        try:
            import importlib

            importlib.import_module("claw_code")
            return True
        except ImportError:
            return False
