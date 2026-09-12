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

A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C).
"""

from __future__ import annotations

import ast
import re
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
    """A globbed directory is how a module reaches another leg's bundle with no
    binding naming it. The set is declared, so the directory must match it."""
    on_disk = sorted(p.name for p in MODULE_DIR.iterdir() if p.is_file())
    assert on_disk == sorted(web_assets.VIEW_MODULE_NAMES), (
        "the packaged view-module directory and the declared module set "
        f"disagree: on disk {on_disk}, declared "
        f"{sorted(web_assets.VIEW_MODULE_NAMES)}")


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


def test_the_assembly_hook_places_every_module_in_the_bundle(tmp_path) -> None:
    """RULED Q5's primary mechanism: the composed install copies them into
    openDox's one `--web-dir` at assembly."""
    web = tmp_path / "web"
    (web / web_assets.BUNDLE_SUBDIR).mkdir(parents=True)
    placed = web_assets.install_view_modules(web)
    assert [p.name for p in placed] == list(web_assets.VIEW_MODULE_NAMES)
    for path, name in zip(placed, web_assets.VIEW_MODULE_NAMES):
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
    (views / web_assets.VIEW_MODULE_NAMES[0]).write_text("// someone else's\n")
    with pytest.raises(web_assets.ViewAssetError) as clash:
        web_assets.install_view_modules(web, overwrite=False)
    assert "already" in str(clash.value) and "overwrite=False" in str(clash.value)
    # NOTHING WAS COPIED (Copilot review, round 1): the collision check runs over
    # every module BEFORE the first write, so a refusal never leaves a
    # half-assembled bundle behind.
    assert sorted(p.name for p in views.iterdir()) == [
        web_assets.VIEW_MODULE_NAMES[0]]


def test_an_undeclared_module_name_is_refused() -> None:
    with pytest.raises(web_assets.ViewAssetError):
        web_assets.module_path("../../etc/passwd")
    with pytest.raises(web_assets.ViewAssetError):
        web_assets.module_path("helpers.js")


# ---------------------------------------------------------------------------
# RULED Q5 — the DECLARED HOSTED FALLBACK. "a contributed GET route is the
# declared hosted fallback."
# ---------------------------------------------------------------------------

def test_the_hosted_fallback_claims_exactly_this_columns_six_paths() -> None:
    pytest.importorskip(
        "route_extension",
        reason="`route_extension` is supplied by the pinned opendox wheel; "
               "the binding shape cannot be built without it")
    from openxdox import serve_views

    bindings = serve_views.view_module_bindings()
    assert [b.pattern for b in bindings] == [
        f"/{web_assets.BUNDLE_SUBDIR}/{name}"
        for name in web_assets.VIEW_MODULE_NAMES]
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
                       "gate.workbench.session"):
        spec = next(s for s in SPECS if s["id"] == binding_id)
        assert spec["requires"] == (), (
            f"{binding_id} degrades to a descriptor without its capability, so "
            "requiring it would remove a surface that works")
    for binding_id in ("gate.lens", "gate.projects", "gate.dispose"):
        spec = next(s for s in SPECS if s["id"] == binding_id)
        assert spec["requires"] == ("actions.gate",), (
            f"{binding_id} mounts a live gate control or nothing, so the "
            "capability is a genuine mount requirement")


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


def test_the_style_residue_is_recorded_rather_than_skipped() -> None:
    """RULED Q7 is NOT realized in this slice, and the record says so with the
    floor constraint that blocks it rather than leaving a silence."""
    residue = view_extensions.STYLE_RESIDUE
    assert residue["exclusive_classes"] > 0 and residue["shared_classes"] > 0
    assert "moved_verbatim" in residue["blocked_by"]
    assert residue["discharged_by"]


# ---------------------------------------------------------------------------
# The materialization — against whatever `opendox` this assembly pinned.
# ---------------------------------------------------------------------------

def _view_extension_or_skip():
    view_extension = pytest.importorskip(
        "opendox.view_extension",
        reason="this leg pins an `opendox` older than the § 3.4 slice S3 view "
               "registry; the specs above are asserted as data, and the "
               "materialization is asserted wherever a contract-bearing "
               "opendox is installed")
    if "exports" not in getattr(view_extension.ViewBinding, "__annotations__", {}):
        pytest.skip(
            "the pinned `opendox.view_extension.ViewBinding` predates RULED Q2's "
            "`exports` field (openxFactory#656 comment 5648049748); the pin bump "
            "to the openDox carrying § 3.4 slice S5 is owed at landing")
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
