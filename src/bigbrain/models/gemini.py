"""Gemini CLI adapter — invokes `gemini -p` and parses JSON output."""

import json

from bigbrain.config import GEMINI_CMD, GEMINI_MODEL
from bigbrain.models.base import CLIModelAdapter


class GeminiAdapter(CLIModelAdapter):
    @property
    def name(self) -> str:
        return "gemini"

    @property
    def cli_command(self) -> str:
        return GEMINI_CMD

    def build_command(self, prompt: str) -> list[str]:
        return [
            self.cli_command,
            "--model", GEMINI_MODEL,
            "-p", prompt,
            "--output-format", "json",
        ]

    def parse_output(self, stdout: str, stderr: str) -> str:
        """Parse JSON output from gemini -p --output-format json.

        Expected format: JSON object with a "response" field.
        Falls back to raw text if parsing fails (known Gemini CLI quirk).
        """
        try:
            data = json.loads(stdout)
            if isinstance(data, dict):
                # Try common response fields
                for key in ("response", "text", "content", "result"):
                    if key in data:
                        text = data[key]
                        if isinstance(text, str):
                            return text.strip()
                        # Handle nested structures
                        return json.dumps(text)
            if isinstance(data, list):
                # Array of response chunks
                parts = []
                for item in data:
                    if isinstance(item, dict):
                        for key in ("response", "text", "content"):
                            if key in item:
                                parts.append(str(item[key]).strip())
                                break
                        else:
                            parts.append(json.dumps(item))
                    else:
                        parts.append(str(item))
                if parts:
                    return "\n".join(parts)
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: return raw output
        return stdout.strip()
