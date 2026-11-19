# Iskele — parametric desk organizer

A single connected body with two open pen towers, a shallow tray and an open-top cable notch. Prototype size **180 × 94 × 100 mm**: towers 100 / 76 mm, tray 18 mm, nominal wall 3 mm, base 5 mm, notch width 10 mm. All of these are named parameters in `model.py`. The dimensions are not a fit guarantee for a particular pen or cable.

This is the most complete example in the repository: it shows the full workflow output — requirements, sources, model and an independent acceptance test.

| File | Contents |
|---|---|
| [`requirements.md`](requirements.md) | Requirements table and how each one is verified |
| [`sources.md`](sources.md) | Where every dimension comes from |
| [`model.py`](model.py) | Parametric model with `checks()` |
| [`test_model.py`](test_model.py) | Acceptance test with fixed-coordinate probes, independent of the model's own checks |

## Run

From the repository root (after creating the environment, see [CONTRIBUTING.md](../../CONTRIBUTING.md#development-setup)):

```bash
.venv/bin/python examples/iskele/test_model.py
.venv/bin/python .agents/skills/agent-cad-skill/scripts/build.py examples/iskele/model.py --out output/iskele
```

Expected result: numeric **PASS**, rendering **PASS** (when the machine can render), overall **NOT_VERIFIED** — exit code 0 covers the numeric checks only; physical printing, strength and real-part fit are not verified. On headless Linux, see [Headless Linux](../../docs/verification.md#headless-linux).

STEP, STL, reports and three preview images are written to `output/iskele/`, which is ignored by Git. The current image list is `report.json` → `images`. The fixed-coordinate acceptance test certifies the prototype dimensions, not arbitrary parameter combinations.
