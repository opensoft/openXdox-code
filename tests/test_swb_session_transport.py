"""`swb-session.js`'s write transport, EXECUTED: which model's header and repair
policy a session request is sent through.

WHY THIS FILE EXISTS. `submitSession` is the ONE request site of the session
column (see the comment above it in `views/swb-session.js`). It takes the two
model functions it needs, `consoleHeaders` and `withConsoleRepair`, from one of
two places: the model namespace its caller validated (`bound`, which is what
`firstEditTransport` passes, because the transport it returns outlives the call
that built it), or, with none, the module-level seam that reads the model the
current mount installed.

`tests/test_session_confinement.py` pins how those two calls are SPELLED, and
only that: it reads the file as text. A pass there says the two names appear at
their call sites, not that the right model answers them. Copilot's review of the
change that restored those spellings (openXdox-code#42) saw the gap: always
selecting the module-level pair, or wiring either wrapper to the wrong function,
left every committed test green. These two probes close it. They run the shipped
module under node, out of a COMPOSED bundle, and assert on the request that
reaches the injected fetcher:

  * BOUND: two transports are built from two models that differ in the very two
    functions under test, then both are called. Each request must carry its own
    model's header and go through its own model's repair policy. A `submitSession`
    that always read the module-level install would send both through the model
    built LAST.
  * UNBOUND: a mounted session form is submitted. The request must carry the
    header the mounted model's `consoleHeaders` builds from the page's `caps`, and
    go through that model's `withConsoleRepair`. A module-level pair that is wired
    to the wrong function sends no header, or throws before it sends.

WHAT THE HARNESS DOES NOT MEASURE. The outcome panel the column writes AFTER the
request needs the shell's `page-overlay` host, which a stub DOM does not provide,
so the form's click handler rejects after the fetcher has been called. The probe
records that rejection and asserts on the REQUEST only, which is what these
tests are about.

A CREATED file, with no manifest row (RULED OQ-C), outside the declared
exclusion: it needs openDox's `web/` bundle and node, as
`tests/test_gate_loop_probes.py` does, and no openxFactory module.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

import opendox_bundle

NODE = shutil.which("node")

_DOM_STUB = r"""
class Node {
  constructor(tag) {
    this.tag = tag; this.children = []; this.attrs = {}; this.listeners = {};
    this.className = ""; this._text = ""; this.type = ""; this.title = "";
    this.value = ""; this.checked = false; this.disabled = false;
    this.hidden = false;
  }
  get textContent() { return this._text; }
  set textContent(v) { this._text = String(v); this.children = []; }
  set innerHTML(v) {
    if (v !== "") throw new Error("innerHTML assigned " + v);
    this.children = []; this._text = "";
  }
  appendChild(c) { this.children.push(c); return c; }
  append(...kids) { for (const k of kids) this.appendChild(k); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  addEventListener(t, fn) { (this.listeners[t] = this.listeners[t] || []).push(fn); }
  focus() {}
  click() { for (const fn of this.listeners.click || []) fn({}); }
}
globalThis.document = { createElement: (tag) => new Node(tag) };
function flatten(node, out = []) {
  out.push(node);
  for (const c of node.children) flatten(c, out);
  return out;
}
globalThis.buttons = (node) => flatten(node).filter((n) => n.tag === "button");
globalThis.settle = () => new Promise((r) => setTimeout(r, 0));
// The outcome panel needs a shell host this stub does not have (see the module
// docstring): the click handler rejects AFTER the request. Recorded, not fatal.
globalThis.rejections = [];
process.on("unhandledRejection", (e) => { globalThis.rejections.push(String(e)); });
"""


@pytest.fixture
def views(tmp_path) -> Path:
    """The COMPOSED bundle's `views/`, copied into `tmp_path` and marked as an
    ES-module tree (a copy has no ancestor `package.json`, so node would read the
    `export` syntax as CommonJS)."""
    target = tmp_path / "web"
    shutil.copytree(opendox_bundle.composed(), target)
    (target / "package.json").write_text('{"type": "module"}\n', encoding="utf-8")
    return target / "views"


def _run_node(body: str, views: Path) -> dict:
    """Run an ES-module harness against the composed bundle and return the ONE
    JSON object it prints last."""
    source = (_DOM_STUB
              + f"\nconst VIEWS = {json.dumps(views.resolve().as_uri() + '/')};\n"
              + body)
    script = views.parent / "harness.mjs"
    script.write_text(source, encoding="utf-8")
    proc = subprocess.run([NODE, str(script)], capture_output=True, text=True,
                          timeout=120)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_each_built_transport_sends_through_its_own_models_header_and_repair(
        views) -> None:
    """BOUND. Two transports, two models that differ in exactly the two functions
    `submitSession` takes from the namespace it was handed. BOTH are built before
    EITHER is called, which is the interleaving a module-level read cannot survive:
    the second build re-points the module-level install."""
    result = _run_node("""
const column = await import(VIEWS + "swb-session.js");
const model = await import(VIEWS + "staging-workbench-model.js");
const repairs = [];
const make = (tag) => ({
  ...model,
  consoleHeaders: (caps) => ({ "x-probe-model": tag,
                               "x-probe-token": String(caps.console_token) }),
  withConsoleRepair: async (send, repair) => { repairs.push(tag); return send(); },
});
const sent = [];
const fetcher = async (route, opts) => {
  sent.push({ route, method: opts.method, headers: opts.headers });
  return { ok: true, status: 200, json: async () => ({ ok: true }) };
};
const req = { key: { repository: "openxFactory", tile_kind: "staged",
                     tile_id: "t-1" },
              document: "d.md", content: "x" };
const first = column.firstEditTransport({
  fetcher, caps: { console_token: "A" }, model: make("first") });
const second = column.firstEditTransport({
  fetcher, caps: { console_token: "B" }, model: make("second") });
await first(req);
await second(req);
console.log(JSON.stringify({ sent, repairs }));
""", views)
    assert [s["method"] for s in result["sent"]] == ["POST", "POST"]
    assert [s["headers"] for s in result["sent"]] == [
        {"x-probe-model": "first", "x-probe-token": "A"},
        {"x-probe-model": "second", "x-probe-token": "B"},
    ], "each request must carry the header ITS OWN model built, from its own caps"
    assert result["repairs"] == ["first", "second"], (
        "each request must go through ITS OWN model's repair policy")


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_js_a_mounted_form_sends_through_the_mounted_models_header_and_repair(
        views) -> None:
    """UNBOUND. A session form is mounted with a model whose `consoleHeaders` and
    `withConsoleRepair` are markers, an affordance is opened and its submit
    pressed. With no `bound` namespace, `submitSession` reaches the model through
    the module-level pair, and the request must show both markers."""
    result = _run_node("""
const column = await import(VIEWS + "swb-session.js");
const model = await import(VIEWS + "staging-workbench-model.js");
const repairs = [];
const mounted = {
  ...model,
  consoleHeaders: (caps) => ({ "x-probe-model": "mounted",
                               "x-probe-token": String(caps.console_token) }),
  withConsoleRepair: async (send, repair) => { repairs.push("mounted"); return send(); },
};
const sent = [];
const fetcher = async (route, opts) => {
  sent.push({ route, method: opts.method, headers: opts.headers });
  return { ok: true, status: 200, json: async () => ({ ok: true }) };
};
const host = document.createElement("div");
const caps = { actions: { gate: true, session: true }, actor: "brett",
               console_token: "tok1" };
column.mountSessionAffordances(host, null, {
  model: mounted, caps, fetcher, actor: "brett",
  session: { scope: { kind: "staged", id: "t-1" },
             posture: { branch: "session/t-1", repository: "openxFactory" } },
});
const openers = buttons(host);
openers[0].click();
await settle();
const submits = buttons(host).filter(
  (b) => !openers.includes(b) && b.textContent !== "cancel");
for (const b of submits) b.click();
await settle(); await settle();
console.log(JSON.stringify({ openers: openers.length, submits: submits.length,
                             sent, repairs, rejections: globalThis.rejections }));
""", views)
    assert result["openers"] >= 1 and result["submits"] == 1, result
    assert [s["route"] for s in result["sent"]] == ["/actions/gate/edit-document"], result
    assert result["sent"][0]["method"] == "POST"
    assert result["sent"][0]["headers"] == {
        "x-probe-model": "mounted", "x-probe-token": "tok1"}, (
        "the request must carry the header the mounted model's consoleHeaders built")
    assert result["repairs"] == ["mounted"], (
        "the request must go through the mounted model's repair policy")
