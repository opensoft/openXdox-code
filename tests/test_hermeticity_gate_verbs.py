"""The two hermeticity cases that drive openXdox's `gate` verbs.

WHERE THEY CAME FROM. Both left openDox-code's `tests/test_hermeticity.py` in
openDox-code#51 (plan 034 task T035), whose pull request body lists them for
this leg's declared exclusion (T041). Their text is the one at openDox-code
`main` `68be484a`, `tests/test_hermeticity.py` lines 226-240 and 262-275,
names and docstrings unchanged. `gate` is not an openDox verb since the carve:
the HOST profile contributes it, and the verbs are openXdox's
(`openxdox.cli_gate.GateSubcommands`). So openDox's own suite has no `gate` to
parse, and this is the leg that owns what they drive.

WHY THIS FILE IS IN THE DECLARED EXCLUSION. `cli_gate` imports `gate_console`,
and `gate_console` imports openxFactory's `doc_health` at module level
(`from doc_health import corpus`), which no lone checkout supplies. So this
file fails at collection on `doc_health`, and `tests/declared_exclusion.yaml`
lists it with that reason, as R1Q6 (d) rules. It cannot go to
`tests/integration/` instead, because F9.2 runs every file there (T042).

THE HOST, STOOD IN. No test in this leg registers an openDox profile that
carries `gate`. openxFactory's `profile_openxfactory.SUBCOMMAND_EXTENSIONS` is
what does it in the composed product. So `gate_host_profile` below registers a
stand-in host that contributes exactly `cli_gate.GateSubcommands()`, as that
tuple does, and it puts the previous registration back afterwards.

MEASURED BEHIND THE EXCLUSION'S REASON. With openxFactory's `scripts/` on
`PYTHONPATH`, which supplies `doc_health` (R1Q23 (a)'s composition), both
cases pass, with openDox-code `5c137a90` installed and with `71b631bc`. That
needs layer 2 of `tests/hermeticity.py` to be on at this leg, which the same
pull request does. Without the stand-in host, `gate` is an
invalid choice. Without layer 2, the unguarded create reaches the `nlm` shim,
the notebook adapter swallows the refusal, and nothing is raised.
"""

from __future__ import annotations

import pytest

import hermeticity

from opendox import branch_session as bs
from opendox import cli as cli_mod
from opendox import domain_profile as opendox_profile
from openxdox import cli_gate

SESSION_ALIAS = bs.notebook_alias("openxFactory", "draft/demo-topic")


class _GateHost:
    """A host profile that contributes openXdox's gate verbs and nothing else,
    as openxFactory's `profile_openxfactory.SUBCOMMAND_EXTENSIONS` does."""

    SUBCOMMAND_EXTENSIONS = (cli_gate.GateSubcommands(),)
    ROUTE_EXTENSIONS = ()


#: The registry's module state. `_registered` is there at every pin.
#: `_is_default` and `_built_from_default` come with T016's default
#: registration (openDox-code `71b631bc`), and they are absent before it
#: (`5c137a90`). So the fixture records whichever of them the pinned openDox
#: keeps.
_REGISTRY_STATE = ("_registered", "_is_default", "_built_from_default")


@pytest.fixture(autouse=True)
def gate_host_profile(monkeypatch):
    """Register the stand-in host for one test, then restore what was there.

    `opendox.cli` registers openDox's own default where no host has, and a
    host's registration is refused once a parser has been built from that
    default (R1Q3 (ii)). So the registration is dropped first, and the host's
    is made on a clean slate. Handing `monkeypatch` each CURRENT value of the
    registry's state records it for teardown, the idiom openDox-code#51 uses
    for the home corpus. So whatever was registered before this test, and
    whether a parser had been built from it, is put back. Only the state the
    pinned openDox keeps is recorded, so the fixture reaches its test at
    either pin."""
    for state in _REGISTRY_STATE:
        if hasattr(opendox_profile, state):
            monkeypatch.setattr(opendox_profile, state,
                                getattr(opendox_profile, state))
    opendox_profile.unregister()
    return opendox_profile.register(_GateHost())


def test_an_unguarded_cli_scoped_create_is_refused(scratch_repo):
    """Finding 17's own reproduction, inverted into a regression.

    This is the exact invocation that ran `nlm notebook create` against the
    shared account: a scoped `gate create-document` with NOTHING injected at
    `cli._notebook_port`. It must now REFUSE. If the guard is removed this test
    does not merely fail — it creates a real notebook, which is what makes it the
    right regression to keep."""
    with pytest.raises(hermeticity.HermeticityViolation):
        cli_mod.main([
            "gate", "create-document", "--repo-root", str(scratch_repo.root),
            "--actor", "brett", "--title", "Unguarded", "--summary", "No fake.",
            "--topics", "alpha", "--repository-context", scratch_repo.repository,
            "--area", "ideation/staging/demo-topic/",
            "--scope-kind", bs.STAGED_TOPIC, "--scope-id", scratch_repo.topic_id])


def test_the_cli_seam_with_a_fake_port_reaches_no_binary(scratch_repo, capsys,
                                                         fake_cli_notebook):
    """The seam `cli._notebook_port`'s docstring already promised, exercised
    through the harness fixture the three repaired CLI tests now request: with a
    fake injected the same scoped create succeeds AND the notebook is created on
    the fake, so the guard costs the suite no coverage."""
    code = cli_mod.main([
        "gate", "create-document", "--repo-root", str(scratch_repo.root),
        "--actor", "brett", "--title", "Guarded", "--summary", "With a fake.",
        "--topics", "alpha", "--repository-context", scratch_repo.repository,
        "--area", "ideation/staging/demo-topic/",
        "--scope-kind", bs.STAGED_TOPIC, "--scope-id", scratch_repo.topic_id])
    assert code == 0, capsys.readouterr().err
    assert fake_cli_notebook.live_aliases() == (SESSION_ALIAS,)
