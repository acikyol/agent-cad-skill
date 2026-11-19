# Laser cutting / CNC / sheet metal

## Laser cutting (2D)
- Set the part to `process="laser"` and pass the 2D profile in the XY plane via `dxf=` (outer contour + inner holes, closed wires). Keep the thickness as an extrusion in the 3D model so assembly/collision checks still work.
- Kerf depends on material, ~0.1–0.2 mm; for tight fits offset the profile by kerf/2 (`offset2D`). Tell the user which value you used.
- Finger-joint / tab-slot width = material thickness (+ measured deviation). Plywood/acrylic thickness differs from nominal; have it measured.
- Inner corners can be sharp; minimum feature width ≥ material thickness.
- DXF units mm; one part per file. For engraving lines, produce a separate DXF if requested.

## CNC milling
- Inner corners cannot be smaller than the tool radius: inner radius ≥ tool Ø/2 (+0.1). If a square corner is needed, add dog-bone cuts.
- Deep narrow pockets: depth ≤ 3–4 × tool diameter.
- Plan workholding margin and holding tabs; keep the bottom flat for one-sided machining.
- `process="cnc"`: STEP is the main output (CAM uses it); for 2.5D parts a `dxf` profile can also be given.

## Sheet metal
- Bend allowance: K-factor ~0.33–0.44; inner bend radius ≥ sheet thickness.
- Holes ≥ 2 × thickness + inner radius away from bend lines.
- Provide the flat pattern as DXF; compute it by hand in CadQuery and show the formula in the report.
