"""Version checks in temporary Git repositories; no live services required."""

import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch


SCRIPT_PATH = (Path(__file__).resolve().parents[1]
               / ".agents/skills/issuepilot/scripts/version_selector.py")
spec = importlib.util.spec_from_file_location("version_selector_under_test", SCRIPT_PATH)
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)


class VersionSelectorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="issuepilot-version-")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.repo = self.base / "repository with spaces"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.com")
        self.git("config", "core.autocrlf", "false")
        (self.repo / "tracked.txt").write_bytes(b"original\n")
        self.git("add", "tracked.txt")
        self.git("commit", "-qm", "Temporary fixture")
        self.sha = self.git("rev-parse", "HEAD").decode().strip()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              capture_output=True, check=True, timeout=15).stdout

    def snapshot(self):
        return {str(path.relative_to(self.repo)):
                (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
                for path in self.repo.rglob("*") if path.is_file()}

    def inspect(self, path=None):
        before = self.snapshot()
        try:
            return selector.select_version(path if path is not None else self.repo)
        finally:
            self.assertEqual(self.snapshot(), before, "Repository was modified")

    def assert_state(self, dirty):
        result = self.inspect()
        self.assertEqual(result, {
            "repo_path": str(self.repo.resolve()), "head_sha": self.sha,
            "is_dirty": dirty, "worktree_status": "dirty" if dirty else "clean",
        })

    def test_clean_head_and_full_sha(self):
        self.assertEqual(len(self.sha), 40)
        self.assert_state(False)

    def test_staged_changes(self):
        (self.repo / "tracked.txt").write_bytes(b"staged\n")
        self.git("add", "tracked.txt")
        self.assert_state(True)

    def test_unstaged_changes(self):
        (self.repo / "tracked.txt").write_bytes(b"unstaged\n")
        self.assert_state(True)

    def test_untracked_files_in_nested_directory(self):
        (self.repo / "nested").mkdir()
        (self.repo / "nested/new.txt").write_bytes(b"untracked\n")
        self.assert_state(True)

    def test_staged_unstaged_and_untracked_together(self):
        (self.repo / "tracked.txt").write_bytes(b"staged\n")
        self.git("add", "tracked.txt")
        (self.repo / "tracked.txt").write_bytes(b"unstaged\n")
        (self.repo / "new.txt").write_bytes(b"untracked\n")
        self.assert_state(True)

    def test_deleted_file(self):
        (self.repo / "tracked.txt").unlink()
        self.assert_state(True)

    def test_ignored_files_are_not_untracked_changes(self):
        (self.repo / ".git/info/exclude").write_text("ignored.txt\n", encoding="utf-8")
        (self.repo / "ignored.txt").write_bytes(b"ignored fixture\n")
        self.assert_state(False)

    def test_staged_rename(self):
        self.git("mv", "tracked.txt", "renamed.txt")
        self.assert_state(True)

    def test_subdirectory_checks_entire_repository(self):
        subdir = self.repo / "subdir"
        subdir.mkdir()
        (self.repo / "outside.txt").write_bytes(b"untracked\n")
        result = self.inspect(subdir)
        self.assertTrue(result["is_dirty"])
        self.assertEqual(result["repo_path"], str(self.repo.resolve()))

    def test_detached_head(self):
        # Only the temporary fixture's HEAD is arranged, never a real checkout.
        (self.repo / ".git/HEAD").write_text(self.sha + "\n", encoding="ascii")
        self.assert_state(False)

    def test_invalid_repository_paths(self):
        for path in [self.base / "absent", self.repo / "tracked.txt"]:
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "existing directory"):
                self.inspect(path)
        with self.assertRaisesRegex(RuntimeError, "Git command failed"):
            self.inspect(self.base)

    def test_unborn_head(self):
        empty = self.base / "empty"
        empty.mkdir()
        subprocess.run(["git", "-C", str(empty), "init", "-q"], check=True, capture_output=True)
        with self.assertRaisesRegex(RuntimeError, "Git command failed"):
            self.inspect(empty)

    def test_bare_repository_rejected(self):
        bare = self.base / "bare.git"
        subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True, capture_output=True)
        with self.assertRaisesRegex(ValueError, "working tree"):
            self.inspect(bare)

    def test_inherited_git_overrides_ignored(self):
        with patch.dict(os.environ, {"GIT_DIR": "absent", "GIT_INDEX_FILE": "bad-index"}):
            self.assert_state(False)

    def test_only_readonly_argument_array_commands(self):
        original = subprocess.run
        with patch.object(selector.subprocess, "run", wraps=original) as run:
            self.assert_state(False)
        for call in run.call_args_list:
            args = call.args[0]
            self.assertIsInstance(args, list)
            self.assertIn(args[7], {"rev-parse", "status"})
            self.assertFalse(call.kwargs["shell"])
            self.assertEqual(call.kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")
            self.assertEqual(call.kwargs["env"]["GIT_NO_LAZY_FETCH"], "1")
            self.assertIn("core.fsmonitor=false", args)

    def test_git_errors(self):
        for error, message in [
            (FileNotFoundError(), "executable not found"),
            (PermissionError("denied"), "Unable to execute"),
            (subprocess.TimeoutExpired("git", 15), "timed out"),
            (subprocess.CalledProcessError(128, "git", stderr=b"fatal: fixture"),
             "Git command failed: fatal: fixture"),
        ]:
            with self.subTest(error=error):
                with patch.object(selector.subprocess, "run", side_effect=error):
                    with self.assertRaisesRegex(RuntimeError, message):
                        self.inspect()

    def test_head_changed_during_inspection(self):
        with patch.object(selector, "_run_git", side_effect=[
            b"true\n", str(self.repo).encode() + b"\n", self.sha.encode(), b"", b"0" * 40,
        ]):
            with self.assertRaisesRegex(RuntimeError, "HEAD changed"):
                self.inspect()

    def run_cli(self, args):
        before = self.snapshot()
        stdout, stderr = io.StringIO(), io.StringIO()
        with (patch.object(sys, "argv", [str(SCRIPT_PATH), *args]),
              redirect_stdout(stdout), redirect_stderr(stderr)):
            try:
                runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
            except SystemExit as exc:
                code = exc.code
            else:
                code = 0
        self.assertEqual(self.snapshot(), before)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_clean_and_dirty_json(self):
        for dirty in [False, True]:
            if dirty:
                (self.repo / "new.txt").write_bytes(b"untracked\n")
            code, stdout, stderr = self.run_cli([str(self.repo)])
            self.assertEqual((code, stderr), (0, ""))
            result = json.loads(stdout)
            self.assertEqual(result["head_sha"], self.sha)
            self.assertEqual(result["is_dirty"], dirty)

    def test_cli_errors_and_no_historical_sha_argument(self):
        for args in [[], [str(self.repo), self.sha], [str(self.base)]]:
            code, stdout, stderr = self.run_cli(args)
            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assertTrue(stderr.startswith("Error: "))
            self.assertNotIn("Traceback", stderr)


if __name__ == "__main__":
    unittest.main()
