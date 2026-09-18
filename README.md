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


Here is the section you can copy and paste directly into your `README.md`. It seamlessly follows the CLI documentation and focuses on how developers can integrate it into their own Python code.

***

## Usage as a Python Module

You can easily integrate this tool into your own Python applications, CI/CD scripts, or automation pipelines by importing it as a module. 

When used as a module, it exposes a clean, high-level API and raises proper Python exceptions instead of terminating the process.

### Basic Integration

Assuming `app.py` is in your project directory (or installed in your environment):

```python
import app

# Post a simple text comment
comment_url = app.post_pr_comment(
    repo_url="https://github.com/myorg/myrepo",
    pr_number=42,
    text="Automated tests passed successfully!"
)

print(f"Comment created at: {comment_url}")
```

### Advanced Usage & Error Handling

For production applications, you should wrap the call in a `try/except` block to handle potential network, authentication, or parsing errors gracefully.

```python
import app

def notify_pr(repo_url: str, pr_number: int, message: str):
    try:
        # You can optionally pass a token directly, otherwise it uses the GITHUB_TOKEN env var
        url = app.post_pr_comment(
            repo_url=repo_url,
            pr_number=pr_number,
            text=message,
            token="ghp_..." # Optional: overrides environment variable
        )
        print(f"Success: {url}")
        
    except app.GitHubAPIError as e:
        # Raised if GitHub returns a 4xx or 5xx error (e.g., bad token, PR not found)
        print(f"GitHub API rejected the request: {e}")
        
    except app.URLParseError as e:
        # Raised if the repo_url format is invalid
        print(f"Invalid repository URL: {e}")
        
    except ValueError as e:
        # Raised if no GitHub token is provided via argument or environment variable
        print(f"Missing configuration: {e}")

notify_pr(
    repo_url="git@github.com:myorg/myrepo.git",
    pr_number=105,
    message="### Deployment\nBuild `v1.2.3` deployed to staging."
)
```

### Module API Reference

#### `app.post_pr_comment(repo_url, pr_number, text, token=None)`

Posts a text comment to a GitHub Pull Request.

**Parameters:**
| Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `repo_url` | `str` | ✅ | The GitHub repository URL (HTTPS or SSH). |
| `pr_number` | `int` | ✅ | The integer Pull Request number. |
| `text` | `str` | ✅ | The text/markdown content to post. |
| `token` | `str` | ❌ | GitHub PAT. Falls back to the `GITHUB_TOKEN` environment variable if omitted. |

**Returns:**
* `str`: The HTML URL of the newly created comment (e.g., `https://github.com/owner/repo/pull/42#issuecomment-123456789`).

**Raises:**
* `app.GitHubAPIError`: If the GitHub API returns an error response.
* `app.URLParseError`: If the `repo_url` cannot be parsed into a valid owner/repo format.
* `ValueError`: If no authentication token is found.

### Note on Environment Variables
When imported as a module, `app.py` will automatically attempt to load a `.env` file using `python-dotenv` (if installed). If you prefer to manage environment variables in your host application, you can safely ignore the `.env` file or disable `python-dotenv`. The module will always fall back to reading `os.environ.get("GITHUB_TOKEN")`.