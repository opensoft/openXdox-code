"""`openxdox.domain_corpus_adapter`: the six operations, the whole refusal
vocabulary, and the structural conformance FLOOR PART 3 measures.

WHAT THE RUNNER MEASURES AND WHAT THIS FILE MEASURES, because they are
deliberately different and neither replaces the other.
`openxFactory/scripts/verify-carve-conformance.py` puts this reader through the
SHIPPED neutral corpus (RULED OQ-3's seed, `tests/corpus-adapter/fixtures/` in
openxFactory) and answers `OK -- 17 of 17`; that run is the evidence in the pull
request and it needs an openxFactory checkout, which this leg does not carry and
must not grow a dependency on. This file therefore lays down a corpus of the
SAME SHAPE in `tmp_path` -- three documents in two roots, one complete, one
missing a field its kind obliges, one carrying no kind at all -- and holds the
reader to the same answers, plus the things the seventeen checks do not reach:
every one of the interface's eight refusal kinds, the line rule, the dispatch
path, and the enclosing-repository guard.

WHY NOT VENDOR THE CORPUS. Eleven rows of `docs/opendox-carve-manifest.yaml`
name openxFactory's fixture paths as `replicated_at_destination`, and a second
copy of the corpus here would be FLOOR PART 3 forked in two -- the runner's own
rule, "a corpus edited to match a reader that answered wrong is FLOOR PART 3
deleted", read one step earlier. The shape is restated; the corpus is not
copied.

A CREATED FILE: no row in `docs/opendox-carve-manifest.yaml` (RULED OQ-C). It
stands alone under `--noconftest`, which is what `.github/workflows/validate.yml`
runs, and it imports nothing beyond `pytest`, the standard library, the PINNED
`opendox` interface and this package.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from opendox.corpus_adapter import (
    CORPUS_ABSENT,
    CORPUS_READ_ONLY,
    CORPUS_UNCLASSIFIABLE,
    CORPUS_UNREADABLE,
    DOCUMENT_UNKNOWN,
    OPERATIONS,
    REVISION_UNKNOWN,
    SCOPE_ALL,
    SCOPE_UNKNOWN,
    SEVERITIES,
    WRITE_PATH_UNREACHABLE,
    CorpusAdapter,
    CorpusRef,
    CorpusRefused,
    DocumentId,
    Finding,
)

from openxdox import conformance_corpus
from openxdox.corpus_shape import CorpusShape, Scope, WritePath
from openxdox.domain_corpus_adapter import (
    DomainCorpusAdapter,
    absent_fields,
    classify_text,
    header_window,
    kind_of,
    real_lines,
)

#: The three documents of a corpus with the neutral conformance corpus's SHAPE:
#: one complete, one classified with a field absent, one that cannot be
#: classified at all and must still be listed.
DOCUMENTS = {
    "notes/alpha.md": "Type: note\nTitle: Alpha\n\n# Alpha\n\nA complete one.\n",
    "notes/beta.md": "Type: note\n\n# Beta\n\nMissing the field its kind obliges.\n",
    "papers/gamma.md": "Title: Gamma\n\n# Gamma\n\nNo kind header at all.\n",
}

SHAPE = conformance_corpus.NEUTRAL_SHAPE


def _lay_down(root: Path, documents=DOCUMENTS) -> Path:
    for relative, text in documents.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    for declared in SHAPE.scan_roots:
        (root / declared).mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture()
def populated(tmp_path: Path) -> Path:
    return _lay_down(tmp_path / "populated")


@pytest.fixture()
def reader() -> DomainCorpusAdapter:
    return DomainCorpusAdapter(SHAPE)


def _resolved(reader: DomainCorpusAdapter, location: Path, name="populated"):
    return reader.resolve(CorpusRef(name=name, location=str(location)))


def _refusal(caught) -> str:
    return caught.value.refusal.kind


# --------------------------------------------------------------------------
# structural conformance -- the seam's whole premise
# --------------------------------------------------------------------------

def test_the_reader_satisfies_the_pinned_interface_structurally(reader) -> None:
    """`isinstance` against a `runtime_checkable` Protocol, which is what the
    conformance runner's first check does. It is true of this class WITHOUT a
    base class, and that is the property the seam exists for: "STRUCTURAL
    conformance lets an implementation authored elsewhere conform without
    importing anything from this repository"."""
    assert isinstance(reader, CorpusAdapter)
    assert CorpusAdapter not in type(reader).__mro__, (
        "conformance here is structural; inheriting the Protocol would make "
        "the seam exactly the dependency it was drawn to remove")


def test_the_public_surface_is_exactly_the_interfaces_six_operations() -> None:
    """A seventh public method would be a route the interface does not define,
    which is `corpus-adapter-seam`'s fourth requirement breached. Asserting it
    here makes a convenience added later a red test rather than a quiet
    privilege."""
    public = {name for name in vars(DomainCorpusAdapter)
              if not name.startswith("_")}
    assert public == set(OPERATIONS)


def test_the_declared_factory_returns_a_reader_carrying_the_six(reader) -> None:
    """`verify-carve-conformance.py --adapter openxdox.conformance_corpus:reader`
    resolves this callable and hands it a name and a location."""
    built = conformance_corpus.reader("populated", "/anywhere")
    assert isinstance(built, DomainCorpusAdapter)
    assert isinstance(built, CorpusAdapter)
    assert all(callable(getattr(built, operation)) for operation in OPERATIONS)


def test_the_factory_is_constructed_from_the_corpuss_terms_alone() -> None:
    """Two calls with different names and locations build equivalent readers:
    the location rides in the `CorpusRef` handed to `resolve`, which is what
    lets ONE declaration answer for the corpus's four states in one run."""
    first = conformance_corpus.reader("populated", "/one")
    second = conformance_corpus.reader("empty", "/two")
    assert first._shape is second._shape is SHAPE


# --------------------------------------------------------------------------
# resolve
# --------------------------------------------------------------------------

def test_resolve_answers_scopes_revision_and_read_only_ness(reader,
                                                            populated) -> None:
    corpus = _resolved(reader, populated)
    assert corpus.location == str(populated.resolve())
    assert SCOPE_ALL in corpus.scopes
    assert corpus.write_path is None, (
        "the neutral corpus declares no governed write path, and read-only-ness "
        "is answered at resolution time rather than at the first write")
    assert corpus.write_path_available is False
    assert corpus.revision is None, (
        "a plain tree of documents carries no version marker, so it has no "
        "revision notion -- which the interface declares legal")


def test_a_corpus_that_is_not_there_refuses_absent(reader, tmp_path) -> None:
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, tmp_path / "never-created", name="absent")
    assert _refusal(caught) == CORPUS_ABSENT
    assert "never-created" in caught.value.refusal.subject


def test_a_location_that_is_a_file_refuses_unreadable(reader,
                                                      tmp_path) -> None:
    """UNREADABLE and never UNCLASSIFIABLE. The interface's own comments are the
    vocabulary -- `corpus-unreadable` is "it is there and cannot be read",
    `corpus-unclassifiable` is "the CORPUS's shape, not a document's" -- and the
    conformance corpus holds every reader to it (`unreadable-refuses`). A real
    reader elsewhere answered UNCLASSIFIABLE here and failed that check."""
    not_a_directory = tmp_path / "not-a-directory"
    not_a_directory.write_text("a file where a corpus is expected\n")
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, not_a_directory, name="unreadable")
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert str(not_a_directory) == caught.value.refusal.subject, (
        "the refusal names the path; the failure this class exists to end is a "
        "reader pointed at the wrong tree that said nothing useful about which")


def test_a_directory_holding_none_of_the_roots_refuses_unclassifiable(
        reader, tmp_path) -> None:
    """The structural test: a tree holding none of the declared roots cannot be
    this corpus. Saying that is a DIFFERENT answer from saying it is empty."""
    stranger = tmp_path / "stranger"
    (stranger / "somewhere-else").mkdir(parents=True)
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, stranger, name="stranger")
    assert _refusal(caught) == CORPUS_UNCLASSIFIABLE
    for declared in SHAPE.scan_roots:
        assert declared in caught.value.refusal.detail


def test_an_empty_corpus_resolves_and_lists_nothing(reader, tmp_path) -> None:
    """An empty corpus is an ANSWER, distinguishable from a refusal. "A
    projection built over the first is correct and a projection built over the
    second is a lie with a timestamp." """
    empty = tmp_path / "empty"
    for declared in SHAPE.scan_roots:
        (empty / declared).mkdir(parents=True)
    corpus = _resolved(reader, empty, name="empty")
    assert reader.list_documents(corpus) == ()


# --------------------------------------------------------------------------
# the revision, and the enclosing repository it must never adopt
# --------------------------------------------------------------------------

def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True,
                   capture_output=True, text=True, timeout=30)


@pytest.fixture()
def git_available() -> None:
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True,
                       timeout=30)
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        pytest.skip("git is not on PATH in this environment")


def test_a_requested_revision_over_an_unversioned_tree_refuses(reader,
                                                               populated) -> None:
    """`None` means "this tree has no revision notion", never "it has revisions
    and I could not work out which". The difference is the seam's second
    requirement in miniature."""
    with pytest.raises(CorpusRefused) as caught:
        reader.resolve(CorpusRef(name="populated", location=str(populated),
                                 revision="whatever"))
    assert _refusal(caught) == REVISION_UNKNOWN


def test_a_versioned_corpus_resolves_to_its_own_commit(reader, populated,
                                                       git_available) -> None:
    _git(populated, "init", "-q")
    _git(populated, "config", "user.email", "corpus@example.invalid")
    _git(populated, "config", "user.name", "The Corpus")
    _git(populated, "add", "-A")
    _git(populated, "commit", "-q", "-m", "the corpus")
    corpus = _resolved(reader, populated)
    assert corpus.revision is not None and len(corpus.revision) == 40
    with pytest.raises(CorpusRefused) as caught:
        reader.resolve(CorpusRef(name="populated", location=str(populated),
                                 revision="no-such-revision-anywhere"))
    assert _refusal(caught) == REVISION_UNKNOWN


def test_a_dirty_versioned_corpus_refuses_rather_than_stamping_head(
        reader, populated, git_available) -> None:
    _git(populated, "init", "-q")
    _git(populated, "config", "user.email", "corpus@example.invalid")
    _git(populated, "config", "user.name", "The Corpus")
    _git(populated, "add", "-A")
    _git(populated, "commit", "-q", "-m", "the corpus")
    (populated / "notes" / "delta.md").write_text("Type: note\nTitle: Delta\n")

    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, populated)
    assert _refusal(caught) == REVISION_UNKNOWN
    assert "uncommitted changes" in caught.value.refusal.detail


def test_a_corpus_inside_someone_elses_checkout_is_not_that_checkouts(
        reader, tmp_path, git_available) -> None:
    """THE SHARPEST ONE, and it is a measured failure of a real reader
    elsewhere. Pointed at a plain directory that merely SITS INSIDE a git
    checkout, this reader answers "no revision notion" -- the truth -- rather
    than stamping every read with the enclosing repository's revision, which is
    a different corpus's answer."""
    enclosing = tmp_path / "enclosing"
    enclosing.mkdir()
    _git(enclosing, "init", "-q")
    _git(enclosing, "config", "user.email", "host@example.invalid")
    _git(enclosing, "config", "user.name", "The Host")
    (enclosing / "unrelated.txt").write_text("nothing to do with the corpus\n")
    _git(enclosing, "add", "-A")
    _git(enclosing, "commit", "-q", "-m", "the enclosing repository")
    inside = _lay_down(enclosing / "somewhere" / "inside")

    corpus = _resolved(reader, inside)
    assert corpus.revision is None, (
        "the corpus directory carries no version marker of its own, so it has "
        "no revision -- the enclosing checkout's is not this corpus's answer")
    with pytest.raises(CorpusRefused) as caught:
        reader.resolve(CorpusRef(name="populated", location=str(inside),
                                 revision="HEAD"))
    assert _refusal(caught) == REVISION_UNKNOWN


def test_a_version_marker_that_git_disowns_refuses_rather_than_guessing(
        reader, populated) -> None:
    """A marker that is there and does not resolve is an UNRESOLVABLE corpus,
    and an unresolvable corpus refuses rather than degrading to a weaker answer
    that reads exactly like a legitimate one."""
    (populated / ".git").write_text("gitdir: /nowhere-at-all\n")
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, populated)
    assert _refusal(caught) == REVISION_UNKNOWN


def test_the_ambient_git_environment_does_not_answer_for_this_corpus(
        reader, tmp_path, monkeypatch, git_available) -> None:
    """THE SECOND DOOR into the same defect, and it is not exotic: git exports
    `GIT_DIR` and `GIT_WORK_TREE` to every hook it runs and to
    `git rebase --exec`, so a projection built from inside one inherits them,
    and `git -C <the corpus>` then answers about the AMBIENT repository. The
    corpus below is at its own commit and the environment points at a different
    repository at a different commit; the reader answers with the corpus's."""
    ambient = tmp_path / "ambient"
    ambient.mkdir()
    _git(ambient, "init", "-q")
    _git(ambient, "config", "user.email", "ambient@example.invalid")
    _git(ambient, "config", "user.name", "The Ambient Repository")
    (ambient / "unrelated.txt").write_text("nothing to do with the corpus\n")
    _git(ambient, "add", "-A")
    _git(ambient, "commit", "-q", "-m", "the ambient repository")

    corpus_tree = _lay_down(tmp_path / "corpus")
    _git(corpus_tree, "init", "-q")
    _git(corpus_tree, "config", "user.email", "corpus@example.invalid")
    _git(corpus_tree, "config", "user.name", "The Corpus")
    _git(corpus_tree, "add", "-A")
    _git(corpus_tree, "commit", "-q", "-m", "the corpus")

    monkeypatch.setenv("GIT_DIR", str(ambient / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(ambient))
    corpus = _resolved(reader, corpus_tree)

    own = subprocess.run(["git", "-C", str(corpus_tree), "rev-parse", "HEAD"],
                         capture_output=True, text=True, timeout=30,
                         env={k: v for k, v in __import__("os").environ.items()
                              if not k.startswith("GIT_")}).stdout.strip()
    theirs = subprocess.run(["git", "-C", str(ambient), "rev-parse", "HEAD"],
                            capture_output=True, text=True, timeout=30,
                            env={k: v for k, v in __import__("os").environ.items()
                                 if not k.startswith("GIT_")}).stdout.strip()
    assert own != theirs, "the control: the two repositories are at different commits"
    assert corpus.revision == own
    assert corpus.revision != theirs


def test_a_work_tree_git_does_not_agree_is_this_corpus_refuses(
        reader, populated, monkeypatch) -> None:
    """The fail-closed guard behind the scrub. Whatever the reason -- a
    configuration this reader did not anticipate, a `core.worktree` pointing
    elsewhere, a git that behaves differently -- if git reports a work tree that
    is not the directory this reader was pointed at, the answer belongs to
    another corpus and the reader refuses rather than serving it."""
    (populated / ".git").mkdir()

    def _pretend(cwd, *args):
        if args[:1] == ("rev-parse",) and "--show-toplevel" in args:
            return "/some/other/work/tree"
        return "0" * 40

    monkeypatch.setattr(DomainCorpusAdapter, "_git", staticmethod(_pretend))
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, populated)
    assert _refusal(caught) == REVISION_UNKNOWN
    assert "/some/other/work/tree" in caught.value.refusal.detail


# --------------------------------------------------------------------------
# list_documents and read
# --------------------------------------------------------------------------

def test_the_listing_is_sorted_unique_and_stable(reader, populated) -> None:
    corpus = _resolved(reader, populated)
    first = reader.list_documents(corpus)
    second = reader.list_documents(corpus)
    keys = [document.key for document in first]
    assert keys == sorted(DOCUMENTS), "sorted, and holding this corpus's three"
    assert len(set(keys)) == len(keys), "unique"
    assert list(second) == list(first), "stable across calls"
    assert {document.corpus for document in first} == {"populated"}


def test_resolving_again_rebuilds_the_listing_for_an_unversioned_tree(
        reader, populated) -> None:
    first = reader.list_documents(_resolved(reader, populated))
    (populated / "notes" / "delta.md").write_text("Type: note\nTitle: Delta\n")
    second = reader.list_documents(_resolved(reader, populated))
    assert [document.key for document in first] == sorted(DOCUMENTS)
    assert [document.key for document in second] == sorted(
        (*DOCUMENTS, "notes/delta.md"))


def test_a_scope_this_corpus_does_not_declare_refuses(reader,
                                                      populated) -> None:
    """Rather than quietly widening to everything: "a silent widening is
    indistinguishable from a correct answer"."""
    corpus = _resolved(reader, populated)
    with pytest.raises(CorpusRefused) as caught:
        reader.list_documents(corpus, "no-such-scope-this-corpus-declares")
    assert _refusal(caught) == SCOPE_UNKNOWN
    assert SCOPE_ALL in caught.value.refusal.detail


def test_a_declared_scope_lists_only_its_own_globs(tmp_path) -> None:
    """Per-kind scopes are the parameterization a descendant asks for. A named
    scope lists ITS documents and `all` lists every scope's."""
    narrow = DomainCorpusAdapter(CorpusShape(
        scan_roots=("notes", "papers"),
        scopes={"jottings": Scope(globs=("notes/**/*.md",)),
                "publications": Scope(globs=("papers/**/*.md",))},
        header_scan_lines=6))
    corpus = narrow.resolve(CorpusRef(name="populated",
                                      location=str(_lay_down(tmp_path / "c"))))
    assert [d.key for d in narrow.list_documents(corpus, "jottings")] == [
        "notes/alpha.md", "notes/beta.md"]
    assert [d.key for d in narrow.list_documents(corpus, "publications")] == [
        "papers/gamma.md"]
    assert len(narrow.list_documents(corpus, SCOPE_ALL)) == 3


def test_excluded_parts_drop_a_document_from_its_scope(tmp_path) -> None:
    root = _lay_down(tmp_path / "c")
    (root / "notes" / "archive").mkdir()
    (root / "notes" / "archive" / "old.md").write_text("Type: note\n")
    excluding = DomainCorpusAdapter(CorpusShape(
        scan_roots=("notes", "papers"),
        scopes={SCOPE_ALL: Scope(globs=("**/*.md",),
                                 excluded_parts=frozenset({"archive"}))},
        header_scan_lines=6))
    corpus = excluding.resolve(CorpusRef(name="populated", location=str(root)))
    assert "notes/archive/old.md" not in {
        d.key for d in excluding.list_documents(corpus)}


def test_an_unreadable_declared_root_refuses(reader, tmp_path) -> None:
    root = _lay_down(tmp_path / "c")
    locked = root / "notes"
    original = locked.stat().st_mode
    locked.chmod(0)
    if os.access(locked, os.R_OK | os.X_OK):  # pragma: no cover
        locked.chmod(original)
        pytest.skip("directory permissions are not enforced here")
    try:
        with pytest.raises(CorpusRefused) as caught:
            _resolved(reader, root)
    finally:
        locked.chmod(original)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == str(locked)


def test_an_unreadable_subtree_refuses_listing_rather_than_omitting_it(
        reader, tmp_path) -> None:
    root = _lay_down(tmp_path / "c")
    locked = root / "notes" / "locked"
    locked.mkdir()
    (locked / "delta.md").write_text("Type: note\nTitle: Delta\n")
    original = locked.stat().st_mode
    locked.chmod(0)
    if os.access(locked, os.R_OK | os.X_OK):  # pragma: no cover
        locked.chmod(original)
        pytest.skip("directory permissions are not enforced here")
    corpus = _resolved(reader, root)
    try:
        with pytest.raises(CorpusRefused) as caught:
            reader.list_documents(corpus)
    finally:
        locked.chmod(original)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == str(locked)


def test_read_returns_the_bytes_and_the_resolved_revision(reader,
                                                          populated) -> None:
    corpus = _resolved(reader, populated)
    document = reader.list_documents(corpus)[0]
    got = reader.read(corpus, document)
    assert got.id == document
    assert got.content == DOCUMENTS["notes/alpha.md"].encode("utf-8")
    assert got.revision == corpus.revision


def test_an_identity_this_corpus_does_not_hold_refuses(reader,
                                                       populated) -> None:
    corpus = _resolved(reader, populated)
    absent = DocumentId(corpus="populated", key="notes/nowhere.md")
    with pytest.raises(CorpusRefused) as caught:
        reader.read(corpus, absent)
    assert _refusal(caught) == DOCUMENT_UNKNOWN
    assert caught.value.refusal.subject == "notes/nowhere.md"


@pytest.mark.parametrize("operation", [
    lambda reader, corpus, document: reader.read(corpus, document),
    lambda reader, corpus, document: reader.classify(corpus, document),
    lambda reader, corpus, document: reader.check(corpus, (document,)),
])
def test_a_foreign_document_identity_refuses_before_key_membership(
        reader, populated, operation) -> None:
    corpus = _resolved(reader, populated)
    foreign = DocumentId(corpus="some-other-corpus", key="notes/alpha.md")
    with pytest.raises(CorpusRefused) as caught:
        operation(reader, corpus, foreign)
    assert _refusal(caught) == DOCUMENT_UNKNOWN
    assert "some-other-corpus" in caught.value.refusal.detail


def test_a_revision_this_reader_cannot_serve_never_falls_back(reader,
                                                              populated) -> None:
    """"A silent fallback returns bytes that answer a question nobody asked." """
    corpus = _resolved(reader, populated)
    document = reader.list_documents(corpus)[0]
    with pytest.raises(CorpusRefused) as caught:
        reader.read(corpus, document, "no-such-revision-this-reader-can-serve")
    assert _refusal(caught) == REVISION_UNKNOWN


# --------------------------------------------------------------------------
# the line rule, and classification
# --------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    # The shared rule's own table, restated as data. It cannot be imported --
    # `doc_health.lines` is openxFactory's and unreachable here -- so the rule
    # is written down instead, and this is where a divergence would show.
    ("", []),                       # no lines, not one empty line
    ("a", ["a"]),
    ("a\n", ["a"]),                 # a final ending TERMINATES; it begins nothing
    ("a\nb", ["a", "b"]),
    ("a\r\nb", ["a", "b"]),
    ("a\rb", ["a", "b"]),
    ("a\n\n", ["a", ""]),           # an ending inside the text DOES begin a line
    ("a\n\nb", ["a", "", "b"]),
    ("\n", [""]),
    ("a\r\nb\r\n", ["a", "b"]),
])
def test_the_three_real_line_endings_separate_lines(text, expected) -> None:
    assert real_lines(text) == expected


@pytest.mark.parametrize("separator", ["\x0b", "\x0c", "\x1c", "\x1d", "\x1e",
                                       "\x85", " ", " "])
def test_no_exotic_separator_splits_a_line(separator: str) -> None:
    """`str.splitlines()` breaks on all eight of these. A header window counted
    that way is a window over FRAGMENTS, so a document carrying one of them can
    have a header the reader never sees and be reported as lacking a field it
    plainly carries -- a FALSE FINDING, which costs more trust than a crash."""
    text = f"Type: note{separator}still the same line"
    assert len(real_lines(text)) == 1
    assert len(text.splitlines()) == 2, (
        "the control: this is exactly what the standard-library rule would do")


def test_the_header_window_is_counted_in_real_lines() -> None:
    """The window bites, and it bites at the right DEPTH -- which is the damage
    the line rule exists to prevent, shown here with its control.

    The document below carries its kind header on its sixth REAL line, inside a
    six-line window, and its first line embeds a form feed. Counted in real
    lines the header is found; counted the standard library's way the first line
    becomes two, the header is pushed to the seventh, and a document that
    plainly declares a kind is reported as declaring none."""
    assert header_window("a\nb\nc\n", 2) == ["a", "b"]
    assert kind_of("\n\n\n\n\n\nType: note\n", SHAPE) is None, (
        "a kind header on the seventh real line is outside a six-line window")

    pushed = "first\x0csame line\n\n\n\n\nType: note\n"
    assert kind_of(pushed, SHAPE) == "note"
    window_the_standard_library_would_have_read = pushed.splitlines()[
        :SHAPE.header_scan_lines]
    assert not any(line.startswith("Type:")
                   for line in window_the_standard_library_would_have_read), (
        "the control: `str.splitlines()` splits the first line on the form feed "
        "and pushes the header out of the window, which is the FALSE FINDING "
        "this rule ends")


def test_a_complete_document_classifies_with_nothing_missing() -> None:
    answer = classify_text(DocumentId(corpus="c", key="notes/alpha.md"),
                           DOCUMENTS["notes/alpha.md"], SHAPE)
    assert answer.kind == "note"
    assert answer.required_fields == ("Type", "Title")
    assert answer.missing_fields == ()
    assert answer.unclassifiable is None


def test_a_document_missing_an_obliged_field_is_reported_as_incomplete() -> None:
    answer = classify_text(DocumentId(corpus="c", key="notes/beta.md"),
                           DOCUMENTS["notes/beta.md"], SHAPE)
    assert answer.kind == "note"
    assert answer.missing_fields == ("Title",)
    assert answer.unclassifiable is None


def test_a_document_with_no_kind_is_reported_and_names_itself() -> None:
    """NEVER OMITTED. "An unresolvable CORPUS refuses; an unrecognizable
    DOCUMENT is reported", and the reason names the document so a human can go
    and look at it."""
    answer = classify_text(DocumentId(corpus="c", key="papers/gamma.md"),
                           DOCUMENTS["papers/gamma.md"], SHAPE)
    assert answer.kind is None
    assert answer.unclassifiable is not None
    assert "papers/gamma.md" in answer.unclassifiable
    assert answer.missing_fields == ("Type",), (
        "the default entry answers for an unclassifiable document too -- a "
        "document missing the kind header IS missing a required field")


def test_the_corpus_wide_classification_shape_is_one_of_each(reader,
                                                             populated) -> None:
    """The same counts `classify-population` holds every reader to: this corpus
    is 1 complete / 1 field-absent / 1 unrecognizable, and the unrecognizable
    one is still in the listing."""
    corpus = _resolved(reader, populated)
    documents = reader.list_documents(corpus)
    answers = [reader.classify(corpus, document) for document in documents]
    complete = [a for a in answers if a.kind and not a.missing_fields]
    incomplete = [a for a in answers if a.kind and a.missing_fields]
    unrecognizable = [a for a in answers if a.kind is None]
    assert (len(complete), len(incomplete), len(unrecognizable)) == (1, 1, 1)
    assert len(documents) == 3, "the unrecognizable one stayed listed"


def test_classifying_an_unlisted_identity_refuses_like_read_does(
        reader, populated) -> None:
    """`classify` reads through `read`, so no second membership rule exists to
    disagree with the first."""
    corpus = _resolved(reader, populated)
    with pytest.raises(CorpusRefused) as caught:
        reader.classify(corpus, DocumentId(corpus="populated", key="nope.md"))
    assert _refusal(caught) == DOCUMENT_UNKNOWN


def test_undecodable_bytes_classify_rather_than_raise(reader,
                                                      tmp_path) -> None:
    """A reader stricter than the corpus's own writers would report a document
    the corpus holds happily as unreadable, and `classify` owes a REPORT about a
    document it cannot recognize, never a refusal."""
    root = _lay_down(tmp_path / "c")
    (root / "notes" / "raw.md").write_bytes(b"Type: note\n\xff\xfe not utf-8\n")
    corpus = _resolved(reader, root)
    answer = reader.classify(corpus, DocumentId(corpus="populated",
                                                key="notes/raw.md"))
    assert answer.kind == "note"


def test_a_shape_declaring_no_kind_field_classifies_nothing_and_says_so(
        tmp_path) -> None:
    """An honest answer rather than a broken one: a corpus may hold documents
    whose kinds it does not declare in a header at all. Nothing is
    `unclassifiable` either, because nothing was asked."""
    kindless = DomainCorpusAdapter(CorpusShape(
        scan_roots=("notes", "papers"),
        scopes={SCOPE_ALL: Scope(globs=("**/*.md",))},
        header_scan_lines=6))
    corpus = kindless.resolve(CorpusRef(name="populated",
                                        location=str(_lay_down(tmp_path / "c"))))
    answers = [kindless.classify(corpus, d)
               for d in kindless.list_documents(corpus)]
    assert all(a.kind is None and a.unclassifiable is None for a in answers)


def test_obliged_prefixes_bound_where_the_field_contract_applies() -> None:
    """Empty means everywhere. A corpus can carry one header contract over part
    of itself and none over the rest, and reporting the rest as field-incomplete
    would be a FALSE FINDING."""
    bounded = CorpusShape(
        scan_roots=("notes", "papers"),
        scopes={SCOPE_ALL: Scope(globs=("**/*.md",))},
        header_scan_lines=6, kind_field="Type",
        required_fields_by_kind={None: ("Type", "Title")},
        obliged_prefixes=("notes/",))
    inside = classify_text(DocumentId(corpus="c", key="notes/beta.md"),
                           DOCUMENTS["notes/beta.md"], bounded)
    outside = classify_text(DocumentId(corpus="c", key="papers/beta.md"),
                            DOCUMENTS["notes/beta.md"], bounded)
    assert inside.missing_fields == ("Title",)
    assert outside.required_fields == () and outside.missing_fields == ()


def test_a_header_line_with_no_value_is_not_a_carried_header() -> None:
    assert absent_fields("Title:   \n", ("Title",), SHAPE) == ("Title",)
    assert absent_fields("Title: G\n", ("Title",), SHAPE) == ()


def test_a_per_kind_entry_beats_the_default() -> None:
    per_kind = CorpusShape(
        scan_roots=("notes",),
        scopes={SCOPE_ALL: Scope(globs=("**/*.md",))},
        header_scan_lines=6, kind_field="Type",
        required_fields_by_kind={None: ("Type", "Title"), "note": ("Type",)})
    answer = classify_text(DocumentId(corpus="c", key="notes/beta.md"),
                           DOCUMENTS["notes/beta.md"], per_kind)
    assert answer.required_fields == ("Type",)
    assert answer.missing_fields == ()


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

def test_a_corpus_with_no_verdict_machinery_answers_honestly_empty(
        reader, populated) -> None:
    """The interface's own answer, not a hole in this one: "a corpus with no
    verdict machinery of its own honestly returns `()`; that is an answer, not a
    refusal, and a consumer must not read it as 'clean' without asking whether
    the corpus judges at all"."""
    corpus = _resolved(reader, populated)
    assert reader.check(corpus) == ()


def test_an_injected_verdict_is_handed_the_listing_and_the_subjects(
        tmp_path) -> None:
    seen: list[tuple] = []

    def verdict(corpus, known, subjects):
        seen.append((corpus.ref.name, known, subjects))
        return (Finding(severity=SEVERITIES[0], subject="notes/alpha.md",
                        code="a-code-this-corpus-declares", message="a finding"),)

    judging = DomainCorpusAdapter(CorpusShape(
        scan_roots=("notes", "papers"),
        scopes={SCOPE_ALL: Scope(globs=("**/*.md",))},
        header_scan_lines=6, verdict=verdict))
    corpus = judging.resolve(CorpusRef(name="populated",
                                       location=str(_lay_down(tmp_path / "c"))))
    findings = judging.check(corpus)
    assert len(findings) == 1 and findings[0].severity in SEVERITIES
    assert seen[0][1] == frozenset(DOCUMENTS)
    assert seen[0][2] is None, "None means the whole corpus"
    judging.check(corpus, (DocumentId(corpus="populated",
                                      key="notes/alpha.md"),))
    assert seen[1][2] == ("notes/alpha.md",)


def test_a_named_subject_this_corpus_does_not_list_refuses(reader,
                                                           populated) -> None:
    """A verdict that quietly checked less than it was asked to is a false
    green."""
    corpus = _resolved(reader, populated)
    with pytest.raises(CorpusRefused) as caught:
        reader.check(corpus, (DocumentId(corpus="populated", key="nope.md"),))
    assert _refusal(caught) == DOCUMENT_UNKNOWN


# --------------------------------------------------------------------------
# write_back -- a DISPATCH, and never a write
# --------------------------------------------------------------------------

def _write_path(**overrides) -> WritePath:
    fields = dict(name="a-governed-path",
                  build_request=lambda proposal: {"key": proposal.document_key,
                                                  "body": proposal.content},
                  correlation_id=lambda request: "correlation-1",
                  routes=lambda key: key,
                  dispatch=lambda request, proposal: None)
    fields.update(overrides)
    return WritePath(**fields)


def _writable(tmp_path: Path, path: WritePath):
    adapter = DomainCorpusAdapter(CorpusShape(
        scan_roots=("notes", "papers"),
        scopes={SCOPE_ALL: Scope(globs=("**/*.md",))},
        header_scan_lines=6, kind_field="Type",
        required_fields_by_kind={None: ("Type", "Title")},
        write_path=path))
    root = _lay_down(tmp_path / "c")
    return adapter, adapter.resolve(CorpusRef(name="populated",
                                              location=str(root))), root


def test_a_read_only_corpus_refuses_the_dispatch(reader, populated) -> None:
    corpus = _resolved(reader, populated)
    document = reader.list_documents(corpus)[0]
    with pytest.raises(CorpusRefused) as caught:
        reader.write_back(corpus, document, b"rewritten", actor="a",
                          basis_revision=str(corpus.revision))
    assert _refusal(caught) == CORPUS_READ_ONLY


def test_a_refused_write_leaves_the_tree_byte_for_byte(reader,
                                                       populated) -> None:
    """The conformance corpus digests the tree before and after for this reason.
    Nothing in the adapter opens a file for writing."""
    corpus = _resolved(reader, populated)
    document = reader.list_documents(corpus)[0]
    before = {p: p.read_bytes() for p in sorted(populated.rglob("*"))
              if p.is_file()}
    with pytest.raises(CorpusRefused):
        reader.write_back(corpus, document, b"rewritten", actor="a",
                          basis_revision=str(corpus.revision))
    after = {p: p.read_bytes() for p in sorted(populated.rglob("*"))
             if p.is_file()}
    assert after == before


def test_a_declared_and_reachable_path_returns_a_receipt(tmp_path) -> None:
    dispatched: list[tuple] = []
    adapter, corpus, root = _writable(
        tmp_path, _write_path(dispatch=lambda request, proposal:
                              dispatched.append((request, proposal))))
    assert corpus.write_path == "a-governed-path"
    assert corpus.write_path_available is True
    document = adapter.list_documents(corpus)[0]
    receipt = adapter.write_back(corpus, document, b"proposed", actor="an actor",
                                 basis_revision="r", reason="because")
    assert receipt.correlation_id == "correlation-1"
    assert receipt.dispatched_to == "a-governed-path"
    assert dispatched[0][1].content == b"proposed"
    assert (root / document.key).read_text(encoding="utf-8") == DOCUMENTS[
        document.key], "a DISPATCH is not a write: the tree did not move"


def test_a_declared_but_unreachable_path_refuses_and_names_it(
        tmp_path) -> None:
    """The requirement's own third scenario: the write refuses, names the path,
    and the document remains unsaved rather than being written by a fallback."""
    adapter, corpus, _ = _writable(
        tmp_path, _write_path(dispatch=None,
                              unavailable_reason="nothing is injected yet"))
    assert corpus.write_path_available is False
    document = adapter.list_documents(corpus)[0]
    with pytest.raises(CorpusRefused) as caught:
        adapter.write_back(corpus, document, b"proposed", actor="a",
                           basis_revision="r")
    assert _refusal(caught) == WRITE_PATH_UNREACHABLE
    assert caught.value.refusal.subject == "a-governed-path"
    assert "nothing is injected yet" in caught.value.refusal.detail


def test_a_document_with_no_target_on_the_path_refuses(tmp_path) -> None:
    adapter, corpus, _ = _writable(tmp_path,
                                   _write_path(routes=lambda key: None))
    document = adapter.list_documents(corpus)[0]
    with pytest.raises(CorpusRefused) as caught:
        adapter.write_back(corpus, document, b"proposed", actor="a",
                           basis_revision="r")
    assert _refusal(caught) == WRITE_PATH_UNREACHABLE
    assert "remains unsaved" in caught.value.refusal.detail


def test_a_forged_reference_naming_another_path_is_refused(tmp_path) -> None:
    """`ResolvedCorpus` is plain frozen data: a caller can build one by hand and
    never pass through `resolve`. So the guards read the shape's own descriptor
    and the reference is checked FOR AGREEMENT rather than trusted."""
    adapter, corpus, _ = _writable(tmp_path, _write_path())
    document = adapter.list_documents(corpus)[0]
    forged = type(corpus)(ref=corpus.ref, location=corpus.location,
                          revision=corpus.revision, scopes=corpus.scopes,
                          write_path="some-other-path",
                          write_path_available=True)
    with pytest.raises(CorpusRefused) as caught:
        adapter.write_back(forged, document, b"proposed", actor="a",
                           basis_revision="r")
    assert _refusal(caught) == WRITE_PATH_UNREACHABLE
    assert caught.value.refusal.subject == "some-other-path"


def test_write_back_refuses_a_foreign_document_identity_before_dispatch(
        tmp_path) -> None:
    dispatched: list[tuple] = []
    adapter, corpus, _ = _writable(
        tmp_path, _write_path(dispatch=lambda request, proposal:
                              dispatched.append((request, proposal))))
    document = DocumentId(corpus="some-other-corpus", key="notes/alpha.md")
    with pytest.raises(CorpusRefused) as caught:
        adapter.write_back(corpus, document, b"proposed", actor="a",
                           basis_revision="r")
    assert _refusal(caught) == DOCUMENT_UNKNOWN
    assert dispatched == []


def test_a_reference_disagreeing_about_reachability_fails_closed(
        tmp_path) -> None:
    """This reader's own path IS reachable and the reference says it is not. A
    write is not the place to resolve that disagreement."""
    adapter, corpus, _ = _writable(tmp_path, _write_path())
    document = adapter.list_documents(corpus)[0]
    stale = type(corpus)(ref=corpus.ref, location=corpus.location,
                         revision=corpus.revision, scopes=corpus.scopes,
                         write_path="a-governed-path",
                         write_path_available=False)
    with pytest.raises(CorpusRefused) as caught:
        adapter.write_back(stale, document, b"proposed", actor="a",
                           basis_revision="r")
    assert _refusal(caught) == WRITE_PATH_UNREACHABLE
    assert "resolve the corpus again" in caught.value.refusal.detail


# --------------------------------------------------------------------------
# the vocabulary as a whole
# --------------------------------------------------------------------------

def test_every_refusal_this_reader_raises_is_one_the_interface_declares() -> None:
    """The closed set, read off the source. A reader that invented a kind would
    be answering with a word no consumer can branch on -- and a consumer
    branches on `err.refusal.kind`, which is a stable string, precisely so the
    exception hierarchy does not have to travel across the seam intact."""
    import ast
    import inspect

    from opendox.corpus_adapter import REFUSAL_KINDS

    from openxdox import domain_corpus_adapter as module

    tree = ast.parse(inspect.getsource(module))
    raised = {node.args[0].id
              for node in ast.walk(tree)
              if isinstance(node, ast.Call)
              and isinstance(node.func, ast.Name) and node.func.id == "_refuse"
              and node.args and isinstance(node.args[0], ast.Name)}
    declared = {name for name in dir(module)
                if getattr(module, name, None) in REFUSAL_KINDS
                and name.isupper()}
    assert raised, "the refusal sites are found by name, not by string literal"
    assert raised <= declared
    assert {getattr(module, name) for name in raised} <= set(REFUSAL_KINDS)
