"""Put this leg's ``src/`` layout on ``sys.path`` for pytest.

Created by the OQ-O scaffold-levelling pass (openxFactory#656) before any
carved content arrives; ``pyproject.toml`` records why the import root has to
exist at all. That file's ``[tool.pytest.ini_options] pythonpath = ["src"]``
does this same job whenever pytest reads that table; this module is the belt
to that pair of braces — it also runs under a runner invoked against a
different ini, and it is the root of the conftest chain that the suites
arriving under ``tests/`` are collected beneath.

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"

if SRC.is_dir():
    _src = str(SRC)
    if _src not in sys.path:
        sys.path.insert(0, _src)


# ---------------------------------------------------------------------------
# THE HOST'S REGISTRATION, MADE AT TEST-PROCESS START (§ 4.4, RULING C2).
#
# `openxdox` is the domain-mapping CORE and ships NO domain's words: since
# § 4.4 the lifecycle engine reads its status vocabulary, terminal statuses and
# immutability point from a profile a DESCENDANT registers at process start
# (RULED ASK-4 Q1/Q5, openxFactory#656 comment 5634195861). A suite that drives
# the engine is a host like any other, so it makes the host's call here, in the
# root of the conftest chain — which IS process start for a pytest run. That is
# not a test convenience standing in for the contract; it is the contract,
# exercised.
#
# The profile is the VENDORED FIXTURE — openXdox-spec's worked example of
# openxFactory's own engineering profile, carrying the corrected nine-word
# taxonomy. The REAL instance is authored at `opensoft/openxFactory` and
# registered by ITS adapter; nothing under `src/` loads this file.
#
# It is registered UNCONDITIONALLY and never behind a try/except: a suite that
# silently ran with no profile would be a suite in which the refusal this slice
# exists to install looks like a passing test.
from openxdox import domain_profile as _domain_profile  # noqa: E402

DOMAIN_PROFILE_FIXTURE = (
    Path(__file__).resolve().parent / "tests" / "fixtures"
    / "openxfactory-engineering-profile.yaml")

_domain_profile.register(_domain_profile.load(DOMAIN_PROFILE_FIXTURE))


# ---------------------------------------------------------------------------
# THE DECLARED EXCLUSION, TAKEN INTO EFFECT (plan 034 task T041; requirement
# 9, first scenario).
#
# `tests/declared_exclusion.yaml` lists the test files a lone checkout cannot
# run, each with its reason, and their count. It acts here, in two ways:
#   * `collect_ignore` below is derived from its entries. So a run that loads
#     this conftest collects the whole suite less those files, and there is no
#     second list to keep. A file named on the command line is still collected,
#     because pytest collects an initial path whatever `collect_ignore` says.
#     That is how `tests/test_declared_exclusion.py` runs each one alone.
#   * `pytest_terminal_summary` below prints the exclusion at the end of the
#     run as an OPEN extraction: the count, each reason with how many files
#     name it, and each file with its reasons. It prints under `-q` as well.
#
# The declaration is held to its rules when it loads, and a broken rule
# REFUSES the run, naming the rule. A declaration that loaded anyway would
# exclude a set nobody declared, and the run would look green for it.
#
# `--noconftest` skips all of this. So a run that must report the exclusion,
# as FR-006 requires, is one that loads this conftest.
# ---------------------------------------------------------------------------
import re  # noqa: E402
from pathlib import PurePosixPath  # noqa: E402
from typing import NoReturn  # noqa: E402

import yaml as _yaml  # noqa: E402

_LEG_ROOT = Path(__file__).resolve().parent
DECLARED_EXCLUSION_FILE = _LEG_ROOT / "tests" / "declared_exclusion.yaml"
DECLARED_EXCLUSION_KIND = "declared-test-exclusion"
_TOP_KEYS = {"schema_version", "kind", "count", "reasons", "entries"}
_REASON_FIELDS = ("id", "reason", "ruled", "open_until")
_REASON_KEYS = {*_REASON_FIELDS, "only"}
_ENTRY_KEYS = {"path", "reasons", "note"}
#: A reason id is printed in a comma-separated list, so it is one plain token.
_REASON_ID = re.compile(r"[a-z][a-z0-9_-]*")
#: The reasons the rulings admit, and no other, each with the ruling that
#: admits it, which its `ruled` text starts with: R1Q6 (d) (`doc_health`,
#: openxFactory#656 comment 5817152735); R1Q24 (a) (the rail and the
#: contracts) and R1Q25 (b) (the consumer's schemas), comment 5850003126. A
#: fifth needs a ruling before it needs a line here.
ADMITTED_REASONS = {
    "doc_health": "R1Q6 (d)",
    "status-exemption-rail": "R1Q24 (a)",
    "openxfactory-contracts": "R1Q24 (a)",
    "consumer-schemas": "R1Q25 (b)",
}
#: The check that holds this declaration to its word. Listed as an entry, it
#: would drop out of every run that loads this conftest, and so would the
#: check's own refusal of that.
DECLARED_EXCLUSION_CHECK = "tests/test_declared_exclusion.py"


class DeclaredExclusionRefused(Exception):
    """`tests/declared_exclusion.yaml` breaks one of its own rules."""


def _is_integer(value) -> bool:
    """An integer as YAML writes one. Not a `bool`, which Python counts as an
    `int`, and not a float, which compares equal to one."""
    return type(value) is int


def _is_one_line(text: str) -> bool:
    """Text the run can print as one line: no line break of any kind, a
    trailing one included."""
    return text.splitlines() == [text]


def _unknown_keys(mapping: dict, known: set) -> str:
    """The keys of `mapping` that `known` lacks, for a refusal to name. A YAML
    key need not be text, and keys of two types do not sort. So each is named
    by its repr, and the names are sorted, never the keys."""
    return ", ".join(sorted(repr(key) for key in mapping if key not in known))


class _KeyGivenTwice(Exception):
    """One mapping in the declaration gives the same key twice."""

    def __init__(self, key, line: int):
        super().__init__(key, line)
        self.key, self.line = key, line


class _DeclarationLoader(_yaml.SafeLoader):
    """PyYAML's safe loader, except that a mapping giving one key twice is
    refused. PyYAML keeps the last and drops the first without a word. So a
    second `entries:` would un-declare every file the first one listed, and a
    `reasons:` given twice in one entry would swap that entry's reasons."""

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                given_twice = key in seen
            except TypeError:  # unhashable: PyYAML refuses that key itself
                continue
            if given_twice:
                raise _KeyGivenTwice(key, key_node.start_mark.line + 1)
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def _read_declaration(text: str):
    """`yaml.safe_load`, through the loader that refuses a key given twice."""
    loader = _DeclarationLoader(text)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


def load_declared_exclusion(path: Path = DECLARED_EXCLUSION_FILE) -> dict:
    """The declaration, held to the rules its own header states.

    Refuses, naming the broken rule, rather than return a set nobody declared.
    """

    def refuse(rule: str) -> NoReturn:
        raise DeclaredExclusionRefused(
            f"{path.name} is refused: {rule}. The run stops here rather than "
            "exclude a set nobody declared (plan 034 T041).")

    try:
        data = _read_declaration(path.read_text(encoding="utf-8"))
    except _KeyGivenTwice as exc:
        refuse(f"it gives the key {exc.key!r} twice in one mapping (line "
               f"{exc.line}), and YAML would keep only the last")
    except (OSError, UnicodeDecodeError, RecursionError,
            _yaml.YAMLError) as exc:
        # Not there, not UTF-8, nested deeper than the parser can follow, or
        # not YAML: each is refused as unreadable, and none is a crash.
        refuse(f"it cannot be read ({type(exc).__name__}: {exc})")
    if not isinstance(data, dict):
        refuse("it is not a mapping")
    unknown = _unknown_keys(data, _TOP_KEYS)
    if unknown:
        refuse(f"it has an unknown key: {unknown}")
    if data.get("kind") != DECLARED_EXCLUSION_KIND:
        refuse(f"its kind must be {DECLARED_EXCLUSION_KIND!r}")
    if not (_is_integer(data.get("schema_version"))
            and data["schema_version"] == 1):
        refuse("its schema_version must be the integer 1, not "
               f"{data.get('schema_version')!r}")

    reasons = data.get("reasons")
    if not isinstance(reasons, list) or not reasons:
        refuse("it declares no reasons")
    ids: list[str] = []
    for reason in reasons:
        if not (isinstance(reason, dict) and all(
                isinstance(reason.get(field), str) and reason[field].strip()
                for field in _REASON_FIELDS)):
            refuse(f"the reason {reason!r} lacks one of "
                   f"{', '.join(_REASON_FIELDS)}")
        unknown = _unknown_keys(reason, _REASON_KEYS)
        if unknown:
            refuse(f"the reason {reason['id']} has an unknown key: {unknown}")
        if not _REASON_ID.fullmatch(reason["id"]):
            refuse(f"the reason id {reason['id']!r} is not a lowercase token "
                   "(a letter, then letters, digits, - and _)")
        if reason["id"] not in ADMITTED_REASONS:
            refuse(f"the reason {reason['id']} is not one the rulings admit "
                   f"({', '.join(ADMITTED_REASONS)}); a fifth needs a ruling "
                   "first")
        multiline = [field for field in _REASON_FIELDS
                     if not _is_one_line(reason[field])]
        if multiline:
            refuse(f"the reason {reason['id']}'s {', '.join(multiline)} is "
                   "not one line, and the run prints each reason on one line")
        ruling = ADMITTED_REASONS[reason["id"]]
        if not reason["ruled"].startswith(ruling):
            refuse(f"the reason {reason['id']} is ruled by {ruling}, but its "
                   f"ruled reads {reason['ruled']!r}")
        ids.append(reason["id"])
    if len(set(ids)) != len(ids):
        refuse("a reason id is declared twice")

    entries = data.get("entries")
    if not isinstance(entries, list):
        refuse("its entries are not a list")
    paths: list[str] = []
    for entry in entries:
        if not (isinstance(entry, dict)
                and isinstance(entry.get("path"), str)):
            refuse(f"the entry {entry!r} names no path")
        unknown = _unknown_keys(entry, _ENTRY_KEYS)
        if unknown:
            refuse(f"{entry['path']} has an unknown key: {unknown}")
        rel = PurePosixPath(entry["path"])
        if (rel.is_absolute() or ".." in rel.parts or len(rel.parts) != 2
                or rel.parts[0] != "tests" or not rel.name.startswith("test_")
                or rel.suffix != ".py"):
            refuse(f"{entry['path']} is not a tests/test_*.py path")
        if entry["path"] != rel.as_posix():
            refuse(f"{entry['path']} is not written plainly, as "
                   f"{rel.as_posix()}, so one file could be listed twice "
                   "under two spellings")
        if entry["path"] == DECLARED_EXCLUSION_CHECK:
            refuse(f"{entry['path']} is the check that holds this "
                   "declaration, and as an entry it would drop out of every "
                   "run that loads this conftest")
        if not (_LEG_ROOT / rel).is_file():
            refuse(f"{entry['path']} names no file in this checkout")
        named = entry.get("reasons")
        if not isinstance(named, list) or not named:
            refuse(f"{entry['path']} carries no reason")
        if not all(isinstance(name, str) for name in named):
            refuse(f"{entry['path']} names a reason that is not an id: "
                   f"{named!r}")
        undeclared =[name for name in named if name not in ids]
        if undeclared:
            refuse(f"{entry['path']} names {undeclared}, which is not a "
                   "declared reason")
        if len(set(named)) != len(named):
            refuse(f"{entry['path']} names one reason twice")
        note = entry.get("note")
        if note is not None and not (isinstance(note, str) and note.strip()
                                     and _is_one_line(note)):
            refuse(f"{entry['path']}'s note is not a line of text")
        paths.append(entry["path"])
    if len(set(paths)) != len(paths):
        refuse("a file is listed twice")
    if paths != sorted(paths):
        refuse("its entries are not in path order")

    for reason in reasons:
        naming = [entry["path"] for entry in entries
                  if reason["id"] in entry["reasons"]]
        if not naming:
            refuse(f"the reason {reason['id']} is named by no entry. A "
                   "cleared reason leaves the declaration with its last entry")
        only = reason.get("only")
        if only is None:
            continue
        if not (isinstance(only, list) and only
                and all(isinstance(item, str) for item in only)):
            refuse(f"the reason {reason['id']}'s only is not a list of paths")
        if len(set(only)) != len(only):
            refuse(f"the reason {reason['id']}'s only lists a file twice")
        absent =[item for item in only if item not in naming]
        if absent:
            refuse(f"the reason {reason['id']} is for {only} alone, but "
                   f"{absent} is not an entry that names it")
        outside = [item for item in naming if item not in only]
        if outside:
            refuse(f"the reason {reason['id']} is for {only} alone, but "
                   f"{outside} name it")

    count = data.get("count")
    if not _is_integer(count):
        refuse(f"its count must be an integer, not {count!r}")
    if count != len(entries):
        refuse(f"its count is {count!r}, but it lists {len(entries)} entries")
    return data


DECLARED_EXCLUSION = load_declared_exclusion()

collect_ignore = [entry["path"] for entry in DECLARED_EXCLUSION["entries"]]


def _files(n: int) -> str:
    return f"{n} file" if n == 1 else f"{n} files"


def pytest_terminal_summary(terminalreporter):
    """Report the declared exclusion as an OPEN extraction (FR-006)."""
    entries = DECLARED_EXCLUSION["entries"]
    where = DECLARED_EXCLUSION_FILE.relative_to(_LEG_ROOT).as_posix()
    write = terminalreporter.write_line
    terminalreporter.write_sep("=", "open extraction: the declared exclusion")
    count = DECLARED_EXCLUSION["count"]
    write(f"declared exclusion: {_files(count)}, listed in {where} and left "
          "out of this run. It is an OPEN extraction: each file runs again "
          "once its reason is cleared.")
    for reason in DECLARED_EXCLUSION["reasons"]:
        named = sum(reason["id"] in entry["reasons"] for entry in entries)
        write(f"  reason {reason['id']} ({_files(named)}): "
              f"{reason['reason']}; open until {reason['open_until']}; "
              f"ruled {reason['ruled']}")
    for entry in entries:
        write(f"  excluded {entry['path']}: {', '.join(entry['reasons'])}")
