"""Step 3: Mode synthesis — link multi-valued atoms into configuration modes.

Takes the flat extracted specs and identifies which atomic values belong to
the same logical operating mode (e.g. same table row, same application code).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI
from pipeline.pdf_parser import ParsedDatasheet
from pipeline.atom_extractor import _parse_json_from_response, BASE_URL
from transceiver_models import MODE_FIELDS

logger = logging.getLogger(__name__)

LINKING_SYSTEM_PROMPT = """\
You are given a pool of atomic parameter values extracted from an optical transceiver datasheet, \
plus the original datasheet content for context.

Task: group these multi-valued parameters into coherent operating modes. \
Each mode represents one selectable configuration (e.g. a table row, an application code, \
a host-to-media binding).

Rules:
- Each mode must include values that co-occur in the source (same row/section/application).
- A parameter with a single value across all modes should be repeated in each mode it applies to.
- Use the datasheet content to determine which values belong together.
- Assign a short descriptive label to each mode.
- Return ONLY valid JSON matching the schema below. No commentary.
"""

USER_PROMPT_TEMPLATE = """\
## Multi-valued parameters to group

```json
{atoms}
```

## Module-level context (single-valued, applies to all modes)

```json
{general}
```

## Original Datasheet Content

{content}

---

## Output Schema

Return a JSON object:
```json
{{
  "modes": [
    {{
      "label": "<short mode name>",
      {field_template}
    }}
  ]
}}
```

Group the multi-valued atoms into modes. Return only the JSON.
"""


def separate_atoms(specs_dict: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split specs into (multi_valued_mode_atoms, general_params).

    Mode fields with >1 value go to multi_valued.
    Mode fields with exactly 1 value or general fields go to general.
    """
    multi = {}
    general = {}

    for key, value in specs_dict.items():
        if key in MODE_FIELDS:
            if isinstance(value, list) and len(value) > 1:
                multi[key] = value
            elif value is not None:
                general[key] = value
        else:
            if value is not None:
                general[key] = value

    return multi, general


def _build_field_template(multi: dict[str, Any]) -> str:
    """Build the per-mode field list for the output schema."""
    lines = []
    for field in multi:
        lines.append(f'      "{field}": "<value from pool>"')
    return ",\n".join(lines)


def synthesize_modes(
    specs_dict: dict[str, Any],
    parsed: ParsedDatasheet,
    *,
    model_id: str | None = None,
    base_url: str = BASE_URL,
    temperature: float = 0.1,
    max_tokens: int = 16384,
) -> tuple[dict[str, Any] | None, dict[str, Any], dict[str, Any]]:
    """Run mode synthesis and return (modes_result, multi_atoms, general_params).

    Returns (None, multi, general) on failure.
    """
    multi, general = separate_atoms(specs_dict)

    if not multi:
        logger.info("No multi-valued mode fields — single mode module.")
        return {"modes": [{"label": "default", **{k: v for k, v in specs_dict.items() if k in MODE_FIELDS and v is not None}}]}, multi, general

    client = OpenAI(base_url=f"{base_url}/v1", api_key="no-key", timeout=600.0)

    if not model_id:
        models_resp = client.models.list()
        model_id = models_resp.data[0].id if models_resp.data else "default"

    content = parsed.markdown or parsed.full_text
    if len(content) > 80_000:
        content = content[:80_000] + "\n\n[...truncated...]"

    field_template = _build_field_template(multi)
    prompt = USER_PROMPT_TEMPLATE.format(
        atoms=json.dumps(multi, indent=2),
        general=json.dumps(general, indent=2),
        content=content,
        field_template=field_template,
    )

    logger.info("Synthesizing modes: %d multi-valued fields, model=%s", len(multi), model_id)

    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": LINKING_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    choice = response.choices[0]
    raw_response = choice.message.content or ""

    if not raw_response.strip():
        reasoning = getattr(choice.message, "reasoning_content", None) or ""
        if reasoning:
            raw_response = reasoning

    if not raw_response.strip():
        logger.error("Mode synthesis: empty LLM response")
        return None, multi, general

    result = _parse_json_from_response(raw_response)
    if not isinstance(result, dict) or "modes" not in result:
        logger.warning("Mode synthesis: unexpected response structure")
        if isinstance(result, list):
            result = {"modes": result}
        else:
            return None, multi, general

    logger.info("Mode synthesis: %d modes identified", len(result.get("modes", [])))
    return result, multi, general


def store_modes(run_dir: Path, modes: dict[str, Any], multi: dict[str, Any], general: dict[str, Any]) -> None:
    """Save mode synthesis results to the run directory."""
    (run_dir / "modes.json").write_text(json.dumps(modes, indent=2), encoding="utf-8")
    (run_dir / "mode_atoms.json").write_text(
        json.dumps({"multi_valued": multi, "general": general}, indent=2),
        encoding="utf-8",
    )
    logger.info("Modes saved to %s", run_dir)
