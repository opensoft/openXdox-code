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


def _declared_runtime_dependency_import_names() -> frozenset[str]:
    """Top-level import name of every `[project] dependencies` entry.

    Two steps, not one hand-maintained table. First, read the DECLARED
    distribution names back out of `pyproject.toml` with `tomllib` (stdlib at
    the interpreter this leg pins, `>=3.12`) — a PEP 508 requirement's
    distinguishing name is everything before its first version/marker/URL
    separator. Second, resolve each distribution to the import root(s) it
    actually installs via `importlib.metadata.packages_distributions()` —
    the same RECORD/top-level metadata `pip` itself relies on — rather than a
    hand-written `{"pyyaml": "yaml"}`-shaped map: a review finding on this
    same PR (Sourcery) noted that a fixed map silently mis-reports the next
    dependency whose distribution and import names differ (`scikit-learn` ->
    `sklearn`, say) as undeclared. Reading the metadata instead means no
    second table to keep in step with `pyproject.toml` as dependencies change.
    """
    import re
    import tomllib
    from importlib.metadata import packages_distributions

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared_distributions = {
        re.split(r"[ @\[<>=!~;]", requirement, maxsplit=1)[0].strip().lower()
        for requirement in data["project"]["dependencies"]
    }
    return frozenset(
        import_name
        for import_name, dist_names in packages_distributions().items()
        if any(dist.lower() in declared_distributions for dist in dist_names)
    )


#: Cross-package roots permitted for a DEFERRED (function-body-only) reach,
#: because the name is a declared runtime dependency — DERIVED from
#: `pyproject.toml` rather than hand-listed, so this set can only ever say
#: "declared", never merely "allowlisted". It overlaps `IMPORT_TIME_ALLOWED`
#: on purpose (`opendox` and `yaml` are declared AND reached at import time;
#: a name does not stop being a declared dependency because it is also
#: reached early) — the union of the two below is what actually gates a
#: deferred reach. `jsonschema` is the one name declared but never reached at
#: import time: one reach, `gate_console.py:563`'s
#: `_validate_contract_document`, exercised only when a caller asks to
#: validate a contract document. It was the BUILD-arc slice 3 finding
#: recorded on opensoft/openxFactory#656 comment 5627156620, correction (c)
#: — undeclared because the derivation walk `pyproject.toml` documents covers
#: module bodies and module-level `if`/`try`/`with` only, never a function
#: body, the same gap this set closes for the CHECK: declaring the name
#: (this same PR) is what makes it appear here, not a second hand-typed copy
#: of it.
DEFERRED_ALLOWED = _declared_runtime_dependency_import_names()

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
    DOES run when the module is imported — and into CLASS bodies, which also
    run on import. Only a FUNCTION body defers. A class nested inside a
    function stays deferred because the flag is already false by the time the
    walk reaches it. A column offset would get all of this wrong:
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
                node, (ast.FunctionDef, ast.AsyncFunctionDef))
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
    """The same list, one name wider: reaches from inside a function body,
    where the name need only be a DECLARED dependency — never hand-listed a
    second time — to count as known."""
    allowed = IMPORT_TIME_ALLOWED | DEFERRED_ALLOWED
    offenders = sorted({
        f"{rel}:{line} -> {root}" for rel, line, root, at_import in _src_census()
        if not at_import and root not in OWN and root not in allowed
        and root not in _STDLIB
    })
    assert offenders == [], (
        "deferred cross-package reach(es) out of src/ that this leg does not "
        f"declare: {offenders}. A name reached only from inside a function "
        "body still needs a declared runtime dependency (pyproject.toml) or "
        "a place on IMPORT_TIME_ALLOWED above — add it there, it is not "
        "enough for the reach to merely defer")


#: Modules of this leg whose whole purpose is to CONSUME openDox — the § 2.4
#: contribution surfaces, which contribute routes and subcommands to openDox's
#: extension points rather than forking the server. If one of these stops
#: importing `opendox`, the leg has forked its upstream.
MUST_CONSUME_OPENDOX = (
    "src/openxdox/serve_gate.py",
    "src/openxdox/serve_projection.py",
    "src/openxdox/cli_gate.py",
)


def test_the_lawful_direction_is_actually_exercised() -> None:
    """openXdox imports openDox — the direction the pin chain declares.

    A guard that only forbids things passes trivially on an empty tree, so the
    edge the chain REQUIRES is asserted too. Asserted as an INVARIANT and not
    as a census: a consolidation of repeated imports is lawful and must not
    fail here, but a contribution surface that stops consuming openDox
    altogether is a fork (§ 4.3, "No fork of the server") and must.
    """
    consumers = {rel for rel, _line, root, _ in _src_census() if root == "opendox"}
    assert consumers, (
        "no module under src/ imports `opendox`: openXdox is supposed to "
        "CONSUME openDox (RULED OQ-2). Check that the leg has not vendored or "
        "forked its upstream")
    missing = [rel for rel in MUST_CONSUME_OPENDOX if rel not in consumers]
    assert missing == [], (
        f"contribution surface(s) that no longer import `opendox`: {missing}. "
        "These modules contribute to openDox's § 2.4 extension points; one "
        "that stops consuming openDox has forked it")


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

#: The openDox -> openXdox back-imports, MEASURED at the commit this leg pins.
#:
#: LOWERED TO ZERO AT IMPORT TIME BY BUILD SLICE 2b — `opensoft/openDox-code`
#: #10, which this file's pin now names (`pyproject.toml`). **0 import-time /
#: 19 deferred over five modules**, from 9 / 19 at the head of that slice and
#: from the 13 / 19 over six modules that the census RULED 5626260214 called
#: "the 13-line openDox->openXdox inversion" stood at.
#:
#: THE WHOLE OF THE INVERSION IS GONE, which is worth stating plainly because
#: this table has never been able to say it before: no module of the pinned
#: openDox names `openxdox` at import time. The 19 deferred reaches are NOT a
#: lesser version of the same defect and are not owed a slice. They resolve
#: inside verbs — the direction working, not the direction surviving
#: (`design.md`:243) — and § 4.3/§ 4.5 injection is what removes the calls
#: themselves, at THIS leg, on its own schedule.
#:
#: HOW SLICE 2b DID IT, in the two shapes slice 2 could not:
#:   - A DEFAULT ARGUMENT cannot be deferred by any stand-in, because it is
#:     evaluated where the `def` sits. openDox now OWNS those values
#:     (`opendox/defaults.py`): `DEFAULT_RECORDS_DIR` at `branch_session.py`'s
#:     nine `records_dir` sites, `DEFAULT_INDEX_NAME` and `PEEK_TTL_SECONDS` at
#:     `serve.py`'s two. Eleven sites, three values, and
#:     `test_the_opendox_owned_defaults_match_this_leg` below is the drift
#:     guard that holds the two spellings together.
#:   - A MIXIN BASE cannot be deferred either, because a class needs its bases
#:     before its first instance exists. `DashboardHandler`'s two consumer
#:     bases are now stand-in bases openDox owns, each forwarding one method per
#:     name to the same function object with the same `self`.
#:
#: A COUNT CORRECTED, since this file carried it too. The note below used to say
#: the reverted default-argument conversions were "(7 sites and 2)". It is NINE
#: and 2: slice 2 miscounted `branch_session.py`, openDox-code's own
#: `tests/test_consumer_reach.py` repeated it, and a review pass on #10 caught
#: it there. Corrected in both files in the same window.
#:
#: WHICH IS THIS CENSUS'S ONE BLIND SPOT, RECORDED RATHER THAN PAPERED OVER:
#: `_census` counts `ast.Import` / `ast.ImportFrom` nodes, and a default
#: argument, an annotation or a decorator that reaches the consumer is none of
#: those. A module can therefore reach (0, n) here and still fail to import.
#: openDox-code asserts the property directly — `tests/test_consumer_reach.py`
#: imports each converted module in a subprocess with `openxdox` blocked — and
#: that is the right home for it: this leg measures a repository it does not
#: write, and cannot import openDox's modules to find out. That file's
#: `NEUTRAL_MODULES` is the asserted half and now holds `branch_session`,
#: `workbench`, `serve_workbench` and `consumer_reach`.
#:
#: TWO MODULES STILL DO NOT IMPORT WITHOUT A CONSUMER, and NEITHER is blocked by
#: `openxdox` any more. `opendox.serve` and `opendox.cli` are blocked by
#: `ideation_dashboard` — openxFactory's PRE-CARVE package name, a
#: `stays_openxfactory_adapter` row (RULING DQ-1) present at neither carve
#: destination, so the carve's `import rewrites` class had nothing lawful to
#: rewrite it to. It is the same defect class § 4.1 fixed on this side, it is
#: censused at openDox-code, and it is owed a later act. It is invisible to THIS
#: table by construction: the table counts `openxdox` and nothing else.
#:
#: A RATCHET, not a target: the numbers may only FALL. When a BUILD-arc slice
#: lands, lower them here in the same act — the suite refuses a silent
#: improvement as well as a regression, so the number in the tree stays true.
OPENDOX_BACK_IMPORTS: dict[str, tuple[int, int]] = {
    # module                        (import-time, deferred)
    "opendox/branch_session.py":    (0, 7),
    "opendox/cli.py":               (0, 1),
    "opendox/serve.py":             (0, 2),
    "opendox/serve_project.py":     (0, 2),
    "opendox/serve_workbench.py":   (0, 7),
}
#: Derived from the table above, never typed twice — a second hand-kept copy
#: is exactly how a compensating fall-and-rise slips past a total.
OPENDOX_BACK_IMPORTS_AT_IMPORT_TIME = sum(v[0] for v in OPENDOX_BACK_IMPORTS.values())
OPENDOX_BACK_IMPORTS_DEFERRED = sum(v[1] for v in OPENDOX_BACK_IMPORTS.values())


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


#: The values openDox now OWNS, and where each one's CANONICAL spelling lives
#: at this leg. `opendox/defaults.py` restates the literal; this table is what
#: makes the restatement safe.
#:
#: WHY A RESTATEMENT NEEDED A GUARD AT ALL. A default argument is evaluated
#: where the `def` sits, so openDox could not defer these reaches behind a
#: stand-in the way it deferred the rest — it had to stop reaching and hold the
#: value itself. That is the right answer for values openDox owns, and it buys
#: the one failure mode a reach does not have: the two copies can DRIFT, and
#: nothing in either repository would notice, because neither module imports the
#: other any more. That is precisely what the direction fix removed.
#:
#: SO THE GUARD LIVES HERE, not at openDox-code, and the asymmetry is
#: deliberate: this leg pins openDox and can read both spellings, while openDox
#: pins nothing back and by construction cannot read this one (design.md:243,
#: RULED OQ-2). A drift guard at the neutral leg would be the back-import all
#: over again.
#:
#: READ BY AST, NOT BY IMPORT. `openxdox.gate_console` pulls in `doc_health`
#: and the rest of this leg's runtime, and a literal comparison should not need
#: any of it — nor should a drift in a CONSTANT be reportable only when every
#: unrelated dependency of its module happens to be installed.
#:
#: THE PAIRING IS NOT AUTHORED HERE. `opendox/defaults.py` publishes
#: `MIRRORED_AT_CONSUMER` — `(consumer module, attribute) -> the name THERE` —
#: for exactly this guard, in its own words: *"so the guard reads the pairing
#: from the side that owns the values rather than restating it a third time."*
#: The tests below read that mapping and compare THIS table against it first.
#: Restating the pairing without checking it is how the guard would end up
#: comparing the wrong pair and staying green: rename or re-home a value
#: upstream and a hand-kept inverse would go on pointing at the old module,
#: which is the failure mode the guard exists to prevent, one level up.
#:
#: It stays a RECORDED expectation rather than being derived silently, for the
#: reason the census above is recorded: a change in what openDox owns should
#: come to a reader of this file as a failure that names the change, not as a
#: table that quietly follows whatever the pin happens to publish.
OPENDOX_OWNED_DEFAULTS = {
    # opendox/defaults.py name       this leg's module,   this leg's name
    "DEFAULT_RECORDS_DIR":          ("gate_console",      "DEFAULT_RECORDS_DIR"),
    "DEFAULT_INDEX_NAME":           ("snapshot_registry", "DEFAULT_INDEX_NAME"),
    "PEEK_TTL_SECONDS":             ("snapshot_registry", "PEEK_TTL_SECONDS"),
}


def _module_level_literals(path: Path) -> dict[str, object]:
    """Every `NAME = <literal>` at a module's top level, without importing it."""
    found: dict[str, object] = {}
    for node in ast.iter_child_nodes(ast.parse(path.read_text(encoding="utf-8"))):
        targets = []
        if isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.value is not None:
            targets = [node.target]
            value = node.value
        else:
            continue
        for target in targets:
            try:
                found[target.id] = ast.literal_eval(value)
            except (ValueError, TypeError, SyntaxError):
                continue  # a derived value, not a literal — not this guard's business
    return found


def _opendox_owned() -> dict[str, object]:
    """`opendox/defaults.py`'s module-level literals, read out of the PINNED tree."""
    return _module_level_literals(_pinned_opendox_root() / "defaults.py")


def test_the_owned_defaults_table_matches_the_mapping_opendox_publishes() -> None:
    """The pairing is openDox's to publish; this file's copy must agree with it.

    `MIRRORED_AT_CONSUMER` exists at openDox-code for this guard and no other
    reader. Comparing against it is what stops the guard from holding the WRONG
    pair: a value re-homed from `gate_console` to some other module of this leg,
    or renamed, would leave a hand-kept inverse pointing at the old one and
    every literal comparison below still green.
    """
    published = _opendox_owned().get("MIRRORED_AT_CONSUMER")
    assert isinstance(published, dict) and published, (
        "`opendox/defaults.py` no longer publishes MIRRORED_AT_CONSUMER as a "
        "module-level literal. It is the pairing this guard reads; if it moved "
        "or became derived, this guard has to follow it in the same act")

    inverted = {owned: pair for pair, owned in published.items()}
    assert inverted == OPENDOX_OWNED_DEFAULTS, (
        f"the pinned openDox publishes a different pairing than this file "
        f"records: {inverted} vs {OPENDOX_OWNED_DEFAULTS}. openDox owns these "
        "values and names where each mirrors at THIS leg, so the mapping there "
        "is the authority — update this table in the same act, and check that "
        "the module it now names is the one this leg actually publishes the "
        "value from")


@pytest.mark.parametrize("owned_name", sorted(OPENDOX_OWNED_DEFAULTS))
def test_the_opendox_owned_defaults_match_this_leg(owned_name: str) -> None:
    """openDox's restated literal still equals the value this leg publishes.

    BUILD slice 2b moved eleven default arguments off this leg's constants —
    `branch_session.py`'s nine `records_dir` sites and `serve.py`'s two in
    `build_server` — onto `opendox/defaults.py`, because a default argument
    cannot be deferred. If these two spellings ever disagree, a gate record
    would be written to one directory and looked for in another, or a snapshot
    peeked with one TTL and served with another, and every suite on both sides
    would stay green while it happened.
    """
    owned = _opendox_owned()
    published = owned.get("MIRRORED_AT_CONSUMER") or {}
    # The OPERATIVE pairing is the one openDox publishes, not this file's copy;
    # the copy is checked against it by the test above, which fails first and
    # says so. Falling back to the recorded table keeps THIS test's failure
    # about the literals when the mapping is what has gone missing.
    pairs = {owned_at: pair for pair, owned_at in published.items()}
    module_name, leg_name = pairs.get(owned_name,
                                      OPENDOX_OWNED_DEFAULTS[owned_name])
    assert owned_name in owned, (
        f"`opendox/defaults.py` no longer defines {owned_name!r} as a "
        f"module-level literal. It holds the value for openDox's default "
        f"arguments; if it moved, this guard has to follow it in the same act "
        f"or the two spellings are unwatched")

    here = _module_level_literals(SRC / "openxdox" / f"{module_name}.py")
    assert leg_name in here, (
        f"`openxdox/{module_name}.py` no longer defines {leg_name!r} as a "
        f"module-level literal — so the value openDox restates has moved at "
        f"THIS leg, and openDox cannot see that it has")

    assert owned[owned_name] == here[leg_name], (
        f"DRIFT: `opendox/defaults.py`'s {owned_name} is "
        f"{owned[owned_name]!r} and `openxdox/{module_name}.py`'s {leg_name} "
        f"is {here[leg_name]!r}. openDox restates this literal because a "
        f"default argument is evaluated at import time and cannot be deferred "
        f"behind a stand-in (BUILD slice 2b); the restatement is only safe "
        f"while this guard holds. Change both, in one act, or move the value "
        f"across the § 2.4 seam so there is only one copy")


def test_the_pinned_opendox_does_not_import_openxdox_back() -> None:
    """The inversion, ratcheted PER MODULE.

    The comparison is the whole table and not the two totals, because a fall
    in one module paired with a rise in another leaves both totals untouched
    and the landed census false.
    """
    observed = {rel: tuple(v) for rel, v in _back_import_census().items()}
    if observed == OPENDOX_BACK_IMPORTS:
        return

    stray = sorted(set(observed) - set(OPENDOX_BACK_IMPORTS))
    assert stray == [], (
        f"the pinned openDox imports `openxdox` from module(s) the census "
        f"does not name: {stray}. openXdox is pinned BY openDox's consumer, "
        "never the reverse (design.md:243, RULED OQ-2) — a NEW back-import is "
        "a regression of the very thing § 2.4's extension points exist to "
        "remove, and it must not be added to the table to make this pass")

    risen = sorted(
        f"{rel}: {OPENDOX_BACK_IMPORTS[rel]} -> {seen}"
        for rel, seen in observed.items()
        if seen[0] > OPENDOX_BACK_IMPORTS[rel][0]
        or seen[1] > OPENDOX_BACK_IMPORTS[rel][1])
    assert risen == [], (
        "openDox→openXdox back-imports ROSE, per module (import-time, "
        f"deferred): {risen}. The direction may only be removed, never added "
        "to — § 2.4's extension points exist to carry these contributions the "
        "other way round")

    fallen = sorted(
        f"{rel}: {OPENDOX_BACK_IMPORTS[rel]} -> {observed.get(rel, (0, 0))}"
        for rel in OPENDOX_BACK_IMPORTS
        if observed.get(rel, (0, 0)) != OPENDOX_BACK_IMPORTS[rel])
    pytest.fail(
        f"openDox→openXdox back-imports FELL, per module (import-time, "
        f"deferred): {fallen} — good, and the census in this file is now "
        "untrue. Update OPENDOX_BACK_IMPORTS to the observed values in the "
        "same act (the two totals derive from it), citing the BUILD-arc "
        "slice; drop a module from the table when it reaches (0, 0). When the "
        "table is empty, delete the ratchet and assert the direction strictly")


def test_the_ratchet_retires_itself_when_the_inversion_is_gone() -> None:
    """A ratchet nobody retires becomes a lie. This is the reminder."""
    if not OPENDOX_BACK_IMPORTS:
        pytest.fail(
            "the openDox→openXdox inversion is recorded as fully removed. "
            "Replace the ratchet above with a strict assertion that the "
            "census is empty, delete this test, and tick "
            "split-opendox-two-layer-product § 4.1's direction clause")



# --------------------------------------------------------------------------
# 4 — the seam's RUNTIME behaviour. The AST checks above prove the edge is
# gone from the tree; these prove the replacement actually works, so the
# inversion cannot regress through a broken seam while CI stays green.
# --------------------------------------------------------------------------

def _fresh_seam():
    """A `consumer_reach` module object with no resolution cached.

    Imported inside the test rather than at module scope: every other test
    here parses trees and must keep working if this package were ever
    unimportable, and importing the seam is itself part of what is asserted.
    """
    import importlib

    import openxdox.consumer_reach as seam
    return importlib.reload(seam)


def test_the_seam_imports_without_its_consumer_present() -> None:
    """`openxdox.consumer_reach` loads with nothing of openxFactory around.

    This is the property the fix exists for: the module-level edge is gone, so
    importing this package no longer requires its own consumer.
    """
    assert "ideation_dashboard" not in sys.modules
    seam = _fresh_seam()
    assert repr(seam.human_seen).endswith("(unresolved)>"), repr(seam.human_seen)


def test_first_attribute_access_refuses_and_names_the_layering() -> None:
    seam = _fresh_seam()
    with pytest.raises(seam.ConsumerReachUnavailable) as caught:
        _ = seam.human_seen.HumanSeenSubmission
    message = str(caught.value)
    assert "human_seen" in message
    assert "RULING F" in message and "openxFactory" in message, message
    assert "ideation_dashboard.human_seen" in message, message


def test_the_seam_resolves_the_consumer_and_caches_it(monkeypatch) -> None:
    """Given the consumer, the proxy forwards to the REAL module object."""
    import types

    package = types.ModuleType("ideation_dashboard")
    package.__path__ = []                                  # a package, not a module
    real = types.ModuleType("ideation_dashboard.human_seen")
    real.HumanSeenSubmission = object()
    real.calls = 0
    package.human_seen = real
    monkeypatch.setitem(sys.modules, "ideation_dashboard", package)
    monkeypatch.setitem(sys.modules, "ideation_dashboard.human_seen", real)

    seam = _fresh_seam()
    assert seam.human_seen.HumanSeenSubmission is real.HumanSeenSubmission
    assert seam.human_seen.resolve() is real, "the module object, not a copy"
    # Cached: dropping it from sys.modules does not un-resolve the proxy.
    monkeypatch.delitem(sys.modules, "ideation_dashboard.human_seen")
    assert seam.human_seen.resolve() is real
    assert repr(seam.human_seen).endswith("(resolved)>")


def test_a_broken_consumer_module_is_not_swallowed(monkeypatch) -> None:
    """A candidate that EXISTS and raises is re-raised, never skipped.

    Catching `ImportError` wholesale would fall through to the bare
    `human_seen` spelling — possibly an unrelated top-level module — or blame
    the layering for a bug inside openxFactory.
    """
    import importlib
    import types

    package = types.ModuleType("ideation_dashboard")
    package.__path__ = []
    monkeypatch.setitem(sys.modules, "ideation_dashboard", package)

    real_import_module = importlib.import_module

    def exploding(name, *args, **kwargs):
        if name == "ideation_dashboard.human_seen":
            raise ModuleNotFoundError("No module named 'yaml'", name="yaml")
        return real_import_module(name, *args, **kwargs)

    seam = _fresh_seam()
    monkeypatch.setattr(seam.importlib, "import_module", exploding)
    with pytest.raises(ModuleNotFoundError) as caught:
        _ = seam.human_seen.HumanSeenSubmission
    assert caught.value.name == "yaml", "the consumer's own failure, re-raised"


def test_cli_gate_binds_the_seam_and_not_the_consumer() -> None:
    """`cli_gate`'s public name still resolves, and it is now the proxy.

    Asserted over the source rather than by import, because `cli_gate` also
    reaches `doc_health` (§ 4.1's implementation surface) and so does not
    import in this environment — the very gap the BUILD arc owes.
    """
    text = (ROOT / "src/openxdox/cli_gate.py").read_text(encoding="utf-8")
    assert "from openxdox.consumer_reach import human_seen as human_seen_mod" in text
    assert "from ideation_dashboard import human_seen" not in text
    # The two call sites are untouched and still reach the same public name.
    assert "human_seen_mod.HumanSeenSubmission(" in text
    assert "human_seen_mod.SubmissionRefused" in text
