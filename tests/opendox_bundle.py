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
pointed the tests at the wrong leg."* Eight further suites at this leg name the
same constant as a SERVE ROOT without naming a view module, so the real count is
31 files and 47 sites.

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
`opendox/web/**` into a wheel at all. Until this leg's pin advances past that
commit, an installed `opendox` carries no bundle — so a module that imports this
one SKIPS, exactly as S5's probes do, rather than failing on a stand-in. A
skipped suite says "the pin is behind"; a failing one would say "the code is
wrong", and only one of those is true.
"""

from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path

import pytest

#: The marker file: any real openDox bundle carries it, and it is class A in the
#: census (`openDox-code tests/fixtures/web_boundary_census.yaml`), so it is not
#: one of the six modules openXdox itself contributes back under RULED Q5.
_MARKER = ("views", "helpers.js")

_REASON = (
    "the installed `opendox` carries no `web/` bundle: this leg pins a commit "
    "older than openDox's own packaging declaration (`[tool.setuptools."
    "package-data] opendox = [\"web/**\"]`, openDox-code#20, § 3.4 slice S5), "
    "so there is nothing here to read. The pin bump makes this suite run — the "
    "same bump `tests/test_gate_loop_probes.py` and `tests/test_gate_loop_"
    "views.py` already wait on. SKIPPED, never failed: the code under test is "
    "not what is missing.")


def find() -> Path | None:
    """The installed openDox's `web/` bundle, or None where the pin carries none."""
    try:
        import opendox
    except ModuleNotFoundError:          # pragma: no cover - no consumer pinned
        return None
    web = Path(opendox.__file__).resolve().parent / "web"
    return web if web.joinpath(*_MARKER).is_file() else None


def require() -> Path:
    """`find()`, or SKIP the importing module where the pin carries no bundle."""
    web = find()
    if web is None:
        pytest.skip(_REASON, allow_module_level=True)
    return web


#: The module-level constant the carved suites bind. Importing this name is what
#: makes a suite skip rather than explode where the pin is behind.
OPENDOX_WEB = require()


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
