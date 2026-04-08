"""Tests for the Pydantic data models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sci.models.local import (
    BacklogItem,
    BacklogItemType,
    BacklogStatus,
    Evidence,
    EvidenceOutcome,
    Experiment,
    Hypothesis,
    HypothesisStatus,
    KanbanColumn,
    Priority,
    ProductBacklog,
    ProjectConfig,
    ProjectInfo,
    Sprint,
    SprintBacklog,
    SprintBacklogEntry,
    SprintTask,
    TaskStatus,
)
from sci.models.scholar import (
    CLITheme,
    GlobalSettings,
    ISPLevel,
    Milestone,
    MilestoneCategory,
    ScholarIdentity,
    ScholarProfile,
    Skill,
    SkillTree,
)


class TestLocalModels:
    """Tests for local state models."""

    def test_project_config(self) -> None:
        config = ProjectConfig(
            project=ProjectInfo(
                name="test",
                description="desc",
                domain="testing",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        assert config.version == "1.0"
        assert config.project.name == "test"
        assert config.scrum.sprint_duration_days == 14

    def test_backlog_item_defaults(self) -> None:
        item = BacklogItem(id="PBI-001", title="Test")
        assert item.type == BacklogItemType.RESEARCH_TASK
        assert item.priority == Priority.MEDIUM
        assert item.status == BacklogStatus.DRAFT
        assert item.story_points is None
        assert item.labels == []

    def test_backlog_item_full(self) -> None:
        item = BacklogItem(
            id="PBI-001",
            title="Implement decoder",
            description="Build MWPM decoder",
            type=BacklogItemType.RESEARCH_TASK,
            priority=Priority.HIGH,
            story_points=8,
            status=BacklogStatus.READY,
            acceptance_criteria=["Handles distance-3 codes"],
            labels=["decoder"],
            assignee="charlie",
            linked_hypotheses=["HYP-001"],
            linked_papers=["arxiv:2301.01234"],
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert item.story_points == 8
        assert len(item.acceptance_criteria) == 1
        assert item.linked_hypotheses[0] == "HYP-001"

    def test_product_backlog(self) -> None:
        backlog = ProductBacklog(items=[
            BacklogItem(id="PBI-001", title="A"),
            BacklogItem(id="PBI-002", title="B"),
        ])
        assert len(backlog.items) == 2

    def test_sprint_task(self) -> None:
        task = SprintTask(
            id="TASK-001",
            title="Write code",
            status=TaskStatus.IN_PROGRESS,
            estimated_hours=8,
        )
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.actual_hours is None

    def test_sprint_backlog(self) -> None:
        sb = SprintBacklog(
            sprint_id="SPR-001",
            items=[
                SprintBacklogEntry(
                    backlog_id="PBI-001",
                    tasks=[SprintTask(id="TASK-001", title="Code")],
                )
            ],
        )
        assert sb.sprint_id == "SPR-001"
        assert len(sb.items[0].tasks) == 1

    def test_sprint(self) -> None:
        sprint = Sprint(
            id="SPR-001",
            goal="Build decoder",
            start_date=datetime(2026, 1, 1, tzinfo=UTC),
            end_date=datetime(2026, 1, 15, tzinfo=UTC),
        )
        assert sprint.status == "active"
        assert sprint.velocity is None

    def test_kanban_column_wip(self) -> None:
        col = KanbanColumn(name="In Progress", wip_limit=3, cards=["A", "B"])
        assert len(col.cards) < col.wip_limit

    def test_hypothesis(self) -> None:
        hyp = Hypothesis(
            id="HYP-001",
            statement="Test statement",
            status=HypothesisStatus.TESTING,
            evidence=[
                Evidence(
                    type="experiment",
                    ref="EXP-001",
                    outcome=EvidenceOutcome.PARTIAL_SUPPORT,
                    notes="Partial results",
                )
            ],
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert hyp.status == HypothesisStatus.TESTING
        assert len(hyp.evidence) == 1
        assert hyp.evidence[0].outcome == EvidenceOutcome.PARTIAL_SUPPORT

    def test_experiment(self) -> None:
        exp = Experiment(
            id="EXP-001",
            title="Noise test",
            hypothesis_id="HYP-001",
            parameters={"noise_rate": 0.01, "distance": 3},
            results={"error_rate": 0.005},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert exp.parameters["noise_rate"] == 0.01


class TestScholarModels:
    """Tests for global scholar models."""

    def test_scholar_profile(self) -> None:
        profile = ScholarProfile(
            scholar=ScholarIdentity(
                name="Charlie",
                email="charlie@test.edu",
                isp_level=ISPLevel.EXPLORER,
                research_interests=["quantum"],
                joined_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        assert profile.scholar.isp_level == ISPLevel.EXPLORER
        assert profile.scholar.research_interests == ["quantum"]

    def test_milestone(self) -> None:
        m = Milestone(
            id="ISP-M001",
            name="First Sprint",
            category=MilestoneCategory.SCRUM,
            achieved=True,
            achieved_at=datetime(2026, 2, 1, tzinfo=UTC),
        )
        assert m.achieved is True
        assert m.category == MilestoneCategory.SCRUM

    def test_skill_bounds(self) -> None:
        skill = Skill(name="Python", level=3)
        assert 1 <= skill.level <= 5

        with pytest.raises(ValidationError):
            Skill(name="Bad", level=0)

        with pytest.raises(ValidationError):
            Skill(name="Bad", level=6)

    def test_skill_tree(self) -> None:
        tree = SkillTree(
            technical=[Skill(name="Python", level=3)],
            research=[Skill(name="Hypothesis", level=2)],
        )
        assert len(tree.technical) == 1
        assert len(tree.research) == 1
        assert len(tree.collaboration) == 0

    def test_global_settings_defaults(self) -> None:
        settings = GlobalSettings()
        assert settings.cli.theme == CLITheme.DARK
        assert settings.agent.default_model == "claude-sonnet-4"
        assert settings.agent.temperature == 0.3
        assert settings.notifications.milestone_celebrations is True

    def test_serialization_roundtrip(self) -> None:
        """Test that models can be serialized and deserialized."""
        profile = ScholarProfile(
            scholar=ScholarIdentity(
                name="Test",
                email="test@test.com",
                isp_level=ISPLevel.CONTRIBUTOR,
                joined_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        data = profile.model_dump(mode="json")
        loaded = ScholarProfile.model_validate(data)
        assert loaded.scholar.name == "Test"
        assert loaded.scholar.isp_level == ISPLevel.CONTRIBUTOR
