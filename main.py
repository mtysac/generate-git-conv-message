import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from argparse import Namespace

OLLAMA_URL: str = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL: str = os.environ.get("OLLAMA_MODEL", "llama3")
MAX_DIFF_CHARS: int = 6000  # ~1500 tokens, leaves plenty of room in llama3's 8k context window
# Budget breakdown: ~120 tokens system prompt + ~1500 tokens diff + ~80 tokens output = ~1700 total

SYSTEM_PROMPT_NO_SCOPE: str = """You are an expert at writing Git conventional commit messages.

Given a git diff, generate a single conventional commit message header in this format:
  <type>: <short description>

Rules:
- type must be one of: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert
- do NOT include a scope
- short description: imperative mood, lowercase, no period, max 72 chars
- Output ONLY the single header line, nothing else
"""

SYSTEM_PROMPT_WITH_SCOPE: str = """You are an expert at writing Git conventional commit messages.

Given a git diff, generate a single conventional commit message header in this format:
  <type>(<scope>): <short description>

Rules:
- type must be one of: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert
- scope should reflect the module, file, or area affected (e.g. auth, api, README)
- short description: imperative mood, lowercase, no period, max 72 chars
- Output ONLY the single header line, nothing else
"""


CONVENTIONAL_TYPES = (
    "feat", "fix", "docs", "style", "refactor",
    "perf", "test", "chore", "ci", "build", "revert",
)


def extract_commit_header(text: str) -> str:
    """Extract just the conventional commit header line from model output.

    Models sometimes prefix the answer with phrases like
    'Here is the commit message:'. This finds the first line that
    looks like a real conventional commit header and returns it.
    """
    for line in text.splitlines():
        line = line.strip()
        if any(line.startswith(t) for t in CONVENTIONAL_TYPES):
            return line
    # Fallback: return the first non-empty line
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return text.strip()


def get_staged_diff() -> str:
    """Run git diff --cached and return the output as a string."""
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


def truncate_diff(diff: str) -> str:
    """Truncate diff to MAX_DIFF_CHARS, cutting at a clean line boundary."""
    if len(diff) <= MAX_DIFF_CHARS:
        return diff
    print(
        f"Warning: diff is large ({len(diff)} chars), truncating to {MAX_DIFF_CHARS} chars to stay within model context limit.\n",
        file=sys.stderr,
    )
    # Keep the start of the diff (file headers + first changes) as they're most informative
    truncated: str = diff[:MAX_DIFF_CHARS]
    # Cut at the last complete line to avoid sending a broken mid-line diff
    last_newline: int = truncated.rfind("\n")
    if last_newline > 0:
        truncated = truncated[:last_newline]
    return truncated + "\n\n[... diff truncated to fit model context limit ...]"


def check_ollama_running() -> bool:
    """Return True if the Ollama server is reachable."""
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
        return True
    except Exception:
        return False


def generate_commit_message(diff: str, model: str, use_scope: bool = False) -> str:
    """Send the diff to Ollama and return a conventional commit message header."""
    if not check_ollama_running():
        print(
            "Error: Ollama is not running.\n"
            "Start it with:  ollama serve\n"
            f"Then pull a model: ollama pull {model}",
            file=sys.stderr,
        )
        sys.exit(1)

    system_prompt: str = SYSTEM_PROMPT_WITH_SCOPE if use_scope else SYSTEM_PROMPT_NO_SCOPE

    payload: bytes = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Generate a conventional commit message for this diff:\n\n{diff}",
            },
        ],
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 80},
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body: dict = json.loads(resp.read().decode())
            return extract_commit_header(body["message"]["content"])
    except urllib.error.URLError as e:
        print(f"Error communicating with Ollama: {e}", file=sys.stderr)
        sys.exit(1)


def copy_to_clipboard(text: str) -> bool:
    """Copy text to the system clipboard. Returns True on success."""
    try:
        subprocess.run(
            ["clip"],
            input=text.encode("utf-16-le"),
            check=True,
            shell=True,
        )
        return True
    except Exception:
        pass
    # fallback for macOS/Linux
    for cmd in [["pbcopy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
        try:
            subprocess.run(cmd, input=text.encode(), check=True)
            return True
        except Exception:
            continue
    return False


def parse_args() -> Namespace:
    """Parse and return CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a conventional commit message from staged git changes using a local LLM."
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Ollama model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--scope", "-s",
        action="store_true",
        help="Include a scope in the commit message e.g. feat(scope): description",
    )
    parser.add_argument(
        "--copy", "-c",
        action="store_true",
        help="Copy the generated message to clipboard",
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Print the diff that would be sent to the model without calling Ollama",
    )
    return parser.parse_args()


def main() -> None:
    args: Namespace = parse_args()

    diff: str = get_staged_diff()

    if not diff.strip():
        print("No staged changes found. Stage your changes with `git add` first.")
        sys.exit(0)

    diff = truncate_diff(diff)

    if args.dry_run:
        print("--- Diff that would be sent to the model ---\n")
        print(diff)
        print(f"\n--- Model: {args.model} | Scope: {'yes' if args.scope else 'no'} ---")
        sys.exit(0)

    print(f"Analyzing staged diff with {args.model}...\n", file=sys.stderr)
    message: str = generate_commit_message(diff, args.model, use_scope=args.scope)
    print(message)

    if args.copy:
        if copy_to_clipboard(message):
            print("\nCopied to clipboard.", file=sys.stderr)
        else:
            print("\nCould not copy to clipboard.", file=sys.stderr)


if __name__ == "__main__":
    main()
