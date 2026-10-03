"""Test harness for the ideation-dashboard suite.

Puts `scripts/` on the import path (so `import ideation_dashboard...` resolves)
and exposes fixture-tree locations. Mirrors tests/doc-health/conftest.py.

The branch-session harness (007-workbench-branch-sessions T001/T002) lives in
`session_fixtures.py` beside this file; its pytest fixtures are re-exported at
the bottom so `scratch_repo` / `fake_pull_requests` / `fake_notebook_adapter`
resolve by name in any test module in this directory.

The STRUCTURAL hermeticity guard (`tests/hermeticity.py`) is registered here as
well as in `tests/conftest.py`, because a targeted `pytest tests/ideation-dashboard`
run makes this directory the rootdir and pytest's `confcutdir` then excludes the
suite-wide conftest from collection — and this is the directory whose CLI verbs
reached the real `nlm` (FR-043, PR #49 finding 17).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS_ROOT = HERE.parent
REPO_ROOT = HERE.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(TESTS_ROOT))

from hermeticity import (  # noqa: E402,F401  (autouse fixture registration)
    claim_conftest_slot,
    hermetic_binary_path,
    hermetic_external_runners,
)

FIXTURES = HERE / "fixtures"
BASE_REPO = FIXTURES / "base-repo"
NEGATIVES = FIXTURES / "negatives"

# The openxFactory validator. Since adopt-neutral-tooling-home (2026-08-03)
# this runtime lives INSIDE openxFactory, so the repo's own validator IS the
# reachable contract; the parent walk to a sibling `openxFactory/` checkout
# remains as a fallback for a checkout of the pre-relocation layout. None when
# no validator is reachable, in which case validator-backed tests skip rather
# than fail.
def find_openxfactory_validator(start: Path | None = None) -> Path | None:
    base = (start or REPO_ROOT).resolve()
    own = base / "scripts" / "validate-ideation-dashboard-contracts.py"
    if own.is_file():
        return own
    rel = Path("openxFactory") / "scripts" / "validate-ideation-dashboard-contracts.py"
    for d in [base, *base.parents]:
        candidate = d / rel
        if candidate.is_file():
            return candidate
    return None


# A stubbed git abstraction for the generator: the fixture base-repo lives INSIDE
# the openxFactory git repo, so a real `RealGit` HEAD is unstable across commits.
# Injecting FakeGit pins `generation.source_revision` and makes any derived
# `generated_at` come from a fixed committer date (never the wall clock), so
# byte-identity is testable (determinism caveat, wave-1 fixture headers).
class FakeGit:
    def __init__(self, head: str = "abcd1234" * 5,
                 date: str = "2026-07-12T00:00:00+00:00") -> None:
        self._head = head
        self._date = date

    def head_sha(self, repo) -> str:
        return self._head

    def commit_date(self, repo, revision: str) -> str:
        return self._date


# The pinned source revision every determinism/conformance test anchors on.
PINNED_REVISION = "abcd1234" * 5


# --------------------------------------------------------------------------
# add-staging-workbench: the staged-topic health fixture shapes, shared by the
# scoring tests, the readiness-gate tests and the branch-session harness so all
# of them exercise ONE definition of "ready", "blocked", and "underdone".
#
# DEFINED in `staging_shapes.py`, re-exported here (PR #49 review finding 19a):
# `session_fixtures.build_scratch_repo` needs the same shapes and used to reach
# them with `from conftest import staging_fragment` executed inside a fixture
# BODY, where the ambient `conftest` name resolves to whichever directory's
# conftest pytest imported last. Test modules keep spelling
# `from conftest import staging_fragment`, which is stable because that import
# runs at module-import time; the harness now imports the plainly named module.
# --------------------------------------------------------------------------

from staging_shapes import (  # noqa: E402,F401  (re-export, one definition)
    staging_fragment,
    thin_fragment,
)


# --------------------------------------------------------------------------
# 007-workbench-branch-sessions: the branch-session harness fixtures (T001,
# T002). Imported for their pytest-fixture side effect — every session test
# builds its world in tmp_path and never touches a real checkout (research R10).
# --------------------------------------------------------------------------

from session_fixtures import (  # noqa: E402,F401  (fixture registration)
    declared_gate_principals,
    declared_human_console,
    fake_cli_notebook,
    fake_notebook_adapter,
    fake_pull_requests,
    scratch_repo,
)


# --------------------------------------------------------------------------
# add-doxbench-editing-phase-b §12.2 — NOTHING PUSHES IMPLICITLY.
#
# ONE canonical list, because two copies of a negative drift apart silently and
# the drift is invisible by construction: both copies keep passing. §11 asserted
# the first four modules (the turn, the thread writer, the harness bridge, the
# MCP server); §12 owns the list now and adds three more — the turn assembler,
# the packet builder, and the nightly lane, which is the "periodic task" the
# requirement names.
#
# WHAT THIS LIST IS AND IS NOT, stated because the earlier wording overclaimed
# (§12 review, P3-5). It is NOT "every place in the package that could reach a
# remote". `register_edit_lane.py` is an automated lane that really does commit
# and push, and it is deliberately absent: it is pre-existing and separately
# ratified (`add-register-edit-lane`), and it pushes the aggregation-owned
# project register by explicit pathspec — never a thread, a buffer, or any
# session artifact, which is exactly what the §12 requirement scopes its
# negative to. `branch_session.py`, `session_git.py`, `session_pr.py` and
# `gate_routes.py` are absent for the plainer reason that they are the governed
# remote-write path itself.
#
# So the claim this list makes is the narrow, checkable one: none of the eight
# modules that carry a TURN, a SAVE, a COMPACTION, or a SCHEDULED doxBench task
# can reach a remote write. The SHARE verb appears nowhere here either — it
# lives in `gate_routes.py`, beside `open-pr` — and that placement is what lets
# this list stay a pure absence.
#
# WIDENED, NEVER NARROWED (`split-opendox-two-layer-product` § 2.4, OQ-1).
# `doxbench_status_exemption.py` is the lifecycle-status read carved out of
# `doxbench_packet.py`; the sweep follows the code rather than the filename, so
# splitting a listed module adds the piece that left instead of quietly
# shrinking what the negative covers. `test_doxbench_share.py` self-asserts
# that §11's four are still a subset, which is the half of this rule a test can
# keep on its own.
# --------------------------------------------------------------------------

NO_IMPLICIT_PUSH_MODULES: tuple[str, ...] = (
    "serve.py", "doxbench_threads.py", "doxbench_bridge.py", "doxbench_mcp.py",
    "doxbench_turns.py", "doxbench_packet.py", "nightly_lane.py",
    # WIDENED by `split-opendox-two-layer-product` § 2.4 (PR 2 of 4), which
    # moved the doxBench workbench routes, the project/notebook/edit routes and
    # the shared wire vocabulary out of `serve.py` into three sibling modules.
    # `serve_workbench.py` is REQUIRED here — it carries the TURN, which is
    # exactly the scope §12 names, and a list that stayed at "serve.py" would
    # have let a file move evade the absence without anything noticing. The
    # other two carry no turn, save, compaction or scheduled task, and are
    # listed anyway: the whole of the surface `serve.py` used to be is now four
    # files, and a sweep over three of them is a sweep with a seam in it.
    "serve_workbench.py", "serve_project.py", "serve_wire.py",
    # WIDENED by § 2.4 OQ-1 (PR #741, landed on `main` after this branch split
    # from it): `doxbench_status_exemption.py` is the lifecycle-status read
    # carved out of `doxbench_packet.py`, so the sweep follows the code rather
    # than the filename.
    "doxbench_status_exemption.py",
    # WIDENED AGAIN by § 2.4 (PR 3 of 4), which moved the gate console's door,
    # the projection/snapshot routes and this repository's own lane routes out
    # of `serve.py` into three more sibling modules. `serve_gate.py` is the
    # load-bearing one: `_handle_gate_action` dispatches the SESSION-BEARING
    # verbs, so a list left at PR 2's five would have let the file move evade
    # the §12 absence with nothing red. The other two carry no turn, save,
    # compaction or scheduled task and are listed for the same reason PR 2
    # listed its quiet pair — a sweep over some of the files the serve is made
    # of is a sweep with a seam in it.
    "serve_gate.py", "serve_projection.py", "serve_openxfactory_lanes.py",
)

# --------------------------------------------------------------------------
# THE SERVE SURFACE (`split-opendox-two-layer-product` § 2.4, PR 2 of 4).
#
# Several suites assert against `serve.py`'s SOURCE rather than over the wire,
# and say why at each site: a route whose alternative proof needs a live
# provider, an absence that no positive test can demonstrate, a call site whose
# enclosing `try` is the property. Those assertions are about THE SERVE, and
# the serve is now seven files rather than one.
#
# So the readers below span the whole surface. This is the same widen-never-
# narrow move `NO_IMPLICIT_PUSH_MODULES` just made, and for the same reason: an
# assertion pinned to one filename silently stops asserting the moment the code
# it was about moves to the next file along, and it keeps passing while it does
# it. Nothing here weakens an assertion — every scan sees strictly more code
# than it saw before — and a module added to the split must be added here.
# --------------------------------------------------------------------------

SERVE_SURFACE_MODULES: tuple[str, ...] = (
    "serve_wire.py", "serve_workbench.py", "serve_project.py",
    # WIDENED by § 2.4 (PR 3 of 4): the openXdox gate and projection columns and
    # the openxFactory lane column. Same rule, same direction — every scan over
    # this tuple now sees strictly more code than it saw before.
    "serve_gate.py", "serve_projection.py", "serve_openxfactory_lanes.py",
    "serve.py",
)

# `profile_openxfactory.py` is DELIBERATELY ABSENT from both this tuple and
# `NO_IMPLICIT_PUSH_MODULES` above, though PR 3 of § 2.4 makes it part of the
# serve surface too — `build_server` imports it and its `ROUTE_EXTENSIONS`
# tuple determines the whole contributed route table. It is left out because
# it is RELATIVE-IMPORT-ONLY BY DESIGN (`from . import serve_gate` etc., the
# same idiom `cli.py` uses for its own profile import — see the module's own
# docstring for why): the D12 relative-import guard these tuples feed
# (`test_serve_module_uses_no_relative_imports`) would fail on those three
# lines for a reason it does not exist to catch, so scanning it there is not
# a widening — it is asking the wrong question of the file. This is not a
# first exception: `snapshot_registry.py` is imported directly by both
# `serve.py` and `serve_projection.py` and has never been in either tuple
# either, so "every file the dashboard serve is made of" has never meant
# "every module `serve.py` transitively imports" — only "every module the
# CONTENT scans below (the credential-free walk, the hosted-session-arrival
# scan, the no-implicit-push sweep) should see."

# WHERE THE SERVE SURFACE LIVES AT THIS LEG (plan 034 task T040). The readers
# below used to find all seven files in openxFactory's
# `scripts/ideation_dashboard/`, a path this leg does not have. The carve split
# them three ways, each by its own manifest destination row:
#   * `serve.py`, `serve_wire.py`, `serve_workbench.py` and `serve_project.py`
#     went to openDox, and this leg reads them through its PIN, in the
#     installed `opendox` package — the same resolution `tests/opendox_bundle.py`
#     makes for the bundle;
#   * `serve_gate.py` and `serve_projection.py` came HERE, to `src/openxdox/`;
#   * `serve_openxfactory_lanes.py`, openxFactory's own lane column, stayed in
#     openxFactory (`not_moved`, `stays_openxfactory_adapter`).
# So the lane column is the one file of the tuple this leg cannot read. It is
# NAMED here rather than dropped from the tuple: the tuple stays the whole
# surface, and a file missing for any other reason still refuses the read. The
# declaration is held to its word as well (`assert_not_at_this_leg`): once the
# file is here, the readers refuse until the name leaves this tuple.
SERVE_SURFACE_NOT_AT_THIS_LEG: tuple[str, ...] = ("serve_openxfactory_lanes.py",)


def carved_module_homes(name: str) -> tuple[Path, Path]:
    """The two places the pre-carve module `scripts/ideation_dashboard/<name>`
    can live at this leg: this leg's own `src/openxdox/`, and the openDox it
    pins."""
    import opendox  # the PINNED openDox, resolved as `opendox_bundle.find()` does

    return (REPO_ROOT / "src" / "openxdox" / name,
            Path(opendox.__file__).resolve().parent / name)


def carved_module_path(name: str) -> Path:
    """Where the pre-carve module `scripts/ideation_dashboard/<name>` lives at
    this leg: in one of its two `carved_module_homes`.

    Refuses a name found in both homes or in neither, so a resolution can never
    quietly pick one, and a module that moved again reads as a failure rather
    than as a scan that got smaller."""
    homes = carved_module_homes(name)
    found = [path for path in homes if path.is_file()]
    if len(found) != 1:
        raise FileNotFoundError(
            f"{name}: expected in exactly one of this leg's src/openxdox/ and "
            f"the pinned opendox package; found in {len(found)} of "
            f"{[str(path) for path in homes]}")
    return found[0]


def assert_not_at_this_leg(names: tuple[str, ...]) -> None:
    """Hold a "not at this leg" declaration to its word: each name must be in
    NEITHER of its `carved_module_homes`.

    A scan skips a declared name. If the module then arrives here, the scan
    would skip code this leg carries and stay green, so this refuses instead.
    The repair is to drop the name from the declaration, so the scan reads it.
    """
    for name in names:
        present = [path for path in carved_module_homes(name)
                   if path.is_file()]
        if present:
            raise AssertionError(
                f"{name} is declared not at this leg, but it is here: "
                f"{[str(path) for path in present]}. Drop it from the "
                f"declaration, so the scan reads it.")


def serve_surface_paths() -> tuple[Path, ...]:
    """Every file the dashboard serve is made of that this leg can read, in
    import-graph order: the tuple above less `SERVE_SURFACE_NOT_AT_THIS_LEG`
    (held to its word by `assert_not_at_this_leg`), each at its carved home
    (`carved_module_path`).

    Dependency-first: `serve_wire.py` imports no sibling; `serve_workbench.py`,
    `serve_project.py`, `serve_gate.py` and `serve_projection.py` each import
    from `serve_wire` and from no other sibling; `serve_openxfactory_lanes.py`
    imports from `serve_projection` and from `serve_wire` NOT AT ALL any more
    (OQ-B re-plumb B-2, ruled on `#656` 2026-09-09: `hosted_ref_refused` was
    re-homed into `serve_projection.py` and the three fixed wire strings into
    the neutral `scripts/wire_messages.py`, so openxFactory's own adapter
    column stopped importing an openDox module) — which the tuple's order
    already accommodates, `serve_projection.py` sitting ahead of it;
    `serve.py` imports all six. No reader of
    `serve_surface_paths()` /
    `serve_surface_source()` depends on this particular order (every scan
    below is a per-file loop, a `.read_text()` join checked for
    substring/absence, or a `.index()` search that resolves within a single
    file's own content) — only the docstring claim above does.
    """
    assert_not_at_this_leg(SERVE_SURFACE_NOT_AT_THIS_LEG)
    return tuple(carved_module_path(name) for name in SERVE_SURFACE_MODULES
                 if name not in SERVE_SURFACE_NOT_AT_THIS_LEG)


def serve_surface_source() -> str:
    """The whole serve surface as one text, for a source-level assertion.

    Concatenated with a newline between files. This guarantees only that a
    SINGLE-newline literal cannot match across a boundary that does not exist
    in any real file — each file already ends in its own trailing newline, so
    the join places TWO newlines between files, and a pattern containing a
    blank line (two consecutive newlines) can still match spuriously across a
    boundary. No assertion over this surface currently uses such a pattern.
    """
    return "\n".join(path.read_text(encoding="utf-8")
                     for path in serve_surface_paths())


FORBIDDEN_PUSH_TOKENS: tuple[str, ...] = (".push(", "open_or_update(", "git push")


# `claim_conftest_slot` re-installs THIS module as the ambient `conftest` for
# nodes under this directory only, so a multi-directory invocation
# (`pytest tests/doc-health tests/ideation-dashboard`) no longer depends on
# argument order — see its docstring in `tests/hermeticity.py` for the
# mechanism, and never add the call to `tests/conftest.py` (issue #305).
claim_conftest_slot(globals())


# ---------------------------------------------------------------------------
# § 4.4: the REGISTERED domain profile, and the way to take it away again.
#
# The registration itself is made at process start by the repository-root
# `conftest.py` — the host contract, exercised rather than simulated. This
# fixture is for the tests that must see the OTHER side of it: `current()`
# refusing when nothing is registered. It removes the registration for the
# duration of one test and puts it back, so no test can leave the suite without
# the words every other test needs.
import pytest as _pytest  # noqa: E402

from openxdox import domain_profile as _domain_profile  # noqa: E402


@_pytest.fixture()
def unregistered_profile():
    """Run one test with NO domain profile registered, then restore it."""
    previous = _domain_profile.current() if _domain_profile.is_registered() else None
    _domain_profile.unregister()
    try:
        yield
    finally:
        _domain_profile.unregister()
        if previous is not None:
            _domain_profile.register(previous)


# ---------------------------------------------------------------------------
# THE HOME CORPUS, REGISTERED AS openxFactory'S HOST REGISTERS IT (plan 034
# T059; holder's ruling on T059, 2026-09-30).
#
# openDox's `authoring.create_scaffold` asks the registered home corpus which
# fields it obliges (`scaffold_lead_fields()`, openDox-code#57, plan 034 T054),
# and with nothing registered it refuses, as #1144's 4.1a has every seam do:
# "A process in which no entry point was built and nothing registered anything
# — an import, a test, a library caller — still refuses with 4.2's
# ADAPTER_NOT_REGISTERED, so the default is a registration the entry point
# makes and never a fallback inside the seam." This leg's governed suites call
# the gate verbs in-process, as a library caller, so from that pin they refused
# on the home corpus where they passed before.
#
# So this harness registers the home a host would, as the root `conftest.py`
# registers the profile a host would: the SAME factory openxFactory's host
# registers (`corpus_adapter_openxfactory.home_corpus`, through
# `scripts/opendox_host.register_seams()`). It is found where F5.2's
# environment composes openxFactory's `scripts/` on `PYTHONPATH` (T007 batch G,
# R1Q23 (a)). The governed layout the suites were written against is that
# adapter's answer: it obliges neither `title` nor `summary`, so a scaffold
# keeps its H1 first.
#
# WHERE IT IS ABSENT, NOTHING IS REGISTERED. A lone checkout carries no
# openxFactory `scripts/`, and there the suites refuse as 4.1a says, which is
# the right answer. Every suite that reaches the home corpus also reaches
# `doc_health`, so each is in the declared exclusion already
# (`tests/declared_exclusion.yaml`), and its evidence is unchanged. Only a
# missing `corpus_adapter_openxfactory` itself means "absent": a present one
# that cannot be imported fails here, loudly.
#
# THE SUITES KEEP READING WHAT THIS CHECKOUT RESOLVES. openxFactory's adapter
# puts its own pinned openDox leg's `src/` FIRST on `sys.path` when it is
# imported (`corpus_adapter_openxfactory/adapter.py`), because that is how
# openxFactory consumes the interface. `opendox` itself is already imported by
# then, from the installed distribution, so its modules keep coming from there.
# The two top-level modules beside it, `route_extension` and
# `subcommand_extension`, are not imported yet, and a later import would have
# found the aggregation's pinned copies ahead of the ones this checkout's own
# path finds (`src/`, then the installed openDox). So both are imported first,
# from there.
import route_extension  # noqa: E402,F401
import subcommand_extension  # noqa: E402,F401

try:
    import corpus_adapter_openxfactory as _openxfactory_corpus  # noqa: E402
except ModuleNotFoundError as _absent:
    if _absent.name != "corpus_adapter_openxfactory":
        raise
    _openxfactory_corpus = None

if _openxfactory_corpus is not None:
    from opendox import corpus_adapter as _corpus_adapter  # noqa: E402

    _corpus_adapter.register_home(_openxfactory_corpus.home_corpus)


# ---------------------------------------------------------------------------
# THE LAUNCH SUITE'S INSTALL (plan 034 T086; the holder's ruling on T086's
# question Q4 (a), 2026-10-02).
#
# From openDox-code's T070 an install is HOSTED unless local is selected, and a
# hosted install with no identity broker refuses. From T072 a local
# `generate-and-open` starts its bundled PostgreSQL before it serves, even
# with `--no-serve`, and the database arrives only with the `local` extra,
# which this leg does not install. `tests/test_snapshot_validation_launch.py`
# drives that verb to prove where the snapshot's validator comes from, which
# neither the install mode nor the database decides. So for that suite alone
# this selects the local install, scrubs every runtime setting the shell may
# carry (a broker setting beside the local mode is refused by design), and
# stands the bundled server in, as openDox-code's own entry-point suites do
# (its `tests/test_doxbench_entrypoint.py`). The suite is one of F5.2's
# protected suites, and its premise lives here so that none of its bytes
# changes.
#
# TWO SHAPES OF PINNED openDox, and only two. Before T070 and T072 the leg has
# no install mode and no bundle (`opendox.cli` carries no `bundle_mod`), and
# this changes nothing. From them on it carries both. A leg carrying one and
# not the other is between those landings, and is refused.
# ---------------------------------------------------------------------------

_LAUNCH_SUITE = "test_snapshot_validation_launch.py"


@_pytest.fixture(autouse=True)
def _the_launch_suite_runs_a_local_install(request, monkeypatch):
    if request.node.path.name != _LAUNCH_SUITE:
        yield
        return
    from opendox import cli as _cli
    from opendox.runtime import config as _config

    has_bundle = hasattr(_cli, "bundle_mod")
    has_mode = hasattr(_config, "INSTALL_MODE_LOCAL")
    assert has_bundle == has_mode, (
        f"the pinned openDox carries {'a bundle' if has_bundle else 'no bundle'} "
        f"and {'an install mode' if has_mode else 'no install mode'}: T070 and "
        "T072 arrive together at every pin this leg takes, so this is neither "
        "shape the launch suite's premise knows")
    if not has_bundle:
        yield
        return
    for name in _config.SETTING_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(_config.PREFIX + "INSTALL_MODE", _config.INSTALL_MODE_LOCAL)
    # A scratch state directory, never the operator's own: a local install
    # keeps its bundle there (T072), and openDox's per-machine binding trust
    # its record (T100), so no case may read or write the real one.
    state_dir = request.getfixturevalue("tmp_path_factory").mktemp("opendox-state")
    monkeypatch.setenv(_config.PREFIX + "STATE_DIR", str(state_dir))

    class _StandInBundle:
        """The bundled PostgreSQL, stood in: the launch reads nothing from it."""

        applied: list = []

        def __init__(self, settings):
            assert settings.install_mode == _config.INSTALL_MODE_LOCAL
            assert Path(settings.state_dir) == state_dir

        def start(self):
            return self

        def stop(self):
            pass

        def report(self):
            return {"data_dir": None, "socket_dir": "(stood in)", "pid": None}

    monkeypatch.setattr(_cli.bundle_mod, "BundledServer", _StandInBundle)
    yield
