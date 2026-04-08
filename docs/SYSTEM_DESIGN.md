# GitScholar CLI (`sci`) — System Design Document

> **Version**: 1.0.0-draft  
> **Last Updated**: 2026-04-08  
> **Status**: Design Phase

---

## Table of Contents

1. [Overview & Architectural Philosophy](#1-overview--architectural-philosophy)
2. [System Data Flow & Persistence Layer Design](#2-system-data-flow--persistence-layer-design)
3. [Orchestration Layer Design](#3-orchestration-layer-design)
4. [Agent Engine Layer Design](#4-agent-engine-layer-design)
5. [Frontend CLI Layer Design](#5-frontend-cli-layer-design)
6. [Command Reference](#6-command-reference)
7. [Independent Scholar Program (ISP)](#7-independent-scholar-program-isp)
8. [Security & Privacy](#8-security--privacy)
9. [Extension & Plugin Architecture](#9-extension--plugin-architecture)

---

## 1. Overview & Architectural Philosophy

### 1.1 Positioning

`sci` (GitScholar CLI) is a command-line collaboration and growth tool tailored for the academic and scientific research domain. Built upon the powerful Agent capabilities of `ultraworkers/claw-code`, it injects standard agile Scrum workflows and the **Independent Scholar Program (ISP)** into the daily Git workflow.

**Core Vision:**

- **Project Completes** — Projects land successfully with the help of Scrum.
- **Individuals Grow** — Scholars emerge and break through via the ISP.

### 1.2 Macro Architecture Design

The system adopts a **Four-Tier Architecture**, decoupling complex LLM reasoning from simple user interactions:

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend CLI Layer                       │
│         (Typer routing + Rich UI rendering)               │
│  Kanban boards · Progress bars · Syntax highlighting      │
│  Interactive dialogues · Scholar dashboards                │
├─────────────────────────────────────────────────────────┤
│                Orchestration Layer (sci Core)              │
│    Command parsing · State management · Prompt building   │
│    Tool registration · Workflow coordination              │
├─────────────────────────────────────────────────────────┤
│              Agent Engine Layer (claw-code)                │
│   LLM dialogue · Context windows · Git Diff analysis      │
│   Academic document reading · Tool execution              │
├─────────────────────────────────────────────────────────┤
│                  Persistence Layer                         │
│     Local State (.gitscholar/) · Global Profile           │
│     (~/.gitscholar/) · JSON/YAML · Git-compatible         │
└─────────────────────────────────────────────────────────┘
```

### 1.3 Design Principles

| Principle | Description |
|-----------|-------------|
| **Plain-text first** | All state stored in JSON/YAML — Git-friendly, human-readable, Agent-parseable |
| **Offline capable** | Core Scrum workflows function without network; LLM features degrade gracefully |
| **Composable** | Each layer can be tested and extended independently |
| **Research-native** | First-class support for papers, experiments, hypotheses, and scholarly milestones |
| **Privacy-conscious** | Scholar profiles are local-first; opt-in sharing only |

---

## 2. System Data Flow & Persistence Layer Design

All files use JSON/YAML formats which are Agent-friendly and fully compatible with Git version control. Data is separated into **local** and **global** tiers.

### 2.1 Local State Library (`.gitscholar/`)

Scoped to a single Git repository, this directory stores all project-level Scrum and research state.

```
.gitscholar/
├── config.yaml              # Project-level configuration
├── backlog/
│   ├── product_backlog.yaml # All user stories / research tasks
│   └── sprint_backlog.yaml  # Current sprint items
├── sprints/
│   ├── current.yaml         # Active sprint metadata
│   └── archive/
│       └── sprint_001.yaml  # Completed sprint records
├── board/
│   └── kanban.yaml          # Board state (columns + card positions)
├── retrospectives/
│   └── sprint_001.yaml      # Retro notes per sprint
├── research/
│   ├── hypotheses.yaml      # Research hypotheses tracker
│   ├── experiments.yaml     # Experiment log
│   └── papers.yaml          # Paper references & reading notes
└── dailies/
    └── 2026-04-08.yaml      # Daily standup records
```

#### 2.1.1 `config.yaml` — Project Configuration

```yaml
version: "1.0"
project:
  name: "quantum-error-correction"
  description: "Exploring novel QEC codes for near-term devices"
  domain: "quantum-computing"
  created_at: "2026-01-15T10:00:00Z"

scrum:
  sprint_duration_days: 14
  roles:
    product_owner: "alice"
    scrum_master: "bob"
    team:
      - "charlie"
      - "diana"

agent:
  engine: "claw-code"
  model: "claude-sonnet-4"
  context_window: 200000
  tools_enabled:
    - "git_diff_analyzer"
    - "paper_reader"
    - "hypothesis_tracker"
```

#### 2.1.2 `product_backlog.yaml` — Product Backlog

```yaml
items:
  - id: "PBI-001"
    title: "Implement surface code decoder"
    description: "Build a minimum-weight perfect matching decoder"
    type: "research_task"          # research_task | experiment | writing | review
    priority: "high"               # critical | high | medium | low
    story_points: 8
    status: "ready"                # draft | ready | in_progress | done | blocked
    acceptance_criteria:
      - "Decoder handles distance-3 codes"
      - "Error rate below threshold on simulated noise"
    labels: ["decoder", "core"]
    assignee: "charlie"
    created_at: "2026-01-20T09:00:00Z"
    updated_at: "2026-02-01T14:30:00Z"
    linked_hypotheses: ["HYP-001"]
    linked_papers: ["arxiv:2301.01234"]
```

#### 2.1.3 `sprint_backlog.yaml` — Sprint Backlog

```yaml
sprint_id: "SPR-003"
items:
  - backlog_id: "PBI-001"
    tasks:
      - id: "TASK-001"
        title: "Write MWPM algorithm"
        assignee: "charlie"
        status: "in_progress"      # todo | in_progress | review | done
        estimated_hours: 12
        actual_hours: 8
        branch: "feature/mwpm-decoder"
      - id: "TASK-002"
        title: "Add unit tests for decoder"
        assignee: "charlie"
        status: "todo"
        estimated_hours: 4
```

#### 2.1.4 `kanban.yaml` — Board State

```yaml
columns:
  - name: "Backlog"
    wip_limit: null
    cards: ["PBI-003", "PBI-004"]
  - name: "To Do"
    wip_limit: 5
    cards: ["PBI-002"]
  - name: "In Progress"
    wip_limit: 3
    cards: ["PBI-001"]
  - name: "In Review"
    wip_limit: 2
    cards: []
  - name: "Done"
    wip_limit: null
    cards: ["PBI-000"]
```

#### 2.1.5 `hypotheses.yaml` — Research Hypotheses

```yaml
hypotheses:
  - id: "HYP-001"
    statement: "MWPM decoding achieves sub-threshold error rates for distance-5 surface codes"
    status: "testing"              # proposed | testing | supported | refuted | revised
    evidence:
      - type: "experiment"
        ref: "EXP-001"
        outcome: "partial_support"
        notes: "Works for distance-3, scaling to distance-5 pending"
    linked_tasks: ["PBI-001"]
    created_at: "2026-01-18T11:00:00Z"
```

### 2.2 Global Scholar Profile (`~/.gitscholar/`)

Spans across all projects. Tracks the individual scholar's growth trajectory via the ISP.

```
~/.gitscholar/
├── profile.yaml               # Scholar identity & preferences
├── isp/
│   ├── milestones.yaml        # ISP milestone tracker
│   ├── skills.yaml            # Skill tree / competency map
│   └── reflections/
│       └── 2026-Q1.yaml       # Quarterly self-reflections
├── contributions/
│   └── log.yaml               # Cross-project contribution log
└── settings.yaml              # Global CLI settings
```

#### 2.2.1 `profile.yaml` — Scholar Profile

```yaml
scholar:
  name: "Charlie Zhang"
  email: "charlie@university.edu"
  orcid: "0000-0002-1234-5678"
  github: "charlie-z"
  institution: "University of Quantum Sciences"
  research_interests:
    - "quantum error correction"
    - "topological codes"
    - "fault-tolerant quantum computing"
  isp_level: "explorer"           # novice | explorer | contributor | scholar | master
  joined_at: "2025-09-01T00:00:00Z"
```

#### 2.2.2 `milestones.yaml` — ISP Milestones

```yaml
milestones:
  - id: "ISP-M001"
    name: "First Research Sprint Completed"
    category: "scrum"
    achieved: true
    achieved_at: "2026-02-01T16:00:00Z"
    project: "quantum-error-correction"
  - id: "ISP-M002"
    name: "First Hypothesis Tested"
    category: "research"
    achieved: true
    achieved_at: "2026-02-15T10:00:00Z"
    project: "quantum-error-correction"
  - id: "ISP-M003"
    name: "First Paper Review Contributed"
    category: "community"
    achieved: false
    criteria: "Complete a structured review of a peer's paper using sci review"
```

#### 2.2.3 `skills.yaml` — Skill Tree

```yaml
skills:
  technical:
    - name: "Python"
      level: 3                    # 1-5 scale
      evidence: ["PBI-001", "PBI-005"]
    - name: "Quantum Computing"
      level: 2
      evidence: ["HYP-001"]
  research:
    - name: "Hypothesis Formation"
      level: 2
      evidence: ["HYP-001", "HYP-002"]
    - name: "Scientific Writing"
      level: 1
      evidence: []
  collaboration:
    - name: "Code Review"
      level: 2
      evidence: ["PR-012", "PR-015"]
    - name: "Sprint Planning"
      level: 1
      evidence: ["SPR-001"]
```

#### 2.2.4 `settings.yaml` — Global Settings

```yaml
cli:
  theme: "dark"                   # dark | light | auto
  language: "en"                  # en | zh | ja | ...
  editor: "vim"
  pager: "less"

agent:
  max_tokens: 4096
  temperature: 0.3

notifications:
  sprint_reminders: true
  daily_standup_prompt: "09:00"
  milestone_celebrations: true
```

### 2.3 Data Flow Diagram

```
User Command (e.g., `sci sprint start`)
        │
        ▼
┌──────────────────┐
│  Frontend CLI     │ ── parse args, validate input
│  (Typer + Rich)   │
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│  Orchestration    │ ── load .gitscholar/ state
│  Layer (sci Core) │ ── construct System Prompt
│                   │ ── register available Tools
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│  Agent Engine     │ ── execute LLM reasoning
│  (claw-code)      │ ── call registered Tools
│                   │ ── return structured output
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│  Persistence      │ ── write updated state
│  Layer            │ ── update .gitscholar/*.yaml
│                   │ ── update ~/.gitscholar/*.yaml
└──────────────────┘
        │
        ▼
    Rich UI Output (Kanban board, progress, etc.)
```

---

## 3. Orchestration Layer Design

### 3.1 Responsibilities

The orchestration layer is the **central nervous system** of `sci`. It:

1. **Parses CLI commands** and maps them to internal operations
2. **Reads/writes local and global state** from the persistence layer
3. **Constructs System Prompts** that are injected into the Agent for context-aware reasoning
4. **Registers and exposes Tool Calling interfaces** customized for research workflows
5. **Coordinates multi-step workflows** (e.g., sprint planning involves backlog grooming → capacity check → commitment)

### 3.2 State Manager

```python
# Conceptual interface
class StateManager:
    """Manages reading and writing of all .gitscholar/ and ~/.gitscholar/ state."""

    def load_local_config(self) -> ProjectConfig: ...
    def load_backlog(self) -> ProductBacklog: ...
    def load_sprint(self) -> Sprint: ...
    def load_board(self) -> KanbanBoard: ...
    def load_scholar_profile(self) -> ScholarProfile: ...

    def save_sprint(self, sprint: Sprint) -> None: ...
    def save_board(self, board: KanbanBoard) -> None: ...
    def save_milestone(self, milestone: Milestone) -> None: ...
```

### 3.3 Prompt Builder

The Prompt Builder constructs rich System Prompts that give the Agent full context:

```python
class PromptBuilder:
    """Builds System Prompts for Agent interactions."""

    def build_sprint_planning_prompt(self, backlog, team, capacity) -> str:
        """Injects backlog items, team composition, and capacity into prompt."""
        ...

    def build_review_prompt(self, diff, paper_context) -> str:
        """Creates a review-focused prompt with Git diff and related paper context."""
        ...

    def build_retrospective_prompt(self, sprint_data, metrics) -> str:
        """Builds a retrospective analysis prompt with sprint metrics."""
        ...
```

### 3.4 Tool Registry

The orchestration layer exposes domain-specific tools to the Agent:

| Tool Name | Description | Input | Output |
|-----------|-------------|-------|--------|
| `git_diff_analyzer` | Analyze Git diffs for code quality & research relevance | `branch`, `base` | Structured analysis |
| `paper_reader` | Read and summarize academic papers | `arxiv_id` or `path` | Summary + key findings |
| `hypothesis_tracker` | Create/update/query research hypotheses | `action`, `hypothesis` | Updated hypothesis state |
| `experiment_logger` | Log experiment parameters and results | `experiment_data` | Experiment record |
| `backlog_manager` | CRUD operations on backlog items | `action`, `item` | Updated backlog |
| `sprint_manager` | Sprint lifecycle operations | `action`, `sprint_data` | Sprint state |
| `skill_assessor` | Evaluate and update scholar skills | `context`, `evidence` | Updated skill levels |
| `milestone_checker` | Check and award ISP milestones | `scholar`, `context` | Milestone updates |

---

## 4. Agent Engine Layer Design

### 4.1 Integration with claw-code

The Agent Engine wraps `ultraworkers/claw-code` as a headless engine:

```python
class AgentEngine:
    """Wraps claw-code as a headless LLM Agent engine."""

    def __init__(self, config: AgentConfig):
        self.model = config.model
        self.tools = ToolRegistry()

    def execute(self, system_prompt: str, user_message: str,
                tools: list[Tool]) -> AgentResponse:
        """
        Execute an Agent interaction.

        1. Injects system_prompt for context
        2. Sends user_message
        3. Agent may call registered tools
        4. Returns structured response
        """
        ...
```

### 4.2 Context Window Management

For research-heavy workflows, context management is critical:

- **Git Diff Context**: Automatically trims diffs to fit within context windows, prioritizing changed files related to current sprint tasks.
- **Paper Context**: Loads relevant sections of linked papers when reviewing code or hypotheses.
- **Sprint Context**: Includes current sprint state, recent standups, and velocity metrics.

### 4.3 Tool Execution Flow

```
Agent receives prompt
    │
    ├── Decides to call `git_diff_analyzer`
    │       │
    │       ▼
    │   Orchestration Layer executes tool
    │       │
    │       ▼
    │   Returns structured result to Agent
    │
    ├── Agent reasons about the result
    │
    ├── May call additional tools (e.g., `hypothesis_tracker`)
    │
    └── Returns final structured response
```

---

## 5. Frontend CLI Layer Design

### 5.1 Technology Stack

| Component | Library | Purpose |
|-----------|---------|---------|
| Command routing | `typer` | Declarative CLI command definition |
| Rich output | `rich` | Tables, panels, progress bars, markdown, syntax highlighting |
| Interactive prompts | `rich.prompt` / `questionary` | User input dialogs |
| Terminal UI | `rich.live` | Live-updating Kanban boards |

### 5.2 UI Components

#### Kanban Board (Terminal)

```
╭──────────────────────────────────────────────────────────────────╮
│                    Sprint 3 — Kanban Board                        │
├────────────┬────────────┬──────────────┬───────────┬─────────────┤
│  Backlog   │   To Do    │ In Progress  │ In Review │    Done     │
│            │  WIP: 5    │   WIP: 3     │  WIP: 2   │             │
├────────────┼────────────┼──────────────┼───────────┼─────────────┤
│ [PBI-003]  │ [PBI-002]  │ [PBI-001]    │           │ [PBI-000]   │
│ Write      │ Set up CI  │ ■■■■□□ 67%  │           │ ✓ Project   │
│ intro      │            │ MWPM decoder │           │   setup     │
│ section    │            │ @charlie     │           │             │
│            │            │              │           │             │
│ [PBI-004]  │            │              │           │             │
│ Lit review │            │              │           │             │
╰────────────┴────────────┴──────────────┴───────────┴─────────────╯
```

#### Sprint Progress Bar

```
Sprint 3 Progress ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 67% (Day 10/14)
  Stories: 2/3 done │ Tasks: 5/8 done │ Velocity: 16 pts (avg: 14)
```

#### Scholar Dashboard

```
╭─────────────────────────────────────────────╮
│          🎓 Scholar Profile                  │
│                                              │
│  Name:  Charlie Zhang                        │
│  Level: Explorer ⭐⭐                        │
│  ORCID: 0000-0002-1234-5678                 │
│                                              │
│  ── Recent Milestones ──                     │
│  ✓ First Sprint Completed     2026-02-01     │
│  ✓ First Hypothesis Tested    2026-02-15     │
│  ○ First Paper Review         In Progress    │
│                                              │
│  ── Skill Highlights ──                      │
│  Python          ███░░  3/5                  │
│  Quantum Comp.   ██░░░  2/5                  │
│  Hypothesis      ██░░░  2/5                  │
│  Sci. Writing    █░░░░  1/5                  │
╰─────────────────────────────────────────────╯
```

---

## 6. Command Reference

### 6.1 Project & Configuration

| Command | Description |
|---------|-------------|
| `sci init` | Initialize `.gitscholar/` in current repo with interactive setup |
| `sci config [key] [value]` | View or update project configuration |
| `sci config --global [key] [value]` | View or update global settings |

### 6.2 Scrum Workflow

| Command | Description |
|---------|-------------|
| `sci backlog list` | Show product backlog with filters and sorting |
| `sci backlog add` | Add a new backlog item (interactive or from flags) |
| `sci backlog groom` | Agent-assisted backlog grooming session |
| `sci sprint start` | Start a new sprint with planning ceremony |
| `sci sprint status` | Show current sprint progress |
| `sci sprint end` | End the current sprint, trigger retrospective |
| `sci board` | Display the Kanban board in terminal |
| `sci board move <item> <column>` | Move an item on the board |
| `sci daily` | Record a daily standup (interactive or Agent-guided) |
| `sci retro` | Run a sprint retrospective (Agent-facilitated) |

### 6.3 Research Workflow

| Command | Description |
|---------|-------------|
| `sci hypothesis add` | Propose a new research hypothesis |
| `sci hypothesis status [id]` | Check hypothesis status and evidence |
| `sci experiment log` | Log experiment parameters and results |
| `sci paper add <ref>` | Add a paper reference (arXiv, DOI, local file) |
| `sci paper review <ref>` | Agent-assisted paper review |
| `sci review` | Agent-assisted code review with research context |

### 6.4 Scholar & ISP

| Command | Description |
|---------|-------------|
| `sci scholar` | Show scholar dashboard |
| `sci scholar milestones` | List all ISP milestones and progress |
| `sci scholar skills` | Show skill tree |
| `sci scholar reflect` | Start a guided self-reflection session |

### 6.5 Agent Interaction

| Command | Description |
|---------|-------------|
| `sci ask <question>` | Ask the Agent a research question with project context |
| `sci analyze` | Agent analysis of recent Git activity and sprint health |
| `sci suggest` | Get Agent suggestions for next actions |

---

## 7. Independent Scholar Program (ISP)

### 7.1 Overview

The ISP is a structured growth framework that tracks and encourages scholar development across multiple dimensions:

- **Research Skills**: Hypothesis formation, experimental design, data analysis
- **Technical Skills**: Programming, tooling, infrastructure
- **Collaboration Skills**: Code review, mentoring, communication
- **Writing Skills**: Scientific writing, documentation, presentations

### 7.2 Level Progression

| Level | Name | Requirements |
|-------|------|-------------|
| 1 | **Novice** | Complete `sci init`, first daily standup |
| 2 | **Explorer** | Complete first sprint, test first hypothesis |
| 3 | **Contributor** | Review a peer's work, contribute to shared backlog |
| 4 | **Scholar** | Publish findings, mentor a novice, demonstrate cross-project impact |
| 5 | **Master** | Lead a multi-sprint research project, demonstrate sustained velocity |

### 7.3 Milestone Categories

- **Scrum Milestones**: Sprint completion, velocity improvements, effective retrospectives
- **Research Milestones**: Hypotheses tested, experiments completed, papers reviewed
- **Community Milestones**: Code reviews, mentoring sessions, knowledge sharing
- **Growth Milestones**: Skill level-ups, self-reflections, cross-project contributions

### 7.4 Milestone Evaluation

Milestones are evaluated automatically by the Agent when relevant commands are executed. For example:

- After `sci sprint end` → checks for sprint-related milestones
- After `sci hypothesis status` → checks for research milestones
- After `sci review` → checks for community milestones

---

## 8. Security & Privacy

### 8.1 Principles

1. **Local-first**: All scholar data lives on the user's machine by default
2. **No telemetry**: Zero data collection without explicit opt-in
3. **API key safety**: Keys stored in environment variables, never in config files
4. **Git-aware**: `.gitscholar/` can be selectively `.gitignore`d for sensitive data

### 8.2 Sensitive Data Handling

```yaml
# Recommended .gitignore additions
.gitscholar/dailies/       # Personal standup notes
.gitscholar/research/      # May contain unpublished research data
```

### 8.3 Agent Interaction Safety

- All Agent interactions are logged locally for auditability
- Tool calls are sandboxed — the Agent cannot modify files outside `.gitscholar/`
- User confirmation required for destructive operations (e.g., deleting backlog items)

---

## 9. Extension & Plugin Architecture

### 9.1 Custom Tools

Third-party tools can be registered with the orchestration layer:

```python
from sci.core.tools import ToolRegistry, Tool

@ToolRegistry.register
class CustomAnalyzer(Tool):
    name = "custom_analyzer"
    description = "Analyze domain-specific data"

    def execute(self, **kwargs) -> dict:
        # Custom analysis logic
        ...
```

### 9.2 Custom Milestone Definitions

Organizations can define custom ISP milestones:

```yaml
# .gitscholar/isp_extensions.yaml
custom_milestones:
  - id: "CUSTOM-M001"
    name: "Lab Meeting Presentation"
    category: "communication"
    criteria: "Present sprint results in a lab meeting (manually confirmed)"
    manual_confirmation: true
```

### 9.3 Theme & Localization

- Custom Rich themes via `~/.gitscholar/themes/`
- Localization files via `~/.gitscholar/i18n/`

---

## Appendix A: Technology Stack Summary

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | ≥ 3.11 |
| CLI Framework | Typer | ≥ 0.9 |
| Terminal UI | Rich | ≥ 13.0 |
| Data Serialization | PyYAML / ruamel.yaml | Latest |
| Data Validation | Pydantic | ≥ 2.0 |
| Agent Engine | claw-code | Latest |
| Testing | pytest | ≥ 7.0 |
| Linting | ruff | Latest |
| Type Checking | mypy | Latest |

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| **ISP** | Independent Scholar Program — a cross-project growth framework |
| **PBI** | Product Backlog Item — a unit of work in the Scrum backlog |
| **Sprint** | A time-boxed iteration (default: 2 weeks) |
| **Kanban Board** | Visual workflow board with columns and WIP limits |
| **Hypothesis** | A testable research claim tracked through the evidence lifecycle |
| **claw-code** | The underlying Agent engine from ultraworkers |
| **Tool Calling** | The mechanism by which the Agent invokes registered tools |
| **Scholar Profile** | A global identity and growth tracker for individual researchers |
