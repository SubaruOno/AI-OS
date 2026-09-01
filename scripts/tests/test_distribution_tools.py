"""Unit tests for the distribution's dependency-free setup helpers."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SetSecretTests(unittest.TestCase):
    def setUp(self):
        self.module = load_script("set_secret")

    def test_replaces_once_without_exposing_other_lines(self):
        original = "# keys\nTOKEN=old\nOTHER=keep\nTOKEN=duplicate\n"
        updated = self.module.update_env_text(original, "TOKEN", "new-value")
        self.assertEqual(updated.count("TOKEN="), 1)
        self.assertIn("TOKEN=new-value", updated)
        self.assertIn("OTHER=keep", updated)

    def test_quotes_values_that_need_dotenv_escaping(self):
        self.assertEqual(self.module.encode_value('a b#c"d'), '"a b#c\\"d"')

    def test_rejects_blank_and_multiline_values(self):
        with self.assertRaises(ValueError):
            self.module.encode_value("")
        with self.assertRaises(ValueError):
            self.module.encode_value("one\ntwo")


class KeyCheckTests(unittest.TestCase):
    def setUp(self):
        self.module = load_script("check_api_key")

    def test_loads_quoted_dotenv_values(self):
        with tempfile.TemporaryDirectory() as temp:
            env_file = Path(temp) / ".env"
            env_file.write_text('OPENAI_API_KEY="secret value"\n', encoding="utf-8")
            self.assertEqual(self.module.load_env(env_file)["OPENAI_API_KEY"], "secret value")

    def test_secret_is_sent_in_header_not_url(self):
        _, request = self.module.request_for("openai", {"OPENAI_API_KEY": "private-test-value"})
        self.assertNotIn("private-test-value", request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer private-test-value")


class SkillSyncTests(unittest.TestCase):
    def setUp(self):
        self.module = load_script("sync_harness_skills")

    def test_manifest_detects_changed_and_extra_files(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            target = base / "target"
            source.mkdir()
            target.mkdir()
            (source / "a.txt").write_text("one", encoding="utf-8")
            (target / "a.txt").write_text("two", encoding="utf-8")
            (target / "extra.txt").write_text("extra", encoding="utf-8")
            delta = self.module.differences(
                self.module.manifest(source), self.module.manifest(target)
            )
            self.assertIn("different content: a.txt", delta)
            self.assertIn("extra in .agents/skills: extra.txt", delta)


class DistributionBuildTests(unittest.TestCase):
    def setUp(self):
        self.module = load_script("build_distribution")

    def test_excludes_local_state_but_keeps_source_archives(self):
        self.assertFalse(self.module.should_include(Path(".env")))
        self.assertFalse(self.module.should_include(Path("private/notes.md")))
        self.assertFalse(self.module.should_include(Path("context/import/export.zip")))
        self.assertTrue(self.module.should_include(Path("context/import/.gitkeep")))
        self.assertTrue(self.module.should_include(Path("packs/source.zip")))


class WorkspaceStatusTests(unittest.TestCase):
    def setUp(self):
        self.module = load_script("workspace_status")

    @unittest.skipUnless(subprocess.run(["git", "--version"], capture_output=True).returncode == 0, "git unavailable")
    def test_classifies_recent_and_stale_untracked_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, capture_output=True, check=True)
            recent = root / "recent.txt"
            stale = root / "stale.txt"
            recent.write_text("recent", encoding="utf-8")
            stale.write_text("stale", encoding="utf-8")
            old = time.time() - 7200
            os.utime(stale, (old, old))
            groups = self.module.classify(root, self.module.changed_paths(root), 60)
            self.assertIn("recent.txt", groups["recent"])
            self.assertIn("stale.txt", groups["stale"])


if __name__ == "__main__":
    unittest.main()
