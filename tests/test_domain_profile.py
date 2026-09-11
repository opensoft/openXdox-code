"""The domain profile: its loader, its refusals, and its ONE registration.

§ 4.4 of `split-opendox-two-layer-product` (RULING C2; ASK-4 RULED on
`openxFactory#656` comment `5634195861`). The engine sites that read this object
are guarded separately by `test_no_hardcoded_status_words.py`; this suite is
about the object itself.

It imports `openxdox.domain_profile` and NOTHING else of this package, because
that module's whole promise is that it stands alone: `yaml` and the standard
library, no engine import, no consumer import, and no side effect at import
time.

A CREATED FILE: no manifest row (RULED OQ-C).
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from openxdox import domain_profile as dp

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "openxfactory-engineering-profile.yaml"


@pytest.fixture()
def raw() -> dict:
    """The fixture profile as a mutable mapping, so a test can break ONE field."""
    return yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture()
def profile() -> dp.DomainProfile:
    return dp.load(FIXTURE)


@pytest.fixture()
def unregistered_profile():
    """Run one test with NO domain profile registered, then restore it.

    Declared HERE and not in `tests/conftest.py` deliberately: this module runs
    under `validate`'s `--noconftest` invocation, beside the other shape
    assertions, so it may not depend on a conftest being collected. Restoring
    whatever was registered means a run that DID come through the root
    `conftest.py` — the host's process-start registration — is left exactly as
    it was found.
    """
    previous = dp.current() if dp.is_registered() else None
    dp.unregister()
    try:
        yield
    finally:
        dp.unregister()
        if previous is not None:
            dp.register(previous)


# --------------------------------------------------------------- the loader


def test_the_canonical_yaml_loads_into_the_runtime_form(profile):
    """ASK-4 Q1: the YAML is canonical, the dataclass is the runtime form."""
    assert isinstance(profile, dp.DomainProfile)
    assert profile.mapping_id == "openxfactory-engineering"
    assert profile.neutral is False
    assert profile.declared_by == "opensoft/openxFactory"
    assert profile.source == str(FIXTURE)


def test_a_mapping_loads_as_well_as_a_path(raw):
    """A host that reads its own configuration hands `load()` the mapping."""
    assert dp.load(raw).mapping_id == dp.load(FIXTURE).mapping_id


@pytest.mark.parametrize("field", dp.REQUIRED_TOP_LEVEL)
def test_every_required_top_level_field_is_refused_by_name(raw, field):
    """The five axes plus the truth store; none of them is optional."""
    del raw[field]
    with pytest.raises(dp.DomainProfileInvalid) as exc:
        dp.load(raw)
    assert field in str(exc.value)


def test_a_profile_claiming_to_be_neutral_is_refused(raw):
    raw["neutral"] = True
    with pytest.raises(dp.DomainProfileInvalid, match="neutral"):
        dp.load(raw)


def test_a_later_schema_version_is_refused_rather_than_guessed(raw):
    raw["schema_version"] = 2
    with pytest.raises(dp.DomainProfileInvalid, match="schema_version"):
        dp.load(raw)


def test_unrecognized_fields_are_tolerated(raw):
    """Forward tolerance: a later revision of the openXdox-spec schema loads.

    The schema lives at openXdox-spec (RULED ASK-4 Q2) and is not vendored here,
    so the engine refuses on what it MISSES and never on what it does not yet
    know about — otherwise every additive schema revision would break the engine
    before anyone had asked it to read the new field.
    """
    raw["some_axis_this_engine_has_not_met"] = {"a": 1}
    loaded = dp.load(raw)
    assert loaded.extra["some_axis_this_engine_has_not_met"] == {"a": 1}


def test_an_immutability_point_outside_its_own_vocabulary_is_refused(raw):
    raw["lifecycle"][0]["immutability_point"]["status"] = "not-a-status"
    with pytest.raises(dp.DomainProfileInvalid, match="not-a-status"):
        dp.load(raw)


def test_a_missing_immutability_point_is_refused_not_defaulted(raw):
    """`domain-mapping-declaration`'s second refusal, encoded.

    "A vocabulary with no declared immutability point SHALL be refused rather
    than defaulted to 'never'" — the permissive answer is unavailable here.
    """
    del raw["lifecycle"][0]["immutability_point"]
    with pytest.raises(dp.DomainProfileInvalid, match="immutability_point"):
        dp.load(raw)


def test_a_transition_without_an_authority_is_refused_not_defaulted(raw):
    """The first refusal: never defaulted to "any actor"."""
    del raw["lifecycle"][0]["transitions"][0]["authority"]
    with pytest.raises(dp.DomainProfileInvalid, match="authority"):
        dp.load(raw)


def test_a_transition_end_outside_the_vocabulary_is_refused(raw):
    raw["lifecycle"][0]["transitions"][0]["to"] = "nowhere"
    with pytest.raises(dp.DomainProfileInvalid, match="nowhere"):
        dp.load(raw)


def test_a_terminal_status_outside_the_vocabulary_is_refused(raw):
    raw["lifecycle"][0]["terminal_statuses"] = ["invented"]
    with pytest.raises(dp.DomainProfileInvalid, match="invented"):
        dp.load(raw)


def test_a_status_without_a_neutral_role_is_refused(raw):
    del raw["lifecycle"][0]["vocabulary"][0]["role"]
    with pytest.raises(dp.DomainProfileInvalid, match="role"):
        dp.load(raw)


def test_a_role_outside_the_neutral_vocabulary_is_refused(raw):
    """The role list is the AXIS the engine shares with every descendant.

    A profile inventing a role would be a word the engine cannot ask for, which
    is the same failure as a hardcoded status by another route.
    """
    raw["lifecycle"][0]["vocabulary"][0]["role"] = "vibes"
    with pytest.raises(dp.DomainProfileInvalid, match="vibes"):
        dp.load(raw)


def test_a_lifecycle_for_an_undeclared_artifact_kind_is_refused(raw):
    raw["lifecycle"][0]["artifact_kind"] = "ghost-kind"
    with pytest.raises(dp.DomainProfileInvalid, match="ghost-kind"):
        dp.load(raw)


def test_a_duplicate_status_id_within_one_kind_is_refused(raw):
    vocab = raw["lifecycle"][0]["vocabulary"]
    vocab.append(copy.deepcopy(vocab[0]))
    with pytest.raises(dp.DomainProfileInvalid, match="more than once"):
        dp.load(raw)


def test_a_profile_that_is_not_yaml_is_refused_naming_the_file(tmp_path):
    bad = tmp_path / "profile.yaml"
    bad.write_text("kind: [unclosed\n", encoding="utf-8")
    with pytest.raises(dp.DomainProfileInvalid, match="not valid YAML"):
        dp.load(bad)


def test_a_profile_that_is_not_there_is_refused_naming_the_path(tmp_path):
    with pytest.raises(dp.DomainProfileInvalid, match="could not be read"):
        dp.load(tmp_path / "absent.yaml")


# ----------------------------------------------- the out-of-band, never-frozen


def test_an_out_of_band_non_immutable_status_loads(profile):
    """The ninth word of the taxonomy — `projection` (retraction 5633989351).

    "Never authoritative, never hand-edited, and not immutable — regenerating it
    is the correct act, not a violation." It loads, it carries the out-of-band
    role, and it changes nothing about the kinds that DO freeze.
    """
    governance = profile.lifecycle_for("governance-document")
    words = governance.status_ids()
    assert len(words) == 9 and "projection" in words
    assert [s.role for s in governance.vocabulary if s.id == "projection"] == ["out-of-band"]


def test_a_kind_that_never_freezes_says_so_in_the_required_field(profile):
    point = profile.immutability_point("projection")
    assert point.addenda == dp.NEVER_FREEZES and point.never_freezes
    assert point.note, "a never-freezing kind must record WHY"
    assert profile.is_immutable("projection", "projection") is False


def test_the_immutability_point_still_binds_every_kind_that_does_freeze(profile):
    """The exemption is a DECLARED value, so nothing about the refusal weakens."""
    assert profile.is_immutable("governance-document", "ratified") is True
    assert profile.is_immutable("governance-document", "draft") is False
    assert profile.immutability_point("evidence-record").addenda == "separate-document"
    assert profile.is_immutable("evidence-record", "record") is True


def test_regenerated_without_its_reason_is_refused(raw):
    """`regenerated` is the one answer that must also say why."""
    point = raw["lifecycle"][0]["immutability_point"]
    point["addenda"] = "regenerated"
    point.pop("note", None)
    with pytest.raises(dp.DomainProfileInvalid, match="never freezes"):
        dp.load(raw)


def test_an_unknown_addenda_value_is_refused(raw):
    raw["lifecycle"][0]["immutability_point"]["addenda"] = "just-edit-it"
    with pytest.raises(dp.DomainProfileInvalid, match="just-edit-it"):
        dp.load(raw)


# ------------------------------------------------------------- the accessors


def test_a_status_is_asked_for_by_ROLE_not_by_word(profile):
    """The whole point of § 4.4: `MedxDox` needs no engine change."""
    kind = profile.kind_declaring("demote")
    assert profile.status("organized", kind=kind) == "staged"
    assert profile.status("proposed", kind=kind) == "draft"


def test_a_renamed_word_changes_nothing_the_engine_asks_for(raw):
    """A descendant spelling its organized status `triaged` still resolves."""
    for entry in raw["lifecycle"]:
        for status in entry["vocabulary"]:
            if status["id"] == "staged":
                status["id"] = "triaged"
        for transition in entry["transitions"]:
            for end in ("from", "to"):
                if transition.get(end) == "staged":
                    transition[end] = "triaged"
        entry["terminal_statuses"] = [
            "triaged" if w == "staged" else w for w in entry.get("terminal_statuses", [])]
        if entry["immutability_point"]["status"] == "staged":
            entry["immutability_point"]["status"] = "triaged"
    renamed = dp.load(raw)
    kind = renamed.kind_declaring("demote")
    assert renamed.status("organized", kind=kind) == "triaged"
    assert renamed.destination_status("demote") == "triaged"


def test_an_ambiguous_role_is_refused_naming_both_candidates(profile):
    """Never resolved by declaration order.

    `proposed` is `draft` for the document spine and `picked` for the possibles
    register, which is a real disagreement and is answered with a refusal.
    """
    with pytest.raises(dp.ProfileLookupError) as exc:
        profile.status("proposed")
    assert "draft" in str(exc.value) and "picked" in str(exc.value)


def test_a_role_no_vocabulary_carries_is_refused(profile):
    with pytest.raises(dp.ProfileLookupError, match="attested"):
        profile.status("attested", kind="governance-document")


def test_terminal_statuses_are_per_kind(profile):
    """RULED ASK-4 Q4 — the two vocabularies stay apart."""
    assert profile.terminal_statuses("governance-document") == ("superseded", "retired")
    assert profile.terminal_statuses("register-possible") == ("rejected", "superseded")


def test_a_kind_is_named_through_the_act_that_operates_on_it(profile):
    """How the engine avoids writing a domain's KIND name down, too."""
    assert profile.kind_declaring("demote") == "governance-document"
    assert profile.kind_declaring("promote-to-staging") == "register-possible"


def test_the_demote_destination_is_the_status_the_transition_lands_on(profile):
    assert profile.destination_status("demote") == "staged"
    assert profile.destination_kind("demote") == "staging-topic"


def test_transitions_that_disagree_are_refused_rather_than_picked_between(raw):
    for entry in raw["lifecycle"]:
        for transition in entry["transitions"]:
            if transition.get("act") == "demote":
                transition["to"] = "retired"
                break
        else:
            continue
        break
    with pytest.raises(dp.ProfileLookupError, match="disagree"):
        dp.load(raw).destination_status("demote")


def test_an_act_no_transition_declares_is_refused(profile):
    with pytest.raises(dp.ProfileLookupError, match="attest"):
        profile.destination_status("attest")


def test_an_unknown_artifact_kind_is_refused_listing_the_declared_ones(profile):
    with pytest.raises(dp.ProfileLookupError) as exc:
        profile.lifecycle_for("clinical-note")
    assert "governance-document" in str(exc.value)


def test_a_word_outside_the_declared_vocabulary_is_refused(profile):
    """The vocabulary half of v1's enforcement (RULED ASK-4 Q3)."""
    assert profile.require_status("governance-document", "ratified") == "ratified"
    with pytest.raises(dp.ProfileLookupError, match="attested"):
        profile.require_status("governance-document", "attested")


def test_transitions_and_authorities_are_DECLARED_and_not_enforced(profile):
    """RULED ASK-4 Q3, stated rather than implied.

    Every transition is parsed, typed and readable, and every one names an
    authority the profile also declares — and nothing in v1 refuses an
    undeclared move or checks an actor against it. A later slice does that; this
    assertion is what makes its absence deliberate.
    """
    declared = {a.id for a in profile.authorities}
    transitions = [t for lc in profile.lifecycle for t in lc.transitions]
    assert transitions and all(t.authority in declared for t in transitions)
    assert not any(name.startswith("enforce") or name.startswith("check")
                   for name in dir(profile))
    assert profile.authority("gate-actor").human_only is True


# ---------------------------------------------- registration and the refusal


def test_current_refuses_when_nothing_is_registered_and_names_the_call(unregistered_profile):
    with pytest.raises(dp.DomainProfileNotRegistered) as exc:
        dp.current()
    message = str(exc.value)
    assert dp.REGISTRATION_CALL in message
    assert "RULING C2" in message
    for word in ("staged", "draft", "ratified"):
        assert f"'{word}'" not in message, "the refusal must not leak a domain's words"


def test_register_then_current_is_the_one_registration(unregistered_profile, profile):
    assert dp.is_registered() is False
    assert dp.register(profile) is profile
    assert dp.is_registered() is True
    assert dp.current() is profile


def test_register_takes_a_profile_not_a_path(unregistered_profile):
    with pytest.raises(TypeError, match="load"):
        dp.register(str(FIXTURE))


def test_unregister_restores_the_refusal(unregistered_profile, profile):
    dp.register(profile)
    dp.unregister()
    with pytest.raises(dp.DomainProfileNotRegistered):
        dp.current()


def test_importing_the_module_registers_nothing():
    """Import stays side-effect-free: resolution happens on first CALL.

    Asserted in a FRESH interpreter, because this process has a profile
    registered by the root `conftest.py` — which is the host contract and
    exactly what must not be confused with an import side effect.
    """
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-c",
         "import openxdox.domain_profile as dp; print(dp.is_registered())"],
        cwd=root, env={"PYTHONPATH": str(root / "src"), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "False"


def test_the_upstream_registry_is_consulted_only_as_a_delegation(unregistered_profile,
                                                                profile, monkeypatch):
    """ASK-4 Q5: ONE registration can serve both legs once § 4.3 lands.

    It is a delegation and never a default — with neither registry holding a
    profile the refusal still stands, which is the case that matters.
    """
    import sys
    import types

    upstream = types.ModuleType("opendox.domain_profile")
    upstream.is_registered = lambda: True          # type: ignore[attr-defined]
    upstream.current = lambda: profile             # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "opendox.domain_profile", upstream)
    assert dp.current() is profile

    upstream.is_registered = lambda: False         # type: ignore[attr-defined]
    with pytest.raises(dp.DomainProfileNotRegistered):
        dp.current()


# ------------------------------- review findings, kept as regression cases


def test_an_undeclared_status_is_refused_even_for_a_kind_that_never_freezes(profile):
    """The vocabulary check runs BEFORE the never-freezes arm.

    Answering `False` for a word the kind does not declare would hand a typo the
    same answer as a lawful projection and drop the vocabulary enforcement RULED
    ASK-4 Q3 for a whole class of kinds.
    """
    with pytest.raises(dp.ProfileLookupError, match="typo"):
        profile.is_immutable("projection", "typo")


@pytest.mark.parametrize("bad", [1, {"a": 1}, "one-string"])
def test_a_scalar_where_a_list_belongs_is_refused_by_name(raw, bad):
    """`load()` refuses once, naming the field — never a raw TypeError."""
    raw["lifecycle"][0]["terminal_statuses"] = bad
    with pytest.raises(dp.DomainProfileInvalid, match="terminal_statuses"):
        dp.load(raw)


def test_a_second_registration_is_refused_not_silently_applied(unregistered_profile,
                                                               profile, raw):
    """ONE registration (RULED ASK-4 Q5).

    Swapping the vocabulary under a running engine would leave half a process
    reading words the other half had stopped using, with nothing reporting it.
    """
    dp.register(profile)
    assert dp.register(profile) is profile, "re-registering the same profile is a no-op"
    raw["mapping_id"] = "some-other-domain"
    with pytest.raises(dp.AlreadyRegistered, match="unregister"):
        dp.register(dp.load(raw))
    assert dp.current() is profile
    dp.unregister()
    other = dp.register(dp.load(raw))
    assert dp.current() is other


# --------------------------------------------------- fix-round regression case
#
# Closes the unresolved thread from the Copilot review round on
# openXdox-code #14 (2026-09-11, domain_profile.py:568): a boolean field was
# silently coerced (`bool(...)`) instead of refused.


@pytest.mark.parametrize("bad", ["false", "true", 0, 1, ["nested"], {"x": 1}])
def test_a_non_bool_where_a_flag_belongs_is_refused_by_name(raw, bad):
    """`bool(...)` would COERCE every one of these; the loader must not.

    `human_only: "false"` is the motivating case: a non-empty string is truthy
    in Python, so the old `bool(mapping.get(key, False))` silently turned a
    NEGATIVE declaration into `True`, changing the authority metadata instead
    of refusing the malformed field.
    """
    raw["authorities"][0]["human_only"] = bad
    with pytest.raises(dp.DomainProfileInvalid, match="human_only"):
        dp.load(raw)


def test_an_absent_flag_still_defaults_to_false(raw):
    """No regression: an authority that omits the key keeps its default."""
    del raw["authorities"][0]["human_only"]
    profile = dp.load(raw)
    assert profile.authority("lane-author").human_only is False


def test_a_declared_bool_flag_still_loads(raw):
    """No regression: an actual `bool` still loads, whichever way it points."""
    raw["authorities"][0]["human_only"] = True
    profile = dp.load(raw)
    assert profile.authority("lane-author").human_only is True


def test_a_non_bool_status_flag_is_also_refused(raw):
    """The same `_flag` helper backs `Status.contradiction_legal` too."""
    raw["lifecycle"][0]["vocabulary"][0]["contradiction_legal"] = "true"
    with pytest.raises(dp.DomainProfileInvalid, match="contradiction_legal"):
        dp.load(raw)


# --------------------------------------------------- fix-round regression case
#
# Closes the unresolved thread from the Copilot review round on
# openXdox-code #14 (2026-09-11, domain_profile.py:882): `load()` checked that
# each lifecycle's `artifact_kind` was DECLARED, but not that it was declared
# only ONCE — a set silently absorbs a duplicate `artifact_kinds[].id`, and
# `lifecycle_for()` returns the first matching entry, so a later lifecycle for
# an already-used kind loaded with no effect and no refusal.


def test_a_duplicate_artifact_kind_id_is_refused(raw):
    """A set comprehension would otherwise absorb the duplicate with no error."""
    raw["artifact_kinds"].append(copy.deepcopy(raw["artifact_kinds"][0]))
    with pytest.raises(dp.DomainProfileInvalid, match="artifact_kinds"):
        dp.load(raw)


def test_a_duplicate_lifecycle_entry_for_one_kind_is_refused(raw):
    """`lifecycle_for()` returns the FIRST match; a second entry for the same
    kind must be refused at load time rather than silently ignored — the
    second entry's vocabulary, immutability point or transitions would
    otherwise have no effect at all."""
    raw["lifecycle"].append(copy.deepcopy(raw["lifecycle"][0]))
    with pytest.raises(dp.DomainProfileInvalid, match="governance-document"):
        dp.load(raw)


# --------------------------------------------------- fix-round regression case
#
# Closes the unresolved thread from the Copilot review round on
# openXdox-code #14 (2026-09-11, gate_console.py:214): `_demote_destination`
# read the `demote` transition's `to:` spelling — validated only against the
# SOURCE kind's (`governance-document`) vocabulary — instead of asking the
# DESTINATION kind (`staging-topic`) for its own "organized" word. The two
# words only coincide by construction in openxFactory's own fixture.
# `generator._declared_origin_kind` read the identical, and identically
# wrong, accessor for the same underlying reason; both now call the new
# `destination_role_status`, added here.


def test_destination_role_status_resolves_via_the_destination_kind(raw):
    """The regression case: source and destination kinds may spell a role
    differently, and the artifact that gets created is the DESTINATION kind.

    `destination_status("demote")` reads the transition's own `to:` spelling —
    a word the loader validates only against the SOURCE kind's vocabulary
    (`governance-document`). The artifact actually created is of the
    DESTINATION kind (`staging-topic`), whose own vocabulary is free to spell
    the same "organized" role differently. `destination_role_status` must
    resolve through the destination kind, not the source's `to:` literal —
    which is exactly what `gate_console._demote_destination` and
    `generator._declared_origin_kind` both now call.
    """
    for entry in raw["lifecycle"]:
        if entry["artifact_kind"] != "staging-topic":
            continue
        for status in entry["vocabulary"]:
            if status["id"] == "staged":
                status["id"] = "collected"
        for transition in entry["transitions"]:
            for end in ("from", "to"):
                if transition.get(end) == "staged":
                    transition[end] = "collected"
    profile = dp.load(raw)
    # The SOURCE kind's transition is untouched: it still says `to: staged`.
    assert profile.destination_status("demote") == "staged"
    assert profile.destination_kind("demote") == "staging-topic"
    # But the artifact that actually exists as a staging-topic now carries
    # THAT kind's own word for "organized", which is no longer "staged".
    assert profile.destination_role_status("demote", "organized") == "collected"


def test_destination_role_status_matches_the_old_accessor_when_the_words_agree(profile):
    """No regression: when source and destination happen to agree (this
    fixture's own shape), the two accessors answer the same question."""
    assert (profile.destination_role_status("demote", "organized")
            == profile.destination_status("demote")
            == "staged")


# --------------------------------------------------- fix-round regression case
#
# Closes a Copilot review thread from the SECOND round on openXdox-code #14
# (2026-09-11, domain_profile.py:500, raised against the first round's own
# `destination_role_status`): `destination_kind()` filtered out rows with no
# declared `destination_kind` BEFORE comparing values, so if one `demote`
# transition named a destination kind and another said nothing at all, the
# filtered set held only the declared value and `_one()` saw no disagreement —
# answering as if every row had agreed, when one of them had not.


def test_destination_kind_refused_when_only_some_transitions_declare_it(raw):
    """`demote` is declared on TWO rows (from draft, from ratified). If one
    names `destination_kind` and the other omits it, the old filter-then-
    compare logic silently returned the one row that DID declare it."""
    for entry in raw["lifecycle"]:
        if entry["artifact_kind"] != "governance-document":
            continue
        for transition in entry["transitions"]:
            if transition.get("from") == "ratified" and transition.get("act") == "demote":
                del transition["destination_kind"]
    profile = dp.load(raw)
    with pytest.raises(dp.ProfileLookupError, match="destination_kind"):
        profile.destination_kind("demote")
