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


def test_a_corpus_path_that_is_a_dangling_symlink_is_unreadable_not_absent(
        reader, tmp_path) -> None:
    corpus = tmp_path / "dangling-corpus"
    corpus.symlink_to(tmp_path / "nowhere")
    assert os.path.lexists(corpus)
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, corpus, name="dangling")
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == str(corpus)


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


def test_a_declared_root_that_is_present_and_is_a_file_refuses(
        reader, tmp_path) -> None:
    """NOT skipped as absent. A corpus whose `notes` is a FILE and whose
    `papers/` is a directory would otherwise resolve on the second root and then
    list nothing from the first — a partial corpus reported as a whole one,
    which is the degradation this interface exists to refuse."""
    root = tmp_path / "c"
    (root / "papers").mkdir(parents=True)
    (root / "papers" / "gamma.md").write_text(DOCUMENTS["papers/gamma.md"])
    (root / "notes").write_text("a file where a declared root is expected\n")
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, root)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == str(root / "notes")
    assert "present and is not a directory" in caught.value.refusal.detail, (
        "and by THAT refusal rather than by the traversability probe tripping "
        "over the same file: an operator told 'the path could not be read' "
        "goes looking for a permission, and the defect is a layout")


def test_a_declared_root_that_is_a_dangling_symlink_refuses_unreadable(
        reader, tmp_path) -> None:
    root = tmp_path / "c"
    (root / "papers").mkdir(parents=True)
    (root / "papers" / "gamma.md").write_text(DOCUMENTS["papers/gamma.md"])
    (root / "notes").symlink_to(root / "missing-notes")
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, root)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == str(root / "notes")


def test_a_corpus_inside_an_unopenable_parent_is_unreadable_not_absent(
        reader, tmp_path, unreadable) -> None:
    """`Path.exists()` answers False for EVERY `OSError`, so an inaccessible
    corpus used to come back as `corpus-absent` — "the checkout is not there" —
    when the truth was that it is there and could not be read. Those send an
    operator to two different places."""
    parent = tmp_path / "parent"
    corpus = _lay_down(parent / "c")
    unreadable(parent)
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, corpus)
    assert _refusal(caught) == CORPUS_UNREADABLE


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


def _head(repository: Path) -> str:
    """One repository's own HEAD, read with no ambient git variables set.

    The test that uses this deliberately SETS those variables afterwards, so
    reading the two commits first — and from an environment scrubbed the same
    way the reader scrubs it — is what makes the comparison mean anything.
    """
    clean = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repository), "rev-parse", "HEAD"],
                          capture_output=True, text=True, timeout=30,
                          check=True, env=clean).stdout.strip()


@pytest.fixture()
def unreadable(request):
    """Make a directory unopenable for the rest of the test, and ALWAYS put it
    back — through a finalizer registered BEFORE anything else can raise.

    A `try/finally` around the assertion is not enough and this is not a
    hypothetical: the setup between the `chmod` and the `try` can itself raise
    (it resolves a corpus), and when it did, a mode-0 directory survived the
    test — after which `pytest`'s own cleanup of old `tmp_path` trees could not
    remove it either, and every later session in that environment reported
    `OSError: Directory not empty`. A finalizer runs however the test leaves.

    Skips rather than fails where the platform does not enforce directory
    permissions for this user — running as root, most obviously, which the
    conformance corpus's own README already names as the reason its unreadable
    fixture is a FILE and not a `chmod`.
    """
    def _make(path):
        original = path.stat().st_mode
        request.addfinalizer(lambda: path.chmod(original))
        path.chmod(0)
        if os.access(path, os.R_OK | os.X_OK):  # pragma: no cover
            pytest.skip("directory permissions are not enforced for this user")
        return path
    return _make


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


def test_a_dirty_work_tree_still_resolves_at_its_own_head(
        reader, populated, git_available) -> None:
    """A REFUSAL WAS TRIED HERE AND IS REVERTED, recorded because the argument
    for it is a real one: bytes read out of an edited work tree are not the
    bytes at `HEAD`, so stamping them with `HEAD` overstates what was read.

    It is not this reader's call to make. The interface says `revision` is "the
    revision they were read at" and nowhere requires a clean tree; openxFactory's
    own § 2.2a adapter resolves `HEAD` over a dirty checkout and serves the
    working tree; and a reader that refused would be unusable for the ordinary
    case of projecting from a checkout somebody is working in — one edited file,
    or one untracked editor swap file, and the whole corpus becomes
    unreadable. Two readers over one corpus giving opposite answers is the thing
    § 3.7 exists to prevent, so the change belongs to a ruling and not to this
    act. The question is registered in this PR rather than decided in it.
    """
    _git(populated, "init", "-q")
    _git(populated, "config", "user.email", "corpus@example.invalid")
    _git(populated, "config", "user.name", "The Corpus")
    _git(populated, "add", "-A")
    _git(populated, "commit", "-q", "-m", "the corpus")
    committed = _head(populated)
    (populated / "notes" / "alpha.md").write_text("Type: note\nTitle: edited\n")
    (populated / "notes" / "untracked.md").write_text("Type: note\nTitle: U\n")

    corpus = _resolved(reader, populated)
    assert corpus.revision == committed
    document = DocumentId(corpus="populated", key="notes/alpha.md")
    assert b"edited" in reader.read(corpus, document).content, (
        "the working tree is what is served, which is what a projection over a "
        "checkout somebody is editing has to be able to do")


def test_a_broken_version_marker_is_present_and_refuses(reader,
                                                       populated) -> None:
    """A `.git` that is a DANGLING symlink is a marker that is there and does
    not work — an unresolvable corpus, which refuses. `Path.exists()` follows
    the link and answers False for a broken one, so this used to read as "no
    revision notion at all" and every read was stamped `revision=None`: the
    weaker answer that reads exactly like a legitimate one."""
    (populated / ".git").symlink_to(populated / "nothing-is-here")
    assert not (populated / ".git").exists(), "the control: exists() says no"
    assert os.path.lexists(populated / ".git"), "and the marker is there"
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, populated)
    assert _refusal(caught) == REVISION_UNKNOWN


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

    own = _head(corpus_tree)
    theirs = _head(ambient)
    assert own != theirs, "the control: the two repositories are at different commits"

    monkeypatch.setenv("GIT_DIR", str(ambient / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(ambient))
    corpus = _resolved(reader, corpus_tree)

    assert corpus.revision == own
    assert corpus.revision != theirs, (
        "the reader answered with the AMBIENT repository's commit, which is a "
        "different corpus's answer wearing this corpus's path")


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


def test_the_listing_is_computed_once_per_resolve_and_not_once_per_read(
        reader, populated, monkeypatch) -> None:
    """THE CACHE IS LOAD-BEARING AND ITS REMOVAL WAS MEASURED.

    `read` decides membership by asking the listing — one definition, so no
    second membership rule can disagree with the first — and `classify` reads.
    A reader without the cache therefore walks the whole tree ONCE PER DOCUMENT,
    which is quadratic in the corpus's own size rather than a constant factor.
    Measured over an 801-document corpus in two roots, classifying every
    document: **0.07s with this cache, 58.85s without it.** Not visible on the
    conformance corpus's three documents, and ruinous on a governed one.

    So the property is asserted here rather than left to a benchmark nobody
    runs: N classifications compute the listing ONCE, not N times.
    """
    corpus = _resolved(reader, populated)
    walks: list[str] = []
    original = DomainCorpusAdapter._scope_keys

    def counting(self, location, scope):
        walks.append(str(location))
        return original(self, location, scope)

    monkeypatch.setattr(DomainCorpusAdapter, "_scope_keys", counting)
    documents = reader.list_documents(corpus)
    for document in documents:
        reader.classify(corpus, document)
    assert len(documents) == 3
    assert len(walks) == 1, (
        f"the tree was walked {len(walks)} times to classify "
        f"{len(documents)} documents; the listing is computed per RESOLVE")


def test_resolving_again_rebuilds_the_listing_even_for_an_unversioned_tree(
        reader, populated) -> None:
    """The staleness the cache could have had, closed where it belongs.

    An unversioned tree carries no revision token for the cache key to change
    with, so `resolve` clears the cache outright: re-resolving is the one act
    that says "the tree may have moved", and it is the cheap place to answer it.
    A caller that edits the tree and re-resolves sees its own edit; a caller
    that does not re-resolve is holding a corpus it was handed at a moment in
    time, which is what a `ResolvedCorpus` IS.
    """
    first = reader.list_documents(_resolved(reader, populated))
    (populated / "notes" / "delta.md").write_text("Type: note\nTitle: Delta\n")
    second = reader.list_documents(_resolved(reader, populated))
    assert [d.key for d in first] == sorted(DOCUMENTS)
    assert [d.key for d in second] == sorted((*DOCUMENTS, "notes/delta.md"))


def test_a_rooted_double_star_lists_every_depth_beneath_it(tmp_path) -> None:
    """THE REGRESSION GUARD FOR A MATCHER THAT WAS TRIED AND MEASURED WRONG.

    `from_profile` emits rooted `**` patterns for every directory-shaped
    location a domain profile declares (`docs/**/*.md`,
    `ideation/staging/*/**/*.md`, ...), so "how deep does `**` go" is not a
    corner case here — it is the ordinary case for every governed corpus this
    reader is meant to serve.

    A hand-rolled matcher built on `PurePath.match`, which has no recursive
    `**`, answered `notes/**/*.md` with 2 of these 4 documents and dropped the
    two below depth one, with nothing reporting a loss. The neutral conformance
    corpus cannot catch it: all three of its documents are exactly one directory
    deep, so it returns 17 of 17 either way. This test is the one that does.
    """
    root = tmp_path / "c"
    for relative in ("notes/top.md", "notes/a/one.md", "notes/a/b/two.md",
                     "notes/a/b/c/three.md", "papers/p.md"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Type: note\nTitle: T\n", encoding="utf-8")

    deep = DomainCorpusAdapter(CorpusShape(
        scan_roots=("notes", "papers"),
        scopes={SCOPE_ALL: Scope(globs=("notes/**/*.md",))},
        header_scan_lines=6))
    corpus = deep.resolve(CorpusRef(name="populated", location=str(root)))
    assert [d.key for d in deep.list_documents(corpus)] == [
        "notes/a/b/c/three.md", "notes/a/b/two.md", "notes/a/one.md",
        "notes/top.md"], (
        "a rooted `**` lists EVERY depth beneath its root, and `papers/p.md` "
        "is outside the pattern rather than missing from it")


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


def test_an_unreadable_declared_root_refuses(reader, tmp_path,
                                             unreadable) -> None:
    """A declared root that is there and cannot be opened is UNREADABLE, not an
    empty corpus. `Path.glob` would have swallowed the `OSError` and answered
    with the documents it could reach, which is a corpus reporting fewer
    documents than it holds and saying nothing about it."""
    root = _lay_down(tmp_path / "c")
    locked = unreadable(root / "notes")
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, root)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == str(locked)


def test_an_unreadable_subtree_refuses_listing_rather_than_omitting_it(
        reader, tmp_path, unreadable) -> None:
    """The same, one level down, where `resolve` cannot see it: the refusal has
    to come from the LISTING, which is why `_require_readable_tree` walks."""
    root = _lay_down(tmp_path / "c")
    subtree = root / "notes" / "locked"
    subtree.mkdir()
    (subtree / "delta.md").write_text("Type: note\nTitle: Delta\n")
    corpus = _resolved(reader, root)
    locked = unreadable(subtree)
    with pytest.raises(CorpusRefused) as caught:
        reader.list_documents(corpus)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == str(locked)


def test_a_declared_root_symlinked_outside_the_corpus_refuses_at_resolution(
        reader, tmp_path) -> None:
    """The root itself can be the tunnel out. If it resolves outside the corpus
    and happens to hold no matching files, document-level confinement never
    runs, so `resolve` has to refuse it by the declared root's path."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "not-a-document.txt").write_text("still not this corpus\n")
    root = tmp_path / "c"
    root.mkdir()
    (root / "notes").symlink_to(outside, target_is_directory=True)

    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, root)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == str(root / "notes")
    assert "outside the corpus" in caught.value.refusal.detail


def test_a_symlink_pointing_out_of_the_corpus_refuses_rather_than_listing(
        reader, tmp_path) -> None:
    """THE ONE WAY A PATH UNDER THE CORPUS IS NOT OF IT.

    `Path.glob` matches a symlinked file by its name in the tree and `read`
    opens it by that name, so a link named `notes/payroll.md` pointing outside
    the corpus would be LISTED as this corpus's document and READ as its
    content: the key is relative, the parent is inside the corpus, and the bytes
    come back. Nothing else in this reader catches it. This leg already holds a
    path to the same rule — `doxbench_scope` refuses a candidate that "resolves
    outside the selected root" — and this is that rule at the corpus seam.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "not-this-corpus.md"
    secret.write_text("Type: note\nTitle: Somebody else's\n")
    root = _lay_down(tmp_path / "c")
    (root / "notes" / "linked.md").symlink_to(secret)

    corpus = _resolved(reader, root)
    with pytest.raises(CorpusRefused) as caught:
        reader.list_documents(corpus)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == "notes/linked.md"
    assert "outside the corpus" in caught.value.refusal.detail


def test_a_link_retargeted_after_listing_is_refused_at_read(
        reader, tmp_path) -> None:
    """CONFINEMENT HOLDS WHERE THE BYTES ARE SERVED, not only where the listing
    was built. The listing is remembered per resolve, so a link that was
    confined when it was listed can be retargeted before it is read — and the
    boundary would then hold only at the moment nobody was looking."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "not-this-corpus.md").write_text("Type: note\nTitle: Theirs\n")
    root = _lay_down(tmp_path / "c")
    link = root / "notes" / "linked.md"
    link.symlink_to(root / "notes" / "alpha.md")

    corpus = _resolved(reader, root)
    listed = {d.key for d in reader.list_documents(corpus)}
    assert "notes/linked.md" in listed, (
        "the control: while it pointed inside, it was an ordinary document")

    link.unlink()
    link.symlink_to(outside / "not-this-corpus.md")
    document = DocumentId(corpus="populated", key="notes/linked.md")
    with pytest.raises(CorpusRefused) as caught:
        reader.read(corpus, document)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert "outside the corpus" in caught.value.refusal.detail


def test_a_declared_root_that_links_outside_the_corpus_refuses(
        reader, tmp_path) -> None:
    """A scan root is a path like any other, and `stat()` follows a link. A
    corpus whose `notes` is a symlink to somebody else's directory would
    otherwise resolve, list that directory's documents, and serve them under
    this corpus's identity."""
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "secret.md").parent.mkdir(parents=True)
    (elsewhere / "secret.md").write_text("Type: note\nTitle: Theirs\n")
    root = tmp_path / "c"
    (root / "papers").mkdir(parents=True)
    (root / "papers" / "gamma.md").write_text(DOCUMENTS["papers/gamma.md"])
    (root / "notes").symlink_to(elsewhere)
    with pytest.raises(CorpusRefused) as caught:
        _resolved(reader, root)
    assert _refusal(caught) == CORPUS_UNREADABLE


def test_a_link_to_nothing_refuses_rather_than_shortening_the_listing(
        reader, tmp_path) -> None:
    """A matched entry that is a LINK to nothing is not a file, so the
    `is_file()` filter used to drop it and the listing came back quietly one
    document short — the same lie as a quietly unreadable directory. A link is
    answered for as a link, before anything is skipped."""
    root = _lay_down(tmp_path / "c")
    (root / "notes" / "dangling.md").symlink_to(root / "notes" / "gone.md")
    corpus = _resolved(reader, root)
    with pytest.raises(CorpusRefused) as caught:
        reader.list_documents(corpus)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == "notes/dangling.md"


def test_a_plain_directory_matching_a_document_glob_is_still_skipped(
        reader, tmp_path) -> None:
    """The refusal above is about LINKS. An ordinary directory whose name
    happens to match the pattern is the ordinary non-document it looks like."""
    root = _lay_down(tmp_path / "c")
    (root / "notes" / "a-directory.md").mkdir()
    corpus = _resolved(reader, root)
    assert [d.key for d in reader.list_documents(corpus)] == sorted(DOCUMENTS)


def test_a_root_that_becomes_unreadable_after_resolve_refuses_the_listing(
        reader, tmp_path, unreadable) -> None:
    """A declared root that became unopenable AFTER `resolve` is a refusal at
    LISTING time, not a shorter corpus."""
    root = _lay_down(tmp_path / "c")
    corpus = _resolved(reader, root)
    unreadable(root / "notes")
    with pytest.raises(CorpusRefused) as caught:
        reader.list_documents(corpus)
    assert _refusal(caught) == CORPUS_UNREADABLE


def test_a_root_that_becomes_a_dangling_symlink_after_resolve_refuses_listing(
        reader, tmp_path) -> None:
    root = _lay_down(tmp_path / "c")
    corpus = _resolved(reader, root)
    notes = root / "notes"
    for child in notes.iterdir():
        child.unlink()
    notes.rmdir()
    notes.symlink_to(root / "missing-notes")

    reader._listings.clear()
    with pytest.raises(CorpusRefused) as caught:
        reader.list_documents(corpus)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == str(notes)


def test_a_root_that_cannot_be_stat_ed_refuses_rather_than_being_skipped(
        reader, tmp_path) -> None:
    """THE CASE THAT SEPARATES `Path.is_dir()` FROM `_stat`, and it needs a
    stat that RAISES rather than a directory that merely cannot be opened.

    A self-referential symlink is one: `is_dir()` answers **False** for it
    (measured — `OSError` suppressed, errno 40, ELOOP) while `stat()` raises. On
    `is_dir()` the root was therefore SKIPPED, `papers/` alone was listed, and a
    three-document corpus came back holding one — a partial listing with nothing
    anywhere reporting a loss. `_stat` turns the same `OSError` into a named
    refusal.

    The loop is created AFTER `resolve`, because `resolve` applies the same
    probe and would refuse there first; this test is about the listing.
    """
    root = _lay_down(tmp_path / "c")
    corpus = _resolved(reader, root)
    assert len(reader.list_documents(corpus)) == 3, "the control, before"

    notes = root / "notes"
    for child in notes.iterdir():
        child.unlink()
    notes.rmdir()
    notes.symlink_to(notes)
    assert notes.is_dir() is False, (
        "the control: `is_dir()` suppresses the OSError and says 'not a "
        "directory', which is how the root came to be skipped")

    reader._listings.clear()
    with pytest.raises(CorpusRefused) as caught:
        reader.list_documents(corpus)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == str(notes)


def test_a_regular_file_below_a_linked_directory_is_still_outside(
        reader, tmp_path) -> None:
    """A path escapes the corpus when ANY component of it does, and only the
    LAST component is the one `is_symlink()` asks about.

    `notes/elsewhere/x.md`, where `elsewhere` is a link out of the corpus, is a
    perfectly ordinary regular file whose real target is somebody else's.
    `**` does not descend through a link, but a single-star segment does — and
    `corpus_shape.from_profile` emits those for every placeholder a domain
    profile declares (`ideation/staging/<topic>/`), so this is the ordinary
    shape rather than a corner.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "theirs.md").write_text("Type: note\nTitle: Theirs\n")
    root = _lay_down(tmp_path / "c")
    (root / "notes" / "elsewhere").symlink_to(outside)

    starred = DomainCorpusAdapter(CorpusShape(
        scan_roots=("notes", "papers"),
        scopes={SCOPE_ALL: Scope(globs=("notes/*/*.md",))},
        header_scan_lines=6))
    corpus = starred.resolve(CorpusRef(name="populated", location=str(root)))
    with pytest.raises(CorpusRefused) as caught:
        starred.list_documents(corpus)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert caught.value.refusal.subject == "notes/elsewhere/theirs.md"


def test_a_root_that_vanishes_between_resolve_and_listing_refuses(
        reader, tmp_path) -> None:
    """A resolution is a statement about a tree at a moment. A root that was
    there when the corpus resolved and is gone at listing used to be skipped,
    so the listing came back holding the other roots' documents alone — a
    partial corpus, and where the last root went, an EMPTY one, neither
    distinguishable from a corpus that is legitimately that size."""
    root = _lay_down(tmp_path / "c")
    corpus = _resolved(reader, root)
    assert len(reader.list_documents(corpus)) == 3, "the control, before"

    notes = root / "notes"
    for child in notes.iterdir():
        child.unlink()
    notes.rmdir()

    reader._listings.clear()
    with pytest.raises(CorpusRefused) as caught:
        reader.list_documents(corpus)
    assert _refusal(caught) == CORPUS_UNREADABLE
    assert "gone now" in caught.value.refusal.detail


def test_a_root_never_present_at_resolution_is_not_missed_later(
        tmp_path) -> None:
    """The refusal is about a root that WAS there and went, not about one this
    corpus never had. A shape may declare roots a given corpus does not use, and
    a corpus holding only one of them is a legitimate corpus."""
    root = tmp_path / "c"
    (root / "papers").mkdir(parents=True)
    (root / "papers" / "gamma.md").write_text(DOCUMENTS["papers/gamma.md"])
    reader = DomainCorpusAdapter(SHAPE)
    corpus = reader.resolve(CorpusRef(name="populated", location=str(root)))
    assert [d.key for d in reader.list_documents(corpus)] == ["papers/gamma.md"]


def test_the_all_scope_walks_each_distinct_pattern_once(tmp_path,
                                                        monkeypatch) -> None:
    """A profile-derived shape declares a scope per artifact kind, and kinds
    share patterns and roots freely, so globbing per SCOPE walked the same tree
    once per kind and again per repeated pattern. The scopes still decide
    membership; what is de-duplicated is the work."""
    # Three scopes, TWO distinct patterns, and no two scopes carrying the same
    # tuple — so de-duplicating by whole scope would still walk three times and
    # only de-duplicating by PATTERN walks two.
    many = DomainCorpusAdapter(CorpusShape(
        scan_roots=("notes", "papers"),
        scopes={"kind-a": Scope(globs=("notes/**/*.md",)),
                "kind-b": Scope(globs=("notes/**/*.md", "papers/**/*.md")),
                "kind-c": Scope(globs=("papers/**/*.md",))},
        header_scan_lines=6))
    corpus = many.resolve(CorpusRef(name="populated",
                                    location=str(_lay_down(tmp_path / "c"))))
    calls: list[tuple[str, ...]] = []
    original = DomainCorpusAdapter._scope_keys

    def counting(self, location, scope):
        calls.append(scope.globs)
        return original(self, location, scope)

    monkeypatch.setattr(DomainCorpusAdapter, "_scope_keys", counting)
    listed = many.list_documents(corpus)
    assert [d.key for d in listed] == sorted(DOCUMENTS), (
        "the union is unchanged — three kinds, two distinct patterns, three "
        "documents")
    assert len(calls) == 2, (
        f"three declared scopes carrying two DISTINCT patterns walked "
        f"{len(calls)} times; each distinct pattern is walked once")


def test_a_symlink_that_stays_inside_the_corpus_is_an_ordinary_document(
        reader, tmp_path) -> None:
    """The confinement check refuses an ESCAPE and not a link: a corpus is
    entitled to lay its own documents out with links inside itself."""
    root = _lay_down(tmp_path / "c")
    (root / "papers" / "also-alpha.md").symlink_to(root / "notes" / "alpha.md")
    corpus = _resolved(reader, root)
    assert "papers/also-alpha.md" in {d.key for d in
                                      reader.list_documents(corpus)}


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


def test_write_back_raises_only_the_kinds_its_row_of_the_interface_names(
        tmp_path) -> None:
    """A `DOCUMENT_UNKNOWN` guard was tried on `write_back` and is reverted.

    The interface enumerates the refusal kinds each operation may raise and says
    what an extra one is: "an implementation raising a kind outside its row is a
    defect the conformance suite is entitled to catch." `write_back`'s row is
    `CORPUS_READ_ONLY` and `WRITE_PATH_UNREACHABLE`, and the question the guard
    answered — has this key a target — is the DECLARED PATH's to answer, through
    `routes`, whose None the interface already turns into a refusal naming the
    path. Pre-empting it with a kind the row does not carry is a conformance
    defect wearing the face of a safety check.
    """
    adapter, corpus, _ = _writable(tmp_path,
                                   _write_path(routes=lambda key: None))
    foreign = DocumentId(corpus="some-other-corpus", key="notes/nowhere.md")
    with pytest.raises(CorpusRefused) as caught:
        adapter.write_back(corpus, foreign, b"proposed", actor="a",
                           basis_revision="r")
    assert _refusal(caught) == WRITE_PATH_UNREACHABLE, (
        "the declared path answered, as its row says it does")


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
