# Person 2 — Canonical Predicate Fix

This package contains the updated Memory & Logic Engine files.

## Canonical predicate vocabulary

| Meaning | Canonical predicate |
|---|---|
| Language known by a character | `knows_language` |
| Character occupation | `occupation` |
| Character residence | `lives_in` |

Legacy predicate names are normalized for compatibility:
- `knows` -> `knows_language`
- `occupation_or_identity` -> `occupation`

`fact_extractor.py` emits canonical names. `approve_candidate_fact()` also canonicalizes the predicate before saving an approved fact. `lore_guard.py` and `consistency_engine.py` normalize predicates before comparing facts.

## Value and subject comparisons

Text values are compared case-insensitively with repeated/leading/trailing whitespace collapsed. Character subjects are also compared case-insensitively in both checkers.

Occupation values are still compared by their normalized text. Therefore, `investigator` and `detective` are treated as different values and produce a contradiction, as requested by the regression test. No semantic synonym inference is performed.

## Files

- `fact_extractor.py` — candidate extraction and canonical predicate helpers.
- `lore_guard.py` — prose extraction and lore comparison.
- `consistency_engine.py` — structured assertion checker using the same canonical predicate helpers.
- `memory.json` — existing sample memory; already uses canonical predicate names.
- `test_fact_extractor.py` — extractor and approval tests.
- `test_lore_guard.py` — prose audit regression tests.
- `test_consistency_engine.py` — structured assertion regression tests.

## Run tests

From this folder:

```bash
python -m unittest test_fact_extractor test_lore_guard test_consistency_engine -v
```

Latest local result: **14 tests passed**.

## Integration note for Person 4

The public function signature `audit_lore(lore, story_text, characters)` and its return schema are unchanged. Existing imports of `extract_candidates`, `approve_candidate_fact`, and the consistency-engine public functions remain compatible. Person 1 should emit canonical predicates in structured assertions, especially `knows_language`, `occupation`, and `lives_in`; the checkers also accept the two listed legacy aliases.
