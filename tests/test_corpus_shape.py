"""`openxdox.corpus_shape`: the construction data, and the derivation from a
registered domain profile that makes this reader the MAPPING CORE's.

WHAT IS ASSERTED HERE AND WHAT IS ASSERTED NEXT DOOR.
`tests/test_domain_corpus_adapter.py` holds the six operations, the refusal
vocabulary and the structural conformance. This file holds the DATA: what a
shape refuses to be, and what `from_profile` derives from a profile's artifact
kinds. The split follows the leg's own convention of one test module per source
module.

A CREATED FILE: no row in `docs/opendox-carve-manifest.yaml` (RULED OQ-C, the
manifest declares what LEAVES openxFactory). It stands alone under
`--noconftest`, which is what `.github/workflows/validate.yml` runs
(`tests/conftest.py` reaches two packages this leg does not carry), and it
imports nothing beyond `pytest`, the standard library and this package.

THE PROFILE THIS EXERCISES `from_profile` AGAINST is the vendored
`tests/fixtures/openxfactory-engineering-profile.yaml` -- the same fixture
`tests/test_domain_profile.py` uses. It is a REAL profile with six artifact
kinds and eleven declared locations in four shapes (a glob, a placeholder
directory, a plain directory, and two kinds sharing a root), which is what makes
it worth deriving from: a hand-built two-line profile would exercise the easy
half of the derivation only.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from opendox.corpus_adapter import SCOPE_ALL

from openxdox import domain_profile
from openxdox.corpus_shape import (
    CorpusShape,
    CorpusShapeInvalid,
    Scope,
    WritePath,
    WriteProposal,
    from_profile,
    globs_of,
    scan_root_of,
)

FIXTURE = (Path(__file__).resolve().parent / "fixtures"
           / "openxfactory-engineering-profile.yaml")


def _shape(**overrides) -> CorpusShape:
    """A minimal valid shape, one keyword away from each refusal below."""
    fields = dict(scan_roots=("one", "two"),
                  scopes={SCOPE_ALL: Scope(globs=("**/*.md",))},
                  header_scan_lines=6)
    fields.update(overrides)
    return CorpusShape(**fields)


# --------------------------------------------------------------------------
# the data types
# --------------------------------------------------------------------------

def test_a_scope_carries_its_own_exclusions_and_defaults_to_none() -> None:
    """Per-scope and not shared: two scopes over one tree can have deliberately
    different membership, and merging them is a defect a ruling has already had
    to correct elsewhere."""
    bare = Scope(globs=("**/*.md",))
    assert bare.excluded_parts == frozenset()
    narrowed = Scope(globs=("**/*.md",), excluded_parts=frozenset({"drafts"}))
    assert narrowed.excluded_parts == frozenset({"drafts"})
    assert bare.excluded_parts == frozenset(), (
        "the default must not be a shared mutable object; a second Scope's "
        "exclusions would otherwise appear on the first")


def test_a_write_path_is_unavailable_until_a_dispatch_is_injected() -> None:
    """`dispatch is None` means DECLARED AND UNREACHABLE, which is why the
    interface carries `write_path_available` at all. Flipping it is one
    construction argument and never a code path."""
    declared = WritePath(name="a-governed-path",
                         build_request=lambda proposal: {},
                         correlation_id=lambda request: "x",
                         routes=lambda key: key)
    assert declared.available is False
    reachable = WritePath(name="a-governed-path",
                          build_request=lambda proposal: {},
                          correlation_id=lambda request: "x",
                          routes=lambda key: key,
                          dispatch=lambda request, proposal: None)
    assert reachable.available is True


def test_a_write_proposal_carries_the_whole_of_what_is_proposed() -> None:
    proposal = WriteProposal(document_key="k", content=b"c", actor="a",
                             basis_revision="r")
    assert (proposal.document_key, proposal.content, proposal.actor,
            proposal.basis_revision, proposal.reason) == (
                "k", b"c", "a", "r", "")


def test_the_required_fields_table_defaults_to_empty_and_not_to_none() -> None:
    """`classify` indexes this table. A `None` here would make every
    classification raise instead of answering, and an answer is what `classify`
    owes even for a document it cannot recognize."""
    assert _shape().required_fields_by_kind == {}


# --------------------------------------------------------------------------
# what a shape refuses to BE -- each refusal is one mutation of the valid shape
# --------------------------------------------------------------------------

def test_a_shape_with_no_scan_roots_is_refused_at_construction() -> None:
    """Not at the first `resolve`. An empty scan-root tuple makes the structural
    test `any(...)` false for every tree, so the reader would refuse every
    corpus with `corpus-unclassifiable` and send the operator to look at a
    corpus that is fine."""
    with pytest.raises(CorpusShapeInvalid) as caught:
        _shape(scan_roots=())
    assert "scan roots" in str(caught.value)


def test_a_shape_with_no_scopes_is_refused_at_construction() -> None:
    """An empty listing would then mean 'this shape declares no globs' rather
    than 'this corpus holds no documents' -- the one distinction the whole seam
    is about."""
    with pytest.raises(CorpusShapeInvalid) as caught:
        _shape(scopes={})
    assert "scopes" in str(caught.value)


@pytest.mark.parametrize("window", [0, -1])
def test_a_header_window_that_reads_no_line_is_refused(window: int) -> None:
    """Every document would classify as unrecognizable and the reader would
    report a corpus-wide defect that is its own."""
    with pytest.raises(CorpusShapeInvalid):
        _shape(header_scan_lines=window)


def test_a_one_line_header_window_is_legal() -> None:
    """The refusal is on a window that reads NOTHING, not on a small one: a
    corpus whose kind header is the first line is a legitimate corpus."""
    assert _shape(header_scan_lines=1).header_scan_lines == 1


# --------------------------------------------------------------------------
# reading a declared location: where its literal root ends, and what it globs
# --------------------------------------------------------------------------

@pytest.mark.parametrize("location,expected", [
    ("docs/**/*.md", "docs"),
    ("ideation/staging/<topic>/", "ideation"),
    ("openspec/changes/<change-id>/", "openspec"),
    ("health/", "health"),
    ("review", "review"),
    ("/leading/separator/", "leading"),
    ("<anything>/below", None),
    ("*/below", None),
    ("", None),
    ("/", None),
])
def test_the_scan_root_is_the_first_literal_segment(location: str,
                                                    expected: str | None) -> None:
    """The FIRST segment and never the deepest literal prefix: `scan_roots`
    answers "could this tree be this corpus", which is about what the tree holds
    at its top. A location whose first segment is already a pattern contributes
    NO root, because a test everything passes is not a test."""
    assert scan_root_of(location) == expected


@pytest.mark.parametrize("location,expected", [
    # already names documents -- used as written, `document_globs` unconsulted
    ("docs/**/*.md", ("docs/**/*.md",)),
    ("notes/*.txt", ("notes/*.txt",)),
    # a directory -- each document glob is appended beneath it
    ("health/", ("health/**/*.md", "health/**/*.rst")),
    ("review", ("review/**/*.md", "review/**/*.rst")),
    # a placeholder segment normalizes to one wildcard
    ("ideation/staging/<topic>/",
     ("ideation/staging/*/**/*.md", "ideation/staging/*/**/*.rst")),
    # a trailing separator makes it a directory even where it carries a glob
    ("docs/*/", ("docs/*/**/*.md", "docs/*/**/*.rst")),
    ("", ()),
])
def test_a_declared_location_globs_by_the_shape_it_declares(
        location: str, expected: tuple[str, ...]) -> None:
    """The two shapes are read off the declaration rather than guessed, and the
    caller's `document_globs` decide what a document looks like -- this module
    must not decide that a governed document is a Markdown file."""
    assert globs_of(location, ("**/*.md", "**/*.rst")) == expected


def test_the_placeholder_word_is_never_read() -> None:
    """`<topic>` and `<change-id>` differ only in a word that belongs to the
    profile. A derivation that read it would be this package learning a
    domain's vocabulary through a path."""
    assert (globs_of("a/<topic>/", ("**/*.md",))
            == globs_of("a/<change-id>/", ("**/*.md",)))


# --------------------------------------------------------------------------
# from_profile -- the parameterization RULING C2 exists for
# --------------------------------------------------------------------------

@pytest.fixture()
def engineering() -> domain_profile.DomainProfile:
    return domain_profile.load(FIXTURE)


def test_the_fixture_is_the_profile_this_derivation_is_measured_against(
        engineering) -> None:
    """Measured, not assumed: if the fixture's kinds or locations change, the
    expectations below have to be re-derived rather than silently drifting."""
    assert engineering.mapping_id == "openxfactory-engineering"
    assert [kind.id for kind in engineering.artifact_kinds] == [
        "governance-document", "staging-topic", "openspec-change",
        "register-possible", "projection", "evidence-record"]
    assert sum(len(kind.locations) for kind in engineering.artifact_kinds) == 11


def test_scan_roots_are_the_literal_roots_the_profile_declares(
        engineering) -> None:
    shape = from_profile(engineering, document_globs=("**/*.md",),
                         header_scan_lines=6)
    assert shape.scan_roots == ("docs", "health", "ideation", "openspec",
                                "review")


def test_every_artifact_kind_that_declares_locations_becomes_a_scope(
        engineering) -> None:
    """The parameterization a descendant actually asks for: "list me every
    governance document". It is free -- the profile already carries the kind ids
    and the locations -- and not declaring it would make `list_documents`' scope
    argument decorative."""
    shape = from_profile(engineering, document_globs=("**/*.md",),
                         header_scan_lines=6)
    assert set(shape.scopes) == {
        SCOPE_ALL, "governance-document", "staging-topic", "openspec-change",
        "register-possible", "projection", "evidence-record"}
    assert shape.scopes["governance-document"].globs == (
        "docs/**/*.md", "ideation/**/*.md", "review/**/*.md")
    assert shape.scopes["staging-topic"].globs == (
        "ideation/staging/*/**/*.md",)


def test_scope_all_is_the_union_of_every_kind_and_holds_no_duplicate(
        engineering) -> None:
    shape = from_profile(engineering, document_globs=("**/*.md",),
                         header_scan_lines=6)
    union = shape.scopes[SCOPE_ALL].globs
    assert len(union) == len(set(union)), "the union de-duplicates"
    for name, scope in shape.scopes.items():
        if name == SCOPE_ALL:
            continue
        assert set(scope.globs) <= set(union), (
            f"{name}'s globs are not all in the union, so a listing under "
            f"{SCOPE_ALL!r} would miss documents a named scope lists")
    # `review/` is declared by TWO kinds (`governance-document` as a glob,
    # `evidence-record` as a directory). Both spellings survive into the union
    # and neither is dropped as a near-duplicate of the other.
    assert "review/**/*.md" in union


def test_the_derivation_carries_the_callers_data_through_untouched(
        engineering) -> None:
    """The profile declares no header axis and no file-shape vocabulary (RULED
    Q-X3 (a), openxFactory#656 comment 5715212264). Inventing either here would
    be this package shipping a domain's words."""
    def verdict(corpus, known, subjects):
        return ()

    path = WritePath(name="p", build_request=lambda proposal: {},
                     correlation_id=lambda request: "c",
                     routes=lambda key: key)
    shape = from_profile(engineering, document_globs=("**/*.md",),
                         header_scan_lines=9, kind_field="Status",
                         required_fields_by_kind={None: ("Status",)},
                         obliged_prefixes=("docs/",),
                         excluded_parts=frozenset({"archive"}),
                         verdict=verdict, write_path=path)
    assert shape.header_scan_lines == 9
    assert shape.kind_field == "Status"
    assert shape.required_fields_by_kind == {None: ("Status",)}
    assert shape.obliged_prefixes == ("docs/",)
    assert shape.verdict is verdict
    assert shape.write_path is path
    assert all(scope.excluded_parts == frozenset({"archive"})
               for scope in shape.scopes.values())


def test_document_globs_reach_every_directory_shaped_location(
        engineering) -> None:
    """Two suffixes in, two globs out under each directory-shaped location --
    proof the caller's vocabulary is applied and not sampled."""
    shape = from_profile(engineering, document_globs=("**/*.md", "**/*.yaml"),
                         header_scan_lines=6)
    assert shape.scopes["register-possible"].globs == (
        "ideation/dashboard/registers/**/*.md",
        "ideation/dashboard/registers/**/*.yaml")


def test_a_kind_named_all_is_refused_rather_than_absorbed(engineering) -> None:
    """`SCOPE_ALL` means "every declared scope". A scope of that name carrying
    one kind's globs would answer a listing for that kind with the WHOLE corpus,
    and "a silent widening is indistinguishable from a correct answer"."""
    raw = domain_profile.load(FIXTURE)
    kinds = list(raw.artifact_kinds)
    kinds[0] = type(kinds[0])(id=SCOPE_ALL, label=kinds[0].label,
                              description=kinds[0].description,
                              locations=kinds[0].locations)
    collides = type(raw)(**{**raw.__dict__, "artifact_kinds": tuple(kinds)})
    with pytest.raises(CorpusShapeInvalid) as caught:
        from_profile(collides, document_globs=("**/*.md",),
                     header_scan_lines=6)
    assert SCOPE_ALL in str(caught.value)
    assert "widening" in str(caught.value)


def test_a_profile_declaring_no_locations_is_refused(engineering) -> None:
    """A reader built from it would list nothing over every corpus, which reads
    exactly like an empty corpus and is not one."""
    kinds = tuple(type(kind)(id=kind.id, label=kind.label,
                             description=kind.description, locations=())
                  for kind in engineering.artifact_kinds)
    bare = type(engineering)(**{**engineering.__dict__,
                                "artifact_kinds": kinds})
    with pytest.raises(CorpusShapeInvalid) as caught:
        from_profile(bare, document_globs=("**/*.md",), header_scan_lines=6)
    assert "declares no artifact-kind locations" in str(caught.value), (
        "and it is THIS refusal rather than the empty-scan-roots one two lines "
        "later: an operator handed 'this shape has no scan roots' would go and "
        "look at the corpus, and the defect is in the profile")


def test_the_derivation_reads_only_the_profiles_location_axis(
        engineering) -> None:
    """A profile whose lifecycle vocabulary, acts, authorities and truth store
    are stripped still derives the same shape. The reader is parameterized by
    WHERE the documents are; the rest of the profile is the lifecycle engine's
    and is not this reader's business."""
    full = from_profile(engineering, document_globs=("**/*.md",),
                        header_scan_lines=6)
    stripped = type(engineering)(
        mapping_id=engineering.mapping_id,
        artifact_kinds=engineering.artifact_kinds,
        lifecycle=(), acts=(), evidence_classes=(), authorities=(),
        truth_store=engineering.truth_store)
    assert from_profile(stripped, document_globs=("**/*.md",),
                        header_scan_lines=6) == full
