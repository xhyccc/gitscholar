"""CLI tests for the backlog commands."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sci.cli.main import app
from sci.models.local import BacklogItem, BacklogItemType, BacklogStatus, Priority
from sci.persistence.state import StateManager


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def init_dir(tmp_path: Path) -> Path:
    """Return a temp directory with a fully initialised GitScholar project."""
    state = StateManager(repo_root=tmp_path)
    state._global_dir = tmp_path / "global"

    from sci.models.local import ProjectConfig, ProjectInfo
    from sci.models.scholar import ScholarIdentity, ScholarProfile

    config = ProjectConfig(
        project=ProjectInfo(
            name="test-project",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    state.init_local(config)
    profile = ScholarProfile(
        scholar=ScholarIdentity(
            name="Test Scholar",
            joined_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    state.init_global(profile)
    return tmp_path


class TestBacklogList:
    def test_list_empty(self, runner: CliRunner, init_dir: Path) -> None:
        import os
        old = os.getcwd()
        os.chdir(init_dir)
        try:
            result = runner.invoke(app, ["backlog", "list"], catch_exceptions=False)
            assert result.exit_code == 0
            assert "No backlog items" in result.output
        finally:
            os.chdir(old)

    def test_list_with_items(self, runner: CliRunner, init_dir: Path) -> None:
        import os

        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"
        backlog = state.load_backlog()
        backlog.items.append(
            BacklogItem(
                id="PBI-001",
                title="My task",
                type=BacklogItemType.RESEARCH_TASK,
                priority=Priority.HIGH,
                status=BacklogStatus.READY,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        state.save_backlog(backlog)

        old = os.getcwd()
        os.chdir(init_dir)
        try:
            result = runner.invoke(app, ["backlog", "list"], catch_exceptions=False)
            assert result.exit_code == 0
            assert "PBI-001" in result.output
            assert "My task" in result.output
        finally:
            os.chdir(old)

    def test_list_filter_by_status(self, runner: CliRunner, init_dir: Path) -> None:
        import os

        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"
        backlog = state.load_backlog()
        backlog.items.extend([
            BacklogItem(
                id="PBI-001",
                title="Ready item",
                priority=Priority.HIGH,
                status=BacklogStatus.READY,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
            BacklogItem(
                id="PBI-002",
                title="Draft item",
                status=BacklogStatus.DRAFT,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        ])
        state.save_backlog(backlog)

        old = os.getcwd()
        os.chdir(init_dir)
        try:
            result = runner.invoke(
                app, ["backlog", "list", "--status", "ready"], catch_exceptions=False
            )
            assert result.exit_code == 0
            assert "PBI-001" in result.output
            assert "PBI-002" not in result.output
        finally:
            os.chdir(old)

    def test_list_not_initialized(self, runner: CliRunner, tmp_path: Path) -> None:
        import os

        old = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["backlog", "list"])
            assert result.exit_code != 0
        finally:
            os.chdir(old)


class TestBacklogAdd:
    def test_add_item(self, runner: CliRunner, init_dir: Path) -> None:
        import os

        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"

        old = os.getcwd()
        os.chdir(init_dir)
        try:
            result = runner.invoke(
                app,
                ["backlog", "add", "--title", "New research task", "--priority", "high"],
                catch_exceptions=False,
            )
            assert result.exit_code == 0
            assert "New research task" in result.output

            backlog = state.load_backlog()
            assert len(backlog.items) == 1
            assert backlog.items[0].id == "PBI-001"
            assert backlog.items[0].title == "New research task"
            assert backlog.items[0].priority == Priority.HIGH
        finally:
            os.chdir(old)

    def test_add_increments_id(self, runner: CliRunner, init_dir: Path) -> None:
        import os

        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"
        backlog = state.load_backlog()
        backlog.items.append(
            BacklogItem(
                id="PBI-005",
                title="Existing",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        state.save_backlog(backlog)

        old = os.getcwd()
        os.chdir(init_dir)
        try:
            result = runner.invoke(
                app,
                ["backlog", "add", "--title", "Another task"],
                catch_exceptions=False,
            )
            assert result.exit_code == 0
            backlog2 = state.load_backlog()
            assert backlog2.items[-1].id == "PBI-006"
        finally:
            os.chdir(old)

    def test_add_with_points_and_assignee(self, runner: CliRunner, init_dir: Path) -> None:
        import os

        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"

        old = os.getcwd()
        os.chdir(init_dir)
        try:
            result = runner.invoke(
                app,
                [
                    "backlog", "add",
                    "--title", "Pointed task",
                    "--points", "5",
                    "--assignee", "alice",
                ],
                catch_exceptions=False,
            )
            assert result.exit_code == 0
            backlog = state.load_backlog()
            item = backlog.items[0]
            assert item.story_points == 5
            assert item.assignee == "alice"
        finally:
            os.chdir(old)
