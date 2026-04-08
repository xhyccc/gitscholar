#!/usr/bin/env bash
#
# install.sh — Build and install GitScholar from source on macOS / Linux.
#
# Usage:
#   ./install.sh              # install in normal (site-packages) mode
#   ./install.sh --dev        # install in editable mode with dev dependencies
#   ./install.sh --uninstall  # remove the package
#
set -euo pipefail

# ── Helpers ──────────────────────────────────────────────────────────────────

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
RESET='\033[0m'

info()  { printf "${BOLD}${GREEN}[INFO]${RESET}  %s\n" "$*"; }
warn()  { printf "${BOLD}${YELLOW}[WARN]${RESET}  %s\n" "$*"; }
error() { printf "${BOLD}${RED}[ERROR]${RESET} %s\n" "$*" >&2; }
die()   { error "$@"; exit 1; }

# ── Locate repository root (directory containing this script) ────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f pyproject.toml ]]; then
    die "pyproject.toml not found in $SCRIPT_DIR — run this script from the repo root."
fi

# ── Detect Python ────────────────────────────────────────────────────────────

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [[ -z "$PYTHON" ]]; then
    die "Python not found. Please install Python 3.11 or later."
fi

PYTHON_VERSION="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PYTHON_MAJOR="$("$PYTHON" -c 'import sys; print(sys.version_info.major)')"
PYTHON_MINOR="$("$PYTHON" -c 'import sys; print(sys.version_info.minor)')"

if (( PYTHON_MAJOR < 3 )) || (( PYTHON_MAJOR == 3 && PYTHON_MINOR < 11 )); then
    die "Python >= 3.11 is required (found $PYTHON_VERSION). Please upgrade."
fi

info "Using $PYTHON ($PYTHON_VERSION)"

# ── Ensure pip is available ──────────────────────────────────────────────────

if ! "$PYTHON" -m pip --version &>/dev/null; then
    die "pip is not installed for $PYTHON. Please install pip first."
fi

# ── Parse arguments ──────────────────────────────────────────────────────────

MODE="install"  # install | dev | uninstall
for arg in "$@"; do
    case "$arg" in
        --dev)       MODE="dev" ;;
        --uninstall) MODE="uninstall" ;;
        -h|--help)
            echo "Usage: ./install.sh [--dev | --uninstall | --help]"
            echo ""
            echo "  (no flag)    Install gitscholar from source"
            echo "  --dev        Install in editable mode with dev dependencies"
            echo "  --uninstall  Uninstall gitscholar"
            exit 0
            ;;
        *)
            die "Unknown option: $arg (try --help)"
            ;;
    esac
done

# ── Execute ──────────────────────────────────────────────────────────────────

case "$MODE" in
    install)
        info "Installing gitscholar …"
        "$PYTHON" -m pip install .
        ;;
    dev)
        info "Installing gitscholar in editable (dev) mode …"
        "$PYTHON" -m pip install -e ".[dev]"
        ;;
    uninstall)
        info "Uninstalling gitscholar …"
        "$PYTHON" -m pip uninstall -y gitscholar
        info "Done."
        exit 0
        ;;
esac

# ── Verify ───────────────────────────────────────────────────────────────────

if command -v sci &>/dev/null; then
    info "Success! GitScholar installed:"
    sci version
else
    warn "The 'sci' command was not found on PATH."
    warn "You may need to add the pip scripts directory to your PATH."
    warn "If you installed with --user: export PATH=\"\$($PYTHON -m site --user-base)/bin:\$PATH\""
    warn "If you are in a virtualenv:    export PATH=\"\$(dirname \$($PYTHON -c 'import sys; print(sys.executable)'))/:\$PATH\""
fi
