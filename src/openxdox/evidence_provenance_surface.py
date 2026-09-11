"""The evidence-and-provenance surface (`split-opendox-two-layer-product` §
4.5, design § D4 machinery (4); RULED ASK-3, `opensoft/openxFactory#656`
comment `5628886636` — second of 4.5's three named features, claimed at
comment `5632730583` immediately after slice 1 (the role-and-authority
projection, `#10`, comment `5629174144`) named this as ASK-3's next
successor).

WHAT THIS RENDERS. `governed-derived-model`'s own Purpose section
(`opensoft/openxFactory` `openspec/specs/governed-derived-model/spec.md`)
states the invariants in order, structural rather than advisory; the second
is *"every fact carrying provenance or a declared assumption"* — spelled out
in full as the "Full provenance" requirement: *"A conforming model object
SHALL tag every fact with provenance — an evidence trace with source
references, or a declared assumption in a required assumption register —
and a domain MAY instead forbid assumptions entirely by declaring the
assumptions-forbidden form (evidence trace with minimum one item plus a
single-value no-invented-facts enum)."* Design § D4 machinery (4) names the
gap in plain words: *"a chart citation, a ledger tie-out and an attribution
chain are ONE machinery over different nouns; `governed-derived-model`
invariant 2 is the contract and nothing renders it."* This module is that
renderer, and nothing more: it does not touch invariant 2's siblings (the
non-authoritative enum, the read-only truth store, the human-gated
promotion) — those belong to the model/scenario workbench (machinery (5),
`split-opendox-two-layer-product` § 4.5's third and largest feature), not to
this one.

WHERE THE DATA COMES FROM. NO NEW DATA MODEL, NO INVENTED FIELD NAMES. Every
domain factory already declares this shape in its own
`models/derived-model-conformance.yaml`, one
`xfactory_derived_model_conformance` document per
`contracts/schemas/xfactory-derived-model-conformance.schema.yaml`
(`opensoft/openxFactory`) — the ratified `medx-governed` and
`ledgerx-calibrated` fixtures
(`examples/derived-models/{medx-governed,ledgerx-calibrated}/
declaration.example.yaml`) are worked instances of it. `project()` below
takes that document, ALREADY PARSED into a plain mapping, as its one
optional argument — the same "caller supplies it, this module never invents
it" discipline `role_authority_projection.layers(domain_labels=...)`
established for § 4.5's first feature — and reads out, per declared FAMILY
and per `role: model` MEMBER, exactly the three `provenance` sub-fields the
schema names (`evidence_field`, `assumption_register_field`,
`invented_facts_field`) under whichever `form` the domain declared
(`assumption_register` or `assumptions_forbidden`). `scenario`-role members
carry no `provenance` block in the schema — invariant 2 binds MODEL objects;
a scenario's own human-gated-promotion invariant is a different requirement
entirely — and are not rendered here.

WHY THIS MODULE COMPUTES NO CONFORMANCE VERDICT. The schema's own header
comment is explicit that its deep template checks — "assumption-register
field present, or the assumptions-forbidden pair: evidence field
required/min 1 + single-value invented-facts `[none]`" — live in "the
canonical validator (`scripts/validate-derived-models.py`), never copied."
Re-deriving any part of that judgment here would be exactly the copy the
schema's own comment refuses, and a second, divergent implementation of a
validation rule is a worse defect than the gap this module closes. So
`EvidenceBinding` below transcribes the declared fields VERBATIM — including
a `form` of `None` where a model member declares no `provenance` block at
all, which is itself an honest rendering of "nothing declared yet" and not
this module's place to flag as wrong.

WHY THIS FILE DOES NOT NEED `gate_console.py` OR ANY BUILD-ARC COMPOSITION
POINT. The same reasoning `role_authority_projection.py` gives for itself:
task 4.3's `profile_openxfactory` composition point (RULED ASK-2, a lazy
proxy) is what will eventually hand a LIVE domain's declaration to a served
request; that wiring is a separate, still-open box. Until it lands, the
handler below reads whatever `self.derived_model_conformance` a future
composition point will one day set, defaulting to an empty document when
the attribute is absent — rendering "no domain profile wired in yet"
honestly, the same choice `layers()` made for `domain_labels=None` — rather
than fabricating a family that was never declared. `project()`/`as_json()`
are fully unit-testable now regardless, and the route contribution is
seam-conformance-tested the same way § 4.5 slice 1's is (see
`tests/test_evidence_provenance_surface_seam.py`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping, Optional

import route_extension  # noqa: E402  (bare top-level import — the seam module)

from opendox.serve_wire import JSON_CTYPE  # noqa: E402

#: The two provenance forms `governed-derived-model`'s "Full provenance"
#: requirement names, transcribed from
#: `contracts/schemas/xfactory-derived-model-conformance.schema.yaml`
#: (`families[].members[].provenance.form` enum) — never extended here: a
#: third form is a schema change upstream, not a rendering choice this
#: module gets to make.
ASSUMPTION_REGISTER_FORM = "assumption_register"
ASSUMPTIONS_FORBIDDEN_FORM = "assumptions_forbidden"

#: The projection's route — an EXACT GET, the same shape as
#: `role_authority_projection.ROLE_AUTHORITY_ROUTE`: one view, no sub-paths.
#: Does not sit under either declared prefix (`ACTIONS_GATE_PREFIX =
#: "/actions/gate/"`, `SOURCE_PREFIX = "/source/"`) and is distinct from
#: `ROLE_AUTHORITY_ROUTE`, so `route_extension.collect_bindings` accepts it
#: beside all three (proved by
#: `tests/test_evidence_provenance_surface_seam.py`).
EVIDENCE_ROUTE = "/projections/evidence"


@dataclass(frozen=True)
class EvidenceBinding:
    """One `role: model` family member's provenance binding, transcribed
    from its `xfactory_derived_model_conformance` declaration — never
    invented, never validated here (see the module docstring's "no
    conformance verdict" section). `form` is `None` where the declaration
    carries no `provenance` block at all; the three field names are `None`
    wherever the declaration omits them, regardless of `form` — this class
    reports exactly what is present, not what a given `form` implies ought
    to be present."""

    family_id: str
    member_kind: str
    form: Optional[str]
    evidence_field: Optional[str]
    assumption_register_field: Optional[str]
    invented_facts_field: Optional[str]

    def as_json(self) -> dict:
        return {
            "family_id": self.family_id,
            "member_kind": self.member_kind,
            "form": self.form,
            "evidence_field": self.evidence_field,
            "assumption_register_field": self.assumption_register_field,
            "invented_facts_field": self.invented_facts_field,
        }


@dataclass(frozen=True)
class EvidenceFamily:
    """One declared derived-model family, carrying only the identifying
    fields (`id`, `display_name`, `tier`) a reader needs to place its
    member bindings in context. The family's other four dials (identity,
    scope, truth store, promoting authority) are a different surface's
    concern — the model/scenario workbench, design § D4 machinery (5) — not
    this one's."""

    family_id: str
    display_name: Optional[str]
    tier: Optional[str]
    members: tuple[EvidenceBinding, ...]

    def as_json(self) -> dict:
        return {
            "family_id": self.family_id,
            "display_name": self.display_name,
            "tier": self.tier,
            "members": [member.as_json() for member in self.members],
        }


@dataclass(frozen=True)
class EvidenceProvenanceView:
    """The whole rendered surface: one domain's declared families, each
    with its `role: model` members' provenance bindings, in declaration
    order."""

    domain_id: Optional[str]
    families: tuple[EvidenceFamily, ...]

    def as_json(self) -> dict:
        return {
            "domain_id": self.domain_id,
            "families": [family.as_json() for family in self.families],
        }


def _member_binding(family_id: str, member: Mapping) -> Optional[EvidenceBinding]:
    """One `role: model` member's `EvidenceBinding`, or `None` for any other
    role. `scenario` carries no `provenance` block anywhere in the schema —
    invariant 2 binds model objects only — so a scenario member is excluded
    rather than rendered with an all-`None` binding that could be misread as
    a declared-but-empty provenance."""
    if member.get("role") != "model":
        return None
    provenance = member.get("provenance") or {}
    return EvidenceBinding(
        family_id=family_id,
        member_kind=member.get("kind", ""),
        form=provenance.get("form"),
        evidence_field=provenance.get("evidence_field"),
        assumption_register_field=provenance.get("assumption_register_field"),
        invented_facts_field=provenance.get("invented_facts_field"),
    )


def _family(raw: Mapping) -> EvidenceFamily:
    family_id = raw.get("id", "")
    members = tuple(
        binding for binding in (
            _member_binding(family_id, member) for member in (raw.get("members") or [])
        )
        if binding is not None
    )
    return EvidenceFamily(
        family_id=family_id,
        display_name=raw.get("display_name"),
        tier=raw.get("tier"),
        members=members,
    )


def project(declaration: Optional[Mapping] = None) -> EvidenceProvenanceView:
    """Build the projection from an `xfactory_derived_model_conformance`
    document, already parsed (e.g. from YAML) into a plain mapping.

    Pure — no I/O, no framework coupling, no reach into `opendox` or
    `doc_health` — so every branch here is unit-testable directly and the
    route handler below is the only place this reaches `self`.

    `declaration=None` (or a mapping with no `families`) renders an empty
    view — "no domain profile wired in yet", the same choice
    `role_authority_projection.layers(domain_labels=None)` makes for its own
    optional caller-supplied input — rather than raising or fabricating a
    family that was never declared."""
    doc = declaration or {}
    domain = doc.get("domain") or {}
    families = tuple(_family(raw) for raw in (doc.get("families") or []))
    return EvidenceProvenanceView(domain_id=domain.get("id"), families=families)


class EvidenceProvenanceRoutes:
    """The evidence-and-provenance surface's HTTP door, mixed into
    `DashboardHandler` the same way `RoleAuthorityRoutes`/`GateRoutes`/
    `serve_projection`'s mixins are (once task 4.3's composition point wires
    it in): every `self.<name>` below resolves through the MRO to
    `serve.py`'s own core implementation.
    """

    def _handle_evidence_provenance_surface(self, head_only: bool) -> None:
        """`GET /projections/evidence` — read-only and ALWAYS visible: unlike
        the role-and-authority projection, nothing this surface renders is
        an actor identity or any other loopback-scoped fact (a domain's
        declared field NAMES for its own evidence/assumption bindings carry
        no one's identity), so no redaction rule applies here."""
        declaration = getattr(self, "derived_model_conformance", None)
        view = project(declaration)
        body = json.dumps(view.as_json()).encode("utf-8")
        self._serve_bytes(body, JSON_CTYPE, head_only)


class EvidenceProvenanceSurfaceExtension:
    """openXdox's evidence-and-provenance route contribution: the
    projection's one GET route, and nothing else. Conforms to
    `route_extension.RouteExtension` STRUCTURALLY, so this column imports
    nothing from the core it contributes to.
    """

    def routes(self) -> tuple[route_extension.RouteBinding, ...]:
        return (
            route_extension.RouteBinding("GET", EVIDENCE_ROUTE, False,
                                         "_handle_evidence_provenance_surface"),
        )
