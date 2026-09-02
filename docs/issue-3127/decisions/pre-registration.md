---
issue: 3127
type: pre-registration
date_stamp: 2026-09-02
status: registered-before-data-collection
---

# issue-3127 — pre-registration (product-discovery-hypothesis-preregistration Step 4)

Written before `scripts/issue-3127/run_consumer_pair.py` is invoked in any
non-`--dry-run` mode. No pair has been run under this registration at the
time this file is written; `git log` on this branch and the absence of a
populated `docs/issue-3127/_assets/consumer-path-results.json` (still the
skeleton from the same commit as this file, `run_status: "not_executed"`) at
this commit are the check that `scripts/issue-3127/verify_preregistration.py`
runs mechanically.

## Theory (Step 1)

Issue #3053 measured a floor condition (bare `claude -p`, no orchestrator, no
`--skills`) and found the skills-on/skills-off blind-score margin
indistinguishable (+1, short of its own registered threshold). It also found
that under the real consumer path — `/on-the-record:run`'s orchestrator
naming skills via `spawn.py --skills` — the same corpus opened 4/4 at BM25
positions 0.12-0.16, against 0.36-0.83 in the floor condition: selection
quality itself differs by path, not just skill availability. We believe that
running both arms through the real `spawn.py --skills` path — same
orchestrator dispatch, same issue, same task, differing only in whether the
skill corpus resolves to anything when spawn.py mounts it — will surface an
effect the floor condition was structurally unable to see, because the floor
condition never exercised the selection/mounting machinery the product
actually uses.

## Hypotheses (Step 2)

- **H1 (manipulation check, gating precondition, not itself the R007
  hypothesis)**: in every completed skills-on arm run, the spawned session's
  init event and directive-composition byte count differ measurably from
  the paired skills-off arm's (i.e. the corpus actually mounted something
  beyond the identically-named `--skills` argument). Falsifiable: could
  return identical directive bytes across arms, meaning the toggle did not
  actually change what the spawned session received (a repeat of #3053's
  first, retracted zero-mount run).
- **H2 (the R007 quality hypothesis)**: across the registered pairs, the
  skills-on arm's blind deliverable score (scrubbed of skill-slug mentions
  before scoring, per #3053's leak finding) is higher than the skills-off
  arm's in a majority of pairs, with a combined margin large enough to read
  as directional rather than noise. Falsifiable: could come back tied,
  reversed, or mounted-with-no-score-movement.
- **H3 (the R007 efficiency hypothesis — the half of the operator's goal
  sentence no prior run measured)**: the skills-on arm needs fewer
  verification rounds per landed PR than the skills-off arm, and/or reaches
  a landed deliverable in less wall-clock, without a token-cost increase
  large enough to erase the efficiency gain. Falsifiable: skills-on could
  need the same or more rounds/wall-clock/tokens than skills-off, which the
  issue explicitly requires reporting as data, not as an excluded bad run.

## Pre-registration form (Step 3, rules 1-5)

| Field | Content |
|---|---|
| (a) Primary metric | H2's blind deliverable score margin (sum(skills-on) − sum(skills-off) across all registered pairs), scored by a rubric-based evaluator blind to arm identity, against each issue's own acceptance criteria |
| (b) Numeric threshold + decision rule (ship criterion, rule 2) | skills-on is called **better** if it scores higher in >=3 of the registered pairs AND the combined margin is >=3 points (same magnitude #3053 registered, for continuity across the floor-vs-consumer-path comparison); **worse** under the symmetric condition; **indistinguishable** otherwise (a tie in win-count, or any win count with margin in [-2, 2]) |
| (c) Guardrail metric + bounded degradation limit (rules 4-5) | wall-clock-to-landed-PR for the skills-on arm must not exceed the skills-off arm's by more than 50% combined across registered pairs, AND verification-round count for skills-on must not exceed skills-off's by more than 1 round combined. A primary-metric win recorded alongside a breached guardrail is reported as **a breach, not an unqualified win** (rule 6) — this is the mechanical form of the issue's own instruction that a same-or-more verification burden on the skills-on arm means "the layer is costing time without buying correctness" even if H2 reads as a win |
| (d) Secondary/diagnostic metrics (not gating, reported regardless) | token cost (total per session + directive-composition bytes alone), verification-round defect counts (not just round counts), BM25 selection position per skill mount (H1's manipulation-check evidence) |
| (e) Sample size / duration (rule 3, rules 9-10) | Registered at n = 2 pairs minimum for a first real run (matched to the two toy tasks already scaffolded in `docs/issue-3053/_assets/01-study-groups` and `docs/issue-3053/_assets/02-onboarding-experiment`'s task text, reused so pair identity is held constant across the floor-condition and consumer-path measurements), extensible to the full n=4 set `run_consumer_pair.py --plan` enumerates. One run per arm per pair, no repeated sampling, no interim peeking before all registered pairs complete. **At n=2-4 this is not a powered significance test** — the decision rule above is a directional read, stated as such in every verdict this harness emits, per experiment-trust's Twyman's-law framing (a large, surprising swing at this n is exactly the shape to distrust before trusting) |
| (f) Date stamp | 2026-09-02, before `run_consumer_pair.py` is invoked under this registration in any executing mode |

## Power statement (must-not clause: no null without stating what it could detect)

At n=2 pairs (1 skills-on + 1 skills-off run each), a binary win/loss/tie
read per pair has no meaningful statistical power — a two-outcome comparison
cannot distinguish a true small effect from noise at this sample size under
any reasonable significance convention. The registered decision rule above is
explicitly a **directional threshold**, not a significance test: it can only
ever report "met" or "not met" against the fixed ±3-point/50%-time/1-round
bars, never "no effect exists." A future run that returns "indistinguishable"
under this registration means the sample could not resolve an effect smaller
than the registered margin (3 points on this rubric's scale, roughly a
one-grade-band shift per pair) — it does not mean no such effect exists. If
this registration is extended to the full n=4 set, that remains true; a
change of decision rule after seeing partial results is itself a mid-flight
threshold change and is refused per rule 8 regardless of n.

## Deviations log

- 2026-09-02: this registration's harness (`run_consumer_pair.py`) was not
  invoked in any executing mode this session — see the accompanying record's
  "Rationale for deviations" section for why, and `docs/issue-3127/_assets/
  consumer-path-results.json`'s `run_status` field for the mechanical
  statement. This is a deviation from the issue's ask to run the
  measurement, not a change to the registered metric, threshold, decision
  rule, or sample size above — those remain fixed for whichever session
  executes this harness next.

## Amendment — H1 re-operationalization (2026-09-02)

Written after two real skills-on arms have run (PR #3172, study-companion
issues #19/#21, real phase-1 PRs #23/#24) and before any skills-off arm
has produced data. **No pair has been scored under this registration
(H2 has never been computed for any pair)**; the amendment below changes
only H1's *observation source*, not the decision rule, threshold, or
sample size in the Pre-registration form above, all of which remain
fixed as originally registered.

**What changed.** PR #3172 ran two real skills-on sessions and found,
with live evidence, that H1's original manipulation-check proxy
(`directive_composition_bytes`, sum of `<workspace>/.on-the-record/
directive/*.md`) cannot see a skills-on/skills-off difference for a
skill delivered via the runtime Skill-tool mechanism: both real
workspaces held only the 8 session-universal baseline policy files in
that directory, byte-identical regardless of which skill was mounted.
This is a construct-validity gap, not a measurement of the manipulation
H1 claims to gate — the metric could never fail even when the
manipulation genuinely had not happened, and could never pass when it
genuinely had.

Per consult (`experiment-trust`, `runs/consult-logs/
20260902T125610799701-948846.log`), H1 is re-operationalized to observe
whether the target skill was actually **invoked**, from a record the
spawned session's own model generation does not author. Four candidate
artifacts were compared for forgeability:

| Artifact | Written by | Records invocation (not just availability)? | Forgeability |
|---|---|---|---|
| Claude Code transcript's `tool_use` entries for the Skill tool (`~/.claude/projects/<hash>/<session-id>.jsonl`) | The CLI host binary, streaming the model's tool calls as they happen | Yes | Not model-authored directly, but the file sits under a path a live, unsandboxed session could in principle discover and append to via Bash (this machine runs no per-session filesystem sandbox — no container/chroot in spawn.py's dispatch path) |
| Hook-side PostToolUse trace | N/A | N/A | No PostToolUse hook in `on-the-record/hooks/hooks.json` fires on the Skill tool (matchers are `Write\|Edit\|MultiEdit\|Bash` only) — this candidate does not exist as a distinct artifact; it reduces to the transcript above |
| `runs/ledger.jsonl` | The orchestrator/parent process (`plumbing.ledger_write()`), called only after the child process has already terminated (`proc.wait()` returned), to a path outside the spawned session's own workspace | **No** — current schema (`skill`, `cost_usd`, `turns`, `rc`, `outcome`) records participation/outcome, not per-invocation skill usage | The write itself cannot be raced by a dead process, but extending it to carry invocation data would still have to derive that data from the same session-log artifact as the transcript, inheriting the same residual risk |
| Workspace's mounted-skill registration written by spawn.py (roster entry, `_skill_roster_fields()`, written before `Popen()`) | The parent process, strictly pre-session | **No** — records only that a skill *resolved* (was mounted/available), never that it was invoked | Temporally impossible to forge (written before the child process exists), but cannot answer the invocation question by construction |

**What was picked, and why.** `collect_skill_invocation()`
(`scripts/issue-3127/run_consumer_pair.py`) parses
`<workspace>.session.<ts>.<pid>.log` — spawn.py's own capture of the
spawned CLI's raw stdout stream, the same artifact
`scripts/measure_skill_invocation.py` already parses in production for
the identical signal (not new instrumentation this harness invented). A
`{"type":"tool_use","name":"Skill","input":{"skill":"<name>"}}` line in
that stream is serialized by the `claude` CLI binary itself the instant
the model's tool call happens — the model's own generation has no
ordinary code path that writes to this file; it can only cause a
genuine entry to appear by actually invoking the Skill tool.

**Honest residual risk (Twyman's-law discipline, not overclaiming
certainty).** This is not cryptographically unforgeable. This machine
runs every spawned session unsandboxed, as the same OS user, on a
filesystem this session's own directives explicitly told it to browse
(`$MUSTER_WORKSPACE_ROOT`) — confirmed live: `ls
~/.tokenmaxxxer/work/` lists every other session's own `.session.*.log`
files, including ones still in flight. A session that discovered its
own log path and deliberately appended a forged `tool_use`/`Skill` line
via Bash before exiting could, in principle, fool a later parse. None of
the four candidates above closes this; the mounted-skill registration
is temporally safe but useless for invocation, and the other three all
ultimately trace back to the same session-log content. What
distinguishes the chosen signal is not immunity but *naturalness*: a
model has no in-task reason to discover and tamper with its own
protocol stream, unlike `directive_composition_bytes`, which sat
directly in the model's own visible, editable workspace
(`.on-the-record/directive/*.md`) where touching it could happen
incidentally, without any adversarial intent. `directive_composition_bytes`
is kept in `compute_h1_manipulation()`'s output as a secondary
environment-parity diagnostic only — it no longer gates H1.

**Cross-check.** `collect_skill_invocation()` also returns `mounted` —
the session's own init-event plugin list, populated from the same
resolved-skill-sources spawn.py itself computes pre-session for the
roster (`_skill_roster_fields()`) — so a pair where the target skill was
invoked but never reported mounted (or mounted but never invoked) is
visible as `mounted_but_not_invoked` / `invoked_but_not_mounted`, an
internal-consistency signal alongside the pass/fail gate itself.

**Verified against PR #3172's real data.** The real skills-on session
logs for study-companion issues #19 and #21 still exist on this machine
(`~/.tokenmaxxxer/work/study-companion-issue-19-product-discovery-
hypothesis-preregistration-f8df81f9.session.20260902T212053.797342.log`
and the issue-21 equivalent). Running `collect_skill_invocation()`
against both real logs for skill
`product-discovery-hypothesis-preregistration` returns `invoked: true`
for both — the new H1 signal detects the real manipulation PR #3172's
own construct-validity finding showed `directive_composition_bytes`
could not. PR #3172's two skills-off arms never dispatched at all (a
separate, already-documented dispatch-blocking defect — a cross-family
skill-source tier conflict, issue #2055's own fail-closed check), so no
real off-arm invocation data exists to complete a full real pair under
the new H1; this is an unrelated, pre-existing limitation, not a gap in
the re-operationalization itself.

**Unchanged.** The decision rule (b), guardrail (c), secondary metrics
(d), sample size (e), and the power statement above all remain exactly
as registered on 2026-09-02 before this amendment. No pair has been
scored under either the old or the new H1 observation.

## Scope note (experiment-trust Step 1 — scope gate)

This is an offline, small-n (2-4) paired comparison with pre-assigned
conditions (one skills-on run and one skills-off run per task through the
same `spawn.py` invocation shape, not random assignment of live production
traffic to variants). `experiment-trust`'s SRM/A-A-validation machinery
(Steps 2-6) targets online controlled experiments with random unit
assignment at volume; applying chi-square/A-A checks to a 2-4-pair offline
comparison would be theater. The applicable machinery is this skill's
pre-registration discipline above, plus `experiment-trust`'s Twyman's-law
skepticism (Step 1) applied to any large, surprising swing this harness's
future run reports — that skepticism is why the decision rule above is
framed as directional, not as a significance claim, at this n.
