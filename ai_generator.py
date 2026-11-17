"""Gemini screenplay generation adapter.

The module keeps the Gemini dependency lazy so the consistency checker and
unit tests work without an API key. ``generate_screenplay`` is the callable
accepted by ``integration.generate_and_check``.
"""
from __future__ import annotations

import json
import os
from typing import Any


class GenerationError(RuntimeError):
    """Raised when screenplay generation cannot produce valid JSON."""


def generate_screenplay(request: dict[str, Any]) -> dict[str, Any]:
    """Generate structured screenplay scenes or branches with Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GenerationError("GEMINI_API_KEY is not configured.")

    try:
        from google import genai
    except ImportError as error:
        raise GenerationError(
            "The google-genai package is required for screenplay generation."
        ) from error

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        contents=build_generation_prompt(request),
        config={"response_mime_type": "application/json"},
    )

    response_text = getattr(response, "text", None)
    if not response_text:
        raise GenerationError("Gemini returned an empty response.")

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise GenerationError("Gemini returned invalid JSON.") from error

    if not isinstance(result, dict):
        raise GenerationError("Gemini response must be a JSON object.")
    return result


def build_generation_prompt(request: dict[str, Any]) -> str:
    """Build a constrained prompt for structured, consistency-checkable output."""
    memory = request.get("memory", {})
    characters = request.get("characters", memory.get("characters", {}))
    lore = request.get("lore", memory.get("world_rules", []))
    branch_count = max(1, int(request.get("branch_count", 1)))

    return f"""
You are a screenplay generator for LoreGuard.

Create {branch_count} alternative screenplay scene(s) from this request:
{request.get('prompt', '')}

Genre: {request.get('genre', 'Drama')}

Established characters:
{json.dumps(characters, ensure_ascii=False, indent=2)}

Established lore and world rules:
{json.dumps(lore, ensure_ascii=False, indent=2)}

Respect every established character trait, fact, ability, and world rule.
Return only valid JSON with this exact shape:
{{
  "branches": [
    {{
      "scene_id": "generated_scene_1",
      "title": "Short scene title",
      "screenplay_text": "The screenplay scene text",
      "assertions": [
        {{"subject": "Name", "predicate": "occupation", "value": "value"}}
      ],
      "actions": [
        {{"character": "Name", "action": "opens the door"}}
      ],
      "suggested_traits": [
        {{"character": "Name", "trait": "trait"}}
      ]
    }}
  ]
}}

Use canonical predicates: knows_language, occupation, and lives_in.
Do not invent contradictions. Keep assertions explicit and evidence-based.
""".strip()
