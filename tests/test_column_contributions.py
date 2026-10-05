"""openXdox's governed columns at openDox's column seams, and the two route
columns through openDox's handler-contribution facet (plan 034 T086).

T084 (openDox-code#77) declares four column seams in `opendox.column_seams`
(gate, scope, kickoff, register), each with a neutral default in
`opendox.default_columns`, and retires the two `Late*` mixin bases. T086 is
openXdox's half: `openxdox.column_contributions` registers the governed four,
and `serve_gate.GateRoutesExtension` and
`serve_projection.ProjectionRoutesExtension` declare the mixins their bindings'
methods live on.

WHERE EACH CASE RUNS. These cases run in a lone checkout, and so in F9.1. The
registration itself is not one of them: openDox reads every name of a
registration when it is made, and the governed gate's names live in
`gate_console`, which imports openxFactory's `doc_health` (the holder's ruling
on T086's Q1 (a)). So the registration's MECHANISM is proved here over stand-in
contributions carrying the seams' names, and the governed objects themselves
are proved where `doc_health` imports, in
`tests/test_column_contributions_governed.py`, which the declared exclusion
lists under `doc_health` (Q9 (a)).

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import copy
import types
from pathlib import Path

import pytest

import route_extension
from opendox import column_seams, default_columns, projection_seams
from opendox import serve as serve_mod
from opendox.doxbench_scope_types import ScopeKey
from opendox.projection_seams import SeamAlreadyRegistered
from openxdox import column_contributions as cc
from openxdox import domain_profile, doxbench_scope, projection_contributions
from openxdox import register as register_mod
from openxdox.serve_gate import GateRoutes, GateRoutesExtension
from openxdox.serve_projection import ProjectionRoutes, ProjectionRoutesExtension

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "openxfactory-engineering-profile.yaml"

SEAM_NAMES = ("gate", "scope", "kickoff", "register")


def _seam(name: str):
    return getattr(column_seams, name)


# --------------------------------------------------------------------------
# isolation, and stand-in contributions carrying each seam's names
# --------------------------------------------------------------------------

@pytest.fixture
def isolated_column_seams():
    """Run one case with the four column seams empty, then put back exactly
    what each held, the default's read flag included."""
    saved = {name: (_seam(name)._registered, _seam(name)._is_default,
                    _seam(name)._default_read) for name in SEAM_NAMES}
    skipped = cc.SKIPPED
    for name in SEAM_NAMES:
        _seam(name).unregister()
    try:
        yield
    finally:
        for name, (registered, is_default, default_read) in saved.items():
            seam = _seam(name)
            with seam._lock:
                seam._registered = registered
                seam._is_default = is_default
                seam._default_read = default_read
        cc.SKIPPED = skipped


def _callables(names) -> dict:
    return {name: (lambda *args, **kwargs: None) for name in names}


def _stand_ins() -> dict:
    """One object per seam, carrying exactly what that seam probes for."""
    gate = types.SimpleNamespace(**_callables(column_seams.GATE_CALLABLES))
    gate.GateRefused = type("GateRefused", (Exception,), {})
    for value in column_seams.GATE_VALUES:
        setattr(gate, value, value.lower())

    class Adapter:
        @classmethod
        def discover(cls, root):
            return cls()

    return {
        "gate": gate,
        "scope": types.SimpleNamespace(**_callables(column_seams.SCOPE_CALLABLES)),
        "kickoff": types.SimpleNamespace(**_callables(column_seams.KICKOFF_CALLABLES)),
        "register": types.SimpleNamespace(CrossReferenceIndexAdapter=Adapter),
    }


@pytest.fixture
def stand_ins(isolated_column_seams, monkeypatch):
    """`column_contributions` over stand-in contributions, as if
    `gate_console` imported."""
    objects = _stand_ins()
    monkeypatch.setattr(cc, "_contributions", lambda: tuple(
        (name, _seam(name), objects[name]) for name in SEAM_NAMES))
    monkeypatch.setattr(cc, "_why_not_importable", lambda: None)
    return objects


# --------------------------------------------------------------------------
# the seams this module writes, and the names it reads off them
# --------------------------------------------------------------------------

def test_the_four_seams_are_openDoxs_and_carry_the_names_this_module_reads() -> None:
    """`_holds` and `_unread_default` read a seam's registration where the seam
    keeps it, because `current()` would close a default's window. Those names
    are openDox's, so a pin move that renames them fails here."""
    for name in SEAM_NAMES:
        seam = _seam(name)
        assert isinstance(seam, projection_seams._Seam)
        assert seam.name == name
        for attr in ("_registered", "_is_default", "_default_read", "_lock"):
            assert hasattr(seam, attr), f"{name} has no {attr}"
        for call in ("register", "register_default", "unregister",
                     "holds_a_hosts", "current"):
            assert callable(getattr(seam, call))
    # The gate's one name that is not `gate_console`'s, which GATE redirects.
    assert "first_edit_gate_factory" in column_seams.GATE_CALLABLES
    assert "CrossReferenceIndexAdapter" in column_seams.REGISTER_CALLABLES


def test_the_contributions_are_the_governed_modules_and_their_names() -> None:
    assert cc.SCOPE is doxbench_scope
    assert cc.REGISTER is register_mod
    assert tuple(name for name, *_ in cc._contributions()) == SEAM_NAMES
    assert [seam for _name, seam, _c in cc._contributions()] == [
        _seam(name) for name in SEAM_NAMES]
    for name in column_seams.SCOPE_CALLABLES:
        assert callable(getattr(cc.SCOPE, name))
    # the register seam's shape: openDox calls `.discover(<root>)`
    assert callable(cc.REGISTER.CrossReferenceIndexAdapter.discover)


# --------------------------------------------------------------------------
# the registration: idempotent, all or none, with put-back
# --------------------------------------------------------------------------

def test_register_writes_all_four_and_again_is_a_no_op(stand_ins) -> None:
    assert cc.register() == SEAM_NAMES
    assert cc.SKIPPED is None
    assert cc.is_registered()
    for name in SEAM_NAMES:
        assert _seam(name)._registered is stand_ins[name]
        assert _seam(name).holds_a_hosts()
    assert column_seams.gate_records_writable()

    assert cc.register() == SEAM_NAMES
    for name in SEAM_NAMES:
        assert _seam(name)._registered is stand_ins[name]


def test_an_unread_default_is_replaced(stand_ins) -> None:
    column_seams.register_defaults()
    assert not column_seams.gate_records_writable()
    cc.register()
    for name in SEAM_NAMES:
        assert _seam(name)._registered is stand_ins[name]
        assert not _seam(name)._is_default


def test_a_refusal_gives_every_seam_written_back_its_unread_default(stand_ins) -> None:
    """A host's registration at the third seam refuses the call. The two seams
    written before it hold openDox's unread default again, AS a default, so a
    later host registration can still replace it."""
    column_seams.register_defaults()
    foreign = _stand_ins()["kickoff"]
    _seam("kickoff").unregister()
    _seam("kickoff").register(foreign)

    with pytest.raises(SeamAlreadyRegistered):
        cc.register()

    assert _seam("gate")._registered is default_columns.GATE
    assert _seam("scope")._registered is default_columns.SCOPE
    for name in ("gate", "scope"):
        assert _seam(name)._is_default and not _seam(name)._default_read
    assert _seam("kickoff")._registered is foreign
    assert _seam("register")._registered is default_columns.REGISTER
    assert not cc.is_registered()


def test_a_read_default_refuses_and_leaves_every_seam_on_the_default(stand_ins) -> None:
    """Once a consumer has read the scope's default, a host registration there
    is refused; the gate, written first, goes back to the default. So the
    process runs on openDox's four defaults, never on a mix."""
    column_seams.register_defaults()
    column_seams.scope.current()

    with pytest.raises(SeamAlreadyRegistered):
        cc.register()

    for name, default in (("gate", default_columns.GATE),
                          ("scope", default_columns.SCOPE),
                          ("kickoff", default_columns.KICKOFF),
                          ("register", default_columns.REGISTER)):
        assert _seam(name)._registered is default, name
        assert _seam(name)._is_default, name
    assert not column_seams.gate_records_writable()


def test_unregister_empties_only_what_this_module_holds(stand_ins) -> None:
    cc.register()
    foreign = _stand_ins()["register"]
    _seam("register").unregister()
    _seam("register").register(foreign)

    cc.unregister()

    for name in ("gate", "scope", "kickoff"):
        assert _seam(name)._registered is None, name
    assert _seam("register")._registered is foreign


# --------------------------------------------------------------------------
# the group rule (the holder's ruling on T086's Q1 (a))
# --------------------------------------------------------------------------

def _gate_console_missing(missing: str, error: type = ModuleNotFoundError):
    def governed(name: str):
        if name == "gate_console":
            raise error(f"No module named {missing!r}", name=missing)
        return cc.importlib.import_module(f"openxdox.{name}")
    return governed


@pytest.mark.parametrize("missing", ["doc_health", "doc_health.lines"])
def test_without_doc_health_nothing_is_written_and_the_reason_is_named(
        isolated_column_seams, monkeypatch, missing) -> None:
    monkeypatch.setattr(cc, "_governed", _gate_console_missing(missing))
    assert cc.register() == ()
    assert "doc_health" in cc.SKIPPED and missing in cc.SKIPPED
    assert "plan 034 T008" in cc.SKIPPED and "R1Q6 (d)" in cc.SKIPPED
    for name in SEAM_NAMES:
        assert _seam(name)._registered is None, name


def test_any_other_missing_module_is_raised(isolated_column_seams, monkeypatch) -> None:
    monkeypatch.setattr(cc, "_governed", _gate_console_missing("yaml"))
    with pytest.raises(ModuleNotFoundError) as raised:
        cc.register()
    assert raised.value.name == "yaml"
    for name in SEAM_NAMES:
        assert _seam(name)._registered is None, name


def test_an_import_error_that_is_no_missing_module_is_raised(
        isolated_column_seams, monkeypatch) -> None:
    monkeypatch.setattr(cc, "_governed", _gate_console_missing("doc_health", ImportError))
    with pytest.raises(ImportError):
        cc.register()


# --------------------------------------------------------------------------
# the forwarding contributions
# --------------------------------------------------------------------------

def test_a_forwarding_contribution_reads_its_module_on_each_use(monkeypatch) -> None:
    forwarding = cc._Forwarding("label", "register")
    assert forwarding.CrossReferenceIndexAdapter is register_mod.CrossReferenceIndexAdapter

    class Replaced:
        pass

    monkeypatch.setattr(register_mod, "CrossReferenceIndexAdapter", Replaced)
    assert forwarding.CrossReferenceIndexAdapter is Replaced

    redirected = cc._Forwarding("label", "register",
                                {"resolve_scope": "doxbench_scope"})
    assert redirected.resolve_scope is doxbench_scope.resolve_scope


def test_the_gate_and_kickoff_name_their_modules_and_import_nothing_until_used() -> None:
    assert (cc.GATE._module, cc.GATE._redirect) == (
        "gate_console", {"first_edit_gate_factory": "gate_routes"})
    assert (cc.KICKOFF._module, cc.KICKOFF._redirect) == ("kickoff", {})
    # A dunder is never forwarded, so copying or inspecting the object reaches
    # no governed module (and so no doc_health).
    assert "read when used" in repr(cc.GATE)
    with pytest.raises(AttributeError):
        cc.GATE.__wrapped__
    assert copy.copy(cc.KICKOFF)._module == "kickoff"


# --------------------------------------------------------------------------
# who registers: domain_profile.register(), never load()
# --------------------------------------------------------------------------

def test_registering_the_profile_registers_the_columns_after_the_projection(
        monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(projection_contributions, "register",
                        lambda: calls.append("projection"))
    monkeypatch.setattr(cc, "register", lambda: calls.append("columns"))
    monkeypatch.setattr(domain_profile, "_registered", None)

    profile = domain_profile.load(PROFILE_FIXTURE)
    assert calls == []
    domain_profile.register(profile)
    assert calls == ["projection", "columns"]


def test_a_refused_column_registration_registers_no_profile(monkeypatch) -> None:
    def refuse():
        raise SeamAlreadyRegistered("a consumer read the default first")

    monkeypatch.setattr(projection_contributions, "register", lambda: ())
    monkeypatch.setattr(cc, "register", refuse)
    monkeypatch.setattr(domain_profile, "_registered", None)
    with pytest.raises(SeamAlreadyRegistered):
        domain_profile.register(domain_profile.load(PROFILE_FIXTURE))
    assert not domain_profile.is_registered()


# --------------------------------------------------------------------------
# the governed scope is stricter than openDox's default (Brett, 5961651355)
# --------------------------------------------------------------------------

def test_a_clusters_members_are_editable_under_the_default_and_not_the_governed_scope(
        tmp_path) -> None:
    """Why the scope seam's registration matters. openDox's default marks a
    tile's own documents editable (RULED `5961651355`), so a group's members
    are. openXdox's governed authority edits only a staged tile's folder and
    what a session created, so the same members are read-only. The seam
    holds one registration, so the two never both apply."""
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

    governed = doxbench_scope.resolve_scope(snapshot, key, source_root=tmp_path)
    neutral = default_columns.resolve_scope(snapshot, key, source_root=tmp_path)

    assert [row.path for section in governed.sections for row in section.documents] == paths
    assert governed.editable_paths == ()
    assert neutral.editable_paths == tuple(paths)


# --------------------------------------------------------------------------
# the handler-contribution facet (R1Q1 (a); Q2 (a), Q3 (a))
# --------------------------------------------------------------------------

def test_each_route_extension_declares_its_one_mixin_as_a_plain_tuple() -> None:
    assert route_extension.HANDLER_FACET == "HANDLER_CONTRIBUTIONS"
    assert type(GateRoutesExtension.HANDLER_CONTRIBUTIONS) is tuple
    assert GateRoutesExtension.HANDLER_CONTRIBUTIONS == (GateRoutes,)
    assert type(ProjectionRoutesExtension.HANDLER_CONTRIBUTIONS) is tuple
    assert ProjectionRoutesExtension.HANDLER_CONTRIBUTIONS == (ProjectionRoutes,)


def test_the_columns_hold_only_the_methods_their_bindings_name() -> None:
    def own(cls):
        return {name for name in vars(cls)
                if not (name.startswith("__") and name.endswith("__"))}

    assert own(ProjectionRoutes) == {"_serve_index"}
    assert own(GateRoutes) == {"_handle_gate_action", "_log_gate_failure"}
    for extension in (GateRoutesExtension(), ProjectionRoutesExtension()):
        (mixin,) = extension.HANDLER_CONTRIBUTIONS
        for binding in extension.routes():
            assert binding.handler in vars(mixin), binding


def test_the_facet_composes_both_columns_after_the_core() -> None:
    base = serve_mod.DashboardHandler
    for name in ("_serve_index", "_handle_gate_action", "_log_gate_failure"):
        assert not hasattr(base, name), f"the core answers {name} itself"
    extensions = (GateRoutesExtension(), ProjectionRoutesExtension())
    contributions = route_extension.collect_handler_contributions(extensions, base=base)
    assert contributions == (GateRoutes, ProjectionRoutes)

    bound = route_extension.compose_handler("Bound", base, contributions, {})
    assert bound.__mro__[1] is base
    assert bound._serve_index is ProjectionRoutes._serve_index
    assert bound._handle_gate_action is GateRoutes._handle_gate_action
    assert bound._log_gate_failure is GateRoutes._log_gate_failure
    for binding in route_extension.collect_bindings(extensions):
        assert callable(getattr(bound, binding.handler)), binding


def test_a_column_that_shadows_the_core_is_refused() -> None:
    """Why `ProjectionRoutes` holds `_serve_index` alone: its four other
    methods are the core's own since T055, and the facet refuses a mixin that
    shadows a core name."""
    restored = type("ProjectionRoutes", (), {
        "_serve_index": ProjectionRoutes._serve_index,
        "_serve_snapshot": lambda self, head_only: None,
    })
    extension = types.SimpleNamespace(HANDLER_CONTRIBUTIONS=(restored,),
                                      routes=lambda: ())
    with pytest.raises(route_extension.RouteBindingError) as refused:
        route_extension.collect_handler_contributions(
            (extension,), base=serve_mod.DashboardHandler)
    assert "_serve_snapshot" in str(refused.value)
