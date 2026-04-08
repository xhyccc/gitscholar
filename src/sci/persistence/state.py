"""State manager for reading and writing .gitscholar/ and ~/.gitscholar/ state files."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel
from ruamel.yaml import YAML

from sci.models.local import (
    DailyLog,
    ExperimentLog,
    HypothesesTracker,
    KanbanBoard,
    PaperLibrary,
    ProductBacklog,
    ProjectConfig,
    Retrospective,
    Sprint,
    SprintBacklog,
)
from sci.models.scholar import (
    ContributionLog,
    GlobalSettings,
    MilestoneTracker,
    ScholarProfile,
    SkillTree,
)

T = TypeVar("T", bound=BaseModel)

LOCAL_DIR = ".gitscholar"
GLOBAL_DIR = Path.home() / ".gitscholar"

yaml = YAML()
yaml.default_flow_style = False


def _ensure_dir(path: Path) -> None:
    """Ensure that a directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def _read_yaml(path: Path) -> dict:
    """Read a YAML file and return a dict. Returns empty dict if file doesn't exist."""
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.load(f)
    return data if data is not None else {}


def _write_yaml(path: Path, data: dict) -> None:
    """Write a dict to a YAML file."""
    _ensure_dir(path.parent)
    with open(path, "w") as f:
        yaml.dump(data, f)


def _load_model(path: Path, model_class: type[T]) -> T:
    """Load a Pydantic model from a YAML file."""
    data = _read_yaml(path)
    return model_class.model_validate(data) if data else model_class.model_validate({})


def _save_model(path: Path, model: BaseModel) -> None:
    """Save a Pydantic model to a YAML file."""
    data = model.model_dump(mode="json")
    _write_yaml(path, data)


class StateManager:
    """Manages reading and writing of all .gitscholar/ and ~/.gitscholar/ state."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self._repo_root = repo_root or Path.cwd()
        self._local_dir = self._repo_root / LOCAL_DIR
        self._global_dir = GLOBAL_DIR

    @property
    def local_dir(self) -> Path:
        return self._local_dir

    @property
    def global_dir(self) -> Path:
        return self._global_dir

    @property
    def is_initialized(self) -> bool:
        """Check if the local .gitscholar/ directory has been initialized."""
        return (self._local_dir / "config.yaml").exists()

    # --- Initialization ---

    def init_local(self, config: ProjectConfig) -> None:
        """Initialize the local .gitscholar/ directory with a project config."""
        _ensure_dir(self._local_dir / "backlog")
        _ensure_dir(self._local_dir / "sprints" / "archive")
        _ensure_dir(self._local_dir / "board")
        _ensure_dir(self._local_dir / "retrospectives")
        _ensure_dir(self._local_dir / "research")
        _ensure_dir(self._local_dir / "dailies")
        self.save_config(config)
        self.save_backlog(ProductBacklog())
        self.save_board(KanbanBoard())
        self.save_hypotheses(HypothesesTracker())
        self.save_experiments(ExperimentLog())
        self.save_papers(PaperLibrary())

    def init_global(self, profile: ScholarProfile) -> None:
        """Initialize the global ~/.gitscholar/ directory with a scholar profile."""
        _ensure_dir(self._global_dir / "isp" / "reflections")
        _ensure_dir(self._global_dir / "contributions")
        self.save_scholar_profile(profile)
        self.save_global_settings(GlobalSettings())
        self.save_milestones(MilestoneTracker())
        self.save_skills(SkillTree())
        self.save_contributions(ContributionLog())

    # --- Local State: Read ---

    def load_config(self) -> ProjectConfig:
        return _load_model(self._local_dir / "config.yaml", ProjectConfig)

    def load_backlog(self) -> ProductBacklog:
        return _load_model(self._local_dir / "backlog" / "product_backlog.yaml", ProductBacklog)

    def load_sprint_backlog(self) -> SprintBacklog:
        return _load_model(self._local_dir / "backlog" / "sprint_backlog.yaml", SprintBacklog)

    def load_current_sprint(self) -> Sprint:
        return _load_model(self._local_dir / "sprints" / "current.yaml", Sprint)

    def load_board(self) -> KanbanBoard:
        return _load_model(self._local_dir / "board" / "kanban.yaml", KanbanBoard)

    def load_hypotheses(self) -> HypothesesTracker:
        return _load_model(self._local_dir / "research" / "hypotheses.yaml", HypothesesTracker)

    def load_experiments(self) -> ExperimentLog:
        return _load_model(self._local_dir / "research" / "experiments.yaml", ExperimentLog)

    def load_papers(self) -> PaperLibrary:
        return _load_model(self._local_dir / "research" / "papers.yaml", PaperLibrary)

    def load_daily(self, date: str) -> DailyLog:
        return _load_model(self._local_dir / "dailies" / f"{date}.yaml", DailyLog)

    def load_retrospective(self, sprint_id: str) -> Retrospective:
        return _load_model(
            self._local_dir / "retrospectives" / f"{sprint_id}.yaml", Retrospective
        )

    # --- Local State: Write ---

    def save_config(self, config: ProjectConfig) -> None:
        _save_model(self._local_dir / "config.yaml", config)

    def save_backlog(self, backlog: ProductBacklog) -> None:
        _save_model(self._local_dir / "backlog" / "product_backlog.yaml", backlog)

    def save_sprint_backlog(self, sprint_backlog: SprintBacklog) -> None:
        _save_model(self._local_dir / "backlog" / "sprint_backlog.yaml", sprint_backlog)

    def save_current_sprint(self, sprint: Sprint) -> None:
        _save_model(self._local_dir / "sprints" / "current.yaml", sprint)

    def save_board(self, board: KanbanBoard) -> None:
        _save_model(self._local_dir / "board" / "kanban.yaml", board)

    def save_hypotheses(self, tracker: HypothesesTracker) -> None:
        _save_model(self._local_dir / "research" / "hypotheses.yaml", tracker)

    def save_experiments(self, log: ExperimentLog) -> None:
        _save_model(self._local_dir / "research" / "experiments.yaml", log)

    def save_papers(self, library: PaperLibrary) -> None:
        _save_model(self._local_dir / "research" / "papers.yaml", library)

    def save_daily(self, date: str, log: DailyLog) -> None:
        _save_model(self._local_dir / "dailies" / f"{date}.yaml", log)

    def save_retrospective(self, retro: Retrospective) -> None:
        _save_model(
            self._local_dir / "retrospectives" / f"{retro.sprint_id}.yaml", retro
        )

    def archive_sprint(self, sprint: Sprint) -> None:
        """Archive a completed sprint."""
        _save_model(self._local_dir / "sprints" / "archive" / f"{sprint.id}.yaml", sprint)

    # --- Global State: Read ---

    def load_scholar_profile(self) -> ScholarProfile:
        return _load_model(self._global_dir / "profile.yaml", ScholarProfile)

    def load_global_settings(self) -> GlobalSettings:
        return _load_model(self._global_dir / "settings.yaml", GlobalSettings)

    def load_milestones(self) -> MilestoneTracker:
        return _load_model(self._global_dir / "isp" / "milestones.yaml", MilestoneTracker)

    def load_skills(self) -> SkillTree:
        return _load_model(self._global_dir / "isp" / "skills.yaml", SkillTree)

    def load_contributions(self) -> ContributionLog:
        return _load_model(self._global_dir / "contributions" / "log.yaml", ContributionLog)

    # --- Global State: Write ---

    def save_scholar_profile(self, profile: ScholarProfile) -> None:
        _save_model(self._global_dir / "profile.yaml", profile)

    def save_global_settings(self, settings: GlobalSettings) -> None:
        _save_model(self._global_dir / "settings.yaml", settings)

    def save_milestones(self, tracker: MilestoneTracker) -> None:
        _save_model(self._global_dir / "isp" / "milestones.yaml", tracker)

    def save_skills(self, skills: SkillTree) -> None:
        _save_model(self._global_dir / "isp" / "skills.yaml", skills)

    def save_contributions(self, log: ContributionLog) -> None:
        _save_model(self._global_dir / "contributions" / "log.yaml", log)
