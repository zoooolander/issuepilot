"""Offline tests for API failures and the github_fetcher command line."""

import importlib.util
import io
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
    / ".agents/skills/issuepilot/scripts/github_fetcher.py"
)
ISSUE_URL = "https://github.com/example/project/issues/123"
API_URL = "https://api.github.com/repos/example/project/issues/123"

spec = importlib.util.spec_from_file_location("github_fetcher_under_test", SCRIPT_PATH)
github_fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(github_fetcher)


def rate_limit_error():
    headers = Message()
    headers["X-RateLimit-Remaining"] = "0"
    return HTTPError(API_URL, 403, "Forbidden", headers, io.BytesIO())


class FetchIssueErrorTests(unittest.TestCase):
    def assert_error_propagates(self, error):
        if isinstance(error, HTTPError):
            self.addCleanup(error.close)
        with patch("urllib.request.urlopen", side_effect=error) as urlopen:
            with self.assertRaises(type(error)) as caught:
                github_fetcher.fetch_issue("example", "project", 123)

        # Preserve the original exception, including HTTP headers and reason.
        self.assertIs(caught.exception, error)
        urlopen.assert_called_once()
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, API_URL)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 15)

    def test_rate_limit_error_propagates(self):
        self.assert_error_propagates(rate_limit_error())

    def test_network_error_propagates(self):
        self.assert_error_propagates(URLError("connection refused"))


class CliErrorTests(unittest.TestCase):
    def assert_cli_error(self, error, expected_message):
        if isinstance(error, HTTPError):
            self.addCleanup(error.close)
        stdout = io.StringIO()
        stderr = io.StringIO()
        # Execute the real __main__ block in-process so urlopen stays mocked.
        with (
            patch.object(sys, "argv", [str(SCRIPT_PATH), ISSUE_URL]),
            patch("urllib.request.urlopen", side_effect=error) as urlopen,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            with self.assertRaises(SystemExit) as caught:
                runpy.run_path(str(SCRIPT_PATH), run_name="__main__")

        self.assertEqual(caught.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), expected_message + "\n")
        urlopen.assert_called_once()
        self.assertEqual(urlopen.call_args.args[0].full_url, API_URL)

    def test_rate_limit_cli_message_and_exit_code(self):
        self.assert_cli_error(
            rate_limit_error(), "Error: GitHub API rate limit exceeded."
        )

    def test_network_cli_message_and_exit_code(self):
        self.assert_cli_error(
            URLError("connection refused"),
            "Error: Network error: connection refused",
        )


if __name__ == "__main__":
    unittest.main()
