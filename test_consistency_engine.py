import unittest
from consistency_engine import check_scene


class StructuredConsistencyPredicateTests(unittest.TestCase):
    def setUp(self):
        self.memory = {
            "characters": {},
            "world_rules": [],
            "established_facts": [
                {"id": "F1", "subject": "Mira", "predicate": "knows_language", "value": "French"},
                {"id": "F2", "subject": "Mira", "predicate": "occupation", "value": "investigator"}
            ],
            "scene_history": []
        }

    def test_legacy_predicate_alias_is_compared_canonically(self):
        scene = {"assertions": [
            {"subject": "Mira", "predicate": "knows", "value": "German"}
        ]}
        result = check_scene(scene, self.memory)
        self.assertEqual(len(result["issues"]), 1)

    def test_occupation_conflict_is_detected(self):
        scene = {"assertions": [
            {"subject": "Mira", "predicate": "occupation_or_identity", "value": "detective"}
        ]}
        result = check_scene(scene, self.memory)
        self.assertEqual(len(result["issues"]), 1)

    def test_case_and_whitespace_do_not_create_false_conflicts(self):
        scene = {"assertions": [
            {"subject": " MIRA ", "predicate": " KNOWS_LANGUAGE ", "value": "  FRENCH  "},
            {"subject": "Mira", "predicate": "occupation", "value": " INVESTIGATOR "}
        ]}
        result = check_scene(scene, self.memory)
        self.assertEqual(result["issues"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
