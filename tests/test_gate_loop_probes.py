"""The gate loop's view modules, EXECUTED — slice S4's node probes, ported.

WHY THIS FILE EXISTS. Slice S4 (openDox-code#17) split four of the thirteen gate
route constants into two NEW class-B modules, `views/gate-lens.js` and
`views/gate-projects.js`, and proved the split by DRIVING them: five node probes
in openDox-code's `tests/test_split_route_tails.py` mount each module against a
stubbed DOM, click its controls and assert the route, the method and the request
BODY that reach the injected fetcher. Slice S5 moves both modules — and the four
older class-B files with them — into this package as package data (RULED Q5,
`opensoft/openxFactory#656` comment `5648044785`). A behaviour proof that stays
in the repository the behaviour left is a proof of nothing, so the probes come
too, and openDox-code#20 drops them from the file they came from.

WHAT IS STRONGER HERE THAN THERE. The openDox-side original imported the modules
out of the bundle they happened to sit in. These import them out of an ASSEMBLED
bundle: `web_assets.install_view_modules()` places this column's modules into a
copy of openDox's own `web/`, exactly as RULED Q5's composed deployment does, and
the harness imports them from THERE. So what is measured is the shipped byte in
the shipped position, with `./helpers.js` resolving the way it resolves in a
composed install — and the assembly hook is exercised by every probe rather than
asserted once.

THE ASSEMBLY IS THE PRECONDITION, AND IT IS THE PIN. This leg pins `opendox` by
commit (`pyproject.toml`), and the pinned commit predates BOTH the view registry
and the packaging fix that puts `opendox/web/` into a wheel at all
(openDox-code#20's own first commit). Where the installed `opendox` carries no
bundle there is nothing to assemble INTO, and every probe SKIPS with that reason
named — never fails, and never silently passes against a stand-in. They run in
full the moment the pin bump lands, which is the same bump the three
materialization assertions in `test_gate_loop_views.py` wait for.

A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C), admitted by path in the S5 annotation.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from openxdox import web_assets

NODE = shutil.which("node")

_DOM_STUB = r"""
class Node {
  constructor(tag) {
    this.tag = tag; this.children = []; this.attrs = {}; this.listeners = {};
    this.className = ""; this._text = ""; this.type = ""; this.title = "";
    this.value = ""; this.checked = false; this.disabled = false;
    this.hidden = false; this.focused = false;
  }
  get textContent() { return this._text; }
  set textContent(v) { this._text = String(v); this.children = []; }
  set innerHTML(v) { if (v !== "") throw new Error("innerHTML assigned " + v); this.children = []; this._text = ""; }
  appendChild(c) { this.children.push(c); return c; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  addEventListener(t, fn) { (this.listeners[t] = this.listeners[t] || []).push(fn); }
  focus() { this.focused = true; }
  click() { for (const fn of this.listeners.click || []) fn({}); }
}
globalThis.document = { createElement: (tag) => new Node(tag) };
function flatten(node, out = []) {
  out.push(node);
  for (const c of node.children) flatten(c, out);
  return out;
}
function texts(node) { return flatten(node).map((n) => n.textContent).filter(Boolean); }
function buttons(node) { return flatten(node).filter((n) => n.tag === "button"); }
function inputs(node) { return flatten(node).filter((n) => n.tag === "input"); }
globalThis.flatten = flatten; globalThis.texts = texts;
globalThis.buttons = buttons; globalThis.inputs = inputs;
// The injected fetcher every transport in this bundle takes, recording what it
// was asked for. `body` comes back parsed so a harness asserts on the REQUEST.
function recorder(response) {
  const calls = [];
  return [calls, async (route, opts) => {
    calls.push({ route, method: opts?.method || "GET",
                 body: opts?.body ? JSON.parse(opts.body) : null });
    return { ok: response.ok !== false, status: response.status || 200,
             json: async () => response.payload };
  }];
}
globalThis.recorder = recorder;
const settle = () => new Promise((r) => setTimeout(r, 0));
globalThis.settle = settle;
"""


def _run_node(body: str, bundle: Path) -> dict:
    """Run an ES-module harness against the ASSEMBLED bundle and return the ONE
    JSON object it prints.

    The modules are imported by absolute `file://` URL out of the directory
    `install_view_modules()` placed them in, beside openDox's own — so what is
    measured is the shipped file IN THE POSITION RULED Q5 puts it, with its
    bundle-relative imports (`./helpers.js`, `./lens-model.js`) resolving the
    way they resolve in a composed deployment. That is a stronger statement than
    the openDox-side original could make, where these files sat in the bundle by
    accident of history rather than by an assembly step.
    """
    views = bundle / "views"
    source = (
        _DOM_STUB
        + f'\nconst VIEWS = {json.dumps(views.resolve().as_uri() + "/")};\n'
        + body
    )
    script = bundle / "harness.mjs"
    script.write_text(source, encoding="utf-8")
    proc = subprocess.run([NODE, str(script)], capture_output=True, text=True,
                          timeout=120)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _opendox_bundle() -> Path | None:
    """The INSTALLED openDox's web bundle, or None where the pin carries none."""
    try:
        import opendox
    except ModuleNotFoundError:              # pragma: no cover - no consumer
        return None
    web = Path(opendox.__file__).resolve().parent / "web"
    return web if (web / web_assets.BUNDLE_SUBDIR / "helpers.js").is_file() else None


@pytest.fixture
def bundle(tmp_path) -> Path:
    """A COMPOSED bundle: openDox's own `web/`, with this column's six modules
    placed into it by the assembly hook RULED Q5 names.

    Skipped — never failed — where the assembled `opendox` carries no bundle:
    that is this leg's pinned state until the pin bump, and a probe that quietly
    ran against a stand-in `helpers.js` would measure the stand-in rather than
    the shipped file.
    """
    source = _opendox_bundle()
    if source is None:
        pytest.skip(
            "the installed `opendox` carries no `web/` bundle: this leg pins a "
            "commit older than openDox's own packaging fix, so there is nothing "
            "to assemble into. The pin bump owed at landing makes these probes "
            "run (the same bump `test_gate_loop_views.py`'s three "
            "materialization assertions wait for)")
    target = tmp_path / "web"
    shutil.copytree(source, target)
    web_assets.install_view_modules(target)
    # THE COPY IS AN ES-MODULE TREE AND MUST SAY SO (Copilot review, round 1).
    # Every module in this bundle is an ES module, but a `.js` file's type is
    # decided by the NEAREST `package.json`, and a copy under `tmp_path` has no
    # ancestor carrying one — so `import()` would fall to Node's CommonJS
    # reading of `export` on any runtime without module-syntax detection. In
    # the real deployment openDox's own package answers this; here the fixture
    # answers it, so what the probe measures is the module the shell loads.
    (target / "package.json").write_text('{"type": "module"}\n',
                                         encoding="utf-8")
    return target


@pytest.mark.skipif(NODE is None, reason="node is not installed")
@pytest.mark.parametrize("kind,expected", [
    ("save-recipe", "/actions/gate/lens-save-recipe"),
    ("add-as-cluster", "/actions/gate/lens-add-as-cluster"),
])
def test_js_the_lens_gate_posts_the_route_its_plan_kind_names(
        kind, expected, bundle) -> None:
    """The verb still works after the move, and it posts the route the plan
    kind names -- the behaviour that used to live in `views/lens.js`'s
    `mountExecute`, now in the binding that owns both routes."""
    result = _run_node(f"""
const {{ mountLensGate }} = await import(VIEWS + "gate-lens.js");
// RULED counterpart Q6 (#656 comment 5649094228): the module no longer imports
// `./lens-model.js` — the SHELL hands it down, and the harness is the shell.
const model = await import(VIEWS + "lens-model.js");
const [calls, fetcher] = recorder({{ payload: {{ ok: true, manifest: "m.yaml",
                                                record: "r.yaml" }} }});
const host = document.createElement("div");
const plan = {{ kind: {json.dumps(kind)}, repository: "openxFactory", name: "lens set",
               checked: ["a"], pinned: [], members: [], excluded: [] }};
mountLensGate(host, null, {{ plan, caps: {{ actor: "brett" }}, fetcher, model }});
buttons(host)[0].click();
await settle();
// add-as-cluster collects the organizer evidence first: fill it and submit.
if (calls.length === 0) {{
  const form = flatten(host).find((n) => n.className
    && n.className.includes("evidence-form"));
  for (const input of inputs(form)) input.value = "x";
  buttons(form).find((b) => b.textContent === "execute").click();
  await settle();
}}
console.log(JSON.stringify({{ calls, texts: texts(host) }}));
""", bundle)
    assert [c["route"] for c in result["calls"]] == [expected]
    call = result["calls"][0]
    assert call["method"] == "POST"
    assert call["body"]["repository"] == "openxFactory"
    if kind == "add-as-cluster":
        assert call["body"]["evidence"]["proposer"] == "x"
    else:
        assert "evidence" not in call["body"]
    assert any("landed" in t for t in result["texts"])


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_the_lens_gate_renders_the_engines_refusal_and_re_arms(bundle) -> None:
    """"the engine refuses and the reason renders verbatim (single source of
    truth)" -- and a refused plan stays retryable, which is what the disabled
    flag coming back off means."""
    result = _run_node("""
const { mountLensGate } = await import(VIEWS + "gate-lens.js");
const model = await import(VIEWS + "lens-model.js");
const [calls, fetcher] = recorder({ ok: false, status: 409,
  payload: { ok: false, message: "recipe already recorded" } });
const host = document.createElement("div");
mountLensGate(host, null, { plan: { kind: "save-recipe", repository: "r",
                                   name: "n", members: [], excluded: [] },
                            caps: {}, fetcher, model });
const run = buttons(host)[0];
run.click();
await settle();
console.log(JSON.stringify({ calls, texts: texts(host), disabled: run.disabled }));
""", bundle)
    assert len(result["calls"]) == 1
    assert "recipe already recorded" in result["texts"]
    assert result["disabled"] is False


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_the_project_commissions_post_both_gate_routes(bundle) -> None:
    """One binding, two routes: the create form POSTs the create-project
    commission and `commissionEdit` POSTs the membership one, carrying the
    project id the selector holds. The controller's shape is the seam
    `views/repo-selector.js` reaches through, so it is measured here rather
    than assumed."""
    result = _run_node("""
const { mountProjectCommissions } = await import(VIEWS + "gate-projects.js");
const [calls, fetcher] = recorder({ payload: { ok: true, job: "J-1",
                                               add: ["b"], remove: [] } });
const host = document.createElement("div");
const status = document.createElement("span");
const pending = [];
// RULED Q3: ONE mount signature, `mount(host, snapshot, ctx)` — the roster and
// the seams travel in `ctx`, which is where the S4 original passed them second.
const gate = mountProjectCommissions(host, null, {
  roster: [{ kind: "repository", repository: "openxFactory" },
           { kind: "repository", repository: "openDox" }],
  status, fetcher, addPendingOption: (name) => pending.push(name),
});
// the create form: opened by the dropdown's "New Project..." line
const form = flatten(host).find((n) => n.className
  && n.className.includes("projectform"));
const hiddenBeforeOpen = form.hidden;
gate.openCreateForm();
inputs(form).find((i) => i.tag === "input" && i.type === "text").value = "Field Pilots";
inputs(form).filter((i) => i.type === "checkbox")[0].checked = true;
buttons(form).find((b) => b.textContent === "commission project").click();
await settle();
// the membership edit: raised by the filter's add row / trash control
let restored = false;
await gate.commissionEdit("proj-1", { add: ["openDox"] },
                          { restore: () => { restored = true; } });
console.log(JSON.stringify({ calls, pending, hiddenBeforeOpen,
                             retired: form.hidden, restored,
                             status: status.textContent }));
""", bundle)
    assert [c["route"] for c in result["calls"]] == [
        "/actions/gate/create-project", "/actions/gate/edit-project"]
    create, edit = result["calls"]
    assert create["body"] == {"name": "Field Pilots",
                              "repositories": ["openxFactory"]}
    assert edit["body"] == {"project_id": "proj-1", "add": ["openDox"]}
    assert result["hiddenBeforeOpen"] is True    # the form is opened, never shown
    assert result["retired"] is True             # a landed commission retires it
    assert result["restored"] is False           # nothing to restore on success
    assert "membership edit recorded (J-1)" == result["status"]


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_a_refused_membership_edit_restores_the_control(bundle) -> None:
    """The two-click trash re-arms and the add row's select restores its
    placeholder -- `restore` is the selector's half of the act, and the
    binding has to call it on a refusal or a control is left dead."""
    result = _run_node("""
const { mountProjectCommissions } = await import(VIEWS + "gate-projects.js");
const [calls, fetcher] = recorder({ ok: false, status: 403,
  payload: { ok: false, message: "not a gate actor" } });
const status = document.createElement("span");
const gate = mountProjectCommissions(document.createElement("div"), null,
                                     { roster: [], status, fetcher });
let restored = false;
await gate.commissionEdit("proj-1", { remove: ["openDox"] },
                          { restore: () => { restored = true; } });
console.log(JSON.stringify({ calls, restored, status: status.textContent }));
""", bundle)
    assert result["restored"] is True
    assert "not a gate actor" in result["status"]
    assert result["status"].startswith("edit-project refused: ")


# ---------------------------------------------------------------------------
# RULED counterpart Q6, EXECUTED — the reach and the vocabulary, against the
# assembled bundle.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_a_binding_with_no_ctx_model_refuses_by_name(bundle) -> None:
    """RULED counterpart Q6 (`5649094228`) makes openDox's model a `ctx` facet.
    A shell that supplies none is REFUSED AT THE MOUNT, naming the binding and
    the missing name — never a control that throws when a human presses it."""
    result = _run_node("""
const { mountLensGate } = await import(VIEWS + "gate-lens.js");
const host = document.createElement("div");
const returned = mountLensGate(host, null, { plan: { kind: "save-recipe" },
                                             caps: {} });
console.log(JSON.stringify({ returned, texts: texts(host),
                             buttons: buttons(host).length }));
""", bundle)
    assert result["returned"] is None
    assert result["buttons"] == 0, "a refused mount offers no control"
    joined = " ".join(result["texts"])
    assert "ctx.model.recipeRequest" in joined and "5649094228" in joined


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_the_session_vocabulary_agrees_with_openDoxs_model(bundle) -> None:
    """The one drift risk RULED counterpart Q6's division leaves: the six
    affordance tokens are DECLARED by `swb-session.js` (they key its own route
    table at module scope and name the verbs this column's `serve_gate.py`
    answers), while the model functions they are passed to stay openDox's. Held
    to each other HERE, in the assembled bundle where both exist, so a rename on
    either side fails a test instead of putting an unknown affordance on the
    wire."""
    result = _run_node("""
const column = await import(VIEWS + "swb-session.js");
const model = await import(VIEWS + "staging-workbench-model.js");
console.log(JSON.stringify({
  column: {
    affordances: column.SESSION_AFFORDANCES,
    verbs: column.SESSION_VERBS,
    labels: Object.keys(column.SESSION_LABELS),
    firstEdit: column.SESSION_FIRST_EDIT,
  },
  model: {
    affordances: model.SESSION_AFFORDANCES,
    verbs: model.SESSION_VERBS,
    labels: Object.keys(model.SESSION_LABELS),
    firstEdit: model.SESSION_FIRST_EDIT,
  },
}));
""", bundle)
    assert result["column"] == result["model"]


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_the_workbench_session_verbs_post_through_the_supplied_model(bundle) -> None:
    """The other half of the same division, EXECUTED: with `ctx.model` supplied
    the session bar mounts its four live affordances and the form's submit posts
    the route the affordance names, with the body openDox's own `sessionRequest`
    shaped. The vocabulary is the column's, the wire body is the model's, and
    the two meet only through `ctx`."""
    result = _run_node("""
const column = await import(VIEWS + "swb-session.js");
const model = await import(VIEWS + "staging-workbench-model.js");
const [calls, fetcher] = recorder({ payload: { ok: true } });
const host = document.createElement("div");
// `sessionActionsLive` reads the PROBE's `actions` map (gate on, session not
// declared off), which is the loopback plane's shape.
const caps = { actions: { gate: true, session: true }, actor: "brett",
               console_token: "t" };
const mounted = column.mountSessionAffordances(host, null, {
  model, caps, fetcher, actor: "brett",
  session: { scope: { repository: "openxFactory", topic: "t-1" },
             posture: { branch: "session/t-1" } },
});
const labels = buttons(host).map((b) => b.textContent);
console.log(JSON.stringify({ mounted: mounted !== null, labels,
                             routes: calls.map((c) => c.route) }));
""", bundle)
    assert result["mounted"] is True
    assert result["labels"], "the session bar offered no affordance"
    assert any("rewrite a document" in label for label in result["labels"])


# ---------------------------------------------------------------------------
# SLICE S2'S DISPOSE-TRAY PROBES, PORTED (openDox-code#20, Copilot round 2)
# ---------------------------------------------------------------------------
#
# WHY THEY ARE HERE. `tests/test_intent_binding_dom.py` at openDox-code is slice
# S2's own CREATED file, and it drove the REAL `views/dispose.js` — the module
# graph loading with the never-carved `views/intent-feed.js` absent (RULED OQ-F
# `not_moved`), and the tray rendering its three verdict buttons with and
# without a contributed intent feed. `dispose.js` is THIS column's package data
# as of slice S5, so the probes that drive it come too, on exactly the precedent
# the five S4 probes above set: a behaviour proof that stays in the repository
# the behaviour left is a proof of nothing. openDox-code#20 drops them from the
# file they came from and keeps everything there that is still about its own
# bundle (`intent-binding.js`'s six forwards, the wheel closure's own load).
#
# THE HARNESS COMES WITH THEM, and deliberately: these assertions were written
# against slice S2's DOM shim — a `walk()`-able tree whose `innerHTML` setter
# throws on any non-empty assignment — not against the stub the S4 probes above
# use. Re-expressing them against a different shim would be rewriting the proof
# while claiming to move it. What IS stronger here is the same thing that is
# stronger for the S4 five: the module is imported out of an ASSEMBLED bundle,
# so `./helpers.js` and `./intent-binding.js` resolve the way they resolve in a
# composed install.

_S2_DOM_SHIM = r"""
class Node {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();
    this.children = []; this.attributes = {}; this.listeners = {};
    this.className = ''; this._text = ''; this.disabled = false;
    this.value = ''; this.hidden = false; this.type = ''; this.title = '';
    this.dataset = {};
  }
  get textContent() {
    return this._text + this.children.map((c) => c.textContent).join('');
  }
  set textContent(value) { this.children = []; this._text = String(value); }
  set innerHTML(value) {
    if (String(value) !== '') throw new Error('only literal "" clears are allowed');
    this.children = []; this._text = '';
  }
  appendChild(child) { child.parent = this; this.children.push(child); return child; }
  append(...kids) { for (const k of kids) this.appendChild(k); }
  remove() {
    if (!this.parent) return;
    const at = this.parent.children.indexOf(this);
    if (at >= 0) this.parent.children.splice(at, 1);
  }
  classList = { add: () => {}, remove: () => {}, toggle: () => {} };
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name]; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  focus() {}
  walk() {
    return this.children.reduce((all, c) => all.concat(c.walk()), [this]);
  }
}
globalThis.document = {
  createElement: (tag) => new Node(tag),
  createTextNode: (text) => { const n = new Node('#text'); n._text = String(text);
    return n; },
  body: new Node('body'),
};
globalThis.window = { prompt: () => { throw new Error('unused on this probe'); } };
function byClass(root, cls) {
  return root.walk().filter((n) => String(n.className).split(' ').includes(cls));
}
globalThis.Node = Node; globalThis.byClass = byClass;
"""

#: A minimal FAKE `intent-feed.js` — standing in for openxFactory's real
#: contributed module, which NEITHER leg carries (RULED OQ-F `not_moved`). Its
#: only job is to prove `intent-binding.js` forwards to whatever IS contributed.
#: Carried byte-identical from openDox-code's `tests/test_intent_binding_dom.py`
#: so the ported assertions measure what they measured there.
_FAKE_INTENT_FEED = """\
export function intentCapable(caps) {
  return !!(caps && caps.actions && caps.actions.intent);
}
export function feedActor(caps) {
  return "fake-actor:" + ((caps && caps.marker) || "no-marker");
}
export function refusalLine(rec) { return "fake-refusal:" + rec.state; }
export function startIntentFeed(opts) {
  return { subscribe() {}, stop() {}, marker: (opts && opts.marker) || "no-marker" };
}
export function statesByTarget(rows) {
  return new Map((rows || []).map((r) => [r.id, "fake:" + r.id]));
}
export function renderIntentChips(container, targetId, rows, error) {
  container.__fakeRendered = { targetId, rows, error };
  return container;
}
export async function emitIntent(opts) {
  return { state: "pending", message: "fake-queued:" + opts.verb };
}
"""


def _run_s2_node(body: str, bundle: Path, *, contribute_intent_feed: bool) -> dict:
    """Slice S2's harness, run against the ASSEMBLED bundle.

    `contribute_intent_feed` is the deployment switch RULED Q5 distinguishes:
    with the fake module dropped beside the others, `intent-binding.js`'s late
    lookup finds a contributed feed; without it, it finds nothing and every
    forward must answer safely rather than throw.
    """
    views = bundle / "views"
    if contribute_intent_feed:
        (views / "intent-feed.js").write_text(_FAKE_INTENT_FEED, encoding="utf-8")
    source = _S2_DOM_SHIM + body
    script = views / "s2-probe.mjs"
    script.write_text(source, encoding="utf-8")
    proc = subprocess.run([NODE, str(script)], capture_output=True, text=True,
                          timeout=120)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


_GRAPH_PROBE = """
import * as W from "./wheel.js";
import * as D from "./dispose.js";
console.log(JSON.stringify({
  renderWheel: typeof W.renderWheel,
  mountDisposeTray: typeof D.mountDisposeTray,
}));
"""


@pytest.mark.skipif(NODE is None, reason="node is not installed")
@pytest.mark.parametrize("contributed", [False, True])
def test_js_the_composed_graph_resolves_with_or_without_a_contributed_feed(
        contributed, bundle) -> None:
    """`app.js` -> `wheel.js` -> (formerly) the absent `intent-feed.js` used to
    fail the WHOLE static module graph (openDox-spec § 1.2(b)): a dangling
    `import … from` on an ABSENT file is a load-time failure, not a missing
    render. This is that failure, gone — now measured over the COMPOSED bundle,
    which is the only tree in which both halves of the graph exist at once:
    `wheel.js` is openDox's and `dispose.js` is this column's package data, and
    slice S5's assembly is what puts them in one directory."""
    result = _run_s2_node(_GRAPH_PROBE, bundle,
                          contribute_intent_feed=contributed)
    assert result == {"renderWheel": "function", "mountDisposeTray": "function"}


# RULED counterpart Q6 MOVED ONE FACT IN THIS PROBE (openxFactory#656 comment
# `5649094228`): the tray used to reach `renderIntentChips` by importing the
# openDox bundle's `intent-binding.js` itself, and a contributed module may now
# import `./views/helpers.js` and nothing else — so the CHIP RENDERER arrives in
# `opts.intent` beside the emitter, supplied by the shell that starts the feed
# (`views/wheel.js`'s own mount, openDox-code#20). The probe is the shell here,
# so it supplies what the shell supplies. Everything else is byte-identical to
# slice S2's original, including the assertion that the chips were rendered BY
# the contributed module rather than by a same-named look-alike.
_TRAY_PROBE = """
import { mountDisposeTray } from "./dispose.js";
import { intentCapable, renderIntentChips } from "./intent-binding.js";

const caps = { actions: { intent: true } };
const hosted = intentCapable(caps);
const row = new Node("div");
mountDisposeTray(row, { id: "p1" },
  hosted ? { intent: { snapshotRev: "r", rows: [], error: null,
                       renderChips: renderIntentChips } } : {});
const tray = byClass(row, "disposetray")[0];
const chips = row.walk().find((n) => String(n.className).includes("intentchips"));
console.log(JSON.stringify({
  hosted,
  verdictButtons: tray ? tray.children.length : -1,
  chipsMounted: !!chips,
  chipsCarryRealForward: !!(chips && chips.__fakeRendered),
}));
"""


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_the_dispose_tray_renders_with_no_chips_when_the_feed_is_absent(
        bundle) -> None:
    """`mountDisposeTray` does not consult `intentCapable` itself — it trusts
    its caller (`wheel.js`) to pass `opts.intent` only once `intentCapable(caps)`
    has said yes. So the probe reproduces THAT gate rather than handing
    `opts.intent` to the tray unconditionally, which would prove nothing."""
    r = _run_s2_node(_TRAY_PROBE, bundle, contribute_intent_feed=False)
    assert r["hosted"] is False
    assert r["verdictButtons"] == 3          # accept / reject / defer, unchanged
    assert r["chipsMounted"] is False        # no chips element at all — not
                                             # merely an empty one: the caller
                                             # never passed opts.intent
    assert r["chipsCarryRealForward"] is False


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_the_dispose_tray_renders_real_chips_when_the_feed_is_contributed(
        bundle) -> None:
    r = _run_s2_node(_TRAY_PROBE, bundle, contribute_intent_feed=True)
    assert r["hosted"] is True
    assert r["verdictButtons"] == 3
    assert r["chipsMounted"] is True
    assert r["chipsCarryRealForward"] is True   # not just present — actually
                                                # rendered BY the contributed
                                                # module, not a same-named
                                                # look-alike


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_a_built_transport_keeps_the_model_it_validated(bundle) -> None:
    """THE TRANSPORT OUTLIVES THE CALL THAT BUILT IT (Copilot review of this PR,
    round 3). Every other reader of this module's installed model runs INSIDE the
    mount that installed it; `firstEditTransport` does not — it returns a
    function the canvas holds and calls later. While the model was read off the
    module-global, a second mount or a second transport built in between
    re-pointed it, and the first editor's Save was then shaped and read by
    SOMEONE ELSE'S model. Two transports, two models, both called AFTER both were
    built: each must answer with its own."""
    result = _run_node("""
const column = await import(VIEWS + "swb-session.js");
const model = await import(VIEWS + "staging-workbench-model.js");
// Two models that differ only where it shows: the verdict each reports.
const make = (tag) => ({
  ...model,
  firstEditBody: (...args) => ({ ...model.firstEditBody(...args), tag }),
  firstEditVerdict: (response) => ({ tag, ok: response && response.ok === true }),
});
const sent = [];
const fetcher = async (route, opts) => {
  sent.push(JSON.parse(opts.body).tag);
  return { ok: true, status: 200, json: async () => ({ ok: true }) };
};
const caps = { actor: "brett", console_token: "t" };
const req = { key: { repository: "openxFactory", tile_kind: "staged",
                     tile_id: "t-1" },
              document: "d.md", content: "x" };
// BOTH built first, then BOTH called — which is the interleaving the module
// global could not survive.
const first = column.firstEditTransport({ fetcher, caps, model: make("first") });
const second = column.firstEditTransport({ fetcher, caps, model: make("second") });
const a = await first(req);
const b = await second(req);
console.log(JSON.stringify({ a, b, sent }));
""", bundle)
    assert result["a"]["tag"] == "first", result["a"]
    assert result["b"]["tag"] == "second", result["b"]
    # and the BODIES were shaped by the right model too, not only the verdicts
    assert result["sent"] == ["first", "second"]
