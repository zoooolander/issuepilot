import re
import sys
import json
import urllib.request


def parse_issue_url(url: str) -> dict:
    pattern = r"^https://github\.com/([^/]+)/([^/]+)/issues/(\d+)/?$"

    match = re.fullmatch(pattern, url)

    if not match:
        raise ValueError("Invalid GitHub Issue URL")

    owner, repo, issue_number = match.groups()

    return {
        "owner": owner,
        "repo": repo,
        "issue_number": int(issue_number)
    }

def fetch_issue(owner: str, repo: str, issue_number: int) -> dict:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"

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
        "issue_number": issue_number,
        "title": data["title"],
        "state": data["state"],
        "body": data["body"],
        "labels": [label["name"] for label in data["labels"]]
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please provide a GitHub Issue URL.")
        sys.exit(1)

    url = sys.argv[1]
    parsed = parse_issue_url(url)

    result = fetch_issue(
        parsed["owner"],
        parsed["repo"],
        parsed["issue_number"]
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))