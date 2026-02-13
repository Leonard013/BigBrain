"""Tests for context.py — shared context building."""

import tempfile
from pathlib import Path

from bigbrain.context import build_prompt_with_context, load_context_file


def test_load_context_file_missing():
    """Returns None for a non-existent file."""
    assert load_context_file(Path("/nonexistent/CLAUDE.md")) is None


def test_load_context_file_empty():
    """Returns None for an empty file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("")
        f.flush()
        assert load_context_file(Path(f.name)) is None


def test_load_context_file_with_content():
    """Returns trimmed content for a file with text."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("  hello world  \n")
        f.flush()
        result = load_context_file(Path(f.name))
        assert result == "hello world"


def test_build_prompt_no_context():
    """With include_context=False, returns prompt unchanged."""
    prompt = "What is the meaning of life?"
    result = build_prompt_with_context(prompt, include_context=False)
    assert result == prompt


def test_build_prompt_no_files():
    """With no CLAUDE.md or MEMORY.md, returns prompt unchanged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = build_prompt_with_context("test prompt", project_path=tmpdir)
        assert result == "test prompt"


def test_build_prompt_with_claude_md():
    """Injects CLAUDE.md content when present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("Project rules here")

        result = build_prompt_with_context("my question", project_path=tmpdir)
        assert "=== Shared Project Context (read-only) ===" in result
        assert "[CLAUDE.md]" in result
        assert "Project rules here" in result
        assert "my question" in result
        assert "=== End Shared Context ===" in result
