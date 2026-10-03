"""openXdox's governed columns, contributed through openDox's column seams.

WHY THIS FILE EXISTS. #1144's 4.3 has openDox route every deferred reach
through a seam it declares, and none stays late-bound by name. Plan 034's T084
(openDox-code#77) declares the last four, in `opendox.column_seams`: the gate
primitives (`gate`), the doxBench scope authority (`scope`), kickoff
(`kickoff`) and the cross-reference register (`register`), each with a small
neutral default in `opendox.default_columns`. R1Q10 (a) (`openxFactory#656`
comment `5850003126`, in R-G3's pattern) has openXdox contribute its governed
mechanism through the same seam. This module is that half for the four (plan
034 T086), as `projection_contributions` is for the projection (T059). It
registers

* the governed gate at `column_seams.gate`: `gate_console`'s names, with
  `gate_routes.first_edit_gate_factory` beside them (`GATE`). It is one
  registration for the whole family, because the names agree with each other:
  a record builder checks a `Provenance` of its own type, and a caller catches
  its own `GateRefused`;
* the governed scope authority at `column_seams.scope`: the
  `openxdox.doxbench_scope` module itself (`SCOPE`). Only a staged tile's
  folder documents and the documents a session created are editable there;
* the governed kickoff at `column_seams.kickoff`: `kickoff`'s dispatched
  commissions and its project-register discovery (`KICKOFF`);
* the cross-reference register at `column_seams.register`: the
  `openxdox.register` module itself (`REGISTER`).

THE FOUR ARE ONE GROUP (the holder's ruling on T086's question Q1 (a),
2026-10-02). `gate_console.py` imports openxFactory's `doc_health` at module
level, which a lone openXdox-code checkout does not carry (R1Q6 (d), comment
`5817152735`; the direction arc is plan 034's T008). openDox reads every name
of a registration when it is made, so the governed gate cannot be registered
where `gate_console` cannot be imported. The governed scope reads governed
gate records for a live session, and kickoff imports `gate_console` itself, so
neither can stand beside openDox's neutral gate. So the four are registered
together, only where `gate_console` imports, and nowhere else. Where it does
not import because `doc_health` is absent, `register()` writes nothing,
records why in `SKIPPED`, and returns no names. openDox's entry points then
register openDox's defaults at all four, as they do in any standalone
process. Any other import error is a defect, and it is raised.

WHO CALLS `register()`. It is the one call, made ONCE, at process start, before
any of openDox's entry points reads a default: a default is sealed once read,
and a host registration over a read default is refused.

* `openxdox.domain_profile.register()` calls it, after
  `projection_contributions.register()`, so openXdox's own registration path
  (this leg's root `conftest.py`, and any openXdox-only host) gets the four
  with no second call.
* openxFactory registers its profile with openDox, never with openXdox, so it
  makes this call itself, after its projection call (plan 034 T094, the
  holder's ruling on T086's question Q6 (a)).
* `domain_profile.load()` does NOT call it, so loading or validating a profile
  registers nothing.

ALL OR NONE, AS `projection_contributions` IS. Each seam refuses a
registration over a host's that differs, and over openDox's default once a
consumer has read it. If any seam refuses, every seam this call wrote holds
again what it held before (nothing, or the unread default this call replaced,
given back as a default) before the refusal reaches the caller. So one process
runs on openXdox's four governed columns or on openDox's four defaults, never
on a mix of the two. Since Brett's ruling at `5961651355` openDox's default
scope marks a tile's own documents editable, which is more than the governed
scope allows; the seam holds one registration, so the two never both apply.

IDEMPOTENT. Each contribution is one object, made once at import. A second
`register()` finds each seam holding the same object, and every seam treats
that as a no-op.

RESOLVED AT USE. `GATE` and `KICKOFF` resolve each name on the governed module
when it is read, so a test's monkeypatch of `gate_console` or `kickoff` is
what openDox's verbs then reach, as it was when they imported those modules by
name. The classes and values themselves are the governed modules' own
objects, so `except <gate>.GateRefused` and `isinstance(..., Provenance)`
hold by identity.

A CREATED FILE: no row in openxFactory's `docs/opendox-carve-manifest.yaml`,
which declares what LEAVES openxFactory, never what a destination assembles
(RULED OQ-C).
"""

from __future__ import annotations

import importlib
import threading
from typing import Any

from opendox import column_seams

from . import doxbench_scope as doxbench_scope_mod
from . import register as register_mod

__all__ = [
    "GATE",
    "KICKOFF",
    "REGISTER",
    "SCOPE",
    "SKIPPED",
    "is_registered",
    "register",
    "unregister",
]


def _governed(name: str) -> Any:
    """`openxdox.<name>`, imported now."""
    return importlib.import_module(f"{__package__}.{name}")


class _Forwarding:
    """A registration whose names are a governed module's, read on each use.

    `redirect` maps a name to the sibling module that holds it instead
    (`first_edit_gate_factory` is `gate_routes`', not `gate_console`'s). A
    dunder is never forwarded, so `copy`, `pickle` and the like see a plain
    object rather than the module's."""

    def __init__(self, label: str, module: str,
                 redirect: dict[str, str] | None = None) -> None:
        self._label = label
        self._module = module
        self._redirect = dict(redirect or {})

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return getattr(_governed(self._redirect.get(name, self._module)), name)

    def __repr__(self) -> str:
        return f"<{self._label}: openxdox.{self._module}, read when used>"


#: The governed gate: `gate_console`'s names, and `first_edit_gate_factory`
#: from `gate_routes`.
GATE = _Forwarding("openxdox.column_contributions.GATE", "gate_console",
                   {"first_edit_gate_factory": "gate_routes"})

#: The governed scope authority, which carries every name the seam asks for.
SCOPE = doxbench_scope_mod

#: The governed kickoff: `kickoff`'s dispatched commissions and its
#: project-register discovery.
KICKOFF = _Forwarding("openxdox.column_contributions.KICKOFF", "kickoff")

#: The cross-reference register, which carries `CrossReferenceIndexAdapter`.
REGISTER = register_mod

#: Why the last `register()` wrote nothing, or None when it registered the
#: four. The one reason is that `gate_console` cannot import `doc_health`.
SKIPPED: str | None = None

_lock = threading.Lock()


def _contributions() -> tuple[tuple[str, Any, Any], ...]:
    """`(name, seam, contribution)`, in the order they are registered."""
    return (
        ("gate", column_seams.gate, GATE),
        ("scope", column_seams.scope, SCOPE),
        ("kickoff", column_seams.kickoff, KICKOFF),
        ("register", column_seams.register, REGISTER),
    )


def _why_not_importable() -> str | None:
    """None where `gate_console` imports. Where it cannot because openxFactory's
    `doc_health` is absent, the reason. Any other import error is raised."""
    try:
        _governed("gate_console")
    except ModuleNotFoundError as exc:
        missing = exc.name or ""
        if missing != "doc_health" and not missing.startswith("doc_health."):
            raise
        return ("openXdox's governed columns are not registered: its gate "
                "console imports openxFactory's doc_health at module level "
                "(src/openxdox/gate_console.py), which this process cannot "
                f"import ({missing}), so openDox's own defaults stand at its "
                "four column seams (R1Q6 (d), openxFactory#656 comment "
                "5817152735; the direction arc is plan 034 T008)")
    return None


def _holds(seam: Any, contribution: Any) -> bool:
    """Does `seam` hold `contribution` now? Read where the seam keeps it,
    because `current()` would close the entry point's default's window. The
    names read are pinned by `tests/test_column_contributions.py`."""
    return seam._registered is contribution


def _unread_default(seam: Any) -> Any:
    """The unread default `seam` holds, or None: the one registration
    `register()` can replace."""
    return seam._registered if seam._is_default else None


def _put_back(seam: Any, displaced: Any) -> None:
    """Empty what this call wrote, and give back the unread default it
    replaced, as the default it was."""
    seam.unregister()
    if displaced is not None:
        seam.register_default(displaced)


def register() -> tuple[str, ...]:
    """Register the four governed columns at their seams, all or none, where
    `gate_console` imports. Returns the seams' names, or none where it wrote
    nothing (see `SKIPPED`).

    A refusal is openDox's own (`SeamAlreadyRegistered`, or the `TypeError` a
    seam raises for a registration missing a name), raised unchanged once
    every seam this call wrote holds again what it held before."""
    global SKIPPED
    with _lock:
        reason = _why_not_importable()
        SKIPPED = reason
        if reason is not None:
            return ()
        written: list[tuple[Any, Any]] = []
        try:
            for _name, seam, contribution in _contributions():
                if _holds(seam, contribution):
                    continue
                displaced = _unread_default(seam)
                seam.register(contribution)
                written.append((seam, displaced))
        except BaseException:
            for seam, displaced in reversed(written):
                _put_back(seam, displaced)
            raise
        return tuple(name for name, *_ in _contributions())


def is_registered() -> bool:
    """Does every seam hold this module's contribution?"""
    return all(_holds(seam, contribution)
               for _name, seam, contribution in _contributions())


def unregister() -> None:
    """Empty every seam that holds this module's contribution, and leave every
    other seam as it is. For test isolation and for a host tearing down."""
    with _lock:
        for _name, seam, contribution in reversed(_contributions()):
            if _holds(seam, contribution):
                seam.unregister()
