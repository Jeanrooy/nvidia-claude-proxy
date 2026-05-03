# Nvidia Claude Code Proxy

A Python port of the `claude-nvidia-proxy` Go server. It accepts requests in the **Anthropic Messages API** format and transparently translates them to the **OpenAI Chat Completions** format before forwarding to the [NVIDIA NIM](https://integrate.api.nvidia.com) (or any OpenAI-compatible) endpoint. Responses and SSE streams are translated back to the Anthropic format before being returned to the client.

This means any tool that speaks the Anthropic API (e.g. [Claude Code](https://docs.anthropic.com/en/docs/claude-code)) can be pointed at this proxy and use NVIDIA-hosted models transparently.

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

Set the `ANTHROPIC_BASE_URL` environment variable before running Claude Code:

```bash
# Windows (PowerShell)
$env:ANTHROPIC_BASE_URL = "http://127.0.0.1:8089"
claude

# Linux / macOS
ANTHROPIC_BASE_URL=http://127.0.0.1:8089 claude
```

Then select any NVIDIA-hosted model using `--model` or the `/model` command inside Claude Code.

---

## Differences from the Go Version

| Feature            | Go version          | Python version       |
|--------------------|---------------------|----------------------|
| Config format      | `config.json`       | `.env`               |
| Runtime            | Native binary       | Python 3.11+ + uvicorn |
| Framework          | `net/http`          | FastAPI + httpx      |
| Streaming          | `bufio` line scan   | `httpx` async stream |
| Hot reload         | Requires rebuild    | `--reload` flag      |

---

## Security Notes

- The `PROVIDER_API_KEY` is **never** logged — only `<redacted>` appears in logs.
- Inbound auth uses `hmac.compare_digest` to prevent timing attacks.
- Base64 image payloads are validated before forwarding.
