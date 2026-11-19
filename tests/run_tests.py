#!/usr/bin/env python3
"""Self-tests: build every example and compare with the expected result.
Run with the skill environment's python:  <skill>/.venv/bin/python tests/run_tests.py
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, ".agents", "skills", "agent-cad-skill", "scripts", "build.py")

CASES = {
    "bracket": dict(exit=0, kinds={"hole roof"}),
    "collisions": dict(exit=1, kinds={"long bridge"}, collision=("Box", "Board"), clearance_fail=("Lid", "Box"),
                       files=["dxf/LaserFrame.dxf", "step_ref/Board.step", "step/Assembly.step"]),
    "bridges": dict(exit=1, kinds={"bridge", "long bridge", "overhang"}),
}


def main():
    failed = 0
    scratch = os.path.join(ROOT, 'output')
    os.makedirs(scratch, exist_ok=True)
    for name, exp in CASES.items():
        model = os.path.join(ROOT, "examples", name, "model.py")
        with tempfile.TemporaryDirectory(dir=scratch) as out:
            r = subprocess.run([sys.executable, BUILD, model, "--out", out, "--no-render"],
                               capture_output=True, text=True)
            problems = []
            if r.returncode != exp["exit"]:
                problems.append(f"exit {r.returncode} != {exp['exit']}")
            try:
                rep = json.load(open(os.path.join(out, "report.json")))
            except Exception:
                problems.append("report.json missing")
                rep = {}
            kinds = {x["kind"] for p in rep.get("parts", []) for x in p.get("overhang", [])}
            if kinds != exp["kinds"]:
                problems.append(f"overhang kinds {sorted(kinds)} != {sorted(exp['kinds'])}")
            if "collision" in exp and not any({c["a"], c["b"]} == set(exp["collision"]) for c in rep.get("collisions", [])):
                problems.append(f"collision {exp['collision']} not detected")
            if "clearance_fail" in exp and not any({c["a"], c["b"]} == set(exp["clearance_fail"]) and not c["ok"]
                                                   for c in rep.get("clearances", [])):
                problems.append(f"clearance failure {exp['clearance_fail']} not detected")
            for f in exp.get("files", []):
                if not os.path.exists(os.path.join(out, f)):
                    problems.append(f"missing output {f}")
            if problems:
                failed += 1
                print(f"FAIL {name}: " + "; ".join(problems))
                print(r.stdout[-800:], r.stderr[-800:])
            else:
                print(f"ok   {name}")
    print("all tests passed" if not failed else f"{failed} test(s) failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
