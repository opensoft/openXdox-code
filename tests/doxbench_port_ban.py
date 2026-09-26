"""The provider-verb ban on openDox's `WorkbenchModelPort`:
`FORBIDDEN_PORT_MEMBERS`, and nothing else.

A CREATED file: no row in openxFactory's `docs/opendox-carve-manifest.yaml`
(RULED OQ-C — the manifest declares what LEAVES openxFactory, never what a
destination assembles).

WHY IT EXISTS (plan 034 task T040). `test_doxbench_bridge.py` takes the ban with
`from test_doxbench_model import FORBIDDEN_PORT_MEMBERS`, inside two tests. The
module it names is openxFactory's `tests/ideation-dashboard/test_doxbench_model.py`,
whose manifest row is `not_moved` (`stays_openxfactory_adapter`), so both tests
failed on `No module named 'test_doxbench_model'` (T005's class D). This module
is the helper of their own that T040 gives them in its place.

WHAT IT CARRIES. The one name the bridge suite imports. The set is copied
unchanged from openxFactory at the carve tag `opendox-carve-0`
(`b075fd91dc8fced8e1373825ba80220c33536bae`), the tree the bridge suite was
carved from; openxFactory's `main` holds the same sixteen members today. The
comment above it comes with it, less one clause: the member set that `dispatch`
joined is named where it is pinned rather than as "below", since nothing is
below it here. openxFactory's own module is not brought whole, because at
`main` it imports a further openxFactory-only helper (`carved_reach`, in
openxFactory's `scripts/`) that the ban does not need.
"""

from __future__ import annotations

# PIN EVOLUTION (T049). `dispatch` LEFT this set and joined the port's declared
# member set (`WorkbenchModelPort.__protocol_attrs__`, which
# `test_doxbench_bridge.py` pins at three). Every other spelling STAYS banned,
# and the ban is what makes the widening narrow: the port gained exactly ONE
# named capability (hand an opaque prompt envelope to an adapter and get its
# answer back), not a family of provider verbs. `generate`/`complete`/`chat`/`send` would be second spellings
# of the same capability; `assemble_prompt`/`prompt` would move prompt assembly
# (doxbench_turns.py) behind the seam; `validate`/`validate_response` would move
# response validation out of `dispatch_turn`, which is exactly where T049 puts
# it; `credentials`/`api_key`/`endpoint`/`client` would make the port a carrier
# for the material FR-020/FR-022 forbid.
FORBIDDEN_PORT_MEMBERS = {
    "generate",
    "complete",
    "chat",
    "send",
    "assemble_prompt",
    "prompt",
    "validate",
    "validate_response",
    "render",
    "save",
    "ensemble",
    "review",
    "credentials",
    "api_key",
    "endpoint",
    "client",
}
