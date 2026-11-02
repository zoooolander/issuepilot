"""Exercise real Git objects in an isolated fixture, never the project repo."""

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
               / ".agents/skills/issuepilot/scripts/repo_inspector.py")
spec = importlib.util.spec_from_file_location("repo_inspector_under_test", SCRIPT_PATH)
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


class RepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="issuepilot-tests-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.repo = Path(cls.temp.name) / "repository with spaces"
        cls.repo.mkdir()
        cls.git("init", "-q")
        cls.git("config", "user.name", "Test Author")
        cls.git("config", "user.email", "test@example.com")
        cls.git("config", "core.autocrlf", "false")
        (cls.repo / "src").mkdir()
        cls.text = "# 測試\nprint('historical')\n"
        (cls.repo / "src/example.py").write_bytes(cls.text.encode("utf-8"))
        (cls.repo / "empty.txt").write_bytes(b"")
        (cls.repo / "binary.bin").write_bytes(b"abc\x00def")
        (cls.repo / "invalid.txt").write_bytes(b"\xff\xfe")
        (cls.repo / "space name.txt").write_bytes(b"spaces\n")
        (cls.repo / "credentials.json").write_bytes(b"fixture-sensitive-marker\n")
        (cls.repo / "private.key").write_bytes(b"fixture-sensitive-marker\n")
        (cls.repo / "long.txt").write_bytes(("x" * 1000 + "needle\n").encode())
        (cls.repo / "matches.txt").write_bytes(b"needle first\nsecond needle\nneedle third\n")
        cls.git("add", ".")
        # Create a symlink entry without requiring OS symlink privileges.
        link_blob = cls.git("hash-object", "-w", "--stdin", data=b"src/example.py").strip()
        cls.git("update-index", "--add", "--cacheinfo",
                f"120000,{link_blob.decode()},link")
        cls.git("commit", "-qm", "Fixture only")
        cls.sha = cls.git("rev-parse", "HEAD").decode().strip()
        cls.blob = cls.git("rev-parse", "HEAD:src/example.py").decode().strip()
        cls.tree = cls.git("rev-parse", "HEAD^{tree}").decode().strip()
        cls.git("tag", "-a", "fixture-tag", "-m", "Fixture tag")
        cls.tag = cls.git("rev-parse", "fixture-tag").decode().strip()
        cls.git("update-index", "--add", "--cacheinfo", f"160000,{cls.sha},submodule")
        cls.git("commit", "-qm", "Fixture submodule")
        cls.submodule_sha = cls.git("rev-parse", "HEAD").decode().strip()
        (cls.repo / "src/example.py").write_bytes(b"newer commit only\n")
        (cls.repo / "new-file.txt").write_bytes(b"newer commit only\n")
        cls.git("add", "src/example.py", "new-file.txt")
        cls.git("commit", "-qm", "Newer fixture version")
        cls.newer_sha = cls.git("rev-parse", "HEAD").decode().strip()
        # Leave staged, unstaged, and untracked data that must survive all reads.
        (cls.repo / "src/example.py").write_bytes(b"staged version\n")
        cls.git("add", "src/example.py")
        (cls.repo / "src/example.py").write_bytes(b"unstaged version\n")
        (cls.repo / "untracked.txt").write_bytes(b"untracked\n")

    @classmethod
    def git(cls, *args, data=None):
        return subprocess.run(
            ["git", "-C", str(cls.repo), *args], input=data,
            capture_output=True, check=True, timeout=15, shell=False,
        ).stdout

    def snapshot(self):
        # Includes index, HEAD, refs, object store, and dirty/untracked files.
        return {str(path.relative_to(self.repo)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.repo.rglob("*") if path.is_file()}

    def setUp(self):
        self.before = self.snapshot()

    def tearDown(self):
        self.assertEqual(self.snapshot(), self.before, "Inspector modified repository files")

    def read(self, path="src/example.py", sha=None, repo=None):
        return inspector.read_file_at_commit(repo or self.repo, sha or self.sha, path)

    def test_read_historical_utf8_not_worktree_or_index(self):
        self.assertEqual(self.read(), self.text)

    def test_empty_file(self):
        self.assertEqual(self.read("empty.txt"), "")

    def test_repository_subdirectory_still_uses_root_relative_path(self):
        self.assertEqual(self.read(repo=self.repo / "src"), self.text)

    def test_path_with_spaces(self):
        self.assertEqual(self.read("space name.txt"), "spaces\n")

    def test_missing_repository(self):
        with self.assertRaisesRegex(ValueError, "existing directory"):
            self.read(repo=self.repo / "absent")

    def test_repository_path_is_file(self):
        with self.assertRaisesRegex(ValueError, "existing directory"):
            self.read(repo=self.repo / "empty.txt")

    def test_non_repository(self):
        with self.assertRaisesRegex(RuntimeError, "Git command failed"):
            self.read(repo=Path(self.temp.name))

    def test_invalid_commit_sha(self):
        for sha in ["HEAD", "main", "a" * 7, "z" * 40, "--help", "a" * 41]:
            with self.subTest(sha=sha), self.assertRaisesRegex(ValueError, "Invalid commit SHA"):
                self.read(sha=sha)

    def test_nonexistent_commit(self):
        with self.assertRaisesRegex(RuntimeError, "Git command failed"):
            self.read(sha="0" * 40)

    def test_non_commit_objects(self):
        for sha in [self.blob, self.tree, self.tag]:
            with self.subTest(sha=sha), self.assertRaisesRegex(ValueError, "not a commit object"):
                self.read(sha=sha)

    def test_invalid_paths_rejected_before_git(self):
        paths = ["", "/etc/passwd", "C:/file", "C:file", "\\\\host\\share",
                 "../file", "src/../../file", "src/./file", "src//file",
                 "src/", "src\\file", "file\x00", "file\n", ":(glob)*"]
        with patch.object(inspector.subprocess, "run") as run:
            for path in paths:
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, "Invalid file path"):
                    self.read(path)
            run.assert_not_called()

    def test_missing_file_and_literal_wildcard(self):
        for path in ["missing.txt", "src/*.py"]:
            with self.subTest(path=path), self.assertRaises(FileNotFoundError):
                self.read(path)

    def test_directory_and_symlink_rejected(self):
        for path in ["src", "link"]:
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "not a regular file"):
                self.read(path)

    def test_submodule_rejected(self):
        with self.assertRaisesRegex(ValueError, "not a regular file"):
            self.read("submodule", sha=self.submodule_sha)

    def test_binary_rejected(self):
        with self.assertRaisesRegex(ValueError, "binary/control"):
            self.read("binary.bin")

    def test_invalid_utf8_rejected(self):
        with self.assertRaisesRegex(ValueError, "not valid UTF-8"):
            self.read("invalid.txt")

    def test_git_missing_timeout_and_execution_errors(self):
        for error, message in [
            (FileNotFoundError(), "Git executable not found"),
            (subprocess.TimeoutExpired("git", 15), "timed out"),
            (PermissionError("denied"), "Unable to execute Git"),
            (subprocess.CalledProcessError(128, "git", stderr=b"fatal: failure"),
             "Git command failed: fatal: failure"),
        ]:
            with self.subTest(error=error):
                with patch.object(inspector.subprocess, "run", side_effect=error):
                    with self.assertRaisesRegex(RuntimeError, message):
                        self.read()

    def test_only_read_commands_and_argument_arrays(self):
        original_run = subprocess.run
        with patch.object(inspector.subprocess, "run", wraps=original_run) as run:
            self.assertEqual(self.read(), self.text)
        commands = []
        for call in run.call_args_list:
            args = call.args[0]
            self.assertIsInstance(args, list)
            self.assertFalse(call.kwargs["shell"])
            self.assertTrue(call.kwargs["check"])
            self.assertEqual(call.kwargs["env"]["GIT_NO_LAZY_FETCH"], "1")
            self.assertEqual(call.kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")
            commands.append(args[6])
        self.assertEqual(commands, ["rev-parse", "cat-file", "ls-tree", "show"])

    def test_inherited_git_overrides_ignored(self):
        with patch.dict(os.environ, {"GIT_DIR": "does-not-exist", "GIT_WORK_TREE": "bad"}):
            self.assertEqual(self.read(), self.text)

    def run_cli(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with (patch.object(sys, "argv", [str(SCRIPT_PATH), *args]),
              redirect_stdout(stdout), redirect_stderr(stderr)):
            try:
                runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
            except SystemExit as exc:
                code = exc.code
            else:
                code = 0
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_success(self):
        self.assertEqual(self.run_cli([str(self.repo), self.sha, "src/example.py"]),
                         (0, self.text, ""))

    def test_cli_wrong_argument_count(self):
        for args in [[], [str(self.repo)], ["a", "b", "c", "d"]]:
            with self.subTest(args=args):
                code, stdout, stderr = self.run_cli(args)
                self.assertEqual(code, 1)
                self.assertEqual(stdout, "")
                self.assertEqual(stderr, "Error: Usage: repo_inspector.py REPOSITORY COMMIT_SHA FILE_PATH\n")

    def test_cli_error_cases(self):
        for sha, path, message in [
            ("HEAD", "empty.txt", "Invalid commit SHA"),
            (self.sha, "../file", "Invalid file path"),
            (self.sha, "absent", "File not found"),
            (self.sha, "link", "not a regular file"),
            (self.sha, "binary.bin", "binary/control"),
            (self.sha, "invalid.txt", "not valid UTF-8"),
            ("0" * 40, "empty.txt", "Git command failed"),
        ]:
            with self.subTest(path=path, sha=sha):
                code, stdout, stderr = self.run_cli([str(self.repo), sha, path])
                self.assertEqual(code, 1)
                self.assertEqual(stdout, "")
                self.assertTrue(stderr.startswith("Error: "))
                self.assertIn(message, stderr)
                self.assertNotIn("Traceback", stderr)

    def test_list_files_and_name_filter(self):
        result = inspector.list_files_at_commit(self.repo, self.sha)
        paths = [item["path"] for item in result["results"]]
        self.assertIn("src/example.py", paths)
        self.assertIn("empty.txt", paths)
        self.assertIn("space name.txt", paths)
        self.assertEqual(result["commit_sha"], self.sha)
        self.assertFalse(result["truncated"])
        self.assertEqual(inspector.list_files_at_commit(
            self.repo, self.sha, "example.py")["results"], [{"path": "src/example.py"}])

    def test_search_content_and_line_numbers(self):
        result = inspector.search_code_at_commit(self.repo, self.sha, "needle",
                                                 filename_query="matches.txt")
        self.assertEqual([m["line_number"] for m in result["results"]], [1, 2, 3])
        self.assertEqual([m["content"] for m in result["results"]],
                         ["needle first", "second needle", "needle third"])
        self.assertTrue(all(m["path"] == "matches.txt" for m in result["results"]))
        self.assertFalse(result["truncated"])

    def test_search_unicode(self):
        result = inspector.search_code_at_commit(self.repo, self.sha, "測試")
        self.assertEqual(result["results"][0]["content"], "# 測試")
        self.assertEqual(result["results"][0]["line_number"], 1)

    def test_search_version_isolation(self):
        self.assertEqual(inspector.search_code_at_commit(
            self.repo, self.sha, "newer commit only")["results"], [])
        self.assertTrue(inspector.search_code_at_commit(
            self.repo, self.newer_sha, "newer commit only")["results"])
        self.assertEqual(inspector.list_files_at_commit(
            self.repo, self.sha, "new-file")["results"], [])
        for query in ["staged version", "unstaged version", "untracked"]:
            self.assertEqual(inspector.search_code_at_commit(
                self.repo, self.sha, query)["results"], [])

    def test_search_no_matches_and_literal_semantics(self):
        for query in ["NEEDLE", "needle.*", "[abc]", "$(echo unsafe)"]:
            result = inspector.search_code_at_commit(self.repo, self.sha, query)
            self.assertEqual(result["results"], [])
            self.assertFalse(result["truncated"])
        self.assertEqual(inspector.list_files_at_commit(
            self.repo, self.sha, "*.py")["results"], [])

    def test_search_excludes_sensitive_and_non_text_files(self):
        original = inspector._run_git
        with patch.object(inspector, "_run_git", wraps=original) as run:
            result = inspector.list_files_at_commit(self.repo, self.submodule_sha)
        paths = [m["path"] for m in result["results"]]
        for path in ["credentials.json", "private.key", "binary.bin", "invalid.txt",
                     "link", "submodule"]:
            self.assertNotIn(path, paths)
        self.assertGreaterEqual(result["skipped_files"], 6)
        self.assertEqual(inspector.search_code_at_commit(
            self.repo, self.sha, "fixture-sensitive-marker")["results"], [])
        # Exclusion happens before opening sensitive blobs.
        sensitive_ids = [self.git("rev-parse", f"{self.sha}:{p}").decode().strip()
                         for p in ["credentials.json", "private.key"]]
        opened = [call.args[-1] for call in run.call_args_list
                  if call.args[1:3] == ("cat-file", "blob")]
        self.assertTrue(set(sensitive_ids).isdisjoint(opened))

    def test_sensitive_path_patterns_and_direct_read(self):
        for path in [".env", ".env.local", "nested/.env.example", ".aws/config",
                     "secrets.toml", "credentials.json", "private.key", ".ssh/id_rsa"]:
            with self.subTest(path=path):
                self.assertTrue(inspector._is_sensitive(path))
                with patch.object(inspector, "_run_git") as run:
                    with self.assertRaisesRegex(ValueError, "Sensitive"):
                        self.read(path)
                    run.assert_not_called()

    def test_search_result_limit(self):
        result = inspector.search_code_at_commit(self.repo, self.sha, "needle",
                                                 filename_query="matches.txt", max_results=2)
        self.assertEqual(len(result["results"]), 2)
        self.assertTrue(result["truncated"])
        exact = inspector.search_code_at_commit(self.repo, self.sha, "needle",
                                                filename_query="matches.txt", max_results=3)
        self.assertFalse(exact["truncated"])
        self.assertTrue(inspector.list_files_at_commit(
            self.repo, self.sha, max_results=1)["truncated"])

    def test_search_output_and_line_limits(self):
        result = inspector.search_code_at_commit(self.repo, self.sha, "needle",
                                                 filename_query="long.txt")
        match = result["results"][0]
        self.assertLessEqual(len(match["content"]), inspector.MAX_LINE_CHARS)
        self.assertIn("needle", match["content"])
        self.assertTrue(match["content_truncated"])
        self.assertGreater(match["content_start_column"], 1)
        for fn, args in [(inspector.list_files_at_commit, ()),
                         (inspector.search_code_at_commit, ("needle",))]:
            result = fn(self.repo, self.sha, *args, max_output_chars=256)
            self.assertLessEqual(len(json.dumps(result)) + 1, 256)
            self.assertTrue(result["truncated"])

    def test_search_invalid_queries_and_limits(self):
        for query in ["", "x\n", "x\x00", "a" * 257, None]:
            with self.subTest(query=query), self.assertRaisesRegex(ValueError, "query"):
                inspector.search_code_at_commit(self.repo, self.sha, query)
        for name, value in [("max_results", 0), ("max_results", 201),
                            ("max_results", True), ("max_output_chars", 255),
                            ("max_output_chars", 50001), ("filename_query", "x\n")]:
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                inspector.list_files_at_commit(self.repo, self.sha, **{name: value})

    def test_search_invalid_repository_commit_and_objects(self):
        for fn, args in [(inspector.list_files_at_commit, ()),
                         (inspector.search_code_at_commit, ("needle",))]:
            for sha in ["HEAD", self.blob, self.tree, self.tag, "0" * 40]:
                with self.subTest(fn=fn.__name__, sha=sha):
                    with self.assertRaises((ValueError, RuntimeError)):
                        fn(self.repo, sha, *args)
            with self.assertRaises(ValueError):
                fn(self.repo / "absent", self.sha, *args)

    def test_search_scan_budgets(self):
        with patch.object(inspector, "MAX_SCAN_FILES", 1):
            self.assertTrue(inspector.list_files_at_commit(
                self.repo, self.sha)["scan_truncated"])
        with patch.object(inspector, "MAX_SCAN_BYTES", 1):
            self.assertTrue(inspector.list_files_at_commit(
                self.repo, self.sha)["scan_truncated"])
        with patch.object(inspector, "MAX_FILE_BYTES", 1):
            result = inspector.list_files_at_commit(self.repo, self.sha)
            self.assertEqual(result["results"], [{"path": "empty.txt"}])
            self.assertGreater(result["skipped_files"], 0)

    def test_search_readonly_commands(self):
        original = subprocess.run
        with patch.object(inspector.subprocess, "run", wraps=original) as run:
            inspector.search_code_at_commit(self.repo / "src", self.sha, "historical")
        for call in run.call_args_list:
            self.assertIsInstance(call.args[0], list)
            self.assertFalse(call.kwargs["shell"])
            self.assertIn(call.args[0][6], {"rev-parse", "cat-file", "ls-tree"})
            self.assertEqual(call.kwargs["env"]["GIT_NO_LAZY_FETCH"], "1")

    def test_long_query_stays_visible_in_snippet(self):
        query = "q" * 256
        matches = list(inspector._line_matches("file.py", "x" * 1000 + query, query))
        self.assertIn(query, matches[0]["content"])
        self.assertLessEqual(len(matches[0]["content"]), inspector.MAX_LINE_CHARS)

    def test_search_git_failure_is_not_empty_success(self):
        with patch.object(inspector, "_run_git", side_effect=RuntimeError("Git unavailable")):
            with self.assertRaisesRegex(RuntimeError, "Git unavailable"):
                inspector.search_code_at_commit(self.repo, self.sha, "needle")

    def test_search_cli_modes_and_json(self):
        for mode in [["--list-files"], ["--search-code", "historical"]]:
            code, stdout, stderr = self.run_cli(
                [*mode, str(self.repo), self.sha, "--name", "example.py", "--limit", "2"])
            self.assertEqual((code, stderr), (0, ""))
            result = json.loads(stdout)
            self.assertEqual(result["commit_sha"], self.sha)
            self.assertEqual(result["results"][0]["path"], "src/example.py")
        code, stdout, stderr = self.run_cli(
            ["--search-code", "absent-query", str(self.repo), self.sha])
        self.assertEqual((code, stderr, json.loads(stdout)["results"]), (0, "", []))

    def test_search_cli_errors_and_output_budget(self):
        for options in [["--limit", "0"], ["--limit", "not-an-int"],
                        ["--max-output-chars", "100"], ["--unknown"]]:
            code, stdout, stderr = self.run_cli(
                ["--list-files", str(self.repo), self.sha, *options])
            self.assertNotEqual(code, 0)
            self.assertEqual(stdout, "")
            self.assertTrue(stderr)
            self.assertNotIn("Traceback", stderr)
        code, stdout, stderr = self.run_cli(
            ["--search-code", "needle", str(self.repo), self.sha,
             "--max-output-chars", "256"])
        self.assertEqual((code, stderr), (0, ""))
        self.assertLessEqual(len(stdout), 256)
        for args in [["--search-code", "", str(self.repo), self.sha],
                     ["--list-files", str(self.repo)],
                     ["--list-files", str(self.repo), "HEAD"]]:
            code, stdout, stderr = self.run_cli(args)
            self.assertNotEqual(code, 0)
            self.assertEqual(stdout, "")
            self.assertTrue(stderr)


if __name__ == "__main__":
    unittest.main()
