"""Read UTF-8 text from an explicit local Git commit without changing it."""

import argparse
import json
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys


MAX_FILE_BYTES = 1024 * 1024
MAX_SCAN_BYTES = 10 * MAX_FILE_BYTES
MAX_SCAN_FILES = 2000
MAX_LINE_CHARS = 300


def _is_sensitive(path: str) -> bool:
    parts = path.lower().split("/")
    names = {"credentials", "credentials.json", "credentials.yaml", "credentials.yml",
             "secrets", "secrets.json", "secrets.yaml", "secrets.yml", "secrets.toml",
             "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", ".netrc", ".npmrc",
             ".pypirc", ".git-credentials", "service-account.json"}
    return any(part in names or part.startswith((".env", "secrets.", "credentials."))
               or part in {".git", ".ssh", ".aws", ".azure", ".gnupg", ".kube", ".docker"}
               or part.endswith((".pem", ".key", ".p12", ".pfx", ".keystore", ".crt", ".cer"))
               for part in parts)


def _validate_repository_commit(repo_path, commit_sha):
    if not isinstance(commit_sha, str) or not re.fullmatch(
        r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", commit_sha
    ):
        raise ValueError("Invalid commit SHA: provide a full 40- or 64-character hex SHA.")
    repo = Path(repo_path).resolve()
    if not repo.is_dir():
        raise ValueError("Repository path must be an existing directory.")
    _run_git(repo, "rev-parse", "--absolute-git-dir")
    if _run_git(repo, "cat-file", "-t", commit_sha).strip() != b"commit":
        raise ValueError("Specified SHA is not a commit object.")
    return repo


def _decode_text(content):
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("File is not valid UTF-8 text.") from exc
    if any((ord(char) < 32 and char not in "\t\n\r") or ord(char) == 127
           for char in text):
        raise ValueError("File contains binary/control data, not plain text.")
    return text


def _run_git(repo_path: Path, *args: str) -> bytes:
    # Ignore inherited Git repository/config overrides; never fetch missing objects.
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    try:
        result = subprocess.run(
            ["git", "--no-pager", "--no-replace-objects", "--literal-pathspecs",
             "-C", str(repo_path), *args],
            capture_output=True, check=True, timeout=15, env=env, shell=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Git executable not found.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Git command timed out.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Git command failed: {detail}") from exc
    except OSError as exc:
        raise RuntimeError(f"Unable to execute Git: {exc}") from exc
    return result.stdout


def read_file_at_commit(repo_path, commit_sha, file_path) -> str:
    """Return a regular UTF-8 blob; the commit is not a verified bug version.

    Paths must be repository-relative POSIX paths. Full SHA-1 or SHA-256 IDs
    are required; branches, tags and abbreviated SHAs are not accepted.
    """
    if not isinstance(commit_sha, str) or not re.fullmatch(
        r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", commit_sha
    ):
        raise ValueError("Invalid commit SHA: provide a full 40- or 64-character hex SHA.")
    if (
        not isinstance(file_path, str) or not file_path
        or file_path.startswith("/") or PureWindowsPath(file_path).drive
        or "\\" in file_path or ":" in file_path
        or any(part in ("", ".", "..") for part in file_path.split("/"))
        or any(ord(char) < 32 or ord(char) == 127 for char in file_path)
    ):
        raise ValueError("Invalid file path: use a repository-relative path without traversal.")
    if _is_sensitive(file_path):
        raise ValueError("Sensitive file paths are excluded.")
    repo = _validate_repository_commit(repo_path, commit_sha)

    entry = _run_git(repo, "ls-tree", "--full-tree", "-z", commit_sha, "--", file_path)
    if not entry:
        raise FileNotFoundError("File not found at the specified commit.")
    metadata, _, _ = entry.partition(b"\t")
    mode, object_type, _ = metadata.split()
    if mode not in (b"100644", b"100755") or object_type != b"blob":
        raise ValueError("Requested path is not a regular file (directory, symlink or submodule).")

    content = _run_git(repo, "show", "--no-ext-diff", "--no-textconv",
                       f"{commit_sha}:{file_path}")
    return _decode_text(content)


def _validate_query(query, allow_empty=False):
    if (not isinstance(query, str) or (not query and not allow_empty)
            or len(query) > 256 or any(ord(c) < 32 or ord(c) == 127 for c in query)):
        raise ValueError("Search query must be single-line text of 1 to 256 characters.")


def _line_matches(path, text, query):
    for number, line in enumerate(text.split("\n"), 1):
        position = line.find(query)
        if position < 0:
            continue
        start = max(0, position - min(100, MAX_LINE_CHARS - len(query)))
        yield {"path": path, "line_number": number,
               "content": line[start:start + MAX_LINE_CHARS],
               "content_start_column": start + 1,
               "content_truncated": len(line) > MAX_LINE_CHARS}


def _search_at_commit(repo_path, commit_sha, filename_query, text_query,
                      max_results, max_output_chars):
    _validate_query(filename_query, allow_empty=True)
    if text_query is not None:
        _validate_query(text_query)
    if type(max_results) is not int or not 1 <= max_results <= 200:
        raise ValueError("max_results must be an integer from 1 to 200.")
    if type(max_output_chars) is not int or not 256 <= max_output_chars <= 50000:
        raise ValueError("max_output_chars must be an integer from 256 to 50000.")
    repo = _validate_repository_commit(repo_path, commit_sha)
    result = {"commit_sha": commit_sha, "results": [], "truncated": False,
              "scan_truncated": False, "skipped_files": 0}
    # -l provides blob sizes before reading; -z keeps spaces/tabs in paths unambiguous.
    entries = _run_git(repo, "ls-tree", "--full-tree", "-r", "-l", "-z", commit_sha)
    scanned = total_bytes = 0
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        if scanned >= MAX_SCAN_FILES:
            result["scan_truncated"] = True
            break
        scanned += 1
        metadata, path_bytes = entry.split(b"\t", 1)
        mode, object_type, object_sha, size = metadata.split()
        try:
            path = path_bytes.decode("utf-8")
        except UnicodeDecodeError:
            result["skipped_files"] += 1
            continue
        if (mode not in (b"100644", b"100755") or object_type != b"blob"
                or _is_sensitive(path) or any(ord(c) < 32 or ord(c) == 127 for c in path)
                or "\\" in path or ":" in path):
            result["skipped_files"] += 1
            continue
        if filename_query not in path:
            continue
        size = int(size)
        if size > MAX_FILE_BYTES:
            result["skipped_files"] += 1
            continue
        if total_bytes + size > MAX_SCAN_BYTES:
            result["scan_truncated"] = True
            break
        total_bytes += size
        # Read blobs directly: no checkout, filters, external diff, or symlink following.
        content = _run_git(repo, "cat-file", "blob", object_sha.decode("ascii"))
        try:
            text = _decode_text(content)
        except ValueError:
            result["skipped_files"] += 1
            continue
        if text_query is None:
            matches = [{"path": path}]
        else:
            matches = _line_matches(path, text, text_query)
        for match in matches:
            if len(result["results"]) >= max_results:
                result["truncated"] = True
                return result
            result["results"].append(match)
            # ASCII JSON makes the output budget deterministic across terminals.
            if len(json.dumps(result, ensure_ascii=True)) + 64 > max_output_chars:
                result["results"].pop()
                result["truncated"] = True
                return result
    return result


def list_files_at_commit(repo_path, commit_sha, filename_query="", *,
                         max_results=50, max_output_chars=20000):
    """List safe UTF-8 files; optional literal, case-sensitive path substring."""
    return _search_at_commit(repo_path, commit_sha, filename_query, None,
                             max_results, max_output_chars)


def search_code_at_commit(repo_path, commit_sha, query, *, filename_query="",
                          max_results=50, max_output_chars=20000):
    """Search literal case-sensitive text at SHA; line numbers are one-based."""
    _validate_query(query)
    return _search_at_commit(repo_path, commit_sha, filename_query, query,
                             max_results, max_output_chars)


if __name__ == "__main__":
    search_mode = len(sys.argv) > 1 and sys.argv[1] in ("--list-files", "--search-code")
    if not search_mode and len(sys.argv) != 4:
        print("Error: Usage: repo_inspector.py REPOSITORY COMMIT_SHA FILE_PATH", file=sys.stderr)
        sys.exit(1)
    try:
        if search_mode:
            parser = argparse.ArgumentParser(description=__doc__)
            mode = parser.add_mutually_exclusive_group(required=True)
            mode.add_argument("--list-files", action="store_true")
            mode.add_argument("--search-code", metavar="QUERY")
            parser.add_argument("repo_path")
            parser.add_argument("commit_sha")
            parser.add_argument("--name", default="", help="Literal path substring")
            parser.add_argument("--limit", type=int, default=50)
            parser.add_argument("--max-output-chars", type=int, default=20000)
            args = parser.parse_args()
            options = {"filename_query": args.name, "max_results": args.limit,
                       "max_output_chars": args.max_output_chars}
            if args.list_files:
                result = list_files_at_commit(args.repo_path, args.commit_sha, **options)
            else:
                result = search_code_at_commit(args.repo_path, args.commit_sha,
                                                args.search_code, **options)
            print(json.dumps(result, ensure_ascii=True))
        else:
            content = read_file_at_commit(*sys.argv[1:])
            sys.stdout.write(content)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
