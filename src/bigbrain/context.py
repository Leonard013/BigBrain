"""Shared context builder — reads CLAUDE.md and MEMORY.md for prompt injection."""

from pathlib import Path

from bigbrain.config import get_claude_md_path, get_memory_md_path, get_project_path


def load_context_file(path: Path) -> str | None:
    """Read a file safely, returning None if missing or unreadable."""
    try:
        text = path.read_text(encoding="utf-8").strip()
        return text if text else None
    except (OSError, UnicodeDecodeError):
        return None


def build_prompt_with_context(
    prompt: str,
    project_path: str | None = None,
    include_context: bool = True,
) -> str:
    """Prepend CLAUDE.md and MEMORY.md as read-only context to a prompt."""
    if not include_context:
        return prompt

    resolved = get_project_path(project_path)
    claude_md = load_context_file(get_claude_md_path(resolved))
    memory_md = load_context_file(get_memory_md_path(resolved))

    if not claude_md and not memory_md:
        return prompt

    sections: list[str] = ["=== Shared Project Context (read-only) ===", ""]
    if claude_md:
        sections.append(f"[CLAUDE.md]\n{claude_md}\n")
    if memory_md:
        sections.append(f"[MEMORY.md]\n{memory_md}\n")
    sections.append("=== End Shared Context ===")
    sections.append("")
    sections.append(prompt)
    return "\n".join(sections)
