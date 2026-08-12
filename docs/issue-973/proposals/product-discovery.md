---
status: proposed
files:
  - docs/issue-973/reports/product-discovery/current-state.md
  - docs/issue-973/reports/product-discovery/scout-brief.md
  - docs/issue-973/proposals/product-discovery.md
---

# Proposal — issue #973: concurrent multi-agent judgment via official cross-session messaging

Phase 1 only. Pre-registers hypothesis, metric, threshold, and decision rule per this role's own
contract obligation. No gate code, no `panel_cmd()` implementation — that is architecture/
implementation's job, built on the write set specified below. Grounded in
`docs/issue-973/reports/product-discovery/current-state.md`; does not re-derive it.

## Framing carried forward from the issue

Issue #973 is the direct build-follow-on to `docs/issue-751/reports/defect-verification.md`
Finding 1: req#5's literal clause names concurrent, discussing multi-agent judgment, and today
nothing in this repo runs it — `consult_cmd()` is one caller, one session, one verdict
(canonical: spawn.py:4095-4162, read this session). The current-state survey's central finding is
that the harness-native fix is already half-built by accident: every session `spawn.py` launches
already runs as non-bare `claude -p` (canonical: spawn.py:4004-4006, spawn.py:4118-4120, read this
session), which per official docs means it already binds an inbox socket and already appears in
`ListAgents`. This proposal is scoped to closing the remaining gap — orchestration and recording —
not to inventing a new session-launch primitive.

## Open questions resolved

**1. What "panel" means, mechanically.** A new orchestration entry point (`panel_cmd()`, sibling to
`consult_cmd()` in `spawn.py`) spawns 2+ role sessions the same way `consult_cmd()` does today
(`role_settings()`/`plugin_dirs()` reuse — the current-state survey names this as the repo's
established anti-drift precedent), but with `crossSessionInbound=accept` added to each session's
settings and without the "answer once and exit" consult prompt. Each judge session receives the
seeded question plus its role's rulebook, is told its peer session's `ListAgents` name, and is
instructed to state a position, then use `SendMessage` to exchange at least one rebuttal round
before either session writes its verdict.

**2. What "on the record" requires.** Every position, every rebuttal, and the joint verdict is
written to `docs/issue-<n>/reports/panel/<question-slug>.md` — not left in the two sessions'
transcripts. Two ways to satisfy this, and the proposal picks the first as primary: (a) each judge
session itself appends its own turn to the panel file as it sends/receives each `SendMessage` (the
file becomes the shared record, `SendMessage` is the live discussion channel, the file is the
audit trail); (b) as a fallback if a judge session cannot reliably write mid-conversation, the
orchestrating `panel_cmd()` call polls both sessions' final JSON outputs (position + rebuttal +
verdict, same `{"answer":..., "confidence":..., "caveats":[...]}` shape `consult_cmd()`'s
`_parse_consult_verdict()` already parses) and writes the combined transcript itself once both
sessions exit. (a) is closer to req#2's "fully on the record" bar since it captures the live
exchange as it happens rather than reconstructing it after both sessions have already exited;
architecture/implementation decides between them against what `SendMessage` delivery timing
actually allows once built.

**3. What "default-on, plugin-only, no explicit skill call" (req#7) means for this mechanism.**
`panel_cmd()` is a `spawn.py` orchestration function, not a skill — the same shape `consult_cmd()`
already has. Whatever calls into it (a deviation-loop step, a contested-judgment hook) triggers it
automatically when the question is flagged contested/high-stakes, with no operator or session
having to invoke a named skill. Scoping this precisely (which callers, which trigger condition)
is deferred to architecture/implementation; this proposal fixes only that the entry point itself
is a plugin-side function call, never a skill invocation.

**4. What the degradation path is, precisely.** If `crossSessionInbound=accept` sessions cannot be
addressed via `ListAgents` (environment lacks socket support), or a `SendMessage` round-trip does
not land within the 5-minute hold window (canonical: gh issue view 751 --comments, read this
session), `panel_cmd()` falls back to calling `consult_cmd()` sequentially against each judge role
with the same question, and the panel record explicitly states `degraded: sequential-consult —
<reason>` at the top of the same `docs/issue-<n>/reports/panel/<question-slug>.md` file a live
panel would have populated — never a silent fallback with no marker, which is the exact failure
class the current-state survey names (a mechanism believed to serve req#5 that in practice does
not).

## Candidates scored (RICE)

Reach/Impact scored against "contested or high-stakes judgment calls the orchestrator currently
accepts from a single unchallenged session, per week" — no direct log exists yet for this
specific cadence; scored qualitatively against `consult_cmd()`'s own trace log
(`_append_consult_trace`, canonical: spawn.py:4080-4090, read this session) as the closest existing
proxy for consult-call volume.

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | `panel_cmd()`: 2+ non-bare `claude -p` judge sessions with `crossSessionInbound=accept`, live `SendMessage` exchange, position/rebuttal/verdict written to `docs/issue-<n>/reports/panel/`, sequential-consult degradation with an explicit marker | 4 | 5 | 0.6 | 3 | 4.0 | **Keep — primary hypothesis (H1)** |
| 2 | Agent Teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, lead+teammate mutual messaging) | 3 | 5 | 0.2 | 3 | 3.3 | Reject — experimental flag, current-state survey's own official-docs citation rules this out against req#7's default-on bar; a default-on plugin cannot depend on an experimental harness feature |
| 3 | Shared-file "mailbox" only (no live `SendMessage`; each session polls a shared file for the other's position) as the *primary* mechanism, not just the degradation path | 3 | 3 | 0.5 | 2 | 4.5 | Reject as primary, adopted as component: this is exactly what the current-state survey's candidate (c) proposes as the *degradation* path, but as the primary path it does not serve req#5's literal "discussing... simultaneously" clause — polling a file is not live discussion, and the harness already supplies a live primitive that candidate 1 uses instead |
| 4 | Single `consult_cmd()` call with a longer, more elaborate prompt asking the one session to "argue both sides" | 5 | 2 | 0.7 | 1 | 7.0 | Reject — highest RICE arithmetic but does not address req#5 at all: one session role-playing disagreement with itself is not "1+ agents... discussing," it is the exact naming-coincidence failure the current-state survey's Finding 1 basis already names for `panel-unanimous-support-v1` |
| 5 | No mechanism (status quo) | 5 | 1 | 0.9 | 0 | 4.5 | Reject — leaves req#5's literal clause unserved, which is the entire reason this issue exists; kept only as the fallback state before candidate 1 ships |

Candidate 1 wins despite candidate 4's higher RICE arithmetic and candidate 3's higher RICE-as-primary
arithmetic, for the same reason `docs/issue-659/proposals/product-discovery.md`'s own table states:
RICE is a screen here, not the verdict — a lower-effort candidate that does not actually run
concurrent multi-agent discussion reproduces the exact failure this issue exists to close.

## Pre-registered hypothesis package

Guardrail metric: `panel_record_incompleteness_rate`, named and non-empty at this same registration
moment, distinct from the primary metric below — a panel mechanism that ships and gets used, but
silently drops a position/rebuttal/verdict from the repo record on some fraction of runs, is a
reduced-trust result, not a win, since req#2's "fully on the record" bar is exactly what would be
quietly violated.

**H1 (primary).** If 2+ role sessions are spawned as message-capable (`crossSessionInbound=accept`,
non-bare `claude -p`) processes that exchange at least one position and one rebuttal via the
harness's own official `SendMessage`/`ListAgents`, with every position/rebuttal/verdict written to
`docs/issue-<n>/reports/panel/`, then contested/high-stakes judgments carry a recorded,
cross-examined basis instead of a single unchallenged opinion — because today (per current-state.md)
zero such judgments exist; the baseline is 0% by construction.

- **Metric**: `panel_invocation_success_rate` = (panel invocations that complete a live
  position+rebuttal+verdict exchange, on the record) / (total panel invocations attempted),
  measured over the fixture's first 20 invocations after `panel_cmd()` ships, seeded by
  `harness/fixture-concurrent-judgment/test_panel.py` per the issue's own acceptance criterion.
  Secondary observation metric: `mean_panel_latency_seconds` (wall-clock from invocation to joint
  verdict), sampled over the same window — reported alongside, not substituted for, the primary
  ratio.
- **Threshold**: baseline is 0% (current-state.md: no live concurrent-discussion mechanism exists
  today). Decision threshold: **`panel_invocation_success_rate` ≥ 70%** over the window — a majority
  of invocations complete a genuine live exchange rather than falling through to the sequential
  degradation path, since a mechanism that degrades on most invocations has not actually delivered
  req#5's live-discussion clause even though it has delivered *some* on-record judgment.
- **Guardrail status at measurement**: `panel_record_incompleteness_rate` (panel invocations whose
  `docs/issue-<n>/reports/panel/` file is missing a position, a rebuttal, or the joint verdict that
  the session transcripts show actually occurred — detectable by comparing the panel record against
  each judge session's own JSON output) must stay **0%** over the same window, stated explicitly
  next to the primary metric's value, never implied. 0%, not a nonzero tolerance, because a
  mechanism whose entire purpose is "fully on the record" (req#2) cannot itself have an acceptable
  rate of records that silently drop part of the discussion.
- **Decision rule**: `panel_invocation_success_rate` ≥ 70% AND `panel_record_incompleteness_rate` =
  0% → **go**. If the primary metric falls short but the guardrail holds → **pivot**: investigate
  whether the shortfall is delivery-timing (messages arriving after the 5-minute hold expires) vs.
  addressability (sessions not appearing in `ListAgents` as expected) and adjust `panel_cmd()`'s
  session-launch parameters, never loosen the recording requirement to compensate. If the guardrail
  exceeds 0% regardless of the primary metric → **kill-and-redesign**: candidate (a) vs (b) from
  Open Question 2 above is re-examined, since an incomplete record is exactly the failure mode
  choosing the wrong write-path (session-writes-live vs. orchestrator-reconstructs-after-exit) would
  produce.
- **Gaming-resistance argument**: `panel_invocation_success_rate` and
  `panel_record_incompleteness_rate` are both computed by comparing the panel record file against
  each judge session's own raw JSON output — not asserted by the orchestrator that ran the panel, the
  same anti-self-report shape `docs/issue-659/proposals/product-discovery.md`'s H1 already
  registered and the current-state survey's own precedent (`_append_consult_trace`, "no traceless
  consults") establishes for this mechanism's nearest sibling.
- **Failure signature**: fails quietly if a judge session's `SendMessage` is delivered but arrives
  after that session has already exited (the 5-minute hold expires with the receiving session gone)
  — the sender would show a rebuttal sent, the panel record would show no corresponding reply, and
  naive success-rate computation from the sender's side alone would miss this. Named here so
  architecture/implementation is on notice that success measurement must read both sessions'
  outcomes, not just the initiating session's.

## ITWWS (if this works we should ...)

If H1 proves out at the ≥70%/0%-guardrail thresholds, extend `panel_cmd()` beyond 2 judges to N
judges for higher-stakes questions (majority/plurality verdict instead of pairwise), and wire it as
the automatic escalation path for `docs/specs/northpole.md`'s "delegated-judgment evaluation ->
escalate" outcome (seen live in issue #751's own session-end trace: "Verdict: PR #? -> escalate
(depth or impact axis did not clear)") rather than escalation defaulting to a single human
round-trip. Deferred to whichever role owns the escalation-routing surface next, not actioned here.

## Deployment-surface constraint carried forward

No mechanism is built in this phase. Architecture/implementation own: `panel_cmd()`'s exact
implementation in `spawn.py` (session-launch parameters, prompt text, `SendMessage`/`ListAgents`
call sequencing); the choice between Open Question 2's candidates (a) live self-writing sessions vs.
(b) orchestrator-reconstructed transcript; the `docs/issue-<n>/reports/panel/` record schema; the
trigger condition that makes this default-on without an explicit skill call (req#7); and
`harness/fixture-concurrent-judgment/test_panel.py`, the seeded two-judge fixture the issue's own
acceptance criterion names. No GitHub Actions — matches this repo's own standing 2026-08-08
constraint (#566) that enforcement lives in deployed hooks, not CI.

## Degradation (restated from current-state.md, binding on architecture/implementation)

Right now no live concurrent-judgment mechanism exists at all — every judgment is a single
`consult_cmd()` call to one session. Per the issue's own acceptance criterion ("with messaging
unavailable, the panel degrades to sequential consults and records that it did"), `panel_cmd()`
must fall back to calling `consult_cmd()` against each judge role in sequence when live messaging
is unavailable, and the resulting `docs/issue-<n>/reports/panel/` file must state the degradation
and its reason explicitly — never presenting a sequential fallback as if it were a live exchange.
The pre-registered measurement window does not open until `panel_cmd()` ships and
`harness/fixture-concurrent-judgment/test_panel.py` produces at least 20 invocations' worth of
trail to measure against; if that window is unfilled at the execution-observation step, the effect
is deferred with that reason, per this role's own contract obligation.
