"""BigBrain MCP Server — exposes multi-model orchestration tools to Claude Code."""

from fastmcp import FastMCP

from bigbrain.config import CONSENSUS_TIMEOUT, DEBATE_TIMEOUT, DEFAULT_TIMEOUT
from bigbrain.models.base import ModelResponse
from bigbrain.orchestrator import ask_both, ask_single, consensus, debate

mcp = FastMCP(
    name="BigBrain",
    instructions=(
        "BigBrain gives you access to Codex (OpenAI) and Gemini (Google) CLI tools. "
        "Use these tools to get second opinions, compare approaches, run debates, "
        "or build consensus on technical decisions. You remain the decision-maker — "
        "these tools provide additional perspectives."
    ),
)


def _format_response(resp: ModelResponse) -> dict:
    """Convert a ModelResponse to a serializable dict."""
    return {
        "model": resp.model,
        "response": resp.response,
        "elapsed_seconds": round(resp.elapsed_seconds, 2),
        "success": resp.success,
        "error": resp.error,
    }


@mcp.tool()
async def ask_codex(
    prompt: str,
    project_path: str | None = None,
    include_context: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """Ask Codex (OpenAI) a question. Returns Codex's response.

    The prompt is automatically enriched with the project's CLAUDE.md and
    MEMORY.md as read-only context (disable with include_context=False).

    Args:
        prompt: The question or task for Codex.
        project_path: Optional project root path. Defaults to BIGBRAIN_PROJECT_PATH env var.
        include_context: Whether to prepend CLAUDE.md/MEMORY.md context.
        timeout: Max seconds to wait for response.
    """
    resp = await ask_single("codex", prompt, project_path, include_context, timeout)
    return _format_response(resp)


@mcp.tool()
async def ask_gemini(
    prompt: str,
    project_path: str | None = None,
    include_context: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """Ask Gemini (Google) a question. Returns Gemini's response.

    The prompt is automatically enriched with the project's CLAUDE.md and
    MEMORY.md as read-only context (disable with include_context=False).

    Args:
        prompt: The question or task for Gemini.
        project_path: Optional project root path. Defaults to BIGBRAIN_PROJECT_PATH env var.
        include_context: Whether to prepend CLAUDE.md/MEMORY.md context.
        timeout: Max seconds to wait for response.
    """
    resp = await ask_single("gemini", prompt, project_path, include_context, timeout)
    return _format_response(resp)


@mcp.tool()
async def ask_both_models(
    prompt: str,
    project_path: str | None = None,
    include_context: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """Ask both Codex and Gemini the same question simultaneously.

    Returns both responses for comparison. Useful when you want to see how
    different models approach the same problem.

    Args:
        prompt: The question or task for both models.
        project_path: Optional project root path.
        include_context: Whether to prepend shared context.
        timeout: Max seconds to wait per model.
    """
    responses = await ask_both(prompt, project_path, include_context, timeout)
    return {
        name: _format_response(resp) for name, resp in responses.items()
    }


@mcp.tool()
async def request_consensus(
    topic: str,
    project_path: str | None = None,
    include_context: bool = True,
    timeout: float = CONSENSUS_TIMEOUT,
) -> dict:
    """Ask both models about a topic, then synthesize their perspectives.

    Both Codex and Gemini answer independently, then a synthesis is generated
    identifying points of agreement, key differences, and a recommendation.

    Args:
        topic: The topic or question to build consensus on.
        project_path: Optional project root path.
        include_context: Whether to prepend shared context.
        timeout: Max seconds per individual call.
    """
    result = await consensus(topic, project_path, include_context, timeout)
    return {
        "codex_response": _format_response(result["codex_response"]),
        "gemini_response": _format_response(result["gemini_response"]),
        "synthesis": _format_response(result["synthesis"]),
    }


@mcp.tool()
async def request_debate(
    topic: str,
    rounds: int = 2,
    project_path: str | None = None,
    include_context: bool = True,
    timeout: float = DEBATE_TIMEOUT,
) -> dict:
    """Run a multi-round debate between Codex and Gemini.

    Each model sees the other's previous response and refines their position.
    Use this for complex topics where iterative refinement adds value.

    Args:
        topic: The topic to debate.
        rounds: Number of debate rounds (1-5, default 2).
        project_path: Optional project root path.
        include_context: Whether to prepend shared context.
        timeout: Max seconds per individual call.
    """
    result = await debate(topic, rounds, project_path, include_context, timeout)
    formatted_rounds = []
    for rd in result["rounds"]:
        formatted_rounds.append({
            "round": rd["round"],
            "codex": _format_response(rd["codex"]),
            "gemini": _format_response(rd["gemini"]),
        })
    return {"topic": result["topic"], "rounds": formatted_rounds}


if __name__ == "__main__":
    mcp.run(transport="stdio")
