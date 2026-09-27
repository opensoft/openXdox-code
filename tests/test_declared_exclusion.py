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
piece of evidence, `EVIDENCE` below: its cause as raised, and only when that
cause is all the result shows. A red result must match exactly one of them.
None is an unattributed failure, and so is a declared cause shown beside
anything else. Two would mean the evidence had stopped telling the reasons
apart, and that is refused as well, though the evidence as written leaves no
result that two reasons can take.

THE LONE CHECKOUT. The child's environment drops `PYTHONPATH`,
`CONTRACTS_DIR`, `PYTEST_ADDOPTS` and `PYTEST_PLUGINS`, which could otherwise
supply what the exclusion says is missing, or change what the child collects.
It also drops this session's hermeticity ledger variable, so the child's guard
declares its own. So the claim checked is the declaration's own claim: that
these files fail in a lone checkout.
"""

from __future__ import annotations

import concurrent.futures
import copy
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
# THE EVIDENCE: what a red result of each reason says, and nothing else.
#
# Each reason's evidence is its cause AS RAISED: the exception with its
# message, or the refusal in its raiser's own words. The same words quoted in
# some other failure are not evidence. And a reason accounts for the whole
# result: every missing module, missing file and refusal the result shows must
# be its own. A result that shows its reason's cause beside anything else is
# unattributed, so an unrelated failure cannot ride along under a declared
# reason. So no two reasons can take one result.
# ---------------------------------------------------------------------------

#: `doc_health`, or one of its modules, as the import raises it missing.
_DOC_HEALTH = re.compile(
    r"ModuleNotFoundError: No module named 'doc_health(?:\.[\w.]+)?'")
#: Any module any line reports missing.
_ANY_MODULE = re.compile(r"No module named '(?P<module>[^']+)'")

#: The refusal openDox's status-exemption seam raises when nothing is
#: registered (plan 034 T027, openDox-code#41). The `AttributeError` the module
#: raises for a rail name chains it, so it shows there too.
_RAIL = re.compile(
    r"StatusExemptionNotRegistered: no status-exemption rail is registered "
    r"at openDox's status-exemption seam")
#: The refusal's words, however they arrive.
_ANY_RAIL = "no status-exemption rail is registered"

#: A missing file as `open()` raises it, or a script the interpreter cannot
#: open.
_MISSING = re.compile(
    r"(?:FileNotFoundError: \[Errno 2\] No such file or directory: "
    r"|can't open file )'(?P<path>[^']+)'")
#: Any path any line reports missing.
_ANY_MISSING = re.compile(
    r"(?:No such file or directory: |can't open file )'(?P<path>[^']+)'")

#: The consumer validator's refusal when neither this tree's `contracts/` nor
#: `CONTRACTS_DIR` supplies its schemas, in the words of this checkout's
#: `scripts/validate-ideation-dashboard-contracts.py` (C3's openXdox-code#28).
#: It names this checkout's own `contracts/schemas`, and why nothing is there.
_CONSUMER_SCHEMAS = re.compile(
    re.escape(f"ERROR harness failure: {LEG_ROOT / 'contracts' / 'schemas'}"
              " carries none of the family's ") + r"\d+"
    + re.escape(" schemas (this tree carries no contracts/ and CONTRACTS_DIR "
                "is not set;"))
#: The refusal's condition, however it arrives.
_ANY_CONSUMER = "CONTRACTS_DIR is not set"

#: The contract files the listed contracts files read, where the contract
#: family looks for them. Its files take `Path(__file__).parents[2]` for
#: openxFactory's root, which from this checkout's `tests/` is the directory
#: above the checkout. `test_doxbench_blank_reason.py` reads
#: `contracts/manifest.yaml` at the checkout's own root instead. These are
#: every path the five contracts files report missing, each run alone. A path
#: a new run shows joins this list in the pull request that quotes that run.
_CONTRACT_VALIDATOR = (LEG_ROOT.parent / "scripts"
                       / "validate-ideation-dashboard-contracts.py")
_CONTRACT_FILES = frozenset({
    LEG_ROOT.parent / "contracts" / "schemas" / "gate-intent.schema.yaml",
    LEG_ROOT.parent / "contracts" / "schemas" / "project-register.schema.yaml",
    _CONTRACT_VALIDATOR,
    LEG_ROOT / "contracts" / "manifest.yaml",
})


def _missing_paths(text: str, pattern: re.Pattern = _ANY_MISSING) -> set:
    """Each path `pattern` finds, resolved. A relative path is the child's,
    which runs from this checkout's root."""
    paths = set()
    for match in pattern.finditer(text):
        path = Path(match.group("path"))
        if not path.is_absolute():
            path = LEG_ROOT / path
        paths.add(path.resolve())
    return paths


def _signals(text: str) -> dict:
    """Everything a red result shows that some reason could account for: its
    missing modules and missing files, and whether it carries the rail's
    refusal or the consumer's."""
    return {"modules": set(_ANY_MODULE.findall(text)),
            "files": _missing_paths(text),
            "rail": _ANY_RAIL in text,
            "consumer": _ANY_CONSUMER in text}


def _is_doc_health(module: str) -> bool:
    return module == "doc_health" or module.startswith("doc_health.")


def _reaches_doc_health(text: str) -> bool:
    """openxFactory's corpus machinery, which `src/openxdox/generator.py`,
    `gate_console.py` and the rest import at module level, raised missing,
    and no other module, file or refusal."""
    shown = _signals(text)
    return (_DOC_HEALTH.search(text) is not None
            and all(_is_doc_health(module) for module in shown["modules"])
            and not (shown["files"] or shown["rail"] or shown["consumer"]))


def _needs_the_rail(text: str) -> bool:
    """openDox's status-exemption seam refused, with no rail registered, and
    nothing else is missing."""
    shown = _signals(text)
    return (_RAIL.search(text) is not None
            and not (shown["modules"] or shown["files"] or shown["consumer"]))


def _reads_openxfactory_contracts(text: str) -> bool:
    """A contract file of `_CONTRACT_FILES`, raised missing, and every file
    the result shows missing is one of them. Any other missing file, even one
    beside those in the same `contracts/`, is some other defect."""
    shown = _signals(text)
    return (bool(_missing_paths(text, _MISSING))
            and shown["files"] <= _CONTRACT_FILES
            and not (shown["modules"] or shown["rail"] or shown["consumer"]))


def _needs_the_consumer_schemas(text: str) -> bool:
    """The consumer validator refused for want of its schemas, in its own
    words, and nothing else is missing."""
    shown = _signals(text)
    return (_CONSUMER_SCHEMAS.search(text) is not None
            and not (shown["modules"] or shown["files"] or shown["rail"]))


EVIDENCE = {
    "doc_health": _reaches_doc_health,
    "status-exemption-rail": _needs_the_rail,
    "openxfactory-contracts": _reads_openxfactory_contracts,
    "consumer-schemas": _needs_the_consumer_schemas,
}


def _missing(path) -> str:
    return f"FileNotFoundError: [Errno 2] No such file or directory: '{path}'"


_DOC_HEALTH_RAISED = "ModuleNotFoundError: No module named 'doc_health'"
_RAIL_RAISED = ("opendox.doxbench_packet.StatusExemptionNotRegistered: no "
                "status-exemption rail is registered at openDox's "
                "status-exemption seam (opendox.doxbench_packet), so no "
                "source can be marked")
_CONSUMER_RAISED = (
    f"AssertionError: ERROR harness failure: {LEG_ROOT / 'contracts'}"
    "/schemas carries none of the family's 10 schemas (this tree carries no "
    "contracts/ and CONTRACTS_DIR is not set; export it as the spec leg's "
    "contracts directory), so nothing can be validated")
_GATE_INTENT = (LEG_ROOT.parent / "contracts" / "schemas"
                / "gate-intent.schema.yaml")

#: What each reason's evidence must take, and must not. Each real shape the
#: listed files' runs show is taken by its reason. The same words quoted
#: elsewhere, a cause beside an unrelated one, and look-alike paths are taken
#: by none.
EVIDENCE_CASES = {
    "doc_health, raised": (_DOC_HEALTH_RAISED, "doc_health"),
    "a doc_health module, raised": (
        "ModuleNotFoundError: No module named 'doc_health.corpus'",
        "doc_health"),
    "doc_health's words in an assertion": (
        "AssertionError: No module named 'doc_health'", None),
    "doc_health beside an unrelated missing module": (
        _DOC_HEALTH_RAISED
        + "\nModuleNotFoundError: No module named 'yaml_extra'", None),
    "doc_health beside an unrelated missing file": (
        _DOC_HEALTH_RAISED + "\n" + _missing("/tmp/t041-x.yaml"), None),
    "the rail's refusal, raised": (_RAIL_RAISED, "status-exemption-rail"),
    "the AttributeError that chains the rail's refusal": (
        _RAIL_RAISED + "\nAttributeError: module 'opendox.doxbench_packet' "
        "has no attribute 'is_compression_exempt': the status-exemption rail "
        "cannot answer it (no status-exemption rail is registered at "
        "openDox's status-exemption seam)", "status-exemption-rail"),
    "the rail's words in another error": (
        "RuntimeError: no status-exemption rail is registered at openDox's "
        "status-exemption seam", None),
    "the rail's refusal beside an unrelated missing file": (
        _RAIL_RAISED + "\n" + _missing("/tmp/t041-x.yaml"), None),
    "the gate-intent schema above the checkout": (
        _missing(_GATE_INTENT), "openxfactory-contracts"),
    "the project-register schema above the checkout": (
        _missing(LEG_ROOT.parent / "contracts" / "schemas"
                 / "project-register.schema.yaml"), "openxfactory-contracts"),
    "the validator above the checkout, as the interpreter reports it": (
        f"AssertionError: /usr/bin/python3: can't open file "
        f"'{_CONTRACT_VALIDATOR}': [Errno 2] No such file or directory",
        "openxfactory-contracts"),
    "the checkout's own contracts/manifest.yaml": (
        _missing(LEG_ROOT / "contracts" / "manifest.yaml"),
        "openxfactory-contracts"),
    "the same, as the child's relative path": (
        _missing("contracts/manifest.yaml"), "openxfactory-contracts"),
    "a known schema beside an unrelated missing file": (
        _missing(_GATE_INTENT) + "\n" + _missing("/tmp/t041-x.yaml"), None),
    "a known schema's path in an assertion": (
        f"AssertionError: No such file or directory: '{_GATE_INTENT}'", None),
    "an unrelated file in the contracts/ above the checkout": (
        _missing(LEG_ROOT.parent / "contracts" / "unrelated.yaml"), None),
    "an unrelated schema beside the known ones": (
        _missing(LEG_ROOT.parent / "contracts" / "schemas"
                 / "unrelated.schema.yaml"), None),
    "an unrelated file in the checkout's own contracts/": (
        _missing(LEG_ROOT / "contracts" / "unrelated.yaml"), None),
    "a contracts/ directory in /tmp": (
        _missing("/tmp/contracts/manifest.yaml"), None),
    "a contracts/ directory beside the checkout's tree": (
        _missing(LEG_ROOT.parent / "elsewhere" / "contracts" / "x.yaml"),
        None),
    "a contracts/ directory inside the checkout's src/": (
        _missing(LEG_ROOT / "src" / "contracts" / "x.yaml"), None),
    "a validator of the same name elsewhere": (
        "can't open file '/tmp/scripts/validate-ideation-dashboard-"
        "contracts.py': [Errno 2]", None),
    "the consumer validator's refusal": (_CONSUMER_RAISED,
                                         "consumer-schemas"),
    "CONTRACTS_DIR's words in an unrelated assertion": (
        "AssertionError: CONTRACTS_DIR is not set", None),
    "the refusal for another tree's schemas": (
        _CONSUMER_RAISED.replace(str(LEG_ROOT), "/tmp/other-tree"), None),
    "the consumer's refusal beside an unrelated missing module": (
        _CONSUMER_RAISED + "\nModuleNotFoundError: No module named 'foo'",
        None),
    "two reasons' causes in one result": (
        _DOC_HEALTH_RAISED + "\n" + _RAIL_RAISED, None),
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
    assert type(DECLARATION["count"]) is int, (
        f"count must be an integer, not {DECLARATION['count']!r}")
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

def test_the_reasons_are_drawn_from_the_four_the_rulings_admit():
    """All four are declared while each has an entry. A reason leaves with
    its last entry (`consumer-schemas` with T061's), and a fifth needs a
    ruling before it needs a line in `RULED_REASONS`."""
    assert set(REASONS) <= set(RULED_REASONS), sorted(REASONS)
    for reason_id, reason in REASONS.items():
        assert reason["ruled"].startswith(RULED_REASONS[reason_id]), (
            reason_id, reason["ruled"])
    assert set(EVIDENCE) == set(RULED_REASONS), (
        "each admitted reason needs its evidence in this module")


def test_the_consumer_schemas_are_tests_test_snapshot_py_s_alone():
    """R1Q25 (b): one narrow exclusion, for one schema-reading suite, until
    7.3 lands. T061 clears the entry, and the reason leaves with it."""
    naming = [entry["path"] for entry in ENTRIES
              if "consumer-schemas" in entry["reasons"]]
    if "consumer-schemas" not in REASONS:
        assert naming == [], naming
        return
    assert REASONS["consumer-schemas"].get("only") == ["tests/test_snapshot.py"]
    assert naming == ["tests/test_snapshot.py"], naming


def test_every_entry_names_a_test_file_this_checkout_carries():
    paths = [entry["path"] for entry in ENTRIES]
    assert len(set(paths)) == len(paths), "a file is listed twice"
    assert paths == sorted(paths), "the entries are not in path order"
    for path in paths:
        rel = PurePosixPath(path)
        assert path == rel.as_posix(), f"{path} is not written plainly"
        assert rel.parts[:1] == ("tests",) and len(rel.parts) == 2, path
        assert rel.name.startswith("test_") and rel.suffix == ".py", path
        assert (LEG_ROOT / rel).is_file(), f"{path} is not in this checkout"
    assert THIS_FILE not in paths, (
        "this module checks the exclusion, and cannot be excluded by it")


@pytest.mark.parametrize("case", sorted(EVIDENCE_CASES))
def test_the_evidence_takes_each_cause_as_raised_and_alone(case):
    """Each reason takes its cause as raised, and only when that cause is
    all the result shows. Otherwise a listed file that gained an unrelated
    failure could have it hidden under a declared reason: a quoted phrase, an
    unrelated missing file beside a known one, or a look-alike path."""
    text, expected = EVIDENCE_CASES[case]
    taken = [reason for reason, matches in EVIDENCE.items() if matches(text)]
    assert taken == ([expected] if expected else []), (text, taken)


# ---------------------------------------------------------------------------
# The root conftest takes the declaration into effect, and refuses a broken one.
# ---------------------------------------------------------------------------

def test_the_root_conftest_admits_the_same_four_reasons(request):
    """The conftest refuses any other reason at load, and a reason whose
    `ruled` does not start with its ruling. This holds its table and this
    module's to one, so neither can admit a fifth, or re-rule one, alone."""
    root = _root_conftest(request.config)
    assert dict(root.ADMITTED_REASONS) == RULED_REASONS


def test_the_root_conftest_holds_the_consumer_schemas_to_one_file(request):
    """R1Q25 (b) admits the consumer's schemas for `tests/test_snapshot.py`
    alone. The conftest refuses a declaration that widens, drops or moves
    that, so the ruling holds in every run, not only one that runs this
    module."""
    root = _root_conftest(request.config)
    assert root.RULED_FILES == {"consumer-schemas": ("tests/test_snapshot.py",)}


def test_the_root_conftest_names_this_module_as_the_check(request):
    """The conftest refuses an entry naming the check, since excluding it
    would drop the check, and its own refusal of that, from every run."""
    root = _root_conftest(request.config)
    assert root.DECLARED_EXCLUSION_CHECK == THIS_FILE


def test_the_root_conftest_derives_collect_ignore_from_the_file(request):
    root = _root_conftest(request.config)
    assert root.collect_ignore == [entry["path"] for entry in ENTRIES]


def _with_entry(declaration: dict, entry: dict) -> None:
    """Add an entry where path order puts it, and move the count with it, so
    only the rule under test is broken."""
    declaration["entries"].append(entry)
    declaration["entries"].sort(key=lambda listed: listed["path"])
    declaration["count"] = len(declaration["entries"])


def _consumer_schemas_on(declaration: dict, only: list, *,
                         drop_from_snapshot: bool = False) -> None:
    """Name the consumer's schemas on `tests/test_canvas.py` too, set their
    `only`, and, if asked, take them off `tests/test_snapshot.py`. `only`
    stays exact, so only R1Q25 (b)'s one-file rule is broken."""
    for entry in declaration["entries"]:
        if entry["path"] == "tests/test_canvas.py":
            entry["reasons"] = [*entry["reasons"], "consumer-schemas"]
        if drop_from_snapshot and entry["path"] == "tests/test_snapshot.py":
            entry["reasons"] = ["doc_health"]
    declaration["reasons"][-1]["only"] = only


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
    "schema_version true": (
        lambda d: d.update(schema_version=True),
        "schema_version must be the integer 1"),
    "schema_version 1.0": (
        lambda d: d.update(schema_version=1.0),
        "schema_version must be the integer 1"),
    "count as a float": (
        lambda d: d.update(count=float(d["count"])),
        "count must be an integer"),
    "count as a string": (
        lambda d: d.update(count=str(d["count"])),
        "count must be an integer"),
    "a reason id that is not a token": (
        lambda d: d["reasons"][0].update(id="doc health"),
        "is not a lowercase token"),
    "an only naming a file that does not name the reason": (
        lambda d: d["reasons"][1].update(only=["tests/test_canvas.py"]),
        "is not an entry that names it"),
    "a reason no entry names": (
        lambda d: d.update(
            entries=[e for e in d["entries"]
                     if "consumer-schemas" not in e["reasons"]],
            count=d["count"] - 1),
        "is named by no entry"),
    "an unknown key on an entry": (
        lambda d: d["entries"][0].update(reason=["doc_health"]),
        "has an unknown key"),
    "an unknown key at the top": (
        lambda d: d.update(counts=d["count"]), "has an unknown key"),
    "a note that is not text": (
        lambda d: d["entries"][0].update(note=5), "is not a line of text"),
    "a note over two lines": (
        lambda d: d["entries"][0].update(note="one\ntwo"),
        "is not a line of text"),
    "a reason the rulings do not admit": (
        lambda d: d["reasons"][0].update(id="some-other-reason"),
        "is not one the rulings admit"),
    "a reason text over two lines": (
        lambda d: d["reasons"][0].update(reason="one\ntwo"),
        "is not one line"),
    "a reason text broken by a carriage return": (
        lambda d: d["reasons"][0].update(reason="one\rtwo"),
        "is not one line"),
    "the check listed as an entry": (
        lambda d: _with_entry(d, {"path": THIS_FILE,
                                  "reasons": ["doc_health"]}),
        "is the check that holds this declaration"),
    "a file listed again under another spelling": (
        lambda d: _with_entry(d, {"path": "tests/./test_canvas.py",
                                  "reasons": ["doc_health"]}),
        "is not written plainly"),
    "a path with a doubled slash": (
        lambda d: d["entries"][0].update(
            path=d["entries"][0]["path"].replace("tests/", "tests//")),
        "is not written plainly"),
    "an only listing a file twice": (
        lambda d: d["reasons"][1].update(
            only=["tests/test_doxbench_abstract_envelope.py"] * 2),
        "only lists a file twice"),
    "a reason citing another ruling": (
        lambda d: d["reasons"][1].update(
            ruled="R1Q6 (d), openxFactory#656 comment 5817152735"),
        "is ruled by R1Q24 (a)"),
    "an entry naming a reason that is not an id": (
        lambda d: d["entries"][0].update(reasons=[[]]),
        "names a reason that is not an id"),
    "unknown keys of two types": (
        lambda d: d.update({1: "one", "counts": d["count"]}),
        "it has an unknown key: 'counts', 1"),
    "the consumer's schemas widened to a second file": (
        lambda d: _consumer_schemas_on(
            d, ["tests/test_canvas.py", "tests/test_snapshot.py"]),
        "is ruled for ['tests/test_snapshot.py'] alone"),
    "the consumer's schemas moved to another file": (
        lambda d: _consumer_schemas_on(d, ["tests/test_canvas.py"],
                                       drop_from_snapshot=True),
        "is ruled for ['tests/test_snapshot.py'] alone"),
    "the consumer's schemas without their only": (
        lambda d: d["reasons"][-1].pop("only"),
        "is ruled for ['tests/test_snapshot.py'] alone"),
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


#: A key given twice in one mapping, which plain YAML settles by keeping the
#: last: an edit of the committed text, and the key its refusal must name.
KEYS_GIVEN_TWICE = {
    "a second entries list": (
        lambda text: text + ("entries:\n"
                             "  - {path: tests/test_canvas.py, "
                             "reasons: [doc_health]}\n"),
        "entries"),
    "reasons given twice in one entry": (
        lambda text: text.replace(
            "{path: tests/test_canvas.py, reasons: [doc_health]}",
            "{path: tests/test_canvas.py, reasons: [doc_health], "
            "reasons: [status-exemption-rail]}", 1),
        "reasons"),
}


@pytest.mark.parametrize("breakage", sorted(KEYS_GIVEN_TWICE))
def test_the_root_conftest_refuses_a_key_given_twice(breakage, request,
                                                     tmp_path):
    """Plain YAML loads both edits. It keeps the last key and drops the first
    without a word, so the first list, or the first reasons, would go
    undeclared. The root conftest refuses them instead."""
    root = _root_conftest(request.config)
    edit, key = KEYS_GIVEN_TWICE[breakage]
    text = DECLARATION_FILE.read_text(encoding="utf-8")
    edited = edit(text)
    assert edited != text, "the edit no longer applies to the committed text"
    assert isinstance(yaml.safe_load(edited), dict)
    broken = tmp_path / "declared_exclusion.yaml"
    broken.write_text(edited, encoding="utf-8")
    with pytest.raises(root.DeclaredExclusionRefused,
                       match=re.escape(f"gives the key {key!r} twice")):
        root.load_declared_exclusion(broken)


#: Files the loader cannot read, each made from the committed file's bytes.
UNREADABLE = {
    "a file that is not UTF-8": (
        lambda committed: committed + b"\n# \xff\xfe\n"),
    "YAML nested past the recursion limit": (
        lambda committed: b"schema_version: " + b"[" * 5000 + b"]" * 5000
        + b"\n"),
}


@pytest.mark.parametrize("breakage", sorted(UNREADABLE))
def test_the_root_conftest_refuses_a_file_it_cannot_read(breakage, request,
                                                         tmp_path):
    """Bytes that are not UTF-8, and nesting deeper than the parser can
    follow, are refused as unreadable, as a missing file is. Neither crashes
    the conftest."""
    root = _root_conftest(request.config)
    broken = tmp_path / "declared_exclusion.yaml"
    broken.write_bytes(UNREADABLE[breakage](DECLARATION_FILE.read_bytes()))
    with pytest.raises(root.DeclaredExclusionRefused, match="cannot be read"):
        root.load_declared_exclusion(broken)


def test_the_root_conftest_refuses_a_file_that_is_not_there(request,
                                                            tmp_path):
    root = _root_conftest(request.config)
    with pytest.raises(root.DeclaredExclusionRefused, match="cannot be read"):
        root.load_declared_exclusion(tmp_path / "declared_exclusion.yaml")


#: Values no rule expects, each put in every place the declaration has one.
_ODD_VALUES = (None, 0, -1, 1.5, True, "", " ", "x\ny", [], [[]], [{}], {},
               {"a": 1}, [1], ["doc_health", []], "doc_health")
#: Keys no rule expects, one of each YAML scalar type, each added beside an
#: unknown text key.
_ODD_KEYS = (1, None, True, 1.5, "zz")
#: libyaml's dumper where PyYAML has it, since the sweep dumps hundreds of
#: variants. It writes what PyYAML's own dumper writes; only the loading has
#: to be the root conftest's own.
_DUMPER = getattr(yaml, "CSafeDumper", yaml.SafeDumper)


def _places(node, where=()):
    """Every place in the declaration: each mapping value, and the first
    four items of each list, so every reason and its `only` among them."""
    if isinstance(node, dict):
        items = list(node.items())
    elif isinstance(node, list):
        items = list(enumerate(node[:4]))
    else:
        return
    for step, value in items:
        yield where + (step,)
        yield from _places(value, where + (step,))


def _at(node, where):
    for step in where:
        node = node[step]
    return node


def _cut_down(declaration: dict) -> dict:
    """The committed declaration with its four reasons and, for each, only
    the first entry that names it. Every rule still has something to hold,
    a two-reason entry and `only` among them, and it loads in a fraction of
    the time."""
    cut = copy.deepcopy(declaration)
    kept = []
    for reason in cut["reasons"]:
        first = next(entry for entry in cut["entries"]
                     if reason["id"] in entry["reasons"])
        if first not in kept:
            kept.append(first)
    cut["entries"] = sorted(kept, key=lambda entry: entry["path"])
    cut["count"] = len(cut["entries"])
    return cut


def test_the_root_conftest_refuses_rather_than_crashes(request, tmp_path):
    """A malformed declaration is REFUSED, naming its rule. Anything else it
    raised would stop the run without saying which rule broke. So each odd
    value goes in each place of a declaration cut down from the committed
    one, and each odd key into each of its mappings, and every load must
    return or refuse."""
    root = _root_conftest(request.config)
    base = _cut_down(_load())
    broken = tmp_path / "declared_exclusion.yaml"
    broken.write_text(yaml.safe_dump(base, sort_keys=False), encoding="utf-8")
    assert root.load_declared_exclusion(broken) == base
    variants = []
    for where in _places(base):
        for odd in _ODD_VALUES:
            variant = copy.deepcopy(base)
            _at(variant, where[:-1])[where[-1]] = copy.deepcopy(odd)
            variants.append((f"{where} := {odd!r}", variant))
    mappings = [()] + [where for where in _places(base)
                       if isinstance(_at(base, where), dict)]
    for where in mappings:
        for key in _ODD_KEYS:
            variant = copy.deepcopy(base)
            _at(variant, where).update({key: 1, "zz-unknown": 1})
            variants.append((f"{where} + key {key!r}", variant))
    crashed = []
    for label, variant in variants:
        broken.write_text(yaml.dump(variant, Dumper=_DUMPER, sort_keys=False),
                          encoding="utf-8")
        try:
            root.load_declared_exclusion(broken)
        except root.DeclaredExclusionRefused:
            continue
        except Exception as exc:  # what escapes the refusal is the finding
            crashed.append(f"{label}: {type(exc).__name__}: {exc}")
    assert len(variants) > 500, len(variants)
    assert crashed == [], (
        f"{len(crashed)} of {len(variants)} declarations crash the loader "
        "instead of being refused:\n" + "\n".join(crashed[:20]))


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
