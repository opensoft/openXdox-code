"""THE DECLARED COMPOSITION, as every test in `tests/integration/` reads it.

Plan 034 task T042 (openxFactory `specs/034-opendox-standalone-operation/`),
box 9.3 of the ratified `add-neutral-product-standalone-operability`:

    "Behaviours needing both legs become declared INTEGRATION tests naming the
     pin they compose at, rather than being dropped from both suites ...
     They live in openXdox-code's `tests/integration/`, because that
     repository's `pyproject.toml` is where the composition is declared: its
     one `opendox` dependency is pinned by full commit."

So the composition is two things, and this module reads both rather than
assuming either:
  * the ONE full-commit pin this leg's `pyproject.toml` declares for
    `opendox` (`tests/opendox_bundle.py::declared_pin`), and
  * the commit the INSTALLED `opendox` was built from, out of the PEP 610
    record pip writes for a VCS install
    (`tests/opendox_bundle.py::installed_commit`).
The two readers are that module's, reused and not copied: both were held to a
long run of review rounds on openXdox-code#21, and a second copy is how two
readers of one declaration drift apart.

THE RULES OF THIS DIRECTORY, and why each is a rule here:

1. EVERY TEST NAMES THE PIN IT COMPOSES AT. It takes the `composition` fixture
   below, which fails unless this checkout IS the declared composition,
   records the pin on the run's report (`composes_at`, a property of the JUnit
   test suite), and returns it, so every assertion message can say which
   openDox it measured. The pin is read from `pyproject.toml` and never
   written into a test. That keeps one declaration: when a later task moves
   the pin (T059, T086), every test here follows it without an edit, and fails
   if the installed openDox did not follow too.

2. NOTHING HERE SKIPS. Elsewhere in this leg a missing bundle may lawfully
   skip, because a consumer may pin a different openDox (RULED
   openxFactory#656 comment 5700475319, and `tests/opendox_bundle.py::_absent`'s
   table). Here the composition is not optional: it is what this directory
   declares, and F9.2 runs every file in it. So an unreadable pin, a different
   installed commit, or a bundle that is not there FAILS, naming what it read.
   A skip would let this suite pass while composing nothing, which is the
   "dropped from both suites" 9.3 exists to end. Leaving a test out of the
   required check is not a skip, and it takes a ruling: the one test left
   out, with its stated reason, until T008, is in
   `test_assembled_surface.py`, which says why and holds the exclusion to it.

3. THERE IS NO `conftest.py` IN THIS DIRECTORY, on purpose. `conftest` is one
   flat module name in `sys.modules`, and a rootless `conftest.py` added here
   would take that slot from `tests/conftest.py` for every module collected
   after this directory (`tests/hermeticity.py::claim_conftest_slot` says how).
   `integration` sorts before every `test_*.py` beside it, so that would be all
   of them. The fixtures live in this plain module instead, and each test
   module imports the ones it uses.

`tests/integration/test_declared_composition.py` holds the directory to all
three. It reads rule 1 from pytest's own collection of the directory, so a
file or a test that pytest collects here cannot pass unexamined.

A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C). Its admission is a `created:` entry in openxFactory's
`docs/opendox-carve-admissions.yaml`, which the openxFactory pin-bump PR carries
(T047), with `since:` the commit that lands it here.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

#: `tests/`, where `opendox_bundle` lives. A run with the conftest chain already
#: has it on `sys.path`, because `tests/conftest.py` is imported from there. This
#: puts it there for a run that names a file here with the chain switched off,
#: so the failure such a run meets is the composition's, not an ImportError.
_TESTS = Path(__file__).resolve().parents[1]
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

import opendox_bundle  # noqa: E402  (after the path line above)

from openxdox import web_assets  # noqa: E402


class CompositionRefused(AssertionError):
    """This checkout is not the composition `pyproject.toml` declares."""


@dataclass(frozen=True)
class Composition:
    """openDox at the one commit this leg pins, as installed here."""

    #: The 40-hex openDox-code commit, read from `pyproject.toml` and equal to
    #: the installed distribution's recorded commit.
    pin: str
    #: The installed openDox's `web/` bundle, where RULED Q5's assembly puts
    #: this column's view assets.
    web: Path

    def __str__(self) -> str:
        return f"openDox-code@{self.pin}"


def read_composition() -> Composition:
    """The declared composition, or `CompositionRefused` naming what was read.

    Refuses for exactly four reasons, each its own message: `pyproject.toml`
    declares no full-commit `opendox` pin; the installed `opendox` records no
    commit; it records a DIFFERENT commit; or openDox at the pin carries no
    `web/` bundle. The first two are F9.2's own assertions: the composition
    names a full-commit pin, and the openDox installed is that one.
    """
    declared = opendox_bundle.declared_pin()
    if declared is None:
        raise CompositionRefused(
            "pyproject.toml declares no full-commit pin of the form `opendox @ "
            "git+https://github.com/opensoft/openDox-code@<40-hex>`, so this "
            "suite has no composition to name. 9.3 puts the composition in that "
            "one declaration, and F9.2 refuses a pin that is not a full commit")
    installed = opendox_bundle.installed_commit()
    if installed is None:
        raise CompositionRefused(
            f"pyproject.toml pins openDox-code@{declared}, but the installed "
            "`opendox` records no openDox-code commit (PEP 610 "
            "`direct_url.json`). pip writes one for every VCS install, so this "
            "is not the pinned install: `pip install '.[test]'` makes it")
    if installed != declared:
        raise CompositionRefused(
            f"the installed openDox is openDox-code@{installed}, and "
            f"pyproject.toml pins openDox-code@{declared}. This suite composes "
            "at the declared pin and at no other commit, which is F9.2's "
            "second assertion. Reinstall with `pip install '.[test]'`")
    web = opendox_bundle.find()
    if web is None:
        raise CompositionRefused(
            f"openDox-code@{declared} is installed at the pin, and it carries "
            "no `web/` bundle (no `views/helpers.js` under the installed "
            "`opendox`). openDox's wheel has carried `web/**` as package data "
            "since openDox-code#20 (`8efb3cf`), so this is a regression at the "
            "pin")
    return Composition(pin=declared, web=web)


#: The compositions this process has already written to the run's report, so
#: the report names each once rather than once per test.
_RECORDED: set[str] = set()


@pytest.fixture
def composition(record_testsuite_property) -> Composition:
    """The composition this test runs at, recorded on the run's report.

    Fails, never skips (rule 2 above): a test here that cannot name its pin has
    nothing to measure.

    The report carries the pin as a `composes_at` property of the test SUITE,
    written once. That is the JUnit form the default `xunit2` family admits:
    pytest refuses a per-test property there with a warning, and a pin is a
    fact about the whole run anyway, since this directory composes at one.
    Each test still names it, because every message it fails with starts with
    the composition it measured.
    """
    try:
        found = read_composition()
    except CompositionRefused as refused:
        pytest.fail(f"no declared composition: {refused}", pytrace=False)
    if str(found) not in _RECORDED:
        record_testsuite_property("composes_at", str(found))
        _RECORDED.add(str(found))
    return found


@pytest.fixture
def assembled_web(composition: Composition, tmp_path: Path) -> Path:
    """A COMPOSED bundle: openDox's own `web/` at the pin, with this column's
    view assets placed into it by the assembly hook RULED Q5 names.

    This is the assembly `tests/test_gate_loop_probes.py`'s `bundle` fixture
    makes, with `overwrite=False`, which the hook offers "for an installer that
    wants to know the bundle was clean". At the pin, openDox's `views/` carries
    none of the ten names this column places. So a collision here would be one
    of openXdox's assets still shipped by openDox, and it refuses rather than
    being overwritten.
    """
    target = tmp_path / "web"
    shutil.copytree(composition.web, target)
    web_assets.install_view_modules(target, overwrite=False)
    return target
