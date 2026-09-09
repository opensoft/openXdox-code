"""Asserts the bootstrap posture of this leg (openXdox-code) is in place.

This is the required pytest suite `.github/workflows/validate.yml` runs on
every pull request. It checks the files that must exist at creation for a
public repository (LICENSE, SECURITY.md, CODEOWNERS) and this leg's own role
directory (`src/`).
"""

from __future__ import annotations

import sys
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


def test_branch_protection_evidence_exists() -> None:
    # tasks.md § 1.5's evidence line: a ruleset is a repository SETTING, so
    # the only thing a tree can assert is that the evidence file naming it is
    # present. Levelled across all six repositories by the OQ-O pass
    # (openxFactory#656).
    assert (ROOT / "docs" / "branch-protection.md").is_file()


def test_import_root_exists() -> None:
    # The import root created by the OQ-O levelling pass (openxFactory#656).
    # A `src/` layout needs one, or `import openxdox` does not resolve under
    # `python -m pytest` run from the repository root once the carve lands,
    # and the required `validate` check goes red for a reason that has
    # nothing to do with the carve.
    assert (ROOT / "pyproject.toml").is_file()
    assert (ROOT / "conftest.py").is_file()


def test_src_is_on_sys_path() -> None:
    # Proves the root `conftest.py` (or `pyproject.toml`'s pytest
    # `pythonpath` setting) actually RAN and put `src/` on sys.path, rather
    # than merely existing.
    assert str(ROOT / "src") in sys.path
