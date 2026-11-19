"""The installable skill must be discoverable at the cross-client path."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_install():
    spec = importlib.util.spec_from_file_location("cad_install", ROOT / "install.py")
    if spec is None or spec.loader is None:
        raise AssertionError("install.py could not be loaded")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SkillLayoutTests(unittest.TestCase):
    def test_repository_skill_is_under_agents_skills(self):
        install = load_install()
        skill = ROOT / ".agents" / "skills" / "agent-cad-skill"
        self.assertEqual(Path(install.SKILL_SRC), skill)
        self.assertTrue((skill / "SKILL.md").is_file())
        self.assertTrue((skill / "scripts" / "build.py").is_file())
        self.assertFalse((ROOT / "SKILL.md").exists())

    def test_checkout_install_uses_nested_skill_without_replacing_repo(self):
        install = load_install()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            skill = home / ".agents" / "skills" / "agent-cad-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: agent-cad-skill\n---\n", encoding="utf-8")
            (home / "install.py").write_text("# checkout marker\n", encoding="utf-8")
            self.assertEqual(Path(install.skill_dir_in(home)), skill)
            self.assertTrue(install.is_skill_checkout(home))

    def test_copy_skill_copies_payload_not_repository_tests(self):
        install = load_install()
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "skill"
            install.copy_skill(str(dst))
            self.assertTrue((dst / "SKILL.md").is_file())
            self.assertTrue((dst / "scripts" / "build.py").is_file())
            self.assertTrue((dst / "requirements.lock").is_file())
            self.assertFalse((dst / "tests").exists())
            self.assertFalse((dst / "examples").exists())
