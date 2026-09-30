"""Four gaps in openXdox's governed registry and writer, closed before they are
registered at openDox's seams (plan 034 T059).

openDox's own defaults closed each of these in openDox-code#59's review
rounds, and #59's body lists them as openXdox-code's to close before T059
registers this leg's mechanisms:

1. `snapshot_registry.resolve_within` met the hidden-name rule only as the URL
   spells a path, so a symlink inside the root led to what the rule refuses by
   name (r4125556296): `link -> .git` served `.git/config`.
2. `SnapshotRegistry.drop` left the active key naming a dropped entry.
3. `snapshot.write_snapshot` wrote in place, so a reader could meet a
   truncated snapshot (r4126138808), and `canonical_json` wrote NaN and
   Infinity, which no JSON reader parses (r4125900060).
4. `SnapshotRegistry` read without its lock, so a reader could answer from the
   middle of a block `atomically()` holds (r4136863481).

Each case below is red against the code before T059.

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import json
import math
import os
import threading
import time
from pathlib import Path

import pytest

from opendox import projection_seams
from opendox.boundary import OutputBoundary
from openxdox import snapshot as snapshot_mod
from openxdox import snapshot_registry as reg


# --------------------------------------------------------------------------
# 1: the hidden-name rule meets the canonical path too
# --------------------------------------------------------------------------

@pytest.fixture
def served_root(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    (root / ".git").mkdir(parents=True)
    (root / ".git" / "config").write_text("[remote]\n", encoding="utf-8")
    (root / ".env").write_text("TOKEN=x\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("# a note\n", encoding="utf-8")
    return root


def test_a_symlink_to_a_dot_directory_serves_nothing(served_root: Path) -> None:
    (served_root / "link").symlink_to(served_root / ".git", target_is_directory=True)
    assert reg.resolve_within(served_root, "link/config") is None


def test_a_symlink_to_a_hidden_file_serves_nothing(served_root: Path) -> None:
    (served_root / "notes.md").symlink_to(served_root / ".env")
    assert reg.resolve_within(served_root, "notes.md") is None


def test_a_symlink_to_a_document_is_still_served(served_root: Path) -> None:
    (served_root / "alias.md").symlink_to(served_root / "docs" / "note.md")
    assert reg.resolve_within(served_root, "alias.md") == (
        served_root / "docs" / "note.md").resolve()
    assert reg.resolve_within(served_root, "docs/note.md") == (
        served_root / "docs" / "note.md").resolve()


def test_the_spelled_rule_still_refuses_first(served_root: Path) -> None:
    assert reg.resolve_within(served_root, ".git/config") is None
    assert reg.resolve_within(served_root, "%2egit/config") is None
    assert reg.resolve_within(served_root, ".env") is None


# --------------------------------------------------------------------------
# 2: dropping the active entry clears the active key
# --------------------------------------------------------------------------

def _entry(repository: str, ref: str = "main") -> reg.SnapshotEntry:
    return reg.SnapshotEntry(repository=repository, ref=ref)


def test_dropping_the_active_entry_leaves_no_active_key() -> None:
    registry = reg.SnapshotRegistry()
    registry.register(_entry("alpha"))
    registry.drop("alpha")
    assert registry.active is None
    assert registry._active is None


def test_after_the_active_entry_is_dropped_the_next_one_becomes_active() -> None:
    """Left set, the stale key kept every later entry from becoming active,
    since `register` promotes only while nothing is."""
    registry = reg.SnapshotRegistry()
    registry.register(_entry("alpha"))
    registry.drop("alpha")
    registry.register(_entry("beta"))
    assert registry.active is not None
    assert registry.active.repository == "beta"


def test_dropping_another_entry_keeps_the_active_one() -> None:
    registry = reg.SnapshotRegistry()
    registry.register(_entry("alpha"))
    registry.register(_entry("beta"))
    registry.drop("beta")
    assert registry.active.repository == "alpha"


# --------------------------------------------------------------------------
# 3: the writer is atomic, and refuses what JSON cannot carry
# --------------------------------------------------------------------------

def _boundary(root: Path, name: str = "snapshot.json") -> OutputBoundary:
    return OutputBoundary(root, [name])


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf],
                         ids=["nan", "infinity", "minus-infinity"])
def test_a_value_json_cannot_carry_is_refused_and_nothing_is_written(tmp_path, value) -> None:
    target = tmp_path / "snapshot.json"
    boundary = _boundary(tmp_path)
    with pytest.raises(snapshot_mod.SnapshotNotWritable):
        snapshot_mod.write_snapshot({"kind": "k", "score": value}, target, boundary)
    assert list(tmp_path.iterdir()) == []


def test_a_value_of_no_json_type_is_refused(tmp_path) -> None:
    with pytest.raises(snapshot_mod.SnapshotNotWritable):
        snapshot_mod.canonical_json({"kind": "k", "when": object()})


def test_the_refusal_is_one_openDox_reports_as_a_seam_refusal() -> None:
    assert issubclass(snapshot_mod.SnapshotNotWritable, projection_seams.ProjectionSeamError)
    assert issubclass(snapshot_mod.SnapshotNotWritable, ValueError)


def test_the_write_replaces_the_target_in_one_move(tmp_path, monkeypatch) -> None:
    """The bytes land in a sibling, and one `os.replace` puts them over the
    target. So the target is never opened for writing."""
    target = tmp_path / "snapshot.json"
    target.write_text("old\n", encoding="utf-8")
    moves = []
    real_replace = os.replace

    def replace(source, destination):
        assert Path(destination) == target
        assert target.read_text(encoding="utf-8") == "old\n"   # untouched until the move
        moves.append(Path(source).name)
        return real_replace(source, destination)

    monkeypatch.setattr(os, "replace", replace)
    written = snapshot_mod.write_snapshot({"kind": "k"}, target, _boundary(tmp_path))
    assert written == target.resolve()
    assert json.loads(target.read_text(encoding="utf-8")) == {"kind": "k"}
    assert len(moves) == 1
    assert moves[0].startswith(".snapshot.json.")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["snapshot.json"]


def test_a_failed_move_leaves_the_old_snapshot_and_no_sibling(tmp_path, monkeypatch) -> None:
    target = tmp_path / "snapshot.json"
    target.write_text("old\n", encoding="utf-8")

    def refuse(source, destination):
        raise OSError("the move failed")

    monkeypatch.setattr(os, "replace", refuse)
    boundary = _boundary(tmp_path)
    with pytest.raises(OSError, match="the move failed"):
        snapshot_mod.write_snapshot({"kind": "k"}, target, boundary)
    assert target.read_text(encoding="utf-8") == "old\n"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["snapshot.json"]


def test_a_rewrite_keeps_the_snapshots_permissions(tmp_path) -> None:
    target = tmp_path / "snapshot.json"
    target.write_text("old\n", encoding="utf-8")
    target.chmod(0o600)
    snapshot_mod.write_snapshot({"kind": "k"}, target, _boundary(tmp_path))
    assert (target.stat().st_mode & 0o777) == 0o600


def test_the_boundary_still_decides_the_destination(tmp_path) -> None:
    from opendox.boundary import BoundaryViolation

    boundary = _boundary(tmp_path)
    with pytest.raises(BoundaryViolation):
        snapshot_mod.write_snapshot({"kind": "k"}, tmp_path / "elsewhere.json", boundary)
    assert list(tmp_path.iterdir()) == []


def test_the_bytes_are_the_canonical_render(tmp_path) -> None:
    snapshot = {"b": 1, "a": {"d": [2, 1], "c": "é"}}
    target = tmp_path / "snapshot.json"
    snapshot_mod.write_snapshot(snapshot, target, _boundary(tmp_path))
    assert target.read_bytes() == snapshot_mod.canonical_bytes(snapshot)


# --------------------------------------------------------------------------
# 4: every read waits for a held read-modify-write
# --------------------------------------------------------------------------

READS = {
    "get": lambda r: r.get("alpha", "session/x"),
    "active": lambda r: r.active,
    "resolve": lambda r: r.resolve(None),
    "entries": lambda r: r.entries(),
    "keys": lambda r: r.keys(),
    "len": lambda r: len(r),
    "aggregates": lambda r: r.aggregates(),
}


@pytest.mark.parametrize("read", sorted(READS))
def test_a_read_waits_for_a_held_read_modify_write(read) -> None:
    """A block holds the registry, registers a session and promotes it, and
    only then puts `main` back. A read started while the block holds must
    answer as the block left the registry, never from its middle."""
    registry = reg.SnapshotRegistry()
    registry.register(_entry("alpha"))
    held = threading.Event()
    answer = []

    def reader() -> None:
        held.wait()
        answer.append(READS[read](registry))

    thread = threading.Thread(target=reader)
    thread.start()
    with registry.atomically():
        registry.register(_entry("alpha", "session/x"), active=True)
        registry.register_aggregate(reg.Aggregate(id="agg"))
        held.set()
        time.sleep(0.2)
        assert not answer, f"{read} answered while the block held the registry"
        registry.set_active("alpha")
    thread.join(timeout=5)
    assert answer, f"{read} never answered"
