"""The DOMAIN PROFILE this engine is parameterized by, resolved LATE.

WHY THIS FILE EXISTS. RULING C2 (`opensoft/openxFactory#656`, 2026-09-04T17:47Z)
is that openXdox is the domain-mapping CORE, *parameterized* by a domain profile
that a descendant supplies — *"a clinician using `MedxDox` never sees the word
'requirement'"*. `split-opendox-two-layer-product` `tasks.md` § 4.4 states the
consequence in one box:

    PARAMETERIZE, do not ship one domain's words (RULING C2). The lifecycle
    engine reads its status vocabulary, transitions, authorities and
    immutability point from a domain profile. A hardcoded status word is a
    defect under `domain-mapping-declaration`.

It did not do this. `gate_console.py` and `generator.py` carried openxFactory's
OWN `Status:` taxonomy as literals — seventeen occurrences over fifteen lines,
re-swept live for this slice — inside the domain-neutral `openxdox` package,
which is verbatim the failure `domain-mapping-declaration` names ("openxFactory's
own vocabulary is treated as neutral ... the placement is refused under RULING
C2"). This module is what those seventeen sites now read instead.

THE SHAPE IS RULED, NOT INVENTED. `openXdox-spec`
`docs/domain-profile-design-note.md` designs it and
`contracts/schemas/domain-profile.schema.yaml` is its schema (openXdox-spec #8,
`446a13f5`). Brett Heap ruled ASK-4's five shape questions on
`openxFactory#656` comment `5634195861` ("recommendations on all five,
proceed"):

* **Q1 — carriage: BOTH.** The YAML is canonical and reviewable; the dataclass
  below is the RUNTIME form, built by `load()`, which is the one place a
  malformed profile is refused rather than twenty call sites.
* **Q2 — the schema lives at openXdox-spec**, the enforcement side. It is NOT
  vendored here: `load()` checks the fields THIS ENGINE CONSUMES and refuses
  clearly, which is a narrower and more honest promise than a copy of a schema
  that can drift out of step with its home.
* **Q3 — v1 ENFORCES vocabulary and the immutability point; transitions and
  authorities are DECLARED only.** Every transition and authority is parsed,
  typed and readable off this object, and nothing here refuses an undeclared
  transition or checks an actor's authority. That is a later slice, and its
  absence is stated rather than implied.
* **Q4 — `terminal_statuses` is PER KIND.** The `("rejected", "superseded")`
  pair at the old `gate_console.py:1151` is a REGISTER-POSSIBLE vocabulary, not
  a document one; a single flat list would have mixed two vocabularies.
* **Q5 — ONE registration, TWO accessors.** `current()` here is this leg's
  accessor. `register()` is the one call the host makes at process start. See
  "THE REGISTRATION CONTRACT" below.

RESOLVE BY ROLE, NEVER BY WORD. `STAGED_STATUS` was never "the string
`staged`"; it is "the status this domain's documents carry while ORGANIZED".
A descendant whose organized status is spelled `triaged` must work with no
engine change, which a `profile.statuses["staged"]` lookup would not deliver —
so the profile carries a NEUTRAL `role:` per status (`captured | organized |
proposed | ratified | promoted | superseded | retired | out-of-band | other`,
the lifecycle-state column of the source taxonomy) and `status(role)` is how
the engine asks.

REFUSAL, NOT A DEFAULT. When no profile is registered the engine REFUSES with
`DomainProfileNotRegistered`, naming the registration call. It does not fall
back to the words it used to hardcode: a fallback is exactly how those literals
would survive this refactor invisibly, and it is the permissive answer
`domain-mapping-declaration`'s second requirement already refuses twice ("both
defaults are the permissive answer to a question the domain was asked precisely
because permissiveness is unsafe").

THE REGISTRATION CONTRACT — what openxFactory's half must honour:

    import openxdox.domain_profile as domain_profile
    domain_profile.register(domain_profile.load(<path to the domain profile YAML>))

called ONCE at process start, by the descendant's own adapter and by nothing in
the neutral packages. `openxdox` never imports `openxFactory`; the direction the
carve removed stays removed. Q5's SECOND accessor is openDox-code's ruled
`profile_openxfactory` lazy proxy (§ 4.3, ASK-2 `5628886636`), which is held
until BUILD slice 2b lands. So that one host call can serve both legs the moment
§ 4.3 exists, `current()` ALSO consults an upstream registry at
`opendox.domain_profile` when nothing has been registered here — late, optional,
and in the lawful direction only (openXdox pins openDox, never the reverse). It
is a delegation, never a default: when neither registry holds a profile the
refusal stands.

FORWARD TOLERANCE, DELIBERATE. `load()` refuses on MISSING required fields and
ignores unrecognized ones. A profile written against a later schema revision —
the one in flight adds openxFactory's ninth status, `projection`, "out of band"
and explicitly NOT immutable, with an `addenda: regenerated` immutability point
(openXdox-spec #11; retraction `openxFactory#656` comment `5633989351`) — must
load here without weakening anything: `immutability_point` stays REQUIRED for
every kind, `regenerated` additionally requires its `note`, and a kind that
never freezes says so in the field built to carry the answer instead of
omitting it.

A CREATED FILE: no row in `docs/opendox-carve-manifest.yaml` (RULED OQ-C — the
manifest declares what LEAVES openxFactory, never what a destination assembles).
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

__all__ = [
    "Act",
    "AlreadyRegistered",
    "ArtifactKind",
    "Authority",
    "DomainProfile",
    "DomainProfileInvalid",
    "DomainProfileNotRegistered",
    "EvidenceClass",
    "Gate",
    "ImmutabilityPoint",
    "Lifecycle",
    "ProfileLookupError",
    "Status",
    "Transition",
    "TruthStore",
    "current",
    "is_registered",
    "load",
    "register",
    "unregister",
]

#: The one call a host makes, quoted in every refusal so the message names the
#: fix rather than the symptom.
REGISTRATION_CALL = (
    "openxdox.domain_profile.register(openxdox.domain_profile.load(<profile.yaml>))"
)

#: Q5's other end. Consulted LATE and only when this leg's own registry is
#: empty; openXdox pins openDox (RULED OQ-2), so this direction is the lawful
#: one. Never imported at module import time.
_UPSTREAM_REGISTRY = "opendox.domain_profile"

#: The neutral role vocabulary a status may declare, as the schema's `role:`
#: enum spells it. The engine asks for a ROLE and is handed the domain's word.
KNOWN_ROLES = (
    "captured",
    "organized",
    "proposed",
    "ratified",
    "promoted",
    "superseded",
    "retired",
    "out-of-band",
    "other",
)

#: How a lawful later write is made past the immutability point, as the schema's
#: `addenda:` enum spells it. `regenerated` is the one value that says a kind
#: NEVER freezes (openxFactory's `projection`), and it is the one value that
#: must also say WHY, in `note`.
KNOWN_ADDENDA = ("separate-document", "cited-change", "appended-addendum", "regenerated")

#: The `addenda` value under which a kind never becomes immutable at all.
NEVER_FREEZES = "regenerated"


class DomainProfileNotRegistered(RuntimeError):
    """No domain profile has been registered, and this engine has no words.

    Raised instead of falling back to the status vocabulary this package used
    to hardcode. The fallback IS the defect RULING C2 names, so it does not
    exist here: a process that drives the lifecycle engine registers its
    domain's profile at start, or the engine refuses.
    """


class DomainProfileInvalid(ValueError):
    """A profile was supplied and this engine cannot read it.

    Raised by `load()` at the ONE point a profile enters the process, naming the
    field, so a malformed declaration fails once, on the way in, rather than at
    each of the sites that consume it.
    """


class AlreadyRegistered(RuntimeError):
    """A second domain profile was registered over a first.

    ONE registration is the contract (RULED ASK-4 Q5). Swapping the vocabulary
    under a running engine is refused rather than applied; `unregister()` makes
    a deliberate swap explicit.
    """


class ProfileLookupError(LookupError):
    """The profile loaded, and it does not declare what the engine asked for.

    A missing artifact kind, a role no vocabulary carries, an act no transition
    declares. Distinct from `DomainProfileInvalid` — the declaration is
    well-formed; it simply does not answer this question, which for a descendant
    profile is a real and reportable gap rather than a parse error.
    """


# ---------------------------------------------------------------- the axes


@dataclass(frozen=True)
class Status:
    """One word in one kind's closed vocabulary, plus its NEUTRAL role."""

    id: str
    role: str
    label: str | None = None
    meaning: str | None = None
    contradiction_legal: bool = False
    excluded_from_conversion: bool = False


@dataclass(frozen=True)
class ImmutabilityPoint:
    """The status at or past which a record freezes, and the lawful later write.

    REQUIRED per kind, never defaulted — `domain-mapping-declaration`'s second
    requirement: *"a vocabulary with no declared immutability point SHALL be
    refused rather than defaulted to 'never'."* A kind that never freezes at all
    still declares this field, with `addenda: regenerated` and a `note` saying
    why (openxFactory's `projection`).
    """

    status: str
    addenda: str
    note: str | None = None

    @property
    def never_freezes(self) -> bool:
        """Is this a kind whose artifacts are RE-DERIVED rather than frozen?"""
        return self.addenda == NEVER_FREEZES


@dataclass(frozen=True)
class Transition:
    """One legal move, and the AUTHORITY it requires.

    DECLARED data in v1 (RULED ASK-4 Q3): the engine reads these rows, and does
    not yet refuse an undeclared move or check an actor against `authority`.
    """

    from_status: str | None
    to: str
    authority: str
    act: str | None = None
    destination_kind: str | None = None
    basis: str | None = None
    reverse_of: str | None = None


@dataclass(frozen=True)
class Lifecycle:
    """Axis 2, per artifact kind."""

    artifact_kind: str
    vocabulary: tuple[Status, ...]
    immutability_point: ImmutabilityPoint
    transitions: tuple[Transition, ...] = ()
    terminal_statuses: tuple[str, ...] = ()

    def status_ids(self) -> tuple[str, ...]:
        return tuple(s.id for s in self.vocabulary)

    def by_role(self, role: str) -> tuple[Status, ...]:
        return tuple(s for s in self.vocabulary if s.role == role)


@dataclass(frozen=True)
class ArtifactKind:
    id: str
    label: str
    description: str | None = None
    locations: tuple[str, ...] = ()


@dataclass(frozen=True)
class Gate:
    id: str
    actor_class: str
    label: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class Act:
    id: str
    gate: str
    label: str | None = None
    target_kind: str | None = None
    requires_evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceClass:
    id: str
    label: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class Authority:
    id: str
    label: str
    description: str | None = None
    human_only: bool = False


@dataclass(frozen=True)
class TruthStore:
    name: str
    external_enforcement_point: str
    description: str | None = None


@dataclass(frozen=True)
class DomainProfile:
    """The runtime form of a domain mapping declaration (ASK-4 Q1: BOTH).

    Read-only by construction. The YAML beside it is canonical; this object is
    what the engine holds.
    """

    mapping_id: str
    artifact_kinds: tuple[ArtifactKind, ...]
    lifecycle: tuple[Lifecycle, ...]
    acts: tuple[Act, ...]
    evidence_classes: tuple[EvidenceClass, ...]
    authorities: tuple[Authority, ...]
    truth_store: TruthStore
    neutral: bool = False
    domain_label: str | None = None
    declared_by: str | None = None
    gates: tuple[Gate, ...] = ()
    basis: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    source: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------ lifecycle

    def kinds(self) -> tuple[str, ...]:
        """Every artifact kind that declares a lifecycle, in declared order."""
        return tuple(lc.artifact_kind for lc in self.lifecycle)

    def lifecycle_for(self, kind: str) -> Lifecycle:
        for lc in self.lifecycle:
            if lc.artifact_kind == kind:
                return lc
        raise ProfileLookupError(
            f"domain profile {self.mapping_id!r} declares no lifecycle for "
            f"artifact kind {kind!r}; it declares {list(self.kinds())}")

    def statuses(self, kind: str | None = None) -> tuple[str, ...]:
        """This domain's words — for one kind, or every word it uses anywhere."""
        if kind is not None:
            return self.lifecycle_for(kind).status_ids()
        seen: list[str] = []
        for lc in self.lifecycle:
            for sid in lc.status_ids():
                if sid not in seen:
                    seen.append(sid)
        return tuple(seen)

    def status(self, role: str, *, kind: str | None = None) -> str:
        """The domain's WORD for a neutral ROLE. The engine's main accessor.

        Asking by role is what makes a descendant whose organized status is
        spelled `triaged` work with no engine change. With no `kind`, the role
        must resolve to ONE word across every kind that carries it: a profile
        where two kinds disagree about the word for a role is answered with a
        refusal naming both, never with whichever came first.
        """
        if kind is not None:
            found = self.lifecycle_for(kind).by_role(role)
            if not found:
                raise ProfileLookupError(
                    f"domain profile {self.mapping_id!r} declares no status "
                    f"with role {role!r} for kind {kind!r}; it declares "
                    f"{[(s.id, s.role) for s in self.lifecycle_for(kind).vocabulary]}")
            if len(found) > 1:
                raise ProfileLookupError(
                    f"role {role!r} is ambiguous within kind {kind!r} of domain "
                    f"profile {self.mapping_id!r}: {[s.id for s in found]}. Ask "
                    "for the status by a role only one word carries.")
            return found[0].id
        words: dict[str, list[str]] = {}
        for lc in self.lifecycle:
            for s in lc.by_role(role):
                words.setdefault(s.id, []).append(lc.artifact_kind)
        if not words:
            raise ProfileLookupError(
                f"domain profile {self.mapping_id!r} declares no status with "
                f"role {role!r} in any kind. Roles this profile uses: "
                f"{sorted({s.role for lc in self.lifecycle for s in lc.vocabulary})}")
        if len(words) > 1:
            detail = ", ".join(f"{w!r} in {sorted(k)}" for w, k in sorted(words.items()))
            raise ProfileLookupError(
                f"role {role!r} resolves to more than one word in domain profile "
                f"{self.mapping_id!r} ({detail}); name the artifact kind")
        return next(iter(words))

    def terminal_statuses(self, kind: str) -> tuple[str, ...]:
        """The statuses from which this kind's artifacts do not move on.

        PER KIND (RULED ASK-4 Q4): a register possible's terminal states are not
        a governance document's, and one flat list would have mixed the two.
        """
        return self.lifecycle_for(kind).terminal_statuses

    def immutability_point(self, kind: str) -> ImmutabilityPoint:
        """Where this kind's records freeze. Enforced in v1 (RULED ASK-4 Q3)."""
        return self.lifecycle_for(kind).immutability_point

    def is_immutable(self, kind: str, status: str) -> bool:
        """Has an artifact of `kind` at `status` passed its immutability point?

        Ordering is the vocabulary's own declared order, which the schema calls
        "spine order" — the profile states it so a reader and this engine share
        one axis. A kind declaring `addenda: regenerated` NEVER freezes, so the
        answer is False at every status: regenerating a projection in place is
        the correct act, not a violation.
        """
        lc = self.lifecycle_for(kind)
        # THE VOCABULARY CHECK COMES FIRST, and specifically before the
        # never-freezes arm. Answering `False` for a status the kind does not
        # declare would hand a typo the same answer as a lawful projection and
        # quietly drop the vocabulary enforcement RULED ASK-4 Q3 for a whole
        # class of kinds. An undeclared word is a refusal whatever the kind's
        # immutability point says.
        self.require_status(kind, status)
        point = lc.immutability_point
        if point.never_freezes:
            return False
        order = lc.status_ids()
        return order.index(status) >= order.index(point.status)

    def require_status(self, kind: str, status: str) -> str:
        """Refuse a word the declared vocabulary of `kind` does not carry.

        The vocabulary half of v1's enforcement (RULED ASK-4 Q3).
        """
        order = self.lifecycle_for(kind).status_ids()
        if status not in order:
            raise ProfileLookupError(
                f"{status!r} is not in the declared vocabulary of kind {kind!r} "
                f"in domain profile {self.mapping_id!r}: {list(order)}")
        return status

    # ---------------------------------------------------------- transitions

    def transitions_for(self, act: str) -> tuple[Transition, ...]:
        """Every declared transition carrying `act`, across every kind."""
        return tuple(t for lc in self.lifecycle for t in lc.transitions if t.act == act)

    def kind_declaring(self, act: str) -> str:
        """The artifact kind whose lifecycle declares transitions for `act`.

        How the engine names a KIND without hardcoding one. `governance-document`
        is openxFactory's word for its governed prose; `MedxDox` will call the
        same thing something else, so an engine site that needs "the kind this
        domain demotes" asks for it by the ACT rather than by the kind's name.
        The engine keeps its own verb list — `demote` is the gate console's own
        API surface, not a status word — and looks the DOMAIN's words up by it.
        """
        kinds = tuple(sorted({lc.artifact_kind for lc in self.lifecycle
                              for t in lc.transitions if t.act == act}))
        if not kinds:
            raise ProfileLookupError(
                f"no lifecycle in domain profile {self.mapping_id!r} declares a "
                f"transition for act {act!r}")
        if len(kinds) > 1:
            raise ProfileLookupError(
                f"act {act!r} is declared by more than one kind in domain profile "
                f"{self.mapping_id!r}: {list(kinds)}; the engine cannot pick one")
        return kinds[0]

    def destination_status(self, act: str) -> str:
        """The status an act's declared transitions land ON.

        One act may be declared on several rows — openxFactory's `demote` is
        declared twice, from `draft` and from `ratified` — and they must agree
        about where the artifact arrives, or the engine has no single answer to
        write into a transition manifest.
        """
        rows = self.transitions_for(act)
        return self._one(rows, act, "to", tuple(sorted({t.to for t in rows})))

    def destination_kind(self, act: str) -> str:
        """The ARTIFACT KIND an act's declared transitions land IN.

        Declared data in v1; carried because the design note's migration table
        names this axis for the demote manifest, and a later slice that enforces
        transitions will want it. The manifest itself records the destination
        STATUS (`destination_status`), which is the token this domain's records
        have always carried.
        """
        rows = self.transitions_for(act)
        declared = [t.destination_kind for t in rows]
        present = [d for d in declared if d]
        if present and len(present) != len(declared):
            # NOT the same as "disagree about a value" (`_one` below already
            # refuses that): here SOME rows for this act name a destination
            # kind and OTHERS say nothing at all. Filtering the missing ones
            # out before comparing would silently answer with whichever rows
            # DID declare it, as if every row had agreed — when one of them
            # declared nothing.
            raise ProfileLookupError(
                f"the transitions for act {act!r} in domain profile "
                f"{self.mapping_id!r} disagree about destination_kind: "
                f"{len(present)} of {len(declared)} declare one and the rest "
                "declare none; either every transition for this act names a "
                "destination_kind or none of them does")
        values = tuple(sorted(set(present)))
        return self._one(rows, act, "destination_kind", values)

    def destination_role_status(self, act: str, role: str) -> str:
        """The word the artifact carries once it EXISTS as `act`'s destination kind.

        Deliberately NOT `status(role, kind=kind_declaring(act))` and NOT
        `destination_status(act)`. Those two ask the kind `act` departs FROM:
        `destination_status` reads the transition's own `to:` spelling, which
        the loader validates only against the SOURCE kind's vocabulary. But an
        act like `demote` creates an artifact of a DIFFERENT kind
        (`destination_kind(act)`, e.g. `staging-topic` for `governance-document`'s
        `demote`), and that new artifact's status header must carry ITS OWN
        kind's word for `role` — not whatever the source kind happened to spell
        the same transition endpoint as. The two words coincide in
        openxFactory's own fixture, which is exactly the coincidence a
        descendant profile is not obliged to share.
        """
        return self.status(role, kind=self.destination_kind(act))

    def _one(self, rows: tuple[Transition, ...], act: str, fieldname: str,
             values: tuple[str, ...]) -> str:
        if not rows:
            raise ProfileLookupError(
                f"domain profile {self.mapping_id!r} declares no transition for "
                f"act {act!r}; acts its transitions declare: "
                f"{sorted({t.act for lc in self.lifecycle for t in lc.transitions if t.act})}")
        if not values:
            raise ProfileLookupError(
                f"no transition for act {act!r} in domain profile "
                f"{self.mapping_id!r} declares {fieldname!r}")
        if len(values) > 1:
            raise ProfileLookupError(
                f"the transitions for act {act!r} in domain profile "
                f"{self.mapping_id!r} disagree about {fieldname!r}: {list(values)}")
        return values[0]

    # ------------------------------------------------------- the other axes

    def act(self, act_id: str) -> Act:
        for a in self.acts:
            if a.id == act_id:
                return a
        raise ProfileLookupError(
            f"domain profile {self.mapping_id!r} declares no act {act_id!r}")

    def authority(self, authority_id: str) -> Authority:
        for a in self.authorities:
            if a.id == authority_id:
                return a
        raise ProfileLookupError(
            f"domain profile {self.mapping_id!r} declares no authority "
            f"{authority_id!r}")

    def artifact_kind(self, kind_id: str) -> ArtifactKind:
        for k in self.artifact_kinds:
            if k.id == kind_id:
                return k
        raise ProfileLookupError(
            f"domain profile {self.mapping_id!r} declares no artifact kind "
            f"{kind_id!r}")


# ------------------------------------------------------------------ loader


def _require(mapping: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in mapping or mapping[key] is None:
        raise DomainProfileInvalid(f"{where}: required field {key!r} is missing")
    return mapping[key]


def _as_mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DomainProfileInvalid(f"{where}: expected a mapping, got {type(value).__name__}")
    return value


def _as_sequence(value: Any, where: str) -> list[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise DomainProfileInvalid(f"{where}: expected a list, got {type(value).__name__}")
    items = list(value)
    if not items:
        raise DomainProfileInvalid(f"{where}: declared empty; at least one entry is required")
    return items


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainProfileInvalid(f"{where}: expected a non-empty string")
    return value


def _opt_text(mapping: Mapping[str, Any], key: str) -> str | None:
    value = mapping.get(key)
    return value if isinstance(value, str) and value.strip() else None


def _flag(mapping: Mapping[str, Any], key: str, where: str) -> bool:
    """A declared boolean, refused if the YAML did not actually declare one.

    `bool(value)` would COERCE any value — a stray string `human_only: "false"`
    is truthy in Python and becomes `True`, silently changing the authority
    metadata rather than refusing the malformed field. The schema declares
    these fields as booleans, so the loader accepts exactly a `bool` (or an
    absent key, which keeps its default) and refuses every other shape, naming
    the field the way every other loader helper here does.
    """
    value = mapping.get(key, False)
    if not isinstance(value, bool):
        raise DomainProfileInvalid(
            f"{where}.{key}: expected a bool, got {type(value).__name__}")
    return value


def _tuple_of_text(value: Any, where: str) -> tuple[str, ...]:
    """A declared list of strings, or ().

    Every shape that is not a list of strings is refused HERE, by name. A scalar
    (`terminal_statuses: 1`) or a mapping would otherwise reach `enumerate()`
    and surface as a raw `TypeError` from inside the loader — which is the one
    thing `load()` promises not to do: a malformed profile is refused once, on
    the way in, naming the field.
    """
    if value is None:
        return ()
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        raise DomainProfileInvalid(
            f"{where}: expected a list of strings, got {type(value).__name__}")
    return tuple(_text(v, f"{where}[{i}]") for i, v in enumerate(value))


def _status(raw: Any, where: str) -> Status:
    data = _as_mapping(raw, where)
    role = _text(_require(data, "role", where), f"{where}.role")
    if role not in KNOWN_ROLES:
        raise DomainProfileInvalid(
            f"{where}.role: {role!r} is not a neutral role this engine knows; "
            f"the declared roles are {list(KNOWN_ROLES)}")
    return Status(
        id=_text(_require(data, "id", where), f"{where}.id"),
        role=role,
        label=_opt_text(data, "label"),
        meaning=_opt_text(data, "meaning"),
        contradiction_legal=_flag(data, "contradiction_legal", where),
        excluded_from_conversion=_flag(data, "excluded_from_conversion", where),
    )


def _immutability_point(raw: Any, where: str) -> ImmutabilityPoint:
    data = _as_mapping(raw, where)
    addenda = _text(_require(data, "addenda", where), f"{where}.addenda")
    if addenda not in KNOWN_ADDENDA:
        raise DomainProfileInvalid(
            f"{where}.addenda: {addenda!r} is not a lawful-later-write this "
            f"engine knows; the declared values are {list(KNOWN_ADDENDA)}")
    note = _opt_text(data, "note")
    if addenda == NEVER_FREEZES and note is None:
        raise DomainProfileInvalid(
            f"{where}: an immutability point declaring {NEVER_FREEZES!r} says this "
            "kind never freezes, and MUST record in `note` why — the reason is "
            "part of the declaration, not something a reader infers")
    return ImmutabilityPoint(
        status=_text(_require(data, "status", where), f"{where}.status"),
        addenda=addenda,
        note=note,
    )


def _transition(raw: Any, where: str) -> Transition:
    data = _as_mapping(raw, where)
    if "from" not in data:
        raise DomainProfileInvalid(f"{where}: required field 'from' is missing")
    origin = data["from"]
    if origin is not None and not isinstance(origin, str):
        raise DomainProfileInvalid(f"{where}.from: expected a status id or null")
    return Transition(
        from_status=origin,
        to=_text(_require(data, "to", where), f"{where}.to"),
        authority=_text(_require(data, "authority", where), f"{where}.authority"),
        act=_opt_text(data, "act"),
        destination_kind=_opt_text(data, "destination_kind"),
        basis=_opt_text(data, "basis"),
        reverse_of=_opt_text(data, "reverse_of"),
    )


def _lifecycle(raw: Any, index: int) -> Lifecycle:
    where = f"lifecycle[{index}]"
    data = _as_mapping(raw, where)
    kind = _text(_require(data, "artifact_kind", where), f"{where}.artifact_kind")
    where = f"lifecycle[{kind}]"
    vocabulary = tuple(
        _status(v, f"{where}.vocabulary[{i}]")
        for i, v in enumerate(_as_sequence(_require(data, "vocabulary", where),
                                           f"{where}.vocabulary")))
    ids = [s.id for s in vocabulary]
    duplicates = sorted({sid for sid in ids if ids.count(sid) > 1})
    if duplicates:
        raise DomainProfileInvalid(
            f"{where}.vocabulary: status id declared more than once: {duplicates}")
    point = _immutability_point(
        _require(data, "immutability_point", where), f"{where}.immutability_point")
    if point.status not in ids:
        raise DomainProfileInvalid(
            f"{where}.immutability_point.status: {point.status!r} is not in this "
            f"kind's declared vocabulary {ids}")
    if point.never_freezes:
        # `addenda: regenerated` says this KIND never freezes (openxFactory's
        # `projection`) — and that claim is only honest when the immutability
        # point's own status is the out-of-band word nothing else in this
        # kind's spine claims. Checking only that `note` is present (already
        # done in `_immutability_point`) lets a profile declare an ordinary
        # spine status such as `ratified` as "regenerated", silently turning
        # off v1's immutability enforcement for it (`is_immutable()` answers
        # `False` at every status once `never_freezes` is true).
        point_status = next(s for s in vocabulary if s.id == point.status)
        if point_status.role != "out-of-band":
            raise DomainProfileInvalid(
                f"{where}.immutability_point: addenda 'regenerated' says "
                f"{point.status!r} never freezes, but its declared role is "
                f"{point_status.role!r}, not 'out-of-band' — a status this "
                "kind otherwise treats as part of its ordinary spine cannot "
                "also claim it never reaches an immutability point")
    transitions = tuple(
        _transition(t, f"{where}.transitions[{i}]")
        for i, t in enumerate(_as_sequence(_require(data, "transitions", where),
                                           f"{where}.transitions")))
    for i, t in enumerate(transitions):
        if t.to not in ids:
            raise DomainProfileInvalid(
                f"{where}.transitions[{i}].to: {t.to!r} is not in this kind's "
                f"declared vocabulary {ids}")
        if t.from_status is not None and t.from_status not in ids:
            raise DomainProfileInvalid(
                f"{where}.transitions[{i}].from: {t.from_status!r} is not in this "
                f"kind's declared vocabulary {ids}")
    # `_require`, not `.get()`: `terminal_statuses` is required by the profile
    # contract EVEN WHEN THE LIST IS EMPTY (openxFactory's own `projection`
    # kind declares `terminal_statuses: []` rather than omitting the key).
    # `.get()` cannot tell "declared empty" apart from "not declared at all" —
    # both reach `_tuple_of_text` as `None` and both become `()` — so a
    # profile that omits the field entirely loaded exactly as if it had
    # explicitly said "no terminal states", instead of being refused for
    # skipping a required declaration.
    terminal = _tuple_of_text(
        _require(data, "terminal_statuses", where), f"{where}.terminal_statuses")
    for word in terminal:
        if word not in ids:
            raise DomainProfileInvalid(
                f"{where}.terminal_statuses: {word!r} is not in this kind's "
                f"declared vocabulary {ids}")
    return Lifecycle(
        artifact_kind=kind,
        vocabulary=vocabulary,
        immutability_point=point,
        transitions=transitions,
        terminal_statuses=terminal,
    )


def _artifact_kind(raw: Any, index: int) -> ArtifactKind:
    where = f"artifact_kinds[{index}]"
    data = _as_mapping(raw, where)
    return ArtifactKind(
        id=_text(_require(data, "id", where), f"{where}.id"),
        label=_text(_require(data, "label", where), f"{where}.label"),
        description=_opt_text(data, "description"),
        locations=_tuple_of_text(data.get("locations"), f"{where}.locations"),
    )


def _act(raw: Any, index: int) -> Act:
    where = f"acts[{index}]"
    data = _as_mapping(raw, where)
    return Act(
        id=_text(_require(data, "id", where), f"{where}.id"),
        gate=_text(_require(data, "gate", where), f"{where}.gate"),
        label=_opt_text(data, "label"),
        target_kind=_opt_text(data, "target_kind"),
        requires_evidence=_tuple_of_text(
            data.get("requires_evidence"), f"{where}.requires_evidence"),
    )


def _gate(raw: Any, index: int) -> Gate:
    where = f"gates[{index}]"
    data = _as_mapping(raw, where)
    return Gate(
        id=_text(_require(data, "id", where), f"{where}.id"),
        actor_class=_text(_require(data, "actor_class", where), f"{where}.actor_class"),
        label=_opt_text(data, "label"),
        description=_opt_text(data, "description"),
    )


def _evidence_class(raw: Any, index: int) -> EvidenceClass:
    where = f"evidence_classes[{index}]"
    data = _as_mapping(raw, where)
    return EvidenceClass(
        id=_text(_require(data, "id", where), f"{where}.id"),
        label=_opt_text(data, "label"),
        description=_opt_text(data, "description"),
    )


def _authority(raw: Any, index: int) -> Authority:
    where = f"authorities[{index}]"
    data = _as_mapping(raw, where)
    return Authority(
        id=_text(_require(data, "id", where), f"{where}.id"),
        label=_text(_require(data, "label", where), f"{where}.label"),
        description=_opt_text(data, "description"),
        human_only=_flag(data, "human_only", where),
    )


def _truth_store(raw: Any) -> TruthStore:
    where = "truth_store"
    data = _as_mapping(raw, where)
    return TruthStore(
        name=_text(_require(data, "name", where), f"{where}.name"),
        external_enforcement_point=_text(
            _require(data, "external_enforcement_point", where),
            f"{where}.external_enforcement_point"),
        description=_opt_text(data, "description"),
    )


#: The fields this ENGINE consumes, and therefore the fields `load()` refuses to
#: proceed without. Deliberately the engine's own list rather than a vendored
#: copy of the schema: the schema lives at openXdox-spec (RULED ASK-4 Q2) and a
#: copy here would be a second source of truth free to drift from its home.
REQUIRED_TOP_LEVEL = (
    "schema_version",
    "kind",
    "mapping_id",
    "neutral",
    "artifact_kinds",
    "lifecycle",
    "acts",
    "evidence_classes",
    "authorities",
    "truth_store",
)

SCHEMA_VERSION = 1
PROFILE_KIND = "domain-profile"

_STRUCTURAL_KEYS = frozenset(REQUIRED_TOP_LEVEL) | {
    "domain_label", "declared_by", "basis", "gates", "notes"}


def load(source: str | Path | Mapping[str, Any]) -> DomainProfile:
    """Build the runtime profile from the canonical YAML, or refuse clearly.

    `source` is a path to the profile YAML (ASK-4 Q1: the YAML is canonical) or
    an already-parsed mapping, which is what a test fixture and a host that
    reads its own configuration both want.

    This is the ONE place a malformed profile is refused. It checks the fields
    the engine CONSUMES — the top-level axes, and per kind a vocabulary with a
    neutral role on every word, a required immutability point inside that
    vocabulary, and transitions whose ends the vocabulary carries — and ignores
    fields it does not recognize, so a profile written against a later revision
    of the openXdox-spec schema still loads.
    """
    origin: str | None = None
    if isinstance(source, Mapping):
        raw: Any = source
    else:
        path = Path(source)
        origin = str(path)
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise DomainProfileInvalid(
                f"the domain profile at {origin!r} could not be read: {exc}") from exc
        except yaml.YAMLError as exc:
            raise DomainProfileInvalid(
                f"the domain profile at {origin!r} is not valid YAML: {exc}") from exc

    where = f"the domain profile at {origin!r}" if origin else "the domain profile"
    data = _as_mapping(raw, where)

    missing = [k for k in REQUIRED_TOP_LEVEL if k not in data or data[k] is None]
    if missing:
        raise DomainProfileInvalid(
            f"{where}: required field(s) {missing} missing. A domain profile "
            "declares all five axes of `domain-mapping-declaration` — artifact "
            "kinds, lifecycle, acts and gates, evidence classes, promoting "
            "authorities — plus its truth store; none of them is optional.")

    if data["schema_version"] != SCHEMA_VERSION:
        raise DomainProfileInvalid(
            f"{where}: schema_version is {data['schema_version']!r}; this engine "
            f"reads {SCHEMA_VERSION}")
    if data["kind"] != PROFILE_KIND:
        raise DomainProfileInvalid(
            f"{where}: kind is {data['kind']!r}, not {PROFILE_KIND!r}")
    if data["neutral"] is not False:
        raise DomainProfileInvalid(
            f"{where}: `neutral` must be false. A profile is a DOMAIN's "
            "declaration; a profile claiming to be neutral is the defect RULING "
            "C2 names — one domain's words presented as everyone's.")

    profile = DomainProfile(
        mapping_id=_text(data["mapping_id"], f"{where}.mapping_id"),
        neutral=False,
        domain_label=_opt_text(data, "domain_label"),
        declared_by=_opt_text(data, "declared_by"),
        basis=_tuple_of_text(data.get("basis"), f"{where}.basis"),
        artifact_kinds=tuple(
            _artifact_kind(v, i)
            for i, v in enumerate(_as_sequence(data["artifact_kinds"], "artifact_kinds"))),
        lifecycle=tuple(
            _lifecycle(v, i)
            for i, v in enumerate(_as_sequence(data["lifecycle"], "lifecycle"))),
        acts=tuple(_act(v, i) for i, v in enumerate(_as_sequence(data["acts"], "acts"))),
        gates=tuple(
            _gate(v, i) for i, v in enumerate(data.get("gates") or [])),
        evidence_classes=tuple(
            _evidence_class(v, i)
            for i, v in enumerate(_as_sequence(data["evidence_classes"], "evidence_classes"))),
        authorities=tuple(
            _authority(v, i)
            for i, v in enumerate(_as_sequence(data["authorities"], "authorities"))),
        truth_store=_truth_store(data["truth_store"]),
        notes=_tuple_of_text(data.get("notes"), "notes"),
        source=origin,
        extra={k: v for k, v in data.items() if k not in _STRUCTURAL_KEYS},
    )

    # Both checks below refuse a DUPLICATE id rather than silently keeping the
    # first: `declared_kinds` is a set, which would otherwise absorb a repeated
    # `artifact_kinds[].id` with no error, and `lifecycle_for()` returns the
    # FIRST matching entry, which would otherwise let a later lifecycle for the
    # same kind — a different vocabulary, immutability point or transition set
    # — load without effect. A malformed profile is refused once, on the way
    # in, exactly like every other shape this loader enforces.
    kind_ids = [k.id for k in profile.artifact_kinds]
    kind_id_dupes = sorted({kid for kid in kind_ids if kind_ids.count(kid) > 1})
    if kind_id_dupes:
        raise DomainProfileInvalid(
            f"artifact_kinds: id declared more than once: {kind_id_dupes}")

    declared_kinds = set(kind_ids)
    seen_lifecycle_kinds: set[str] = set()
    for lc in profile.lifecycle:
        if lc.artifact_kind not in declared_kinds:
            raise DomainProfileInvalid(
                f"lifecycle[{lc.artifact_kind}]: no such entry in `artifact_kinds` "
                f"({sorted(declared_kinds)})")
        if lc.artifact_kind in seen_lifecycle_kinds:
            raise DomainProfileInvalid(
                f"lifecycle: artifact_kind {lc.artifact_kind!r} declares more "
                "than one lifecycle entry; lifecycle_for() would silently "
                "return only the first and ignore the rest")
        seen_lifecycle_kinds.add(lc.artifact_kind)
    return profile


# ------------------------------------------------- registration, resolved late


_registered: DomainProfile | None = None


def register(profile: DomainProfile) -> DomainProfile:
    """THE one registration. Called by the host's own adapter at process start.

    Returns the profile so a host can register and hold it in one expression.
    """
    global _registered
    if not isinstance(profile, DomainProfile):
        raise TypeError(
            "register() takes a DomainProfile; build one with "
            "openxdox.domain_profile.load(<profile.yaml>)")
    if _registered is not None and _registered is not profile:
        # ONE registration is the contract (RULED ASK-4 Q5), so a SECOND one is
        # refused rather than applied. Silently swapping the vocabulary under a
        # running engine is worse than either profile: half a process would go
        # on reading words the other half had already stopped using, and nothing
        # would report it. Re-registering the SAME object is a no-op, so an
        # idempotent host start-up is not punished; a deliberate swap says so by
        # calling `unregister()` first.
        raise AlreadyRegistered(
            f"a domain profile is already registered ({_registered.mapping_id!r}"
            f"), and {profile.mapping_id!r} would replace it. Registration "
            "happens ONCE, at process start (RULED ASK-4 Q5): a second one "
            "would change this engine's vocabulary underneath callers that have "
            "already read the first. Call "
            "openxdox.domain_profile.unregister() first if the swap is "
            "deliberate.")
    _registered = profile
    return profile


def unregister() -> None:
    """Drop the registration. For test isolation and for a host tearing down."""
    global _registered
    _registered = None


def is_registered() -> bool:
    """Has a profile been registered here, without resolving or refusing?"""
    return _registered is not None


def _upstream() -> DomainProfile | None:
    """Q5's shared registration, consulted LATE and only as a delegation.

    openXdox pins openDox (RULED OQ-2), so reaching `opendox.domain_profile` is
    the lawful direction. It is absent today — § 4.3 is held until BUILD slice 2b
    lands — and its absence is not an error: only a module that IS there and
    holds a profile answers. Anything else leaves the refusal below standing.
    """
    try:
        module = importlib.import_module(_UPSTREAM_REGISTRY)
    except ModuleNotFoundError:
        return None
    getter = getattr(module, "current", None)
    checker = getattr(module, "is_registered", None)
    if getter is None or (callable(checker) and not checker()):
        return None
    try:
        candidate = getter()
    except Exception:      # noqa: BLE001 — an upstream refusal is "not here"
        return None
    return candidate if isinstance(candidate, DomainProfile) else None


def current() -> DomainProfile:
    """The registered domain profile, or a refusal naming the registration call.

    Resolved at FIRST CALL and never at import time, on `consumer_reach.py`'s
    pattern: importing `openxdox.gate_console` must not require a host to have
    registered anything, and nothing in this package may resolve a profile
    before the host's process-start call has run.

    There is no fallback to the words this package used to hardcode. That
    fallback is precisely how the seventeen literals would have survived § 4.4
    invisibly, and it is the permissive default `domain-mapping-declaration`
    refuses.
    """
    if _registered is not None:
        return _registered
    upstream = _upstream()
    if upstream is not None:
        return upstream
    raise DomainProfileNotRegistered(
        "no domain profile is registered, so this engine has no status "
        "vocabulary, no terminal statuses and no immutability point. openXdox "
        "is the domain-mapping CORE and ships NO domain's words (RULING C2, "
        "openxFactory#656): the descendant that drives it registers its own "
        "profile at process start with\n\n    " + REGISTRATION_CALL + "\n\n"
        "and the neutral package never registers one for it. This is a refusal, "
        "not a missing default: falling back to a vocabulary here is the defect "
        "`domain-mapping-declaration` names.")
