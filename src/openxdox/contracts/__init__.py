"""THE CONSUMER VALIDATOR, AND THE PACKAGED COPIES OF ITS OWN THREE SCHEMAS.

WHY THIS PACKAGE EXISTS. Plan 034's T061 realizes #1144's 7.3 (RULED R1Q14 (a),
`opensoft/openxFactory#656` comment `5850003126`): *"openXdox's validator and its
three schemas (7.1's openXdox-spec three) are located through the INSTALLED
openXdox distribution, and no parent walk remains."* T007's batch I amends it
on R1Q27 (a) (comment `5851950767`): the validator validates its own three kinds
from its installed distribution, wherever it runs, and the family's other kinds
only where the tree it runs from supplies their schemas.

So an install carries what the validator needs to validate its own kinds, and
it carries it as PACKAGE DATA (`pyproject.toml`'s `[tool.setuptools.package-data]`):

* `validate-ideation-dashboard-contracts.py`: the validator. It is byte for
  byte the repository's `scripts/validate-ideation-dashboard-contracts.py`,
  which a source checkout runs, and which openxFactory's lanes and farm read
  at that path. A test holds the two equal.
* `schemas/`: the three copies. Each one is byte for byte the spec leg's file
  of the same name, `contracts/schemas/<id>.schema.yaml` in
  opensoft/openXdox-spec.
* `copies.yaml`: the record. It names the spec-leg commit the copies were taken
  at, and each copy's id, spec-leg path and sha256.

WHERE EACH COPY IS FOUND. The packaged validator's own tree is this package, so
its `contracts/schemas/` is these copies. A source checkout's
`scripts/validate-ideation-dashboard-contracts.py` has no `contracts/` of its
own, so it finds the copies here through the import system
(`importlib.util.find_spec("openxdox.contracts")`), the distribution the running
interpreter has installed, and never by position.

PRESENCE IS NOT IDENTITY. A copy is read only through `verified_bytes()` or
`verified_path()`. Each recomputes the copy's sha256 and compares it with the
record BEFORE the copy is used, and refuses, with `CopyRefused`, a copy that
differs from its digest, a copy that is absent, and a copy whose digest the
record leaves empty (`neutral-product-pin`'s rule for a vendored contract, as
openDox's `opendox.contracts` applies it). The validator script makes the same
check itself, since it must run where this package cannot be imported.

CONSUMED, NOT OWNED. openXdox-spec owns these three schemas (R1Q12 (a)). A copy
is changed in the spec leg and then copied here again, never edited here. The
copies, the record, and the `commit` it names move together, in one commit.

IMPORT WEIGHT. The standard library, and PyYAML (a runtime dependency) when the
record is read. Importing this package reads no file.

A CREATED FILE: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path, PurePosixPath

__all__ = [
    "COPY_IDS",
    "COPY_KIND",
    "CopyRefused",
    "PackagedCopy",
    "Record",
    "RECORD_NAME",
    "SPEC_LEG",
    "VALIDATOR_NAME",
    "package_dir",
    "record",
    "validator_path",
    "verified_bytes",
    "verified_path",
]

RECORD_NAME = "copies.yaml"
COPY_KIND = "packaged-contract-copies"
SPEC_LEG = "opensoft/openXdox-spec"
SCHEMA_DIR = "schemas"
VALIDATOR_NAME = "validate-ideation-dashboard-contracts.py"

#: The consumer validator's own three kinds, 7.1's openXdox-spec three.
COPY_IDS = frozenset({"gate-action-record", "ideation-dashboard-snapshot",
                      "ideation-dashboard-snapshot-index"})

_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class CopyRefused(RuntimeError):
    """A packaged copy, or the record that pins the copies, cannot be trusted.

    Raised before the copy is used. The message names the copy, what was
    found, and the one remedy: copy the spec leg's file again at the recorded
    commit, and record its digest in the same commit."""


@dataclass(frozen=True)
class PackagedCopy:
    """One copy, as the record declares it."""

    id: str
    path: str       # its path in the spec leg: contracts/schemas/<id>.schema.yaml
    sha256: str     # its digest at the recorded commit

    @property
    def filename(self) -> str:
        return PurePosixPath(self.path).name


@dataclass(frozen=True)
class Record:
    """`copies.yaml`, read and checked."""

    spec_leg: str
    commit: str
    copies: tuple[PackagedCopy, ...]

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(copy.id for copy in self.copies)

    def copy(self, copy_id: str) -> PackagedCopy:
        for copy in self.copies:
            if copy.id == copy_id:
                return copy
        raise CopyRefused(
            f"{copy_id!r} is not one of the packaged copies {list(self.ids)} "
            f"({RECORD_NAME} records no such copy, so none is read)")


def package_dir() -> Path:
    """This package's directory on disk: where the copies and the validator sit."""
    return Path(str(resources.files(__name__)))


def _refuse(detail: str) -> CopyRefused:
    return CopyRefused(
        f"{RECORD_NAME} cannot be trusted: {detail}. The record is written with "
        f"the copies it pins, in one commit, from {SPEC_LEG} at the commit the "
        "openXdox root pins")


def _read(name: str) -> bytes:
    """`name`'s bytes from the package. Every `OSError` is a refusal."""
    try:
        return (package_dir() / name).read_bytes()
    except (FileNotFoundError, IsADirectoryError, NotADirectoryError) as exc:
        raise CopyRefused(
            f"openxdox.contracts has no {name}: the package was built or "
            f"installed without it ({type(exc).__name__})") from exc
    except OSError as exc:
        raise CopyRefused(
            f"openxdox.contracts has {name}, and it cannot be read "
            f"({type(exc).__name__}: {exc.strerror or exc})") from exc


def _checked_copy(index: int, entry: object) -> PackagedCopy:
    where = f"copies[{index}]"
    if not isinstance(entry, dict) or set(entry) != {"id", "path", "sha256"}:
        raise _refuse(f"{where} is not a mapping of exactly id, path and sha256")
    copy_id, path, digest = entry["id"], entry["path"], entry["sha256"]
    if not isinstance(copy_id, str) or not _ID.fullmatch(copy_id):
        raise _refuse(f"{where}.id is {copy_id!r}, not a lowercase hyphenated id")
    if path != f"contracts/schemas/{copy_id}.schema.yaml":
        raise _refuse(f"{where}.path is {path!r}, not "
                      f"'contracts/schemas/{copy_id}.schema.yaml'")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        # An EMPTY digest lands here too: it is drift, never a pass.
        raise _refuse(f"{where}.sha256 is {digest!r}, not a 64-hex digest")
    return PackagedCopy(copy_id, path, digest)


def record() -> Record:
    """The record, read from the package and checked field by field.

    Refuses, with `CopyRefused`, a record it cannot hold every copy to: a
    missing or unknown field, a repeated id, an id that is not one of the
    three, a path that is not the id's schema path in the spec leg, and an
    empty or malformed digest."""
    import yaml

    try:
        data = yaml.safe_load(_read(RECORD_NAME))
    except (yaml.YAMLError, RecursionError, ValueError) as exc:
        raise _refuse(f"it is not YAML this module can read "
                      f"({exc.__class__.__name__})") from exc
    if not isinstance(data, dict):
        raise _refuse(f"it is a {type(data).__name__}, not a mapping")
    expected = {"schema_version", "kind", "spec_leg", "commit", "copies"}
    if set(data) != expected:
        raise _refuse(f"its keys are {sorted(data, key=repr)}, not {sorted(expected)}")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise _refuse(f"schema_version is {data['schema_version']!r}, not 1")
    if data["kind"] != COPY_KIND:
        raise _refuse(f"kind is {data['kind']!r}, not {COPY_KIND!r}")
    if data["spec_leg"] != SPEC_LEG:
        raise _refuse(f"spec_leg is {data['spec_leg']!r}, not {SPEC_LEG!r}")
    commit = data["commit"]
    if not isinstance(commit, str) or not _COMMIT.fullmatch(commit):
        raise _refuse(f"commit is {commit!r}, not a full 40-hex commit id")
    entries = data["copies"]
    if not isinstance(entries, list) or not entries:
        raise _refuse("copies is not a non-empty list")
    copies = tuple(_checked_copy(index, entry) for index, entry in enumerate(entries))
    ids = [copy.id for copy in copies]
    if len(set(ids)) != len(ids):
        raise _refuse(f"an id is given twice in {ids}")
    if set(ids) != COPY_IDS:
        raise _refuse(f"it records {sorted(ids)}, not the consumer's three {sorted(COPY_IDS)}")
    return Record(data["spec_leg"], commit, copies)


def verified_bytes(copy_id: str) -> bytes:
    """The copy's bytes, once its sha256 equals the record's. `CopyRefused`
    otherwise, before a byte of it is parsed."""
    copy = record().copy(copy_id)
    data = _read(f"{SCHEMA_DIR}/{copy.filename}")
    actual = hashlib.sha256(data).hexdigest()
    if actual != copy.sha256:
        raise CopyRefused(
            f"the packaged copy {SCHEMA_DIR}/{copy.filename} is not the spec "
            f"leg's file: its sha256 is {actual}, and {RECORD_NAME} records "
            f"{copy.sha256} for {copy.path} at {SPEC_LEG}@{record().commit}. "
            "Copy the spec leg's file again at that commit; never edit a copy")
    return data


def verified_path(copy_id: str) -> Path:
    """The copy's path on disk, once its digest has been checked."""
    verified_bytes(copy_id)
    return package_dir() / SCHEMA_DIR / record().copy(copy_id).filename


def validator_path() -> Path | None:
    """The packaged validator, or None when this install carries none, or when
    the file there links out of this package. `is_file()` follows a symlink, so
    containment is checked on the RESOLVED path, as `openxdox.snapshot` checks
    it before running the validator (Copilot on openXdox-code#36)."""
    package = package_dir()
    candidate = package / VALIDATOR_NAME
    if candidate.is_file() and candidate.resolve().is_relative_to(package.resolve()):
        return candidate
    return None
