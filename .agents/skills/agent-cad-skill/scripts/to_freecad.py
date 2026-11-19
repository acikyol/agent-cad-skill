#!/usr/bin/env python3
"""OPTIONAL: convert build.py output into a FreeCAD document (.FCStd).

Usage:  python to_freecad.py <output_dir> [<target.FCStd>]
Runs FreeCAD's command-line build (freecadcmd); never touches an open FreeCAD window.
If freecadcmd is not found, set FREECADCMD to its path. If FreeCAD is not installed this step is skipped.
"""
import glob
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def find_freecadcmd():
    cands = [os.environ.get("FREECADCMD"), shutil.which("freecadcmd"), shutil.which("FreeCADCmd"),
             "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"]
    cands += glob.glob(r"C:\Program Files\FreeCAD*\bin\FreeCADCmd.exe")
    cands += glob.glob("/usr/bin/freecadcmd*") + glob.glob("/snap/bin/freecad.cmd")
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


def main():
    out = os.path.abspath(sys.argv[1])
    target = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(
        out, os.path.basename(os.path.dirname(out)) + ".FCStd")
    fc = find_freecadcmd()
    if not fc:
        print("FreeCAD (freecadcmd) not found — this step is optional and was skipped. "
              "Set FREECADCMD=<path> to use it, or open the STEP files in FreeCAD manually.")
        sys.exit(3)
    if os.path.exists(target):
        bak = target[:-6] + time.strftime("_backup_%Y%m%d-%H%M%S") + ".FCStd"
        shutil.copy2(target, bak)
        print("backup:", bak)
    # A fresh staging path prevents an existing target from proving success.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='freecad-', dir=os.path.dirname(target)) as staging:
        fresh = os.path.join(staging, os.path.basename(target))
        env = dict(os.environ, FCI_OUT=out, FCI_FCSTD=fresh)
        r = subprocess.run([fc, os.path.join(HERE, "fc_import.py")], env=env, capture_output=True, text=True)
        lines = [l for l in (r.stdout + r.stderr).splitlines() if "FCSTD_OK" in l or "rror" in l or "Traceback" in l]
        print("\n".join(lines))
        if r.returncode == 0 and os.path.isfile(fresh) and os.path.getsize(fresh) > 0 and 'FCSTD_OK' in r.stdout:
            os.replace(fresh, target)
            print("FreeCAD document:", target)
        else:
            print(f"FreeCAD export failed (exit {r.returncode}); original target preserved")
            sys.exit(1)


if __name__ == "__main__":
    main()
