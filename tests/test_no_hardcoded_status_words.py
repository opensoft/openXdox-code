"""THE RULING C2 GUARD: no domain's status word survives in the engine.

`split-opendox-two-layer-product` `tasks.md` § 4.4, in one box:

    PARAMETERIZE, do not ship one domain's words (RULING C2). The lifecycle
    engine reads its status vocabulary, transitions, authorities and
    immutability point from a domain profile. **A hardcoded status word is a
    defect under `domain-mapping-declaration`.**

§ 4.4's code half moved seventeen occurrences over fifteen lines out of
`gate_console.py` and `generator.py`. This module is what stops the eighteenth
arriving. It is a SOURCE sweep, not an import: it parses the two modules with
`ast` and reads their text, so it runs without `doc_health` — openxFactory's own
corpus machinery, which this leg does not vendor and cannot import (RULED
Q-L8 (b'); `test_dependency_direction.py` enumerates the same reach) — and
therefore keeps working whatever the BUILD arc does to the rest of the suite.

Why a guard rather than a note in the commit message: the literals were not
introduced by anyone careless. They were the obvious way to write the code when
the engine and its one domain lived in the same repository, and they will be the
obvious way again the next time someone adds a status-bearing step. The defect
class needs a test, not a memory.

A CREATED FILE: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "openxdox"

#: The modules § 4.4 names, and the only ones this guard speaks for. Other
#: modules of this package carry `staged` as a DASHBOARD TILE KIND
#: (`doxbench_scope.py`), which is the snapshot's own column vocabulary and a
#: different question from the lifecycle engine's status words.
ENGINE_MODULES = ("gate_console.py", "generator.py")

#: openxFactory's own controlled `Status:` taxonomy — nine words, including the
#: out-of-band `projection` the retraction on `openxFactory#656` (comment
#: `5633989351`) restored. NONE of them belongs in a domain-neutral package.
TAXONOMY_WORDS = frozenset({
    "brainstorm", "staged", "draft", "ratified", "standard",
    "superseded", "retired", "record", "projection",
})

#: The possibles register's terminal pair, hardcoded at the old
#: `gate_console.py:1151` and migrated to a per-kind `terminal_statuses` under
#: RULED ASK-4 Q4. `superseded` is already in the set above; `rejected` is the
#: register's own word and is named here so the pair cannot come back together.
REGISTER_TERMINAL_WORDS = frozenset({"rejected"})

#: The register's other two lifecycle words: `_PROMOTABLE_STATE = "latent"` and
#: a literal `"picked"` check in `gate_console.promotability_refusal`, plus a
#: second `"picked"` literal in `generator._cluster_lineage` — a fix-round
#: review caught the first pair and a sweep for the same word found the third
#: site. All three now resolve through `gate_console._promotable_register_state`
#: / `_picked_register_state` or `generator._picked_register_state`. Named here,
#: like `REGISTER_TERMINAL_WORDS` above, so none of the three can come back.
REGISTER_OTHER_WORDS = frozenset({"latent", "picked"})

WATCHED_WORDS = TAXONOMY_WORDS | REGISTER_TERMINAL_WORDS | REGISTER_OTHER_WORDS

#: `\bword\b` for each watched word — a STANDALONE-TOKEN match, not a bare
#: substring search: it catches `f"status={state} (staged)"` (a longer
#: Constant part the old two narrow patterns both missed) without also
#: matching a word merely embedded in a longer one (`unstaged` does not trip
#: `staged`).
_STANDALONE_WORD_RE = {w: re.compile(rf"\b{re.escape(w)}\b") for w in WATCHED_WORDS}

#: Individually audited f-string literal parts, by (module, JoinedStr lineno),
#: where a taxonomy word appears as ordinary English prose or an established
#: identifier — never as a value this engine compares against or writes into
#: a status field. A NEW finding is not silenced by adding a line here: it is
#: read first, and only added if it really is prose, with the same kind of
#: justification as its neighbours.
PROSE_EXEMPT: frozenset[tuple[str, int]] = frozenset({
    ("gate_console.py", 315),   # "the record's provenance names one of" (OutputBoundary refusal prose)
    ("gate_console.py", 319),   # the same sentence's other raise site
    ("gate_console.py", 829),   # "gate-action record " — the audit-record noun, not a status
    ("gate_console.py", 1066),  # "'Returned drafts' record" / "returned draft proposals" — README/INDEX prose
    ("gate_console.py", 1675),  # "draft workspace" / "draft ideas" / "draft-proposal convention" — prose
    ("gate_console.py", 1848),  # ".ratification-record.yaml" — a filename, not a written status
    ("gate_console.py", 1851),  # "the ratified state" — prose
})


def _module_source(name: str) -> tuple[str, ast.Module]:
    text = (SRC / name).read_text(encoding="utf-8")
    return text, ast.parse(text)


def _dict_key_nodes(tree: ast.Module) -> set[int]:
    """Every string constant used as a DICT KEY, by node id.

    A key is a field name in a record this engine writes — `{"record": ...}` in
    the demote plan's README step — and not a status claim about anything. The
    sweep has to tell the two apart or it reports a defect that is not one.
    """
    keys: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant):
                    keys.add(id(key))
    return keys


@pytest.mark.parametrize("module", ENGINE_MODULES)
def test_no_status_word_survives_as_a_literal(module):
    """The count that matters is ZERO, in both modules."""
    text, tree = _module_source(module)
    keys = _dict_key_nodes(tree)
    found = [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value in WATCHED_WORDS
        and id(node) not in keys
    ]
    assert not found, (
        f"{module} carries {len(found)} hardcoded status word(s) at "
        f"{[f'line {line}: {word!r}' for line, word in found]}. A hardcoded "
        "status word is a defect under `domain-mapping-declaration` (RULING "
        "C2): ask the registered profile for it instead — `status(<role>)`, "
        "`terminal_statuses(<kind>)` or `destination_status(<act>)` in "
        "`openxdox.domain_profile` — and name the kind through the act that "
        "operates on it rather than by its domain name.")


def _f_string_offenders(text: str, module: str = "<test>") -> list[tuple[int, str, str]]:
    """Every (lineno, literal part, word) where an f-string carries a watched
    word as a standalone token, outside `PROSE_EXEMPT`. Factored out of the
    test below so the SWEEP LOGIC can be proven against a synthetic snippet,
    not only against however `gate_console.py`/`generator.py` happen to read
    today."""
    tree = ast.parse(text)
    return [
        (node.lineno, part.value, word)
        for node in ast.walk(tree)
        if isinstance(node, ast.JoinedStr)
        and (module, node.lineno) not in PROSE_EXEMPT
        for part in node.values
        if isinstance(part, ast.Constant) and isinstance(part.value, str)
        for word in WATCHED_WORDS
        if _STANDALONE_WORD_RE[word].search(part.value)
    ]


@pytest.mark.parametrize("module", ENGINE_MODULES)
def test_no_status_word_survives_inside_an_f_string(module):
    """An f-string's literal halves are `Constant` nodes too, and are swept.

    Matched as a STANDALONE TOKEN (`_STANDALONE_WORD_RE`), not the two narrow
    shapes this test used to check (`"Status: <word>"` and a part that IS just
    the word, nothing else): `f"status={state} (staged)"` carries the word in
    a longer `Constant` part neither of those two shapes recognizes, and a
    sweep that only looked for them would miss it. The wider match is a
    superset of both — anything that used to trip this test still does.

    `PROSE_EXEMPT` names the lines already audited as ordinary English prose
    or an established identifier (a filename, "gate-action record") rather
    than a status value; everything else in these two modules is swept.
    """
    text, _tree = _module_source(module)
    offenders = _f_string_offenders(text, module)
    assert not offenders, (
        f"{module} writes a status word into an f-string at {offenders}; the "
        "word belongs to the registered profile")


def test_the_f_string_sweep_catches_a_word_embedded_in_a_longer_literal():
    """The regression case the second-round review named directly: neither of
    the two shapes this test used to recognize (`"Status: <word>"`, or a part
    that IS just the word) matches a status word sitting beside an
    interpolated value in a longer literal."""
    offenders = _f_string_offenders('state = "x"\nmsg = f"status={state} (staged)"\n')
    assert [word for _lineno, _part, word in offenders] == ["staged"]


def test_the_f_string_sweep_still_catches_the_original_two_shapes():
    """No regression: the wider standalone-token match is a superset of the
    two narrower shapes this test used to check on their own."""
    offenders = _f_string_offenders('word = "x"\na = f"Status: {word}"\nb = f"draft"\n')
    assert {w for _lineno, _part, w in offenders} == {"draft"}


def test_the_f_string_sweep_does_not_flag_a_word_embedded_in_a_longer_word():
    """A STANDALONE token, not a bare substring: `unstaged` must not trip
    `staged`."""
    offenders = _f_string_offenders('x = "y"\nmsg = f"an unstaged {x}"\n')
    assert offenders == []


@pytest.mark.parametrize("module", ENGINE_MODULES)
def test_the_module_resolves_no_profile_at_import_time(module):
    """Nothing at module level calls `current()`.

    The registration contract is that a host registers at PROCESS START and the
    engine resolves LATE. A module-level `domain_profile.current()` would move
    the resolution to import time and make every importer of this package — a
    CLI listing its own subcommands, a test collecting — need a profile it never
    uses. Asserted structurally so it cannot creep back in as a "cached
    constant".
    """
    _text, tree = _module_source(module)
    module_level = [n for n in tree.body
                    if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    calls = [
        node.lineno
        for stmt in module_level
        for node in ast.walk(stmt)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"current", "load", "register"}
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "domain_profile"
    ]
    assert not calls, (
        f"{module} resolves a domain profile at import time, at line(s) {calls}. "
        "Resolution is LATE by contract: importing this package must register "
        "nothing, resolve nothing and refuse nothing.")


@pytest.mark.parametrize("module", ENGINE_MODULES)
def test_the_module_reads_the_profile(module):
    """The other half of the assertion above: it must read it SOMEWHERE.

    A module that neither hardcodes a status word nor reads the profile has not
    been parameterized — it has had its lifecycle logic deleted. Cheap, and it
    is the failure mode a zero-literal assertion cannot see on its own.
    """
    text, _tree = _module_source(module)
    assert "domain_profile" in text, (
        f"{module} names no domain profile at all; § 4.4 parameterizes this "
        "module, it does not empty it")


def test_the_engine_names_no_artifact_kind_of_any_domain():
    """A kind's NAME is a domain's word too, and is reached through an act.

    `governance-document` and `register-possible` are openxFactory's names for
    its governed prose and its candidate register; `MedxDox` calls them
    something else. The engine asks `kind_declaring(<act>)` — its own verb — and
    never writes a kind's name into a neutral module.
    """
    domain_kind_names = ("governance-document", "register-possible",
                         "staging-topic", "openspec-change", "evidence-record")
    offenders = {}
    for module in ENGINE_MODULES:
        text, tree = _module_source(module)
        keys = _dict_key_nodes(tree)
        hits = [(node.lineno, node.value)
                for node in ast.walk(tree)
                if isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in domain_kind_names
                and id(node) not in keys]
        if hits:
            offenders[module] = hits
    assert not offenders, (
        f"an artifact kind of one domain is named in the neutral engine: "
        f"{offenders}. Reach it with `kind_declaring(<act>)` instead.")


def test_the_seventeen_sites_are_gone_and_the_count_is_recorded():
    """The number § 4.4 works from, kept in the tree rather than in a thread.

    Seventeen occurrences over fifteen lines across the two modules, re-swept
    live against `openXdox-code` `main` for the design note
    (`openXdox-spec docs/domain-profile-design-note.md` § 1) and again in this
    branch. The sweep that measured them is the one above; this test states the
    number it was measured at, so a future reader of a commit message that says
    "seventeen" can see where the number came from.
    """
    total = 0
    for module in ENGINE_MODULES:
        _text, tree = _module_source(module)
        keys = _dict_key_nodes(tree)
        total += sum(
            1 for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and node.value in WATCHED_WORDS and id(node) not in keys)
    assert total == 0, (
        "the seventeen literal occurrences over fifteen lines that § 4.4 "
        f"migrated have not all gone: {total} remain")
