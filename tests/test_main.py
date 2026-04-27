from unittest.mock import MagicMock, patch

import pytest

from main import (
    MAX_DIFF_CHARS,
    check_ollama_running,
    copy_to_clipboard,
    extract_commit_header,
    get_staged_diff,
    truncate_diff,
)

# --- extract_commit_header ---

def test_extract_commit_header_clean_input():
    assert extract_commit_header("feat(auth): add login endpoint") == "feat(auth): add login endpoint"

def test_extract_commit_header_strips_preamble():
    text = "Here is the conventional commit message header:\ndocs(README): update readme"
    assert extract_commit_header(text) == "docs(README): update readme"

def test_extract_commit_header_strips_extra_lines():
    text = "Sure! Here you go:\nfix(api): handle null response\n\nLet me know if you need changes."
    assert extract_commit_header(text) == "fix(api): handle null response"

def test_extract_commit_header_fallback_to_first_nonempty_line():
    # No conventional type found, should return first non-empty line
    text = "\n\nsome unexpected output"
    assert extract_commit_header(text) == "some unexpected output"


# --- truncate_diff ---

def test_truncate_diff_short_diff_unchanged():
    diff = "small diff"
    assert truncate_diff(diff) == diff


def test_truncate_diff_large_diff_is_truncated():
    diff = "a" * (MAX_DIFF_CHARS + 1000)
    result = truncate_diff(diff)
    assert len(result) <= MAX_DIFF_CHARS + 100  # allows for the appended notice
    assert "[... diff truncated" in result


def test_truncate_diff_cuts_at_newline():
    # Build a diff that exceeds the limit, with newlines throughout
    line = "x" * 100 + "\n"
    diff = line * (MAX_DIFF_CHARS // len(line) + 5)
    result = truncate_diff(diff)
    notice = "\n\n[... diff truncated to fit model context limit ...]"
    # Result must contain the truncation notice
    assert notice in result
    # The body before the notice must not contain a broken (non-newline-terminated) mid-line cut
    body = result[: result.index(notice)]
    assert "\n" in body  # body has complete lines


def test_truncate_diff_exactly_at_limit_unchanged():
    diff = "b" * MAX_DIFF_CHARS
    assert truncate_diff(diff) == diff


# --- check_ollama_running ---

def test_check_ollama_running_returns_true_when_reachable():
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        assert check_ollama_running() is True


def test_check_ollama_running_returns_false_when_unreachable():
    with patch("urllib.request.urlopen", side_effect=Exception("connection refused")):
        assert check_ollama_running() is False


# --- get_staged_diff ---

def test_get_staged_diff_returns_output():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "diff --git a/file.py b/file.py\n+new line\n"
    with patch("subprocess.run", return_value=mock_result):
        result = get_staged_diff()
    assert result == mock_result.stdout


def test_get_staged_diff_returns_empty_string_when_no_changes():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result):
        result = get_staged_diff()
    assert result == ""


def test_get_staged_diff_exits_on_git_error():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "not a git repository"
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(SystemExit):
            get_staged_diff()


# --- copy_to_clipboard ---

def test_copy_to_clipboard_returns_true_on_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = copy_to_clipboard("feat(scope): test message")
    assert result is True


def test_copy_to_clipboard_returns_false_when_all_fail():
    with patch("subprocess.run", side_effect=Exception("not found")):
        result = copy_to_clipboard("feat: test")
    assert result is False
