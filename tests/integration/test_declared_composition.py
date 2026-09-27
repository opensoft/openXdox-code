"""The rules of `tests/integration/`, held to the files in it.

Plan 034 task T042 (box 9.3). `declared_composition.py` states three rules for
this directory. Two of them are properties of the code here, so they are
checked here, where a new file that breaks one fails the run instead of
waiting for a reviewer to notice:

  * every test names the pin it composes at, by taking `composition`;
  * nothing here skips, marks a skip, or expects a failure.

The third rule, no `conftest.py` here, is a property of the directory's
layout, and its reason is `declared_composition.py`'s.

And the composition itself, in F9.2's own words: the first block of F9.2
asserts that `pyproject.toml` names ONE full-commit `opendox` pin and that the
installed openDox is that commit. `test_the_composition_names_one_full_commit_pin_and_installs_it`
runs that block's two assertions as a test, so every run of the whole suite
(9.2's required check, from T043) makes them, not only a run of the falsifier.

A CREATED file: no carve-manifest row (RULED OQ-C). Its admission is a
`created:` entry in openxFactory's `docs/opendox-carve-admissions.yaml` (T047).
"""

from __future__ import annotations

import ast
import importlib.metadata as md
import json
import re
import tomllib
from pathlib import Path

from declared_composition import (  # noqa: F401  (a fixture, by name)
    Composition,
    composition,
)

HERE = Path(__file__).resolve().parent
LEG_ROOT = HERE.parents[1]

#: The pytest names that skip a test or expect it to fail. Each is refused
#: wherever it is reached in this directory, as `pytest.<name>`, as
#: `pytest.mark.<name>`, or through an alias of either.
REFUSED_PYTEST_NAMES = ("skip", "skipif", "importorskip", "xfail")


def _modules() -> list[Path]:
    """Every Python file here, this one included."""
    return sorted(HERE.glob("*.py"))


def _test_modules() -> list[Path]:
    return [path for path in _modules() if path.name.startswith("test_")]


def _tests(tree: ast.Module):
    """Every test function pytest would collect from a module: module-level
    `test_*` functions, and `test_*` methods of `Test*` classes."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                yield node.name, node
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for item in node.body:
                if (isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and item.name.startswith("test_")):
                    yield f"{node.name}.{item.name}", item


def _arguments(node) -> set[str]:
    args = node.args
    return {arg.arg for arg in (*args.posonlyargs, *args.args,
                                *args.kwonlyargs)}


def _dotted(node) -> str:
    """`pytest.mark.skipif` for that attribute chain; "" for anything else."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def test_the_composition_names_one_full_commit_pin_and_installs_it(
        composition: Composition) -> None:
    """F9.2's first block, as a test: `pyproject.toml` names ONE `opendox`
    dependency pinned by full commit, and the installed openDox is that
    commit, read from the `direct_url.json` pip records for a VCS install."""
    deps = tomllib.loads((LEG_ROOT / "pyproject.toml").read_text(
        encoding="utf-8"))["project"]["dependencies"]
    pins = [d for d in deps if re.match(r"opendox\s*@", d)]
    assert len(pins) == 1 and re.search(r"@[0-9a-f]{40}$", pins[0]), (
        f"the composition names no full-commit pin: {pins}")
    got = json.loads(md.distribution("opendox").read_text("direct_url.json")
                     or "{}").get("vcs_info", {}).get("commit_id")
    assert got == pins[0].rsplit("@", 1)[1], (
        f"the installed openDox is {got!r}, not the pinned commit")
    # And the fixture every test here takes read the same commit, so the pin
    # the tests name is the one F9.2 checks.
    assert composition.pin == got, (composition.pin, got)


def test_every_test_here_names_the_pin_it_composes_at(
        composition: Composition) -> None:
    """Rule 1: each test takes `composition`, which records the pin on its
    report and fails if this checkout is not the declared composition."""
    unnamed = []
    for path in _test_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for name, node in _tests(tree):
            if "composition" not in _arguments(node):
                unnamed.append(f"{path.name}::{name}")
    assert unnamed == [], (
        f"at {composition}: these tests do not take `composition`, so they do "
        f"not name the pin they compose at (box 9.3): {unnamed}")
    assert _test_modules(), "no test module here: the rule checked nothing"


def test_nothing_here_skips_or_expects_a_failure(
        composition: Composition) -> None:
    """Rule 2: at the declared composition a skip is a composition that is
    missing, and F9.2 runs every file here. So no file here reaches
    `pytest.skip`, `pytest.importorskip`, `pytest.xfail` or a `skip`,
    `skipif` or `xfail` mark, by name or through an alias."""
    reached = []
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        # The names this module binds to `pytest` and to `pytest.mark`:
        # `import pytest as pt` and `from pytest import mark as m` are aliases
        # whose attributes this scan must still see.
        pytest_names, mark_names = {"pytest"}, set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                pytest_names |= {a.asname for a in node.names
                                 if a.name == "pytest" and a.asname}
            elif isinstance(node, ast.ImportFrom) and node.module == "pytest":
                for alias in node.names:
                    if alias.name in REFUSED_PYTEST_NAMES:
                        reached.append(f"{path.name}:{node.lineno} imports "
                                       f"pytest.{alias.name}")
                    elif alias.name == "mark":
                        mark_names.add(alias.asname or "mark")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            head, _, rest = _dotted(node).partition(".")
            if head in pytest_names:
                parts = rest.split(".")
            elif head in mark_names:
                parts = ["mark", *rest.split(".")]
            else:
                continue
            if parts[0] in REFUSED_PYTEST_NAMES or (
                    parts[0] == "mark" and len(parts) > 1
                    and parts[1] in REFUSED_PYTEST_NAMES):
                reached.append(f"{path.name}:{node.lineno} reaches "
                               f"{_dotted(node)}")
    assert sorted(set(reached)) == [], (
        f"at {composition}: a declared integration test may not skip or "
        f"expect a failure, because the composition is what this directory "
        f"declares: {sorted(set(reached))}")
