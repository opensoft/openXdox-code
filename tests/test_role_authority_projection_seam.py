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
"""

from __future__ import annotations

import pytest
import route_extension

from openxdox.role_authority_projection import (
    ROLE_AUTHORITY_ROUTE,
    RoleAuthorityProjectionExtension,
    RoleAuthorityRoutes,
)


def _existing_contribution_extensions():
    """Import the two ALREADY-LANDED contribution columns, or skip.

    `openxdox.serve_projection` reaches `doc_health` at import time (via
    `snapshot_registry`), which § 4.1's own second clause already names as
    lawful-but-not-yet-reachable here: `doc_health` is openxFactory's own
    corpus machinery, not vendored, not on PyPI, and making it reachable is
    BUILD-arc work (§ 3.5/3.6) this slice does not touch. Where that gap is
    unresolved in the running environment, the two tests that need these
    extensions skip with the reason on the record rather than failing on a
    module this slice has no ruling to fix — and start asserting for real
    the day the BUILD arc closes it."""
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


def test_assembles_beside_the_two_existing_contribution_columns() -> None:
    # The real assembly, once task 4.3's composition point exists, combines
    # every § 2.4 contribution in one tuple. Proving that combination here —
    # ahead of that wiring — is what makes this a seam-conformance test and
    # not just a unit test of one class.
    GateRoutesExtension, ProjectionRoutesExtension = _existing_contribution_extensions()
    extensions = [
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
        RoleAuthorityProjectionExtension(),
    ]
    bindings = route_extension.collect_bindings(extensions)
    # 1 (gate prefix) + 3 (snapshot-index exact, bare-source exact, source
    # prefix) + 1 (this projection's exact GET) = 5, and no
    # RouteBindingError means none of the five collide or nest.
    assert len(bindings) == 5
    assert ROLE_AUTHORITY_ROUTE in {b.pattern for b in bindings}


def test_assembly_is_order_insensitive() -> None:
    # collect_bindings groups every exact binding ahead of every prefix one
    # regardless of declaration order (route_extension.py's own docstring) —
    # declaring this extension FIRST must assemble identically.
    GateRoutesExtension, ProjectionRoutesExtension = _existing_contribution_extensions()
    extensions = [
        RoleAuthorityProjectionExtension(),
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
    ]
    bindings = route_extension.collect_bindings(extensions)
    assert len(bindings) == 5


def test_role_authority_route_does_not_sit_under_either_declared_prefix() -> None:
    # Belt and braces beyond the collect_bindings proof above: the pattern
    # itself must not share either existing prefix's namespace, so a future
    # third prefix declared alongside "/source/" or "/actions/gate/" can
    # never retroactively swallow this route.
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
