# Sources — Iskele

Original procedural design made for the user's delegated creative brief.
No external CAD model, commercial component, external part geometry, branded
product dimensions, or exact consumer-fit assumptions were used.
All dimensions are prototype choices, recorded in `requirements.md` and `P`.

Local workflow/API references consulted:
- `.agents/skills/agent-cad-skill/SKILL.md` and its `references/clarify.md`, `references/fdm_printing.md`.
- `.agents/skills/agent-cad-skill/assets/model_template.py`, `examples/bracket/model.py`,
  `examples/bridges/model.py` for build contract and established box/boolean APIs.
- New vertical fillet and geometric probe operations were exercised by the
  actual acceptance test and build with installed CadQuery 2.8.0.

The FDM reference is process guidance, not a source of measured dimensions for
this design and not evidence of strength or printability.
