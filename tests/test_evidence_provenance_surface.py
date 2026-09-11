"""Unit tests for `openxdox.evidence_provenance_surface` (`split-opendox-
two-layer-product` § 4.5, design § D4 machinery (4); RULED ASK-3, claimed at
`opensoft/openxFactory#656` comment `5632730583`).

Covers the PURE rendering logic (`project`, `_family`, `_member_binding`,
the three dataclasses' `as_json`) directly against declaration shapes
transcribed from the two RATIFIED fixtures
(`examples/derived-models/{medx-governed,ledgerx-calibrated}/
declaration.example.yaml`, `opensoft/openxFactory`) — this repository's to
RENDER, never to author — plus the HTTP handler mixin against a fake
request-handler double. No real `DashboardHandler` or live domain profile is
needed for either, for the same reason `test_role_authority_projection.py`
gives: task 4.3's composition point (wiring a contributed route, and a real
domain's declaration, into the live served app) is a separate, still-open
box, and this projection is fully testable on its own terms in the
meantime.
"""

from __future__ import annotations

import json

from openxdox.evidence_provenance_surface import (
    ASSUMPTION_REGISTER_FORM,
    ASSUMPTIONS_FORBIDDEN_FORM,
    EVIDENCE_ROUTE,
    EvidenceBinding,
    EvidenceFamily,
    EvidenceProvenanceRoutes,
    EvidenceProvenanceSurfaceExtension,
    project,
)

# ---------------------------------------------------------------------------
# Declarations transcribed verbatim from the ratified examples
# (opensoft/openxFactory examples/derived-models/*/declaration.example.yaml)
# ---------------------------------------------------------------------------

MEDX_GOVERNED_DECLARATION = {
    "schema_version": 1,
    "kind": "xfactory_derived_model_conformance",
    "conforms_to": "governed-derived-model",
    "domain": {"id": "medx"},
    "families": [
        {
            "id": "dream_simulation",
            "display_name": "Dream Object and Simulation Scenario",
            "tier": "governed",
            "members": [
                {
                    "role": "model",
                    "kind": "dream_object",
                    "template": "templates/dream-object.yaml",
                    "provenance": {
                        "form": "assumptions_forbidden",
                        "evidence_field": "source_trace",
                        "invented_facts_field": "invented_patient_facts",
                    },
                    "truth_store_access": {"gate": "cannot_write_patient_truth_model"},
                },
                {
                    "role": "scenario",
                    "kind": "simulation_scenario",
                    "template": "templates/simulation-scenario.yaml",
                    "truth_store_access": {"field": "truth_model_write_access",
                                            "value": "read_only"},
                    "action_authority": [{"gate": "cannot_create_orders"}],
                    "output_status_field": "output_status",
                },
            ],
            "dials": {
                "identity": "synthetic", "scope": "domain",
                "truth_store": "patient_truth_model",
                "truth_store_class": "hermes_memory",
                "promoting_authority": "clinician_of_record",
                "person_modeling": "synthetic_only",
            },
        },
    ],
}

LEDGERX_CALIBRATED_DECLARATION = {
    "schema_version": 1,
    "kind": "xfactory_derived_model_conformance",
    "conforms_to": "governed-derived-model",
    "domain": {"id": "ledgerx"},
    "families": [
        {
            "id": "counterparty_health",
            "display_name": "Counterparty Health Profile and Financial Scenario",
            "tier": "calibrated",
            "identity_subject_kind": "counterparty",
            "members": [
                {
                    "role": "model",
                    "kind": "counterparty_health_profile",
                    "template": "templates/counterparty-health-profile.yaml",
                    "provenance": {
                        "form": "assumption_register",
                        "evidence_field": "signals",
                        "assumption_register_field": "assumption_register",
                    },
                    "truth_store_access": {"field": "ledger_write_access",
                                            "value": "read_only"},
                },
                {
                    "role": "scenario",
                    "kind": "financial_scenario",
                    "template": "templates/financial-scenario.yaml",
                    "truth_store_access": {"field": "ledger_write_access",
                                            "value": "read_only"},
                    "action_authority": [{"field": "posting_authority",
                                           "value": "none"}],
                    "output_status_field": "output_status",
                },
            ],
            "dials": {
                "identity": "real_entity", "scope": "subject",
                "isolation_boundary": "per_client",
                "truth_store": "ledger",
                "truth_store_class": "external_enforcement",
                "calibration_writer": "close_readiness",
                "calibration_source": "close_cycle_actuals",
                "promoting_authority": "licensed_professional_of_record",
                "person_modeling": "identified_organizations_only",
            },
        },
    ],
}


# ---------------------------------------------------------------------------
# `project()` against the two ratified fixture shapes
# ---------------------------------------------------------------------------

def test_project_renders_the_medx_governed_assumptions_forbidden_form() -> None:
    view = project(MEDX_GOVERNED_DECLARATION)
    assert view.domain_id == "medx"
    assert len(view.families) == 1
    family = view.families[0]
    assert family.family_id == "dream_simulation"
    assert family.display_name == "Dream Object and Simulation Scenario"
    assert family.tier == "governed"
    # Only the ONE role:model member renders; the scenario member does not
    # (invariant 2 binds model objects; scenario members carry no
    # `provenance` block in the schema).
    assert len(family.members) == 1
    binding = family.members[0]
    assert binding.member_kind == "dream_object"
    assert binding.form == ASSUMPTIONS_FORBIDDEN_FORM
    assert binding.evidence_field == "source_trace"
    assert binding.invented_facts_field == "invented_patient_facts"
    assert binding.assumption_register_field is None


def test_project_renders_the_ledgerx_calibrated_assumption_register_form() -> None:
    view = project(LEDGERX_CALIBRATED_DECLARATION)
    assert view.domain_id == "ledgerx"
    family = view.families[0]
    assert family.tier == "calibrated"
    binding = family.members[0]
    assert binding.member_kind == "counterparty_health_profile"
    assert binding.form == ASSUMPTION_REGISTER_FORM
    assert binding.evidence_field == "signals"
    assert binding.assumption_register_field == "assumption_register"
    assert binding.invented_facts_field is None


def test_project_excludes_scenario_role_members() -> None:
    view = project(MEDX_GOVERNED_DECLARATION)
    kinds = [m.member_kind for m in view.families[0].members]
    assert "simulation_scenario" not in kinds


def test_project_renders_multiple_families_in_declaration_order() -> None:
    combined = {
        "domain": {"id": "medx"},
        "families": [
            MEDX_GOVERNED_DECLARATION["families"][0],
            {
                "id": "second_family",
                "tier": "governed",
                "members": [
                    {"role": "model", "kind": "x",
                     "provenance": {"form": "assumption_register",
                                    "evidence_field": "e",
                                    "assumption_register_field": "a"}},
                ],
            },
        ],
    }
    view = project(combined)
    assert len(view.families) == 2
    assert [f.family_id for f in view.families] == ["dream_simulation", "second_family"]


# ---------------------------------------------------------------------------
# Absent / malformed input — "no domain profile wired in yet"
# ---------------------------------------------------------------------------

def test_project_with_no_declaration_renders_an_empty_view() -> None:
    view = project()
    assert view.domain_id is None
    assert view.families == ()


def test_project_with_none_renders_an_empty_view() -> None:
    view = project(None)
    assert view.domain_id is None
    assert view.families == ()


def test_project_with_empty_mapping_renders_an_empty_view() -> None:
    view = project({})
    assert view.domain_id is None
    assert view.families == ()


def test_project_with_no_families_key_renders_an_empty_families_tuple() -> None:
    view = project({"domain": {"id": "medx"}})
    assert view.domain_id == "medx"
    assert view.families == ()


def test_project_renders_form_none_for_a_model_member_with_no_provenance_block() -> None:
    # An honest rendering of "nothing declared yet" — not this module's
    # place to flag as a defect (that is
    # scripts/validate-derived-models.py's job, never copied here).
    doc = {"families": [{"id": "f", "tier": "governed",
                          "members": [{"role": "model", "kind": "m"}]}]}
    view = project(doc)
    binding = view.families[0].members[0]
    assert binding.form is None
    assert binding.evidence_field is None
    assert binding.assumption_register_field is None
    assert binding.invented_facts_field is None


def test_project_renders_a_family_with_no_model_members_as_an_empty_tuple() -> None:
    doc = {"families": [{"id": "f", "tier": "governed",
                          "members": [{"role": "scenario", "kind": "s"}]}]}
    view = project(doc)
    assert view.families[0].members == ()


def test_project_handles_a_family_with_no_members_key() -> None:
    doc = {"families": [{"id": "f", "tier": "governed"}]}
    view = project(doc)
    assert view.families[0].members == ()


def test_project_reports_only_the_fields_present_regardless_of_form() -> None:
    # A malformed declaration (assumption_register form missing its own
    # register field) is rendered exactly as given, not corrected or
    # rejected — validity is scripts/validate-derived-models.py's question.
    doc = {"families": [{"id": "f", "tier": "governed", "members": [
        {"role": "model", "kind": "m",
         "provenance": {"form": "assumption_register", "evidence_field": "e"}},
    ]}]}
    binding = project(doc).families[0].members[0]
    assert binding.form == ASSUMPTION_REGISTER_FORM
    assert binding.evidence_field == "e"
    assert binding.assumption_register_field is None


# ---------------------------------------------------------------------------
# `as_json` — JSON-serializable, round trips
# ---------------------------------------------------------------------------

def test_evidence_binding_as_json_round_trips() -> None:
    binding = EvidenceBinding(family_id="f", member_kind="m",
                               form=ASSUMPTION_REGISTER_FORM,
                               evidence_field="e",
                               assumption_register_field="a",
                               invented_facts_field=None)
    encoded = json.loads(json.dumps(binding.as_json()))
    assert encoded == {
        "family_id": "f", "member_kind": "m", "form": "assumption_register",
        "evidence_field": "e", "assumption_register_field": "a",
        "invented_facts_field": None,
    }


def test_evidence_family_as_json_round_trips() -> None:
    family = EvidenceFamily(
        family_id="f", display_name="F", tier="governed",
        members=(EvidenceBinding("f", "m", None, None, None, None),))
    encoded = json.loads(json.dumps(family.as_json()))
    assert encoded["family_id"] == "f"
    assert encoded["display_name"] == "F"
    assert len(encoded["members"]) == 1


def test_full_view_as_json_is_fully_json_serializable() -> None:
    view = project(LEDGERX_CALIBRATED_DECLARATION)
    encoded = json.dumps(view.as_json())
    assert json.loads(encoded) == view.as_json()


# ---------------------------------------------------------------------------
# The route contribution
# ---------------------------------------------------------------------------

def test_extension_routes_returns_exactly_one_get_binding() -> None:
    bindings = EvidenceProvenanceSurfaceExtension().routes()
    assert len(bindings) == 1
    binding = bindings[0]
    assert binding.method == "GET"
    assert binding.pattern == EVIDENCE_ROUTE
    assert binding.is_prefix is False
    assert binding.handler == "_handle_evidence_provenance_surface"


class _FakeHandler(EvidenceProvenanceRoutes):
    """A minimal stand-in for `DashboardHandler` carrying only the one
    optional attribute the handler reaches through `self` — proves the
    mixin's own logic without needing the real served app."""

    def __init__(self, *, derived_model_conformance=None) -> None:
        if derived_model_conformance is not None:
            self.derived_model_conformance = derived_model_conformance
        self.sent: list[tuple[bytes, str, bool]] = []

    def _serve_bytes(self, body: bytes, content_type: str, head_only: bool) -> None:
        self.sent.append((body, content_type, head_only))


def test_handler_with_no_declaration_wired_renders_an_empty_view() -> None:
    fake = _FakeHandler()
    fake._handle_evidence_provenance_surface(head_only=False)
    assert len(fake.sent) == 1
    body, content_type, head_only = fake.sent[0]
    document = json.loads(body)
    assert document == {"domain_id": None, "families": []}
    assert content_type == "application/json; charset=utf-8"
    assert head_only is False


def test_handler_renders_a_wired_declaration() -> None:
    fake = _FakeHandler(derived_model_conformance=MEDX_GOVERNED_DECLARATION)
    fake._handle_evidence_provenance_surface(head_only=False)
    body, _ct, _ho = fake.sent[0]
    document = json.loads(body)
    assert document["domain_id"] == "medx"
    assert document["families"][0]["family_id"] == "dream_simulation"


def test_handler_passes_head_only_through() -> None:
    fake = _FakeHandler()
    fake._handle_evidence_provenance_surface(head_only=True)
    _body, _content_type, head_only = fake.sent[0]
    assert head_only is True
