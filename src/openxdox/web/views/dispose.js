// ---------------------------------------------------------------------------
// THIS FILE IS openXdox's NOW — § 3.4 slice S5, "contribute the gate loop"
// (openDox-spec `docs/front-end-package-boundary.md` § 5 row S5 @ `7d12428c`).
// It arrived here from openDox-code `src/opendox/web/views/dispose.js` and is
// SHIPPED AS PACKAGE DATA: RULED Q5 (openxFactory#656 comment `5648044785`,
// Brett Heap, 2026-09-12) — "the COMPOSED DEPLOYMENT assembles the bundle …
// the composed install copies them into openDox's one `--web-dir` at assembly;
// a contributed GET route is the declared hosted fallback". The bytes are
// placed by `openxdox.web_assets.install_view_modules()`; the fallback is
// `openxdox.serve_views`. The binding that declares it is in
// `src/openxdox/view_extensions.py`.
//
// WHAT IT MAY IMPORT FROM THE BUNDLE (counterpart Q6). `./views/helpers.js` is
// the RULED guarantee; every other openDox module reached from here is declared
// in `view_extensions.BUNDLE_REACH` and held there by
// `tests/test_gate_loop_views.py`, so the reach is NAMED and checkable instead
// of silent. This module reaches: `./helpers.js` (RULED guarantee), `./intent-binding.js`.
// ---------------------------------------------------------------------------
// Dispose tray + refusal panel — the LOCAL action center's first verb
// (openxFactory add-ideation-intent-plane §3, design D5 local-first; the
// hosted intent plane later swaps the transport, not this UI).
//
// The tray mounts on a pending_review possible tile when the capability
// probe reports `actions.gate` (loopback bind + real checkout + resolved
// actor — the deployed image never qualifies). Accept / reject / defer POST
// to `/actions/gate/dispose-possible`; reject collects the REQUIRED reason
// and citation first (the register kernel's uncited-rejection rule — the
// engine refuses without them, and that refusal renders in the panel).
//
// TWO TRANSPORTS, ONE TRAY (add-ideation-intent-plane task 4.4, design D5:
// "the identical tray then targets the intent API when hosted"). `opts.intent`
// selects the HOSTED transport: the click emits a `gate-intent` to the inbox
// instead of executing, and the tray shows the feed's chips for this target
// beside the buttons. Absent `opts.intent` NOTHING about the local path
// changes — same route, same body, same panel entries, same overlay.
//
// DOM-safety: every dynamic value is bound via textContent — refusal
// messages from the engine included — never innerHTML (the house posture).
// Two-plane rendering: a successful disposition NEVER mutates the
// snapshot-derived model; it lands in the local `applied` overlay the wheel
// consults, and the tile shows the verdict with a regenerate hint.

import { el } from "./helpers.js";

// THE INTENT BINDING IS NOT IMPORTED HERE ANY MORE — RULED counterpart Q6
// (Brett Heap, 2026-09-12, `opensoft/openxFactory#656` comment `5649094228`):
// "what a CONTRIBUTED view module may IMPORT from openDox's bundle:
// `./views/helpers.js` and NOTHING ELSE. Every other need reaches the binding
// through its `ctx` (Q1-Q4) or its own package (Q5)."
//
// This module named `{ emitIntent, renderIntentChips }` from openDox's
// `./intent-binding.js`. That module is openDox's OWN optional-binding shim for
// the hosted intent feed (slice S2) — a class-A file this column does not own —
// and the tray already took its hosted context through `opts.intent`, so the
// emitter and the chip renderer travel the SAME way: `ctx.intent.emit` and
// `ctx.intent.renderChips`, supplied by the shell that starts the feed
// (`views/wheel.js`) and absent exactly where the feed is. A hosted tray whose
// shell supplied neither refuses IN THE PANEL, naming what was missing.

export const GATE_DISPOSE_ROUTE = "/actions/gate/dispose-possible";
export const GATE_PROPOSE_ROUTE = "/actions/gate/propose";

// THE FOUR ACTION-ROW VERB ROUTES, DECLARED AS LITERALS — RULED Q12
// (openxFactory#656 comment `5648065587`, Brett Heap, 2026-09-12): "a COMPUTED
// route is declared as its LITERALS: the dispose binding declares four
// `/actions/gate/<verb>` routes; no prefix semantics on the declaring side;
// assertion 2's grep sees them."
//
// WHAT THIS REPLACES. `mountWheelVerb`'s dispatch posted to
// `"/actions/gate/" + verb` (this file's :396 at openDox-code `cb343ae8`), with
// the four verbs supplied by its caller (`views/wheel.js`:140-146). Two things
// were wrong with that and only one of them was cosmetic. A binding's `routes:`
// is an OWNERSHIP CLAIM the registry checks (`view_extension.py`'s
// `_route_ownership_breach`), and a route nobody can write down is a claim
// nobody can check; and openDox-spec § 4.5 assertion 2 greps for route
// LITERALS, so a concatenation was invisible to the one instrument that
// measures this boundary — "the gap is in the INSTRUMENT, not in this file"
// (`docs/front-end-package-boundary.md` § 4.5 point 2, amendment #2, @
// `7d12428c`). They are a closed set the caller already spells out, so
// enumerating them keeps `routes` a declaration rather than a pattern language.
export const GATE_PROMOTE_TO_STAGING_ROUTE = "/actions/gate/promote-to-staging";
export const GATE_RESEARCH_BRIEF_ROUTE = "/actions/gate/research-brief";
export const GATE_DERIVE_POSSIBLES_ROUTE = "/actions/gate/derive-possibles";
export const GATE_DEMOTE_ROUTE = "/actions/gate/demote";

//: verb -> the literal route it posts to. The dispatch reads this map; a verb
//: with no declared route REFUSES rather than composing a path the binding
//: never claimed.
export const VERB_ROUTE = {
  "promote-to-staging": GATE_PROMOTE_TO_STAGING_ROUTE,
  "research-brief": GATE_RESEARCH_BRIEF_ROUTE,
  "derive-possibles": GATE_DERIVE_POSSIBLES_ROUTE,
  "demote": GATE_DEMOTE_ROUTE,
};

//: Every route this module calls, in one place, so the `gate.dispose` binding's
//: `routes:` tuple and this module cannot drift apart — the shape
//: `views/gate-lens.js` and `views/swb-session.js` already use.
export const DISPOSE_GATE_ROUTES = [
  GATE_DISPOSE_ROUTE,
  GATE_PROPOSE_ROUTE,
  GATE_PROMOTE_TO_STAGING_ROUTE,
  GATE_RESEARCH_BRIEF_ROUTE,
  GATE_DERIVE_POSSIBLES_ROUTE,
  GATE_DEMOTE_ROUTE,
];

// verdict -> { label, needsCitation }
const VERDICTS = [
  { outcome: "accepted", label: "✓ accept", title: "becomes first-class latent backlog (keeps ai-derived provenance)" },
  { outcome: "rejected", label: "✕ reject", title: "closes it with a required reason + citation; never silently re-derived" },
  { outcome: "deferred", label: "◔ defer", title: "parks it; the only re-disposable outcome" },
];

// The session-local applied overlay: possible id -> outcome. Snapshot stays
// deterministic; views consult this to decorate tiles until a regenerate.
const applied = new Map();

export function appliedOutcome(possibleId) {
  return applied.get(possibleId) || null;
}

export function gateCapable(caps) {
  return !!(caps && caps.actions && caps.actions.gate);
}

// ---- refusal panel (one per page; every refusal is visible, never silent) --
//
// THE HOST IS A DECLARED REGION NOW, NOT `document.body` — RULED Q8
// (openxFactory#656 comment `5648049748`, Brett Heap, 2026-09-12): "a fourth
// `shell` region, `page-overlay`, is the declared host for page-level panels
// (dispose.js's refusal panel); `document.body` is never a contract surface."
//
// This module used to append a singleton `aside.refusalpanel` straight to
// `document.body` — a mount point no region declared, which openXdox-spec
// `docs/gate-loop-view-contract.md` § 8 Q8 (@ `d73767b7`) names as "exactly the
// silence the REGIONS table exists to end, and a contributed column appending
// to the body is a collision nothing can refuse". The shell now builds the
// `page-overlay` host and hands it to this binding's entry
// (`mountRefusalPanel`), and every later `panelEntry` renders into it.
let panelHost = null;
let panel = null;

// THE BINDING'S ENTRY (`gate.dispose`), in the ONE mount signature RULED Q3.
// `host` is the shell's `page-overlay` element. Called once per render, before
// any view mounts, which is what makes the refusal panel available to every
// verb this column contributes.
export function mountRefusalPanel(host, snapshot, ctx) {
  if (!host) {
    throw new Error(
      "the gate column's refusal panel was mounted with no host: its region " +
      "`page-overlay` is a shell region, and the shell builds the host and " +
      "hands it over (RULED Q8, openxFactory#656 comment 5648049748)");
  }
  if (panel && panel.parentNode !== host) panel.remove();
  panelHost = host;
  return ensurePanel();
}

//: TEST SEAM — the host is page-lifetime state, so a probe can read and reset it.
export function refusalPanelHost() {
  return panelHost;
}

export function resetRefusalPanel() {
  if (panel) panel.remove();
  panel = null;
  panelHost = null;
}

function ensurePanel() {
  // REFUSAL, NOT A DEFAULT. Falling back to `document.body` here is precisely
  // what Q8 forbids, and a silent no-op would make a refused gate verb
  // invisible — the one thing this panel exists to prevent. A shell that
  // reaches a gate verb without having mounted this column's `page-overlay`
  // binding is mis-assembled, and says so.
  if (!panelHost) {
    throw new Error(
      "the gate column's refusal panel has no `page-overlay` host: this shell " +
      "reached a gate verb without mounting the `gate.dispose` binding. A " +
      "refusal that cannot be shown is a refusal that is silent, which is what " +
      "this panel exists to prevent (RULED Q8).");
  }
  if (panel && panelHost.contains(panel)) return panel;
  panel = el("aside", "refusalpanel");
  panel.hidden = true;
  const head = el("header", "refusalpanel-head");
  head.appendChild(el("span", "refusalpanel-title", "gate console"));
  const clear = el("button", "refusalpanel-clear", "clear");
  clear.type = "button";
  clear.addEventListener("click", () => {
    list.innerHTML = "";
    panel.hidden = true;
  });
  head.appendChild(clear);
  const list = el("ul", "refusalpanel-list");
  panel.append(head, list);
  panelHost.appendChild(panel);
  return panel;
}

// The panel's vocabulary. "ok"/"refused" are the LOCAL executing plane's two
// outcomes and are unchanged; the other three are the hosted plane's, because a
// submitted intent is neither applied nor refused yet and calling it either
// would be a lie the human acts on (design D1: the click is the decision, the
// apply is the custody step behind it).
//
// THE HOSTED PLANE HAS FOUR OUTCOMES, NOT TWO, and the panel must be able to
// SAY each of them. `emitIntent` normalizes the inbox's responses to
// pending | refused | stalled | error, and the last two are not refusals:
//   * "stalled" (HTTP 502) - the intent WAS recorded and the apply run could
//     not be started. Labelling it "refused" tells the human their decision was
//     rejected when in fact it is on file and undecided, so they re-submit a
//     decision that is already queued.
//   * "error" (401 / 429 / 400, or an unreachable inbox) - NOTHING was
//     recorded. Labelling that "refused" is the opposite lie: it reads as a
//     server verdict on the decision when the decision never arrived, so the
//     human does NOT re-submit the thing that never got sent.
const PANEL_KIND = {
  ok: { label: "applied", cls: "is-ok" },
  queued: { label: "queued", cls: "is-queued" },
  stalled: { label: "stalled", cls: "is-stalled" },
  error: { label: "not sent", cls: "is-error" },
  refused: { label: "refused", cls: "is-refused" },
};

// `emitIntent`/`readEmission` state -> the panel's word for it. Unknown states
// fall back to "refused", the conservative reading (something went wrong and
// the human must look), which is also what the whole map used to collapse to.
export const EMISSION_PANEL_KIND = {
  pending: "queued",
  refused: "refused",
  stalled: "stalled",
  error: "error",
};

export function panelEntry(kind, message) {
  const host = ensurePanel();
  const list = host.querySelector(".refusalpanel-list");
  const shape = PANEL_KIND[kind] || PANEL_KIND.refused;
  const item = el("li", "refusalpanel-item " + shape.cls);
  item.appendChild(el("span", "refusalpanel-kind", shape.label));
  item.appendChild(el("span", "refusalpanel-msg", message));
  list.insertBefore(item, list.firstChild);
  host.hidden = false;
}

// ---- the tray ---------------------------------------------------------------

async function post(route, body, fetcher) {
  const doFetch = fetcher || fetch;
  const response = await doFetch(route, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = { ok: false, message: "malformed response (HTTP " + response.status + ")" };
  }
  return payload;
}

// Collect reason + citation for a rejection. window.prompt keeps v1 honest
// and tiny; a refusal for an empty value is the engine's job, surfaced in
// the panel like every other refusal.
function collectRejection() {
  const reason = window.prompt("Rejection REASON (required — the durable why):", "");
  if (reason === null) return null; // cancelled
  const citation = window.prompt("Rejection CITATION (required — what the rejection cites):", "");
  if (citation === null) return null;
  return { reason, citation };
}

// Mount the tray for one pending possible into `container`. `opts.fetcher`
// and `opts.collect` are test seams; `opts.onApplied(outcome)` lets the view
// refresh its overlay.
//
// `opts.intent` present => THE HOSTED TRANSPORT (task 4.4). It carries
// `{ snapshotRev, rows, error, emit? }`: the revision the human is looking at
// (design D4's `snapshot_rev_seen`), the merged feed rows and error this
// render saw, and an optional emitter seam. The verdict buttons then submit a
// request instead of performing an act, and the chips for this target render
// beside them from the rows handed in — the tray subscribes to nothing and
// owns no timer, so a rail redraw can never leak one.
export function mountDisposeTray(container, possible, opts) {
  const o = opts || {};
  const intent = o.intent || null;
  const tray = el("span", "disposetray");
  for (const v of VERDICTS) {
    const btn = el("button", "disposebtn dispose-" + v.outcome, v.label);
    btn.type = "button";
    btn.title = intent
      ? v.title + " (hosted: this submits an intent the apply lane decides)"
      : v.title;
    btn.addEventListener("click", async (ev) => {
      ev.stopPropagation();
      const body = { possible_id: possible.id, outcome: v.outcome };
      if (v.outcome === "rejected") {
        const extra = (o.collect || collectRejection)();
        if (extra === null) return; // human cancelled
        body.reason = extra.reason;
        body.citation = extra.citation;
      }
      tray.classList.add("is-busy");
      if (intent) {
        // The kernel forbids a target key inside `args` (the validated target
        // is the only target — intent_apply_lane.shape_error), so the verb's
        // arguments travel WITHOUT `possible_id`.
        const { possible_id: _target, ...args } = body;
        // RULED counterpart Q6: the emitter is the shell's to supply. It was
        // `intent.emit || emitIntent` — the bundle import as the fallback —
        // and a fallback into a module this column may not import is a
        // refusal, not a default.
        if (typeof intent.emit !== "function") {
          tray.classList.remove("is-busy");
          panelEntry("refused", possible.id + " → dispose-possible " +
            v.outcome + ": the shell supplied no ctx.intent.emit — a " +
            "contributed binding reaches openDox's intent binding through ctx " +
            "(RULED counterpart Q6, openxFactory#656 comment 5649094228)");
          return;
        }
        const result = await intent.emit({
          verb: "dispose-possible",
          targetId: possible.id,
          args,
          snapshotRev: intent.snapshotRev,
          fetcher: o.fetcher,
        });
        tray.classList.remove("is-busy");
        panelEntry(EMISSION_PANEL_KIND[result.state] || "refused",
          possible.id + " → dispose-possible " + v.outcome + ": " +
          result.message);
        if (o.onEmitted) o.onEmitted(result);
        return;
      }
      const result = await post(GATE_DISPOSE_ROUTE, body, o.fetcher);
      tray.classList.remove("is-busy");
      if (result && result.ok) {
        applied.set(possible.id, result.outcome);
        panelEntry("ok", possible.id + " → " + result.outcome +
          " (regenerate the snapshot to fold it in)");
        if (o.onApplied) o.onApplied(result.outcome);
      } else {
        panelEntry("refused", (result && result.message) || "gate action failed");
      }
    });
    tray.appendChild(btn);
  }
  container.appendChild(tray);
  // RULED counterpart Q6: the chip renderer is the shell's too. No
  // `renderChips` is "this shell renders no chips" — the same silence a
  // plane with no feed already produced — and never an import of openDox's
  // `./intent-binding.js` from here.
  if (intent && typeof intent.renderChips === "function") {
    container.appendChild(intent.renderChips(el("span", "intentchips"),
      possible.id, intent.rows, intent.error));
  }
  return tray;
}

// ---- the propose button (add-propose-verb) ---------------------------------
// Mounts on a STAGED tile under the same capability gate as the tray: one click
// commissions proposal authoring for the topic (a recorded workflow-job
// dispatch — never authoring). Session-local overlay only; the snapshot stays
// deterministic.
//
// `opts.compact` is the IN-TILE mount (2026-07-25): the button now lives in the
// expanded tile's action row rather than the badge rail, so it takes smaller
// chrome (.dispose-intile) to fit. Behaviour is identical either way — same
// route, same panel entries, same disable-on-success.

// SESSION COMMISSIONS, keyed by (VERB, TARGET) — 011 add-wheel-action-verbs.
//
// This map used to be keyed by target id alone, which was unambiguous only
// while one verb per column existed. The possibles column now hosts TWO
// commission verbs, so a target-keyed flag would retire both when either fired
// — contradicting the (verb, target) duplicate rule the engine enforces
// (FR-027/FR-033). `propose` keeps its exact observable behaviour: it is simply
// the "propose" verb in the same store, and `commissionedWorkflow` still
// answers for it with the same signature.
//
// The VALUE is a per-verb marker, not strictly a workflow id: the three
// commissions store their workflow, and `demote` — which commissions nothing —
// stores a non-workflow marker recording that a plan was recorded this session
// (FR-033a). Session-local only: nothing is persisted, and a reload clears it.
const commissions = new Map();   // `${verb}\u0000${target}` -> marker

const DEMOTE_RECORDED = "demote:planned";

function commissionKey(verb, targetId) {
  return `${verb}\u0000${targetId}`;
}

export function commissionedVerb(verb, targetId) {
  return commissions.get(commissionKey(verb, targetId)) || null;
}

export function setCommission(verb, targetId, marker) {
  commissions.set(commissionKey(verb, targetId), marker);
}

/** TEST SEAM: the store is process-lifetime state, so probes reset it. */
export function resetSessionCommissions() {
  commissions.clear();
}

export function commissionedWorkflow(topicId) {
  return commissionedVerb("propose", topicId);
}

export function mountProposeButton(container, topic, opts) {
  const o = opts || {};
  const btn = el("button",
    "disposebtn dispose-propose" + (o.compact ? " dispose-intile" : ""),
    "\u25b6 draft proposal");
  btn.type = "button";
  btn.title = "commission proposal authoring for this staging topic " +
    "(recorded dispatch; the change lands for review + ratify)";
  btn.addEventListener("click", async (ev) => {
    ev.stopPropagation();
    btn.disabled = true;
    const result = await post(GATE_PROPOSE_ROUTE, { topic_id: topic.id }, o.fetcher);
    if (result && result.ok) {
      setCommission("propose", topic.id, result.workflow);
      panelEntry("ok", topic.id + " \u2192 proposal authoring commissioned (" +
        result.workflow + "); the change arrives for review + ratify");
      if (o.onApplied) o.onApplied(result.workflow);
    } else {
      btn.disabled = false;
      panelEntry("refused", (result && result.message) || "gate action failed");
    }
  });
  container.appendChild(btn);
  return btn;
}


// ---- the wheel action-row verbs (011 add-wheel-action-verbs) ---------------
//
// ONE mounter for all four. They differ only in their target field and in
// whether they collect a reason first, so a per-verb mounter would be four
// copies of the same transport with four chances to diverge.
//
// Every control is composed with `el`, which assigns `textContent` — so a
// refusal message can never introduce markup, and the DOM probe asserts that
// rather than trusting it.

const VERB_TARGET_FIELD = {
  "promote-to-staging": "possible_id",
  "research-brief": "possible_id",
  "derive-possibles": "cluster_id",
  "demote": "change_id",
};

const VERB_TITLE = {
  "promote-to-staging":
    "commission this ACCEPTED possible into a staging fragment " +
    "(recorded dispatch; the register is not touched)",
  "research-brief":
    "commission a pre-verdict evidence brief for this possible " +
    "(it informs the verdict and never makes it)",
  "derive-possibles":
    "commission a cluster-scoped run of the derivation lane " +
    "(candidates arrive pending_review)",
  "demote":
    "send this proposal back to staging: PLANS and RECORDS only — " +
    "the file moves stay a separate, human-run step",
};

/**
 * The in-page reason form (FR-006/FR-006a). Deliberately NOT `window.prompt`:
 * accessibility item 19 moved this codebase off blocking prompts, and adopting
 * one for new work would walk that back.
 *
 * Focus moves to the input on open and returns to `opener` on cancel or submit,
 * so a keyboard user is never stranded. An empty submit refocuses and dispatches
 * nothing; Escape cancels and dispatches nothing.
 */
function mountReasonForm(container, opener, onReason) {
  const form = el("div", "wheelreasonform");
  const input = el("input", "wheelreasoninput");
  input.type = "text";
  input.setAttribute("aria-label", "Reason this proposal goes back to staging");
  const close = () => { form.remove(); opener.disabled = false; opener.focus(); };
  const submit = () => {
    const reason = String(input.value || "").trim();
    if (!reason) { input.focus(); return; }   // nothing dispatched
    close();
    onReason(reason);
  };
  input.addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter" && ev.key !== "Escape") return;
    // STOP THE EVENT HERE. The wheel collapses an expanded tile on any Escape
    // that reaches it ("Escape collapses from anywhere the keypress can
    // reach", wheel.js) — so a bubbling Escape would cancel this form AND
    // destroy the action row it lives in, leaving the verb unoffered and no
    // control to return focus to. Found by driving the real dashboard; a
    // synthetic event aimed straight at this input has no ancestor to reach,
    // which is why the unit probe missed it.
    ev.preventDefault();
    ev.stopPropagation();
    if (ev.key === "Enter") submit(); else close();
  });
  const ok = el("button", "cbtn wheelreasonsubmit", "record demotion");
  ok.type = "button";
  ok.addEventListener("click", (ev) => { ev.stopPropagation(); submit(); });
  const cancel = el("button", "cbtn wheelreasoncancel", "cancel");
  cancel.type = "button";
  cancel.addEventListener("click", (ev) => { ev.stopPropagation(); close(); });
  form.append(input, ok, cancel);
  container.appendChild(form);
  input.focus();
  return form;
}

/**
 * Mount ONE action-row verb. `opts.verb` selects the route, the target field
 * and the title; `opts.collectReason` is a test seam standing in for the form.
 *
 * On success the verb is retired for this (verb, target) THIS SESSION and the
 * tile is decorated by the caller's `onApplied`. On refusal the control is
 * re-enabled and nothing is retired, so the human can correct and retry.
 */
export function mountWheelVerb(container, item, opts) {
  const o = opts || {};
  const verb = o.verb;
  const targetField = VERB_TARGET_FIELD[verb];
  const btn = el("button",
    "disposebtn dispose-" + verb + (o.compact === false ? "" : " dispose-intile"),
    o.label || verb);
  btn.type = "button";
  btn.title = VERB_TITLE[verb] || verb;

  const dispatch = async (extra) => {
    btn.disabled = true;
    const body = { [targetField]: item.id, ...(extra || {}) };
    if (o.topic) body.topic = o.topic;
    const route = VERB_ROUTE[verb];
    if (!route) {
      // A verb this binding never declared a route for. Refused, named, and
      // NOT composed: the binding's `routes:` is the ownership claim the
      // registry checks, and posting to a path outside it would be this
      // column reaching past its own declaration (RULED Q12).
      btn.disabled = false;
      panelEntry("refused", "no gate route is declared for verb " +
        JSON.stringify(verb) + "; this column declares " +
        DISPOSE_GATE_ROUTES.join(", "));
      return;
    }
    const result = await post(route, body, o.fetcher);
    if (result && result.ok) {
      // demote commissions no workflow, so the marker is per-verb, never a
      // required `workflow` field on the response (FR-033a).
      setCommission(verb, item.id, result.workflow || DEMOTE_RECORDED);
      const where = result.job || result.plan || result.record || "";
      panelEntry("ok", item.id + " → " + verb + " recorded" +
        (where ? " (" + where + ")" : ""));
      if (o.onApplied) o.onApplied(result.workflow || DEMOTE_RECORDED);
    } else {
      btn.disabled = false;                       // retry after correcting
      panelEntry("refused", (result && result.message) || "gate action failed");
    }
  };

  btn.addEventListener("click", async (ev) => {
    ev.stopPropagation();
    if (verb !== "demote") { await dispatch(); return; }
    // demote REQUIRES a typed reason, collected before anything is dispatched
    if (o.collectReason) {
      const reason = o.collectReason();
      if (!reason) return;                        // cancelled: nothing sent
      await dispatch({ reason });
      return;
    }
    btn.disabled = true;                          // the form owns the control now
    mountReasonForm(container, btn, (reason) => { dispatch({ reason }); });
  });

  container.appendChild(btn);
  return btn;
}
