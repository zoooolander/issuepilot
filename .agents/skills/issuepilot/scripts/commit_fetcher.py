import re
import sys
import json
import urllib.request
from urllib.error import HTTPError, URLError


def parse_commit_url(url: str) -> dict:
    pattern = r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/commit/([0-9a-fA-F]{40})/?$"
    match = re.fullmatch(pattern, url)

    if not match:
        raise ValueError("Invalid GitHub Commit URL")

    owner, repo, sha = match.groups()

    return {
        "owner": owner,
        "repo": repo,
        "sha": sha
    }


def fetch_commit(owner: str, repo: str, sha: str) -> dict:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/commits/{sha}"
    request = urllib.request.Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "IssuePilot"
        }
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.load(response)

    return {
        "sha": data["sha"],
        "message": data["message"],
        "parents": [parent["sha"] for parent in data["parents"]],
        "author": data["author"]
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please provide a GitHub Commit URL.", file=sys.stderr)
        sys.exit(1)

    try:
        parsed = parse_commit_url(sys.argv[1])
        result = fetch_commit(parsed["owner"], parsed["repo"], parsed["sha"])
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except HTTPError as e:
        if e.code == 404:
            print("Error: GitHub Commit not found.", file=sys.stderr)
        elif e.code == 429 or (
            e.code == 403 and (e.headers or {}).get("X-RateLimit-Remaining") == "0"
        ):
            print("Error: GitHub API rate limit exceeded.", file=sys.stderr)
        else:
            print(f"Error: GitHub API returned HTTP {e.code}.", file=sys.stderr)
        sys.exit(1)

    except URLError as e:
        print(f"Error: Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)
