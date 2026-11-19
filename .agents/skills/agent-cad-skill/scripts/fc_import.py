# Runs inside freecadcmd (called by to_freecad.py). Never touches an open FreeCAD window.
# Environment variables: FCI_OUT (build output dir), FCI_FCSTD (target .FCStd)
import json
import os

import FreeCAD as App
import Part

out = os.environ["FCI_OUT"]
target = os.environ["FCI_FCSTD"]
man = json.load(open(os.path.join(out, "manifest.json")))

name = os.path.splitext(os.path.basename(target))[0].replace("-", "_").replace(" ", "_")
doc = App.newDocument(name)
groups = {}


def group(gname):
    key = "".join(ch if ch.isalnum() else "_" for ch in gname)
    if key[0].isdigit():
        key = "_" + key
    if key not in groups:
        g = doc.addObject("App::DocumentObjectGroup", key)
        g.Label = gname
        groups[key] = g
    return groups[key]


for p in man["parts"]:
    step = p["files"].get("step")
    if not step:
        continue
    s = Part.Shape()
    s.read(os.path.join(out, step))
    o = doc.addObject("Part::Feature", p["name"])
    o.Shape = s
    group(p.get("group", "Parts")).addObject(o)

ref_dir = os.path.join(out, "step_ref")
if os.path.isdir(ref_dir):
    for f in sorted(os.listdir(ref_dir)):
        if f.lower().endswith((".step", ".stp")):
            s = Part.Shape()
            s.read(os.path.join(ref_dir, f))
            o = doc.addObject("Part::Feature", os.path.splitext(f)[0])
            o.Shape = s
            group("References (not manufactured)").addObject(o)

doc.recompute()
doc.saveAs(target)
print("FCSTD_OK", target, len(doc.Objects))
