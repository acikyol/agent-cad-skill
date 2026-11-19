"""Example with deliberate mistakes — should FAIL with: long bridge (shelf), collision (board), clearance (lid).
Also exports a laser-cut DXF. Origin: bottom centre of the box, +Z up. Units: mm.
"""
import cadquery as cq

P = dict(bed=(235, 235), overhang_deg=45, bridge_max=25, L=80, W=60, H=40, t=2.5)


def references(P):
    # board placed 1 mm into the floor on purpose -> must collide with Box
    board = cq.Workplane("XY").box(50, 40, 1.6, centered=(True, True, False)).translate((0, 0, P["t"] - 1.0))
    return [dict(name="Board", shape=board)]


def box(P):
    L, W, H, t = P["L"], P["W"], P["H"], P["t"]
    b = cq.Workplane("XY").box(L, W, H, centered=(True, True, False))
    b = b.cut(cq.Workplane("XY").box(L - 2 * t, W - 2 * t, H, centered=(True, True, False)).translate((0, 0, t)))
    # horizontal shelf spanning the inner width (55 mm) -> long bridge
    shelf = cq.Workplane("XY").box(15, W - 2 * t, 2, centered=(False, True, False)).translate((L / 2 - t - 15, 0, 25))
    return b.union(shelf)


def lid(P):
    # 0.1 mm above the box while 0.3 is required -> clearance failure
    return cq.Workplane("XY").box(P["L"], P["W"], 2, centered=(True, True, False)).translate((0, 0, P["H"] + 0.1))


def parts(P):
    frame = (cq.Workplane("XY").rect(P["L"], P["W"]).extrude(3).faces(">Z").workplane()
             .rect(P["L"] - 20, P["W"] - 20).cutThruAll())
    return [
        dict(name="Box", shape=box(P), process="fdm", print_rot=[], group="Body", color=(0.4, 0.4, 0.45)),
        dict(name="Lid", shape=lid(P), process="fdm", print_rot=[("X", 180)], group="Body", color=(0.8, 0.5, 0.2)),
        dict(name="LaserFrame", shape=frame.translate((0, 0, -10)), process="laser",
             dxf=cq.Workplane("XY").rect(P["L"], P["W"]).rect(P["L"] - 20, P["W"] - 20),
             group="Laser", color=(0.2, 0.6, 0.3)),
    ]


CLEARANCES = [("Lid", "Box", 0.3)]
