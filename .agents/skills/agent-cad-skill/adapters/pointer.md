## CAD / 3D model work — agent-cad-skill skill

When the user asks for a 3D model, CAD part, assembly, enclosure, bracket, STL/STEP/DXF output, modeling from measurements, a laser/CNC profile or a 3D-printed part, **first read this file and follow its instructions:**

`{SKILL_DIR}/SKILL.md`

In short: (1) clarify requirements with option-based questions and get approval, (2) research off-the-shelf part dimensions from official sources, (3) write one parametric CadQuery `model.py`, (4) build and verify with `python {SKILL_DIR}/scripts/build.py model.py`, (5) FreeCAD output only if the user wants it. **Talk to the user in the language they write in** (questions, summaries, answers); code and files stay in English. Script paths and details are in SKILL.md; read files under `{SKILL_DIR}/references/` as needed.
