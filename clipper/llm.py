"""Shared Claude helper. Every LLM call in the project goes through `ask_json`.

Usage:
    class Picks(BaseModel):
        clips: list[ClipPick]

    picks = ask_json(SYSTEM, prompt, Picks)

Callers must catch `LLMError` and fall back to a non-LLM result (see CLAUDE.md).
"""

from __future__ import annotations

import logging
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from clipper import config

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Server-side refusal fallback: if the model declines, the API re-runs on a fallback model.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_ATTEMPTS = 2  # our retry on top of the SDK's own retries for 429/5xx/network

_client: anthropic.Anthropic | None = None


class LLMError(Exception):
    """Claude couldn't produce a valid answer. Callers should fall back."""


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        # api_key=None lets the SDK resolve ANTHROPIC_API_KEY / `ant auth login` itself.
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY or None, timeout=120.0)
    return _client


def ask_json(
    system: str,
    prompt: str,
    schema: type[T],
    *,
    max_tokens: int = 16000,
    effort: str | None = None,
    client: anthropic.Anthropic | None = None,
) -> T:
    """Ask Claude for a JSON answer matching `schema`; return the validated model.

    Raises LLMError on refusal, truncation, invalid output after retries, or API failure.
    """
    client = client or get_client()
    last_error = "unknown error"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.beta.messages.parse(
                model=config.CLAUDE_MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_format=schema,
                output_config={"effort": effort or config.CLAUDE_EFFORT},
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            raise LLMError(f"Claude auth failed, check ANTHROPIC_API_KEY: {e}") from e
        except anthropic.BadRequestError as e:
            raise LLMError(f"Claude rejected the request: {e.message}") from e
        except (anthropic.RateLimitError, anthropic.APIConnectionError) as e:
            last_error = f"{type(e).__name__}: {e}"
            log.warning("Claude call failed (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, last_error)
            continue
        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                last_error = f"server error {e.status_code}"
                log.warning("Claude %s (attempt %d/%d)", last_error, attempt, MAX_ATTEMPTS)
                continue
            raise LLMError(f"Claude API error {e.status_code}: {e.message}") from e

        if response.stop_reason == "refusal":
            raise LLMError("Claude declined the request (refusal)")
        if response.stop_reason == "max_tokens":
            raise LLMError(f"Claude output was cut off at max_tokens={max_tokens}")

        parsed = response.parsed_output
        if parsed is not None:
            log.debug("Claude ok (model=%s, request=%s)", response.model, response._request_id)
            return parsed
        last_error = "response did not match the schema"
        log.warning("Claude %s (attempt %d/%d)", last_error, attempt, MAX_ATTEMPTS)

    raise LLMError(f"Claude failed after {MAX_ATTEMPTS} attempts: {last_error}")
