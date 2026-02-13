"""Tests for Codex adapter — command building and output parsing."""

from bigbrain.models.codex import CodexAdapter


def test_codex_name():
    adapter = CodexAdapter()
    assert adapter.name == "codex"


def test_codex_build_command():
    adapter = CodexAdapter()
    cmd = adapter.build_command("hello world")
    assert cmd[0] == adapter.cli_command
    assert "exec" in cmd
    assert "--model" in cmd
    assert "--json" in cmd
    assert "--full-auto" in cmd
    assert "--skip-git-repo-check" in cmd
    assert "hello world" in cmd


def test_codex_parse_documented_format():
    """Parses the documented format: item.text directly on the item object."""
    adapter = CodexAdapter()
    stdout = (
        '{"type":"item.completed","item":{"id":"item_3","type":"agent_message","text":"Hello from Codex"}}\n'
    )
    result = adapter.parse_output(stdout, "")
    assert result == "Hello from Codex"


def test_codex_parse_content_array_fallback():
    """Parses fallback content array format for compatibility."""
    adapter = CodexAdapter()
    stdout = (
        '{"type":"item.completed","item":{"type":"agent_message",'
        '"content":[{"text":"Hello via content array"}]}}\n'
    )
    result = adapter.parse_output(stdout, "")
    assert result == "Hello via content array"


def test_codex_parse_multiple_messages():
    """Concatenates multiple agent messages."""
    adapter = CodexAdapter()
    stdout = (
        '{"type":"item.completed","item":{"id":"item_1","type":"agent_message","text":"First"}}\n'
        '{"type":"item.completed","item":{"id":"item_2","type":"agent_message","text":"Second"}}\n'
    )
    result = adapter.parse_output(stdout, "")
    assert "First" in result
    assert "Second" in result


def test_codex_parse_fallback_raw():
    """Falls back to raw stdout when no structured events found."""
    adapter = CodexAdapter()
    result = adapter.parse_output("just plain text output", "")
    assert result == "just plain text output"


def test_codex_parse_non_agent_events_ignored():
    """Non-agent_message events are ignored."""
    adapter = CodexAdapter()
    stdout = '{"type":"item.completed","item":{"type":"function_call","content":[]}}\n'
    result = adapter.parse_output(stdout, "")
    # Should fall back to raw since no agent_message was found
    assert result == stdout.strip()
