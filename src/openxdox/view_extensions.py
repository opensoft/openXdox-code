"""openXdox's VIEW contribution: the gate loop, declared as `ViewBinding`s.

THE SLICE. `split-opendox-two-layer-product` § 3.4 slice S5 — "contribute the
gate loop" (openDox-spec `docs/front-end-package-boundary.md` § 5 row S5 @
`7d12428c`): *"The four class-B files and all 13 route constants — now all
declared in class-B files — move behind a binding openXdox supplies; a student
install comes up with no gate bar, no dispose tray, no session verbs, and no
404."* Its contract is openXdox-spec `docs/gate-loop-view-contract.md` @
`d73767b7`, whose § 8 Q1–Q12 were RULED by Brett Heap on 2026-09-12 at
`opensoft/openxFactory#656` comments `5648044785`, `5648049748` and
`5648065587`.

THE SHAPE IS `serve_gate.GateRoutesExtension`'s, deliberately. That class
contributes this column's ROUTES to `opendox.serve.build_server()`'s
`route_extension` seam without openDox importing anything from here; this one
contributes its PANELS to the same server's `view_extension` seam the same way.
Structural conformance, never nominal: `opendox.view_extension.ViewExtension` is
a `runtime_checkable` `Protocol` precisely so that a binding authored in the
repository that PINS openDox conforms without inheriting from it.

WHY THE BINDINGS ARE DECLARED AS DATA AND MATERIALIZED LATE. This leg pins
`opendox` by commit (`pyproject.toml`), and the pinned commit is older than the
view registry itself — `opendox.view_extension` does not exist there, and the
`exports` field RULED Q2 adds is newer still, landing in openDox-code's own S5
leg. Importing either at module-import time would make this module unimportable
under its own declared dependency and would put this leg's `validate` red for a
reason that has nothing to do with this column. So `VIEW_BINDING_SPECS` below is
plain data — the same JSON shape the manifest crosses the process boundary as —
and `GateLoopViews.views()` materializes it through whatever `opendox` the
ASSEMBLY installed, at the one moment an assembly exists to have installed one.
That is `profile_openxfactory.__getattr__`'s own PEP 562 posture, for the same
reason: hold back WHEN the import happens, never what it returns.

WHAT EACH RULING PUT HERE, so a reader can check the realization against the
sitting rather than against this module's own account of it:

  Q1  the shell mounts contributed `dom`-region bindings generically; every
      binding here is a `shell` region, so each is caller-driven — the gate
      bar's pattern, which Q1 names as the one it preserves.
  Q2  `exports` — every export the shell may reach, listed on the binding and
      validated the way `entry` is. `isGateBearing` (openDox `app.js`'s reach
      past the declaration) and `firstEditTransport` (Q10) are named here.
  Q3  ONE mount signature, `mount(host, snapshot, ctx)`. Every `entry` below
      takes it; the gate bar was re-signatured in this slice, which is where the
      declared exception Q3 recorded ends.
  Q4  `requires` names DOTTED PATHS into the `/capabilities` payload. What each
      binding declares is argued against its own degrade-to-descriptor
      behaviour below — a binding that renders a descriptor without the
      capability does not REQUIRE it.
  Q5  the bytes are package data placed by `openxdox.web_assets`; the hosted
      fallback is `openxdox.serve_views`.
  Q6  (counterpart) what a contributed module may import from the bundle:
      `./views/helpers.js` AND NOTHING ELSE. Every other need reaches the
      binding through its `ctx` — `CTX_MODEL_REACH` below is the whole of what
      each binding asks the shell for — and `BUNDLE_REACH` is held to the
      guarantee by `tests/test_gate_loop_views.py`.
  Q7  a contributed binding's CSS lives with the binding. NOT realized in this
      slice and NOT silently skipped: see `STYLE_RESIDUE` below.
  Q8  `page-overlay`, the declared host for page-level panels — the region
      `gate.dispose` mounts its refusal panel into, replacing this column's old
      reach into `document.body`.
  Q9  `wheel-intent` / `dispose-intent` stay declared, unhosted and unread. No
      binding here names either, and that is the record on this side of the
      seam.
  Q10 `firstEditTransport` travels as a declared NON-MOUNT export of the
      workbench binding, reached through the registry.
  Q11 the shell catches `ViewBindingError` separately. openDox's, not this
      leg's — named here only so the pair is readable from one place.
  Q12 a COMPUTED route is declared as its LITERALS: `gate.dispose` declares the
      four `/actions/gate/<verb>` routes `dispose.js` used to concatenate.

A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C).
"""

from __future__ import annotations

from typing import Any

from openxdox import web_assets

__all__ = [
    "BUNDLE_REACH",
    "CTX_MODEL_REACH",
    "GUARANTEED_BUNDLE_MODULE",
    "STYLE_RESIDUE",
    "VIEW_BINDING_SPECS",
    "VIEW_EXTENSIONS",
    "GateLoopViews",
    "ViewContractUnsupported",
    "declared_routes",
]


class ViewContractUnsupported(RuntimeError):
    """The assembled `opendox` is older than the view contract this column declares.

    Raised where the bindings are MATERIALIZED, never at import, and it names
    the pin rather than the symptom: an assembly that pins an openDox without
    `view_extension.ViewBinding`, or without the `exports` field RULED Q2 adds,
    cannot mount this column, and a `TypeError` from a dataclass constructor
    three frames down says none of that.
    """


#: The ONE openDox bundle module a contributed binding may import — RULED
#: counterpart Q6, Brett Heap, 2026-09-12, `opensoft/openxFactory#656` comment
#: `5649094228`: "what a CONTRIBUTED view module may IMPORT from openDox's
#: bundle: `./views/helpers.js` and NOTHING ELSE. Every other need reaches the
#: binding through its `ctx` (Q1-Q4) or its own package (Q5)."
GUARANTEED_BUNDLE_MODULE = "./helpers.js"

#: WHAT EACH CONTRIBUTED MODULE IMPORTS — counterpart Q6, DECLARED and held to
#: the guarantee. `./helpers.js` is the one permitted bundle reach; a module of
#: THIS column (`./dispose.js`) is not a bundle reach at all, since the assembly
#: (RULED Q5) places both side by side in the same `views/` directory.
#:
#: THE RESIDUE THAT WAS HERE IS GONE. At `01b06c94` this table also carried
#: `./lens-model.js` (`gate-lens.js`), `./intent-binding.js` (`dispose.js`) and
#: `./staging-workbench-model.js` (`swb-create.js`, `swb-session.js`) — three
#: class-A openDox modules — and the record said the reach was measured "so a
#: guarantee-list ruling has a number to be made against". The ruling came, and
#: it granted no list: `./views/helpers.js` and nothing else. Every one of those
#: reaches is now a `ctx` facet (`CTX_MODEL_REACH`), so openDox's model stays in
#: openDox, single-sourced, and the dependency is VISIBLE at the seam rather
#: than resolved silently by a bundler.
BUNDLE_REACH: dict[str, tuple[str, ...]] = {
    "gate.js": (),
    "gate-lens.js": ("./helpers.js",),
    "gate-projects.js": ("./helpers.js",),
    "dispose.js": ("./helpers.js",),
    "swb-create.js": ("./helpers.js", "./dispose.js"),
    "swb-session.js": ("./helpers.js", "./dispose.js"),
}

#: WHAT EACH BINDING ASKS THE SHELL FOR — counterpart Q6's other half. A name
#: here is a name the mount reads off `ctx` and refuses BY NAME when it is
#: absent; nothing reaches openDox except through this table.
#:
#: `model` is openDox's `views/staging-workbench-model.js` / `views/lens-model.js`
#: namespace (behaviour openDox owns and keeps); `intent` is the hosted intent
#: feed's emitter and chip renderer, which openDox's `views/intent-binding.js`
#: supplies to the shell that starts the feed.
#:
#: THE AFFORDANCE VOCABULARY IS NOT HERE, deliberately: the six session tokens,
#: `SESSION_AFFORDANCES`, `SESSION_VERBS` and `SESSION_LABELS` are DECLARED by
#: `swb-session.js` itself, on RULED Q3's precedent from slice S4 ("a route
#: constant travels with the binding that calls it, never with the model that
#: happens to declare it", `5642758731`) — they key this column's own route
#: table at module scope, they name the gate verbs this column's own
#: `openxdox/serve_gate.py` answers, and after S5 no file in openDox's bundle
#: reads one of them.
CTX_MODEL_REACH: dict[str, dict[str, tuple[str, ...]]] = {
    "gate.bar": {},
    "gate.lens": {"model": ("recipeRequest", "clusterRequest")},
    "gate.projects": {},
    "gate.dispose": {"intent": ("emit", "renderChips")},
    "gate.workbench.create": {"model": ("createRequest", "createDocumentCommand",
                                        "consoleHeaders", "withConsoleRepair",
                                        "CONTINUATIONS")},
    "gate.workbench.session": {"model": ("sessionRequest", "sessionCommand",
                                         "sessionActionsLive",
                                         "sessionSurfaceHidden",
                                         "consoleHeaders", "withConsoleRepair",
                                         "notebookRefreshCommand",
                                         "firstEditBody", "firstEditVerdict")},
}

#: Q7's UNFINISHED HALF, stated rather than skipped. RULED Q7 (`5648049748`):
#: "a contributed binding's CSS lives WITH THE BINDING, in its own sheet;
#: openDox's declared design tokens (the `--st-*` family, S7) are the one stable
#: styling surface; nothing else in `styles.css` is." This slice does NOT move
#: the gate loop's selectors out of openDox's `styles.css`, and the reason is a
#: floor constraint rather than an omission: that file is a `moved_verbatim` row
#: of openxFactory's `docs/opendox-carve-manifest.yaml`, whose declared-edit
#: vocabulary is the RULED closed list `import rewrites | path constants |
#: adapter calls`, and "a stylesheet block leaves for another leg" is in none of
#: them — the same wall slice S6 met on one test file and WITHDREW from rather
#: than work round. It needs the `re_destined:` form RULED Q6 of the boundary
#: note (`5648044785`), which is being built in parallel, or its own ruling.
#: MEASURED at openDox-code `cb343ae8`, so the successor slice starts from a
#: number and not from a re-derivation: 51 CSS classes are used by this column's
#: six modules and by nothing else in openDox's bundle; 24 more are shared with
#: modules that stay.
STYLE_RESIDUE: dict[str, Any] = {
    "measured_at": "opensoft/openDox-code cb343ae8",
    "exclusive_classes": 51,
    "shared_classes": 24,
    "blocked_by": "styles.css is a moved_verbatim carve row; no edit class "
                  "covers a stylesheet block leaving for another leg",
    "discharged_by": "the re_destined: form (RULED Q6, openxFactory#656 "
                     "comment 5648044785) or a ruling of its own; the shared "
                     "half is slice S7's --st-* token work",
}


#: THE SIX BINDINGS, as the JSON the manifest carries. Field for field what
#: `opendox.view_extension.ViewBinding` takes, so the materialization below is a
#: constructor call and not a translation — a translation is where two
#: vocabularies start.
#:
#: EVERY ONE IS `optional: true`, and that is the whole slice in one field: a
#: shell assembled without this column renders the viewer with no gate bar, the
#: wheel with no dispose tray, the workbench with no session verbs and the lens
#: plan panel plan-only — "and no 404".
#:
#: EVERY ONE NAMES A `shell` REGION, so RULED Q1's generic mount pass (which
#: mounts contributed `dom`-region bindings) never reaches them: each is mounted
#: by the caller that builds its host, which is the gate bar's pattern Q1 keeps.
VIEW_BINDING_SPECS: tuple[dict[str, Any], ...] = (
    {
        # THE GATE BAR. `viewer.js` builds the `div.viewer-gate` per artifact
        # and the shell hands this entry to it as `mountGate`.
        #
        # `requires` IS EMPTY, AND THAT IS A CORRECTION THIS SLICE MAKES. The
        # transitional core-arm entry openDox carried (`app.js`:599-602 at
        # `cb343ae8`) declared `requires: ["actions.gate"]` while NOTHING read
        # it — the counterpart note's own finding: "a binding declaring
        # `requires` is declaring an intention the shell does not act on"
        # (§ 4.4 @ `d73767b7`). RULED Q4 makes the shell act on it, so the
        # declaration has to become true in the same slice. This bar does not
        # need `actions.gate` to MOUNT: without it, it renders the four CLI
        # action descriptors and does not execute (`gate.js`'s `upgrade`), which
        # is the read-only web surface working as designed. Declaring the
        # capability would delete that surface on every non-loopback plane.
        "id": "gate.bar",
        "region": "viewer-gatebar",
        "module": "./views/gate.js",
        "entry": "mountGateBar",
        "view_class": "B",
        "routes": ("/actions/gate/ratify",),
        # Q2: `isGateBearing` is the export openDox's `app.js` reached past the
        # declaration for (`app.js`:971 at `cb343ae8`, through the namespace
        # `resolveView` returns). It is NAMED now.
        "exports": ("mountGateBar", "isGateBearing"),
        "requires": (),
        "optional": True,
    },
    {
        # THE LENS'S TWO GATE VERBS (slice S4's module). The plan panel's
        # execute box is a live gate control with no descriptor form, so the
        # capability is a genuine mount requirement.
        "id": "gate.lens",
        "region": "lens-gate",
        "module": "./views/gate-lens.js",
        "entry": "mountLensGate",
        "view_class": "B",
        "routes": ("/actions/gate/lens-save-recipe",
                   "/actions/gate/lens-add-as-cluster"),
        "exports": ("mountLensGate",),
        "requires": ("actions.gate",),
        "optional": True,
    },
    {
        # THE PROJECT COMMISSIONS (slice S4's module). Same reading: the
        # create/edit-project controls are live gate verbs or they are nothing.
        "id": "gate.projects",
        "region": "repo-projects",
        "module": "./views/gate-projects.js",
        "entry": "mountProjectCommissions",
        "view_class": "B",
        "routes": ("/actions/gate/create-project",
                   "/actions/gate/edit-project"),
        "exports": ("mountProjectCommissions",),
        "requires": ("actions.gate",),
        "optional": True,
    },
    {
        # THE DISPOSE COLUMN. Its entry mounts the REFUSAL PANEL into RULED
        # Q8's `page-overlay` region — the shell builds that host and hands it
        # over, replacing this module's old singleton append to `document.body`.
        # Its other seven exports are the tray, the two commission buttons, the
        # action-row verb mounter and the three pure predicates openDox's
        # `views/wheel.js` used to reach by a static import.
        #
        # ROUTES: SIX, and four of them are RULED Q12's. `dispose.js` posted to
        # `"/actions/gate/" + verb` for the wheel's four action-row verbs, which
        # `ViewBinding.routes` cannot express and openDox-spec § 4.5 assertion
        # 2's literal grep cannot see. They are literals in the module now and
        # they are declared here.
        "id": "gate.dispose",
        "region": "page-overlay",
        "module": "./views/dispose.js",
        "entry": "mountRefusalPanel",
        "view_class": "B",
        "routes": ("/actions/gate/dispose-possible",
                   "/actions/gate/propose",
                   "/actions/gate/promote-to-staging",
                   "/actions/gate/research-brief",
                   "/actions/gate/derive-possibles",
                   "/actions/gate/demote"),
        "exports": ("mountRefusalPanel", "appliedOutcome", "commissionedVerb",
                    "commissionedWorkflow", "gateCapable", "mountDisposeTray",
                    "mountProposeButton", "mountWheelVerb", "panelEntry"),
        # `requires` IS EMPTY, AND THAT IS THE INTENT PLANE (Copilot review of
        # this PR, round 2). This module is the ONE binding of the six that
        # serves TWO mutually exclusive transports: the LOCAL executing gate
        # (`actions.gate`, loopback) and the HOSTED intent plane
        # (`actions.intent`, which openDox's `serve.py` computes as
        # `intent = not loopback` — so exactly one of the pair is ever true).
        # openDox's `views/wheel.js` mounts this namespace's tray when
        # `gateCapable(caps) || intentCapable(caps)`, and hands it the hosted
        # emitter and chip renderer in the second case. Declaring
        # `actions.gate` would make `resolveView` answer `null` on every hosted
        # plane, which would take the tray, its chips and `panelEntry`'s
        # refusal surface away from the plane the intent work exists for — a
        # capability declaration deleting the surface it was meant to describe,
        # which is the exact defect the gate bar's own transitional
        # `requires: ["actions.gate"]` already was.
        #
        # The plane choice stays where it has always been: in the CALLER, which
        # knows which transport it is holding, and in the module, which takes
        # `opts.intent` or does not.
        "requires": (),
        "optional": True,
    },
    {
        # THE WORKBENCH'S CREATE AFFORDANCE. `requires` is empty for the gate
        # bar's reason: without `actions.gate` this module renders the seeded
        # CLI descriptor (`renderDescriptor`), which is the read-only surface.
        "id": "gate.workbench.create",
        "region": "workbench-create",
        "module": "./views/swb-create.js",
        "entry": "mountCreateAffordance",
        "view_class": "B",
        "routes": ("/actions/gate/create-document",),
        "exports": ("mountCreateAffordance", "openCreateDialog",
                    "createGateLive"),
        "requires": (),
        "optional": True,
    },
    {
        # THE WORKBENCH'S SESSION AFFORDANCES — and RULED Q10's home for
        # `firstEditTransport`, openDox `app.js`'s remaining class-A → class-B
        # static import (`app.js`:57 at `cb343ae8`, called at :1171). A
        # transport is not a panel, so it travels as a DECLARED NON-MOUNT
        # EXPORT of this binding and is reached by `resolveView` at that one
        # call site, with a refusal-shaped fallback in openDox when this column
        # is absent — "never a blank".
        #
        # `requires` is empty for the same reason as its two siblings:
        # `mountSessionAffordances` renders descriptors when the session
        # capability is off and nothing at all when the plane declares
        # `session: false`, both of which are its own correct behaviour.
        "id": "gate.workbench.session",
        "region": "workbench-session",
        "module": "./views/swb-session.js",
        "entry": "mountSessionAffordances",
        "view_class": "B",
        "routes": ("/actions/gate/edit-document",
                   "/actions/gate/open-pr",
                   "/actions/gate/first-edit",
                   "/actions/gate/abandon-session",
                   "/actions/gate/share-session"),
        "exports": ("mountSessionAffordances", "firstEditTransport",
                    "createdDocuments", "documentCreated", "endedSessions",
                    "openedSessions", "sessionOpened"),
        "requires": (),
        "optional": True,
    },
)


def declared_routes() -> tuple[str, ...]:
    """Every gate route this column's bindings claim, in declaration order.

    Seventeen: the thirteen route CONSTANTS openDox-spec § 1.2(c) measures in
    the tree, plus the four literals RULED Q12 turns `dispose.js`'s computed
    route into. Used by this leg's own test and by anyone asking what the gate
    column owns without reading six JavaScript modules.
    """
    return tuple(route for spec in VIEW_BINDING_SPECS
                 for route in spec["routes"])


class GateLoopViews:
    """openXdox's view contribution: the gate loop, and nothing else.

    Conforms to `opendox.view_extension.ViewExtension` STRUCTURALLY — one
    `views()` method — so nothing about this class is imported by the core it
    contributes to. `serve_gate.GateRoutesExtension`'s own shape and its own
    reason, one seam over.
    """

    def views(self) -> tuple[Any, ...]:
        """Materialize the declared specs as the pinned openDox's `ViewBinding`s.

        Called ONCE at assembly time by `opendox.view_extension.collect_view_bindings`,
        never per render.
        """
        try:
            from opendox import view_extension
        except ImportError as exc:                      # pragma: no cover
            raise ViewContractUnsupported(
                "this assembly's `opendox` carries no `view_extension` module, "
                "so openDox's view seam (§ 3.4 slice S3) is not there to "
                "contribute to. Pin an openDox at or after the S5 view "
                "contract and re-assemble") from exc
        try:
            return tuple(view_extension.ViewBinding(**spec)
                         for spec in VIEW_BINDING_SPECS)
        except TypeError as exc:
            raise ViewContractUnsupported(
                "this assembly's `opendox.view_extension.ViewBinding` does not "
                f"take the fields this column declares ({exc}). RULED Q2 "
                "(openxFactory#656 comment 5648049748) adds `exports` — every "
                "export the shell may reach, validated the way `entry` is — and "
                "a pinned openDox older than that cannot express this column's "
                "contract. Bump the pin to the openDox that carries § 3.4 "
                "slice S5") from exc


#: THE FACET, beside `ROUTE_EXTENSIONS` and `SUBCOMMAND_EXTENSIONS` — one
#: composite profile, one registration, now four facets, all resolved through
#: the SAME lazy proxy (RULED ASK-2 option (2), openxFactory#656 comment
#: `5628886636`). `opendox.view_extension.host_view_extensions()` reads it off
#: the registered profile by the name `PROFILE_FACET` = `"VIEW_EXTENSIONS"`;
#: a host registered without it gets an empty consumer column with the absence
#: NAMED in the manifest (`host_facet: "absent"`), never a refusal.
#:
#: THE ASSEMBLY'S PROFILE MODULE RE-EXPORTS THIS. `profile_openxfactory.py`
#: (openxFactory `scripts/`, the composite profile this estate registers) adds
#: `VIEW_EXTENSIONS = view_extensions.VIEW_EXTENSIONS` beside its
#: `ROUTE_EXTENSIONS` tuple, exactly as it names `serve_gate.GateRoutesExtension()`
#: there. That one line is the assembly's, not this leg's, and it is recorded as
#: owed rather than reached for from here.
VIEW_EXTENSIONS: tuple[GateLoopViews, ...] = (GateLoopViews(),)


#: Re-exported so a reader of this module can see, in one place, that the
#: BYTES and the DECLARATION are two halves of one contribution (RULED Q5).
VIEW_MODULE_NAMES = web_assets.VIEW_MODULE_NAMES
