"""openXdox's governed projection is what openDox's seams hold (plan 034 T059).

T059's falsifier opens with "seam tests that show openXdox's contributions are
the registered ones". These are they. Each seam holds openXdox's own
contribution once `projection_contributions.register()` has run: the governed
generator, this leg's snapshot registry, its corpus-root predicate, its writer,
and its validator for openXdox-spec's three kinds. openDox's own kinds keep
openDox's validator.

The rest pin the registration's contract: it is idempotent, all or none, made
by `domain_profile.register()` and never by `domain_profile.load()`, and
import-free of `doc_health`, so a lone checkout registers and fails only where
a governed generation runs.

This leg's root `conftest.py` registers the fixture profile at import, and so
the contributions. A case that empties a seam runs inside `isolated_seams`,
which puts the contributions back afterwards.

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from opendox import generator_seam, projection_seams
from openxdox import domain_profile, projection_contributions as pc
from openxdox import snapshot as snapshot_mod
from openxdox import snapshot_registry

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
PROFILE_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "openxfactory-engineering-profile.yaml"


def _empty_every_seam() -> None:
    generator_seam.unregister()
    projection_seams.registry.unregister()
    projection_seams.corpus_root.unregister()
    projection_seams.writer.unregister()
    projection_seams.validators.unregister()


@pytest.fixture
def isolated_seams():
    """Run one case with every seam empty, then put the contributions back.

    openDox's entry points register their own defaults again wherever nothing
    is registered, so a later case that runs one gets them as before."""
    _empty_every_seam()
    try:
        yield
    finally:
        _empty_every_seam()
        pc.register()


def _registered_profile():
    return domain_profile.current() if domain_profile.is_registered() else None


# --------------------------------------------------------------------------
# the registered ones
# --------------------------------------------------------------------------

def test_each_seam_holds_openxdoxs_contribution() -> None:
    """The process this suite runs in registered the fixture profile at
    import, so every seam holds openXdox's own, and nothing else."""
    assert pc.is_registered()
    assert generator_seam.current() is pc.GENERATOR
    assert projection_seams.registry.current() is snapshot_registry
    assert projection_seams.corpus_root.current() is pc.CORPUS_ROOT
    assert projection_seams.writer.current() is snapshot_mod
    for kind in pc.GOVERNED_KINDS:
        assert projection_seams.validators.for_kind(kind) is pc.VALIDATOR


def test_the_generator_is_the_governed_one_declaring_its_two_inputs() -> None:
    assert pc.GENERATOR.contract == "ideation-dashboard-snapshot"
    assert pc.GENERATOR.inputs == ("project_register_source", "possibles_source")
    assert pc.GOVERNED_KINDS == ("ideation-dashboard-snapshot",
                                 "ideation-dashboard-snapshot-index",
                                 "gate-action-record")


def test_the_generator_hands_the_seams_call_to_generate_snapshot(monkeypatch) -> None:
    """Every argument the seam passes reaches `generate_snapshot` unchanged,
    and nothing else does."""
    calls = []

    class Generator:
        @staticmethod
        def generate_snapshot(*args, **kwargs):
            calls.append((args, kwargs))
            return {"kind": "ideation-dashboard-snapshot", "schema_version": 1}

    monkeypatch.setattr(pc, "_governed",
                        lambda name: Generator if name == "generator" else None)
    answered = generator_seam.generate(
        Path("/corpus"), "repo", source_revision="a" * 40,
        generated_at="2026-09-30T00:00:00Z",
        project_register_source=Path("/register.yaml"))
    assert answered == {"kind": "ideation-dashboard-snapshot", "schema_version": 1}
    assert calls == [((Path("/corpus"), "repo"), {
        "source_revision": "a" * 40, "generated_at": "2026-09-30T00:00:00Z",
        "project_register_source": Path("/register.yaml"),
        "possibles_source": None})]


def test_openDoxs_own_kinds_keep_openDoxs_validator(isolated_seams) -> None:
    """The entry points' defaults land on openDox's kinds, and none of ours."""
    pc.register()
    projection_seams.register_defaults()
    from opendox import default_projection

    # openDox-code 047bb4fa (plan 034 T058) registers one validator per own
    # kind, `default_projection.VALIDATORS[kind]`, where 814516b7 had one
    # stand-in, `VALIDATOR`, for all of them.
    for kind in default_projection.OWN_KINDS:
        assert projection_seams.validators.for_kind(kind) is default_projection.VALIDATORS[kind]
    for kind in pc.GOVERNED_KINDS:
        assert projection_seams.validators.for_kind(kind) is pc.VALIDATOR
    assert projection_seams.registry.current() is snapshot_registry


def test_the_entry_points_defaults_do_not_displace_it(isolated_seams) -> None:
    pc.register()
    projection_seams.register_defaults()
    from opendox import default_generator

    generator_seam.register_default(default_generator.GENERATOR)
    assert pc.is_registered()


# --------------------------------------------------------------------------
# idempotent, and all or none
# --------------------------------------------------------------------------

def test_a_second_registration_is_a_no_op() -> None:
    names = pc.register()
    assert names == pc.register()
    assert pc.is_registered()


def test_a_refusal_takes_back_every_seam_this_call_wrote(isolated_seams) -> None:
    """A host's other writer is registered, so the writer seam refuses. The
    generator, registry and corpus-root seams, written before it, are empty
    again, and the host's writer is untouched."""

    class OtherWriter:
        @staticmethod
        def write_snapshot(snapshot, path, boundary):  # pragma: no cover
            raise AssertionError("never called")

    other = OtherWriter()
    projection_seams.writer.register(other)
    with pytest.raises(projection_seams.SeamAlreadyRegistered):
        pc.register()
    assert not generator_seam.is_registered()
    assert not projection_seams.registry.is_registered()
    assert not projection_seams.corpus_root.is_registered()
    assert projection_seams.writer.current() is other
    assert projection_seams.validators.kinds() == ()


def test_a_replaced_unread_default_is_given_back_as_a_default(isolated_seams) -> None:
    """The entry points registered their defaults, and something read the
    writer's. This call replaces the unread defaults before the writer
    refuses. It gives each one back as the unread default it was (Copilot on
    openXdox-code#35), so a caller that catches the refusal keeps its neutral
    generator, registry and corpus root. No seam is left governed while the
    writer stays neutral, and none is left empty either."""
    from opendox import default_generator, default_projection, default_registry

    generator_seam.register_default(default_generator.GENERATOR)
    projection_seams.register_defaults()
    registry_default = projection_seams.registry._registered
    corpus_root_default = projection_seams.corpus_root._registered
    assert projection_seams.writer.current() is default_projection.WRITER  # read
    with pytest.raises(projection_seams.SeamAlreadyRegistered):
        pc.register()
    # each is back, and still an unread default: the names are pinned here
    assert generator_seam._registered is default_generator.GENERATOR
    assert generator_seam._is_default
    assert projection_seams.registry._registered is registry_default is default_registry
    assert projection_seams.registry._is_default
    assert projection_seams.corpus_root._registered is corpus_root_default
    assert projection_seams.corpus_root._is_default
    assert projection_seams.writer.current() is default_projection.WRITER
    # and replaceable still: once the writer's reader lets go, this call lands
    projection_seams.writer.unregister()
    pc.register()
    assert pc.is_registered()


def test_a_seam_already_holding_the_contribution_is_not_taken_back(isolated_seams) -> None:
    """The registry already held this leg's module, so this call did not write
    it, and a refusal later leaves it where it was."""

    class OtherWriter:
        @staticmethod
        def write_snapshot(snapshot, path, boundary):  # pragma: no cover
            raise AssertionError("never called")

    projection_seams.registry.register(snapshot_registry)
    projection_seams.writer.register(OtherWriter())
    with pytest.raises(projection_seams.SeamAlreadyRegistered):
        pc.register()
    assert projection_seams.registry.current() is snapshot_registry
    assert not generator_seam.is_registered()


def test_asking_whether_it_is_registered_leaves_a_default_replaceable(isolated_seams) -> None:
    """`is_registered()` reads each projection seam where it keeps its
    registration, because `current()` would close the default's window. So a
    default asked about stays replaceable, and the names read are pinned
    here: a pin move that renamed them fails this case."""
    projection_seams.register_defaults()
    assert not pc.is_registered()
    assert hasattr(projection_seams.registry, "_registered")
    assert isinstance(projection_seams.validators._registered, dict)
    pc.register()
    assert pc.is_registered()


def test_unregister_empties_only_what_it_holds(isolated_seams) -> None:
    pc.register()
    from opendox import default_projection

    projection_seams.validators.register_default(
        "opendox-snapshot", default_projection.VALIDATORS["opendox-snapshot"])
    pc.unregister()
    assert not generator_seam.is_registered()
    assert not projection_seams.writer.is_registered()
    assert projection_seams.validators.kinds() == ("opendox-snapshot",)


# --------------------------------------------------------------------------
# who registers it
# --------------------------------------------------------------------------

def test_registering_openxdoxs_profile_registers_the_contributions(isolated_seams) -> None:
    held = _registered_profile()
    domain_profile.unregister()
    try:
        domain_profile.register(domain_profile.load(PROFILE_FIXTURE))
        assert pc.is_registered()
    finally:
        domain_profile.unregister()
        if held is not None:
            domain_profile.register(held)


def test_unregistering_the_profile_leaves_the_contributions(isolated_seams) -> None:
    """The profile's teardown drops the profile only. The contributions are the
    process's, and a teardown that took them back could not be undone once a
    default had been read (the docstring of `domain_profile.unregister`)."""
    held = _registered_profile()
    domain_profile.unregister()
    try:
        profile = domain_profile.load(PROFILE_FIXTURE)
        domain_profile.register(profile)
        domain_profile.unregister()
        assert not domain_profile.is_registered()
        assert pc.is_registered()
        domain_profile.register(profile)                  # and back, as a fixture does
        assert domain_profile.is_registered()
        pc.unregister()
        assert not pc.is_registered()
    finally:
        domain_profile.unregister()
        if held is not None:
            domain_profile.register(held)


def test_a_refused_contribution_leaves_no_profile_registered(isolated_seams) -> None:
    class OtherWriter:
        @staticmethod
        def write_snapshot(snapshot, path, boundary):  # pragma: no cover
            raise AssertionError("never called")

    held = _registered_profile()
    domain_profile.unregister()
    projection_seams.writer.register(OtherWriter())
    try:
        profile = domain_profile.load(PROFILE_FIXTURE)
        with pytest.raises(projection_seams.SeamAlreadyRegistered):
            domain_profile.register(profile)
        assert not domain_profile.is_registered()
    finally:
        projection_seams.writer.unregister()
        if held is not None:
            domain_profile.register(held)


def test_loading_a_profile_registers_nothing(isolated_seams) -> None:
    domain_profile.load(PROFILE_FIXTURE)
    assert not generator_seam.is_registered()
    assert not projection_seams.registry.is_registered()
    assert projection_seams.validators.kinds() == ()


# --------------------------------------------------------------------------
# resolved at use
# --------------------------------------------------------------------------

_BLOCKED = textwrap.dedent('''
    import importlib.abc, sys

    class Block(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name == "doc_health" or name.startswith("doc_health."):
                raise ModuleNotFoundError(f"No module named {name!r}", name=name)
            return None

    sys.meta_path.insert(0, Block())
''')


def _run_blocked(body: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    return subprocess.run(
        [sys.executable, "-c", _BLOCKED + textwrap.dedent(body)],
        capture_output=True, text=True, env=env, cwd=str(REPO_ROOT))


def test_registering_reaches_no_module_that_needs_doc_health() -> None:
    """With `doc_health` unimportable, the registration succeeds and imports
    none of the governed modules that need it."""
    done = _run_blocked('''
        import json, sys
        from openxdox import projection_contributions as pc
        pc.register()
        print(json.dumps({
            "registered": pc.is_registered(),
            "loaded": sorted(m for m in ("openxdox.generator", "openxdox.corpus_root",
                                         "openxdox.completeness", "doc_health")
                             if m in sys.modules)}))
    ''')
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout.splitlines()[-1]) == {"registered": True, "loaded": []}


def test_without_doc_health_a_governed_generation_fails_on_doc_health() -> None:
    """Where it always failed, and with the same final exception, which is
    what the declared exclusion's `doc_health` evidence reads."""
    done = _run_blocked('''
        from pathlib import Path
        from openxdox import projection_contributions as pc
        pc.register()
        from opendox import generator_seam
        try:
            generator_seam.generate(Path("."), "repo")
        except ModuleNotFoundError as exc:
            print("refused:", exc.name)
        else:
            print("generated")
    ''')
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().splitlines()[-1] == "refused: doc_health"


def test_without_doc_health_an_entry_that_carries_its_revision_is_indexed() -> None:
    """`doc_health` is read only for the sentinel an entry with no revision
    gets, so an index of entries that carry theirs is served without it, and
    the sentinel alone still fails on `doc_health` (Copilot on #35)."""
    done = _run_blocked('''
        import json
        from openxdox import snapshot_registry as reg
        versioned = reg.SnapshotEntry(repository="alpha", ref="main", source_revision="a" * 40)
        print(json.dumps(versioned.index_entry()["source_revision"]))
        try:
            reg.SnapshotEntry(repository="beta", ref="main").index_entry()
        except ModuleNotFoundError as exc:
            print("refused:", exc.name)
    ''')
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().splitlines()[-2:] == ['"' + "a" * 40 + '"', "refused: doc_health"]


def test_the_scanned_roots_are_read_when_used(monkeypatch) -> None:
    reads = []

    class CorpusRoot:
        @property
        def SCANNED_ROOTS(self):  # noqa: N802 - the governed module's own name
            reads.append(1)
            return ("docs", "openspec")

    monkeypatch.setattr(pc, "_governed", lambda name: CorpusRoot())
    roots = pc.CORPUS_ROOT.SCANNED_ROOTS
    assert "read when used" in repr(roots)
    assert reads == []
    assert tuple(roots) == ("docs", "openspec")
    assert len(roots) == 2
    assert roots[1] == "openspec"
    assert "docs" in roots


def test_the_change_rows_are_the_governed_enumeration_with_each_origin(monkeypatch) -> None:
    """What `branch_session._change_rows` computed before T055 routed it here."""
    folder = Path("/corpus/openspec/changes/add-x")

    class Generator:
        @staticmethod
        def iter_changes(root):
            assert root == Path("/corpus")
            return [("add-x", "active", folder, None)]

        @staticmethod
        def declared_origin_state(path):
            assert path == folder
            return ("staged", "ideation/staging/x")

    monkeypatch.setattr(pc, "_governed", lambda name: Generator)
    assert projection_seams.corpus_root.current().change_rows("/corpus") == (
        ("add-x", "active", folder, "staged", "ideation/staging/x"),)


# --------------------------------------------------------------------------
# the validator
# --------------------------------------------------------------------------

def test_the_validator_is_the_installed_distributions_own_whatever_the_roots(monkeypatch,
                                                                           tmp_path) -> None:
    """Plan 034 T061 (#1144 7.3): the lookup ignores its start, so the roots
    openDox offers are not read, and the one validator runs."""
    found = tmp_path / "validator.py"
    asked = []

    def find_validator(start=None):
        asked.append(start)
        return found

    ran = []
    monkeypatch.setattr(snapshot_mod, "find_validator", find_validator)
    monkeypatch.setattr(snapshot_mod, "validate_snapshot",
                        lambda path, **kw: ran.append((path, kw)) or "result")
    result = pc.VALIDATOR.validate(tmp_path / "s.json", strict=True,
                                   search_from=(tmp_path / "first", tmp_path / "second"))
    assert result == "result"
    assert asked == [None]
    assert ran == [(tmp_path / "s.json", {"validator": found, "strict": True})]


def test_the_locate_answer_is_snapshots_own(tmp_path) -> None:
    assert pc.VALIDATOR.locate((tmp_path / "anywhere",)) == snapshot_mod.find_validator()


def test_no_validator_of_its_own_is_unavailable_naming_the_script(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(snapshot_mod, "find_validator", lambda start=None: None)
    result = pc.VALIDATOR.validate(tmp_path / "s.json",
                                   search_from=(tmp_path / "a", tmp_path / "b"))
    assert result.outcome == projection_seams.VALIDATOR_UNAVAILABLE
    assert not result.available
    assert result.validator is None
    assert snapshot_mod.VALIDATOR_RELPATH.name in result.unavailable_reason
    assert "never adopted" in result.unavailable_reason
    assert pc.VALIDATOR.dependency_remedy == snapshot_mod.DEPENDENCY_REMEDY
