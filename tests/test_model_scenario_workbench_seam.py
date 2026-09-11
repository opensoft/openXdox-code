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
through the one seam, and the full five-column assembly below is the first
test anywhere that proves all of them fit together.
"""

from __future__ import annotations

import pytest
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


def _existing_gate_and_projection_extensions():
    """Import the two ALREADY-LANDED columns that reach `doc_health`
    transitively (via `snapshot_registry`), or skip — the identical guard
    `test_role_authority_projection_seam.py` and
    `test_evidence_provenance_surface_seam.py` use, for the identical
    reason: `doc_health` reachability is BUILD-arc work (§ 3.5/3.6), not
    this slice's to fix. The skip is NARROW — any `ModuleNotFoundError` that
    is not `doc_health` re-raises, so a genuine breakage in this slice can
    never hide behind it. All three § 4.5 features import nothing but
    `route_extension` and `opendox.serve_wire`, so their mutual assembly is
    asserted unconditionally below instead of behind this guard."""
    try:
        from openxdox.serve_gate import GateRoutesExtension
        from openxdox.serve_projection import ProjectionRoutesExtension
    except ModuleNotFoundError as exc:
        if exc.name != "doc_health" and not (exc.name or "").startswith("doc_health"):
            raise
        pytest.skip(
            f"existing § 2.4 contribution column not importable in this "
            f"environment ({exc!r}) — doc_health reachability is BUILD-arc "
            "work (§ 3.5/3.6), not this slice's to fix; this test will "
            "assert for real once that lands")
    return GateRoutesExtension, ProjectionRoutesExtension


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
    # asserted unconditionally, ahead of the fuller (and possibly-skipped)
    # assembly below that also brings in the gate/projection columns. Three
    # bindings, three distinct exact routes: § 4.5's whole build content,
    # assembled.
    extensions = [
        RoleAuthorityProjectionExtension(),
        EvidenceProvenanceSurfaceExtension(),
        ModelScenarioWorkbenchExtension(),
    ]
    bindings = route_extension.collect_bindings(extensions)
    assert len(bindings) == 3
    assert {b.pattern for b in bindings} == {
        ROLE_AUTHORITY_ROUTE, EVIDENCE_ROUTE, WORKBENCH_ROUTE}


def test_assembles_beside_all_four_existing_contribution_columns() -> None:
    # The real assembly, once task 4.3's composition point exists, combines
    # every § 2.4 contribution in one tuple. Proving that combination here —
    # ahead of that wiring — is what makes this a seam-conformance test and
    # not just a unit test of one class.
    GateRoutesExtension, ProjectionRoutesExtension = _existing_gate_and_projection_extensions()
    extensions = [
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
        RoleAuthorityProjectionExtension(),
        EvidenceProvenanceSurfaceExtension(),
        ModelScenarioWorkbenchExtension(),
    ]
    bindings = route_extension.collect_bindings(extensions)
    # 1 (gate prefix) + 3 (projection: snapshot-index exact, bare-source
    # exact, source prefix) + 1 (role-authority exact) + 1 (evidence exact)
    # + 1 (this bench's exact GET) = 7, and no RouteBindingError means none
    # of the seven collide or nest.
    assert len(bindings) == 7
    assert WORKBENCH_ROUTE in {b.pattern for b in bindings}


def test_assembly_is_order_insensitive() -> None:
    # collect_bindings groups every exact binding ahead of every prefix one
    # regardless of declaration order (route_extension.py's own docstring) —
    # declaring this extension FIRST must assemble identically, and the
    # RESULTING SET must be identical too, not merely the same size.
    GateRoutesExtension, ProjectionRoutesExtension = _existing_gate_and_projection_extensions()
    declared_last = [
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
        RoleAuthorityProjectionExtension(),
        EvidenceProvenanceSurfaceExtension(),
        ModelScenarioWorkbenchExtension(),
    ]
    declared_first = [
        ModelScenarioWorkbenchExtension(),
        EvidenceProvenanceSurfaceExtension(),
        RoleAuthorityProjectionExtension(),
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
    ]
    last = route_extension.collect_bindings(declared_last)
    first = route_extension.collect_bindings(declared_first)
    assert len(first) == len(last) == 7
    assert {b.key for b in first} == {b.key for b in last}


def test_workbench_route_does_not_sit_under_either_declared_prefix() -> None:
    # Belt and braces beyond the collect_bindings proof above: the pattern
    # itself must not share either existing prefix's namespace, so a future
    # third prefix declared alongside "/source/" or "/actions/gate/" can
    # never retroactively swallow this route.
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
