# Iskele — prototype requirements and verification

The user explicitly delegated the design, dimensions and style: imagine an original
model and actually build it, without another planning/approval round. Dimensions
below are **prototype assumptions (left to us)**, not product standards or
measurements of a commercial pen/cable. No external part is used.

## Concept

A small architectural quay: a low rounded plinth, two independently open stepped
pen towers at the rear left, and a shallow square catch-all tray on the right.
A roofless U-notch in the tray's front rim is a cable resting place, not a clip,
strain relief, or a captive connector. The front-left plinth stays clear.
All features belong to one connected solid. Vertical corner rounds soften the
silhouette without rounding the underside away from the desk.

Coordinates: origin at the base centre on the desk, +X right, +Y rear, +Z up.
All dimensions in mm. `P` in `model.py` holds the design parameters.

| ID | Requirement | Value | Status / source | Verification and actual result |
|---|---|---|---|---|
| R1 | One connected manufactured body | One valid solid | Confirmed design brief | BRep validity and solid count: PASS, 1 solid, 158063.689 mm³ |
| R2 | Prototype envelope; flat desk datum | 180 × 94 × 100, zmin=0 | Assumption, left to us | Actual BRep bounding box: 180.000 × 94.000 × 100.000; zmin=0.000: PASS |
| R3 | Two upward-open wells | Nominal rounded openings 30 × 30; inner radius 2 | Assumption, left to us | Rounded 29.80 × 29.80 air probes extend from z=5.1 above the highest rim: zero material intersection, PASS for both |
| R3 | Upward-open catch-all tray | Nominal rounded opening 72 × 72; inner radius 5 | Assumption, left to us | Rounded 71.80 × 71.80 air probe from z=5.1 above highest rim: zero intersection, PASS |
| R4 | Closed floors | Nominal 5 thick | Assumption, left to us | Rounded floor witnesses spanning z=0.1..4.9 under each cavity have zero missing volume: PASS. This proves these regions, not a global minimum thickness |
| R5 | Architectural stepped heights | Tower heights 100 and 76; tray rim 18 | Assumption, left to us | Actual rear-rim section bounding-box heights 100.000, 76.000, 18.000: PASS |
| R6 | Cable rest open upward and through front rim | Nominal width 10; landing at z=9 | Confirmed feature; dimensions left to us | 9.80-wide air prism through rim and above: zero material; 8.80-high landing witness: zero missing volume, PASS |
| R7 | Unified simple rounded appearance | Teal rendering; vertical corner radii 8 base/tray, 5 towers | Assumption, left to us | Three actual PNGs generated (rendering PASS). Independent visual review pending; images alone are not inspection |
| R8 | Upright additive-manufacturing candidate, no designed roofs or ledges | Flat base down; nominal 3 wall; assumed 220 × 220 bed | Assumption, not an identified printer | Build's mesh/bed/overhang numeric checks PASS; 0 mm² detected overhang. Not a printability guarantee |
| R9 | Editable CAD and mesh deliverables | STEP, STL, PNG, JSON/Markdown report | Requested delegated workflow | Actual build exit 0, exports present under ignored `output/iskele/` |

## Executed verification

Before `model.py` existed, `test_model.py` was written and executed. It failed with
`AssertionError: False is not true : Iskele model has not been implemented` (exit 1).
After implementation, the same test passed (1 test, exit 0). Besides model checks,
it independently uses fixed-coordinate empty-space prisms and material points.

```bash
.venv/bin/python examples/iskele/test_model.py
LD_LIBRARY_PATH=$HOME/cad-render-libs/extracted/usr/lib/x86_64-linux-gnu \
VTK_DEFAULT_OPENGL_WINDOW=vtkOSOpenGLRenderWindow \
.venv/bin/python .agents/skills/agent-cad-skill/scripts/build.py examples/iskele/model.py --out output/iskele
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python tests/run_tests.py
```

Actual build: exit **0**, numeric **PASS**, rendering **PASS**, overall
**NOT_VERIFIED** (independent visual review and real-world validation are separate).
All 12 custom BRep checks passed. STL watertight and winding consistent;
mesh/BRep volume difference **0.014%**, 1916 faces, mesh tolerance 0.02 mm.
Regression results: **14 hardening tests PASS**; the three existing example tests
(`bracket`, `collisions`, `bridges`) all matched their expected outcomes.
The latter two are deliberately failing designs, not failing regression tests.

The graphics environment variables apply only to that command. No system
configuration was changed; the OSMesa library was already supplied in a user directory.

## Limitations and assumptions

- No physical print, slicing, load, tip-over, durability, temperature, material,
  cable bend-radius, retention or real-object fit test was performed.
- No claim that a particular pen, connector, phone or cable fits. No mating parts
  or clearance pairs exist, so report clearances remain NOT_VERIFIED.
- Intended candidate process is upright FDM; material, nozzle, layer height,
  tolerances and printer remain unspecified. Bed size is an assumption, not
  evidence of the user's machine. The overhang classifier is a heuristic.
- Open-space/floor/section probes evaluate actual geometry but are selected
  witnesses, not an exhaustive wall-thickness or topology proof. Probe inset is
  0.1 mm to avoid ambiguous coincident boundary booleans.
- Parametric means dimensions are editable and geometry regenerates; arbitrary
  parameter combinations are not certified. Maintain positive inner radii,
  nonoverlapping cavities, walls on the base, and notch above the tray floor.
- No DXF (no sheet-cut component) or FreeCAD-native file was requested/generated.
- Rendering is verified separately from visual inspection. Parent agent will
  inspect the current report's PNG list before publishing. No commit/push here.
