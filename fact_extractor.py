"""
Conservative rule-based screenplay fact extractor.

This is a first MVP, not a full natural-language understanding system.
It extracts only a few explicit sentence patterns and marks every result
as a candidate with confidence/source text. Review candidates before saving.
"""
from __future__ import annotations

import re


def extract_candidates(screenplay_text: str) -> dict:
    """
    Return candidate facts/actions from screenplay prose.

    Supported examples:
      "Mira is a detective."
      "Mira knows French."
      "Mira lives in Kolkata."
      "Mira enters the archive."
      "Mira opens the door."

    Unsupported or ambiguous sentences are deliberately ignored.
    """
    facts = []
    actions = []
    ignored_sentences = []

    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+|\n+", screenplay_text)
        if part.strip()
    ]

    fact_patterns = [
        (
            re.compile(r"^(?P<name>[A-Z][a-z]+)\s+is\s+(?:a|an)\s+(?P<value>[^.!?]+)[.!?]?$"),
            "occupation_or_identity"
        ),
        (
            re.compile(r"^(?P<name>[A-Z][a-z]+)\s+knows\s+(?P<value>[^.!?]+)[.!?]?$"),
            "knows"
        ),
        (
            re.compile(r"^(?P<name>[A-Z][a-z]+)\s+lives\s+in\s+(?P<value>[^.!?]+)[.!?]?$"),
            "lives_in"
        ),
    ]

    action_pattern = re.compile(
        r"^(?P<name>[A-Z][a-z]+)\s+"
        r"(?P<action>enters|leaves|opens|closes|takes|finds|checks|"
        r"reads|writes|runs|walks|speaks|looks at|picks up)\s+"
        r"(?P<object>[^.!?]+)[.!?]?$",
        re.IGNORECASE
    )

    for sentence in sentences:
        matched = False

        for pattern, predicate in fact_patterns:
            match = pattern.match(sentence)
            if match:
                facts.append({
                    "subject": match.group("name"),
                    "predicate": predicate,
                    "value": match.group("value").strip(),
                    "confidence": 0.85,
                    "status": "candidate",
                    "source_text": sentence
                })
                matched = True
                break

        if matched:
            continue

        match = action_pattern.match(sentence)
        if match:
            actions.append({
                "character": match.group("name"),
                "action": f'{match.group("action").lower()} {match.group("object").strip()}',
                "confidence": 0.85,
                "status": "candidate",
                "source_text": sentence
            })
            matched = True

        if not matched:
            ignored_sentences.append(sentence)

    return {
        "candidate_facts": facts,
        "candidate_actions": actions,
        "ignored_sentences": ignored_sentences,
        "requires_human_review": True
    }


def approve_candidate_fact(candidate: dict, fact_id: str) -> dict:
    """Convert a reviewed candidate into the established-fact schema."""
    required = ("subject", "predicate", "value")
    missing = [key for key in required if key not in candidate]
    if missing:
        raise ValueError(f"Candidate missing fields: {', '.join(missing)}")
    return {
        "id": fact_id,
        "subject": candidate["subject"],
        "predicate": candidate["predicate"],
        "value": candidate["value"],
        "severity": "high",
        "source_text": candidate.get("source_text", ""),
        "reviewed": True
    }
