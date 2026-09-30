"""openXdox's governed projection, contributed through openDox's seams.

WHY THIS FILE EXISTS. Box 5.4a of openxFactory's
`add-neutral-product-standalone-operability` (RATIFIED, `openxFactory#656`
comment `5815412869`) has openXdox KEEP `generator.py`, `snapshot.py`,
`snapshot_registry.py`, `completeness.py` and `corpus_root.py`, and contribute
its governed generator through the seam 5.4 declares. R1Q10 (a) (comment
`5850003126`, in R-G3's pattern) gives every consumer mechanism on release 1's
path an openDox-owned neutral default, and has openXdox contribute its
governed one through the same seam. openDox-code declares the seams: the
generator seam (`opendox.generator_seam`, plan 034 T052) and the four
projection seams (`opendox.projection_seams`, T055). This module is openXdox's
half (plan 034 T059): it registers

* the governed generator (`generator.generate_snapshot`) at the generator seam,
  writing `ideation-dashboard-snapshot` and declaring the two inputs a governed
  generation takes, `project_register_source` and `possibles_source`;
* the snapshot registry and the source over it (`snapshot_registry`) at
  `projection_seams.registry`;
* the corpus-root predicate (`corpus_root`), with the corpus's change rows, at
  `projection_seams.corpus_root`;
* the canonical writer (`snapshot`) at `projection_seams.writer`;
* this product's validator (`snapshot.validate_snapshot`) at
  `projection_seams.validators`, for each of openXdox-spec's three kinds.
  openDox's own kinds (`opendox-snapshot`, `ideation-workbench`) keep openDox's
  own validator: a host that contributes its governed validator does not take
  openDox's kinds with it (`projection_seams`' own rule).

WHO CALLS `register()`. It is the one call, made ONCE, at process start, before
any of openDox's entry points reads a default: a default is sealed once read,
and a host registration over a read default is refused.

* `openxdox.domain_profile.register()` calls it, so openXdox's own
  registration path (this leg's root `conftest.py`, and any openXdox-only
  host) gets the contributions with no second call.
* openxFactory registers its profile with openDox, never with openXdox, so it
  makes this call itself: plan 034's T064 adds it to
  `scripts/opendox_host.register_openxfactory()`. The holder decided this on
  2026-09-29 and revised the 2026-09-27 decision in openDox-code#54's body,
  which assumed openxFactory already called openXdox's registration hook.
* `domain_profile.load()` does NOT call it. Loading or validating a profile
  registers nothing, so a verifier, a sync or a test that only reads a profile
  never changes what a process serves.

ALL OR NONE. Each seam refuses a registration over a host's that differs, and
over openDox's default once a consumer has read it. If any seam refuses, every
seam this call wrote is emptied again, in reverse order, before the refusal
reaches the caller. A seam that already held this module's contribution was
not written, since its registration is a no-op, and it is left as it was. A
seam where this call replaced openDox's unread default is emptied too, and
openDox's entry points register the default there again, as they do wherever
nothing is registered. So a refused call never leaves one process projecting
through some governed mechanisms and some neutral ones.

IDEMPOTENT. Each contribution below is one object, made once at import. A
second `register()` finds each seam holding the same object, and every seam
treats that as a no-op.

RESOLVED AT USE, AS THE REACH IT REPLACES WAS. `generator.py`, `corpus_root.py`
and `completeness.py` import openxFactory's `doc_health` at module level, which
a lone openXdox-code checkout does not carry (R1Q6 (d), comment `5817152735`;
the direction arc is plan 034's T008). openDox probes a registration's names
when it is made, so a contribution that imported those modules would make the
registration itself fail in a lone checkout, and with it every process that
registers a profile. So the generator and the corpus-root predicate are
adapters that import the governed module when they are CALLED, as openDox's
`consumer_reach` stand-ins did before T055. In a lone checkout a governed
generation then fails where it always failed, on `doc_health`, and registering
does not. `snapshot_registry.py` reads `doc_health` only for one sentinel, so it
imports it there (T059), and the module itself is registered.

A CREATED FILE: no row in openxFactory's `docs/opendox-carve-manifest.yaml`,
which declares what LEAVES openxFactory, never what a destination assembles
(RULED OQ-C).
"""

from __future__ import annotations

import importlib
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from opendox import generator_seam, projection_seams

from . import snapshot as snapshot_mod
from . import snapshot_registry as snapshot_registry_mod

__all__ = [
    "CORPUS_ROOT",
    "GENERATOR",
    "GENERATOR_INPUTS",
    "GOVERNED_KINDS",
    "GOVERNED_SNAPSHOT_KIND",
    "GovernedCorpusRoot",
    "GovernedValidator",
    "REGISTRY",
    "VALIDATOR",
    "WRITER",
    "generate",
    "is_registered",
    "register",
    "unregister",
]

#: The contract openXdox's governed generator writes, and the kind every
#: snapshot it answers carries. openXdox-spec owns its schema.
GOVERNED_SNAPSHOT_KIND = "ideation-dashboard-snapshot"

#: The kinds this product's validator is registered for: openXdox-spec's three
#: (#1144 7.1's second row), which are this consumer's own.
GOVERNED_KINDS: tuple[str, ...] = (
    GOVERNED_SNAPSHOT_KIND,
    "ideation-dashboard-snapshot-index",
    "gate-action-record",
)

#: The inputs a governed generation takes beyond the seam's own four. Both are
#: optional, as the seam requires: openDox passes one only when its caller has
#: a value for it. `generate_snapshot`'s test-only keywords (`git`,
#: `generator_version`, `excluded_documents`) are not declared, so the seam
#: never passes them.
GENERATOR_INPUTS: tuple[str, ...] = ("project_register_source", "possibles_source")


def _governed(name: str) -> Any:
    """`openxdox.<name>`, imported now. The one place a contribution reaches a
    governed module that needs `doc_health`, so a lone checkout fails here, at
    use, naming the missing module."""
    return importlib.import_module(f"{__package__}.{name}")


# --------------------------------------------------------------------------
# the generator
# --------------------------------------------------------------------------

def generate(repo_root: Path | str, repository: str, *,
             source_revision: str | None = None,
             generated_at: str | None = None,
             project_register_source: Path | None = None,
             possibles_source: Path | None = None) -> dict:
    """openXdox's governed generation, the seam's operation:
    `generator.generate_snapshot`, resolved at each call."""
    return _governed("generator").generate_snapshot(
        repo_root, repository, source_revision=source_revision,
        generated_at=generated_at,
        project_register_source=project_register_source,
        possibles_source=possibles_source)


GENERATOR = generator_seam.SnapshotGenerator(
    contract=GOVERNED_SNAPSHOT_KIND, generate=generate, inputs=GENERATOR_INPUTS)


# --------------------------------------------------------------------------
# the corpus-root predicate
# --------------------------------------------------------------------------

class _ScannedRoots(Sequence):
    """`corpus_root.SCANNED_ROOTS`, read when it is used.

    The roots derive from openxFactory's doc-health scan
    (`corpus.GOVERNED_ROOTS`), so they cannot be read before `doc_health` is
    reached. openDox takes the value when the registration is made and reads
    it only through sequence operations (`tuple(...)`), so this defers to the
    first of them. `repr` does not resolve, so a debugger or an assertion
    rewrite never makes the reach."""

    def _roots(self) -> tuple[str, ...]:
        return tuple(_governed("corpus_root").SCANNED_ROOTS)

    def __getitem__(self, index):
        return self._roots()[index]

    def __len__(self) -> int:
        return len(self._roots())

    def __iter__(self):
        return iter(self._roots())

    def __contains__(self, item: Any) -> bool:
        return item in self._roots()

    def __repr__(self) -> str:
        return "<openxdox.corpus_root.SCANNED_ROOTS, read when used>"


class GovernedCorpusRoot:
    """openXdox's corpus-root predicate at `projection_seams.corpus_root`.

    `corpus_scan_defect`, `corpus_root_refusal` and `SCANNED_ROOTS` are
    `corpus_root`'s own. `change_rows` is the corpus's change enumeration with
    each change's declared staged origin, which `branch_session._change_rows`
    computed from `generator.iter_changes` and
    `generator.declared_origin_state` before T055 routed it here."""

    SCANNED_ROOTS: Sequence = _ScannedRoots()

    @staticmethod
    def corpus_scan_defect(repo_root: Path | str) -> str | None:
        return _governed("corpus_root").corpus_scan_defect(repo_root)

    @staticmethod
    def corpus_root_refusal(repo_root: Path | str, *, flag: str = "--repo-root",
                            shape: str = "") -> str | None:
        return _governed("corpus_root").corpus_root_refusal(
            repo_root, flag=flag, shape=shape)

    @staticmethod
    def change_rows(checkout_root: Path | str) -> tuple:
        """`(change id, status, folder, origin state, origin)` per change."""
        generator = _governed("generator")
        return tuple(
            (change_id, status, folder, *generator.declared_origin_state(folder))
            for change_id, status, folder, _archive_date
            in generator.iter_changes(Path(checkout_root)))


CORPUS_ROOT = GovernedCorpusRoot()


# --------------------------------------------------------------------------
# the validator
# --------------------------------------------------------------------------

class GovernedValidator:
    """This product's validator at `projection_seams.validators`, for
    openXdox-spec's three kinds.

    openDox hands it the roots a search may start from, the written snapshot's
    directory first and the served checkout second. Since plan 034 T061 there
    is no search: `snapshot.find_validator` answers the installed
    distribution's own validator whatever the start (#1144 7.3, RULED R1Q14
    (a)), so `locate()` asks it once and the roots are not read.
    `snapshot.validate_snapshot` reaches the verdict, with its three outcomes,
    and its result carries every attribute openDox reads."""

    #: The remedy openDox prints when the validator is found but cannot run.
    dependency_remedy = snapshot_mod.DEPENDENCY_REMEDY

    def locate(self, search_from: tuple = ()) -> Path | None:
        """The installed distribution's own validator, or None. `search_from`
        keeps the seam's signature and is not read."""
        return snapshot_mod.find_validator()

    def validate(self, path: Path | str, *, strict: bool = False,
                 search_from: tuple = ()) -> snapshot_mod.ValidationResult:
        validator = self.locate(search_from)
        if validator is not None:
            return snapshot_mod.validate_snapshot(path, validator=validator,
                                                  strict=strict)
        return snapshot_mod.ValidationResult(
            False, -1, "", "validator not found", None,
            snapshot_mod.VALIDATOR_UNAVAILABLE,
            f"this product's own validator ({snapshot_mod.VALIDATOR_RELPATH.name}) "
            f"was not found: {snapshot_mod._validator_not_found_reason(None)}")


VALIDATOR = GovernedValidator()

#: The registry module carries every name `projection_seams.registry` asks for.
REGISTRY = snapshot_registry_mod

#: The canonical writer: `snapshot.write_snapshot(snapshot, path, boundary)`.
WRITER = snapshot_mod


# --------------------------------------------------------------------------
# the one registration
# --------------------------------------------------------------------------

_lock = threading.Lock()


def _contributions() -> tuple[tuple[str, Any, str | None, Any], ...]:
    """`(name, seam, kind, contribution)`, in the order they are registered."""
    return (
        ("generator", generator_seam, None, GENERATOR),
        ("registry", projection_seams.registry, None, REGISTRY),
        ("corpus_root", projection_seams.corpus_root, None, CORPUS_ROOT),
        ("writer", projection_seams.writer, None, WRITER),
        *((f"validators[{kind}]", projection_seams.validators, kind, VALIDATOR)
          for kind in GOVERNED_KINDS),
    )


def _holds(seam: Any, kind: str | None, contribution: Any) -> bool:
    """Does `seam` hold `contribution` now? Answered without reading it.

    The generator seam's `current()` records nothing, so it is asked. A
    projection seam's `current()` and `for_kind()` close the entry point's
    default's window, and asking one would turn a replaceable default into a
    refusal. So its registration is read where the seam keeps it. The names
    read are pinned by `tests/test_projection_contributions.py`, so a pin move
    that renames them fails there rather than here."""
    if seam is generator_seam:
        try:
            return generator_seam.current() is contribution
        except generator_seam.GeneratorNotRegistered:
            return False
    if kind is None:
        return seam._registered is contribution
    held = seam._registered.get(kind)
    return held is not None and held[0] is contribution


def _register_one(seam: Any, kind: str | None, contribution: Any) -> None:
    if kind is None:
        seam.register(contribution)
    else:
        seam.register(kind, contribution)


def _take_back(seam: Any, kind: str | None) -> None:
    if kind is None:
        seam.unregister()
    else:
        seam.unregister(kind)


def _unread_default(seam: Any, kind: str | None) -> Any:
    """The unread default `seam` holds (for `kind`), or None. It is the one
    registration `register()` can replace: a host's refuses, and so does a
    default that has been read. Read where the seam keeps it, like `_holds`,
    because `current()` would close the default's window."""
    if seam is generator_seam:
        return generator_seam._registered if generator_seam._is_default else None
    if kind is None:
        return seam._registered if seam._is_default else None
    held = seam._registered.get(kind)
    return held[0] if held is not None and held[1] else None


def _put_back(seam: Any, kind: str | None, displaced: Any) -> None:
    """Empty what this call wrote, and give back the unread default it
    replaced, as the default it was (Copilot on openXdox-code#35)."""
    _take_back(seam, kind)
    if displaced is None:
        return
    if kind is None:
        seam.register_default(displaced)
    else:
        seam.register_default(kind, displaced)


def register() -> tuple[str, ...]:
    """Register every contribution at its seam, all or none. Returns the
    seams' names.

    A refusal is openDox's own (`GeneratorAlreadyRegistered`,
    `SeamAlreadyRegistered`), raised unchanged once every seam this call wrote
    holds again what it held before: nothing, or the unread default this call
    replaced, given back as a default."""
    with _lock:
        written: list[tuple[Any, str | None, Any]] = []
        try:
            for _name, seam, kind, contribution in _contributions():
                if _holds(seam, kind, contribution):
                    continue
                displaced = _unread_default(seam, kind)
                _register_one(seam, kind, contribution)
                written.append((seam, kind, displaced))
        except BaseException:
            for seam, kind, displaced in reversed(written):
                _put_back(seam, kind, displaced)
            raise
        return tuple(name for name, *_ in _contributions())


def is_registered() -> bool:
    """Does every seam hold this module's contribution?"""
    return all(_holds(seam, kind, contribution)
               for _name, seam, kind, contribution in _contributions())


def unregister() -> None:
    """Empty every seam that holds this module's contribution, and leave every
    other seam as it is. For test isolation and for a host tearing down."""
    with _lock:
        for _name, seam, kind, contribution in reversed(_contributions()):
            if _holds(seam, kind, contribution):
                _take_back(seam, kind)
