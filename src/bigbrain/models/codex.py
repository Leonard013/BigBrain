"""Codex CLI adapter — invokes `codex exec` and parses JSONL event stream."""

import json
import os

from bigbrain.config import CODEX_CMD
from bigbrain.models.base import CLIModelAdapter


class CodexAdapter(CLIModelAdapter):
    @property
    def name(self) -> str:
        return "codex"

    @property
    def cli_command(self) -> str:
        return CODEX_CMD

    def build_command(self, prompt: str) -> list[str]:
        return [self.cli_command, "exec", "--quiet", "--json", "--full-auto", prompt]

    def build_env(self) -> dict[str, str]:
        env = dict(os.environ)
        # CODEX_API_KEY takes precedence, fall back to OPENAI_API_KEY
        api_key = os.environ.get("CODEX_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if api_key:
            env["OPENAI_API_KEY"] = api_key
        return env

    def parse_output(self, stdout: str, stderr: str) -> str:
        """Parse JSONL event stream from codex exec --json.

        Looks for item.completed events with item.type == "agent_message"
        and extracts their text content.
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

            # Handle codex JSONL event format
            event_type = event.get("type")
            if event_type == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    # Extract text from content array
                    for part in item.get("content", []):
                        if part.get("type") == "output_text":
                            text = part.get("text", "").strip()
                            if text:
                                messages.append(text)
            elif event_type == "message":
                # Simpler message format fallback
                text = event.get("content", "").strip()
                if text:
                    messages.append(text)

        if messages:
            return "\n\n".join(messages)

        # Fallback: return raw stdout if no structured events parsed
        return stdout.strip()
