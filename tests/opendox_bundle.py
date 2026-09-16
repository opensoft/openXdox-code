"""The INSTALLED openDox bundle — where this leg's suites read openDox's `web/`.

**A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`**
(RULED OQ-C — the manifest declares what LEAVES openxFactory, never what a
destination assembles). It is admitted by name in
`docs/opendox-carve-admissions.yaml`, under § 3.4 slice S8.

WHAT THIS REPAIRS, and why it is a path and not a move.
`docs/front-end-package-boundary.md` § 1.2(d) measured it exactly: *"23 at
openXdox-code [name a `views/<name>.js` path], and every one of them resolves it
under `REPO_ROOT / "src" / "openxdox" / "web"` — a directory openXdox-code does
not have … the carve's `import rewrites` edit class rewrote the path constant and
pointed the tests at the wrong leg."* Further suites at this leg name the same
constant as a SERVE ROOT without naming a view module, and the total is the one
**openXdox-code#19's LANDING re-derived** (`main 0a0265f`, "RE-DERIVED AT LANDING,
AND ONLY THE COUNT MOVED"): under a named, re-runnable instrument — a ROOT SPELLING
is a line spelling `REPO_ROOT / "src" / "openxdox" / "web"` in any Path or slash
form, counted over the REVISIONS with `git grep` and never a worktree — **46 root
spellings over 31 files**, as 22 resolving a concrete `views/<name>.js` module plus
9 using the root as a serve root (the ninth being the tool at
`tests/tools/playwright-smoke.py`, outside `validate`'s list). `validate.yml`'s S8
block carries that same 46. The review rounds on #19 said "31 files, 47 sites";
that figure is left ATTRIBUTED and not restated, for #19's own reason — a root
spelled once carries several derived sites, so neither total corrects the other —
and this line asserted it as "the real count" until the review of `de7d966` on #21
found the two numbers disagreeing across this repository.

The note's § 5 S8 row then infers that those files *"go to the leg the census
says owns each bundle file"*. **That inference does not hold, and the reason is
RULED OQ-G's own TEST HOMES rule.** Every one of the 23 imports a real `openxdox`
module — `openxdox.generator`, `openxdox.snapshot_registry`,
`openxdox.gate_console`, `openxdox.gate_routes`, `openxdox.doxbench_scope`,
`openxdox.round_trip` — and OQ-G places a mixed file HERE precisely because
**openXdox pins openDox and openDox pins nothing back** (split-opendox § 4.2,
RULED OQ-2). Moved to openDox-code each one fails on its first import line, and
declaring `openxdox` there would be the unlawful direction
`tests/test_dependency_direction.py` exists to refuse. So the placement RULED
OQ-G made is CORRECT and the path constant is the whole defect — which is what
§ 1.2(d)'s own sentence says.

WHERE THE BUNDLE ACTUALLY IS, AND WHOSE PRECEDENT THIS IS.
It is in the openDox this leg PINS. Slice S5 landed the identical resolution at
this leg, in `tests/test_gate_loop_probes.py::_opendox_bundle`, for the same
reason and with the same skip:

    web = Path(opendox.__file__).resolve().parent / "web"

and S5 leg B (`openDox-code#20`) landed the packaging declaration that puts
`opendox/web/**` into a wheel at all. THIS LEG'S PIN HAS NOW ADVANCED PAST IT —
2026-09-16, `a99eba03` -> `0b4e8bbf` (openDox-code#23, § 3.4 slice S8 leg B) —
and the bundle is there: `find()` returns a real directory under the installed
`opendox`, and the suites that import `OPENDOX_WEB` run instead of skipping.
This paragraph used to end "Until this leg's pin advances past that commit, an
installed `opendox` carries no bundle", which was true of `a99eba03` and is
quoted here as provenance, not as a claim.

A SKIP STAYS FOR TWO CASES AND TWO ONLY — and THAT IT STAYS AT ALL is ruled, not
chosen here. RULED openxFactory#656 comment 5700475319 (Brett Heap, 2026-09-16,
by interactive multi-choice): asked whether to keep these guards with corrected
reasons or delete them on pin lockstep #2's precedent, Brett Heap answered
(a) KEEP THEM and correct the reasons, "they test the ASSEMBLED openDox; a
consumer may pin behind the view contract".

This paragraph overstated the skip until the review of `7c0a3b6` on
openXdox-code#21. A missing bundle is honest to skip
where the installed distribution records a commit that is NOT the one this leg
declares — note the claim is "different", never "older": nothing here proves an
ordering, only a disagreement — and where the installation records no provenance
at all AND the run is off CI. Everywhere else `_absent()` fails closed, the
declared pin included, and under CI unrecorded provenance included.

FOUR OUTCOMES, NOT THREE. Two review rounds on #21 caught this paragraph running
them together: at `27a89fd` it had one sentence for both SKIPS, and at `f6f1b991`
the sentence below still said every FAILURE means "the openDox we declare is
wrong", which is true of one of the two failures and a misdiagnosis of the other.
`_absent()`'s docstring holds the canonical table; these are the four things it
says, and they are four different claims:

  * DIFFERENT commits -> SKIP, saying "this is not the openDox we declare" and
    naming both commits to prove it;
  * an unreadable side, OFF CI -> SKIP, saying only "the comparison could not be
    made". It claims nothing about what is installed, and it exists because off
    the required path an unreadable side is lawful;
  * EQUAL commits -> FAIL, saying "the openDox we declare is wrong". This is the
    only outcome that is an assertion about the package;
  * an unreadable side, UNDER CI -> FAIL, naming WHICH side could not be read
    and saying the two commits could not be COMPARED. It does NOT say "this run
    cannot say which openDox is installed": where `pyproject.toml` is the
    unreadable side the installed commit is in hand and gets printed, so that
    claim was false for one of the two shapes this row covers — caught at the
    review of `24cd5f2` on #21. It is a COMPARISON anomaly, not proof of a bad
    package: `validate.yml` installs `-e ".[test]"` against a PEP 508 direct VCS
    reference and pip records `direct_url.json` for that every time, so a
    required run that cannot read one side has lost the ability to check, which
    is itself worth stopping for.

The guard's whole job is to keep those four apart instead of answering "skip" to
all of them.
"""

from __future__ import annotations

import atexit
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import NoReturn

import pytest

#: The marker file: any real openDox bundle carries it, and it is class A in the
#: census (`openDox-code tests/fixtures/web_boundary_census.yaml`), so it is not
#: one of the six modules openXdox itself contributes back under RULED Q5.
_MARKER = ("views", "helpers.js")

# `_REASON`, the module-level skip string, is GONE — `_absent()` below composes the
# reason from what it measured instead of stating it in advance. It read "this leg
# pins a commit older than openDox's own packaging declaration … The pin bump makes
# this suite run", which was true of `a99eba03` and became false at `0b4e8bbf`; the
# replacement's whole point is that it cannot go stale, because every reason is
# composed from what the run just read. In the DIFFERENT-COMMIT outcome that is the
# two commits, named; where a side is unreadable there is no comparison to name, and
# the reason says WHICH side could not be read instead. (The review of `e6cd0e8`
# caught this comment claiming the two commits for all four rows.)


def find() -> Path | None:
    """The installed openDox's `web/` bundle, or None where no bundle was found.

    DISCOVERY ONLY: this function tests for the marker and says nothing about
    WHY it is absent. `None` used to be documented as "the pin carries none",
    which was the single expected cause before the bump and is now one of four
    (a regression at the declared pin, a consumer at a different commit, or
    either side unreadable). Classifying it is `_absent()`'s job and its table
    is not restated here — a caller that read the old line could have concluded
    "stale pin, skip" and walked straight past the identity check. Caught at the
    review of `399e2a9` on openXdox-code#21.
    """
    try:
        import opendox
    except ModuleNotFoundError:          # pragma: no cover - no consumer pinned
        return None
    web = Path(opendox.__file__).resolve().parent / "web"
    return web if web.joinpath(*_MARKER).is_file() else None



# ---------------------------------------------------------------------------
# PROVENANCE — WHICH openDox IS ACTUALLY INSTALLED, and why the skip must ask.
#
# Copilot's round-1 review of openXdox-code#21 (suppressed comment on this file,
# and the same finding twice more on `tests/test_gate_loop_probes.py` and
# `tests/test_gate_loop_views.py`) was ACCURATE and is answered here rather than
# argued: `find()` tests for a MARKER, never for an identity, so a skip reason
# that says "the installed `opendox` came from somewhere older than the declared
# pin" was asserting something it had not measured. Before the pin bump that cost
# nothing — a missing bundle WAS the declared state. After it the same skip would
# hide the opposite fact: if the declared pin itself ever stopped shipping
# `web/**`, thirteen node probes, three materialization assertions and every
# bundle suite would go quietly green in a REQUIRED check, and the coverage this
# bump exists to gain would be lost in silence.
#
# So the two facts are now READ, and the skip is conditional on them:
#   * `declared_pin()`   — the 40-hex this leg's own `pyproject.toml` declares.
#   * `installed_commit()` — the commit pip actually built, out of the
#     distribution's `direct_url.json` (PEP 610), which a VCS install always
#     records.
# Bundle missing AND the two agree  -> FAIL: a regression at the declared pin.
# Bundle missing AND they differ    -> SKIP: a consumer assembling at a
#                                      DIFFERENT commit, both named in the
#                                      reason. DIFFERENT, never "older": this
#                                      guard compares two identities and never
#                                      asks git which came first.
# Provenance unreadable, UNDER CI   -> FAIL. Round 2 of the same review was right
#                                      that skipping here left the required job
#                                      able to go green with the bundle missing;
#                                      on the required path an unreadable
#                                      provenance is itself the anomaly, because
#                                      `validate.yml` installs a PEP 508 direct
#                                      VCS reference and pip records one every
#                                      time.
# Provenance unreadable, OFF CI     -> SKIP, saying so: an editable checkout or a
#                                      hand-placed wheel lawfully has none, and
#                                      nothing measured means nothing claimed.
# ---------------------------------------------------------------------------

#: A git object name, matched CASE-INSENSITIVELY and normalized to lowercase
#: below. Copilot asked for the normalization on openXdox-code#21, and it can
#: only ever turn an "unknown" into a real comparison: a lawful record that
#: happens to spell its commit in upper case would otherwise read as
#: unreadable provenance and FAIL under CI for a formatting difference.
_SHA_RE = re.compile(r"[0-9a-fA-F]{40}")

_PIN_RE = re.compile(r"opendox\s*@\s*git\+[^@\s\"']+@([0-9a-fA-F]{40})")


def declared_pin() -> str | None:
    """The openDox-code commit `pyproject.toml` declares, or None if unreadable."""
    toml = Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        match = _PIN_RE.search(toml.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        # UnicodeDecodeError is a ValueError, NOT an OSError, so a non-UTF-8
        # `pyproject.toml` would have escaped this function and bypassed
        # `_absent()`'s explicit unknown-provenance policy altogether. Caught at
        # the review of `27a89fd` on openXdox-code#21. The `# pragma: no cover`
        # that sat on this line is GONE rather than kept: the review of
        # `f6f1b991` asked for a test that makes the read fail, and BOTH raising
        # types are now driven by
        # `tests/test_gate_loop_probes.py::test_declared_pin_is_none_when_*`, so
        # the pragma had become a false claim about the branch it labelled.
        return None
    return match.group(1).lower() if match else None


def installed_commit() -> str | None:
    """The commit the INSTALLED `opendox` was built from (PEP 610), or None.

    None means NO USABLE PROVENANCE WAS READ — which is broader than "none was
    recorded", and saying only the narrow thing made this contract inaccurate
    (caught at the review of `27a89fd` on #21). It covers: no `direct_url.json`,
    malformed JSON, an `archive_info` (non-VCS) install, a record whose `vcs` is
    not git, a `commit_id` that is not 40 hex, the distribution lookup raising,
    and the read raising. Every one of those has its own test below.

    WHAT THE CALLER DOES WITH None IS NOT "always skip", and this docstring said
    so until Copilot's round-3 review of #21 caught it: `_absent()` FAILS on None
    under CI and SKIPS off it. The rule is the required path, not the value —
    see `_absent()`'s own table. A future caller that reads only this line would
    otherwise bypass the safety rule the required check depends on.
    """
    try:
        from importlib.metadata import distribution
        raw = distribution("opendox").read_text("direct_url.json")
    except Exception:
        # Driven by `test_installed_commit_is_none_when_the_package_is_not_installed`
        # (the LOOKUP raises) and `…_when_reading_the_record_raises` (the read does).
        return None
    if not raw:
        return None
    try:
        vcs_info = json.loads(raw).get("vcs_info") or {}
        vcs, commit = vcs_info.get("vcs"), vcs_info.get("commit_id")
    except (ValueError, AttributeError):
        # Driven by `test_installed_commit_is_none_on_malformed_json`.
        return None
    # BOTH CHECKS ARE LOAD-BEARING, and the second is Copilot's finding at the
    # head before this one: `len(commit) == 40` admitted any forty CHARACTERS, so
    # a malformed record carrying a forty-character non-hex id read as "a
    # different pin" and `_absent()` SKIPPED under CI — the silent green this
    # whole guard exists to prevent, reached through the parser instead of
    # through the decision. A commit id is 40 lowercase hex and the record must
    # say it is git, or this function does not know what is installed.
    if vcs != "git" or not isinstance(commit, str):
        return None
    return commit.lower() if _SHA_RE.fullmatch(commit) else None


def under_ci() -> bool:
    """True on the REQUIRED path — GitHub Actions sets `CI=true` on every runner."""
    return os.environ.get("CI", "").strip().lower() in {"1", "true", "yes"}


def _unreadable_side(declared: str | None, installed: str | None) -> str:
    """WHICH side of the comparison could not be read — never "which openDox is
    installed", because two of these three shapes have a commit in hand.

    Copilot's review of `24cd5f2` on #21 caught the CI branch saying "this run
    cannot say which `opendox` is installed" while the very next field printed the
    installed hash: when `pyproject.toml` is the unreadable side, the provenance is
    known and it is the COMPARISON that cannot be made. Both branches compose their
    phrase here now, so the two can no longer drift apart — which is how the off-CI
    branch came to name the side (review of `27a89fd`) while the CI branch did not.
    """
    if declared is None and installed is None:
        return ("NEITHER side could be read: this leg's declared pin is unreadable "
                "in `pyproject.toml` and the installed distribution records no "
                "usable PEP 610 provenance")
    if declared is None:
        return "this leg's declared pin could not be read from `pyproject.toml`"
    return ("no usable PEP 610 provenance could be read from the installed "
            "distribution")


def _absent(subject: str, *, module_level: bool) -> NoReturn:
    """Raise the RIGHT outcome for a missing `subject`.

    | installed vs declared | outcome |
    | --- | --- |
    | equal | FAIL — a regression at the pin this leg declares |
    | different | SKIP — a consumer assembling at a DIFFERENT commit (identity, never ancestry) |
    | UNKNOWN, under CI | FAIL — see below |
    | UNKNOWN, off CI | SKIP — a developer box may install however it likes |

    THE "UNKNOWN, UNDER CI" ROW IS COPILOT ROUND 2's FINDING, and it was right:
    skipping on unknown provenance left the required `validate` job able to go
    green with the bundle missing, which is the exact silence this guard exists to
    break. On the required path unknown provenance is not a neutral state — 
    `validate.yml` installs with `pip install -e ".[test]"` against a PEP 508
    direct VCS reference, and pip records `direct_url.json` for that every time —
    so failing to read one there is itself the anomaly. Off CI the permissive
    branch stays, because an editable checkout or a hand-placed wheel is a lawful
    way to work and has no provenance to record.
    """
    declared, installed = declared_pin(), installed_commit()
    if declared is not None and installed is not None and declared == installed:
        pytest.fail(
            f"{subject} is missing from the `opendox` this leg DECLARES "
            f"(`pyproject.toml` pins {declared[:8]}, and the installed "
            f"distribution records that same commit in its `direct_url.json`). "
            f"That is a REGRESSION at the declared pin, not a stale consumer, so "
            f"it fails here instead of skipping: a skip would take every suite "
            f"that depends on {subject} quietly green in a required check.")
    if declared is None or installed is None:
        unreadable = _unreadable_side(declared, installed)
        if under_ci():
            pytest.fail(
                f"{subject} is missing and the two commits could not be COMPARED: "
                f"{unreadable} (declared={declared or 'unreadable'}, "
                f"installed={installed or 'unrecorded'}). Where the field above "
                f"prints a commit, THAT side was read fine; nothing here claims the "
                f"installed openDox is unknown. On CI the unreadable side is itself "
                f"the anomaly: `validate.yml` installs `-e \".[test]\"` against a "
                f"PEP 508 direct VCS reference, and pip records `direct_url.json` "
                f"for that every time. Failing rather than skipping, because a skip "
                f"here is exactly the silent green this guard exists to prevent.")
        pytest.skip(
            f"{subject} is missing and the comparison could not be made: {unreadable} "
            f"(declared={declared or 'unreadable'}, "
            f"installed={installed or 'unreadable'}). NOTHING is claimed here about "
            f"whether the installed openDox IS the declared one — the comparison "
            f"never happened. This is not the different-commit skip, which reads "
            f"both sides and names them. Off the CI path an unreadable side is "
            f"lawful (an "
            f"editable checkout or a hand-placed wheel records none). Under CI this "
            f"same condition FAILS.",
            allow_module_level=module_level)
    pytest.skip(
        f"{subject} is missing, and this is NOT the declared pin's doing: the "
        f"installed distribution was built from {installed[:8]}, while "
        f"`pyproject.toml` declares {declared[:8]}. Under the declared pin these "
        f"suites RUN — reaching this reason means the `opendox` actually installed "
        f"came from somewhere else (an assembly at its own pin, or a stale editable "
        f"checkout).",
        allow_module_level=module_level)


_STAGED: Path | None = None


def require(*, module_level: bool = True) -> Path:
    """The pinned bundle, STAGED once per process as an ESM-marked tree — or,
    where there is none, whatever `_absent()` decides.

    THE OUTCOME IS `_absent()`'s FOUR-ROW TABLE AND THIS DOCSTRING DOES NOT
    RESTATE IT. Two reviews on #21 caught a paraphrase here losing a row (first
    "SKIP where the pin carries no bundle", then a summary that dropped the
    off-CI unreadable case), which is what a second copy of a table is for. Read
    `_absent()`.

    `module_level` SCOPES THE SKIP OUTCOME AND NOTHING ELSE. With True a skip
    takes the IMPORTING MODULE, which is what the thirty suites whose whole
    subject is the bundle want; `web()` below passes False, so a skip takes only
    the calling TEST (see its docstring for when that is the honest reading). The
    FAIL outcomes — the declared pin, and an unreadable side under CI — are not
    scoped by it at all: `pytest.fail` fails the test that reached the guard,
    whichever flag was passed. The review of `e6cd0e8` caught this paragraph
    reading as though the flag governed every outcome.

    WHY A STAGED COPY AND NOT THE INSTALLED DIRECTORY ITSELF (Copilot review of
    openXdox-code#19, the `test_round_trip.py` finding — accurate). Several of
    these suites hand a module of this bundle to `node` by ABSOLUTE PATH from a
    `.mjs` harness in `tmp_path`, and node decides a `.js` file's format from
    the NEAREST `package.json` to the file itself. openDox-code carries one at
    its repository root — `{"type": "module"}`, added by openDox-code#14 for
    exactly this reason — but it is NOT under `src/opendox/web/`, so it is not
    in the wheel's `package-data` and an installed bundle has no ESM marker
    above it at all. Importing from there would fall to node's
    `--experimental-detect-module` heuristic: on by default today, a warning,
    and not a thing a required check should rest on. Staging the tree and
    writing the marker beside it is what openDox-code's own `package.json`
    docstring calls "an explicit, version-independent answer", and it is what
    slice S5's `tests/test_gate_loop_probes.py::bundle` fixture already does
    for the composed case.

    READ-ONLY BY CONVENTION, like the directory it copies: every caller of this
    root copies OUT of it into `tmp_path`. It is staged ONCE per process — the
    suites that use it number thirty and a per-test copytree would be thirty
    copies of a 41-file tree for no added isolation.
    """
    global _STAGED
    if _STAGED is None:
        web = find()
        if web is None:
            # THE 29 IMPORTER ANNOTATIONS THAT REACH THIS LINE ARE STALE, AND
            # THEY ARE NOT REPAIRED HERE. Copilot's review of `399e2a9` on
            # openXdox-code#21 is right about the fact: 29 files carry
            # `from opendox_bundle import OPENDOX_WEB  # noqa: E402  (skips
            # where the pin carries no bundle)`, and after the bump this path
            # also FAILS — at the declared pin, and for an unreadable side under
            # CI. Measured, not estimated:
            #   grep -rn 'skips where the pin carries no bundle' tests/ \
            #        --include='test_*.py'                              -> 29
            #     sites in 29 files. The --include is load-bearing: this comment
            #     quotes the annotation, so the unfiltered command answers 30 and
            #     counts the helper that reports the count. Caught at the review
            #     of `de7d966` on #21.
            #   git diff --name-only main -- <those 29>                  -> 0
            #   all 29 appear in openxFactory `docs/opendox-carve-manifest.yaml`
            # Every one of them is an ARRIVED carve row whose edits are declared
            # at openxFactory, and none is otherwise touched by this act, so
            # editing them here would be an undeclared edit to a declared
            # surface — the same ground on which
            # `tests/test_doxbench_mutation_boundary.py` is DROPPED from
            # `validate.yml` rather than repaired. Registered as residue in #21's
            # description for a later declared act. Nothing is hidden by the
            # wait: the annotation is a `# noqa` justification, while the
            # outcome those files actually get is composed below, from what it
            # measured, and names itself in full.
            _absent("openDox's `web/` bundle", module_level=module_level)
        staging = Path(tempfile.mkdtemp(prefix="opendox-bundle-"))
        atexit.register(shutil.rmtree, staging, True)
        target = staging / "web"
        shutil.copytree(web, target)
        target.joinpath("package.json").write_text('{"type": "module"}\n',
                                                   encoding="utf-8")
        # AND `vendor/` BACK TO CommonJS (Copilot review of openXdox-code#19,
        # accurate). The root marker above sets the package scope for the WHOLE
        # staged tree, `vendor/` included, and the one file there is a vendored
        # UMD build — `markdown-it.min.js` — that `tests/test_explorer_viewer.py`
        # hands to node with `require()`. Under an inherited `"type": "module"`
        # that is `ERR_REQUIRE_ESM`: the ESM marker this function exists to write
        # would have broken the one suite that reads the vendored file the old
        # way. Three suites at this leg already write exactly this marker into
        # their own copies (`test_doxbench_transport.py`,
        # `test_doxbench_mutation_boundary.py`, `test_session_confinement.py`),
        # so the staged root states the same thing once, in the same place it
        # states the ESM one. Written only where the directory exists, because a
        # bundle carrying no vendor tree must not gain a package.json for a
        # directory it does not have.
        vendor = target / "vendor"
        if vendor.is_dir():
            vendor.joinpath("package.json").write_text(
                '{"type": "commonjs"}\n', encoding="utf-8")
        _STAGED = target
    return _STAGED


def web() -> Path:
    """The pinned bundle; where there is none, `_absent()`'s outcome scoped to
    the CALLING TEST rather than the module. Which outcome is `_absent()`'s
    table's to say, and this docstring does not restate it — for the reason
    `require()` above gives.

    FOR THE SUITE WHOSE SUBJECT IS NOT THE BUNDLE (Copilot review of
    `openXdox-code#19` is the class of finding this anticipates, and the
    measurement is `tests/test_doxbench_turns.py`: 183 tests, of which THREE
    read a bundle file and 180 exercise this leg's own scope resolution and
    openDox's turn assembler). Binding `OPENDOX_WEB` at module level there
    would trade 37 failing tests for 183 skipped ones — the repair would
    SILENCE more than it fixed, and a required check would go green over a
    suite it no longer runs.

    So the rule is the subject, not the convenience: a module whose every test
    reads the bundle imports `OPENDOX_WEB` and takes the outcome module-wide; a
    module where the bundle is an aside calls this and takes it per test. WHERE
    THE OUTCOME IS A SKIP, that reads "skips whole" and "skips the three tests
    that need it"; where `_absent()` FAILS — the declared pin, or an unreadable
    side under CI — the failure lands on whatever test reached the guard, and no
    scoping flag softens it. Caught at the review of `e6cd0e8`, which was right
    that promising a skip here contradicts the table this docstring defers to.
    """
    return require(module_level=False)


def __getattr__(name: str) -> Path:
    """`OPENDOX_WEB`, RESOLVED ON THE IMPORT AND NOT ON THIS MODULE'S OWN.

    PEP 562, and it is load-bearing rather than a style. `OPENDOX_WEB =
    require()` at this module's top level runs at the FIRST import of this
    file, so it skipped every module that imported ANY name from here —
    `web()` included — and a per-test skip could not exist beside it. Resolved
    here, the module-level skip is raised while the importing module executes
    `from opendox_bundle import OPENDOX_WEB`, which is exactly where it was
    raised before and what makes that suite skip whole; a module that imports
    only `web` never asks for this name and never skips on the import.
    """
    if name == "OPENDOX_WEB":
        return require()
    raise AttributeError(name)


# ---------------------------------------------------------------------------
# THE COMPOSED BUNDLE — RULED Q5's deployment, materialized once.
#
# Four suites at this leg assert ACROSS the seam: they read openDox's own
# modules AND the six this column contributes back (`swb-session.js`,
# `swb-create.js`, `dispose.js`, `gate.js`, `gate-lens.js`, `gate-projects.js`).
# Neither root alone answers them — openDox's bundle does not carry this
# column's modules and this column's package data does not carry openDox's —
# and RULED Q5 (`#656` comment `5648044785`) says what does: *"the COMPOSED
# DEPLOYMENT assembles the bundle. openXdox ships its view modules as package
# data; the composed install copies them into openDox's one `--web-dir` at
# assembly."*
#
# So the composed root is built by the assembly hook ITSELF —
# `openxdox.web_assets.install_view_modules()`, the same call `serve_views` and
# `tests/test_gate_loop_probes.py::bundle` use — rather than by a hand-rolled
# copy that could drift from it. Built ONCE per process and read-only: every
# caller copies OUT of it into `tmp_path`, which is what these suites already
# did with the repository tree they used to point at.
_COMPOSED_ROOT: Path | None = None


def composed() -> Path:
    """openDox's bundle with THIS column's six modules installed into it."""
    global _COMPOSED_ROOT
    if _COMPOSED_ROOT is None:
        from openxdox import web_assets
        staging = Path(tempfile.mkdtemp(prefix="openxdox-composed-"))
        atexit.register(shutil.rmtree, staging, True)
        target = staging / "web"
        shutil.copytree(require(), target)
        web_assets.install_view_modules(target)
        _COMPOSED_ROOT = target
    return _COMPOSED_ROOT
