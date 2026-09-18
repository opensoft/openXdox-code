"""openXdox's DECLARED reader for FLOOR PART 3 -- the `--adapter` factory the
neutral conformance corpus's runner resolves.

WHAT THE FLOOR ASKS OF A DESTINATION. `split-opendox-two-layer-product`
`design.md` § D6 part 3, RULED OQ-1: "A NEUTRAL CONFORMANCE CORPUS EVERY
DESTINATION PASSES ... a corpus with no `openspec/`, no `contracts/`, no
lifecycle headers", and the ruling's word is EVERY -- "openXdox's adapter
implementation and openxFactory's own adapter run it too, which is the only
mechanical proof that `corpus-adapter-seam`'s no-privileged-route requirement
holds for the home corpus". The CHECKS are openxFactory's
(`scripts/carve_conformance.py`) and are never copied here; what a destination
owes is a way to be POINTED AT: a callable `(name, location) -> reader`, named by
the operator on the command line and written down in the pull request that
reports the run.

    python3 scripts/verify-carve-conformance.py \\
        --destination openxdox_code \\
        --dest-root   <this checkout> \\
        --adapter     openxdox.conformance_corpus:reader

WHY THIS FILE IS SO SMALL, WHICH IS THE ARGUMENT AND NOT AN APOLOGY.
openxFactory's own declaration is nine lines and says the same thing about
itself: "what a destination has to write in order to be measured is therefore
exactly this: name your reader, and say how to point it at a location. A
destination that needs more than that has built something the interface cannot
address, which is itself the finding." This one is the same size because
`DomainCorpusAdapter` takes a corpus's terms as construction data, so declaring a
corpus is declaring a VALUE.

NO TRANSPOSITION, AND THAT IS A PROPERTY OF THIS READER RATHER THAN A CONVENIENCE
(RULED Q-X2 (a), `opensoft/openxFactory#656` comment `5715212264`). The other
destination's reader addresses git HISTORY, so the corpus has to be laid down as
repositories before it can be read at all (RULED Q-F1 (a), comment `5714365086`,
`conformance_corpus.transpose()` at openDox). A profile-parameterized FILESYSTEM
reader's location vocabulary is a directory tree, which is exactly what the
corpus is, so the seventeen checks run over `tests/corpus-adapter/fixtures/` AS
IT SHIPS -- same documents, same keys, same bytes, no intermediate form to keep
faithful.

WHY IT SITS UNDER `src/` AND NOT UNDER `tests/`. openxFactory puts its own
factory in `tests/carve_conformance/` for two reasons that are both about
openxFactory: a guard holding every module under `scripts/` to the adapter
package's two public names, and a vocabulary scan over that package's string
literals. Neither exists here, and two considerations point the other way. The
runner imports by MODULE NAME under `--dest-root` roots (`""`, `src`, `scripts`),
so a module under `src/` is reachable by the package name this leg already
installs, with no `--sys-path` and no second import root. And openDox's twin is
specified at `src/opendox/runtime/conformance_corpus.py` (the same file name,
deliberately): the two destinations of § 3.7 declare their readers the same way,
which is what makes the box's eventual tick one sentence in one style.

THE SHAPE BELOW BELONGS TO THE NEUTRAL CORPUS AND TO NOTHING ELSE. Two roots of
its own, a two-field header vocabulary of its own that belongs to no governed
repository, no declared governed write path and no verdict machinery. It is
declared here as a VALUE rather than built from a `DomainProfile` for the reason
the corpus exists: the corpus has no domain, and `domain_profile.current()`
refuses rather than inventing one. `corpus_shape.from_profile` is the path a real
descendant takes and is exercised against the vendored engineering profile in
`tests/test_corpus_shape.py`; this module is the path the FLOOR takes, and the
two produce the same kind of object.
"""

from __future__ import annotations

from opendox.corpus_adapter import SCOPE_ALL

from .corpus_shape import CorpusShape, Scope
from .domain_corpus_adapter import DomainCorpusAdapter

#: The neutral conformance corpus's own terms (RULED OQ-3's seed, openxFactory
#: `tests/corpus-adapter/fixtures/`). Every value here describes THAT corpus and
#: none of them describes openXdox, which is why they are a value in this module
#: rather than a default in `CorpusShape`.
NEUTRAL_SHAPE = CorpusShape(
    scan_roots=("notes", "papers"),
    scopes={SCOPE_ALL: Scope(globs=("**/*.md",))},
    header_scan_lines=6,
    kind_field="Type",
    required_fields_by_kind={None: ("Type", "Title")},
)


def reader(name: str, location: str) -> DomainCorpusAdapter:
    """The factory FLOOR PART 3 asks for: a reader pointed at one location.

    Both arguments are the runner's, and neither is needed to CONSTRUCT the
    reader: the location rides in the `CorpusRef` the runner hands `resolve`, and
    the name is the caller's word for the corpus. That is not an oversight, it is
    the property being measured -- a reader built from a corpus's terms alone can
    be pointed at four different locations in one run, which is what the corpus's
    three resolution-time negative confirmations require.
    """
    del name, location
    return DomainCorpusAdapter(NEUTRAL_SHAPE)
