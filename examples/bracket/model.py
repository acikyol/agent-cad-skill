"""Example: L bracket with two M4 holes — should PASS.
Origin: inner corner of the L, +X along the horizontal leg, +Z up. Units: mm.
"""
import cadquery as cq

P = dict(bed=(235, 235), overhang_deg=45, bridge_max=25,
         w=40.0, t=4.0, leg_a=50.0, leg_b=35.0, hole_d=4.4, chamfer=1.0)


def bracket(P):
    w, t = P["w"], P["t"]
    body = (cq.Workplane("XY").box(P["leg_a"], w, t, centered=(False, True, False))
            .union(cq.Workplane("XY").box(t, w, P["leg_b"], centered=(False, True, False))))
    body = body.faces(">Z[-1]").workplane(centerOption="CenterOfBoundBox").center(P["leg_a"] / 4, 0).hole(P["hole_d"])
    body = body.faces("<X").workplane(centerOption="CenterOfBoundBox").hole(P["hole_d"])
    return body.edges("|Y and >X").chamfer(min(P["chamfer"], 0.3 * t))


def parts(P):
    return [dict(name="Bracket", shape=bracket(P), process="fdm", print_rot=[("Y", -90)],
                 color=(0.85, 0.5, 0.2))]


def checks(P, S):
    bb = S["Bracket"].BoundingBox()
    return [("R1", abs(bb.xlen - P["leg_a"]) < 0.01, f"horizontal leg {bb.xlen:.2f}"),
            ("R2", P["t"] >= 3.0, f"thickness {P['t']} >= 3.0")]
