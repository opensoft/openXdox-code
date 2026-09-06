"""Asserts the bootstrap posture of this leg (openXdox-code) is in place.

This is the required pytest suite `.github/workflows/validate.yml` runs on
every pull request. It checks the files that must exist at creation for a
public repository (LICENSE, SECURITY.md, CODEOWNERS) and this leg's own role
directory (`src/`).
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".gitignore",
    "LICENSE",
    "SECURITY.md",
    ".github/CODEOWNERS",
]


@pytest.mark.parametrize("relpath", REQUIRED_FILES)
def test_required_file_exists(relpath: str) -> None:
    path = ROOT / relpath
    assert path.is_file(), f"required posture file {relpath!r} is missing"


def test_license_is_apache_2_0() -> None:
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in text
    assert "Version 2.0" in text


def test_role_directory_exists() -> None:
    # This leg's role, per the assembly root's project.yaml (`legs[].role:
    # code`), is `src/`. project.yaml itself lives in the assembly root
    # (opensoft/openXdox), not in this leg.
    assert (ROOT / "src").is_dir()
