"""Read UTF-8 text from an explicit local Git commit without changing it."""

import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys


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

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Error: Usage: repo_inspector.py REPOSITORY COMMIT_SHA FILE_PATH", file=sys.stderr)
        sys.exit(1)
    try:
        content = read_file_at_commit(*sys.argv[1:])
        sys.stdout.write(content)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
