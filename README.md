# git-commit-msg

A CLI tool that reads your staged git diff and generates a conventional commit message header using a local LLM (Ollama). No API key, no cost, works offline. Once installed, works globally across all your repos.

![Tests](https://github.com/mtysac/generate-git-conv-messa/actions/workflows/test.yml/badge.svg)

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
# macOS/Linux
pkill ollama

# Windows
taskkill /IM ollama.exe /F
```

You can verify Ollama is running by visiting http://localhost:11434 in your browser. If you see `Ollama is running`, you're good.

---

## 2. Install this tool globally

This makes `git-msg` available in every repo on your machine. Run this once from anywhere — replace the path with wherever this project lives on your machine:

```bash
pip install --editable "C:\path\to\016_git_conv_m\git_commit_msg"
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
| `--copy` | `-c` | Copy the generated message to clipboard |

Examples:

```bash
# use a different model
git-msg --model mistral

# copy result straight to clipboard
git-msg --copy

# both
git-msg --model mistral --copy
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

Tests cover diff truncation, Ollama connectivity checks, git diff parsing, and clipboard handling. CI runs automatically on every push via GitHub Actions.

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
