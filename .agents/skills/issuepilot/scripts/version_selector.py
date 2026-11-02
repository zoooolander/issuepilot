"""Report the current local HEAD and working-tree state without changing Git."""

import json
import os
from pathlib import Path
import subprocess
import sys


def _run_git(repo_path, *args):
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    try:
        return subprocess.run(
            ["git", "--no-pager", "--no-replace-objects", "-c", "core.fsmonitor=false",
             "-C", str(repo_path), *args],
            capture_output=True, check=True, timeout=15, env=env, shell=False,
        ).stdout
    except FileNotFoundError as exc:
        raise RuntimeError("Git executable not found.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Git command timed out.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Git command failed: {detail}") from exc
    except OSError as exc:
        raise RuntimeError(f"Unable to execute Git: {exc}") from exc


def select_version(repo_path) -> dict:
    """Snapshot HEAD and dirty state; neither is proof of bug reproduction.

    Ignored files are not untracked changes. Bare repositories and repositories
    without a commit have no supported checkout to analyze and are rejected.
    """
    repo = Path(repo_path).resolve()
    if not repo.is_dir():
        raise ValueError("Repository path must be an existing directory.")
    if _run_git(repo, "rev-parse", "--is-inside-work-tree").strip() != b"true":
        raise ValueError("Repository must have a working tree; bare repositories are unsupported.")
    root = _run_git(repo, "rev-parse", "--show-toplevel").decode("utf-8").rstrip("\r\n")
    repo = Path(root)
    head_sha = _run_git(repo, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    status = _run_git(repo, "status", "--porcelain=v1", "-z",
                      "--untracked-files=all", "--ignore-submodules=none")
    final_head = _run_git(repo, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    if final_head != head_sha:
        raise RuntimeError("HEAD changed during inspection; run version selection again.")
    return {
        "repo_path": str(repo.resolve()),
        "head_sha": head_sha,
        "is_dirty": bool(status),
        "worktree_status": "dirty" if status else "clean",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error: Usage: version_selector.py REPOSITORY", file=sys.stderr)
        sys.exit(1)
    try:
        print(json.dumps(select_version(sys.argv[1]), ensure_ascii=True, indent=2))
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
