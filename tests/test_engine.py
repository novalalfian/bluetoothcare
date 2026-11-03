"""Pengujian mesin inferensi terhadap 13 skenario uji (7 PRD + 6 perluasan).

Jalankan dari akar proyek:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inference_engine import (  # noqa: E402
    InputError,
    KnowledgeBase,
    premise_label,
    run_inference,
    validate_answers,
)


class EngineTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kb = KnowledgeBase.load(ROOT / "knowledge_base.json")

    def answers(self, yes: list[str]) -> dict[str, bool]:
        return {fid: fid in yes for fid in self.kb.fact_order}

    def infer(self, yes: list[str]) -> dict:
        return run_inference(self.kb, {"answers": self.answers(yes)})


class TestKnowledgeBase(EngineTestCase):
    def test_minimum_specification(self) -> None:
        self.assertEqual(len(self.kb.facts), 20)
        self.assertEqual(len(self.kb.rules), 31)
        self.assertEqual(len(self.kb.final_conclusions), 10)
        self.assertEqual(
            sum(1 for item in self.kb.conclusions.values() if item["type"] == "intermediate"),
            9,
        )
        for check in self.kb.compliance():
            self.assertTrue(check["met"], f"Spesifikasi gagal: {check}")

    def test_premise_labels_include_nested_or(self) -> None:
        self.assertEqual(premise_label(self.kb.rules["R14"]["if"]), "F7 DAN (F5 ATAU F11)")
        self.assertEqual(premise_label(self.kb.rules["R3"]["if"]), "F13 ATAU F9")
        self.assertEqual(premise_label(self.kb.rules["R8"]["if"]), "K1 DAN F4")

    def test_public_data_has_rule_explanations(self) -> None:
        data = self.kb.public_data()
        self.assertEqual(len(data["facts"]), 20)
        self.assertEqual(len(data["rules"]), 31)
        rule = next(item for item in data["rules"] if item["id"] == "R14")
        self.assertEqual(rule["premise_label"], "F7 DAN (F5 ATAU F11)")
        self.assertIn("Baterai perangkat", rule["premise_sentence"])

    def test_every_rule_cites_a_known_source(self) -> None:
        source_ids = {source["id"] for source in self.kb.sources}
        for rule in self.kb.raw_rules:
            with self.subTest(rule=rule["id"]):
                self.assertIn(rule.get("source"), source_ids)

    def test_literature_sources_are_complete(self) -> None:
        by_id = {source["id"]: source for source in self.kb.sources}
        for source_id in ("S5", "S6", "S7", "S8", "S9", "S10"):
            with self.subTest(source=source_id):
                source = by_id[source_id]
                self.assertTrue(source["title"].strip())
                self.assertTrue(source["publisher"].strip())
                self.assertTrue(source["url"].startswith("https://"))
                self.assertEqual(source["status"], "terverifikasi")
                self.assertTrue(source["contribution"].strip())


class TestScenarios(EngineTestCase):
    def test_all_prd_scenarios(self) -> None:
        scenarios = self.kb.meta["test_scenarios"]
        matched = 0
        for scenario in scenarios:
            with self.subTest(scenario=scenario["no"], facts=scenario["facts"]):
                result = self.infer(scenario["facts"])
                fired = [record["rule_id"] for record in result["trace"]]
                diagnoses = [item["id"] for item in result["diagnoses"]]

                self.assertEqual(fired, scenario["rules"], "Aturan yang berjalan tidak sesuai")
                if scenario["result"] is None:
                    self.assertEqual(result["status"], "inconclusive")
                    self.assertEqual(diagnoses, [])
                    self.assertIn("Belum dapat disimpulkan", result["inconclusive"]["message"])
                else:
                    self.assertEqual(result["status"], "diagnosed")
                    self.assertEqual(diagnoses, [scenario["result"]])

                matched += 1

                # Aturan tidak boleh dijalankan dua kali.
                self.assertEqual(len(fired), len(set(fired)))

        self.assertEqual(
            round((matched / len(scenarios)) * 100),
            100,
            "Seluruh skenario harus sesuai, termasuk skenario tanpa diagnosis",
        )

    def test_scenario_7_reports_detected_single_fact(self) -> None:
        result = self.infer(["F7"])
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual([fact["id"] for fact in result["detected_facts"]], ["F7"])
        self.assertTrue(
            any("baterai" in text.lower() for text in result["inconclusive"]["suggestions"])
        )

    def test_rule_iteration_trace(self) -> None:
        result = self.infer(["F1", "F14"])
        self.assertEqual(result["status"], "diagnosed")
        self.assertEqual(result["diagnoses"][0]["id"], "H1")
        self.assertEqual(len(result["trace"]), 2)
        self.assertEqual([record["iteration"] for record in result["trace"]], [1, 2])
        self.assertEqual([record["rule_id"] for record in result["trace"]], ["R1", "R9"])
        self.assertTrue(all(record["is_new"] for record in result["trace"]))
        self.assertEqual(result["stats"]["iterations"], 2)

    def test_derivation_tree_contains_intermediate_rule(self) -> None:
        result = self.infer(["F1", "F14"])
        causes = result["diagnoses"][0]["derivation"]["causes"]
        self.assertEqual(causes[0]["rule_id"], "R9")
        antecedent_ids = [item["id"] for item in causes[0]["antecedents"]]
        self.assertIn("K1", antecedent_ids)
        self.assertIn("F14", antecedent_ids)
        k1 = next(item for item in causes[0]["antecedents"] if item["id"] == "K1")
        self.assertEqual(k1["causes"][0]["rule_id"], "R1")
        self.assertEqual(k1["causes"][0]["antecedents"][0]["id"], "F1")


class TestAdditionalCases(EngineTestCase):
    def test_all_no_is_inconclusive(self) -> None:
        result = self.infer([])
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(result["trace"], [])
        self.assertEqual(result["diagnoses"], [])
        self.assertEqual(result["inconclusive"]["detected_facts"], [])
        self.assertEqual(result["stats"]["iterations"], 0)
        self.assertTrue(result["inconclusive"]["suggestions"])

    def test_and_or_semantics(self) -> None:
        # OR: salah satu cukup.
        self.assertEqual(self.infer(["F7", "F5"])["diagnoses"][0]["id"], "H4")
        self.assertEqual(self.infer(["F7", "F11"])["diagnoses"][0]["id"], "H4")
        # AND: F7 saja tidak cukup.
        self.assertEqual(self.infer(["F7"])["diagnoses"], [])
        # F13 saja hanya menghasilkan K2, belum H2 karena F2 belum ada.
        result = self.infer(["F13"])
        self.assertEqual([item["id"] for item in result["diagnoses"]], [])
        self.assertEqual(result["working_memory"]["intermediate"][0]["id"], "K2")
        # F2 melengkapi K2 -> H2.
        self.assertEqual(self.infer(["F2", "F13"])["diagnoses"][0]["id"], "H2")

    def test_multiple_diagnoses_sorted_by_priority(self) -> None:
        result = self.infer(["F1", "F4", "F7", "F11"])
        self.assertEqual([item["id"] for item in result["diagnoses"]], ["H1", "H4"])
        self.assertEqual([item["priority"] for item in result["diagnoses"]], [1, 5])

    def test_multiple_rules_can_support_same_diagnosis(self) -> None:
        result = self.infer(["F1", "F4", "F14"])
        self.assertEqual(result["diagnoses"][0]["id"], "H1")
        self.assertEqual(set(result["diagnoses"][0]["rule_ids"]), {"R8", "R9"})

    def test_validation_rejects_missing_answers(self) -> None:
        with self.assertRaises(InputError) as context:
            validate_answers(self.kb, {"answers": {"F1": True}})
        self.assertEqual(len(context.exception.missing), 19)
        self.assertIn("F2", context.exception.missing)

    def test_validation_rejects_invalid_values(self) -> None:
        answers = self.answers([])
        answers["F1"] = "ya"
        with self.assertRaises(InputError) as context:
            validate_answers(self.kb, {"answers": answers})
        self.assertIn("F1", context.exception.invalid)

    def test_validation_rejects_unknown_and_missing_payload(self) -> None:
        answers = self.answers([])
        answers["F99"] = True
        with self.assertRaises(InputError):
            validate_answers(self.kb, {"answers": answers})
        with self.assertRaises(InputError):
            validate_answers(self.kb, {})
        with self.assertRaises(InputError):
            validate_answers(self.kb, None)

    def test_inference_is_fast(self) -> None:
        result = self.infer(self.kb.fact_order)
        self.assertLess(result["stats"]["elapsed_ms"], 1000)
        self.assertGreater(result["stats"]["elapsed_ms"], 0)


if __name__ == "__main__":
    unittest.main()
