"""The suites that read the console token run on a host's plane (plan 034 T086,
step (b); openDox-code's T104, RULED openxFactory#656 comment 5963851934), and
the governed suites that drive openXdox's gate verbs run under the governed
host (plan 038 T020, U-1; R2Q8 (a)).

`tests/conftest.py`'s `_a_hosts_plane_for_the_token_reading_suites` registers a
stand-in host for the length of each test of the modules `HOST_PLANE_SUITES`
names, because from T104 openDox publishes the console token on
`/capabilities` only on a host's plane. Its
`_the_governed_host_for_the_governed_suites` registers the governed host, the
same way, for the modules `GOVERNED_HOST_SUITES` names. These cases hold both
lists and both hosts to their reasons, and they run in a lone checkout, so in
F9.1. None of them needs openxFactory: its host is stood in where a case needs
one.

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import re
import sys
import types
from pathlib import Path

import pytest

import conftest as tests_conftest
from opendox import default_profile
from opendox import domain_profile as registry

TESTS = Path(__file__).resolve().parent

#: A test module reads the token where it names `console_token` as a key, as a
#: capability document is read, or where it imports one of the two harnesses
#: that read it for their callers.
_TOKEN_KEY = re.compile(r"""["']console_token["']""")
_HARNESS_IMPORT = re.compile(
    r"^\s*(?:from|import)\s+(?:doxbench_routes_harness|gate_routes_harness)\b",
    re.M)


def _reads_the_token(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return bool(_TOKEN_KEY.search(text) or _HARNESS_IMPORT.search(text))


def test_the_list_is_every_suite_that_reads_the_token() -> None:
    scanned = {path.name for path in sorted(TESTS.glob("test_*.py"))
               if path.name != Path(__file__).name and _reads_the_token(path)}
    listed = set(tests_conftest.HOST_PLANE_SUITES)
    assert scanned == listed, (
        f"read the token but are not listed: {sorted(scanned - listed)}; "
        f"listed but read no token: {sorted(listed - scanned)}. A suite that "
        "reads the console token from /capabilities needs a host's plane from "
        "T104, so it joins tests/conftest.py's HOST_PLANE_SUITES")
    for harness in ("doxbench_routes_harness.py", "gate_routes_harness.py"):
        assert _TOKEN_KEY.search((TESTS / harness).read_text(encoding="utf-8")), (
            f"{harness} no longer reads the token, so the harness rule above "
            "lists suites for a reason that has gone")


def test_the_stand_in_host_contributes_nothing_the_default_does_not() -> None:
    """The plane changes owner, not routes: openDox's default contributes no
    route, and neither does the stand-in, so every server these suites build
    serves the same table. The stand-in carries no subcommand either, so no
    case in these suites gains a verb."""
    host = tests_conftest.StandInHost()
    assert tuple(default_profile.ROUTE_EXTENSIONS) == ()
    assert host.ROUTE_EXTENSIONS == () and host.SUBCOMMAND_EXTENSIONS == ()
    assert host is not default_profile


def test_on_the_stand_in_hosts_plane_the_token_stays_on_capabilities() -> None:
    """Where the pinned openDox delivers the token by plane (T104), the
    stand-in host's plane keeps it on `/capabilities` and the default's moves
    it to the opened URL. Where it does not, the serve publishes the token on
    `/capabilities` whatever is registered, so the fixture changes no token
    there."""
    if importlib.util.find_spec("opendox.console_access") is not None:
        from opendox import console_access

        assert (console_access.delivery_for(tests_conftest.StandInHost())
                == console_access.DELIVERY_CAPABILITIES)
        assert (console_access.delivery_for(default_profile)
                == console_access.DELIVERY_OPENED_URL)
    else:
        from opendox import serve as serve_mod

        source = inspect.getsource(serve_mod.build_server)
        assert "capabilities[CONSOLE_TOKEN_FIELD] = console_token" in source
        assert "delivery_for" not in source


# ---------------------------------------------------------------------------
# THE GOVERNED HOST (plan 038 T020, U-1).
# ---------------------------------------------------------------------------

SOURCE = TESTS.parent / "src"

#: A `gate` verb, as a test module spells it: the string `gate` and, after the
#: comma, the verb, the way an argument vector names a subcommand.
_GATE_VERB = re.compile(r"""["']gate["']\s*,\s*["']([a-z][a-z-]*)["']""")


def _gate_verbs() -> frozenset[str]:
    """The verbs openXdox's `gate` command declares: every name
    `src/openxdox/cli_gate.py` hands to `add_parser`, less `gate` itself. Read
    from the source, so a lone checkout can read it without `doc_health`."""
    tree = ast.parse((SOURCE / "openxdox" / "cli_gate.py").read_text(encoding="utf-8"))
    names = {node.args[0].value for node in ast.walk(tree)
             if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute)
             and node.func.attr == "add_parser" and node.args
             and isinstance(node.args[0], ast.Constant)
             and isinstance(node.args[0].value, str)}
    return frozenset(names - {"gate"})


def _drives_a_gate_verb(path: Path, verbs: frozenset[str]) -> bool:
    return any(verb in verbs
               for verb in _GATE_VERB.findall(path.read_text(encoding="utf-8")))


def test_the_governed_list_is_every_governed_suite_that_drives_a_gate_verb() -> None:
    verbs = _gate_verbs()
    assert {"create-document", "edit-document", "abandon-session"} <= verbs
    governed = tests_conftest.governed_suites()
    assert len(governed) >= 16, "12.5's floor: fewer means a proof vanished"
    scanned = {name for name in governed
               if _drives_a_gate_verb(TESTS / name, verbs)}
    listed = set(tests_conftest.GOVERNED_HOST_SUITES)
    assert scanned == listed, (
        f"drive a gate verb but are not listed: {sorted(scanned - listed)}; "
        f"listed but drive none: {sorted(listed - scanned)}. A governed suite "
        "(12.5's set) that drives openXdox's gate verbs needs a host carrying "
        "openXdox's columns, so it joins tests/conftest.py's "
        "GOVERNED_HOST_SUITES")
    # The scan is 12.5's own set, and not every module that drives a verb:
    # outside the governed set a suite registers its own host, or none.
    assert any(_drives_a_gate_verb(path, verbs)
               for path in TESTS.glob("test_*.py") if path.name not in governed)


def test_a_module_on_both_lists_runs_under_the_governed_host() -> None:
    governed = tests_conftest.GOVERNED_HOST_SUITES
    plane = tests_conftest.HOST_PLANE_SUITES
    assert governed & plane, "no module is on both lists, so nothing tests the order"
    for name in governed:
        assert tests_conftest.plane_host_for(name) == "governed", name
    for name in plane - governed:
        assert tests_conftest.plane_host_for(name) == "stand-in", name
    assert tests_conftest.plane_host_for(Path(__file__).name) is None


def _stand_in_columns(monkeypatch) -> list[str]:
    """A module object for each of openXdox's governed columns, standing in for
    the real one, which reaches `doc_health`. Each carries its named class, and
    the harness's imports of them are recorded, in order, in the list returned.
    Nothing else is imported differently, and `sys.modules` is not touched."""
    modules: dict[str, types.ModuleType] = {}
    for _, module, name in tests_conftest.GOVERNED_COLUMNS:
        stand_in = modules.setdefault(module, types.ModuleType(module))
        setattr(stand_in, name, type(name, (), {}))
    imported: list[str] = []
    real_import = importlib.import_module

    def import_module(name: str, package: str | None = None):
        if name in modules:
            imported.append(name)
            return modules[name]
        return real_import(name, package)

    monkeypatch.setattr(tests_conftest, "importlib",
                        types.SimpleNamespace(import_module=import_module))
    return imported


def test_the_governed_stand_in_carries_openxdoxs_three_columns(monkeypatch) -> None:
    """openXdox's share of openxFactory's profile: its gate verbs, and its gate
    and projection routes. Each named class is defined where it is named."""
    assert tests_conftest.GOVERNED_COLUMNS == (
        ("SUBCOMMAND_EXTENSIONS", "openxdox.cli_gate", "GateSubcommands"),
        ("ROUTE_EXTENSIONS", "openxdox.serve_gate", "GateRoutesExtension"),
        ("ROUTE_EXTENSIONS", "openxdox.serve_projection", "ProjectionRoutesExtension"),
    )
    for _, module, name in tests_conftest.GOVERNED_COLUMNS:
        source = (SOURCE / Path(*module.split("."))).with_suffix(".py")
        tree = ast.parse(source.read_text(encoding="utf-8"))
        assert name in {node.name for node in tree.body
                        if isinstance(node, ast.ClassDef)}, (module, name)

    _stand_in_columns(monkeypatch)
    monkeypatch.setitem(sys.modules, "opendox_host", None)   # not composed
    host = tests_conftest.governed_host()
    assert isinstance(host, tests_conftest.GovernedStandInHost)
    assert [type(c).__name__ for c in host.SUBCOMMAND_EXTENSIONS] == ["GateSubcommands"]
    assert [type(c).__name__ for c in host.ROUTE_EXTENSIONS] == [
        "GateRoutesExtension", "ProjectionRoutesExtension"]
    assert host.ROUTE_EXTENSIONS is host.ROUTE_EXTENSIONS
    assert host is not default_profile
    if importlib.util.find_spec("opendox.console_access") is not None:
        from opendox import console_access

        assert (console_access.delivery_for(host)
                == console_access.DELIVERY_CAPABILITIES)


class _Composite:
    """openxFactory's composite, stood in. Reading a built facet records
    whether openXdox's columns were already imported, and then does what
    importing openxFactory's lane column does: puts a pinned leg at the head
    of `sys.path`."""

    def __init__(self, leg: Path, imported: list[str], on_read=None) -> None:
        self.leg, self.imported, self.on_read, self.reads = leg, imported, on_read, []

    def __getattr__(self, name: str):
        if name not in tests_conftest.BUILT_FACETS:
            raise AttributeError(name)
        columns = {module for _, module, _ in tests_conftest.GOVERNED_COLUMNS}
        self.reads.append((name, columns <= set(self.imported)))
        if str(self.leg) not in sys.path:
            sys.path.insert(0, str(self.leg))
        if self.on_read is not None:
            self.on_read()
        return ()


def _composed(monkeypatch, composite: _Composite) -> None:
    host_module = types.ModuleType("opendox_host")
    host_module.profile = lambda: composite
    monkeypatch.setitem(sys.modules, "opendox_host", host_module)


def test_composed_the_governed_host_is_the_composite_and_the_reach_is_put_back(
        monkeypatch, tmp_path) -> None:
    imported = _stand_in_columns(monkeypatch)
    composite = _Composite(tmp_path / "openXdox" / "code" / "src", imported)
    _composed(monkeypatch, composite)
    before = list(sys.path)
    earlier = tests_conftest.StandInHost()
    with tests_conftest.a_hosts_plane(lambda: earlier):
        with tests_conftest.a_hosts_plane(tests_conftest.governed_host) as host:
            assert host is composite
            assert registry.current() is composite
            assert sys.path == before
        assert registry.current() is earlier
    assert [name for name, _ in composite.reads] == list(tests_conftest.BUILT_FACETS)
    assert all(imported for _, imported in composite.reads), (
        "a facet was read before openXdox's columns were imported from this "
        "checkout")


def test_an_openxdox_module_from_elsewhere_refuses_the_case(monkeypatch, tmp_path) -> None:
    imported = _stand_in_columns(monkeypatch)
    elsewhere = types.ModuleType("openxdox.from_a_pinned_leg")
    elsewhere.__file__ = str(tmp_path / "openxdox" / "from_a_pinned_leg.py")

    def import_from_the_leg():
        monkeypatch.setitem(sys.modules, elsewhere.__name__, elsewhere)

    composite = _Composite(tmp_path / "leg", imported, on_read=import_from_the_leg)
    _composed(monkeypatch, composite)
    before = list(sys.path)
    with pytest.raises(RuntimeError, match=r"openxdox\.from_a_pinned_leg"):
        tests_conftest.governed_host()
    assert sys.path == before


def test_openxfactorys_host_is_absent_only_when_its_own_module_is(monkeypatch, tmp_path) -> None:
    monkeypatch.setitem(sys.modules, "opendox_host", None)
    assert tests_conftest.openxfactory_host() is None
    monkeypatch.delitem(sys.modules, "opendox_host")
    (tmp_path / "opendox_host.py").write_text(
        "import a_dependency_the_host_lacks\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    with pytest.raises(ModuleNotFoundError) as refused:
        tests_conftest.openxfactory_host()
    assert refused.value.name == "a_dependency_the_host_lacks"
