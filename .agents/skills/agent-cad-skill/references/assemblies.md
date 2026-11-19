# Assemblies and reference parts

## Use real models
- Find the **manufacturer STEP** of mating components (boards, displays, motors, bearings, connectors) and load it via `references()`. Use an estimated box model only if none exists, and mark it as an "assumption" in the report.
- Large STEP files (thousands of solids) are slow: load once and cache as `sources/*.brep`, or crop to the relevant region with `intersect`.
- Write the component placement as a **transform function** (e.g. `board_to_assembly(x, y, z)`); avoid mirror transforms (determinant must be +1); when mounting upside down, flip two axes together.

## What to check
- The component's **moving/plugged parts**: the plug body inserted into a connector, cable bend allowance, a button's travel, a fan's intake space. Add them as separate "envelope" solids in `references()` (e.g. `HDMI_plug_envelope`).
- For parts with uncertain height (heatsink, battery) model the worst case and report the margin.
- Pin critical gaps (≥ 0.3–0.5 mm) with `CLEARANCES`; a 0.04 mm "touch" with zero collision volume becomes a collision within print tolerance.
- Screw path: screw length = sum of clamped parts + thread engagement (in plastic ≥ 2–2.5 × diameter); check that the screw head fits.

## Assembly order and access
- Can every screw be reached during assembly? If one part covers another part's screws, state the order in the report.
- Direction and hand/tool access for plugging cables/connectors.
- For products that must stand (stands, feet) compute the centre of mass from mass estimates, show it stays inside the support polygon, and report the tipping margin in mm.
