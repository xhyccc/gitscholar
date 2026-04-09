"""CLI and unit tests for the paper management commands."""

from __future__ import annotations

import os
import textwrap
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from sci.cli.main import app
from sci.cli.paper import _fetch_arxiv, _fetch_doi, _next_paper_id
from sci.models.local import PaperReference
from sci.persistence.state import StateManager


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def init_dir(tmp_path: Path) -> Path:
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


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------

class TestNextPaperId:
    def test_empty(self) -> None:
        assert _next_paper_id([]) == "PAP-001"

    def test_sequential(self) -> None:
        assert _next_paper_id(["PAP-001", "PAP-002"]) == "PAP-003"

    def test_gap(self) -> None:
        assert _next_paper_id(["PAP-005"]) == "PAP-006"


_ARXIV_ATOM = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Quantum Error Correction via MWPM</title>
        <author><name>Alice Smith</name></author>
        <author><name>Bob Jones</name></author>
        <summary>This paper describes MWPM decoding for surface codes.</summary>
      </entry>
    </feed>
""").encode()

_CROSSREF_JSON = b"""{
  "message": {
    "title": ["A DOI Paper"],
    "author": [
      {"given": "Charlie", "family": "Brown"},
      {"given": "Dana", "family": "White"}
    ]
  }
}"""


class TestFetchArxiv:
    def test_parses_metadata(self) -> None:
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.read.return_value = _ARXIV_ATOM
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _fetch_arxiv("2301.01234")

        assert result is not None
        assert result["title"] == "Quantum Error Correction via MWPM"
        assert "Alice Smith" in result["authors"]
        assert result["ref"] == "arxiv:2301.01234"

    def test_strips_arxiv_prefix(self) -> None:
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.read.return_value = _ARXIV_ATOM
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _fetch_arxiv("arxiv:2301.01234")

        assert result is not None
        assert result["ref"] == "arxiv:2301.01234"

    def test_returns_none_on_network_error(self) -> None:
        import urllib.error

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
            result = _fetch_arxiv("2301.01234")
        assert result is None

    def test_returns_none_on_empty_feed(self) -> None:
        from unittest.mock import MagicMock

        empty_feed = b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        mock_resp = MagicMock()
        mock_resp.read.return_value = empty_feed
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _fetch_arxiv("0000.00000")
        assert result is None


class TestFetchDOI:
    def test_parses_metadata(self) -> None:
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.read.return_value = _CROSSREF_JSON
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _fetch_doi("10.1000/xyz")

        assert result is not None
        assert result["title"] == "A DOI Paper"
        assert "Charlie Brown" in result["authors"]
        assert result["ref"] == "doi:10.1000/xyz"

    def test_strips_doi_prefix(self) -> None:
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.read.return_value = _CROSSREF_JSON
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _fetch_doi("doi:10.1000/xyz")

        assert result is not None
        assert result["ref"] == "doi:10.1000/xyz"

    def test_returns_none_on_network_error(self) -> None:
        import urllib.error

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
            result = _fetch_doi("10.1000/xyz")
        assert result is None


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

class TestPaperList:
    def test_list_empty(self, runner: CliRunner, init_dir: Path) -> None:
        with _chdir(init_dir):
            result = runner.invoke(app, ["paper", "list"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "No papers" in result.output

    def test_list_with_paper(self, runner: CliRunner, init_dir: Path) -> None:
        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"
        library = state.load_papers()
        library.papers.append(
            PaperReference(
                id="PAP-001",
                title="Surface Code Paper",
                authors=["Alice", "Bob"],
                ref="arxiv:2301.01234",
                added_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        state.save_papers(library)

        with _chdir(init_dir):
            result = runner.invoke(app, ["paper", "list"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "PAP-001" in result.output
        assert "Surface Code Paper" in result.output


class TestPaperAdd:
    def test_add_paper_manually(self, runner: CliRunner, init_dir: Path) -> None:
        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"

        with _chdir(init_dir):
            result = runner.invoke(
                app,
                [
                    "paper", "add",
                    "--title", "My Paper",
                    "--ref", "arxiv:1234.56789",
                    "--authors", "Alice, Bob",
                    "--tags", "quantum,error-correction",
                ],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "PAP-001" in result.output

        library = state.load_papers()
        paper = library.papers[0]
        assert paper.title == "My Paper"
        assert paper.ref == "arxiv:1234.56789"
        assert "Alice" in paper.authors
        assert "quantum" in paper.tags


class TestPaperFetch:
    def test_fetch_arxiv(self, runner: CliRunner, init_dir: Path) -> None:
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.read.return_value = _ARXIV_ATOM
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        state = StateManager(repo_root=init_dir)
        state._global_dir = init_dir / "global"

        with _chdir(init_dir), patch("urllib.request.urlopen", return_value=mock_resp):
            result = runner.invoke(
                app, ["paper", "fetch", "2301.01234"], catch_exceptions=False
            )
        assert result.exit_code == 0
        assert "PAP-001" in result.output or "fetched" in result.output.lower()

        library = state.load_papers()
        assert len(library.papers) == 1
        assert "MWPM" in library.papers[0].title

    def test_fetch_fails_gracefully(self, runner: CliRunner, init_dir: Path) -> None:
        import urllib.error

        with (
            _chdir(init_dir),
            patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")),
        ):
            result = runner.invoke(app, ["paper", "fetch", "9999.99999"])
        assert result.exit_code != 0
