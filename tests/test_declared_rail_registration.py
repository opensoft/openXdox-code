"""The rail registration `tests/conftest.py` makes for the declared rail
suites, held to its word (plan 038 task T073; ARC-Q2 (a), openxFactory#656
comment 6003918488; Copilot r4197793290 on openXdox-code#45).

Where the run is composed, each test of a file `tests/declared_exclusion.yaml`
names under `status-exemption-rail` runs with the rail openxFactory's host
registers, through `conftest.a_hosts_rail`. Those runs prove the rail is
registered. These cases prove what a composed run cannot see: that the seam is
put back afterwards, so no test after a rail suite meets a rail it did not
register, and no host's rail is lost to one. They use stand-in rails, so they
run in a lone checkout too, inside the required check.

Each case leaves openDox's seam exactly as it found it: `_the_seam_as_found`
records the seam's three globals through `monkeypatch`, which writes them back
at teardown, whatever the case did.
"""

from __future__ import annotations

import pytest
import yaml

from conftest import HERE, a_hosts_rail, status_exemption_rail_suites
from opendox import doxbench_packet


class _Rail:
    """A stand-in rail: the two names a rail must carry, each its own."""

    def __init__(self, name: str):
        self.name = name

        def lifecycle_status(text):
            return None

        def is_compression_exempt(text):
            return False

        self.lifecycle_status = lifecycle_status
        self.is_compression_exempt = is_compression_exempt


def _answering() -> object:
    """The rail openDox's seam answers with now, read through the name it
    hands over (`doxbench_packet.is_compression_exempt`), or None when no
    rail is registered."""
    if not doxbench_packet.status_exemption_registered():
        return None
    return doxbench_packet.is_compression_exempt


@pytest.fixture(autouse=True)
def _the_seam_as_found(monkeypatch):
    for name in ("_status_exemption_rail", "_status_exemption_is_default",
                 "_status_exemption_default_read"):
        monkeypatch.setattr(doxbench_packet, name, getattr(doxbench_packet, name))
    doxbench_packet.unregister_status_exemption()


def test_a_hosts_earlier_rail_is_dropped_for_the_block_and_put_back_after():
    earlier, rail = _Rail("earlier"), _Rail("the host's")
    doxbench_packet.register_status_exemption(earlier)
    with a_hosts_rail(rail):
        assert _answering() is rail.is_compression_exempt
    assert _answering() is earlier.is_compression_exempt


def test_no_rail_is_left_behind_where_none_was_registered():
    rail = _Rail("the host's")
    with a_hosts_rail(rail):
        assert _answering() is rail.is_compression_exempt
    assert _answering() is None


def test_opendoxs_own_default_is_not_put_back():
    """As `a_hosts_plane` treats the default profile: the next entry point
    registers the default again, as it does in any process."""
    default, rail = _Rail("openDox's default"), _Rail("the host's")
    doxbench_packet.register_default_status_exemption(default)
    with a_hosts_rail(rail):
        assert _answering() is rail.is_compression_exempt
    assert _answering() is None


def test_the_seam_is_put_back_when_the_block_fails():
    earlier, rail = _Rail("earlier"), _Rail("the host's")
    doxbench_packet.register_status_exemption(earlier)
    with pytest.raises(RuntimeError, match="the case failed"):
        with a_hosts_rail(rail):
            raise RuntimeError("the case failed")
    assert _answering() is earlier.is_compression_exempt


def test_the_rail_suites_are_the_declarations_rail_entries():
    declaration = yaml.safe_load(
        (HERE / "declared_exclusion.yaml").read_text(encoding="utf-8"))
    named = {entry["path"].rsplit("/", 1)[-1] for entry in declaration["entries"]
             if "status-exemption-rail" in entry["reasons"]}
    assert named, "the declaration names no rail file"
    assert status_exemption_rail_suites() == frozenset(named)
