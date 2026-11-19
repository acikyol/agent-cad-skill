# Clarify before modeling

Goal: the model is **right the first time**. A model built on a wrong assumption is expensive to fix (print time, material, the user's trust). Don't start modeling while critical points are unclear.

All questions and summaries to the user are in **the user's language**; this file and `requirements.md` column names stay in English (cell contents may be in the user's language).

## 1. Requirements checklist

Map the request onto this list. Status of each item: **confirmed** (user said / measured / official source) · **assumption** (you proposed, user approved) · **open**.

**Purpose and use**
- What does the part do, where, how is it used (handheld, desk, wall, vehicle, outdoors)?
- Loads/forces, temperature, humidity, UV, vibration?
- Quantity: one-off or series?

**Mating parts**
- Which off-the-shelf parts does it mate with (exact model, revision, accessories: heatsink, HAT, cable)? → `off_the_shelf_parts.md`
- Which surfaces/holes does it attach to; joint type (screw, snap-fit, glue, magnet)?
- Ports, buttons, LEDs, cards, ventilation that must stay accessible; cable entry/exit directions?

**Dimensions and tolerances**
- Critical dimensions (outer limits, hole spacing, seating faces) — source (calipers, drawing, estimate)?
- Which dimensions are free (aesthetic) and which are exact?
- Fit types: press / sliding / clearance.

**Manufacturing**
- Method: FDM (printer model, bed, nozzle), laser (material, thickness), CNC, sheet metal, bought-in?
- Material (PLA, PETG, ABS, aluminium…)? Supports allowed? Colour/finish?
- Hardware the user already has (diameter, length, head type) — design around it.

**Outputs**
- Which files: STL (print orientation) · STEP (assembly/CAD) · DXF (2D cutting) · **FreeCAD .FCStd (optional)** · images?
- Output folder / naming preferences?

**Appearance**
- Style (plain, industrial, rounded/sharp), visible screws OK, logo/text?
- Maximum size/thickness?

## 2. Asking questions

- Ask about every **open** critical item; for non-critical ones propose a sensible default and get it confirmed.
- Ask **with options**: use the agent's question/choice tool if it has one; otherwise numbered questions with a/b/c options in a message. 2–4 concrete options per question, mark your pick "(Önerilen)" with a one-line reason; the user may answer freely.
- At most 4 questions per round; first the ones that change the design most (method, mating parts, critical dimensions), then details.
- Don't re-ask what the user already answered; read the project's `requirements.md`.
- Don't ask what research can answer (a board's dimensions) — research it. But do ask which exact model/revision.
- Don't proceed on a critical item without an answer. If the user says "you decide", choose the safest option and record it in `requirements.md` as "assumption (left to us)".

## 3. Requirements summary and approval

Once clear, write `requirements.md` in the project and show the user a short summary in their language:

```markdown
# Requirements — <project>
| # | Requirement | Value | Status | Source | Verification |
|---|---|---|---|---|---|
| R1 | Pi 5 + Active Cooler must fit | board 85×56, cooler 63.5×42.5×~11 | confirmed | pip.raspberrypi.com (2026-10-11) | collision + clearance ≥0.4 |
| R2 | Wall thickness | ≥ 2.0 | assumption (approved) | — | check: min wall |
| R3 | USB ports reachable from outside | opening ≥ port+0.5 | confirmed | Pi 5 STEP | check: opening |
```

- The "Verification" column is never empty: each requirement is verified by build's automatic checks, a custom check in `checks()`, or explicitly "visual check".
- Start modeling after the user approves. Record later changes in this table first.

## 4. Verification gate (before delivery)

Before saying "done", all of these must hold:
1. build exit code 0 (all automatic and `checks()` checks passed),
2. every row of `requirements.md` has been verified and the result recorded,
3. the images were actually looked at (no flipped/missing/misoriented features),
4. the list of assumptions was stated to the user.
If something cannot be verified (e.g. no real model of the part), report it as "not verified" — never "correct".
