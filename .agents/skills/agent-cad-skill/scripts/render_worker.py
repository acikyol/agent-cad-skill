#!/usr/bin/env python3
"""Isolated VTK worker. Consume exported geometry, never re-run model.py."""
import json
import sys
from pathlib import Path

import cadquery as cq
import trimesh
from build import render, shape_to_trimesh, to_shape


def main():
    out, staging = map(Path, sys.argv[1:3])
    manifest = json.loads((out / 'manifest.json').read_text())
    meshes = [(shape_to_trimesh(to_shape(cq.importers.importStep(str(out / e['files']['step'])))),
               tuple(e['color']), 1.0) for e in manifest['parts']]
    meshes += [(shape_to_trimesh(to_shape(cq.importers.importStep(str(out / 'step_ref' / f'{name}.step')))),
                (0.3, 0.55, 0.9), 0.35) for name in manifest['references']]
    images = []
    for name, view in [('Assembly', (1, -1, 0.8)), ('Assembly_back', (-1, 1, -0.6))]:
        png = staging / f'{name}.png'
        render(meshes, str(png), view)
        images.append(png.name)
    for e in manifest['parts']:
        if 'stl' in e['files']:
            png = staging / f"{e['name']}_print.png"
            render([(trimesh.load(out / e['files']['stl'], force='mesh'), tuple(e['color']), 1.0)],
                   str(png), (1, -1, 0.9), (900, 700))
            images.append(png.name)
    (staging / 'images.json').write_text(json.dumps(images))


if __name__ == '__main__':
    main()
