#!/usr/bin/env python3

import os
import re
import sys
from typing import Tuple, Optional

import requests

# Safely load .env if it exists (useful when running as CLI or in host app)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Custom Exceptions (Crucial for module usage)
# ---------------------------------------------------------------------------
class GitHubAPIError(Exception):
    """Raised when the GitHub API returns an error."""
    pass

class URLParseError(ValueError):
    """Raised when a URL cannot be parsed."""
    pass


# ---------------------------------------------------------------------------
# URL Parsing Helpers
# ---------------------------------------------------------------------------
def parse_repo_url(url: str) -> Tuple[str, str]:
    """Extract owner and repo from various GitHub URL formats."""
    pattern = r"(?:https?://(?:[^@/]+@)?github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+)/([^/.]+?)(?:\.git)?/?$"
    match = re.match(pattern, url)
    if not match:
        raise URLParseError(f"Could not parse owner/repo from URL: {url}")
    return match.group(1), match.group(2)


# ---------------------------------------------------------------------------
# GitHub API Client
# ---------------------------------------------------------------------------
class GitHubClient:
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        self.base_url = base_url.rstrip("/")

    def post_issue_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict:
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        return self._post(url, {"body": body})

    def _post(self, url: str, payload: dict) -> dict:
        resp = self.session.post(url, json=payload)
        if not resp.ok:
            # Raise an exception instead of sys.exit() so the host app can catch it
            raise GitHubAPIError(f"GitHub API error {resp.status_code}: {resp.text}")
        return resp.json()


# ---------------------------------------------------------------------------
# High-Level Module API (Use this in your other project)
# ---------------------------------------------------------------------------
def post_pr_comment(
    repo_url: str, 
    pr_number: int, 
    text: str, 
    token: Optional[str] = None
) -> str:
    """
    Posts a text comment to a GitHub Pull Request.
    
    Args:
        repo_url: The GitHub repository URL (HTTPS or SSH).
        pr_number: The integer PR number.
        text: The text content to post.
        token: Optional GitHub PAT. Falls back to GITHUB_TOKEN env var.
        
    Returns:
        The HTML URL of the created comment.
        
    Raises:
        URLParseError: If the repo_url is invalid.
        ValueError: If no token is provided/found.
        GitHubAPIError: If the GitHub API rejects the request.
    """
    # 1. Resolve Token
    auth_token = token or os.environ.get("GITHUB_TOKEN")
    if not auth_token:
        raise ValueError("GitHub token is required. Pass it via 'token' or set GITHUB_TOKEN env var.")

    # 2. Parse URL
    owner, repo = parse_repo_url(repo_url)

    # 3. Post Comment
    client = GitHubClient(auth_token)
    result = client.post_issue_comment(owner, repo, pr_number, text)
    
    return result.get("html_url", "Unknown URL")


# ---------------------------------------------------------------------------
# CLI Implementation (Kept for standalone usage)
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Post a comment to a GitHub PR.")
    parser.add_argument("repo_url", help="GitHub repository URL")
    parser.add_argument("pr", type=int, help="PR number")
    parser.add_argument("--body", required=True, help="Comment text")
    parser.add_argument("--token", help="GitHub PAT (overrides env var)")
    
    args = parser.parse_args()

    try:
        url = post_pr_comment(args.repo_url, args.pr, args.body, args.token)
        print(f"Comment posted: {url}")
    except (URLParseError, ValueError, GitHubAPIError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()