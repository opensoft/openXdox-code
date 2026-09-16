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
leg; the `styles` field RULED Q7 adds is newer again, landing in openDox-code's
own Q7 leg, which is why `views()` below FEATURE-DETECTS it rather than
declaring it unconditionally. Importing either at module-import time would make this module unimportable
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
  Q7  a contributed binding's CSS lives with the binding, in its own sheet.
      REALIZED: each binding that owns selectors names its sheet in `styles`
      below, the bytes ship as package data beside the modules
      (`web_assets.VIEW_SHEET_NAMES`), and `STYLE_RESIDUE` records the
      discharge with the figures it was opened with. THE SHAPE IS RULED, not
      merely measured: FOUR sheets rather than six, a single `styles`
      specifier, and href de-duplication load-bearing — RULED openxFactory#656
      comment `5700475319` (Brett Heap, 2026-09-16, by interactive
      multi-choice), on the question this column's author put after measuring
      that `gate-lens.js` owns no selector of its own and that the two
      workbench modules name eleven blocks between them.
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

import dataclasses
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
    "specs_for",
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

#: Q7's DISCHARGE, with the figures it was opened with. RULED Q7
#: (`5648049748`): "a contributed binding's CSS lives WITH THE BINDING, in its
#: own sheet; openDox's declared design tokens (the `--st-*` family, S7) are the
#: one stable styling surface; nothing else in `styles.css` is."
#:
#: WHAT WAS HERE AND WHY IT IS GONE. At `01b06c94` this table recorded the
#: extraction as BLOCKED: `styles.css` was a `moved_verbatim` row of
#: openxFactory's `docs/opendox-carve-manifest.yaml`, whose declared-edit
#: vocabulary is the RULED closed list `import rewrites | path constants |
#: adapter calls`, and "a stylesheet block leaves for another leg" was in none
#: of them. **That wall no longer stands, and it was not worked round.** Slice
#: S7 (openxFactory #1030 -> `b3a75537`) converted the row to
#: `moved_with_declared_edit` with 152 `adapter calls` lines, so the question
#: narrowed from "may this row carry an edit at all" to "is a DELETION
#: declarable", which the floor already answers twice: § 3.4 slice S6 declared
#: 122 `serve_projection.py` DELETIONS under `adapter calls` and landed, and
#: `scripts/verify-carve-arrival.py` accepts this act's own 89 deleted carve
#: lines under the same class — MEASURED, not argued, before a line of this
#: column was written.
#:
#: THE CENSUS, RE-MEASURED at openDox-code `0b4e8bbf` and openXdox-code
#: `0a0265f7` rather than carried forward. The `51 / 24` this table recorded at
#: `cb343ae8` reproduces EXACTLY under a literal-only scan — and the `51` was
#: three short: `.dispose-accepted`, `.dispose-rejected` and `.dispose-deferred`
#: are built by `"disposebtn dispose-" + v.outcome` (`dispose.js`:275), which no
#: literal search can see. 54 classes are this column's own; 21 are shared with
#: modules that stay and are openDox's, which is where they remain.
STYLE_RESIDUE: dict[str, Any] = {
    "measured_at": "opensoft/openDox-code 0b4e8bbf, opensoft/openXdox-code 0a0265f7",
    "exclusive_classes": 54,
    "shared_classes": 21,
    "rule_blocks_moved": 59,
    #: AND THE TWO MIXED RULES, counted separately because they are a different
    #: act (Copilot review, round 3, which found the sheets carrying 61 blocks
    #: against a record that said 59). `.filterpop[hidden], .projectform
    #: .projectpanel[hidden]` was SPLIT — openDox keeps its half and this
    #: column re-states the gate half — and `.swb-draftchrome .swb-cactions`
    #: MOVED WHOLE, carrying the one openDox class a sheet here names as host
    #: context. 59 + 2 = 61, which is what the four sheets contain and what
    #: `test_the_sheets_carry_the_blocks_the_residue_counts` asserts.
    "mixed_blocks_handled": 2,
    "rule_blocks_in_sheets": 61,
    "styles_css_lines_declared": 89,
    "sheets": web_assets.VIEW_SHEET_NAMES,
    "previously_measured_at": "opensoft/openDox-code cb343ae8 (51 exclusive / "
                              "24 shared; the 51 missed the three classes "
                              "`dispose.js` builds by concatenation)",
    "blocked_by": None,
    "discharged_by": "RULED Q7 realized here and at openDox-code: `ViewBinding."
                     "styles` names each sheet, `views/view_extension.js` "
                     "injects one `<link>` per href into `document.head` "
                     "(never `document.body`, RULED Q8), and the 89 carve "
                     "lines the blocks left on are declared `adapter calls` on "
                     "the `styles.css` row (RULED Q-L1's form, `#656` comment "
                     "`5628560136`)",
    #: THE ONE THING THIS ACT DOES NOT CLOSE, AND IT IS RULED THAT WAY. The
    #: sheets read 13 of openDox's NON-token custom properties, which RULED
    #: Q7's own sentence says are not a stable surface. Put to Brett Heap with
    #: the three alternatives (widen the stable surface by ruling; a second
    #: declared token family for contributed chrome; defer to the BUILD arc)
    #: and RULED openxFactory#656 comment `5700475319` (2026-09-16, by
    #: interactive multi-choice): **MOVE them VERBATIM and REGISTER the
    #: coupling BY MEASUREMENT** — this entry, asserted by this leg's own
    #: `tests/test_gate_loop_views.py`. The only alternative that removes the
    #: coupling is inlining the colour values, which would end dark mode for
    #: this column on every install.
    "open_coupling": {
        "non_token_custom_properties_read": 13,
        "st_tokens_read": 3,
        "st_tokens_declared": 0,
        "host_context_classes": ("swb-draftchrome",),
        "note": "RULED Q7 makes the `--st-*` family the one stable styling "
                "surface; these sheets also READ openDox's own non-token "
                "properties and one openDox class as host context. Registered "
                "here and held by this leg's own suite, so a rename at openDox "
                "turns this column red rather than blank",
    },
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
        "styles": "./views/gate.css",
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
        # NO `styles`, AND THAT IS MEASURED. `gate-lens.js` names no class
        # that openDox's own bundle does not also name: its plan-panel controls
        # reuse the shell's shared `.cbtn` / `.lens` chrome. RULED Q7 sends a
        # binding's OWN CSS to its own sheet; this binding has none, and an
        # empty sheet shipped for symmetry would be a file nothing declares.
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
        "styles": "./views/gate-projects.css",
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
        "styles": "./views/dispose.css",
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
        "styles": "./views/swb.css",
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
        "styles": "./views/swb.css",
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


def specs_for(binding_cls: Any) -> tuple[dict[str, Any], ...]:
    """The declared specs, ADAPTED to the `ViewBinding` an assembly installed.

    RULED Q7's `styles` FIELD IS NEWER THAN THE PIN, and this is slice S5's
    posture applied in the other direction. `styles` lands in openDox-code's own
    Q7 leg; until this leg pins an `opendox` that carries it, handing it to the
    constructor raises the same `TypeError` `ViewContractUnsupported` names for
    `exports` — and refusing the WHOLE COLUMN because its panels would be
    unstyled is the "a declaration deleting the surface it was meant to
    describe" defect `gate.dispose`'s own `requires` note argues against at
    length. Unstyled panels are degraded; absent panels are deleted.

    So the field is DROPPED where the installed class does not take it, the
    column mounts, and the pin bump that follows openDox-code's Q7 leg turns
    the sheets on with no edit here. `exports` is NOT treated this way and must
    not be: an undeclared reach is a refusal RULED Q2 asks for, so a pin that
    cannot express it is a pin this column cannot run on, which is what
    `ViewContractUnsupported` says.

    A FIELD SET, never a `try`/`except TypeError` retry: the retry cannot tell
    "this class has no `styles`" from "this spec is malformed", and swallowing
    the second is how a declaration defect becomes a silent degrade.
    """
    try:
        fields = {f.name for f in dataclasses.fields(binding_cls)}
    except TypeError:                                   # not a dataclass at all
        return VIEW_BINDING_SPECS
    if "styles" in fields:
        return VIEW_BINDING_SPECS
    return tuple({k: v for k, v in spec.items() if k != "styles"}
                 for spec in VIEW_BINDING_SPECS)


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
                         for spec in specs_for(view_extension.ViewBinding))
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

#: And the sheets, RULED Q7 — same reason, one tier over: the BYTES of a
#: binding's appearance and the DECLARATION that names them are two halves of
#: one contribution, and a reader should see both from one place.
VIEW_SHEET_NAMES = web_assets.VIEW_SHEET_NAMES
