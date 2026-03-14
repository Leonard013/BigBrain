# 🧠 BigBrain

MCP server that lets Claude Code talk to Codex (OpenAI) and Gemini (Google) CLIs. Claude stays in charge — the other models provide second opinions. No API keys needed; both CLIs use their own cached OAuth.

## 🍹 Origin Story

> *This project was born on a Saturday night vibecoding session fueled by spiced rum.*

The kind of evening where you look at your API bill 💸, look at your glass 🥃, and think: ***"there has to be a better way."***

Turns out, both Codex and Gemini have CLIs with free OAuth access. So instead of paying per token like a responsible adult, BigBrain just shells out to the CLIs like a genius cheapskate. No API keys. No billing surprises on Monday morning. Just three AI models arguing with each other over stdio while you sip your drink. 🍹

Does it work? **Yes.** Is it elegant? *Debatable.* Did it save money? **Absolutely.** 💰 Will your future self thank your rum-fueled past self? *Also debatable.* 😅

> ***Enjoy responsibly*** *(the rum and the code).* 🥂

## 🏗️ Architecture

```
You 🫵
 └─> Claude Code (chairman — decides, writes memory, synthesizes)
       └─> BigBrain MCP Server (Python, FastMCP, stdio)
             ├─> Codex CLI  (async subprocess)
             └─> Gemini CLI (async subprocess)
```

**🔗 Shared context**: Every prompt sent to Codex/Gemini is automatically prepended with the current project's `CLAUDE.md` and `MEMORY.md`. Claude is the sole writer of these files; the other models only read them.

**📍 Dynamic project detection**: All tools accept an optional `project_path` param. Falls back to `BIGBRAIN_PROJECT_PATH` env var, then cwd. Works with any Claude Code project.

## 🛠️ Tools

| Tool | What it does |
|------|-------------|
| `ask_codex` | Ask Codex a single question 🤖 |
| `ask_gemini` | Ask Gemini a single question 💎 |
| `ask_both_models` | Ask both in parallel, get both answers ⚡ |
| `request_consensus` | Both answer independently, then one synthesizes agreements/differences 🤝 |
| `request_debate` | Multi-round debate — each model sees the other's previous answer (1–5 rounds) 🥊 |
| `request_council` | Three-stage council with anonymized peer review *(see below)* 👑 |

## 👑 Council — Three-Stage Process

The most thorough tool. All three models participate equally. Based on [Karpathy's llm-council](https://github.com/karpathy/llm-council):

```
Stage 1: Individual 🗣️       Stage 2: Peer Review 🔍      Stage 3: Chairman 🏛️
┌─────────┐                  ┌─────────┐                  ┌─────────┐
│ Claude  │──> Answer A      │ Codex   │──> Reviews &     │ Claude  │──> Final
│ Codex   │──> Answer B      │ Gemini  │    ranks all     │         │   answer
│ Gemini  │──> Answer C      │ Claude  │    (anonymized)  │         │
└─────────┘                  └─────────┘                  └─────────┘
  (all three)                  (all three)                 (chairman)
```

1. **🗣️ Individual** — Claude forms its opinion first, then Codex and Gemini answer independently in parallel. All three answers collected.
2. **🔍 Peer Review** — All answers are anonymized as Model A/B/C. Codex and Gemini each review and rank them. Claude receives the same anonymized prompt and does its own review too. *No model knows which answer is whose* 🕵️
3. **🏛️ Chairman** — Claude synthesizes all three individual answers + all three peer reviews into the final answer.

## 🚀 Quick Start

### 1. Prerequisites

Install the Codex and Gemini CLIs, then authenticate once:

```bash
npm install -g @openai/codex @google/gemini-cli
codex   # follow OAuth prompts 🔐
gemini  # follow OAuth prompts 🔐
```

### 2. Install & Register *(one command each)*

```bash
pip install git+https://github.com/Leonard013/BigBrain.git
claude mcp add bigbrain -- bigbrain
```

### 3. Done 🎉

Restart Claude Code, run `/mcp` — `bigbrain` should show as connected. ✅

That's it. Start asking Claude to use `ask_codex`, `ask_gemini`, `request_council`, etc.

---

<details>
<summary>⚙️ Advanced Configuration</summary>

#### Custom Python environment

If you want a dedicated env (conda, venv, etc.):

```bash
conda create -n bigbrain python=3.12 -y
conda activate bigbrain
pip install git+https://github.com/Leonard013/BigBrain.git
```

Then register with the full path to the `bigbrain` binary:

```bash
claude mcp add bigbrain -- /path/to/envs/bigbrain/bin/bigbrain
```

#### Override models

```bash
export BIGBRAIN_CODEX_MODEL="gpt-5.4"
export BIGBRAIN_GEMINI_MODEL="gemini-3.1-pro-preview"
```

#### Dev install (from source)

```bash
git clone https://github.com/Leonard013/BigBrain.git
cd BigBrain
pip install -e ".[dev]"
pytest tests/ -v
```

</details>
