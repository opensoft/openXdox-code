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
"""

from __future__ import annotations

from pathlib import Path

import pytest

import hermeticity

from opendox import branch_session as bs
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
