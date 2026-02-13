"""Tests for Gemini adapter — command building and output parsing."""

from bigbrain.models.gemini import GeminiAdapter


def test_gemini_name():
    adapter = GeminiAdapter()
    assert adapter.name == "gemini"


def test_gemini_build_command():
    adapter = GeminiAdapter()
    cmd = adapter.build_command("hello world")
    assert cmd[0] == adapter.cli_command
    assert "--model" in cmd
    assert "-p" in cmd
    assert "hello world" in cmd
    assert "--output-format" in cmd
    assert "json" in cmd


def test_gemini_parse_json_response():
    """Parses JSON with 'response' field."""
    adapter = GeminiAdapter()
    stdout = '{"response": "Hello from Gemini"}'
    result = adapter.parse_output(stdout, "")
    assert result == "Hello from Gemini"


def test_gemini_parse_json_text_field():
    """Parses JSON with 'text' field."""
    adapter = GeminiAdapter()
    stdout = '{"text": "Alt text field"}'
    result = adapter.parse_output(stdout, "")
    assert result == "Alt text field"


def test_gemini_parse_json_array():
    """Parses JSON array of response chunks."""
    adapter = GeminiAdapter()
    stdout = '[{"text": "chunk1"}, {"text": "chunk2"}]'
    result = adapter.parse_output(stdout, "")
    assert "chunk1" in result
    assert "chunk2" in result


def test_gemini_parse_fallback_raw():
    """Falls back to raw text when JSON parsing fails."""
    adapter = GeminiAdapter()
    result = adapter.parse_output("not json at all", "")
    assert result == "not json at all"
