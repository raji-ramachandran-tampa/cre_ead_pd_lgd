"""Optional Pandoc publishing invoked through the Python project interface."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def publish_docx(source: Path, output: Path, defaults: Path) -> Path:
    """Publish Markdown to DOCX using optional Pandoc and return the output path."""
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise RuntimeError(
            "Pandoc is required only for DOCX publication and was not found"
        )
    source, output, defaults = Path(source), Path(output), Path(defaults)
    for required in (source, defaults):
        if not required.is_file():
            raise FileNotFoundError(required)
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            pandoc,
            "--defaults",
            defaults.name,
            "--output",
            str(output.resolve()),
            source.name,
        ],
        cwd=source.parent,
        check=True,
    )
    return output.resolve()

