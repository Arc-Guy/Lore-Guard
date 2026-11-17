"""
Person 2 — Memory & Logic Engineer
A deterministic MVP consistency checker using only Python's standard library.

Public interface:
    load_memory(path) -> dict
    save_memory(memory, path) -> None
    add_character(memory, character_id, profile) -> None
    add_world_rule(memory, rule) -> None
    add_fact(memory, fact) -> None
    check_scene(scene, memory) -> dict
    remember_scene(scene, memory) -> None

Scene input format:
{
  "scene_id": "scene_01",
  "title": "The locked room",
  "assertions": [
    {"subject": "Mira", "predicate": "knows_language", "value": "French",
     "type": "character_fact", "evidence": "Mira speaks French."}
  ],
  "actions": [
    {"character": "Mira", "action": "opens the door"}
  ],
  "suggested_traits": [
    {"character": "Mira", "trait": "reckless"}
  ]
}

This MVP checks explicit structured assertions. It does not yet understand
arbitrary screenplay prose; Person 1/the LLM should convert scene text into
the structured scene format above.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_MEMORY = {
    "schema_version": "1.0",
    "characters": {},
    "world_rules": [],
    "established_facts": [],
    "scene_history": []
}


def load_memory(path: str | Path) -> dict:
    """Load memory JSON, creating a fresh memory object if the file is absent."""
    path = Path(path)
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_MEMORY))
    with path.open("r", encoding="utf-8") as file:
        memory = json.load(file)
    for key, default in DEFAULT_MEMORY.items():
        memory.setdefault(key, json.loads(json.dumps(default)))
    return memory


def save_memory(memory: dict, path: str | Path) -> None:
    """Persist memory safely as readable UTF-8 JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(memory, file, indent=2, ensure_ascii=False)
    temp_path.replace(path)


def add_character(memory: dict, character_id: str, profile: dict) -> None:
    """Add or update a character profile."""
    if not character_id.strip():
        raise ValueError("character_id cannot be empty")
    memory.setdefault("characters", {})[character_id] = profile


def add_world_rule(memory: dict, rule: dict) -> None:
    """Add a world rule. Recommended fields: id, description, subject,
    predicate, value, severity."""
    _require_fields(rule, ("id", "description"))
    _upsert_by_id(memory.setdefault("world_rules", []), rule)


def add_fact(memory: dict, fact: dict) -> None:
    """Add an established fact. Required: id, subject, predicate, value."""
    _require_fields(fact, ("id", "subject", "predicate", "value"))
    _upsert_by_id(memory.setdefault("established_facts", []), fact)


def retrieve_character(memory: dict, character_id: str) -> dict | None:
    """Retrieve one character's stored profile."""
    return memory.get("characters", {}).get(character_id)


def retrieve_relevant_memory(memory: dict, scene: dict) -> dict:
    """Return memory relevant to entities/assertions mentioned in a scene."""
    names = {
        item.get("subject") for item in scene.get("assertions", [])
        if item.get("subject")
    }
    names.update(
        item.get("character") for item in scene.get("actions", [])
        if item.get("character")
    )
    names.update(
        item.get("character") for item in scene.get("suggested_traits", [])
        if item.get("character")
    )
    return {
        "characters": {
            name: memory.get("characters", {})[name]
            for name in names if name in memory.get("characters", {})
        },
        "world_rules": list(memory.get("world_rules", [])),
        "established_facts": [
            fact for fact in memory.get("established_facts", [])
            if fact.get("subject") in names or fact.get("subject") == "*"
        ]
    }


def check_scene(scene: dict, memory: dict) -> dict:
    """
    Check a structured scene against memory.
    Returns a report with issues, repeated actions, trait warnings and score.
    """
    issues: list[dict] = []
    warnings: list[dict] = []

    # 1. Compare new assertions with established facts.
    facts = memory.get("established_facts", [])
    for assertion in scene.get("assertions", []):
        subject = assertion.get("subject")
        predicate = assertion.get("predicate")
        value = assertion.get("value")
        for fact in facts:
            same_key = (
                fact.get("subject") == subject
                and fact.get("predicate") == predicate
            )
            if same_key and _normal(value) != _normal(fact.get("value")):
                issues.append({
                    "kind": "fact_contradiction",
                    "severity": fact.get("severity", "high"),
                    "message": (
                        f"{subject}: new value for '{predicate}' is "
                        f"'{value}', but established memory says "
                        f"'{fact.get('value')}'."
                    ),
                    "expected": fact.get("value"),
                    "found": value,
                    "source": fact.get("id")
                })

    # 2. Check explicit world-rule constraints.
    for rule in memory.get("world_rules", []):
        subject = rule.get("subject")
        predicate = rule.get("predicate")
        expected = rule.get("value")
        if not predicate:
            continue
        for assertion in scene.get("assertions", []):
            applies = (
                assertion.get("predicate") == predicate
                and (subject in (None, "*", assertion.get("subject")))
            )
            if applies and expected is not None:
                if _normal(assertion.get("value")) != _normal(expected):
                    issues.append({
                        "kind": "world_rule_violation",
                        "severity": rule.get("severity", "high"),
                        "message": (
                            f"World rule '{rule.get('id')}' expects "
                            f"{predicate}='{expected}', but scene has "
                            f"'{assertion.get('value')}'."
                        ),
                        "source": rule.get("id")
                    })

    # 3. Detect repeated actions across recent scenes.
    previous_actions = []
    for old_scene in memory.get("scene_history", []):
        previous_actions.extend(old_scene.get("actions", []))

    previous_counts = Counter(
        (_normal(a.get("character")), _normal(a.get("action")))
        for a in previous_actions
    )
    current_counts = Counter(
        (_normal(a.get("character")), _normal(a.get("action")))
        for a in scene.get("actions", [])
    )
    for key, count in current_counts.items():
        old_count = previous_counts.get(key, 0)
        if old_count and count:
            character, action = key
            warnings.append({
                "kind": "repeated_action",
                "message": (
                    f"{character} repeats the action '{action}' "
                    f"({old_count} time(s) in previous scenes)."
                ),
                "character": character,
                "action": action,
                "previous_count": old_count
            })

    # 4. Flag suggested traits that conflict with a character's defined traits.
    for suggestion in scene.get("suggested_traits", []):
        character = suggestion.get("character")
        trait = suggestion.get("trait")
        profile = memory.get("characters", {}).get(character, {})
        established_traits = profile.get("traits", [])
        opposite_traits = profile.get("contradictory_traits", {})
        conflicts_with = opposite_traits.get(trait, [])
        if trait and any(_normal(t) in {_normal(x) for x in established_traits}
                         for t in conflicts_with):
            warnings.append({
                "kind": "trait_inconsistency",
                "message": (
                    f"{character} is suggested to be '{trait}', which may "
                    f"conflict with established traits: {conflicts_with}."
                ),
                "character": character,
                "suggested_trait": trait,
                "established_traits": established_traits
            })

    high_issues = sum(1 for item in issues if item.get("severity") == "high")
    score = max(0, 100 - 25 * high_issues - 10 * (len(issues) - high_issues)
                - 5 * len(warnings))

    return {
        "scene_id": scene.get("scene_id", "unknown"),
        "title": scene.get("title", ""),
        "consistent": len(issues) == 0,
        "consistency_score": score,
        "issues": issues,
        "warnings": warnings,
        "summary": (
            f"{len(issues)} contradiction(s), {len(warnings)} warning(s)."
        )
    }


def remember_scene(scene: dict, memory: dict) -> None:
    """Append a scene to history after it has been reviewed/approved."""
    memory.setdefault("scene_history", []).append({
        "scene_id": scene.get("scene_id", "unknown"),
        "title": scene.get("title", ""),
        "actions": scene.get("actions", [])
    })


def _require_fields(obj: dict, fields: tuple[str, ...]) -> None:
    missing = [field for field in fields if field not in obj]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")


def _upsert_by_id(items: list, item: dict) -> None:
    for index, existing in enumerate(items):
        if existing.get("id") == item["id"]:
            items[index] = item
            return
    items.append(item)


def _normal(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())
