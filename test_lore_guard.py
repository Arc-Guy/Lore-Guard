import unittest
from lore_guard import audit_lore


class LoreGuardInterfaceTests(unittest.TestCase):
    def test_exact_output_contract_and_conflict(self):
        lore = {
            "established_facts": [
                {"id": "F1", "subject": "Mira", "predicate": "knows_language",
                 "value": "French"}
            ],
            "world_rules": []
        }
        result = audit_lore(lore, "Mira knows German.", {})
        self.assertEqual(set(result), {"score", "issues", "summary"})
        self.assertEqual(result["score"], 80)
        self.assertEqual(result["issues"][0]["severity"], "High")
        self.assertEqual(result["issues"][0]["type"], "Character contradiction")
        self.assertIn("description", result["issues"][0])

    def test_character_profile_facts(self):
        characters = {
            "Mira": {"known_facts": {"lives_in": "Kolkata"}}
        }
        result = audit_lore({}, "Mira lives in Delhi.", characters)
        self.assertEqual(len(result["issues"]), 1)

    def test_no_conflict_returns_valid_schema(self):
        result = audit_lore({}, "The castle is quiet.", {})
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["issues"], [])
        self.assertTrue(result["summary"])

    def test_language_conflict_detected_with_canonical_predicate(self):
        lore = {"established_facts": [
            {"id": "F-001", "subject": "Mira", "predicate": "knows_language", "value": "French"}
        ]}
        result = audit_lore(lore, "Mira knows German.", {})
        self.assertEqual(len(result["issues"]), 1)

    def test_occupation_conflict_detected(self):
        lore = {"established_facts": [
            {"id": "F-002", "subject": "Mira", "predicate": "occupation", "value": "investigator"}
        ]}
        result = audit_lore(lore, "Mira is a detective.", {})
        self.assertEqual(len(result["issues"]), 1)

    def test_matching_canonical_facts_do_not_conflict(self):
        lore = {"established_facts": [
            {"id": "F-001", "subject": "Mira", "predicate": "knows_language", "value": "French"},
            {"id": "F-002", "subject": "Mira", "predicate": "occupation", "value": "detective"}
        ]}
        result = audit_lore(lore, "Mira knows French. Mira is a detective.", {})
        self.assertEqual(result["issues"], [])

    def test_case_and_extra_spaces_are_normalized(self):
        lore = {"established_facts": [
            {"id": "F-001", "subject": " MIRA ", "predicate": " KNOWS_LANGUAGE ", "value": "  FRENCH   "}
        ]}
        result = audit_lore(lore, "Mira knows French.", {})
        self.assertEqual(result["issues"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
