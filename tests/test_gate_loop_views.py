"""The gate loop CONTRIBUTED — § 3.4 slice S5, leg A (openXdox-code).

What this file measures is the half of slice S5 that lives at THIS leg: the six
class-B modules arriving as package data, the six `ViewBinding` specs that
declare them, the assembly hook that places the bytes, and the hosted GET
fallback. The other half — the shell losing its gate literals, the generic mount
pass, `requires` acted on, `ViewBindingError` surfaced — is openDox-code's, and
is measured there by `tests/test_gate_loop_contributed.py`.

THE RULINGS IT EXECUTES, each named at the assertion that carries it. openXdox-spec
`docs/gate-loop-view-contract.md` § 8 Q1-Q12 @ `d73767b7`, RULED by Brett Heap
on 2026-09-12 at `opensoft/openxFactory#656` comments `5648044785` (Q5, Q1, Q3),
`5648049748` (Q2, Q4, Q7, Q8) and `5648065587` (Q9, Q10, Q11, Q12).

`--noconftest` SAFE, like its four neighbours on `validate`'s explicit list: it
imports this package's own modules and reads this package's own files as text.
It drives no browser and parses no JavaScript with a parser this leg does not
have — the JS assertions are text/regex SHAPE assertions, the same constraint
openDox-spec's own § 4.5 test is written to, and the BEHAVIOURAL probes of these
modules live at openDox-code where the shell that mounts them is.

AND THE DISPLAY FACET, the second thing `view_extensions` declares for openDox's
shell (RULED `opensoft/openxFactory#656` comment `5784683830`). Its section, at
the end of this file, is where this suite reaches the pinned openDox's
`display_profile`, `profile_proxy` and `domain_profile`, and reads the pinned
`serve.py` as text. It registers a host built from the vendored engineering
profile with openDox's registry, one test at a time, and reads the facet back
through the lazy proxy by the statement the pinned `serve.build_server()` makes.
Every test there that reads anything off openDox asks `_display_profile_or_skip()`
first, on `_view_extension_or_skip()`'s footing. The guard's own call-site tests
are the exception: they take openDox apart before they call it, which is their
point.

A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C).
"""

from __future__ import annotations

import ast
import dataclasses
import fnmatch
import re
import sys
from pathlib import Path

import pytest

from openxdox import view_extensions, web_assets

MODULE_DIR = web_assets.VIEW_MODULE_DIR
SPECS = view_extensions.VIEW_BINDING_SPECS

#: The gate prefix `openxdox/serve_gate.py` contributes. Every route these
#: bindings declare must sit under it: a view binding of THIS column claiming a
#: path another column serves would be the § 2.2 rule 1 breach the whole boundary
#: exists to end, pointed the other way.
GATE_PREFIX = "/actions/gate/"

#: The regions this column's bindings may name, and the KIND each is. Held
#: against openDox's own `REGIONS` table where an openDox new enough to have one
#: is installed (below); declared here as well so this leg's suite states its own
#: expectation rather than only echoing its upstream's.
EXPECTED_REGIONS = {
    "gate.bar": "viewer-gatebar",
    "gate.lens": "lens-gate",
    "gate.projects": "repo-projects",
    "gate.dispose": "page-overlay",
    "gate.workbench.create": "workbench-create",
    "gate.workbench.session": "workbench-session",
}


def _module_text(name: str) -> str:
    return (MODULE_DIR / name).read_text(encoding="utf-8")


def _exported_names(text: str) -> set[str]:
    """Every top-level `export` NAME in a module, read as text.

    `export function f`, `export async function f`, `export const X`,
    `export let x` — the four forms this column actually uses. A re-export or a
    default export would not be found, and neither appears here (asserted).
    """
    return set(re.findall(
        r"^export\s+(?:async\s+)?(?:function|const|let|var|class)\s+"
        r"([A-Za-z_$][A-Za-z0-9_$]*)",
        text, re.MULTILINE))


def _module_constant(path: Path, name: str) -> tuple[str, ...]:
    """Read one module-level tuple constant out of a Python file by PARSING it.

    This package's heavier modules reach `doc_health` at import time and this
    suite is `--noconftest` and consumer-free by construction, so a declaration
    is read the way `tests/test_no_hardcoded_status_words.py` reads one: with
    `ast`, never with an import."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        targets = (node.targets if isinstance(node, ast.Assign)
                   else [node.target] if isinstance(node, ast.AnnAssign) else [])
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                return tuple(ast.literal_eval(node.value))
    raise AssertionError(f"{name} is not declared in {path}")


def _relative_imports(text: str) -> set[str]:
    return set(re.findall(r'from\s*["\'](\.\.?/[^"\']+)["\']', text)) | set(
        re.findall(r'^\s*import\s*["\'](\.\.?/[^"\']+)["\']', text, re.MULTILINE))


# ---------------------------------------------------------------------------
# RULED Q5 — the BYTES. "openXdox ships its view modules as package data."
# ---------------------------------------------------------------------------

def test_every_declared_view_module_ships_with_this_package() -> None:
    for name in web_assets.VIEW_MODULE_NAMES:
        path = web_assets.module_path(name)
        assert path.is_file(), f"{name} is declared and not shipped"
        assert path.stat().st_size > 0, f"{name} ships empty"


def test_the_package_directory_carries_nothing_undeclared() -> None:
    """A globbed directory is how a file reaches another leg's bundle with no
    binding naming it. The set is declared, so the directory must match it —
    and since RULED Q7 the set is modules AND sheets, which is why the
    comparison is against `VIEW_ASSET_NAMES` rather than against the modules
    alone: a sheet in this directory that no binding names would be exactly the
    quiet arrival this test exists to refuse."""
    on_disk = sorted(p.name for p in MODULE_DIR.iterdir() if p.is_file())
    assert on_disk == sorted(web_assets.VIEW_ASSET_NAMES), (
        "the packaged view-asset directory and the declared asset set "
        f"disagree: on disk {on_disk}, declared "
        f"{sorted(web_assets.VIEW_ASSET_NAMES)}")


def test_no_module_reaches_an_external_url() -> None:
    """§ 4.4's vendor policy — "no CDN, no external font, no remote script" —
    now applies to bytes THIS leg ships into someone else's bundle, so this leg
    proves it rather than relying on openDox's own bundle grep, which cannot see
    a file that is not in the bundle yet."""
    offenders = []
    for name in web_assets.VIEW_MODULE_NAMES:
        for match in re.finditer(r'["\'](https?:)?//[^"\']+["\']',
                                 _module_text(name)):
            offenders.append(f"{name}: {match.group(0)}")
    assert offenders == [], (
        f"{len(offenders)} external URL(s) in this column's contributed "
        f"modules: {offenders}")


def test_the_assembly_hook_places_every_asset_in_the_bundle(tmp_path) -> None:
    """RULED Q5's primary mechanism: the composed install copies them into
    openDox's one `--web-dir` at assembly — and since RULED Q7, the SHEETS by
    the same act. A bundle carrying this column's modules and not its sheets is
    a gate loop that mounts unstyled, which is a half-assembly."""
    web = tmp_path / "web"
    (web / web_assets.BUNDLE_SUBDIR).mkdir(parents=True)
    placed = web_assets.install_view_modules(web)
    assert [p.name for p in placed] == list(web_assets.VIEW_ASSET_NAMES)
    for path, name in zip(placed, web_assets.VIEW_ASSET_NAMES):
        assert path.parent.name == web_assets.BUNDLE_SUBDIR
        assert path.read_bytes() == web_assets.module_source(name)


def test_the_assembly_hook_refuses_rather_than_creating_a_bundle(tmp_path) -> None:
    """REFUSAL, NOT A DEFAULT (`build_server()`'s posture). A `--web-dir` that
    is not there means openDox was not assembled, and creating it would ship a
    bundle with no shell in it."""
    with pytest.raises(web_assets.ViewAssetError) as absent:
        web_assets.install_view_modules(tmp_path / "nothing-here")
    assert "is not a directory" in str(absent.value)

    bare = tmp_path / "web"
    bare.mkdir()
    with pytest.raises(web_assets.ViewAssetError) as no_views:
        web_assets.install_view_modules(bare)
    assert web_assets.BUNDLE_SUBDIR in str(no_views.value)


def test_the_assembly_hook_can_refuse_to_overwrite(tmp_path) -> None:
    web = tmp_path / "web"
    views = web / web_assets.BUNDLE_SUBDIR
    views.mkdir(parents=True)
    (views / web_assets.VIEW_SHEET_NAMES[0]).write_text("/* someone else's */\n")
    with pytest.raises(web_assets.ViewAssetError) as clash:
        web_assets.install_view_modules(web, overwrite=False)
    assert "already" in str(clash.value) and "overwrite=False" in str(clash.value)
    # ASSET, not MODULE (Copilot review, round 2): the collision sweep covers
    # `VIEW_ASSET_NAMES` since RULED Q7, so a colliding `gate.css` must not be
    # described as a second copy of the gate loop's modules.
    assert "asset(s)" in str(clash.value)
    # NOTHING WAS COPIED (Copilot review, round 1): the collision check runs over
    # every module BEFORE the first write, so a refusal never leaves a
    # half-assembled bundle behind.
    assert sorted(p.name for p in views.iterdir()) == [
        web_assets.VIEW_SHEET_NAMES[0]]


def test_an_undeclared_asset_name_is_refused() -> None:
    with pytest.raises(web_assets.ViewAssetError):
        web_assets.module_path("../../etc/passwd")
    with pytest.raises(web_assets.ViewAssetError):
        web_assets.module_path("helpers.js")
    # A SHEET NAME NOTHING DECLARES IS REFUSED THE SAME WAY, and the refusal
    # says ASSET rather than MODULE (Copilot review, round 2): since RULED Q7
    # this function answers for both kinds, and a diagnostic that calls a
    # missing stylesheet a "view module" points an operator at the wrong
    # package-data line.
    with pytest.raises(web_assets.ViewAssetError) as undeclared:
        web_assets.module_path("gate-lens.css")
    assert "view asset" in str(undeclared.value)
    assert "module" not in str(undeclared.value).split("view asset")[0]


# ---------------------------------------------------------------------------
# RULED Q5 — the DECLARED HOSTED FALLBACK. "a contributed GET route is the
# declared hosted fallback."
# ---------------------------------------------------------------------------

def test_the_hosted_fallback_claims_exactly_this_columns_declared_paths() -> None:
    """RULED Q5's fallback, over RULED Q7's assets too: a deployment that cannot
    write into openDox's bundle receives neither the modules nor the sheets, and
    a fallback answering only for `.js` would serve that deployment a gate loop
    with no appearance and no error."""
    pytest.importorskip(
        "route_extension",
        reason="`route_extension` is supplied by the pinned opendox wheel; "
               "the binding shape cannot be built without it")
    from openxdox import serve_views

    bindings = serve_views.view_module_bindings()
    assert [b.pattern for b in bindings] == [
        f"/{web_assets.BUNDLE_SUBDIR}/{name}"
        for name in web_assets.VIEW_ASSET_NAMES]
    for binding in bindings:
        assert binding.method == "GET"
        # NEVER A PREFIX. openDox consults contributed routes before its static
        # fallback, so a `/views/` prefix binding would make this column answer
        # for the shell's own modules.
        assert binding.is_prefix is False, (
            f"{binding.pattern} is a prefix binding: this column would "
            "intercept openDox's own view modules")
        assert binding.handler == "_serve_contributed_view_module"
    assert serve_views.ViewModuleRoutesExtension().routes() == bindings
    # ONE MEDIA TYPE PER SUFFIX, and the sheet's is not the module's: a browser
    # in standards mode DROPS a stylesheet served as anything but `text/css`,
    # and the symptom is an unstyled panel with no error event at all.
    assert serve_views.CTYPES == {".js": serve_views.JS_CTYPE,
                                  ".css": serve_views.CSS_CTYPE}
    assert "text/css" in serve_views.CSS_CTYPE
    # AND THE HANDLER'S OWN CONTRACT SAYS SO (Copilot review, round 3): a
    # docstring promising only `/views/<module>.js` documents the CSS path as
    # unsupported, and a later change could reintroduce a JS-only assumption
    # without contradicting anything written down.
    doc = serve_views.ContributedViewModuleRoutes \
        ._serve_contributed_view_module.__doc__
    assert ".css" in doc and ".js" in doc, doc


def test_the_hosted_fallback_serves_only_declared_names() -> None:
    pytest.importorskip("route_extension")
    from openxdox import serve_views

    class Probe(serve_views.ContributedViewModuleRoutes):
        def __init__(self, path):
            self.path = path
            self.served = None
            self.errored = None

        def _serve_bytes(self, body, ctype, head_only):
            self.served = (body, ctype, head_only)

        def send_error(self, code, message):
            self.errored = (code, message)

    ok = Probe("/views/gate.js?v=1")
    ok._serve_contributed_view_module(False)
    assert ok.errored is None
    assert ok.served[0] == web_assets.module_source("gate.js")
    assert ok.served[1] == serve_views.JS_CTYPE

    traversal = Probe("/views/../../etc/passwd")
    traversal._serve_contributed_view_module(False)
    assert traversal.served is None and traversal.errored[0] == 404

    other_leg = Probe("/views/app.js")
    other_leg._serve_contributed_view_module(False)
    assert other_leg.served is None and other_leg.errored[0] == 404

    # AND A DECLARED SHEET, THROUGH THE SAME HANDLER (Copilot review, round 1).
    # Asserting the `CTYPES` table alone left the `.css` branch of
    # `_serve_contributed_view_module` unexercised: a regression in the suffix
    # lookup, in the bytes, or in the content type would pass while every
    # hosted stylesheet was served as `text/javascript` — which a browser in
    # standards mode answers by DROPPING the sheet, with no error event and an
    # unstyled panel as the only symptom.
    sheet = Probe("/views/gate.css")
    sheet._serve_contributed_view_module(False)
    assert sheet.errored is None
    assert sheet.served[0] == web_assets.module_source("gate.css")
    assert sheet.served[1] == serve_views.CSS_CTYPE
    assert sheet.served[1] != serve_views.JS_CTYPE
    # every declared sheet, not just the one above
    for name in web_assets.VIEW_SHEET_NAMES:
        probe = Probe(f"/views/{name}")
        probe._serve_contributed_view_module(True)
        assert probe.errored is None, name
        assert probe.served[1] == serve_views.CSS_CTYPE, name
        assert probe.served[2] is True, name


# ---------------------------------------------------------------------------
# The six bindings — the DECLARATION half.
# ---------------------------------------------------------------------------

def test_the_six_bindings_are_declared_once_each() -> None:
    ids = [spec["id"] for spec in SPECS]
    assert len(ids) == 6 and len(set(ids)) == 6, ids
    assert set(ids) == set(EXPECTED_REGIONS)
    slots = [(spec["region"], spec["id"]) for spec in SPECS]
    assert len(set(slots)) == len(slots), f"(region, id) collision: {slots}"


def test_every_binding_is_class_b_optional_and_shell_region() -> None:
    """`optional: true` IS THE SLICE: "a student install comes up with no gate
    bar, no dispose tray, no session verbs, and no 404". And every region is a
    `shell` one, so RULED Q1's generic mount pass — which mounts contributed
    `dom`-region bindings — never reaches them: each is mounted by the caller
    that builds its host, the gate bar's pattern Q1 keeps."""
    for spec in SPECS:
        assert spec["view_class"] == "B", spec["id"]
        assert spec["optional"] is True, spec["id"]
        assert spec["region"] == EXPECTED_REGIONS[spec["id"]], spec["id"]


def test_every_binding_names_a_module_this_package_ships() -> None:
    for spec in SPECS:
        module = spec["module"]
        assert module.startswith("./views/") and module.endswith(".js"), module
        assert module.split("/")[-1] in web_assets.VIEW_MODULE_NAMES, module


def test_every_declared_route_is_this_columns_and_nothing_is_computed() -> None:
    """RULED Q12 (`5648065587`): "a COMPUTED route is declared as its LITERALS:
    the dispose binding declares four `/actions/gate/<verb>` routes; no prefix
    semantics on the declaring side; assertion 2's grep sees them."

    Seventeen routes: openDox-spec § 1.2(c)'s thirteen constants plus Q12's
    four literals.
    """
    routes = view_extensions.declared_routes()
    assert len(routes) == 17, routes
    assert len(set(routes)) == 17, "a route is declared twice"
    for route in routes:
        assert route.startswith(GATE_PREFIX), route
        assert not route.endswith("/"), f"{route} is a prefix, not a literal"

    dispose = next(s for s in SPECS if s["id"] == "gate.dispose")
    for verb in ("promote-to-staging", "research-brief", "derive-possibles",
                 "demote"):
        assert GATE_PREFIX + verb in dispose["routes"], verb


def test_the_dispose_module_no_longer_computes_a_gate_route() -> None:
    """The other half of Q12: the literals are IN THE MODULE, so § 4.5
    assertion 2's grep — which greps for route literals — can see them."""
    text = _module_text("dispose.js")
    code = "\n".join(line for line in text.splitlines()
                     if not line.lstrip().startswith("//"))
    assert '"/actions/gate/" +' not in code, (
        "dispose.js still composes a gate route; RULED Q12 requires the four "
        "verbs to be declared as literals")
    for verb in ("promote-to-staging", "research-brief", "derive-possibles",
                 "demote"):
        assert f'"{GATE_PREFIX}{verb}"' in text, verb


def test_every_binding_declares_the_routes_its_module_names() -> None:
    """RULED Q3 of the boundary note's own sitting — "a route constant travels
    with the binding that calls it" — checked in the one place both facts are
    visible: the module's literals and the binding's declaration."""
    for spec in SPECS:
        text = _module_text(spec["module"].split("/")[-1])
        in_module = set(re.findall(r'"(/actions/gate/[a-z0-9-]+)"', text))
        declared = set(spec["routes"])
        assert in_module == declared, (
            f"{spec['id']}: the module names {sorted(in_module)} and the "
            f"binding declares {sorted(declared)}")


# ---------------------------------------------------------------------------
# RULED Q2 — "a binding's contract is its module NAMESPACE, DECLARED as an
# `exports` tuple: every export the shell may reach is listed on the binding
# and validated the way `entry` is; an undeclared reach (today `isGateBearing`,
# app.js:939) is a refusal."
# ---------------------------------------------------------------------------

def test_every_declared_export_is_really_exported_and_the_entry_is_one() -> None:
    for spec in SPECS:
        name = spec["module"].split("/")[-1]
        real = _exported_names(_module_text(name))
        missing = sorted(set(spec["exports"]) - real)
        assert missing == [], (
            f"{spec['id']} declares export(s) {missing} that {name} does not "
            "export — a binding that cannot be reached must not look declared")
        assert spec["entry"] in spec["exports"], (
            f"{spec['id']}'s entry {spec['entry']!r} is not in its own "
            "`exports` tuple: Q2 makes the tuple the WHOLE namespace the shell "
            "may reach, and the entry is the first member of it")


def test_the_two_reaches_the_shell_makes_past_a_mount_are_named() -> None:
    """The two exports RULED Q2 and Q10 exist for, named on the bindings that
    carry them rather than reached through a namespace nothing validated."""
    gate = next(s for s in SPECS if s["id"] == "gate.bar")
    assert "isGateBearing" in gate["exports"], (
        "RULED Q2: `isGateBearing` was openDox `app.js`'s undeclared reach; it "
        "is declared or it is a refusal")
    session = next(s for s in SPECS if s["id"] == "gate.workbench.session")
    assert "firstEditTransport" in session["exports"], (
        "RULED Q10 (5648065587): app.js:57's `firstEditTransport` travels as a "
        "DECLARED NON-MOUNT EXPORT of the workbench binding")


def test_the_declared_exports_cover_every_reach_openDox_makes() -> None:
    """The shell's side of the contract, stated here so this leg knows what it
    owes. These are the names openDox's `app.js`, `views/wheel.js` and
    `views/staging-workbench.js` reached by a STATIC IMPORT at openDox-code
    `cb343ae8` and now reach through the registry."""
    owed = {
        "gate.bar": {"mountGateBar", "isGateBearing"},
        "gate.dispose": {"appliedOutcome", "commissionedVerb",
                         "commissionedWorkflow", "gateCapable",
                         "mountDisposeTray", "mountProposeButton",
                         "mountWheelVerb", "panelEntry"},
        "gate.workbench.create": {"mountCreateAffordance", "openCreateDialog",
                                  "createGateLive"},
        "gate.workbench.session": {"createdDocuments", "documentCreated",
                                   "endedSessions", "mountSessionAffordances",
                                   "openedSessions", "sessionOpened",
                                   "firstEditTransport"},
    }
    for binding_id, names in owed.items():
        spec = next(s for s in SPECS if s["id"] == binding_id)
        missing = sorted(names - set(spec["exports"]))
        assert missing == [], (
            f"{binding_id} owes openDox {missing}: the shell reached them by a "
            "static import before this slice and reaches them through the "
            "registry after it")


# ---------------------------------------------------------------------------
# RULED Q3 — "ONE mount signature, `mount(host, snapshot, ctx)`; the gate bar's
# `(container, ctx, opts)` is recorded as the one declared exception until S5
# rewrites it."
# ---------------------------------------------------------------------------

def test_every_entry_takes_the_one_mount_signature() -> None:
    for spec in SPECS:
        name = spec["module"].split("/")[-1]
        text = _module_text(name)
        pattern = (r"export\s+function\s+" + re.escape(spec["entry"])
                   + r"\s*\(\s*host\s*,\s*snapshot\s*,\s*ctx\s*\)")
        assert re.search(pattern, text), (
            f"{spec['id']}'s entry {spec['entry']} in {name} does not take "
            "`(host, snapshot, ctx)` — RULED Q3 leaves the shell ONE mount "
            "shape, and this slice is where the gate bar's declared exception "
            "ends")


def test_the_gate_bars_declared_exception_is_gone() -> None:
    text = _module_text("gate.js")
    assert "mountGateBar(container, ctx, opts)" not in text
    assert "export function mountGateBar(host, snapshot, ctx)" in text


# ---------------------------------------------------------------------------
# RULED Q4 — "`requires` names DOTTED PATHS into the `/capabilities` payload;
# unmet + `optional: true` renders the region empty with a NAMED reason; unmet +
# required REFUSES."
# ---------------------------------------------------------------------------

def test_every_requires_entry_is_a_dotted_capabilities_path() -> None:
    for spec in SPECS:
        for path in spec["requires"]:
            assert re.fullmatch(r"[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)+", path), (
                f"{spec['id']} requires {path!r}: RULED Q4 makes `requires` a "
                "DOTTED PATH into the /capabilities payload, and a bare key is "
                "the spelling the docstring guessed at and the estate never used")


def test_the_bindings_that_degrade_to_a_descriptor_require_nothing() -> None:
    """The correction this slice makes, and why it is a correction rather than a
    regression. openDox's transitional core-arm entry declared
    `requires: ["actions.gate"]` on the gate bar while NOTHING read it — the
    counterpart note's own § 4.4 finding. Q4 makes the shell ACT on it, so the
    declaration has to become true: a binding that renders a CLI descriptor
    without the capability does not require the capability to mount, and
    declaring it would delete the read-only gate surface on every hosted plane."""
    for binding_id in ("gate.bar", "gate.workbench.create",
                       "gate.workbench.session", "gate.dispose"):
        spec = next(s for s in SPECS if s["id"] == binding_id)
        assert spec["requires"] == (), (
            f"{binding_id} degrades to a descriptor without its capability, so "
            "requiring it would remove a surface that works")
    for binding_id in ("gate.lens", "gate.projects"):
        spec = next(s for s in SPECS if s["id"] == binding_id)
        assert spec["requires"] == ("actions.gate",), (
            f"{binding_id} mounts a live gate control or nothing, so the "
            "capability is a genuine mount requirement")


def test_the_dispose_binding_resolves_on_the_hosted_intent_plane() -> None:
    """THE FOURTH BINDING THAT MUST NOT REQUIRE THE GATE, and the reason is
    different from the other three's (Copilot review of this PR, round 2).

    `gate.bar`, `gate.workbench.create` and `gate.workbench.session` degrade to a
    read-only descriptor. `gate.dispose` does something else: it serves TWO
    mutually exclusive transports, the LOCAL executing gate (`actions.gate`,
    loopback) and the HOSTED intent plane (`actions.intent`, which openDox's
    `serve.py` computes as `intent = not loopback`). openDox's `views/wheel.js`
    mounts this namespace's tray when `gateCapable(caps) || intentCapable(caps)`
    and hands it the hosted emitter in the second case, so a
    `requires: ["actions.gate"]` would make `resolveView` answer `null` on
    exactly the plane the intent work exists for — taking the tray, its chips
    and `panelEntry`'s refusal surface with it."""
    spec = next(s for s in SPECS if s["id"] == "gate.dispose")
    assert spec["requires"] == ()
    # and the module really does carry both transports, so the claim above is
    # about this file rather than about a comment in it
    text = _module_text("dispose.js")
    assert "o.intent" in text, "the hosted transport's own branch"
    assert "gateCapable" in text, "the local transport's own capability read"


# ---------------------------------------------------------------------------
# RULED Q8 — "a fourth `shell` region, `page-overlay`, is the declared host for
# page-level panels (dispose.js's refusal panel); `document.body` is never a
# contract surface."
# ---------------------------------------------------------------------------

def test_the_refusal_panel_mounts_into_a_declared_region() -> None:
    text = _module_text("dispose.js")
    code = "\n".join(line for line in text.splitlines()
                     if not line.lstrip().startswith("//"))
    assert "document.body" not in code, (
        "dispose.js still reaches `document.body`: RULED Q8 makes that never a "
        "contract surface, and the refusal panel's host is the shell's "
        "`page-overlay` element")
    assert "export function mountRefusalPanel(host, snapshot, ctx)" in text
    dispose = next(s for s in SPECS if s["id"] == "gate.dispose")
    assert dispose["region"] == "page-overlay"
    assert dispose["entry"] == "mountRefusalPanel"


# ---------------------------------------------------------------------------
# RULED Q9 — "`wheel-intent` / `dispose-intent` stay DECLARED in both REGIONS
# tables, recorded as unhosted and unread today."
# ---------------------------------------------------------------------------

def test_this_column_names_neither_unhosted_region() -> None:
    """The record on THIS side of the seam: S5 is not the slice that retires
    S2's provision, and a binding naming either would mount into nothing."""
    named = {spec["region"] for spec in SPECS}
    assert not named & {"wheel-intent", "dispose-intent"}, (
        "a binding names one of the two declared-but-unhosted regions; RULED "
        "Q9 keeps them declared for a future intent panel, and a panel bound "
        "to one today mounts into nothing, silently")


# ---------------------------------------------------------------------------
# Counterpart Q6 — what a contributed module may IMPORT from the bundle.
# ---------------------------------------------------------------------------

def test_no_module_imports_anything_but_the_one_guaranteed_bundle_module() -> None:
    """RULED counterpart Q6, the whole of it: "`./views/helpers.js` and NOTHING
    ELSE". A specifier naming a module of THIS column is not a bundle reach at
    all — the assembly (RULED Q5) places both side by side — and every other
    specifier is a reach into a module openDox owns, may move and may rename."""
    own = {f"./{name}" for name in web_assets.VIEW_MODULE_NAMES}
    offenders: dict[str, tuple[str, ...]] = {}
    for name in web_assets.VIEW_MODULE_NAMES:
        reach = tuple(sorted(
            path for path in _relative_imports(_module_text(name))
            if path != view_extensions.GUARANTEED_BUNDLE_MODULE
            and path not in own))
        if reach:
            offenders[name] = reach
    assert offenders == {}, (
        "a contributed module imports openDox's bundle past the guarantee: "
        f"{offenders}. RULED counterpart Q6 (openxFactory#656 comment "
        "5649094228): `./views/helpers.js` and nothing else; every other need "
        "reaches the binding through its `ctx` or its own package")


def test_the_bundle_reach_is_exactly_declared() -> None:
    """The reach is NAMED as well as narrow: what each module imports is what
    `BUNDLE_REACH` says it imports, so a widening shows up as a failing
    declaration and not only as a failing rule."""
    observed = {name: tuple(sorted(_relative_imports(_module_text(name))))
                for name in web_assets.VIEW_MODULE_NAMES}
    declared = {name: tuple(sorted(paths))
                for name, paths in view_extensions.BUNDLE_REACH.items()}
    assert observed == declared, (
        "this column's reach into openDox's bundle moved.\n"
        f"declared: {declared}\nobserved: {observed}")


def test_every_binding_declares_what_it_asks_the_shell_for() -> None:
    """Counterpart Q6's other half: what left the import list arrived on `ctx`,
    and `CTX_MODEL_REACH` is the whole of it. Every binding has an entry (an
    absent one would be a silence, not a zero) and every name it declares is
    really read out of `ctx` by the module that declares it."""
    ids = {spec["id"] for spec in view_extensions.VIEW_BINDING_SPECS}
    assert set(view_extensions.CTX_MODEL_REACH) == ids

    module_of = {spec["id"]: spec["module"].rsplit("/", 1)[-1]
                 for spec in view_extensions.VIEW_BINDING_SPECS}
    for binding_id, facets in view_extensions.CTX_MODEL_REACH.items():
        text = _module_text(module_of[binding_id])
        for facet, names in facets.items():
            for name in names:
                assert f'"{name}"' in text or f".{name}" in text, (
                    f"{binding_id} declares ctx.{facet}.{name} and "
                    f"{module_of[binding_id]} never reads it")


def test_the_three_reaches_the_ruling_closed_are_gone_from_every_module() -> None:
    """The three class-A modules this column used to import BY NAME —
    `lens-model.js`, `intent-binding.js`, `staging-workbench-model.js` — are
    named in no module's import list and in no binding's declared reach. The
    record at `01b06c94` carried all three as measured residue; RULED
    counterpart Q6 granted no guarantee list, so they became `ctx` facets."""
    closed = ("./lens-model.js", "./intent-binding.js",
              "./staging-workbench-model.js")
    for name in web_assets.VIEW_MODULE_NAMES:
        imports = _relative_imports(_module_text(name))
        for specifier in closed:
            assert specifier not in imports, (name, specifier)
    for paths in view_extensions.BUNDLE_REACH.values():
        for specifier in closed:
            assert specifier not in paths, specifier


def test_the_session_vocabulary_is_declared_by_the_binding_that_posts_it() -> None:
    """The six affordance tokens key this module's OWN route table at module
    scope and name the gate verbs this column's own `serve_gate.py` answers, so
    they are declared here rather than taken from `ctx` (RULED Q3's precedent
    from slice S4: a constant travels with the binding that calls it). The
    verbs are held to `gate_routes.SESSION_BEARING_VERBS` so the two halves of
    this column cannot drift apart.

    `gate_routes.py` is PARSED, never imported — it reaches `gate_console` and
    `doc_health` at import time, and this suite runs `--noconftest` against this
    package's own files. The same posture `test_no_hardcoded_status_words.py`
    takes with `generator.py`."""
    session_bearing = _module_constant(
        Path(view_extensions.__file__).with_name("gate_routes.py"),
        "SESSION_BEARING_VERBS")

    text = _module_text("swb-session.js")
    for token in ("SESSION_EDIT", "SESSION_SAVE", "SESSION_ABANDON",
                  "SESSION_SHARE", "SESSION_FIRST_EDIT",
                  "SESSION_REFRESH_NOTEBOOK", "SESSION_AFFORDANCES",
                  "SESSION_VERBS", "SESSION_LABELS"):
        assert re.search(rf"^export const {token}\b", text, re.M), token
    verbs = re.findall(r'\]: "([a-z-]+)",', text)
    for verb in ("edit-document", "open-pr", "abandon-session",
                 "share-session"):
        assert verb in verbs, verb
        assert verb in session_bearing, verb


def test_the_style_residue_records_the_discharge_rather_than_the_block() -> None:
    """RULED Q7 IS realized now, and the record says so where it said blocked.

    The `blocked_by` sentence this table carried ("styles.css is a
    moved_verbatim carve row; no edit class covers a stylesheet block leaving
    for another leg") is GONE, and it is gone because the premise is: slice S7
    converted that row to `moved_with_declared_edit`. Asserting the absence
    rather than deleting the test is the point — a successor that re-blocks
    this work has to say so here.
    """
    residue = view_extensions.STYLE_RESIDUE
    assert residue["blocked_by"] is None
    assert residue["exclusive_classes"] == 54
    # 18, not 21: openxFactory #1068's round 5 narrowed the census's gate-side
    # scan again and `g`, `lens` and `topic` were shared only through a dotted
    # view id, a sentence's `.g` and a `btn.title` string. What LEAVES is
    # unchanged — the three assertions below say so.
    assert residue["shared_classes"] == 18
    assert residue["rule_blocks_moved"] == 59
    assert residue["mixed_blocks_handled"] == 2
    assert residue["rule_blocks_in_sheets"] == 61
    assert (residue["rule_blocks_moved"] + residue["mixed_blocks_handled"]
            == residue["rule_blocks_in_sheets"])
    # THE RULING IS CITED WHERE THE DECISION IS STATED (RULED openxFactory#656
    # comment `5700475319`, Brett Heap, 2026-09-16, by interactive
    # multi-choice). Both halves of this act that were put to him — the
    # verbatim move with the coupling REGISTERED, and the four-sheet shape —
    # are his answers rather than this column's preference, and a reader of the
    # residue must be able to see that without leaving the file.
    for module in (view_extensions, web_assets):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "5700475319" in source, module.__name__
    assert residue["styles_css_lines_declared"] == 89
    assert residue["sheets"] == web_assets.VIEW_SHEET_NAMES
    assert "RULED Q7 realized" in residue["discharged_by"]
    # The census it moved FROM is named with the defect it carried, so the
    # figures cannot look like a silent re-measurement.
    assert "cb343ae8" in residue["previously_measured_at"]
    assert "concatenation" in residue["previously_measured_at"]


# ---------------------------------------------------------------------------
# RULED Q7 — the sheets themselves.
# ---------------------------------------------------------------------------

SHEET_DIR = Path(view_extensions.__file__).with_name("web") / "views"


def _sheet_text(name: str) -> str:
    return (SHEET_DIR / name).read_text(encoding="utf-8")


def _sheet_body(name: str) -> str:
    """The sheet with its `/* … */` prose blanked, newlines kept."""
    text, out, i, n = _sheet_text(name), [], 0, 0
    n = len(text)
    while i < n:
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", text[i:j]))
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def test_the_package_data_globs_cover_every_declared_asset() -> None:
    """A TYPO IN `pyproject.toml` LEAVES THIS SUITE GREEN AND THE WHEEL EMPTY
    (Copilot review, round 1).

    Every asset test above reads `src/openxdox/web/views/` directly, so none of
    them touches `[tool.setuptools.package-data]`. Drop the `*.css` pattern and
    a source checkout still passes while the built wheel carries four bindings
    whose sheets cannot load — and `module_path()`'s own refusal message is
    written for exactly that day. The patterns are read from the real file and
    matched against the real declared set, which is the check a wheel build
    would make without needing one.
    """
    # ANCHORED ON THIS FILE, not on the package: `view_extensions.__file__`
    # points into site-packages under a non-editable install, where there is no
    # `pyproject.toml` to read — and this suite runs `--noconftest` from the
    # checkout, whose root is this file's parent's parent.
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if not pyproject.is_file():
        pytest.skip("no `pyproject.toml` beside `tests/`: this is an installed "
                    "tree, and the pattern it declares is not there to read")
    text = pyproject.read_text(encoding="utf-8")
    block = re.search(r"^\[tool\.setuptools\.package-data\]\s*$(.*?)(?=^\[|\Z)",
                      text, re.M | re.S)
    assert block, "pyproject.toml declares no [tool.setuptools.package-data]"
    patterns = re.findall(r'"([^"]+)"', block.group(1))
    assert patterns, block.group(1)
    # A package-data pattern is relative to the PACKAGE directory, so the path
    # to match is `web/views/<name>` — DERIVED from `VIEW_MODULE_DIR` rather
    # than spelled here, or this test would carry a second copy of the layout
    # it is checking.
    package_dir = Path(web_assets.__file__).resolve().parent
    subdir = web_assets.VIEW_MODULE_DIR.resolve().relative_to(package_dir)
    # `fnmatch` IS NOT PATH-AWARE, and setuptools' globbing is (Copilot
    # review, round 7). `fnmatch.fnmatch("web/views/gate.css", "web/*.css")`
    # is TRUE because `*` there matches `/` like any other character, while a
    # package-data pattern of `web/*.css` does NOT cover a file one directory
    # down — so this guard would have passed a declaration that leaves the
    # sheets out of the wheel, which is the single failure it exists to catch.
    # Matching SEGMENT BY SEGMENT is the fix: each pattern segment is matched
    # against the corresponding path segment, and only a `**` segment spans
    # separators.
    def _covers(pattern: str, rel_path: str) -> bool:
        pattern_parts = pattern.split("/")
        path_parts = rel_path.split("/")
        if "**" in pattern_parts:
            head = pattern_parts[:pattern_parts.index("**")]
            tail = pattern_parts[pattern_parts.index("**") + 1:]
            if len(path_parts) < len(head) + len(tail):
                return False
            pairs = list(zip(head, path_parts[:len(head)]))
            pairs += list(zip(tail, path_parts[len(path_parts) - len(tail):]
                              if tail else []))
        else:
            if len(pattern_parts) != len(path_parts):
                return False
            pairs = list(zip(pattern_parts, path_parts))
        return all(fnmatch.fnmatch(part, glob) for glob, part in pairs)

    # the guard's own guard: the defect it was blind to must now be caught
    assert not _covers("web/*.css", "web/views/gate.css")
    assert _covers("web/views/*.css", "web/views/gate.css")
    assert _covers("web/**/*.css", "web/views/gate.css")

    for name in web_assets.VIEW_ASSET_NAMES:
        rel = f"{subdir.as_posix()}/{name}"
        assert any(_covers(pattern, rel) for pattern in patterns), (
            f"{rel!r} is declared in `VIEW_ASSET_NAMES` and matches no "
            f"package-data pattern {patterns}: it would be missing from the "
            "built wheel while every test in this file, which reads the source "
            "tree, stayed green")


def test_every_declared_sheet_ships_and_every_shipped_sheet_is_declared() -> None:
    """`VIEW_MODULE_NAMES`' own rule, applied to the sheets: a file nothing
    declares is a file shipped into another leg's bundle with no binding naming
    it, and a glob is how that happens quietly."""
    declared = set(web_assets.VIEW_SHEET_NAMES)
    shipped = {p.name for p in SHEET_DIR.glob("*.css")}
    assert declared == shipped, (declared ^ shipped)
    for name in declared:
        assert (SHEET_DIR / name).is_file()


def test_each_binding_names_the_sheet_that_carries_its_own_selectors() -> None:
    """RULED Q7's placement, held to the census rather than to a list.

    FOUR sheets for six bindings, and both departures from one-each are
    measured: `gate.lens` names none because `gate-lens.js` owns no selector of
    its own, and the two workbench bindings name the SAME sheet because eleven
    of its nineteen blocks are named by both modules. openDox's registry
    dedupes the injected link by href, so the second naming costs nothing.
    """
    by_id = {spec["id"]: spec.get("styles", "") for spec in SPECS}
    assert by_id == {
        "gate.bar": "./views/gate.css",
        "gate.lens": "",
        "gate.projects": "./views/gate-projects.css",
        "gate.dispose": "./views/dispose.css",
        "gate.workbench.create": "./views/swb.css",
        "gate.workbench.session": "./views/swb.css",
    }
    for spec in SPECS:
        sheet = spec.get("styles", "")
        if not sheet:
            continue
        assert sheet.startswith("./views/") and sheet.endswith(".css"), sheet
        assert sheet[len("./views/"):] in web_assets.VIEW_SHEET_NAMES, sheet


def test_no_contributed_sheet_declares_a_design_token() -> None:
    """RULED Q7: the `--st-*` family is openDox's ONE stable styling surface.

    A contributed sheet READS `var(--st-…)` — that is what the surface is for —
    and never WRITES one: `views/display.js`'s `applyTokens` is already the one
    authority, and a second would shadow a host's declared role per theme.
    """
    for name in web_assets.VIEW_SHEET_NAMES:
        written = _declared_st_tokens(_sheet_body(name))
        assert written == [], f"{name} declares {written}"


#: A DECLARATION FOLLOWS THE START OF THE TEXT, A `{`, OR A `;` — never only a
#: newline (Copilot review, round 1). These sheets are written one rule per
#: line, so `.x { --st-proposed: red; }` declares the token after a `{` and a
#: second one after a `;`, and a `^\s*` scan saw neither. `(` is deliberately
#: not in the list: that is what bounds a `var()` READ, which RULED Q7 permits
#: and this guard must not catch.
_ST_DECLARATION = re.compile(r"(?:^|[{;])\s*(--st-[A-Za-z0-9_-]+)\s*:")


def _declared_st_tokens(css: str) -> list[str]:
    """Every `--st-*` a sheet WRITES. Comments must already be blanked."""
    return _ST_DECLARATION.findall(css)


def test_the_design_token_guard_sees_an_inline_declaration() -> None:
    """The guard above is worth running only if it catches the shape these
    sheets are actually written in. Asserted, because a guard that cannot fail
    is a comment."""
    assert _declared_st_tokens(".x { --st-proposed: red; }") == ["--st-proposed"]
    assert _declared_st_tokens("a{color:red;--st-captured:blue}") == ["--st-captured"]
    assert _declared_st_tokens("  --st-organized: green;") == ["--st-organized"]
    assert _declared_st_tokens(".x { color: var(--st-proposed); }") == []


def test_the_sheets_carry_the_blocks_the_residue_counts() -> None:
    """61 RULE BLOCKS, AND THE RECORD SAYS WHY IT IS NOT 59 (Copilot review,
    round 3, which counted the shipped bytes against the recorded figure).

    59 blocks are the EXCLUSIVE ones — every class in the selector this
    column's own. The other two are the file's only MIXED rules and were
    handled rather than exempted: one selector list SPLIT, so openDox keeps
    `.filterpop[hidden]` and this column re-states the gate half; and
    `.swb-draftchrome .swb-cactions` MOVED WHOLE, carrying the one openDox
    class a sheet here names as host context.

    Counted off the shipped sheets, so the audit record cannot silently
    disagree with the bytes.
    """
    blocks = 0
    for name in web_assets.VIEW_SHEET_NAMES:
        body = _sheet_body(name)
        blocks += body.count("{")
        assert body.count("{") == body.count("}"), name
    residue = view_extensions.STYLE_RESIDUE
    assert blocks == residue["rule_blocks_in_sheets"], blocks
    assert blocks == residue["rule_blocks_moved"] + residue["mixed_blocks_handled"]

    # THE TWO MIXED RULES ARE WHERE THE RECORD SAYS, not merely counted.
    projects = _sheet_body("gate-projects.css")
    assert ".projectform.projectpanel[hidden]" in projects
    swb = _sheet_body("swb.css")
    for host in residue["open_coupling"]["host_context_classes"]:
        assert f".{host} " in swb, host


def test_every_sheet_header_declares_the_host_context_exception() -> None:
    """The headers said every selector's classes are this column's own, and
    `swb.css` carries `.swb-draftchrome .swb-cactions` (Copilot review, round
    3). A sheet whose own prose contradicts the census is worse than one with
    no prose."""
    for name in web_assets.VIEW_SHEET_NAMES:
        header = _sheet_text(name)
        assert "WITH ONE DECLARED EXCEPTION" in header, name
        assert "host_context_classes" in header, name
        # and the tool is named as it is committed, not as it was drafted
        assert "scripts/measure_opendox_css_census.py" in header, name
        assert "measure-css-census.py" not in header, name


def test_the_non_token_coupling_is_the_number_the_residue_records() -> None:
    """The one thing RULED Q7 leaves open here, COUNTED instead of hidden.

    These sheets read openDox's non-token custom properties, which Q7's own
    sentence says are not a stable surface. Inlining their values would end dark
    mode for this column on every install, so the reads stay — and the count is
    pinned, so a new one arrives as a red test and a decision rather than as a
    quiet widening of the coupling.
    """
    read: set[str] = set()
    for name in web_assets.VIEW_SHEET_NAMES:
        read.update(re.findall(r"var\(\s*(--[A-Za-z0-9_-]+)", _sheet_body(name)))
    tokens = {p for p in read if p.startswith("--st-")}
    non_token = read - tokens
    residue = view_extensions.STYLE_RESIDUE["open_coupling"]
    assert len(tokens) == residue["st_tokens_read"], sorted(tokens)
    assert len(non_token) == residue["non_token_custom_properties_read"], \
        sorted(non_token)


def test_a_pin_that_carries_styles_materializes_the_declared_sheets(
        monkeypatch) -> None:
    """THE NEW-PIN BRANCH, EXECUTED (Copilot review, round 3).

    `GateLoopViews.views()` is where `specs_for()`'s answer becomes real
    bindings, and nothing ELSE drives it with a `ViewBinding` that HAS
    `styles`: the three live materialization assertions below read region,
    routes, exports, requires and the manifest ids — never the SHEET — and the
    `specs_for` test drives the filter and not the constructor. So a regression
    between the two — a spec the filter kept that the constructor drops — would
    leave the sheets inert with every test green.

    Driven through a STUB `opendox.view_extension`. This paragraph read
    "because the pin bump that brings the real one is a later act and this
    assertion must not wait for it", and that bump has since landed
    (`0b4e8bbf` -> `5c137a90`, openXdox-code#24, openDox-code#27's field). THE
    STUB STAYS: what it holds is the constructor's behaviour for a binding that
    CARRIES the field, and an ASSEMBLY chooses the `opendox` this column runs
    under — so both shapes must be driven from either pin, which is the same
    reason `test_an_old_pin_materializes_without_the_field` below is a stub too.
    """
    import types

    @dataclasses.dataclass(frozen=True)
    class StubBinding:
        id: str = ""
        region: str = ""
        module: str = ""
        entry: str = ""
        view_class: str = ""
        routes: tuple = ()
        exports: tuple = ()
        requires: tuple = ()
        optional: bool = False
        styles: str = ""

    stub = types.ModuleType("opendox.view_extension")
    stub.ViewBinding = StubBinding
    package = types.ModuleType("opendox")
    package.view_extension = stub
    monkeypatch.setitem(sys.modules, "opendox", package)
    monkeypatch.setitem(sys.modules, "opendox.view_extension", stub)

    bindings = view_extensions.GateLoopViews().views()
    assert [b.id for b in bindings] == [spec["id"] for spec in SPECS]
    assert [b.styles for b in bindings] == [
        "./views/gate.css", "", "./views/gate-projects.css",
        "./views/dispose.css", "./views/swb.css", "./views/swb.css"]
    # every declared sheet is reached by at least one binding, and no binding
    # names a sheet this column does not ship
    named = {b.styles[len("./views/"):] for b in bindings if b.styles}
    assert named == set(web_assets.VIEW_SHEET_NAMES)


def test_an_old_pin_materializes_without_the_field(monkeypatch) -> None:
    """The other side of the same call path: a `ViewBinding` with no `styles`
    still materializes the whole column, unstyled rather than absent."""
    import types

    @dataclasses.dataclass(frozen=True)
    class OldBinding:
        id: str = ""
        region: str = ""
        module: str = ""
        entry: str = ""
        view_class: str = ""
        routes: tuple = ()
        exports: tuple = ()
        requires: tuple = ()
        optional: bool = False

    stub = types.ModuleType("opendox.view_extension")
    stub.ViewBinding = OldBinding
    package = types.ModuleType("opendox")
    package.view_extension = stub
    monkeypatch.setitem(sys.modules, "opendox", package)
    monkeypatch.setitem(sys.modules, "opendox.view_extension", stub)

    bindings = view_extensions.GateLoopViews().views()
    assert [b.id for b in bindings] == [spec["id"] for spec in SPECS]
    assert not any(hasattr(b, "styles") for b in bindings)


def test_the_styles_field_is_dropped_for_a_pin_that_cannot_express_it() -> None:
    """RULED Q7's field REACHED THIS LEG'S PIN, and the drop path still runs.

    Driven against two stub `ViewBinding` shapes rather than against whatever
    `opendox` happens to be installed, so the behaviour is asserted at BOTH
    shapes from either pin — the one this leg pinned until openXdox-code#24
    (`0b4e8bbf`, no `styles`), which an assembly is still free to install, and
    the one it pins today (`5c137a90`, openDox-code#27), which carries it.
    This summary read "is NEWER THAN THIS LEG'S PIN" while that was true; it is
    corrected rather than quoted as provenance, because it was a claim about
    what is installed TODAY and the paragraph below carries the history.
    """
    @dataclasses.dataclass(frozen=True)
    class Old:
        id: str = ""
        styles_absent: bool = True

    @dataclasses.dataclass(frozen=True)
    class New:
        id: str = ""
        styles: str = ""

    dropped = view_extensions.specs_for(Old)
    assert all("styles" not in spec for spec in dropped)
    assert [spec["id"] for spec in dropped] == [spec["id"] for spec in SPECS]
    # and nothing else is lost with it
    assert [spec["exports"] for spec in dropped] == [spec["exports"] for spec in SPECS]

    kept = view_extensions.specs_for(New)
    assert kept == SPECS
    assert [spec.get("styles", "") for spec in kept] == [
        "./views/gate.css", "", "./views/gate-projects.css", "./views/dispose.css",
        "./views/swb.css", "./views/swb.css"]


def test_the_sheets_carry_no_remote_asset_and_no_import() -> None:
    """§ 4.4's vendor policy, at the one seam that could leak past it.

    `_SHEET` bounds the SPECIFIER a binding declares; nothing bounds what the
    sheet then fetches. A `url(https://…)`, an `@import` or a `src:` reaching
    out is a remote asset arriving through a door the module loader never sees,
    which is `test_renderer.py::test_no_external_urls_anywhere_in_bundle`'s
    subject one file over.
    """
    # CSS AT-RULES AND `url()` ARE CASE-INSENSITIVE (Copilot review, round 1):
    # `@IMPORT` and `URL(https://…)` are valid CSS and both evaded a lowercase
    # scan, which is the whole policy this test states. The scheme is folded
    # too, because `HTTPS://` is equally valid.
    for name in web_assets.VIEW_SHEET_NAMES:
        body = _sheet_body(name)
        assert not re.search(r"@import\b", body, re.I), name
        for url in re.findall(r"url\(([^)]*)\)", body, re.I):
            assert not re.match(r"\s*['\"]?(?:https?:)?//", url, re.I), (name, url)

    # AND THE SCAN CATCHES BOTH SPELLINGS, asserted rather than assumed.
    assert re.search(r"@import\b", "@IMPORT url(x);", re.I)
    assert re.match(r"\s*['\"]?(?:https?:)?//", "HTTPS://cdn.example/x.css", re.I)


# ---------------------------------------------------------------------------
# The materialization — against whatever `opendox` this assembly pinned.
# ---------------------------------------------------------------------------

def _view_extension_or_skip():
    """The assembled openDox's view registry, or — where it has none — whichever
    of FAIL and SKIP `tests/opendox_bundle.py::_absent` measures: FAIL for the
    commit this leg DECLARES and for an UNREADABLE SIDE (either commit) under CI;
    SKIP for a DIFFERENT commit and for an unreadable side OFF CI.

    This summary took two goes. It read "or SKIP where it has none", which
    contradicted the table four paragraphs down; the review of `42741fd` on #21
    caught that, and the review of `7c0a3b6` caught the replacement too — it said
    a skip was "only for a demonstrably different consumer" and dropped the
    off-CI unrecorded branch. All four rows are on the line now, because the
    summary is the line a reader trusts and a half-table is how it went wrong
    twice.

    ALL THREE REFUSAL BRANCHES ARE SATISFIED BY THIS LEG'S OWN PIN, since
    2026-09-16 (the module, the `ViewBinding` class, and RULED Q2's `exports`
    field — the enumeration is below; this line said "BOTH GUARDS" until the
    review of `8b9ece1`, having been written when there were two).
    They were not when slice S5 wrote them: the pin was `a99eba03`, the first
    reason read "this leg pins an `opendox` older than the § 3.4 slice S3 view
    registry" and the second said the bump "is owed at landing". The bump landed
    (`a99eba03` -> `0b4e8bbf`, openDox-code#23, § 3.4 slice S8 leg B) and the
    three assertions below went 3 skipped -> 3 passed under `validate.yml`'s own
    invocation. The old wording is quoted here as provenance, not asserted.

    THE GUARDS STAY, and that is RULED rather than preferred:
    RULED openxFactory#656 comment 5700475319 (Brett Heap, 2026-09-16, by
    interactive multi-choice) answered the question "keep the guards and correct
    their reasons, or delete them on pin lockstep #2's precedent" with
    (a) KEEP — because what they
    test is the ASSEMBLED openDox, not this leg's declared pin (the section header
    above says so), and an assembly is free to install an openDox behind the view
    contract. That is the same
    condition `view_extensions.ViewContractUnsupported` names at runtime, and
    the three refusal branches below are its test-time counterpart (the paragraph
    said "these two guards" until the review of `52453af`, having been written when
    there were two).

    BUT THEY NO LONGER SKIP BLINDLY. Copilot's round-1 review of openXdox-code#21
    was right that `pytest.importorskip` cannot tell a DIFFERENT assembly from "a
    regression in the openDox this leg DECLARES", and after the bump only the
    first of those may skip. (That review said "an older assembly"; the guard that
    replaced `importorskip` cannot measure ordering, only identity, so this summary
    stopped borrowing the word — the review of `cb84001` caught it here, the last
    copy left in the file.) If `5c137a90` — the leg this pin names now — lost
    `view_extension` or the `exports` field, all three assertions below would
    have gone quietly green in a required check.
    `tests/opendox_bundle.py::_absent` decides by READING the declared pin
    out of `pyproject.toml` and the installed commit out of the distribution's
    PEP 610 `direct_url.json`. This docstring said "different (or unrecorded) ->
    SKIP", and Copilot's round-3 review of #21 was right that the parenthesis is
    false: an UNREADABLE SIDE fails under CI and skips only off it, because a
    skip on the required path is the silent green the guard exists to prevent.
    The table `_absent()` actually carries: equal -> FAIL; different -> SKIP with
    both commits named; either side unreadable -> FAIL under CI naming WHICH side
    it was, SKIP off it.
    """
    import opendox_bundle
    try:
        from opendox import view_extension
    except ImportError:
        # FAIL at the declared pin, SKIP only for a different one. `importorskip`
        # could not tell those apart, and after the pin bump that difference is
        # the whole point: a packaging or API regression at the DECLARED leg —
        # `5c137a90` today — would have taken all three assertions below quietly
        # green in a required check.
        opendox_bundle._absent(
            "`opendox.view_extension` (§ 3.4 slice S3's view registry)",
            module_level=False)
    binding = getattr(view_extension, "ViewBinding", None)
    if binding is None:
        # THE MODULE WITHOUT ITS CLASS — a third unsupported shape, and until the
        # review of `24cd5f2` on #21 the only one that escaped this guard: the
        # class was dereferenced here directly, so an assembly shipping
        # `view_extension` without `ViewBinding` raised AttributeError instead of
        # taking the declared FAIL/SKIP. `view_extensions.ViewContractUnsupported`
        # names exactly that assembly as unsupported (its docstring: "an assembly
        # that pins an openDox without `view_extension.ViewBinding`"), so it is
        # `_absent()`'s to classify, like the other two.
        opendox_bundle._absent(
            "`opendox.view_extension.ViewBinding` (§ 3.4 slice S3's view "
            "registry class)", module_level=False)
    if "exports" not in getattr(binding, "__annotations__", {}):
        opendox_bundle._absent(
            "RULED Q2's `exports` field on `opendox.view_extension.ViewBinding` "
            "(openxFactory#656 comment 5648049748)", module_level=False)
    return view_extension


def test_the_facet_conforms_to_the_view_extension_protocol() -> None:
    view_extension = _view_extension_or_skip()
    assert len(view_extensions.VIEW_EXTENSIONS) == 1
    extension = view_extensions.VIEW_EXTENSIONS[0]
    assert isinstance(extension, view_extension.ViewExtension)
    bindings = extension.views()
    assert [b.id for b in bindings] == [spec["id"] for spec in SPECS]
    for binding, spec in zip(bindings, SPECS):
        assert binding.region == spec["region"]
        assert binding.routes == spec["routes"]
        assert binding.exports == spec["exports"]
        assert binding.requires == spec["requires"]


def test_the_pinned_binding_class_answers_for_the_sheets_or_for_none() -> None:
    """THE DECLARED PIN'S OWN ANSWER about `styles`, asserted (Copilot round 10).

    The two stub tests above drive `GateLoopViews.views()` through `ViewBinding`
    shapes this file defines, which is how BOTH pins are asserted from either —
    but until this one, nothing read the sheet off a binding the DECLARED PIN
    constructed. The live materialization assertions around it read region,
    routes, exports, requires and the manifest ids and never the SHEET, so a pin
    that stopped carrying the field, or a `specs_for()` that stopped handing it
    over, would leave all four contributed sheets inert with every test green.

    BOTH BRANCHES ASSERT, because the point is to refuse a quiet green: where
    the installed `ViewBinding` takes `styles` the values must be this column's
    declared sheets, and where it does not the materialized bindings must carry
    no such attribute at all — the degrade `specs_for()` exists to produce. The
    branch is chosen by the same `dataclasses.fields()` reading the module makes,
    never by a version.
    """
    view_extension = _view_extension_or_skip()
    fields = {f.name for f in dataclasses.fields(view_extension.ViewBinding)}
    bindings = view_extensions.GateLoopViews().views()
    assert [b.id for b in bindings] == [spec["id"] for spec in SPECS]
    if "styles" in fields:
        assert [b.styles for b in bindings] == [
            "./views/gate.css", "", "./views/gate-projects.css",
            "./views/dispose.css", "./views/swb.css", "./views/swb.css"], (
                "the pinned `ViewBinding` takes `styles`, so every binding that "
                "owns selectors must reach this column's own sheet")
        assert [b.styles for b in bindings] == [
            spec.get("styles", "") for spec in SPECS]
        named = {b.styles[len("./views/"):] for b in bindings if b.styles}
        assert named == set(web_assets.VIEW_SHEET_NAMES)
    else:
        assert not any(hasattr(b, "styles") for b in bindings), (
            "the pinned `ViewBinding` cannot express `styles`, so `specs_for()` "
            "must have dropped it and the column must mount unstyled")


def test_the_column_collects_through_openDox_beside_its_own_routes() -> None:
    """The whole contribution, assembled the way `serve.build_server()` does it:
    this column's bindings collected against this column's contributed ROUTES.
    Class B is exempt from the ownership refusal by construction, so a gate
    binding naming a gate route is the boundary working — and that is the one
    property this assertion exists to hold."""
    view_extension = _view_extension_or_skip()
    route_extension = pytest.importorskip("route_extension")
    from openxdox import serve_gate

    contributed = route_extension.collect_bindings(
        (serve_gate.GateRoutesExtension(),))
    collected = view_extension.collect_view_bindings(
        view_extensions.VIEW_EXTENSIONS, contributed_routes=contributed)
    assert len(collected) == 6
    manifest = view_extension.view_manifest(
        collected, contributed_routes=contributed,
        host_facet="declared", host_profile="openxdox")
    assert manifest["kind"] == view_extension.MANIFEST_KIND
    assert [entry["id"] for entry in manifest["views"]] == \
        [spec["id"] for spec in SPECS]
    # AND THE SHEETS CROSS IT (Copilot round 10). The manifest is the JSON
    # openDox's registry injects the `<link>` elements from, so a `styles` that
    # reaches the binding and not the manifest is four inert sheets with every
    # other assertion green. Both branches assert, for the reason the sibling
    # test above gives.
    if "styles" in {f.name for f in dataclasses.fields(view_extension.ViewBinding)}:
        assert [entry.get("styles", "") for entry in manifest["views"]] == \
            [spec.get("styles", "") for spec in SPECS]
    else:
        assert all("styles" not in entry for entry in manifest["views"])


def test_every_region_this_column_names_is_a_declared_shell_region() -> None:
    view_extension = _view_extension_or_skip()
    for spec in SPECS:
        region = spec["region"]
        assert region in view_extension.REGIONS, (
            f"{spec['id']} names region {region!r}, which openDox does not "
            "declare")
        assert view_extension.REGIONS[region] == "shell", (
            f"{region} is a `dom` region at openDox, so RULED Q1's generic "
            "mount pass would mount this binding — and this column's mounts are "
            "caller-driven")


# ---------------------------------------------------------------------------
# THE CREATE AFFORDANCE'S ONE WRITE — openDox-code's five statements, ported
# ---------------------------------------------------------------------------

def test_the_draft_views_one_action_is_the_create_forms_own_submit() -> None:
    """FIVE STATEMENTS ABOUT `swb-create.js`, MOVED WITH IT (openDox-code#20,
    Copilot round 2). They lived in openDox-code's
    `tests/test_bullseye_widget.py::test_the_draft_view_has_one_action_called_save_reachable_from_both_tabs`,
    where they read `src/opendox/web/views/swb-create.js` as text — a file that
    bundle no longer ships (RULED Q5, openxFactory#656 comment `5648044785`).
    That test keeps every statement about `views/staging-workbench.js` and
    `styles.css`, which are openDox's own; these five come here, to the column
    that owns the module they quote.

    WHAT THEY HOLD, in the words of the review they came from (MEASURED IN A
    BROWSER, 2026-08-10): `name it and create →` created nothing — it switched
    tabs — and is gone; the remaining action is `save`, it lives in the draft
    CHROME outside both panes so it is on screen from either tab, and it is the
    create form's OWN submit RELOCATED, never a second write path. The
    relocation is `o.actionsHost`; "never a second write path" is the count of
    `method: "POST"`; and the TILE path is untouched, where a new document
    really is being started and the label is still `create document`."""
    create = _module_text("swb-create.js")
    # the submit is RELOCATED into a host the caller supplies, not duplicated
    assert "const actions = o.actionsHost || form;" in create
    assert "actions.appendChild(bar);" in create
    assert "actions.appendChild(result);" in create
    # ONE write, and the count is the whole assertion
    assert create.count('method: "POST"') == 1, "still exactly one write"
    # the TILE path is untouched: there a new document really is being started
    assert 'o.submitLabel || "create document"' in create


# ---------------------------------------------------------------------------
# `_view_extension_or_skip`'s OWN CALL SITES — Copilot's review of `8b23f6f` on
# openXdox-code#21, and it was right: the three materialization assertions above
# exercise only the SUCCESSFUL import-and-`exports` path. The guard's refusal
# branches were reached by nothing, so replacing any one `_absent()` call with a
# bare `pytest.skip` would have left every required test green while restoring the
# silent green this act exists to remove. There are THREE of them, and the third
# arrived with the review of `cb84001` (the review of `b22a6fd` caught this header
# still saying two):
#   1. `opendox.view_extension` absent           — the module is not there at all;
#   2. `view_extension.ViewBinding` absent       — the module without its class,
#      which was an AttributeError out of this guard until `cb84001`;
#   3. `ViewBinding` without RULED Q2's `exports` — the partial packaging
#      regression: the registry present, the contract behind it.
# Each is driven BOTH ways below — FAIL at the commit this leg declares, SKIP for a
# different one — because a branch proved only at the declared pin can be replaced
# by an unconditional failure with every added test still green, and that breaks the
# consumer RULED 5700475319 protects. The direct `_absent()` tests in
# `tests/test_gate_loop_probes.py` prove what the guard DECIDES; these prove that
# this caller still asks it.
# ---------------------------------------------------------------------------

_PIN_DECLARED = "a" * 40
_PIN_OTHER = "b" * 40


def _guard_reads(monkeypatch, declared, installed, *, ci=True):
    import opendox_bundle
    monkeypatch.setattr(opendox_bundle, "declared_pin", lambda: declared)
    monkeypatch.setattr(opendox_bundle, "installed_commit", lambda: installed)
    monkeypatch.setenv("CI", "true" if ci else "")


def _without_view_extension(monkeypatch):
    """Make `from opendox import view_extension` raise ImportError.

    BOTH steps are needed and neither is enough: the attribute is deleted
    because the package object already carries it once anything has imported it,
    and the `sys.modules` entry is set to `None` because otherwise the submodule
    is simply re-imported from disk. A `None` entry is the documented way to
    make an import fail without touching the filesystem.
    """
    import sys
    import opendox
    monkeypatch.delattr(opendox, "view_extension", raising=False)
    monkeypatch.setitem(sys.modules, "opendox.view_extension", None)


def test_a_missing_view_extension_FAILS_at_the_declared_pin(monkeypatch) -> None:
    """The ImportError branch, at the pin this leg declares, under CI."""
    _guard_reads(monkeypatch, _PIN_DECLARED, _PIN_DECLARED)
    _without_view_extension(monkeypatch)
    with pytest.raises(pytest.fail.Exception) as raised:
        _view_extension_or_skip()
    message = str(raised.value)
    assert "REGRESSION at the declared pin" in message
    assert "view_extension" in message


def test_a_missing_view_extension_SKIPS_for_a_different_installed_commit(
        monkeypatch) -> None:
    """...and the DIFFERENT-COMMIT reading that RULED 5700475319 rests on still holds.

    Not "older", and the thread on `24cd5f2` was right to say so twice: `_absent()`
    compares two identities and never asks git which came first, so `b`*40 against
    `a`*40 is a different assembly and nothing more. The ruling's own ground — an
    assembly is free to install an openDox behind the view contract — is what this
    skip serves, and it needs no ordering to hold.
    """
    _guard_reads(monkeypatch, _PIN_DECLARED, _PIN_OTHER)
    _without_view_extension(monkeypatch)
    with pytest.raises(pytest.skip.Exception) as raised:
        _view_extension_or_skip()
    message = str(raised.value)
    assert _PIN_DECLARED[:8] in message
    assert _PIN_OTHER[:8] in message


def test_a_ViewBinding_without_exports_FAILS_at_the_declared_pin(
        monkeypatch) -> None:
    """The SECOND branch: the module imports, and RULED Q2's field is gone.

    This is the branch a partial packaging regression would take — the registry
    present, the contract behind it — and it was the less obvious of the two to
    leave unproven.

    THE MODULE COMES THROUGH THE HELPER, not `from opendox import view_extension`:
    the review of `24cd5f2` caught that a bare import here raises ImportError for
    exactly the consumer this helper exists to SKIP (a different openDox without
    the module), turning a supported assembly into a hard failure inside the test
    that proves the guard. This call is made BEFORE `_guard_reads()` patches
    anything, so it is the real installed module or the real skip.
    """
    view_extension = _view_extension_or_skip()
    _guard_reads(monkeypatch, _PIN_DECLARED, _PIN_DECLARED)
    monkeypatch.setattr(view_extension.ViewBinding, "__annotations__", {})
    with pytest.raises(pytest.fail.Exception) as raised:
        _view_extension_or_skip()
    assert "`exports` field" in str(raised.value)


def test_a_ViewBinding_without_exports_SKIPS_for_a_different_installed_commit(
        monkeypatch) -> None:
    """The SKIP half of the `exports` branch, at the CALL SITE.

    The declared-pin FAIL above and the generic `_absent()` tests would both stay
    green if this call became an unconditional failure, and the consumer RULED
    5700475319 protects — an assembly pinning an openDox behind the view contract —
    would break with them green. Caught at the review of `cb84001`.
    """
    view_extension = _view_extension_or_skip()
    _guard_reads(monkeypatch, _PIN_DECLARED, _PIN_OTHER)
    monkeypatch.setattr(view_extension.ViewBinding, "__annotations__", {})
    with pytest.raises(pytest.skip.Exception) as raised:
        _view_extension_or_skip()
    message = str(raised.value)
    assert _PIN_DECLARED[:8] in message
    assert _PIN_OTHER[:8] in message


def test_a_view_extension_without_ViewBinding_FAILS_at_the_declared_pin(
        monkeypatch) -> None:
    """THE THIRD unsupported shape: the module imports, the CLASS is not there.

    It raised `AttributeError` before the review of `24cd5f2` — the one path out
    of this guard that never reached `_absent()` — and an AttributeError three
    frames from a dataclass is precisely what
    `view_extensions.ViewContractUnsupported` exists to replace with a sentence.
    """
    view_extension = _view_extension_or_skip()
    _guard_reads(monkeypatch, _PIN_DECLARED, _PIN_DECLARED)
    monkeypatch.delattr(view_extension, "ViewBinding")
    with pytest.raises(pytest.fail.Exception) as raised:
        _view_extension_or_skip()
    message = str(raised.value)
    assert "ViewBinding" in message
    assert "REGRESSION at the declared pin" in message


def test_a_view_extension_without_ViewBinding_SKIPS_for_a_different_commit(
        monkeypatch) -> None:
    """...and the same branch at a DIFFERENT commit takes the ruled skip.

    The third unsupported shape has to be COMPATIBLE for a consumer behind the
    view contract, exactly as the other two are; with only the FAIL case driven,
    an unconditional failure here would pass every added test and break that
    consumer. Caught at the review of `cb84001`.
    """
    view_extension = _view_extension_or_skip()
    _guard_reads(monkeypatch, _PIN_DECLARED, _PIN_OTHER)
    monkeypatch.delattr(view_extension, "ViewBinding")
    with pytest.raises(pytest.skip.Exception) as raised:
        _view_extension_or_skip()
    message = str(raised.value)
    assert "ViewBinding" in message
    assert _PIN_DECLARED[:8] in message
    assert _PIN_OTHER[:8] in message


# ---------------------------------------------------------------------------
# THE DISPLAY FACET — RULED `opensoft/openxFactory#656` comment `5784683830`
# (Brett Heap, 2026-09-22, verbatim "1, keep completed and overlay
# implemented"). The facet `view_extensions` declares beside `VIEW_EXTENSIONS`,
# read the way openDox reads it: off the ONE registered host, through the lazy
# proxy, by the statement the pinned `serve.build_server()` makes. The host is
# built from the vendored engineering profile and registered for ONE test at a
# time; nothing here leaves a registration behind.
# ---------------------------------------------------------------------------

#: The word the ruling overlays on openDox's sixth stage.
IMPLEMENTED = "implemented"

#: The vendored engineering profile, openXdox-spec's worked example of
#: openxFactory's OWN profile. The host below is built from it, so the name the
#: served payload carries is the engineering domain's rather than a stand-in's.
ENGINEERING_PROFILE = (Path(__file__).resolve().parent / "fixtures"
                       / "openxfactory-engineering-profile.yaml")

#: EVERY name this section reads off the pinned openDox, by module, so the guard
#: below can check all of them (Copilot review of `7956c05c`: checking only the
#: three readers left the constants, the proxy and the registry to surface as an
#: `AttributeError` instead of the ruled outcome).
#: `test_the_guard_checks_every_name_the_display_section_reads` holds this table
#: to the section's own reads, both ways, so a new read cannot slip past it and
#: no entry outlives the read it was added for.
DISPLAY_READS: dict[str, tuple[str, ...]] = {
    "display_profile": ("normalize_display", "host_display", "display_manifest",
                        "DISPLAY_KIND", "DISPLAY_SCHEMA_VERSION", "PROFILE_FACET",
                        "NEUTRAL_DISPLAY", "STAGE_ROLES", "DisplayFacetError"),
    "profile_proxy": ("profile_openxfactory",),
    "domain_profile": ("register", "unregister", "current", "is_registered"),
    "view_extension": ("host_profile_name",),
}


def _display_profile_or_skip():
    """`opendox.display_profile` and `opendox.view_extension`, or `_absent()`'s outcome.

    `_view_extension_or_skip()`'s guard, one facet over, on the same ruled
    footing (RULED openxFactory#656 comment 5700475319: keep the guards, "they
    test the ASSEMBLED openDox; a consumer may pin behind the view contract").
    `display_profile` arrived with openDox-code#21 (§ 3.4 slice S7), one PR after
    the view contract's `exports` (#20), so an assembly can carry a view registry
    this column mounts on and no display reader at all. It checks every module
    and name in `DISPLAY_READS`. At the pin this leg declares, anything missing
    FAILS; at a different installed commit it SKIPS, naming both.
    """
    import importlib
    import opendox_bundle
    view_extension = _view_extension_or_skip()
    modules: dict[str, object] = {}
    missing: list[str] = []
    for module, names in DISPLAY_READS.items():
        try:
            modules[module] = importlib.import_module(f"opendox.{module}")
        except ImportError:
            missing.append(f"opendox.{module}")
            continue
        missing += [f"opendox.{module}.{name}" for name in names
                    if not hasattr(modules[module], name)]
    if missing:
        opendox_bundle._absent(
            "what the DISPLAY facet's reader needs from openDox "
            f"({', '.join(missing)}; § 3.4 slice S7, openDox-code#21)",
            module_level=False)
    return modules["display_profile"], view_extension


def _engineering_host(*facets: str):
    """openxFactory's engineering profile, composed into a host as the estate does.

    openxFactory's `scripts/opendox_host.py` builds `OpenxFactoryProfile`, an
    `openxdox.domain_profile.DomainProfile` subclass that FORWARDS its declared
    facets when ordinary attribute lookup fails. This is that shape with this
    leg's module as the forward target: each name in `facets` is read off
    `view_extensions` at the moment openDox asks for it, and every other name is
    an `AttributeError`, so `host_display()`'s three-argument `getattr` answers
    `None` for a facet this host does not forward.
    """
    from openxdox import domain_profile

    loaded = domain_profile.load(ENGINEERING_PROFILE)

    class EngineeringHost(domain_profile.DomainProfile):
        __slots__ = ()

        def __getattr__(self, name: str):
            if name in facets:
                return getattr(view_extensions, name)
            raise AttributeError(name)

    return EngineeringHost(**{f.name: getattr(loaded, f.name)
                              for f in dataclasses.fields(loaded)})


@pytest.fixture
def register_host():
    """Hand a test openDox's `register`, and restore the registry afterwards.

    The registry is process-global and `validate` runs every listed file in ONE
    process, so whatever was registered before is put back and nothing this
    section registers survives the test that registered it. The guard runs
    FIRST, so an assembly without the display reader gets its ruled outcome
    before this fixture reaches openDox's registry at all.
    """
    _display_profile_or_skip()
    from opendox import domain_profile as registry

    previous = registry.current() if registry.is_registered() else None
    registry.unregister()
    try:
        yield registry.register
    finally:
        registry.unregister()
        if previous is not None:
            registry.register(previous)


def _served_display(display_profile, view_extension) -> dict:
    """`/capabilities["display"]`, by the pinned `serve.build_server()`'s statement.

    `opendox.serve` cannot be imported at this leg (it reaches
    `ideation_dashboard`, which is openxFactory's), so the statement is REPLAYED
    rather than called, and
    `test_the_replayed_statement_is_the_one_the_pinned_serve_makes` holds the
    replay to the installed `serve.py`'s text.
    """
    from opendox.profile_proxy import profile_openxfactory

    return display_profile.display_manifest(
        display_profile.host_display(profile_openxfactory),
        host_profile=view_extension.host_profile_name(profile_openxfactory))


def _reports_the_facet(manifest: dict) -> bool:
    return manifest["host_facet"] == "declared"


def _completion_renders_implemented(manifest: dict) -> bool:
    completion = manifest["stages"]["completion"]
    return completion["short"] == IMPLEMENTED and completion["label"] == IMPLEMENTED


def _flatten(value, path: str = "") -> dict[str, object]:
    """Every leaf of a payload by dotted path, so two payloads compare leaf by leaf."""
    if isinstance(value, dict):
        out: dict[str, object] = {}
        for key, item in value.items():
            out.update(_flatten(item, f"{path}.{key}" if path else str(key)))
        return out
    return {path: value}


def test_the_display_facet_declares_one_stage_entry_and_nothing_else() -> None:
    """The ruling's partial facet, pinned as a value: `stages.completion`, two fields.

    `short` and `label` because they are the stage's two rendered names and
    openDox spells both `completed`; `one`, `many` and `gate` are left to
    openDox. The block above `DISPLAY` in `view_extensions.py` gives the render
    sites.
    """
    assert "DISPLAY" in view_extensions.__all__
    assert view_extensions.DISPLAY == {
        "stages": {"completion": {"short": IMPLEMENTED, "label": IMPLEMENTED}},
    }


def test_the_display_facet_conforms_to_the_pinned_reader() -> None:
    """Handed to the pinned `normalize_display` itself, never a copy of its schema."""
    display_profile, _ = _display_profile_or_skip()
    merged = display_profile.normalize_display(view_extensions.DISPLAY)
    assert merged["stages"]["completion"]["short"] == IMPLEMENTED
    assert merged["stages"]["completion"]["label"] == IMPLEMENTED


def test_the_facet_name_is_not_a_field_of_the_domain_profile() -> None:
    """The name stays OFF `DomainProfile`, which is why the facet is a module value.

    The composite host forwards a facet only when ordinary attribute lookup
    fails, and openxFactory's `opendox_host.build_profile()` refuses a facet
    named like a profile field. A `DISPLAY` on the dataclass would be read
    instead of forwarded, and would stop that composite being built at all.
    """
    from openxdox import domain_profile

    fields = {f.name for f in dataclasses.fields(domain_profile.DomainProfile)}
    assert "DISPLAY" not in fields
    assert not hasattr(domain_profile.load(ENGINEERING_PROFILE), "DISPLAY")


def test_the_manifest_through_the_xfactory_host_reports_the_facet_declared(
        register_host) -> None:
    """The named absence turns into a named presence, and the host is named."""
    display_profile, view_extension = _display_profile_or_skip()
    register_host(_engineering_host("DISPLAY"))
    served = _served_display(display_profile, view_extension)
    assert served["kind"] == display_profile.DISPLAY_KIND
    assert served["schema_version"] == display_profile.DISPLAY_SCHEMA_VERSION
    assert served["facet"] == display_profile.PROFILE_FACET == "DISPLAY"
    assert _reports_the_facet(served), served["host_facet"]
    assert served["host_profile"] == "openxfactory-engineering"


def test_the_completion_stage_renders_implemented_through_the_host(
        register_host) -> None:
    """Both of the stage's names say `implemented`; its item nouns stay openDox's."""
    display_profile, view_extension = _display_profile_or_skip()
    register_host(_engineering_host("DISPLAY"))
    served = _served_display(display_profile, view_extension)
    assert _completion_renders_implemented(served), served["stages"]["completion"]
    neutral = display_profile.NEUTRAL_DISPLAY["stages"]["completion"]
    for field in ("one", "many", "gate"):
        assert served["stages"]["completion"][field] == neutral[field], field


def test_every_other_stage_still_renders_the_neutral_word(register_host) -> None:
    """Five stages, every field, exactly as openDox declares them."""
    display_profile, view_extension = _display_profile_or_skip()
    register_host(_engineering_host("DISPLAY"))
    served = _served_display(display_profile, view_extension)
    others = [role for role in display_profile.STAGE_ROLES if role != "completion"]
    assert len(others) == 5
    for role in others:
        neutral = display_profile.NEUTRAL_DISPLAY["stages"][role]
        assert served["stages"][role] == neutral, role


def test_the_overlay_changes_two_words_and_the_named_absence_and_nothing_else(
        register_host) -> None:
    """Against the same host WITHOUT the facet: three leaves differ, and they are these.

    Both payloads come through the same chain. The facet-less host is registered
    second, after an explicit `unregister()`, because the registry refuses a
    second, different profile over a first.
    """
    from opendox import domain_profile as registry

    display_profile, view_extension = _display_profile_or_skip()
    register_host(_engineering_host("DISPLAY"))
    declared = _flatten(_served_display(display_profile, view_extension))
    registry.unregister()
    register_host(_engineering_host())
    absent = _flatten(_served_display(display_profile, view_extension))
    assert absent["host_facet"] == "absent"
    assert declared.keys() == absent.keys()
    changed = {path: (absent[path], declared[path])
               for path in declared if declared[path] != absent[path]}
    assert changed == {
        "host_facet": ("absent", "declared"),
        "stages.completion.short": ("completed", IMPLEMENTED),
        "stages.completion.label": ("completed", IMPLEMENTED),
    }


def test_the_replayed_statement_is_the_one_the_pinned_serve_makes() -> None:
    """`_served_display` replays `serve.build_server()`; this holds it to the text.

    A pin bump that changed how the server builds the block would otherwise
    leave every assertion in this section green over a replay of a statement
    the server no longer makes.
    """
    display_profile, _ = _display_profile_or_skip()
    serve = Path(display_profile.__file__).with_name("serve.py")
    source = serve.read_text(encoding="utf-8")
    for fragment in (
            "from opendox.profile_proxy import profile_openxfactory",
            'capabilities["display"] = display_profile.display_manifest(',
            "display_profile.host_display(profile_openxfactory),",
            "host_profile=view_extension.host_profile_name(profile_openxfactory),"):
        assert fragment in source, (
            f"the installed {serve} no longer carries {fragment!r}: "
            "`_served_display` replays a statement the pinned server may no "
            "longer make, and needs re-reading against it")


@pytest.mark.parametrize("dropped", ["host-forwards-no-facet", "module-value-deleted"])
def test_dropping_the_facet_fails_the_overlay(register_host, monkeypatch,
                                              dropped) -> None:
    """THE FIRST MUTATION: the facet is gone, so both positive checks above fail.

    Dropped two ways, because either is a real regression: an assembly that
    stops forwarding the name, and a module that stops declaring it. Either way
    openDox reports the named absence and renders its own word, which is exactly
    what the two predicates the positive tests use must refuse.
    """
    display_profile, view_extension = _display_profile_or_skip()
    if dropped == "host-forwards-no-facet":
        register_host(_engineering_host())
    else:
        register_host(_engineering_host("DISPLAY"))
        monkeypatch.delattr(view_extensions, "DISPLAY")
    served = _served_display(display_profile, view_extension)
    assert served["host_facet"] == "absent"
    assert served["stages"]["completion"]["short"] == "completed"
    assert not _reports_the_facet(served)
    assert not _completion_renders_implemented(served)


@pytest.mark.parametrize("typo", ["completed", "complete", "completions",
                                  "Completion"])
def test_a_misspelled_stage_role_is_refused_where_the_server_is_built(
        register_host, monkeypatch, typo) -> None:
    """THE SECOND MUTATION: the role is misspelled, and the build refuses it by name.

    `completed` leads the list because it is the likeliest slip: the neutral
    WORD in place of the ROLE. A role openDox does not read renders nowhere, so
    `normalize_display` refuses it rather than serving a silent no-op, and that
    refusal is raised where `build_server()` builds `/capabilities`.
    """
    display_profile, view_extension = _display_profile_or_skip()
    entry = dict(view_extensions.DISPLAY["stages"]["completion"])
    monkeypatch.setattr(view_extensions, "DISPLAY", {"stages": {typo: entry}})
    register_host(_engineering_host("DISPLAY"))
    with pytest.raises(display_profile.DisplayFacetError) as raised:
        _served_display(display_profile, view_extension)
    message = str(raised.value)
    assert repr([typo]) in message
    assert "under stages" in message


def test_a_misspelled_stage_field_is_refused_the_same_way(register_host,
                                                          monkeypatch) -> None:
    """One tier down: the role right, a field wrong, refused naming the field."""
    display_profile, view_extension = _display_profile_or_skip()
    monkeypatch.setattr(view_extensions, "DISPLAY",
                        {"stages": {"completion": {"shrot": IMPLEMENTED}}})
    register_host(_engineering_host("DISPLAY"))
    with pytest.raises(display_profile.DisplayFacetError) as raised:
        _served_display(display_profile, view_extension)
    message = str(raised.value)
    assert "['shrot']" in message
    assert "under stages.completion" in message


# `_display_profile_or_skip`'s OWN CALL SITE, driven both ways for the reason the
# section above gives for `_view_extension_or_skip`'s three: a branch proved only
# at the declared pin can become an unconditional failure with every test green,
# and that breaks the consumer RULED 5700475319 protects. ONE call site, two
# shapes: the module absent, and the module present without one of its readers.

def _without_display_profile(monkeypatch) -> None:
    """Make `from opendox import display_profile` raise ImportError.

    The same two steps `_without_view_extension` takes, for the same reason.
    """
    import sys
    import opendox
    monkeypatch.delattr(opendox, "display_profile", raising=False)
    monkeypatch.setitem(sys.modules, "opendox.display_profile", None)


def _without_a_display_reader(monkeypatch) -> None:
    """Leave the module importable and take `normalize_display` off it."""
    display_profile, _ = _display_profile_or_skip()
    monkeypatch.delattr(display_profile, "normalize_display")


@pytest.mark.parametrize("shape", [_without_display_profile,
                                   _without_a_display_reader])
def test_a_missing_display_reader_FAILS_at_the_declared_pin(monkeypatch,
                                                           shape) -> None:
    shape(monkeypatch)
    _guard_reads(monkeypatch, _PIN_DECLARED, _PIN_DECLARED)
    with pytest.raises(pytest.fail.Exception) as raised:
        _display_profile_or_skip()
    message = str(raised.value)
    assert "REGRESSION at the declared pin" in message
    assert "display_profile" in message


@pytest.mark.parametrize("shape", [_without_display_profile,
                                   _without_a_display_reader])
def test_a_missing_display_reader_SKIPS_for_a_different_installed_commit(
        monkeypatch, shape) -> None:
    shape(monkeypatch)
    _guard_reads(monkeypatch, _PIN_DECLARED, _PIN_OTHER)
    with pytest.raises(pytest.skip.Exception) as raised:
        _display_profile_or_skip()
    message = str(raised.value)
    assert _PIN_DECLARED[:8] in message
    assert _PIN_OTHER[:8] in message


def test_the_guard_checks_every_name_the_display_section_reads() -> None:
    """`DISPLAY_READS` against the section's own reads, parsed rather than trusted.

    The section is every top-level statement after its header. Inside it, the
    names that hold an openDox module are the guard's two returns
    (`display_profile`, `view_extension`) and every alias a
    `from opendox import X` binds (`registry`). Each attribute read off one of
    them, and each name a `from opendox.X import Y` takes, must be a pair in the
    table. The check runs both ways: a new read the guard does not check fails
    here, and so does a table entry nothing reads, which would make the guard
    refuse an assembly over a name the section never uses. It also holds a
    `from opendox import X` to a module the table names (Copilot review of
    `f8d2aad7`: the first version checked two aliases and two names, not every
    module and proxy read).
    """
    source = Path(__file__).read_text(encoding="utf-8")
    header = source.count("\n", 0, source.index("# THE DISPLAY FACET — RULED")) + 1
    section = [node for node in ast.parse(source).body if node.lineno > header]
    walked = [node for top in section for node in ast.walk(top)]

    held = {"display_profile": "display_profile", "view_extension": "view_extension"}
    modules: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    for node in walked:
        if isinstance(node, ast.ImportFrom) and node.module == "opendox":
            for alias in node.names:
                held[alias.asname or alias.name] = alias.name
                modules.add(alias.name)
        elif (isinstance(node, ast.ImportFrom)
              and (node.module or "").startswith("opendox.")):
            module = node.module.split(".", 1)[1]
            modules.add(module)
            pairs |= {(module, alias.name) for alias in node.names}
    pairs |= {(held[node.value.id], node.attr) for node in walked
              if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
              and node.value.id in held and node.attr != "__file__"}

    assert {("display_profile", "display_manifest"), ("domain_profile", "register"),
            ("profile_proxy", "profile_openxfactory"),
            ("view_extension", "host_profile_name")} <= pairs, (
        "the parse no longer sees the section's own reads")
    assert modules <= set(DISPLAY_READS), sorted(modules - set(DISPLAY_READS))
    table = {(module, name) for module, names in DISPLAY_READS.items()
             for name in names}
    assert pairs - table == set(), sorted(pairs - table)
    assert table - pairs == set(), sorted(table - pairs)
