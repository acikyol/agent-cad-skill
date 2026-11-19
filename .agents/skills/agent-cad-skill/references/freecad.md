# FreeCAD (optional)

FreeCAD is **not required** by this workflow. The real outputs are STEP/STL/DXF; STEP opens in any CAD tool (FreeCAD, Fusion, Onshape, SolidWorks, KiCad…). Produce a FreeCAD document only if the user asked for it; during clarification ask whether they also want a FreeCAD (.FCStd) file.

## Export
- `PY <SKILL_DIR>/scripts/to_freecad.py <project>/output [target.FCStd]`
  - Runs FreeCAD's command-line build (`freecadcmd`); independent of any open FreeCAD window and doesn't affect it.
  - Parts go into the groups from `manifest.json`; references into a "References (not manufactured)" group. An existing target is backed up with a timestamp.
  - If `freecadcmd` is not found it exits with code 3 and skips; tell the user to set `FREECADCMD=<path>` or open the STEP files manually. (macOS: `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd`; Windows: `C:\Program Files\FreeCAD x.y\bin\FreeCADCmd.exe`)

## With an open FreeCAD (e.g. via MCP)
- Don't do heavy work (multi-part booleans, collisions against STEP files with thousands of solids) in an open FreeCAD: it can crash, lose output, or reopen an old recovery copy. Heavy work belongs in build.py.
- Use the open FreeCAD only to open the finished `.FCStd` and take screenshots.

## After a crash / undo
- Compare the file on disk with the open document (object list, volumes); if the open one is older, close it without saving and reopen from disk.
- The source of truth is `model.py`: when in doubt, rerun build.
