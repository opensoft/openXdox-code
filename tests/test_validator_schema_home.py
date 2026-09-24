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
demotion-receipt at openxFactory. A kind whose schema the resolved directory
does not carry is refused BY NAME (exit 2), never passed.

Each case copies the REAL validator script into a layout built in `tmp_path`
and runs it the documented way, as a subprocess, with `CONTRACTS_DIR` removed
from the inherited environment unless the case sets it. The spec leg carries a
STAND-IN snapshot schema: the real one lives in openXdox-spec, which this leg's
hermetic suite does not reach. What is proven is the RESOLUTION and that the
validator really runs its snapshot rules (a dangling edge is a finding, exit 1),
not the content of the real schema.
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


def _run(script: Path, *args: Path, cwd: Path,
         contracts_dir: Path | None = None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "CONTRACTS_DIR"}
    if contracts_dir is not None:
        env["CONTRACTS_DIR"] = str(contracts_dir)
    cwd.mkdir(parents=True, exist_ok=True)
    return subprocess.run([sys.executable, str(script), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd, env=env, timeout=120)


def test_with_contracts_dir_the_validator_runs_against_the_spec_legs_schemas(tmp_path):
    """(i) THE REGISTERED DEFECT. A lone code leg, given the spec leg's
    contracts through the declared channel, RUNS: a conforming snapshot
    validates (exit 0), from a clean cwd."""
    script = _script_in(tmp_path / "openXdox" / "code")
    contracts = _spec_contracts(tmp_path / "openXdox" / "spec")
    snap = _write(tmp_path / "out" / "s.yaml", _snapshot())
    proc = _run(script, snap, cwd=tmp_path / "elsewhere", contracts_dir=contracts)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "0 error(s)" in proc.stdout


def test_a_referentially_broken_snapshot_is_a_verdict_not_a_harness_error(tmp_path):
    """(i) It is a real run, not an early exit: the validator's own snapshot
    rule fires on a dangling cluster edge — a FINDING (exit 1), which is what
    `openxdox.snapshot` reads as not-conformant rather than unavailable."""
    script = _script_in(tmp_path / "code")
    contracts = _spec_contracts(tmp_path / "spec")
    broken = _snapshot(clusters=[{
        "id": "cl-x", "name": "X", "topics": ["x"],
        "document_edges": [{"document": "doc-missing", "matched_topics": ["x"]}]}])
    proc = _run(script, _write(tmp_path / "out" / "bad.yaml", broken), cwd=tmp_path,
                contracts_dir=contracts)
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
    assert "ideation-workbench.schema.yaml is not carried under" in proc.stderr
    assert str(contracts / "schemas") in proc.stderr
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
    """(i) No contracts of its own and no `CONTRACTS_DIR`: the run refuses as a
    harness error (exit 2), in both the default and the single-file mode, and
    the refusal says which variable would supply the contracts rather than only
    that a directory is missing."""
    script = _script_in(tmp_path / "openXdox-code")
    default = _run(script, cwd=tmp_path)
    assert default.returncode == 2, default.stdout + default.stderr
    assert "CONTRACTS_DIR is not set" in default.stderr
    single = _run(script, _write(tmp_path / "out" / "s.yaml", _snapshot()), cwd=tmp_path)
    assert single.returncode == 2, single.stdout + single.stderr
    assert "CONTRACTS_DIR is not set" in single.stderr


def test_a_declared_directory_without_schemas_is_refused_by_name(tmp_path):
    """(i) A `CONTRACTS_DIR` that carries no `schemas/` validates nothing; the
    refusal names the declared directory, not the leg's own absent one."""
    script = _script_in(tmp_path / "code")
    empty = tmp_path / "empty-contracts"
    empty.mkdir()
    proc = _run(script, _write(tmp_path / "out" / "s.yaml", _snapshot()), cwd=tmp_path,
                contracts_dir=empty)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert str(empty / "schemas") in proc.stderr
    assert f"CONTRACTS_DIR={empty}" in proc.stderr


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
    _spec_contracts(root / "spec")
    proc = _run(script, _write(tmp_path / "out" / "s.yaml", _snapshot()), cwd=root)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert str(root / "code" / "contracts" / "schemas") in proc.stderr
    assert str(root / "spec") not in proc.stderr


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
