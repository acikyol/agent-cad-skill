#!/usr/bin/env python3
"""agent-cad-skill installer — global or per-project, for any coding agent.

The discoverable skill in this repository is `.agents/skills/agent-cad-skill`.
A full git checkout is preserved; only that skill payload is copied elsewhere.
    python install.py --global [--agents claude,codex,antigravity] [--with-env]
      - the skill lives in ~/.agent-cad-skill (override with AGENT_CAD_SKILL_HOME)
      - registers with agents that have a global config file:
          claude       ~/.claude/skills/agent-cad-skill          (symlink, copy on Windows)
          codex        ~/.codex/AGENTS.md                     (pointer block)
          antigravity  ~/.gemini/config/skills/agent-cad-skill  (symlink; Antigravity CLI `agy` + App)
        "gemini" is accepted as an alias of "antigravity" (Gemini CLI was replaced by Antigravity CLI).
      - Cursor / Zed / Copilot have no global rules file: use --project, or paste the printed text
        into the agent's user-rules setting.

Per project:
    python install.py --project <dir> [--agents cursor,zed,...] [--vendor]
      - adds a pointer block to the project's agent files (default: all of them):
          claude   <dir>/.claude/skills/agent-cad-skill
          cursor   <dir>/.cursor/rules/agent-cad-skill.mdc
          zed      <dir>/.rules
          agents   <dir>/AGENTS.md   (Codex, Zed, Cursor, Aider, Jules… read this)
          copilot  <dir>/.github/copilot-instructions.md
      - the skill itself is always placed at <dir>/.agents/skills/agent-cad-skill, which Antigravity
        discovers natively (no extra file needed)
      - points at the global install if there is one; with --vendor (or when there is no global
        install) the skill is copied into <dir>/.agents/skills/agent-cad-skill with relative paths, so
        the repo works for everyone who clones it.

Other options:
    --with-env     create the shared CAD environment (<skill>/.venv, ~500 MB)
    --check        run the self-tests (needs the environment)
    --uninstall    remove pointer blocks / links (and the vendored copy for --project);
                   with --global --purge also delete ~/.agent-cad-skill
Running the installer again is safe: blocks are updated in place, nothing is duplicated.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.abspath(__file__))
SKILL_SRC = os.path.join(REPO, ".agents", "skills", "agent-cad-skill")
SRC = SKILL_SRC  # installer copies the skill payload, never the tests/examples checkout
HOME = os.path.expanduser("~")
GLOBAL_DIR = os.path.abspath(os.path.expanduser(os.environ.get("AGENT_CAD_SKILL_HOME", "~/.agent-cad-skill")))


def skill_dir_in(home):
    """Directory containing SKILL.md. Prefer the cross-client nested layout."""
    home = os.path.abspath(home)
    nested = os.path.join(home, ".agents", "skills", "agent-cad-skill")
    if os.path.isfile(os.path.join(nested, "SKILL.md")):
        return nested
    if os.path.isfile(os.path.join(home, "SKILL.md")):
        return home
    return ""


def is_skill_checkout(home):
    """A repository checkout must not be replaced by a flat skill copy."""
    home = os.path.abspath(home)
    nested = skill_dir_in(home)
    return bool(nested) and nested != home and os.path.isfile(os.path.join(home, "install.py"))
BEGIN, END = "<!-- agent-cad-skill:begin -->", "<!-- agent-cad-skill:end -->"
IGNORE = shutil.ignore_patterns(".git", ".venv", "__pycache__", "output", "*.pyc", ".DS_Store")
GLOBAL_AGENTS = ["claude", "codex", "antigravity"]
PROJECT_AGENTS = ["claude", "cursor", "zed", "agents", "copilot", "antigravity"]
ALIASES = {"gemini": "antigravity", "agy": "antigravity"}
ANTIGRAVITY_SKILL = os.path.join(os.path.expanduser("~"), ".gemini", "config", "skills", "agent-cad-skill")
LEGACY_GEMINI_MD = os.path.join(os.path.expanduser("~"), ".gemini", "GEMINI.md")  # pre-Antigravity pointer
CURSOR_HEADER = ("---\ndescription: CAD, 3D models, STL/STEP/DXF, enclosure/part design, 3D printing, "
                 "laser/CNC, modeling from measurements\nalwaysApply: false\n---\n")


# ---------------------------------------------------------------- file helpers
def pointer(shown_dir):
    with open(os.path.join(SRC, "adapters", "pointer.md"), encoding="utf-8") as f:
        return f.read().replace("{SKILL_DIR}", shown_dir.replace("\\", "/"))


def upsert_block(path, body, header=""):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else header
    block = f"{BEGIN}\n{body.strip()}\n{END}"
    if BEGIN in old and END in old:
        new = old[:old.index(BEGIN)] + block + old[old.index(END) + len(END):]
    else:
        new = (old.rstrip() + "\n\n" if old.strip() else "") + block + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    print("  updated", path)


def remove_block(path, drop_if_empty_header=None):
    if not os.path.exists(path):
        return
    old = open(path, encoding="utf-8").read()
    if BEGIN not in old or END not in old:
        return
    new = (old[:old.index(BEGIN)] + old[old.index(END) + len(END):]).strip()
    if not new or (drop_if_empty_header and new == drop_if_empty_header.strip()):
        os.remove(path)
        print("  removed", path)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new + "\n")
        print("  cleaned", path)


def copy_skill(dst):
    if os.path.abspath(dst) == SRC:
        return
    venv = os.path.join(dst, ".venv")
    keep_venv = os.path.isdir(venv)
    tmp_venv = dst + ".venv-keep"
    if keep_venv:
        shutil.move(venv, tmp_venv)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(SRC, dst, ignore=IGNORE)
    if keep_venv:
        shutil.move(tmp_venv, venv)
    print("  skill copied to", dst)


def link_or_copy(target, link):
    """Point 'link' at 'target' (symlink; copy where symlinks are not available)."""
    if os.path.islink(link):
        os.remove(link)
    elif os.path.exists(link):
        bak = f"{link}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.move(link, bak)
        print("  existing folder moved to", bak)
    os.makedirs(os.path.dirname(link), exist_ok=True)
    try:
        rel = os.path.relpath(target, os.path.dirname(link))
        os.symlink(rel if not os.path.isabs(rel) else target, link, target_is_directory=True)
        print("  linked", link, "->", target)
    except (OSError, NotImplementedError):
        shutil.copytree(target, link, ignore=IGNORE)
        print("  copied", link, "(symlink not available; rerun the installer after updates)")


def unlink(link):
    if os.path.islink(link):
        os.remove(link)
        print("  removed", link)
    elif os.path.isdir(link) and os.path.exists(os.path.join(link, "SKILL.md")):
        shutil.rmtree(link)
        print("  removed", link)


def prune_empty(path, stop):
    """Remove now-empty parent folders the installer created (e.g. .cursor/rules), never 'stop' itself."""
    d = os.path.dirname(os.path.abspath(path))
    stop = os.path.abspath(stop)
    while d.startswith(stop + os.sep) and os.path.isdir(d) and not os.listdir(d):
        os.rmdir(d)
        d = os.path.dirname(d)


def parse_agents(s, allowed):
    if not s or s == "all":
        return list(allowed)
    out = [ALIASES.get(a.strip(), a.strip()) for a in s.split(",") if a.strip()]
    bad = [a for a in out if a not in allowed]
    if bad:
        raise SystemExit(f"unknown/unsupported agent(s) here: {bad}; allowed: {allowed}")
    return out


# ---------------------------------------------------------------- environment / tests
def env_python(skill_dir):
    v = os.path.join(skill_dir, ".venv")
    return os.path.join(v, "Scripts", "python.exe") if os.name == "nt" else os.path.join(v, "bin", "python")


def setup_env(skill_dir):
    print("creating CAD environment (this can take a few minutes)…")
    r = subprocess.call([sys.executable, os.path.join(skill_dir, "scripts", "setup_env.py"),
                         os.path.join(skill_dir, ".venv")])
    if r != 0:
        sys.exit("environment setup failed (see above); the skill itself is installed — "
                 "fix the problem and rerun with --with-env")


def run_checks(skill_dir=None):
    skill_dir = skill_dir or SKILL_SRC
    py = next((p for p in (env_python(skill_dir), env_python(REPO)) if os.path.exists(p)), "")
    if not py:
        raise SystemExit("environment missing: run with --with-env first")
    tests = os.path.join(REPO, "tests", "run_tests.py")
    if not os.path.exists(tests):
        raise SystemExit("self-tests are in the git checkout, not a flat installed skill")
    sys.exit(subprocess.call([py, tests]))


# ---------------------------------------------------------------- global
def install_global(agents, with_env):
    if is_skill_checkout(GLOBAL_DIR):
        skill_dir = skill_dir_in(GLOBAL_DIR)
        print(f"global install -> {skill_dir} (checkout preserved)")
    else:
        print(f"global install -> {GLOBAL_DIR}")
        copy_skill(GLOBAL_DIR)
        skill_dir = GLOBAL_DIR
    p = pointer(skill_dir)
    discover = os.path.join(HOME, ".agents", "skills", "agent-cad-skill")
    for ag in agents:
        if ag == "claude":
            link_or_copy(skill_dir, os.path.join(HOME, ".claude", "skills", "agent-cad-skill"))
        elif ag == "codex":
            upsert_block(os.path.join(HOME, ".codex", "AGENTS.md"), p)
        elif ag == "antigravity":
            link_or_copy(skill_dir, ANTIGRAVITY_SKILL)
            remove_block(LEGACY_GEMINI_MD)  # the native skill replaces the old pointer; avoid loading it twice
    if os.path.abspath(discover) != os.path.abspath(skill_dir):
        link_or_copy(skill_dir, discover)
    if with_env:
        setup_env(skill_dir)
    installer = os.path.join(GLOBAL_DIR if is_skill_checkout(GLOBAL_DIR) else REPO, "install.py")
    print("\nCursor / Zed / Copilot have no global rules file. Either run per project:\n"
          f"  python {installer} --project <dir>\n"
          "or paste this into the agent's user rules:\n")
    print(p)


def uninstall_global(agents, purge):
    print("global uninstall")
    paths = dict(claude=os.path.join(HOME, ".claude", "skills", "agent-cad-skill"),
                 codex=os.path.join(HOME, ".codex", "AGENTS.md"),
                 antigravity=ANTIGRAVITY_SKILL)
    for ag in agents:
        if ag in ("claude", "antigravity"):
            unlink(paths[ag])
            if ag == "antigravity":
                remove_block(LEGACY_GEMINI_MD)
        else:
            remove_block(paths[ag])
        prune_empty(paths[ag], HOME)
    unlink(os.path.join(HOME, ".agents", "skills", "agent-cad-skill"))
    prune_empty(os.path.join(HOME, ".agents", "skills", "agent-cad-skill"), HOME)
    if purge and os.path.isdir(GLOBAL_DIR) and skill_dir_in(GLOBAL_DIR):
        shutil.rmtree(GLOBAL_DIR)
        print("  deleted", GLOBAL_DIR)


# ---------------------------------------------------------------- project
def project_paths(proj):
    return dict(
        claude=os.path.join(proj, ".claude", "skills", "agent-cad-skill"),
        cursor=os.path.join(proj, ".cursor", "rules", "agent-cad-skill.mdc"),
        zed=os.path.join(proj, ".rules"),
        agents=os.path.join(proj, "AGENTS.md"),
        copilot=os.path.join(proj, ".github", "copilot-instructions.md"),
        antigravity=os.path.join(proj, "GEMINI.md"),  # only cleaned up: .agents/skills is discovered natively
    )


def install_project(proj, agents, vendor, with_env):
    proj = os.path.abspath(proj)
    if not os.path.isdir(proj):
        raise SystemExit(f"project folder not found: {proj}")
    global_skill = skill_dir_in(GLOBAL_DIR)
    discover = os.path.join(proj, ".agents", "skills", "agent-cad-skill")
    if vendor or not global_skill:
        skill_dir = discover
        print(f"project install (vendored) -> {skill_dir}")
        copy_skill(skill_dir)
        shown = "./.agents/skills/agent-cad-skill"
        gi = os.path.join(proj, ".gitignore")
        lines = open(gi, encoding="utf-8").read().splitlines() if os.path.exists(gi) else []
        add = [l for l in (".agents/skills/agent-cad-skill/.venv/", "output/") if l not in lines]
        if add:
            with open(gi, "a", encoding="utf-8") as f:
                f.write(("\n" if lines and lines[-1] else "") + "\n".join(add) + "\n")
            print("  updated", gi)
    else:
        skill_dir = global_skill
        shown = global_skill
        print(f"project install -> {proj} (using global skill at {global_skill})")
        if os.path.abspath(discover) != os.path.abspath(skill_dir):
            link_or_copy(skill_dir, discover)
    p = pointer(shown)
    paths = project_paths(proj)
    for ag in agents:
        if ag == "claude":
            link_or_copy(skill_dir, paths["claude"])
        elif ag == "cursor":
            upsert_block(paths["cursor"], p, CURSOR_HEADER)
        elif ag == "antigravity":
            remove_block(paths[ag])  # legacy pointer from older installers
            print("  antigravity: uses", discover)
        else:
            upsert_block(paths[ag], p)
    if with_env:
        setup_env(skill_dir)


def uninstall_project(proj, agents):
    proj = os.path.abspath(proj)
    print(f"project uninstall -> {proj}")
    paths = project_paths(proj)
    for ag in agents:
        if ag == "claude":
            unlink(paths["claude"])
        elif ag == "cursor":
            remove_block(paths["cursor"], CURSOR_HEADER)
        else:
            remove_block(paths[ag])
        prune_empty(paths[ag], proj)
    for vend in (os.path.join(proj, ".agents", "skills", "agent-cad-skill"),
                 os.path.join(proj, ".agent-cad-skill")):
        if os.path.abspath(vend) == os.path.abspath(SKILL_SRC):
            print("  kept source skill", vend)
            continue
        if os.path.islink(vend) or os.path.exists(os.path.join(vend, "SKILL.md")):
            unlink(vend)
            prune_empty(vend, proj)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--global", dest="glob", action="store_true", help="install for this user (default)")
    mode.add_argument("--project", metavar="DIR", help="install into a project")
    ap.add_argument("--agents", default="all", help="comma list or 'all' (default)")
    ap.add_argument("--vendor", action="store_true", help="--project: copy the skill into the project")
    ap.add_argument("--with-env", action="store_true", help="create the CAD environment")
    ap.add_argument("--check", action="store_true", help="run self-tests")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--purge", action="store_true", help="with --global --uninstall: also delete the skill folder")
    a = ap.parse_args()

    if a.check:
        run_checks(SRC)
    if a.project:
        agents = parse_agents(a.agents, PROJECT_AGENTS)
        (uninstall_project(a.project, agents) if a.uninstall
         else install_project(a.project, agents, a.vendor, a.with_env))
    else:
        agents = parse_agents(a.agents, GLOBAL_AGENTS)
        uninstall_global(agents, a.purge) if a.uninstall else install_global(agents, a.with_env)
    print("done.")


if __name__ == "__main__":
    main()
