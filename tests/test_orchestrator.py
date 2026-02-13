"""Tests for orchestrator — mock-based tests for collaboration patterns."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from bigbrain.models.base import ModelResponse
from bigbrain.orchestrator import ask_both, ask_single


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
