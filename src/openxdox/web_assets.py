"""The gate loop's VIEW MODULE BYTES, and the assembly hook that places them.

RULED Q5 (`opensoft/openxFactory#656` comment `5648044785`, Brett Heap,
2026-09-12, on openXdox-spec `docs/gate-loop-view-contract.md` § 8 Q5 @
`d73767b7`): **"where a contributed view module's BYTES come from: the COMPOSED
DEPLOYMENT assembles the bundle. openXdox ships its view modules as package
data; the composed install copies them into openDox's one `--web-dir` at
assembly; a contributed GET route is the declared hosted fallback. § 4.4's
bundle-relative rule stands."**

THE GAP THIS CLOSES, in the contract note's own words: *"`_MODULE` admits only a
bundle-relative `./…js` (`view_extension.py`:193-202), `resolveView` resolves it
against the bundle root (`views/view_extension.js`:400), and `build_server`
serves ONE directory (`serve.py`:1596; default `--web-dir` at :1743).
`openXdox-code` `main` `17384c07` carries no `.js` file at all. So a module
openXdox contributes has no route into the directory the browser imports
from."* This module is that route, and it is deliberately the DULLEST of the two
lawful mechanisms: a copy at assembly time, so that in the running server a
contributed module is an ordinary file of the served bundle and every rule the
registry already enforces — bundle-relative specifiers, no remote script,
§ 4.4's vendor policy — holds without a second code path. The hosted fallback,
for a deployment that cannot write into the bundle, is `openxdox.serve_views`.

WHAT THIS MODULE IS NOT. It is not a build step, a bundler or a watcher: it
copies N declared files once, refuses what it cannot place, and reports what it
placed. An installer (`openDox`'s composed assembly, a container build, a
`make`) calls `install_view_modules(web_dir)` after openDox's own bundle is in
place and before the server starts.

A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C — the manifest declares what LEAVES openxFactory, never what a
destination assembles).
"""

from __future__ import annotations

import shutil
from pathlib import Path

__all__ = [
    "BUNDLE_SUBDIR",
    "VIEW_MODULE_DIR",
    "VIEW_MODULE_NAMES",
    "ViewAssetError",
    "install_view_modules",
    "module_path",
    "module_source",
    "served_path",
]


class ViewAssetError(RuntimeError):
    """An assembly that cannot place this column's view modules.

    One exception for every placement defect — a missing package file, a target
    that is not a directory, a copy that failed — because a caller does nothing
    different for any of them: they are all "this bundle must not be assembled
    this way", which is `route_extension.RouteBindingError`'s reasoning applied
    to bytes instead of routes.
    """


#: Where the modules live INSIDE this package. Shipped by
#: `pyproject.toml`'s `[tool.setuptools.package-data]`, so the paths below
#: resolve in an installed wheel and not only in a source checkout.
VIEW_MODULE_DIR: Path = Path(__file__).resolve().parent / "web" / "views"

#: Where they must land INSIDE openDox's served `--web-dir`. Not a choice:
#: every binding this column declares names `./views/<file>` and
#: `resolveView` resolves that against the bundle root, so the subdirectory is
#: fixed by the specifier the registry already refuses to widen.
BUNDLE_SUBDIR = "views"

#: The six modules, in the order `view_extensions.VIEW_BINDING_SPECS` declares
#: their bindings. DECLARED rather than globbed: a file that appears in the
#: package directory without a binding to declare it would be a module shipped
#: into somebody else's bundle with nothing naming it, and a glob is how that
#: happens quietly.
VIEW_MODULE_NAMES: tuple[str, ...] = (
    "gate.js",
    "gate-lens.js",
    "gate-projects.js",
    "dispose.js",
    "swb-create.js",
    "swb-session.js",
)


def module_path(name: str) -> Path:
    """The packaged path of one declared module, refusing an undeclared name."""
    if name not in VIEW_MODULE_NAMES:
        raise ViewAssetError(
            f"{name!r} is not one of this column's declared view modules "
            f"({list(VIEW_MODULE_NAMES)}): a module nothing declares is a file "
            "shipped into another leg's bundle with no binding naming it")
    path = VIEW_MODULE_DIR / name
    if not path.is_file():
        raise ViewAssetError(
            f"declared view module {name!r} is missing from this package at "
            f"{path}: the wheel was built without "
            "`[tool.setuptools.package-data] openxdox = [\"web/views/*.js\"]`, "
            "so every binding this column declares names a module that cannot "
            "load — and a binding that cannot be mounted must not look "
            "registered (openDox `views/view_extension.js`'s own rule)")
    return path


def module_source(name: str) -> bytes:
    """One declared module's bytes — what both mechanisms hand over."""
    return module_path(name).read_bytes()


def served_path(name: str) -> str:
    """The URL path the browser imports this module from.

    `./views/gate.js` resolved against the bundle root, which is what
    `views/view_extension.js`'s `resolveView` computes and therefore what the
    hosted fallback (`openxdox.serve_views`) must answer.
    """
    return f"/{BUNDLE_SUBDIR}/{name}"


def install_view_modules(web_dir: str | Path, *,
                         overwrite: bool = True) -> tuple[Path, ...]:
    """THE ASSEMBLY HOOK. Copy this column's view modules into openDox's bundle.

    `web_dir` is the ONE directory `serve.build_server(web_dir=…)` serves. The
    modules land in its `views/` subdirectory, which is where the specifier
    every binding declares resolves to.

    Returns the placed paths, in declaration order, so an installer can log or
    assert what it assembled rather than trusting that it did.

    REFUSAL, NOT A DEFAULT — `build_server()`'s own posture. A `web_dir` that
    does not exist is an assembly error and not something to create: creating it
    would mean assembling a bundle that has no openDox in it, and the first
    symptom would be a page that never loads rather than an install that
    refused. `overwrite=False` refuses an existing file instead of replacing
    it, for an installer that wants to know the bundle was clean.
    """
    target_root = Path(web_dir)
    if not target_root.is_dir():
        raise ViewAssetError(
            f"--web-dir {str(target_root)!r} is not a directory: this column's "
            "view modules are copied INTO openDox's assembled bundle (RULED "
            "Q5), so the bundle must already be there. Assemble openDox first, "
            "then place this column")
    target_dir = target_root / BUNDLE_SUBDIR
    if not target_dir.is_dir():
        raise ViewAssetError(
            f"{str(target_dir)!r} does not exist: openDox's bundle keeps its "
            f"view modules in `{BUNDLE_SUBDIR}/`, and every binding this column "
            "declares names `./views/<file>`. A bundle with no views directory "
            "is not the bundle these modules were declared against")
    placed: list[Path] = []
    for name in VIEW_MODULE_NAMES:
        source = module_path(name)
        destination = target_dir / name
        if destination.exists() and not overwrite:
            raise ViewAssetError(
                f"{str(destination)!r} already exists and overwrite=False: "
                "this column's module would replace a file the bundle already "
                "carries, which is either a second copy of the gate loop or a "
                "name collision, and neither is something to do silently")
        shutil.copyfile(source, destination)
        placed.append(destination)
    return tuple(placed)
