"""Pure-Python command-line interface for local development workflows."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .paths import fannie_data_root, fannie_release_directory
from .publishing import publish_docx


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _test(_: argparse.Namespace) -> int:
    return subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
        cwd=REPOSITORY_ROOT,
        check=False,
    ).returncode


def _data_root(arguments: argparse.Namespace) -> int:
    path = (
        fannie_release_directory(arguments.release)
        if arguments.release
        else fannie_data_root()
    )
    print(path)
    return 0


def _build_document(arguments: argparse.Namespace) -> int:
    directory = REPOSITORY_ROOT / "docs" / arguments.document
    source = directory / arguments.source
    defaults = directory / "pandoc.yaml"
    output = Path(arguments.output)
    if not output.is_absolute():
        output = directory / output
    print(publish_docx(source, output, defaults))
    return 0


def parser() -> argparse.ArgumentParser:
    """Create the command parser."""
    result = argparse.ArgumentParser(prog="cre-el")
    commands = result.add_subparsers(dest="command", required=True)

    tests = commands.add_parser("test", help="run the repository test suite")
    tests.set_defaults(handler=_test)

    data = commands.add_parser("data-root", help="show the configured Fannie data path")
    data.add_argument("--release", help="optional release such as 2026Q1")
    data.set_defaults(handler=_data_root)

    document = commands.add_parser("build-doc", help="publish a Markdown document to DOCX")
    document.add_argument(
        "--document",
        choices=("model_design", "model_development"),
        default="model_design",
    )
    document.add_argument("--source", default="content.md")
    document.add_argument("--output", default="preview.docx")
    document.set_defaults(handler=_build_document)
    return result


def main() -> int:
    """Run the selected command."""
    arguments = parser().parse_args()
    return int(arguments.handler(arguments))


if __name__ == "__main__":
    raise SystemExit(main())

