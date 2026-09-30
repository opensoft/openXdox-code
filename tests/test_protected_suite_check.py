"""The allow-list subtraction F5.2 and 12.5's falsifier run
(`scripts/protected_suites.py`; plan 034 T059, T007's batch C).

The check runs against a real history, so these cases build one: a scratch
repository whose commits play the arc's landings. A landing is a first-parent
commit carrying the `Arc:` line. Each case holds one rule of the check:

* an arc landing that touches a protected suite with no entry is refused;
* one whose diff for that suite is exactly an entry's `old` to `new`, inside
  the test the entry names, is admitted;
* an entry is refused as soon as its landing's diff differs from its recorded
  text in any way: another edit beside it, a text that occurs twice, an edit in
  another test or reaching out of the named one, or blobs that are not the
  entry's;
* a commit without the `Arc:` line is not a landing, whatever it touches;
* entries for one suite chain, and a file that breaks its own rules refuses
  the whole check rather than subtracting less;
* an ADDED test (plan 034 T061) is admitted only where the edit adds it and
  nothing else.

The last cases hold this repository's own allow-list to those rules. Which
landing each entry holds at is the falsifier's to show, at the head it runs
at: a pull request's checkout here has no history to walk.

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

import protected_suites as ps

REPO_ROOT = Path(__file__).resolve().parents[1]
ARC = "Arc: neutral-product-standalone-operability"
SUITE = "tests/test_governed.py"

BEFORE = textwrap.dedent('''\
    def test_first() -> None:
        assert 1 == 1


    def test_second() -> None:
        """The second."""
        assert {"a": 1} == {"a": 1}
''')
OLD = '''    assert {"a": 1} == {"a": 1}
'''
NEW = '''    assert {"a": 1, "b": 2} == {"a": 1, "b": 2}
'''
AFTER = BEFORE.replace(OLD, NEW)


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.env = {**os.environ,
                    "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                    "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
        root.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        # Signing off, whatever the developer's own configuration says, as this
        # repository's other git fixtures do (tests/test_trust_gaps.py).
        return subprocess.run(("git", "-C", str(self.root), "-c", "commit.gpgsign=false",
                               *args), check=True, capture_output=True, text=True,
                              env=self.env).stdout.strip()

    def commit(self, files: dict[str, str], message: str) -> str:
        for rel, text in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            self.git("add", "--", rel)
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def blob(self, text: str) -> str:
        return subprocess.run(("git", "-C", str(self.root), "hash-object", "--stdin"),
                              input=text, check=True, capture_output=True,
                              text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    made = Repo(tmp_path / "repo")
    made.commit({SUITE: BEFORE, "README.md": "base\n"}, "base")
    return made


def _entry(repo: Repo, *, before: str = BEFORE, after: str = AFTER, old: str = OLD,
           new: str = NEW, test: str = "test_second", **extra) -> dict:
    entry = {
        "suite": SUITE, "test": test, "landing": "opensoft/openXdox-code#1",
        "edit": "admitted", "reason": "a reason", "ruled": "a ruling",
        "review": "a review", "before_blob": repo.blob(before),
        "after_blob": repo.blob(after), "old": old, "new": new,
    }
    entry.update(extra)
    return entry


def _check(repo: Repo, entries: list[dict]) -> list[ps.Finding]:
    landings = repo.git("log", "--first-parent", "--format=%H", f"--grep=^{ARC}$",
                        "HEAD").splitlines()
    return ps.check(repo.root, landings, {SUITE}, entries)


# --------------------------------------------------------------------------
# the check
# --------------------------------------------------------------------------

def test_an_unentered_edit_to_a_protected_suite_is_refused(repo) -> None:
    repo.commit({SUITE: AFTER}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [])
    assert finding.admitted_by is None
    assert finding.path == SUITE
    assert "no entry names this suite" in finding.why


def test_an_edit_that_is_exactly_its_entry_is_admitted(repo) -> None:
    repo.commit({SUITE: AFTER}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo)])
    assert finding.admitted_by == 1


def test_an_edit_beside_the_entered_one_is_refused(repo) -> None:
    """The weakening batch C names: the entered text changes, and another
    assertion is weakened in the same landing."""
    weakened = AFTER.replace("assert 1 == 1", "assert True")
    repo.commit({SUITE: weakened}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo)])
    assert finding.admitted_by is None
    assert "not the entry's" in finding.why


def test_an_entry_whose_blobs_match_but_whose_text_does_not_is_refused(repo) -> None:
    """The blobs are the landing's, but the recorded text is not the edit."""
    repo.commit({SUITE: AFTER}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, new=NEW.replace('"b": 2', '"b": 3'))])
    assert finding.admitted_by is None
    assert "does not give the suite at the landing" in finding.why


def test_an_old_text_that_occurs_twice_is_refused(repo) -> None:
    twice = BEFORE + "\n\ndef test_third() -> None:\n" + OLD
    repo.commit({SUITE: twice}, "the same assertion in a third test")
    repo.commit({SUITE: twice.replace(OLD, NEW, 1)}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, before=twice, after=twice.replace(OLD, NEW, 1))])
    assert finding.admitted_by is None
    assert "occurs 2 times" in finding.why


def test_an_old_text_that_is_the_tail_of_a_line_is_refused(repo) -> None:
    """`old` ends in a newline, but it is only the end of a line: the entry
    would admit a change to part of an assertion, never shown whole
    (Copilot on #35)."""
    after = BEFORE.replace("assert 1 == 1", "assert 2 == 2")
    repo.commit({SUITE: after}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, after=after, test="test_first",
                                     old="1 == 1\n", new="2 == 2\n")])
    assert finding.admitted_by is None
    assert "does not start a line" in finding.why


def test_an_edit_outside_the_named_test_is_refused(repo) -> None:
    """The text is exact, but it lies in `test_second`, and the entry names
    `test_first`."""
    repo.commit({SUITE: AFTER}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, test="test_first")])
    assert finding.admitted_by is None
    assert "not inside test_first" in finding.why


@pytest.mark.parametrize("side", ["before_blob", "after_blob"])
def test_an_entry_whose_recorded_blob_is_not_the_landings_is_refused(repo, side) -> None:
    """The text would apply, but the entry names another blob on one side, so
    it records some other edit than this landing's."""
    repo.commit({SUITE: AFTER}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, **{side: repo.blob("some other text\n")})])
    assert finding.admitted_by is None
    assert f"not the entry's {repo.blob('some other text' + chr(10))}" in finding.why


def test_an_edit_that_turns_module_code_into_test_code_is_refused(repo) -> None:
    """What the entry replaces lies outside the named test, although what it
    leaves lies inside it: a module-level line becomes the test's last line."""
    before = BEFORE + "X = 1\n"
    after = BEFORE + "    assert 1\n"
    repo.commit({SUITE: before}, "a module-level line after the test")
    repo.commit({SUITE: after}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, before=before, after=after,
                                     old="X = 1\n", new="    assert 1\n")])
    assert finding.admitted_by is None
    assert "old text is not inside test_second" in finding.why


def test_an_edit_that_moves_test_code_out_of_the_test_is_refused(repo) -> None:
    """The reverse: what the entry replaces lies inside the named test, and
    what it leaves lies outside it, so the test loses an assertion."""
    after = BEFORE.replace(OLD, 'X = {"a": 1}\n')
    repo.commit({SUITE: after}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, after=after, new='X = {"a": 1}\n')])
    assert finding.admitted_by is None
    assert "new text is not inside test_second" in finding.why


def test_a_protected_suite_renamed_away_is_refused(repo) -> None:
    """A rename is the suite's deletion at its own path, whatever the
    destination: rename detection must not hide it."""
    repo.git("mv", SUITE, "tests/renamed_away.py")
    repo.git("commit", "-q", "-m", f"rename\n\n{ARC}")
    [finding] = _check(repo, [])
    assert finding.admitted_by is None
    assert finding.path == SUITE


def test_an_entry_admits_one_landing_and_a_replay_is_refused(repo) -> None:
    """Two reviewed landings take the suite X -> Y and back to X. A third,
    unreviewed, repeats the first edit: the suite is at entry 1's
    `before_blob` again and its diff is entry 1's text, but entry 1 has
    admitted its landing and admits no second one (Copilot on #35)."""
    first = repo.commit({SUITE: AFTER}, f"reviewed edit\n\n{ARC}")
    second = repo.commit({SUITE: BEFORE}, f"reviewed revert\n\n{ARC}")
    replay = repo.commit({SUITE: AFTER}, f"the same edit, unreviewed\n\n{ARC}")
    entries = [_entry(repo),
               _entry(repo, before=AFTER, after=BEFORE, old=NEW, new=OLD)]
    findings = {f.landing: f for f in _check(repo, entries)}
    assert findings[first].admitted_by == 1
    assert findings[second].admitted_by == 2
    assert findings[replay].admitted_by is None
    assert f"it admitted {first[:12]} already" in findings[replay].why


def test_the_landings_are_taken_oldest_first_in_any_order(repo) -> None:
    """The falsifier lists landings newest first; the check does not depend
    on it."""
    first = repo.commit({SUITE: AFTER}, f"reviewed edit\n\n{ARC}")
    repo.commit({SUITE: BEFORE}, "an unentered revert, no landing")
    replay = repo.commit({SUITE: AFTER}, f"the same edit again\n\n{ARC}")
    for order in ([first, replay], [replay, first]):
        findings = {f.landing: f for f in
                    ps.check(repo.root, order, {SUITE}, [_entry(repo)])}
        assert findings[first].admitted_by == 1
        assert findings[replay].admitted_by is None


THIRD = """

def test_third() -> None:
    \"\"\"The third, added.\"\"\"
    assert 3 == 3
"""


def test_an_added_test_is_admitted_when_the_edit_adds_it_and_nothing_else(repo) -> None:
    """Plan 034 T061 (batch F admits an added test): the named test has no body
    before the landing, so `new` is `old` and then the test, and nothing else."""
    after = BEFORE + THIRD
    repo.commit({SUITE: after}, f"add\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, after=after, test="test_third",
                                     old=OLD, new=OLD + THIRD)])
    assert finding.admitted_by == 1


def test_an_added_test_whose_edit_also_changes_its_neighbour_is_refused(repo) -> None:
    changed = NEW + THIRD
    after = BEFORE.replace(OLD, changed)
    repo.commit({SUITE: after}, f"add\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, after=after, test="test_third",
                                     old=OLD, new=changed)])
    assert finding.admitted_by is None
    assert "does not begin with its old text" in finding.why


def test_an_added_test_beside_other_added_code_is_refused(repo) -> None:
    helper = "\n\nHELPER = 1\n"
    after = BEFORE + helper + THIRD
    repo.commit({SUITE: after}, f"add\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, after=after, test="test_third",
                                     old=OLD, new=OLD + helper + THIRD)])
    assert finding.admitted_by is None
    assert "not test_third's own" in finding.why


def test_an_entry_naming_a_test_that_exists_nowhere_is_refused(repo) -> None:
    repo.commit({SUITE: AFTER}, f"edit\n\n{ARC}")
    [finding] = _check(repo, [_entry(repo, test="test_nowhere")])
    assert finding.admitted_by is None
    assert "not one module-level test" in finding.why


def test_a_commit_without_the_trailer_is_not_a_landing(repo) -> None:
    repo.commit({SUITE: AFTER}, "an edit that is no arc landing")
    assert _check(repo, []) == []


def test_a_landing_that_touches_no_protected_suite_is_not_reported(repo) -> None:
    repo.commit({"README.md": "changed\n"}, f"docs\n\n{ARC}")
    assert _check(repo, []) == []


def test_two_landings_admitted_by_two_chained_entries(repo) -> None:
    repo.commit({SUITE: AFTER}, f"first edit\n\n{ARC}")
    third = AFTER.replace("assert 1 == 1", "assert 2 == 2")
    repo.commit({SUITE: third}, f"second edit\n\n{ARC}")
    first = _entry(repo)
    second = _entry(repo, before=AFTER, after=third, test="test_first",
                    old="    assert 1 == 1\n", new="    assert 2 == 2\n")
    findings = _check(repo, [first, second])
    assert sorted(f.admitted_by for f in findings) == [1, 2]


def _command(repo: Repo, *, landings: str | None = None, suites: str = SUITE + "\n") -> list[str]:
    """The falsifier's call: each option carries its list, one item per line."""
    if landings is None:
        landings = repo.git("log", "--first-parent", "--format=%H", f"--grep=^{ARC}$",
                            "HEAD") + "\n"
    return [f"--landings={landings}", f"--suites={suites}"]


def test_the_command_exits_one_on_a_refusal_and_zero_when_every_edit_holds(repo,
                                                                           monkeypatch) -> None:
    repo.commit({SUITE: AFTER}, f"edit\n\n{ARC}")
    allow = repo.root / ps.ALLOW_LIST
    monkeypatch.chdir(repo.root)
    allow.write_text(yaml.safe_dump({"schema_version": 1, "kind": ps.KIND, "entries": []}),
                     encoding="utf-8")
    assert ps.main(_command(repo)) == 1
    allow.write_text(yaml.safe_dump({"schema_version": 1, "kind": ps.KIND,
                                     "entries": [_entry(repo)]}), encoding="utf-8")
    assert ps.main(_command(repo)) == 0
    allow.write_text("schema_version: 1\nschema_version: 1\n", encoding="utf-8")
    assert ps.main(_command(repo)) == 2


@pytest.mark.parametrize("landings, suites", [
    ("HEAD\n", SUITE + "\n"),                        # a revision, not a commit id
    ("--output=/tmp/x\n", SUITE + "\n"),             # an option git would take
    (None, "../outside.py\n"),                       # not a tests/test_<name>.py
    (None, "tests/test_é.py\n"),                     # outside ASCII
], ids=["revision", "option", "outside-path", "non-ascii"])
def test_an_item_of_neither_shape_is_refused_before_anything_is_checked(
        repo, monkeypatch, capsys, landings, suites) -> None:
    """The lists are values, never paths, and each item is held to its shape
    before any of it reaches git."""
    repo.commit({SUITE: AFTER}, f"edit\n\n{ARC}")
    monkeypatch.chdir(repo.root)
    (repo.root / ps.ALLOW_LIST).write_text(yaml.safe_dump(
        {"schema_version": 1, "kind": ps.KIND, "entries": [_entry(repo)]}), encoding="utf-8")
    command = _command(repo, landings=landings, suites=suites)
    assert ps.main(command) == 2
    assert "so nothing is checked" in capsys.readouterr().err


def test_a_landing_this_checkout_does_not_hold_is_an_input_refusal(repo, monkeypatch,
                                                                   capsys) -> None:
    """A well-formed commit id with no object behind it is missing history,
    not an edit the arc made: exit 2, never 1 (Copilot on #35)."""
    monkeypatch.chdir(repo.root)
    (repo.root / ps.ALLOW_LIST).write_text(yaml.safe_dump(
        {"schema_version": 1, "kind": ps.KIND, "entries": []}), encoding="utf-8")
    assert ps.main(_command(repo, landings="0" * 40 + "\n")) == 2
    assert "git could not read the history" in capsys.readouterr().err


def test_a_missing_option_is_a_usage_refusal(repo, monkeypatch) -> None:
    monkeypatch.chdir(repo.root)
    assert ps.main([f"--suites={SUITE}"]) == 2


# --------------------------------------------------------------------------
# the allow-list's own rules
# --------------------------------------------------------------------------

def _write(tmp_path: Path, document: object) -> Path:
    path = tmp_path / "allow.yaml"
    path.write_text(document if isinstance(document, str) else yaml.safe_dump(document),
                    encoding="utf-8")
    return path


def _valid_entry(**changes) -> dict:
    entry = {"suite": SUITE, "test": "test_second", "landing": "opensoft/openXdox-code#7",
             "edit": "admitted", "reason": "r", "ruled": "u", "review": "v",
             "before_blob": "a" * 40, "after_blob": "b" * 40,
             "old": "x\n", "new": "y\n"}
    entry.update(changes)
    return entry


@pytest.mark.parametrize("broken, why", [
    ({"schema_version": 2, "kind": ps.KIND, "entries": []}, "schema_version"),
    ({"schema_version": True, "kind": ps.KIND, "entries": []}, "schema_version"),
    ({"schema_version": 1.0, "kind": ps.KIND, "entries": []}, "schema_version"),
    ({"schema_version": 1, "kind": "other", "entries": []}, "kind"),
    ({"schema_version": 1, "kind": ps.KIND, "entries": [], "extra": 1}, "carries"),
    ({"schema_version": 1, "kind": ps.KIND, "entries": [_valid_entry(edit="rewrite")]}, "edit is"),
    ({"schema_version": 1, "kind": ps.KIND, "entries": [_valid_entry(edit=[])]}, "edit is"),
    ("schema_version: 1\nkind: protected-suite-respellings\nentries: []\n? [a]\n: 1\n",
     "plain scalar"),
    ({"schema_version": 1, "kind": ps.KIND, "entries": [_valid_entry(respelled="x")]}, "carries"),
    ({"schema_version": 1, "kind": ps.KIND,
      "entries": [{k: v for k, v in _valid_entry().items() if k != "review"}]}, "carries"),
    ({"schema_version": 1, "kind": ps.KIND, "entries": [_valid_entry(before_blob="abc")]}, "full object id"),
    ({"schema_version": 1, "kind": ps.KIND, "entries": [_valid_entry(old="x")]}, "newline"),
    ({"schema_version": 1, "kind": ps.KIND, "entries": [_valid_entry(new="x\n")] }, "same text"),
    ({"schema_version": 1, "kind": ps.KIND, "entries": [_valid_entry(suite="src/x.py")]}, "suite"),
    ({"schema_version": 1, "kind": ps.KIND, "entries": [_valid_entry(landing="#7")]}, "landing"),
    ({"schema_version": 1, "kind": ps.KIND,
      "entries": [_valid_entry(), _valid_entry(before_blob="c" * 40)]}, "do not chain"),
    ("schema_version: 1\nschema_version: 1\n", "given twice"),
], ids=lambda value: value if isinstance(value, str) else None)
def test_a_list_that_breaks_its_own_rules_subtracts_nothing(tmp_path, broken, why) -> None:
    written = _write(tmp_path, broken)
    with pytest.raises(ps.AllowListInvalid, match=why):
        ps.load_allow_list(written)


def test_a_respelling_names_what_it_respelled(tmp_path) -> None:
    entry = _valid_entry(edit="respelling", respelled="a -> b")
    del entry["reason"]
    assert ps.load_allow_list(_write(tmp_path, {
        "schema_version": 1, "kind": ps.KIND, "entries": [entry]})) == [entry]


def test_this_repositorys_allow_list_keeps_its_rules() -> None:
    assert ps.load_allow_list(REPO_ROOT / ps.ALLOW_LIST), "the allow-list enters no edit"
