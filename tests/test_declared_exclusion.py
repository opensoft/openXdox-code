"""The declared exclusion, held to its word (plan 034 task T041).

`tests/declared_exclusion.yaml` lists the test files a lone openXdox-code
checkout cannot run, each with its reason, and their count. The
repository-root `conftest.py` derives `collect_ignore` from it, and prints it
as an OPEN extraction at the end of every run that loads it (requirement 9,
first scenario; FR-006). This module is what keeps that list honest rather
than convenient:

  * T007 batch B's three assertions on the file: its count equals its
    entries, every entry carries its reason, and a run that loads the root
    conftest prints it;
  * the reasons are the four the rulings admit (R1Q6 (d); R1Q24 (a) twice;
    R1Q25 (b)), and the consumer's schemas are `tests/test_snapshot.py`'s
    alone;
  * the root conftest derives `collect_ignore` from the file, refuses a file
    that breaks a rule, and the whole suite collects less exactly these files;
  * each listed file, RUN ALONE, fails, and every red result it shows is
    caused by one of the reasons its entry names, each of them at least once.

The last is the one that stops the exclusion from hiding anything. A listed
file that also failed for some other cause would turn its case red, and so
would a file that stopped failing for its reason. That file then leaves the
list, in the pull request that clears the reason (T061's, for
`tests/test_snapshot.py`). An entry may name two reasons, and each is then
checked (`tests/test_doxbench_packet.py` and
`tests/test_doxbench_blank_reason.py`).

HOW A RED RESULT IS ATTRIBUTED. Each listed file runs in a child pytest of its
own, from this checkout's root, with a JUnit report. Every failure and error
in the report is read through its message and the lines pytest marks `E`. So
source lines a traceback quotes are never read as evidence. Each reason has one
piece of evidence, `EVIDENCE` below, and a red result must match exactly one of
them. None is an unattributed failure. Two means the evidence has stopped
telling the reasons apart, and it is refused as well.

THE LONE CHECKOUT. The child's environment drops `PYTHONPATH`,
`CONTRACTS_DIR`, `PYTEST_ADDOPTS` and `PYTEST_PLUGINS`, which could otherwise
supply what the exclusion says is missing, or change what the child collects.
It also drops this session's hermeticity ledger variable, so the child's guard
declares its own. So the claim checked is the declaration's own claim: that
these files fail in a lone checkout.
"""

from __future__ import annotations

import concurrent.futures
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

import pytest
import yaml

import hermeticity

LEG_ROOT = Path(__file__).resolve().parents[1]
DECLARATION_FILE = LEG_ROOT / "tests" / "declared_exclusion.yaml"
THIS_FILE = f"tests/{Path(__file__).name}"

#: The reasons the rulings admit, by id, with the ruling each one carries out.
#: A fifth needs a ruling before it needs a line here.
RULED_REASONS = {
    "doc_health": "R1Q6 (d)",
    "status-exemption-rail": "R1Q24 (a)",
    "openxfactory-contracts": "R1Q24 (a)",
    "consumer-schemas": "R1Q25 (b)",
}

#: How long one listed file may take to run alone. Every file measured runs in
#: under ten seconds, so this only stops a hung child from hanging the suite.
ALONE_TIMEOUT_SECONDS = 600

#: The variables a lone checkout does not have, dropped from each child run.
SCRUBBED_ENVIRONMENT = ("PYTHONPATH", "CONTRACTS_DIR", "PYTEST_ADDOPTS",
                        "PYTEST_PLUGINS", hermeticity.REFUSAL_LOG_ENV)


def _load() -> dict:
    return yaml.safe_load(DECLARATION_FILE.read_text(encoding="utf-8"))


DECLARATION = _load()
ENTRIES = DECLARATION.get("entries") or []
REASONS = {reason["id"]: reason for reason in DECLARATION.get("reasons") or []}


# ---------------------------------------------------------------------------
# THE EVIDENCE: what a red result of each reason says.
# ---------------------------------------------------------------------------

_DOC_HEALTH = re.compile(r"No module named 'doc_health(?:\.[\w.]+)?'")

#: The refusal openDox's status-exemption seam raises when nothing is
#: registered (plan 034 T027, openDox-code#41): `StatusExemptionNotRegistered`,
#: and the `AttributeError` the module raises for a rail name, which quotes it.
_RAIL = ("no status-exemption rail is registered at openDox's "
         "status-exemption seam")

#: A missing path, as `open()` and the interpreter each report one.
_MISSING = re.compile(
    r"(?:No such file or directory: |can't open file )'(?P<path>[^']+)'")

#: The consumer validator's own refusal when neither a `contracts/` in its
#: tree nor `CONTRACTS_DIR` supplies its schemas (C3's openXdox-code#28).
_CONSUMER_SCHEMAS = "CONTRACTS_DIR is not set"


def _reaches_doc_health(text: str) -> bool:
    """`ModuleNotFoundError: No module named 'doc_health'`: openxFactory's
    corpus machinery, which `src/openxdox/generator.py`, `gate_console.py`
    and the rest import at module level."""
    return _DOC_HEALTH.search(text) is not None


def _needs_the_rail(text: str) -> bool:
    """openDox's status-exemption seam refused: no rail is registered."""
    return _RAIL in text


def _reads_openxfactory_contracts(text: str) -> bool:
    """A contract file of openxFactory's is missing where openxFactory's tree
    keeps it: a path under a `contracts/` directory, or the contract validator
    `scripts/validate-ideation-dashboard-contracts.py`, that lies OUTSIDE this
    checkout (the contract-family files read `Path(__file__).parents[2]`, one
    directory above it) or under the `contracts/` this checkout does not
    carry. A missing file anywhere else in the checkout is some other defect,
    and it is not this reason."""
    for match in _MISSING.finditer(text):
        path = Path(match.group("path"))
        shown = path.as_posix()
        if not ("/contracts/" in shown or shown.endswith(
                "/scripts/validate-ideation-dashboard-contracts.py")):
            continue
        try:
            inside = path.resolve().relative_to(LEG_ROOT.resolve())
        except ValueError:
            return True
        if inside.parts[:1] == ("contracts",):
            return True
    return False


def _needs_the_consumer_schemas(text: str) -> bool:
    """The consumer validator found no schemas, and says why."""
    return _CONSUMER_SCHEMAS in text


EVIDENCE = {
    "doc_health": _reaches_doc_health,
    "status-exemption-rail": _needs_the_rail,
    "openxfactory-contracts": _reads_openxfactory_contracts,
    "consumer-schemas": _needs_the_consumer_schemas,
}


# ---------------------------------------------------------------------------
# Child pytest runs.
# ---------------------------------------------------------------------------

def _child_environment() -> dict[str, str]:
    return {key: value for key, value in os.environ.items()
            if key not in SCRUBBED_ENVIRONMENT}


def _child_pytest(args, *, timeout=ALONE_TIMEOUT_SECONDS):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *args],
        cwd=LEG_ROOT, env=_child_environment(), capture_output=True,
        text=True, timeout=timeout)


def _evidence_text(element) -> str:
    """A red result's message and the lines pytest marks `E`, and nothing
    else, so a quoted source line is never read as evidence."""
    lines = [element.get("message") or ""]
    lines += [line for line in (element.text or "").splitlines()
              if line.startswith("E ")]
    return "\n".join(lines)


def _run_alone(path: str, report: Path) -> dict:
    """Run one listed file alone and attribute each red result."""
    done = _child_pytest(["-q", f"--junitxml={report}", path])
    red = []
    if report.is_file():
        for case in ET.parse(report).getroot().iter("testcase"):
            for tag in ("failure", "error"):
                element = case.find(tag)
                if element is None:
                    continue
                text = _evidence_text(element)
                red.append({
                    "case": case.get("name"),
                    "tag": tag,
                    "reasons": sorted(reason for reason, matches
                                      in EVIDENCE.items() if matches(text)),
                    "message": text.splitlines()[0][:300],
                })
    return {"returncode": done.returncode, "report": report.is_file(),
            "red": red, "tail": (done.stdout + done.stderr)[-2000:]}


_ALONE_CASE = "test_each_listed_file_fails_alone_for_exactly_its_reasons"


@pytest.fixture(scope="session")
def alone_runs(request, tmp_path_factory):
    """Every listed file this session will check, each run alone, in parallel.

    Only the files whose case was selected are run, so `-k` or a node id runs
    one child and not all of them."""
    selected = [item.callspec.params["entry"]["path"]
                for item in request.session.items
                if getattr(item, "originalname", None) == _ALONE_CASE
                and hasattr(item, "callspec")]
    base = tmp_path_factory.mktemp("declared-exclusion")
    workers = max(1, min(8, os.cpu_count() or 1))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            path: pool.submit(_run_alone, path,
                              base / f"{Path(path).stem}.xml")
            for path in dict.fromkeys(selected)}
        yield futures


@pytest.fixture(scope="module")
def collect_only_run():
    """One collect-only run of the whole suite that loads the root conftest."""
    return _child_pytest(["--co", "-q"])


def _root_conftest(config):
    """The repository-root `conftest.py`, as this session loaded it."""
    target = (LEG_ROOT / "conftest.py").resolve()
    for plugin in config.pluginmanager.get_plugins():
        location = getattr(plugin, "__file__", None)
        if location and Path(location).resolve() == target:
            return plugin
    pytest.fail("the repository-root conftest.py is not loaded in this "
                "session, so the declared exclusion is not in effect here. "
                "Run without --noconftest.")


# ---------------------------------------------------------------------------
# T007 batch B's three assertions on the exclusion.
# ---------------------------------------------------------------------------

def test_the_count_equals_the_entries():
    assert DECLARATION["count"] == len(ENTRIES), (
        f"count is {DECLARATION['count']}, but {len(ENTRIES)} entries are "
        "listed. The count moves with the entries, in the same pull request.")


def test_every_entry_carries_its_reason():
    missing = [entry.get("path") for entry in ENTRIES
               if not entry.get("reasons")]
    assert missing == [], f"entries with no reason: {missing}"
    undeclared = {entry["path"]: sorted(set(entry["reasons"]) - set(REASONS))
                  for entry in ENTRIES if set(entry["reasons"]) - set(REASONS)}
    assert undeclared == {}, (
        f"entries naming an undeclared reason: {undeclared}")
    for reason in REASONS.values():
        for field in ("reason", "ruled", "open_until"):
            assert str(reason.get(field) or "").strip(), (
                f"the reason {reason['id']} states no {field}")


def test_a_run_that_loads_the_root_conftest_prints_the_exclusion(
        collect_only_run):
    """The run prints the exclusion as an OPEN extraction: the count, each
    reason with its text, and each file with its reasons. Checked on a
    collect-only run of the whole suite, which loads the root conftest and
    prints what every run prints."""
    out = collect_only_run.stdout
    assert re.search(r"^=+ open extraction: the declared exclusion =+$", out,
                     re.MULTILINE), out[-3000:]
    count = DECLARATION["count"]
    assert (f"declared exclusion: {count} file{'' if count == 1 else 's'}, "
            f"listed in tests/declared_exclusion.yaml") in out, out[-3000:]
    assert "It is an OPEN extraction" in out
    for reason in REASONS.values():
        named = sum(reason["id"] in entry["reasons"] for entry in ENTRIES)
        assert (f"  reason {reason['id']} ({named} "
                f"file{'' if named == 1 else 's'}): {reason['reason']}; "
                f"open until {reason['open_until']}; ruled {reason['ruled']}"
                ) in out, reason["id"]
    printed = re.findall(r"^  excluded (\S+): (.+)$", out, re.MULTILINE)
    assert printed == [(entry["path"], ", ".join(entry["reasons"]))
                       for entry in ENTRIES], printed


# ---------------------------------------------------------------------------
# The declaration's own rules.
# ---------------------------------------------------------------------------

def test_the_reasons_are_the_four_the_rulings_admit():
    assert set(REASONS) == set(RULED_REASONS), sorted(REASONS)
    for reason_id, ruling in RULED_REASONS.items():
        assert REASONS[reason_id]["ruled"].startswith(ruling), (
            reason_id, REASONS[reason_id]["ruled"])
    assert set(EVIDENCE) == set(RULED_REASONS), (
        "each admitted reason needs its evidence in this module")


def test_the_consumer_schemas_are_tests_test_snapshot_py_s_alone():
    """R1Q25 (b): one narrow exclusion, for one schema-reading suite, until
    7.3 lands (T061 clears the entry)."""
    assert REASONS["consumer-schemas"].get("only") == ["tests/test_snapshot.py"]
    naming = [entry["path"] for entry in ENTRIES
              if "consumer-schemas" in entry["reasons"]]
    assert naming in ([], ["tests/test_snapshot.py"]), naming


def test_every_entry_names_a_test_file_this_checkout_carries():
    paths = [entry["path"] for entry in ENTRIES]
    assert len(set(paths)) == len(paths), "a file is listed twice"
    assert paths == sorted(paths), "the entries are not in path order"
    for path in paths:
        rel = PurePosixPath(path)
        assert rel.parts[:1] == ("tests",) and len(rel.parts) == 2, path
        assert rel.name.startswith("test_") and rel.suffix == ".py", path
        assert (LEG_ROOT / rel).is_file(), f"{path} is not in this checkout"
    assert THIS_FILE not in paths, (
        "this module checks the exclusion, and cannot be excluded by it")


# ---------------------------------------------------------------------------
# The root conftest takes the declaration into effect, and refuses a broken one.
# ---------------------------------------------------------------------------

def test_the_root_conftest_derives_collect_ignore_from_the_file(request):
    root = _root_conftest(request.config)
    assert root.collect_ignore == [entry["path"] for entry in ENTRIES]


#: Each rule the root conftest holds the declaration to, broken once, with the
#: words its refusal must use to name that rule.
BROKEN_DECLARATIONS = {
    "count off by one": (
        lambda d: d.update(count=d["count"] + 1), "its count is"),
    "an entry with no reason": (
        lambda d: d["entries"][0].update(reasons=[]), "carries no reason"),
    "an undeclared reason": (
        lambda d: d["entries"][0].update(reasons=["no-such-reason"]),
        "which is not a declared reason"),
    "a reason with no open_until": (
        lambda d: d["reasons"][0].pop("open_until"), "lacks one of"),
    "a file listed twice": (
        lambda d: d["entries"].insert(1, dict(d["entries"][0])),
        "a file is listed twice"),
    "entries out of path order": (
        lambda d: d["entries"].reverse(), "not in path order"),
    "a path that is not a test file": (
        lambda d: d["entries"][0].update(path="tests/hermeticity.py"),
        "is not a tests/test_*.py path"),
    "a file this checkout lacks": (
        lambda d: d["entries"][0].update(path="tests/test_no_such_file.py"),
        "names no file in this checkout"),
    "the consumer's schemas on another file": (
        lambda d: d["entries"][0].update(reasons=["consumer-schemas"]),
        "is for ['tests/test_snapshot.py'] alone"),
    "a different kind": (
        lambda d: d.update(kind="something-else"), "its kind must be"),
}


@pytest.mark.parametrize("breakage", sorted(BROKEN_DECLARATIONS))
def test_the_root_conftest_refuses_a_declaration_that_breaks_a_rule(
        breakage, request, tmp_path):
    root = _root_conftest(request.config)
    mutate, rule = BROKEN_DECLARATIONS[breakage]
    data = _load()
    mutate(data)
    broken = tmp_path / "declared_exclusion.yaml"
    broken.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    with pytest.raises(root.DeclaredExclusionRefused, match=re.escape(rule)):
        root.load_declared_exclusion(broken)


def test_the_root_conftest_accepts_the_declaration_as_committed(request):
    root = _root_conftest(request.config)
    assert root.load_declared_exclusion(DECLARATION_FILE) == DECLARATION


def test_the_whole_suite_collects_less_the_exclusion(collect_only_run):
    """Collected: every test file here except the listed ones. Not collected:
    any node of a listed file."""
    assert collect_only_run.returncode == 0, collect_only_run.stdout[-3000:]
    collected = {line.split("::", 1)[0]
                 for line in collect_only_run.stdout.splitlines()
                 if line.startswith("tests/") and "::" in line}
    listed = {entry["path"] for entry in ENTRIES}
    assert collected & listed == set(), sorted(collected & listed)
    present = {f"tests/{path.name}"
               for path in (LEG_ROOT / "tests").glob("test_*.py")}
    assert collected == present - listed, (
        f"not collected: {sorted(present - listed - collected)}; "
        f"collected but not a test file here: {sorted(collected - present)}")


# ---------------------------------------------------------------------------
# Each listed file fails, alone, for exactly its entry's reasons.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("entry", ENTRIES, ids=[e["path"] for e in ENTRIES])
def test_each_listed_file_fails_alone_for_exactly_its_reasons(entry,
                                                              alone_runs):
    path, declared = entry["path"], set(entry["reasons"])
    run = alone_runs[path].result()
    # pytest's own exit codes: 0 all passed, 1 some failed, 2 interrupted (a
    # collection error), 5 nothing collected. Anything else (3 internal error,
    # 4 usage error) means the file never ran as a test run does.
    assert run["report"] and run["returncode"] in (0, 1, 2, 5), (
        f"{path}, run alone, did not run as a test run does (exit "
        f"{run['returncode']}, report written: {run['report']}):\n"
        f"{run['tail']}")
    assert run["returncode"] in (1, 2) and run["red"], (
        f"{path}, run alone, no longer fails (exit {run['returncode']}). It "
        f"leaves the declared exclusion, in the pull request that clears its "
        f"reason.")
    unattributed = [r for r in run["red"] if not r["reasons"]]
    assert unattributed == [], (
        f"{path} fails for a cause none of the four reasons names. The "
        f"exclusion must not hide it:\n" + "\n".join(
            f"  {r['case']} ({r['tag']}): {r['message']}"
            for r in unattributed))
    ambiguous = [r for r in run["red"] if len(r["reasons"]) > 1]
    assert ambiguous == [], (
        f"{path}: the evidence of two reasons matched one result, so it no "
        f"longer tells them apart: {ambiguous}")
    shown = {r["reasons"][0] for r in run["red"]}
    assert shown - declared == set(), (
        f"{path} fails for {sorted(shown - declared)}, which its entry does "
        f"not name (it names {sorted(declared)})")
    assert declared - shown == set(), (
        f"{path}'s entry names {sorted(declared - shown)}, but no result fails "
        f"for it. Drop that reason from the entry.")
