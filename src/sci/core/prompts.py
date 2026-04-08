"""Prompt builder for constructing System Prompts injected into the Agent."""

from __future__ import annotations

from sci.models.local import (
    KanbanBoard,
    ProductBacklog,
    Sprint,
    SprintBacklog,
)
from sci.models.scholar import ScholarProfile


class PromptBuilder:
    """Builds System Prompts for Agent interactions.

    Constructs rich, context-aware prompts that give the Agent full awareness
    of the current project state, scholar profile, and domain context.
    """

    BASE_SYSTEM = (
        "You are the GitScholar AI assistant, embedded in the `sci` CLI tool. "
        "You help academic researchers manage their projects using Scrum methodology "
        "and support their growth through the Independent Scholar Program (ISP). "
        "Always provide actionable, research-aware advice."
    )

    def build_sprint_planning_prompt(
        self,
        backlog: ProductBacklog,
        sprint_backlog: SprintBacklog | None,
        team: list[str],
        sprint_duration_days: int,
    ) -> str:
        """Build a prompt for sprint planning."""
        backlog_summary = "\n".join(
            f"  - [{item.id}] {item.title} (priority: {item.priority.value}, "
            f"points: {item.story_points or '?'}, status: {item.status.value})"
            for item in backlog.items
            if item.status.value in ("ready", "draft")
        )

        return (
            f"{self.BASE_SYSTEM}\n\n"
            f"## Sprint Planning Session\n\n"
            f"Team members: {', '.join(team)}\n"
            f"Sprint duration: {sprint_duration_days} days\n\n"
            f"### Available Backlog Items:\n{backlog_summary}\n\n"
            f"Help the team select items for the sprint, estimate story points, "
            f"and break items into tasks. Consider team capacity and priorities."
        )

    def build_review_prompt(
        self,
        diff: str,
        sprint: Sprint | None = None,
        related_papers: list[str] | None = None,
    ) -> str:
        """Build a prompt for code review with research context."""
        context_parts = [
            f"{self.BASE_SYSTEM}\n\n",
            "## Code Review\n\n",
            f"### Git Diff:\n```\n{diff}\n```\n\n",
        ]

        if sprint:
            context_parts.append(f"Current sprint: {sprint.id} — Goal: {sprint.goal}\n\n")

        if related_papers:
            papers_str = "\n".join(f"  - {p}" for p in related_papers)
            context_parts.append(f"### Related Papers:\n{papers_str}\n\n")

        context_parts.append(
            "Review this code change for:\n"
            "1. Correctness and potential bugs\n"
            "2. Alignment with the sprint goal and research objectives\n"
            "3. Code quality and maintainability\n"
            "4. Scientific rigor (if applicable)"
        )

        return "".join(context_parts)

    def build_retrospective_prompt(
        self,
        sprint: Sprint,
        board: KanbanBoard,
        velocity: int | None = None,
    ) -> str:
        """Build a prompt for sprint retrospective facilitation."""
        done_count = 0
        total_count = 0
        for col in board.columns:
            total_count += len(col.cards)
            if col.name == "Done":
                done_count = len(col.cards)

        return (
            f"{self.BASE_SYSTEM}\n\n"
            f"## Sprint Retrospective: {sprint.id}\n\n"
            f"Sprint Goal: {sprint.goal}\n"
            f"Items completed: {done_count}/{total_count}\n"
            f"Velocity: {velocity or 'N/A'} story points\n\n"
            f"Facilitate a retrospective discussion:\n"
            f"1. What went well?\n"
            f"2. What could be improved?\n"
            f"3. What action items should we commit to?\n\n"
            f"Focus on research-specific insights and team dynamics."
        )

    def build_daily_standup_prompt(
        self,
        participant: str,
        board: KanbanBoard,
        profile: ScholarProfile | None = None,
    ) -> str:
        """Build a prompt for daily standup facilitation."""
        in_progress = []
        for col in board.columns:
            if col.name == "In Progress":
                in_progress = col.cards
                break

        return (
            f"{self.BASE_SYSTEM}\n\n"
            f"## Daily Standup for {participant}\n\n"
            f"Items currently in progress: {', '.join(in_progress) or 'None'}\n\n"
            f"Guide the standup with:\n"
            f"1. What did you accomplish yesterday?\n"
            f"2. What will you work on today?\n"
            f"3. Are there any blockers?\n\n"
            f"Keep it focused and time-boxed."
        )

    def build_hypothesis_prompt(
        self,
        action: str,
        context: str = "",
    ) -> str:
        """Build a prompt for hypothesis-related interactions."""
        return (
            f"{self.BASE_SYSTEM}\n\n"
            f"## Research Hypothesis — {action.title()}\n\n"
            f"{context}\n\n"
            f"Help the scholar formulate a clear, testable hypothesis. "
            f"Consider:\n"
            f"1. Is the hypothesis specific and falsifiable?\n"
            f"2. What experiments could test it?\n"
            f"3. What evidence would support or refute it?"
        )

    def build_analysis_prompt(
        self,
        board: KanbanBoard,
        sprint: Sprint | None = None,
        backlog: ProductBacklog | None = None,
    ) -> str:
        """Build a prompt for project health analysis."""
        return (
            f"{self.BASE_SYSTEM}\n\n"
            f"## Project Health Analysis\n\n"
            f"Analyze the current state of the project and provide insights on:\n"
            f"1. Sprint health and progress\n"
            f"2. Potential risks or blockers\n"
            f"3. Suggestions for improving velocity\n"
            f"4. Research progress assessment"
        )
