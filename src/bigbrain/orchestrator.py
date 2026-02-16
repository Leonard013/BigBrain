"""Orchestration patterns for multi-model collaboration."""

import asyncio

from bigbrain.config import CONSENSUS_TIMEOUT, DEBATE_TIMEOUT, DEFAULT_TIMEOUT
from bigbrain.context import build_prompt_with_context
from bigbrain.models.base import ModelResponse
from bigbrain.models.codex import CodexAdapter
from bigbrain.models.gemini import GeminiAdapter

codex = CodexAdapter()
gemini = GeminiAdapter()


async def ask_single(
    model: str,
    prompt: str,
    project_path: str | None = None,
    include_context: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
) -> ModelResponse:
    """Ask a single model."""
    full_prompt = build_prompt_with_context(prompt, project_path, include_context)
    adapter = codex if model == "codex" else gemini
    return await adapter.ask(full_prompt, timeout=timeout)


async def ask_both(
    prompt: str,
    project_path: str | None = None,
    include_context: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, ModelResponse]:
    """Ask both models in parallel and return both responses."""
    full_prompt = build_prompt_with_context(prompt, project_path, include_context)
    codex_resp, gemini_resp = await asyncio.gather(
        codex.ask(full_prompt, timeout=timeout),
        gemini.ask(full_prompt, timeout=timeout),
    )
    return {"codex": codex_resp, "gemini": gemini_resp}


async def consensus(
    topic: str,
    project_path: str | None = None,
    include_context: bool = True,
    timeout: float = CONSENSUS_TIMEOUT,
) -> dict:
    """Both models answer independently, then Gemini synthesizes."""
    responses = await ask_both(topic, project_path, include_context, timeout)

    codex_answer = responses["codex"].response if responses["codex"].success else f"[Codex error: {responses['codex'].error}]"
    gemini_answer = responses["gemini"].response if responses["gemini"].success else f"[Gemini error: {responses['gemini'].error}]"

    synthesis_prompt = (
        f"Two AI models were asked: \"{topic}\"\n\n"
        f"Codex's answer:\n{codex_answer}\n\n"
        f"Gemini's answer:\n{gemini_answer}\n\n"
        "Synthesize these perspectives. Identify:\n"
        "1. Points of agreement\n"
        "2. Key differences\n"
        "3. A balanced recommendation\n"
        "Be concise and structured."
    )

    synthesis = await gemini.ask(synthesis_prompt, timeout=timeout)

    return {
        "codex_response": responses["codex"],
        "gemini_response": responses["gemini"],
        "synthesis": synthesis,
    }


async def debate(
    topic: str,
    rounds: int = 2,
    project_path: str | None = None,
    include_context: bool = True,
    timeout: float = DEBATE_TIMEOUT,
) -> dict:
    """Multi-round debate: each model sees the other's previous response."""
    rounds = max(1, min(rounds, 5))  # Clamp to 1-5
    full_topic = build_prompt_with_context(topic, project_path, include_context)

    history: list[dict] = []

    # Round 1: both answer independently
    codex_resp, gemini_resp = await asyncio.gather(
        codex.ask(full_topic, timeout=timeout),
        gemini.ask(full_topic, timeout=timeout),
    )
    history.append({
        "round": 1,
        "codex": codex_resp,
        "gemini": gemini_resp,
    })

    # Subsequent rounds: each sees the other's previous answer
    for r in range(2, rounds + 1):
        prev_codex = history[-1]["codex"].response if history[-1]["codex"].success else "[no response]"
        prev_gemini = history[-1]["gemini"].response if history[-1]["gemini"].success else "[no response]"

        codex_prompt = (
            f"Topic: {topic}\n\n"
            f"Gemini's previous response:\n{prev_gemini}\n\n"
            f"This is round {r} of a debate. Refine your position, "
            "address their points, and strengthen your argument."
        )
        gemini_prompt = (
            f"Topic: {topic}\n\n"
            f"Codex's previous response:\n{prev_codex}\n\n"
            f"This is round {r} of a debate. Refine your position, "
            "address their points, and strengthen your argument."
        )

        codex_resp, gemini_resp = await asyncio.gather(
            codex.ask(codex_prompt, timeout=timeout),
            gemini.ask(gemini_prompt, timeout=timeout),
        )
        history.append({
            "round": r,
            "codex": codex_resp,
            "gemini": gemini_resp,
        })

    return {"topic": topic, "rounds": history}


async def council(
    topic: str,
    claude_opinion: str | None = None,
    project_path: str | None = None,
    include_context: bool = True,
    timeout: float = DEBATE_TIMEOUT,
) -> dict:
    """Three-stage council inspired by Karpathy's llm-council.

    Stage 1 — Individual: Each model answers independently.
    Stage 2 — Peer Review: Each model reviews all answers (anonymized) and ranks them.
    Stage 3 — Chairman: Returns everything so Claude can synthesize as chairman.
    """
    full_topic = build_prompt_with_context(topic, project_path, include_context)

    # ── Stage 1: Individual responses ──
    codex_resp, gemini_resp = await asyncio.gather(
        codex.ask(full_topic, timeout=timeout),
        gemini.ask(full_topic, timeout=timeout),
    )

    # Build anonymized answers for peer review
    answers: dict[str, str] = {}
    labels = []

    if claude_opinion:
        answers["Model A"] = claude_opinion
        labels.append(("Model A", "claude"))
    answers["Model B" if claude_opinion else "Model A"] = (
        codex_resp.response if codex_resp.success else "[failed to respond]"
    )
    labels.append(("Model B" if claude_opinion else "Model A", "codex"))
    answers["Model C" if claude_opinion else "Model B"] = (
        gemini_resp.response if gemini_resp.success else "[failed to respond]"
    )
    labels.append(("Model C" if claude_opinion else "Model B", "gemini"))

    answers_block = "\n\n".join(
        f"=== {label} ===\n{text}" for label, text in answers.items()
    )

    # ── Stage 2: Peer review (anonymized) ──
    review_prompt = (
        f"Several AI models were asked: \"{topic}\"\n\n"
        f"Here are their anonymized responses:\n\n{answers_block}\n\n"
        "As a peer reviewer:\n"
        "1. Rank the responses from best to worst (by label)\n"
        "2. For each response, note its key strengths and weaknesses\n"
        "3. Identify any factual errors or important omissions\n"
        "4. State which response you'd recommend and why\n"
        "Be concise and critical."
    )

    codex_review, gemini_review = await asyncio.gather(
        codex.ask(review_prompt, timeout=timeout),
        gemini.ask(review_prompt, timeout=timeout),
    )

    # ── Stage 3: Return everything for Claude (chairman) to synthesize ──
    return {
        "topic": topic,
        "stage1_individual": {
            "codex": codex_resp,
            "gemini": gemini_resp,
        },
        "stage2_peer_review": {
            "codex_review": codex_review,
            "gemini_review": gemini_review,
        },
        "label_map": {label: model for label, model in labels},
    }
