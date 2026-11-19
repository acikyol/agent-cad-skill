#!/usr/bin/env python3
"""Build parts from model.py, verify them, render images and write a report.

Usage:
    <env-python> build.py <project>/model.py [--out <dir>] [--no-render]

Exit: 0 = numeric PASS only; 1 = numeric FAIL/NOT_VERIFIED; 2 = load/CLI error.
Overall/visual verification is separate; rendering never proves design validity.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import subprocess
import tempfile
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

AXES = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}
MESH_TOLS = [(0.02, 0.2), (0.05, 0.3), (0.1, 0.5)]
RENDER_WORKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "render_worker.py")


# ---------------------------------------------------------------- helpers
def load_model(path):
    spec = importlib.util.spec_from_file_location("model", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def to_shape(obj):
    """Workplane / Assembly / Shape -> single cq.Shape."""
    if isinstance(obj, cq.Assembly):
        return obj.toCompound()
    if isinstance(obj, cq.Workplane):
        vals = [v for v in obj.vals() if isinstance(v, cq.Shape)]
        if not vals:
            raise ValueError("Workplane contains no solid")
        return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    if isinstance(obj, cq.Shape):
        return obj
    raise TypeError(f"Unsupported shape type: {type(obj)}")


def solids_of(shape):
    s = shape.Solids()
    return s if s else [shape]


def bbox_overlap(a, b, pad=0.0):
    A, B = a.BoundingBox(), b.BoundingBox()
    return not (A.xmax + pad < B.xmin or B.xmax + pad < A.xmin or
                A.ymax + pad < B.ymin or B.ymax + pad < A.ymin or
                A.zmax + pad < B.zmin or B.zmax + pad < A.zmin)


def common_volume(a, b):
    """Intersection volume, solid by solid with bounding-box pre-filtering (fast for big STEP files)."""
    if not bbox_overlap(a, b):
        return 0.0
    vol = 0.0
    for sa in solids_of(a):
        if not bbox_overlap(sa, b):
            continue
        for sb in solids_of(b):
            if not bbox_overlap(sa, sb):
                continue
            intersection = sa.intersect(sb)
            if not intersection.isValid():
                raise ValueError('invalid intersection shape')
            v = intersection.Volume()
            if not math.isfinite(v) or v < 0:
                raise ValueError(f'invalid intersection volume: {v}')
            vol += v
    return vol


def min_distance(a, b):
    try:
        return a.distance(b)
    except Exception:
        from OCP.BRepExtrema import BRepExtrema_DistShapeShape
        d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
        d.Perform()
        return d.Value()


def to_print_pose(shape, rots):
    s = shape
    for axis, deg in rots or []:
        s = s.rotate((0, 0, 0), AXES[axis.upper()], deg)
    bb = s.BoundingBox()
    return s.translate(cq.Vector(-bb.center.x, -bb.center.y, -bb.zmin))


def write_stl_checked(shape, path):
    """Write STL with progressively coarser tolerances until it is watertight and the volume matches."""
    ref_vol = shape.Volume()
    last = None
    for tol, atol in MESH_TOLS:
        cq.exporters.export(shape, path, tolerance=tol, angularTolerance=atol)
        m = trimesh.load(path, force="mesh")
        dv = abs(m.volume - ref_vol) / ref_vol * 100 if ref_vol else 0
        ok = m.is_watertight and m.is_winding_consistent and dv < 0.2
        last = dict(watertight=bool(m.is_watertight), winding=bool(m.is_winding_consistent),
                    vol_diff_pct=round(float(dv), 3), tolerance=tol, faces=int(len(m.faces)), ok=bool(ok))
        if ok:
            return m, last
    return m, last


def _bridge_span(m, comp, lo, hi, tol=1.0):
    """Span of a bridge if the region is supported by walls coming up from below on two opposite ends, else None.
    A boundary edge is 'supported' when the neighbouring face outside the region goes below the edge (a wall)."""
    inset = np.zeros(len(m.faces), bool)
    inset[comp] = True
    adj, aedges = m.face_adjacency, m.face_adjacency_edges
    border = inset[adj[:, 0]] != inset[adj[:, 1]]
    mids, dirs = [], []
    for (f1, f2), ev in zip(adj[border], aedges[border]):
        nb = f2 if inset[f1] else f1
        a, b = m.vertices[ev[0]], m.vertices[ev[1]]
        if m.vertices[m.faces[nb]][:, 2].min() < (a[2] + b[2]) / 2 - 0.3:
            d = b - a
            ln = np.linalg.norm(d)
            if ln > 1e-9:
                mids.append((a + b) / 2)
                dirs.append(d / ln)
    if not mids:
        return None
    mids, dirs = np.array(mids), np.array(dirs)
    best = None
    for ax in (0, 1):
        # span along 'ax': supporting edges must be perpendicular to it and present at both ends
        perp = np.abs(dirs[:, ax]) < 0.5
        if not perp.any():
            continue
        p = mids[perp]
        if (p[:, ax] <= lo[ax] + tol).any() and (p[:, ax] >= hi[ax] - tol).any():
            span = float(hi[ax] - lo[ax])
            best = span if best is None else min(best, span)
    return best


def overhang_regions(m, deg=45.0, bed_eps=0.3, bridge_max=25.0, small_mm2=10.0):
    """Downward-facing regions flatter than 'deg' from horizontal, in print orientation."""
    n = m.face_normals
    c = m.triangles_center
    thr = -math.cos(math.radians(deg)) - 0.01          # an exact 45° face is not an overhang
    mask = (n[:, 2] < thr) & (c[:, 2] > bed_eps)
    idx = np.nonzero(mask)[0]
    if len(idx) == 0:
        return []
    sel = set(idx.tolist())
    adj = [e for e in m.face_adjacency if e[0] in sel and e[1] in sel]
    comps = trimesh.graph.connected_components(adj, nodes=idx, min_len=1)
    regions = []
    for comp in comps:
        comp = np.array(sorted(comp))
        area = float(m.area_faces[comp].sum())
        pts = m.triangles[comp].reshape(-1, 3)
        lo, hi = pts.min(0), pts.max(0)
        horiz = float((m.area_faces[comp] * (n[comp, 2] < -0.995)).sum()) / area if area else 0
        sx, sy, sz = (float(v) for v in (hi - lo))
        bspan = _bridge_span(m, comp, lo, hi) if horiz > 0.8 else None
        if bspan is not None and bspan <= bridge_max:
            kind = "bridge"
        elif bspan is not None:
            kind = "long bridge"           # supported both ends but longer than bridge_max -> sag risk
        elif max(sx, sy) <= 8.0 and sz <= 3.0:
            kind = "hole roof"             # top of a small horizontal hole (Ø ≲ 8): prints without support
        elif area < small_mm2:
            kind = "small"
        else:
            kind = "overhang"
        regions.append(dict(kind=kind, area_mm2=round(area, 1), z=[round(float(lo[2]), 2), round(float(hi[2]), 2)],
                            xy_size=[round(sx, 1), round(sy, 1)],
                            center=[round(float(v), 1) for v in (lo + hi) / 2]))
    regions.sort(key=lambda r: -r["area_mm2"])
    return regions


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:12]


# ---------------------------------------------------------------- rendering
def render(meshes, png, view=(1, -1, 0.8), size=(1400, 1000)):
    """meshes: [(trimesh, (r,g,b), opacity)] -> png (offscreen)."""
    import vtk
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray

    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    for m, col, op in meshes:
        pts = vtk.vtkPoints()
        pts.SetData(numpy_to_vtk(np.ascontiguousarray(m.vertices, dtype=np.float64), deep=True))
        offsets = np.arange(0, 3 * len(m.faces) + 1, 3, dtype=np.int64)
        conn = np.ascontiguousarray(m.faces, dtype=np.int64).ravel()
        cells = vtk.vtkCellArray()
        cells.SetData(numpy_to_vtkIdTypeArray(offsets, deep=True), numpy_to_vtkIdTypeArray(conn, deep=True))
        poly = vtk.vtkPolyData()
        poly.SetPoints(pts)
        poly.SetPolys(cells)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(poly)
        normals.SetFeatureAngle(30)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*col)
        actor.GetProperty().SetOpacity(op)
        ren.AddActor(actor)
        edges = vtk.vtkFeatureEdges()
        edges.SetInputConnection(normals.GetOutputPort())
        edges.BoundaryEdgesOn(); edges.FeatureEdgesOn(); edges.SetFeatureAngle(35)
        edges.ManifoldEdgesOff(); edges.NonManifoldEdgesOff()
        em = vtk.vtkPolyDataMapper(); em.SetInputConnection(edges.GetOutputPort()); em.ScalarVisibilityOff()
        ea = vtk.vtkActor(); ea.SetMapper(em); ea.GetProperty().SetColor(0.15, 0.15, 0.15)
        ea.GetProperty().SetOpacity(min(1.0, op + 0.2))
        ren.AddActor(ea)
    cam = ren.GetActiveCamera()
    cam.SetPosition(*view)
    cam.SetFocalPoint(0, 0, 0)
    cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    cam.Zoom(1.1)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(*size)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()
    wr = vtk.vtkPNGWriter()
    wr.SetFileName(png)
    wr.SetInputConnection(w2i.GetOutputPort())
    wr.Write()


def shape_to_trimesh(shape, tol=0.1, atol=0.3):
    verts, tris = shape.tessellate(tol, atol)
    v = np.array([[p.x, p.y, p.z] for p in verts])
    return trimesh.Trimesh(v, np.array(tris), process=False)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--render-timeout", type=float, default=60.0)
    a = ap.parse_args()
    if not math.isfinite(a.render_timeout) or a.render_timeout <= 0:
        ap.error("--render-timeout must be finite and positive")

    model_path = os.path.abspath(a.model)
    proj = os.path.dirname(model_path)
    out = os.path.abspath(a.out or os.path.join(proj, "output"))
    os.chdir(proj)
    for sub in ("step", "stl", "dxf", "render"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    t0 = time.time()
    try:
        mod = load_model(model_path)
        P = getattr(mod, "P", {})
        parts = mod.parts(P)
        refs = mod.references(P) if hasattr(mod, "references") else []
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"MODEL FAILED TO LOAD: {e}")
        sys.exit(2)

    bed = P.get("bed")
    if isinstance(bed, (int, float)):
        bed = (bed, bed)
    deg = float(P.get("overhang_deg", 45))
    clearances = getattr(mod, "CLEARANCES", [])
    ignore = {tuple(sorted(p)) for p in getattr(mod, "IGNORE_CONTACT", [])}

    old_manifest = {}
    mpath = os.path.join(out, "manifest.json")
    if os.path.exists(mpath):
        try:
            old_manifest = {p["name"]: p for p in json.load(open(mpath))["parts"]}
        except Exception:
            pass

    fails, report, manifest = [], [], []
    shapes = {}

    for p in parts:
        name = p["name"]
        if name in shapes:
            fails.append(f'duplicate shape name: {name}; collision coverage incomplete')
            continue
        proc = p.get("process", "none")
        entry = dict(name=name, process=proc, qty=p.get("qty", 1), group=p.get("group", "Parts"),
                     color=p.get("color", (0.7, 0.7, 0.72)), files={})
        try:
            s = to_shape(p["shape"])
        except Exception as e:
            fails.append(f"{name}: could not build shape ({e})")
            report.append(dict(name=name, error=str(e)))
            continue
        shapes[name] = s
        r = dict(name=name, process=proc, valid=bool(s.isValid()), volume_mm3=round(float(s.Volume()), 1))
        if not r["valid"] or r["volume_mm3"] <= 0:
            fails.append(f"{name}: invalid solid (isValid={r['valid']}, volume={r['volume_mm3']})")

        step = os.path.join(out, "step", f"{name}.step")
        cq.exporters.export(s, step)
        entry["files"]["step"] = os.path.relpath(step, out)

        if proc == "fdm":
            ps = to_print_pose(s, p.get("print_rot", []))
            bb = ps.BoundingBox()
            r["print_size"] = [round(float(bb.xlen), 1), round(float(bb.ylen), 1), round(float(bb.zlen), 1)]
            stl = os.path.join(out, "stl", f"{name}.stl")
            m, mesh_info = write_stl_checked(ps, stl)
            r["mesh"] = mesh_info
            if not mesh_info["ok"]:
                fails.append(f"{name}: STL mesh problem {mesh_info}")
            if bed and (bb.xlen > bed[0] or bb.ylen > bed[1]):
                fails.append(f"{name}: does not fit the bed {r['print_size'][:2]} > {list(bed)}")
            regs = overhang_regions(m, deg, bridge_max=float(P.get("bridge_max", 25)))
            r["overhang"] = regs
            over = sum(x["area_mm2"] for x in regs if x["kind"] in ("overhang", "long bridge"))
            r["overhang_mm2"] = round(over, 1)
            if over > p.get("allow_overhang_mm2", 0):
                fails.append(f"{name}: needs supports, overhang {over:.0f} mm² (allowed {p.get('allow_overhang_mm2', 0)})")
            entry["files"]["stl"] = os.path.relpath(stl, out)
            entry["hash"] = sha1(stl)
            entry["print_rot"] = p.get("print_rot", [])
        if p.get("dxf") is not None:
            dxf = os.path.join(out, "dxf", f"{name}.dxf")
            cq.exporters.export(p["dxf"], dxf)
            entry["files"]["dxf"] = os.path.relpath(dxf, out)
            entry.setdefault("hash", sha1(dxf))
        entry.setdefault("hash", sha1(step))
        prev = old_manifest.get(name)
        entry["changed"] = (prev is None) or (prev.get("hash") != entry["hash"])
        manifest.append(entry)
        report.append(r)

    ref_shapes = {}
    for rf in refs:
        try:
            if rf['name'] in shapes or rf['name'] in ref_shapes:
                raise ValueError(f"duplicate shape name: {rf['name']}; collision coverage incomplete")
            ref_shapes[rf["name"]] = to_shape(rf["shape"])
            os.makedirs(os.path.join(out, "step_ref"), exist_ok=True)
            cq.exporters.export(ref_shapes[rf["name"]], os.path.join(out, "step_ref", f"{rf['name']}.step"))
        except Exception as e:
            fails.append(f"reference {rf.get('name')}: failed to load ({e})")

    # collisions
    allshp = list(shapes.items()) + list(ref_shapes.items())
    collisions = []
    collision_checks = []
    unverified = []
    for i in range(len(allshp)):
        for j in range(i + 1, len(allshp)):
            na, sa = allshp[i]
            nb, sb = allshp[j]
            if na in ref_shapes and nb in ref_shapes:
                continue
            if tuple(sorted((na, nb))) in ignore:
                collision_checks.append(dict(a=na, b=nb, status="NOT_VERIFIED", reason="IGNORE_CONTACT bypass"))
                unverified.append(f"collision {na} <-> {nb}: ignored, not verified")
                continue
            try:
                v = common_volume(sa, sb)
                if not math.isfinite(v) or v < 0:
                    raise ValueError(f"invalid intersection volume: {v}")
            except Exception as e:
                collision_checks.append(dict(a=na, b=nb, status="NOT_VERIFIED", reason=str(e)))
                fails.append(f"collision check failed: {na} <-> {nb}: {e}")
                unverified.append(f"collision {na} <-> {nb}: {e}")
                continue
            collision_checks.append(dict(a=na, b=nb, status="FAIL" if v > 0.01 else "PASS", volume_mm3=v))
            if v > 0.01:
                collisions.append(dict(a=na, b=nb, volume_mm3=round(v, 2)))
                fails.append(f"collision: {na} <-> {nb} ({v:.2f} mm³)")

    # clearances
    clr = []
    every = {**shapes, **ref_shapes}
    for na, nb, need in clearances:
        if na not in every or nb not in every:
            fails.append(f"clearance check: '{na}' or '{nb}' not found")
            continue
        try:
            d = min_distance(every[na], every[nb])
            if not math.isfinite(d) or d < 0 or not math.isfinite(need) or need < 0:
                raise ValueError('invalid distance or clearance threshold')
        except Exception as e:
            clr.append(dict(a=na, b=nb, mm=None, need=need, ok=False, status='NOT_VERIFIED', reason=str(e)))
            fails.append(f'clearance check failed: {na} <-> {nb}: {e}')
            continue
        clr.append(dict(a=na, b=nb, mm=round(d, 3), need=need, ok=d >= need, status='PASS' if d >= need else 'FAIL'))
        if d < need:
            fails.append(f"clearance too small: {na} <-> {nb} = {d:.2f} mm (need {need})")

    # user requirement checks
    reqs = []
    requirements_error = None
    if hasattr(mod, "checks"):
        try:
            for item in mod.checks(P, every) or []:
                code, ok, msg = item[0], bool(item[1]), str(item[2]) if len(item) > 2 else ""
                reqs.append(dict(id=code, passed=ok, detail=msg))
                if not ok:
                    fails.append(f"requirement {code}: {msg}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            fails.append(f"checks() failed to run: {e}")
            requirements_error = str(e)

    # assembly STEP
    try:
        comp = cq.Compound.makeCompound(list(shapes.values()))
        cq.exporters.export(comp, os.path.join(out, "step", "Assembly.step"))
    except Exception as e:
        fails.append(f"Assembly.step could not be written: {e}")

    # images
    renders = []

    # report
    numeric_status = "FAIL" if fails else "NOT_VERIFIED" if unverified else "PASS"
    verification = dict(requirements=dict(status=("FAIL" if any(not r["passed"] for r in reqs) else "PASS") if reqs else "NOT_VERIFIED"),
                        visual=dict(status="NOT_VERIFIED", reason="Images are not visual inspection"),
                        clearances=dict(status=("FAIL" if any(not c["ok"] for c in clr) else "PASS") if clr else "NOT_VERIFIED"))
    status = "FAIL" if fails else "NOT_VERIFIED"
    if requirements_error:
        verification['requirements'] = dict(status='NOT_VERIFIED', reason=requirements_error)
    data = dict(model=model_path, seconds=round(time.time() - t0, 1), passed=numeric_status == "PASS", failures=fails,
                status=status, numeric_status=numeric_status, verification=verification, unverified=unverified,
                collision_checks=collision_checks,
                parts=report, collisions=collisions, clearances=clr, requirements=reqs, images=renders)
    json.dump(data, open(os.path.join(out, "report.json"), "w"), ensure_ascii=False, indent=2)
    json.dump(dict(parts=manifest, references=list(ref_shapes)), open(mpath, "w"), ensure_ascii=False, indent=2)

    L = [f"# Build report — {os.path.basename(proj)}", "",
         f"Status: **{status}**; numeric: **{numeric_status}** ({data['seconds']} s)", "",
         "Visual inspection: NOT_VERIFIED. Requirements/clearances without results: NOT_VERIFIED.", ""]
    L += [f"- NOT_VERIFIED: {s}" for s in unverified]
    if fails:
        L += ["## Problems", ""] + [f"- {f}" for f in fails] + [""]
    L += ["## Parts", "", "| Part | Process | Qty | Size (print) | Mesh | Overhang mm² | Changed |", "|---|---|---|---|---|---|---|"]
    man = {e["name"]: e for e in manifest}
    for r in report:
        e = man.get(r["name"], {})
        size = " × ".join(str(v) for v in r.get("print_size", [])) or "-"
        mesh = "-" if "mesh" not in r else ("clean" if r["mesh"]["ok"] else "PROBLEM")
        L.append(f"| {r['name']} | {r.get('process', '-')} | {e.get('qty', '-')} | {size} | {mesh} | "
                 f"{r.get('overhang_mm2', '-')} | {'yes' if e.get('changed') else 'no'} |")
    for r in report:
        if r.get("overhang"):
            L += ["", f"### {r['name']} — downward-facing regions (print orientation)", ""]
            for x in r["overhang"][:12]:
                L.append(f"- {x['kind']}: {x['area_mm2']} mm², z {x['z']}, size {x['xy_size']}, center {x['center']}")
    if reqs:
        L += ["", "## Requirements", "", "| ID | Result | Detail |", "|---|---|---|"]
        L += [f"| {r['id']} | {'✓' if r['passed'] else '✗ FAILED'} | {r['detail']} |" for r in reqs]
    if collisions or clr:
        L += ["", "## Collisions / clearances", ""]
        L += [f"- COLLISION {c['a']} <-> {c['b']}: {c['volume_mm3']} mm³" for c in collisions]
        L += [f"- {c['a']} <-> {c['b']}: {c['mm']} mm (need {c['need']}) {'✓' if c['ok'] else '✗'}" for c in clr]
    elif len(allshp) > 1 and not unverified:
        L += ["", "No collisions."]
    if renders:
        L += ["", "## Images", ""] + [f"![{r}]({r})" for r in renders]
    open(os.path.join(out, "report.md"), "w").write("\n".join(L) + "\n")

    data['rendering'] = dict(status="NOT_VERIFIED", reason="disabled by --no-render")
    if not a.no_render:
        with tempfile.TemporaryDirectory(prefix="render-", dir=out) as staging:
            log = os.path.join(out, "render.log")
            with open(log, "w") as stream:
                try:
                    result = subprocess.run([sys.executable, RENDER_WORKER, out, staging],
                                            stdout=stream, stderr=stream, timeout=a.render_timeout)
                    data['rendering'] = dict(status="NOT_VERIFIED", returncode=result.returncode,
                                             reason="renderer failed; see render.log")
                    if result.returncode == 0:
                        try:
                            from PIL import Image
                            names = json.loads((Path(staging) / 'images.json').read_text())
                            expected = ['Assembly.png', 'Assembly_back.png'] + [f"{e['name']}_print.png" for e in manifest if 'stl' in e['files']]
                            if sorted(names) != sorted(expected):
                                raise ValueError('incomplete image set')
                            for name in names:
                                if Path(name).name != name:
                                    raise ValueError('invalid image path')
                                with Image.open(Path(staging) / name) as image:
                                    if image.format != 'PNG':
                                        raise ValueError('not PNG')
                                    image.verify()
                            for name in names:
                                os.replace(Path(staging) / name, Path(out) / 'render' / name)
                            data['images'] = [f'render/{name}' for name in names]
                            data['rendering'] = dict(status="PASS", returncode=0, reason="Images generated; visual inspection still required")
                        except Exception as e:
                            data['rendering']['reason'] = f'invalid renderer output: {e}'
                except subprocess.TimeoutExpired:
                    data['rendering'] = dict(status="NOT_VERIFIED", reason="timeout")
                except OSError as e:
                    data['rendering'] = dict(status="NOT_VERIFIED", reason=str(e))
    json.dump(data, open(os.path.join(out, "report.json"), "w"), ensure_ascii=False, indent=2)
    with open(os.path.join(out, "report.md"), "a") as stream:
        stream.write(f"\nRendering: {data['rendering']}\n")
        stream.write(''.join(f"\n![{image}]({image})\n" for image in data['images']))

    print("\n".join(L[:8 + len(fails)]))
    print(f"\nReport: {os.path.join(out, 'report.md')}")
    sys.exit(0 if numeric_status == "PASS" else 1)


if __name__ == "__main__":
    main()
