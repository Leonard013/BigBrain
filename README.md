# BigBrain

MCP server that lets Claude Code talk to Codex (OpenAI) and Gemini (Google) CLIs. Claude stays in charge — the other models provide second opinions.

## How It Works

```
You <-> Claude Code <-> BigBrain MCP Server <-> Codex CLI / Gemini CLI
```

- Claude calls tools like `ask_codex`, `ask_gemini`, or `ask_both_models` mid-conversation
- BigBrain spawns the CLIs as async subprocesses and returns structured responses
- Every prompt sent to Codex/Gemini is prepended with the current project's `CLAUDE.md` and `MEMORY.md` as read-only context
- Both CLIs authenticate via their own cached OAuth — no API keys needed

## Tools

| Tool | What it does |
|------|-------------|
| `ask_codex` | Ask Codex a question |
| `ask_gemini` | Ask Gemini a question |
| `ask_both_models` | Ask both in parallel |
| `request_consensus` | Both answer, then synthesize agreements/differences |
| `request_debate` | Multi-round debate (1-5 rounds) |

## Setup

### 1. Install CLIs

```bash
npm install -g @openai/codex @google/gemini-cli
```

Authenticate each one:

```bash
codex   # follow OAuth prompts
gemini  # follow OAuth prompts
```

### 2. Create conda environment

```bash
conda create -n bigbrain python=3.12 -y
```

### 3. Install BigBrain

```bash
/path/to/miniconda3/envs/bigbrain/bin/pip install -e /path/to/BigBrain
```

### 4. Register with Claude Code

Add to `~/.claude.json` under `mcpServers`:

```json
{
  "bigbrain": {
    "command": "/path/to/BigBrain/run_server.sh",
    "args": []
  }
}
```

Update `run_server.sh` to point to your conda python:

```bash
#!/usr/bin/env bash
exec /path/to/miniconda3/envs/bigbrain/bin/python -m bigbrain.server "$@"
```

### 5. Restart Claude Code

Start a new session. Run `/mcp` to verify `bigbrain` shows as connected.

## Configuration

Models are configurable via environment variables:

```bash
export BIGBRAIN_CODEX_MODEL="gpt-5.3-codex"          # default
export BIGBRAIN_GEMINI_MODEL="gemini-3-pro-preview"   # default
```

## Dev

```bash
# run tests
/path/to/miniconda3/envs/bigbrain/bin/pytest tests/ -v

# reinstall after changes
/path/to/miniconda3/envs/bigbrain/bin/pip install -e .
```
