"""Parametric model template (agent-cad-skill skill).

Requirements: requirements.md   Sources: sources.md
Coordinate system: <where is the origin, which way is +X/+Y/+Z — fill this in>
Units: mm
Put a source next to every off-the-shelf dimension:  PI_HOLE_SPACING = 58.0  # pip.raspberrypi.com mechanical drawing, 2026-10-11
"""
import cadquery as cq

# ---------------------------------------------------------------- parameters
P = dict(
    bed=(235, 235),        # FDM bed (x, y); remove if not FDM
    overhang_deg=45,       # support-free limit (from horizontal)
    bridge_max=25,         # longest acceptable bridge
    # example part: L bracket with holes
    w=40.0,                # width
    t=4.0,                 # thickness
    leg_a=50.0,            # horizontal leg
    leg_b=35.0,            # vertical leg
    hole_d=4.4,            # M4 clearance
    chamfer=1.0,
)


# ---------------------------------------------------------------- references (optional)
def references(P):
    # e.g.: return [dict(name="Motor", shape=cq.importers.importStep("sources/motor.step"))]
    return []


# ---------------------------------------------------------------- parts
def bracket(P):
    w, t = P["w"], P["t"]
    horizontal = cq.Workplane("XY").box(P["leg_a"], w, t, centered=(False, True, False))
    vertical = cq.Workplane("XY").box(t, w, P["leg_b"], centered=(False, True, False))
    body = horizontal.union(vertical)
    body = (body.faces(">Z[-1]").workplane(centerOption="CenterOfBoundBox")   # top face of the horizontal leg
            .center(P["leg_a"] / 4, 0).hole(P["hole_d"]))
    body = body.faces("<X").workplane(centerOption="CenterOfBoundBox").hole(P["hole_d"])
    # tie chamfers/fillets to thickness, otherwise OCC fails with "command not done" on thin sections
    return body.edges("|Y and >X").chamfer(min(P["chamfer"], 0.3 * t))


def parts(P):
    return [
        dict(name="Bracket", shape=bracket(P), process="fdm",
             print_rot=[("Y", -90)],     # vertical leg on the bed: one hole axis horizontal -> small hole roof, fine
             qty=1, group="Parts", color=(0.85, 0.5, 0.2), allow_overhang_mm2=0),
    ]


def checks(P, S):
    """Every measurable row of requirements.md becomes a check here.
    S: {name: cq.Shape} in assembly position. Return: [(id, passed, detail)]"""
    b = S["Bracket"]
    bb = b.BoundingBox()
    # example checks — replace with your own requirements
    return [
        ("R1", abs(bb.xlen - P["leg_a"]) < 0.01, f"horizontal leg {bb.xlen:.2f} = {P['leg_a']}"),
        ("R2", P["t"] >= 3.0, f"thickness {P['t']} >= 3.0 (load-bearing)"),
        ("R3", P["hole_d"] >= 4.3, f"M4 clearance hole Ø{P['hole_d']} >= 4.3"),
    ]


CLEARANCES = []          # [("A", "B", 0.3)]
IGNORE_CONTACT = []      # [("Lid", "Body")]
