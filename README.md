# git-commit-msg

A CLI tool that reads your staged git diff and generates a conventional commit message header using a local LLM (Ollama). No API key, no cost, works offline. Once installed, works globally across all your repos.

![Tests](https://github.com/mtysac/git-conventional-message/actions/workflows/test.yml/badge.svg)

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
pip install --editable "C:\path\to\016_git_conv_m\git_commit_msg"
```

> **Note:** If you get a `BackendUnavailable` error, make sure setuptools is up to date:
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

### Interactive mode

After generating a message, you'll be prompted to act on it:

```
  feat: add login endpoint

[u] Use   [r] Regenerate   [e] Edit   [q] Quit
>
```

- **u** — use the message as-is
- **r** — send the diff again and get a new suggestion
- **e** — manually edit the message before using it
- **q** — abort without committing

---

## 4. Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--model` | `-m` | Ollama model to use (default from config or `llama3`) |
| `--scope` | `-s` | Include a scope e.g. `feat(auth): description` |
| `--copy` | `-c` | Copy the generated message to clipboard |
| `--dry-run` | `-d` | Preview the diff sent to the model without calling Ollama |
| `--list-models` | | List all models available in Ollama |
| `--init-config` | | Create an example `~/.git-msg.toml` config file |
| `--verbose` | `-v` | Enable debug logging |

Examples:

```bash
# default — no scope
git-msg
# feat: add login endpoint

# with scope
git-msg --scope
# feat(auth): add login endpoint

# use a different model
git-msg --model mistral

# preview what gets sent to the model
git-msg --dry-run

# see what models you have installed
git-msg --list-models

# scope + copy to clipboard
git-msg --scope --copy
```

If Ollama is not running you'll see a helpful error:

```
Error: Ollama is not running.
Start it with:  ollama serve
Then pull a model: ollama pull llama3
```

---

## 5. Config file

Set your preferences permanently so you don't need flags every time.

Generate an example config:

```bash
git-msg --init-config
```

This creates `~/.git-msg.toml`:

```toml
# git-msg configuration
# model = "llama3"
# ollama_url = "http://localhost:11434"
# scope = false
# verbose = false
```

Uncomment and edit any values. CLI flags always override the config file.

---

## Configuration via environment variables

| Variable       | Default                  | Description           |
|----------------|--------------------------|-----------------------|
| `OLLAMA_URL`   | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | `llama3`                 | Default model to use  |

Priority order: **CLI flag > config file > environment variable > built-in default**

### Large diffs

If your staged diff is very large, it gets automatically truncated to ~1500 tokens before being sent to the model. This keeps every run safely within llama3's 8k context window. You'll see a warning if truncation happens:

```
Warning: diff is large (XXXX chars), truncating to 6000 chars to stay within model context limit.
```

---

## Development

### Project structure

```
git_commit_msg/
├── git_msg/
│   ├── __init__.py
│   ├── cli.py        # argument parsing, interactive mode, entry point
│   ├── llm.py        # Ollama API calls and prompts
│   ├── git.py        # git diff and truncation
│   └── config.py     # ~/.git-msg.toml loading
├── tests/
│   └── test_main.py
├── main.py           # backwards-compatible shim
├── pyproject.toml
├── ruff.toml
└── README.md
```

### Running tests

```bash
pip install pytest
pytest tests/ -v --import-mode=importlib
```

### Linting

```bash
pip install ruff
ruff check .
```

CI runs lint and tests automatically on every push via GitHub Actions.

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
