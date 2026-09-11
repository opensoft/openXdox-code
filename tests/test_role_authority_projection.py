"""Unit tests for `openxdox.role_authority_projection` (`split-opendox-two-
layer-product` § 4.5, design § D4 machinery (6); RULED ASK-3).

Covers the PURE logic (`layers`, `project`, `_flatten_truthy_grants`, the two
dataclasses' `as_json`) directly, and the HTTP handler mixin against a fake
request-handler double — no real `DashboardHandler` is needed for either,
which is deliberate: task 4.3's composition point (wiring a contributed route
into the live served app) is a separate, still-open box, and this projection
is fully testable on its own terms in the meantime.
"""

from __future__ import annotations

import json

import pytest

from openxdox.role_authority_projection import (
    NEUTRAL_LAYERS,
    ROLE_AUTHORITY_ROUTE,
    AuthorityLayer,
    RoleAuthorityProjectionExtension,
    RoleAuthorityRoutes,
    SessionAuthorityView,
    _flatten_truthy_grants,
    layers,
    project,
)

# ---------------------------------------------------------------------------
# The neutral role table
# ---------------------------------------------------------------------------

def test_neutral_layers_are_the_six_hermes_level_roles_in_document_order() -> None:
    # Transcribed from docs/roles-and-authority.md's "Hermes-Level Roles"
    # table, in its own row order.
    role_ids = [role_id for role_id, _name, _decides in NEUTRAL_LAYERS]
    assert role_ids == ["PO", "PM", "CA", "PA", "Merge Council", "Merge Master"]


def test_neutral_layers_are_a_closed_six_row_table() -> None:
    assert len(NEUTRAL_LAYERS) == 6


def test_every_neutral_layer_has_a_non_empty_decides_summary() -> None:
    for role_id, role_name, decides in NEUTRAL_LAYERS:
        assert role_id, "role_id must not be empty"
        assert role_name, f"{role_id}: role_name must not be empty"
        assert decides, f"{role_id}: decides must not be empty"


def test_layers_with_no_domain_labels_renders_the_neutral_table_alone() -> None:
    result = layers()
    assert len(result) == 6
    for layer in result:
        assert isinstance(layer, AuthorityLayer)
        assert layer.domain_label is None


def test_layers_applies_domain_labels_by_role_id() -> None:
    # RULING C2: the neutral engine takes labels from a caller-supplied
    # mapping rather than guessing a domain's words — this is the injection
    # point, exercised with a stand-in mapping (not MedxFactory's real one,
    # which this repository must not hardcode).
    result = layers({"CA": "clinician of record", "PA": "licensed professional"})
    by_id = {layer.role_id: layer for layer in result}
    assert by_id["CA"].domain_label == "clinician of record"
    assert by_id["PA"].domain_label == "licensed professional"
    # Roles with no supplied label stay neutral.
    assert by_id["PO"].domain_label is None
    assert by_id["Merge Master"].domain_label is None


def test_layers_ignores_domain_labels_for_unknown_role_ids() -> None:
    # A mapping keyed on a role this table does not have must not raise or
    # silently invent a seventh row.
    result = layers({"nonexistent-role": "whatever"})
    assert len(result) == 6


def test_authority_layer_as_json_round_trips_through_json_dumps() -> None:
    layer = AuthorityLayer("CA", "Chief Architect", "how systems integrate",
                           "clinician of record")
    encoded = json.loads(json.dumps(layer.as_json()))
    assert encoded == {
        "role_id": "CA",
        "role_name": "Chief Architect",
        "decides": "how systems integrate",
        "domain_label": "clinician of record",
    }


# ---------------------------------------------------------------------------
# Capability-grant flattening
# ---------------------------------------------------------------------------

def test_flatten_truthy_grants_walks_nested_dicts() -> None:
    capabilities = {"actions": {"gate": True, "projection": False},
                    "top_level": True}
    assert _flatten_truthy_grants(capabilities) == (
        "actions.gate", "top_level",
    )


def test_flatten_truthy_grants_excludes_falsy_leaves() -> None:
    capabilities = {"actions": {"gate": False, "other": 0, "empty": ""}}
    assert _flatten_truthy_grants(capabilities) == ()


def test_flatten_truthy_grants_handles_none_and_empty() -> None:
    assert _flatten_truthy_grants(None) == ()
    assert _flatten_truthy_grants({}) == ()


def test_flatten_truthy_grants_is_sorted_regardless_of_input_order() -> None:
    first = _flatten_truthy_grants({"b": True, "a": True})
    second = _flatten_truthy_grants({"a": True, "b": True})
    assert first == second == ("a", "b")


def test_flatten_truthy_grants_deep_nesting() -> None:
    capabilities = {"a": {"b": {"c": {"d": True}}}}
    assert _flatten_truthy_grants(capabilities) == ("a.b.c.d",)


# ---------------------------------------------------------------------------
# `project()` — the pure projection builder
# ---------------------------------------------------------------------------

def test_project_with_resolved_actor_marks_console_token_present() -> None:
    view = project(actor="engineer-1", capabilities={}, loopback=True)
    assert view.console_token_present is True
    assert view.actor == "engineer-1"


@pytest.mark.parametrize("actor", [None, ""])
def test_project_with_no_actor_marks_console_token_absent(actor) -> None:
    view = project(actor=actor, capabilities={}, loopback=False)
    assert view.console_token_present is False
    assert view.actor is None


def test_project_coerces_loopback_to_bool() -> None:
    view = project(actor=None, capabilities={}, loopback=1)
    assert view.loopback is True
    assert isinstance(view.loopback, bool)


def test_project_flattens_capability_grants() -> None:
    view = project(actor=None, capabilities={"actions": {"gate": True}},
                   loopback=False)
    assert view.capability_grants == ("actions.gate",)


def test_project_threads_domain_labels_into_layers() -> None:
    view = project(actor=None, capabilities={}, loopback=False,
                   domain_labels={"CA": "clinician of record"})
    by_id = {layer.role_id: layer for layer in view.layers}
    assert by_id["CA"].domain_label == "clinician of record"


def test_project_returns_all_six_neutral_layers() -> None:
    view = project(actor=None, capabilities={}, loopback=False)
    assert len(view.layers) == 6


# ---------------------------------------------------------------------------
# `SessionAuthorityView.as_json` — the redaction rule
# ---------------------------------------------------------------------------

def test_as_json_reveals_actor_when_asked() -> None:
    view = SessionAuthorityView(console_token_present=True, loopback=True,
                                actor="engineer-1", capability_grants=(),
                                layers=())
    document = view.as_json(reveal_actor=True)
    assert document["actor"] == "engineer-1"


def test_as_json_redacts_actor_when_not_revealed() -> None:
    # "Belt and braces on the hosted plane" — the same redaction discipline
    # serve_projection._serve_index already applies off-loopback. The
    # console_token_present FACT still shows even when the actor identity is
    # redacted: they are two different questions.
    view = SessionAuthorityView(console_token_present=True, loopback=False,
                                actor="engineer-1", capability_grants=(),
                                layers=())
    document = view.as_json(reveal_actor=False)
    assert document["actor"] is None
    assert document["console_token_present"] is True


def test_as_json_reveal_actor_has_no_default() -> None:
    # A caller must consciously decide the redaction rule; there is no
    # accidental default that could leak an identity off-loopback.
    view = SessionAuthorityView(console_token_present=False, loopback=False,
                                actor=None, capability_grants=(), layers=())
    with pytest.raises(TypeError):
        view.as_json()  # type: ignore[call-arg]


def test_as_json_is_fully_json_serializable() -> None:
    view = project(actor="engineer-1",
                   capabilities={"actions": {"gate": True}}, loopback=True,
                   domain_labels={"CA": "clinician of record"})
    document = view.as_json(reveal_actor=True)
    # Must not raise — every value is a JSON-safe primitive.
    encoded = json.dumps(document)
    assert json.loads(encoded) == document


# ---------------------------------------------------------------------------
# The route contribution
# ---------------------------------------------------------------------------

def test_extension_routes_returns_exactly_one_get_binding() -> None:
    bindings = RoleAuthorityProjectionExtension().routes()
    assert len(bindings) == 1
    binding = bindings[0]
    assert binding.method == "GET"
    assert binding.pattern == ROLE_AUTHORITY_ROUTE
    assert binding.is_prefix is False
    assert binding.handler == "_handle_role_authority_projection"


class _FakeHandler(RoleAuthorityRoutes):
    """A minimal stand-in for `DashboardHandler` carrying only the
    primitives `_handle_role_authority_projection` reaches through `self` —
    proves the mixin's own logic without needing the real served app."""

    def __init__(self, *, loopback: bool, actor, capabilities) -> None:
        self.loopback = loopback
        self.actor = actor
        self.capabilities = capabilities
        self.sent: list[tuple[bytes, str, bool]] = []

    def _serve_bytes(self, body: bytes, content_type: str, head_only: bool) -> None:
        self.sent.append((body, content_type, head_only))


def test_handler_reveals_actor_on_loopback() -> None:
    fake = _FakeHandler(loopback=True, actor="engineer-1",
                        capabilities={"actions": {"gate": True}})
    fake._handle_role_authority_projection(head_only=False)
    assert len(fake.sent) == 1
    body, content_type, head_only = fake.sent[0]
    document = json.loads(body)
    assert document["actor"] == "engineer-1"
    assert document["loopback"] is True
    assert document["console_token_present"] is True
    assert content_type == "application/json; charset=utf-8"
    assert head_only is False


def test_handler_redacts_actor_off_loopback() -> None:
    fake = _FakeHandler(loopback=False, actor="engineer-1", capabilities={})
    fake._handle_role_authority_projection(head_only=False)
    body, _content_type, _head_only = fake.sent[0]
    document = json.loads(body)
    assert document["actor"] is None
    # The console-token FACT still surfaces even though the identity is
    # redacted — it is the diagnostic the workbench already shows.
    assert document["console_token_present"] is True


def test_handler_passes_head_only_through() -> None:
    fake = _FakeHandler(loopback=True, actor=None, capabilities={})
    fake._handle_role_authority_projection(head_only=True)
    _body, _content_type, head_only = fake.sent[0]
    assert head_only is True


def test_handler_always_renders_all_six_layers_regardless_of_loopback() -> None:
    fake = _FakeHandler(loopback=False, actor=None, capabilities={})
    fake._handle_role_authority_projection(head_only=False)
    body, _ct, _ho = fake.sent[0]
    document = json.loads(body)
    assert len(document["layers"]) == 6
