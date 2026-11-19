# agent-cad-skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platforms](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)](#requirements)

**An agent skill that turns any coding agent into a careful parametric CAD designer.**
Works with Claude Code, Cursor, Zed, Codex, GitHub Copilot, Antigravity, Aider and other agents that can read files and run shell commands.

Ask for a part — *"design a wall-mountable case for a Raspberry Pi 5"* — and the agent clarifies requirements, looks up real dimensions, writes a single parametric Python model, builds STEP/STL/DXF, and verifies the result automatically before calling it done.
The agent talks to you in the language you write in.

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Verification](#verification)
- [Project structure](#project-structure)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Features

One workflow for every CAD job — parts, enclosures, brackets, fixtures, reverse-engineering from measurements, laser/CNC profiles and 3D-printed parts:

1. **Clarify** — asks option-based questions until every critical requirement is clear, writes `requirements.md` and waits for your approval.
2. **Research** — takes off-the-shelf part dimensions (Raspberry Pi, displays, motors, bearings, screws…) from official drawings or STEP files, never from memory, and records the sources.
3. **Model** — one parametric `model.py`; every dimension is a named parameter, the model is rebuilt from scratch on every change.
4. **Build & verify** — exports STEP, STL (in print orientation) and DXF, then checks solid validity, watertight meshes, print-bed fit, support-free printing (bridges vs. overhangs), collisions and clearances against real part models, and your own requirements.
5. **Report** — renders preview images, writes `output/report.md`, and can export a FreeCAD `.FCStd` document.

## Requirements

- `git`
- Python **3.10+** (3.12 recommended — the tested environment)
- ~500 MB disk space for the CAD environment
- [uv](https://docs.astral.sh/uv/) *(optional)* — makes environment setup much faster
- [FreeCAD](https://www.freecad.org/) *(optional)* — only for `.FCStd` export
- **Linux only:** the OpenGL runtime. Desktop systems usually have it; on minimal or server images install it first:

  ```bash
  sudo apt-get install -y libgl1 libegl1   # Debian / Ubuntu
  ```

  `libegl1` lets preview images render on machines without a display. Without it the build still works, but images are skipped.

## Quick start

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/acikyol/agent-cad-skill/main/install.sh | bash
```

Windows (PowerShell):

```powershell
irm https://raw.githubusercontent.com/acikyol/agent-cad-skill/main/install.ps1 | iex
```

Then open your agent and ask for a part. The CAD environment is created automatically the first time it is needed.

> [!TIP]
> Prefer to read scripts before piping them into a shell? Use the [manual install](#manual-install) below.

## Installation

### Global (once per machine)

The installer clones the skill into `~/.agent-cad-skill` and registers it with agents that have a global config:

| Agent | Where |
|---|---|
| Claude Code | `~/.claude/skills/agent-cad-skill` (symlink) |
| Codex | `~/.codex/AGENTS.md` (pointer block) |
| Antigravity CLI (`agy`) and App | `~/.gemini/config/skills/agent-cad-skill` (symlink) |
| Cursor, Zed, Copilot | No global rules file — install per project, or paste the text the installer prints into the agent's user rules |

#### Manual install

```bash
git clone https://github.com/acikyol/agent-cad-skill.git ~/.agent-cad-skill
python ~/.agent-cad-skill/install.py --global
```

### Per project

```bash
python ~/.agent-cad-skill/install.py --project /path/to/project            # point at the global install
python ~/.agent-cad-skill/install.py --project /path/to/project --vendor   # copy the skill into the repo
```

Or in one line, without a global install:

```bash
curl -fsSL https://raw.githubusercontent.com/acikyol/agent-cad-skill/main/install.sh | bash -s -- --project /path/to/project --vendor
```

| Agent | Project file |
|---|---|
| Claude Code | `.claude/skills/agent-cad-skill` |
| Cursor | `.cursor/rules/agent-cad-skill.mdc` |
| Zed | `.rules` |
| Codex, Aider, Jules, … | `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Antigravity CLI (`agy`) and App | `.agents/skills/agent-cad-skill` (discovered natively) |

`--vendor` copies the skill to `<project>/.agents/skills/agent-cad-skill` with relative paths, so everyone who clones the project gets it. Its `.venv/` and `output/` are added to `.gitignore`.

### Installer options

| Option | Meaning |
|---|---|
| `--agents claude,cursor,…` | Limit to some agents (default: all) |
| `--with-env` | Create the shared CAD environment now (`<skill>/.venv`); otherwise the agent creates it on first use |
| `--check` | Run the self-tests (needs the environment) |
| `--uninstall` | Remove pointer blocks / links (and the vendored copy for `--project`) |
| `--global --uninstall --purge` | Also delete `~/.agent-cad-skill` |

Running the installer again is safe: blocks are updated in place and your own content in those files is kept.

Environment variables: `AGENT_CAD_SKILL_REPO` (clone URL) and `AGENT_CAD_SKILL_HOME` (install directory) override the defaults of `install.sh` / `install.ps1`.

### Update

Run the one-line installer again (it does `git pull`), or:

```bash
git -C ~/.agent-cad-skill pull
```

Vendored copies: rerun `install.py --project <dir> --vendor`.

### Uninstall

```bash
python ~/.agent-cad-skill/install.py --global --uninstall --purge
```

## Usage

Ask your agent in plain language, for example:

- *"Design a wall-mountable case for a Raspberry Pi 5"*
- *"I measured this bracket with calipers, model it"*
- *"Make this part printable without supports"*
- *"This plate will be laser cut, give me a DXF"*

The agent reads `SKILL.md` and walks through the workflow above.

### Running a build yourself

```bash
~/.agent-cad-skill/.venv/bin/python ~/.agent-cad-skill/.agents/skills/agent-cad-skill/scripts/build.py path/to/model.py
```

| Option | Meaning |
|---|---|
| `--out DIR` | Output directory (default: `output/` next to the model) |
| `--no-render` | Skip preview images (visual check stays *NOT_VERIFIED*) |
| `--render-timeout SEC` | Time limit for the isolated renderer (default: 60) |

Outputs: `step/`, `stl/`, `dxf/`, `render/`, `report.md`, `report.json`, `manifest.json`.

| Exit code | Meaning |
|---|---|
| `0` | All executed numeric checks passed (not a full design approval) |
| `1` | Numeric failure or an unverified collision |
| `2` | Model or command line could not be loaded |

### Model contract

A model is a plain Python file. Start from [`model_template.py`](.agents/skills/agent-cad-skill/assets/model_template.py):

```python
P = dict(w=40.0, t=4.0, hole_d=4.4, bed=(235, 235))   # every dimension is a parameter

def parts(P):          # parts to build, with print orientation and process
    return [dict(name="Bracket", shape=bracket(P), process="fdm", print_rot=[("Y", -90)])]

def references(P):     # optional: real off-the-shelf parts for collision checks
    return []

def checks(P, S):      # your requirements as automatic checks
    return [("R2", P["t"] >= 3.0, f"thickness {P['t']} >= 3.0")]

CLEARANCES = []        # [("Lid", "Box", 0.3)] — minimum gaps in mm
```

## Examples

| Example | What it shows | Expected result |
|---|---|---|
| [`examples/bracket`](examples/bracket/model.py) | Simple L bracket | Passes |
| [`examples/iskele`](examples/iskele/README.md) | Desk organizer with requirements, sources and an acceptance test | Passes |
| [`examples/collisions`](examples/collisions/model.py) | Assembly with a collision and a too-small clearance | **Fails on purpose** |
| [`examples/bridges`](examples/bridges/model.py) | Bridges and overhangs that need supports | **Fails on purpose** |

## Verification

Reports use three states: **PASS**, **FAIL** and **NOT_VERIFIED**. The tool never declares a design fully verified on its own — numeric checks can pass, but visual review and real-world validation remain your call. Strength, tolerances and requirements not written as `checks()` are outside the automatic proof.

See [docs/verification.md](docs/verification.md) for the exact semantics, limits and how to reproduce the tested environment.

> [!WARNING]
> `model.py` files are executed as regular Python. Only build models you trust. See [SECURITY.md](SECURITY.md).

## Project structure

```text
.agents/skills/agent-cad-skill/
├── SKILL.md                 # Main instructions — what the agent reads
├── references/              # Clarification, part research, FDM, laser/CNC, measurements, assemblies, FreeCAD
├── scripts/
│   ├── build.py             # Build + verify + render + report
│   ├── setup_env.py         # Creates the pinned Python CAD environment
│   ├── render_worker.py     # Isolated preview renderer
│   └── to_freecad.py        # Optional FreeCAD export
├── assets/model_template.py # Starter model
└── requirements.lock        # Pinned, tested dependency versions
docs/                        # Detailed guides
examples/                    # Example models (two fail on purpose)
tests/                       # Self-tests and regression tests
install.py / install.sh / install.ps1
```

## Documentation

- [Verification semantics](docs/verification.md)
- [Changelog](CHANGELOG.md)

## Contributing

Contributions are welcome — bug reports, new reference notes, example models and fixes. Please read [CONTRIBUTING.md](CONTRIBUTING.md) first. This project follows a [Code of Conduct](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE)
