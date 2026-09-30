"""Seam-conformance: the role-and-authority projection registers through
`route_extension` (`split-opendox-two-layer-product` § 2.4) exactly the way
`serve_gate.GateRoutesExtension` and `serve_projection.ProjectionRoutesExtension`
already do, and does not collide with either.

This is what "a route contribution through the § 2.4 seam" MEANS as a tested
property, independent of task 4.3's still-open composition-point wiring: an
extension that (a) structurally conforms to `route_extension.RouteExtension`,
(b) contributes bindings `collect_bindings` accepts without a
`RouteBindingError`, (c) whose handler name RESOLVES to a real callable on the
class it will be mixed into (`resolve_handlers` — the "a route that cannot be
served must not start" refusal), and (d) that assembles cleanly beside the
OTHER two existing contribution columns, in either declaration order.

(d) IS ASSERTED ELSEWHERE, since plan 034 task T044. The two columns are
`serve_gate.GateRoutesExtension` and `serve_projection.ProjectionRoutesExtension`,
and `serve_projection` reached openxFactory's `doc_health` when it was
imported (through `snapshot_registry`), which no lone checkout supplies. So
this suite's two cases for (d) sat behind a guard that skipped on every lone
run, until T044 made them assert for real and moved them to
`tests/test_seam_assembly_beside_gate_and_projection.py`. That file was in the
declared exclusion (`tests/declared_exclusion.yaml`) under `doc_health` until
plan 034 T059 moved `snapshot_registry`'s one `doc_health` read out of its
module level. It runs in this leg's required check now.
"""

from __future__ import annotations

import route_extension

from openxdox.role_authority_projection import (
    ROLE_AUTHORITY_ROUTE,
    RoleAuthorityProjectionExtension,
    RoleAuthorityRoutes,
)


def test_extension_conforms_structurally_to_route_extension() -> None:
    # runtime_checkable Protocol: conformance by having the method, no
    # inheritance from route_extension needed (and none exists — the module
    # imports nothing from the core it contributes to).
    assert isinstance(RoleAuthorityProjectionExtension(), route_extension.RouteExtension)


def test_collect_bindings_accepts_the_extension_alone() -> None:
    bindings = route_extension.collect_bindings([RoleAuthorityProjectionExtension()])
    assert len(bindings) == 1
    assert bindings[0].pattern == ROLE_AUTHORITY_ROUTE


def test_handler_name_resolves_on_the_mixin_class() -> None:
    # "A route that cannot be served must not start" — resolve_handlers is
    # the build-time refusal `route_extension.py` documents; this proves the
    # binding's handler name is a real, callable attribute of the class it
    # will be mixed into, without needing the full DashboardHandler.
    bindings = route_extension.collect_bindings([RoleAuthorityProjectionExtension()])
    route_extension.resolve_handlers(bindings, RoleAuthorityRoutes)  # must not raise


def test_role_authority_route_does_not_sit_under_either_declared_prefix() -> None:
    # Belt and braces beyond the collect_bindings proof above: the pattern
    # itself must not share either prefix's namespace, so a future prefix
    # declared alongside "/source/" or "/actions/gate/" can never
    # retroactively swallow this route. `/source/` is `opendox/serve.py`'s
    # CORE prefix since § 3.4 slice S6 rather than this column's contributed
    # one, which makes this check more necessary and not less: a contributed
    # route must not sit under a core prefix either, and `collect_bindings`
    # never sees the core arms to refuse it.
    assert not ROLE_AUTHORITY_ROUTE.startswith("/source/")
    assert not ROLE_AUTHORITY_ROUTE.startswith("/actions/gate/")


def test_getting_the_binding_via_match_reaches_the_right_handler() -> None:
    # match() is the actual per-request dispatch primitive; exercising it
    # end-to-end (pattern in, handler name out) is the closest this suite
    # gets to a live request without the real server.
    bindings = route_extension.collect_bindings([RoleAuthorityProjectionExtension()])
    hit = route_extension.match(bindings, "GET", ROLE_AUTHORITY_ROUTE)
    assert hit is not None
    binding, remainder = hit
    assert binding.handler == "_handle_role_authority_projection"
    assert remainder == ""


def test_head_request_also_matches_the_get_binding() -> None:
    # "A GET binding answers both GET and HEAD" (route_extension.py's own
    # docstring) — this projection is a plain read, so HEAD must resolve
    # exactly as GET does.
    bindings = route_extension.collect_bindings([RoleAuthorityProjectionExtension()])
    hit = route_extension.match(bindings, "HEAD", ROLE_AUTHORITY_ROUTE)
    assert hit is not None
