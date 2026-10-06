#!/usr/bin/env python3
"""The "unedited by the arc" check of F5.2 and 12.5's falsifier, with the
reviewed allow-list subtracted (plan 034 T059; T007's batch C).

WHAT IT REPLACES. #1144's F5.2 (5.4a's falsifier) and 12.5's falsifier each end
the same way. They list the arc's landings in this repository
(`git log --first-parent --grep='^Arc: neutral-product-standalone-operability$'
"$ARC_BASE..HEAD"`), collect every path each landing touched against the main
before it (`git diff --name-only "$c^1" "$c"`), and refuse if any of those paths
is one of their protected suites. T007's batch C amends both (RULED R1Q7 (a),
openxFactory#656 comment `5817152735`): the check SUBTRACTS the edits entered in
this repository's reviewed allow-list, `tests/protected_suite_respellings.yaml`,
and it must validate, before trusting any subtraction, that the landing's
actual diff for that path contains ONLY the entry's recorded text. A path whose
landing diff does not match stays refused, exactly like an unentered edit.
Batch C gives the wiring to T059 and T086. This is T059's.

HOW EACH FALSIFIER CALLS IT. The protected set and the landings are computed in
the falsifier's own block, as #1144 writes them. The last step, the inline
Python that intersected them, becomes this call, from the checkout's root:

    python3 scripts/protected_suites.py --chains --landings="$(cat "$W/x-arc.txt")" \
        --suites="$(cat "$W/gen-suites.txt")"                                   # F5.2
    python3 scripts/protected_suites.py --landings="$(cat "$W/x-arc.txt")" \
        --suites="$(cat "$W/governed.txt")"                                     # 12.5

(`--chains` is F5.2's alone, since T061; see SEVERAL EDITS IN ONE LANDING.)

Each option carries its LIST, one item per line, and never a path to one: the
landings, each a full commit id as `git log --format=%H` prints it, and the
protected suites, each `tests/test_<name>.py`. (The `=` keeps a value that
begins with a dash a value.) So the check opens no file a caller names, and it
refuses an item of neither shape (exit 2) rather than handing it to git. The one file it reads is the allow-list, at its fixed path
under the checkout it runs in. It exits 0 when no landing touched a protected
suite outside an entry that holds, 1 when one did (naming each landing and
path), and 2 when its input or the allow-list itself breaks its rules, or when
the checkout does not hold the history a landing needs.

WHEN AN ENTRY HOLDS (the file's own header states the rule, and T060 wrote it).
For a landing L that touches a protected `suite`, an entry for that suite holds
at L when all of these are true:

* `git rev-parse L^1:<suite>` is its `before_blob`, and `git rev-parse
  L:<suite>` is its `after_blob`;
* its `old` text occurs exactly once in the `before_blob` text, starting a
  line (it ends one, by the file's rules), and replacing it with `new` gives
  the `after_blob` text byte for byte;
* the replaced text lies inside the one test the entry names, in the before
  text, and its replacement lies inside that test in the after text. So an
  entry cannot admit an edit to any other test of the suite.
* AN ADDED TEST (plan 034 T061; T007's batch F admits one). Where the named
  test does not exist before the landing, `new` is `old` followed by that test's
  whole definition and blank lines, and nothing else, so the edit adds the one
  test and changes no line it does not add. `old` is then the text the test is
  added after, and may lie in a neighbouring test, which it leaves as it was.

* A NAMED MODULE-LEVEL SPAN (plan 038 T026; R-1 (a), RULED by Brett Heap at
  openxFactory#656 comment 6013547504, "Admitted edit kind (Recommended)", and
  recorded at 12.5's falsifier by T005's batch Q). An `admitted` entry may
  name, in place of `test`, a `span`: one module-level constant or helper
  function of the suite, such as a harness text several tests run or the
  helper that runs it, which lies inside no test. Comment 6016648451 ("Widen
  the spans, served display (Recommended)") names three helpers among the six
  spans, so a function may be one. Its `old` text must then lie inside that
  constant's or function's statement in the before text, and its `new` text
  inside it in the after text, so the entry admits an edit to that one
  statement and to nothing else of the suite. A span is one module-level
  assignment to that one name, or one module-level function of that name,
  and it must exist before the landing and at it: no span is added, and a
  class, an import or a second binding of the name is never one. A
  respelling names its test, never a span, and a test is never a span.

A landing that touches a protected suite is admitted for that suite only if one
entry holds at it, or, in F5.2's call, a CHAIN of entries does. Every other
protected path it touches is refused.

SEVERAL EDITS IN ONE LANDING (plan 034 T061; T007's batch K, on Brett's ruling
at openxFactory#656 comment 5916000030). A landing may edit one suite in more
than one test: T061 edits `tests/test_snapshot.py` twice and
`tests/test_snapshot_validation_launch.py` nine times. Each edit is its own
entry, and the entries for that suite are applied in the order they are listed,
each to the text the one before it leaves. They admit the landing together when:

* the first one's `before_blob` is the suite before the landing, and the last
  one's `after_blob` is the suite at it;
* each one in between has, as its `after_blob`, the git blob id of the text its
  own edit leaves (`git hash-object` of that text, which no commit need hold),
  and the next one's `before_blob` is that id, as the chain rule below already
  requires of any two entries for one suite;
* each one holds on its own texts, by every condition above: its `old` occurs
  once, starting a line; its replacement gives its `after_blob` text; and the
  edit lies inside its one named test, or adds only it;
* they all name the same landing.

So the landing's diff for that suite is exactly those entries' recorded texts,
each inside its own test, and nothing else. Every entry of the chain is spent by
that landing.

F5.2'S CALL ALONE. Brett's ruling admits T061's ten under F5.2, whose protected
set they are in, and 12.5's governed set holds neither of their suites. So a
chain is admitted only when the call passes `--chains`, which F5.2's does and
12.5's does not. Without it, a landing's edits to one suite are admitted by one
entry or not at all, as T059 wired the check, and a chain is refused.

AN ENTRY ADMITS ONE LANDING (Copilot on openXdox-code#35). The landings are
taken oldest first, and an entry that has admitted one is spent: a later
landing that repeats the same edit, after the suite came back to the entry's
`before_blob`, is refused unless an entry of its own holds. An entry names its
landing by pull request, not by commit (T019's rule), so the commit it admits
is found here, once.

THE ALLOW-LIST'S OWN RULES are checked before anything is subtracted, and a
file that breaks one refuses the whole check (exit 2) rather than subtracting
less: `schema_version` 1, `kind` `protected-suite-respellings`, no key given
twice, and each entry carrying exactly its declared keys (an admitted entry
names a `test` or a `span`, never both), with blobs that are
full object ids, `old` and `new` that are whole lines ending in a newline, and
entries for one suite that chain (each `before_blob` is the previous entry's
`after_blob`).

WHAT IT DOES NOT DO. It does not decide what is protected, and it does not find
the landings: both are the falsifier's, so the check here cannot drift from the
text #1144 ratified. It reads the allow-list from the working tree, at the head
the falsifier runs at. A CREATED file: no row in openxFactory's
`docs/opendox-carve-manifest.yaml` (RULED OQ-C).
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ALLOW_LIST = Path("tests") / "protected_suite_respellings.yaml"
KIND = "protected-suite-respellings"
SCHEMA_VERSION = 1

#: Every key an entry may carry, and the keys each kind of edit requires.
COMMON_KEYS = frozenset({"suite", "test", "landing", "edit", "ruled", "review",
                         "before_blob", "after_blob", "old", "new"})
EDIT_KEYS = {"respelling": frozenset({"respelled"}),
             "admitted": frozenset({"reason"})}
#: R-1 (a) (plan 038 T026): the key an `admitted` entry names IN PLACE OF
#: `test` when its edit lies in a module-level constant or helper function of
#: the suite.
SPAN_KEY = "span"
SPAN_EDITS = frozenset({"admitted"})

#: A full object id: a blob in an entry, or a landing's commit in the input.
_BLOB = re.compile(r"[0-9a-f]{40}")
_COMMIT = _BLOB
#: ASCII only: a suite, a test or a landing is never spelled outside it.
_SUITE = re.compile(r"tests/test_\w+\.py", re.ASCII)
_LANDING = re.compile(r"opensoft/openXdox-code#[1-9]\d*", re.ASCII)
_TEST = re.compile(r"test_\w+", re.ASCII)
#: A span is a module-level name, and never a test's.
_SPAN = re.compile(r"[A-Za-z_]\w*", re.ASCII)


class AllowListInvalid(ValueError):
    """The allow-list breaks one of its own rules. Nothing is subtracted."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """YAML keeps only the last of two equal keys. Refuse the second instead."""


def _mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False):
    seen: set[Any] = set()
    for key_node, _value in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, (str, int, float, bool)) and key is not None:
            raise AllowListInvalid(
                f"a key is a {type(key).__name__} (line {key_node.start_mark.line + 1}), "
                "and every key is a plain scalar")
        if key in seen:
            raise AllowListInvalid(
                f"the key {key!r} is given twice (line {key_node.start_mark.line + 1})")
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AllowListInvalid(f"{where} is not a non-empty text")
    return value


def _whole_lines(value: Any, where: str) -> str:
    text = _text(value, where)
    if not text.endswith("\n"):
        raise AllowListInvalid(f"{where} does not end in a newline, so it is not whole lines")
    return text


def _document(path: Path) -> dict:
    """The allow-list as a mapping, read with no key given twice."""
    try:
        raw = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except OSError as exc:
        raise AllowListInvalid(f"{path} could not be read: {exc}") from exc
    except yaml.YAMLError as exc:
        raise AllowListInvalid(f"{path} is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise AllowListInvalid(f"{path} is not a mapping")
    if set(raw) != {"schema_version", "kind", "entries"}:
        raise AllowListInvalid(
            f"{path} carries {sorted(map(str, raw))}, not schema_version, kind and entries")
    version = raw["schema_version"]
    # The integer itself: not a bool, and not `1.0`, which equals 1 in Python.
    if type(version) is not int or version != SCHEMA_VERSION:
        raise AllowListInvalid(f"schema_version is {version!r}, not {SCHEMA_VERSION}")
    if raw["kind"] != KIND:
        raise AllowListInvalid(f"kind is {raw['kind']!r}, not {KIND!r}")
    if not isinstance(raw["entries"], list):
        raise AllowListInvalid("entries is not a list")
    return raw


def _check_keys(entry: Any, where: str) -> None:
    """An entry is a mapping carrying exactly its kind's keys, each a text."""
    if not isinstance(entry, dict):
        raise AllowListInvalid(f"{where} is not a mapping")
    edit = entry.get("edit")
    if not isinstance(edit, str) or edit not in EDIT_KEYS:
        raise AllowListInvalid(f"{where}: edit is {edit!r}, not one of {sorted(EDIT_KEYS)}")
    wanted = COMMON_KEYS | EDIT_KEYS[edit]
    if SPAN_KEY in entry:
        # R-1 (a): a span stands IN PLACE OF the test, and only an admitted
        # entry names one. Naming both still fails the key check below.
        if edit not in SPAN_EDITS:
            raise AllowListInvalid(
                f"{where}: names a span, and only an admitted entry may (R-1 (a)); "
                f"a {edit} entry names its test")
        wanted = (wanted - {"test"}) | {SPAN_KEY}
    if set(entry) != wanted:
        raise AllowListInvalid(
            f"{where}: carries {sorted(map(str, entry))}, and a {edit} entry "
            f"carries exactly {sorted(wanted)}")
    for key in wanted - {"old", "new"}:
        _text(entry[key], f"{where}: {key}")


def _check_spellings(entry: dict, where: str) -> None:
    """The suite, test, landing and blobs are each spelled as the rules say."""
    if not _SUITE.fullmatch(entry["suite"]):
        raise AllowListInvalid(f"{where}: suite {entry['suite']!r} is not tests/test_<name>.py")
    if SPAN_KEY in entry:
        span = entry[SPAN_KEY]
        if not _SPAN.fullmatch(span) or _TEST.fullmatch(span):
            raise AllowListInvalid(
                f"{where}: span {span!r} is not a module-level name, or is a test's")
    elif not _TEST.fullmatch(entry["test"]):
        raise AllowListInvalid(f"{where}: test {entry['test']!r} is not a test's name")
    if not _LANDING.fullmatch(entry["landing"]):
        raise AllowListInvalid(
            f"{where}: landing {entry['landing']!r} is not opensoft/openXdox-code#<n>")
    for key in ("before_blob", "after_blob"):
        if not _BLOB.fullmatch(entry[key]):
            raise AllowListInvalid(f"{where}: {key} is not a full object id")


def _check_texts(entry: dict, where: str) -> None:
    """`old` and `new` are whole lines, and differ."""
    old = _whole_lines(entry["old"], f"{where}: old")
    new = _whole_lines(entry["new"], f"{where}: new")
    if old == new:
        raise AllowListInvalid(f"{where}: old and new are the same text")


def load_allow_list(path: Path) -> list[dict]:
    """The allow-list's entries, in landing order, once every rule holds."""
    entries = _document(path)["entries"]
    last_after: dict[str, str] = {}
    for n, entry in enumerate(entries, 1):
        where = f"entry {n}"
        _check_keys(entry, where)
        _check_spellings(entry, where)
        _check_texts(entry, where)
        suite = entry["suite"]
        if suite in last_after and entry["before_blob"] != last_after[suite]:
            raise AllowListInvalid(
                f"{where}: its before_blob is not the after_blob of the entry before it "
                f"for {suite}, so the two do not chain")
        last_after[suite] = entry["after_blob"]
    return entries


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(("git", "-C", str(repo), *args), check=True,
                          capture_output=True, text=True).stdout


def _blob(repo: Path, revision: str, path: str) -> str | None:
    done = subprocess.run(("git", "-C", str(repo), "rev-parse", "--verify", "--quiet",
                           f"{revision}:{path}"), capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else None


def _blob_text(repo: Path, blob: str) -> str:
    return subprocess.run(("git", "-C", str(repo), "cat-file", "blob", blob),
                          check=True, capture_output=True).stdout.decode("utf-8")


def _test_lines(text: str, test: str) -> tuple[int, int] | None:
    """The 1-based line span of the module-level test function `test`, or None."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    found = [node for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
             and node.name == test]
    if len(found) != 1:
        return None
    node = found[0]
    return min([node.lineno, *(d.lineno for d in node.decorator_list)]), node.end_lineno


def _span_lines(text: str, span: str) -> tuple[int, int] | None:
    """The 1-based line span of the module-level constant or function `span`,
    or None.

    R-1 (a) (plan 038 T026): a span is ONE module-level assignment whose one
    target is the bare name `span`, or ONE module-level function named `span`
    (comment 6016648451 names three helpers among the spans), and no other
    module-level statement binds that name. So a class, an import or a second
    binding is never a span. A function's span starts at its first decorator,
    as a test's does."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    binders = [node for node in _module_scope(tree.body) if span in _module_names(node)]
    if len(binders) != 1 or binders[0] not in tree.body:
        return None
    node = binders[0]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return min([node.lineno, *(d.lineno for d in node.decorator_list)]), node.end_lineno
    if isinstance(node, ast.Assign):
        single = len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
    else:
        single = (isinstance(node, ast.AnnAssign) and node.value is not None
                  and isinstance(node.target, ast.Name))
    return (node.lineno, node.end_lineno) if single else None


def _module_scope(body: list[ast.stmt]):
    """Every statement in module scope: the module's own, and those nested in
    its compound statements (`if`, `try`, `with`, loops), but never those in a
    function's or a class's body, which bind no module-level name."""
    for node in body:
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for field in ("body", "orelse", "finalbody"):
            yield from _module_scope(getattr(node, field, []) or [])
        for handler in getattr(node, "handlers", []) or []:
            yield from _module_scope(handler.body)


def _module_names(node: ast.stmt) -> set[str]:
    """Every name a module-scope statement binds itself (a compound statement's
    nested statements are walked on their own)."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return {(alias.asname or alias.name).split(".")[0] for alias in node.names}
    targets = (node.targets if isinstance(node, ast.Assign)
               else [node.target] if isinstance(node, (ast.AnnAssign, ast.AugAssign,
                                                       ast.For, ast.AsyncFor))
               else [item.optional_vars for item in node.items if item.optional_vars]
               if isinstance(node, (ast.With, ast.AsyncWith))
               else [])
    return {name.id for target in targets for name in ast.walk(target)
            if isinstance(name, ast.Name)}


def _inside(lines: tuple[int, int] | None, text: str, start: int, piece: str) -> bool:
    if lines is None:
        return False
    first_line = text.count("\n", 0, start) + 1
    last_line = first_line + piece.count("\n") - 1
    return lines[0] <= first_line and last_line <= lines[1]


def _inside_the_test(text: str, start: int, piece: str, test: str) -> bool:
    return _inside(_test_lines(text, test), text, start, piece)


def _inside_the_span(text: str, start: int, piece: str, span: str) -> bool:
    """`_inside_the_test`'s rule, amended by R-1 (a) to admit the new kind:
    `piece` lies inside the one module-level constant or function `span`
    names."""
    return _inside(_span_lines(text, span), text, start, piece)


def _only_the_added_test(after_text: str, at: int, old: str, new: str, test: str) -> str | None:
    """None when `new` is `old` followed by the named test's whole definition
    and blank lines, and nothing else; else why not. The test is found in the
    text at the landing, and must lie wholly inside what the edit appended."""
    span = _test_lines(after_text, test)
    if span is None:
        return f"{test} is not one module-level test before the landing or at it"
    if not new.startswith(old):
        return (f"{test} is added by this landing, and the entry's new text does not "
                "begin with its old text, so the edit changes more than it adds")
    first = after_text.count("\n", 0, at + len(old)) + 1
    tail = new[len(old):].splitlines()
    last = first + len(tail) - 1
    if not (first <= span[0] and span[1] <= last):
        return f"{test} does not lie wholly inside the text the entry appends"
    outside = [line for number, line in enumerate(tail, first)
               if not span[0] <= number <= span[1] and line.strip()]
    if outside:
        return (f"the entry appends {len(outside)} line(s) that are not {test}'s own: "
                f"{outside[0].strip()[:60]!r}")
    return None


def entry_holds(repo: Path, landing: str, entry: dict) -> str | None:
    """None when `entry` alone holds at `landing`, else why it does not."""
    suite = entry["suite"]
    before = _blob(repo, f"{landing}^1", suite)
    after = _blob(repo, landing, suite)
    if before != entry["before_blob"]:
        return f"{suite} before the landing is {before}, not the entry's {entry['before_blob']}"
    if after != entry["after_blob"]:
        return f"{suite} at the landing is {after}, not the entry's {entry['after_blob']}"
    return _edit_holds(_blob_text(repo, before), _blob_text(repo, after), entry)


def _hash_text(repo: Path, text: str) -> str:
    """The git blob id `text` would have. Nothing is written to the object store."""
    return subprocess.run(("git", "-C", str(repo), "hash-object", "--stdin"),
                          input=text.encode("utf-8"), check=True,
                          capture_output=True).stdout.decode("ascii").strip()


def chain_holds(repo: Path, landing: str, chain: list[dict]) -> str | None:
    """None when the entries of `chain`, applied in order, admit `landing`'s
    edits to their one suite together, else why they do not. A chain of one is
    `entry_holds`."""
    if len(chain) == 1:
        return entry_holds(repo, landing, chain[0])
    why = _chain_ends_why(repo, landing, chain)
    if why is not None:
        return why
    text = _blob_text(repo, chain[0]["before_blob"])
    last = _blob_text(repo, chain[-1]["after_blob"])
    for step, entry in enumerate(chain, 1):
        following = text.replace(entry["old"], entry["new"], 1)
        why = _step_why(repo, chain, step, text, following, last)
        if why is not None:
            return f"step {step}: {why}"
        text = following
    return None


def _chain_ends_why(repo: Path, landing: str, chain: list[dict]) -> str | None:
    """Why `chain` cannot admit `landing` whatever its steps say, or None: its
    entries name more than one suite or landing, or its ends are not the
    suite before the landing and at it."""
    suite = chain[0]["suite"]
    if any(entry["suite"] != suite for entry in chain):
        return "a chain's entries name more than one suite"
    if any(entry["landing"] != chain[0]["landing"] for entry in chain):
        return "a chain's entries name more than one landing"
    before = _blob(repo, f"{landing}^1", suite)
    if before != chain[0]["before_blob"]:
        return f"{suite} before the landing is {before}, not the chain's {chain[0]['before_blob']}"
    after = _blob(repo, landing, suite)
    if after != chain[-1]["after_blob"]:
        return f"{suite} at the landing is {after}, not the chain's {chain[-1]['after_blob']}"
    return None


def _step_why(repo: Path, chain: list[dict], step: int, text: str, following: str,
              last: str) -> str | None:
    """Why step `step` (1-based) of `chain` does not hold on `text`, the text
    the steps before it leave, or None. `following` is what its edit leaves,
    and `last` the suite at the landing."""
    entry = chain[step - 1]
    if step > 1 and entry["before_blob"] != chain[step - 2]["after_blob"]:
        return "its before_blob is not the after_blob of the step before it"
    if text.count(entry["old"]) != 1:
        return (f"its old text occurs {text.count(entry['old'])} times in the text "
                "the steps before it leave, not once")
    if step == len(chain) and following != last:
        return "the chain's texts do not give the suite at the landing"
    if step < len(chain) and _hash_text(repo, following) != entry["after_blob"]:
        return ("its after_blob is not the blob of the text its edit leaves, so the "
                "chain does not record the text in between")
    return _edit_holds(text, following, entry)


def _edit_holds(before_text: str, after_text: str, entry: dict) -> str | None:
    """None when `entry`'s one edit turns `before_text` into `after_text`,
    inside its named test (or adding only it), else why not."""
    old, new = entry["old"], entry["new"]
    if before_text.count(old) != 1:
        return f"the entry's old text occurs {before_text.count(old)} times before the landing, not once"
    at = before_text.index(old)
    if at and before_text[at - 1] != "\n":
        # Whole lines: the occurrence starts a line, as it ends one.
        return "the entry's old text does not start a line before the landing, so it is not whole lines"
    if before_text.replace(old, new, 1) != after_text:
        return "replacing the entry's old text with its new text does not give the suite at the landing"
    if SPAN_KEY in entry:
        # R-1 (a): the edit lies inside the one module-level constant or
        # function the entry names, before the landing and at it. No span is
        # ever added.
        span = entry[SPAN_KEY]
        if _span_lines(before_text, span) is None:
            return (f"{span} is not one module-level constant or function "
                    "before the landing")
        if not _inside_the_span(before_text, at, old, span):
            return f"the entry's old text is not inside {span} before the landing"
        if not _inside_the_span(after_text, at, new, span):
            return f"the entry's new text is not inside {span} at the landing"
        return None
    if _test_lines(before_text, entry["test"]) is None:
        # An ADDED test (plan 034 T061; T007 batch F admits one): it has no body
        # before the landing to lie inside, so the edit must add it and only it.
        return _only_the_added_test(after_text, at, old, new, entry["test"])
    if not _inside_the_test(before_text, at, old, entry["test"]):
        return f"the entry's old text is not inside {entry['test']} before the landing"
    if not _inside_the_test(after_text, at, new, entry["test"]):
        return f"the entry's new text is not inside {entry['test']} at the landing"
    return None


@dataclass
class Finding:
    landing: str
    path: str
    admitted_by: int | None
    why: str
    #: Every entry (1-based) that admitted it, in order: one, or a chain.
    chain: tuple[int, ...] = ()


def _admitting(repo: Path, landing: str, path: str, entries: list[dict],
               spent: dict[int, str], chains: bool) -> tuple[tuple[int, ...], list[str]]:
    """The entries (1-based) for `path` that admit `landing`, one or (with
    `chains`) a chain, or () and every candidate's reason for not holding. A
    candidate starts at an unspent entry for `path` and, with `chains`, runs on
    through the entries for `path` that follow it in the list, until one
    records the suite at the landing. Without `chains` a candidate is its one
    entry. An entry in `spent` has admitted another landing already and admits
    no second one."""
    reasons = []
    ours = [n for n, entry in enumerate(entries, 1) if entry["suite"] == path]
    after = _blob(repo, landing, path)
    for i, n in enumerate(ours):
        if n in spent:
            reasons.append(f"entry {n}: it admitted {spent[n][:12]} already, "
                           "and an entry admits one landing")
            continue
        run = [n]
        for m in (ours[i + 1:] if chains else ()):
            if entries[run[-1] - 1]["after_blob"] == after or m in spent:
                break
            run.append(m)
        why = chain_holds(repo, landing, [entries[k - 1] for k in run])
        if why is None:
            return tuple(run), []
        label = f"entry {n}" if len(run) == 1 else f"entries {run[0]}-{run[-1]}"
        reasons.append(f"{label}: {why}")
    return (), reasons


def check(repo: Path, landings: list[str], protected: set[str],
          entries: list[dict], *, chains: bool = False) -> list[Finding]:
    """One finding per protected path each landing touched: admitted by the
    entry (1-based) that holds there, or, with `chains` (F5.2's call), by the
    chain of entries that does, or refused with every candidate's reason. The
    landings are taken oldest first, whatever order they come in, and each
    entry admits one of them at most."""
    findings: list[Finding] = []
    spent: dict[int, str] = {}
    ancestors = {landing: int(_git(repo, "rev-list", "--count", landing).strip())
                 for landing in landings}
    for landing in sorted(landings, key=ancestors.__getitem__):
        # --no-renames: a protected suite renamed away is a deletion at its
        # own path, never only the destination's addition.
        touched = {line.strip() for line in
                   _git(repo, "diff", "--no-renames", "--name-only",
                        f"{landing}^1", landing).splitlines()
                   if line.strip()}
        for path in sorted(touched & protected):
            chain, reasons = _admitting(repo, landing, path, entries, spent, chains)
            for n in chain:
                spent[n] = landing
            findings.append(Finding(
                landing, path, chain[0] if chain else None,
                "" if chain else ("; ".join(reasons) or "no entry names this suite"),
                chain))
    return findings


class InputInvalid(ValueError):
    """An item of a list the caller passed is neither a landing nor a suite."""


def _items(text: str, shape: re.Pattern[str], what: str) -> list[str]:
    """The non-empty lines of `text`, each of `shape`, in order."""
    items = [line.strip() for line in text.splitlines() if line.strip()]
    for item in items:
        if not shape.fullmatch(item):
            raise InputInvalid(f"{item!r} is not {what}")
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="The unedited-by-the-arc check, with the reviewed allow-list subtracted.")
    parser.add_argument("--landings", required=True,
                        help="the arc's landings, one full commit id per line")
    parser.add_argument("--suites", required=True,
                        help="the protected suites, one tests/test_<name>.py per line")
    parser.add_argument("--chains", action="store_true",
                        help="admit a chain of entries for one landing's several edits "
                             "to a suite (F5.2's call alone; plan 034 T061, batch K)")
    try:
        args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    repo = Path.cwd()
    try:
        landings = _items(args.landings, _COMMIT, "a full commit id")
        suites = set(_items(args.suites, _SUITE, "a tests/test_<name>.py path"))
    except InputInvalid as exc:
        print(f"FAIL: {exc}, so nothing is checked", file=sys.stderr)
        return 2
    try:
        entries = load_allow_list(repo / ALLOW_LIST)
    except AllowListInvalid as exc:
        print(f"FAIL: {ALLOW_LIST} breaks its own rules, so nothing is subtracted: {exc}",
              file=sys.stderr)
        return 2
    try:
        findings = check(repo, landings, suites, entries, chains=args.chains)
    except subprocess.CalledProcessError as exc:
        # A landing this checkout does not hold, or one with no parent: the
        # history the check needs is not here, which is not a refusal.
        detail = (exc.stderr or "").strip().splitlines()
        print(f"FAIL: git could not read the history the check needs "
              f"({' '.join(map(str, exc.cmd[3:]))}: {detail[0] if detail else exc.returncode}), "
              "so nothing is checked", file=sys.stderr)
        return 2
    return _report(findings)


def _report(findings: list[Finding]) -> int:
    """Print each finding, and answer the exit code: 1 when any is refused."""
    refused = []
    for f in findings:
        if f.admitted_by is not None:
            by = (f"entry {f.admitted_by}" if len(f.chain) <= 1 else
                  f"entries {', '.join(map(str, f.chain))}, in that order,")
            print(f"admitted: {f.landing[:12]} {f.path}, by {by} of {ALLOW_LIST}")
        else:
            print(f"refused:  {f.landing[:12]} {f.path}: {f.why}")
            refused.append(f.path)
    if refused:
        print("FAIL: the arc edited protected suites outside the reviewed allow-list: "
              + ", ".join(sorted(set(refused))), file=sys.stderr)
        return 1
    print(f"ok: {len(findings)} protected edit(s), each entered and holding")
    return 0


if __name__ == "__main__":
    sys.exit(main())
