"""Pydantic models for the global scholar profile (~/.gitscholar/)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# --- Enums ---


class ISPLevel(StrEnum):
    NOVICE = "novice"
    EXPLORER = "explorer"
    CONTRIBUTOR = "contributor"
    SCHOLAR = "scholar"
    MASTER = "master"


class MilestoneCategory(StrEnum):
    SCRUM = "scrum"
    RESEARCH = "research"
    COMMUNITY = "community"
    GROWTH = "growth"


class CLITheme(StrEnum):
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"


# --- Scholar Profile ---


class ScholarIdentity(BaseModel):
    name: str
    email: str = ""
    orcid: str = ""
    github: str = ""
    institution: str = ""
    research_interests: list[str] = Field(default_factory=list)
    isp_level: ISPLevel = ISPLevel.NOVICE
    joined_at: datetime = Field(default_factory=datetime.now)


class ScholarProfile(BaseModel):
    scholar: ScholarIdentity


# --- ISP Milestones ---


class Milestone(BaseModel):
    id: str
    name: str
    category: MilestoneCategory
    achieved: bool = False
    achieved_at: datetime | None = None
    project: str | None = None
    criteria: str = ""


class MilestoneTracker(BaseModel):
    milestones: list[Milestone] = Field(default_factory=list)


# --- Skills ---


class Skill(BaseModel):
    name: str
    level: int = Field(default=1, ge=1, le=5)
    evidence: list[str] = Field(default_factory=list)


class SkillTree(BaseModel):
    technical: list[Skill] = Field(default_factory=list)
    research: list[Skill] = Field(default_factory=list)
    collaboration: list[Skill] = Field(default_factory=list)
    writing: list[Skill] = Field(default_factory=list)


# --- Contributions ---


class Contribution(BaseModel):
    id: str
    project: str
    type: str  # code | review | research | writing | mentoring
    description: str = ""
    date: datetime = Field(default_factory=datetime.now)
    impact: str = ""


class ContributionLog(BaseModel):
    contributions: list[Contribution] = Field(default_factory=list)


# --- Reflections ---


class Reflection(BaseModel):
    period: str  # e.g., "2026-Q1"
    date: datetime = Field(default_factory=datetime.now)
    accomplishments: list[str] = Field(default_factory=list)
    challenges: list[str] = Field(default_factory=list)
    learnings: list[str] = Field(default_factory=list)
    goals_next_period: list[str] = Field(default_factory=list)
    notes: str = ""


# --- Global Settings ---


class CLISettings(BaseModel):
    theme: CLITheme = CLITheme.DARK
    language: str = "en"
    editor: str = "vim"
    pager: str = "less"


class LLMProviderConfig(BaseModel):
    """LLM API provider configuration.

    By default, values are read from environment variables:
      - SCI_LLM_API_KEY  (or CLAW_API_KEY as legacy fallback)
      - SCI_LLM_API_BASE
      - SCI_LLM_MODEL
      - SCI_LLM_PROVIDER
    """

    provider: str = ""
    api_key: str = ""
    api_base: str = ""
    model: str = ""


class AgentSettings(BaseModel):
    default_model: str = "claude-sonnet-4"
    api_key_env: str = "CLAW_API_KEY"
    max_tokens: int = 4096
    temperature: float = 0.3
    llm: LLMProviderConfig = Field(default_factory=LLMProviderConfig)


class GitConfig(BaseModel):
    """Git account configuration.

    By default, values are read from the system git config.
    Explicit values here override the system defaults.
    """

    user_name: str = ""
    user_email: str = ""
    signing_key: str = ""


class NotificationSettings(BaseModel):
    sprint_reminders: bool = True
    daily_standup_prompt: str = "09:00"
    milestone_celebrations: bool = True


class GlobalSettings(BaseModel):
    cli: CLISettings = Field(default_factory=CLISettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    git: GitConfig = Field(default_factory=GitConfig)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
