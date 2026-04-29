# git-commit-msg

A CLI tool that reads your staged git diff and generates a conventional commit message header using a local LLM (Ollama). No API key, no cost, works offline. Once installed, works globally across all your repos.

Website about conventional commits: https://www.conventionalcommits.org/en/v1.0.0/

![Tests](https://github.com/mtysac/generate-git-conv-message/actions/workflows/test.yml/badge.svg)

<!-- Demo GIF: record with ScreenToGif (Windows) or asciinema and drop the file here -->
<!-- ![demo](demo.gif) -->

---

## 1. Install Ollama

Download and install from https://ollama.com/download

Then pull a model (llama3 is a good default):

```bash
ollama pull llama3
```

Start the Ollama server (it may start automatically after install):

```bash
ollama serve
```

To stop it, press `Ctrl+C` in the terminal where it's running. If it's running as a background service, stop it with:

```bash
# Linux
sudo service ollama stop

# macOS
killall Ollama

# Windows
Get-Process | Where-Object {$_.ProcessName -like '*ollama*'} | Stop-Process 

# if you installed Ollama with homebrew
brew services stop ollama

```
or open Task Manager (Ctrl + Shift + Esc), find the processes named "ollama" or similar, and manually end those tasks to stop Ollama

These commands do not work when stopping it from running (it will restart right after):

```bash
# macOS
pkill ollama

# Windows
taskkill /F /IM ollama.exe
```

You can verify Ollama is running by visiting http://localhost:11434 in your browser. If you see `Ollama is running`, you're good.

---

## 2. Install this tool globally

This makes `git-msg` available in every repo on your machine. Run this once from anywhere — replace the path with wherever this project lives on your machine:

```bash
pip install --editable "C:\path\to\git-conventional-message"
```

> **Note:** Use `pyproject.toml`-based install (already configured). If you get a `BackendUnavailable` error, make sure setuptools is up to date:
> ```bash
> pip install --upgrade setuptools
> ```

---

## 3. Usage

From any git repo, stage your changes then run:

```bash
git add .
git-msg
```

Or pipe directly into a commit:

```bash
git commit -m "$(git-msg)"
```

**Flags:**

| Flag | Short | Description |
|------|-------|-------------|
| `--model` | `-m` | Ollama model to use (default: `llama3`) |
| `--scope` | `-s` | Include a scope in the message e.g. `feat(auth): description` |
| `--copy` | `-c` | Copy the generated message to clipboard |
| `--dry-run` | `-d` | Print the diff that would be sent to the model without calling Ollama |

Examples:

```bash
# default — no scope
git-msg
# feat: add login endpoint

# with scope
git-msg --scope
# feat(auth): add login endpoint

# preview what gets sent to the model
git-msg --dry-run

# use a different model
git-msg --model mistral

# scope + copy to clipboard
git-msg --scope --copy

# all flags
git-msg --model mistral --scope --copy
```

If Ollama is not running you'll see a helpful error:

```
Error: Ollama is not running.
Start it with:  ollama serve
Then pull a model: ollama pull llama3
```

---

## Configuration

Override defaults with environment variables:

| Variable       | Default                  | Description           |
|----------------|--------------------------|-----------------------|
| `OLLAMA_URL`   | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | `llama3`                 | Default model to use  |

The `--model` flag takes precedence over `OLLAMA_MODEL` if both are set.

### Large diffs

If your staged diff is very large, it gets automatically truncated to ~1500 tokens before being sent to the model. This keeps every run safely within llama3's 8k context window. You'll see a warning in the terminal if truncation happens:

```
Warning: diff is large (XXXX chars), truncating to 6000 chars to stay within model context limit.
```

The tool always cuts at a complete line so the diff sent to the model is clean.

---

## Development

### Running tests

```bash
pip install pytest
pytest tests/ -v --import-mode=importlib
```

Tests cover diff truncation, Ollama connectivity checks, git diff parsing, clipboard handling, and commit header extraction. CI runs lint (ruff) then tests automatically on every push via GitHub Actions.

### Linting

```bash
pip install ruff
ruff check .
```

---

## Uninstall

```bash
pip uninstall git-commit-msg
```

To also remove the Ollama model:

```bash
ollama rm llama3
```

To remove Ollama itself, uninstall it like any other application on your OS.

---

## Conventional Commit Types

| Type       | When to use                          |
|------------|--------------------------------------|
| `feat`     | New feature                          |
| `fix`      | Bug fix                              |
| `docs`     | Documentation only                   |
| `style`    | Formatting, no logic change          |
| `refactor` | Code restructure, no feature/fix     |
| `perf`     | Performance improvement              |
| `test`     | Adding or fixing tests               |
| `chore`    | Build process, tooling, dependencies |
| `ci`       | CI/CD configuration                  |
| `build`    | Build system changes                 |
| `revert`   | Revert a previous commit             |
