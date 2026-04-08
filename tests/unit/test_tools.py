"""Tests for the tool registry."""

from __future__ import annotations

from typing import Any

from sci.core.tools import Tool, ToolRegistry


class MockTool(Tool):
    name = "mock_tool"
    description = "A mock tool for testing"

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        return {"result": "mock"}


class AnotherTool(Tool):
    name = "another_tool"
    description = "Another mock tool"

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        return {"result": "another"}


class TestToolRegistry:
    """Tests for tool registration and retrieval."""

    def setup_method(self) -> None:
        ToolRegistry.clear()

    def test_register_tool(self) -> None:
        ToolRegistry.register(MockTool)
        assert ToolRegistry.get("mock_tool") is not None

    def test_get_nonexistent(self) -> None:
        assert ToolRegistry.get("nonexistent") is None

    def test_list_tools(self) -> None:
        ToolRegistry.register(MockTool)
        ToolRegistry.register(AnotherTool)
        tools = ToolRegistry.list_tools()
        assert len(tools) == 2

    def test_list_schemas(self) -> None:
        ToolRegistry.register(MockTool)
        schemas = ToolRegistry.list_schemas()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "mock_tool"
        assert schemas[0]["description"] == "A mock tool for testing"

    def test_clear(self) -> None:
        ToolRegistry.register(MockTool)
        assert len(ToolRegistry.list_tools()) == 1
        ToolRegistry.clear()
        assert len(ToolRegistry.list_tools()) == 0

    def test_tool_execute(self) -> None:
        tool = MockTool()
        result = tool.execute()
        assert result == {"result": "mock"}
