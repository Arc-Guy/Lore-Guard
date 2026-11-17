import unittest
from fact_extractor import extract_candidates, approve_candidate_fact


class FactExtractorTests(unittest.TestCase):
    def test_extracts_explicit_facts(self):
        result = extract_candidates("Mira is a detective. Mira knows French.")
        self.assertEqual(len(result["candidate_facts"]), 2)
        self.assertEqual(result["candidate_facts"][0]["subject"], "Mira")
        self.assertEqual(result["candidate_facts"][1]["value"], "French")

    def test_extracts_simple_action(self):
        result = extract_candidates("Mira opens the door.")
        self.assertEqual(len(result["candidate_actions"]), 1)
        self.assertEqual(result["candidate_actions"][0]["action"], "opens the door")

    def test_marks_for_review_and_ignores_ambiguous_text(self):
        result = extract_candidates("The room was dark.")
        self.assertTrue(result["requires_human_review"])
        self.assertEqual(len(result["ignored_sentences"]), 1)

    def test_approval_converts_candidate(self):
        candidate = {
            "subject": "Mira", "predicate": "knows",
            "value": "French", "source_text": "Mira knows French."
        }
        fact = approve_candidate_fact(candidate, "F-100")
        self.assertEqual(fact["id"], "F-100")
        self.assertTrue(fact["reviewed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
