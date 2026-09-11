"""Unit tests for `openxdox.model_scenario_workbench`
(`split-opendox-two-layer-product` § 4.5, design § D4 machinery (5); RULED
ASK-3, claimed at `opensoft/openxFactory#656` comment `5633537301`).

Covers the PURE rendering logic (`project`, `_station`, `_member`,
`_access_binding`, the four dataclasses' `as_json`) directly against
declaration shapes transcribed from the two RATIFIED fixtures
(`examples/derived-models/{medx-governed,ledgerx-calibrated}/
declaration.example.yaml`, `opensoft/openxFactory`) — this repository's to
RENDER, never to author — plus the HTTP handler mixin against a fake
request-handler double. No real `DashboardHandler` or live domain profile is
needed for either, for the reason both landed § 4.5 slices give: task 4.3's
composition point (wiring a contributed route, and a real domain's
declaration, into the live served app) is a separate, still-open box, and
this bench is fully testable on its own terms in the meantime.

THE TWO FIXTURES ARE NOT INTERCHANGEABLE and are both exercised throughout,
because between them they cover every branch D4 machinery (5) names:
`medx-governed` is a `governed`, `scope: domain` family whose truth-store
protection is a GATE and which declares no isolation boundary;
`ledgerx-calibrated` is a `calibrated`, `scope: subject` family whose
protection is a single-value FIELD LOCK and which therefore does declare one
(`per_client`). A suite proving only one of the two would prove half of the
either/or the schema describes.
"""

from __future__ import annotations

import dataclasses
import json

from openxdox.model_scenario_workbench import (
    HYPOTHESIS_OUTPUT_STATUSES,
    MODEL_ROLE,
    SCENARIO_ROLE,
    WORKBENCH_ROUTE,
    AccessBinding,
    BenchMember,
    BenchStation,
    ModelScenarioWorkbenchExtension,
    ModelScenarioWorkbenchRoutes,
    WorkbenchView,
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
                    "truth_store_access": {
                        "gate": "cannot_write_patient_truth_model",
                    },
                },
                {
                    "role": "scenario",
                    "kind": "simulation_scenario",
                    "template": "templates/simulation-scenario.yaml",
                    "truth_store_access": {
                        "field": "truth_model_write_access",
                        "value": "read_only",
                    },
                    "action_authority": [{"gate": "cannot_create_orders"}],
                    "output_status_field": "output_status",
                },
            ],
            "dials": {
                "identity": "synthetic",
                "scope": "domain",
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
                    "truth_store_access": {
                        "field": "ledger_write_access",
                        "value": "read_only",
                    },
                },
                {
                    "role": "scenario",
                    "kind": "financial_scenario",
                    "template": "templates/financial-scenario.yaml",
                    "truth_store_access": {
                        "field": "ledger_write_access",
                        "value": "read_only",
                    },
                    "action_authority": [
                        {"field": "posting_authority", "value": "none"},
                    ],
                    "output_status_field": "output_status",
                },
            ],
            "dials": {
                "identity": "real_entity",
                "scope": "subject",
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
# The contract enum this bench renders
# ---------------------------------------------------------------------------


def test_hypothesis_output_statuses_are_exactly_the_ratified_three() -> None:
    # `governed-derived-model`'s "Human-gated promotion" requirement: outputs
    # expressible ONLY as `hypothesis_proposed | no_signal | discarded`. The
    # ORDER is the requirement's own; a fourth value here would be a silent
    # divergence from a ratified contract this module only renders.
    assert HYPOTHESIS_OUTPUT_STATUSES == (
        "hypothesis_proposed", "no_signal", "discarded")


def test_the_two_member_roles_match_the_schema_enum() -> None:
    assert (MODEL_ROLE, SCENARIO_ROLE) == ("model", "scenario")


# ---------------------------------------------------------------------------
# project() over the ratified declarations
# ---------------------------------------------------------------------------


def test_medx_station_renders_the_five_named_elements() -> None:
    view = project(MEDX_GOVERNED_DECLARATION)
    assert view.domain_id == "medx"
    assert len(view.stations) == 1
    station = view.stations[0]
    assert station.family_id == "dream_simulation"
    assert station.display_name == "Dream Object and Simulation Scenario"
    assert station.tier == "governed"
    # (2) declared scope — this family is domain-scoped, so no isolation
    # boundary is declared and None is the correct rendering, not a gap.
    assert station.scope == "domain"
    assert station.isolation_boundary is None
    # (3) the truth store the model may never write, with its class.
    assert station.truth_store == "patient_truth_model"
    assert station.truth_store_class == "hermes_memory"
    # (5) the named human promoting authority.
    assert station.promoting_authority == "clinician_of_record"
    # (1) one model member and one optional scenario member, separated.
    assert len(station.model_members) == 1
    assert len(station.scenario_members) == 1
    assert station.model_members[0].kind == "dream_object"
    assert station.scenario_members[0].kind == "simulation_scenario"


def test_medx_model_member_truth_store_access_is_the_gate_form() -> None:
    # The schema allows EITHER a single-value field lock OR a declared gate;
    # medx's model member uses the gate form and must render as declared,
    # not normalized into a field/value pair this declaration never wrote.
    member = project(MEDX_GOVERNED_DECLARATION).stations[0].model_members[0]
    assert member.truth_store_access == AccessBinding(
        field=None, value=None, gate="cannot_write_patient_truth_model")
    assert member.template == "templates/dream-object.yaml"
    # Provenance is machinery (4)'s and is NOT re-rendered here.
    assert not hasattr(member, "provenance")


def test_medx_scenario_member_carries_output_field_and_action_authority() -> None:
    scenario = project(MEDX_GOVERNED_DECLARATION).stations[0].scenario_members[0]
    assert scenario.output_status_field == "output_status"
    assert scenario.truth_store_access == AccessBinding(
        field="truth_model_write_access", value="read_only", gate=None)
    assert scenario.action_authority == (
        AccessBinding(field=None, value=None, gate="cannot_create_orders"),)


def test_ledgerx_station_renders_the_subject_scope_isolation_pair() -> None:
    view = project(LEDGERX_CALIBRATED_DECLARATION)
    assert view.domain_id == "ledgerx"
    station = view.stations[0]
    assert station.tier == "calibrated"
    # "Declared scope and cross-scope review": scope: subject NAMES the
    # isolation boundary. The bench renders the pair, never one alone.
    assert station.scope == "subject"
    assert station.isolation_boundary == "per_client"
    assert station.truth_store == "ledger"
    assert station.truth_store_class == "external_enforcement"
    assert station.promoting_authority == "licensed_professional_of_record"


def test_ledgerx_members_use_the_field_lock_form_of_both_bindings() -> None:
    station = project(LEDGERX_CALIBRATED_DECLARATION).stations[0]
    model = station.model_members[0]
    scenario = station.scenario_members[0]
    assert model.truth_store_access == AccessBinding(
        field="ledger_write_access", value="read_only", gate=None)
    assert scenario.action_authority == (
        AccessBinding(field="posting_authority", value="none", gate=None),)


def test_dials_this_machinery_does_not_name_are_not_rendered() -> None:
    # identity / person_modeling / calibration_* are declared in the SAME
    # document and are deliberately absent from the station: D4 machinery
    # (5) does not name them, and rendering them here would make this bench
    # a second, partial copy of the whole declaration.
    station_json = project(LEDGERX_CALIBRATED_DECLARATION).stations[0].as_json()
    for absent in ("identity", "person_modeling", "calibration_writer",
                   "calibration_source", "identity_subject_kind"):
        assert absent not in station_json


# ---------------------------------------------------------------------------
# The optionality of the scenario member, and other honest-None cases
# ---------------------------------------------------------------------------


def test_model_only_family_renders_an_empty_scenario_tuple() -> None:
    # "the declaration is valid and scenario invariants are not required"
    # (governed-derived-model, "model-only family" scenario). A model-only
    # family is VALID, so the bench renders it as a station with no scenario
    # members rather than flagging or dropping it.
    declaration = {
        "domain": {"id": "adx"},
        "families": [
            {
                "id": "persona_campaign",
                "tier": "calibrated",
                "members": [{"role": "model", "kind": "persona",
                             "template": "templates/persona.yaml"}],
                "dials": {"scope": "subject", "isolation_boundary": "per_advertiser",
                          "truth_store": "brand_truth",
                          "promoting_authority": "launch_and_spend_approver"},
            },
        ],
    }
    station = project(declaration).stations[0]
    assert len(station.model_members) == 1
    assert station.scenario_members == ()
    assert station.model_members[0].output_status_field is None
    assert station.model_members[0].truth_store_access is None
    assert station.model_members[0].action_authority == ()


def test_none_declaration_renders_an_empty_bench_carrying_the_enum() -> None:
    view = project(None)
    assert view.domain_id is None
    assert view.stations == ()
    # The enum is a property of the CONTRACT, not of any declaration, so it
    # is present even with no domain profile wired in.
    assert view.hypothesis_output_statuses == HYPOTHESIS_OUTPUT_STATUSES


def test_empty_and_familyless_declarations_render_the_same_empty_bench() -> None:
    assert project({}).as_json() == project(None).as_json()
    assert project({"domain": {"id": "medx"}}).stations == ()
    assert project({"families": []}).as_json() == project(None).as_json()


def test_a_family_with_no_dials_block_renders_all_dials_none() -> None:
    station = project({"families": [{"id": "bare", "members": []}]}).stations[0]
    assert (station.scope, station.isolation_boundary, station.truth_store,
            station.truth_store_class, station.promoting_authority) == (
                None, None, None, None, None)
    assert station.model_members == () and station.scenario_members == ()


def test_a_member_whose_role_is_outside_the_enum_lands_in_neither_tuple() -> None:
    # The schema's role enum admits exactly two values. Inventing a third
    # bucket for an out-of-enum value would be this module ruling on a
    # declaration it explicitly does not validate.
    station = project({
        "families": [{"id": "f", "members": [
            {"role": "calibration_writer", "kind": "close_readiness"},
            {"role": "model", "kind": "m"},
        ]}],
    }).stations[0]
    assert [m.kind for m in station.model_members] == ["m"]
    assert station.scenario_members == ()


def test_non_mapping_shapes_render_rather_than_raise() -> None:
    # This module reads a document it did not write and does not own the
    # judgment that a malformed declaration is malformed — the canonical
    # validator does. So an illegible sub-shape renders as "nothing legible
    # declared" without taking the rest of the bench down with it.
    view = project({
        "domain": "medx",                      # not a mapping
        "families": [
            "not-a-family",                    # not a mapping
            {"id": "f", "dials": ["nope"],     # not a mapping
             "members": [
                 "not-a-member",               # not a mapping
                 {"role": "model", "kind": "m",
                  "truth_store_access": "read_only",   # not a mapping
                  "action_authority": ["nope", {"gate": "g"}]},
             ]},
        ],
    })
    assert view.domain_id is None
    assert len(view.stations) == 1
    member = view.stations[0].model_members[0]
    assert member.truth_store_access is None
    assert member.action_authority == (AccessBinding(gate="g"),)


def test_declaration_order_of_families_and_members_is_preserved() -> None:
    declaration = {
        "families": [
            {"id": "second_declared", "members": []},
            {"id": "first_declared", "members": [
                {"role": "model", "kind": "b"},
                {"role": "model", "kind": "a"},
            ]},
        ],
    }
    view = project(declaration)
    assert [s.family_id for s in view.stations] == [
        "second_declared", "first_declared"]
    assert [m.kind for m in view.stations[1].model_members] == ["b", "a"]


# ---------------------------------------------------------------------------
# as_json()
# ---------------------------------------------------------------------------


def test_as_json_is_json_serializable_and_shaped_as_declared() -> None:
    document = project(MEDX_GOVERNED_DECLARATION).as_json()
    round_tripped = json.loads(json.dumps(document))
    assert round_tripped == document
    assert round_tripped["domain_id"] == "medx"
    assert round_tripped["hypothesis_output_statuses"] == [
        "hypothesis_proposed", "no_signal", "discarded"]
    station = round_tripped["stations"][0]
    assert set(station) == {
        "family_id", "display_name", "tier", "scope", "isolation_boundary",
        "truth_store", "truth_store_class", "promoting_authority",
        "model_members", "scenario_members"}
    member = station["scenario_members"][0]
    assert set(member) == {
        "role", "kind", "template", "truth_store_access", "action_authority",
        "output_status_field"}
    assert member["truth_store_access"] == {
        "field": "truth_model_write_access", "value": "read_only", "gate": None}


def test_as_json_renders_a_missing_truth_store_access_as_null() -> None:
    member = BenchMember(role="model", kind="m", template=None,
                         truth_store_access=None, action_authority=(),
                         output_status_field=None)
    assert member.as_json()["truth_store_access"] is None
    assert member.as_json()["action_authority"] == []


def test_empty_view_as_json() -> None:
    assert project(None).as_json() == {
        "domain_id": None,
        "hypothesis_output_statuses": [
            "hypothesis_proposed", "no_signal", "discarded"],
        "stations": [],
    }


def test_the_dataclasses_are_frozen() -> None:
    # Declared once from a document and read many times: a station a caller
    # could mutate after rendering is a projection that can disagree with
    # the declaration it projects.
    for cls in (AccessBinding, BenchMember, BenchStation, WorkbenchView):
        assert dataclasses.fields(cls) is not None
        assert cls.__dataclass_params__.frozen is True


# ---------------------------------------------------------------------------
# The HTTP door
# ---------------------------------------------------------------------------


class _FakeHandler(ModelScenarioWorkbenchRoutes):
    """A minimal stand-in for `DashboardHandler` carrying only the one
    optional attribute the handler reaches through `self` — proves the
    mixin's own logic without needing the real served app."""

    def __init__(self, *, derived_model_conformance=None) -> None:
        if derived_model_conformance is not None:
            self.derived_model_conformance = derived_model_conformance
        self.sent: list[tuple[bytes, str, bool]] = []

    def _serve_bytes(self, body: bytes, content_type: str, head_only: bool) -> None:
        self.sent.append((body, content_type, head_only))


def test_handler_with_no_declaration_wired_renders_an_empty_bench() -> None:
    fake = _FakeHandler()
    fake._handle_model_scenario_workbench(head_only=False)
    assert len(fake.sent) == 1
    body, content_type, head_only = fake.sent[0]
    assert json.loads(body) == project(None).as_json()
    assert content_type == "application/json; charset=utf-8"
    assert head_only is False


def test_handler_renders_a_wired_declaration() -> None:
    fake = _FakeHandler(derived_model_conformance=LEDGERX_CALIBRATED_DECLARATION)
    fake._handle_model_scenario_workbench(head_only=False)
    body, _ct, _ho = fake.sent[0]
    document = json.loads(body)
    assert document["domain_id"] == "ledgerx"
    assert document["stations"][0]["isolation_boundary"] == "per_client"


def test_handler_passes_head_only_through() -> None:
    fake = _FakeHandler()
    fake._handle_model_scenario_workbench(head_only=True)
    _body, _content_type, head_only = fake.sent[0]
    assert head_only is True


def test_extension_declares_exactly_one_binding_for_the_workbench_route() -> None:
    bindings = ModelScenarioWorkbenchExtension().routes()
    assert len(bindings) == 1
    binding = bindings[0]
    assert (binding.method, binding.pattern, binding.is_prefix) == (
        "GET", WORKBENCH_ROUTE, False)
    assert binding.handler == "_handle_model_scenario_workbench"
    assert WORKBENCH_ROUTE == "/projections/workbench"
