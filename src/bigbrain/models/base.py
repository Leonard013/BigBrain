"""Abstract base class for CLI model adapters."""

import asyncio
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from bigbrain.config import DEFAULT_TIMEOUT


@dataclass
class ModelResponse:
    """Structured response from a CLI model invocation."""

    model: str
    response: str
    elapsed_seconds: float
    success: bool
    error: str | None = None


class CLIModelAdapter(ABC):
    """Base adapter for invoking an AI CLI tool as a subprocess."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable model name (e.g. 'codex', 'gemini')."""

    @property
    @abstractmethod
    def cli_command(self) -> str:
        """Full path to the CLI executable."""

    @abstractmethod
    def build_command(self, prompt: str) -> list[str]:
        """Build the command-line arguments for a prompt."""

    @abstractmethod
    def parse_output(self, stdout: str, stderr: str) -> str:
        """Extract the model's answer from CLI output."""

    def build_env(self) -> dict[str, str]:
        """Return environment dict for subprocess. Override to inject API keys."""
        return dict(os.environ)

    async def ask(
        self, prompt: str, timeout: float = DEFAULT_TIMEOUT
    ) -> ModelResponse:
        """Spawn the CLI subprocess and return a structured response."""
        cmd = self.build_command(prompt)
        start = time.monotonic()

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.build_env(),
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            elapsed = time.monotonic() - start
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                return ModelResponse(
                    model=self.name,
                    response="",
                    elapsed_seconds=elapsed,
                    success=False,
                    error=f"Exit code {proc.returncode}: {stderr.strip() or stdout.strip()}",
                )

            parsed = self.parse_output(stdout, stderr)
            return ModelResponse(
                model=self.name,
                response=parsed,
                elapsed_seconds=elapsed,
                success=True,
            )

        except asyncio.TimeoutError:
            elapsed = time.monotonic() - start
            # Try to kill the hung process
            try:
                proc.kill()  # type: ignore[possibly-undefined]
            except (ProcessLookupError, OSError):
                pass
            return ModelResponse(
                model=self.name,
                response="",
                elapsed_seconds=elapsed,
                success=False,
                error=f"Timeout after {timeout}s",
            )
        except FileNotFoundError:
            return ModelResponse(
                model=self.name,
                response="",
                elapsed_seconds=time.monotonic() - start,
                success=False,
                error=f"CLI not found: {self.cli_command}",
            )
        except Exception as exc:
            return ModelResponse(
                model=self.name,
                response="",
                elapsed_seconds=time.monotonic() - start,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )
