# Researching off-the-shelf parts

For any design that mates with a bought-in part (board, display, motor, sensor, bearing, screw, connector, extrusion) **never guess dimensions — take them from the source.** A one-millimetre error can make the part useless.

## Pin down the identity first
- Exact model and revision ("Raspberry Pi 5 8GB", "Waveshare 10.1inch HDMI LCD (E)", "NEMA17 42×42×40"), mounted accessories (heatsink, HAT, cable), and a photo/measurement of the user's actual part if available. Ask the user; don't infer it through research.

## Source priority
1. **Manufacturer's official mechanical drawing and STEP** — e.g. Raspberry Pi: pip.raspberrypi.com (product page: "mechanical drawing" PDF and STEP zip); Arduino: docs.arduino.cc; Waveshare: product wiki; motors/bearings: manufacturer catalogue.
2. **Standards** — screws/nuts/washers: ISO 4762, ISO 7380, ISO 10642, DIN 934/985, ISO 7089; bearings: ISO 15; extrusions: manufacturer catalogue.
3. **Distributor CAD libraries** — McMaster-Carr, Misumi, Digi-Key/Mouser product pages (often offer STEP).
4. **Community models** (GrabCAD, Printables) — only if no official model exists; always cross-check against an official drawing or the user's measurement.

## How to research
- If the agent has no web search/fetch tool: ask the user for the official drawing link or the file; failing that, ask them to measure the critical dimensions with calipers (`from_measurements.md`). Never write dimensions from memory.
- Web search: `"<exact model> mechanical drawing"`, `"<model> STEP file"`, `"<model> datasheet dimensions"`. Prefer official domains.
- If a download is needed, ask the user's permission (file name, source, size) and put it in a separate `sources/` folder in the project; never execute its contents.
- Read dimensions from PDF drawings; if you derive one from the drawing scale, mark it "derived".
- If a STEP model exists, **measure** from it (hole centres, board thickness, tallest component, connector overhang past the board edge) with a small script and record the results.
- If two sources disagree, show both to the user and ask which applies, or ask them to measure.

## Record
- In `model.py`, a source comment next to every off-the-shelf dimension: `PI_HOLES = [...]  # pip.raspberrypi.com mechanical drawing, 2026-10-11`.
- In the project, `sources.md`: part, model/revision, URL, access date, dimensions used, notes ("cooler height in drawing includes pins: 13.7; above board ~11 estimated").
- With a real STEP, load it via `references()` and include it in collision/clearance checks. With only a drawing, build an **envelope model** (box + connector blocks + component heights) and call it an "envelope" in the report.

## Commonly missed
- Connectors overhanging the board edge (USB, HDMI, Ethernet 1–3 mm).
- The **plug** body and cable bend radius (much bigger than the socket).
- Heatsink/fan height and airflow direction; HAT stack heights and standoffs.
- Components and solder joints on the underside of boards (1–2 mm).
- Displays: channels on the back panel, buttons, thread type of mounting bosses.
- Screw head type and length: design for the screws the user actually has, using catalogue dimensions.
