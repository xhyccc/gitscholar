# GitScholar CLI (`sci`)

> A command-line collaboration and growth tool for academic and scientific research.

**Core Vision**: *Project Completes* (via Scrum) · *Individuals Grow* (via the Independent Scholar Program)

## Features

- 📋 **Scrum Workflow**: Full product backlog, sprint management, Kanban board, dailies, and retrospectives — all from your terminal
- 🔬 **Research Native**: Track hypotheses, log experiments, manage paper references
- 🎓 **Scholar Growth**: Independent Scholar Program (ISP) with milestones, skill trees, and self-reflection
- 🤖 **Agent-Powered**: Built on [claw-code](https://github.com/ultraworkers/claw-code) for LLM-assisted planning, review, and analysis
- 📄 **Plain-Text State**: All data in YAML/JSON — Git-friendly, human-readable, version-controlled

## Architecture

```
Frontend CLI Layer     ← Typer + Rich (beautiful terminal UI)
Orchestration Layer    ← sci Core (state management, prompt building, tool registry)
Agent Engine Layer     ← claw-code (LLM reasoning, tool calling)
Persistence Layer      ← .gitscholar/ (local) + ~/.gitscholar/ (global)
```

## Quick Start

### Installation

```bash
pip install gitscholar
```

### Initialize a Project

```bash
cd your-research-repo
sci init
```

### Daily Workflow

```bash
# View and manage your backlog
sci backlog list
sci backlog add --title "Implement decoder" --priority high --points 8

# Sprint management
sci sprint start --goal "Build core decoder"
sci sprint status

# Kanban board
sci board
sci board move PBI-001 "In Progress"

# Daily standup
sci daily

# Research tracking
sci hypothesis add --statement "MWPM achieves sub-threshold error rates"
sci hypothesis list

# Scholar dashboard
sci scholar
sci scholar milestones
sci scholar skills
```

## Commands

| Command | Description |
|---------|-------------|
| `sci init` | Initialize `.gitscholar/` in current repo |
| `sci config show` | Show project or global configuration |
| `sci backlog list/add` | Manage the product backlog |
| `sci sprint start/status/end` | Sprint lifecycle management |
| `sci board` | Display the Kanban board |
| `sci board move <item> <col>` | Move items on the board |
| `sci daily` | Record daily standup |
| `sci hypothesis list/add/status` | Track research hypotheses |
| `sci scholar` | Scholar profile and ISP dashboard |
| `sci scholar milestones/skills` | ISP progress tracking |
| `sci version` | Show CLI version |

## Data Storage

### Local (per-project): `.gitscholar/`

- `config.yaml` — Project configuration and Scrum settings
- `backlog/` — Product and sprint backlogs
- `sprints/` — Sprint metadata and archive
- `board/` — Kanban board state
- `research/` — Hypotheses, experiments, papers
- `dailies/` — Daily standup records

### Global (per-scholar): `~/.gitscholar/`

- `profile.yaml` — Scholar identity and ISP level
- `isp/` — Milestones, skills, reflections
- `contributions/` — Cross-project contribution log
- `settings.yaml` — Global CLI preferences

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Documentation

See [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) for the full system design document.

## License

MIT
