"""`scripts/composed_placements.py`, held in CI (plan 038 T022, U-3; option (a)
of the holder's ruling on opensoft/openxFactory#656, comment 6016356225).

WHY HERE. The script makes links in this checkout's working tree for a
composed run, and refuses (exit 2) whatever would let that run read anything
but the pinned document, or overwrite or take away anything but its own link.
A script that changes the file system keeps its guards in the suite CI runs,
so each guard below is a case.

HOW. Each case runs the script as the composed run calls it: in a child
interpreter, against a scratch openxFactory tree whose openDox root pins
commit A of a scratch spec repository, where commit B changes the runbook.
The script it runs is a COPY of this checkout's script, inside a scratch
checkout that also carries a copy of this checkout's own `.gitignore`. The
script places relative to its own location, so no case writes into this
checkout. And the `.gitignore` the cases read is the one this checkout
commits, so a placement it stops ignoring turns the first case red.

The standard library, `git` and pytest are all it needs; no case skips.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

CHECKOUT = Path(__file__).resolve().parents[1]
SCRIPT = Path("scripts") / "composed_placements.py"

#: The one placement: openDox-spec's session runbook, at the same path here.
RUNBOOK = "docs/ideation-dashboard-session-runbook.md"


def _environment(**overrides: str) -> dict[str, str]:
    """The child's environment: no inherited `GIT_*` (a hook's `GIT_DIR`
    would aim every call at another repository), no user or system git
    configuration, and a fixed identity for the scratch commits."""
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("GIT_")}
    environment.update(
        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="composed placements", GIT_AUTHOR_EMAIL="cases@invalid",
        GIT_COMMITTER_NAME="composed placements",
        GIT_COMMITTER_EMAIL="cases@invalid")
    environment.update(overrides)
    return environment


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, env=_environment(),
                          check=True, capture_output=True, text=True).stdout.strip()


@dataclass
class Composed:
    """The scratch checkout, the scratch composed tree, and the script."""

    checkout: Path
    openxfactory: Path
    root: Path
    spec: Path

    @property
    def destination(self) -> Path:
        return self.checkout / RUNBOOK

    @property
    def source(self) -> Path:
        return self.spec / RUNBOOK

    @property
    def pinned(self) -> str:
        return _git("rev-parse", "HEAD:spec", cwd=self.root)

    def run(self, *extra: str, **environment: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.checkout / SCRIPT),
             "--openxfactory", str(self.openxfactory), *extra],
            capture_output=True, text=True, env=_environment(**environment))

    def refused(self, *extra: str, **environment: str) -> str:
        """Run the script, hold it to a refusal, and answer what it said."""
        result = self.run(*extra, **environment)
        assert result.returncode == 2, (result.returncode, result.stdout,
                                        result.stderr)
        assert result.stdout == "", result.stdout
        assert result.stderr.startswith("composed_placements: refused: "), \
            result.stderr
        return result.stderr


def _spec_repository(spec: Path) -> str:
    """A spec repository whose commit A holds runbook A and whose commit B
    changes it; checked out at A. Answers A."""
    spec.mkdir(parents=True)
    _git("init", "-q", cwd=spec)
    (spec / RUNBOOK).parent.mkdir(parents=True)
    (spec / RUNBOOK).write_text("runbook A\n", encoding="utf-8")
    _git("add", RUNBOOK, cwd=spec)
    _git("commit", "-q", "-m", "A", cwd=spec)
    commit_a = _git("rev-parse", "HEAD", cwd=spec)
    (spec / RUNBOOK).write_text("runbook B\n", encoding="utf-8")
    _git("commit", "-q", "-a", "-m", "B", cwd=spec)
    _git("checkout", "-q", commit_a, cwd=spec)
    return commit_a


def _opendox_root(root: Path, pinned: str) -> None:
    """An openDox root whose `spec` gitlink pins `pinned`."""
    root.mkdir(parents=True, exist_ok=True)
    _git("init", "-q", cwd=root)
    _git("update-index", "--add", "--cacheinfo", f"160000,{pinned},spec",
         cwd=root)
    _git("commit", "-q", "-m", "the openDox root", cwd=root)


@pytest.fixture
def composed(tmp_path: Path) -> Composed:
    checkout = tmp_path / "openXdox-code"
    (checkout / SCRIPT).parent.mkdir(parents=True)
    shutil.copyfile(CHECKOUT / SCRIPT, checkout / SCRIPT)
    shutil.copyfile(CHECKOUT / ".gitignore", checkout / ".gitignore")
    _git("init", "-q", cwd=checkout)
    _git("add", ".gitignore", str(SCRIPT), cwd=checkout)
    _git("commit", "-q", "-m", "the scratch checkout", cwd=checkout)
    openxfactory = tmp_path / "openxFactory"
    root = openxfactory / "openDox"
    spec = root / "spec"
    _opendox_root(root, _spec_repository(spec))
    return Composed(checkout, openxfactory, root, spec)


# --- what it places -------------------------------------------------------


def test_a_pinned_unmodified_runbook_is_linked_and_leaves_the_checkout_clean(
        composed):
    result = composed.run()
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"composed_placements: placed {RUNBOOK} -> " \
                            f"{composed.source.resolve()}\n"
    assert composed.destination.is_symlink()
    assert Path(os.readlink(composed.destination)) == composed.source.resolve()
    assert composed.destination.read_text(encoding="utf-8") == "runbook A\n"
    # Ignored by the checkout's own `.gitignore`: nothing placed can be committed.
    assert _git("status", "--porcelain", "--untracked-files=all",
                cwd=composed.checkout) == ""


def test_placing_again_is_a_no_op(composed):
    assert composed.run().returncode == 0
    result = composed.run()
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(f"composed_placements: already placed {RUNBOOK}")
    assert composed.destination.read_text(encoding="utf-8") == "runbook A\n"


def test_remove_takes_back_its_own_link_and_nothing_else(composed):
    assert composed.run().returncode == 0
    result = composed.run("--remove")
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"composed_placements: removed {RUNBOOK}\n"
    assert not os.path.lexists(composed.destination)
    assert composed.source.read_text(encoding="utf-8") == "runbook A\n"
    # And with nothing placed, there is nothing to take back.
    again = composed.run("--remove")
    assert (again.returncode, again.stdout) == (0, ""), again.stderr


# --- what it refuses, placing nothing --------------------------------------


def test_a_spec_checkout_off_the_opendox_roots_pin_is_refused(composed):
    _git("checkout", "-q", "-", cwd=composed.spec)  # commit B
    said = composed.refused()
    assert f"and the openDox root pins {composed.pinned}" in said
    assert "git submodule update --init --recursive" in said
    assert not os.path.lexists(composed.destination)


def test_a_modified_runbook_is_refused(composed):
    composed.source.write_text("edited in the working tree\n", encoding="utf-8")
    said = composed.refused()
    assert "differs from openDox-spec's pinned commit" in said
    assert not os.path.lexists(composed.destination)


def test_a_runbook_the_spec_does_not_track_is_refused(composed):
    _git("rm", "-q", "--cached", RUNBOOK, cwd=composed.spec)
    said = composed.refused()
    assert f"openDox-spec does not track {RUNBOOK}" in said
    assert not os.path.lexists(composed.destination)


def test_an_uninitialized_spec_leg_is_refused_as_not_checked_out(composed):
    # What a composed checkout without `--recursive` holds: an empty directory,
    # where git would answer for the openDox root above it.
    shutil.rmtree(composed.spec)
    composed.spec.mkdir()
    said = composed.refused()
    assert "is not checked out" in said
    assert "git submodule update --init --recursive" in said
    assert not os.path.lexists(composed.destination)


def test_an_uninitialized_opendox_root_is_refused(composed):
    shutil.rmtree(composed.root)
    composed.root.mkdir()
    # An openxFactory checkout above it, whose own tree has no `spec`.
    _git("init", "-q", cwd=composed.openxfactory)
    (composed.openxfactory / "README.md").write_text("openxFactory\n", encoding="utf-8")
    _git("add", "README.md", cwd=composed.openxfactory)
    _git("commit", "-q", "-m", "openxFactory", cwd=composed.openxfactory)
    said = composed.refused()
    assert "is not an openDox root checkout with a `spec` gitlink" in said
    assert not os.path.lexists(composed.destination)


def _drop_the_gitignore_line(composed: Composed) -> None:
    gitignore = composed.checkout / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert f"/{RUNBOOK}\n" in text, "this checkout's .gitignore names the runbook"
    gitignore.write_text(text.replace(f"/{RUNBOOK}\n", ""), encoding="utf-8")


def _exclude_locally(composed: Composed, where: str, tmp_path: Path) -> None:
    """Name the runbook in a local exclude, which no other checkout carries."""
    if where == "info/exclude":
        exclude = composed.checkout / ".git" / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a", encoding="utf-8") as handle:
            handle.write(f"/{RUNBOOK}\n")
    else:
        excludes = tmp_path / "excludes"
        excludes.write_text(f"/{RUNBOOK}\n", encoding="utf-8")
        _git("config", "core.excludesFile", str(excludes), cwd=composed.checkout)


def test_a_destination_the_gitignore_does_not_name_is_refused(composed):
    _drop_the_gitignore_line(composed)
    said = composed.refused()
    assert "is not ignored by this checkout's .gitignore" in said
    assert not os.path.lexists(composed.destination)


@pytest.mark.parametrize("where", ["info/exclude", "core.excludesFile"])
def test_a_destination_only_a_local_exclude_names_is_refused(composed, tmp_path,
                                                             where):
    # Copilot r4196244480; the holder's ruling on opensoft/openxFactory#656,
    # comment 6026275158, item 2: the root .gitignore must be the source.
    _drop_the_gitignore_line(composed)
    _exclude_locally(composed, where, tmp_path)
    said = composed.refused()
    assert "a local exclude that no other checkout carries" in said
    assert not os.path.lexists(composed.destination)


def test_a_local_exclude_beside_the_gitignore_line_still_places(composed,
                                                                 tmp_path):
    # The root .gitignore outranks a local exclude, so it stays the source.
    _exclude_locally(composed, "info/exclude", tmp_path)
    result = composed.run()
    assert result.returncode == 0, result.stderr
    assert composed.destination.is_symlink()


def test_a_gitignore_that_negates_the_destination_is_refused(composed):
    # `git check-ignore -v` exits 0 for a negated pattern too.
    with (composed.checkout / ".gitignore").open("a", encoding="utf-8") as handle:
        handle.write(f"!/{RUNBOOK}\n")
    said = composed.refused()
    assert "is not ignored by this checkout's .gitignore" in said
    assert not os.path.lexists(composed.destination)


def test_without_git_on_path_it_refuses(composed, tmp_path):
    nothing = tmp_path / "an-empty-PATH"
    nothing.mkdir()
    said = composed.refused(PATH=str(nothing))
    assert "git is not on PATH" in said
    assert not os.path.lexists(composed.destination)


@pytest.mark.parametrize("edited", [False, True], ids=["clean", "edited"])
def test_ambient_git_repository_variables_do_not_redirect_the_checks(
        composed, tmp_path, edited):
    # Copilot r4200975244: git sets GIT_DIR and GIT_WORK_TREE for every hook,
    # and honours them over the directory each check runs in. Pointed at a
    # decoy repository, they must change nothing.
    decoy = tmp_path / "decoy"
    decoy.mkdir()
    _git("init", "-q", cwd=decoy)
    (decoy / "README.md").write_text("decoy\n", encoding="utf-8")
    _git("add", "README.md", cwd=decoy)
    _git("commit", "-q", "-m", "decoy", cwd=decoy)
    ambient = {"GIT_DIR": str(decoy / ".git"), "GIT_WORK_TREE": str(decoy),
               "GIT_INDEX_FILE": str(decoy / ".git" / "index")}
    if edited:
        composed.source.write_text("edited in the working tree\n",
                                   encoding="utf-8")
        said = composed.refused(**ambient)
        assert "differs from openDox-spec's pinned commit" in said
        assert not os.path.lexists(composed.destination)
    else:
        result = composed.run(**ambient)
        assert result.returncode == 0, result.stderr
        assert composed.destination.read_text(encoding="utf-8") == "runbook A\n"


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_an_edit_the_index_is_told_to_overlook_is_refused(composed, flag):
    # Copilot r4201032934: with either flag `git diff` calls the file clean
    # without reading it. The check compares the bytes with the pinned blob.
    _git("update-index", flag, RUNBOOK, cwd=composed.spec)
    composed.source.write_text("edited in the working tree\n", encoding="utf-8")
    said = composed.refused()
    assert "differs from openDox-spec's pinned commit" in said
    assert not os.path.lexists(composed.destination)


def _pin(composed: Composed, commit: str) -> None:
    """Move the openDox root's `spec` gitlink to `commit`, and check it out."""
    _git("checkout", "-q", commit, cwd=composed.spec)
    _git("update-index", "--cacheinfo", f"160000,{commit},spec", cwd=composed.root)
    _git("commit", "-q", "-m", "pin", cwd=composed.root)


def test_a_runbook_the_pinned_commit_tracks_as_a_link_is_refused(composed):
    # Copilot r4201424060: the pinned "document" is a link to a file whose
    # bytes `git diff` on the link never reads.
    real = composed.spec / "docs" / "real-runbook.md"
    real.write_text("runbook A\n", encoding="utf-8")
    composed.source.unlink()
    composed.source.symlink_to("real-runbook.md")
    _git("add", "-A", "docs", cwd=composed.spec)
    _git("commit", "-q", "-m", "the runbook as a link", cwd=composed.spec)
    _pin(composed, _git("rev-parse", "HEAD", cwd=composed.spec))
    real.write_text("edited behind the link\n", encoding="utf-8")
    said = composed.refused()
    assert "is a symbolic link" in said
    assert not os.path.lexists(composed.destination)


def test_a_runbook_replaced_by_a_link_to_identical_bytes_is_refused(composed,
                                                                    tmp_path):
    # Identical bytes today; a link can be repointed after the check.
    copy = tmp_path / "identical-runbook.md"
    copy.write_text("runbook A\n", encoding="utf-8")
    composed.source.unlink()
    composed.source.symlink_to(copy)
    said = composed.refused()
    assert "is a symbolic link" in said
    assert not os.path.lexists(composed.destination)


def test_an_opendox_root_answered_by_an_enclosing_repository_is_refused(
        composed):
    # Copilot r4201032886: without its own repository, git would answer
    # `HEAD:spec` from the repository above, if its tree had a `spec` entry.
    pinned = composed.pinned
    shutil.rmtree(composed.root / ".git")
    _git("init", "-q", cwd=composed.openxfactory)
    _git("update-index", "--add", "--cacheinfo", f"160000,{pinned},spec",
         cwd=composed.openxfactory)
    _git("commit", "-q", "-m", "an enclosing repository", cwd=composed.openxfactory)
    said = composed.refused()
    assert "is not an openDox root checkout with a `spec` gitlink" in said
    assert not os.path.lexists(composed.destination)


def test_an_opendox_root_without_a_spec_gitlink_is_refused(composed):
    _git("rm", "-q", "--cached", "spec", cwd=composed.root)
    _git("commit", "-q", "-m", "no spec leg", cwd=composed.root)
    said = composed.refused()
    assert "is not an openDox root checkout with a `spec` gitlink" in said
    assert not os.path.lexists(composed.destination)


def test_a_spec_leg_whose_work_tree_is_configured_elsewhere_is_refused(
        composed, tmp_path):
    # Copilot r4201032886: `core.worktree` points the checks at another tree.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    _git("config", "core.worktree", str(elsewhere), cwd=composed.spec)
    said = composed.refused()
    assert "is not checked out" in said
    assert not os.path.lexists(composed.destination)


# --- what it never overwrites or takes away ---------------------------------


def _a_file_of_someone_elses(composed: Composed) -> None:
    composed.destination.parent.mkdir(parents=True)
    composed.destination.write_text("someone's own file\n", encoding="utf-8")


def _a_link_elsewhere(composed: Composed, tmp_path: Path) -> Path:
    elsewhere = tmp_path / "another-runbook.md"
    elsewhere.write_text("another runbook\n", encoding="utf-8")
    composed.destination.parent.mkdir(parents=True)
    composed.destination.symlink_to(elsewhere)
    return elsewhere


@pytest.mark.parametrize("verb", [(), ("--remove",)], ids=["place", "remove"])
def test_a_file_at_the_destination_is_refused_and_kept(composed, verb):
    _a_file_of_someone_elses(composed)
    said = composed.refused(*verb)
    assert ("is not this script's link, so it is not removed" if verb
            else "already exists and is not this script's link") in said
    assert not composed.destination.is_symlink()
    assert composed.destination.read_text(encoding="utf-8") == "someone's own file\n"


@pytest.mark.parametrize("verb", [(), ("--remove",)], ids=["place", "remove"])
def test_a_link_elsewhere_at_the_destination_is_refused_and_kept(composed,
                                                                tmp_path, verb):
    elsewhere = _a_link_elsewhere(composed, tmp_path)
    said = composed.refused(*verb)
    assert ("is not this script's link, so it is not removed" if verb
            else "already exists and is not this script's link") in said
    assert Path(os.readlink(composed.destination)) == elsewhere
