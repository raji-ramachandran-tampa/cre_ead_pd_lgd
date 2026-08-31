"""Tests for the Markdown-to-DOCX model-design publishing workflow."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "docs" / "model_design"
DEVELOPMENT = ROOT / "docs" / "model_development"
SOURCE = DESIGN / "content.md"
DEFAULTS = DESIGN / "pandoc.yaml"
REFERENCE = DESIGN / "reference.docx"
BUILD_SCRIPT = DESIGN / "build.ps1"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def source_heading_count(markdown: str) -> int:
    """Count level-one and level-two Markdown headings outside front matter."""
    return len(re.findall(r"^#{1,2}\s+\S", markdown, flags=re.MULTILINE))


def source_table_count(markdown: str) -> int:
    """Count GitHub/Pandoc pipe tables by their separator rows."""
    separator = re.compile(
        r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$",
        flags=re.MULTILINE,
    )
    return len(separator.findall(markdown))


def docx_xml(path: Path, member: str) -> ElementTree.Element:
    """Read and parse an XML member from an Office Open XML package."""
    with zipfile.ZipFile(path) as package:
        return ElementTree.fromstring(package.read(member))


class PublishingInputsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.markdown = SOURCE.read_text(encoding="utf-8")
        cls.defaults = DEFAULTS.read_text(encoding="utf-8")

    def test_authoritative_source_has_metadata_and_substance(self) -> None:
        self.assertTrue(self.markdown.startswith("---\n"))
        self.assertIn('title: "Commercial Real Estate Expected Loss', self.markdown)
        self.assertGreaterEqual(source_heading_count(self.markdown), 20)
        self.assertGreaterEqual(source_table_count(self.markdown), 10)

    def test_regulatory_links_are_explicit_https_links(self) -> None:
        links = re.findall(r"\[[^]]+]\((https://[^)]+)\)", self.markdown)
        self.assertGreaterEqual(len(links), 2)
        self.assertTrue(all(url.startswith("https://") for url in links))

    def test_pandoc_defaults_define_controlled_word_output(self) -> None:
        for setting in (
            "from: markdown+yaml_metadata_block+pipe_tables+task_lists",
            "to: docx",
            "standalone: true",
            "toc: true",
            "reference-doc: reference.docx",
        ):
            self.assertIn(setting, self.defaults)

    def test_reference_document_is_a_valid_docx(self) -> None:
        self.assertTrue(zipfile.is_zipfile(REFERENCE))
        with zipfile.ZipFile(REFERENCE) as package:
            members = set(package.namelist())
        self.assertIn("word/document.xml", members)
        self.assertIn("word/styles.xml", members)
        self.assertIn("word/settings.xml", members)

    def test_build_script_delegates_to_pandoc(self) -> None:
        script = BUILD_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Get-Command pandoc", script)
        self.assertIn("--defaults pandoc.yaml", script)
        self.assertIn("content.md", script)
        self.assertFalse((ROOT / "docs" / "build_model_design.py").exists())
        self.assertFalse((DESIGN / "build_document.py").exists())


class ModelDevelopmentSpecificationTest(unittest.TestCase):
    def test_required_development_documents_exist(self) -> None:
        required = {
            "README.md",
            "specification.md",
            "data_dictionary.md",
            "methodology_candidates.md",
            "acceptance_criteria.md",
            "pandoc.yaml",
        }
        self.assertTrue(required.issubset({path.name for path in DEVELOPMENT.iterdir()}))

    def test_specification_covers_all_expected_loss_components(self) -> None:
        specification = (DEVELOPMENT / "specification.md").read_text(encoding="utf-8")
        required_sections = (
            "# 7. PD development requirements",
            "# 8. LGD development requirements",
            "# 9. EAD development requirements",
            "# 10. Scenarios and expected-loss aggregation",
            "# 13. Required testing",
            "# 15. Open decisions and approvals required",
        )
        for section in required_sections:
            self.assertIn(section, specification)
        self.assertRegex(specification, r"does not establish\s+model approval")

    def test_acceptance_criteria_have_unique_requirement_ids(self) -> None:
        criteria = (DEVELOPMENT / "acceptance_criteria.md").read_text(encoding="utf-8")
        identifiers = re.findall(r"\| (DEV-[A-Z]+-\d{3}) \|", criteria)
        self.assertGreaterEqual(len(identifiers), 25)
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_data_dictionary_declares_core_output_fields(self) -> None:
        dictionary = (DEVELOPMENT / "data_dictionary.md").read_text(encoding="utf-8")
        for field in (
            "conditional_pd",
            "marginal_pd",
            "cumulative_pd",
            "projected_lgd",
            "projected_ead",
            "discount_factor",
            "expected_loss",
            "run_id",
        ):
            self.assertRegex(dictionary, rf"(?m)^\| {field} \|")

    def test_development_pandoc_config_reuses_controlled_template(self) -> None:
        defaults = (DEVELOPMENT / "pandoc.yaml").read_text(encoding="utf-8")
        self.assertIn("to: docx", defaults)
        self.assertIn("reference-doc: ../model_design/reference.docx", defaults)


@unittest.skipUnless(shutil.which("pandoc"), "Pandoc is not installed")
class PandocIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_directory = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp_directory.name) / "model-design.docx"
        subprocess.run(
            [
                "pandoc",
                "--defaults",
                "pandoc.yaml",
                "--output",
                str(cls.output),
                "content.md",
            ],
            cwd=DESIGN,
            check=True,
            capture_output=True,
            text=True,
        )
        cls.markdown = SOURCE.read_text(encoding="utf-8")
        cls.document = docx_xml(cls.output, "word/document.xml")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_directory.cleanup()

    def test_pandoc_creates_valid_docx(self) -> None:
        self.assertTrue(self.output.is_file())
        self.assertTrue(zipfile.is_zipfile(self.output))

    def test_all_source_headings_are_published_as_word_headings(self) -> None:
        styles = self.document.findall(f".//{{{W}}}pStyle")
        heading_count = sum(
            1
            for style in styles
            if style.get(f"{{{W}}}val", "").lower() in {"heading1", "heading2"}
        )
        self.assertEqual(source_heading_count(self.markdown), heading_count)

    def test_all_source_tables_are_published(self) -> None:
        tables = self.document.findall(f".//{{{W}}}tbl")
        self.assertEqual(source_table_count(self.markdown), len(tables))

    def test_external_hyperlinks_are_preserved(self) -> None:
        relationships = docx_xml(
            self.output, "word/_rels/document.xml.rels"
        )
        hyperlinks = [
            relationship
            for relationship in relationships.findall(f"{{{PKG_REL}}}Relationship")
            if relationship.get("Type", "").endswith("/hyperlink")
            and relationship.get("TargetMode") == "External"
        ]
        source_links = set(re.findall(r"\[[^]]+]\((https://[^)]+)\)", self.markdown))
        published_targets = {link.get("Target") for link in hyperlinks}
        self.assertTrue(source_links.issubset(published_targets))


@unittest.skipUnless(shutil.which("pandoc"), "Pandoc is not installed")
class DevelopmentDocumentPandocIntegrationTest(unittest.TestCase):
    def test_each_development_artifact_builds_as_docx(self) -> None:
        sources = (
            "specification.md",
            "data_dictionary.md",
            "methodology_candidates.md",
            "acceptance_criteria.md",
        )
        with tempfile.TemporaryDirectory() as temp_directory:
            for source in sources:
                with self.subTest(source=source):
                    output = Path(temp_directory) / source.replace(".md", ".docx")
                    subprocess.run(
                        [
                            "pandoc",
                            "--defaults",
                            "pandoc.yaml",
                            "--output",
                            str(output),
                            source,
                        ],
                        cwd=DEVELOPMENT,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    self.assertTrue(zipfile.is_zipfile(output))


if __name__ == "__main__":
    unittest.main(verbosity=2)
