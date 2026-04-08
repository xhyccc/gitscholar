"""Tests for the prompt builder."""

from __future__ import annotations

from datetime import UTC, datetime

from sci.core.prompts import PromptBuilder
from sci.models.local import (
    BacklogItem,
    BacklogStatus,
    KanbanBoard,
    KanbanColumn,
    Priority,
    ProductBacklog,
    Sprint,
)


class TestPromptBuilder:
    """Tests for prompt construction."""

    def setup_method(self) -> None:
        self.builder = PromptBuilder()

    def test_sprint_planning_prompt(self) -> None:
        backlog = ProductBacklog(items=[
            BacklogItem(
                id="PBI-001",
                title="Implement decoder",
                priority=Priority.HIGH,
                story_points=8,
                status=BacklogStatus.READY,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
            BacklogItem(
                id="PBI-002",
                title="Done item",
                status=BacklogStatus.DONE,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        ])

        prompt = self.builder.build_sprint_planning_prompt(
            backlog=backlog,
            sprint_backlog=None,
            team=["alice", "bob"],
            sprint_duration_days=14,
        )

        assert "Sprint Planning" in prompt
        assert "PBI-001" in prompt
        assert "Implement decoder" in prompt
        assert "alice" in prompt
        assert "PBI-002" not in prompt  # Done items excluded

    def test_review_prompt(self) -> None:
        prompt = self.builder.build_review_prompt(
            diff="+ added line\n- removed line",
            sprint=Sprint(
                id="SPR-001",
                goal="Build decoder",
                start_date=datetime(2026, 1, 1, tzinfo=UTC),
                end_date=datetime(2026, 1, 15, tzinfo=UTC),
            ),
            related_papers=["arxiv:2301.01234"],
        )

        assert "Code Review" in prompt
        assert "added line" in prompt
        assert "SPR-001" in prompt
        assert "arxiv:2301.01234" in prompt

    def test_retrospective_prompt(self) -> None:
        board = KanbanBoard(columns=[
            KanbanColumn(name="In Progress", cards=["PBI-001"]),
            KanbanColumn(name="Done", cards=["PBI-002", "PBI-003"]),
        ])

        prompt = self.builder.build_retrospective_prompt(
            sprint=Sprint(
                id="SPR-001",
                goal="Test goal",
                start_date=datetime(2026, 1, 1, tzinfo=UTC),
                end_date=datetime(2026, 1, 15, tzinfo=UTC),
            ),
            board=board,
            velocity=16,
        )

        assert "Retrospective" in prompt
        assert "SPR-001" in prompt
        assert "2/3" in prompt
        assert "16" in prompt

    def test_daily_standup_prompt(self) -> None:
        board = KanbanBoard(columns=[
            KanbanColumn(name="In Progress", cards=["PBI-001"]),
            KanbanColumn(name="Done", cards=[]),
        ])

        prompt = self.builder.build_daily_standup_prompt(
            participant="alice",
            board=board,
        )

        assert "Daily Standup" in prompt
        assert "alice" in prompt
        assert "PBI-001" in prompt

    def test_hypothesis_prompt(self) -> None:
        prompt = self.builder.build_hypothesis_prompt(
            action="add",
            context="Testing quantum error rates",
        )

        assert "Hypothesis" in prompt
        assert "Add" in prompt
        assert "quantum error rates" in prompt

    def test_base_system_in_all_prompts(self) -> None:
        """Verify all prompts include the base system context."""
        board = KanbanBoard()
        sprint = Sprint(
            id="SPR-001",
            goal="Test",
            start_date=datetime(2026, 1, 1, tzinfo=UTC),
            end_date=datetime(2026, 1, 15, tzinfo=UTC),
        )

        prompts = [
            self.builder.build_sprint_planning_prompt(ProductBacklog(), None, [], 14),
            self.builder.build_review_prompt("diff"),
            self.builder.build_retrospective_prompt(sprint, board),
            self.builder.build_daily_standup_prompt("user", board),
            self.builder.build_hypothesis_prompt("add"),
            self.builder.build_analysis_prompt(board),
        ]

        for prompt in prompts:
            assert "GitScholar AI assistant" in prompt
