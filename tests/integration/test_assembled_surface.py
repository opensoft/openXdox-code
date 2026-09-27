"""The ASSEMBLED command line: the 31-entry `--help` tree neither leg makes alone.

Plan 034 task T042, box 9.3 of the ratified
`add-neutral-product-standalone-operability`: behaviours needing both legs
become declared integration tests, "including the 31-entry assembled `--help`
tree the carve manifest records as one 'which after the carve neither leg
produces alone'". F9.2's last line runs the test below by name.

WHAT THE MANIFEST RECORDS. openxFactory's `docs/opendox-carve-manifest.yaml`
keeps `tests/ideation-dashboard/fixtures/cli-help-tree.golden.txt` as a
`not_moved` row, and its evidence names that golden "the 31-entry --help tree
of the ASSEMBLED CLI, which after the carve neither leg produces alone". The
golden is text: one `===== <entry point> =====` section per entry point, each
holding that entry point's help at `COLUMNS=100`. This test holds the tree it
builds to that golden twice:
  * its entry points, by name and in order, which is what a reader needs first
    when the tree changes shape. They are the golden's 31 section headers;
  * its text, by the golden's sha256. The golden itself stays in openxFactory,
    where the manifest keeps it, and its text-level diff is that repository's
    `tests/ideation-dashboard/test_extension_point_parity.py::test_the_help_text_of_every_entry_point_is_unchanged`.
    R1Q5 (a) says the 31-entry goldens stand, and this is where that is
    checked at the declared composition.
Both were read at openxFactory `d90df42d`.

WHY IT IS 31 AND NOT MORE. The default profile openDox registers where no host
has contributes the runtime verbs (`RuntimeSubcommand`, R1Q5 (a)). A host that
registers its own profile does not get them, so the assembled tree stays at 31
entries: the root, six top-level subcommands, `gate`'s nineteen verbs and
`model-binding`'s five. Eleven are openDox's own (research R8), and the other
twenty are this column's `gate` tree.

THE HOST, STOOD IN, IN A FRESH INTERPRETER. No module in this leg registers an
openDox profile. openxFactory's `profile_openxfactory.SUBCOMMAND_EXTENSIONS` is
what carries `cli_gate.GateSubcommands()` in the composed product, so the child
below registers a stand-in host that carries exactly that, as
`tests/test_hermeticity_gate_verbs.py` does. It runs in its own interpreter
because a registration is process-wide, and a host's registration is refused
once a parser has been built from openDox's default (R1Q3 (ii)). A fresh
process builds nothing before the host registers, which is the order a real
host keeps. The child is given this process's environment less `PYTHONPATH`,
which a lone checkout does not have (the same scrub
`tests/test_declared_exclusion.py` gives its children), so openDox arrives only
through the pin, as F9.2 requires.

WHAT BUILDING IT REACHES. The twenty `gate` entries come from
`openxdox.cli_gate`, which imports `openxdox.gate_console` at module level, and
`gate_console` imports openxFactory's `doc_health` at module level
(`from doc_health import corpus`). So the child needs `doc_health` to be
importable, and where it is not, this test fails with the child's own
`ModuleNotFoundError`, naming what the assembly could not reach.

SO THE REQUIRED CHECK LEAVES IT OUT, UNTIL T008, WITH ITS STATED REASON.
RULED openxFactory#656 comment 5859927858 (Brett Heap, 2026-09-27, "(b)
Exclude it until T008's arc"): "The test leaves T042's integration step, with
its stated reason: cli_gate imports openxFactory's doc_health at load time,
which is R1Q6 (d)'s kind of exclusion. It runs again once the doc_health
direction arc (T008) lands. F9.2 is unchanged." So `validate.yml`'s
`integration (9.3)` step deselects the help-tree test and prints why, and
F9.2, unchanged, still runs it and stays red on it until then. The second test
below holds that exclusion to its reason: it passes only while the same child
fails exactly the way the reason says, so once the arc lands it fails, and the
pull request that clears the reason takes the exclusion out of `validate.yml`
and that test with it.

A CREATED file: no carve-manifest row (RULED OQ-C). Its admission is a
`created:` entry in openxFactory's `docs/opendox-carve-admissions.yaml` (T047).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from declared_composition import (  # noqa: F401  (a fixture, by name)
    Composition,
    composition,
)

#: The width the golden was taken at. `argparse` wraps help to
#: `shutil.get_terminal_size()`, which honours `COLUMNS`, so the width is part
#: of what the golden records.
GOLDEN_COLUMNS = "100"

#: The label the walk gives the root, which is also the parser's `prog`
#: (`opendox.cli.build_parser`). The golden's sections are named with it.
ROOT_LABEL = "ideation-dashboard"

#: THE TREE THE MANIFEST RECORDS: the golden's 31 section headers, in its order
#: (depth-first, each level's subcommands sorted), as read at openxFactory
#: `d90df42d` from `tests/ideation-dashboard/fixtures/cli-help-tree.golden.txt`.
MANIFEST_RECORDED_ENTRY_POINTS = (
    "ideation-dashboard",
    "ideation-dashboard create",
    "ideation-dashboard edit",
    "ideation-dashboard gate",
    "ideation-dashboard gate abandon-session",
    "ideation-dashboard gate cleanup-abandoned-branch",
    "ideation-dashboard gate create-document",
    "ideation-dashboard gate create-project",
    "ideation-dashboard gate demote",
    "ideation-dashboard gate derive-possibles",
    "ideation-dashboard gate dispose-possible",
    "ideation-dashboard gate edit-apply",
    "ideation-dashboard gate edit-document",
    "ideation-dashboard gate edit-project",
    "ideation-dashboard gate kickoff",
    "ideation-dashboard gate lens-add-as-cluster",
    "ideation-dashboard gate lens-save-recipe",
    "ideation-dashboard gate open-pr",
    "ideation-dashboard gate promote-to-staging",
    "ideation-dashboard gate propose",
    "ideation-dashboard gate ratify",
    "ideation-dashboard gate research-brief",
    "ideation-dashboard gate share-session",
    "ideation-dashboard generate",
    "ideation-dashboard generate-and-open",
    "ideation-dashboard model-binding",
    "ideation-dashboard model-binding add",
    "ideation-dashboard model-binding edit",
    "ideation-dashboard model-binding list",
    "ideation-dashboard model-binding remove",
    "ideation-dashboard model-binding set-credential",
)

#: The sha256 of that golden's bytes at openxFactory `d90df42d`. The tree's
#: text, joined the way the golden joins it, must hash to it.
MANIFEST_RECORDED_GOLDEN_SHA256 = (
    "9cbeca997f38b5c3f1b5e95ed83b1e62ac9cacb131852914c1e462adfc3ef875")

#: The variables a lone checkout does not have, dropped from the child.
SCRUBBED_ENVIRONMENT = ("PYTHONPATH",)

#: Why the required check leaves the help-tree test out, in the ruling's words
#: (RULED openxFactory#656 comment 5859927858).
LEFT_OUT_REASON = (
    "cli_gate imports openxFactory's doc_health at load time, which is "
    "R1Q6 (d)'s kind of exclusion")

#: What the child ends with while that reason holds: `doc_health`, or a module
#: in it, not found. It is the evidence `tests/test_declared_exclusion.py`
#: takes for R1Q6 (d)'s reason.
_DOC_HEALTH_NOT_FOUND = re.compile(
    r"ModuleNotFoundError: No module named 'doc_health(?:\.[\w.]+)?'")

#: The frame that says the child reached it through this column's `cli_gate`,
#: which is the reason's own account of where the import happens.
_THROUGH_CLI_GATE = re.compile(r'File "[^"]*openxdox[/\\]cli_gate\.py"')

#: The child: the host registers its profile, THEN the parser is built, and the
#: tree is walked the way openxFactory's golden was taken.
_ASSEMBLE = r'''
import argparse, json, sys

from opendox import cli, domain_profile
from openxdox import cli_gate


class AssembledHost:
    """The composition point, stood in: this column's one command-line
    contribution, as openxFactory's `profile_openxfactory.SUBCOMMAND_EXTENSIONS`
    carries it."""

    SUBCOMMAND_EXTENSIONS = (cli_gate.GateSubcommands(),)
    ROUTE_EXTENSIONS = ()


domain_profile.register(AssembledHost())
parser = cli.build_parser()


def walk(p, path):
    yield " ".join(path), p.format_help()
    for action in p._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in sorted(action.choices.items()):
                yield from walk(sub, path + [name])


json.dump({"entries": list(walk(parser, [sys.argv[1]])),
           "registered": type(domain_profile.current()).__name__},
          sys.stdout)
'''


def _assemble(where: Path) -> subprocess.CompletedProcess:
    env = {key: value for key, value in os.environ.items()
           if key not in SCRUBBED_ENVIRONMENT}
    env["COLUMNS"] = GOLDEN_COLUMNS
    return subprocess.run(
        [sys.executable, "-c", _ASSEMBLE, ROOT_LABEL], cwd=where, env=env,
        capture_output=True, text=True, timeout=300)


def test_the_assembled_help_tree_is_the_31_entry_tree_the_manifest_records(
        composition: Composition, tmp_path: Path) -> None:
    """openDox's parser at the pin, with this column's `gate` tree contributed
    by a host's own profile, is the 31-entry tree the carve manifest records:
    the same entry points, and the golden's text byte for byte."""
    done = _assemble(tmp_path)
    last = (done.stderr.strip().splitlines() or [""])[-1]
    assert done.returncode == 0, (
        f"at {composition}: the assembled command line could not be built. "
        f"The child ended with: {last}\n{done.stderr[-4000:]}")
    built = json.loads(done.stdout)
    assert built["registered"] == "AssembledHost", (
        f"at {composition}: the parser was built from {built['registered']}, "
        "not from the host's own profile")

    names = [name for name, _ in built["entries"]]
    recorded = list(MANIFEST_RECORDED_ENTRY_POINTS)
    added = sorted(set(names) - set(recorded))
    removed = sorted(set(recorded) - set(names))
    assert names == recorded, (
        f"at {composition}: the assembled tree has {len(names)} entry points, "
        f"and the manifest records {len(recorded)}. Added: {added}; removed: "
        f"{removed}. The order is the golden's too (depth-first, each level "
        "sorted), so equal sets in another order also fail here. "
        "A host that registers its own profile does not get the default's "
        "runtime verbs (R1Q5 (a)), so `runtime` is never among them")

    text = "\n".join(f"===== {name} =====\n{help_text}"
                     for name, help_text in built["entries"])
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert digest == MANIFEST_RECORDED_GOLDEN_SHA256, (
        f"at {composition}: the assembled tree has the 31 recorded entry "
        f"points, but its text hashes to {digest}, not to the golden's "
        f"{MANIFEST_RECORDED_GOLDEN_SHA256}. The help text of an entry point "
        "changed. openxFactory's "
        "`tests/ideation-dashboard/test_extension_point_parity.py::"
        "test_the_help_text_of_every_entry_point_is_unchanged` names the "
        "changed entry points against the golden's text")


def test_the_help_tree_is_left_out_only_while_its_stated_reason_holds(
        composition: Composition, tmp_path: Path) -> None:
    """The required check leaves the test above out of its integration step,
    with its stated reason, until the doc_health direction arc (T008) lands
    (RULED openxFactory#656 comment 5859927858). This test holds that
    exclusion to the reason. It builds the same assembled command line in the
    same child, and passes only while the child fails exactly as the reason
    says: `doc_health` not found, on the way in through `openxdox/cli_gate.py`.

    Once the arc lands and the child builds, this test fails. So the pull
    request that clears the reason takes the exclusion out of `validate.yml`,
    and this test with it, and the help-tree test runs again. A child that
    fails for any other reason fails this test as well, because the exclusion
    must not hide a failure its reason does not name."""
    done = _assemble(tmp_path)
    last = (done.stderr.strip().splitlines() or [""])[-1]
    assert done.returncode != 0, (
        f"at {composition}: the assembled command line builds now, so the "
        f"help-tree test's stated reason for leaving the required check "
        f"({LEFT_OUT_REASON}) no longer holds. Take its `--deselect` out of "
        "validate.yml's `integration (9.3)` step, and this test with it, so "
        "that it runs again (RULED openxFactory#656 comment 5859927858)")
    assert (_DOC_HEALTH_NOT_FOUND.fullmatch(last)
            and _THROUGH_CLI_GATE.search(done.stderr)), (
        f"at {composition}: the assembled command line fails to build for a "
        f"reason the exclusion does not state. It states: {LEFT_OUT_REASON}. "
        f"The child ended with: {last}\n{done.stderr[-4000:]}")
