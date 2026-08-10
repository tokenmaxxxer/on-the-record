---
status: proposed
files:
  - docs/issue-476/reports/architecture/survey-round2.md
  - docs/issue-476/reports/architecture/scout-brief-round2.md
  - docs/issue-476/proposals/architecture-round2.md
---

# Proposal -- issue #476 round 2 architecture: wiring candidate A

Phase 1 only, per role-handoff contract v3 s19. Builds on
`docs/issue-476/proposals/discovery-round2.md` (approved, candidate A
primary, H1-wiring + H1b pre-registered) and this round's own survey
(`docs/issue-476/reports/architecture/survey-round2.md`) and scout brief
(`docs/issue-476/reports/architecture/scout-brief-round2.md`), both linked
above by path. Scope: fix the design candidate A left open --
`claim_scan` call shape, matcher coverage, fail posture, kill switch, and
copy-avoidance -- as an ADR-shaped decision, not new code (phase 2, on
approval).

## Context

discovery-round2 named candidate A (a `PreToolUse` `Bash` hook on `gh pr
create`/`gh pr edit`, calling `claim_scan.scan_text()` inline, warn-only
first) as this round's build target, and registered a failure signature
naming the open design question explicitly: matcher coverage of call
*shapes*, not just the `gh` subcommand name, must be verified, not
assumed. The survey confirms this repo already has two competing
precedents for how a `PreToolUse` hook reaches a `gates/*.py` check --
`pr-preflight.sh` (irreversible act, ports the check inline, fails open)
and `record-claim-guard.sh` (cheap-retry write, imports `gates/` by
relative path, fails closed) -- and that this new hook's blast radius
(same chokepoint as `pr-preflight.sh`: `gh pr create`/`gh pr edit`, before
the PR exists or is changed) matches the former, not the latter. The
survey also confirms, by direct read, that `pr-preflight.sh`'s own
matcher already misses `gh api` PR-body writes and wrapper-script
indirection -- a live blind spot this new hook inherits unless the
proposal states otherwise.

## Decision

### New hook: `on-the-record/hooks/claim-scan-preflight.sh`

1. **Chokepoint and ordering.** Joins the existing `PreToolUse` ->
   `matcher: "Bash"` array in `hooks.json` as a new sibling entry,
   ordered immediately after `pr-preflight.sh` and before
   `spec-index-preflight.sh`/`impact-guard.sh`. Rationale: a command
   `pr-preflight.sh` already denies (wrong Closes/plain-`#n` trailer)
   never reaches this hook, so ordering after it avoids running a second
   regex extraction on a command about to be blocked anyway; ordering is
   not a correctness requirement (`hooks.json`'s hooks in one matcher
   group are independent, not short-circuiting on each other's exit
   code), only a cost minimization.
2. **Matcher shape -- inherits `pr-preflight.sh`'s regex verbatim this
   round, gap registered not silently fixed.** Same regex,
   `gh\s+pr\s+(create|edit)`, against the raw `Bash` command string, same
   `--body`/`--body-file` extraction. This is a deliberate, named
   inheritance of the gap the survey confirmed live (`gh api` PR-body
   writes, wrapper-script indirection) -- not an oversight. Per
   H1-wiring's own registered decision rule ("`wiring_coverage_rate` <
   95%: ... widen the matcher or add a second chokepoint ... before
   declaring wiring insufficient"), matcher-widening is the *pivot*
   action taken after the coverage metric is measured and found
   deficient, not a precondition to shipping candidate A at all --
   widening now, before any measurement, would be solving a problem the
   metric has not yet demonstrated at the wiring layer specifically
   (`pr-preflight.sh` carries the identical gap today and no one has
   registered evidence it is being exploited). The implementation
   record must cite this paragraph if it ships with a narrower or wider
   matcher than stated here.
3. **Check logic -- inline port of `claim_scan`'s two matching regexes
   (`CLAIM_RE`, `EVIDENCE_MARKER_RE`, and the code-fence adjacency
   check), not an import of `gates/claim_scan.py`.** Same precedent and
   same reasoning `pr-preflight.sh` already established for
   `gates/pr_reference.py`: a zero-install hook cannot assume `gates/` is
   on `sys.path` in a consumer repo, because `gates/` is this repo's own
   dev/CI tooling and sits outside the shipped `on-the-record/` plugin
   tree (`record-claim-guard.sh`'s relative-path resolution back to
   `gates/` only works in this repo's own dev checkout, not in a
   marketplace-installed consumer repo -- survey's "two competing
   precedents" section). This is not a second copy of check logic in the
   sense discovery's must-be #1 warns against (drift between two
   independently-maintained implementations of the same decision): it is
   the same qualified, already-accepted tradeoff this repo's own
   `pr-preflight.sh` and `spec-index-preflight.sh` already ship with --
   the single source of truth is `gates/claim_scan.py`'s regex constants,
   copied verbatim at write time, not reimplemented from the spec. The
   implementation record must show the ported regex text is copied
   character-for-character from `gates/claim_scan.py`, and any future
   change to `CLAIM_RE`/`EVIDENCE_MARKER_RE` must update both sites in
   the same commit -- named here so a future PR that edits one and not
   the other is a reviewable contract violation, not a silent drift.
   `reexecution_gate.run_reexecution()` is explicitly NOT ported or
   called from this hook (candidate B territory, deferred per
   discovery-round2's ITWWS section -- synchronous subprocess
   re-execution inside a `PreToolUse` hook is a separate latency decision
   this round does not make).
4. **Fail posture -- fails open on ambiguity, matching `pr-preflight.sh`,
   not `record-claim-guard.sh`.** Any parse failure, missing `python3`,
   non-matching command, absent `--body`/`--body-file`, unreadable
   body-file -> exit 0 (pass through). This is the act-time posture the
   survey's "two competing precedents" section assigns to this hook's
   blast radius, not the write-time cheap-retry posture
   `record-claim-guard.sh` uses.
5. **Warn-only per H1b, not deny -- a distinct third fail-posture axis
   from ambiguity-handling.** On a positive `claim_scan` hit (claim
   vocabulary present with no adjacent evidence marker/fence, exactly
   `scan_text`'s existing finding shape), this hook exits 0 (never
   blocks) and emits guidance two ways: `additionalContext` in the hook's
   JSON stdout (visible to the session inline, per Claude Code's
   `PreToolUse` hook output contract) and a mirrored message on stderr
   (visible even if the session does not surface `additionalContext`),
   both naming the specific claim line, the missing evidence-marker
   requirement, and the exact "flip to deny" condition below. This is
   deliberately not the same code path as step 4's ambiguity-driven
   `exit 0` -- ambiguity is "nothing to check," a positive hit under
   warn-mode is "found a violation, choosing not to block it yet" -- kept
   as two distinct branches in the implementation so the flip to deny
   (step 6) only has to change the positive-hit branch's exit code, not
   touch the ambiguity branches at all.
6. **Registered flip-to-deny rule, cited inline in the hook's own
   header comment, not left to institutional memory.** H1b's own
   decision rule, copied verbatim into the new hook's file header at
   implementation time: two-week warn-only period starting from the
   hook's first shipped commit date; flips to deny (step 5's positive-hit
   branch changes from `exit 0` + guidance to `exit 2` + the same
   guidance) if `warn_period_correction_rate` >= 60% measured over that
   window; if < 60%, the pivot is a `run.md` documentation fix to the
   evidence-marker guidance, not tightened enforcement, per H1b's own
   pivot branch. The two-week date and the 60% threshold are not
   renewable by a config edit alone -- an implementation or later PR that
   keeps `deny=false` past the registered date must cite this section
   and state why, per H1b's own gaming-resistance argument (no informally
   moved finish line).
7. **Kill switch -- `ORCHESTRATE_OFF`, checked first, before any
   parsing.** Same convention every ported guard in this repo already
   carries (survey's must-be #3, scout brief's must-be #3): `case
   "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac` as
   the hook's first executable line, verbatim shape from
   `pr-preflight.sh`.

## Consequences

- A fourth entry joins the `PreToolUse`/`Bash` array in `hooks.json`,
  adding one more regex-extraction pass to every `gh pr create`/`gh pr
  edit` call -- bounded cost (no subprocess beyond what
  `pr-preflight.sh` already runs for the same command), not a new
  latency class.
- The registered matcher-coverage gap (`gh api` PR-body writes,
  wrapper-script indirection) remains live and shared across
  `pr-preflight.sh` and this new hook simultaneously -- a session that
  already knew how to route around `pr-preflight.sh`'s Closes-trailer
  check via that gap gains no NEW route by this hook shipping, but also
  loses none of the OLD route. This is the deliberate scope boundary
  stated in Decision point 2, not an omission.
- The warn-mode-to-deny-mode flip (H1b) is a future required edit to this
  same hook file, on a fixed calendar date, gated on a measured rate --
  the implementation record and any later PR touching this hook's
  positive-hit branch must state which side of that flip it is on.
- `claim_scan.py`'s two regex constants now have two maintained copies
  (`gates/claim_scan.py`, this hook) -- an explicit, reviewable
  duplication cost accepted for the same zero-install reason
  `pr-preflight.sh` already accepted it for `pr_reference.check_body`,
  not a new precedent.

## Alternatives considered (rejected)

1. **Import `gates/claim_scan.py` via `record-claim-guard.sh`'s
   relative-path resolution pattern.** Rejected -- that pattern is a
   same-repo dev-checkout convenience (`gates/` sits beside
   `on-the-record/` only in this repo's own tree), not a zero-install
   guarantee for a marketplace-installed consumer plugin; using it here
   would silently break in exactly the deployment surface this
   mechanism's constraint requires it to reach.
2. **Widen the matcher now to cover `gh api` PR-body writes and
   wrapper-script indirection.** Rejected for this round -- discovery-
   round2's own decision rule treats matcher-widening as the pivot action
   taken after `wiring_coverage_rate` is measured and found deficient,
   not a precondition; widening now with no measurement would exceed
   this round's registered scope (discovery-round2's Out-of-scope
   section: "declaring round one's fabrication_survival_rate window
   closed or reset" and, by the same logic, declaring this round's own
   coverage question resolved before it is measured).
3. **Ship deny-mode immediately, skip H1b's warn period.** Rejected --
   H1b is already approved (discovery-round2, approved), and the
   survey's initial-friction constraint (thirty-four qualifying records
   scanned, only two show the evidence marker present) means immediate
   deny would block nearly every qualifying PR on day one, the exact
   operator-visible "tool breaking, not tool working" failure H1b exists
   to avoid.
4. **A brand-new `PreToolUse` matcher group instead of joining the
   existing `Bash` array.** Rejected -- `hooks.json`'s existing shape
   already supports multiple hooks per matcher as an ordered list; a
   second matcher group on the same tool name would be an unnecessary
   structural change with no behavioral difference.

## Files (write set)

- `docs/issue-476/reports/architecture/survey-round2.md` (this phase)
- `docs/issue-476/reports/architecture/scout-brief-round2.md` (this
  phase)
- `docs/issue-476/proposals/architecture-round2.md` (this phase)
- Phase 2, on approval: `on-the-record/hooks/claim-scan-preflight.sh`
  (new), `on-the-record/hooks/hooks.json` (new array entry),
  `docs/issue-476/reports/architecture.md` (phase-2 record, per contract
  waits for the Approve), `on-the-record/UNENFORCED-CLAUSES.md` (gates
  table row for `claim_scan.py` updated from CI-supplement to
  zero-install-hooked).

## How success will be judged

This proposal succeeds if, on `APPROVE issue-476/architecture`, phase 2
ships a hook that: fires on the same chokepoint as `pr-preflight.sh`
(verified by a constructed `gh pr create --body "..."` call carrying
claim vocabulary with no evidence marker, reaching the hook and producing
`additionalContext`/stderr guidance, not a silent pass); does not import
`gates/`; carries the `ORCHESTRATE_OFF` kill switch as its first
executable check; and states the H1b flip-to-deny date and threshold
verbatim in its own header comment. Discovery-round2's own
`wiring_coverage_rate` (>= 95%) and `warn_period_correction_rate` (>= 60%
over two weeks) remain the metrics this design is measured against
downstream, in step 4 (execution-observation) -- this architecture phase
is judged on whether the shipped hook is the mechanism those metrics can
actually be measured on, not on the metrics' outcome itself.
