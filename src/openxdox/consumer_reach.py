"""Late-bound reaches from openXdox INTO its consumer's column.

WHY THIS FILE EXISTS. The pin chain runs one way — `openxFactory` pins the
openXdox assembly root (`split-opendox-two-layer-product` § 5.1, RULING F) and
openXdox pins openDox (RULED OQ-2) — so a module of THIS package may import
`opendox` freely and may never import `openxFactory`'s own column at import
time. `design.md`:243 states the standard the carve is held to in one sentence:
*"What must not survive is the direction, not the calls."*

One call survived the carve pointing the wrong way. `cli_gate.py`'s
`cmd_gate_lens_add_as_cluster` verb submits a `pending_review` entry into the
CROSS-REFERENCE QUEUE, and that queue is `human_seen` — a
`not_moved / stays_openxfactory_adapter` row under RULING DQ-1
(`docs/opendox-carve-manifest.yaml`: *"the cross-reference submission queue is
openxFactory's own candidate register (design.md § D3, 'the candidate-register
row')"*). It exists at NEITHER destination. The arrived module therefore
carried, at module level, `from ideation_dashboard import human_seen as
human_seen_mod` — the PRE-CARVE package name, an `import rewrites` line the
manifest declares (`cli_gate.py` lines 44-54, 74) and the carve left unapplied,
because there was nothing lawful to rewrite it TO.

WHAT THIS MODULE DOES, AND WHAT IT DELIBERATELY DOES NOT. It makes that one
reach LATE, NAMED and REFUSABLE instead of an import-time dependency on the
consumer. Importing `openxdox.cli_gate` no longer requires openxFactory to be
importable; the verb that actually needs the queue resolves it on first
attribute access and, when it is absent, refuses with the layering spelled out
rather than raising `ModuleNotFoundError` from an import line eleven hundred
lines away from the verb.

It does NOT pretend to be the design fix. The right long-run shape is
INJECTION — openxFactory hands its submission sink to the verb, and openXdox
names a protocol rather than a module — and that is BUILD-arc work
(`split-opendox-two-layer-product` § 3.5/3.6), not a direction fix. This module
is deliberately narrow so that it cannot grow into a general facade: a name is
added here only when a verb of this column is ruled to reach the consumer for
it, and every addition carries its manifest row and its reason.

A CREATED FILE: it has no row in `docs/opendox-carve-manifest.yaml`, because the
manifest declares what LEAVES openxFactory and never what a destination
assembles (RULED OQ-C). It sits under a declared root, so the arrival verifier
is told about it explicitly with
`--allow-created src/openxdox/consumer_reach.py`.
"""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any

#: Where the consumer's column can be reached from, in the order tried. Both
#: spellings are openxFactory's own: `ideation_dashboard.<name>` is the package
#: form, `<name>` the bare form a `scripts/`-on-`sys.path` runner exposes. This
#: package supplies NEITHER — that is the point of the list being data.
_CANDIDATE_PREFIXES = ("ideation_dashboard.", "")


def _names_the_candidate(missing: str, dotted: str) -> bool:
    """Is `missing` the candidate itself, or a package on its dotted path?

    `import_module("ideation_dashboard.human_seen")` raises
    `ModuleNotFoundError(name="ideation_dashboard")` when the PACKAGE is absent
    and `name="ideation_dashboard.human_seen"` when only the submodule is — both
    mean "the consumer is not here". `name="yaml"`, raised from inside a
    consumer module that DID load, does not, and must not be swallowed.
    """
    return dotted == missing or dotted.startswith(f"{missing}.")


class ConsumerReachUnavailable(RuntimeError):
    """A verb of this column reached its consumer's column and it is absent.

    Raised instead of `ModuleNotFoundError` so the failure names the LAYERING
    rather than a module path: openXdox does not ship, pin or depend on
    openxFactory's adapter column, and a caller that needs this verb is
    responsible for making the named module importable — or, better, for the
    injection the BUILD arc owes.
    """


class _LateConsumerModule:
    """A stand-in for a consumer-column module, resolved on first use.

    Attribute access — and nothing earlier — performs the import. The resolved
    module is cached, so the cost is paid once and `is` identity holds across
    accesses, which is what lets a caller `monkeypatch.setattr` the real module
    and be seen by this column's verbs.
    """

    __slots__ = ("_name", "_reason", "_module")

    def __init__(self, name: str, *, reason: str) -> None:
        self._name = name
        self._reason = reason
        self._module: ModuleType | None = None

    @property
    def name(self) -> str:
        return self._name

    def resolve(self) -> ModuleType:
        """Import the consumer-column module, or refuse naming the layering.

        A candidate that is ABSENT is skipped; a candidate that is PRESENT and
        raises while executing is re-raised untouched. Catching `ImportError`
        wholesale would turn a broken consumer module into a silent fall-through
        to the next candidate — which could be an unrelated top-level module of
        the same name — or into a `ConsumerReachUnavailable` blaming the
        layering for a bug inside openxFactory. Only `ModuleNotFoundError`
        naming the candidate itself, or a package on its own dotted path, means
        "not here".
        """
        if self._module is not None:
            return self._module
        tried: list[str] = []
        for prefix in _CANDIDATE_PREFIXES:
            dotted = f"{prefix}{self._name}"
            tried.append(dotted)
            try:
                self._module = importlib.import_module(dotted)
            except ModuleNotFoundError as exc:
                if exc.name is not None and _names_the_candidate(exc.name, dotted):
                    continue
                raise
            return self._module
        raise ConsumerReachUnavailable(
            f"{self._name!r} is openxFactory's own adapter column and this "
            f"package does not supply it: {self._reason}. Tried "
            f"{', '.join(repr(t) for t in tried)}. openXdox pins openDox and "
            "is itself pinned BY openxFactory (split-opendox § 5.1, RULING F), "
            "so the dependency may not run the other way at import time; a "
            "caller that needs this verb must make the module importable, and "
            "the BUILD arc (split-opendox § 3.5/3.6) owes the injection that "
            "removes the reach altogether")

    def __getattr__(self, attr: str) -> Any:
        if attr.startswith("__") and attr.endswith("__"):
            raise AttributeError(attr)
        return getattr(self.resolve(), attr)

    def __repr__(self) -> str:
        state = "resolved" if self._module is not None else "unresolved"
        return f"<late consumer module {self._name!r} ({state})>"


#: The cross-reference submission queue, RULING DQ-1's candidate register.
#: `cli_gate.cmd_gate_lens_add_as_cluster` reads `HumanSeenSubmission`,
#: `SubmissionRefused` and `SubmissionInvalid` off it, all inside the verb.
human_seen = _LateConsumerModule(
    "human_seen",
    reason="the cross-reference submission queue stays in openxFactory under "
           "RULING DQ-1 (manifest row: not_moved / stays_openxfactory_adapter) "
           "and exists at neither carve destination")

__all__ = ["ConsumerReachUnavailable", "human_seen"]
