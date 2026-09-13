"""The DECLARED HOSTED FALLBACK for this column's view modules (RULED Q5).

RULED Q5 (`opensoft/openxFactory#656` comment `5648044785`, Brett Heap,
2026-09-12): *"the COMPOSED DEPLOYMENT assembles the bundle. openXdox ships its
view modules as package data; the composed install copies them into openDox's
one `--web-dir` at assembly; **a contributed GET route is the declared hosted
fallback**. § 4.4's bundle-relative rule stands."*

WHEN THE FALLBACK IS THE RIGHT MECHANISM. `openxdox.web_assets.install_view_modules()`
is the primary path and is the dull one: after it runs, a contributed module is
an ordinary file of the served bundle. It needs a writable bundle. A deployment
that serves openDox's `web/` read-only — a container layer, a read-only mount, a
wheel installed into a site-packages nobody writes into — cannot run it, and
this module is what makes that deployment lawful instead of unserved.

WHY EXACT BINDINGS AND NOT A `/views/` PREFIX. openDox consults contributed
routes AFTER every fixed core arm and BEFORE the static fallback
(`opendox/serve.py`'s `_route`), so a PREFIX binding on `/views/` would
intercept every one of openDox's own view modules and this column would be
answering for the shell's files. Six EXACT bindings claim exactly the six paths
this column contributes and nothing else; anything else under `/views/` falls
through to openDox's static fallback exactly as it does today. That is the same
discipline `route_extension.collect_bindings` enforces between columns, applied
by this column to itself.

THE HANDLER IS A METHOD NAME, never a callable: `serve.build_server()` refuses a
build whose contributed handler does not resolve on the bound handler class, so
the mixin below must be composed into `DashboardHandler` exactly as
`serve_gate.GateRoutes` is.

A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C).
"""

from __future__ import annotations

import route_extension

from openxdox import web_assets

__all__ = [
    "JS_CTYPE",
    "ContributedViewModuleRoutes",
    "ViewModuleRoutesExtension",
    "view_module_bindings",
]

#: The media type an ES module must be served with. A browser refuses to
#: evaluate a module served as anything else, and a refusal from the module
#: loader is exactly the "failed to load" refusal `resolveView` reports without
#: being able to say why — so it is stated here rather than inferred.
JS_CTYPE = "text/javascript; charset=utf-8"


class ContributedViewModuleRoutes:
    """The GET door for this column's view modules, mixed into `DashboardHandler`.

    `self._serve_bytes` resolves through the MRO to openDox's own
    implementation, exactly as every method `serve_gate.GateRoutes` uses does —
    that is what makes a contributed route reach the same response discipline a
    fixed core arm reaches.
    """

    def _serve_contributed_view_module(self, head_only: bool) -> None:
        """Answer one exact `/views/<module>.js` this column declares.

        The binding is EXACT, so openDox's dispatcher calls this with
        `head_only` alone and the path is read off the request. The name is
        re-checked against the declared set rather than trusted: the dispatcher
        only ever routes a declared pattern here, and a handler that would serve
        whatever path it was handed is a directory traversal waiting for the
        day someone adds a prefix binding.
        """
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        prefix = f"/{web_assets.BUNDLE_SUBDIR}/"
        name = path[len(prefix):] if path.startswith(prefix) else ""
        if name not in web_assets.VIEW_MODULE_NAMES:
            # Not this column's to answer. 404 rather than falling through:
            # the dispatcher already decided this route is ours, and serving
            # openDox's bundle from here would be the fork the seam prevents.
            self.send_error(404, "not found")
            return
        self._serve_bytes(web_assets.module_source(name), JS_CTYPE, head_only)


def view_module_bindings() -> tuple[route_extension.RouteBinding, ...]:
    """One EXACT GET binding per declared view module, in declaration order."""
    return tuple(
        route_extension.RouteBinding(
            "GET", web_assets.served_path(name), False,
            "_serve_contributed_view_module")
        for name in web_assets.VIEW_MODULE_NAMES
    )


class ViewModuleRoutesExtension:
    """openXdox's route contribution for the view column's BYTES.

    Deliberately a SECOND extension rather than more bindings on
    `serve_gate.GateRoutesExtension`: that one contributes the gate VERBS, a
    POST prefix the whole estate reasons about as "the gate column's routes",
    and folding six static GETs into it would make `contributed_routes` — which
    openDox's registry checks every view binding's ownership against — read as
    though the gate column had claimed the shell's view directory.

    NOT REGISTERED BY DEFAULT. An assembly that ran the copy hook must NOT also
    register this extension: the modules are already in the bundle, and two
    answers for one path is the collision `collect_bindings` exists to refuse.
    The profile names one mechanism or the other, and says which.
    """

    def routes(self) -> tuple[route_extension.RouteBinding, ...]:
        return view_module_bindings()
