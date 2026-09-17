"""openXdox's conformant implementation of the corpus-adapter interface: six
operations over ONE corpus, built from ONE `CorpusShape`.

WHAT THIS IS, AND WHICH RULING PUT IT HERE. `split-opendox-two-layer-product`
`design.md` § D4 machinery (1) -- "the corpus-adapter IMPLEMENTATION -- chart,
firm document store, campaign repository: listed, read, written back and
checked" -- under RULING Q4 (`opensoft/openxFactory#656`, 2026-09-04T15:34Z):
"openDox defines a corpus-adapter interface; openXdox implements it." It is the
reader `tasks.md` § 3.7 calls "§ 4's mapping core for openXdox" and records as
the missing half of FLOOR PART 3 (RULED OQ-1, `design.md` § D6 (3)): "a neutral
conformance corpus EVERY destination passes ... openXdox's adapter
implementation and openxFactory's own adapter run it too, which is the only
mechanical proof that `corpus-adapter-seam`'s no-privileged-route requirement
holds for the home corpus".

WHY IT IS NOT CALLED `corpus_adapter.py`. That name belongs to the INTERFACE,
which is openDox's (RULED OQ-Q / #872) and which this module imports from the
pinned copy rather than replicating. There is exactly one definition of the six
operations in this estate and this file is not a second one; it is an
implementation, and its name says so.

STRUCTURAL CONFORMANCE, NOT NOMINAL -- AND THAT IS THE SEAM. The interface is a
`runtime_checkable` `Protocol` for a stated reason: "an ABC forces
`class X(CorpusAdapter)` ... STRUCTURAL conformance lets an implementation
authored elsewhere conform without importing anything from this repository --
which is the property the seam exists for". This class therefore declares no
base, and `isinstance(reader, CorpusAdapter)` is true of it because it has the
six methods. The conformance runner reads a REFUSAL the same way -- structurally,
off `err.refusal.kind` -- so a destination could raise its own refusal class and
still pass. This one raises the pinned interface's, because openXdox pins openDox
(RULED OQ-2) and inventing a parallel refusal type would be a second definition
of a thing that already has one.

WHAT IT KNOWS ABOUT A CORPUS: NOTHING IT WAS NOT HANDED. There is no path
literal, no header word and no `if home:` branch anywhere below. Everything
arrives as a `CorpusShape` at construction -- which is what lets the same class,
by the same code path, serve a descendant's governed corpus and the neutral
conformance corpus that has "no `openspec/`, no `contracts/`, no lifecycle
headers". openXdox has a stronger reason for that discipline than openxFactory
does: openxFactory owns a corpus and must prove it has no private door, while
openXdox owns NO corpus at all and would have nothing to hardcode that was not
someone else's domain.

FAIL CLOSED, TWO DIFFERENT WAYS, AND THE DIFFERENCE IS THE WHOLE POINT. An
unresolvable CORPUS refuses, naming what it could not resolve, and never degrades
to an empty listing -- "a projection built over the first is correct and a
projection built over the second is a lie with a timestamp". An unrecognizable
DOCUMENT does the opposite: it is REPORTED, with `kind=None` and a reason that
names it, and it STAYS in the listing. Corpus -> refusal; document -> report. This
leg already wrote the first half of that lesson down once, in `corpus_root.py`,
after T092: a `--repo-root` from another filesystem namespace produced a written,
exit-0, entirely empty snapshot, and nothing downstream could tell an empty
corpus from a wrong path.

NOTHING HERE WRITES. `write_back` DISPATCHES through the shape's declared write
path and returns its receipt; no method in this module opens a file for writing,
which the conformance corpus checks by digesting the tree before and after a
refused write.

THREE THINGS THIS READER GETS RIGHT THAT A MEASUREMENT OF ANOTHER GOT WRONG, and
they are recorded because the measurement exists (actor `floor37`, 2026-09-17,
openDox-code #26 at `6c8f19e7`: 11 of 17):

  1. A LOCATION THAT IS A FILE REFUSES `CORPUS_UNREADABLE`, never
     `CORPUS_UNCLASSIFIABLE`. The interface's own comments are the vocabulary:
     `CORPUS_UNREADABLE = "it is there and cannot be read"` against
     `CORPUS_UNCLASSIFIABLE = "the CORPUS's shape, not a document's"`, and the
     corpus's README holds its `not-a-directory` fixture to "refuses UNREADABLE
     and names the path".
  2. THE DECLARED WRITE PATH IS CONSTRUCTION DATA, never a module constant. A
     reader whose write path is a constant can serve no read-only corpus at all,
     so `read-only-declared-at-resolution` fails, `write_back`'s own read-only
     branch becomes unreachable, and a refused write lands in the tree.
  3. THE CLASSIFICATION VOCABULARY IS CONSTRUCTION DATA TOO. A reader that
     classifies by file suffix reports every document in a corpus it does not own
     as the same kind, obliging nothing -- which is a plausible answer and a false
     one.

AND ONE MORE, WHICH IS THE SHARPEST OF THEM: THIS READER NEVER ADOPTS AN
ENCLOSING REPOSITORY. `_revision` looks for a version marker at the location's
OWN ROOT and asks git about that directory only. Pointed at a plain directory
that happens to sit inside somebody's checkout, it answers "this corpus carries
no revision notion", which is the truth, rather than answering with the enclosing
repository's revision -- a different corpus's answer -- or, worse, writing into
it. That failure was measured on a real reader, and a corpus is not a tree's
landlord.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from opendox.corpus_adapter import (
    CORPUS_ABSENT,
    CORPUS_READ_ONLY,
    CORPUS_UNCLASSIFIABLE,
    CORPUS_UNREADABLE,
    DOCUMENT_UNKNOWN,
    REVISION_UNKNOWN,
    SCOPE_ALL,
    SCOPE_UNKNOWN,
    WRITE_PATH_UNREACHABLE,
    Classification,
    CorpusRef,
    CorpusRefused,
    Document,
    DocumentId,
    Finding,
    Refusal,
    ResolvedCorpus,
    WriteReceipt,
)

from .corpus_shape import CorpusShape, Scope, WriteProposal

#: The marker a versioned corpus root carries. A checkout has it as a directory;
#: a worktree, a submodule and a linked checkout each have it as a FILE naming
#: the real git directory; a plain tree of documents has neither -- in which case
#: the corpus has no revision notion at all, which the interface declares legal.
VERSION_MARKER = ".git"

#: The reference a corpus resolves to when the caller names none.
DEFAULT_REF = "HEAD"

#: How long git is given to answer. A hung subprocess inside a reader would look
#: exactly like a corpus that is merely large.
GIT_TIMEOUT_SECONDS = 30

#: THE LINE RULE. CR, LF and CRLF separate lines -- and nothing else does.
#:
#: NOT `str.splitlines()`, which also breaks on `\x0b`, `\x0c`, `\x1c`-`\x1e`,
#: `\x85`, U+2028 and U+2029. A header window counted that way is a window over
#: fragments rather than over lines, so a document carrying one of those
#: characters can have a header the reader never sees and be reported as lacking
#: a field it plainly carries. That is a FALSE FINDING, and a false finding costs
#: more trust than a crash: it accuses a correct document and leaves its author
#: no recourse but to disbelieve the reader.
#:
#: openxFactory paid for this once already and fixed it by converging ten Python
#: spellings of "what is a line" on one shared rule
#: (`align-status-reader-to-real-lines`, ruled 2026-08-19). That rule lives in
#: `doc_health.lines`, which is openxFactory's own corpus machinery and is
#: therefore exactly what a neutral reader may not reach for -- it is not a
#: package on PyPI, it is not this leg's dependency, and importing it would be
#: the consumer-direction reach `test_dependency_direction.py` enumerates. So the
#: RULE is adopted and the CODE is not: eleven characters of regular expression,
#: no dependency, and `tests/test_domain_corpus_adapter.py` asserts both halves
#: of it -- that the three real endings split, and that the exotic ones do not.
_EOL = re.compile(r"\r\n|\r|\n")


def _refuse(kind: str, subject: str, detail: str) -> CorpusRefused:
    return CorpusRefused(Refusal(kind=kind, subject=subject, detail=detail))


def real_lines(text: str) -> list[str]:
    """`text` split into lines on CR / LF / CRLF only, endings dropped.

    The bodies alone, because every caller here reads header VALUES and none of
    them rewrites the document. A writer would need the endings back; this module
    has no writer, by construction.
    """
    return _EOL.split(text)


def header_window(text: str, scan_lines: int) -> list[str]:
    """The first `scan_lines` real lines of `text`."""
    return real_lines(text)[:scan_lines]


def kind_of(text: str, shape: CorpusShape) -> str | None:
    """The document's declared kind, or None where it carries none.

    A shape declaring no `kind_field` classifies nothing, and that is an honest
    answer rather than a broken one: a corpus may hold documents whose kinds it
    does not declare in a header at all.
    """
    if not shape.kind_field:
        return None
    prefix = shape.kind_field + ":"
    for body in header_window(text, shape.header_scan_lines):
        if body.startswith(prefix):
            return body[len(prefix):].strip() or None
    return None


def obliged_fields(document_key: str, kind: str | None,
                   shape: CorpusShape) -> tuple[str, ...]:
    """Which fields this document's kind obliges, here.

    Outside every declared obliged prefix the answer is `()`: this corpus carries
    no field contract over that part of itself, and reporting one would be a
    false finding rather than a strict one.

    The `None` key is the default, and it answers for an UNCLASSIFIABLE document
    too -- a document missing the kind header is missing a required field, so one
    entry covers both and a corpus does not have to say the same thing twice.
    """
    if shape.obliged_prefixes and not any(
            document_key.startswith(prefix)
            for prefix in shape.obliged_prefixes):
        return ()
    table = shape.required_fields_by_kind or {}
    if kind in table:
        return tuple(table[kind])
    return tuple(table.get(None, ()))


def absent_fields(text: str, fields: tuple[str, ...],
                  shape: CorpusShape) -> tuple[str, ...]:
    """Of `fields`, the ones this document does not carry a VALUE for.

    A header line with an empty value is not a carried header. The order of
    `fields` is preserved, so a report reads in the order the corpus declared its
    obligations rather than in whatever order a set happened to iterate.
    """
    window = header_window(text, shape.header_scan_lines)
    present: set[str] = set()
    for body in window:
        for field in fields:
            prefix = field + ":"
            if body.startswith(prefix) and body[len(prefix):].strip():
                present.add(field)
    return tuple(field for field in fields if field not in present)


def classify_text(document: DocumentId, text: str,
                  shape: CorpusShape) -> Classification:
    """The whole operation: kind, obligation, absence, and -- where the kind is
    absent -- a reason that names the document.

    NEVER OMITS. An unrecognized document comes back with `kind=None` and an
    `unclassifiable` reason, and the caller's listing still holds it. The
    asymmetry is the interface's own, stated twice in `design.md` § D2: an
    unresolvable CORPUS refuses; an unrecognizable DOCUMENT is reported.
    """
    kind = kind_of(text, shape)
    required = obliged_fields(document.key, kind, shape)
    missing = absent_fields(text, required, shape)
    unclassifiable = None
    if kind is None and shape.kind_field:
        unclassifiable = (
            f"{document.key} carries no {shape.kind_field} header value, so its "
            "declared shape is not recognizable to this reader")
    return Classification(id=document, kind=kind, required_fields=required,
                          missing_fields=missing, unclassifiable=unclassifiable)


class DomainCorpusAdapter:
    """Six operations over one corpus, built from one `CorpusShape`.

    Six PUBLIC methods, and they are the interface's six. A seventh would be a
    route the interface does not define, which is the seam's fourth requirement
    breached -- `tests/test_domain_corpus_adapter.py` reads this class's public
    surface against `opendox.corpus_adapter.OPERATIONS` so that a convenience
    added later is a red test rather than a quiet privilege.
    """

    def __init__(self, shape: CorpusShape) -> None:
        self._shape = shape
        # One listing per (location, revision, scope), remembered for this
        # INSTANCE only. Not an optimization for its own sake: `read` decides
        # membership by asking the listing -- one definition, so no second
        # membership rule can disagree with the first -- and re-walking the tree
        # per read would make classifying a corpus quadratic in its own size.
        # The instance is bound to the revision it resolved, so the cache can
        # only be stale for a caller that changed the tree underneath it, and
        # such a caller has to resolve again anyway to learn the new revision.
        self._listings: dict[tuple[str, str | None, str], tuple[str, ...]] = {}

    # -- the six -----------------------------------------------------------

    def resolve(self, ref: CorpusRef) -> ResolvedCorpus:
        """Which checkout, which revision, which scopes, which write path.

        The structural test is the shape's `scan_roots`: a tree holding none of
        them cannot be this corpus. A tree that IS this corpus and happens to
        hold no documents resolves fine and lists nothing -- the one distinction
        the whole requirement is about.

        The three refusals are deliberately three and not one. ABSENT is "there
        is nothing here", UNREADABLE is "there is something here and it is not a
        corpus directory" (a file, or a directory the process cannot open), and
        UNCLASSIFIABLE is "this is a directory and it is not laid out as this
        corpus". An operator can act on each; a single refusal covering all three
        would send them all to the same wrong place.
        """
        location = Path(ref.location)
        try:
            if not location.exists():
                raise _refuse(CORPUS_ABSENT, str(location),
                              "the path does not exist")
            if not location.is_dir():
                raise _refuse(CORPUS_UNREADABLE, str(location),
                              "the path is not a directory")
            if not any((location / root).is_dir()
                       for root in self._shape.scan_roots):
                raise _refuse(
                    CORPUS_UNCLASSIFIABLE, str(location),
                    "the directory holds none of the roots this corpus is "
                    f"declared over ({', '.join(self._shape.scan_roots)})")
        except OSError as exc:   # an unreadable path is not this corpus either
            raise _refuse(
                CORPUS_UNREADABLE, str(location),
                f"the path could not be read ({exc.strerror or exc})") from exc

        resolved = location.resolve()
        revision = self._revision(resolved, ref.revision)
        write_path = self._shape.write_path
        return ResolvedCorpus(
            ref=ref,
            location=str(resolved),
            revision=revision,
            # De-duplicated, and `SCOPE_ALL` announced whether or not the shape
            # declares an entry under that name: it is the one scope name every
            # implementation SHALL accept, and `list_documents` honours it as
            # the union of everything declared.
            scopes=tuple(dict.fromkeys(
                (SCOPE_ALL, *sorted(self._shape.scopes)))),
            write_path=None if write_path is None else write_path.name,
            write_path_available=bool(write_path and write_path.available),
        )

    def list_documents(self, corpus: ResolvedCorpus,
                       scope: str = SCOPE_ALL) -> tuple[DocumentId, ...]:
        """Every document identity under one declared scope, sorted and unique.

        A scope this corpus does not declare REFUSES rather than quietly widening
        to everything, because "a silent widening is indistinguishable from a
        correct answer". A descendant's per-kind scopes come from its profile's
        artifact kinds (`corpus_shape.from_profile`), so the names a caller may
        use are the names its own domain declared.
        """
        if scope != SCOPE_ALL and scope not in self._shape.scopes:
            raise _refuse(
                SCOPE_UNKNOWN, scope,
                f"{corpus.ref.name} declares "
                f"{', '.join(dict.fromkeys((SCOPE_ALL, *sorted(self._shape.scopes))))}")
        return tuple(DocumentId(corpus=corpus.ref.name, key=key)
                     for key in self._keys(corpus, scope))

    def read(self, corpus: ResolvedCorpus, document: DocumentId,
             revision: str | None = None) -> Document:
        """The bytes of one listed document, at the revision this corpus was
        resolved at.

        Reading arbitrary history is deliberately OUT: this reader reads the tree
        it is pointed at, and any other revision REFUSES rather than silently
        answering from the one it has. "A silent fallback returns bytes that
        answer a question nobody asked." A caller that wants another revision
        resolves another corpus.
        """
        if revision is not None and revision != corpus.revision:
            raise _refuse(
                REVISION_UNKNOWN, revision,
                f"{corpus.ref.name} is resolved at {corpus.revision!r} and this "
                "reader serves the tree it is pointed at, never another "
                "revision from it")
        self._require_listed(corpus, (document.key,))
        path = Path(corpus.location) / document.key
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise _refuse(
                CORPUS_UNREADABLE, document.key,
                f"the document could not be read ({exc.strerror or exc})") from exc
        return Document(id=document, content=content, revision=corpus.revision)

    def classify(self, corpus: ResolvedCorpus,
                 document: DocumentId) -> Classification:
        """This document's kind and the fields its kind obliges.

        Reads through `read`, so an unknown identity refuses exactly as it does
        there and no second membership rule exists to disagree with the first.
        Decoding replaces undecodable bytes rather than raising: a reader
        stricter than the corpus's own writers would report a document the corpus
        holds happily as unreadable, and `classify` owes a REPORT about a
        document it cannot recognize, never a refusal.
        """
        text = self.read(corpus, document).content.decode("utf-8",
                                                          errors="replace")
        return classify_text(document, text, self._shape)

    def check(self, corpus: ResolvedCorpus,
              subjects: tuple[DocumentId, ...] | None = None) -> tuple[Finding, ...]:
        """This corpus's own verdict, as neutral findings.

        A corpus whose shape declares NO verdict machinery honestly returns an
        empty result. That is the interface's own answer and not a hole in this
        one: "a corpus with no verdict machinery of its own honestly returns
        `()`; that is an answer, not a refusal, and a consumer must not read it
        as 'clean' without asking whether the corpus judges at all". openXdox
        ships no verdict provider for the same reason it ships no status words --
        a check family is a domain's judgement and this package has no domain --
        so a descendant injects its own through `CorpusShape.verdict`.

        A named subject this corpus does not list REFUSES rather than being
        silently dropped: a verdict that quietly checked less than it was asked
        to is a false green.
        """
        known = frozenset(self._keys(corpus, SCOPE_ALL))
        wanted = None
        if subjects is not None:
            wanted = tuple(doc.key for doc in subjects)
            self._require_listed(corpus, wanted, known=known)
        verdict = self._shape.verdict
        if verdict is None:
            return ()
        return tuple(verdict(corpus, known, wanted))

    def write_back(self, corpus: ResolvedCorpus, document: DocumentId,
                   content: bytes, *, actor: str, basis_revision: str,
                   reason: str = "") -> WriteReceipt:
        """DISPATCH a proposed body through the DECLARED governed write path.

        Nothing in this method writes, and the order of its guards is part of
        that: read-only and unreachable are answered BEFORE any request artifact
        is built, so a refusal cannot have produced a side effect on the way to
        being raised.

        REACHABILITY IS THIS READER'S OWN ANSWER, NEVER THE REFERENCE'S.
        `ResolvedCorpus` is plain frozen data: a caller can build one by hand and
        never pass through `resolve` at all, so `corpus.write_path_available` is
        a REPORT of what this reader said and not an authorization. The guards
        below therefore read the shape's own descriptor, and the reference is
        checked FOR AGREEMENT rather than trusted -- a reference naming a path
        this reader does not serve is a refusal, never a dispatch through
        whichever path the reader happens to hold.
        """
        write_path = self._shape.write_path
        if write_path is None or corpus.write_path is None:
            raise _refuse(
                CORPUS_READ_ONLY, corpus.ref.name,
                "this corpus declares no governed write path, and resolution "
                "already reported it as read-only")
        if corpus.write_path != write_path.name:
            raise _refuse(
                WRITE_PATH_UNREACHABLE, corpus.write_path,
                "this reference names a write path this reader does not serve; "
                f"it declares {write_path.name!r}. A mismatch is a refusal, "
                "never a dispatch through whichever path the reader happens to "
                "hold")
        if not write_path.available:
            raise _refuse(WRITE_PATH_UNREACHABLE, write_path.name,
                          write_path.unavailable_reason
                          or "the declared write path cannot be reached")
        if not corpus.write_path_available:
            # This reader's own path IS reachable and the reference says it is
            # not. Fail closed on the disagreement rather than picking a winner.
            raise _refuse(
                WRITE_PATH_UNREACHABLE, write_path.name,
                "the reference this write was made against reports the declared "
                "path unavailable, and a write is not the place to resolve that "
                "disagreement -- resolve the corpus again")
        target = write_path.routes(document.key)
        if target is None:
            raise _refuse(
                WRITE_PATH_UNREACHABLE, write_path.name,
                f"{document.key} has no target on the declared write path, so "
                "there is nothing to dispatch through it and the document "
                "remains unsaved")
        proposal = WriteProposal(document_key=document.key, content=content,
                                 actor=actor, basis_revision=basis_revision,
                                 reason=reason)
        request = write_path.build_request(proposal)
        correlation_id = write_path.correlation_id(request)
        write_path.dispatch(request, proposal)
        return WriteReceipt(correlation_id=correlation_id,
                            dispatched_to=write_path.name)

    # -- private -----------------------------------------------------------

    def _revision(self, location: Path, requested: str | None) -> str | None:
        """The commit this corpus is read at, or None where it carries none.

        `None` MEANS ONE THING ONLY: this tree carries no version marker AT ITS
        OWN ROOT, so it has no revision notion, which the interface declares
        legal. It does NOT mean "it has revisions and I could not work out
        which": a versioned corpus whose ref will not resolve is an UNRESOLVABLE
        corpus and refuses, because degrading to a weaker answer that reads
        exactly like a legitimate one is the failure the seam exists to end.

        THE MARKER IS LOOKED FOR AT THE LOCATION'S OWN ROOT AND NOWHERE ABOVE IT,
        and this is the one line in this module that a real reader elsewhere got
        wrong. Walking UP to the enclosing work tree -- which is what
        `git rev-parse --show-toplevel` does from any subdirectory, and what this
        leg's own `record_binding.repository_root` is FOR -- makes a plain
        directory inside somebody's checkout resolve with that checkout's
        revision. Every read is then stamped with a revision belonging to a
        different corpus, and a write path built the same way commits into a
        repository nobody pointed this reader at. So: marker at the root, git
        asked about that directory only, and the answer cross-checked against
        git's own toplevel before it is believed.
        """
        if not (location / VERSION_MARKER).exists():
            if requested is not None:
                raise _refuse(
                    REVISION_UNKNOWN, requested,
                    f"{location} carries no revisions to resolve against")
            return None
        ref = requested or DEFAULT_REF
        toplevel = self._git(location, "rev-parse", "--show-toplevel")
        if toplevel is None or Path(toplevel).resolve() != location:
            raise _refuse(
                REVISION_UNKNOWN, ref,
                f"{location} carries a version marker and git reports its work "
                f"tree as {toplevel!r}. This reader resolves the corpus it was "
                "pointed at and never the repository that happens to enclose "
                "it, so it refuses rather than answering with another corpus's "
                "revision")
        resolved = self._git(location, "rev-parse", "--verify", f"{ref}^{{commit}}")
        if resolved is None:
            raise _refuse(
                REVISION_UNKNOWN, ref,
                f"{location} carries revisions and {ref!r} resolves to none of "
                "them, so this corpus cannot be read at a revision anyone can "
                "name")
        return resolved

    @staticmethod
    def _git(cwd: Path, *args: str) -> str | None:
        """git's stdout for one query about ONE directory, or None.

        `-C <cwd>` and nothing else: no environment is set, no configuration is
        read from the caller, and no second directory is ever consulted. A
        failure of any kind -- git absent, the directory not a work tree, a
        timeout, a non-zero exit -- comes back as None and the caller turns it
        into a named refusal, because a reader that cannot answer must say so
        rather than guess.

        Deliberately NOT `record_binding.repository_root`, which exists to walk
        UP to the enclosing work tree; see `_revision` for why that is the one
        thing this operation must not do.
        """
        try:
            completed = subprocess.run(
                ["git", "-C", str(cwd), *args],
                capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS,
                check=False)
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        return (completed.stdout or "").strip() or None

    def _keys(self, corpus: ResolvedCorpus, scope: str) -> tuple[str, ...]:
        cached = self._listings.get((corpus.location, corpus.revision, scope))
        if cached is not None:
            return cached
        location = Path(corpus.location)
        names = sorted(self._shape.scopes) if scope == SCOPE_ALL else [scope]
        keys: set[str] = set()
        for name in names:
            keys.update(self._scope_keys(location, self._shape.scopes[name]))
        listed = tuple(sorted(keys))
        self._listings[(corpus.location, corpus.revision, scope)] = listed
        return listed

    def _scope_keys(self, location: Path, scope: Scope) -> set[str]:
        keys: set[str] = set()
        for pattern in scope.globs:
            for match in location.glob(pattern):
                if not match.is_file():
                    continue
                rel = match.relative_to(location)
                if any(part in scope.excluded_parts for part in rel.parts):
                    continue
                keys.add(rel.as_posix())
        return keys

    def _require_listed(self, corpus: ResolvedCorpus, keys: tuple[str, ...],
                        known: frozenset | None = None) -> None:
        if known is None:
            known = frozenset(self._keys(corpus, SCOPE_ALL))
        for key in keys:
            if key not in known:
                raise _refuse(DOCUMENT_UNKNOWN, key,
                              f"{corpus.ref.name} lists no such document")
