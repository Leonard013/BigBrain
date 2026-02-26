"""Configuration and path resolution for BigBrain."""

import os
import shutil
import subprocess
from pathlib import Path


def _find_cli(name: str) -> str:
    """Find a CLI executable by searching PATH, npm global prefix, and common locations."""
    # 1. shutil.which — checks the current PATH
    found = shutil.which(name)
    if found:
        return found

    # 2. Ask npm where its global bin is
    try:
        result = subprocess.run(
            ["npm", "prefix", "-g"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            npm_bin = Path(result.stdout.strip()) / "bin" / name
            if npm_bin.is_file():
                return str(npm_bin)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 3. Common locations
    candidates = [
        Path.home() / ".npm-global" / "bin" / name,
        Path("/usr/local/bin") / name,
        Path("/usr/bin") / name,
    ]
    # nvm versions
    nvm_dir = Path.home() / ".nvm" / "versions" / "node"
    if nvm_dir.is_dir():
        for version_dir in sorted(nvm_dir.iterdir(), reverse=True):
            candidates.append(version_dir / "bin" / name)

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    # 4. Fall back to bare name — let the OS resolve it at runtime
    return name


# CLI commands — auto-detected, overridable via env vars
CODEX_CMD = os.environ.get("BIGBRAIN_CODEX_CMD", _find_cli("codex"))
GEMINI_CMD = os.environ.get("BIGBRAIN_GEMINI_CMD", _find_cli("gemini"))

# Model selection
CODEX_MODEL = os.environ.get("BIGBRAIN_CODEX_MODEL", "gpt-5.3-codex")
GEMINI_MODEL = os.environ.get("BIGBRAIN_GEMINI_MODEL", "gemini-3.1-pro-preview")

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
