"""Integration boundary between screenplay generation and consistency checks.

The generator is injected as a callable so this module does not depend on
Streamlit, Gemini, or a particular LLM SDK. A generator should accept one
request dictionary and return a scene dictionary, a JSON string, or an
envelope containing ``scene`` or ``branches``.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from consistency_engine import check_scene, load_memory, remember_scene, save_memory
from lore_guard import audit_lore


class IntegrationError(ValueError):
	"""Raised when generated output cannot be converted into a scene."""


Generator = Callable[[dict[str, Any]], Any]


def load_story_memory(path: str | Path = "memory.json") -> dict[str, Any]:
	"""Load the structured memory used by the consistency engine."""
	return load_memory(path)


def normalize_scene(response: Any) -> dict[str, Any]:
	"""Convert one generator response into the engine's scene schema."""
	payload = _decode_response(response)
	if isinstance(payload, dict) and isinstance(payload.get("scene"), dict):
		payload = payload["scene"]
	if not isinstance(payload, dict):
		raise IntegrationError("Generated scene must be a JSON object.")

	scene = deepcopy(payload)
	for field in ("assertions", "actions", "suggested_traits"):
		value = scene.get(field, [])
		if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
			raise IntegrationError(f"Scene field '{field}' must be a list of objects.")
		scene[field] = value

	scene.setdefault("scene_id", "generated_scene")
	scene.setdefault("title", "Generated scene")
	return scene


def normalize_branches(response: Any) -> list[dict[str, Any]]:
	"""Convert generator output into a list of normalized scene branches."""
	payload = _decode_response(response)
	if isinstance(payload, dict) and "branches" in payload:
		payload = payload["branches"]
	elif isinstance(payload, dict) and "scenes" in payload:
		payload = payload["scenes"]
	else:
		payload = [payload]

	if not isinstance(payload, list):
		raise IntegrationError("Generated branches must be a JSON list.")
	return [normalize_scene(item) for item in payload]


def check_generated_scene(
	response: Any,
	memory: dict[str, Any],
	*,
	persist: bool = False,
	memory_path: str | Path = "memory.json",
) -> dict[str, Any]:
	"""Normalize and check one generated scene, optionally saving its history."""
	scene = normalize_scene(response)
	report = check_scene(scene, memory)
	if persist and report["consistent"]:
		remember_scene(scene, memory)
		save_memory(memory, memory_path)
	return {"scene": scene, "report": report}


def check_generated_branches(
	response: Any,
	memory: dict[str, Any],
) -> list[dict[str, Any]]:
	"""Check every generated story branch against the same memory snapshot."""
	return [
		{"branch": scene, "report": check_scene(scene, memory)}
		for scene in normalize_branches(response)
	]


def generate_and_check(
	generator: Generator,
	request: dict[str, Any],
	memory: dict[str, Any],
	*,
	branches: bool = False,
) -> dict[str, Any]:
	"""Call an injected AI generator and return a frontend-safe result."""
	try:
		generated = generator(request)
	except Exception as error:
		return {
			"ok": False,
			"error": f"Screenplay generation failed: {error}",
			"generated": None,
			"results": [],
		}

	try:
		results = (
			check_generated_branches(generated, memory)
			if branches
			else [check_generated_scene(generated, memory)]
		)
	except (IntegrationError, json.JSONDecodeError, TypeError, ValueError) as error:
		return {
			"ok": False,
			"error": f"Generated response format is invalid: {error}",
			"generated": generated,
			"results": [],
		}

	return {
		"ok": True,
		"error": None,
		"generated": generated,
		"results": results,
	}


def audit_generated_text(
	story_text: str,
	memory: dict[str, Any],
) -> dict[str, Any]:
	"""Run the prose adapter when the generator returns screenplay text."""
	return audit_lore(
		memory,
		story_text,
		memory.get("characters", {}),
	)


def _decode_response(response: Any) -> Any:
	if isinstance(response, str):
		try:
			return json.loads(response)
		except json.JSONDecodeError as error:
			raise IntegrationError("Generated response is not valid JSON.") from error
	return response

