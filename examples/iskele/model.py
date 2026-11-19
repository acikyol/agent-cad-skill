"""Iskele: two stepped towers on a low quay with an open cable landing.

Original prototype, no purchased-part dimensions. See requirements.md.
Coordinates: origin at base centre on desk; +X right, +Y rear, +Z up.
Units: mm. One connected manufactured solid, upright build orientation.
"""
import cadquery as cq

P = dict(
    bed=(220, 220), overhang_deg=45, bridge_max=25,
    width=180.0, depth=94.0, floor=5.0, base_radius=8.0,
    well_width=36.0, well_depth=36.0, wall=3.0, corner_radius=5.0,
    well_centres=((-64.0, 22.0), (-22.0, 22.0)),
    well_heights=(100.0, 76.0),
    tray_centre=(43.0, 0.0), tray_width=78.0, tray_depth=78.0,
    tray_height=18.0, tray_radius=8.0,
    notch_x=58.0, notch_width=10.0, notch_floor=9.0,
    probe_inset=0.1, probe_extension=1.0, volume_tolerance=0.001,
)


def rounded_prism(width, depth, height, radius, x=0, y=0, z=0):
    """Vertical edge rounds retain a flat underside and upward-open profile."""
    return (cq.Workplane("XY").box(width, depth, height,
                                  centered=(True, True, False))
            .edges("|Z").fillet(radius).translate((x, y, z)))


def parts(P):
    floor, wall = P["floor"], P["wall"]
    body = rounded_prism(P["width"], P["depth"], floor, P["base_radius"])
    # All towers start at z=0, so each overlaps the common base in volume.
    for (x, y), height in zip(P["well_centres"], P["well_heights"]):
        tower = rounded_prism(P["well_width"], P["well_depth"], height,
                              P["corner_radius"], x, y)
        body = body.union(tower)
    tx, ty = P["tray_centre"]
    tray = rounded_prism(P["tray_width"], P["tray_depth"], P["tray_height"],
                         P["tray_radius"], tx, ty)
    body = body.union(tray)
    for (x, y), height in zip(P["well_centres"], P["well_heights"]):
        cavity = rounded_prism(P["well_width"] - 2*wall, P["well_depth"] - 2*wall,
                               height, P["corner_radius"] - wall, x, y, floor)
        body = body.cut(cavity)
    tray_cavity = rounded_prism(P["tray_width"] - 2*wall, P["tray_depth"] - 2*wall,
                                P["tray_height"], P["tray_radius"] - wall, tx, ty, floor)
    body = body.cut(tray_cavity)
    # Rectangular U-notch through front rim: no roof, cable not captive.
    notch = (cq.Workplane("XY").box(P["notch_width"], 3*wall, P["tray_height"],
                                    centered=(True, True, False))
             .translate((P["notch_x"], ty-P["tray_depth"]/2, P["notch_floor"])))
    body = body.cut(notch)
    return [dict(name="Iskele", shape=body, process="fdm", print_rot=[],
                 qty=1, group="Iskele", color=(0.16, 0.48, 0.53),
                 allow_overhang_mm2=0)]


def checks(P, S):
    """BRep measurements and volumetric witnesses, not parameter-only claims.

    Probe tests establish selected regions, not a global wall-thickness proof.
    """
    body = S["Iskele"]
    bb = body.BoundingBox()
    tol, e = P["volume_tolerance"], P["probe_inset"]
    results = [
        ("R1", body.isValid() and len(body.Solids()) == 1,
         f"valid={body.isValid()}, solids={len(body.Solids())}, volume={body.Volume():.3f} mm3"),
        ("R2", all(abs(a-b) < e for a,b in zip((bb.xlen, bb.ylen, bb.zlen),
                          (P["width"], P["depth"], max(P["well_heights"])))) and abs(bb.zmin) < e,
         f"measured envelope={bb.xlen:.3f} x {bb.ylen:.3f} x {bb.zlen:.3f} mm; zmin={bb.zmin:.3f}"),
    ]
    regions = [(f"well_{i+1}", x, y, P["well_width"], P["well_depth"], height, P["corner_radius"])
               for i, ((x,y),height) in enumerate(zip(P["well_centres"], P["well_heights"]))]
    regions.append(("tray", *P["tray_centre"], P["tray_width"], P["tray_depth"],
                    P["tray_height"], P["tray_radius"]))
    for name,x,y,w,d,h,r in regions:
        iw, id_ = w-2*P["wall"]-2*e, d-2*P["wall"]-2*e
        # Probe above every rim too: a lid or roof would fail this check.
        air = rounded_prism(iw, id_, max(P["well_heights"])+P["probe_extension"],
                            r-P["wall"]-e, x,y,P["floor"]+e).val()
        intersection = body.intersect(air).Volume()
        results.append((f"R3_{name}_open", intersection < tol,
                        f"empty rounded access prism {iw:.2f} x {id_:.2f} mm; material={intersection:.6f} mm3"))
        floor_probe = rounded_prism(iw,id_,P["floor"]-2*e,r-P["wall"]-e,x,y,e).val()
        missing_floor = floor_probe.cut(body).Volume()
        results.append((f"R4_{name}_floor", missing_floor < tol,
                        f"floor witness depth={P['floor']-2*e:.2f} mm; missing={missing_floor:.6f} mm3"))
        # Measure rear rim height from an actual narrow section of the model.
        rim = (cq.Workplane("XY").box(iw/2, P["wall"]-2*e,
                                      max(P["well_heights"])+P["probe_extension"],
                                      centered=(True,True,False))
               .translate((x,y+d/2-P["wall"]/2,0)).val())
        section = body.intersect(rim)
        measured_h = section.BoundingBox().zlen if section.Volume() > tol else 0
        results.append((f"R5_{name}_height", abs(measured_h-h) < e,
                        f"rear rim measured height={measured_h:.3f} mm (target {h:.3f})"))
    nx, ny = P["notch_x"], P["tray_centre"][1]-P["tray_depth"]/2
    air = (cq.Workplane("XY").box(P["notch_width"]-2*e, 3*P["wall"]-2*e,
                                  max(P["well_heights"]), centered=(True,True,False))
           .translate((nx,ny,P["notch_floor"]+e)).val())
    intrusion = body.intersect(air).Volume()
    landing = (cq.Workplane("XY").box(P["notch_width"]-2*e,P["wall"]-2*e,
                                      P["notch_floor"]-2*e, centered=(True,True,False))
               .translate((nx,ny+P["wall"]/2,e)).val())
    missing = landing.cut(body).Volume()
    results.append(("R6_notch", intrusion < tol and missing < tol,
                    f"open notch witness width={P['notch_width']-2*e:.2f} mm; material={intrusion:.6f}; landing missing={missing:.6f} mm3"))
    return results


CLEARANCES = []  # No mating parts: a cable size/fit is deliberately not certified.
IGNORE_CONTACT = []
