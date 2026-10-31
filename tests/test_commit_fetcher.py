"""Offline metadata and CLI tests; every HTTP request is mocked."""

import importlib.util
import io
import json
from pathlib import Path
import runpy
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError, URLError


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents/skills/issuepilot/scripts/commit_fetcher.py"
)
VALUE = "a" * 40
URL = f"https://github.com/example/project/commit/{VALUE}"
API_URL = f"https://api.github.com/repos/example/project/git/commits/{VALUE}"
spec = importlib.util.spec_from_file_location("commit_fetcher_under_test", SCRIPT_PATH)
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)

PAYLOAD = {
    "sha": VALUE, "message": "測試 commit",
    "parents": [{"sha": "b" * 40}, {"sha": "c" * 40}],
    "author": {"name": "Example", "email": "example@example.com",
               "date": "2026-01-01T00:00:00Z"},
    "tree": {"sha": "d" * 40},
}
EXPECTED = {
    "sha": VALUE, "message": "測試 commit",
    "parents": ["b" * 40, "c" * 40], "author": PAYLOAD["author"],
}


def http_error(code, remaining=None):
    headers = Message()
    if remaining is not None:
        headers["X-RateLimit-Remaining"] = remaining
    error = HTTPError(API_URL, code, "API error", headers, io.BytesIO())
    error.close()
    return error


class MetadataTests(unittest.TestCase):
    def test_parse_valid_urls(self):
        for owner, repo in [("example", "project"), ("another-org", "other.repo")]:
            for suffix in ("", "/"):
                with self.subTest(owner=owner, suffix=suffix):
                    self.assertEqual(
                        fetcher.parse_commit_url(
                            f"https://github.com/{owner}/{repo}/commit/{VALUE}{suffix}"
                        ),
                        {"owner": owner, "repo": repo, "sha": VALUE},
                    )

    def test_parse_invalid_urls(self):
        urls = [
            "", "not-a-url", URL.replace("https:", "http:"),
            URL.replace("github.com", "example.com"),
            URL.replace("/commit/", "/issues/"),
            URL + "/files", URL + "?query=1",
            URL[:-1], URL + "a", URL.replace(str(VALUE), "z" * 40),
        ]
        for url in urls:
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, "^Invalid GitHub Commit URL$"):
                    fetcher.parse_commit_url(url)

    def test_fetch_success(self):
        with patch("urllib.request.urlopen", return_value=io.BytesIO(
            json.dumps(PAYLOAD).encode("utf-8")
        )) as urlopen:
            result = fetcher.fetch_commit("example", "project", VALUE)
        self.assertEqual(result, EXPECTED)
        urlopen.assert_called_once()
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, API_URL)
        self.assertEqual(request.get_header("Accept"), "application/vnd.github+json")
        self.assertEqual(request.get_header("User-agent"), "IssuePilot")
        self.assertEqual(urlopen.call_args.kwargs, {"timeout": 15})

    def test_fetch_errors_propagate(self):
        for error in [
            http_error(404), http_error(403, "0"), http_error(429),
            URLError("connection refused"),
        ]:
            with self.subTest(error=error):
                with patch("urllib.request.urlopen", side_effect=error) as urlopen:
                    with self.assertRaises(type(error)) as caught:
                        fetcher.fetch_commit("example", "project", VALUE)
                self.assertIs(caught.exception, error)
                urlopen.assert_called_once()

    def test_root_commit_without_parents(self):
        payload = dict(PAYLOAD, parents=[])
        with patch("urllib.request.urlopen", return_value=io.BytesIO(
            json.dumps(payload).encode("utf-8")
        )):
            self.assertEqual(
                fetcher.fetch_commit("example", "project", VALUE),
                dict(EXPECTED, parents=[]),
            )


class CliTests(unittest.TestCase):
    def run_cli(self, args, error=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.object(sys, "argv", [str(SCRIPT_PATH), *args]),
            patch("urllib.request.urlopen", side_effect=error, return_value=io.BytesIO(
                json.dumps(PAYLOAD).encode("utf-8")
            )) as urlopen,
            redirect_stdout(stdout), redirect_stderr(stderr),
        ):
            try:
                runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
            except SystemExit as exc:
                code = exc.code
            else:
                code = 0
        return code, stdout.getvalue(), stderr.getvalue(), urlopen

    def assert_cli_error(self, error, message):
        code, stdout, stderr, urlopen = self.run_cli([URL], error)
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, message + "\n")
        urlopen.assert_called_once()
        self.assertEqual(urlopen.call_args.args[0].full_url, API_URL)

    def test_success(self):
        code, stdout, stderr, urlopen = self.run_cli([URL])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout), EXPECTED)
        self.assertEqual(stderr, "")
        urlopen.assert_called_once()

    def test_missing_url(self):
        code, stdout, stderr, urlopen = self.run_cli([])
        self.assertEqual((code, stdout, stderr),
                         (1, "", "Error: Please provide a GitHub Commit URL.\n"))
        urlopen.assert_not_called()

    def test_invalid_url(self):
        code, stdout, stderr, urlopen = self.run_cli(["invalid"])
        self.assertEqual((code, stdout, stderr),
                         (1, "", "Error: Invalid GitHub Commit URL\n"))
        urlopen.assert_not_called()

    def test_not_found(self):
        self.assert_cli_error(http_error(404), "Error: GitHub Commit not found.")

    def test_rate_limit_403(self):
        self.assert_cli_error(
            http_error(403, "0"), "Error: GitHub API rate limit exceeded."
        )

    def test_rate_limit_429(self):
        self.assert_cli_error(http_error(429), "Error: GitHub API rate limit exceeded.")

    def test_other_http_errors(self):
        for code, remaining in [(403, "1"), (403, None), (500, None)]:
            with self.subTest(code=code, remaining=remaining):
                self.assert_cli_error(
                    http_error(code, remaining), f"Error: GitHub API returned HTTP {code}."
                )

    def test_network_error(self):
        self.assert_cli_error(
            URLError("connection refused"), "Error: Network error: connection refused"
        )


if __name__ == "__main__":
    unittest.main()
