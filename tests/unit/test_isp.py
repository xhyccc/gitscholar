"""Tests for ISP level auto-computation."""

from __future__ import annotations

from datetime import UTC, datetime

from sci.core.isp import compute_isp_level
from sci.models.scholar import (
    ISPLevel,
    Milestone,
    MilestoneCategory,
    MilestoneTracker,
    Skill,
    SkillTree,
)


def _milestone(i: int, achieved: bool = True) -> Milestone:
    return Milestone(
        id=f"ISP-M{i:03d}",
        name=f"Milestone {i}",
        category=MilestoneCategory.SCRUM,
        achieved=achieved,
        achieved_at=datetime(2026, 1, 1, tzinfo=UTC) if achieved else None,
    )


def _skill(level: int) -> Skill:
    return Skill(name=f"skill-{level}", level=level)


class TestComputeISPLevel:
    def test_novice_no_milestones_no_skills(self) -> None:
        level = compute_isp_level(MilestoneTracker(), SkillTree())
        assert level == ISPLevel.NOVICE

    def test_explorer_by_milestone(self) -> None:
        tracker = MilestoneTracker(milestones=[_milestone(1)])
        level = compute_isp_level(tracker, SkillTree())
        assert level == ISPLevel.EXPLORER

    def test_explorer_by_skill_points(self) -> None:
        # 5 points total (one skill at level 5) → EXPLORER
        tree = SkillTree(technical=[_skill(5)])
        level = compute_isp_level(MilestoneTracker(), tree)
        assert level == ISPLevel.EXPLORER

    def test_contributor_by_milestones(self) -> None:
        tracker = MilestoneTracker(milestones=[_milestone(i) for i in range(3)])
        level = compute_isp_level(tracker, SkillTree())
        assert level == ISPLevel.CONTRIBUTOR

    def test_contributor_by_skill_points(self) -> None:
        # 3 skills at level 4 = 12 points → CONTRIBUTOR
        tree = SkillTree(technical=[_skill(4), _skill(4), _skill(4)])
        level = compute_isp_level(MilestoneTracker(), tree)
        assert level == ISPLevel.CONTRIBUTOR

    def test_scholar_by_milestones(self) -> None:
        tracker = MilestoneTracker(milestones=[_milestone(i) for i in range(7)])
        level = compute_isp_level(tracker, SkillTree())
        assert level == ISPLevel.SCHOLAR

    def test_master_by_milestones(self) -> None:
        tracker = MilestoneTracker(milestones=[_milestone(i) for i in range(15)])
        level = compute_isp_level(tracker, SkillTree())
        assert level == ISPLevel.MASTER

    def test_master_by_skill_points(self) -> None:
        # 7 skills at level 5 = 35 points → MASTER
        tree = SkillTree(technical=[_skill(5) for _ in range(7)])
        level = compute_isp_level(MilestoneTracker(), tree)
        assert level == ISPLevel.MASTER

    def test_unachieved_milestones_dont_count(self) -> None:
        # 5 milestones but none achieved → NOVICE
        tracker = MilestoneTracker(
            milestones=[_milestone(i, achieved=False) for i in range(5)]
        )
        level = compute_isp_level(tracker, SkillTree())
        assert level == ISPLevel.NOVICE

    def test_mixed_skills_across_categories(self) -> None:
        # 3 points each across 4 categories = 12 → CONTRIBUTOR
        tree = SkillTree(
            technical=[_skill(3)],
            research=[_skill(3)],
            collaboration=[_skill(3)],
            writing=[_skill(3)],
        )
        level = compute_isp_level(MilestoneTracker(), tree)
        assert level == ISPLevel.CONTRIBUTOR

    def test_higher_of_milestones_or_skills(self) -> None:
        # 1 milestone = EXPLORER, but 5*5 + 1*4 = 29 skill points = SCHOLAR
        # (SCHOLAR threshold: 22+ points) → skill-based level wins
        tracker = MilestoneTracker(milestones=[_milestone(1)])
        tree = SkillTree(technical=[_skill(5) for _ in range(5)],
                         research=[_skill(4) for _ in range(1)])
        level = compute_isp_level(tracker, tree)
        assert level == ISPLevel.SCHOLAR
