"""The construction DATA a `DomainCorpusAdapter` is built from, and the one
function that derives it from a registered domain profile.

WHAT THIS IS FOR. `split-opendox-two-layer-product` `design.md` § D4 names seven
machineries as openXdox's content, and the first is "the corpus-adapter
IMPLEMENTATION -- chart, firm document store, campaign repository: listed, read,
written back and checked". RULING Q4 (`opensoft/openxFactory#656`,
2026-09-04T15:34Z) is the ruling that puts an implementation here at all:
"openDox defines a corpus-adapter interface; openXdox implements it." RULING C2
(same day, 17:47Z) is the one that says WHAT KIND of implementation: "openXdox is
the domain-mapping core, PARAMETERIZED", and engineering vocabulary "stays in
openxFactory as its own adapter over the corpus-adapter interface". This module
is where that parameterization is carried.

WHY THE LAYOUT IS A VALUE AND NEVER A LITERAL IN THE CLASS. `corpus-adapter-seam`'s
fourth requirement forbids a reader any route the interface does not define, and
openxFactory's own adapter states the argument in one sentence this module
adopts: "a class that carried the home layout in its own body would have exactly
that route: a literal, unreachable from outside and untestable against any other
corpus". The same sentence is sharper HERE, because openXdox ships no domain at
all -- `domain_profile.current()` refuses rather than falling back, and "openXdox
is the domain-mapping CORE and ships NO domain's words" is that module's own
refusal text. A path or a header word in this file would be a domain smuggled
into a neutral package through its reader.

So: NOTHING IN THIS MODULE NAMES A PATH, A FILE SUFFIX, A HEADER FIELD OR A
GOVERNANCE NOUN. Every one of those arrives as a value -- from a caller, or from
a `DomainProfile` the descendant registered. The only strings this file contains
are glob syntax (`*`, `?`, `[`, `/`) and the profile grammar's own placeholder
delimiters (`<`, `>`), neither of which belongs to any domain.

WHY IT MIRRORS `corpus_adapter_openxfactory.shape` RATHER THAN IMPORTING IT.
openxFactory is this leg's CONSUMER (`test_dependency_direction.py`: the pin
chain runs openxFactory -> openXdox -> openDox, and a reach the other way is the
inversion § 4.1 exists to end). The two shapes are therefore deliberate
independent implementations of one idea, and they agree because the interface
they serve is one interface, not because either imports the other. What this one
adds is `from_profile`: openxFactory's shape is hand-built by `home.py` for one
corpus it owns, and a mapping core cannot hand-build its descendants' corpora.

WHAT IT DOES NOT CARRY, AND WHY THAT IS THE RULING AND NOT A GAP. `DomainProfile`
declares artifact kinds, their locations, per-kind lifecycle vocabulary,
immutability points, acts, gates, evidence classes, authorities and a truth
store. It declares NO header axis -- nothing that says which header field names a
document's kind, or which fields a kind obliges -- and `classify` needs both. They
are therefore CONSTRUCTION DATA here (`kind_field`, `required_fields_by_kind`),
exactly as openxFactory's shape carries them, so this act changes no schema and
no promoted spec, and the profile stays the vocabulary-and-lifecycle authority it
was ruled to be. A sixth profile axis is the registered successor, not this act.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PureWindowsPath
from typing import Callable, Mapping

from opendox.corpus_adapter import SCOPE_ALL, Finding, ResolvedCorpus

from .domain_profile import DomainProfile

#: What a verdict provider is handed, and what it gives back.
#:
#: `(resolved corpus, known_keys, subjects) -> neutral findings`. `known_keys` is
#: the set of identities the adapter's own listing returned, so a provider can
#: tell a finding about a listed document from a finding about the corpus at
#: large; `subjects` is None for "the whole corpus" and otherwise the identities
#: the caller asked about.
#:
#: A corpus with no verdict machinery declares None and the adapter honestly
#: answers `()`. The interface says that in terms -- "a corpus with no verdict
#: machinery of its own honestly returns `()`; that is an answer, not a refusal"
#: -- and it is the neutral conformance corpus's own case. openXdox ships NO
#: verdict provider of its own for the same reason it ships no status words: a
#: check family is a domain's judgement, and this package has no domain.
Verdict = Callable[
    [ResolvedCorpus, frozenset, tuple[str, ...] | None], tuple[Finding, ...]]

#: The characters that make a path segment a PATTERN rather than a name. `fnmatch`
#: syntax, which is what `pathlib.Path.glob` speaks; listed here so the two
#: questions this module asks of a location -- "where does its literal part end"
#: and "does it already name documents" -- are asked against one definition.
GLOB_METACHARACTERS = "*?["

#: The profile grammar's placeholder delimiters. A domain profile writes a
#: variable path segment as `<topic>` / `<change-id>` (the shape every location
#: in the vendored engineering-profile fixture uses), which is a name for a
#: reader and a wildcard for a walker. Normalizing it to `*` is the whole of the
#: translation; the words inside the brackets are the profile's and are never
#: read here.
PLACEHOLDER_OPEN = "<"
PLACEHOLDER_CLOSE = ">"


#: Path segments a declared location may never carry, and the reason is a
#: traversal rather than a style preference: `scan_roots` and every glob are
#: joined onto a corpus's resolved location, so a `..` in either walks OUT of
#: the corpus and a reader would serve bytes from a tree nobody pointed it at.
#: An absolute location does the same in one step.
#:
#: This estate already refuses exactly this shape one layer up, in the words of
#: `docs/opendox-carve-admissions.yaml`'s own header: a declared path is "a
#: plain path relative to the destination's own root -- never absolute, never
#: carrying a `.`/`..` segment". `doxbench_scope`'s confinement check is the
#: same rule again at this leg. A corpus shape is held to it too, and HERE
#: rather than at the first listing, because a shape that cannot be confined is
#: not a corpus this reader can answer for at all.
TRAVERSAL_SEGMENTS = frozenset({".", ".."})


class CorpusShapeInvalid(ValueError):
    """A shape that could not answer for any corpus, refused at construction.

    Refusing HERE rather than at the first `resolve` is deliberate and is the
    T092 lesson this estate has already paid for once: an adapter built from an
    empty scan-root tuple refuses every corpus with `corpus-unclassifiable`, and
    an operator reading that refusal would go looking at the corpus -- which is
    correct -- and find nothing wrong with it, because the defect is in the
    reader's construction and was silent at the moment it was made.
    """


def _reject_traversal(value: str, where: str) -> None:
    """Refuse an absolute declared path, or one carrying `.` or `..`.

    Named `where` so the refusal says which declaration is at fault -- a scan
    root, a scope's glob, or an artifact kind's location in a profile -- because
    the operator who has to fix it is reading a profile, not this module.
    """
    if PureWindowsPath(value).drive:
        raise CorpusShapeInvalid(
            f"{where} declares {value!r}, which is DRIVE-QUALIFIED. Every "
            "declared location is joined onto the corpus's own resolved "
            "location, so a drive-qualified one answers for some other tree and "
            "this reader would serve bytes from a place nobody pointed it at")
    if value.startswith("/") or value.startswith("\\"):
        raise CorpusShapeInvalid(
            f"{where} declares {value!r}, which is an ABSOLUTE path. Every "
            "declared location is joined onto the corpus's own resolved "
            "location, so an absolute one leaves the corpus in a single step "
            "and this reader would answer for a tree nobody pointed it at")
    # BOTH SEPARATORS, and it is not Windows courtesy: these values are joined
    # with `pathlib`, and a check that split on `/` alone would pass `a\\..\\b`
    # to a path library that may read it as a traversal. A guard that is right
    # only on the platform it was written on is a guard nobody can move.
    #
    # THROUGH `_segments`, which is the same splitter the derivation itself
    # uses, so the guard and the code it guards can never disagree about where
    # a segment boundary is -- the class of divergence that makes a check pass
    # over a value the consumer then reads differently.
    for segment in _segments(value):
        if segment in TRAVERSAL_SEGMENTS:
            raise CorpusShapeInvalid(
                f"{where} declares {value!r}, which carries a {segment!r} "
                "segment. Declared locations are joined onto the corpus's own "
                "resolved location, so a traversal segment walks OUT of the "
                "corpus and this reader would serve bytes from a tree nobody "
                "pointed it at")


@dataclass(frozen=True)
class Scope:
    """One declared scope: which globs it resolves, and what it drops.

    The exclusion set is PER SCOPE rather than shared. That is openxFactory's
    shape's rule and its reason travels: two scopes over one tree can have
    deliberately different membership, and merging them is a defect a ruling has
    already had to correct once elsewhere. One field, two values, no union.
    """

    globs: tuple[str, ...]
    excluded_parts: frozenset[str] = frozenset()


@dataclass(frozen=True)
class WriteProposal:
    """What a caller proposes: the whole of it, and nothing about how."""

    document_key: str
    content: bytes
    actor: str
    basis_revision: str
    reason: str = ""


@dataclass(frozen=True)
class WritePath:
    """A corpus's DECLARED governed write path, as an injectable descriptor.

    The adapter never learns what the path IS. It asks this object for the
    request artifact and the correlation identifier, hands the artifact to
    `dispatch`, and returns a receipt. That indirection is what keeps
    `write_back` a DISPATCH rather than a write, which the interface states as a
    rule: "an implementation that writes the corpus tree here is not conformant,
    even where it would produce identical bytes".

    `dispatch is None` means DECLARED AND UNREACHABLE, which is why the interface
    carries a `write_path_available` flag at all. Flipping it is one construction
    argument rather than a code path, so the act that eventually hardens a
    descendant's write path turns a refusal into a receipt without touching the
    adapter.

    `routes` answers whether one document identity has a target on this path at
    all; None from it is a refusal naming the path, never a fallback write.
    """

    name: str
    build_request: Callable[[WriteProposal], Mapping]
    correlation_id: Callable[[Mapping], str]
    routes: Callable[[str], str | None]
    dispatch: Callable[[Mapping, WriteProposal], None] | None = None
    unavailable_reason: str = ""

    @property
    def available(self) -> bool:
        return self.dispatch is not None


@dataclass(frozen=True)
class CorpusShape:
    """Everything a `DomainCorpusAdapter` needs in order to serve ONE corpus, and
    the only thing it is constructed from.

    `scan_roots` is the STRUCTURAL test `resolve` applies: a tree holding none of
    them cannot be this corpus, and saying that is a different answer from saying
    the corpus is empty. `scopes` drives every listing. `header_scan_lines` bounds
    the window `classify` reads, in REAL lines (see `domain_corpus_adapter`).

    `kind_field` names the header a document's kind is read from; a document
    carrying no value for it is UNCLASSIFIABLE -- reported, named, and still
    listed. `required_fields_by_kind`'s `None` key is the DEFAULT: the fields
    obliged of a kind not separately listed, AND of an unclassifiable document
    too. That second half is not an accident -- a document missing the kind header
    is missing a required field, so one answer covers both.

    `obliged_prefixes` bounds WHERE the field obligation applies; empty means
    everywhere. A corpus can carry one header contract over part of itself and
    none over the rest, and reporting the rest as field-incomplete would be a
    FALSE FINDING -- the failure class this estate has paid for before, and the
    one that costs more trust than a crash because it accuses a correct document.
    """

    scan_roots: tuple[str, ...]
    scopes: Mapping[str, Scope]
    header_scan_lines: int
    kind_field: str | None = None
    required_fields_by_kind: Mapping = None  # type: ignore[assignment]
    obliged_prefixes: tuple[str, ...] = ()
    verdict: Verdict | None = None
    write_path: WritePath | None = None

    def __post_init__(self) -> None:
        if self.required_fields_by_kind is None:
            object.__setattr__(self, "required_fields_by_kind", {})
        if not self.scan_roots:
            raise CorpusShapeInvalid(
                "a corpus shape with no scan roots refuses every corpus it is "
                "ever pointed at, because the structural test `resolve` applies "
                "is 'the tree holds at least one declared root'. Declare the "
                "roots this corpus is laid out under, or build the shape from a "
                "domain profile whose artifact kinds declare locations")
        if self.header_scan_lines < 1:
            raise CorpusShapeInvalid(
                "a header window of "
                f"{self.header_scan_lines} lines reads no line at all, so every "
                "document in this corpus would classify as unrecognizable and "
                "the reader would report a corpus-wide defect that is its own")
        if not self.scopes:
            raise CorpusShapeInvalid(
                "a corpus shape declaring no scopes lists nothing under any "
                "name, so an empty listing would mean 'this shape declares no "
                "globs' and not 'this corpus holds no documents' -- the one "
                "distinction the whole seam is about")
        for root in self.scan_roots:
            _reject_traversal(root, "a scan root")
        for name, scope in self.scopes.items():
            for glob in scope.globs:
                _reject_traversal(glob, f"scope {name!r}")
        for prefix in self.obliged_prefixes:
            _reject_traversal(prefix, "an obliged prefix")


# --------------------------------------------------------------------------
# deriving a shape from a registered domain profile
# --------------------------------------------------------------------------

def _segments(location: str) -> list[str]:
    return [segment for segment in location.replace("\\", "/").split("/")
            if segment]


def _is_placeholder(segment: str) -> bool:
    return (segment.startswith(PLACEHOLDER_OPEN)
            and segment.endswith(PLACEHOLDER_CLOSE)
            and len(segment) > 1)


def _is_pattern(segment: str) -> bool:
    return (_is_placeholder(segment)
            or any(character in segment for character in GLOB_METACHARACTERS))


def scan_root_of(location: str) -> str | None:
    """The literal top-level directory a declared location is rooted under, or
    None where it names no literal root at all.

    The FIRST segment and never the deepest literal prefix: `scan_roots` answers
    "could this tree be this corpus", which is a question about what the tree
    holds at its top and not about how deep the declaration goes. A location
    whose first segment is already a pattern (`<something>/...`) contributes no
    root, because every tree would hold it and a test everything passes is not a
    test.
    """
    segments = _segments(location)
    if not segments or _is_pattern(segments[0]):
        return None
    return segments[0]


def globs_of(location: str, document_globs: tuple[str, ...]) -> tuple[str, ...]:
    """The listing patterns one declared location resolves to.

    A profile declares a location in one of two shapes, and the difference is
    read off the declaration rather than guessed:

      * it already NAMES DOCUMENTS -- its last segment carries glob syntax and it
        does not end in a separator. It is used as written (after placeholder
        normalization) and `document_globs` is not consulted: the profile has
        already said which files it means.
      * it names a DIRECTORY -- anything else, trailing separator or not. Each of
        the caller's `document_globs` is appended beneath it, because only the
        caller knows what a document looks like in its domain. This module must
        not decide that a governed document is a Markdown file.

    Placeholder segments normalize to a single wildcard. `<topic>` is a name for
    a human and a variable for a walker; the word inside the brackets is the
    profile's own and is never read here.
    """
    raw = location.strip()
    segments = _segments(raw)
    if not segments:
        return ()
    normalized = "/".join("*" if _is_placeholder(segment) else segment
                          for segment in segments)
    names_documents = (not raw.endswith("/")
                       and any(character in segments[-1]
                               for character in GLOB_METACHARACTERS))
    if names_documents:
        return (normalized,)
    return tuple(f"{normalized}/{pattern}" for pattern in document_globs)


def from_profile(profile: DomainProfile, *,
                 document_globs: tuple[str, ...],
                 header_scan_lines: int,
                 kind_field: str | None = None,
                 required_fields_by_kind: Mapping | None = None,
                 obliged_prefixes: tuple[str, ...] = (),
                 excluded_parts: frozenset = frozenset(),
                 verdict: Verdict | None = None,
                 write_path: WritePath | None = None) -> CorpusShape:
    """The shape of the corpus a registered domain profile describes.

    THIS FUNCTION IS WHY THIS READER IS THE MAPPING CORE'S AND NOT A SECOND COPY
    OF openxFactory's. RULING C2's word is PARAMETERIZED: a `<Domainx>Dox`
    descendant registers its own `DomainProfile` at process start
    (`domain_profile.register`, the call `current()`'s refusal spells out) and
    gets a reader over its own corpus without writing one. Everything derived
    here is derived from the profile's `artifact_kinds[].locations`, which is the
    only axis of a profile that describes WHERE documents are.

    WHAT IS DERIVED, AND WHAT IS STILL THE CALLER'S:

      * `scan_roots` -- every literal top-level directory the declared locations
        are rooted under, de-duplicated and sorted.
      * `scopes` -- ONE PER ARTIFACT KIND that declares locations, named by the
        kind's own id, plus `SCOPE_ALL` over the union. The per-kind scopes are
        the parameterization a descendant actually asks for ("list me every
        governance document"), and they are free: the profile already carries the
        kind ids and the locations, so declaring them costs nothing and NOT
        declaring them would make `list_documents`' scope argument decorative.
      * `document_globs`, `header_scan_lines`, `kind_field`,
        `required_fields_by_kind`, `obliged_prefixes` -- the CALLER's. The profile
        declares no header axis and no file-shape vocabulary, and inventing
        either here would be this package shipping a domain's words.

    A KIND ID EQUAL TO `SCOPE_ALL` IS REFUSED rather than absorbed. `SCOPE_ALL` is
    the union of every declared scope, so a scope of that name holding one kind's
    globs would answer a `list_documents` for that kind with the WHOLE corpus --
    a silent widening, which is precisely what the interface holds
    `SCOPE_UNKNOWN` in reserve to prevent ("a silent widening is
    indistinguishable from a correct answer").
    """
    per_kind: dict[str, Scope] = {}
    roots: set[str] = set()
    union: list[str] = []
    for kind in profile.artifact_kinds:
        globs: list[str] = []
        for declared in kind.locations:
            # STRIPPED ONCE, HERE, AND BOTH DERIVATIONS READ THE SAME VALUE.
            # `DomainProfile` accepts a non-empty string without trimming it, and
            # `globs_of` used to strip while `scan_root_of` did not -- so a
            # location written `" docs/**/*.md "` produced the scan root
            # `" docs"` (a directory no corpus has) against a glob rooted at
            # `docs`, and every real corpus then refused `corpus-unclassifiable`.
            location = declared.strip()
            _reject_traversal(
                location,
                f"domain profile {profile.mapping_id!r}, artifact kind "
                f"{kind.id!r}")
            root = scan_root_of(location)
            if root is not None:
                roots.add(root)
            for pattern in globs_of(location, document_globs):
                if pattern not in globs:
                    globs.append(pattern)
                if pattern not in union:
                    union.append(pattern)
        if not globs:
            continue
        if kind.id == SCOPE_ALL:
            raise CorpusShapeInvalid(
                f"domain profile {profile.mapping_id!r} declares an artifact "
                f"kind whose id is {SCOPE_ALL!r}, which is the one scope name "
                "every implementation of the corpus-adapter interface SHALL "
                "accept and which means 'every declared scope'. A scope of that "
                "name carrying one kind's globs would answer a listing for that "
                "kind with the whole corpus, and a silent widening is "
                "indistinguishable from a correct answer. Rename the kind")
        per_kind[kind.id] = Scope(globs=tuple(globs),
                                  excluded_parts=excluded_parts)
    if not per_kind:
        raise CorpusShapeInvalid(
            f"domain profile {profile.mapping_id!r} declares no artifact-kind "
            "locations, so there is nothing to say where this domain's "
            "documents are. A reader built from it would list nothing over "
            "every corpus, which reads exactly like an empty corpus and is not "
            "one -- declare `locations:` on at least one artifact kind")
    scopes: dict[str, Scope] = {
        SCOPE_ALL: Scope(globs=tuple(union), excluded_parts=excluded_parts)}
    scopes.update(per_kind)
    return CorpusShape(
        scan_roots=tuple(sorted(roots)),
        scopes=scopes,
        header_scan_lines=header_scan_lines,
        kind_field=kind_field,
        required_fields_by_kind=required_fields_by_kind,
        obliged_prefixes=obliged_prefixes,
        verdict=verdict,
        write_path=write_path,
    )
