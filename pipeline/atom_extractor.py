"""Step 2: Atomic parameter extraction via LLM.

Sends parsed datasheet content to an LLM and extracts each field from
TransceiverSpecs as an independent atomic value.

Uses a local llama-server router (OpenAI-compatible at 127.0.0.1:8080).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from transceiver_models import TransceiverSpecs
from pipeline.pdf_parser import ParsedDatasheet

logger = logging.getLogger(__name__)

_LIST_FIELDS: set[str] = {
    f for f, info in TransceiverSpecs.model_fields.items()
    if "list" in str(info.annotation).lower()
}


def _coerce_types(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize scalar/list mismatches before Pydantic validation."""
    for key, value in list(raw.items()):
        if value is None:
            continue
        if key in _LIST_FIELDS:
            if not isinstance(value, list):
                raw[key] = [value]
        else:
            if isinstance(value, list) and len(value) == 1:
                raw[key] = value[0]
    return raw


SYSTEM_PROMPT = """\
You are an optical transceiver datasheet extraction engine.
Your task: extract every parameter from the datasheet text and fill the JSON schema below.

Rules:
- Copy numeric values EXACTLY as printed. Do not invent, convert, or round.
- If a value is not present in the source, use null.
- For list fields, collect ALL distinct values mentioned across the document.
- Each field is an independent atomic extraction — do not infer one from another.
- Return ONLY valid JSON matching the schema. No commentary outside the JSON block.
- Do not ignore new line within the a table cell. If a value is split across lines, concatenate it with a space.
"""

USER_PROMPT_TEMPLATE = """\
## Target Schema

```json
{schema}
```

## Section Headings

{headings}

## Datasheet Content

{content}

---

Extract all parameters into the JSON schema above. Return only the JSON object.
"""

BASE_URL = "http://127.0.0.1:8080"


def _build_schema_text() -> str:
    """Generate a compact JSON schema description from TransceiverSpecs."""
    schema = TransceiverSpecs.model_json_schema()
    props = schema.get("properties", {})
    compact = {}
    for name, info in props.items():
        desc = info.get("description", "")
        typ = info.get("type", info.get("anyOf", ""))
        compact[name] = f"{typ} — {desc}" if desc else str(typ)
    return json.dumps(compact, indent=2)


def _truncate(text: str, max_chars: int = 120_000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[...truncated...]"


def _extract_headings(md_text: str) -> str:
    """Return a newline-separated list of markdown headings found in the text."""
    headings = [
        line.strip() for line in md_text.splitlines()
        if re.match(r"^#{1,6}\s+", line)
    ]
    return "\n".join(headings) if headings else "(none found)"


def _parse_json_from_response(raw: str) -> Any:
    """Extract JSON dict from LLM response, handling fences and preamble."""
    s = raw.strip()
    # Strip markdown fences
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", s, re.DOTALL)
    if m:
        s = m.group(1).strip()
    try:
        v = json.loads(s)
        if isinstance(v, dict):
            return v
    except json.JSONDecodeError:
        pass
    # Fallback: find first { to last }
    start = s.find("{")
    end = s.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(s[start : end + 1])
        except json.JSONDecodeError:
            pass
    return {}


def extract_atoms(
    parsed: ParsedDatasheet,
    *,
    model_id: str | None = None,
    max_chars: int = 120_000,
    base_url: str = BASE_URL,
    temperature: float = 0.1,
    max_tokens: int = 16384,
) -> tuple[TransceiverSpecs | None, dict[str, Any]]:
    """Run LLM extraction and return (validated_specs, raw_dict).

    Returns (None, raw_dict) if validation fails but JSON was parsed.
    Returns (None, {}) on total failure.
    """
    client = OpenAI(base_url=f"{base_url}/v1", api_key="no-key", timeout=600.0)

    content = _truncate(parsed.markdown or parsed.full_text, max_chars)
    schema_text = _build_schema_text()
    headings = _extract_headings(parsed.markdown or parsed.full_text)
    prompt = USER_PROMPT_TEMPLATE.format(schema=schema_text, headings=headings, content=content)

    # Auto-detect model if not specified
    if not model_id:
        models_resp = client.models.list()
        model_id = models_resp.data[0].id if models_resp.data else "default"

    logger.info("Extracting atoms: %d chars content, model=%s", len(content), model_id)

    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    choice = response.choices[0]
    raw_response = choice.message.content or ""

    # Thinking models may put output in reasoning_content if content is empty
    if not raw_response.strip():
        reasoning = getattr(choice.message, "reasoning_content", None) or ""
        if reasoning:
            logger.info("Content empty, checking reasoning_content (%d chars)", len(reasoning))
            raw_response = reasoning

    if not raw_response.strip():
        logger.error("LLM returned completely empty response (finish_reason=%s)", choice.finish_reason)
        return None, {}

    raw_dict = _parse_json_from_response(raw_response)

    if not isinstance(raw_dict, dict):
        logger.error("LLM returned non-dict: %s", type(raw_dict))
        return None, {}

    raw_dict = _coerce_types(raw_dict)

    try:
        specs = TransceiverSpecs.model_validate(raw_dict)
        logger.info("Extraction validated successfully.")
        return specs, raw_dict
    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc.error_count())
        for err in exc.errors():
            logger.debug("  %s: %s", err["loc"], err["msg"])
        return None, raw_dict
