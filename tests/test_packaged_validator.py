"""THE PACKAGED VALIDATOR AND ITS THREE COPIES (plan 034 T061; #1144 7.3, RULED
R1Q14 (a), as T007's batch I amends it on R1Q27 (a), `opensoft/openxFactory#656`
comments 5850003126 and 5851950767).

An install ships no `scripts/`, so it carries its validator, and the three
schemas that validator owns, as package data (`openxdox.contracts`). These
tests hold each shipped piece to what it claims to be:

* THE VALIDATOR. The packaged copy is byte for byte the repository's
  `scripts/validate-ideation-dashboard-contracts.py`, which a source checkout
  runs and openxFactory's lanes read at that path. One file, two places; they
  cannot drift apart unseen.
* THE COPIES. Each copy's sha256 is the one `copies.yaml` records, and the
  record names the spec-leg commit the openXdox root pins (f088b097). The
  record is refused, before any copy is read, for each way it can be wrong.
* THE PACKAGE-DATA LINE. `pyproject.toml`'s `"openxdox.contracts"` patterns
  match every data file in the package and nothing else, so a wheel ships the
  record, the three copies and the validator, and `__init__.py` alone is not
  what an install gets.

The fresh-venv, non-editable run of the same claims is #1144's F7.1, which
the pull request's evidence carries."""
from __future__ import annotations

import hashlib
import shutil
import tomllib
from pathlib import Path

import pytest
import yaml

from openxdox import contracts

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "src" / "openxdox" / "contracts"
SCRIPT = REPO_ROOT / "scripts" / contracts.VALIDATOR_NAME

#: The spec-leg commit the openXdox root pins (opensoft/openXdox `main`
#: 57e2b8f2: its `spec` gitlink and `contracts/spec-pin.yaml`).
ROOT_SPEC_PIN = "f088b09732e236279898b53ab9fb0f5ebc89509a"


# --------------------------- the validator ---------------------------

def test_the_packaged_validator_is_the_scripts_validator_byte_for_byte():
    packaged = PACKAGE / contracts.VALIDATOR_NAME
    assert packaged.is_file(), f"{packaged} is not shipped"
    assert packaged.read_bytes() == SCRIPT.read_bytes(), (
        f"{packaged} differs from {SCRIPT}: copy the script again, in the same commit")


def test_the_source_tree_answers_the_package_it_imports():
    """In this checkout `openxdox.contracts` is the source package itself, so
    what the tests below read is what the wheel is built from."""
    assert contracts.package_dir().resolve() == PACKAGE.resolve()
    assert contracts.validator_path() == PACKAGE / contracts.VALIDATOR_NAME


# ----------------------------- the copies -----------------------------

def test_every_copy_is_the_digest_its_record_gives_at_the_root_pin():
    record = contracts.record()
    assert record.spec_leg == "opensoft/openXdox-spec"
    assert record.commit == ROOT_SPEC_PIN
    assert set(record.ids) == contracts.COPY_IDS
    for copy in record.copies:
        on_disk = PACKAGE / "schemas" / copy.filename
        assert hashlib.sha256(on_disk.read_bytes()).hexdigest() == copy.sha256, copy.id
        assert contracts.verified_bytes(copy.id) == on_disk.read_bytes()
        assert contracts.verified_path(copy.id) == on_disk


def test_the_copies_are_the_validators_own_three_kinds():
    """The record's three are the validator's `OWN_KIND_SCHEMAS`, and each copy
    declares the kind its id names, so no fourth kind rides in as a copy."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("vidc_packaged_copies", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    record = contracts.record()
    assert {copy.filename for copy in record.copies} == module.OWN_KIND_SCHEMAS
    for copy in record.copies:
        schema = yaml.safe_load(contracts.verified_bytes(copy.id))
        assert schema["properties"]["kind"]["const"] == copy.id


@pytest.fixture
def staged(tmp_path, monkeypatch):
    """A copy of the package's data files, which `openxdox.contracts` reads in
    place of its own, so a test can break one piece at a time."""
    staged = tmp_path / "contracts"
    shutil.copytree(PACKAGE, staged, ignore=shutil.ignore_patterns("__pycache__", "*.py"))
    monkeypatch.setattr(contracts, "package_dir", lambda: staged)
    return staged


def _edit_record(staged: Path, change) -> None:
    path = staged / contracts.RECORD_NAME
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_the_staged_package_reads_as_the_real_one(staged):
    assert contracts.record() == contracts.Record(
        "opensoft/openXdox-spec", ROOT_SPEC_PIN, contracts.record().copies)
    for copy_id in contracts.COPY_IDS:
        assert contracts.verified_path(copy_id).parent == staged / "schemas"


def _drop(key):
    return lambda data: data.pop(key)


def _set(key, value):
    return lambda data: data.__setitem__(key, value)


def _copy_field(index, key, value):
    return lambda data: data["copies"][index].__setitem__(key, value)


RECORD_REFUSALS = {
    "a missing key": (_drop("commit"), "its keys are"),
    "an unknown key": (_set("extra", 1), "its keys are"),
    "a boolean schema_version": (_set("schema_version", True), "schema_version is True"),
    "a string schema_version": (_set("schema_version", "1"), "schema_version is '1'"),
    "another kind": (_set("kind", "contract-manifest"), "kind is 'contract-manifest'"),
    "another spec leg": (_set("spec_leg", "opensoft/openDox-spec"), "spec_leg is"),
    "a short commit": (_set("commit", ROOT_SPEC_PIN[:8]), "not a full 40-hex commit id"),
    "no copies": (_set("copies", []), "copies is not a non-empty list"),
    "a copy with an extra field": (_copy_field(0, "note", "x"), "copies[0] is not a mapping"),
    "an uppercase id": (_copy_field(0, "id", "Gate-Action-Record"), "copies[0].id is"),
    "a path that is not the id's": (
        _copy_field(0, "path", "contracts/schemas/other.schema.yaml"), "copies[0].path is"),
    "an empty digest": (_copy_field(1, "sha256", ""), "copies[1].sha256 is ''"),
    "a short digest": (_copy_field(1, "sha256", "ab" * 16), "not a 64-hex digest"),
    "a repeated id": (
        lambda data: data["copies"].__setitem__(2, dict(data["copies"][1])),
        "an id is given twice"),
    "a fourth kind in place of one of the three": (
        lambda data: data["copies"].__setitem__(2, {
            "id": "gate-intent", "path": "contracts/schemas/gate-intent.schema.yaml",
            "sha256": "0" * 64}),
        "not the consumer's three"),
}


@pytest.mark.parametrize("case", sorted(RECORD_REFUSALS))
def test_a_record_that_cannot_be_trusted_is_refused_before_any_copy_is_read(staged, case):
    change, needle = RECORD_REFUSALS[case]
    _edit_record(staged, change)
    with pytest.raises(contracts.CopyRefused) as refused:
        contracts.record()
    assert needle in str(refused.value), str(refused.value)
    with pytest.raises(contracts.CopyRefused):
        contracts.verified_bytes("ideation-dashboard-snapshot")


def test_a_record_that_is_not_a_mapping_is_refused(staged):
    (staged / contracts.RECORD_NAME).write_text("- a list\n", encoding="utf-8")
    with pytest.raises(contracts.CopyRefused, match="it is a list, not a mapping"):
        contracts.record()


def test_an_absent_record_is_refused_by_name(staged):
    (staged / contracts.RECORD_NAME).unlink()
    with pytest.raises(contracts.CopyRefused, match="has no copies.yaml"):
        contracts.record()


def test_a_copy_edited_in_place_is_refused_not_read(staged):
    copy = staged / "schemas" / "ideation-dashboard-snapshot.schema.yaml"
    copy.write_bytes(copy.read_bytes() + b"\n")
    with pytest.raises(contracts.CopyRefused, match="is not the spec leg's file"):
        contracts.verified_bytes("ideation-dashboard-snapshot")
    with pytest.raises(contracts.CopyRefused, match="is not the spec leg's file"):
        contracts.verified_path("ideation-dashboard-snapshot")
    # the other two are untouched, and still read
    assert contracts.verified_path("gate-action-record").is_file()


def test_an_absent_copy_is_refused_by_name(staged):
    (staged / "schemas" / "gate-action-record.schema.yaml").unlink()
    with pytest.raises(contracts.CopyRefused, match="has no schemas/gate-action-record"):
        contracts.verified_bytes("gate-action-record")


def test_a_copy_the_record_does_not_name_is_refused(staged):
    with pytest.raises(contracts.CopyRefused, match="is not one of the packaged copies"):
        contracts.verified_path("gate-intent")


# ------------------------ the package-data line ------------------------

def test_the_package_data_line_ships_every_data_file_and_nothing_else():
    """The patterns are held to the files they ship: each one matches at least
    one file, and together they match every file in the package but its module
    (`__init__.py`) and bytecode, so a file added beside them is either declared
    or refused here."""
    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        declared = tomllib.load(fh)["tool"]["setuptools"]["package-data"]["openxdox.contracts"]
    assert declared == ["copies.yaml", "schemas/*.schema.yaml", contracts.VALIDATOR_NAME]
    shipped = set()
    for pattern in declared:
        matched = {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.glob(pattern) if p.is_file()}
        assert matched, f"{pattern!r} ships nothing"
        shipped |= matched
    present = {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob("*")
               if p.is_file() and "__pycache__" not in p.parts}
    assert present - shipped == {"__init__.py"}, present - shipped
    assert shipped == {contracts.RECORD_NAME, contracts.VALIDATOR_NAME} | {
        f"schemas/{copy.filename}" for copy in contracts.record().copies}

