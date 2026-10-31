import re
import sys
import json
import urllib.request
from urllib.error import HTTPError, URLError


def parse_pr_url(url: str) -> dict:
    pattern = r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/([1-9][0-9]*)/?$"
    match = re.fullmatch(pattern, url)

    if not match:
        raise ValueError("Invalid GitHub PR URL")

    owner, repo, pr_number = match.groups()

    return {
        "owner": owner,
        "repo": repo,
        "pr_number": int(pr_number)
    }


def fetch_pr(owner: str, repo: str, pr_number: int) -> dict:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
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
        "owner": owner,
        "repo": repo,
        "pr_number": pr_number,
        "title": data["title"],
        "state": data["state"],
        "merged": data["merged"],
        "base_sha": data["base"]["sha"],
        "head_sha": data["head"]["sha"]
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please provide a GitHub PR URL.", file=sys.stderr)
        sys.exit(1)

    try:
        parsed = parse_pr_url(sys.argv[1])
        result = fetch_pr(parsed["owner"], parsed["repo"], parsed["pr_number"])
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except HTTPError as e:
        if e.code == 404:
            print("Error: GitHub PR not found.", file=sys.stderr)
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
