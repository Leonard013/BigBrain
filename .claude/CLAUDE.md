<claude-mem-context>
# Recent Activity

### Feb 13, 2026

| ID | Time | T | Title | Read |
|----|------|---|-------|------|
| #94 | 12:21 PM | ✅ | Expanded BigBrain Project Permissions | ~312 |
| #93 | 12:20 PM | 🔵 | System Environment and Tool Availability Audit | ~451 |
</claude-mem-context>

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# BigBrain — Multi-Model Orchestration MCP Server

## What This Is

MCP server that gives Claude Code access to Codex (OpenAI) and Gemini (Google) CLIs.
Claude remains the decision-maker; Codex and Gemini provide second opinions.
Both CLIs use their own cached OAuth auth — no API keys needed.

## Architecture

- **FastMCP** server over stdio transport, registered at user scope
- **5 tools**: `ask_codex`, `ask_gemini`, `ask_both_models`, `request_consensus`, `request_debate`
- **Models**: Codex uses `gpt-5.3-codex`, Gemini uses `gemini-3-pro-preview` (configurable via env vars)
- **Shared context**: CLAUDE.md + MEMORY.md injected as read-only preamble into every prompt sent to other models. Claude is the sole writer; Codex/Gemini only read.
- **Error handling**: Failed CLI calls return `ModelResponse(success=False)` — never exceptions
- **Dynamic project detection**: Tools accept optional `project_path` param, falls back to `BIGBRAIN_PROJECT_PATH` env var, then cwd

## Project Layout

```
src/bigbrain/
  server.py        # FastMCP app with all 5 MCP tools
  config.py        # Paths, timeouts, model names, env var names
  context.py       # CLAUDE.md + MEMORY.md reader and prompt builder
  models/
    base.py        # Abstract CLIModelAdapter (async subprocess)
    codex.py       # codex exec --model gpt-5.3-codex --json --full-auto
    gemini.py      # gemini --model gemini-3-pro-preview -p --output-format json
  orchestrator.py  # Parallel, consensus, and debate patterns
```

## Key Paths

- Conda env: `/home/leonardo/miniconda3/envs/bigbrain/`
- CLIs: `~/.npm-global/bin/codex`, `~/.npm-global/bin/gemini`
- Launcher: `run_server.sh` (uses conda python directly)
- MCP registration: `~/.claude/settings.json` → `mcpServers.bigbrain`

## Dev Commands

```bash
# Run tests
/home/leonardo/miniconda3/envs/bigbrain/bin/pytest tests/ -v

# Run a single test file
/home/leonardo/miniconda3/envs/bigbrain/bin/pytest tests/test_codex.py -v

# Install after changes
/home/leonardo/miniconda3/envs/bigbrain/bin/pip install -e .
```
