# Nvidia Claude Code Proxy

> **Use Claude Code with powerful NVIDIA-hosted models — for free.**
> Skip the $100–$200/month Anthropic subscription. Point Claude Code at this proxy and get access to large frontier models (70B, 405B+) using NVIDIA's free NIM preview tier.

![Nvidia Claude Code Proxy Dashboard](dashboard.png)

---

## What is this?

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) is Anthropic's official AI coding agent — one of the most capable on the market. By default it requires an Anthropic API subscription that can cost **$100–$200+ per month** for heavy usage.

**This proxy changes that.** It sits between Claude Code and the internet, translating Anthropic API calls into OpenAI-compatible requests and forwarding them to [NVIDIA NIM](https://build.nvidia.com/) — which offers a **free preview tier** with access to large open-weight models (Llama 3.1 405B, Mistral, GLM, and more).

```
Claude Code / VS Code Extension
         │  Anthropic API format
         ▼
  ┌─────────────────────┐
  │  nvidia-claude-proxy │  ← this repo (runs locally on port 8089)
  └─────────────────────┘
         │  OpenAI API format
         ▼
   NVIDIA NIM API (free tier)
```

### Why use this?

| Without this proxy | With this proxy |
|---|---|
| Pay $100–$200/month for Claude API | **Free** NVIDIA NIM preview models |
| Limited to Anthropic's model lineup | Access to 70B–405B+ open-weight models |
| Single provider dependency | Any OpenAI-compatible backend |
| No request visibility | Real-time dashboard with logs & analytics |

---

## Features

- **Full Anthropic → OpenAI request translation**
  - System prompts (string or block array)
  - User / assistant messages (plain text, multi-part, images via base64 or URL)
  - Tool definitions (`tools`, `tool_choice`)
  - Assistant messages with tool calls
  - Tool result messages
- **Full OpenAI → Anthropic response translation**
  - Non-streaming JSON responses
  - Streaming SSE (`message_start`, `content_block_start/delta/stop`, `message_delta`, `message_stop`)
  - Tool-call streaming with `input_json_delta` events
- **Configuration via `.env`** — no JSON config file needed
- **Optional inbound auth** — protect the proxy with a `SERVER_API_KEY`
- **Structured logging** — request summaries, forwarded headers (key redacted), body previews

---

## Project Structure

```
python-proxy/
├── main.py           # FastAPI app & HTTP handlers
├── config.py         # .env loader & ServerConfig dataclass
├── models.py         # Pydantic models (Anthropic + OpenAI schemas)
├── translation.py    # Conversion logic (Anthropic ↔ OpenAI)
├── requirements.txt  # Python dependencies
├── .env              # Your local config (gitignored)
└── .env.example      # Template — copy to .env and fill in values
```

---

## Prerequisites

- Python 3.11+
- `pip`
- An [NVIDIA NIM API key](https://build.nvidia.com/) — free tier available

> **Free models:** NVIDIA offers a generous set of free preview models (no billing required).
> Browse the full list at **[build.nvidia.com/models → Free Preview](https://build.nvidia.com/models?filters=nimType%3Anim_type_preview)** and use any model ID (e.g. `z-ai/glm4.7`) as the value for `YOUR_MODEL_HERE` in your settings.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Jeanrooy/nvidia-claude-proxy.git
cd nvidia-claude-proxy
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure `.env`

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Address to listen on
ADDR=127.0.0.1:8089

# NVIDIA NIM endpoint (or any OpenAI-compatible URL)
UPSTREAM_URL=https://integrate.api.nvidia.com/v1/chat/completions

# Your NVIDIA API key
PROVIDER_API_KEY=nvapi-your-key-here

# Optional: protect this proxy with a Bearer / x-api-key token
SERVER_API_KEY=

# Upstream request timeout in seconds (non-streaming)
UPSTREAM_TIMEOUT_SECONDS=300

# Max chars to log for request/response bodies (0 = disabled)
LOG_BODY_MAX_CHARS=4096

# Max chars of streamed text to preview in logs (0 = disabled)
LOG_STREAM_TEXT_PREVIEW_CHARS=256
```

### 4. Run

```bash
python main.py
```

Or via `uvicorn` directly (with auto-reload for development):

```bash
uvicorn main:app --host 127.0.0.1 --port 8089 --reload
```

---

## Usage

The proxy exposes the same endpoint as the Anthropic API:

| Method | Path           | Description                  |
|--------|----------------|------------------------------|
| `GET`  | `/`            | Health check                 |
| `POST` | `/v1/messages` | Anthropic Messages API proxy |

### Quick test (streaming)

```bash
curl -N http://127.0.0.1:8089/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "z-ai/glm4.7",
    "max_tokens": 256,
    "stream": true,
    "messages": [{"role": "user", "content": "hello"}]
  }'
```

### Quick test (non-streaming)

```bash
curl http://127.0.0.1:8089/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "z-ai/glm4.7",
    "max_tokens": 256,
    "messages": [{"role": "user", "content": "What is 2+2?"}]
  }'
```

### With inbound auth

If `SERVER_API_KEY` is set in `.env`, every request must include a matching key:

```bash
curl http://127.0.0.1:8089/v1/messages \
  -H "Authorization: Bearer your-server-api-key" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

---

## Environment Variables Reference

| Variable                       | Default                                               | Description                                         |
|--------------------------------|-------------------------------------------------------|-----------------------------------------------------|
| `ADDR`                         | `127.0.0.1:8089`                                      | `host:port` the server listens on                   |
| `UPSTREAM_URL`                 | *(required)*                                          | OpenAI-compatible upstream endpoint                 |
| `PROVIDER_API_KEY`             | *(required)*                                          | API key forwarded to the upstream (as Bearer token) |
| `SERVER_API_KEY`               | *(empty = disabled)*                                  | Protect this proxy with inbound auth                |
| `UPSTREAM_TIMEOUT_SECONDS`     | `300`                                                 | Timeout for non-streaming upstream requests         |
| `LOG_BODY_MAX_CHARS`           | `4096`                                                | Max chars logged for bodies (`0` = disabled)        |
| `LOG_STREAM_TEXT_PREVIEW_CHARS`| `256`                                                 | Max chars of streamed text previewed in logs        |

---

## Pointing Claude Code at the Proxy

There are two ways to configure Claude Code to use this proxy — choose whichever fits your workflow.

---

### Option A — Per-Project `.claude/settings.json` *(recommended)*

This is the cleanest approach and works for both the **Claude Code CLI** and the **Claude Code VS Code extension**. Each project that should use the proxy gets its own `.claude/` folder.

#### 1. Copy the template into your project

```bash
# From your target project root
cp -r /path/to/nvidia-claude-proxy/.claude .claude
```

Or manually create `.claude/settings.json` in your project with the following content
(a ready-to-copy template is also shipped in this repo at `.claude/settings.json`):

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:8089",
    "ANTHROPIC_API_KEY": "YOUR_NVIDIA_API_KEY_HERE",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_NVIDIA_API_KEY_HERE",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "YOUR_MODEL_HERE",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "YOUR_MODEL_HERE",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "YOUR_MODEL_HERE"
  },
  "model": "YOUR_MODEL_HERE"
}
```

Replace every `YOUR_*` placeholder with your real values, e.g.:

| Placeholder | Example value |
|---|---|
| `YOUR_NVIDIA_API_KEY_HERE` | `nvapi-xxxxxxxxxxxxxxxxxxxx` |
| `YOUR_MODEL_HERE` | `z-ai/glm4.7` |

#### 2. Add `.claude/settings.local.json` to your `.gitignore`

`settings.json` is safe to commit (it contains no real secrets when you use the template).  
`settings.local.json` **must never be committed** — add it to your project's `.gitignore`:

```gitignore
# Claude Code local overrides — contains real API keys
.claude/settings.local.json
```

#### 3. Start the proxy, then open Claude Code

```bash
# Terminal 1 — run the proxy
cd /path/to/nvidia-claude-proxy
python main.py

# Terminal 2 — use Claude Code CLI in your project
cd /path/to/your-project
claude
```

Or simply open your project in VS Code — the Claude Code extension automatically reads `.claude/settings.json` from the workspace root.

> **Tip:** You only need to run the proxy once per machine session. Any number of projects can point at it simultaneously.

---

### Option B — Environment variable (quick / temporary)

If you just want to test the proxy without modifying any project:

```bash
# Windows (PowerShell)
$env:ANTHROPIC_BASE_URL = "http://127.0.0.1:8089"
$env:ANTHROPIC_API_KEY  = "nvapi-your-key"
claude

# Linux / macOS
ANTHROPIC_BASE_URL=http://127.0.0.1:8089 ANTHROPIC_API_KEY=nvapi-your-key claude
```

---


## Security Notes

- The `PROVIDER_API_KEY` is **never** logged — only `<redacted>` appears in logs.
- Inbound auth uses `hmac.compare_digest` to prevent timing attacks.
- Base64 image payloads are validated before forwarding.
