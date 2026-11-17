import unittest

from integration import audit_generated_text, generate_and_check


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.memory = {
            "characters": {"Mira": {}},
            "world_rules": [],
            "established_facts": [
                {
                    "id": "mira-language",
                    "subject": "Mira",
                    "predicate": "knows_language",
                    "value": "French",
                }
            ],
            "scene_history": [],
        }

    def test_generator_scene_is_checked(self):
        def generator(_request):
            return {
                "scene_id": "scene_01",
                "assertions": [
                    {
                        "subject": "Mira",
                        "predicate": "knows_language",
                        "value": "Spanish",
                    }
                ],
            }

        result = generate_and_check(generator, {"prompt": "continue"}, self.memory)

        self.assertTrue(result["ok"])
        self.assertFalse(result["results"][0]["report"]["consistent"])
        self.assertEqual(
            result["results"][0]["report"]["issues"][0]["kind"],
            "fact_contradiction",
        )

    def test_all_story_branches_are_checked(self):
        def generator(_request):
            return {
                "branches": [
                    {
                        "scene_id": "branch_a",
                        "assertions": [
                            {
                                "subject": "Mira",
                                "predicate": "knows_language",
                                "value": "French",
                            }
                        ],
                    },
                    {
                        "scene_id": "branch_b",
                        "assertions": [
                            {
                                "subject": "Mira",
                                "predicate": "knows_language",
                                "value": "Spanish",
                            }
                        ],
                    },
                ]
            }

        result = generate_and_check(
            generator,
            {"prompt": "create two alternatives"},
            self.memory,
            branches=True,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["results"]), 2)
        self.assertTrue(result["results"][0]["report"]["consistent"])
        self.assertFalse(result["results"][1]["report"]["consistent"])

    def test_invalid_ai_json_returns_controlled_error(self):
        result = generate_and_check(
            lambda _request: "not valid json",
            {"prompt": "continue"},
            self.memory,
        )

        self.assertFalse(result["ok"])
        self.assertIn("invalid", result["error"])
        self.assertEqual(result["results"], [])

    def test_text_adapter_uses_existing_lore_contract(self):
        report = audit_generated_text("Mira knows Spanish.", self.memory)

        self.assertEqual(report["score"], 100 - 20)
        self.assertEqual(len(report["issues"]), 1)


if __name__ == "__main__":
    unittest.main()
