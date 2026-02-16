"""Tests for orchestrator — mock-based tests for collaboration patterns."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from bigbrain.models.base import ModelResponse
from bigbrain.orchestrator import ask_both, ask_single, council


def _ok_response(model: str, text: str) -> ModelResponse:
    return ModelResponse(
        model=model, response=text, elapsed_seconds=1.0, success=True
    )


def _err_response(model: str, error: str) -> ModelResponse:
    return ModelResponse(
        model=model, response="", elapsed_seconds=0.5, success=False, error=error
    )


@pytest.mark.asyncio
async def test_ask_single_codex():
    """ask_single('codex', ...) calls the codex adapter."""
    mock_resp = _ok_response("codex", "Codex says hi")
    with patch("bigbrain.orchestrator.codex") as mock_codex:
        mock_codex.ask = AsyncMock(return_value=mock_resp)
        result = await ask_single("codex", "test prompt", include_context=False)
        assert result.model == "codex"
        assert result.response == "Codex says hi"
        mock_codex.ask.assert_called_once()


@pytest.mark.asyncio
async def test_ask_single_gemini():
    """ask_single('gemini', ...) calls the gemini adapter."""
    mock_resp = _ok_response("gemini", "Gemini says hi")
    with patch("bigbrain.orchestrator.gemini") as mock_gemini:
        mock_gemini.ask = AsyncMock(return_value=mock_resp)
        result = await ask_single("gemini", "test prompt", include_context=False)
        assert result.model == "gemini"
        assert result.response == "Gemini says hi"


@pytest.mark.asyncio
async def test_ask_both():
    """ask_both runs both models in parallel."""
    codex_resp = _ok_response("codex", "Codex answer")
    gemini_resp = _ok_response("gemini", "Gemini answer")

    with (
        patch("bigbrain.orchestrator.codex") as mock_codex,
        patch("bigbrain.orchestrator.gemini") as mock_gemini,
    ):
        mock_codex.ask = AsyncMock(return_value=codex_resp)
        mock_gemini.ask = AsyncMock(return_value=gemini_resp)

        result = await ask_both("test prompt", include_context=False)
        assert "codex" in result
        assert "gemini" in result
        assert result["codex"].response == "Codex answer"
        assert result["gemini"].response == "Gemini answer"


@pytest.mark.asyncio
async def test_ask_single_handles_error():
    """Error responses are returned, not raised."""
    mock_resp = _err_response("codex", "CLI not found")
    with patch("bigbrain.orchestrator.codex") as mock_codex:
        mock_codex.ask = AsyncMock(return_value=mock_resp)
        result = await ask_single("codex", "test", include_context=False)
        assert not result.success
        assert "CLI not found" in result.error


@pytest.mark.asyncio
async def test_council_three_stages():
    """Council runs stage 1 (individual) and stage 2 (peer review)."""
    codex_resp = _ok_response("codex", "Codex individual answer")
    gemini_resp = _ok_response("gemini", "Gemini individual answer")
    codex_review = _ok_response("codex", "Codex review of answers")
    gemini_review = _ok_response("gemini", "Gemini review of answers")

    with (
        patch("bigbrain.orchestrator.codex") as mock_codex,
        patch("bigbrain.orchestrator.gemini") as mock_gemini,
    ):
        # Stage 1 returns individual answers, Stage 2 returns reviews
        mock_codex.ask = AsyncMock(side_effect=[codex_resp, codex_review])
        mock_gemini.ask = AsyncMock(side_effect=[gemini_resp, gemini_review])

        result = await council("test topic", include_context=False)

        # Verify structure
        assert result["topic"] == "test topic"
        assert "stage1_individual" in result
        assert "stage2_peer_review" in result
        assert "label_map" in result

        # Stage 1: both models answered
        assert result["stage1_individual"]["codex"].response == "Codex individual answer"
        assert result["stage1_individual"]["gemini"].response == "Gemini individual answer"

        # Stage 2: both models reviewed
        assert result["stage2_peer_review"]["codex_review"].response == "Codex review of answers"
        assert result["stage2_peer_review"]["gemini_review"].response == "Gemini review of answers"

        # Each model was called twice (once for answer, once for review)
        assert mock_codex.ask.call_count == 2
        assert mock_gemini.ask.call_count == 2


@pytest.mark.asyncio
async def test_council_with_claude_opinion():
    """Council includes Claude's opinion in peer review when provided."""
    codex_resp = _ok_response("codex", "Codex answer")
    gemini_resp = _ok_response("gemini", "Gemini answer")
    codex_review = _ok_response("codex", "Review with 3 models")
    gemini_review = _ok_response("gemini", "Review with 3 models")

    with (
        patch("bigbrain.orchestrator.codex") as mock_codex,
        patch("bigbrain.orchestrator.gemini") as mock_gemini,
    ):
        mock_codex.ask = AsyncMock(side_effect=[codex_resp, codex_review])
        mock_gemini.ask = AsyncMock(side_effect=[gemini_resp, gemini_review])

        result = await council(
            "test topic",
            claude_opinion="Claude's take on this",
            include_context=False,
        )

        # Label map should include claude
        assert "claude" in result["label_map"].values()
        assert "codex" in result["label_map"].values()
        assert "gemini" in result["label_map"].values()

        # Stage 2 review prompt should contain "Model A" (claude's anonymized label)
        review_call_args = mock_codex.ask.call_args_list[1]
        review_prompt = review_call_args[0][0]
        assert "Model A" in review_prompt
        assert "Model B" in review_prompt
        assert "Model C" in review_prompt
