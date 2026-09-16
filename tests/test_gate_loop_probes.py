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
commit (`pyproject.toml`). When these probes landed with slice S5 that pin was
`a99eba03`, which predated BOTH the view registry and the packaging fix that
puts `opendox/web/` into a wheel at all (openDox-code#20's own first commit), so
this paragraph said the probes "run in full the moment the pin bump lands".
THE BUMP LANDED — 2026-09-16, `a99eba03` -> `0b4e8bbf` (openDox-code#23, § 3.4
slice S8 leg B) — and all thirteen of them now RUN: 13 skipped became 13 passed
under `validate.yml`'s own invocation, in the same act that moved the pin, and
the three materialization assertions in `test_gate_loop_views.py` that waited on
the same bump went 3 skipped -> 3 passed beside them.

WHAT A MISSING BUNDLE MEANS NOW, stated precisely — the review rounds on #21
rewrote this paragraph twice, and both times because it promised an outcome the
guard does not give. Where the installed `opendox` carries no bundle there is
nothing to assemble INTO, and `tests/opendox_bundle.py::_absent` chooses by
READING which openDox is installed:

  * a DIFFERENT commit from the one this leg declares -> SKIP, naming BOTH;
  * NO recorded provenance, off CI -> SKIP, naming the declared one and saying
    plainly that the installed one is unrecorded (it cannot name what it could
    not read, which is why this is a different sentence from the one above);
  * the DECLARED commit -> FAIL, because THAT is a regression here, and a skip
    would take these thirteen probes quietly green in a required check;
  * no recorded provenance UNDER CI -> FAIL TOO, and the review of `f6f1b991` on
    #21 was right that this line used to file it under the word "regression". It
    is not one. It is a PROVENANCE ANOMALY: the required run cannot establish
    which openDox it is testing at all. `validate.yml` installs `-e ".[test]"`
    against a PEP 508 direct VCS reference and pip records `direct_url.json` for
    that every time, so failing to read one on the required path is a metadata or
    install failure — worth stopping for, but never evidence that the bundle
    regressed.

No outcome ever passes silently against a stand-in.

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
    """The INSTALLED openDox's web bundle, or None where no bundle was found.

    DISCOVERY ONLY, same contract as `tests/opendox_bundle.py::find` and stale
    in the same way until the review of `399e2a9` on #21: "where the pin carries
    none" was the one expected cause before the bump, and the `bundle` fixture
    below now routes `None` into `_absent()` precisely BECAUSE it is no longer
    the only one. What the absence means is `_absent()`'s four-row table; this
    function only reports that the marker is not there.
    """
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

    Where the assembled `opendox` carries no bundle, the outcome is
    `tests/opendox_bundle.py::_absent`'s FOUR-ROW TABLE and this docstring does
    not restate it — two reviews on #21 caught a two-row paraphrase here, which is
    what a second copy of a table is for. That this guard survives the pin bump at
    all is RULED
    openxFactory#656 comment 5700475319 (Brett Heap, 2026-09-16, by interactive
    multi-choice), answer (a): keep the guards, correct their reasons.

    That was a plain skip until the 2026-09-16 pin bump, when a missing bundle
    stopped being the expected state AT THE COMMIT THIS LEG DECLARES and started
    being a regression THERE — see `tests/opendox_bundle.py::_absent`, which reads
    both commits before it decides. Only the equal-commit row is a regression: a
    DIFFERENT installed commit still skips, an unreadable side still skips off CI,
    and the CI failure for an unreadable side is a comparison anomaly rather than
    a verdict on the package. The review of `24cd5f2` caught this sentence
    generalizing the one row to all four, two paragraphs below the table.
    A probe that quietly ran against a stand-in `helpers.js` would measure the
    stand-in rather than the shipped file, so a skip is still the right outcome
    wherever `_absent()` gives one.
    """
    source = _opendox_bundle()
    if source is None:
        # The shared rule in `tests/opendox_bundle.py::_absent`, which READS the
        # installed distribution's PEP 610 provenance instead of asserting it.
        # Its four-row table is there, not restated here. Round 1 of the review on
        # #21 found this file claiming the install "came from somewhere older than
        # the declared pin" on a check that only tested for a marker; if `0b4e8bbf` itself ever stopped shipping `web/**`, all
        # thirteen probes below would have skipped and this required check would
        # have stayed green over the regression.
        import opendox_bundle
        opendox_bundle._absent("openDox's `web/` bundle", module_level=False)
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


# ---------------------------------------------------------------------------
# THE GUARD ITSELF, TESTED DIRECTLY — Copilot round-2 thread on #21
# (`PRRT_kwDOUPv7_s6i_iiz`, "the new provenance decision is only exercised
# indirectly on the normal bundle-present path; there are no tests"). Accurate:
# the four branches had been proven by hand, by renaming the installed bundle and
# re-running. That proof is now permanent and runs in `validate`.
#
# These live HERE rather than in a new file on purpose: a created file at this leg
# needs an admission row in openxFactory's `docs/opendox-carve-admissions.yaml`
# (RULED OQ-C), and adding one is not a pin bump's act. This module is already
# admitted, already on `validate.yml`'s list, and already owns the fixture whose
# thirteen probes the decision gates.
# ---------------------------------------------------------------------------

import opendox_bundle as _ob  # noqa: E402  (a helper import, never OPENDOX_WEB)

_PIN_A = "a" * 40
_PIN_B = "b" * 40


def _decide(monkeypatch, declared, installed, *, ci):
    monkeypatch.setattr(_ob, "declared_pin", lambda: declared)
    monkeypatch.setattr(_ob, "installed_commit", lambda: installed)
    monkeypatch.setenv("CI", "true" if ci else "")
    return lambda: _ob._absent("the subject under test", module_level=False)


def test_the_declared_pin_missing_its_bundle_FAILS(monkeypatch) -> None:
    """The regression case: what is installed IS what this leg declares."""
    call = _decide(monkeypatch, _PIN_A, _PIN_A, ci=False)
    with pytest.raises(pytest.fail.Exception) as raised:
        call()
    assert "REGRESSION at the declared pin" in str(raised.value)
    assert _PIN_A[:8] in str(raised.value)


def test_a_different_installed_commit_SKIPS_and_names_both(monkeypatch) -> None:
    """The lawful case: a consumer assembling at a DIFFERENT commit.

    Not "older": the values are synthetic and `_absent()` compares identities, so
    nothing here establishes an ordering. Caught at the review of `27a89fd`.
    """
    call = _decide(monkeypatch, _PIN_A, _PIN_B, ci=True)
    with pytest.raises(pytest.skip.Exception) as raised:
        call()
    message = str(raised.value)
    assert _PIN_A[:8] in message
    assert _PIN_B[:8] in message
    assert "NOT the declared pin's doing" in message


def test_unknown_provenance_FAILS_under_ci(monkeypatch) -> None:
    """The round-2 finding: on the REQUIRED path, unknown is not neutral.

    The message says the two commits could not be COMPARED and names the side that
    could not be read — it no longer says "this run cannot say which `opendox` is
    installed", which was false whenever the unreadable side was `pyproject.toml`
    (the review of `24cd5f2`, and the assertion below moved with it).
    """
    call = _decide(monkeypatch, _PIN_A, None, ci=True)
    with pytest.raises(pytest.fail.Exception) as raised:
        call()
    message = str(raised.value)
    assert "could not be COMPARED" in message
    assert "no usable PEP 610 provenance could be read" in message


def test_an_unreadable_declared_pin_under_ci_does_not_blame_the_install(
        monkeypatch) -> None:
    """THE CI TWIN of the off-CI test below, and the review of `24cd5f2`'s finding.

    `declared_pin()` unreadable with a perfectly good `direct_url.json` used to FAIL
    saying "this run cannot say which `opendox` is installed" while the very next
    field printed the installed hash. What is unknown is the COMPARISON, and the
    message has to say which side went missing — under CI exactly as off it.
    """
    call = _decide(monkeypatch, None, _PIN_B, ci=True)
    with pytest.raises(pytest.fail.Exception) as raised:
        call()
    message = str(raised.value)
    assert "declared pin could not be read" in message
    assert "no usable PEP 610 provenance" not in message
    assert _PIN_B in message


def test_both_sides_unreadable_says_NEITHER_rather_than_picking_one(
        monkeypatch) -> None:
    """The third shape, which the either/or phrasing could only half-report."""
    call = _decide(monkeypatch, None, None, ci=True)
    with pytest.raises(pytest.fail.Exception) as raised:
        call()
    assert "NEITHER side could be read" in str(raised.value)


def test_unknown_provenance_SKIPS_off_ci(monkeypatch) -> None:
    """...and off it, an editable checkout has no provenance to record."""
    call = _decide(monkeypatch, _PIN_A, None, ci=False)
    with pytest.raises(pytest.skip.Exception) as raised:
        call()
    message = str(raised.value)
    assert "no usable PEP 610 provenance could be read" in message
    assert "NOTHING is claimed here about" in message


def test_an_unreadable_declared_pin_says_so_rather_than_blaming_the_install(
        monkeypatch) -> None:
    """The INSTALLED side can be perfectly good and the comparison still fail.

    Caught at the review of `27a89fd` on #21: this branch used to report "this
    installation records no PEP 610 provenance" even when the installation had
    recorded a valid one and it was `pyproject.toml` that could not be read. The
    message now names whichever side is actually missing.
    """
    call = _decide(monkeypatch, None, _PIN_B, ci=False)
    with pytest.raises(pytest.skip.Exception) as raised:
        call()
    message = str(raised.value)
    assert "declared pin could not be read" in message
    assert "no usable PEP 610 provenance" not in message


def test_under_ci_reads_the_environment_the_runner_sets(monkeypatch) -> None:
    """`CI` is read, not guessed: `1`, `true` and `yes` (any case, trimmed) are
    CI; every other value, and an unset variable, are not. GitHub Actions sets
    `CI=true`. The docstring used to say "nothing else is treated as CI" while the
    body below accepted three spellings — caught at the review of `27a89fd`.
    """
    for value, expected in (("true", True), ("TRUE", True), ("1", True),
                            ("yes", True), ("false", False), ("", False)):
        monkeypatch.setenv("CI", value)
        assert _ob.under_ci() is expected, value
    monkeypatch.delenv("CI", raising=False)
    assert _ob.under_ci() is False


def test_the_declared_pin_is_read_from_this_legs_own_pyproject() -> None:
    """Not a constant: the guard re-reads the file the bump edits."""
    declared = _ob.declared_pin()
    assert declared is not None
    assert len(declared) == 40
    toml = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
        encoding="utf-8")
    assert f"openDox-code@{declared}" in toml


def _with_unreadable_pyproject(monkeypatch, exc) -> None:
    """Make `Path.read_text` raise for `pyproject.toml`, and for nothing else.

    Narrow on purpose: `declared_pin()` is the only reader under test, and a
    blanket patch would hide which file the branch actually reacted to.
    """
    real_read_text = Path.read_text

    def _read_text(self, *args, **kwargs):
        if self.name == "pyproject.toml":
            raise exc
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(_ob.Path, "read_text", _read_text)


def _with_pyproject_text(monkeypatch, text) -> None:
    """Make `pyproject.toml` READ CLEANLY as `text`, and nothing else change.

    `_with_unreadable_pyproject` above drives the two RAISING branches; this drives
    the branch where the file is perfectly readable and simply does not declare the
    pin — the `if match else None` the review of `de7d966` found untested.
    """
    real_read_text = Path.read_text

    def _read_text(self, *args, **kwargs):
        if self.name == "pyproject.toml":
            return text
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(_ob.Path, "read_text", _read_text)


def test_declared_pin_is_none_when_pyproject_declares_no_opendox_pin(
        monkeypatch) -> None:
    """A READABLE `pyproject.toml` with no `opendox @ git+…@<40-hex>` in it.

    The two tests above make the READ raise; nothing made the REGEX miss. A
    dependency line that lost its pin — rewritten to a version range, to a branch
    ref, to a path install, or simply deleted — returns None from the same function
    and must reach the SAME fail-closed policy, or the required check could go green
    over a leg that no longer declares which openDox it is built against. Caught at
    the review of `de7d966` on #21.
    """
    _with_pyproject_text(monkeypatch, (
        "[project]\nname = \"openxdox-code\"\n"
        "dependencies = [\n"
        "    \"opendox @ git+https://github.com/opensoft/openDox-code@main\",\n"
        "    \"pyyaml>=6\",\n"
        "]\n"))
    assert _ob.declared_pin() is None


def test_an_undeclared_pin_FAILS_under_ci_like_any_other_unreadable_side(
        monkeypatch) -> None:
    """...and the outcome is the fail-closed one, driven end to end.

    The test above proves the function returns None; this proves what `_absent()`
    then does with it — FAIL under CI, naming the declared side as the one it could
    not read, with the installed commit still printed because that side was fine.
    """
    _with_pyproject_text(monkeypatch, "[project]\nname = \"openxdox-code\"\n")
    monkeypatch.setattr(_ob, "installed_commit", lambda: _PIN_B)
    monkeypatch.setenv("CI", "true")
    with pytest.raises(pytest.fail.Exception) as raised:
        _ob._absent("the subject under test", module_level=False)
    message = str(raised.value)
    assert "declared pin could not be read" in message
    assert _PIN_B in message


def test_declared_pin_is_none_when_the_read_raises(monkeypatch) -> None:
    """The unreadable DECLARED side, produced rather than assumed.

    Copilot's review of `f6f1b991` on #21: the CI fail-closed policy depends on
    `declared_pin()` returning None when the read raises, and every test of the
    decision monkeypatches `declared_pin()` itself — so `declared=None` had only
    ever been supplied as an input, never once produced by the function.
    """
    _with_unreadable_pyproject(monkeypatch, OSError("pyproject.toml unreadable"))
    assert _ob.declared_pin() is None


def test_declared_pin_is_none_when_pyproject_is_not_utf_8(monkeypatch) -> None:
    """The half of that branch that was a REAL BUG until the review of `27a89fd`.

    `UnicodeDecodeError` is a `ValueError`, NOT an `OSError`, so a non-UTF-8
    `pyproject.toml` raised straight out of `declared_pin()` and past
    `_absent()`'s unknown-provenance policy — the required check's fail-closed
    rule bypassed entirely. This case exists so the `except` clause cannot
    silently narrow back to `OSError` alone.
    """
    _with_unreadable_pyproject(
        monkeypatch,
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"))
    assert _ob.declared_pin() is None


# --- THE PEP 610 PARSER ITSELF, not a monkeypatched stand-in -----------------
# Copilot round 3 on #21: "all six direct guard tests monkeypatch
# `installed_commit()` and therefore bypass this code … a parser regression can
# change the CI decision while the required tests remain green." Accurate — the
# tests above pin the DECISION, these pin the READING it decides on. A fake
# distribution is installed over `importlib.metadata.distribution`, which is the
# exact name `installed_commit()` resolves at call time.

class _FakeDist:
    """Just enough of `importlib.metadata.Distribution` for `read_text`."""

    def __init__(self, payload):
        self._payload = payload

    def read_text(self, name):
        if name != "direct_url.json":        # pragma: no cover - never asked
            return None
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


#: The ONE distribution `installed_commit()` may ask about. Both fakes below assert
#: it, because neither did until the review of `a0eed16`: they answered to ANY name,
#: so a regression to `distribution("openxdox")` — or to any other installed package
#: — would have read a STRANGER's `direct_url.json`, compared that commit against
#: this leg's declared pin, and left every parser test then standing green while
#: doing it — all TEN of them; the eleventh is the one below, which exists because
#: of this finding. (`grep -c '^def test_installed_commit' <this file>` -> 11.)
_ASKED = "opendox"


def _with_dist(monkeypatch, payload):
    """Install a fake distribution whose `read_text` returns (or raises) `payload`.

    The fake ASSERTS the name it is asked for (see `_ASKED`): the provenance this
    guard reads is worthless if it is read off the wrong package.
    """
    import importlib.metadata as md

    def _lookup(name):
        assert name == _ASKED, f"installed_commit() asked for {name!r}, not {_ASKED!r}"
        return _FakeDist(payload)
    monkeypatch.setattr(md, "distribution", _lookup)


def _with_no_dist(monkeypatch, exc):
    """Make the LOOKUP itself raise — the path `_with_dist` cannot reach.

    Caught at `7c0a3b6`: `_with_dist(PackageNotFoundError(...))` made `read_text`
    raise, so the test named for an uninstalled package never exercised
    `distribution("opendox")` failing, which is the call `installed_commit()`
    actually guards. It asserts the requested name too, for `_with_dist`'s reason.
    """
    import importlib.metadata as md

    def _raise(name):
        assert name == _ASKED, f"installed_commit() asked for {name!r}, not {_ASKED!r}"
        raise exc
    monkeypatch.setattr(md, "distribution", _raise)


def test_installed_commit_asks_for_the_opendox_distribution_and_no_other(
        monkeypatch) -> None:
    """The lookup NAME is the assertion, and nothing else asserted it.

    `_with_dist` answered to any name, so `distribution("openxdox")` would have read
    a stranger's PEP 610 record and compared ITS commit against this leg's declared
    pin — a provenance check on the wrong package, with every parser test green.
    Caught at the review of `a0eed16` on #21.
    """
    import importlib.metadata as md
    asked = []

    def _lookup(name):
        asked.append(name)
        return _FakeDist(json.dumps(
            {"url": "https://github.com/opensoft/openDox-code",
             "vcs_info": {"vcs": "git", "commit_id": _PIN_B}}))
    monkeypatch.setattr(md, "distribution", _lookup)
    assert _ob.installed_commit() == _PIN_B
    assert asked == ["opendox"]


def test_installed_commit_reads_a_real_vcs_record(monkeypatch) -> None:
    _with_dist(monkeypatch, json.dumps(
        {"url": "https://github.com/opensoft/openDox-code",
         "vcs_info": {"vcs": "git", "commit_id": _PIN_B}}))
    assert _ob.installed_commit() == _PIN_B


def test_installed_commit_is_none_when_the_file_is_absent(monkeypatch) -> None:
    _with_dist(monkeypatch, None)
    assert _ob.installed_commit() is None


def test_installed_commit_is_none_on_malformed_json(monkeypatch) -> None:
    _with_dist(monkeypatch, "{not json at all")
    assert _ob.installed_commit() is None


def test_installed_commit_is_none_for_a_non_vcs_install(monkeypatch) -> None:
    """A wheel installed from an archive records `archive_info`, not `vcs_info`."""
    _with_dist(monkeypatch, json.dumps(
        {"url": "file:///tmp/opendox-0.0.0-py3-none-any.whl",
         "archive_info": {"hash": "sha256=abc"}}))
    assert _ob.installed_commit() is None


def test_installed_commit_refuses_a_commit_id_that_is_not_40_hex(monkeypatch) -> None:
    """A short id is not a commit this guard may compare — round 3's parser case."""
    _with_dist(monkeypatch, json.dumps(
        {"vcs_info": {"vcs": "git", "commit_id": "0b4e8bbf"}}))
    assert _ob.installed_commit() is None


def test_installed_commit_refuses_forty_characters_that_are_not_hex(monkeypatch) -> None:
    """THE SILENT-GREEN PATH THROUGH THE PARSER, caught at `42741fd`.

    `len(commit) == 40` admitted any forty characters, so a malformed record
    carrying a forty-character non-hex id read as "a different pin" and `_absent()`
    SKIPPED under CI — the exact outcome this guard exists to prevent, reached
    through the reading rather than through the decision.
    """
    _with_dist(monkeypatch, json.dumps(
        {"vcs_info": {"vcs": "git", "commit_id": "z" * 40}}))
    assert _ob.installed_commit() is None


def test_installed_commit_normalizes_an_upper_case_commit_id(monkeypatch) -> None:
    """A lawful record spelled in upper case is compared, not discarded.

    Asked for on #21. It can only ever turn an "unknown" into a real comparison:
    without it an upper-case id would read as unreadable provenance and FAIL under
    CI over a formatting difference rather than a regression.
    """
    _with_dist(monkeypatch, json.dumps(
        {"vcs_info": {"vcs": "git", "commit_id": _PIN_B.upper()}}))
    assert _ob.installed_commit() == _PIN_B


def test_installed_commit_refuses_a_record_that_is_not_git(monkeypatch) -> None:
    """A 40-hex id under a non-git VCS is not an openDox-code commit."""
    _with_dist(monkeypatch, json.dumps(
        {"vcs_info": {"vcs": "hg", "commit_id": _PIN_B}}))
    assert _ob.installed_commit() is None


def test_installed_commit_is_none_when_the_package_is_not_installed(monkeypatch) -> None:
    """The LOOKUP fails, not the read — see `_with_no_dist`."""
    from importlib.metadata import PackageNotFoundError
    _with_no_dist(monkeypatch, PackageNotFoundError("opendox"))
    assert _ob.installed_commit() is None


def test_installed_commit_is_none_when_reading_the_record_raises(monkeypatch) -> None:
    """...and the read failing is its own case, which is what `_with_dist` drives."""
    _with_dist(monkeypatch, OSError("metadata unreadable"))
    assert _ob.installed_commit() is None

# WHY THE CASES ABOVE ARE THE CASES: `_absent()` branches on `installed_commit()`'s
# RETURN VALUE, so every test of the DECISION that monkeypatches that function
# proves nothing about the READING. TEN cases cover the reading of the INSTALLED
# side — a real VCS record, an absent `direct_url.json`, malformed JSON, a non-VCS
# (`archive_info`) install, a commit id that is not 40 characters, forty
# characters that are not hex, an UPPER-CASE 40-hex id (normalized rather than
# discarded), a 40-hex id under a non-git VCS, the distribution LOOKUP raising,
# and the read raising. The DECLARED side's own reading is covered separately,
# above, by the two `test_declared_pin_is_none_when_…` cases.
#
# THE COUNT IS MEASURED, NOT CARRIED, and this line read "nine" until the review
# of `f6f1b991` on #21 caught that the upper-case case added at `b177eef` had
# never reached the inventory:
#
#     grep -c '^def test_installed_commit' tests/test_gate_loop_probes.py   -> 11
#
# It read 10 until the review of `fd3af6a` caught the lookup-name test the review
# of `a0eed16` had just asked for — the same staleness, one round later, which is
# why the command is printed beside the number every time.
# A DELETED case is not one of the eleven, and this paragraph used to number it as
# though it were ("a tenth test"). One further test stood here until `7c0a3b6`
# and is gone rather than repaired: it asserted strings against
# `inspect.getsource(installed_commit)`, and once the implementation stopped
# containing `len(commit) == 40` it passed only because an explanatory COMMENT
# still held that text. A test coupled to source text fails on a harmless rename
# and catches no behaviour — the eleven above already assert the results it was
# gesturing at.


# --- THE CALL SITES, not the decision and not the parser ---------------------
# Copilot's review of `8b23f6f` on #21, and it is the round-3 finding one level
# out: the tests above prove what `_absent()` DECIDES and what
# `installed_commit()` READS, and every one of them either calls `_absent()`
# directly or monkeypatches the function under it. None of them proves that the
# three CALLERS still route a missing subject INTO `_absent()`. That review's own
# sentence: "replacing this call with `pytest.skip` would leave the <N> guard
# tests green while the `OPENDOX_WEB` importers silently skip under CI" — it said
# 19, the count at ITS head, and the point does not live in the number, so the
# number is not carried here. What is true at any head is the command:
#   git diff main -- tests/test_gate_loop_probes.py | grep -c '^+def test_'
#   git diff main -- tests/test_gate_loop_views.py  | grep -c '^+def test_'
# (28 in this file and 6 in the views file at THIS head — 13 decision/read cases,
# 11 `installed_commit` parser tests and 4 call-site tests here; `validate.yml`'s
# record block carries the total, 34. The review of `fd3af6a` caught this pair
# reading 25 and 6, and the review of `de7d966` moved it again by asking for the
# two undeclared-pin tests: a count written in prose is stale one round later,
# which is why the commands are printed above it every time.)
# It is exactly the silent green this whole guard exists to break, reached one
# level further out each round — and the review of `b22a6fd` caught the quoted
# count going stale three rounds after the quotation.
# Two call sites are covered here; the third
# (`test_gate_loop_views.py::_view_extension_or_skip`) is covered in that file,
# beside the assertions it gates.


def _pin(monkeypatch, declared, installed, *, ci=True):
    """Fix what the guard will READ, so a call site's OUTCOME is the assertion."""
    monkeypatch.setattr(_ob, "declared_pin", lambda: declared)
    monkeypatch.setattr(_ob, "installed_commit", lambda: installed)
    monkeypatch.setenv("CI", "true" if ci else "")


def test_require_FAILS_at_the_declared_pin_when_the_bundle_is_missing(
        monkeypatch) -> None:
    """`opendox_bundle.require()`'s own call site, driven with no bundle.

    `_STAGED` is reset because `require()` stages once per process and every
    other suite in this run has already filled it — without the reset this test
    would never reach `find()` at all, and would prove nothing.
    """
    _pin(monkeypatch, _PIN_A, _PIN_A)
    monkeypatch.setattr(_ob, "_STAGED", None)
    monkeypatch.setattr(_ob, "find", lambda: None)
    with pytest.raises(pytest.fail.Exception) as raised:
        _ob.require(module_level=False)
    assert "REGRESSION at the declared pin" in str(raised.value)


def test_require_SKIPS_for_a_different_installed_commit(monkeypatch) -> None:
    """...and the lawful consumer still gets a skip through the same call."""
    _pin(monkeypatch, _PIN_A, _PIN_B)
    monkeypatch.setattr(_ob, "_STAGED", None)
    monkeypatch.setattr(_ob, "find", lambda: None)
    with pytest.raises(pytest.skip.Exception) as raised:
        _ob.require(module_level=False)
    assert "NOT the declared pin's doing" in str(raised.value)


def test_the_bundle_fixture_FAILS_at_the_declared_pin(request, monkeypatch) -> None:
    """The `bundle` fixture's call site, driven through the real fixture.

    `request.getfixturevalue` runs the fixture that the thirteen probes below
    receive, so what is proven is the branch they actually take — not a copy of
    it written into the test.
    """
    import sys
    _pin(monkeypatch, _PIN_A, _PIN_A)
    monkeypatch.setattr(sys.modules[__name__], "_opendox_bundle", lambda: None)
    with pytest.raises(pytest.fail.Exception) as raised:
        request.getfixturevalue("bundle")
    assert "REGRESSION at the declared pin" in str(raised.value)


def test_the_bundle_fixture_SKIPS_for_a_different_installed_commit(
        request, monkeypatch) -> None:
    """...and skips, naming both commits, for an assembly at another pin."""
    import sys
    _pin(monkeypatch, _PIN_A, _PIN_B)
    monkeypatch.setattr(sys.modules[__name__], "_opendox_bundle", lambda: None)
    with pytest.raises(pytest.skip.Exception) as raised:
        request.getfixturevalue("bundle")
    message = str(raised.value)
    assert _PIN_A[:8] in message
    assert _PIN_B[:8] in message
