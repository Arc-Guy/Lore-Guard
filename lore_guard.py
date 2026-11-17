"""
Person 2's agreed Lore Guard interface.

Exact public interface:
    audit_lore(lore, story_text, characters) -> {
        "score": int,
        "issues": [{"severity": str, "type": str, "description": str}],
        "summary": str
    }

This first implementation is deterministic and conservative. It checks
explicit facts extracted by fact_extractor.py against supplied lore and
character profiles. It does not claim to understand every sentence.
"""
from __future__ import annotations

from fact_extractor import extract_candidates, normalize_predicate, normalize_value


def audit_lore(lore, story_text, characters):
    """Audit story_text against lore and characters using the agreed schema."""
    issues = []
    known_facts = _collect_facts(lore, characters)

    extracted = extract_candidates(story_text or "")
    candidates = extracted["candidate_facts"]

    for candidate in candidates:
        subject = _norm(candidate.get("subject"))
        predicate = normalize_predicate(candidate.get("predicate", ""))
        value = _norm(candidate.get("value"))

        for fact in known_facts:
            if (
                _norm(fact.get("subject")) == subject
                and normalize_predicate(fact.get("predicate", "")) == predicate
                and normalize_value(fact.get("value")) != value
            ):
                issues.append({
                    "severity": "High",
                    "type": "Character contradiction",
                    "description": (
                        f"{candidate['subject']} has '{candidate['predicate']}' "
                        f"as '{candidate['value']}' in the story, but established "
                        f"lore says '{fact.get('value')}'."
                    )
                })

    # Check explicit world-rule violations when rules use the same
    # subject/predicate/value representation.
    for rule in _collect_rules(lore):
        rule_predicate = rule.get("predicate")
        if not rule_predicate or "value" not in rule:
            continue
        for candidate in candidates:
            subject_matches = rule.get("subject") in (None, "*", candidate.get("subject"))
            if (
                subject_matches
                and normalize_predicate(candidate.get("predicate", "")) == normalize_predicate(rule_predicate)
                and normalize_value(candidate.get("value")) != normalize_value(rule.get("value"))
            ):
                issue = {
                    "severity": "High",
                    "type": "World-rule violation",
                    "description": (
                        f"Story conflicts with world rule "
                        f"'{rule.get('description', rule.get('id', rule_predicate))}': "
                        f"expected '{rule.get('value')}', found "
                        f"'{candidate.get('value')}'."
                    )
                }
                if issue not in issues:
                    issues.append(issue)

    # The extractor deliberately reports sentences it could not parse.
    # They are not contradictions; mention the limitation in summary only.
    high_count = sum(1 for issue in issues if issue["severity"] == "High")
    score = max(0, 100 - 20 * high_count)

    if issues:
        summary = (
            f"Found {len(issues)} lore issue(s), including "
            f"{high_count} high-severity issue(s)."
        )
    else:
        summary = (
            "No contradictions were found in the facts this MVP could "
            "extract. This is not a guarantee that all story text is consistent."
        )

    if extracted["ignored_sentences"]:
        summary += (
            f" {len(extracted['ignored_sentences'])} sentence(s) could not be "
            "checked by the current rule-based extractor."
        )

    return {
        "score": score,
        "issues": issues,
        "summary": summary
    }


def _collect_facts(lore, characters):
    facts = []

    if isinstance(lore, dict):
        facts.extend(lore.get("established_facts", []))
        # Support a simple lore["facts"] list too.
        facts.extend(lore.get("facts", []))
    elif isinstance(lore, list):
        facts.extend(item for item in lore if isinstance(item, dict))

    if isinstance(characters, dict):
        for name, profile in characters.items():
            if not isinstance(profile, dict):
                continue
            for predicate, value in profile.get("known_facts", {}).items():
                facts.append({
                    "subject": name,
                    "predicate": predicate,
                    "value": value
                })
            for predicate, value in profile.get("facts", {}).items():
                facts.append({
                    "subject": name,
                    "predicate": predicate,
                    "value": value
                })
    elif isinstance(characters, list):
        for profile in characters:
            if not isinstance(profile, dict):
                continue
            name = profile.get("name") or profile.get("id")
            for predicate, value in profile.get("known_facts", {}).items():
                facts.append({
                    "subject": name,
                    "predicate": predicate,
                    "value": value
                })
            for predicate, value in profile.get("facts", {}).items():
                facts.append({
                    "subject": name,
                    "predicate": predicate,
                    "value": value
                })

    return [fact for fact in facts if isinstance(fact, dict)]


def _collect_rules(lore):
    if isinstance(lore, dict):
        return lore.get("world_rules", [])
    return []


def _norm(value):
    return " ".join(str(value).strip().lower().split())
