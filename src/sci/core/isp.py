"""ISP (Independent Scholar Program) level computation."""

from __future__ import annotations

from sci.models.scholar import ISPLevel, MilestoneTracker, SkillTree

# Thresholds: (min_milestones_achieved, min_total_skill_points)
_LEVEL_THRESHOLDS: list[tuple[ISPLevel, int, int]] = [
    (ISPLevel.MASTER, 15, 35),
    (ISPLevel.SCHOLAR, 7, 22),
    (ISPLevel.CONTRIBUTOR, 3, 12),
    (ISPLevel.EXPLORER, 1, 5),
    (ISPLevel.NOVICE, 0, 0),
]


def compute_isp_level(milestones: MilestoneTracker, skills: SkillTree) -> ISPLevel:
    """Compute the ISP level from milestones and skills.

    A scholar advances when they satisfy *either* the milestone count
    **or** the total skill-point threshold for that level.

    Level thresholds (highest first):
      MASTER      — 15+ achieved milestones  OR  35+ total skill points
      SCHOLAR     —  7+ achieved milestones  OR  22+ total skill points
      CONTRIBUTOR —  3+ achieved milestones  OR  12+ total skill points
      EXPLORER    —  1+ achieved milestones  OR   5+ total skill points
      NOVICE      — (default)
    """
    achieved_milestones = sum(1 for m in milestones.milestones if m.achieved)

    all_skills = (
        skills.technical
        + skills.research
        + skills.collaboration
        + skills.writing
    )
    total_skill_points = sum(s.level for s in all_skills)

    for level, min_milestones, min_skill_points in _LEVEL_THRESHOLDS:
        if achieved_milestones >= min_milestones or total_skill_points >= min_skill_points:
            return level

    return ISPLevel.NOVICE
