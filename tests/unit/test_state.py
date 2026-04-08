"""Tests for the persistence layer state manager."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from sci.models.local import (
    BacklogItem,
    BacklogItemType,
    BacklogStatus,
    Hypothesis,
    HypothesisStatus,
    KanbanBoard,
    Priority,
    ProjectConfig,
    ProjectInfo,
    Sprint,
)
from sci.models.scholar import (
    Milestone,
    MilestoneCategory,
    ScholarIdentity,
    ScholarProfile,
    Skill,
)
from sci.persistence.state import StateManager


@pytest.fixture
def tmp_state(tmp_path: Path) -> StateManager:
    """Create a StateManager with temp directories for local and global state."""
    state = StateManager(repo_root=tmp_path)
    # Override global dir for testing
    state._global_dir = tmp_path / "global"
    return state


@pytest.fixture
def initialized_state(tmp_state: StateManager) -> StateManager:
    """Create a fully initialized StateManager."""
    config = ProjectConfig(
        project=ProjectInfo(
            name="test-project",
            description="A test project",
            domain="testing",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    tmp_state.init_local(config)

    profile = ScholarProfile(
        scholar=ScholarIdentity(
            name="Test Scholar",
            email="test@example.com",
            joined_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    tmp_state.init_global(profile)

    return tmp_state


class TestStateManagerInit:
    """Tests for initialization."""

    def test_is_initialized_false(self, tmp_state: StateManager) -> None:
        assert not tmp_state.is_initialized

    def test_init_local_creates_directories(self, tmp_state: StateManager) -> None:
        config = ProjectConfig(
            project=ProjectInfo(name="test", created_at=datetime(2026, 1, 1, tzinfo=UTC))
        )
        tmp_state.init_local(config)

        assert tmp_state.is_initialized
        assert (tmp_state.local_dir / "config.yaml").exists()
        assert (tmp_state.local_dir / "backlog").is_dir()
        assert (tmp_state.local_dir / "sprints" / "archive").is_dir()
        assert (tmp_state.local_dir / "board").is_dir()
        assert (tmp_state.local_dir / "research").is_dir()
        assert (tmp_state.local_dir / "dailies").is_dir()

    def test_init_global_creates_directories(self, tmp_state: StateManager) -> None:
        profile = ScholarProfile(
            scholar=ScholarIdentity(
                name="Scholar",
                joined_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        tmp_state.init_global(profile)

        assert (tmp_state.global_dir / "profile.yaml").exists()
        assert (tmp_state.global_dir / "settings.yaml").exists()
        assert (tmp_state.global_dir / "isp").is_dir()
        assert (tmp_state.global_dir / "contributions").is_dir()


class TestLocalState:
    """Tests for local state read/write."""

    def test_config_roundtrip(self, initialized_state: StateManager) -> None:
        config = initialized_state.load_config()
        assert config.project.name == "test-project"
        assert config.project.domain == "testing"

    def test_backlog_roundtrip(self, initialized_state: StateManager) -> None:
        backlog = initialized_state.load_backlog()
        assert len(backlog.items) == 0

        item = BacklogItem(
            id="PBI-001",
            title="Test item",
            type=BacklogItemType.RESEARCH_TASK,
            priority=Priority.HIGH,
            story_points=5,
            status=BacklogStatus.READY,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        backlog.items.append(item)
        initialized_state.save_backlog(backlog)

        loaded = initialized_state.load_backlog()
        assert len(loaded.items) == 1
        assert loaded.items[0].id == "PBI-001"
        assert loaded.items[0].title == "Test item"
        assert loaded.items[0].priority == Priority.HIGH
        assert loaded.items[0].story_points == 5

    def test_board_default_columns(self, initialized_state: StateManager) -> None:
        board = initialized_state.load_board()
        assert len(board.columns) == 5
        column_names = [c.name for c in board.columns]
        assert "Backlog" in column_names
        assert "In Progress" in column_names
        assert "Done" in column_names

    def test_board_roundtrip(self, initialized_state: StateManager) -> None:
        board = initialized_state.load_board()
        board.columns[0].cards.append("PBI-001")
        initialized_state.save_board(board)

        loaded = initialized_state.load_board()
        assert "PBI-001" in loaded.columns[0].cards

    def test_sprint_roundtrip(self, initialized_state: StateManager) -> None:
        sprint = Sprint(
            id="SPR-001",
            goal="Test sprint",
            start_date=datetime(2026, 1, 1, tzinfo=UTC),
            end_date=datetime(2026, 1, 15, tzinfo=UTC),
            status="active",
        )
        initialized_state.save_current_sprint(sprint)

        loaded = initialized_state.load_current_sprint()
        assert loaded.id == "SPR-001"
        assert loaded.goal == "Test sprint"
        assert loaded.status == "active"

    def test_sprint_archive(self, initialized_state: StateManager) -> None:
        sprint = Sprint(
            id="SPR-001",
            goal="Archived sprint",
            start_date=datetime(2026, 1, 1, tzinfo=UTC),
            end_date=datetime(2026, 1, 15, tzinfo=UTC),
            status="completed",
        )
        initialized_state.archive_sprint(sprint)

        archive_path = initialized_state.local_dir / "sprints" / "archive" / "SPR-001.yaml"
        assert archive_path.exists()

    def test_hypotheses_roundtrip(self, initialized_state: StateManager) -> None:
        tracker = initialized_state.load_hypotheses()
        hyp = Hypothesis(
            id="HYP-001",
            statement="Test hypothesis",
            status=HypothesisStatus.PROPOSED,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        tracker.hypotheses.append(hyp)
        initialized_state.save_hypotheses(tracker)

        loaded = initialized_state.load_hypotheses()
        assert len(loaded.hypotheses) == 1
        assert loaded.hypotheses[0].statement == "Test hypothesis"


class TestGlobalState:
    """Tests for global state read/write."""

    def test_profile_roundtrip(self, initialized_state: StateManager) -> None:
        profile = initialized_state.load_scholar_profile()
        assert profile.scholar.name == "Test Scholar"
        assert profile.scholar.email == "test@example.com"

    def test_settings_defaults(self, initialized_state: StateManager) -> None:
        settings = initialized_state.load_global_settings()
        assert settings.cli.theme.value == "dark"
        assert settings.agent.default_model == "claude-sonnet-4"
        assert settings.notifications.sprint_reminders is True

    def test_milestones_roundtrip(self, initialized_state: StateManager) -> None:
        tracker = initialized_state.load_milestones()
        milestone = Milestone(
            id="ISP-M001",
            name="First Sprint",
            category=MilestoneCategory.SCRUM,
            achieved=True,
            achieved_at=datetime(2026, 2, 1, tzinfo=UTC),
            project="test-project",
        )
        tracker.milestones.append(milestone)
        initialized_state.save_milestones(tracker)

        loaded = initialized_state.load_milestones()
        assert len(loaded.milestones) == 1
        assert loaded.milestones[0].achieved is True

    def test_skills_roundtrip(self, initialized_state: StateManager) -> None:
        skills = initialized_state.load_skills()
        skills.technical.append(Skill(name="Python", level=3, evidence=["PBI-001"]))
        skills.research.append(Skill(name="Hypothesis Formation", level=2))
        initialized_state.save_skills(skills)

        loaded = initialized_state.load_skills()
        assert len(loaded.technical) == 1
        assert loaded.technical[0].name == "Python"
        assert loaded.technical[0].level == 3
        assert len(loaded.research) == 1


class TestKanbanBoard:
    """Tests for Kanban board model behavior."""

    def test_default_board(self) -> None:
        board = KanbanBoard()
        assert len(board.columns) == 5
        assert board.columns[0].name == "Backlog"
        assert board.columns[0].wip_limit is None
        assert board.columns[2].name == "In Progress"
        assert board.columns[2].wip_limit == 3

    def test_move_card(self) -> None:
        board = KanbanBoard()
        board.columns[0].cards.append("PBI-001")
        assert "PBI-001" in board.columns[0].cards

        board.columns[0].cards.remove("PBI-001")
        board.columns[2].cards.append("PBI-001")
        assert "PBI-001" not in board.columns[0].cards
        assert "PBI-001" in board.columns[2].cards
