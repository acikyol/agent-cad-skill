---
name: agent-cad-skill
description: General CAD workflow — when designing or modifying any part, assembly, enclosure/case, bracket, fixture, adapter, mechanical part, reverse-engineered part from measurements, laser/CNC profile or 3D-printed part, first clarifies requirements with questions and researches off-the-shelf part dimensions (Raspberry Pi, displays, motors, bearings, screws…) from official sources; then writes a single parametric CadQuery model.py; exports STEP/STL/DXF; automatically verifies mesh, overhangs, print bed, collisions, clearances and the user's own requirements; renders images; optionally exports to FreeCAD (.FCStd). Use this skill whenever the user asks for a 3D model, CAD part, STL/STEP/DXF, "design/model/draw", "make a case/enclosure", "I measured with calipers", "CadQuery", "parametric", "print without supports", "laser cut", "does it collide in the assembly" — in any language.
---

# Parametric CAD workflow with CadQuery

**Language rule:** this skill is written in English, but **always talk to the user in the language they write in** — every question, option, summary and final answer. Keep code, file names and generated files in English.

This skill works in any coding agent (Claude Code, Cursor, Zed, Codex, Copilot, Antigravity…). Requirements: read/write files, run shell commands, Python 3.10+. Web search and image viewing are used when available; otherwise ask the user for help (see below).

**`<SKILL_DIR>`** = the folder containing this SKILL.md. All script paths are relative to it.

Goal: a model that is **right the first time**. Three pillars:
1. **Clarify** — every ambiguous critical point is asked before modeling.
2. **Sourced dimensions** — off-the-shelf part dimensions are never guessed; they come from official drawings/STEP.
3. **Proof** — every requirement is verified by an automatic check; nothing is "done" until the checks pass.

The design lives in **one Python script (`model.py`)** and is regenerated from scratch on every change. Why: incremental boolean edits in an open CAD session crash, lose outputs and mix up versions; a script gives the same result every time and can be tracked in git.

## Behaviour depending on agent capabilities

| Need | If the agent has it | Otherwise |
|---|---|---|
| Ask the user | Use the agent's question/choice tool | Write numbered questions with a/b/c options in a message and wait |
| Research off-the-shelf parts | Use web search/fetch | Ask the user for the official drawing/STEP link or file; else ask them to measure with calipers |
| Visual check | Open `output/render/*.png` as images | Ask the user to look; base your own check on the numeric report and say so |
| Long commands | Run in the foreground and read output directly | — (no background job + polling loops) |

## Which reference to read when

| Situation | Read |
|---|---|
| **Every new design / ambiguous request** | `references/clarify.md` (first) |
| Mates with an off-the-shelf part | `references/off_the_shelf_parts.md` |
| Assembly, real components, plugs/cables, stability | `references/assemblies.md` |
| FDM 3D printing | `references/fdm_printing.md` |
| Laser / CNC / sheet metal | `references/laser_cnc.md` |
| Modeling from caliper/photo measurements | `references/from_measurements.md` |
| User asked for FreeCAD output | `references/freecad.md` |

## Workflow

### A. Clarify (before modeling)
1. Work through the checklist in `references/clarify.md`; if the project has `requirements.md`, read it first.
2. **Ask about ambiguous critical items** (with options, max 4 per round, mark your recommendation) — in the user's language. One question is always **the desired outputs**: STL / STEP / DXF and optional **FreeCAD (.FCStd)**. Don't ask what research can answer; do ask which exact model/revision.
3. **Research off-the-shelf parts** (`references/off_the_shelf_parts.md`); ask permission before downloading; record sources in `sources.md`.
4. Write the `requirements.md` table (requirement · value · status · source · **verification method**), summarise it to the user in their language and **get approval**.

If the request is already precise (e.g. "make the wall 3 mm"), keep A short: update only the affected requirement.

### B. Model
5. **Environment (once per machine/install):** if this skill is checked out at `.agents/skills/agent-cad-skill` inside its own repository and a root `.venv` already exists, use that interpreter. Otherwise the shared environment is `<SKILL_DIR>/.venv`; its python is `<SKILL_DIR>/.venv/bin/python` (Windows: `<SKILL_DIR>\.venv\Scripts\python.exe`), called `PY` below. If it doesn't exist, create it: `python <SKILL_DIR>/scripts/setup_env.py` (~500 MB, a few minutes — tell the user before starting). Never create one per project.
6. Copy `<SKILL_DIR>/assets/model_template.py` to `<project>/model.py` and fill it in. In this repository the working examples are `examples/`, not inside the skill directory. All dimensions in `P`; source comment next to every off-the-shelf dimension; real models via `references()`.
7. Turn every measurable requirement into a check in `checks(P, S)`.

### C. Build, verify, show
8. `PY <SKILL_DIR>/scripts/build.py <project>/model.py` → `<project>/output/` (step, stl, dxf, render, report.md/json, manifest.json). Exit 0 means numeric checks only passed, 1 numeric failure/unverified collision, 2 model/CLI load failure. Read separate overall `status` and `verification`; never infer full verification from exit 0. Renderer crash/timeout preserves the numeric report and leaves visual verification NOT_VERIFIED.
9. Inspect only the current report's `images` list (not stale directory contents): flipped parts, missing/misoriented holes, ports facing the wrong way are not caught by numbers. No images means visual NOT_VERIFIED. Image generation alone is not inspection.
10. **Only if the user wants FreeCAD:** `PY <SKILL_DIR>/scripts/to_freecad.py <project>/output`. Skipped if FreeCAD is not installed; STEP opens in any CAD tool.
11. If the **verification gate** (`clarify.md` §4) passes, report to the user in their language: what changed, which parts must be re-made (manifest `changed`), requirement results, assumptions, "not verified" items; give the `output/report.md` path.

Change requests follow the same loop: update requirement → `model.py` → build → images → report (only what changed).

## model.py contract

```python
import cadquery as cq
P = dict(bed=(235, 235), overhang_deg=45, bridge_max=25, ...)   # all dimensions, mm

def references(P):            # optional: real parts / envelopes that are not manufactured
    return [dict(name="Pi5", shape=cq.importers.importStep("sources/pi5.step"))]

def parts(P):                 # required
    return [dict(
        name="Body", shape=...,        # cq.Workplane / Shape / Assembly — in ASSEMBLY position
        process="fdm",                 # "fdm" | "laser" | "cnc" | "none"
        print_rot=[("X", 180)],        # fdm: rotations from assembly to print orientation
        dxf=None,                      # laser/cnc: 2D profile in XY (cq.Workplane)
        qty=1, group="Body", color=(0.3, 0.3, 0.32),
        allow_overhang_mm2=0,
    )]

def checks(P, S):             # required when there are requirements; S: {name: cq.Shape} in assembly position
    bb = S["Body"].BoundingBox()
    return [("R4", bb.zlen <= 40, f"height {bb.zlen:.1f} <= 40")]

CLEARANCES = [("Pi5", "Body", 0.4)]       # (a, b, min mm)
IGNORE_CONTACT = []                       # legacy bypass marks pairs NOT_VERIFIED; face contact needs no bypass
```

Relative paths are resolved from the folder of `model.py`.

## Modeling habits

- Write the **coordinate system** first as a comment (origin, front/up directions); all parts share one assembly frame.
- Derive dimensions; never bury numbers in geometry. Dimensions tied to an off-the-shelf part come from its sourced parameters.
- Main body → subtractive features → additive features → chamfers/fillets last; each step in its own variable.
- Rigid moves: `translate/rotate/moved`; avoid general matrix transforms that turn surfaces into B-splines.
- Tie chamfers/fillets to the relevant thickness (`min(P["chamfer"], 0.3*t)`) so parameter changes don't break the model; if one fails, shrink or skip it and say so in the report.
- If unsure about the CadQuery API, run a small experiment; don't guess.

## Automatic checks (build.py)

- **Solid:** every part valid, volume > 0.
- **Mesh:** watertight, consistent winding, volume difference < 0.2 % (retries with coarser tolerance).
- **FDM:** fits the bed; downward-facing regions classified as `bridge` (supported on two opposite ends, span ≤ bridge_max) · `long bridge` · `hole roof` (≤ 8 mm) · `small` · `overhang` (one-sided cantilever or flatter than 45°); `overhang + long bridge` > `allow_overhang_mm2` → FAIL.
- **Collision:** part–part and part–reference pairs; common volume > 0.01 mm³ → FAIL. Kernel errors fail closed. IGNORE_CONTACT pairs become NOT_VERIFIED and prevent numeric PASS. Reference–reference pairs are outside scope.
- **Clearance:** CLEARANCES.
- **Requirements:** results of `checks()`; any failure → FAIL.

## Cautions

- Never delete the user's files; build writes only under `output/`.
- Say "correct", "no collision", "fits" only when the corresponding check passed; mark everything else "not verified".
- Edits made by hand in another tool (FreeCAD etc.) are overwritten by the next build → move lasting changes into `model.py` and tell the user.
