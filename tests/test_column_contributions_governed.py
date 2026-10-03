"""openXdox's governed columns are what openDox's column seams hold (plan 034
T086), proved where they can be registered.

The four are registered only where `gate_console` imports, and it imports
openxFactory's `doc_health` at module level (the holder's ruling on T086's Q1
(a)). So these cases run where `doc_health` imports: the composed environment
F5.2 runs in, with openxFactory's `scripts/` on the path. In a lone checkout
this module stops at its first import, on `doc_health` alone, and the declared
exclusion lists it for that reason (Q9 (a); T044's precedent). The mechanism
the registration shares with every seam (idempotent, all or none, put-back,
the group rule) is proved over stand-ins in `tests/test_column_contributions.py`,
which runs lone.

This leg's root `conftest.py` registers the fixture profile at import, and
with it the four columns. A case that empties a seam restores it.

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import http.client
import json
import threading
from contextlib import contextmanager

import pytest

from openxdox import gate_console  # reaches doc_health: the declared reason

from conftest import BASE_REPO, PINNED_REVISION, FakeGit

from opendox import column_seams, default_columns
from opendox import serve as serve_mod
from opendox.doxbench_scope_types import ScopeKey
from opendox.projection_seams import SeamAlreadyRegistered
from openxdox import column_contributions as cc
from openxdox import doxbench_scope, gate_routes, kickoff
from openxdox import register as register_mod
from openxdox.generator import generate_snapshot
from openxdox.serve_gate import GateRoutesExtension
from openxdox.serve_projection import SNAPSHOT_INDEX_ROUTE, ProjectionRoutesExtension

from opendox_bundle import OPENDOX_WEB  # noqa: E402  (skips where the pin carries no bundle)

SEAM_NAMES = ("gate", "scope", "kickoff", "register")


def _seam(name: str):
    return getattr(column_seams, name)


@pytest.fixture
def restored_column_seams():
    saved = {name: (_seam(name)._registered, _seam(name)._is_default,
                    _seam(name)._default_read) for name in SEAM_NAMES}
    try:
        yield
    finally:
        for name, (registered, is_default, default_read) in saved.items():
            seam = _seam(name)
            with seam._lock:
                seam._registered = registered
                seam._is_default = is_default
                seam._default_read = default_read


# --------------------------------------------------------------------------
# the registered ones
# --------------------------------------------------------------------------

def test_each_column_seam_holds_openxdoxs_governed_column() -> None:
    assert cc.SKIPPED is None
    assert cc.is_registered()
    assert column_seams.gate.current() is cc.GATE
    assert column_seams.scope.current() is doxbench_scope
    assert column_seams.kickoff.current() is cc.KICKOFF
    assert column_seams.register.current() is register_mod
    for name in SEAM_NAMES:
        assert _seam(name).holds_a_hosts(), name


def test_a_host_gate_is_registered_so_governed_records_are_writable() -> None:
    """With openXdox's gate registered, openDox offers model approval and the
    intake again (Brett, `5961364221` item 1: refused by name only where no
    host's gate is registered)."""
    assert column_seams.gate_records_writable()


def test_the_gate_is_gate_consoles_own_names_read_when_used(monkeypatch) -> None:
    gate = column_seams.gate.current()
    for name in column_seams.GATE_CALLABLES + column_seams.GATE_VALUES:
        if name == "first_edit_gate_factory":
            assert gate.first_edit_gate_factory is gate_routes.first_edit_gate_factory
        else:
            assert getattr(gate, name) is getattr(gate_console, name), name
    # `except <gate>.GateRefused` catches what the governed engine raises
    assert gate.GateRefused is gate_console.GateRefused
    assert gate.Provenance is gate_console.Provenance

    def stamped():
        return "2026-10-03T00:00:00Z"

    monkeypatch.setattr(gate_console, "_stamp", stamped)
    assert column_seams.gate.proxy._stamp is stamped


def test_kickoff_is_kickoffs_own_names_read_when_used(monkeypatch) -> None:
    for name in column_seams.KICKOFF_CALLABLES:
        assert getattr(column_seams.kickoff.current(), name) is getattr(kickoff, name), name

    def none(root):
        return None

    monkeypatch.setattr(kickoff, "discover_project_register", none)
    assert column_seams.kickoff.proxy.discover_project_register is none


def test_the_scope_seam_answers_the_governed_rule_not_the_default(tmp_path) -> None:
    """The scope a turn is held to is the registered one. Under openXdox's,
    a group's members are read-only; under openDox's default (RULED
    `5961651355`) they would be editable. The seam holds one registration."""
    paths = ["ideation/brainstorm/a.md", "ideation/brainstorm/b.md"]
    for rel in paths:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("# a document\n", encoding="utf-8")
    # A group's edges name its documents by ID, which the snapshot contract
    # does not promise equals the path (openDox-code#77's fix round 3).
    ids = [f"doc-{rel.rsplit('/', 1)[1][:-3]}" for rel in paths]
    snapshot = {
        "documents": [{"id": doc_id, "path": rel} for doc_id, rel in zip(ids, paths)],
        "clusters": [{"id": "c1", "document_edges": [{"document": doc_id} for doc_id in ids]}],
    }
    key = ScopeKey(repository="fixture-repo", ref="main", tile_kind="cluster", tile_id="c1")
    registered = column_seams.scope.proxy.resolve_scope(snapshot, key, source_root=tmp_path)
    assert registered.editable_paths == ()
    assert default_columns.resolve_scope(
        snapshot, key, source_root=tmp_path).editable_paths == tuple(paths)


def test_a_read_default_refuses_the_governed_columns_and_leaves_every_default(
        restored_column_seams) -> None:
    """The governed registration over a default some consumer has read is
    refused, with every seam it wrote back on openDox's default."""
    for name in SEAM_NAMES:
        _seam(name).unregister()
    column_seams.register_defaults()
    column_seams.scope.current()

    with pytest.raises(SeamAlreadyRegistered):
        cc.register()

    assert column_seams.gate.current() is default_columns.GATE
    assert column_seams.scope.current() is default_columns.SCOPE
    assert column_seams.kickoff.current() is default_columns.KICKOFF
    assert column_seams.register.current() is default_columns.REGISTER
    assert not column_seams.gate_records_writable()


def test_registering_over_unread_defaults_takes_all_four(restored_column_seams) -> None:
    for name in SEAM_NAMES:
        _seam(name).unregister()
    column_seams.register_defaults()
    assert cc.register() == SEAM_NAMES
    assert cc.is_registered()
    assert column_seams.gate_records_writable()


# --------------------------------------------------------------------------
# both columns, served (batch L's composed half)
# --------------------------------------------------------------------------

@contextmanager
def _serving(tmp_path, *, route_extensions):
    snap_path = tmp_path / "snapshot.json"
    snap_path.write_text(json.dumps(generate_snapshot(
        BASE_REPO, "fixture-repo", source_revision=PINNED_REVISION, git=FakeGit())),
        encoding="utf-8")
    httpd = serve_mod.build_server(OPENDOX_WEB, snap_path, BASE_REPO,
                                   head=PINNED_REVISION, actor="tester",
                                   route_extensions=route_extensions)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    try:
        yield host, port
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def _request(host, port, method, path, body=None):
    conn = http.client.HTTPConnection(host, port, timeout=5)
    payload = None if body is None else json.dumps(body)
    conn.request(method, path, body=payload,
                 headers={"Content-Type": "application/json"} if payload else {})
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status, json.loads(data)


def test_a_server_collecting_both_columns_serves_them_through_the_facet(tmp_path) -> None:
    with _serving(tmp_path, route_extensions=(
            GateRoutesExtension(), ProjectionRoutesExtension())) as (host, port):
        status, index = _request(host, port, "GET", SNAPSHOT_INDEX_ROUTE)
        _caps_status, caps = _request(host, port, "GET", "/capabilities")
        gate_status, gate = _request(host, port, "POST",
                                     "/actions/gate/create-document", body={})
        unknown_status, unknown = _request(host, port, "POST",
                                           "/actions/no-such-column/x", body={})

    assert status == 200 and index["kind"] == "ideation-dashboard-snapshot-index"
    # the capability claims the gate where its route is bound (batch L)
    assert caps["actions"]["gate"] is True
    # the gate door answered (a session-bearing verb with no console token),
    # not the server's own unknown-route refusal
    assert (gate_status, gate["error"]) == (403, "agent_invocation")
    assert (unknown_status, unknown["error"]) == (404, "unknown_action")


def test_a_server_collecting_neither_column_claims_no_gate(tmp_path) -> None:
    with _serving(tmp_path, route_extensions=()) as (host, port):
        _caps_status, caps = _request(host, port, "GET", "/capabilities")
        gate_status, gate = _request(host, port, "POST",
                                     "/actions/gate/create-document", body={})
    assert caps["actions"]["gate"] is False
    assert (gate_status, gate["error"]) == (404, "unknown_action")
