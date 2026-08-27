---
issue: 2628
role: adversarial-review+silent-failure-audit-f8365dc9
author: adversarial-review+silent-failure-audit-f8365dc9
skills: adversarial-review (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
code_under_review:
  - gates/spawn_on_pr.py
  - gates/test_spawn_on_pr.py
  - test/test_verifies_subject_scaffold.py
type: review
breaking: false
verdict: pass
verifies_subject: true
loop_state: terminal
upstream:
  - path: PR #2640 (issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41, not merged to this branch)
    sha: 686237cdf8f180d84de55c3e2eaf4d882875a87a
---

# issue-2628 — adversarial-review+silent-failure-audit-f8365dc9 record

## What was done

Independent re-verification of PR #2640 against issue #2628's Acceptance
section, run in two fresh detached-HEAD worktrees (`origin/main` at
`2cb0bab2`, PR branch tip at `686237cd`) so nothing was taken on the PR
body's or the implementation record's word — every check below was
re-executed from scratch in this session.

**Acceptance bullet 1 — "no closed set of names decides which sessions are
auto-spawned."** Present.
canonical: `grep -rn 'AUTO_SPAWN_ROLES' --include=*.py .` in the `origin/main`
worktree — result: 8 hits (`gates/spawn_on_pr.py:50,140,171,214,231,296,308,626`,
`test/test_verifies_subject_scaffold.py:51`).
canonical: same command in the PR-branch worktree — result: 0 hits, exit 1.

**Acceptance bullet 2 — "the obligation AUTO_SPAWN_ROLES served still
happens, demonstrated end-to-end."** Present.
derived: ad hoc script run against the real, unmodified
`verification_deficit()`/`spawn_missing_for_pr()` in the PR-branch worktree
(only `gh`/`git` boundary functions monkeypatched) — result:
```
deficit 0 records: 2
deficit 1 record (other author): 1
deficit 1 record (SELF author, must not count): 2
deficit 2 records: 0
dry-run pairs for deficit=2: [('issue-2628', 'independent-verification-1'), ('issue-2628', 'independent-verification-2')]
```
Matches the record's pasted numbers exactly — independently re-derived, not
copied.

**Acceptance bullet 3 — "checked with `scripts/audit_removal_claim.py`
before the PR is opened, output in the record."** Present.
derived: `python3 scripts/audit_removal_claim.py /tmp/audit_claim_2628_repro_indep.json --root .`
(same claim JSON the record used: `removed_names: [AUTO_SPAWN_ROLES,
applicable_record_kinds]`, `member_samples: [execution-observation,
conformance-review]`), run fresh in the PR-branch worktree after clearing
stray `__pycache__` — result: `verdict: RESHAPE_DETECTED`, q2 colocated
files `['./.claude-plugin/marketplace.json', './directive_assembly.py',
'./gates/merge_gate.py', './gates/spawn_on_approve.py',
'./on-the-record/commands/run.md', './on-the-record/directive/spawn-and-board.md',
'./on-the-record/hooks/pr-base-guard.sh', './spawn.py']` — matches the
record's own tool output exactly (an initial run of mine additionally
surfaced `__pycache__/*.pyc` hits absent from the record's run; these are
stale bytecode mirrors of already-classified `.py` sources, not a
discrepancy in the code — removed and re-run for a clean comparison).
Hand-reclassified each hit myself rather than trusting the record's
classification:
```
gates/merge_gate.py:123,327 — docstring/comment examples, no live dict/tuple
gates/spawn_on_approve.py:8 — background-context comment
directive_assembly.py:273,582,692 — anti-pattern warning + unrelated comments
spawn.py:9,740,1548,3673 — CLI help text + LEGACY dict (0 usages anywhere
  else in spawn.py, per `grep -n '\bLEGACY\b' spawn.py` — dead, unrelated
  to spawn_on_pr's auto-spawn decision, out of this issue's Non-goals scope)
```
All false positives — none is a live dict/tuple/dispatch that gates
auto-spawn identity. Independent classification agrees with the record's.
`grep -rn 'spawn_on_pr.py.*unpark\|spawn_on_pr.py.*clear-ceiling\|unpark.*--role\|clear-ceiling.*--role' --include=*.py --include=*.sh --include=*.md .`
outside `docs/issue-2628/` found only historical record prose (issue #1476,
#2607 records), never a live `.py`/`.sh` caller passing `--role` — confirms
the record's "no such caller found" claim and the honest `breaking: true`
frontmatter (main's `unpark_p.add_argument("--role", required=True, ...)`
at `gates/spawn_on_pr.py:804` is genuinely gone on the PR branch, per
`grep -n '"--role"' gates/spawn_on_pr.py` in both worktrees).

**Load-bearing claim 1 — "`verification_deficit()` mirrors
`merge_gate.py::required_verification_missing()` exactly."** PLAUSIBLE but
imprecise as stated. Read both in full
(`gates/spawn_on_pr.py:160-174`, `gates/merge_gate.py:178-213`). The core
formula is identical: `max(0, REQUIRED_INDEPENDENT_VERIFICATIONS -
verifying_record_count(subject_board, subject_author))`. They CAN
disagree, however: `required_verification_missing(root, subject, repo, pr)`
has an extra early-return-0 branch (`_own_pr_supplies_verification()`,
`gates/merge_gate.py:117-175`, pre-existing on `main` before this PR, per
`grep -n '_own_pr_supplies_verification' gates/merge_gate.py` in the
`origin/main` worktree) that exempts a PR under merge-gate evaluation from
the count when that PR's own branch tip (not yet landed) already supplies
a qualifying `verifies_subject: true` record. `verification_deficit(subject_board,
subject_author)` takes no `repo`/`pr` parameters and structurally can never
apply that exemption — it only ever sees landed board records. So for the
one PR that is itself the record supplying the missing verification,
`required_verification_missing()` can return 0 while `verification_deficit()`
computed on the same `subject_board` at the same moment still returns > 0.
canonical: PR #2640's own implementation record (not present on this
branch; read via `git show origin/issue-2628/architecture-interface-
contract-shape+silent-failure-audit-c4b1fc41:docs/issue-2628/reports/
architecture-interface-contract-shape+silent-failure-audit-c4b1fc41.md`),
section "Why", paragraph "Why `verification_deficit()` mirrors
`merge_gate.required_verification_missing()` instead of importing it
directly" — the record itself discloses and reasons about exactly this
divergence, calling `verification_deficit()` "the smaller, count-only
subset both callers actually share." This is not a regression introduced
by this PR — the same asymmetry already existed on `main` (the retired
`applicable_record_kinds()`/`missing_verification()` also took no
`repo`/`pr` parameters, per `grep -n 'def missing_verification\|def
applicable_record_kinds' gates/spawn_on_pr.py` in the `origin/main`
worktree). The PR body's one-line "mirrors...exactly" phrasing overstates
what the full record itself correctly qualifies. Finding, but low
severity: disclosed, pre-existing, and does not affect either function's
actual call sites (spawn_on_pr never evaluates one specific candidate PR
the way merge_gate does).

**Load-bearing claim 2 — respawn-ceiling defeat found and fixed.**
Present, independently reproduced both directions. The "first pass" commit
(seed `eb61de56`, cited in the hunt record) never landed on the PR branch
(only the fixed version did — `git log --oneline` in the PR-branch
worktree shows exactly 2 commits, both post-fix), so I could not check it
out directly; instead I re-derived the defect's shape from the hunt
record's own description (positional `range(1, deficit+1)` slot numbers,
`park_state` keyed `f"{subject}/{role}"`) and independently verified the
CURRENT (fixed) code no longer exhibits it, using a scenario analogous to
the hunt's own repro:
derived: ad hoc script, PR-branch worktree, `max_respawn_attempts=4`,
subject seeded with cumulative `attempts: 3`, deficit 1 for two
consecutive ticks — result: tick 1 spawns `independent-verification-4`
(`attempts` → 4), tick 2 correctly prints `CEILING HIT` and spawns nothing
(`ceiling_hit: True`, `attempts` stays 4) — the ceiling holds.
Also ran the PR's own regression test in isolation:
derived: `python3 -m pytest gates/test_spawn_on_pr.py::test_sibling_slot_resolving_does_not_reset_ceiling_progress -q` — result: `1 passed`.
This test (`gates/test_spawn_on_pr.py:270-320`) directly encodes the hunt's
exact scenario (deficit 2 → one sibling slot resolves → deficit 1, three
ticks) and asserts slot numbers never repeat (`independent-verification-1,
2` then `3`, never re-issuing `1`) and the ceiling trips at the subject's
true cumulative count (3), not a reset one. Full suite:
derived: `python3 -m pytest gates/test_spawn_on_pr.py test/test_verifies_subject_scaffold.py test/test_watchdog_heartbeat_noise.py test/test_merge_gate_record_kind.py -q` — result: `43 passed`.
Matches the PR body's claimed count.

**Capability-change honesty.** Present.
canonical: `gates/spawn_on_pr.py:140-176` (`applicable_record_kinds()`) in
the `origin/main` worktree — matches each subject's missing entries
against the fixed `AUTO_SPAWN_ROLES = ("execution-observation",
"conformance-review")` tuple and invites up to those two specific named
roles. On the PR branch, the same board states now produce
`deficit`-many generic `independent-verification-<n>` invitations with no
skill/expertise identity attached (demonstrated end-to-end above: 0→2
generic, 1→1 generic, 2→0). What stops working, stated plainly: the
auto-spawn tick can no longer target a specific kind of expertise (e.g.
conformance-review-style vs. execution-observation-style) by name — it
invites N generic "read the PR and verify independently" sessions and
relies on the spawned session's own task-text-driven skill matching.
`REQUIRED_INDEPENDENT_VERIFICATIONS` itself is unchanged (`= 2` in both
worktrees, per `grep -n 'REQUIRED_INDEPENDENT_VERIFICATIONS = '
gates/spawn_on_pr.py` run against both) — the pre-merge
independent-verification obligation was not weakened as a side effect.

## Why

canonical: `gh issue view 2628`, this session — the issue's own "must not"
clause (renaming/relocating/sharding a closed set again, or weakening
`REQUIRED_INDEPENDENT_VERIFICATIONS` as a side effect) is the exact
failure mode #2615 and #2625 already hit. This review's task was to apply
the same test the removal audit (#2626/#2627) applied to the original
claim, not accept a second self-report of "0 hits" at face value — hence
every check above was re-derived from a fresh worktree against both
`origin/main` and the PR branch tip, rather than read from the PR body or
the implementation record's pasted output, per this review task's
explicit instruction.

## What did not work

derived: my first `python3 scripts/audit_removal_claim.py ... --root .`
run in the PR-branch worktree surfaced extra `__pycache__/*.pyc` hits
(`./__pycache__/directive_assembly.cpython-310.pyc`,
`./gates/__pycache__/spawn_on_approve.cpython-310.pyc`) not present in the
implementation record's own run — traced these to stale bytecode left
over from this session's own earlier `pytest` invocation in that worktree,
not a code discrepancy (each `.pyc` mirrors a `.py` source already
classified false-positive above). Cleared with `rm -rf __pycache__
gates/__pycache__ test/__pycache__` and re-ran; the second run's output
matched the record's exactly. No re-derivation of any Acceptance bullet
was invalidated by this — the classification was identical either way.

## Upstream basis

canonical: `git rev-parse origin/issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41 origin/main HEAD`, this session — result: PR branch tip `686237cdf8f180d84de55c3e2eaf4d882875a87a`, `origin/main` `2cb0bab2cd4c3cd376af29b838bd81e2635b0e5f`.

- PR #2640 (`issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41`,
  not merged to this branch), branch tip
  `686237cdf8f180d84de55c3e2eaf4d882875a87a` — the subject of this review.
- `origin/main` at `2cb0bab2cd4c3cd376af29b838bd81e2635b0e5f` — the
  pre-PR baseline used for every "before" comparison above.
- PR #2640's own implementation record and hunt record (both landed in
  the same PR-branch commit `563afffc`/`686237cd`, read via `git show
  origin/issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41:<path>`
  since neither is on this branch) — read and independently re-derived
  against, never copied from.

## Open findings

1. PR body's one-line claim "`verification_deficit()` mirrors
   `merge_gate.py::required_verification_missing()` exactly" is imprecise
   — the two functions can disagree in the narrow self-referential-PR
   case (`_own_pr_supplies_verification()` exemption, pre-existing on
   `main`, structurally unreachable from `verification_deficit()`'s
   signature). Already disclosed and reasoned about in PR #2640's own
   record "Why" section (see "Load-bearing claim 1" above), so not a
   hidden defect — resolution path is tightening the PR body's own
   summary line to match the record's more careful phrasing; no code
   change needed, not a re-open of this issue.

## Next steps

None. `loop_state: terminal`.

amendments-reconciled: issuecomment-5436750956 (JiwonJung94, 2026-08-27T08:59:31Z)
— posted after this review session started. canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5436750956 --jq '.body'`,
this session — live evidence that on `origin/main`'s still-deployed
`AUTO_SPAWN_ROLES` path, `python3 spawn.py --skills conformance-review
"<task>" --issue 2628` fails outright (`--skills: 모르는 스킬
conformance-review`) because `conformance-review` stopped being an
installed skill once the record-kind axis was retired, while the
heartbeat kept printing `missing=['execution-observation',
'conformance-review']` regardless — the closed set had gone stale against
the very names it invited, and nothing in a roster can notice that; a
count (PR #2640's `verification_deficit()`) has nothing analogous to go
stale against. This corroborates rather than contradicts every verdict
above — it is additional evidence for the same fix, not a new claim to
adjudicate — so no verdict in this record changes.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; this review session
is itself the structurally independent evaluator this skill describes —
re-derived every acceptance check and both load-bearing claims from a
fresh worktree rather than trusting the PR body or the implementation
record's pasted output, per the skill's core mechanism (session
separation, not "be critical" prompting).

skill-verdict: silent-failure-audit — applied: invoked;
derived: ad hoc reproduction scripts run against the real
`spawn_missing_for_pr()` in the PR-branch worktree (see "Load-bearing
claim 2" above) — traced the respawn-ceiling guard
(`gates/spawn_on_pr.py`'s `attempts >= max_respawn_attempts` check) forward
from guard site to downstream consequence on both the described pre-fix
shape (positional slot renumbering silently discarding a stuck slot's
attempt history — a Silently Absorbed pattern, guard exists but its effect
was defeated without any signal, per the hunt record's own trace) and the
current fixed shape (subject-level cumulative `attempts`: my own repro
above showed it prints `CEILING HIT`, writes a
`spawn_on_pr_respawn_ceiling_hit` ledger event, and actually stops
spawning — Handled, independently reproduced, not read off the record's
own trace).
