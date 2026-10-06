#!/usr/bin/env python3
"""Place, for a COMPOSED run, the files this checkout's suites read from the
composed tree (plan 038 T022, U-3; R2Q8 (a); P4F-3, ruled with plan 038 on
opensoft/openxFactory#656 comment 6013547504).

WHY IT EXISTS. 12.5's falsifier runs openxFactory's governed suites in this
checkout, composed: openxFactory checked out with its submodules initialized
recursively, and its `scripts/` on `PYTHONPATH` (R1Q23 (a)). Two of those
suites read the session runbook at this checkout's
`docs/ideation-dashboard-session-runbook.md`, which is where it sat before the
carve: `tests/test_session_runbook.py` (its module constant `RUNBOOK`) and
`tests/test_session_notebook.py` (inline). The carve sent the runbook to
openDox-spec (`docs/opendox-carve-manifest.yaml`, in openxFactory), and this
checkout carries none. Neither suite may be edited outside an allow-list
entry, and a module constant lies inside no test.

WHY A PLACEMENT AND NOT A COPY. openXdox-code's copy record
(`src/openxdox/contracts/copies.yaml`) is single-source: openXdox-spec, at one
commit, and the consumer validator's three kinds. An openDox-spec document
cannot be a row in it, and a second copy of it here would be one more copy to
keep in step. So the runbook is LINKED, for the run, from the composed tree,
where it is openDox-spec's own file at the commit the openDox root pins. The
placed path is in `.gitignore`, so the checkout stays clean and nothing placed
can be committed.

WHAT IT CHECKS BEFORE IT PLACES ANYTHING, refusing (exit 2) and naming the
remedy otherwise:
  * each source is a regular file (not a link) openDox-spec TRACKS whose
    bytes are the pinned blob, in a spec checkout whose HEAD is the commit
    the openDox root's `spec` gitlink names, each answered by its own
    repository and work tree. So the run reads the pinned document, and not
    whatever a working tree or an index flag says;
  * each destination is ignored by this checkout's own `.gitignore`, not
    only by a local exclude (`.git/info/exclude`, `core.excludesFile`);
  * a destination already present is this script's own link to that same
    source. Anything else there is refused, never overwritten.
It places all or nothing: every check passes before the first link is made.

USAGE, from anywhere:

    python3 scripts/composed_placements.py --openxfactory "$OPENXFACTORY"
    python3 scripts/composed_placements.py --openxfactory "$OPENXFACTORY" --remove

`--remove` takes back this script's own links and nothing else. The composed
workflow (T029) and the documented local composed run both call it before
they run the suites. The standard library and `git` are all it needs.

A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

CHECKOUT = Path(__file__).resolve().parents[1]

#: The openDox root inside the openxFactory checkout, and its `spec` leg.
OPENDOX_ROOT = PurePosixPath("openDox")
SPEC_LEG = PurePosixPath("spec")


@dataclass(frozen=True)
class Placement:
    """One file the composed run places: `source`, a path inside openDox-spec,
    linked to `destination`, a path inside this checkout."""

    source: PurePosixPath
    destination: PurePosixPath


#: Every placement, and the only ones. A new one comes with its reader's
#: reason here and its path in `.gitignore`.
PLACEMENTS: tuple[Placement, ...] = (
    # The session runbook: read by tests/test_session_runbook.py (`RUNBOOK`)
    # and tests/test_session_notebook.py, at this checkout's `docs/`.
    Placement(PurePosixPath("docs/ideation-dashboard-session-runbook.md"),
              PurePosixPath("docs/ideation-dashboard-session-runbook.md")),
)


class PlacementRefused(Exception):
    """A placement this script will not make, with the reason and the remedy."""


#: Git variables that select a repository, work tree or index. Git honours
#: them over the directory each check runs in, and it sets `GIT_DIR` and
#: `GIT_WORK_TREE` for every hook it runs, so a hook running this script would
#: point the pin, clean and ignore checks at another repository. They are
#: dropped for every call, as `openxdox.domain_corpus_adapter`'s
#: `AMBIENT_GIT_VARIABLES` drops them (Copilot r4200975244).
AMBIENT_GIT_VARIABLES = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES", "GIT_PREFIX",
)


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    environment = {key: value for key, value in os.environ.items()
                   if key not in AMBIENT_GIT_VARIABLES}
    try:
        return subprocess.run(["git", *args], cwd=cwd, env=environment,
                              capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise PlacementRefused(
            "git is not on PATH, and the placements are checked with it") from exc


def _is_its_own_work_tree(path: Path) -> bool:
    """Git answers for `path` from `path`'s own repository, whose work tree is
    `path`: not from a repository above it (an uninitialized submodule is an
    empty directory) and not from a work tree its configuration puts
    elsewhere (`core.worktree`). As `openxdox.domain_corpus_adapter` checks
    `--show-toplevel` before it trusts a revision (Copilot r4201032886)."""
    if not (path / ".git").exists():
        return False
    top = _git("rev-parse", "--show-toplevel", cwd=path)
    return (top.returncode == 0
            and Path(top.stdout.strip()).resolve() == path.resolve())


def _pinned_spec(openxfactory: Path) -> Path:
    """The spec checkout, once its HEAD is the commit the openDox root pins."""
    root = openxfactory / OPENDOX_ROOT
    spec = root / SPEC_LEG
    pinned = _git("rev-parse", "--verify", f"HEAD:{SPEC_LEG}", cwd=root) \
        if _is_its_own_work_tree(root) else None
    if pinned is None or pinned.returncode != 0:
        raise PlacementRefused(
            f"{root} is not an openDox root checkout with a `spec` gitlink. "
            "Check openxFactory out with its submodules initialized "
            "recursively (`git submodule update --init --recursive`).")
    # Its own work tree: an uninitialized leg is an empty directory, and git
    # would answer for the openDox root above it.
    head = _git("rev-parse", "--verify", "HEAD", cwd=spec) \
        if _is_its_own_work_tree(spec) else None
    if head is None or head.returncode != 0:
        raise PlacementRefused(
            f"{spec} is not checked out. Initialize openxFactory's submodules "
            "recursively (`git submodule update --init --recursive`).")
    if head.stdout.strip() != pinned.stdout.strip():
        raise PlacementRefused(
            f"{spec} is at {head.stdout.strip()}, and the openDox root pins "
            f"{pinned.stdout.strip()}. The run must read the pinned document: "
            "run `git submodule update --init --recursive` in the openxFactory "
            "checkout.")
    return spec


def _check(placement: Placement, spec: Path) -> tuple[Path, Path]:
    """The placement's source and destination, once every check has passed."""
    source = spec / placement.source
    tracked = _git("ls-files", "--error-unmatch", "--", str(placement.source), cwd=spec)
    if tracked.returncode != 0 or not source.is_file():
        raise PlacementRefused(
            f"openDox-spec does not track {placement.source} at its pinned "
            "commit, so there is nothing pinned to place")
    if source.is_symlink():
        raise PlacementRefused(
            f"{source} is a symbolic link. The run links only the regular "
            "file openDox-spec tracks at its pinned commit, whose bytes a link "
            "does not fix (Copilot r4201424060).")
    # The bytes themselves against the pinned blob. `git diff` can call a file
    # clean without reading it, where the index marks it `assume-unchanged` or
    # `skip-worktree` (Copilot r4201032934).
    pinned_blob = _git("rev-parse", "--verify", f"HEAD:{placement.source}",
                       cwd=spec)
    on_disk = _git("hash-object", "--", str(placement.source), cwd=spec)
    if (pinned_blob.returncode != 0 or on_disk.returncode != 0
            or pinned_blob.stdout.strip() != on_disk.stdout.strip()):
        raise PlacementRefused(
            f"{source} differs from openDox-spec's pinned commit. The run must "
            "read the pinned document; restore it with `git checkout -- "
            f"{placement.source}` in {spec}.")
    destination = CHECKOUT / placement.destination
    # Ignored by the repository-root `.gitignore` itself, never by a local
    # exclude (`.git/info/exclude`, `core.excludesFile`), which no other
    # checkout carries. `-v` prints the deciding pattern as
    # `<source>:<line>:<pattern><TAB><path>`, its source relative to the
    # repository root, and exits 0 for a negated (`!`) pattern too.
    verdict = _git("check-ignore", "-v", "--", str(placement.destination),
                   cwd=CHECKOUT)
    ignored_by, _, rest = verdict.stdout.partition(":")
    pattern = rest.partition(":")[2].partition("\t")[0]
    if verdict.returncode != 0 or pattern.startswith("!"):
        raise PlacementRefused(
            f"{placement.destination} is not ignored by this checkout's "
            ".gitignore, so a placed file could be committed. Name it there.")
    if ignored_by != ".gitignore":
        raise PlacementRefused(
            f"{placement.destination} is ignored only by {ignored_by}, a local "
            "exclude that no other checkout carries, and not by this "
            "checkout's .gitignore, so a placed file could be committed "
            "elsewhere. Name it in .gitignore.")
    if os.path.lexists(destination):
        if not (destination.is_symlink()
                and Path(os.readlink(destination)) == source):
            raise PlacementRefused(
                f"{placement.destination} already exists and is not this "
                f"script's link to {source}. It is not overwritten; move it "
                "away first.")
    return source, destination


def place(openxfactory: Path) -> list[str]:
    """Make every placement, all or nothing. Answers what was done."""
    spec = _pinned_spec(openxfactory.resolve())
    checked = [(placement, *_check(placement, spec)) for placement in PLACEMENTS]
    done = []
    for placement, source, destination in checked:
        if destination.is_symlink():
            done.append(f"already placed {placement.destination} -> {source}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(source)
        done.append(f"placed {placement.destination} -> {source}")
    return done


def remove(openxfactory: Path) -> list[str]:
    """Take back this script's own links, and nothing else."""
    spec = openxfactory.resolve() / OPENDOX_ROOT / SPEC_LEG
    done = []
    for placement in PLACEMENTS:
        destination = CHECKOUT / placement.destination
        if not os.path.lexists(destination):
            continue
        if not (destination.is_symlink()
                and Path(os.readlink(destination)) == spec / placement.source):
            raise PlacementRefused(
                f"{placement.destination} is not this script's link, so it "
                "is not removed")
        destination.unlink()
        done.append(f"removed {placement.destination}")
    return done


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Place, for a composed run, the files this checkout's "
                    "suites read from the composed tree (plan 038 T022).")
    parser.add_argument("--openxfactory", required=True, type=Path,
                        help="the openxFactory checkout of the composed run, "
                             "its submodules initialized recursively")
    parser.add_argument("--remove", action="store_true",
                        help="take back this script's own links")
    args = parser.parse_args(argv)
    try:
        done = (remove if args.remove else place)(args.openxfactory)
    except PlacementRefused as exc:
        print(f"composed_placements: refused: {exc}", file=sys.stderr)
        return 2
    for line in done:
        print(f"composed_placements: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
