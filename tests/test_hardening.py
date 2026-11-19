"""Fail-closed regressions; run with unittest discovery."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "agent-cad-skill"
sys.path.insert(0, str(SKILL / "scripts"))
import build


def setUpModule():
    (ROOT / 'output').mkdir(exist_ok=True)


class EnvironmentTests(unittest.TestCase):
    def test_setup_installs_tested_lock(self):
        import setup_env
        self.assertEqual(setup_env.PKGS, ['-r', str(SKILL/'requirements.lock')])


class CollisionTests(unittest.TestCase):
    def test_invalid_boolean_result_is_not_zero(self):
        from unittest.mock import patch
        shape = build.cq.Workplane('XY').box(2, 2, 2).val()
        class Invalid:
            def isValid(self): return False
            def Volume(self): return 0.0
        with patch.object(build.cq.Solid, 'intersect', return_value=Invalid()):
            with self.assertRaisesRegex(ValueError, 'invalid intersection'):
                build.common_volume(shape, shape)

    def test_real_geometry_touch_separation_and_overlap(self):
        shape = build.cq.Workplane('XY').box(2, 2, 2).val()
        self.assertAlmostEqual(build.common_volume(shape, shape.translate((3,0,0))), 0)
        self.assertAlmostEqual(build.common_volume(shape, shape.translate((2,0,0))), 0)
        self.assertAlmostEqual(build.common_volume(shape, shape.translate((1,0,0))), 4)

    def test_boolean_exception_is_not_zero_volume(self):
        class Broken:
            def BoundingBox(self):
                return build.cq.Workplane('XY').box(1, 1, 1).val().BoundingBox()
            def Solids(self):
                return [self]
            def intersect(self, other):
                raise RuntimeError('boolean failed')
        with self.assertRaisesRegex(RuntimeError, 'boolean failed'):
            build.common_volume(Broken(), Broken())


class ReportTests(unittest.TestCase):
    def test_collision_engine_failure_preserves_failure_report(self):
        import tempfile, subprocess, json
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
            model = Path(tmp) / 'model.py'
            model.write_text("import cadquery as cq\nimport __main__\ndef broken(*a): raise RuntimeError('kernel failure')\n__main__.common_volume=broken\ndef parts(P):\n return [dict(name=n, shape=cq.Workplane('XY').box(2,2,2)) for n in ['A','B']]\n")
            result = subprocess.run([sys.executable, str(SKILL/'scripts/build.py'), str(model), '--out', tmp, '--no-render'], capture_output=True, text=True)
            self.assertTrue((Path(tmp)/'report.json').exists(), result.stderr)
            rep = json.loads((Path(tmp)/'report.json').read_text())
            self.assertEqual(rep['status'], 'FAIL')
            self.assertEqual(rep['collision_checks'][0]['status'], 'NOT_VERIFIED')
            self.assertIn('kernel failure', str(rep['failures']))
            self.assertEqual(result.returncode, 1)

    def test_renderer_crash_keeps_numeric_report(self):
        import tempfile, subprocess, json
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
            tmp = Path(tmp)
            worker = tmp/'worker.py'
            worker.write_text("import json, pathlib, sys, os, signal\np=pathlib.Path(sys.argv[1])\nr=json.loads((p/'report.json').read_text())\nassert r['numeric_status']=='PASS'\nassert (p/'report.md').exists()\nos.kill(os.getpid(), signal.SIGKILL)\n")
            model = tmp/'model.py'
            model.write_text(f"import cadquery as cq\nimport __main__\n__main__.RENDER_WORKER={str(worker)!r}\ndef parts(P): return [dict(name='A',shape=cq.Workplane('XY').box(2,2,2))]\n")
            result = subprocess.run([sys.executable, str(SKILL/'scripts/build.py'), str(model), '--out', str(tmp)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            rep = json.loads((tmp/'report.json').read_text())
            self.assertEqual(rep['numeric_status'], 'PASS')
            self.assertEqual(rep['rendering']['status'], 'NOT_VERIFIED')
            self.assertEqual(rep['rendering']['returncode'], -9)
            self.assertEqual(rep['images'], [])

    def test_renderer_timeout_keeps_report(self):
        import tempfile, subprocess, json
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
            tmp = Path(tmp)
            worker = tmp/'worker.py'
            worker.write_text('import time\ntime.sleep(20)\n')
            model = tmp/'model.py'
            model.write_text(f"import cadquery as cq\nimport __main__\n__main__.RENDER_WORKER={str(worker)!r}\ndef parts(P): return [dict(name='A',shape=cq.Workplane('XY').box(2,2,2))]\n")
            result = subprocess.run([sys.executable, str(SKILL/'scripts/build.py'), str(model), '--out', str(tmp), '--render-timeout', '0.1'], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            rep = json.loads((tmp/'report.json').read_text())
            self.assertEqual(rep['rendering']['reason'], 'timeout')
            self.assertEqual(rep['rendering']['status'], 'NOT_VERIFIED')

    def test_render_worker_exports_all_views_without_reloading_model(self):
        import tempfile, subprocess, json
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
            tmp = Path(tmp)
            result = subprocess.run([sys.executable, str(SKILL/'scripts/build.py'), str(ROOT/'examples/bracket/model.py'), '--out', str(tmp), '--no-render'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            staging = tmp/'staging'
            staging.mkdir()
            # Replace only the unavailable graphics backend, not job preparation.
            runner = "import build, runpy, sys; from PIL import Image; build.render=lambda meshes,png,*args: Image.new('RGB',(2,2)).save(png); sys.argv=['render_worker',sys.argv[1],sys.argv[2]]; runpy.run_path(sys.argv[3] if len(sys.argv)>3 else '.agents/skills/agent-cad-skill/scripts/render_worker.py',run_name='__main__')"
            result = subprocess.run([sys.executable, '-c', runner, str(tmp), str(staging)], cwd=ROOT, env={**__import__('os').environ, 'PYTHONPATH': str(SKILL/'scripts')}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            images = json.loads((staging/'images.json').read_text())
            self.assertIn('Assembly.png', images)
            self.assertIn('Assembly_back.png', images)
            self.assertTrue(any(n.endswith('_print.png') for n in images))
            self.assertTrue(all((staging/n).stat().st_size > 0 for n in images))

    def test_successful_renderer_publishes_only_fresh_complete_images(self):
        import tempfile, subprocess, json
        for produce in (True, False):
            with self.subTest(produce=produce), tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
                tmp = Path(tmp)
                (tmp/'render').mkdir()
                (tmp/'render/Assembly.png').write_bytes(b'stale')
                worker = tmp/'worker.py'
                worker.write_text("import sys,json\nfrom pathlib import Path\nfrom PIL import Image\np=Path(sys.argv[2])\n" + ("names=['Assembly.png','Assembly_back.png']\nfor n in names: Image.new('RGB',(2,2)).save(p/n)\n(p/'images.json').write_text(json.dumps(names))\n" if produce else ''))
                model = tmp/'model.py'
                model.write_text(f"import cadquery as cq\nimport __main__\n__main__.RENDER_WORKER={str(worker)!r}\ndef parts(P): return [dict(name='A',shape=cq.Workplane('XY').box(2,2,2))]\n")
                result = subprocess.run([sys.executable, str(SKILL/'scripts/build.py'), str(model), '--out', str(tmp)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                rep = json.loads((tmp/'report.json').read_text())
                self.assertEqual(rep['rendering']['status'], 'PASS' if produce else 'NOT_VERIFIED')
                self.assertEqual(len(rep['images']), 2 if produce else 0)
                self.assertEqual(rep['verification']['visual']['status'], 'NOT_VERIFIED')

    def test_clearance_engine_failure_is_reported(self):
        import tempfile, subprocess, json
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
            tmp = Path(tmp)
            model = tmp/'model.py'
            model.write_text("import cadquery as cq\nimport __main__\ndef broken(*a): raise RuntimeError('distance failed')\n__main__.min_distance=broken\nCLEARANCES=[('A','B',1)]\ndef parts(P): return [dict(name=n,shape=cq.Workplane('XY').box(2,2,2).translate((i*5,0,0))) for i,n in enumerate(['A','B'])]\n")
            result = subprocess.run([sys.executable, str(SKILL/'scripts/build.py'), str(model), '--out', str(tmp), '--no-render'], capture_output=True, text=True)
            self.assertTrue((tmp/'report.json').exists(), result.stderr)
            rep = json.loads((tmp/'report.json').read_text())
            self.assertEqual(result.returncode, 1)
            self.assertEqual(rep['status'], 'FAIL')
            self.assertEqual(rep['clearances'][0]['status'], 'NOT_VERIFIED')

    def test_partial_requirements_are_not_marked_verified(self):
        import tempfile, subprocess, json
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
            tmp = Path(tmp)
            model = tmp/'model.py'
            model.write_text("import cadquery as cq\ndef parts(P): return [dict(name='A',shape=cq.Workplane('XY').box(2,2,2))]\ndef checks(P,shapes):\n yield ('first',True,'ok')\n raise RuntimeError('incomplete requirements')\n")
            result = subprocess.run([sys.executable, str(SKILL/'scripts/build.py'), str(model), '--out', str(tmp), '--no-render'], capture_output=True, text=True)
            rep = json.loads((tmp/'report.json').read_text())
            self.assertEqual(result.returncode, 1)
            self.assertEqual(rep['verification']['requirements']['status'], 'NOT_VERIFIED')

    def test_duplicate_names_cannot_hide_collision(self):
        import tempfile, subprocess, json
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
            tmp = Path(tmp)
            model = tmp/'model.py'
            model.write_text("import cadquery as cq\ndef parts(P): return [dict(name='A',shape=cq.Workplane('XY').box(2,2,2)) for i in range(2)]\n")
            result = subprocess.run([sys.executable, str(SKILL/'scripts/build.py'), str(model), '--out', str(tmp), '--no-render'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            rep = json.loads((tmp/'report.json').read_text())
            self.assertEqual(rep['numeric_status'], 'FAIL')
            self.assertIn('duplicate', str(rep['failures']))

    def test_ignored_collision_and_missing_checks_are_not_verified(self):
        import tempfile
        import subprocess
        import json
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
            model = Path(tmp) / 'model.py'
            model.write_text("import cadquery as cq\nIGNORE_CONTACT=[('A','B')]\ndef parts(P):\n return [dict(name=n, shape=cq.Workplane('XY').box(2,2,2)) for n in ['A','B']]\n")
            result = subprocess.run([sys.executable, str(SKILL/'scripts/build.py'), str(model), '--out', tmp, '--no-render'], capture_output=True, text=True)
            rep = json.loads((Path(tmp)/'report.json').read_text())
            self.assertEqual(rep.get('status'), 'NOT_VERIFIED')
            self.assertEqual(rep['numeric_status'], 'NOT_VERIFIED')
            self.assertFalse(rep['passed'])
            self.assertEqual(result.returncode, 1)
            self.assertEqual(rep['collision_checks'][0]['status'], 'NOT_VERIFIED')
            self.assertEqual(rep['verification']['requirements']['status'], 'NOT_VERIFIED')


class FreeCADTests(unittest.TestCase):
    def test_stale_target_cannot_mask_failed_export(self):
        import tempfile, subprocess, os
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as tmp:
            tmp = Path(tmp)
            target = tmp/'model.FCStd'
            target.write_bytes(b'original')
            fake = tmp/'freecadcmd'
            fake.write_text('#!/bin/sh\nexit 1\n')
            fake.chmod(0o700)
            result = subprocess.run([sys.executable, str(SKILL/'scripts/to_freecad.py'), str(tmp), str(target)], env={**os.environ, 'FREECADCMD':str(fake)}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            fake.write_text('#!/bin/sh\necho FCSTD_OK\nexit 0\n')
            result = subprocess.run([sys.executable, str(SKILL/'scripts/to_freecad.py'), str(tmp), str(target)], env={**os.environ, 'FREECADCMD':str(fake)}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertEqual(target.read_bytes(), b'original')


if __name__ == '__main__':
    unittest.main()
