"""Contract tests for the proposed public-data source registry."""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "public_sources.yaml"
SELECTION = ROOT / "docs" / "data_sources" / "public_source_selection.md"
MAPPING = ROOT / "docs" / "data_sources" / "field_mapping.md"
EXPERIMENTS = ROOT / "config" / "comparative_experiments.yaml"
COMPARISON = ROOT / "docs" / "model_development" / "comparative_methodology_plan.md"


class PublicSourceRegistryStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = REGISTRY.read_text(encoding="utf-8")
        cls.selection = SELECTION.read_text(encoding="utf-8")
        cls.mapping = MAPPING.read_text(encoding="utf-8")

    def test_source_ids_are_unique_and_expected_sources_are_present(self) -> None:
        identifiers = re.findall(r"(?m)^\s+- id: ([a-z0-9_]+)$", self.registry)
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertGreaterEqual(len(identifiers), 11)
        for required in (
            "fannie_mflpd",
            "sec_abs_ee",
            "frb_scenario",
            "fred_alfred",
            "ffiec_call",
        ):
            self.assertIn(required, identifiers)

    def test_registry_uses_https_and_environment_variable_credentials(self) -> None:
        urls = re.findall(r"(?m)^\s+(?:api|landing|discovery|documentation)_url: (\S+)$", self.registry)
        self.assertGreaterEqual(len(urls), 10)
        self.assertTrue(all(url.startswith("https://") for url in urls))
        self.assertNotRegex(self.registry, r"(?i)(api_key|password|secret):\s+[A-Za-z0-9]{8,}")
        self.assertIn("FRED_API_KEY", self.registry)
        self.assertIn("BEA_API_KEY", self.registry)

    def test_primary_source_and_restrictions_are_explicit(self) -> None:
        self.assertRegex(
            self.registry,
            r"(?s)id: fannie_mflpd.*?status: selected_primary_registration_required"
            r".*?restrictions_review: required_no_redistribution",
        )
        self.assertIn("does not yet support production", self.selection)
        self.assertIn("Major gap risk", self.mapping)

    def test_all_registry_sources_appear_in_selection_document(self) -> None:
        identifiers = re.findall(r"(?m)^\s+- id: ([a-z0-9_]+)$", self.registry)
        labels = {
            "fannie_mflpd": "FANNIE-MFLPD",
            "sec_abs_ee": "SEC-ABS-EE",
            "frb_scenario": "FRB-SCENARIO",
            "fred_alfred": "FRED-ALFRED",
            "bls_public": "BLS-PUBLIC",
            "bea_regional": "BEA-REGIONAL",
            "census_bps": "CENSUS-BPS",
            "ffiec_call": "FFIEC-CALL",
            "frb_sloos": "FRB-SLOOS",
            "fhfa_hpi": "FHFA-HPI",
            "bis_cppi": "BIS-CPPI",
        }
        self.assertEqual(set(identifiers), set(labels))
        for identifier in identifiers:
            self.assertIn(labels[identifier], self.selection)

    def test_comparative_plan_covers_three_families_for_each_component(self) -> None:
        experiments = EXPERIMENTS.read_text(encoding="utf-8")
        comparison = COMPARISON.read_text(encoding="utf-8")
        for component in ("pd", "lgd", "ead"):
            self.assertRegex(experiments, rf"(?m)^  {component}:$")
        self.assertEqual(experiments.count("    classical:"), 3)
        self.assertEqual(experiments.count("    bayesian:"), 3)
        self.assertEqual(experiments.count("    machine_learning:"), 3)
        for heading in ("# 3. PD comparison", "# 4. LGD comparison", "# 5. EAD comparison"):
            self.assertIn(heading, comparison)
        self.assertIn("does not assume", comparison)


@unittest.skipUnless(importlib.util.find_spec("yaml"), "PyYAML is not installed")
class PublicSourceRegistryYamlTest(unittest.TestCase):
    def test_registry_parses_and_has_required_contract(self) -> None:
        import yaml

        registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(registry["approval_status"], "proposed_not_approved")
        self.assertIsInstance(registry["sources"], list)
        for source in registry["sources"]:
            for required in ("id", "authority", "role", "status", "authentication"):
                self.assertIn(required, source)
            self.assertIn("restrictions_review", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
