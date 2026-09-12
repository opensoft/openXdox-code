"""The openXdox column of the dashboard serve: the projection and snapshot
routes (`split-opendox-two-layer-product` § 2.4, PR 3 of 4).

Design § D3's "projection and snapshot" cluster — the MECHANISM openXdox owns —
lifted out of `serve.py` UNCHANGED, byte for byte, as a mixin
`DashboardHandler` composes: the snapshot read and the index roster. Every
`self.<name>` these methods use (`_send_json`, `_serve_bytes`, `_active_entry`,
`_divergence_headers`, `loopback`, `source`, `snapshot_path`)
resolves through the MRO to `serve.py`'s own core implementation.

WHAT ARRIVES THROUGH THE SEAM AND WHAT STAYS A CORE ARM. `/snapshot-index.json`
is CONTRIBUTED here (`ProjectionRoutesExtension` below, assembled in
`profile_openxfactory.py`), so `_route` no longer branches on it.
`/snapshot.json` deliberately does NOT become a binding: its arm tests
`path == self.snapshot_route`, a PER-SERVER class attribute fed by
`build_server(snapshot_route=…)`, and a `RouteBinding.pattern` is a frozen
string — contributing it would silently break that public keyword for any caller
who set it. So the METHOD moved here with its neighbours and the ARM stayed core,
which is the only split that keeps both the column boundary and the keyword. See
the PR body's "Design decisions taken".

THE `/source` PAIR HAS LEFT THIS COLUMN — RULED Q4, § 3.4 slice S6 (Brett Heap,
2026-09-12, `opensoft/openxFactory#656` comment `5642758731`): *"`/source/` is
openDox's, and openXdox's projection binding keeps only `/snapshot-index.json`
and the three `/projections/*` routes."* Reading a file out of the pinned
checkout is the NEUTRAL product's own read-only pass-through; it predates the
gate loop and nothing about it is a gate act, and under RULING OQ-2 a student
runs openDox alone — so a viewer that cannot load a file without the consumer
layer was a route-ownership defect, not a layering one. The boundary note
(openDox-spec `docs/front-end-package-boundary.md` § 2.2 rule 1, § 4.5
assertion 2) measured it as the census's ONE class-A breach: `views/viewer.js`
addressed a route another column declared.

So `SOURCE_PREFIX`, `BARE_SOURCE_ROUTE`, their two `RouteBinding`s and the three
methods they reached (`_serve_source`, `_refuse_bare_source`, `_keyed_source`)
are now FIXED CORE ARMS of `opendox/serve.py`, together with the single-root
containment entry point `resolve_source_path` — whose only readers outside this
file were already openDox's (`serve.py`'s re-export and `notebook_action.py`'s
re-check). The per-ENTRY containment rule itself has not moved: it is
`snapshot_registry.resolve_within`, which is still this column's, and openDox's
arm reaches it through the same late seam `serve_workbench.py` already uses. The
ORDER the move preserves is the one the paragraph this replaced was written to
protect — an exact `/source` arm consulted before a `/source/` prefix arm, so
`/source/` still reaches `_serve_source("")` and answers 404 with divergence
headers and a zero-length body rather than an HTML error page.

INVOCATION (design D12): `serve.py` runs BOTH as a script and as a module, so
this module uses ABSOLUTE `ideation_dashboard.*` imports, never `from . import`,
and self-inserts `scripts/` on the import path for the bare `route_extension`
import the same way `serve.py` and `snapshot_registry.py` do.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path


import route_extension  # noqa: E402

from openxdox import snapshot_registry as registry_mod  # noqa: E402
from opendox.serve_wire import (  # noqa: E402
    HOSTED_SESSION_REFUSAL,
    JSON_CTYPE,
)

SNAPSHOT_INDEX_ROUTE = "/snapshot-index.json"
#: `SOURCE_PREFIX`, `BARE_SOURCE_ROUTE` and `resolve_source_path` STOOD HERE and
#: are now `opendox.serve`'s (RULED Q4, § 3.4 slice S6 — see the module
#: docstring). `snapshot_registry.resolve_within`, the per-entry containment rule
#: the pass-through is confined by, is unmoved and still this column's.


# ------------------------ hosted-plane index projection (pure) ------------------------
# RE-HOMED HERE, byte for byte, by pre-carve split S-3 of
# `split-opendox-two-layer-product` § 3.1, out of `serve_wire.py:1387-1433`.
# That module's own docstring named the obligation: `hosted_index` is an
# openXdox FR-048 index-confinement rule with exactly one in-tree reader,
# `_serve_index` below, and the shared wire vocabulary goes WHOLE to openDox —
# so the carve manifest, which files each path under ONE column, could not have
# filed `serve_wire.py` while this function was still in it. Nothing changed but
# the address: the body is the same text, `registry_mod` is the import this
# module already had, and `serve.py` re-exports the name from here instead.

def hosted_index(document: dict) -> dict:
    """The snapshot INDEX as a hosted plane may project it (FR-048, PR #49 review
    finding 14): every non-`main` entry dropped, a non-`main` `active` dropped with
    them, and every non-`main` AGGREGATE MEMBER dropped too.

    `hosted_ref_refused` guards the routes that NAME a ref; the index names none,
    so it was outside that confinement entirely and published the branch names of
    unmerged work — the topic and cluster ids of work in progress — to anyone who
    could reach the bind. Pure, so the rule is testable on its own, and it reuses
    the SAME `is_publishable_ref` predicate the refusal does, so there is still
    one definition of "a ref a hosted plane may see".

    THE MEMBER PASS IS WAVE 2's. `entries` and `active` were projected and
    `aggregates[].members` was not, though `SnapshotRegistry.index_document` emits
    those members as `{repository, ref}` pairs — so an aggregate naming a session
    ref published `draft/<topic>` off-loopback with a 200 while `entries` was
    correctly main-only (reproduced by the wave-2 critic on a production-shaped
    hosted plane, and reproduced again here before the fix). Content stayed confined
    (`?ref=…` still 403), so what leaked is the topic id of unmerged work — the same
    class FR-048 exists to prevent. An aggregate whose members are ALL unpublishable
    is dropped whole rather than published empty: an aggregate is defined by the
    snapshots it composes, and one with no visible members is not a narrower view of
    itself, it is a name with nothing behind it (and a hosted plane composing it
    would find nothing to render)."""
    projected = dict(document)
    entries = [entry for entry in projected.get("entries") or []
               if registry_mod.is_publishable_ref(entry.get("ref"))]
    projected["entries"] = entries
    active = projected.get("active")
    if isinstance(active, dict) and not registry_mod.is_publishable_ref(active.get("ref")):
        projected.pop("active", None)
    if "aggregates" in projected:
        aggregates = []
        for aggregate in projected.get("aggregates") or []:
            if not isinstance(aggregate, dict):
                continue
            members = [member for member in aggregate.get("members") or []
                       if isinstance(member, dict)
                       and registry_mod.is_publishable_ref(member.get("ref"))]
            if not members:
                continue
            aggregates.append({**aggregate, "members": members})
        if aggregates:
            projected["aggregates"] = aggregates
        else:
            projected.pop("aggregates", None)
    return projected


# ------------------------ hosted-plane ref confinement (pure) -------------------------
# RE-HOMED HERE, byte for byte, by pre-carve split OQ-B B-2 of
# `split-opendox-two-layer-product` § 3.1, out of `serve_wire.py:1359-1393`,
# on Brett Heap's ruling of 2026-09-09 (`#656`, "rule B-2 (i')").
# The same reasoning S-3 recorded for `hosted_index` above, one name along,
# and this one also removes an IMPORT EDGE rather than only a mixed file:
# `serve_openxfactory_lanes.py` is openxFactory's own adapter column and
# STAYS, and it read this predicate from the wire module, which goes WHOLE
# to openDox — the direction RULING OQ-2 forbids. A neutral home was not
# available either: the body reaches `snapshot_registry.is_publishable_ref`,
# and `snapshot_registry` is the openXdox column, so a module replicated at
# every destination could not resolve it (`tests/doc-health/
# test_import_direction.py` asserts that property by parsing). Here it costs
# nothing: this module ALREADY imports `snapshot_registry`, already holds
# `hosted_index`, is already in the serve surface `conftest.py` scans, and
# already holds three of the predicate's four call sites.
# Nothing changed but the address: the body below is the same text, byte for
# byte, `registry_mod` is the alias this module already had, and `serve.py`
# re-exports the name from here instead.
def hosted_ref_refused(loopback: bool, ref: str | None) -> bool:
    """Whether a request naming `ref` must be REFUSED because this is the hosted
    plane (007-workbench-branch-sessions T083, FR-048).

    FR-048: "The hosted dashboard MUST expose NONE of this capability — no session,
    no branch-ref selection, no session verb, no worktree, no non-`main` snapshot —
    and a hosted request naming a non-`main` ref MUST refuse."

    The test is the BIND, not the advertised capability. A capability dict is a
    startup verdict a handler could in principle be constructed with by hand; the
    bind is what makes a plane hosted, and the confinement has to hold for any
    handler that is not on loopback. `None` / blank means `main` (the registry's own
    `normalize_ref` default), so every pre-existing ref-less request is untouched,
    and the LOCAL plane is untouched entirely — confining the hosted plane must not
    confine the plane this whole feature lives on.

    Why the hosted plane cannot simply have sessions: the session's remote-write
    identity is the invoking engineer's OWN `gh` authentication (FR-034, D22) — a
    personal credential, which a hosted plane must never hold or borrow — and the
    worktree a session reads through is a per-machine directory beside a real
    checkout, which a served image does not have (research R7).

    THE ARRIVAL PATH, RECORDED AND DELIBERATELY NOT BUILT (FR-048, chg 7.2). A
    hosted session becomes possible by binding the INTENT PLANE's apply-lane ref
    (openxFactory `add-ideation-intent-plane` §4) through the EXISTING
    (repository, ref) seam this function guards: the intent plane's lane already
    owns an identity that is not anybody's personal credential, and a lane ref is
    already a (repository, ref) pair, so the session would arrive as another row in
    the same registry — no new seam, no second write chokepoint, and the openxfactory
    App as the ruled hosted identity (D22). That binding is a SEPARATE change with
    its own gate: nothing in this module reaches for a lane, and this refusal is
    where the next reader will be standing when they ask why."""
    if loopback:
        return False
    return not registry_mod.is_publishable_ref(ref)


class ProjectionRoutes:
    """The projection column, mixed into `DashboardHandler`."""

    def _query_key(self) -> tuple[str | None, str | None]:
        """The optional `?repository=&ref=` of a read route. Absent repository
        means the ACTIVE entry — which is what every pre-existing caller sends,
        so today's behaviour is unchanged."""
        query = urllib.parse.urlsplit(self.path).query
        params = urllib.parse.parse_qs(query)
        repository = (params.get("repository") or [None])[0]
        ref = (params.get("ref") or [None])[0]
        return repository, ref

    # ---- snapshot ----
    def _read_snapshot(self) -> bytes | None:
        """The ACTIVE snapshot's bytes, through the registry when one is bound
        (the in-process derived cache included) and from the configured path
        otherwise."""
        entry = self._active_entry()
        if entry is not None:
            return entry.read_bytes()
        try:
            return Path(self.snapshot_path).read_bytes()
        except OSError:
            return None

    def _serve_snapshot(self, head_only: bool) -> None:
        """`/snapshot.json` — the active snapshot, or any registered
        (repository, ref) named by the query. An unknown pair is a 404; the
        active view the client already has stays untouched.

        On the HOSTED plane a non-`main` ref refuses before resolution (FR-048):
        the serving index legitimately advertises a live session row (FR-014), so
        without this a hosted request could name one."""
        repository, ref = self._query_key()
        if hosted_ref_refused(self.loopback, ref):
            self._send_json(403, {"ok": False, "error": "session_unavailable",
                                  "message": HOSTED_SESSION_REFUSAL})
            return
        if repository and self.source is not None:
            entry = self.source.registry.resolve(repository, ref)
            if entry is None:
                # An AGGREGATE id (declared, or register-derived per project —
                # add-project-merged-projection D11) composes at the default
                # ref only. Off-loopback, members at unpublishable refs are
                # dropped before composition (the hosted_index projection,
                # applied to content).
                composed = None
                if registry_mod.is_publishable_ref(ref):
                    composed = self.source.compose_view(
                        repository, publishable_only=not self.loopback)
                if composed is not None:
                    self._serve_bytes(json.dumps(composed).encode("utf-8"),
                                      JSON_CTYPE, head_only)
                    return
                self.send_error(404, "no such snapshot")
                return
            if self._hosted_entry_refused(entry):
                return
            self._serve_bytes(entry.read_bytes(), JSON_CTYPE, head_only, entry=entry)
            return
        if repository and self.source is None:
            self.send_error(404, "no such snapshot")
            return
        # THE REF-LESS HOLE (PR #49 review finding 14, composing with finding
        # 10b): a request that NAMES no ref resolves to the ACTIVE entry, and
        # `hosted_ref_refused` only ever inspected the ref a request named. A
        # non-`main` active entry would therefore have been served off-loopback
        # with no key in sight. The refusal now follows the RESOLVED entry.
        if self._hosted_entry_refused(self._active_entry()):
            return
        self._serve_bytes(self._read_snapshot(), JSON_CTYPE, head_only)

    def _hosted_entry_refused(self, entry) -> bool:
        """Refuse (and answer) when the entry a request RESOLVED to is
        session-local and this is the hosted plane. Returns whether it answered."""
        if entry is None or not hosted_ref_refused(self.loopback, getattr(entry, "ref", None)):
            return False
        self._send_json(403, {"ok": False, "error": "session_unavailable",
                              "message": HOSTED_SESSION_REFUSAL})
        return True

    def _serve_index(self, head_only: bool) -> None:
        """`/snapshot-index.json` — the roster the selector reads, composed from
        the registry. No registry (a hand-built handler) means no index, which
        is exactly how the renderer degrades to a single snapshot."""
        if self.source is None:
            self.send_error(404, "no snapshot index")
            return
        document = self.source.index_document()
        # belt AND braces on the hosted plane (FR-048, finding 14): the bootstrap
        # above admits no session rows off-loopback, and this projection would
        # drop them anyway — a handler constructed by hand, or a registry a future
        # route populates, cannot reopen the hole.
        if not self.loopback:
            document = hosted_index(document)
        body = json.dumps(document).encode("utf-8")
        self._serve_bytes(body, JSON_CTYPE, head_only)

class ProjectionRoutesExtension:
    """openXdox's projection contribution: the index roster, and — since RULED
    Q4 (§ 3.4 slice S6) — nothing else. Conforms to
    `route_extension.RouteExtension` STRUCTURALLY, so this column imports
    nothing from the core it contributes to.

    THE `/source` PAIR IS GONE FROM THIS TUPLE and is `opendox/serve.py`'s core
    arm now. The column's OTHER three contributed routes — `/projections/evidence`,
    `/projections/workbench`, `/projections/role-authority` — were never declared
    here: each travels with the surface that answers it
    (`evidence_provenance_surface.py`, `model_scenario_workbench.py`,
    `role_authority_projection.py`), and the ruling leaves all three untouched.
    """

    def routes(self) -> tuple[route_extension.RouteBinding, ...]:
        return (
            route_extension.RouteBinding("GET", SNAPSHOT_INDEX_ROUTE, False,
                                         "_serve_index"),
        )
