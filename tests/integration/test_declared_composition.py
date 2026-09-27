"""The rules of `tests/integration/`, held to the files in it.

Plan 034 task T042 (box 9.3). `declared_composition.py` states three rules for
this directory, and each is checked here, where a new file that breaks one
fails the run instead of waiting for a reviewer to notice:

  * every test names the pin it composes at, by taking `composition`, and
    every file pytest collects here is one F9.2 runs;
  * nothing here skips, marks a skip, or expects a failure;
  * there is no `conftest.py` here.

Rule 1 is read from pytest's own COLLECTION of this directory, not from a
reading of its source. A child interpreter collects it with this run's
`python_files`, `python_classes` and `python_functions`, and reports every item
it collects. So a test that pytest collects by a route a source reading would
miss is still examined: a `unittest.TestCase` of any name, a method inherited
from a base class, or a test bound by assignment.

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
import fnmatch
import importlib.metadata as md
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from declared_composition import (  # noqa: F401  (a fixture, by name)
    Composition,
    composition,
)

HERE = Path(__file__).resolve().parent
LEG_ROOT = HERE.parents[1]

#: The files F9.2 runs, one at a time: `ls tests/integration/test_*.py`.
F92_GLOB = "test_*.py"

#: Every name that skips a test or expects it to fail, in pytest and in
#: `unittest`, compared case-insensitively. Rule 2 refuses each of them wherever
#: this directory's code names it: as an attribute (`pytest.skip`,
#: `m.skipif` for any alias `m`, `unittest.SkipTest`), as an imported name, or
#: as a string that reaches one (`getattr(pytest, "skip")`,
#: `add_marker("xfail")`). This tuple is the one place that may spell them.
REFUSED_NAMES = ("skip", "skipif", "skipunless", "importorskip", "xfail",
                 "skiptest", "expectedfailure", "skipped", "xfailed")


#: The collection settings the child is given, as this run has them.
COLLECTION_SETTINGS = ("python_files", "python_classes", "python_functions")

#: What the child does not inherit: `PYTHONPATH`, which a lone checkout does not
#: have, and `PYTEST_ADDOPTS` and `PYTEST_PLUGINS`, which could change what it
#: collects. `tests/test_declared_exclusion.py` gives its own children the
#: same scrub.
SCRUBBED_ENVIRONMENT = ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS")
#: What the child is given: plugin autoloading off, so the collection it
#: reports is pytest's own plugins and this directory, and no installed plugin
#: can add items, fixtures or hooks to it.
CHILD_ENVIRONMENT = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}

#: The child: pytest collects this directory, and each item is reported with
#: whether pytest hands it `composition` as an argument of its own, and with
#: the names of the marks pytest finds on it. Taking the fixture needs both
#: halves: its function has a parameter of that name with no default (pytest
#: does not fill a parameter that has one), and pytest resolves the fixture
#: for it. The conftest chain is off, because what is audited is what this
#: directory holds.
_COLLECT = r'''
import inspect, json, sys

import pytest


class Audit:
    def __init__(self):
        self.items = []

    def pytest_collection_finish(self, session):
        for item in session.items:
            try:
                parameter = inspect.signature(item.obj).parameters.get(
                    "composition")
            except (AttributeError, TypeError, ValueError):
                parameter = None
            takes = (parameter is not None
                     and parameter.default is inspect.Parameter.empty
                     and parameter.kind not in (parameter.VAR_POSITIONAL,
                                                parameter.VAR_KEYWORD)
                     and "composition" in getattr(item, "fixturenames", ()))
            self.items.append({"nodeid": item.nodeid, "path": str(item.path),
                               "takes": takes,
                               "marks": sorted({mark.name for mark
                                                in item.iter_markers()})})


audit = Audit()
code = pytest.main(sys.argv[2:], plugins=[audit])
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump({"code": int(code), "items": audit.items}, handle)
'''

#: The child's reading, once per run and per collection settings.
_COLLECTED: dict = {}


def _collected(composition: Composition, config) -> list[dict]:
    """Every item pytest collects from this directory, at any depth, with this
    run's collection settings. Fails, naming pytest's own words, if the
    directory does not collect cleanly, since then no rule can be read."""
    settings = tuple((name, tuple(config.getini(name)))
                     for name in COLLECTION_SETTINGS)
    if settings not in _COLLECTED:
        args = ["--collect-only", "-q", "--noconftest", "-p", "no:cacheprovider"]
        for name, values in settings:
            args += ["-o", f"{name}={' '.join(values)}"]
        env = {key: value for key, value in os.environ.items()
               if key not in SCRUBBED_ENVIRONMENT}
        env.update(CHILD_ENVIRONMENT)
        with tempfile.TemporaryDirectory() as scratch:
            report = Path(scratch) / "collected.json"
            done = subprocess.run(
                [sys.executable, "-c", _COLLECT, str(report), *args, str(HERE)],
                cwd=LEG_ROOT, env=env, capture_output=True, text=True,
                timeout=300)
            found = (json.loads(report.read_text(encoding="utf-8"))
                     if report.exists() else {"code": None, "items": []})
        found["tail"] = (done.stdout + done.stderr)[-3000:]
        _COLLECTED[settings] = found
    found = _COLLECTED[settings]
    # pytest's own exit codes: 0 collected, 2 a collection error, 5 nothing.
    assert found["code"] == 0 and found["items"], (
        f"at {composition}: pytest did not collect this directory cleanly "
        f"(exit {found['code']}, {len(found['items'])} items), so its rules "
        f"cannot be read:\n{found['tail']}")
    return found["items"]


def _refused(name: str) -> bool:
    return name.lower() in REFUSED_NAMES


#: The no-argument `str` methods a constant string expression may use, so that
#: `"SK".lower()` is read as the string it makes.
_STRING_METHODS = ("lower", "upper", "casefold", "strip", "lstrip", "rstrip",
                   "capitalize", "swapcase", "title")

#: The longest string a repetition is folded into; a longer one is left
#: unread rather than built.
_FOLD_LIMIT = 256


def _folded(node):
    """The string a CONSTANT string expression makes, or None if the node is
    not one. That is a string literal, `+` of two of them, `*` by an integer
    literal, an f-string of them, `sep.join([...])` of them, and the case
    methods above. So `getattr(pytest, "s" + "kip")` is read as what it
    reaches."""
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _folded(node.left), _folded(node.right)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        for text, count in ((node.left, node.right), (node.right, node.left)):
            value = _folded(text)
            if (value is not None and isinstance(count, ast.Constant)
                    and type(count.value) is int
                    and 0 <= len(value) * count.value <= _FOLD_LIMIT):
                return value * count.value
        return None
    if isinstance(node, ast.JoinedStr):
        parts = []
        for part in node.values:
            if isinstance(part, ast.FormattedValue):
                if part.conversion != -1 or part.format_spec is not None:
                    return None
                part = part.value
            value = _folded(part)
            if value is None:
                return None
            parts.append(value)
        return "".join(parts)
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and not node.keywords):
        base = _folded(node.func.value)
        if base is None:
            return None
        if (node.func.attr == "join" and len(node.args) == 1
                and isinstance(node.args[0], (ast.List, ast.Tuple))):
            items = [_folded(item) for item in node.args[0].elts]
            return None if None in items else base.join(items)
        if node.func.attr in _STRING_METHODS and not node.args:
            return getattr(base, node.func.attr)()
    return None


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


def test_every_file_pytest_collects_here_is_one_f9_2_runs(
        composition: Composition, request) -> None:
    """Rule 1's other half. F9.2 runs `ls tests/integration/test_*.py`, one
    file at a time. pytest also collects `*_test.py` by default, and it
    collects a subdirectory's files. A test file of either kind would run in
    the whole suite and never in F9.2's loop."""
    missed = sorted({
        Path(item["path"]).resolve().relative_to(HERE).as_posix()
        for item in _collected(composition, request.config)
        if Path(item["path"]).resolve().parent != HERE
        or not fnmatch.fnmatch(Path(item["path"]).name, F92_GLOB)})
    assert missed == [], (
        f"at {composition}: pytest collects these files here, and F9.2's "
        f"`ls tests/integration/{F92_GLOB}` does not list them: {missed}")


def test_every_test_here_names_the_pin_it_composes_at(
        composition: Composition, request) -> None:
    """Rule 1: each test takes `composition`, which records the pin on the
    run's report and fails if this checkout is not the declared composition.
    Every item pytest collects here is read, however pytest reached it, and
    each must have the fixture handed to it as an argument of its own: a
    default value, a `usefixtures` mark or another fixture that uses it does
    not give the test the pin to name."""
    unnamed = [item["nodeid"]
               for item in _collected(composition, request.config)
               if not item["takes"]]
    assert unnamed == [], (
        f"at {composition}: these tests do not take `composition`, so they do "
        f"not name the pin they compose at (box 9.3): {unnamed}")


def test_nothing_here_skips_or_expects_a_failure(
        composition: Composition, request) -> None:
    """Rule 2: at the declared composition a skip is a composition that is
    missing, and F9.2 runs every file here. So no code here names a way to
    skip or to expect a failure, from pytest or from `unittest`, by any
    alias: not as an attribute, not as an imported name, and not as a string
    that reaches one, a constant string expression included. Only
    `REFUSED_NAMES` itself may spell them. And no item pytest collects here
    carries a skip or xfail mark, however the mark was spelled, as pytest's
    own collection reports it.

    A name computed at run time from something that is not a constant is past
    what any reading of source can see. It is not past the required check:
    JUnit reports every skip and every xfail as skipped, and the triple pins
    SKIPPED exactly, so such a test here refuses `validate`'s `Pin the
    triple` all the same."""
    reached = []
    for path in sorted(HERE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        # The one declaration that may spell the names: this module's tuple.
        spelled_here = set()
        for node in tree.body:
            if (isinstance(node, ast.Assign) and path == Path(__file__).resolve()
                    and any(isinstance(target, ast.Name)
                            and target.id == "REFUSED_NAMES"
                            for target in node.targets)):
                spelled_here |= {id(item) for item in ast.walk(node.value)}
        for node in ast.walk(tree):
            where = f"{path.relative_to(HERE).as_posix()}:{getattr(node, 'lineno', '?')}"
            if isinstance(node, ast.Attribute) and _refused(node.attr):
                reached.append(f"{where} reaches .{node.attr}")
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    for part in alias.name.split("."):
                        if _refused(part):
                            reached.append(f"{where} imports {alias.name}")
            elif isinstance(node, ast.Name) and _refused(node.id):
                reached.append(f"{where} names {node.id}")
            elif id(node) not in spelled_here:
                value = _folded(node)
                if value is not None and _refused(value):
                    reached.append(f"{where} spells {value!r}")
    for item in _collected(composition, request.config):
        for name in item["marks"]:
            if _refused(name):
                reached.append(f"{item['nodeid']} is marked {name}")
    assert sorted(set(reached)) == [], (
        f"at {composition}: a declared integration test may not skip or "
        f"expect a failure, because the composition is what this directory "
        f"declares: {sorted(set(reached))}")


def test_no_conftest_takes_the_flat_slot_here(
        composition: Composition) -> None:
    """Rule 3. `conftest` is one flat name in `sys.modules`, and pytest imports
    a rootless `conftest.py` under it, deleting the previous occupant first. A
    `conftest.py` here, or in a directory below, would take that slot from
    `tests/conftest.py` for every module collected after this directory, and
    `integration` sorts before every `test_*.py` beside it. The fixtures live in
    `declared_composition.py` instead."""
    found = sorted(path.relative_to(HERE).as_posix()
                   for path in HERE.rglob("conftest.py"))
    assert found == [], (
        f"at {composition}: {found} would take the flat `conftest` slot from "
        "tests/conftest.py for every module collected after this directory "
        "(tests/hermeticity.py::claim_conftest_slot says how)")
