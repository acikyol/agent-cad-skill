#!/usr/bin/env bash
# One-line installer (macOS / Linux):
#   curl -fsSL https://raw.githubusercontent.com/acikyol/agent-cad-skill/main/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --project /path/to/project --vendor
# Clones or updates the skill in ~/.agent-cad-skill, then runs install.py with the given arguments
# (default: --global). Override with AGENT_CAD_SKILL_REPO / AGENT_CAD_SKILL_HOME.
set -euo pipefail
REPO="${AGENT_CAD_SKILL_REPO:-https://github.com/acikyol/agent-cad-skill.git}"
DEST="${AGENT_CAD_SKILL_HOME:-$HOME/.agent-cad-skill}"

command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }
PY="$(command -v python3 || command -v python || true)"
[ -n "$PY" ] || { echo "Python 3.10+ is required" >&2; exit 1; }

if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --ff-only -q
else
  git clone -q --depth 1 "$REPO" "$DEST"
fi

[ "$#" -gt 0 ] || set -- --global
exec "$PY" "$DEST/install.py" "$@"
