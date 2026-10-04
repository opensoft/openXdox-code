"""The suites that read the console token run on a host's plane (plan 034 T086,
step (b); openDox-code's T104, RULED openxFactory#656 comment 5963851934).

`tests/conftest.py`'s `_a_hosts_plane_for_the_token_reading_suites` registers a
stand-in host for the length of each test of the modules `HOST_PLANE_SUITES`
names, because from T104 openDox publishes the console token on
`/capabilities` only on a host's plane. These cases hold that list and that
host to their reasons, and they run in a lone checkout, so in F9.1.

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import importlib.util
import inspect
import re
from pathlib import Path

import conftest as tests_conftest
from opendox import default_profile

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
