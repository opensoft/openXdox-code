"""The gate loop's CSS extraction, re-derived where both legs are present.

WHERE THESE CASES CAME FROM. openDox-code#55 (plan 034 task T037, box 9.4)
took them out of openDox-code's `tests/test_binding_stylesheets.py`, where
they SKIPPED on every run of that leg's suite: they need openXdox's six
contributed view modules and its sheets, and openDox never ships them, because
RULED Q5 places them at assembly. That pull request's body and that file's
closing comment send them here, to the declared composition (T042; FR-006,
"Behaviour that needs both legs SHALL be declared integration tests at the
declared composition"):

  * `test_the_gate_exclusive_set_is_re_derived_where_the_modules_are_present`,
    with the scan of an ASSEMBLED bundle's `views/**/*.css` that the same file
    ran as `test_no_contributed_sheet_declares_a_design_token`. Here the six
    are placed in the pinned openDox's bundle on every run, so the derivation
    asserts for real: no class the six name and no openDox file names is still
    declared in `styles.css`, and each of the 54 classes is named by one of
    the six.
  * `test_a_partial_assembly_is_a_failure_and_not_a_skip`, with its helper
    `_assembled_views()`. Its rule existed so that a partial assembly could not
    hide behind the first case's skip.

openDox-code keeps the half that needs no assembly, and asserts it on every run
there: `test_opendox_own_bundle_names_no_gate_exclusive_class`. openXdox-code's
`tests/test_gate_loop_views.py` already carries the design-token guard over
every sheet this leg declares, with its negative control, so this file scans
only what an ASSEMBLY placed.

WHAT IS VERBATIM, AND WHAT CHANGED ON ARRIVAL. The helpers
(`_blank_css_comments`, `_selector_classes`, `_blank_code_comments`,
`_ST_DECLARATION` and `_declared_st_tokens`) and the `GATE_EXCLUSIVE` tuple are
openDox-code's text at `55194335`, the last commit that carried all five, byte
for byte. The tuple and the three helpers openDox-code kept are unchanged at
`2d116415` and at `814516b7`. Their comments are kept too, so "Copilot review, round N" in them
is a round on openDox-code#27, where that file was written. Four things changed,
each because this is the composition and not a lone leg:
  1. A missing assembly FAILS here, where it skipped there. The composition is
     what this directory declares (`declared_composition.py`, rule 2).
  2. The bundle is `assembled_web`, a copy of the pinned openDox's `web/` with
     this column's assets placed by `web_assets.install_view_modules()`, in
     place of a module-level `WEB` that pointed at openDox-code's own tree. So
     `_assembled_views()` takes the bundle as an argument, and the
     partial-assembly case passes a scratch bundle where it used to patch
     `WEB`.
  3. The six module names are `web_assets.VIEW_MODULE_NAMES`, this column's own
     declaration, where openDox-code carried a copy of them. It is the same six
     in the same order.
  4. Every test takes `composition`, so it names the pin it composes at, and
     its messages say which openDox they measured.

A CREATED file: no carve-manifest row (RULED OQ-C). Its admission is a
`created:` entry in openxFactory's `docs/opendox-carve-admissions.yaml` (T047).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from declared_composition import (  # noqa: F401  (fixtures, by name)
    Composition,
    assembled_web,
    composition,
)

from openxdox import view_extensions, web_assets

#: The six modules this column contributes (RULED Q5's package data), in the
#: order `view_extensions.VIEW_BINDING_SPECS` declares their bindings. The name
#: openDox-code's copy of them went by is kept, so the cases below read as they
#: did there.
GATE_MODULES = web_assets.VIEW_MODULE_NAMES

#: The 54 classes the census measures as the gate loop's own at openDox-code
#: `0b4e8bbf` / openXdox-code `0a0265f7`: every class named by one of the six
#: modules and by NO file of openDox's own bundle. Carried from openDox-code's
#: `tests/test_binding_stylesheets.py`, where the lone leg asserts that
#: `styles.css` declares none of them and that its own bundle names none. That
#: the six name every one needs both legs, so it is checked here, and the
#: carried tuple is held to this column's own count of it
#: (`view_extensions.STYLE_RESIDUE["exclusive_classes"]`) below.
GATE_EXCLUSIVE = (
    "dispose-accepted", "dispose-deferred", "dispose-propose", "dispose-rejected",
    "disposetray", "gatebar", "gatebar-actions", "gatebar-cmd", "gatebar-title",
    "gatebtn", "gatebtn-live", "intentchips", "is-busy", "is-error", "is-ok",
    "is-queued", "is-refused", "is-stalled", "panelbuttons", "panelfield",
    "panelhead", "panellabel", "panelmembers", "panelnote", "projectform",
    "projectmember", "projectname", "projectpanel", "refusalpanel",
    "refusalpanel-clear", "refusalpanel-head", "refusalpanel-item",
    "refusalpanel-kind", "refusalpanel-list", "refusalpanel-msg",
    "refusalpanel-title", "swb-cactions", "swb-ccmd", "swb-cdescriptor",
    "swb-cform", "swb-ch", "swb-chelp", "swb-clanded", "swb-cline", "swb-cnote",
    "swb-crefused", "swb-creq", "swb-cresult", "swb-csource", "swb-cwrap",
    "swb-notice", "swb-sessionactions", "swb-sessionbtn",
    "swb-sessiondescriptors",
)


def _blank_css_comments(css: str) -> str:
    """`/* … */` blanked, newlines kept — a selector scan must not read prose."""
    out, i, n = [], 0, len(css)
    while i < n:
        if css.startswith("/*", i):
            j = css.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", css[i:j]))
            i = j
            continue
        out.append(css[i])
        i += 1
    return "".join(out)


def _selector_classes(css: str) -> set[str]:
    """Every class token declared in a SELECTOR, comments and bodies excluded.

    The body is excluded because `content: ".foo"` and a `url(.../x.css)` are
    not selectors; the comments because openDox's prose may legitimately discuss
    a rule that has left, and a scan that read it would make the record of a
    move into a violation of it.
    """
    scan = _blank_css_comments(css)
    out: set[str] = set()
    i, n, seg = 0, len(scan), 0
    while i < n:
        c = scan[i]
        if c == "{":
            prelude = scan[seg:i]
            if not prelude.strip().startswith("@"):
                out.update(re.findall(r"\.([A-Za-z_][A-Za-z0-9_-]*)", prelude))
            depth, j = 1, i + 1
            while j < n and depth:
                if scan[j] == "{":
                    depth += 1
                elif scan[j] == "}":
                    depth -= 1
                j += 1
            if prelude.strip().startswith("@"):
                out |= _selector_classes(scan[i + 1:j - 1])
            i = seg = j
            continue
        if c == ";":
            seg = i + 1
        i += 1
    return out


def _blank_code_comments(text: str, html: bool = False) -> str:
    """`//`, `/* */` and `<!-- -->` blanked, QUOTE-AWARE, newlines kept.

    A COMMENT IS NOT OWNERSHIP EVIDENCE (Copilot review, round 2). The orphan
    register below asks "does openDox's own bundle NAME this class", and a raw
    concatenation answers yes for a class mentioned only in a comment or a
    docstring — so a gate-only selector left behind in `styles.css` could be
    excused by prose that never emits it, which is the one way that register
    can be talked out of a finding.

    QUOTE-AWARE and not a regex, because `"https://…"` carries a `//` inside a
    string and blanking from there would delete real code — a false GREEN is
    what this whole function is about, and a false RED for the same reason is
    no better. A local copy of `test_web_boundary.py`'s walk rather than an
    import: these files are collected `--noconftest` as top-level modules and
    neither may depend on the other being importable.
    """
    out, i, n = [], 0, len(text)
    quote = ""
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if quote:
            out.append(c)
            if c == "\\":
                if i + 1 < n:
                    out.append(nxt)
                i += 2
                continue
            if c == quote:
                quote = ""
            i += 1
            continue
        if not html and c in "\"'`":
            quote = c
            out.append(c)
            i += 1
            continue
        if html and text.startswith("<!--", i):
            j = text.find("-->", i + 4)
            j = n if j < 0 else j + 3
            out.append(re.sub(r"[^\n]", " ", text[i:j]))
            i = j
            continue
        if not html and c == "/" and nxt == "/":
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        if not html and c == "/" and nxt == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", text[i:j]))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


#: A CUSTOM PROPERTY IS DECLARED WHEREVER A DECLARATION MAY START, not only at
#: the beginning of a line (Copilot review, round 1). This read
#: `^\s*(--st-…)\s*:` under `re.M`, and every sheet in this bundle is written
#: one rule per line — `.x { --st-proposed: red; }` declares the token after a
#: `{`, and a second declaration after a `;`, and the guard saw neither. The
#: contexts a declaration can follow are the start of the text, `{` and `;`;
#: `var(--st-…)` is a READ and is bounded by `(`, which is none of them.
_ST_DECLARATION = re.compile(r"(?:^|[{;])\s*(--st-[A-Za-z0-9_-]+)\s*:")


def _declared_st_tokens(css: str) -> list[str]:
    """Every `--st-*` this stylesheet WRITES. Comments must already be blanked."""
    return _ST_DECLARATION.findall(css)


def _assembled_views(web: Path) -> Path | None:
    """`views/` if an assembly has placed the contributed modules there.

    A PARTIAL ASSEMBLY IS NOT "NO ASSEMBLY" (Copilot review, round 5). This
    returned `None` unless all six were present, so a bundle carrying five of
    them skipped the derived ownership check entirely and a packaging error
    hid behind a pytest skip. Absent is a legitimate state — this leg ships
    none of the six, and RULED Q5 places them at assembly — but a bundle that
    has SOME of them has been assembled wrongly, and that is a failure here
    rather than a silence.

    (openDox-code's text at `55194335`, with the bundle an argument where it
    was the module-level `WEB`. "This leg" is openDox-code there. At the
    composition, absent is NOT a legitimate state, and the caller that meets
    `None` fails.)
    """
    views = web / "views"
    present = [name for name in GATE_MODULES if (views / name).is_file()]
    if not present:
        return None
    assert len(present) == len(GATE_MODULES), (
        "this bundle carries a PARTIAL contributed column — "
        f"{sorted(present)} and not {sorted(set(GATE_MODULES) - set(present))}. "
        "`openxdox.web_assets.install_view_modules` places every declared asset "
        "or refuses, so a partial set is an assembly that failed halfway and "
        "must not read as an install that never happened")
    return views


def test_the_carried_gate_exclusive_set_is_the_one_this_column_counts(
        composition: Composition) -> None:
    """The carried tuple is anchored to this column's own record of it.

    `GATE_EXCLUSIVE` is a copy, because the lone leg's copy lives in a test
    module that no wheel installs. A copy with nothing holding it is a second
    authority. So its size is held to `STYLE_RESIDUE["exclusive_classes"]`,
    the figure this column records for the same census, and it may carry no
    class twice.
    """
    counted = view_extensions.STYLE_RESIDUE["exclusive_classes"]
    assert len(set(GATE_EXCLUSIVE)) == len(GATE_EXCLUSIVE), (
        f"at {composition}: GATE_EXCLUSIVE names a class twice")
    assert len(GATE_EXCLUSIVE) == counted, (
        f"at {composition}: GATE_EXCLUSIVE carries {len(GATE_EXCLUSIVE)} "
        f"classes, and this column records {counted} gate-exclusive classes "
        "(`view_extensions.STYLE_RESIDUE`). One of the two has drifted from "
        "the census")


def test_the_gate_exclusive_set_is_re_derived_where_the_modules_are_present(
        composition: Composition, assembled_web: Path) -> None:
    """Where an assembly has placed the six modules, the declared set above is
    CHECKED against them rather than trusted: every class in `GATE_EXCLUSIVE` is
    named by at least one of the six, and none is named by openDox's own
    bundle.

    At the composition the six are placed on every run, so this asserts for
    real. It skipped in openDox-code's lone suite, where it was written.
    """
    views = _assembled_views(assembled_web)
    if views is None:
        pytest.fail(
            f"at {composition}: the assembly placed none of the six contributed "
            f"modules {list(GATE_MODULES)} in the bundle. At the declared "
            "composition that is a failed assembly, not an install to skip "
            "over", pytrace=False)
    # COMMENTS ARE BLANKED ON BOTH CORPORA (Copilot review, round 3). The
    # no-assembly path already did it; this one read them raw, so a class named
    # only in a comment counted as ownership on EITHER side — a gate-only
    # selector excused by openDox prose, or a contributed module credited with
    # a class it only documents. Same walk, same reason.
    gate_text = "\n".join(
        _blank_code_comments((views / name).read_text(encoding="utf-8"))
        for name in GATE_MODULES)
    own = [p for p in sorted(views.glob("*.js")) if p.name not in GATE_MODULES]
    own_text = "\n".join(_blank_code_comments(p.read_text(encoding="utf-8"))
                         for p in own)
    own_text += _blank_code_comments(
        (assembled_web / "app.js").read_text(encoding="utf-8"))
    own_text += _blank_code_comments(
        (assembled_web / "index.html").read_text(encoding="utf-8"), html=True)

    # THE SET IS DERIVED FROM THE MODULES AND THE STYLESHEET, not read off the
    # tuple (Copilot review, round 1). Checking only that every DECLARED token
    # is named by the six answers a question nobody asked: a gate-only class
    # this tuple forgot would be named by the six, left behind in `styles.css`,
    # and invisible to both halves of the old assertion. The derivation is the
    # census tool's own: every class token `styles.css` still declares in a
    # SELECTOR, classified by which side of the seam names it, with the
    # concatenation forms (`"disposebtn dispose-" + v.outcome`) counted by
    # PREFIX because no literal search can see a name never written down.
    def names(token: str, corpus: str) -> bool:
        if re.search(rf"(?<![A-Za-z0-9_-]){re.escape(token)}(?![A-Za-z0-9_-])",
                     corpus):
            return True
        return any(token.startswith(prefix) for prefix in
                   re.findall(r"[\"\'`\s]([A-Za-z_][A-Za-z0-9_-]*-)(?:[\"\'`]|\$\{)",
                              corpus))

    still_declared = _selector_classes(
        (assembled_web / "styles.css").read_text(encoding="utf-8"))
    derived_leftovers = sorted(
        token for token in still_declared
        if names(token, gate_text) and not names(token, own_text))
    assert derived_leftovers == [], (
        f"at {composition}: these classes are named by openXdox's six "
        "contributed modules and by no file of openDox's own bundle, yet "
        f"`styles.css` still declares a selector for them: {derived_leftovers}. "
        "RULED Q7 sends them to the binding's own sheet — and this set is "
        "DERIVED from the modules, so it catches a class `GATE_EXCLUSIVE` never "
        "heard of")

    # AND THE DECLARED SET IS STILL CHECKED AGAINST THE MODULES, because the
    # derivation above can only see what `styles.css` still declares: a token in
    # the tuple that no contributed module names would be a stale entry, and the
    # tuple is what this suite asserts against in a leg with no assembly.
    for token in GATE_EXCLUSIVE:
        assert names(token, gate_text), \
            f"at {composition}: {token} is named by none of the six contributed modules"
        assert not names(token, own_text), \
            f"at {composition}: {token} is named by openDox's own bundle and must not have left"


def test_no_sheet_in_the_assembled_bundle_declares_a_design_token(
        composition: Composition, assembled_web: Path) -> None:
    """A contributed sheet READS `var(--st-…)` and never WRITES one, measured
    over every sheet the ASSEMBLY placed.

    RULED Q7 makes the `--st-*` family openDox's one stable styling surface; a
    contributed sheet that declared one would be a second authority for it, and
    `views/display.js`'s `applyTokens` is already the first.

    This is the scan openDox-code's `test_no_contributed_sheet_declares_a_design_token`
    ran over an assembled bundle, and skipped where there was none. This leg's
    `tests/test_gate_loop_views.py` carries a case of that name over the sheets
    it DECLARES. This one reads what the assembly actually put in `views/`, at
    any depth.
    """
    views = assembled_web / "views"
    # RECURSIVE, because `_SHEET` admits a nested specifier (Copilot review,
    # round 2): `./views/gate/panel.css` is a lawful `styles` value, and a
    # direct-child glob would have let a sheet in a subdirectory declare an
    # `--st-*` token with this guard claiming to cover every contributed sheet.
    sheets = sorted(views.rglob("*.css"))
    # WHERE THE ASSEMBLY WRITES THEM (Copilot review of `f5efc756`):
    # `install_view_modules()` writes each sheet to `views/<name>`, so each is
    # looked for there, and not by name anywhere in the tree. A file of the
    # same name deeper down is not the sheet this assembly placed, and must not
    # stand in for it.
    missing = [name for name in web_assets.VIEW_SHEET_NAMES
               if not (views / name).is_file()]
    assert missing == [], (
        f"at {composition}: the assembled bundle lacks this column's sheets "
        f"{missing} at `views/<name>`, where `install_view_modules()` places "
        "them with the modules. A scan that found none would prove nothing")
    for sheet in sheets:
        css = _blank_css_comments(sheet.read_text(encoding="utf-8"))
        written = _declared_st_tokens(css)
        assert written == [], (
            f"at {composition}: {sheet.relative_to(views).as_posix()} "
            f"declares {written}")


def test_a_partial_assembly_is_a_failure_and_not_a_skip(
        composition: Composition, tmp_path: Path) -> None:
    """`_assembled_views()`'s own rule, driven (Copilot review, round 5)."""
    views = tmp_path / "views"
    views.mkdir()
    assert _assembled_views(tmp_path) is None   # none of the six: no assembly
    (views / GATE_MODULES[0]).write_text("// one\n", encoding="utf-8")
    with pytest.raises(AssertionError) as partial:
        _assembled_views(tmp_path)
    assert "PARTIAL" in str(partial.value), f"at {composition}: {partial.value}"
    for name in GATE_MODULES[1:]:
        (views / name).write_text("// placed\n", encoding="utf-8")
    assert _assembled_views(tmp_path) == views   # all six: an assembly
