"""Overhang classifier example — should FAIL with exactly:
20 mm window -> bridge, 40 mm window -> long bridge, ledge attached on one long edge -> overhang.
Origin: bottom centre of the wall, +Z up. Units: mm.
"""
import cadquery as cq

P = dict(bed=(235, 235), overhang_deg=45, bridge_max=25)


def parts(P):
    wall = cq.Workplane("XY").box(120, 3, 40, centered=(True, True, False))
    wall = wall.cut(cq.Workplane("XY").box(20, 10, 8, centered=(True, True, False)).translate((-30, 0, 15)))
    wall = wall.cut(cq.Workplane("XY").box(40, 10, 8, centered=(True, True, False)).translate((30, 0, 15)))
    ledge = cq.Workplane("XY").box(30, 10, 2, centered=(True, False, False)).translate((-30, 1.5, 30))
    return [dict(name="Wall", shape=wall.union(ledge), process="fdm", print_rot=[], color=(0.5, 0.5, 0.6))]
