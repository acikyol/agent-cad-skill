"""End-to-end geometric acceptance test; run with repository .venv Python."""
import importlib.util
from pathlib import Path
import unittest
import cadquery as cq


class IskeleTest(unittest.TestCase):
    def test_connected_open_organizer(self):
        path = Path(__file__).with_name("model.py")
        self.assertTrue(path.exists(), "Iskele model has not been implemented")
        spec = importlib.util.spec_from_file_location("iskele", path)
        assert spec is not None and spec.loader is not None
        model = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(model)
        entries = model.parts(model.P)
        self.assertEqual(len(entries), 1)
        shape = entries[0]["shape"].val()
        self.assertTrue(shape.isValid())
        self.assertEqual(len(shape.Solids()), 1)
        bb = shape.BoundingBox()
        for measured, expected in zip((bb.xlen, bb.ylen, bb.zlen), (180, 94, 100)):
            self.assertAlmostEqual(measured, expected, places=4)
        # Independent fixed-coordinate witnesses, not parameter assertions.
        # Each empty prism runs through the entire upward access path.
        for x, y, z, w, d, h in [(-64, 22, 5, 26, 26, 100),
                                 (-22, 22, 5, 26, 26, 100),
                                 (43, 0, 5, 62, 62, 100),
                                 (58, -39, 9, 9, 10, 100)]:
            probe = cq.Workplane("XY").box(w, d, h, centered=(True, True, False)).translate((x, y, z)).val()
            self.assertLess(shape.intersect(probe).Volume(), 0.001)
        for point in [(-64,22,2), (-22,22,2), (43,0,2), (58,-38,7), (-80,22,50), (-38,22,50)]:
            self.assertTrue(shape.isInside(point), str(point))
        results = model.checks(model.P, {"Iskele": shape})
        self.assertTrue(results)
        self.assertTrue(all(ok for _, ok, _ in results), results)


if __name__ == "__main__":
    unittest.main(verbosity=2)
