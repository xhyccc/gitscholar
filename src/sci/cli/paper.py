"""sci paper — Paper reference management with arXiv/DOI auto-fetch."""

from __future__ import annotations

import contextlib
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import typer
from rich.panel import Panel
from rich.table import Table

from sci.cli.utils import console, err_console, get_state_manager, require_init
from sci.models.local import PaperReference

app = typer.Typer(no_args_is_help=True)

# XML namespace used by the arXiv Atom feed
_ATOM_NS = "http://www.w3.org/2005/Atom"
_ARXIV_API = "https://export.arxiv.org/api/query?id_list={arxiv_id}"
_CROSSREF_API = "https://api.crossref.org/works/{doi}"


def _next_paper_id(existing_ids: list[str]) -> str:
    """Generate the next paper ID."""
    max_num = 0
    for pid in existing_ids:
        parts = pid.split("-")
        if len(parts) == 2:
            with contextlib.suppress(ValueError):
                max_num = max(max_num, int(parts[1]))
    return f"PAP-{max_num + 1:03d}"


def _fetch_arxiv(arxiv_id: str) -> dict[str, str | list[str]] | None:
    """Fetch paper metadata from the arXiv API.

    Returns a dict with keys: title, authors, ref, notes or None on failure.
    """
    # Normalise: strip leading "arxiv:" prefix if present
    clean_id = arxiv_id.lower().removeprefix("arxiv:")
    url = _ARXIV_API.format(arxiv_id=urllib.parse.quote(clean_id))
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read()
    except (urllib.error.URLError, OSError):
        return None

    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None

    entry = root.find(f"{{{_ATOM_NS}}}entry")
    if entry is None:
        return None

    title_el = entry.find(f"{{{_ATOM_NS}}}title")
    title = (
        title_el.text.strip().replace("\n", " ")
        if title_el is not None and title_el.text
        else ""
    )

    authors: list[str] = []
    for author_el in entry.findall(f"{{{_ATOM_NS}}}author"):
        name_el = author_el.find(f"{{{_ATOM_NS}}}name")
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    summary_el = entry.find(f"{{{_ATOM_NS}}}summary")
    notes = summary_el.text.strip()[:200] if summary_el is not None and summary_el.text else ""

    return {
        "title": title,
        "authors": authors,
        "ref": f"arxiv:{clean_id}",
        "notes": notes,
    }


def _fetch_doi(doi: str) -> dict[str, str | list[str]] | None:
    """Fetch paper metadata from the Crossref API.

    Returns a dict with keys: title, authors, ref, notes or None on failure.
    """
    clean_doi = doi.lower().removeprefix("doi:")
    url = _CROSSREF_API.format(doi=urllib.parse.quote(clean_doi, safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": "gitscholar-sci/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None

    work = data.get("message", {})
    title_list = work.get("title") or []
    title = title_list[0] if title_list else ""

    authors: list[str] = []
    for author in work.get("author", []):
        given = author.get("given", "")
        family = author.get("family", "")
        full = f"{given} {family}".strip()
        if full:
            authors.append(full)

    return {
        "title": title,
        "authors": authors,
        "ref": f"doi:{clean_doi}",
        "notes": "",
    }


@app.command("list")
def list_papers() -> None:
    """List all paper references."""
    state = get_state_manager()
    require_init(state)

    library = state.load_papers()

    if not library.papers:
        console.print(
            "[dim]No papers yet. Run [bold]sci paper add[/bold] or "
            "[bold]sci paper fetch[/bold] to add one.[/dim]"
        )
        return

    table = Table(title="Paper Library", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Authors", style="blue")
    table.add_column("Ref", style="green")
    table.add_column("Tags")

    for paper in library.papers:
        authors_str = ", ".join(paper.authors[:3])
        if len(paper.authors) > 3:
            authors_str += " et al."
        table.add_row(
            paper.id,
            paper.title,
            authors_str,
            paper.ref,
            ", ".join(paper.tags) or "-",
        )

    console.print(table)


@app.command("add")
def add_paper(
    title: str = typer.Option(..., "--title", "-t", prompt="Title"),
    ref: str = typer.Option(..., "--ref", "-r", prompt="arXiv ID / DOI / path"),
    authors: str = typer.Option("", "--authors", "-a", help="Comma-separated author names"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
    notes: str = typer.Option("", "--notes", "-n"),
) -> None:
    """Add a paper reference manually."""
    state = get_state_manager()
    require_init(state)

    library = state.load_papers()
    paper_id = _next_paper_id([p.id for p in library.papers])

    paper = PaperReference(
        id=paper_id,
        title=title,
        authors=[a.strip() for a in authors.split(",") if a.strip()],
        ref=ref,
        notes=notes,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        added_at=datetime.now(UTC),
    )

    library.papers.append(paper)
    state.save_papers(library)

    console.print(f"[bold green]✓[/bold green] Added [{paper_id}] {title}")


@app.command("fetch")
def fetch_paper(
    identifier: str = typer.Argument(
        help="arXiv ID (e.g. 2301.01234 or arxiv:2301.01234) or DOI (e.g. doi:10.1000/xyz)"
    ),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
) -> None:
    """Auto-fetch paper metadata from arXiv or DOI (Crossref)."""
    state = get_state_manager()
    require_init(state)

    console.print(f"[dim]Fetching metadata for [bold]{identifier}[/bold]...[/dim]")

    lower = identifier.lower()
    if lower.startswith("doi:") or lower.startswith("10."):
        metadata = _fetch_doi(identifier)
        source = "Crossref (DOI)"
    else:
        metadata = _fetch_arxiv(identifier)
        source = "arXiv"

    if metadata is None:
        err_console.print(
            f"[bold red]Error:[/bold red] Could not fetch metadata from {source}.\n"
            "Check the identifier and your internet connection, or use "
            "[bold]sci paper add[/bold] to add manually."
        )
        raise SystemExit(1)

    library = state.load_papers()
    paper_id = _next_paper_id([p.id for p in library.papers])

    paper = PaperReference(
        id=paper_id,
        title=str(metadata["title"]),
        authors=list(metadata["authors"]),
        ref=str(metadata["ref"]),
        notes=str(metadata["notes"]),
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        added_at=datetime.now(UTC),
    )

    library.papers.append(paper)
    state.save_papers(library)

    authors_display = ", ".join(paper.authors[:3])
    if len(paper.authors) > 3:
        authors_display += " et al."

    console.print(Panel.fit(
        f"[bold green]✓ {paper_id} fetched from {source}[/bold green]\n\n"
        f"[bold]{paper.title}[/bold]\n"
        f"[dim]{authors_display}[/dim]\n"
        f"Ref: {paper.ref}",
        border_style="green",
    ))
