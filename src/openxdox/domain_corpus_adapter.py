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

import os
import re
import stat
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

#: The ambient git variables this reader REMOVES from its subprocess environment.
#:
#: They are the second door into the defect `_revision`'s docstring is about, and
#: it is not exotic: git sets `GIT_DIR` and `GIT_WORK_TREE` for every hook it
#: runs and for `git rebase --exec`, so a projection built from inside a hook
#: inherits them. With them set, `git -C <the corpus> rev-parse HEAD` answers
#: with the AMBIENT repository's commit and not the corpus's -- measured: a
#: corpus at its own commit `128660da` answers `dd09f3df`, the enclosing
#: repository's, purely because the environment said so.
#:
#: A path this reader was handed is the corpus. Whatever repository the calling
#: process happens to be operating on is a different question, and answering the
#: first with the second is the same error as walking up the tree, arriving by a
#: different door. So the variables are dropped for the call, and `_revision`'s
#: cross-check against git's own reported work tree stays as the fail-closed
#: guard for anything that still disagrees.
AMBIENT_GIT_VARIABLES = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES", "GIT_PREFIX",
)

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

    A FINAL LINE ENDING TERMINATES THE LAST LINE AND DOES NOT BEGIN A NEW ONE.
    `re.split` alone yields a trailing empty element for any text ending in a
    separator, which almost every document does, and `''` would come back as one
    empty line rather than as no lines.

    THIS CHANGES NO ANSWER THIS MODULE GIVES, and saying so is the honest form
    of the claim: the spare element is always LAST, so slicing a window off the
    front cannot lose a real line to it, and an empty string starts with no
    header prefix. It is corrected because this helper is PUBLIC and because the
    module's claim is that the shared rule is ADOPTED — a helper that counts one
    more line than the rule it names would be a trap for the next caller, and a
    line count is exactly the kind of thing a later writer or a report would
    reach for. The behaviour is now identical to that rule's for every input:
    `''` is no lines, `'a'` and `'a\n'` are one, `'a\n\n'` is two — asserted
    against the rule's own table in `tests/test_domain_corpus_adapter.py`.
    """
    if not text:
        return []
    rows = _EOL.split(text)
    if rows[-1] == "":
        rows.pop()
    return rows


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
        # One listing per RESOLVED CORPUS and scope, remembered for this
        # INSTANCE only. NOT AN OPTIMIZATION FOR ITS OWN SAKE, and it has now
        # been removed once and measured: `read` decides membership by asking
        # the listing -- one definition, so no second membership rule can
        # disagree with the first -- and `classify` reads, so a reader without
        # this walks the whole tree once PER DOCUMENT. Over an 801-document
        # corpus in two roots, classifying every document took **0.07s with
        # this cache and 58.85s without it**, and the cost is quadratic in the
        # corpus's own size rather than a constant factor.
        #
        # THE STALENESS IT COULD HAVE HAD IS CLOSED AT `resolve`, FOR THE
        # CORPUS BEING RESOLVED AND FOR NO OTHER. An unversioned tree has no
        # revision token for the key to change with, so a caller that
        # re-resolved after editing the tree would otherwise have been served
        # the listing from before its own edit. Re-resolving is the one act
        # that says "the tree may have moved", and it is the cheap place to
        # answer it -- but it says that about ONE corpus, so `resolve` empties
        # that corpus's own entry instead of the whole map.
        #
        # THE KEY IS THE `ResolvedCorpus` ITSELF and the map is an ORDINARY
        # dict, both deliberately. The pinned interface declares that type
        # `@dataclass(frozen=True)` with `eq=True`, so it hashes BY VALUE: two
        # handles describing the same corpus are already the same key, and
        # keying on the handle costs nothing over keying on its location while
        # separating two handles that genuinely differ. A `WeakKeyDictionary`
        # was tried here and is NOT used, for two measured reasons. It would
        # make this module depend on `ResolvedCorpus` being weak-referenceable
        # -- true today only because that dataclass is declared `slots=False,
        # weakref_slot=False`, an undeclared property of a PINNED interface
        # this leg does not own, and `@dataclass(slots=True)` there would turn
        # every `resolve` into `TypeError: cannot create weak reference`. And
        # it silently drops the cache for a handle `resolve` never inserted --
        # which the interface explicitly permits a caller to build, "plain
        # frozen data, so it can" -- putting that caller straight back on the
        # once-per-document walk: **0.17s against 101.38s** over the same
        # 801-document corpus. `setdefault` below is what keeps that path
        # cached; the map grows by one small entry per distinct corpus an
        # adapter instance is pointed at, which for the reader this leg ships
        # is four.
        self._listings: dict[ResolvedCorpus, dict[str, tuple[str, ...]]] = {}
        #: Which declared roots were PRESENT when a location last resolved.
        #:
        #: A corpus is resolved once and listed many times, and a root can be
        #: removed in between. `_stat` then answers None, the loop skipped it,
        #: and the listing came back holding the other roots' documents alone
        #: -- a partial corpus, or an empty one where the last root went, and
        #: neither distinguishable from a corpus that is legitimately that
        #: size. A resolution is a statement about a tree at a moment; this is
        #: what that statement was, so the listing can refuse rather than
        #: quietly answer for a different corpus.
        self._resolved_roots: dict[ResolvedCorpus, tuple[str, ...]] = {}

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
        if not self._is_directory(location, absent_refuses=True):
            raise _refuse(CORPUS_UNREADABLE, str(location),
                          "the path is not a directory")
        present_roots: list[str] = []
        for root in self._shape.scan_roots:
            declared = location / root
            present = self._stat(declared)
            if present is None:
                continue
            if not stat.S_ISDIR(present.st_mode):
                # NOT skipped as absent. A declared root that is THERE and is a
                # file is a corpus laid out wrongly, and skipping it lets the
                # corpus resolve on its other roots and then list nothing from
                # this one -- a partial corpus reported as a whole one, which is
                # the degradation this interface exists to refuse.
                raise _refuse(
                    CORPUS_UNREADABLE, str(declared),
                    "this declared root is present and is not a directory, so "
                    "the corpus cannot be read under it; resolving anyway "
                    "would report a partial corpus as a whole one")
            self._require_confined_root(location, declared)
            self._require_traversable(declared)
            present_roots.append(root)
        if not present_roots:
            raise _refuse(
                CORPUS_UNCLASSIFIABLE, str(location),
                "the directory holds none of the roots this corpus is "
                f"declared over ({', '.join(self._shape.scan_roots)})")

        resolved = location.resolve()
        revision = self._revision(resolved, ref.revision)
        write_path = self._shape.write_path
        corpus = ResolvedCorpus(
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
        # INVALIDATION IS SCOPED TO THE CORPUS BEING RESOLVED, and the scope is
        # the whole point. Clearing the WHOLE map answered the staleness above
        # for one corpus by breaking every other: this reader is built to be
        # pointed at several locations in one run (the conformance corpus
        # points it at four), and a caller holding a `ResolvedCorpus` for A had
        # A's listing dropped merely because it went on to resolve B -- so A's
        # next listing re-walked and answered for a tree A never resolved
        # against. Nothing about resolving B is news about A.
        #
        # WHAT THIS MAP IS, EXACTLY, BECAUSE THE PRECISE CLAIM IS THE WHOLE
        # VALUE OF IT: a MEMO WITH AN INVALIDATION RULE, and not a per-handle
        # snapshot. The rule is "re-resolving a corpus invalidates that
        # corpus's memo", and the key is the handle's VALUE, so two handles
        # that compare equal share one memo and cannot disagree.
        #
        # KEYING ON OBJECT IDENTITY WAS PROPOSED AND IS DELIBERATELY NOT DONE.
        # `ResolvedCorpus` is frozen value data: two equal handles are
        # indistinguishable to every tool a caller has -- `==`, `hash`, `dict`,
        # `set` -- so making them answer `list_documents` differently would
        # make a value type behave like a reference type and hand the caller
        # two answers with no way to predict which it gets. The narrower
        # guarantee this map does make is the one the interface's own
        # `list-stable` check measures: for one corpus, repeated listings agree
        # until something re-resolves it. A caller that needs the stronger
        # thing -- a listing frozen against its own later re-resolution -- can
        # hold the tuple `list_documents` already returned, which is immutable
        # and is the snapshot.
        self._listings[corpus] = {}
        self._resolved_roots[corpus] = tuple(present_roots)
        return corpus

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
        self._require_own_identity(corpus, document)
        self._require_listed(corpus, (document.key,))
        path = Path(corpus.location) / document.key
        # CONFINEMENT IS RE-CHECKED HERE, AT THE MOMENT THE BYTES ARE SERVED,
        # and not only while the listing was built. The listing is remembered
        # per resolve, so a link that was confined when it was listed can be
        # retargeted before it is read, and the boundary this reader documents
        # would then hold only at the moment nobody was looking.
        #
        # WHAT THIS DOES NOT CLAIM, because the honest version is the useful
        # one: the window is narrowed to the gap between this check and the
        # `open` below, not closed. Closing it needs an `openat`/`O_NOFOLLOW`
        # descriptor dance the standard library does not offer portably, and a
        # claim of atomicity here would be the kind of overstatement this
        # module has already had to correct once (`_git`'s isolation). What is
        # guaranteed is that a link retargeted between listing and read is
        # refused rather than served.
        self._require_confined(Path(corpus.location), path,
                               Path(document.key))
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
            for document in subjects:
                self._require_own_identity(corpus, document)
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
        # THE IDENTITY GUARD, AND THE KIND IT REFUSES WITH IS THE POINT.
        # Without it a `DocumentId` belonging to ANOTHER corpus, whose key
        # happens to have a target on this path, was built into a
        # `WriteProposal` and dispatched under THIS corpus -- the one route in
        # this class that acts on a document identity it never listed.
        # `_require_own_identity` is deliberately NOT reused: it raises
        # `DOCUMENT_UNKNOWN`, and this operation's row of the interface is
        # exactly `CORPUS_READ_ONLY` and `WRITE_PATH_UNREACHABLE`. A round of
        # review already proposed widening that row and it was reverted, so
        # the guard is written here with a kind the row names -- which is also
        # the honest statement, and the same one the `routes` refusal below
        # makes: this path is not reachable FOR THIS DOCUMENT.
        if document.corpus != corpus.ref.name:
            raise _refuse(
                WRITE_PATH_UNREACHABLE, write_path.name,
                f"{document.corpus!r} does not name {corpus.ref.name!r}, so "
                "this is another corpus's document identity and this reader "
                "will not dispatch it through this corpus's write path; the "
                "document remains unsaved")
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
        # `os.path.lexists` AND NOT `Path.exists()`, and the difference is a
        # fail-closed branch. `exists()` follows the link and answers False for
        # a BROKEN one, so a corpus whose `.git` is a dangling symlink was read
        # as "no revision notion at all" and every read was stamped
        # `revision=None` — the weaker answer that reads exactly like a
        # legitimate one, which is the degradation the branch below exists to
        # refuse. A marker that is THERE and does not work is an unresolvable
        # corpus, and `rev-parse` failing turns it into a named refusal.
        if not os.path.lexists(location / VERSION_MARKER):
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

        `-C <cwd>`, and no second directory is ever consulted. WHAT IT DOES NOT
        CLAIM, because the claim was once written wider than the code: this is
        not a configuration-isolated git. The subprocess inherits the
        environment minus `AMBIENT_GIT_VARIABLES`, so system, global and
        repository configuration are all still read -- which is deliberate,
        since `safe.directory` and a CI runner's own settings live there and a
        git that ignored them would refuse work trees it should read. What is
        guaranteed is the DIRECTORY: the ambient variables that could redirect
        `-C` are removed, and `_revision` cross-checks git's answer against the
        path it asked about. A failure of any kind -- git absent, the directory not a work tree, a
        timeout, a non-zero exit -- comes back as None and the caller turns it
        into a named refusal, because a reader that cannot answer must say so
        rather than guess.

        THE AMBIENT GIT ENVIRONMENT IS DROPPED, and that is the other half of
        "one directory" (see `AMBIENT_GIT_VARIABLES`). `-C` alone is not enough:
        `GIT_DIR` and `GIT_WORK_TREE` override it, git exports both to every
        hook it runs, and a reader inheriting them answers about the caller's
        repository while looking as if it answered about the corpus.

        Deliberately NOT `record_binding.repository_root`, which exists to walk
        UP to the enclosing work tree; see `_revision` for why that is the one
        thing this operation must not do.
        """
        environment = {name: value for name, value in os.environ.items()
                       if name not in AMBIENT_GIT_VARIABLES}
        try:
            completed = subprocess.run(
                ["git", "-C", str(cwd), *args],
                capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS,
                check=False, env=environment)
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        return (completed.stdout or "").strip() or None

    def _keys(self, corpus: ResolvedCorpus, scope: str) -> tuple[str, ...]:
        # `setdefault` AND NOT `get`: a handle `resolve` never inserted is a
        # corpus the interface permits a caller to build by hand, and leaving
        # it uncached puts it back on the once-per-document walk.
        cached = self._listings.setdefault(corpus, {})
        if scope in cached:
            return cached[scope]
        location = Path(corpus.location)
        # ONCE PER LISTING, not once per scope: `SCOPE_ALL` unions every
        # declared scope, and a profile-derived shape declares one per artifact
        # kind, so walking the roots inside `_scope_keys` walked the whole tree
        # once per kind for a single `list_documents`.
        self._require_readable_tree(corpus, location)
        names = sorted(self._shape.scopes) if scope == SCOPE_ALL else [scope]
        # ONE WALK PER DISTINCT (pattern, exclusions) PAIR, not one per scope.
        # A profile-derived shape declares a scope per artifact kind and those
        # kinds share patterns and roots freely -- the vendored engineering
        # profile's six kinds declare eleven locations over five roots, several
        # of them the same glob -- so globbing per SCOPE walked the same tree
        # once per kind and again per repeated pattern. The scopes still decide
        # MEMBERSHIP exactly as before; what is de-duplicated is the work, and
        # `SCOPE_ALL` is by definition their union so no scope can lose a
        # document to it.
        work: dict[tuple[tuple[str, ...], frozenset], None] = {}
        for name in names:
            declared = self._shape.scopes[name]
            for pattern in declared.globs:
                work[((pattern,), declared.excluded_parts)] = None
        keys: set[str] = set()
        for globs, excluded in work:
            keys.update(self._scope_keys(
                location, Scope(globs=globs, excluded_parts=excluded)))
        listed = tuple(sorted(keys))
        cached[scope] = listed
        return listed

    def _scope_keys(self, location: Path, scope: Scope) -> set[str]:
        """One scope's document keys, matched by the shape's own glob syntax.

        MEMBERSHIP IS `Path.glob`'s AND NOTHING HAND-ROLLED. A replacement
        matcher was tried here and is recorded because its defect is the exact
        failure class this seam exists to end: built on `PurePath.match`, which
        has no recursive `**`, it answered a rooted `notes/**/*.md` with the
        documents at depth 0 and 1 and SILENTLY DROPPED every one below them --
        measured, 2 of 4 against `Path.glob`'s 4. The conformance corpus cannot
        catch that (its three documents are all one directory deep) and
        `from_profile` emits exactly those rooted patterns, so a governed corpus
        would have lost its deeper documents with nothing anywhere reporting a
        loss. A listing that is quietly short is worse than one that is quietly
        wide: the seam forbids the second by name, and the first is the same lie
        with less to look at.

        THE UNREADABLE DIRECTORY IS STILL A REFUSAL, and that is what the walk
        below is for and all it is for. `Path.glob` swallows `OSError` and
        returns the entries it could reach, so a directory this process cannot
        open would come back as an absence -- a corpus that "has no documents
        there" -- which is the degradation the interface's second requirement
        forbids in terms. The pre-flight walks the declared roots with
        `os.walk`'s `onerror`, refuses `CORPUS_UNREADABLE` naming the path it
        could not open, and decides nothing about membership.
        """
        keys: set[str] = set()
        for pattern in scope.globs:
            for match in location.glob(pattern):
                rel = match.relative_to(location)
                if any(part in scope.excluded_parts for part in rel.parts):
                    continue
                # CONFINEMENT IS DECIDED BEFORE "is this a file", because the
                # order used to hide the case it exists for. A matched entry
                # that is a LINK to nothing, or to somewhere outside, is not a
                # file -- so `is_file()` dropped it and the listing came back
                # quietly one document short, which is the same lie as a
                # quietly unreadable directory.
                #
                # AND IT IS DECIDED FOR EVERY MATCH, NOT ONLY FOR THE ONES THAT
                # ARE THEMSELVES LINKS. A path escapes the corpus when ANY
                # component of it does, and only the last component is the one
                # `is_symlink()` asks about: `notes/elsewhere/x.md`, where
                # `elsewhere` is a link out of the corpus, is a perfectly
                # ordinary regular file whose real target is somebody else's.
                # `**` does not descend through a link, but a single-star
                # segment does -- and `from_profile` emits those for every
                # placeholder a domain profile declares
                # (`ideation/staging/<topic>/`), so this is the ordinary shape
                # rather than a corner. `resolve()` answers for the whole path,
                # which is why the check reads it and not the last name in it.
                self._require_confined(location, match, rel)
                if not match.is_file():
                    if match.is_symlink():
                        raise _refuse(
                            CORPUS_UNREADABLE, rel.as_posix(),
                            "this path is a link that does not resolve to a "
                            "file, so it matches a document pattern and is not "
                            "a document; omitting it would report a corpus "
                            "shorter than it is")
                    continue
                keys.add(rel.as_posix())
        return keys

    @staticmethod
    def _require_confined(location: Path, match: Path, rel: Path) -> None:
        """A listed document's real target must lie inside the corpus.

        A SYMLINK IS THE ONE WAY A PATH UNDER THE CORPUS IS NOT OF IT.
        `Path.glob` matches a symlinked file by its name in the tree, and `read`
        opens it by that name, so a link named `notes/payroll.md` pointing at
        `/etc/shadow` would be LISTED as this corpus's document and READ as its
        content. Nothing above catches it: the key is relative, the parent is
        inside the corpus, and the bytes come back.

        This leg already holds a path to exactly this rule -- `doxbench_scope`
        resolves a candidate and refuses one that "resolves outside the selected
        root" -- and this is that rule at the corpus seam.

        IT REFUSES RATHER THAN OMITTING, which is the harder of the two and the
        right one. Dropping the entry would make a corpus with a stray link
        report fewer documents than it holds and say nothing, and a listing that
        is quietly short is the same class of lie the interface forbids for a
        corpus that is quietly unreadable. The refusal names the path, so the
        operator is told which link to look at.
        """
        try:
            target = match.resolve()
        except (OSError, RuntimeError, ValueError) as exc:
            raise _refuse(
                CORPUS_UNREADABLE, rel.as_posix(),
                f"the document's target could not be resolved ({exc})") from exc
        try:
            target.relative_to(location.resolve())
        except ValueError as exc:
            raise _refuse(
                CORPUS_UNREADABLE, rel.as_posix(),
                f"this path resolves to {str(target)!r}, which is outside the "
                "corpus. A link is not a document of the corpus it happens to "
                "sit in, and serving its bytes under this corpus's identity "
                "would answer for a tree nobody pointed this reader at") from exc

    @staticmethod
    def _require_confined_root(location: Path, root: Path) -> None:
        """A declared root's real target must lie inside the corpus.

        The same symlink escape exists one level higher than a matched document:
        a declared root can itself be a symlink to some other directory, and if
        that directory happens to hold no matching files the document-level
        confinement check never runs. The corpus would then resolve and report
        an empty scope for a tree outside itself, which is the same false answer
        in smaller numbers.
        """
        try:
            target = root.resolve()
        except (OSError, RuntimeError, ValueError) as exc:
            raise _refuse(
                CORPUS_UNREADABLE, str(root),
                f"the declared root's target could not be resolved ({exc})") from exc
        try:
            target.relative_to(location.resolve())
        except ValueError as exc:
            raise _refuse(
                CORPUS_UNREADABLE, str(root),
                f"this declared root resolves to {str(target)!r}, which is "
                "outside the corpus. A declared root is part of the corpus's "
                "layout, not a tunnel to some other tree") from exc

    def _require_readable_tree(self, corpus: ResolvedCorpus,
                               location: Path) -> None:
        """Refuse a declared root, or anything under one, that cannot be opened.

        Detection only: it yields no keys and applies no pattern, so the
        listing's membership rule stays `Path.glob`'s alone.
        """
        def _onerror(exc: OSError) -> None:
            raise _refuse(
                CORPUS_UNREADABLE, exc.filename or str(location),
                f"the path could not be read ({exc.strerror or exc})") from exc

        # The roots THIS corpus resolved with, where the location is one this
        # reader resolved; otherwise every declared root, which is the honest
        # answer for a `ResolvedCorpus` a caller built by hand and never put
        # through `resolve` (plain frozen data, so it can).
        expected = self._resolved_roots.get(corpus)
        for root_name in self._shape.scan_roots:
            root = location / root_name
            # `_stat` AND NOT `Path.is_dir()`, for the reason `_stat`'s own
            # docstring gives: `is_dir()` answers False for every `OSError`, so
            # a declared root that became inaccessible AFTER `resolve` was
            # silently skipped here -- a partial listing where another root is
            # present, and an empty one where it is not. Both read exactly like
            # a legitimate answer.
            info = self._stat(root)
            if info is None:
                if expected is not None and root_name in expected:
                    raise _refuse(
                        CORPUS_UNREADABLE, str(root),
                        "this root was there when the corpus resolved and is "
                        "gone now, so a listing would answer for a corpus this "
                        "reader never resolved; resolve it again")
                continue
            if expected is not None and root_name not in expected:
                # THE SYMMETRIC HALF OF THE GUARD ABOVE. Losing a root after
                # resolution refuses; GAINING one silently widened the listing
                # with documents from a root that was not part of the corpus
                # when it resolved -- the same "answers for a corpus this
                # reader never resolved" in the other direction, and the more
                # dangerous one, because the extra documents look exactly like
                # members. Dropping the new root instead would be the silent
                # narrowing this module refuses everywhere else; the resolution
                # is what is stale, so the resolution is what the caller is
                # sent back to.
                raise _refuse(
                    CORPUS_UNREADABLE, str(root),
                    "this root was not there when the corpus resolved and is "
                    "now, so a listing would answer for a corpus this reader "
                    "never resolved; resolve it again")
            if not stat.S_ISDIR(info.st_mode):
                raise _refuse(
                    CORPUS_UNREADABLE, str(root),
                    "this declared root is present and is not a directory, so "
                    "the corpus cannot be listed under it")
            self._require_confined_root(location, root)
            self._require_traversable(root)
            for _dirpath, _dirnames, _filenames in os.walk(root,
                                                           onerror=_onerror):
                pass

    @staticmethod
    def _stat(path: Path) -> os.stat_result | None:
        """`os.stat` for a path, or None where it genuinely is not there.

        NOT `Path.exists()`, and the difference is a refusal kind. `exists()`
        answers False for EVERY `OSError` -- a parent directory this process
        cannot open included -- so an inaccessible corpus came back as
        `corpus-absent`, "the checkout is not there", when the truth was that
        it is there and could not be read. Those are different facts to hand an
        operator: one sends them to find the corpus, the other to fix a
        permission. Only `FileNotFoundError` (and `NotADirectoryError`, which is
        a component of the path not being a directory) means absent.
        """
        try:
            return path.stat()
        except FileNotFoundError as exc:
            if os.path.lexists(path):
                raise _refuse(
                    CORPUS_UNREADABLE, str(path),
                    "the path is present as a dangling symlink, so it cannot "
                    "be read as the corpus path it names") from exc
            return None
        except NotADirectoryError:
            return None
        except OSError as exc:
            raise _refuse(
                CORPUS_UNREADABLE, str(path),
                f"the path could not be read ({exc.strerror or exc})") from exc

    @classmethod
    def _is_directory(cls, path: Path, *, absent_refuses: bool) -> bool:
        info = cls._stat(path)
        if info is None:
            if absent_refuses:
                raise _refuse(CORPUS_ABSENT, str(path),
                              "the path does not exist")
            return False
        return stat.S_ISDIR(info.st_mode)

    @staticmethod
    def _require_traversable(path: Path) -> None:
        try:
            with os.scandir(path):
                pass
        except OSError as exc:
            raise _refuse(
                CORPUS_UNREADABLE, str(path),
                f"the path could not be read ({exc.strerror or exc})") from exc

    @staticmethod
    def _require_own_identity(corpus: ResolvedCorpus, document: DocumentId) -> None:
        if document.corpus != corpus.ref.name:
            raise _refuse(
                DOCUMENT_UNKNOWN, document.key,
                f"{document.corpus!r} does not name {corpus.ref.name!r}; this "
                "reader answers only for this corpus's own document identities")

    def _require_listed(self, corpus: ResolvedCorpus, keys: tuple[str, ...],
                        known: frozenset | None = None) -> None:
        if known is None:
            known = frozenset(self._keys(corpus, SCOPE_ALL))
        for key in keys:
            if key not in known:
                raise _refuse(DOCUMENT_UNKNOWN, key,
                              f"{corpus.ref.name} lists no such document")
