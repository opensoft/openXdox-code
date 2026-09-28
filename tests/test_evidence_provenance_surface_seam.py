"""Seam-conformance: the evidence-and-provenance surface registers through
`route_extension` (`split-opendox-two-layer-product` § 2.4) exactly the way
`serve_gate.GateRoutesExtension`, `serve_projection.ProjectionRoutesExtension`
and `role_authority_projection.RoleAuthorityProjectionExtension` (§ 4.5
slice 1) already do, and does not collide with any of the three.

This is what "a route contribution through the § 2.4 seam" MEANS as a
tested property, independent of task 4.3's still-open composition-point
wiring: an extension that (a) structurally conforms to
`route_extension.RouteExtension`, (b) contributes bindings
`collect_bindings` accepts without a `RouteBindingError`, (c) whose handler
name RESOLVES to a real callable on the class it will be mixed into
(`resolve_handlers` — the "a route that cannot be served must not start"
refusal), and (d) that assembles cleanly beside the OTHER existing
contribution columns, in either declaration order — see
`tests/test_role_authority_projection_seam.py`'s own docstring, which states
this reasoning first.

(d) IS ASSERTED IN TWO PLACES, since plan 034 task T044. Beside role
authority alone, which needs nothing a lone checkout lacks, it is asserted
below. Beside the gate and projection columns it is asserted in
`tests/test_seam_assembly_beside_gate_and_projection.py`, because
`serve_projection` reaches openxFactory's `doc_health` when it is imported
(through `snapshot_registry`), which no lone checkout supplies. Those two
cases sat here behind a guard that skipped on every lone run, until T044 made
them assert for real and moved them. That file is in the declared exclusion
(`tests/declared_exclusion.yaml`) under `doc_health`. It runs wherever
`doc_health` is present, and everywhere else it is reported as an open
extraction.
"""

from __future__ import annotations

import route_extension

from openxdox.evidence_provenance_surface import (
    EVIDENCE_ROUTE,
    EvidenceProvenanceRoutes,
    EvidenceProvenanceSurfaceExtension,
)
from openxdox.role_authority_projection import (
    ROLE_AUTHORITY_ROUTE,
    RoleAuthorityProjectionExtension,
)


def test_extension_conforms_structurally_to_route_extension() -> None:
    # runtime_checkable Protocol: conformance by having the method, no
    # inheritance from route_extension needed (and none exists — the module
    # imports nothing from the core it contributes to).
    assert isinstance(EvidenceProvenanceSurfaceExtension(), route_extension.RouteExtension)


def test_collect_bindings_accepts_the_extension_alone() -> None:
    bindings = route_extension.collect_bindings([EvidenceProvenanceSurfaceExtension()])
    assert len(bindings) == 1
    assert bindings[0].pattern == EVIDENCE_ROUTE


def test_handler_name_resolves_on_the_mixin_class() -> None:
    bindings = route_extension.collect_bindings([EvidenceProvenanceSurfaceExtension()])
    route_extension.resolve_handlers(bindings, EvidenceProvenanceRoutes)  # must not raise


def test_assembles_beside_role_authority_alone() -> None:
    # Neither § 4.5 feature reaches doc_health, so this pair is asserted
    # unconditionally, here. The fuller assembly that also brings in the
    # gate/projection columns is in
    # `tests/test_seam_assembly_beside_gate_and_projection.py` (plan 034 T044).
    extensions = [RoleAuthorityProjectionExtension(), EvidenceProvenanceSurfaceExtension()]
    bindings = route_extension.collect_bindings(extensions)
    assert len(bindings) == 2
    assert {b.pattern for b in bindings} == {ROLE_AUTHORITY_ROUTE, EVIDENCE_ROUTE}


def test_evidence_route_does_not_sit_under_either_declared_prefix() -> None:
    # Belt and braces beyond the collect_bindings proof above: the pattern
    # itself must not share either prefix's namespace, so a future prefix
    # declared alongside "/source/" or "/actions/gate/" can never
    # retroactively swallow this route. Since § 3.4 slice S6 `/source/` is
    # `opendox/serve.py`'s CORE prefix rather than this column's contributed
    # one, which makes the check more necessary and not less: a contributed
    # route must not sit under a core prefix either, and `collect_bindings`
    # never sees the core arms to refuse it.
    assert not EVIDENCE_ROUTE.startswith("/source/")
    assert not EVIDENCE_ROUTE.startswith("/actions/gate/")


def test_evidence_route_is_distinct_from_role_authority_route() -> None:
    assert EVIDENCE_ROUTE != ROLE_AUTHORITY_ROUTE


def test_getting_the_binding_via_match_reaches_the_right_handler() -> None:
    # match() is the actual per-request dispatch primitive; exercising it
    # end-to-end (pattern in, handler name out) is the closest this suite
    # gets to a live request without the real server.
    bindings = route_extension.collect_bindings([EvidenceProvenanceSurfaceExtension()])
    hit = route_extension.match(bindings, "GET", EVIDENCE_ROUTE)
    assert hit is not None
    binding, remainder = hit
    assert binding.handler == "_handle_evidence_provenance_surface"
    assert remainder == ""


def test_head_request_also_matches_the_get_binding() -> None:
    # "A GET binding answers both GET and HEAD" (route_extension.py's own
    # docstring) — this projection is a plain read, so HEAD must resolve
    # exactly as GET does.
    bindings = route_extension.collect_bindings([EvidenceProvenanceSurfaceExtension()])
    hit = route_extension.match(bindings, "HEAD", EVIDENCE_ROUTE)
    assert hit is not None
