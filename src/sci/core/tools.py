"""Tool registry and base classes for Agent Tool Calling."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Base class for all tools exposed to the Agent engine."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with the given arguments."""
        ...

    def to_schema(self) -> dict[str, Any]:
        """Return the tool's schema for Agent registration."""
        return {
            "name": self.name,
            "description": self.description,
        }


class ToolRegistry:
    """Registry for managing tools exposed to the Agent engine."""

    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool_class: type[Tool]) -> type[Tool]:
        """Decorator to register a tool class."""
        instance = tool_class()
        cls._tools[instance.name] = instance
        return tool_class

    @classmethod
    def get(cls, name: str) -> Tool | None:
        """Get a registered tool by name."""
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> list[Tool]:
        """List all registered tools."""
        return list(cls._tools.values())

    @classmethod
    def list_schemas(cls) -> list[dict[str, Any]]:
        """List all registered tool schemas."""
        return [tool.to_schema() for tool in cls._tools.values()]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (useful for testing)."""
        cls._tools = {}
