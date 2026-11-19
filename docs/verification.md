# Verification semantics

This page describes exactly what `build.py` checks, what its results mean, and what it deliberately does **not** prove.

## Result states

Reports use **PASS / FAIL / NOT_VERIFIED**.

| Field | Meaning |
|---|---|
| `numeric_status` | Result of the executed numeric checks only. The legacy `passed` boolean mirrors it. |
| `status` | Overall result: `FAIL` on any numeric failure, otherwise `NOT_VERIFIED` until independent visual and requirements review. |
| `verification` | Per-area breakdown (numeric, rendering, …). |

The tool never emits an overall `PASS` automatically, even when every check passes and images are generated.

| Exit code | Meaning |
|---|---|
| `0` | Executed numeric checks passed — **not** a full design approval |
| `1` | Numeric failure, or an ignored collision pair |
| `2` | Model or command line could not be loaded |

## Rules

- **No silent zeros.** Boolean exceptions, invalid intersection shapes and non-finite or negative volumes are never treated as "no intersection". A check error is recorded as `NOT_VERIFIED` and makes the numeric result fail (non-zero exit).
- **Collisions.** Intersections larger than **0.01 mm³** fail. Face contact is allowed without `IGNORE_CONTACT`. Pairs listed in `IGNORE_CONTACT` become `NOT_VERIFIED` and prevent a numeric pass — ignoring a pair is not proof that the penetration is acceptable.
- **Missing checks.** A missing or empty `checks()` or clearance list is `NOT_VERIFIED`.
- **Reports first.** Numeric JSON, Markdown and the manifest are written **before** rendering starts, so a renderer crash never loses them.
- **Isolated rendering.** The render worker reads the exported STEP/STL files, not `model.py`. `--render-timeout` limits it (default 60 s). Crash and timeout logs go to `output/render.log`; rendering is then `NOT_VERIFIED` and numeric results are kept. `--no-render` is an explicit `NOT_VERIFIED`.
- **Fresh images only.** Only a complete, freshly validated PNG set is published; images left over from an earlier run are never listed. Read `report.json` → `images` instead of globbing the directory.
- **Safe FreeCAD export.** Export goes to a fresh temporary file and replaces the original only after exit code 0, a `FCSTD_OK` marker and a non-empty result. On failure the old document is kept.

## Outside the automatic proof

- Strength, tolerances and manufacturability
- Requirements that are not written as `checks()`
- Collisions between two reference parts, and reference parts that are missing
- Print-bed fit when `P['bed']` is not set
- FDM overhang classification is a heuristic
- Successful PNG generation is not a visual inspection — someone still has to look at the images

## Trust model

`model.py` is executed as ordinary Python and is **not** sandboxed. Native geometry-kernel crashes during the numeric phase and arbitrary model/export exceptions are not isolated. Only build models you trust — see [SECURITY.md](../SECURITY.md).

## Reproducing the tested environment

[`requirements.lock`](../.agents/skills/agent-cad-skill/requirements.lock) pins every distribution of the environment tested on **Linux x86_64 with CPython 3.12**. It is not a hash lock and does not guarantee identical results on other Python versions or platforms. `setup_env.py` installs from this file; it does not install system graphics libraries.

```bash
python3 .agents/skills/agent-cad-skill/scripts/setup_env.py .venv
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python tests/run_tests.py
.venv/bin/python .agents/skills/agent-cad-skill/scripts/build.py examples/bracket/model.py --out output/smoke --render-timeout 15
```

The regression suite covers kernel failures, ignored pairs, real geometry, clearance failures, incomplete requirements, renderer kill/timeout, fresh image publication and stale FreeCAD targets. Success-path graphics tests use a tiny stand-in PNG backend, so they do not prove real rendering on your machine.

### Headless Linux

On servers without a display, rendering fails when EGL/OSMesa libraries are missing; the numeric results are still saved and rendering is reported as `NOT_VERIFIED`. On Debian/Ubuntu, `sudo apt-get install -y libgl1 libegl1` is enough (verified on a clean Ubuntu 24.04 arm64 VM: full test suite and real rendering pass). Alternatively install `libosmesa6` and set `VTK_DEFAULT_OPENGL_WINDOW=vtkOSOpenGLRenderWindow`.
