"""Layer 2 of the hermeticity guard, proved where this leg's whole suite runs.

Until plan 034 task T041, `tests/hermeticity.py`'s `runner_seams()` probed
openxFactory's `ideation_dashboard.*` and so returned no seams at this leg.
Layer 2 was off, and an escape through the default `nlm` runner degraded
silently. It now names the pinned openDox's `opendox.workbench` and
`opendox.session_pr`. The regression that needed it,
`tests/test_hermeticity_gate_verbs.py`, sits in the declared exclusion on
`doc_health`, so it proves nothing in a lone checkout. These cases import only
the pinned openDox and the guard, so they run wherever the whole suite runs.

The two refusal cases are openDox-code's own, as they read at openDox-code
`main` `68be484a` (`tests/test_hermeticity.py` lines 185-198), where they stay.
The seam-table case is new here: it fails the moment `runner_seams()` stops
naming the two seams, before any refusal is attempted.

The two port cases are new here too. The refusal cases call the patched seams
by hand, so they pass whatever the production code does. The port cases drive
the production call path instead: the notebook port and the pull-request port
that a CLI verb declares, each with no runner injected. Suppose a port bound
the real runner before the guard ran. It would miss layer 2, and layer 1's
non-zero exit would degrade in silence. The seam-table and refusal cases
would still pass, and so would every other case of the whole suite less the
declared exclusion. Each port case fails. Each drives a read, so a guard that
failed would write nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import hermeticity

from opendox import branch_session as bs
from opendox import cli
from opendox import session_pr as session_pr_mod
from opendox import workbench as wb

REPO_ROOT = Path(__file__).resolve().parents[1]
SESSION_ALIAS = bs.notebook_alias("openxFactory", "draft/demo-topic")


def test_layer_two_names_the_pinned_opendox_seams():
    """The table both installers read. A probe that answered "absent" here
    returned an empty table, and every layer-2 refusal silently went with
    it."""
    seams = [(target, attribute)
             for target, attribute, _ in hermeticity.runner_seams()]
    assert seams == [(wb, "_default_runner"),
                     (session_pr_mod.SubprocessCommandRunner, "run")], seams


def test_the_default_notebook_runner_refuses_instead_of_running_nlm():
    with pytest.raises(hermeticity.HermeticityViolation) as raised:
        wb._default_runner("notebook", "create", SESSION_ALIAS)
    message = str(raised.value)
    assert hermeticity.MARKER in message
    assert "test_the_default_notebook_runner_refuses_instead_of_running_nlm" in message


def test_the_default_pull_request_runner_refuses_instead_of_running_gh():
    with pytest.raises(hermeticity.HermeticityViolation) as raised:
        session_pr_mod.SubprocessCommandRunner().run("gh", "pr", "create",
                                                    cwd=REPO_ROOT)
    assert hermeticity.MARKER in str(raised.value)


def test_the_cli_notebook_port_reaches_the_refusal_by_its_default_runner():
    """`cli._notebook_port` is a `NotebookAdapter` with no runner injected.
    Its listing must be refused, and the refusal must pass through the
    adapter's `except Exception`, which turns an `nlm` failure into a listing
    that could not be read."""
    port = cli._notebook_port(REPO_ROOT)
    with pytest.raises(hermeticity.HermeticityViolation) as raised:
        port.list_titled_result(wb.NOTEBOOK_PREFIX)
    message = str(raised.value)
    assert hermeticity.MARKER in message
    assert ("test_the_cli_notebook_port_reaches_the_refusal_by_its_default_"
            "runner" in message)


def test_the_cli_pull_request_port_reaches_the_refusal_by_its_default_runner():
    """`cli._pull_request_port` is a `GhPullRequests` with no runner injected.
    Its side-effect-free `find_open` must be refused on its first command, and
    the refusal must not be taken for the port's own `PullRequestRefused`."""
    port = cli._pull_request_port(REPO_ROOT)
    with pytest.raises(hermeticity.HermeticityViolation) as raised:
        port.find_open("t041-hermeticity-probe")
    message = str(raised.value)
    assert hermeticity.MARKER in message
    assert ("test_the_cli_pull_request_port_reaches_the_refusal_by_its_"
            "default_runner" in message)
