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


# ---------------------------------------------------------------------------
# THE COMPOSED HARNESS FOR THE DECLARED INTEGRATION TESTS (plan 038 T095; T094's
# map R2-INV-R9, ruled at openxFactory#656 comment 6021830531). Its lists are
# held to their rules, and each of its pieces to its behaviour, here, in a
# lone checkout: openxFactory's host, its reach and its composite are stood in
# where a case needs them.
# ---------------------------------------------------------------------------

import contextlib  # noqa: E402
import os  # noqa: E402

import yaml  # noqa: E402

from opendox import doxbench_trust, workbench  # noqa: E402

#: A test module that registers openXdox's columns itself names one of these.
_OWN_COLUMNS = re.compile(r"\b(?:column_contributions|column_seams)\b")


def _declared_entries() -> frozenset[str]:
    declaration = yaml.safe_load(
        (TESTS / "declared_exclusion.yaml").read_text(encoding="utf-8"))
    return frozenset(Path(entry["path"]).name for entry in declaration["entries"])


def _composed_lists() -> dict[str, frozenset[str]]:
    return {
        "DECLARED_HOST_SUITES": tests_conftest.DECLARED_HOST_SUITES,
        "HOST_SEAM_SUITES": frozenset(tests_conftest.HOST_SEAM_SUITES),
        "LOCAL_INSTALL_SUITES": tests_conftest.LOCAL_INSTALL_SUITES,
    }


def test_each_composed_list_names_declared_files_outside_the_governed_set() -> None:
    """Each list names test files the declaration lists, which run composed
    and never in a lone checkout, and none of 12.5's governed suites, which
    have their own host list and their own scan."""
    declared = _declared_entries()
    governed = tests_conftest.governed_suites()
    for name, members in _composed_lists().items():
        assert members, f"{name} is empty"
        assert members <= declared, (
            f"{name} names files the declaration does not list: "
            f"{sorted(members - declared)}. Its pieces are for the declared "
            "integration tests, which run only composed")
        assert not members & governed, (
            f"{name} names 12.5's governed suites: {sorted(members & governed)}")
        for member in members:
            assert (TESTS / member).is_file(), (name, member)


def test_a_file_that_registers_openxdoxs_columns_never_gets_the_declared_host() -> None:
    """OQ-R9-1: `test_column_contributions_governed.py` registers openXdox's
    columns itself, and T094 measured two of its cases red under the governed
    host, where two bindings claim `POST /actions/gate/`. So it stays off the
    list, as does any file that registers the columns itself."""
    assert "test_column_contributions_governed.py" in _declared_entries()
    assert "test_column_contributions_governed.py" not in tests_conftest.DECLARED_HOST_SUITES
    for member in tests_conftest.DECLARED_HOST_SUITES:
        assert not _OWN_COLUMNS.search((TESTS / member).read_text(encoding="utf-8")), member


def test_the_seam_suites_name_seams_opendox_carries() -> None:
    """Each seam named is a registration call openDox carries, with the
    holder and the call that empties it that `a_hosts_seam` reads."""
    named = {seam for seams in tests_conftest.HOST_SEAM_SUITES.values() for seam in seams}
    assert named == set(tests_conftest.HOST_SEAM_HOLDERS)
    for (module_name, call), (held, is_default, unregister) in (
            tests_conftest.HOST_SEAM_HOLDERS.items()):
        module = importlib.import_module(module_name)
        assert callable(getattr(module, call)), (module_name, call)
        assert callable(getattr(module, unregister)), (module_name, unregister)
        assert hasattr(module, held), (module_name, held)
        assert is_default is None or hasattr(module, is_default), (module_name, is_default)


def test_the_local_install_suites_drive_generate_and_open() -> None:
    """W2's premise: a suite on the list drives `generate-and-open`, the verb
    a hosted install refuses."""
    for member in tests_conftest.LOCAL_INSTALL_SUITES | {tests_conftest._LAUNCH_SUITE}:
        assert "generate-and-open" in (TESTS / member).read_text(encoding="utf-8"), member


def _not_composed(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "opendox_host", None)


def _a_host_module(monkeypatch, root: Path, **calls) -> types.ModuleType:
    """openxFactory's host module, stood in at `root/scripts/opendox_host.py`."""
    host_module = types.ModuleType("opendox_host")
    host_module.__file__ = str(root / "scripts" / "opendox_host.py")
    for name, call in calls.items():
        setattr(host_module, name, call)
    monkeypatch.setitem(sys.modules, "opendox_host", host_module)
    return host_module


def test_lone_nothing_of_the_composed_harness_acts(monkeypatch) -> None:
    """Where `opendox_host` is absent, which is every lone checkout, no list
    gets a host, a seam, a farm or a local install, and the environment is
    untouched."""
    _not_composed(monkeypatch)
    assert tests_conftest.openxfactory_root() is None
    for member in tests_conftest.DECLARED_HOST_SUITES:
        assert tests_conftest.declared_host_for(member) is None, member
    for member, seams in tests_conftest.HOST_SEAM_SUITES.items():
        assert tests_conftest.openxfactory_seams(seams) == (), member
    for member in tests_conftest.LOCAL_INSTALL_SUITES:
        assert not tests_conftest.runs_a_local_install(member), member
    assert tests_conftest.runs_a_local_install(tests_conftest._LAUNCH_SUITE)
    environ: dict[str, str] = {}
    assert tests_conftest.compose_the_contracts_farm(environ) is None
    assert environ == {}


def test_this_process_has_a_farm_exactly_where_it_is_composed() -> None:
    """CONTRACTS_DIR is None in a lone checkout. Where the run is composed it
    names the farm this conftest built at import, and so does the
    environment every subprocess inherits."""
    if tests_conftest.openxfactory_root() is None:
        assert tests_conftest.CONTRACTS_DIR is None
        return
    farm = tests_conftest.CONTRACTS_DIR
    assert farm is not None
    assert farm.name == "contracts"
    assert (farm / "schemas").is_dir()
    assert (farm.parent / "examples" / "ideation-dashboard").is_dir()
    assert os.environ["CONTRACTS_DIR"] == str(farm)
    assert not farm.resolve().is_relative_to(TESTS.parent.resolve())


def test_composed_openxfactorys_root_is_the_directory_above_its_host_module(
        monkeypatch, tmp_path) -> None:
    _a_host_module(monkeypatch, tmp_path / "openxFactory")
    assert tests_conftest.openxfactory_root() == (tmp_path / "openxFactory").resolve()


def test_composed_a_declared_host_suite_runs_under_the_governed_host(
        monkeypatch, tmp_path) -> None:
    """Composed, each listed file's cases get the governed host, inside the
    stand-in host's plane where the file is on both lists, and the stand-in
    is back afterwards. A file off the list gets nothing."""
    imported = _stand_in_columns(monkeypatch)
    composite = _Composite(tmp_path / "openXdox" / "code" / "src", imported)
    _composed(monkeypatch, composite)
    for member in tests_conftest.DECLARED_HOST_SUITES:
        assert tests_conftest.declared_host_for(member) is tests_conftest.governed_host
    for other in ("test_column_contributions_governed.py", Path(__file__).name,
                  "test_session_gates.py"):
        assert tests_conftest.declared_host_for(other) is None, other
    both = tests_conftest.DECLARED_HOST_SUITES & tests_conftest.HOST_PLANE_SUITES
    assert both, "no listed file is on the stand-in's list too, so nothing tests the order"
    before = list(sys.path)
    earlier = tests_conftest.StandInHost()
    with tests_conftest.a_hosts_plane(lambda: earlier):
        with tests_conftest.a_hosts_plane(
                tests_conftest.declared_host_for(sorted(both)[0])) as host:
            assert host is composite
            assert registry.current() is composite
            assert sys.path == before
        assert registry.current() is earlier


def _fixture_definition(request, name: str):
    manager = request.config.pluginmanager.get_plugin("funcmanage")
    definitions = manager.getfixturedefs(name, request.node)
    assert definitions, name
    assert len(definitions) == 1, name
    return definitions[0]


def test_the_declared_host_is_set_up_inside_the_stand_in_hosts_plane(request) -> None:
    """The declared host's fixture requests the stand-in's, so pytest sets the
    stand-in up first, and the governed host is the one registered while a
    file on both lists runs."""
    definition = _fixture_definition(
        request, "_the_governed_host_for_the_declared_host_suites")
    assert "_a_hosts_plane_for_the_token_reading_suites" in definition.argnames


def test_the_launch_suites_fixture_reads_the_extended_list(request, monkeypatch,
                                                           tmp_path) -> None:
    """W2: T086's fixture runs for each file `runs_a_local_install` answers,
    and that is the launch suite everywhere and LOCAL_INSTALL_SUITES composed."""
    definition = _fixture_definition(request, "_the_launch_suite_runs_a_local_install")
    assert "runs_a_local_install(request.node.path.name)" in inspect.getsource(definition.func)
    _a_host_module(monkeypatch, tmp_path / "openxFactory")
    for member in tests_conftest.LOCAL_INSTALL_SUITES:
        assert tests_conftest.runs_a_local_install(member), member
    assert tests_conftest.runs_a_local_install(tests_conftest._LAUNCH_SUITE)
    assert not tests_conftest.runs_a_local_install("test_canvas.py")


class _Policy:
    """A trust policy, stood in."""

    def verdict(self, binding, *, root):  # noqa: D102
        return None

    def record(self, binding, *, root):  # noqa: D102
        return None


def _health_check(*args, **kwargs):  # noqa: D103
    return None


def _another_check(*args, **kwargs):  # noqa: D103
    return None


@contextlib.contextmanager
def _the_seams_kept(monkeypatch):
    """Whatever this case does at the two seams, they are as they were after."""
    for attribute in ("_health_check",):
        monkeypatch.setattr(workbench, attribute, getattr(workbench, attribute))
    for attribute in ("_registered", "_is_default", "_default_read"):
        monkeypatch.setattr(doxbench_trust, attribute, getattr(doxbench_trust, attribute))
    yield


def test_composed_the_seam_rows_are_read_off_the_hosts_table(monkeypatch, tmp_path) -> None:
    policy = _Policy()
    table = ((workbench, "register_session_notebook_scope", "documents"),
             (workbench, "register_health_check", _health_check),
             (doxbench_trust, "register", policy))
    _a_host_module(monkeypatch, tmp_path, seams=lambda: table)
    assert tests_conftest.openxfactory_seams((tests_conftest.HEALTH_CHECK_SEAM,)) == (
        (workbench, "register_health_check", _health_check),)
    assert tests_conftest.openxfactory_seams(
        (tests_conftest.HEALTH_CHECK_SEAM, tests_conftest.BINDING_TRUST_SEAM)) == (
        (workbench, "register_health_check", _health_check),
        (doxbench_trust, "register", policy))
    _a_host_module(monkeypatch, tmp_path, seams=lambda: table + table[1:2])
    with pytest.raises(RuntimeError, match="names 2 rows"):
        tests_conftest.openxfactory_seams((tests_conftest.HEALTH_CHECK_SEAM,))
    _a_host_module(monkeypatch, tmp_path, seams=lambda: table[:1])
    with pytest.raises(RuntimeError, match="names 0 rows"):
        tests_conftest.openxfactory_seams((tests_conftest.HEALTH_CHECK_SEAM,))


def test_composed_the_seam_table_is_read_with_the_reach_put_back(monkeypatch, tmp_path) -> None:
    """Reading the table may put a pinned leg on `sys.path` and import an
    `openxdox` module from it, as the composite's facets can. The path is put
    back, and a module from elsewhere refuses the case, by name."""
    elsewhere = types.ModuleType("openxdox.from_the_seam_table")
    elsewhere.__file__ = str(tmp_path / "openxdox" / "from_the_seam_table.py")

    def seams():
        sys.path.insert(0, str(tmp_path / "leg"))
        return ((workbench, "register_health_check", _health_check),)

    _a_host_module(monkeypatch, tmp_path, seams=seams)
    before = list(sys.path)
    tests_conftest.openxfactory_seams((tests_conftest.HEALTH_CHECK_SEAM,))
    assert sys.path == before
    monkeypatch.setitem(sys.modules, elsewhere.__name__, elsewhere)
    with pytest.raises(RuntimeError, match=r"openxdox\.from_the_seam_table"):
        tests_conftest.openxfactory_seams((tests_conftest.HEALTH_CHECK_SEAM,))
    assert sys.path == before


def _raise_inside(module, call, what) -> None:
    with tests_conftest.a_hosts_seam(module, call, what):
        raise RuntimeError("raised in the block")


def test_a_hosts_health_check_is_registered_for_the_block_and_put_back(monkeypatch) -> None:
    with _the_seams_kept(monkeypatch):
        workbench.unregister_health_check()
        with tests_conftest.a_hosts_seam(workbench, "register_health_check", _health_check):
            assert workbench._health_check is _health_check
        assert not workbench.health_check_registered()
        workbench.register_health_check(_another_check)
        with tests_conftest.a_hosts_seam(workbench, "register_health_check", _health_check):
            assert workbench._health_check is _health_check
        assert workbench._health_check is _another_check
        with pytest.raises(RuntimeError, match="raised in the block"):
            _raise_inside(workbench, "register_health_check", _health_check)
        assert workbench._health_check is _another_check


def test_a_hosts_trust_policy_is_registered_for_the_block_and_put_back(monkeypatch) -> None:
    """A host's policy held before is registered again after; openDox's own
    default is not, since its consumers register it again."""
    policy, earlier = _Policy(), _Policy()
    with _the_seams_kept(monkeypatch):
        doxbench_trust.unregister()
        doxbench_trust.policy()  # openDox's default, registered and read
        with tests_conftest.a_hosts_seam(doxbench_trust, "register", policy):
            assert doxbench_trust.current() is policy
        assert not doxbench_trust.is_registered()
        doxbench_trust.register(earlier)
        with tests_conftest.a_hosts_seam(doxbench_trust, "register", policy):
            assert doxbench_trust.current() is policy
        assert doxbench_trust.current() is earlier


def _a_tree(root: Path, files: dict[str, str]) -> None:
    for relative, text in files.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(text, encoding="utf-8")


def _a_reach(root: Path, rows: dict[str, Path]) -> types.SimpleNamespace:
    """openxFactory's reach (`carved_reach`), stood in over the tree `root`."""
    return types.SimpleNamespace(
        __file__=str(root / "scripts" / "carved_reach.py"),
        REPO_ROOT=root,
        MOUNTS={"opendox_spec": root / "openDox" / "spec",
                "openxdox_spec": root / "openXdox" / "spec"},
        sources_under=lambda prefix: {key: path for key, path in rows.items()
                                      if key.startswith(prefix.rstrip("/") + "/")})


def _links(base: Path) -> dict[str, Path]:
    return {path.relative_to(base).as_posix(): Path(os.readlink(path))
            for path in sorted(base.rglob("*")) if path.is_symlink()}


def test_the_farm_links_the_familys_schemas_and_examples(tmp_path) -> None:
    """The schemas: each carve row under `contracts/schemas/` at its file today
    (nested rows are not the family's), then openxFactory's own not linked yet.
    The examples: each owner's YAML at its relative path, less openDox's own
    snapshot examples."""
    root = tmp_path / "openxFactory"
    _a_tree(root, {
        "contracts/schemas/gate-intent.schema.yaml": "",
        "contracts/schemas/project-register.schema.yaml": "",
        "contracts/schemas/notes.md": "",
        "openXdox/spec/contracts/schemas/gate-action-record.schema.yaml": "",
        "openXdox/spec/contracts/schemas/nested/inner.schema.yaml": "",
        "openDox/spec/contracts/schemas/project-register.schema.yaml": "",
        "examples/ideation-dashboard/gate-intent-x.example.yaml": "",
        "examples/ideation-dashboard/transitions/t.example.yaml": "",
        "openDox/spec/examples/ideation-dashboard/workbench-x.example.yaml": "",
        "openDox/spec/examples/ideation-dashboard/opendox-snapshot-x.example.yaml": "",
        "openDox/spec/examples/ideation-dashboard/negative/opendox-snapshot-y.negative.yaml": "",
        "openDox/spec/examples/ideation-dashboard/negative/pair/turn.negative.yaml": "",
        "openXdox/spec/examples/ideation-dashboard/README.md": "",
        "openXdox/spec/examples/ideation-dashboard/negative/record.negative.yaml": "",
    })
    rows = {
        "contracts/schemas/gate-action-record.schema.yaml":
            root / "openXdox/spec/contracts/schemas/gate-action-record.schema.yaml",
        "contracts/schemas/project-register.schema.yaml":
            root / "openDox/spec/contracts/schemas/project-register.schema.yaml",
        "contracts/schemas/nested/inner.schema.yaml":
            root / "openXdox/spec/contracts/schemas/nested/inner.schema.yaml",
        "examples/ideation-dashboard/gate-intent-x.example.yaml": root / "elsewhere.yaml",
    }
    farm = tmp_path / "farm"
    contracts = tests_conftest.build_contracts_farm(_a_reach(root, rows), farm)
    assert contracts == farm / "contracts"
    assert _links(contracts / "schemas") == {
        "gate-action-record.schema.yaml":
            root / "openXdox/spec/contracts/schemas/gate-action-record.schema.yaml",
        "gate-intent.schema.yaml": root / "contracts/schemas/gate-intent.schema.yaml",
        "project-register.schema.yaml":
            root / "openDox/spec/contracts/schemas/project-register.schema.yaml",
    }
    assert _links(farm / "examples" / "ideation-dashboard") == {
        "gate-intent-x.example.yaml": root / "examples/ideation-dashboard/gate-intent-x.example.yaml",
        "transitions/t.example.yaml": root / "examples/ideation-dashboard/transitions/t.example.yaml",
        "workbench-x.example.yaml":
            root / "openDox/spec/examples/ideation-dashboard/workbench-x.example.yaml",
        "negative/pair/turn.negative.yaml":
            root / "openDox/spec/examples/ideation-dashboard/negative/pair/turn.negative.yaml",
        "negative/record.negative.yaml":
            root / "openXdox/spec/examples/ideation-dashboard/negative/record.negative.yaml",
    }


def test_the_farm_refuses_an_example_two_owners_keep(tmp_path) -> None:
    root = tmp_path / "openxFactory"
    _a_tree(root, {
        "examples/ideation-dashboard/negative/same.negative.yaml": "",
        "openXdox/spec/examples/ideation-dashboard/negative/same.negative.yaml": "",
    })
    reach, farm = _a_reach(root, {}), tmp_path / "farm"
    with pytest.raises(RuntimeError, match=r"two owners keep the example negative/same"):
        tests_conftest.build_contracts_farm(reach, farm)


def test_composed_the_farm_is_built_outside_the_checkout_and_named_in_the_environment(
        monkeypatch, tmp_path) -> None:
    root = tmp_path / "openxFactory"
    _a_tree(root, {"contracts/schemas/gate-intent.schema.yaml": ""})
    _a_host_module(monkeypatch, root)
    monkeypatch.setitem(sys.modules, "carved_reach", _a_reach(root, {}))
    removed = []
    monkeypatch.setattr(tests_conftest, "_atexit", types.SimpleNamespace(
        register=lambda call, *args, **kwargs: removed.append((call, args, kwargs))))
    (tmp_path / "t").mkdir()
    environ = {"CONTRACTS_DIR": "a directory the environment named before"}
    contracts = tests_conftest.compose_the_contracts_farm(environ, under=str(tmp_path / "t"))
    assert contracts is not None
    assert contracts.parent.parent == tmp_path / "t"
    assert contracts.parent.name.startswith("openxdox-contracts-farm-")
    assert environ == {"CONTRACTS_DIR": str(contracts)}
    assert _links(contracts / "schemas") == {
        "gate-intent.schema.yaml": root / "contracts/schemas/gate-intent.schema.yaml"}
    assert removed == [(tests_conftest._shutil.rmtree, (contracts.parent,),
                        {"ignore_errors": True})]


def test_composed_a_reach_from_another_tree_is_refused(monkeypatch, tmp_path) -> None:
    root = tmp_path / "openxFactory"
    _a_tree(root, {"contracts/schemas/gate-intent.schema.yaml": ""})
    _a_host_module(monkeypatch, root)
    monkeypatch.setitem(sys.modules, "carved_reach", _a_reach(tmp_path / "another", {}))
    environ: dict[str, str] = {}
    with pytest.raises(RuntimeError, match="not from the composed tree"):
        tests_conftest.compose_the_contracts_farm(environ, under=str(tmp_path))
    assert environ == {}
