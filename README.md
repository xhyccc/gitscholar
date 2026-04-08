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

## Configuration

GitScholar is **configurable** at two levels:

- **Global** (`~/.gitscholar/settings.yaml`) — LLM API credentials, git identity, CLI theme
- **Local** (`.gitscholar/config.yaml`) — per-project Scrum, agent, and research settings

By default the system uses your **system git config** and looks for API keys in **environment variables**, so zero configuration is needed to get started.

### Setting values

```bash
# Set LLM provider and API key (global)
sci config set agent.llm.provider openai --global
sci config set agent.llm.api_key sk-proj-abc123 --global
sci config set agent.llm.api_base https://api.openai.com/v1 --global
sci config set agent.llm.model gpt-4o --global

# Set git identity (overrides system git config)
sci config set git.user_name "Jane Doe" --global
sci config set git.user_email jane@university.edu --global
sci config set git.signing_key ABCDEF1234567890 --global

# Set per-project settings
sci config set scrum.sprint_duration_days 7
sci config set agent.engine claw-code
```

### Reading values

```bash
sci config show                # show project config
sci config show --global       # show global settings
sci config show --global -r    # show resolved settings (with env/git defaults applied)
sci config get agent.llm.model --global
sci config get git.user_email --global --resolved
```

### Environment variables

Sensitive values like API keys can be provided via environment variables instead of storing them in config files:

| Variable | Description |
|----------|-------------|
| `SCI_LLM_API_KEY` | LLM provider API key |
| `SCI_LLM_API_BASE` | LLM provider base URL |
| `SCI_LLM_MODEL` | Default model name |
| `SCI_LLM_PROVIDER` | Provider name (e.g. `openai`, `anthropic`) |
| `CLAW_API_KEY` | Legacy API key (fallback) |

### Example `~/.gitscholar/settings.yaml`

```yaml
cli:
  theme: dark
  language: en
  editor: vim
  pager: less
agent:
  default_model: claude-sonnet-4
  api_key_env: CLAW_API_KEY
  max_tokens: 4096
  temperature: 0.3
  llm:
    provider: openai
    api_key: ""            # prefer SCI_LLM_API_KEY env var
    api_base: https://api.openai.com/v1
    model: gpt-4o
git:
  user_name: Jane Doe
  user_email: jane@university.edu
  signing_key: ""
notifications:
  sprint_reminders: true
  daily_standup_prompt: "09:00"
  milestone_celebrations: true
```

> **Tip:** Run `sci config show --global --resolved` to see the effective configuration after merging environment variables and system git defaults.

## Commands

| Command | Description |
|---------|-------------|
| `sci init` | Initialize `.gitscholar/` in current repo |
| `sci config show` | Show project or global configuration |
| `sci config show --resolved` | Show resolved config with env/git defaults |
| `sci config set <key> <val>` | Set a config value (dot-notation) |
| `sci config get <key>` | Get a single config value |
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
