"""Canonical byte-identical snapshot render/write + load + validation (plan
"snapshot.py"; change task 3.1; FR-002 / SC-001 / SC-002).

Serialization is canonical so two runs over an identical tree yield
BYTE-IDENTICAL bytes: sorted keys (recursively), fixed separators, a trailing
newline, and NO wall-clock — this module never reads the clock; any
`generation.generated_at` is derived upstream from `source_revision`'s commit
date by the generator. List ordering is the generator's responsibility.

Writes go through the interactivity boundary (never around it): `write_snapshot`
takes an `OutputBoundary` and writes only under a declared output path.

Validation is DELEGATED to this product's own validator, in this repository
(`scripts/validate-ideation-dashboard-contracts.py`) — the schema is never
restated here. `validate_or_raise` fails loudly on a non-conforming snapshot.
It reports THREE outcomes: validated, not conformant, and validator
unavailable — see the commentary above `VALIDATED` for why the third one exists.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# RELATIVE TO THIS PRODUCT'S OWN ROOT — the repository this module ships in —
# never to an aggregation checkout above it. openxFactory's § 5.2 shed
# (`cc4ae9d3`) deleted `openxFactory/scripts/validate-ideation-dashboard-contracts.py`
# and the carve moved the validator HERE: carve-manifest row
# `scripts/validate-ideation-dashboard-contracts.py` -> `openxdox_code`, same
# path. The aggregation-relative value this replaces named a file no post-shed
# tree carries, so the only thing it could still find was a stale pre-shed copy
# (split-opendox-two-layer-product § 8.9 residue (ii)).
VALIDATOR_RELPATH = Path("scripts") / "validate-ideation-dashboard-contracts.py"


class SnapshotInvalid(Exception):
    """A rendered snapshot failed the pinned validator (or it could not run)."""


# --------------------------- canonical serialization ---------------------------

def canonical_json(snapshot: dict[str, Any]) -> str:
    """Deterministic, diffable JSON: sorted keys, 2-space indent, trailing
    newline (the house canonical-render discipline — see doc_health/runner.py,
    execution_lane/bundler.py)."""
    return json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def canonical_bytes(snapshot: dict[str, Any]) -> bytes:
    return canonical_json(snapshot).encode("utf-8")


def load_snapshot(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_snapshot(snapshot: dict[str, Any], path: Path | str, boundary) -> Path:
    """Render canonically and write through the interactivity boundary. Every
    snapshot write lands under the boundary's declared output allowlist."""
    return boundary.write_output(path, canonical_json(snapshot))


# --------------------------- validator location ---------------------------

# The explicit marker that makes a directory THIS product's root: the source
# layout `<root>/src/openxdox/<this module>` plus a `<root>/pyproject.toml` whose
# `[project] name` is this distribution's. It is read from where this module
# actually sits — never from the cwd, a snapshot's directory, a corpus, or any
# ancestor of them.
PRODUCT_DISTRIBUTION = "openxdox"


def product_root() -> Path | None:
    """This product's own source tree, or None when the module is not running
    from one (an installed wheel ships no `scripts/`, so it has no validator of
    its own to offer, and it must not go looking for somebody else's).

    NO WALK. The root is fixed arithmetic on this module's own resolved path —
    `parents[2]` of `src/openxdox/snapshot.py` — confirmed by the explicit
    marker above, so there is no ancestor for it to adopt."""
    module = Path(__file__).resolve()
    if module.parent.name != PRODUCT_DISTRIBUTION or module.parents[1].name != "src":
        return None
    root = module.parents[2]
    try:
        with (root / "pyproject.toml").open("rb") as fh:
            name = tomllib.load(fh).get("project", {}).get("name")
    except (OSError, tomllib.TOMLDecodeError):
        return None
    if not isinstance(name, str) or name.lower().replace("_", "-") != PRODUCT_DISTRIBUTION:
        return None
    return root


def _inside(path: Path, root: Path) -> bool:
    return Path(path).resolve().is_relative_to(root.resolve())


def find_validator(start: Path | None = None) -> Path | None:
    """THIS PRODUCT'S OWN validator, `product_root() / VALIDATOR_RELPATH`, or
    None. It is looked for in exactly one place, and never above the product's
    root: the parent walk this replaces ADOPTED whatever enclosing checkout
    still carried a pre-shed copy (split-opendox-two-layer-product § 8.9
    residue (iii) — a reader adopting its enclosing tree).

    `start` keeps its declared signature (openDox's `consumer_reach` binds this
    function by name) and now CONFINES instead of widening: a `start` outside
    this product's own tree answers None, because nothing outside that tree is
    ever consulted, and `start=None` asks from the module itself. A caller that
    means a validator from anywhere else passes it explicitly —
    `validate_snapshot(..., validator=...)`; none is ever inferred from where a
    snapshot, a corpus or the cwd happens to sit."""
    root = product_root()
    if root is None:
        return None
    if start is not None and not _inside(Path(start), root):
        return None
    candidate = root / VALIDATOR_RELPATH
    # `is_file()` follows a symlink, so containment is checked on the RESOLVED
    # path as well: a `scripts/` link pointing out of the tree is refused.
    if candidate.is_file() and _inside(candidate, root):
        return candidate
    return None


def _validator_not_found_reason(search_from: Path | None) -> str:
    """Why `find_validator` answered None, in the three ways it can."""
    root = product_root()
    if root is None:
        where = ("this openxdox is not running from a source checkout, so it "
                 f"carries no {VALIDATOR_RELPATH} of its own")
    elif search_from is not None and not _inside(Path(search_from), root):
        where = (f"the search was confined to {search_from}, which lies outside "
                 f"this product's own tree ({root})")
    else:
        where = f"{root / VALIDATOR_RELPATH} does not exist"
    return (f"{where}; a validator in an enclosing checkout is never adopted — "
            "pass validator= to use one explicitly")


# --------------------------- validation ---------------------------
#
# THREE outcomes, not two. "the snapshot is wrong" and "the check could not be
# performed" are different facts about the world and they deserve different
# consequences, but a bare `ok = (returncode == 0)` collapses them into one — and
# the collapse shipped: on a host whose python lacks the validator's own
# dependencies the validator exits non-zero, `ok` was False, and
# `generate-and-open` returned before starting the server. A human with a
# perfectly good corpus was told, in effect, that his corpus was bad, and got no
# dashboard. (The bug was latent until PR #51 taught the search to find the
# validator via `--repo-root`: before that the validator was simply not reached
# on the documented launch, validation SKIPPED, and the server started.)

VALIDATED = "validated"
NOT_CONFORMANT = "not-conformant"
VALIDATOR_UNAVAILABLE = "validator-unavailable"

# THE SIGNAL for "unavailable", and why it is not a string match. The pinned
# validator publishes an exit-code contract in its own module docstring —
# "Exit codes: 0 ok, 1 findings (or warnings under --strict), 2 harness error" —
# and honours it: `report()` is the ONLY place a verdict on the DATA is turned
# into a status, and it returns 1 (findings, or warnings under --strict) or 0.
# Every other non-zero exit is environmental: PyYAML absent, jsonschema/
# referencing absent, the schema directory missing, the target path unreadable,
# or the catch-all `ERROR harness failure:` around `main()`. So the classifier
# reads the number, not the prose. Matching the English of one dependency
# message would break on the next wording change, would miss the PyYAML variant
# sitting three lines above it, and would say nothing about a validator that
# could not be launched at all.
FINDINGS_EXIT = 1

# One spelling of the remedy, shared by every surface that has to state it.
DEPENDENCY_REMEDY = "pip install 'jsonschema>=4.18' referencing rfc3339-validator"


@dataclass
class ValidationResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    validator: Path | None
    # Additive: `outcome` refines `ok` without displacing it, so every existing
    # `if not result.ok` caller keeps its exact behaviour. Left unset it is
    # derived from `ok` under the old two-outcome reading.
    outcome: str | None = None
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        if self.outcome is None:
            self.outcome = VALIDATED if self.ok else NOT_CONFORMANT

    @property
    def available(self) -> bool:
        """Did the validator actually reach a verdict? False means NOTHING is
        known about this snapshot's conformance — not that it is bad."""
        return self.outcome != VALIDATOR_UNAVAILABLE

    def summary(self) -> str:
        if self.validator is None:
            return "validator not found (only this product's own tree is searched)"
        tail = (self.stdout or self.stderr).strip().splitlines()
        return tail[-1] if tail else f"returncode={self.returncode}"


def _is_readable_json(path: Path) -> bool:
    """Can WE read the file we just handed the validator? This is the one
    attribution the exit code cannot make for us: the validator also exits with
    a harness code when the target file will not parse, and that failure is the
    DATA's, not the environment's. Asking locally keeps a truncated or corrupt
    snapshot classified as non-conformant — so this fix cannot turn a real
    blocking failure into a warning."""
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    return True


def validate_snapshot(
    path: Path | str, *, validator: Path | None = None, strict: bool = False,
    search_from: Path | None = None,
) -> ValidationResult:
    """Validate a rendered snapshot file with the pinned validator (single-file
    mode auto-detects `kind`). Returns a result; never raises for a mere
    validation failure — use `validate_or_raise` for loud failure.

    `result.outcome` is one of `VALIDATED`, `NOT_CONFORMANT`, or
    `VALIDATOR_UNAVAILABLE`; `result.ok` stays True only for `VALIDATED`."""
    path = Path(path).resolve()
    # The snapshot's own directory is NOT a search root any more: a snapshot
    # written inside some other checkout must not choose that checkout's
    # validator (§ 8.9 residue (iii)). `search_from`, when given, only confines.
    validator = validator or find_validator(search_from)
    if validator is None:
        return ValidationResult(
            False, -1, "", "validator not found", None, VALIDATOR_UNAVAILABLE,
            _validator_not_found_reason(search_from))
    if not Path(validator).is_file():
        # Checked BEFORE launching, because the exit code cannot carry this one:
        # `python3 <a directory>` exits 1 — the validator's own findings code —
        # so a bogus explicitly-passed path would otherwise be read as a verdict
        # against the snapshot. `find_validator` can never produce it (it tests
        # `is_file`), but a caller supplying `validator=` can.
        return ValidationResult(
            False, -1, "", f"not a file: {validator}", Path(validator),
            VALIDATOR_UNAVAILABLE,
            f"the validator path is not a readable file ({validator})")
    cmd = [sys.executable, str(validator), str(path)]
    if strict:
        cmd.append("--strict")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:      # not executable, interpreter gone, ENOMEM, ...
        return ValidationResult(
            False, -1, "", f"{type(exc).__name__}: {exc}", validator,
            VALIDATOR_UNAVAILABLE,
            f"the validator could not be launched with {sys.executable}")
    if proc.returncode == 0:
        return ValidationResult(True, 0, proc.stdout, proc.stderr, validator,
                                VALIDATED)
    if proc.returncode == FINDINGS_EXIT:
        return ValidationResult(False, proc.returncode, proc.stdout, proc.stderr,
                                validator, NOT_CONFORMANT)
    if not _is_readable_json(path):
        return ValidationResult(False, proc.returncode, proc.stdout, proc.stderr,
                                validator, NOT_CONFORMANT)
    return ValidationResult(
        False, proc.returncode, proc.stdout, proc.stderr, validator,
        VALIDATOR_UNAVAILABLE,
        f"the validator exited {proc.returncode}, which is a HARNESS error in its "
        f"own documented contract (0 ok, {FINDINGS_EXIT} findings, 2 harness "
        f"error) — it never reached a verdict on this snapshot")


def validate_or_raise(
    path: Path | str, *, validator: Path | None = None, strict: bool = False,
    search_from: Path | None = None,
) -> ValidationResult:
    """Validate and raise `SnapshotInvalid` on non-conformance (or on an
    unrunnable validator) — the generator's fail-loud path (SC-002).

    An UNAVAILABLE validator still raises here, deliberately, and that is not an
    oversight left over from the three-outcome split. This is the path a caller
    chooses when it wants a guarantee rather than a report, and "I could not
    check" is not the guarantee it asked for. The warn-and-continue judgement
    belongs to the CLI, which knows a human is standing there and that a
    dashboard he cannot start helps him less than an unchecked one he can."""
    result = validate_snapshot(path, validator=validator, strict=strict,
                               search_from=search_from)
    if not result.ok:
        raise SnapshotInvalid(
            f"{path}: {result.summary()}\n{result.stdout}{result.stderr}".rstrip())
    return result
