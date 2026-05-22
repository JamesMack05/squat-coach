"""Claude API call -- AsyncAnthropic with structured outputs + prompt caching.

Per claude-api skill:
- Default model: claude-opus-4-7 (override via ANTHROPIC_MODEL)
- Adaptive thinking + effort parameter
- Structured outputs via messages.parse(output_format=CoachResponse) — returns
  a typed CoachResponse(reply, profile_updates) the bot can act on directly
- cache_control on the last system block (set by prompt.build_system_blocks)
- Async client matches PTB v21 handler shape
"""

from __future__ import annotations

import logging

from anthropic import AsyncAnthropic

from . import config
from .schemas import CoachResponse

log = logging.getLogger("squat-coach.llm")

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        config.require("ANTHROPIC_API_KEY", config.ANTHROPIC_API_KEY)
        _client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


async def coach_reply(
    system_blocks: list[dict],
    user_message: str,
) -> CoachResponse:
    """Call Claude with the prompted coach config and return a typed CoachResponse.

    system_blocks: list of system content blocks with cache_control on the last.
    user_message: pre-formatted user content (profile + pose + text).

    On API error or refusal, returns a CoachResponse with a fallback reply
    and empty profile_updates.
    """
    client = _get_client()

    try:
        response = await client.messages.parse(
            model=config.ANTHROPIC_MODEL,
            max_tokens=config.ANTHROPIC_MAX_TOKENS,
            thinking={"type": "adaptive"},
            output_config={"effort": config.ANTHROPIC_EFFORT},
            system=system_blocks,
            messages=[{"role": "user", "content": user_message}],
            output_format=CoachResponse,
        )
    except Exception as exc:
        log.exception("Anthropic API call failed")
        return CoachResponse(
            reply=f"(Coach is offline — API error: {exc!r})",
            profile_updates=[],
        )

    if response.usage:
        log.info(
            "tokens input=%d cache_read=%d cache_write=%d output=%d",
            response.usage.input_tokens,
            getattr(response.usage, "cache_read_input_tokens", 0) or 0,
            getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
            response.usage.output_tokens,
        )

    if response.stop_reason == "refusal":
        return CoachResponse(
            reply="(I can't help with that — it falls outside what I can safely coach on.)",
            profile_updates=[],
        )

    parsed = response.parsed_output
    if parsed is None:
        log.warning("structured output parse failed; falling back to text content")
        text_blocks = [b.text for b in response.content if b.type == "text"]
        return CoachResponse(
            reply="\n".join(text_blocks) if text_blocks else "(No reply.)",
            profile_updates=[],
        )

    return parsed
