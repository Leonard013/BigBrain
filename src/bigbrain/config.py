"""Configuration and path resolution for BigBrain."""

import os
from pathlib import Path

# CLI commands — use full paths since MCP subprocess won't have user PATH
CODEX_CMD = os.environ.get(
    "BIGBRAIN_CODEX_CMD",
    str(Path.home() / ".npm-global" / "bin" / "codex"),
)
GEMINI_CMD = os.environ.get(
    "BIGBRAIN_GEMINI_CMD",
    str(Path.home() / ".npm-global" / "bin" / "gemini"),
)

# Model selection
CODEX_MODEL = os.environ.get("BIGBRAIN_CODEX_MODEL", "gpt-5.3-codex")
GEMINI_MODEL = os.environ.get("BIGBRAIN_GEMINI_MODEL", "gemini-3-pro-preview")

# Timeouts (seconds)
DEFAULT_TIMEOUT = 120
CONSENSUS_TIMEOUT = 180
DEBATE_TIMEOUT = 300

# Environment variable for project path
PROJECT_PATH_ENV = "BIGBRAIN_PROJECT_PATH"


def get_project_path(override: str | None = None) -> Path:
    """Resolve project path from override, env var, or cwd."""
    if override:
        return Path(override).resolve()
    env_path = os.environ.get(PROJECT_PATH_ENV)
    if env_path:
        return Path(env_path).resolve()
    return Path.cwd()


def _project_slug(project_path: Path) -> str:
    """Convert project path to Claude memory slug format: -home-user-project."""
    return str(project_path).replace("/", "-").lstrip("-")


def get_claude_md_path(project_path: Path) -> Path:
    """Return path to the project's CLAUDE.md."""
    return project_path / ".claude" / "CLAUDE.md"


def get_memory_md_path(project_path: Path) -> Path:
    """Return path to Claude's auto-memory MEMORY.md for this project."""
    slug = _project_slug(project_path)
    return Path.home() / ".claude" / "projects" / slug / "memory" / "MEMORY.md"
