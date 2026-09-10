"""Asserts the DEPENDENCY DIRECTION this leg is held to.

`split-opendox-two-layer-product` § 4.1 carves openXdox's column into this
repository, and `design.md`:243 states the standard the carve is held to in one
sentence: **"What must not survive is the direction, not the calls."** The pin
chain runs one way — `openxFactory` pins the openXdox assembly root (§ 5.1,
RULING F), openXdox pins openDox (RULED OQ-2) — so:

* a module of this package may import `opendox` freely;
* it may NOT import openxFactory's own column (its consumer) at import time;
* and the `opendox` this leg PINS may not import `openxdox` back.

The first two are asserted STRICTLY here and hold today. The third does not
hold today and cannot be made to hold from this repository: the back-imports
are in `opensoft/openDox-code`, which this leg consumes and does not write. It
is therefore asserted as a RATCHET over a landed census — the count may fall,
never rise — so the BUILD arc (§ 3.5/3.6) is measured against a number in the
tree rather than one re-derived from a thread each time.

A CREATED FILE: no row in `docs/opendox-carve-manifest.yaml` (RULED OQ-C, the
manifest declares what LEAVES openxFactory). Run by `.github/workflows/
validate.yml` beside `test_leg_shape.py`; it is a SHAPE assertion authored at
this leg, and adding it does not un-narrow RULED Q-L8 (b′) — the carved suites
stay out of `validate` until the BUILD arc makes them runnable.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

#: The only list of standard-library roots correct for the interpreter that is
#: actually running — the set moves between versions and this leg pins 3.12.
_STDLIB = frozenset(sys.stdlib_module_names)

# --------------------------------------------------------------------------
# What this leg is allowed to reach, and why each name is on the list
# --------------------------------------------------------------------------

#: This leg's own importable names: the package and the two top-level
#: extension-point seams that sit beside it under `src/` (RULED Q-L1/Q-L8 (a)).
OWN = frozenset({"openxdox", "route_extension", "subcommand_extension"})

#: Cross-package roots `src/` may reach AT IMPORT TIME.
#:   opendox    — the pinned upstream; this IS the lawful direction.
#:   yaml       — a declared runtime dependency (`pyproject.toml`).
#:   doc_health — § 4.1's own second clause makes these the adapter's
#:                IMPLEMENTATION SURFACE, "where importing doc-health is
#:                lawful". Lawful here does not mean REACHABLE here: the
#:                module is openxFactory's corpus machinery, is not vendored,
#:                is not on PyPI and is not in this leg's dependency set, so
#:                these imports still raise at run time. Making them resolve
#:                is BUILD-arc work (§ 3.5/3.6); keeping them ENUMERATED is
#:                this suite's job.
IMPORT_TIME_ALLOWED = frozenset({"opendox", "yaml", "doc_health"})

#: Additionally reachable inside a function body. `jsonschema` is reached once
#: (`gate_console.py:563`) and is NOT in `pyproject.toml`'s dependency set —
#: recorded here as a finding rather than silently declared, because adding a
#: dependency is not a direction fix.
DEFERRED_ALSO_ALLOWED = frozenset({"jsonschema"})

#: The pre-carve package name. Every arrived module's `import rewrites` edit
#: class exists to retire it; a survivor under `src/` is an UNAPPLIED rewrite,
#: and — because openxFactory is this leg's CONSUMER — a wrong-direction edge.
PRE_CARVE_PACKAGE = "ideation_dashboard"


# --------------------------------------------------------------------------
# The import census — "runs at import time" means what it says
# --------------------------------------------------------------------------

def _census(tree: ast.Module) -> list[tuple[ast.stmt, str, bool]]:
    """Every absolute import as `(node, root_module, runs_at_import_time)`.

    Descends into module-level `if` / `try` / `with` blocks — an import there
    DOES run when the module is imported — and stops at function and class
    bodies, which do not. A column offset would get both of those wrong:
    `serve_gate.py`'s reaches sit at column 8 inside a function, and a
    module-level `try:` import sits at column 4 and is import-time.
    """
    found: list[tuple[ast.stmt, str, bool]] = []

    def walk(nodes: list[ast.stmt], at_import_time: bool) -> None:
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.append((node, alias.name.split(".")[0], at_import_time))
            elif isinstance(node, ast.ImportFrom) and not node.level:
                found.append((node, (node.module or "").split(".")[0], at_import_time))
            deeper = at_import_time and not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            for _field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    walk([n for n in value if isinstance(n, ast.stmt)], deeper)

    walk(tree.body, True)
    return found


def _modules(base: Path) -> list[Path]:
    return sorted(p for p in base.rglob("*.py") if ".git" not in p.parts)


def _src_census() -> list[tuple[str, int, str, bool]]:
    """`(relpath, lineno, root_module, runs_at_import_time)` for all of `src/`."""
    rows: list[tuple[str, int, str, bool]] = []
    for path in _modules(SRC):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(ROOT).as_posix()
        for node, root, at_import_time in _census(tree):
            rows.append((rel, node.lineno, root, at_import_time))
    return rows


# --------------------------------------------------------------------------
# 1 — this leg's own tree. STRICT; these hold today.
# --------------------------------------------------------------------------

def test_the_pre_carve_package_name_does_not_survive_under_src() -> None:
    """No module under `src/` imports `ideation_dashboard`.

    It survived the carve at exactly one site — `cli_gate.py:49`,
    `from ideation_dashboard import human_seen as human_seen_mod`, an
    `import rewrites` line the manifest declares (lines 44-54, 74) and the
    carve left unapplied because `human_seen` is a
    `not_moved / stays_openxfactory_adapter` row that exists at NEITHER
    destination. It is now reached late through `openxdox.consumer_reach`.
    """
    survivors = [f"{rel}:{line}" for rel, line, root, _ in _src_census()
                 if root == PRE_CARVE_PACKAGE]
    assert survivors == [], (
        f"{len(survivors)} import(s) under src/ still name the PRE-CARVE "
        f"package {PRE_CARVE_PACKAGE!r}: {survivors}. openxFactory is this "
        "leg's CONSUMER (split-opendox § 5.1, RULING F), so an import of its "
        "column is the dependency direction running backwards, and an "
        "unapplied `import rewrites` edit besides")


def test_no_module_under_src_reaches_its_consumer_at_import_time() -> None:
    """Every import-time cross-package reach out of `src/` is on the list."""
    offenders = sorted({
        f"{rel}:{line} -> {root}" for rel, line, root, at_import in _src_census()
        if at_import and root not in OWN
        and root not in IMPORT_TIME_ALLOWED
        and root not in _STDLIB
    })
    assert offenders == [], (
        "import-time reach(es) out of src/ that this leg does not declare: "
        f"{offenders}. Importing a module of this package must not require "
        "anything but `opendox` (the pinned upstream), its declared runtime "
        "dependencies, and — under § 4.1's own second clause — `doc_health`. "
        "A new name here is a new dependency or a new direction defect; "
        "declare it in pyproject.toml and add it above, or reach it late")


def test_every_deferred_cross_package_reach_out_of_src_is_known() -> None:
    """The same list, one name wider, for reaches inside a function body."""
    allowed = IMPORT_TIME_ALLOWED | DEFERRED_ALSO_ALLOWED
    offenders = sorted({
        f"{rel}:{line} -> {root}" for rel, line, root, at_import in _src_census()
        if not at_import and root not in OWN and root not in allowed
        and root not in _STDLIB
    })
    assert offenders == [], (
        f"deferred cross-package reach(es) out of src/ nothing declares: "
        f"{offenders}")


def test_the_lawful_direction_is_actually_exercised() -> None:
    """openXdox imports openDox — the direction the pin chain declares.

    A guard that only forbids things passes trivially on an empty tree. This
    one asserts the edge the chain REQUIRES is present, so a future change
    that severs it (a vendored fork of openDox, say) is caught here too.
    """
    opendox_sites = [f"{rel}:{line}" for rel, line, root, _ in _src_census()
                     if root == "opendox"]
    assert len(opendox_sites) >= 20, (
        f"only {len(opendox_sites)} import(s) of `opendox` under src/: "
        "openXdox is supposed to CONSUME openDox (RULED OQ-2). If the count "
        "fell this far, check that the leg has not forked its upstream")


# --------------------------------------------------------------------------
# 2 — § 4.1's own second clause: the doc-health implementation surface
# --------------------------------------------------------------------------

#: § 4.1: "The 23 outbound `doc_health` imports become the adapter's
#: IMPLEMENTATION SURFACE here, where importing doc-health is lawful."
#: MEASURED at the leg's own tree rather than carried: 13 statements over 8
#: modules under `src/` (8 at import time, 5 deferred); 25 over 15 files
#: counting the carved `tests/`. The box's "23" is a whole-package figure from
#: design § D3's `serve.py` paragraph and is not exactly measurable as written
#: — recorded, on the reality check of 2026-09-10, as an arithmetic note and
#: not a defect. What this test does is make the surface ENUMERATED, so a new
#: reach into openxFactory's corpus machinery is a deliberate act.
DOC_HEALTH_SURFACE: dict[str, tuple[int, int]] = {
    # module                              (import-time, deferred)
    "src/openxdox/cli_gate.py":           (0, 1),
    "src/openxdox/completeness.py":       (1, 0),
    "src/openxdox/corpus_root.py":        (1, 0),
    "src/openxdox/gate_console.py":       (1, 3),
    "src/openxdox/gate_routes.py":        (0, 1),
    "src/openxdox/generator.py":          (3, 0),
    "src/openxdox/round_trip.py":         (1, 0),
    "src/openxdox/snapshot_registry.py":  (1, 0),
}


def test_the_doc_health_implementation_surface_is_exactly_declared() -> None:
    observed: dict[str, list[int]] = {}
    for rel, _line, root, at_import in _src_census():
        if root != "doc_health":
            continue
        slot = observed.setdefault(rel, [0, 0])
        slot[0 if at_import else 1] += 1
    assert {k: tuple(v) for k, v in observed.items()} == DOC_HEALTH_SURFACE, (
        "the doc_health implementation surface (§ 4.1's second clause) moved. "
        f"declared={DOC_HEALTH_SURFACE} observed="
        f"{ {k: tuple(v) for k, v in observed.items()} }. Update the table "
        "with the reason in the commit message; these imports are lawful HERE "
        "and nowhere else in the estate")


# --------------------------------------------------------------------------
# 3 — the RATCHET over the pinned openDox. Does not hold yet, by construction.
# --------------------------------------------------------------------------

#: The openDox → openXdox back-imports, MEASURED at the commit this leg pins
#: (`pyproject.toml`: `opendox @ git+…@8e9ffa628e96f621ab23af47873e5f2c2267b8db`)
#: and identical at `ce53b489`, the commit openDox's ASSEMBLY ROOT pins. The 13
#: import-time reaches are the census RULED 5626260214 calls "the 13-line
#: openDox→openXdox inversion" — recorded on openxFactory#656 as
#: `cli.py ×5, serve.py ×5, serve_workbench.py, branch_session.py,
#: workbench.py`. Removing them is BUILD-arc work (§ 3.5/3.6) at
#: `opensoft/openDox-code`, through the § 2.4 extension points; this leg
#: already supplies its half of those seams.
#:
#: A RATCHET, not a target: the numbers may only FALL. When a BUILD-arc slice
#: lands, lower them here in the same act — the suite refuses a silent
#: improvement as well as a regression, so the number in the tree stays true.
OPENDOX_BACK_IMPORTS: dict[str, tuple[int, int]] = {
    # module                        (import-time, deferred)
    "opendox/branch_session.py":    (1, 7),
    "opendox/cli.py":               (5, 1),
    "opendox/serve.py":             (5, 2),
    "opendox/serve_project.py":     (0, 2),
    "opendox/serve_workbench.py":   (1, 7),
    "opendox/workbench.py":         (1, 0),
}
OPENDOX_BACK_IMPORTS_AT_IMPORT_TIME = 13
OPENDOX_BACK_IMPORTS_DEFERRED = 19


def _pinned_opendox_root() -> Path:
    spec = importlib.util.find_spec("opendox")
    if spec is None or not spec.submodule_search_locations:
        pytest.fail(
            "`opendox` is not importable, so the direction of the pinned "
            "upstream cannot be measured. It is a declared RUNTIME dependency "
            "of this leg (pyproject.toml) and `.github/workflows/validate.yml` "
            "installs it with `pip install -e \".[test]\"` — run that first")
    return Path(list(spec.submodule_search_locations)[0])


def _back_import_census() -> dict[str, list[int]]:
    base = _pinned_opendox_root()
    observed: dict[str, list[int]] = {}
    for path in _modules(base):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"),
                         filename=str(path))
        rel = f"opendox/{path.relative_to(base).as_posix()}"
        for _node, root, at_import_time in _census(tree):
            if root != "openxdox":
                continue
            slot = observed.setdefault(rel, [0, 0])
            slot[0 if at_import_time else 1] += 1
    return observed


def test_the_pinned_opendox_does_not_import_openxdox_back() -> None:
    """The inversion, ratcheted. Fails on a rise AND on an unrecorded fall."""
    observed = _back_import_census()
    stray = sorted(set(observed) - set(OPENDOX_BACK_IMPORTS))
    assert stray == [], (
        f"the pinned openDox imports `openxdox` from module(s) the census "
        f"does not name: {stray}. openXdox is pinned BY openDox's consumer, "
        "never the reverse (design.md:243, RULED OQ-2) — a NEW back-import is "
        "a regression of the very thing § 2.4's extension points exist to "
        "remove, and it must not be added to the table to make this pass")

    counts = Counter()
    for rel, (at_import, deferred) in observed.items():
        counts["import-time"] += at_import
        counts["deferred"] += deferred

    for label, seen, baseline in (
            ("import-time", counts["import-time"],
             OPENDOX_BACK_IMPORTS_AT_IMPORT_TIME),
            ("deferred", counts["deferred"], OPENDOX_BACK_IMPORTS_DEFERRED)):
        assert seen <= baseline, (
            f"{label} openDox→openXdox back-imports ROSE from {baseline} to "
            f"{seen}. The direction may only be removed, never added to")
        assert seen == baseline, (
            f"{label} openDox→openXdox back-imports FELL from {baseline} to "
            f"{seen} — good, and the census in this file is now untrue. Lower "
            f"OPENDOX_BACK_IMPORTS{'_AT_IMPORT_TIME' if label == 'import-time' else '_DEFERRED'} "
            f"to {seen} (and the per-module table with it) in the same act, "
            "citing the BUILD-arc slice. When BOTH reach 0, delete the "
            "ratchet and assert the direction strictly")


def test_the_ratchet_retires_itself_when_the_inversion_is_gone() -> None:
    """A ratchet nobody retires becomes a lie. This is the reminder."""
    if (OPENDOX_BACK_IMPORTS_AT_IMPORT_TIME == 0
            and OPENDOX_BACK_IMPORTS_DEFERRED == 0):
        pytest.fail(
            "the openDox→openXdox inversion is recorded as fully removed. "
            "Replace the ratchet above with a strict assertion that the "
            "census is empty, delete this test, and tick "
            "split-opendox-two-layer-product § 4.1's direction clause")

