#!/usr/bin/env python3
"""Create the CadQuery environment (Windows / macOS / Linux).

Usage:  python setup_env.py [<env_dir>]      (default: <skill>/.venv — one shared environment)
Uses uv if available (fast, no ensurepip needed), otherwise python -m venv + pip.
Python version: CQ_PYVER environment variable (default 3.12; CadQuery wheels are most reliable there).
Prints the environment's python path at the end: use it for every later command.
"""
import os
import shutil
import subprocess
import sys

PKGS = ['-r', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'requirements.lock')]


def venv_python(venv):
    return os.path.join(venv, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv, "bin", "python")


def run(cmd):
    print("$", " ".join(cmd))
    subprocess.check_call(cmd)


def main():
    default = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv")
    venv = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else default)
    pyver = os.environ.get("CQ_PYVER", "3.12")
    vpy = venv_python(venv)
    uv = shutil.which("uv")
    if uv:
        if not os.path.exists(vpy):
            run([uv, "venv", "-q", "--python", pyver, venv])
        run([uv, "pip", "install", "-q", "--python", vpy] + PKGS)
    else:
        if not os.path.exists(vpy):
            cand = shutil.which(f"python{pyver}") or sys.executable
            run([cand, "-m", "venv", venv])
        run([vpy, "-m", "pip", "install", "-q", "--upgrade", "pip"])
        run([vpy, "-m", "pip", "install", "-q"] + PKGS)
    r = subprocess.run([vpy, "-c",
        "import sys,cadquery,vtk,trimesh;print(sys.executable);print('CadQuery',cadquery.__version__);"
        "print('VTK',vtk.vtkVersion.GetVTKVersion());print('trimesh',trimesh.__version__)"],
        capture_output=True, text=True)
    if r.returncode != 0:
        err = r.stderr.strip().splitlines()
        print(err[-1] if err else "import failed", file=sys.stderr)
        if "libGL" in r.stderr or "libEGL" in r.stderr:
            # minimal Linux images lack the OpenGL runtime the geometry kernel links against
            print("Missing system OpenGL library. On Debian/Ubuntu run:  sudo apt-get install -y libgl1 libegl1\n"
                  "then run this script again (packages already installed are kept).", file=sys.stderr)
        sys.exit(1)
    print(r.stdout.strip())
    print(f"ENV_PYTHON={vpy}")


if __name__ == "__main__":
    main()
