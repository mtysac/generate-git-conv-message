import subprocess
import sys
import os
import json
import urllib.request
import urllib.error

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

SYSTEM_PROMPT = """You are an expert at writing Git conventional commit messages.

Given a git diff, generate a single conventional commit message following this format:
  <type>(<scope>): <short description>

  [optional body]

  [optional footer]

Rules:
- type must be one of: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert
- scope is optional but recommended (e.g. the module or file affected)
- short description: imperative mood, lowercase, no period, max 72 chars
- body: explain *what* and *why*, not *how* (wrap at 72 chars)
- footer: reference issues if relevant (e.g. Closes #123)
- Output ONLY the commit message, no extra commentary or markdown fences
"""


def get_staged_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--cached"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print(f"Error running git diff: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout or ""


def check_ollama_running() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
        return True
    except Exception:
        return False


def generate_commit_message(diff: str) -> str:
    if not check_ollama_running():
        print(
            "Error: Ollama is not running.\n"
            "Start it with:  ollama serve\n"
            f"Then pull a model: ollama pull {OLLAMA_MODEL}",
            file=sys.stderr,
        )
        sys.exit(1)

    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Generate a conventional commit message for this diff:\n\n{diff}",
            },
        ],
        "stream": False,
        "options": {"temperature": 0.2},
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode())
            return body["message"]["content"].strip()
    except urllib.error.URLError as e:
        print(f"Error communicating with Ollama: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    diff = get_staged_diff()

    if not diff.strip():
        print("No staged changes found. Stage your changes with `git add` first.")
        sys.exit(0)

    print(f"Analyzing staged diff with {OLLAMA_MODEL}...\n", file=sys.stderr)
    message = generate_commit_message(diff)
    print(message)


if __name__ == "__main__":
    main()
