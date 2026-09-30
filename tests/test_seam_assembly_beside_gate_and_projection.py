"""The § 4.5 route contributions, assembled beside the gate and projection
columns: the six seam cases that need both, each asserting for real (plan 034
task T044, in openxFactory `specs/034-opendox-standalone-operation/`; box 9.4
of the ratified `add-neutral-product-standalone-operability`).

WHAT THESE ARE. Each of the three § 4.5 seam suites proves four things of its
extension, which `tests/test_role_authority_projection_seam.py`'s docstring
states first. The fourth, (d), is that the extension assembles cleanly beside
the OTHER existing contribution columns, in either declaration order. Two of
those columns are `serve_gate.GateRoutesExtension` and
`serve_projection.ProjectionRoutesExtension`, and until plan 034 T059
`serve_projection` reached openxFactory's `doc_health` when it was imported,
through `snapshot_registry`. So each suite imported the two behind a guard
that SKIPPED when `doc_health` was absent, saying "doc_health reachability is
BUILD-arc work (§ 3.5/3.6) ... this test will assert for real once that
lands". A lone checkout never has `doc_health`, so the six cases behind that
guard skipped on every run of this leg's required check until T044. 9.4 named
them: "every one of openXdox's six skips carries the same reason ... The
whole-product assertions are precisely the ones that skip".

WHAT T044 DID. It removed the guard, so each case asserts for real, and it
moved the six here. Each keeps its body and its comments, except that the
guard's call gives way to this module's own imports and a comment's "this
extension" now names the extension. Each name now leads with the extension it
assembles, since three of the six were all called
`test_assembly_is_order_insensitive`. The two columns are imported at module
level, beside the three § 4.5 extensions, because every case in this file
needs both. Where `doc_health` is present, as it is with openxFactory's
`scripts/` on `PYTHONPATH`, all six run and pass.

WHY IT WAS DECLARED, AND WHY IT IS NOT NOW. At T044 this module could not be
imported in a lone checkout: `serve_projection` imports `snapshot_registry`,
which read openxFactory's `doc_health` at module level. So
`tests/declared_exclusion.yaml` listed this file under `doc_health` (R1Q6 (d),
openxFactory#656 comment 5817152735), and the root `conftest.py` left it out
of every whole-suite run. Plan 034 T059 moved that read into the one method
that uses it (`SnapshotEntry.index_entry`), so openXdox's registry can be
registered at openDox's registry seam in a checkout without `doc_health`
(`openxdox.projection_contributions`). The module now imports in a lone
checkout, and all six cases pass there, so `tests/test_declared_exclusion.py`
turned red on this file's entry, as it is built to. The entry left the
declaration in T059, the pull request that cleared its reason, and the six
cases run in this leg's required check.

WHAT STAYS BEHIND. The 24 seam cases that need neither column stay in their
three suites, in the required check. They cover structural conformance, the
bindings alone, handler resolution, the prefix and distinctness checks,
dispatch through `match()`, and the § 4.5 siblings' assembly with each other.

A CREATED file: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import route_extension

from openxdox.evidence_provenance_surface import (
    EVIDENCE_ROUTE,
    EvidenceProvenanceSurfaceExtension,
)
from openxdox.model_scenario_workbench import (
    WORKBENCH_ROUTE,
    ModelScenarioWorkbenchExtension,
)
from openxdox.role_authority_projection import (
    ROLE_AUTHORITY_ROUTE,
    RoleAuthorityProjectionExtension,
)

# The two ALREADY-LANDED contribution columns every case below assembles
# beside. From T044 to T059 `serve_projection` reached `doc_health` when it
# was imported (through `snapshot_registry`), so in a lone checkout this
# module stopped at its import, on `doc_health` alone, and the declaration
# held it to that failure. Since T059 both import in a lone checkout, and
# this module runs in the required check. No guard turns a case into a skip.
from openxdox.serve_gate import GateRoutesExtension
from openxdox.serve_projection import ProjectionRoutesExtension


# ---------------------------------------------------------------------------
# § 4.5 slice 1: the role-and-authority projection, beside the two columns.
# Moved from `tests/test_role_authority_projection_seam.py`.
# ---------------------------------------------------------------------------

def test_role_authority_assembles_beside_the_two_existing_contribution_columns() -> None:
    # The real assembly, once task 4.3's composition point exists, combines
    # every § 2.4 contribution in one tuple. Proving that combination here —
    # ahead of that wiring — is what makes this a seam-conformance test and
    # not just a unit test of one class.
    extensions = [
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
        RoleAuthorityProjectionExtension(),
    ]
    bindings = route_extension.collect_bindings(extensions)
    # 1 (gate prefix) + 1 (snapshot-index exact) + 1 (the role-and-authority
    # projection's exact GET) = 3, and no RouteBindingError means none of the
    # three collide or nest.
    # WAS 5 UNTIL § 3.4 SLICE S6 (RULED Q4, `#656` comment `5642758731`):
    # `/source` (exact) and `/source/` (prefix) left this column with the
    # route, and are fixed core arms of `opendox/serve.py` now. The count is
    # the seam's own arithmetic, so it moves with the contribution.
    assert len(bindings) == 3
    assert ROLE_AUTHORITY_ROUTE in {b.pattern for b in bindings}


def test_role_authority_assembly_is_order_insensitive() -> None:
    # collect_bindings groups every exact binding ahead of every prefix one
    # regardless of declaration order (route_extension.py's own docstring) —
    # declaring the role-and-authority extension FIRST must assemble
    # identically.
    extensions = [
        RoleAuthorityProjectionExtension(),
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
    ]
    bindings = route_extension.collect_bindings(extensions)
    assert len(bindings) == 3


# ---------------------------------------------------------------------------
# § 4.5 slice 2: the evidence-and-provenance surface, beside all three.
# Moved from `tests/test_evidence_provenance_surface_seam.py`.
# ---------------------------------------------------------------------------

def test_evidence_surface_assembles_beside_all_three_existing_contribution_columns() -> None:
    # The real assembly, once task 4.3's composition point exists, combines
    # every § 2.4 contribution in one tuple. Proving that combination here —
    # ahead of that wiring — is what makes this a seam-conformance test and
    # not just a unit test of one class.
    extensions = [
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
        RoleAuthorityProjectionExtension(),
        EvidenceProvenanceSurfaceExtension(),
    ]
    bindings = route_extension.collect_bindings(extensions)
    # 1 (gate prefix) + 1 (projection: snapshot-index exact) + 1
    # (role-authority exact) + 1 (the evidence surface's exact GET) = 4, and
    # no RouteBindingError means none of the four collide or nest.
    # WAS 6 UNTIL § 3.4 SLICE S6 (RULED Q4, `#656` comment `5642758731`):
    # the projection's `/source` exact and `/source/` prefix bindings left
    # this column and are fixed core arms of `opendox/serve.py` now.
    assert len(bindings) == 4
    assert EVIDENCE_ROUTE in {b.pattern for b in bindings}


def test_evidence_surface_assembly_is_order_insensitive() -> None:
    # collect_bindings groups every exact binding ahead of every prefix one
    # regardless of declaration order (route_extension.py's own docstring) —
    # declaring the evidence extension FIRST must assemble identically.
    extensions = [
        EvidenceProvenanceSurfaceExtension(),
        RoleAuthorityProjectionExtension(),
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
    ]
    bindings = route_extension.collect_bindings(extensions)
    assert len(bindings) == 4


# ---------------------------------------------------------------------------
# § 4.5 slice 3: the model/scenario workbench, beside all four. With it the
# assembly is complete for § 4.5, and the five-column case below is the first
# test anywhere that proves all of the columns fit together.
# Moved from `tests/test_model_scenario_workbench_seam.py`.
# ---------------------------------------------------------------------------

def test_workbench_assembles_beside_all_four_existing_contribution_columns() -> None:
    # The real assembly, once task 4.3's composition point exists, combines
    # every § 2.4 contribution in one tuple. Proving that combination here —
    # ahead of that wiring — is what makes this a seam-conformance test and
    # not just a unit test of one class.
    extensions = [
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
        RoleAuthorityProjectionExtension(),
        EvidenceProvenanceSurfaceExtension(),
        ModelScenarioWorkbenchExtension(),
    ]
    bindings = route_extension.collect_bindings(extensions)
    # 1 (gate prefix) + 1 (projection: snapshot-index exact) + 1
    # (role-authority exact) + 1 (evidence exact) + 1 (the bench's exact
    # GET) = 5, and no RouteBindingError means none of the five collide or
    # nest.
    # WAS 7 UNTIL § 3.4 SLICE S6 (RULED Q4, `#656` comment `5642758731`):
    # the projection's `/source` exact and `/source/` prefix bindings left
    # this column and are fixed core arms of `opendox/serve.py` now.
    assert len(bindings) == 5
    assert WORKBENCH_ROUTE in {b.pattern for b in bindings}


def test_workbench_assembly_is_order_insensitive() -> None:
    # collect_bindings groups every exact binding ahead of every prefix one
    # regardless of declaration order (route_extension.py's own docstring) —
    # declaring the workbench extension FIRST must assemble identically, and
    # the RESULTING SET must be identical too, not merely the same size.
    declared_last = [
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
        RoleAuthorityProjectionExtension(),
        EvidenceProvenanceSurfaceExtension(),
        ModelScenarioWorkbenchExtension(),
    ]
    declared_first = [
        ModelScenarioWorkbenchExtension(),
        EvidenceProvenanceSurfaceExtension(),
        RoleAuthorityProjectionExtension(),
        GateRoutesExtension(),
        ProjectionRoutesExtension(),
    ]
    last = route_extension.collect_bindings(declared_last)
    first = route_extension.collect_bindings(declared_first)
    assert len(first) == len(last) == 5
    assert {b.key for b in first} == {b.key for b in last}
