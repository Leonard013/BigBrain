"""Codex CLI adapter — invokes `codex exec` and parses JSONL event stream."""

import json

from bigbrain.config import CODEX_CMD, CODEX_MODEL
from bigbrain.models.base import CLIModelAdapter


class CodexAdapter(CLIModelAdapter):
    @property
    def name(self) -> str:
        return "codex"

    @property
    def cli_command(self) -> str:
        return CODEX_CMD

    def build_command(self, prompt: str) -> list[str]:
        return [
            self.cli_command, "exec",
            "--model", CODEX_MODEL,
            "--json", "--full-auto", "--skip-git-repo-check",
            prompt,
        ]

    def parse_output(self, stdout: str, stderr: str) -> str:
        """Parse JSONL event stream from codex exec --json.

        Per docs, item.completed events have: {"type":"item.completed",
        "item":{"id":"...","type":"agent_message","text":"..."}}
        The text field lives directly on item, not in a nested content array.
        Also handles content array format as fallback for compatibility.
        """
        messages: list[str] = []
        for line in stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = event.get("type")
            if event_type == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    # Primary: text directly on item (documented format)
                    text = item.get("text", "").strip()
                    if text:
                        messages.append(text)
                        continue
                    # Fallback: content array format
                    for part in item.get("content", []):
                        if isinstance(part, dict):
                            t = part.get("text", "").strip()
                            if t:
                                messages.append(t)

        if messages:
            return "\n\n".join(messages)

        # Fallback: return raw stdout if no structured events parsed
        return stdout.strip()
