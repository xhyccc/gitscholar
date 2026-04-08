"""Pydantic models for the local project state (.gitscholar/)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# --- Enums ---


class BacklogItemType(str, Enum):
    RESEARCH_TASK = "research_task"
    EXPERIMENT = "experiment"
    WRITING = "writing"
    REVIEW = "review"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BacklogStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class HypothesisStatus(str, Enum):
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    REVISED = "revised"


class EvidenceOutcome(str, Enum):
    SUPPORT = "support"
    PARTIAL_SUPPORT = "partial_support"
    REFUTE = "refute"
    INCONCLUSIVE = "inconclusive"


# --- Project Configuration ---


class ScrumRoles(BaseModel):
    product_owner: str | None = None
    scrum_master: str | None = None
    team: list[str] = Field(default_factory=list)


class ScrumConfig(BaseModel):
    sprint_duration_days: int = 14
    roles: ScrumRoles = Field(default_factory=ScrumRoles)


class AgentConfig(BaseModel):
    engine: str = "claw-code"
    model: str = "claude-sonnet-4"
    context_window: int = 200000
    tools_enabled: list[str] = Field(default_factory=lambda: [
        "git_diff_analyzer",
        "paper_reader",
        "hypothesis_tracker",
    ])


class ProjectInfo(BaseModel):
    name: str
    description: str = ""
    domain: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class ProjectConfig(BaseModel):
    version: str = "1.0"
    project: ProjectInfo
    scrum: ScrumConfig = Field(default_factory=ScrumConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)


# --- Backlog ---


class BacklogItem(BaseModel):
    id: str
    title: str
    description: str = ""
    type: BacklogItemType = BacklogItemType.RESEARCH_TASK
    priority: Priority = Priority.MEDIUM
    story_points: int | None = None
    status: BacklogStatus = BacklogStatus.DRAFT
    acceptance_criteria: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    assignee: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    linked_hypotheses: list[str] = Field(default_factory=list)
    linked_papers: list[str] = Field(default_factory=list)


class ProductBacklog(BaseModel):
    items: list[BacklogItem] = Field(default_factory=list)


# --- Sprint ---


class SprintTask(BaseModel):
    id: str
    title: str
    assignee: str | None = None
    status: TaskStatus = TaskStatus.TODO
    estimated_hours: float | None = None
    actual_hours: float | None = None
    branch: str | None = None


class SprintBacklogEntry(BaseModel):
    backlog_id: str
    tasks: list[SprintTask] = Field(default_factory=list)


class SprintBacklog(BaseModel):
    sprint_id: str
    items: list[SprintBacklogEntry] = Field(default_factory=list)


class Sprint(BaseModel):
    id: str
    goal: str = ""
    start_date: datetime
    end_date: datetime
    status: str = "active"  # active | completed | cancelled
    velocity: int | None = None


# --- Kanban Board ---


class KanbanColumn(BaseModel):
    name: str
    wip_limit: int | None = None
    cards: list[str] = Field(default_factory=list)


class KanbanBoard(BaseModel):
    columns: list[KanbanColumn] = Field(default_factory=lambda: [
        KanbanColumn(name="Backlog"),
        KanbanColumn(name="To Do", wip_limit=5),
        KanbanColumn(name="In Progress", wip_limit=3),
        KanbanColumn(name="In Review", wip_limit=2),
        KanbanColumn(name="Done"),
    ])


# --- Research ---


class Evidence(BaseModel):
    type: str  # experiment | observation | literature
    ref: str
    outcome: EvidenceOutcome = EvidenceOutcome.INCONCLUSIVE
    notes: str = ""


class Hypothesis(BaseModel):
    id: str
    statement: str
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    evidence: list[Evidence] = Field(default_factory=list)
    linked_tasks: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class HypothesesTracker(BaseModel):
    hypotheses: list[Hypothesis] = Field(default_factory=list)


class Experiment(BaseModel):
    id: str
    title: str
    hypothesis_id: str | None = None
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)
    results: dict[str, str | int | float | bool] = Field(default_factory=dict)
    conclusion: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class ExperimentLog(BaseModel):
    experiments: list[Experiment] = Field(default_factory=list)


class PaperReference(BaseModel):
    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    ref: str  # arXiv ID, DOI, or local path
    notes: str = ""
    tags: list[str] = Field(default_factory=list)
    added_at: datetime = Field(default_factory=datetime.now)


class PaperLibrary(BaseModel):
    papers: list[PaperReference] = Field(default_factory=list)


# --- Daily Standup ---


class DailyEntry(BaseModel):
    date: str  # YYYY-MM-DD
    participant: str
    yesterday: str = ""
    today: str = ""
    blockers: str = ""
    notes: str = ""


class DailyLog(BaseModel):
    entries: list[DailyEntry] = Field(default_factory=list)


# --- Retrospective ---


class RetroItem(BaseModel):
    category: str  # went_well | to_improve | action_item
    text: str
    author: str | None = None


class Retrospective(BaseModel):
    sprint_id: str
    date: datetime = Field(default_factory=datetime.now)
    items: list[RetroItem] = Field(default_factory=list)
    summary: str = ""
