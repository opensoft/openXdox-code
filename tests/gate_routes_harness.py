"""The real-HTTP gate-route harness this leg's project suites ride: `_serving`
and `_post`, and nothing else.

A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C — the manifest declares what LEAVES openxFactory, never what a
destination assembles).

WHY IT EXISTS (plan 034 task T040, research R10). Three suites at this leg —
`test_create_project.py`, `test_edit_project.py` and
`test_register_edit_lane.py` — drive their wire half through
`from test_gate_routes import _post, _serving`. The module they name is
openxFactory's `tests/ideation-dashboard/test_gate_routes.py`, whose manifest
row is `not_moved` (`stays_openxfactory_adapter`): it never arrived here, so all
three failed collection on `No module named 'test_gate_routes'` (T005's class B).
This module is the helper of their own that T040 gives them in its place.

WHAT IT CARRIES, AND FROM WHERE. Exactly the names those three import, plus the
definitions those names reach: `_serving`, `_post`, and behind them
`_openx_root`, `_derived_entry`, `_fake_validator` and `_console_token`. Each
definition is copied from openxFactory at the carve tag `opendox-carve-0`
(`b075fd91dc8fced8e1373825ba80220c33536bae`), the tree those three suites were
carved from, and the changes listed below are the only ones.
openxFactory's own copy is not brought whole because its
module-level imports reach openxFactory-only modules (`human_seen`,
`find_openxfactory_validator`'s checkout walk) that no name used here needs.

WHAT CHANGED IN THE COPY, and each change is one the carve itself makes:

  * the carve's `import rewrites` edit class: `ideation_dashboard.serve` is
    `opendox.serve`, the module's own destination row;
  * the one `path constant`: the served web root was
    `REPO_ROOT / "scripts" / "ideation_dashboard" / "web"`, a pre-carve path this
    leg does not have. It is the PINNED openDox bundle now, through
    `opendox_bundle.web()`, which is this leg's one resolution of that bundle
    (§ 3.4 slice S8). It is read inside `_serving`, per call, rather than bound
    at module scope, because these suites' ENGINE half never serves, and
    `opendox_bundle`'s own rule is that a module whose subject is not the bundle
    takes a missing bundle per test (`web()`'s docstring);
  * `staging_fragment` comes from `staging_shapes`, the plainly named module the
    conftest re-exports it from, rather than through the ambient `conftest`
    name (`tests/conftest.py` records why a helper module imports it that way).
"""

from __future__ import annotations

import http.client
import json
import threading
from contextlib import contextmanager
from pathlib import Path

import yaml as yaml_mod

import opendox_bundle
from staging_shapes import staging_fragment

from opendox import serve as serve_mod


def _derived_entry(pid="pos-derived-x"):
    return {
        "id": pid, "title": "Derived", "claim": "c", "state": "latent",
        "origin": "ai-derived",
        "provenance": {"document": "d", "section": "s"},
        "derivation": {"worker_run": {
            "correlation_id": "DPOSS-1", "worker_profile": "derive-possibles",
            "prompt_contract_version": "derive-possibles-prompt-v1"},
            "disposition": "pending_review"},
        "claiming_clusters": ["cl-a"],
        "supporting_evidence": [{"document": "d", "section": "s",
                                 "passage_sha256": "0" * 64}],
    }


def _openx_root(tmp_path: Path) -> Path:
    root = tmp_path / "openx"
    (root / "ideation").mkdir(parents=True)
    # `topic-x` is worked to done, so the propose route's readiness gate
    # (add-staging-workbench) lets the commission through; `topic-blocked`
    # carries a standing open item, so the same gate refuses it. Both shapes
    # come from the shared conftest fixtures.
    for topic, text in (("topic-x", staging_fragment("Topic X", "topic-x")),
                        ("topic-blocked",
                         staging_fragment("Topic Blocked", "topic-blocked",
                                          resolved=False))):
        (root / "ideation" / "staging" / topic).mkdir(parents=True)
        (root / "ideation" / "staging" / topic / f"{topic}.md").write_text(
            text, encoding="utf-8")
    index = {"schema_version": 1, "kind": "ideation-cross-reference",
             "repository": "openxFactory",
             "generation": {"source_revision": "e" * 40,
                            "generator_version": "test"},
             "topic_entries": [{"id": "cl-a", "name": "A",
                                "members": [{"path": "p", "stage": "staged"}]}],
             "possibles_register": [_derived_entry()]}
    (root / "ideation" / "cross-reference.yaml").write_text(
        yaml_mod.safe_dump(index, sort_keys=False), encoding="utf-8")
    return root


def _fake_validator(tmp_path: Path, accept: bool = True) -> Path:
    script = tmp_path / "fake_index_validator.py"
    script.write_text(f"import sys\nsys.exit(0 if {accept!r} else 1)\n",
                      encoding="utf-8")
    return script


@contextmanager
def _serving(tmp_path, *, host="127.0.0.1", actor="brett", validator=True,
             monkeypatch=None, snapshot=None,
             manifest_validator=None, xref_validator=None):
    if monkeypatch is not None:  # hermetic .md projection
        renderer_root = tmp_path / "fake-openx" / "scripts"
        renderer_root.mkdir(parents=True, exist_ok=True)
        (renderer_root / "render-ideation-cross-reference.py").write_text(
            "def render_markdown(index):\n    return '# projection\\n'\n",
            encoding="utf-8")
        monkeypatch.setenv("OPENXFACTORY_ROOT", str(tmp_path / "fake-openx"))
    root = _openx_root(tmp_path)
    snap_path = tmp_path / "snapshot.json"
    snap_path.write_text(json.dumps(snapshot or {"generation": {}}), encoding="utf-8")
    httpd = serve_mod.build_server(
        opendox_bundle.web(), snap_path, root, host=host, actor=actor,
        gate_index_validator=_fake_validator(tmp_path, accept=validator),
        gate_manifest_validator=manifest_validator,
        gate_xref_validator=xref_validator)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    bind_host, port = httpd.server_address[:2]
    try:
        yield ("127.0.0.1" if bind_host in ("0.0.0.0", "") else bind_host,
               port, root)
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def _console_token(host, port):
    """The per-serve human-console token (FR-019's third clause; PR #49 review
    finding 2), read as the served page reads it — a same-origin
    `GET /capabilities`. Absent on a plane with no session capability, and the
    session verbs are the only ones that require it."""
    conn = http.client.HTTPConnection(host, port, timeout=10)
    conn.request("GET", "/capabilities")
    response = conn.getresponse()
    caps = json.loads(response.read().decode("utf-8"))
    conn.close()
    return caps.get("console_token")


def _post(host, port, path, body):
    payload = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json",
               "Content-Length": str(len(payload))}
    token = _console_token(host, port)
    if token:
        headers["X-XF-Console-Token"] = token
    conn = http.client.HTTPConnection(host, port, timeout=10)
    conn.request("POST", path, body=payload, headers=headers)
    response = conn.getresponse()
    data = json.loads(response.read().decode("utf-8"))
    conn.close()
    return response.status, data
