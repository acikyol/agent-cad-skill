# FDM 3D printing rules

These rules were learned from real print trials. Each has its reason next to it.

## Print orientation first
- Choose each part's print orientation before designing and record it in `print_rot`. Put the visible/cosmetic face on the bed (smoothest surface).
- In long load-bearing parts, lay the layers so the load runs along them; layer adhesion is the weak direction.
- Changing orientation changes every overhang decision; never say "we'll just flip it" — verify with build.

## Overhangs (support-free printing)
- Every downward-facing surface ≥ **45°** from horizontal (P["overhang_deg"]). Never go below this on visible faces.
- Fillets on the bed side create near-horizontal overhangs → use **45° chamfers** there.
- Horizontal holes: Ø ≤ 6 is usually fine; give larger horizontal holes/slots a **45° teardrop** top.
- Put a **45° wedge** under horizontal ledges, or start the ledge from the bed side.
- Bridges: a horizontal ceiling supported at both ends ≤ ~25 mm is fine. Turn long horizontal openings into edge-open notches.
- Report regions "small", "hole roof" and "bridge" are usually fine; fix "overhang" and "long bridge", or accept them with `allow_overhang_mm2` and a stated reason.

## Sizes and tolerances (0.4 nozzle, PLA/PETG)
| Purpose | Size |
|---|---|
| Self-tapping M2 / M2.5 / M3 | Ø1.7 / Ø2.2 / Ø2.6 |
| Clearance hole M2 / M2.5 / M3 / M4 | Ø2.3 / Ø2.8 / Ø3.3 / Ø4.4 |
| Countersink M2 / M2.5 / M3 | Ø4.0 / Ø5.0 / Ø6.0 |
| Nut trap (across flats) M3 / M4 | 5.7 / 7.2 (hexagon vertex up in print) |
| Heat-set insert M3 / M4 | Ø4.0 × 5 / Ø5.6 × 8 |
| Sliding fit gap (per side) | 0.25–0.35 |
| Press fit | 0.0–0.1 |
| Minimum wall | 1.2 (3 perimeters); load-bearing 2+ |
- Keep ≥ 1.5 mm material between a countersink and a part edge; less splits the edge.
- Dovetail + 0.15 gap was too tight; **straight rectangular tongue + 0.25** worked well.

## Parts larger than the bed
- Split them; hide the seam on visible faces with a 0.5 mm V-groove (optionally a matching fake groove for symmetry).
- Joint: straight tongue/slot (0.25 gap) + ideally screws of other parts clamping both sides of the seam.
- When a part nearly fills the bed, the brim must be off; tell the user.

## Mechanisms and strength
- Small sliding parts (buttons, sliders) in narrow horizontal holes jam because the hole roof sags → use a **flexure**: a ~1 mm lamella cut from the body, 0.6 mm slits on both sides, a pusher nub at its end. Force: F ≈ 3·E·I·δ/L³ (PLA E ≈ 3500 MPa); 2–4 N presses comfortably.
- Thin tall posts snap at the base → profile that widens smoothly toward the base (multi-section loft, quadratic growth); restrict the growth direction near components.
- Sharp inner corners start cracks → small chamfer/radius on inner corners.

## Slicer recommendations (mention in the report)
- First-layer squish: "elephant foot compensation" 0.2.
- High fan for bridges.
- PETG for parts with repeated flexing (flexures, hinges).
