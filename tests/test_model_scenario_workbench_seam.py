"""Seam-conformance: the model/scenario workbench registers through
`route_extension` (`split-opendox-two-layer-product` § 2.4) exactly the way
`serve_gate.GateRoutesExtension`, `serve_projection.ProjectionRoutesExtension`,
`role_authority_projection.RoleAuthorityProjectionExtension` (§ 4.5 slice 1)
and `evidence_provenance_surface.EvidenceProvenanceSurfaceExtension` (§ 4.5
slice 2) already do, and does not collide with any of the four.

This is what "a route contribution through the § 2.4 seam" MEANS as a tested
property, independent of task 4.3's still-open composition-point wiring: an
extension that (a) structurally conforms to `route_extension.RouteExtension`,
(b) contributes bindings `collect_bindings` accepts without a
`RouteBindingError`, (c) whose handler name RESOLVES to a real callable on
the class it will be mixed into (`resolve_handlers` — the "a route that
cannot be served must not start" refusal), and (d) that assembles cleanly
beside the OTHER existing contribution columns, in either declaration order
— see `tests/test_role_authority_projection_seam.py`'s own docstring, which
states this reasoning first, and
`tests/test_evidence_provenance_surface_seam.py`, which restates it for the
second slice.

WITH THIS SLICE THE ASSEMBLY IS COMPLETE for § 4.5: all three features D4
names as openXdox's unbuilt centre of gravity now contribute a route
through the one seam, and the full five-column assembly is the first test
anywhere that proves all of them fit together. Since plan 034 task T044 that
assembly is in `tests/test_seam_assembly_beside_gate_and_projection.py`.

(d) IS ASSERTED IN TWO PLACES, since T044. Beside the other two § 4.5
features, which need nothing a lone checkout lacks, it is asserted below.
Beside the gate and projection columns it is asserted in that file, because
`serve_projection` reached openxFactory's `doc_health` when it was imported
(through `snapshot_registry`), which no lone checkout supplies. Those two
cases sat here behind a guard that skipped on every lone run, until T044 made
them assert for real and moved them. That file was in the declared exclusion
(`tests/declared_exclusion.yaml`) under `doc_health` until plan 034 T059 moved
`snapshot_registry`'s one `doc_health` read out of its module level. It runs
in this leg's required check now.
"""

from __future__ import annotations

import route_extension

from openxdox.evidence_provenance_surface import (
    EVIDENCE_ROUTE,
    EvidenceProvenanceSurfaceExtension,
)
from openxdox.model_scenario_workbench import (
    WORKBENCH_ROUTE,
    ModelScenarioWorkbenchExtension,
    ModelScenarioWorkbenchRoutes,
)
from openxdox.role_authority_projection import (
    ROLE_AUTHORITY_ROUTE,
    RoleAuthorityProjectionExtension,
)


def test_extension_conforms_structurally_to_route_extension() -> None:
    # runtime_checkable Protocol: conformance by having the method, no
    # inheritance from route_extension needed (and none exists — the module
    # imports nothing from the core it contributes to).
    assert isinstance(ModelScenarioWorkbenchExtension(), route_extension.RouteExtension)


def test_collect_bindings_accepts_the_extension_alone() -> None:
    bindings = route_extension.collect_bindings([ModelScenarioWorkbenchExtension()])
    assert len(bindings) == 1
    assert bindings[0].pattern == WORKBENCH_ROUTE


def test_handler_name_resolves_on_the_mixin_class() -> None:
    bindings = route_extension.collect_bindings([ModelScenarioWorkbenchExtension()])
    route_extension.resolve_handlers(bindings, ModelScenarioWorkbenchRoutes)  # must not raise


def test_assembles_beside_both_section_4_5_siblings() -> None:
    # None of the three § 4.5 features reaches doc_health, so this trio is
    # asserted unconditionally, here. The fuller assembly that also brings in
    # the gate/projection columns is in
    # `tests/test_seam_assembly_beside_gate_and_projection.py` (plan 034
    # T044). Three bindings, three distinct exact routes: § 4.5's whole build
    # content, assembled.
    extensions = [
        RoleAuthorityProjectionExtension(),
        EvidenceProvenanceSurfaceExtension(),
        ModelScenarioWorkbenchExtension(),
    ]
    bindings = route_extension.collect_bindings(extensions)
    assert len(bindings) == 3
    assert {b.pattern for b in bindings} == {
        ROLE_AUTHORITY_ROUTE, EVIDENCE_ROUTE, WORKBENCH_ROUTE}


def test_workbench_route_does_not_sit_under_either_declared_prefix() -> None:
    # Belt and braces beyond the collect_bindings proof above: the pattern
    # itself must not share either prefix's namespace, so a future prefix
    # declared alongside "/source/" or "/actions/gate/" can never
    # retroactively swallow this route. Since § 3.4 slice S6 `/source/` is
    # `opendox/serve.py`'s CORE prefix rather than this column's contributed
    # one, which makes the check more necessary and not less: a contributed
    # route must not sit under a core prefix either, and `collect_bindings`
    # never sees the core arms to refuse it.
    assert not WORKBENCH_ROUTE.startswith("/source/")
    assert not WORKBENCH_ROUTE.startswith("/actions/gate/")


def test_the_three_projection_routes_are_distinct() -> None:
    # Three exact GETs under one unclaimed "/projections/" namespace, and
    # nothing declares that namespace as a PREFIX — which is why all three
    # can be exact and why none of them can swallow the others.
    assert len({ROLE_AUTHORITY_ROUTE, EVIDENCE_ROUTE, WORKBENCH_ROUTE}) == 3


def test_getting_the_binding_via_match_reaches_the_right_handler() -> None:
    # match() is the actual per-request dispatch primitive; exercising it
    # end-to-end (pattern in, handler name out) is the closest this suite
    # gets to a live request without the real server.
    bindings = route_extension.collect_bindings([ModelScenarioWorkbenchExtension()])
    hit = route_extension.match(bindings, "GET", WORKBENCH_ROUTE)
    assert hit is not None
    binding, remainder = hit
    assert binding.handler == "_handle_model_scenario_workbench"
    assert remainder == ""


def test_head_request_also_matches_the_get_binding() -> None:
    # "A GET binding answers both GET and HEAD" (route_extension.py's own
    # docstring) — this bench is a plain read, so HEAD must resolve exactly
    # as GET does.
    bindings = route_extension.collect_bindings([ModelScenarioWorkbenchExtension()])
    hit = route_extension.match(bindings, "HEAD", WORKBENCH_ROUTE)
    assert hit is not None
    binding, _remainder = hit
    assert binding.handler == "_handle_model_scenario_workbench"


def test_a_sibling_path_under_the_bench_route_does_not_match_it() -> None:
    # The binding is EXACT, not a prefix: nothing below it is claimed, so a
    # future contribution may declare "/projections/workbench/<something>"
    # without this one having silently taken the subtree.
    bindings = route_extension.collect_bindings([ModelScenarioWorkbenchExtension()])
    assert route_extension.match(bindings, "GET", WORKBENCH_ROUTE + "/station") is None


def test_the_module_imports_nothing_from_the_core_it_contributes_to() -> None:
    # The property the seam exists for: structural conformance WITHOUT a
    # nominal dependency. `route_extension` itself is the neutral seam module
    # (it belongs to neither package by construction) — the check here is
    # that the extension class is not a subclass of the Protocol.
    assert route_extension.RouteExtension not in ModelScenarioWorkbenchExtension.__mro__
