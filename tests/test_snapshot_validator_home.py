"""Where `openxdox.snapshot` finds its validator: ONLY in this product's own
tree (split-opendox-two-layer-product § 8.9 residue (ii) and (iii)).

Registered at openxFactory `openspec/changes/archive/2026-09-22-split-opendox-
two-layer-product/tasks.md` § 8.9 (amendment #6, RULED Q-P3 (a),
`opensoft/openxFactory#656` comment 5728856581), verbatim:

  (ii)  "`openxdox/snapshot.py`'s `VALIDATOR_RELPATH` names a path
        `openxFactory` SHED at `cc4ae9d3`, so the constant outlived its target"
  (iii) "`find_validator`'s parent walk ADOPTS an enclosing pre-shed checkout —
        which is `floor37` § 6's defect class, *a reader adopting its enclosing
        tree*"

THE ENCLOSING-TREE CASES RUN A BYTE-IDENTICAL COPY of the module under test,
placed inside a layout built in `tmp_path` whose parent carries a pre-shed
`openxFactory/scripts/validate-ideation-dashboard-contracts.py`. Copying is the
only way to put the module's OWN path under such a parent without touching this
checkout, and it keeps the module under test the real one: the copy is read
from `snapshot.__file__`. Every stand-in validator is a script that prints its
own name, so an assertion can say WHOSE validator ran rather than only that one
did.

`--noconftest`-safe: the standard library, pytest and this package only.
"""

from __future__ import annotations

import importlib.util
import inspect
import os
import shutil
import sys
import uuid
from pathlib import Path

import pytest

from openxdox import snapshot

REPO_ROOT = Path(__file__).resolve().parents[1]
PRE_SHED_RELPATH = (Path("openxFactory") / "scripts"
                    / "validate-ideation-dashboard-contracts.py")


def _stand_in(path: Path, name: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("import sys\n"
                    f"print('{name}: 0 error(s), 0 warning(s)')\n"
                    "sys.exit(0)\n", encoding="utf-8")
    return path


def _snapshot_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(snapshot.canonical_json({
        "schema_version": 1, "kind": "ideation-dashboard-snapshot",
        "repository": "fixture-repo",
        "generation": {"source_revision": "0" * 40},
        "documents": [], "clusters": [], "possibles": [], "staged_topics": [],
        "changes": [], "keyword_index": [],
    }), encoding="utf-8")
    return path


@pytest.fixture
def load_copy():
    """Import a copy of `snapshot.py` from wherever a test placed it, under a
    unique module name, and forget it afterwards."""
    loaded: list[str] = []

    def _load(module_path: Path):
        name = f"_snapshot_copy_{uuid.uuid4().hex}"
        spec = importlib.util.spec_from_file_location(name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module      # `dataclass` resolves its module by name
        loaded.append(name)
        spec.loader.exec_module(module)
        return module

    yield _load
    for name in loaded:
        sys.modules.pop(name, None)


def _product(root: Path, *, own_validator: bool = True,
             distribution: str | None = None) -> Path:
    """A copy of this product's source layout at `root`: its own
    `pyproject.toml`, the module under test at `src/openxdox/snapshot.py`, and —
    unless told otherwise — a stand-in validator at its own `VALIDATOR_RELPATH`."""
    (root / "src" / "openxdox").mkdir(parents=True)
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if distribution is not None:
        pyproject = pyproject.replace('name = "openxdox"', f'name = "{distribution}"', 1)
    (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    shutil.copy2(snapshot.__file__, root / "src" / "openxdox" / "snapshot.py")
    if own_validator:
        _stand_in(root / "scripts" / "validate-ideation-dashboard-contracts.py", "OWN")
    return root


def _enclosed_product(tmp_path: Path, load_copy, *, own_validator: bool = True):
    """The (iii) layout: an enclosing checkout that still carries the pre-shed
    validator at `openxFactory/scripts/...` (with a `.git` boundary of its own),
    and this product nested beneath it."""
    agg = tmp_path / "agg"
    enclosing = _stand_in(agg / PRE_SHED_RELPATH, "ENCLOSING")
    (agg / "openxFactory" / ".git").mkdir()
    product = _product(agg / "work" / "openXdox-code", own_validator=own_validator)
    module = load_copy(product / "src" / "openxdox" / "snapshot.py")
    return agg, enclosing, product, module


# ------------------------------------------------------------------ (ii) ----

def test_the_validator_relpath_names_the_file_this_repository_carries():
    """(ii) The constant is RELATIVE TO THIS REPOSITORY and names the file the
    carve moved here — not the aggregation-relative path openxFactory shed."""
    rel = snapshot.VALIDATOR_RELPATH
    assert rel.parts[0] != "openxFactory", rel
    assert rel == Path("scripts") / "validate-ideation-dashboard-contracts.py"
    assert (REPO_ROOT / rel).is_file(), f"{REPO_ROOT / rel} is not in this checkout"


def test_find_validator_returns_this_products_own_validator():
    """(ii) The product's own validator is found — from the module itself and
    from inside the product's own tree — where the shed constant found nothing."""
    own = REPO_ROOT / snapshot.VALIDATOR_RELPATH
    assert snapshot.find_validator() == own
    assert snapshot.find_validator(REPO_ROOT) == own
    assert snapshot.find_validator(REPO_ROOT / "src" / "openxdox") == own
    assert snapshot.product_root() == REPO_ROOT


def test_a_snapshot_written_anywhere_is_checked_by_this_products_own_validator(tmp_path):
    """(ii) `validate_snapshot` on a snapshot OUTSIDE the product — the ordinary
    case, a run directory — reaches the product's own validator. Only WHICH
    validator is asserted: its verdict depends on whether that validator is
    given its contracts (`CONTRACTS_DIR`), which is residue (i)'s question."""
    result = snapshot.validate_snapshot(_snapshot_file(tmp_path / "run" / "s.json"))
    assert result.validator == REPO_ROOT / snapshot.VALIDATOR_RELPATH


# ----------------------------------------------------------------- (iii) ----

def test_an_enclosing_pre_shed_validator_is_never_adopted(tmp_path, load_copy):
    """(iii) THE REGISTERED DEFECT. The product sits under a checkout that still
    carries the pre-shed validator; the product's OWN validator is the one
    found, and the one that runs, for a snapshot written anywhere under that
    enclosing checkout."""
    agg, enclosing, product, module = _enclosed_product(tmp_path, load_copy)
    own = product / "scripts" / "validate-ideation-dashboard-contracts.py"
    assert module.find_validator() == own

    result = module.validate_snapshot(_snapshot_file(agg / "work" / "out" / "s.json"))
    assert result.validator == own, f"adopted {result.validator}, not {own}"
    assert result.outcome == module.VALIDATED
    assert "OWN" in result.stdout and "ENCLOSING" not in result.stdout


def test_a_start_outside_the_product_is_refused_not_walked(tmp_path, load_copy):
    """(iii) `start` CONFINES. Every directory above or beside the product —
    the enclosing checkout's root, its `openxFactory/`, a run directory — answers
    None; none of them is walked to the enclosing validator sitting right there."""
    agg, enclosing, product, module = _enclosed_product(tmp_path, load_copy)
    assert enclosing.is_file()
    for start in (agg, agg / "openxFactory", agg / "work", agg / "work" / "out"):
        assert module.find_validator(start) is None, start
    assert module.find_validator(product / "src") == \
        product / "scripts" / "validate-ideation-dashboard-contracts.py"


def test_with_no_validator_of_its_own_the_product_refuses_rather_than_adopting(
        tmp_path, load_copy):
    """(iii) The case the walk existed for: the product has no validator of its
    own. The answer is UNAVAILABLE with a reason that says why — never the
    enclosing tree's validator standing in for one."""
    agg, enclosing, product, module = _enclosed_product(tmp_path, load_copy,
                                                        own_validator=False)
    assert module.find_validator() is None
    result = module.validate_snapshot(_snapshot_file(agg / "work" / "out" / "s.json"))
    assert result.outcome == module.VALIDATOR_UNAVAILABLE
    assert result.validator is None
    assert "never adopted" in result.unavailable_reason
    assert str(product / module.VALIDATOR_RELPATH) in result.unavailable_reason


def test_a_snapshot_written_into_a_pre_shed_corpus_does_not_choose_its_validator(
        tmp_path, load_copy):
    """(iii) by a second road. A snapshot written INSIDE a pre-shed openxFactory
    checkout (which has its own `.git` boundary and its own validator) is still
    checked by the product's validator. This also refuses the tempting half-fix
    — re-point the constant and bound the walk at `start`'s first `.git` — which
    would adopt that corpus's own `scripts/validate-ideation-dashboard-contracts.py`."""
    agg, enclosing, product, module = _enclosed_product(tmp_path, load_copy)
    _stand_in(agg / "openxFactory" / "scripts" / "validate-ideation-dashboard-contracts.py",
              "CORPUS")
    result = module.validate_snapshot(_snapshot_file(agg / "openxFactory" / "out" / "s.json"))
    assert result.validator == product / "scripts" / "validate-ideation-dashboard-contracts.py"
    assert "OWN" in result.stdout and "CORPUS" not in result.stdout


def test_the_cwd_is_not_a_search_root(tmp_path, load_copy, monkeypatch):
    """(iii) The walk this replaces started at the cwd when given no `start`, so
    running from inside the enclosing checkout adopted it. The cwd is consulted
    for nothing now, with or without a validator of the product's own."""
    agg, enclosing, product, module = _enclosed_product(tmp_path, load_copy)
    monkeypatch.chdir(product)
    assert module.find_validator() == product / "scripts" / "validate-ideation-dashboard-contracts.py"
    (product / "scripts" / "validate-ideation-dashboard-contracts.py").unlink()
    monkeypatch.chdir(agg / "work")
    assert module.find_validator() is None


def test_a_module_outside_a_source_layout_has_no_root_to_search(
        tmp_path, load_copy, monkeypatch):
    """(iii) An INSTALLED copy — `site-packages/openxdox/snapshot.py`, no `src/`,
    no `pyproject.toml` — has no validator of its own (a wheel ships no
    `scripts/`), and must not borrow the one an enclosing directory carries."""
    _stand_in(tmp_path / PRE_SHED_RELPATH, "ENCLOSING")
    _stand_in(tmp_path / "scripts" / "validate-ideation-dashboard-contracts.py", "ENCLOSING")
    installed = tmp_path / "venv" / "lib" / "site-packages" / "openxdox"
    installed.mkdir(parents=True)
    shutil.copy2(snapshot.__file__, installed / "snapshot.py")
    module = load_copy(installed / "snapshot.py")
    monkeypatch.chdir(tmp_path)
    assert module.find_validator() is None
    assert module.find_validator(tmp_path) is None
    assert module.product_root() is None


def test_a_pyproject_naming_another_distribution_is_not_this_product(
        tmp_path, load_copy, monkeypatch):
    """The marker is EXPLICIT: a source layout whose `pyproject.toml` names some
    other distribution is not this product's root, so nothing under it counts —
    and nothing above it either, however close a pre-shed copy sits."""
    _stand_in(tmp_path / PRE_SHED_RELPATH, "ENCLOSING")
    product = _product(tmp_path / "other", distribution="not-openxdox")
    module = load_copy(product / "src" / "openxdox" / "snapshot.py")
    monkeypatch.chdir(product)
    assert module.find_validator() is None
    assert module.product_root() is None


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="no symlinks on this platform")
def test_a_scripts_link_out_of_the_tree_is_refused(tmp_path, load_copy):
    """Containment is checked on the RESOLVED path: a `scripts/` that is a link
    to a directory outside the product is somebody else's validator by another
    name, and is refused."""
    product = _product(tmp_path / "product", own_validator=False)
    outside = tmp_path / "outside" / "scripts"
    _stand_in(outside / "validate-ideation-dashboard-contracts.py", "OUTSIDE")
    try:
        (product / "scripts").symlink_to(outside, target_is_directory=True)
    except OSError as exc:              # e.g. unprivileged Windows
        pytest.skip(f"cannot create a symlink here: {exc}")
    module = load_copy(product / "src" / "openxdox" / "snapshot.py")
    assert module.product_root() is not None
    assert module.find_validator() is None


def test_find_validator_keeps_its_declared_signature():
    """openDox's `consumer_reach` binds `find_validator` by name and calls it
    with one positional directory; the reach is declared there, so the
    signature does not move with the semantics."""
    params = list(inspect.signature(snapshot.find_validator).parameters.values())
    assert [p.name for p in params] == ["start"]
    assert params[0].default is None
