***

# GitHub PR Commenter CLI (`app.py`)

A lightweight, zero-config CLI tool to post comments (Text, Markdown, or HTML) to GitHub Pull Requests. It supports top-level PR comments and inline code review comments.

## Quick Start

```bash
# 1. Install dependencies
pip install requests html2text python-dotenv

# 2. Set up your token
echo "GITHUB_TOKEN=ghp_YOUR_TOKEN_HERE" > .env

# 3. Post a comment
python app.py https://github.com/owner/repo 42 --body "LGTM!"
```

---

## Setup & Configuration

### 1. Virtual Environment & Dependencies
It is highly recommended to use a virtual environment.

```bash
# Create and activate venv
python -m venv venv
source venv/bin/activate        # On macOS/Linux
# venv\Scripts\activate         # On Windows

# Install required packages
pip install requests html2text python-dotenv
```

### 2. Environment Variables (`.env`)
Create a `.env` file in the root directory. The script uses `python-dotenv` to load this automatically.

```env
# REQUIRED: GitHub Personal Access Token
# Must have the 'repo' scope enabled.
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OPTIONAL: Override for GitHub Enterprise Server
# GITHUB_API_URL=https://github.yourcompany.com/api/v3
```

> **Security:** Ensure `.env` is added to your `.gitignore` to prevent leaking your PAT.

---

## Usage Guide

### Basic Syntax
```bash
python app.py <repo_url> <pr_number_or_url> [options]
```

### 1. Standard Top-Level Comments
You can pass the repo URL and PR number (or the full PR URL) as positional arguments.

```bash
# Using PR number
python app.py https://github.com/myorg/myrepo 42 --body "Build passed!"

# Using full PR URL
python app.py https://github.com/myorg/myrepo https://github.com/myorg/myrepo/pull/42 --body "Approved"
```

### 2. Markdown & Multi-line Comments
GitHub natively renders Markdown. Use `\n` for newlines in bash, or wrap the string in quotes.

```bash
python app.py https://github.com/myorg/myrepo 42 --body "## Summary
- ✅ Tests pass
- ⚠️ Needs docs
**LGTM**"
```

### 3. HTML Content
If you have an HTML report, use `--format html`. The script will automatically convert it to GitHub-flavored Markdown using `html2text`.

```bash
# From a string
python app.py https://github.com/myorg/myrepo 42 --format html --body "<h1>Report</h1><p>Success</p>"

# From a file
python app.py https://github.com/myorg/myrepo 42 --format html --body-file coverage_report.html
```

### 4. Inline Code Review Comments
To comment on a specific line of code, provide the file `--path` and `--line`. The script will automatically fetch the latest commit SHA.

```bash
python app.py https://github.com/myorg/myrepo 42 \
    --path src/main.py \
    --line 42 \
    --body "Consider extracting this into a helper function."
```

### 5. Piping Input (CI/CD & Automation)
You can pipe the output of other commands directly into the comment body via `stdin`.

```bash
# Pipe a text file
cat release_notes.txt | python app.py https://github.com/myorg/myrepo 42

# Pipe the output of a linter or test runner
npm run lint | python app.py https://github.com/myorg/myrepo 42 --body-file -
```
*(Note: When piping, you don't need `--body` or `--body-file`, it reads from stdin automatically).*

---

## CLI Arguments Reference

| Argument | Required | Description |
| :--- | :---: | :--- |
| `repo_url` | ✅ | GitHub repo URL (HTTPS or SSH). |
| `pr` | ✅ | PR number (e.g., `42`) or full PR URL. |
| `--body` | ❌ | The comment text. |
| `--body-file`| ❌ | Path to a file containing the comment text. |
| `--format` | ❌ | `text`, `markdown` (default), or `html`. |
| `--path` | ❌ | File path for inline comments (e.g., `src/app.py`). |
| `--line` | ❌ | Line number for inline comments. |
| `--token` | ❌ | Pass PAT directly (overrides `.env`). |
| `--dry-run` | ❌ | Prints the formatted output without posting to GitHub. |

---

## Troubleshooting

**Q: I'm getting a `401 Unauthorized` or `403 Forbidden` error.**
* **A:** Check your `GITHUB_TOKEN`. Ensure it hasn't expired. If it's a Classic PAT, ensure the **`repo`** scope is checked. If it's a Fine-Grained PAT, ensure it has **Read and Write** access to "Pull requests" and "Issues" for the specific repository.

**Q: I'm getting a `404 Not Found` error, but the PR exists.**
* **A:** GitHub returns 404 instead of 403 for private repos if the token lacks permissions. Verify your PAT has access to the repository. Also, ensure the `repo_url` exactly matches the repository name (case-sensitive).

**Q: My HTML comment looks broken on GitHub.**
* **A:** GitHub aggressively sanitizes raw HTML in comments (stripping `<style>`, `<script>`, and certain tags). The script attempts to convert HTML to Markdown via `html2text`. For best results, write comments in Markdown natively. Use `--dry-run` to preview how the HTML is being converted before posting.

**Q: The inline comment failed with a "path not in diff" error.**
* **A:** GitHub only allows inline comments on lines that are actually part of the PR's diff (added or modified lines). You cannot comment on unchanged lines.