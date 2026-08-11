---
status: proposed
files:
  - docs/issue-787/reports/product-discovery/current-state.md
  - docs/issue-787/reports/product-discovery/scout-brief.md
  - docs/issue-787/proposals/product-discovery.md
---

# Proposal — issue #787: plain-session auto-orchestration (root gap)

Phase 1 only, per this role's contract obligation and the issue's step-1 assignment
("product-discovery"). No hook code, no gate code — that is step 2 (implementation)'s job. Grounded
in `docs/issue-787/reports/product-discovery/current-state.md` and `scout-brief.md`; does not
re-derive either.

## Open question resolved: build a new mechanism, or fix the existing one?

The current-state survey found that `on-the-record/hooks/deliverable-guard.sh` already implements
the exact policy this issue asks for (deny an orchestrator-session deliverable write, redirect to
`spawn.py`) but fails to engage on the #776 baseline's target shape for two independent, narrow
reasons: a tree-pattern regex scoped to `on-the-record`'s own layout, and a precondition that the
target repo already carry `docs/specs/approvers.md`. Both are detection-scope bugs in an existing
mechanism, not evidence that no hooks-only mechanism can work. The proposal below is a targeted fix
to that existing gate, not a new mechanism.

## Candidates scored (RICE)

Reach/Impact scored against "plain plugin-installed sessions per week that receive a requirement
against an ordinary (non-self-hosted) target repo" — no direct log exists for this cadence yet in
this repo; scored qualitatively at the same order of magnitude as the #776 harness's own single-run
cadence (this is the harness this issue is measured against, so its cadence is the direct floor).

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Widen `deliverable-guard.sh`'s tree detection and drop/relax the `approvers.md` precondition; keep the existing deny-and-redirect message and `CLAUDE_ROLE`/kill-switch exemptions unchanged | 5 | 5 | 0.7 | 2 | 8.75 | **Keep — primary hypothesis (H1)** |
| 2 | New UserPromptSubmit classifier (requirement-shaped vs. chat) writing a session-scoped state file, plus a new PreToolUse gate reading it | 5 | 4 | 0.3 | 4 | 1.5 | Reject — duplicates `session-role-bind.sh`'s snapshot mechanism for no added benefit (scout-brief "skip"), and carries real false-positive risk on chat/questions that candidate 1's tool-call-gated design structurally avoids |
| 3 | Default-deny ALL `Write/Edit/MultiEdit/NotebookEdit` in an orchestrator session outside a small explicit allowlist (issue drafts, `approvers.md`, scratch), replacing the tree-allowlist logic entirely | 4 | 5 | 0.5 | 3 | 3.3 | Reject for this issue — correct direction long-term (matches the "installing this plugin IS the opt-in" default-on posture already stated in `directive.sh`), but effort/confidence tradeoff is worse than candidate 1 for closing THIS issue's specific #776 gap; noted as ITWWS follow-up |
| 4 | Also gate `Bash`-mediated file mutation (`sed -i`, heredoc redirection) in the same pass | 3 | 3 | 0.3 | 3 | 0.9 | Reject for this issue — current-state survey flags this as a real residual gap, but the #776 baseline's own denial point would already be `Edit`/`Write` calls (its 17 tool calls include direct `Edit`/`Write`, not `Bash`-mediated writes to the target); scoping this in now widens effort for a risk not evidenced by the baseline this issue is measured against |
| 5 | No change (status quo — rely on the directive text alone) | 5 | 1 | 0.9 | 0 | 4.5 | Reject — this is exactly the #776 baseline's already-measured FAIL; kept only as the fallback candidate 1 must degrade to if it fails its own hypothesis test |

Candidate 1 wins on RICE and on the discriminating-assumption test the current-state survey set up:
it directly closes the two named detection gaps with no new mechanism, preserving the existing
deny-and-redirect message, `CLAUDE_ROLE` exemption, and `ORCHESTRATE_OFF` kill switch byte-identical
for every session that mechanism already correctly serves.

## Pre-registered hypothesis package

Guardrail metric: `non_requirement_false_deny_count` — count of `deliverable-guard.sh` denies fired
during a non-requirement (pure chat/question) prompt turn in the #776 harness's empty-state variant,
named and non-empty at this same registration moment, distinct from the primary metric below. A win
on the primary while this guardrail is nonzero is a reduced-trust result: the empty-state acceptance
criterion ("a plain session given a NON-requirement prompt... does not spuriously enter
orchestration — asserted") is violated even if delegation now fires correctly on real requirements.

**H1 (primary).** If `deliverable-guard.sh`'s tree-pattern detection is widened to catch the #776
fixture's flat-package layout and its `approvers.md` precondition is relaxed so an ordinary,
non-self-hosted target repo is still recognized as guarded, then a re-run of the #776 harness against
the same fixture and the same requirement text produces at least one delegation-shaped event
(`spawn.py`/`Task`) before any direct deliverable write in the transcript — because today (per
current-state.md) the gate allows both touched files through unexamined by construction, so the
baseline delegation-event count on that exact scenario is 0.

- **Metric**: `pre_write_delegation_events` = count of `Task`/`spawn.py`-shaped tool-use events in
  the harness transcript that occur before the first successful `Write`/`Edit` to a deliverable path
  in the target repo, measured on the next #776 harness re-run against the same fixture and
  requirement, post-fix.
- **Threshold**: baseline is 0 (current-state.md's reading of `deliverable-guard.sh`'s two
  detection gaps and the #776 transcript's own zero-delegation result). Decision threshold:
  **`pre_write_delegation_events` >= 1** on the re-run.
- **Guardrail status at measurement**: `non_requirement_false_deny_count` must be **exactly 0** on
  the harness's empty-state variant run in the same pass, stated explicitly next to the primary
  metric's value, never implied.
- **Decision rule**: `pre_write_delegation_events` >= 1 AND `non_requirement_false_deny_count` = 0 ->
  **persist** (signals #1/#2/#5 re-scored on the same re-run). If the primary metric stays at 0
  (the widened gate still does not fire, e.g. because a third undiscovered detection gap exists) ->
  **pivot**: re-open the current-state survey's still-open question — whether `spawn.py` itself can
  complete a delegation in a target repo with no GitHub remote — before touching the gate's detection
  logic further. If `non_requirement_false_deny_count` is nonzero, regardless of the primary metric ->
  **kill immediately**: the widened detection is too aggressive and reverts, per the empty-state
  acceptance criterion's own "asserted, not assumed" bar.
- **Gaming-resistance argument**: the metric counts actual tool-use events in a captured transcript,
  the same evidence shape `docs/issue-776/reports/execution-observation.md` already used for signal
  #1 (`jq` count of `type=="assistant"` tool_use blocks) — not a self-report by the session under
  test.
- **Failure signature**: a widened gate that denies the write but the session still cannot complete
  `spawn.py` (no GitHub remote in the fixture, per current-state.md's still-open item) would show
  `pre_write_delegation_events` as an *attempted* spawn call without a completed one — named here so
  implementation checks for a stalled/errored `spawn.py` invocation specifically, not just its
  presence in the transcript.

## ITWWS (if this works we should ...)

If H1 persists, generalize candidate 3 (default-deny outside a small explicit allowlist, replacing
the tree-allowlist logic entirely) as the durable version of this fix — the widened tree regex this
proposal specs is itself still an allowlist-of-known-shapes and will have the same class of blind
spot against a third, still-undiscovered target-repo layout. Also action the current-state survey's
`Bash`-mediated-mutation gap (candidate 4) as a follow-up once real usage shows whether it is
observed in practice, not pre-emptively. Deferred to whichever role owns the gate surface next
(architecture/implementation), not actioned here.

## Spec-or-kill verdict

**SPEC.** Widening `deliverable-guard.sh`'s existing detection is viable and should be specified for
step 2 (implementation), scoped exactly as follows — this is the frozen contract step 2 inherits:

- **Tree detection**: replace the `src`/`test(s)`/`docs`-segment-only regex with a broader
  "does this path look like a source/test file in the target repo" classifier that also matches a
  flat top-level package layout (a `Write`/`Edit` target whose path is not itself a scratch/tmp
  path, not `docs/specs/approvers.md`, and not under a `.git`/plugin-cache directory) — implementation
  decides the exact classifier shape; the requirement this proposal fixes is that a flat package
  layout like the #776 fixture's must be caught, not any specific regex.
- **Target-repo precondition**: drop the `docs/specs/approvers.md`-presence requirement as the sole
  gate-activation signal; replace it with "any git repo root reachable from cwd, when this session is
  orchestrator-shaped (no bound `CLAUDE_ROLE`, matching `directive.sh`'s own existing exemption
  condition)" — i.e. the same scope `directive.sh` already delivers its directive to, so detection
  and delivery cover the identical session population. `docs/specs/approvers.md`'s presence stays a
  signal implementation MAY use to distinguish an `on-the-record`-hosted board repo from an ordinary
  target repo for message wording, but never as a precondition that silently disables the gate.
- **Unchanged, byte-identical**: the `CLAUDE_ROLE`/session-role-bind exemption, the `ORCHESTRATE_OFF`
  kill switch, the `docs/specs/approvers.md`-itself allowlist entry, the deny-and-redirect message
  shape, and the fail-closed-on-unparseable-payload behavior.
- **Empty state**: unaffected by construction (per current-state.md) — the gate only ever fires on an
  actual `Write`/`Edit`/`MultiEdit`/`NotebookEdit` call; a chat/question prompt issues no such call.
  Step 2 must still add the harness's empty-state variant run (`non_requirement_false_deny_count`) to
  the re-run this hypothesis package specifies, to assert this rather than assume it.
- **Kill condition, pre-committed**: if `non_requirement_false_deny_count` is ever nonzero during the
  re-run, the widened detection is killed immediately per the decision rule above, not iterated on.

## Known residual risk (after-proposal hunt)

`docs/issue-787/reports/product-discovery/hunt-after-proposal.md` (stance 0, reproduced) found that
H1 as specified inherits `deliverable-guard.sh`'s existing root-finding fallback unchanged:
`cwd = e.get("cwd") or os.getcwd()`. When a `PreToolUse` payload omits `cwd`, a relative `file_path`
resolves against the hook process's own unrelated working directory instead of the session's actual
one, the `.git` walk-up finds no root, and the gate silently ALLOWs a write that is genuinely inside
a guarded repo's source tree — a silent failure indistinguishable from a correct ALLOW on an
out-of-scope path. This is not a defect this proposal's own changes (the tree regex, the
`approvers.md` precondition) introduce — the fallback predates H1 — but H1's "any git repo root
reachable from cwd" precondition depends on that same root-finding code being reliable, and it is
not always reliable per the reproduction. Step 2 must additionally decide: fail closed when `cwd` is
missing/empty (matching this same file's own stated philosophy elsewhere — "a delivery failure on
stdin must not silently become an ALLOW"), or otherwise stop trusting `os.getcwd()` as a silent
substitute. Carried forward as a fixed requirement for step 2, not reopened as a new open question.

## Deployment-surface constraint carried forward

No mechanism is built in this phase. Architecture/implementation own: the exact classifier replacing
the tree regex, the exact target-repo-root detection replacing the `approvers.md` precondition, and
re-running the #776 harness (both the representative-requirement run and the empty-state
chat/question variant) to populate this hypothesis package's metric and guardrail. No CI, no new
skill/command surface — the fix stays entirely inside the existing `PreToolUse` hook, matching this
issue's own feasibility question ("feasibility of doing this with hooks alone, no CI, no skill
call"): **feasible** — the mechanism this issue needs already exists as a hook and the fix is a
detection-scope widening within that same hook, not a new enforcement layer.
