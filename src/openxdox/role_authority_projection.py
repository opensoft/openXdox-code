"""The role-and-authority projection (`split-opendox-two-layer-product` § 4.5,
design § D4 machinery (6); RULED ASK-3, `opensoft/openxFactory#656` comment
`5628886636` — launches first among 4.5's three named features, "contracts
already exist... no ruling needed").

WHAT THIS RENDERS. `docs/roles-and-authority.md` (`opensoft/openxFactory`,
ratified by `define-human-escalation-contract`, amended by
`add-github-app-identity-tiers`) and its own `roles-authority-model` capability
already own the cross-factory authority layers and the neutral Hermes-level
role table. Design § D4 names the gap in plain words: *"clinician of record,
licensed professional, launch approver; the contracts exist and the workbench
shows only a per-serve console token and a loopback verdict."* This module is
the projection that closes that gap — it reads the ALREADY-RATIFIED role table
and joins it, at request time, to the primitives every core route already
reaches through `self` (`route_extension.py`'s own "SAME PRIMITIVES are
REACHABLE" guarantee: "the loopback verdict, the capability dict, the resolved
actor, the console-host and console-token checks"), and renders NAMED roles
instead of a bare token. NO NEW DATA MODEL: every field below is either
transcribed from the neutral table in `docs/roles-and-authority.md` (the same
discipline `gate_console.Provenance` states for its own vocabulary — "the
READ-ONLY truth, transcribed and never invented") or lifted verbatim off the
request primitives the existing gate/projection columns already consume the
same way (`serve_gate.py`, `serve_projection.py`).

WHY THE DOMAIN-SPECIFIC LABELS DESIGN § D4 NAMES ARE NOT HARDCODED HERE, EVEN
THOUGH THE BOX TEXT NAMES THEM. `roles-authority-model`'s first requirement
binds `openxFactory` to express the neutral model "without any single domain's
execution roles, group names, or tooling" (`openspec/specs/roles-authority-
model/spec.md`), and task 4.4's own RULING C2 refuses exactly this failure one
column over: shipping one domain's words inside the shared, domain-neutral
package. "Clinician of record" is `MedxFactory`'s own instantiation of the
neutral model (design § D4's table, "promoting authority" row) — hardcoding it
into `openxdox` would be a NEW instance of the defect 4.4 exists to remove, not
a rendering of the neutral contract. So `layers()` below ships the NEUTRAL
Hermes-level roles (PO/PM/CA/PA/Merge Council/Merge Master) and accepts an
OPTIONAL `domain_labels` mapping instead: a future `domain-mapping-
declaration` "promoting authorities" axis (task 4.4, not yet built — no
schema/loader exists anywhere in the packet as of this writing) is the intended
supplier. Absent one, the projection still renders the neutral vocabulary
alone, on its own authority, rather than nothing and rather than guessing a
domain's words.

WHY THIS FILE DOES NOT NEED `gate_console.py` OR ANY BUILD-ARC COMPOSITION
POINT. Task 4.3 (the `profile_openxfactory` composition-point fix, RULED
ASK-2: a lazy proxy) is what wires a contributed route into the LIVE served
app; that ruling is dated AFTER this module's own claim and is a separate,
still-open box. This module supplies its half of the seam the same way
`serve_gate.py`/`serve_projection.py` already do — a `routes()` method
returning `RouteBinding`s — and is fully testable on its own terms (unit tests
over the pure `project()`/`layers()` functions, a seam-conformance test over
`.routes()`) without that wiring existing yet.
"""

from __future__ import annotations

import json
from collections.abc import Mapping as ABCMapping
from dataclasses import dataclass
from typing import Mapping, Optional

import route_extension  # noqa: E402  (bare top-level import — the seam module)

from opendox.serve_wire import JSON_CTYPE  # noqa: E402


@dataclass(frozen=True)
class AuthorityLayer:
    """One row of the neutral Hermes-level role table
    (`docs/roles-and-authority.md`, "Hermes-Level Roles"). `role_id`,
    `role_name` and `decides` are transcribed from that ratified table
    verbatim — never invented here. `domain_label` is the ONLY field this
    module ever fills from outside the neutral contract: an optional
    per-domain instantiation name a caller supplies (design § D4's "clinician
    of record", "licensed professional", "launch approver"), defaulted to
    `None` so the neutral row renders on its own when no domain profile is
    wired in yet (RULING C2)."""

    role_id: str
    role_name: str
    decides: str
    domain_label: Optional[str] = None

    def as_json(self) -> dict:
        return {
            "role_id": self.role_id,
            "role_name": self.role_name,
            "decides": self.decides,
            "domain_label": self.domain_label,
        }


#: The neutral Hermes-level role table, transcribed from
#: `docs/roles-and-authority.md` ("Hermes-Level Roles") — NOT this module's to
#: invent or extend; a new row here without a matching row landing in that
#: ratified document first would be a drift between the rendered projection
#: and the contract it renders, exactly the failure `Provenance`'s own
#: docstring warns against one column over. Declaration order is the
#: document's own table order.
NEUTRAL_LAYERS: tuple[tuple[str, str, str], ...] = (
    ("PO", "Project Owner",
     "what problem the feature solves, what is in or out of scope, whether "
     "behavior preserves product value"),
    ("PM", "Project Manager",
     "when work happens, how features are sequenced, who must be consulted "
     "or escalated"),
    ("CA", "Chief Architect",
     "which system owns a capability, how projects integrate, which "
     "contracts are canonical, whether repo design violates the system "
     "model"),
    ("PA", "Project Architect",
     "how one project should satisfy CA constraints, where project "
     "boundaries sit, whether project architecture remains coherent"),
    ("Merge Council", "Merge readiness body",
     "whether a domain work product is ready, not ready, or needs fixes "
     "before enforcement"),
    ("Merge Master", "Merge authority agent",
     "approve actions inside the low-risk envelope, park out-of-envelope "
     "actions for the human gate, or block"),
)


def layers(domain_labels: Optional[Mapping[str, str]] = None
           ) -> tuple[AuthorityLayer, ...]:
    """The neutral role table, each row optionally labelled by a domain
    profile.

    `domain_labels` keys on `role_id` (e.g. `{"CA": "clinician of record"}`
    for a future `MedxDox` profile) — a future `domain-mapping-declaration`
    "promoting authorities" axis (task 4.4) is the intended supplier; `None`
    or a missing key renders the neutral row alone, never a guessed domain
    word (RULING C2)."""
    resolved = domain_labels or {}
    return tuple(
        AuthorityLayer(role_id, role_name, decides, resolved.get(role_id))
        for role_id, role_name, decides in NEUTRAL_LAYERS
    )


def _flatten_truthy_grants(capabilities) -> tuple[str, ...]:
    """Every dotted path through `capabilities` whose leaf is truthy, sorted.

    `capabilities` is the SAME nested capability dict `serve_gate.py` reads
    one leaf of at a time (`self.capabilities.get("actions", {}).get("gate")`)
    — this walks the whole tree once instead of one hand-picked leaf, so a
    capability grant no existing column happens to gate on still surfaces in
    the projection. Sorted at every level so the result is stable across two
    calls with the same dict, never an accident of dict iteration order."""
    grants: list[str] = []

    def walk(node, prefix: str) -> None:
        if isinstance(node, ABCMapping):
            for key in sorted(node, key=str):
                walk(node[key], f"{prefix}.{key}" if prefix else str(key))
        elif node:
            grants.append(prefix)

    walk(capabilities or {}, "")
    return tuple(sorted(grants))


@dataclass(frozen=True)
class SessionAuthorityView:
    """What ONE request's caller may act as, replacing the bare console-token
    + loopback pair design § D4 names as today's whole surface.

    `console_token_present` and `loopback` are the SAME two facts the
    workbench already shows (unchanged meaning, not reinterpreted — see
    `project()`); `actor` and `capability_grants` are the other two
    primitives `route_extension.py`'s own docstring names as reachable
    through the same object every core route reaches. `layers` is the
    neutral table above, in ratified declaration order."""

    console_token_present: bool
    loopback: bool
    actor: Optional[str]
    capability_grants: tuple[str, ...]
    layers: tuple[AuthorityLayer, ...]

    def as_json(self, *, reveal_actor: bool) -> dict:
        """The wire shape the route below serves.

        `reveal_actor` is REQUIRED, not defaulted, so a caller must decide
        the redaction rule rather than inherit an accidental default that
        leaks an identity off-loopback — "belt and braces on the hosted
        plane" the same way `serve_projection._serve_index` redacts its own
        index document off-loopback (`hosted_index(document)`)."""
        return {
            "console_token_present": self.console_token_present,
            "loopback": self.loopback,
            "actor": self.actor if reveal_actor else None,
            "capability_grants": list(self.capability_grants),
            "layers": [layer.as_json() for layer in self.layers],
        }


def project(*, actor: Optional[str], capabilities,
            loopback: bool,
            domain_labels: Optional[Mapping[str, str]] = None
            ) -> SessionAuthorityView:
    """Build the projection from the request primitives.

    Pure — no I/O, no framework coupling — so every branch here is
    unit-testable directly and the route handler below is the only place
    this reaches `self`. `console_token_present` is derived from whether an
    actor was resolved at all: the same proxy `serve_gate.py:77`'s own gating
    already treats as load-bearing (`not self.capabilities...get("gate") or
    not self.actor`) — an actor resolves only after the gateway's own
    console-presence check has already run (`gate_console.py`'s
    `CONSOLE_PRESENCES` — console-token, tty, declared, or ingress-auth), so
    "an actor is resolved" and "console presence was shown" are the same
    fact observed from this side of the gateway. A more granular signal
    (which of the four presences fired) is a `Provenance`-shaped BUILD-arc
    refinement for task 4.3's composition point, once it exists — not
    invented here."""
    resolved_actor = actor if actor else None
    return SessionAuthorityView(
        console_token_present=resolved_actor is not None,
        loopback=bool(loopback),
        actor=resolved_actor,
        capability_grants=_flatten_truthy_grants(capabilities),
        layers=layers(domain_labels),
    )


#: The projection's route — an EXACT GET, not a prefix: one view, no
#: sub-paths. Does not sit under either declared prefix
#: (`ACTIONS_GATE_PREFIX = "/actions/gate/"`, `SOURCE_PREFIX = "/source/"`),
#: so `route_extension.collect_bindings` accepts it beside both (proved by
#: `tests/test_role_authority_projection_seam.py`).
ROLE_AUTHORITY_ROUTE = "/projections/role-authority"


class RoleAuthorityRoutes:
    """The role-and-authority projection's HTTP door, mixed into
    `DashboardHandler` the same way `GateRoutes`/`serve_projection`'s mixins
    are (once task 4.3's composition point wires it in): every `self.<name>`
    below resolves through the MRO to `serve.py`'s own core implementation,
    so this reaches the same actor/capabilities/loopback every core route
    reaches — `route_extension.py`'s own reachability guarantee, and the
    reason a contributed route is not a privileged one.
    """

    def _handle_role_authority_projection(self, head_only: bool) -> None:
        """`GET /projections/role-authority` — read-only and ungated beyond
        the same loopback-scoped redaction `serve_projection._serve_index`
        already applies to the snapshot index: the neutral role table and
        the console-token/loopback facts are always visible (they are the
        diagnostic the workbench already shows, unconditionally), and the
        resolved actor identity is revealed only on loopback — the same
        "belt and braces on the hosted plane" the projection column already
        keeps, not a new gating philosophy invented here."""
        view = project(
            actor=getattr(self, "actor", None),
            capabilities=getattr(self, "capabilities", {}) or {},
            loopback=bool(getattr(self, "loopback", False)),
        )
        document = view.as_json(reveal_actor=bool(getattr(self, "loopback", False)))
        body = json.dumps(document).encode("utf-8")
        self._serve_bytes(body, JSON_CTYPE, head_only)


class RoleAuthorityProjectionExtension:
    """openXdox's role-and-authority route contribution: the projection's one
    GET route, and nothing else. Conforms to
    `route_extension.RouteExtension` STRUCTURALLY, so this column imports
    nothing from the core it contributes to.
    """

    def routes(self) -> tuple[route_extension.RouteBinding, ...]:
        return (
            route_extension.RouteBinding("GET", ROLE_AUTHORITY_ROUTE, False,
                                         "_handle_role_authority_projection"),
        )
