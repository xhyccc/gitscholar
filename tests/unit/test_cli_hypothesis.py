"""CLI tests for the hypothesis commands."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sci.cli.main import app
from sci.models.local import Evidence, EvidenceOutcome, Hypothesis, HypothesisStatus
from sci.persistence.state import StateManager


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def init_dir(tmp_path: Path) -> Path:
    """Return a temp directory with a fully initialised GitScholar project."""
    state = StateManager(repo_root=tmp_path)
    state._global_dir = tmp_path / "global"

    from sci.models.local import ProjectConfig, ProjectInfo
    from sci.models.scholar import ScholarIdentity, ScholarProfile

    config = ProjectConfig(
        project=ProjectInfo(
            name="test-project",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    state.init_local(config)
    profile = ScholarProfile(
        scholar=ScholarIdentity(
            name="Test Scholar",
            joined_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    state.init_global(profile)
    return tmp_path


def _chdir(path: Path):
    """Context manager that changes cwd and restores it."""
    import contextlib

    @contextlib.contextmanager
    def _cm():
        old = os.getcwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(old)

    return _cm()


class TestHypothesisList:
    def test_list_empty(self, runner: CliRunner, init_dir: Path) -> None:
        with _chdir(init_dir):
            result = runner.invoke(app, ["hypothesis", "list"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "No hypotheses" in result.output

    def test_list_with_hypotheses(self, runner: CliRunner, init_dir: Path) -> None:
        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"
        tracker = state.load_hypotheses()
        tracker.hypotheses.append(
            Hypothesis(
                id="HYP-001",
                statement="MWPM achieves sub-threshold error rates",
                status=HypothesisStatus.TESTING,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        state.save_hypotheses(tracker)

        with _chdir(init_dir):
            result = runner.invoke(app, ["hypothesis", "list"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "HYP-001" in result.output
        assert "MWPM" in result.output
        assert "testing" in result.output

    def test_list_not_initialized(self, runner: CliRunner, tmp_path: Path) -> None:
        with _chdir(tmp_path):
            result = runner.invoke(app, ["hypothesis", "list"])
        assert result.exit_code != 0


class TestHypothesisAdd:
    def test_add_hypothesis(self, runner: CliRunner, init_dir: Path) -> None:
        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"

        with _chdir(init_dir):
            result = runner.invoke(
                app,
                ["hypothesis", "add", "--statement", "Noise is below threshold"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "HYP-001" in result.output
        assert "Proposed" in result.output or "Noise is below threshold" in result.output

        tracker = state.load_hypotheses()
        assert len(tracker.hypotheses) == 1
        assert tracker.hypotheses[0].id == "HYP-001"
        assert tracker.hypotheses[0].status == HypothesisStatus.PROPOSED

    def test_add_increments_id(self, runner: CliRunner, init_dir: Path) -> None:
        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"
        tracker = state.load_hypotheses()
        tracker.hypotheses.append(
            Hypothesis(
                id="HYP-003",
                statement="Existing",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        state.save_hypotheses(tracker)

        with _chdir(init_dir):
            result = runner.invoke(
                app,
                ["hypothesis", "add", "--statement", "New hypothesis"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        tracker2 = state.load_hypotheses()
        assert tracker2.hypotheses[-1].id == "HYP-004"


class TestHypothesisStatus:
    def test_show_status(self, runner: CliRunner, init_dir: Path) -> None:
        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"
        tracker = state.load_hypotheses()
        tracker.hypotheses.append(
            Hypothesis(
                id="HYP-001",
                statement="Test statement",
                status=HypothesisStatus.SUPPORTED,
                evidence=[
                    Evidence(
                        type="experiment",
                        ref="EXP-001",
                        outcome=EvidenceOutcome.SUPPORT,
                        notes="Confirmed!",
                    )
                ],
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        state.save_hypotheses(tracker)

        with _chdir(init_dir):
            result = runner.invoke(
                app, ["hypothesis", "status", "HYP-001"], catch_exceptions=False
            )
        assert result.exit_code == 0
        assert "HYP-001" in result.output
        assert "Test statement" in result.output
        assert "supported" in result.output

    def test_status_not_found(self, runner: CliRunner, init_dir: Path) -> None:
        with _chdir(init_dir):
            result = runner.invoke(app, ["hypothesis", "status", "HYP-999"])
        assert result.exit_code != 0
