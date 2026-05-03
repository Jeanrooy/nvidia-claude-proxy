"""config.py – Load and validate server configuration from the .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_int(key: str, default: int) -> int:
    raw = _env(key)
    if not raw:
        return default
    try:
        val = int(raw)
    except ValueError:
        raise ValueError(f"Invalid value for {key}: {raw!r} (expected integer)")
    if val < 0:
        raise ValueError(f"Invalid value for {key}: {raw!r} (must be >= 0)")
    return val


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int
    upstream_url: str
    provider_api_key: str
    server_api_key: str
    timeout_seconds: int
    log_body_max: int
    log_stream_preview_max: int


def load_config() -> ServerConfig:
    addr = _env("ADDR", "127.0.0.1:8089")
    if ":" in addr:
        host, port_str = addr.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            raise ValueError(f"Invalid port in ADDR: {addr!r}")
    else:
        host = addr
        port = 8089

    upstream_url = _env("UPSTREAM_URL")
    provider_api_key = _env("PROVIDER_API_KEY")
    server_api_key = _env("SERVER_API_KEY")
    timeout_seconds = _env_int("UPSTREAM_TIMEOUT_SECONDS", 300)
    log_body_max = _env_int("LOG_BODY_MAX_CHARS", 4096)
    log_stream_preview_max = _env_int("LOG_STREAM_TEXT_PREVIEW_CHARS", 256)

    if not upstream_url:
        raise ValueError("Missing UPSTREAM_URL in .env")
    if not provider_api_key:
        raise ValueError("Missing PROVIDER_API_KEY in .env")

    return ServerConfig(
        host=host,
        port=port,
        upstream_url=upstream_url,
        provider_api_key=provider_api_key,
        server_api_key=server_api_key,
        timeout_seconds=timeout_seconds,
        log_body_max=log_body_max,
        log_stream_preview_max=log_stream_preview_max,
    )
