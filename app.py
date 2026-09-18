#!/usr/bin/env python3
"""
GitHub PR Comment Writer (URL-based)

Posts comments to GitHub Pull Requests using just the Repo URL and a PAT.
Supports plain text, Markdown, and HTML content.

Usage:
    python pr_comment.py <repo_url> <pr_number_or_url> --body "LGTM!"
"""

import argparse
import json
import os
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Tuple

import requests
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# URL Parsing Helpers
# ---------------------------------------------------------------------------
def parse_repo_url(url: str) -> Tuple[str, str]:
    """Extract owner and repo from various GitHub URL formats."""
    # Supports:
    # https://github.com/owner/repo
    # https://github.com/owner/repo.git
    # git@github.com:owner/repo.git
    # ssh://git@github.com/owner/repo.git
    pattern = r"(?:https?://(?:[^@/]+@)?github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+)/([^/.]+?)(?:\.git)?/?$"
    match = re.match(pattern, url)
    if not match:
        raise ValueError(f"❌ Could not parse owner/repo from URL: {url}")
    return match.group(1), match.group(2)


def parse_pr_identifier(pr_input: str) -> int:
    """Extract PR number from an integer string or a full PR URL."""
    if pr_input.isdigit():
        return int(pr_input)
    
    # Try to extract from a URL like https://github.com/owner/repo/pull/123
    match = re.search(r"/pull/(\d+)", pr_input)
    if match:
        return int(match.group(1))
        
    raise ValueError(f"❌ Could not parse PR number from: {pr_input}. Provide a number or a PR URL.")


# ---------------------------------------------------------------------------
# Content format handling
# ---------------------------------------------------------------------------
class ContentFormat(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"

def convert_html_to_markdown(html: str) -> str:
    try:
        import html2text
        converter = html2text.HTML2Text()
        converter.body_width = 0
        return converter.handle(html).strip()
    except ImportError:
        print("⚠️  html2text not installed. Passing HTML as-is.", file=sys.stderr)
        return html

def prepare_body(raw: str, fmt: ContentFormat) -> str:
    if fmt == ContentFormat.HTML:
        return convert_html_to_markdown(raw)
    return raw


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

    def post_review_comment(self, owner: str, repo: str, pr_number: int, body: str, 
                            commit_id: str, path: str, line: int, side: str = "RIGHT") -> dict:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        payload = {"body": body, "commit_id": commit_id, "path": path, "line": line, "side": side}
        return self._post(url, payload)

    def get_latest_commit_sha(self, owner: str, repo: str, pr_number: int) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()["head"]["sha"]

    def _post(self, url: str, payload: dict) -> dict:
        resp = self.session.post(url, json=payload)
        if not resp.ok:
            print(f"❌ GitHub API error {resp.status_code}:\n{resp.text}", file=sys.stderr)
            sys.exit(1)
        return resp.json()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Post a comment to a GitHub PR using just URLs.")
    
    # Positional arguments for maximum convenience
    p.add_argument("repo_url", help="GitHub repository URL (e.g., https://github.com/owner/repo)")
    p.add_argument("pr", help="PR number (e.g., 42) or PR URL (e.g., https://github.com/owner/repo/pull/42)")
    
    p.add_argument("--format", type=ContentFormat, choices=list(ContentFormat), 
                   default=ContentFormat.MARKDOWN, help="Content format (default: markdown)")
    
    body_group = p.add_mutually_exclusive_group()
    body_group.add_argument("--body", help="Comment body as a string")
    body_group.add_argument("--body-file", help="Read comment body from a file")
    
    p.add_argument("--token", help="GitHub PAT (overrides GITHUB_TOKEN env var)")

    # Inline comment options
    p.add_argument("--path", help="File path for an inline review comment")
    p.add_argument("--line", type=int, help="Line number for an inline review comment")
    
    p.add_argument("--dry-run", action="store_true", help="Print the prepared comment instead of posting")
    return p

def read_body(args) -> str:
    if args.body_file:
        return Path(args.body_file).read_text(encoding="utf-8")
    if args.body:
        return args.body
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("❌ Provide --body, --body-file, or pipe content via stdin.", file=sys.stderr)
    sys.exit(1)

def main():
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    # 1. Parse URLs
    try:
        owner, repo = parse_repo_url(args.repo_url)
        pr_number = parse_pr_identifier(args.pr)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    # 2. Read & prepare body
    raw_body = read_body(args)
    body = prepare_body(raw_body, args.format)

    if args.dry_run:
        print(f"── Prepared comment for {owner}/{repo} PR #{pr_number} ──")
        print(body)
        return

    # 3. Authenticate
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ Provide a token via --token or set the GITHUB_TOKEN environment variable.", file=sys.stderr)
        sys.exit(1)

    client = GitHubClient(token)

    # 4. Post
    if args.path and args.line:
        commit_sha = client.get_latest_commit_sha(owner, repo, pr_number)
        result = client.post_review_comment(owner, repo, pr_number, body, commit_sha, args.path, args.line)
        print(f"✅ Inline comment posted: {result['html_url']}")
    else:
        result = client.post_issue_comment(owner, repo, pr_number, body)
        print(f"✅ Comment posted: {result['html_url']}")

if __name__ == "__main__":
    main()