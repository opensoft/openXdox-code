"""Where `scripts/validate-ideation-dashboard-contracts.py` finds its schemas
(split-opendox-two-layer-product § 8.9 residue (i)).

Registered at openxFactory `openspec/changes/archive/2026-09-22-split-opendox-
two-layer-product/tasks.md` § 8.9 (amendment #6, RULED Q-P3 (a),
`opensoft/openxFactory#656` comment 5728856581), verbatim:

  (i) "`openXdox-code`'s `SCHEMAS_DIR` resolves to an ABSENT directory
      (`ROOT / "contracts" / "schemas"`), so as carved the validator cannot run
      from anywhere"

THE CHANNEL IS DECLARED, NOT DISCOVERED. The assembly root's `AGENTS-shape.md`
(openRepoShape's, digest-pinned in opensoft/openXdox) says where a code leg's
tooling finds a contract it reads but does not own: "A contract the code READS
but does not OWN lives in the SPEC leg ... the code leg's tooling now takes
`CONTRACTS_DIR` from the environment ... rather than each script guessing at
`../`". So the validator reads its own tree's `contracts/` when the tree carries
one, otherwise the directory `CONTRACTS_DIR` names, and nothing else — never an
enclosing directory by position, which is the class § 8.9 residue (iii) names.

THE SCHEMAS ARE NOT ALL IN ONE PLACE. Since the carve the ten family schemas are
split three ways: snapshot, snapshot-index and gate-action at openXdox-spec
(this product's own spec leg); workbench, chat-turn and model-catalog at
openDox-spec; possibles-register, project-register, gate-intent and
demotion-receipt at openxFactory. A kind whose schema no channel supplies is
refused BY NAME (exit 2), never passed.

THE SCHEMAS' NEW HOME, SINCE PLAN 034 T061 (#1144 7.3 as T007's batch I amends
it, RULED R1Q14 (a) and R1Q27 (a)). The validator's own three kinds, the
openXdox-spec three, come from its INSTALLED distribution: the packaged copies
in `openxdox/contracts/schemas/`, each held to `copies.yaml`'s digest, found
through the import system wherever the running tree carries none of its own.
`CONTRACTS_DIR` supplies only the family's other seven, and never the three.
So the declared channel is exercised here with a kind of the seven, a STAND-IN
`gate-intent` schema, and the snapshot is checked against the real packaged
schema, since the three now travel with the install.

Each case copies the REAL validator script into a layout built in `tmp_path`
and runs it the documented way, as a subprocess, with `CONTRACTS_DIR` removed
from the inherited environment unless the case sets it. Where a case needs an
interpreter whose openxdox distribution carries no copies, it puts a DECOY
`openxdox/contracts/` package first on `PYTHONPATH`, which the import system
finds before the installed one.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

# The validator refuses to start without these (its own import guards, exit 2),
# so a runner that lacks them cannot measure resolution at all.
pytest.importorskip("yaml")
pytest.importorskip("jsonschema")
pytest.importorskip("referencing")
pytest.importorskip("rfc3339_validator")

import yaml  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts" / "validate-ideation-dashboard-contracts.py"

STAND_IN_GATE_INTENT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "gate-intent.schema.yaml",
    "schema_version": 1,
    "kind": "json-schema",
    "type": "object",
    "required": ["schema_version", "kind"],
    "properties": {"kind": {"const": "gate-intent"}},
}
GATE_INTENT = {"schema_version": 1, "kind": "gate-intent"}

STAND_IN_SNAPSHOT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "ideation-dashboard-snapshot.schema.yaml",
    "schema_version": 1,
    "kind": "json-schema",
    "type": "object",
    "required": ["schema_version", "kind", "repository"],
    "properties": {"kind": {"const": "ideation-dashboard-snapshot"}},
}


def _snapshot(**over) -> dict:
    doc = {
        "schema_version": 1, "kind": "ideation-dashboard-snapshot",
        "repository": "fixture-repo",
        "generation": {"source_revision": "0" * 40},
        "documents": [], "clusters": [], "possibles": [], "staged_topics": [],
        "changes": [], "keyword_index": [],
    }
    doc.update(over)
    return doc


def _write(path: Path, doc) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=True), encoding="utf-8")
    return path


def _script_in(root: Path) -> Path:
    """A copy of the real validator at `<root>/scripts/`. A COPY, not a link:
    the script derives its root from its own resolved `__file__`, and a link
    would resolve straight back to this checkout."""
    target = root / "scripts" / VALIDATOR.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(VALIDATOR, target)
    return target


def _spec_contracts(spec: Path, schema: dict = STAND_IN_SNAPSHOT_SCHEMA) -> Path:
    """A spec leg carrying the snapshot schema; returns its `contracts/`."""
    _write(spec / "contracts" / "schemas" / "ideation-dashboard-snapshot.schema.yaml", schema)
    return spec / "contracts"


def _declared(contracts: Path) -> Path:
    """A `CONTRACTS_DIR` carrying the stand-in `gate-intent` schema, a kind of
    the family's other seven; returns it."""
    _write(contracts / "schemas" / "gate-intent.schema.yaml", STAND_IN_GATE_INTENT_SCHEMA)
    return contracts


def _decoy_distribution(root: Path, *, copies_from: Path | None = None) -> Path:
    """A directory for `PYTHONPATH` whose `openxdox.contracts` the import system
    finds first. Empty, it carries no copies; `copies_from` fills it with a copy
    of a real `openxdox/contracts/` (record and schemas). Returns the directory."""
    package = root / "openxdox" / "contracts"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    if copies_from is not None:
        shutil.copy2(copies_from / "copies.yaml", package / "copies.yaml")
        shutil.copytree(copies_from / "schemas", package / "schemas", dirs_exist_ok=True)
    return root


PACKAGED = REPO_ROOT / "src" / "openxdox" / "contracts"


def _run(script: Path, *args: Path, cwd: Path,
         contracts_dir: Path | None = None,
         pythonpath: Path | None = None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("CONTRACTS_DIR", "PYTHONPATH")}
    if contracts_dir is not None:
        env["CONTRACTS_DIR"] = str(contracts_dir)
    if pythonpath is not None:
        env["PYTHONPATH"] = str(pythonpath)
    cwd.mkdir(parents=True, exist_ok=True)
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd, env=env, timeout=120)


def test_with_contracts_dir_the_validator_runs_against_the_declared_schemas(tmp_path):
    """(i) THE REGISTERED DEFECT. A lone code leg, given a contract it does not
    own through the declared channel, RUNS: a conforming instance of that kind
    validates (exit 0), from a clean cwd."""
    script = _script_in(tmp_path / "openXdox" / "code")
    contracts = _declared(tmp_path / "declared" / "contracts")
    intent = _write(tmp_path / "out" / "gi.yaml", GATE_INTENT)
    proc = _run(script, intent, cwd=tmp_path / "elsewhere", contracts_dir=contracts)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "0 error(s)" in proc.stdout


def test_its_own_three_come_from_the_installed_distribution_never_contracts_dir(tmp_path):
    """PLAN 034 T061 (#1144 7.3; R1Q27 (a)). The validator's own kinds are read
    from its installed distribution, and `CONTRACTS_DIR` never supplies them:
    here the declared directory's snapshot schema would REJECT the instance, so
    exit 0 proves the packaged copy was read. With no `CONTRACTS_DIR` at all the
    snapshot validates the same way, since the three need no channel."""
    script = _script_in(tmp_path / "code")
    stricter = dict(STAND_IN_SNAPSHOT_SCHEMA, required=["never_present"])
    declared = _spec_contracts(tmp_path / "spec", stricter)
    snap = _write(tmp_path / "out" / "s.yaml", _snapshot())
    for contracts in (declared, None):
        proc = _run(script, snap, cwd=tmp_path, contracts_dir=contracts)
        assert proc.returncode == 0, (contracts, proc.stdout + proc.stderr)
        assert "0 error(s)" in proc.stdout


def test_a_packaged_copy_that_differs_from_its_record_is_refused(tmp_path):
    """PRESENCE IS NOT IDENTITY. A distribution whose snapshot copy is not the
    spec leg's file (one byte appended) is refused by name before it is read,
    as a harness error (exit 2), never used and never passed."""
    decoy = _decoy_distribution(tmp_path / "decoy", copies_from=PACKAGED)
    copy = decoy / "openxdox" / "contracts" / "schemas" / "ideation-dashboard-snapshot.schema.yaml"
    copy.write_bytes(copy.read_bytes() + b"\n")
    script = _script_in(tmp_path / "code")
    proc = _run(script, _write(tmp_path / "out" / "s.yaml", _snapshot()), cwd=tmp_path,
                pythonpath=decoy)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "is not the spec leg's file" in proc.stderr
    assert "0 error(s)" not in proc.stdout


def test_the_packaged_validator_reads_the_copies_beside_it(tmp_path):
    """An INSTALL's validator is `openxdox/contracts/validate-...py`, and its own
    tree is that package, so it reads the copies beside it, digest-checked,
    and not whatever distribution the interpreter would find (a decoy with no
    copies stands first on `PYTHONPATH` here). A copy edited in place beside it
    is refused the same way."""
    site = tmp_path / "site"
    shutil.copytree(PACKAGED, site / "openxdox" / "contracts",
                    ignore=shutil.ignore_patterns("__pycache__"))
    script = site / "openxdox" / "contracts" / VALIDATOR.name
    decoy = _decoy_distribution(tmp_path / "decoy")
    snap = _write(tmp_path / "out" / "s.yaml", _snapshot())
    proc = _run(script, snap, cwd=tmp_path, pythonpath=decoy)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    edited = site / "openxdox" / "contracts" / "schemas" / "gate-action-record.schema.yaml"
    edited.write_bytes(edited.read_bytes().replace(b"gate-action-record", b"gate-action-recorD", 1))
    proc = _run(script, snap, cwd=tmp_path, pythonpath=decoy)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "is not the spec leg's file" in proc.stderr


def test_a_referentially_broken_snapshot_is_a_verdict_not_a_harness_error(tmp_path):
    """(i) It is a real run, not an early exit: the validator's own snapshot
    rule fires on a dangling cluster edge — a FINDING (exit 1), which is what
    `openxdox.snapshot` reads as not-conformant rather than unavailable. The
    snapshot schema is the packaged one (T061), with no channel set."""
    script = _script_in(tmp_path / "code")
    broken = _snapshot(clusters=[{
        "id": "cl-x", "name": "X", "topics": ["x"],
        "document_edges": [{"document": "doc-missing", "matched_topics": ["x"]}]}])
    proc = _run(script, _write(tmp_path / "out" / "bad.yaml", broken), cwd=tmp_path)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "snapshot-dangling-edge" in proc.stdout


def test_a_kind_the_declared_contracts_do_not_carry_is_refused_by_name(tmp_path):
    """(i) FAIL CLOSED, NAMED. The spec leg carries three of the ten; an instance
    of any other kind has not been validated, and the harness says which schema
    is missing, where, and through which channel — exit 2, which
    `openxdox.snapshot` reads as unavailable, never as a pass and never as a
    verdict on the data."""
    script = _script_in(tmp_path / "code")
    contracts = _spec_contracts(tmp_path / "spec")
    workbench = _write(tmp_path / "out" / "wb.yaml",
                       {"schema_version": 1, "kind": "ideation-workbench"})
    proc = _run(script, workbench, cwd=tmp_path, contracts_dir=contracts)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "ideation-workbench.schema.yaml is not supplied" in proc.stderr
    assert f"not carried under {contracts / 'schemas'}" in proc.stderr
    assert f"CONTRACTS_DIR={contracts}" in proc.stderr


def _load(script: Path, monkeypatch, contracts_dir: Path | None):
    """Import a copied script as a module — its top level resolves the paths."""
    if contracts_dir is None:
        monkeypatch.delenv("CONTRACTS_DIR", raising=False)
    else:
        monkeypatch.setenv("CONTRACTS_DIR", str(contracts_dir))
    spec = importlib.util.spec_from_file_location(f"_vidc_{uuid.uuid4().hex}", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_declared_directory_sets_the_schemas_and_the_packaged_examples(tmp_path, monkeypatch):
    """(i) Both carved path constants follow the declared directory: the
    schemas under it, and the packaged examples beside it — where the spec leg
    carries them (`examples/ideation-dashboard/`)."""
    script = _script_in(tmp_path / "code")
    contracts = _spec_contracts(tmp_path / "spec")
    module = _load(script, monkeypatch, contracts)
    assert module.SCHEMAS_DIR == contracts.resolve() / "schemas"
    assert module.EXAMPLES_DIR == contracts.resolve().parent / "examples" / "ideation-dashboard"


def test_with_neither_the_refusal_names_the_channel(tmp_path):
    """(i) No contracts of its own and no `CONTRACTS_DIR`: the default mode,
    whose packaged examples live in a contracts tree, and a single file of a
    kind the validator does not own both refuse as a harness error (exit 2),
    and the refusal says which variable would supply the contracts rather than
    only that a directory is missing. A snapshot, one of its own three,
    validates from the installed distribution (plan 034 T061)."""
    script = _script_in(tmp_path / "openXdox-code")
    default = _run(script, cwd=tmp_path)
    assert default.returncode == 2, default.stdout + default.stderr
    assert "CONTRACTS_DIR is not set" in default.stderr
    single = _run(script, _write(tmp_path / "out" / "gi.yaml", GATE_INTENT), cwd=tmp_path)
    assert single.returncode == 2, single.stdout + single.stderr
    assert "CONTRACTS_DIR is not set" in single.stderr
    own = _run(script, _write(tmp_path / "out" / "s.yaml", _snapshot()), cwd=tmp_path)
    assert own.returncode == 0, own.stdout + own.stderr


def test_a_declared_directory_without_schemas_is_refused_by_name(tmp_path):
    """(i) A `CONTRACTS_DIR` that carries no `schemas/` validates nothing; the
    refusal names the declared directory, not the leg's own absent one."""
    script = _script_in(tmp_path / "code")
    empty = tmp_path / "empty-contracts"
    empty.mkdir()
    proc = _run(script, _write(tmp_path / "out" / "gi.yaml", GATE_INTENT), cwd=tmp_path,
                contracts_dir=empty)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert str(empty / "schemas") in proc.stderr
    assert f"CONTRACTS_DIR={empty}" in proc.stderr


def test_no_mode_passes_having_loaded_no_schema(tmp_path):
    """(i) FAIL CLOSED BEFORE ANY MODE RUNS (Copilot review of
    openXdox-code#28, round 2).

    Once `build_registry` skipped each schema the resolved directory does not
    carry, a directory sweep that met no recognized instance could exit 0
    having loaded no schema at all. It did so on an empty directory, and on a
    directory holding only unrecognized YAML, whether nothing was resolved or
    the declared `schemas/` carried none of the ten. `run_path` never reached a
    kind to refuse.

    Every mode is now a harness error, exit 2, naming the directory and the
    channel. It covers four modes: both sweeps, a register transition, and the
    default self-test. It covers two ways the ten can be missing: no contracts
    resolved at all, and a `schemas/` of unrelated files. Since plan 034 T061 an
    installed distribution supplies the validator's own three wherever it is
    importable, so "nothing loaded" also needs an interpreter whose openxdox
    carries no copies: a decoy stands first on `PYTHONPATH` here."""
    script = _script_in(tmp_path / "code")
    decoy = _decoy_distribution(tmp_path / "decoy")
    empty = tmp_path / "sweep-empty"
    empty.mkdir()
    unrecognized = _write(tmp_path / "sweep-unrecognized" / "notes.yaml",
                          {"schema_version": 1, "kind": "something-else"}).parent
    register = _write(tmp_path / "register.yaml", {"possibles_register": []})
    unrelated = tmp_path / "unrelated" / "contracts"
    _write(unrelated / "schemas" / "unrelated.schema.yaml", {"type": "object"})
    for contracts, schemas, channel in (
            (None, tmp_path / "code" / "contracts" / "schemas", "CONTRACTS_DIR is not set"),
            (unrelated, unrelated.resolve() / "schemas", f"CONTRACTS_DIR={unrelated}")):
        for args in ((empty,), (unrecognized,), ("--transition", register, register), ()):
            proc = _run(script, *args, cwd=tmp_path / "elsewhere", contracts_dir=contracts,
                        pythonpath=decoy)
            assert proc.returncode == 2, (contracts, args, proc.stdout + proc.stderr)
            assert str(schemas) in proc.stderr, (contracts, args, proc.stderr)
            assert channel in proc.stderr, (contracts, args, proc.stderr)
            assert "0 error(s)" not in proc.stdout, (contracts, args, proc.stdout)


def test_an_enclosing_assembly_root_is_never_read_by_position(tmp_path):
    """NO `../`. The code leg mounted in a full assembly root — lockstep pins
    naming it, and a spec leg beside it carrying the schema — but WITHOUT
    `CONTRACTS_DIR`: the validator does not go looking above its own root, so
    it refuses on the leg's own absent directory and never names the spec
    leg's. A guard that holds on both sides of the fix."""
    root = tmp_path / "openXdox"
    for role, repo, leg in (("code", "openXdox-code", "code"), ("spec", "openXdox-spec", "spec")):
        _write(root / "contracts" / f"{role}-pin.yaml", {
            "schema_version": 1, "kind": "pinned_contract_manifest", "leg_role": role,
            "source_repository": f"opensoft/{repo}", "submodule_path": leg})
    script = _script_in(root / "code")
    _declared(root / "spec" / "contracts")
    _spec_contracts(root / "spec", dict(STAND_IN_SNAPSHOT_SCHEMA, required=["never_present"]))
    proc = _run(script, _write(tmp_path / "out" / "gi.yaml", GATE_INTENT), cwd=root)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert str(root / "code" / "contracts" / "schemas") in proc.stderr
    assert str(root / "spec") not in proc.stderr
    # and the spec leg's stricter snapshot schema is not read either: the
    # packaged copy is, so the snapshot validates (plan 034 T061)
    own = _run(script, _write(tmp_path / "out" / "s.yaml", _snapshot()), cwd=root)
    assert own.returncode == 0, own.stdout + own.stderr


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="no symlinks on this platform")
def test_an_own_contracts_link_out_of_the_tree_is_refused(tmp_path):
    """NO `../` BY LINK EITHER (Copilot review, openXdox-code#28). A code leg
    whose `contracts/` is a LINK to the spec leg beside it would read that leg
    by position under this tree's own name. The run refuses, naming the link,
    with or without `CONTRACTS_DIR`, rather than reading it."""
    script = _script_in(tmp_path / "code")
    spec_contracts = _spec_contracts(tmp_path / "spec")
    try:
        (tmp_path / "code" / "contracts").symlink_to(spec_contracts, target_is_directory=True)
    except OSError as exc:              # e.g. unprivileged Windows
        pytest.skip(f"cannot create a symlink here: {exc}")
    snap = _write(tmp_path / "out" / "s.yaml", _snapshot())
    for declared in (None, spec_contracts):
        proc = _run(script, snap, cwd=tmp_path, contracts_dir=declared)
        assert proc.returncode == 2, (declared, proc.stdout + proc.stderr)
        assert "outside this tree, so it is not read" in proc.stderr, proc.stderr
        assert "0 error(s)" not in proc.stdout, proc.stdout


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="no symlinks on this platform")
def test_an_escaping_own_link_is_refused_whatever_it_reaches(tmp_path):
    """NO `../` BY LINK, EVEN WHEN THE LINK LEADS NOWHERE USEFUL (Copilot review,
    openXdox-code#28, round 3).

    The escaping-link check used to run only when `contracts/schemas/` was a
    directory. So a link that dangled, or that reached a directory with no
    `schemas/`, was never examined. With a valid `CONTRACTS_DIR` the run then
    validated against the declared directory (exit 0) and left the escaping
    link silently in place.

    Each of the three shapes is now refused before any directory is chosen,
    with or without `CONTRACTS_DIR`:
      * `contracts/` a dangling link out of the tree;
      * `contracts/` a link to an outside directory that has no `schemas/`;
      * a real `contracts/` whose `schemas/` is a dangling link out of it."""
    spec_contracts = _spec_contracts(tmp_path / "spec")
    snap = _write(tmp_path / "out" / "s.yaml", _snapshot())
    (tmp_path / "bare-contracts").mkdir()
    shapes = {
        "dangling": ("contracts", tmp_path / "gone"),
        "no-schemas": ("contracts", tmp_path / "bare-contracts"),
        "schemas-dangling": ("contracts/schemas", tmp_path / "gone-schemas"),
    }
    for name, (link, target) in shapes.items():
        script = _script_in(tmp_path / name)
        (tmp_path / name / link).parent.mkdir(parents=True, exist_ok=True)
        try:
            (tmp_path / name / link).symlink_to(target, target_is_directory=True)
        except OSError as exc:          # e.g. unprivileged Windows
            pytest.skip(f"cannot create a symlink here: {exc}")
        for declared in (spec_contracts, None):
            proc = _run(script, snap, cwd=tmp_path, contracts_dir=declared)
            assert proc.returncode == 2, (name, declared, proc.stdout + proc.stderr)
            assert "outside this tree, so it is not read" in proc.stderr, (name, proc.stderr)
            assert "0 error(s)" not in proc.stdout, (name, proc.stdout)


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="no symlinks on this platform")
def test_a_real_schemas_directory_of_linked_files_is_still_its_own_tree(tmp_path):
    """The confinement is on the DIRECTORY, not on each schema file.
    openxFactory's `doxbench_contracts._composed_validator` builds a REAL
    `contracts/schemas/` whose entries are links to the pinned files, and that
    farm keeps validating (exit 0) with no `CONTRACTS_DIR` at all."""
    farm = tmp_path / "farm"
    script = _script_in(farm)
    pinned = (_spec_contracts(tmp_path / "pinned") / "schemas"
              / "ideation-dashboard-snapshot.schema.yaml")
    (farm / "contracts" / "schemas").mkdir(parents=True)
    try:
        (farm / "contracts" / "schemas" / pinned.name).symlink_to(pinned)
    except OSError as exc:              # e.g. unprivileged Windows
        pytest.skip(f"cannot create a symlink here: {exc}")
    proc = _run(script, _write(tmp_path / "out" / "s.yaml", _snapshot()), cwd=tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "0 error(s)" in proc.stdout


def _family_names() -> list[str]:
    """The validator's own `SCHEMA_FILENAMES`, read from the script rather than
    restated here."""
    spec = importlib.util.spec_from_file_location("_vidc_family", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.SCHEMA_FILENAMES)


def test_its_own_tree_still_wins_so_a_composed_family_keeps_working(tmp_path):
    """A tree that carries the WHOLE family under `contracts/schemas/` beside its
    copy of the script — the pre-shed layout, and openxFactory's composed
    validator (`doxbench_contracts._composed_validator`) — is read first, even
    with `CONTRACTS_DIR` set: here the declared directory's snapshot schema
    would REJECT the instance, so exit 0 proves the tree's own was used. A
    guard that holds on both sides of the fix."""
    farm = tmp_path / "farm"
    script = _script_in(farm)
    for name in _family_names():
        doc = (STAND_IN_SNAPSHOT_SCHEMA
               if name == "ideation-dashboard-snapshot.schema.yaml"
               else {"$schema": "https://json-schema.org/draft/2020-12/schema",
                     "$id": name, "$defs": {"possibles_register": {"type": "array"}}})
        _write(farm / "contracts" / "schemas" / name, doc)
    stricter = dict(STAND_IN_SNAPSHOT_SCHEMA, required=["never_present"])
    elsewhere = _spec_contracts(tmp_path / "spec", stricter)
    proc = _run(script, _write(tmp_path / "out" / "s.yaml", _snapshot()), cwd=tmp_path,
                contracts_dir=elsewhere)
    assert proc.returncode == 0, proc.stdout + proc.stderr
