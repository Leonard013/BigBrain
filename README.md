# BigBrain

MCP server that lets Claude Code talk to Codex (OpenAI) and Gemini (Google) CLIs. Claude stays in charge — the other models provide second opinions. No API keys needed; both CLIs use their own cached OAuth.

Inspired by [Karpathy's llm-council](https://github.com/karpathy/llm-council).

## Architecture

```
You
 └─> Claude Code (chairman — decides, writes memory, synthesizes)
       └─> BigBrain MCP Server (Python, FastMCP, stdio)
             ├─> Codex CLI  (async subprocess)
             └─> Gemini CLI (async subprocess)
```

**Shared context**: Every prompt sent to Codex/Gemini is automatically prepended with the current project's `CLAUDE.md` and `MEMORY.md`. Claude is the sole writer of these files; the other models only read them.

**Dynamic project detection**: All tools accept an optional `project_path` param. Falls back to `BIGBRAIN_PROJECT_PATH` env var, then cwd. Works with any Claude Code project.

## Tools

| Tool | What it does |
|------|-------------|
| `ask_codex` | Ask Codex a single question |
| `ask_gemini` | Ask Gemini a single question |
| `ask_both_models` | Ask both in parallel, get both answers |
| `request_consensus` | Both answer independently, then one synthesizes agreements/differences |
| `request_debate` | Multi-round debate — each model sees the other's previous answer (1-5 rounds) |
| `request_council` | Three-stage council with anonymized peer review (see below) |

## Council — Three-Stage Process

The most thorough tool. All three models participate equally. Based on [Karpathy's llm-council](https://github.com/karpathy/llm-council):

```
Stage 1: Individual          Stage 2: Peer Review         Stage 3: Chairman
┌─────────┐                  ┌─────────┐                  ┌─────────┐
│ Claude  │──> Answer A      │ Codex   │──> Reviews &     │ Claude  │──> Final
│ Codex   │──> Answer B      │ Gemini  │    ranks all     │         │   answer
│ Gemini  │──> Answer C      │ Claude  │    (anonymized)  │         │
└─────────┘                  └─────────┘                  └─────────┘
  (all three)                  (all three)                 (chairman)
```

1. **Individual** — Claude forms its opinion first, then Codex and Gemini answer independently in parallel. All three answers collected.
2. **Peer Review** — All answers are anonymized as Model A/B/C. Codex and Gemini each review and rank them. Claude receives the same anonymized prompt and does its own review too. No model knows which answer is whose.
3. **Chairman** — Claude synthesizes all three individual answers + all three peer reviews into the final answer.

## Setup

### 1. Install CLIs

```bash
npm install -g @openai/codex @google/gemini-cli
```

Authenticate each (one-time):

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

Start a new session. Run `/mcp` — `bigbrain` should show as connected.

## Configuration

Models default to `gpt-5.3-codex` and `gemini-3-pro-preview`. Override via env vars:

```bash
export BIGBRAIN_CODEX_MODEL="gpt-5.3-codex"
export BIGBRAIN_GEMINI_MODEL="gemini-3-pro-preview"
```

## Project Structure

```
src/bigbrain/
  server.py        # FastMCP app — all 6 MCP tools
  config.py        # Paths, timeouts, model names
  context.py       # CLAUDE.md + MEMORY.md reader
  models/
    base.py        # Abstract CLIModelAdapter (async subprocess)
    codex.py       # Codex CLI adapter
    gemini.py      # Gemini CLI adapter
  orchestrator.py  # Parallel, consensus, debate, council patterns
```

## Dev

```bash
# run tests
/path/to/miniconda3/envs/bigbrain/bin/pytest tests/ -v

# reinstall after changes
/path/to/miniconda3/envs/bigbrain/bin/pip install -e .
```
