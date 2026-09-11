"""The model/scenario workbench (`split-opendox-two-layer-product` § 4.5,
design § D4 machinery (5); RULED ASK-3, `opensoft/openxFactory#656` comment
`5628886636` — the LAST of 4.5's three named features, authored after the
role-and-authority projection (`#10`, machinery (6)) and the
evidence-and-provenance surface (`#11`, machinery (4)) landed in the order
that ruling fixed).

WHAT THIS RENDERS, AND WHY IT IS THE CENTRE OF GRAVITY. Design § D4's
extraction of the seven machineries common to every domain mapping names
this one in full: *"(5) The MODEL/SCENARIO WORKBENCH — a `model` member and
an optional `scenario` member, a declared scope and isolation boundary, a
truth store the model may never write, output confined to
`hypothesis_proposed | no_signal | discarded`, and a named human promoting
authority. **It exists nowhere in the 80,000 lines and it is openXdox's
centre of gravity** — which changes the character of the work from 'carve'
to 'carve and build'."* Five named elements, and this module renders exactly
those five and stops:

  1. the family's `role: model` members and its OPTIONAL `role: scenario`
     members, separated rather than listed together — the optionality is a
     declared property of the family (`governed-derived-model`'s
     "Conformance declaration" requirement: *"Scenario members are optional;
     model members are not"*), and a bench that flattened the two roles into
     one list would render a model-only family and a model+scenario family
     identically;
  2. the declared `scope` and, where `scope: subject`, the
     `isolation_boundary` the same requirement pairs with it
     (*"a conforming family SHALL declare `scope: domain | subject` … THEN
     the declaration names the isolation boundary (e.g. per_advertiser,
     per_client)"*);
  3. the truth store the model may never write — the family's declared
     `truth_store` and `truth_store_class` JOINED to each member's own
     `truth_store_access` binding, which is the one join neither sibling
     surface makes: `role_authority_projection` renders no family data at
     all and `evidence_provenance_surface` deliberately left "the family's
     other four dials (identity, scope, truth store, promoting authority)"
     to "a different surface's concern — the model/scenario workbench,
     design § D4 machinery (5)" (its own `EvidenceFamily` docstring, landed
     at `427230c3`). This module is that surface, and the four dials it
     names are the four rendered here;
  4. the confinement of scenario output — the member's declared
     `output_status_field` alongside `HYPOTHESIS_OUTPUT_STATUSES`, the enum
     `governed-derived-model`'s "Human-gated promotion" requirement fixes
     (*"A conforming scenario member SHALL express outputs only as
     hypotheses (`hypothesis_proposed | no_signal | discarded`)"*), plus the
     member's `action_authority` bindings, which are how "Read-only truth
     store and zero action authority" makes an external act unrepresentable
     rather than merely disallowed;
  5. the named human promoting authority — the family's
     `promoting_authority` dial, which that same requirement makes the only
     route by which "any hypothesis becomes action or truth".

WHERE THE DATA COMES FROM. NO NEW DATA MODEL, NO INVENTED FIELD NAMES — the
identical discipline slices 1 and 2 established and the only discipline that
keeps three renderers of one contract from becoming three divergent readings
of it. Every field below is named by
`contracts/schemas/xfactory-derived-model-conformance.schema.yaml`
(`opensoft/openxFactory`), and the ratified `medx-governed` /
`ledgerx-calibrated` declarations
(`examples/derived-models/{medx-governed,ledgerx-calibrated}/
declaration.example.yaml`) are worked instances of it. `project()` takes that
`xfactory_derived_model_conformance` document ALREADY PARSED into a plain
mapping, as its one optional argument — "the caller supplies it, this module
never invents it", after
`role_authority_projection.layers(domain_labels=...)` and
`evidence_provenance_surface.project(declaration=...)`.

WHAT THIS DELIBERATELY DOES NOT RENDER. The `provenance` block: that is
machinery (4)'s, rendered by `evidence_provenance_surface` and NOT
duplicated here — two renderings of one declaration that could drift apart
is precisely the defect the "never copied" rule below exists to prevent, and
a bench reader who wants provenance asks the evidence surface for it. The
`identity` / `person_modeling` / `calibration_*` dials are likewise left
alone: `identity` and `person_modeling` are the two dials D4 machinery (5)
does not name, and `calibration_writer`/`calibration_source` belong to the
calibrated tier's own separate requirement. `tier` IS carried, as an
identifying field only — the same role it plays in `EvidenceFamily` — since
a bench station that did not say whether it was reading a `governed` or a
`calibrated` family would be ambiguous about which requirements even apply
to it.

WHY THIS MODULE COMPUTES NO CONFORMANCE VERDICT. The schema's own header
comment states that its deep template checks — including, verbatim,
*"scenario members' output status enum is exactly
hypothesis_proposed|no_signal|discarded"* and *"access bindings resolve as
single-value field locks or present gates"* — live in "the canonical
validator (`scripts/validate-derived-models.py`), never copied." Those two
are EXACTLY the checks a workbench is most tempted to re-derive, because
they are the two invariants it renders most prominently. It does not: this
module transcribes what the declaration says and renders
`HYPOTHESIS_OUTPUT_STATUSES` beside it as the CONTRACT's enum, so a reader
can see the confinement without this module ever opening a template file or
pronouncing on whether a given template honours it. A second, divergent
implementation of a validation rule is a worse defect than an unrendered
one, and a rendered `None` — a member declaring no `output_status_field`,
a family declaring no `promoting_authority` — is an honest rendering of
"nothing declared yet", not this module's place to flag as wrong.

WHY THIS FILE DOES NOT NEED `gate_console.py` OR ANY BUILD-ARC COMPOSITION
POINT. The reasoning `role_authority_projection.py` and
`evidence_provenance_surface.py` each give for themselves, unchanged: task
4.3's `profile_openxfactory` composition point (RULED ASK-2, a lazy proxy)
is what will eventually hand a LIVE domain's declaration to a served
request; that wiring is a separate, still-open box. Until it lands the
handler below reads whatever `self.derived_model_conformance` that
composition point will one day set — the SAME attribute name
`evidence_provenance_surface` already reads, because both surfaces render
one document and a second attribute for the same document would be a second
thing for the composition point to remember to set — defaulting to an empty
document when the attribute is absent. `project()`/`as_json()` are fully
unit-testable now regardless, and the route contribution is
seam-conformance-tested the way both siblings' are (see
`tests/test_model_scenario_workbench_seam.py`).
"""

from __future__ import annotations

import json
from collections.abc import Mapping as ABCMapping
from dataclasses import dataclass
from typing import Mapping, Optional

import route_extension  # noqa: E402  (bare top-level import — the seam module)

from opendox.serve_wire import JSON_CTYPE  # noqa: E402

#: The output enum `governed-derived-model`'s "Human-gated promotion"
#: requirement fixes for every conforming scenario member, transcribed
#: verbatim from that requirement (and restated identically in the
#: conformance schema's own header comment). NEVER extended or reordered
#: here: a fourth status is a change to that ratified requirement, not a
#: rendering choice this module gets to make, and the bench renders this
#: tuple precisely so a reader sees the confinement WITHOUT this module
#: having to open a template and judge one.
HYPOTHESIS_OUTPUT_STATUSES: tuple[str, ...] = (
    "hypothesis_proposed",
    "no_signal",
    "discarded",
)

#: The two member roles the schema's `members[].role` enum allows. Model
#: members are required and scenario members are optional
#: (`governed-derived-model`, "Conformance declaration"), which is why the
#: bench station below keeps them in two separate tuples rather than one.
MODEL_ROLE = "model"
SCENARIO_ROLE = "scenario"

#: The workbench's route — an EXACT GET, the same shape as
#: `role_authority_projection.ROLE_AUTHORITY_ROUTE` and
#: `evidence_provenance_surface.EVIDENCE_ROUTE`: one view, no sub-paths.
#: Sits under NEITHER declared prefix (`ACTIONS_GATE_PREFIX =
#: "/actions/gate/"`, `SOURCE_PREFIX = "/source/"`) and is distinct from both
#: sibling projection routes, so `route_extension.collect_bindings` accepts
#: it beside all four existing columns (proved by
#: `tests/test_model_scenario_workbench_seam.py`).
WORKBENCH_ROUTE = "/projections/workbench"


@dataclass(frozen=True)
class AccessBinding:
    """One declared access binding, transcribed as the schema allows it to be
    written: EITHER a single-value field lock (`{field, value}`) OR a named
    gate (`{gate: …}`). The schema describes `truth_store_access` as exactly
    that either/or — *"a single-value field lock {field, value: read_only} or
    a declared gate {gate: <gate name/id>}"* — and `action_authority` as the
    same shape (*"{field, value: none} or {gate: ...}"*), so ONE class serves
    both and the two forms are rendered as the declaration wrote them rather
    than normalized into a single invented shape.

    All three fields are `Optional` and none is cross-checked against
    another: a binding declaring neither form, or both, is rendered exactly
    as declared. Whether a binding "resolves" is the canonical validator's
    judgment (see the module docstring), never this renderer's."""

    field: Optional[str] = None
    value: Optional[str] = None
    gate: Optional[str] = None

    def as_json(self) -> dict:
        return {"field": self.field, "value": self.value, "gate": self.gate}


@dataclass(frozen=True)
class BenchMember:
    """One declared family member on the bench — a `role: model` or
    `role: scenario` object — carrying what D4 machinery (5) names about a
    member and nothing else.

    `output_status_field` is the scenario member's declared field whose enum
    the contract confines to `HYPOTHESIS_OUTPUT_STATUSES`; it is `None` on a
    model member because the schema only describes it for scenario members,
    and `None` on a scenario member that declares none — the same honest
    "nothing declared yet" a `None` means everywhere in this module.
    `provenance` is absent BY DESIGN: it is machinery (4)'s, rendered by
    `evidence_provenance_surface`."""

    role: str
    kind: str
    template: Optional[str]
    truth_store_access: Optional[AccessBinding]
    action_authority: tuple[AccessBinding, ...]
    output_status_field: Optional[str]

    def as_json(self) -> dict:
        return {
            "role": self.role,
            "kind": self.kind,
            "template": self.template,
            "truth_store_access": (
                self.truth_store_access.as_json()
                if self.truth_store_access is not None else None
            ),
            "action_authority": [b.as_json() for b in self.action_authority],
            "output_status_field": self.output_status_field,
        }


@dataclass(frozen=True)
class BenchStation:
    """ONE declared family, rendered as one station of the workbench: its
    model members, its optional scenario members, and the four dials D4
    machinery (5) names around them — scope (with its isolation boundary),
    the truth store (with its class) the model may never write, and the
    named human promoting authority.

    `model_members` and `scenario_members` are separate tuples, each in
    declaration order, because the optionality of the second is a contract
    property a reader must be able to see at a glance (a model-only family
    renders an empty `scenario_members`, which is VALID — "the declaration
    is valid and scenario invariants are not required" — and not a defect
    this station flags)."""

    family_id: str
    display_name: Optional[str]
    tier: Optional[str]
    scope: Optional[str]
    isolation_boundary: Optional[str]
    truth_store: Optional[str]
    truth_store_class: Optional[str]
    promoting_authority: Optional[str]
    model_members: tuple[BenchMember, ...]
    scenario_members: tuple[BenchMember, ...]

    def as_json(self) -> dict:
        return {
            "family_id": self.family_id,
            "display_name": self.display_name,
            "tier": self.tier,
            "scope": self.scope,
            "isolation_boundary": self.isolation_boundary,
            "truth_store": self.truth_store,
            "truth_store_class": self.truth_store_class,
            "promoting_authority": self.promoting_authority,
            "model_members": [m.as_json() for m in self.model_members],
            "scenario_members": [m.as_json() for m in self.scenario_members],
        }


@dataclass(frozen=True)
class WorkbenchView:
    """The whole bench: one domain's declared families as stations, in
    declaration order, plus the output enum the contract confines every
    scenario's outputs to.

    `hypothesis_output_statuses` is rendered ONCE at the top rather than
    repeated per station because it is a property of the CONTRACT, not of
    any one domain's declaration — a domain cannot declare a fourth status,
    and a per-station copy would invite exactly the misreading that it
    could."""

    domain_id: Optional[str]
    hypothesis_output_statuses: tuple[str, ...]
    stations: tuple[BenchStation, ...]

    def as_json(self) -> dict:
        return {
            "domain_id": self.domain_id,
            "hypothesis_output_statuses": list(self.hypothesis_output_statuses),
            "stations": [station.as_json() for station in self.stations],
        }


def _access_binding(raw) -> Optional[AccessBinding]:
    """One `{field, value}` / `{gate: …}` mapping as an `AccessBinding`, or
    `None` where the declaration carries nothing at all. A non-mapping value
    also renders `None` rather than raising: this module reads a document it
    did not write and does not own the judgment that a malformed declaration
    is malformed (the canonical validator does), so it renders "nothing
    legible declared" instead of refusing to render the rest of the bench."""
    if not isinstance(raw, ABCMapping):
        return None
    return AccessBinding(
        field=raw.get("field"),
        value=raw.get("value"),
        gate=raw.get("gate"),
    )


def _member(raw: Mapping) -> BenchMember:
    action_authority = tuple(
        binding for binding in (
            _access_binding(entry) for entry in (raw.get("action_authority") or [])
        )
        if binding is not None
    )
    return BenchMember(
        role=raw.get("role", ""),
        kind=raw.get("kind", ""),
        template=raw.get("template"),
        truth_store_access=_access_binding(raw.get("truth_store_access")),
        action_authority=action_authority,
        output_status_field=raw.get("output_status_field"),
    )


def _station(raw: Mapping) -> BenchStation:
    dials = raw.get("dials")
    if not isinstance(dials, ABCMapping):
        dials = {}
    members = [
        _member(entry) for entry in (raw.get("members") or [])
        if isinstance(entry, ABCMapping)
    ]
    return BenchStation(
        family_id=raw.get("id", ""),
        display_name=raw.get("display_name"),
        tier=raw.get("tier"),
        scope=dials.get("scope"),
        isolation_boundary=dials.get("isolation_boundary"),
        truth_store=dials.get("truth_store"),
        truth_store_class=dials.get("truth_store_class"),
        promoting_authority=dials.get("promoting_authority"),
        model_members=tuple(m for m in members if m.role == MODEL_ROLE),
        scenario_members=tuple(m for m in members if m.role == SCENARIO_ROLE),
    )


def project(declaration: Optional[Mapping] = None) -> WorkbenchView:
    """Build the workbench view from an `xfactory_derived_model_conformance`
    document, already parsed (e.g. from YAML) into a plain mapping.

    Pure — no I/O, no framework coupling, no reach into `opendox` or
    `doc_health` — so every branch here is unit-testable directly and the
    route handler below is the only place this reaches `self`.

    `declaration=None` (or a mapping with no `families`) renders an empty
    bench — "no domain profile wired in yet", the same choice
    `evidence_provenance_surface.project(None)` and
    `role_authority_projection.layers(None)` make — rather than raising or
    fabricating a family that was never declared. A member whose `role` is
    neither `model` nor `scenario` appears in NEITHER tuple: the schema's
    enum admits exactly two, and inventing a third bucket for an
    out-of-enum value would be this module ruling on a declaration it does
    not validate."""
    doc = declaration or {}
    domain = doc.get("domain")
    if not isinstance(domain, ABCMapping):
        domain = {}
    stations = tuple(
        _station(raw) for raw in (doc.get("families") or [])
        if isinstance(raw, ABCMapping)
    )
    return WorkbenchView(
        domain_id=domain.get("id"),
        hypothesis_output_statuses=HYPOTHESIS_OUTPUT_STATUSES,
        stations=stations,
    )


class ModelScenarioWorkbenchRoutes:
    """The workbench's HTTP door, mixed into `DashboardHandler` the same way
    `RoleAuthorityRoutes`/`EvidenceProvenanceRoutes`/`GateRoutes`/
    `serve_projection`'s mixins are (once task 4.3's composition point wires
    it in): every `self.<name>` below resolves through the MRO to
    `serve.py`'s own core implementation.
    """

    def _handle_model_scenario_workbench(self, head_only: bool) -> None:
        """`GET /projections/workbench` — read-only and ALWAYS visible, for
        the reason `EvidenceProvenanceRoutes` gives for its own surface:
        nothing rendered here is an actor identity or any other
        loopback-scoped fact. A domain's declared scope, truth store, output
        field name and promoting-authority ROLE are contract facts about the
        domain's own model family, not about whoever is reading them, so the
        redaction rule `role_authority_projection` applies to a resolved
        actor has nothing to bite on here."""
        declaration = getattr(self, "derived_model_conformance", None)
        view = project(declaration)
        body = json.dumps(view.as_json()).encode("utf-8")
        self._serve_bytes(body, JSON_CTYPE, head_only)


class ModelScenarioWorkbenchExtension:
    """openXdox's model/scenario workbench route contribution: the bench's
    one GET route, and nothing else. Conforms to
    `route_extension.RouteExtension` STRUCTURALLY, so this column imports
    nothing from the core it contributes to.
    """

    def routes(self) -> tuple[route_extension.RouteBinding, ...]:
        return (
            route_extension.RouteBinding("GET", WORKBENCH_ROUTE, False,
                                         "_handle_model_scenario_workbench"),
        )
