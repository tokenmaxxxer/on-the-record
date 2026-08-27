---
issue: 2628
role: conformance-review-traceability-and-evidence+conformance-review-verdict-assignment-2d6823f8
author: conformance-review-traceability-and-evidence+conformance-review-verdict-assignment-2d6823f8
skills: conformance-review-traceability-and-evidence (skill-repository(297e350)), conformance-review-verdict-assignment (skill-repository(297e350))
verifies_subject: true
loop_state: landed
upstream:
  - path: gates/spawn_on_pr.py (PR #2640, branch issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41, untracked in this branch)
    sha: 686237cdf8f180d84de55c3e2eaf4d882875a87a
  - path: gates/merge_gate.py (baseline, untouched by PR #2640)
    sha: 2cb0bab2cd4c3cd376af29b838bd81e2635b0e5f
---

# issue-2628 — conformance-review-traceability-and-evidence+conformance-review-verdict-assignment-2d6823f8 record

## What was done

Independent verification of PR #2640 (issue #2628, "PR_TRIGGERED_RECORD_KINDS
survived as AUTO_SPAWN_ROLES — byte-identical tuple, still gating auto-spawn")
against the issue's own Acceptance section, re-derived in a fresh worktree
against `origin/main` and the branch tip, not read from the PR body or the
implementation record's pasted output.

canonical: `gh pr view 2640 --json title,body,number,headRefName,baseRefName,mergeable,state`
— head `issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41`,
base `main`, state OPEN, mergeable MERGEABLE.

derived: `git worktree add /tmp/verify-2628-worktree origin/issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41 && git -C /tmp/verify-2628-worktree rev-parse HEAD origin/main`
— result:
```
686237cdf8f180d84de55c3e2eaf4d882875a87a
2cb0bab2cd4c3cd376af29b838bd81e2635b0e5f
```
All checks below ran against this worktree.

**Verdict: Present** on all three acceptance bullets and the `must not`
clause. Two load-bearing claims independently checked, both hold.

### Acceptance bullet 1 — "No closed set of names decides which sessions are auto-spawned"

acceptance: `grep -rn 'AUTO_SPAWN_ROLES' --include=*.py .` (run in
/tmp/verify-2628-worktree, branch tip `686237cd`) — result:
```
(no output, exit 1)
```
Acceptance requirement met.

derived: `git diff origin/main...HEAD -- gates/spawn_on_pr.py | grep -n "^-.*AUTO_SPAWN_ROLES\|^-.*applicable_record_kinds"`
(run in /tmp/verify-2628-worktree) — result:
```
29:-AUTO_SPAWN_ROLES = ("execution-observation", "conformance-review")
123:-def applicable_record_kinds(subject_board: dict, kinds: tuple[str, ...] = AUTO_SPAWN_ROLES, ...
292:-        missing = applicable_record_kinds(subject_board, subject_author=subject_author)
717:-        missing = applicable_record_kinds(subject_board, subject_author=subject_author)
```
Both `AUTO_SPAWN_ROLES` and the kind-matching function that consumed it
(`applicable_record_kinds()`) are fully deleted, all call sites migrated to
`verification_deficit()` (`686237cd:gates/spawn_on_pr.py:160-174`). **Present.**

### Acceptance bullet 2 — "the obligation still happens, demonstrated end-to-end"

derived: independently constructed script (not copy-pasted from the PR
record) calling the real, unmodified `spawn_on_pr.verifying_record_count()` /
`verification_deficit()` / `subject_deliverable_record()`
(`686237cd:gates/spawn_on_pr.py:67-174`) against synthetic `subject_board`
dicts, run as `python3 /tmp/demo_invite.py` — result:
```
n_verifying=0 -> verifying_record_count=0, deficit=2
  invited roles: ['independent-verification-1', 'independent-verification-2']
n_verifying=1 -> verifying_record_count=1, deficit=1
  invited roles: ['independent-verification-1']
n_verifying=2 -> verifying_record_count=2, deficit=0
  invited roles: []

self-authored verifying record must not count:
  verifying_record_count: 0 deficit: 2
```
Numbers match the PR record's own demonstration exactly. Acceptance
requirement met — the rule: a subject gets `REQUIRED_INDEPENDENT_VERIFICATIONS
(2) - verifying_record_count(subject_board, subject_author)` generic
`independent-verification-<n>` invitations, self-authored records excluded,
never a named role. **Present.**

**Capability-change honesty check (explicitly required by the spawning
task):**

canonical: `git show 49c4854b:gates/spawn_on_pr.py` lines 140-180 (pre-PR
`applicable_record_kinds()`, read in /tmp/verify-2628-worktree) — matched by
**named kind presence**, not raw count:
`matched = kind_field if kind_field in kinds else (name if name in kinds else None)`.
A subject with 2 records of the *same* kind (e.g. two `execution-observation`
-kind records, zero `conformance-review`-kind) would still have been told
"conformance-review is missing" and invited one more, whereas
`verification_deficit()` (`686237cd:gates/spawn_on_pr.py:160-174`) counts
total `verifies_subject: true` records regardless of kind and would report
deficit=0 for the same board (independently confirmed above in the bullet-2
demonstration, which uses no `kind:` field at all). This is a real, named
behavior change: the automation can no longer target a *specific kind of
expertise* by name, only a raw count. This is disclosed in PR #2640's own
description (untracked in this branch, lives at
`docs/issue-2628/reports/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41.md`
on branch `issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41`,
sha `686237cd`, "Why" section: "the auto-spawn tick can no longer target a
specific kind of expertise by name"). No unstated behavior change surfaced
beyond what the PR already states.

### Acceptance bullet 3 — "checked with `scripts/audit_removal_claim.py`, output in the record"

derived: `python3 -c "import json; json.dump({'name': 'AUTO_SPAWN_ROLES tuple removed from gates/spawn_on_pr.py, no closed set of names replaces it (issue #2628)', 'removed_names': ['AUTO_SPAWN_ROLES', 'applicable_record_kinds'], 'member_samples': ['execution-observation', 'conformance-review'], 'min_coloc': 2}, open('/tmp/audit_claim_2628_indep.json','w'))" && python3 scripts/audit_removal_claim.py /tmp/audit_claim_2628_indep.json --root .`
(run in /tmp/verify-2628-worktree) — result:
```
verdict: RESHAPE_DETECTED
q1: live_hits=[], gone=true
q2 colocated_files (2 member samples in one file): .claude-plugin/marketplace.json,
  __pycache__/directive_assembly.cpython-310.pyc, directive_assembly.py,
  gates/__pycache__/spawn_on_approve.cpython-310.pyc, gates/merge_gate.py,
  gates/spawn_on_approve.py, on-the-record/commands/run.md,
  on-the-record/directive/spawn-and-board.md,
  on-the-record/hooks/pr-base-guard.sh, spawn.py
q3: branch_hits=[]
```
(Two extra `__pycache__/*.pyc` hits vs. the record's list are stale bytecode
of the same already-classified `.py` files, generated by this session's own
test run — not new source; `.git/*` hits present in the PR record's own run
are session-local reflog noise absent from a fresh worktree, as expected —
both are git/build-artifact noise, not source.)

derived: independently re-grepped every non-`.git`/non-cache hit myself
(not trusting the PR record's classification) — `grep -n "execution-observation\|conformance-review" <file>`
for each of `directive_assembly.py`, `gates/merge_gate.py`,
`gates/spawn_on_approve.py`, `on-the-record/commands/run.md`,
`on-the-record/directive/spawn-and-board.md`,
`on-the-record/hooks/pr-base-guard.sh`, `spawn.py`,
`.claude-plugin/marketplace.json` (all in /tmp/verify-2628-worktree). Result:
`directive_assembly.py` — 1 anti-pattern warning comment + 2 unrelated
historical comments, no dict/tuple/dispatch structure;
`gates/merge_gate.py` — 2 unrelated docstring/comment examples;
`gates/spawn_on_approve.py` — 1 background-context comment describing a
retired mechanism, its own actual logic already role-agnostic;
`on-the-record/commands/run.md` + `on-the-record/directive/spawn-and-board.md`
— document the separate human-driven `spawn.py --skills` workflow, not this
automatic tick; `on-the-record/hooks/pr-base-guard.sh` — prose narrating a
specific past incident by branch name, not live logic; `spawn.py` — CLI help
text + 2 unrelated comments + a pre-existing, out-of-scope `LEGACY` dict
(`spawn.py:740`) containing only 1 of the 2 member samples;
`.claude-plugin/marketplace.json` — different subsystem (plugin marketplace
repos coincidentally named `*-rulebook`). **All independently confirmed
false positives** — none is a live dict/tuple/dispatch structure gating
`spawn_on_pr.py`'s auto-spawn decision. Acceptance requirement met — tool
run and hand-classification both hold up under independent re-derivation.
**Present.**

### `must not` clause — no rename/relocation/sharding/config-read; `REQUIRED_INDEPENDENT_VERIFICATIONS` not weakened

derived: `git diff origin/main...HEAD --stat` (run in
/tmp/verify-2628-worktree) — result:
```
gates/spawn_on_pr.py       | 511 +++++++++++----------
gates/test_spawn_on_pr.py  |  92 +++-
test/test_verifies_subject_scaffold.py | 8 +-
```
(plus 3 docs/-only paths). `gates/merge_gate.py` has zero diff lines in this
PR — `REQUIRED_INDEPENDENT_VERIFICATIONS = 2` and
`required_verification_missing()` (`2cb0bab2:gates/merge_gate.py:43,178-213`)
are untouched. Acceptance requirement met — the capability was dropped per
the operator ruling (bullet 2's honesty check above), not
renamed/relocated/sharded, and the merge-gate obligation is unweakened.
**Present.**

## Load-bearing claim 1 — does `verification_deficit()` mirror `merge_gate.py::required_verification_missing()` exactly?

canonical: read `686237cd:gates/spawn_on_pr.py:160-174` and
`2cb0bab2:gates/merge_gate.py:116-213` in full (both in
/tmp/verify-2628-worktree). **They can disagree**, but narrowly, and the
disagreement is already disclosed in PR #2640's own record — not a hidden
defect.

`required_verification_missing(root, subject, repo=None, pr=None)` has two
branches: when `repo`/`pr` are both given, it first checks
`_own_pr_supplies_verification()` (`gates/merge_gate.py:116-163`) — if the PR
currently under merge-gate evaluation itself carries an unlanded qualifying
`verifies_subject: true` record for `subject`, it returns `0` outright (a
cycle-breaker, issue #2233/#2380: a verification PR must not be blocked from
merging by the very record it is about to supply). Only when that exemption
doesn't apply does it fall through to the same formula
`verification_deficit()` uses
(`max(0, REQUIRED_INDEPENDENT_VERIFICATIONS - verifying_record_count(...))`).
`verification_deficit()` has no `repo`/`pr` parameters and never takes the
exemption branch — it is only the second branch's formula.

Concretely: for a subject with 1 landed verifying record (deficit=1) and a
second, not-yet-merged PR open that itself carries a qualifying record,
`required_verification_missing(root, subject, repo=repo, pr=<that PR's
number>)` returns `0` (exempt — that PR can merge), while
`verification_deficit(subject_board)` on the same board still returns `1`
(the record hasn't landed yet, so `verifying_record_count()` doesn't see it).
Same subject, same instant, different numbers from the two functions.

This does not make the PR's own claim false: PR #2640's record (untracked in
this branch; on branch
`issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41`,
sha `686237cd`) explicitly scopes the claim to "mirrors ... count-only branch
exactly" and its "Why" section states the reason for not sharing code
(`gates/merge_gate.py:19: import spawn_on_pr` makes a reverse import
circular) and explicitly names the `repo`/`pr` exemption path as the part
deliberately not mirrored.

derived: `grep -n "verification_deficit(" gates/spawn_on_pr.py` (run in
/tmp/verify-2628-worktree) — result:
```
364:        deficit = verification_deficit(subject_board, subject_author=subject_author)
793:        deficit = verification_deficit(subject_board, subject_author=subject_author)
```
Read both call sites (`missing_verification()` at line 333,
`_missing_verification_closed()` at line 762, plus `spawn_missing_for_pr()`
at line 570) — none of them ever passes a `repo`/`pr` pair for the subject
being evaluated in the exemption sense; they board-sweep across all
subjects rather than evaluate one specific PR under review, so the
exemption's absence never actually produces a wrong auto-spawn decision in
this code's own usage. Claim assessed as **accurate as scoped, not
misleading** — the PR body's own summary line says "a count ... mirroring
merge_gate.py's existing count-only obligation check," the same careful
scoping the fuller record uses, narrower than the "mirrors ... exactly"
framing this review was asked to test.

## Load-bearing claim 2 — respawn-ceiling defect and fix

Confirmed real, and confirmed fixed — independently reproduced, not read
from the hunt record's narrative.

Pre-fix commit `eb61de56` (cited in PR #2640's hunt record as the seed) is
not reachable in this repo's git history.
derived: `git cat-file -t eb61de56` (run in /tmp/verify-2628-worktree) —
result: `fatal: Not a valid object name eb61de56` — it was an in-session,
never-landed intermediate state, fixed before the single landing commit.
Since it cannot be checked out, the specific buggy fragment described
(positional `slot = range(1, deficit+1)` renumbered fresh every tick, park
keys `f"{subject}/{role}"`) was independently re-implemented in an isolated
script, seeded with the described scenario (slot 1 at attempts=1, slot 2 —
the stuck one — at attempts=3, deficit drops 2→1 when slot 1 resolves).

derived: `python3 /tmp/repro_prefix_bug.py` — result:
```
spawned: ['issue-88002/independent-verification-1']
{
  "issue-88002/independent-verification-1": {"attempts": 2},
  "issue-88002/independent-verification-2": {"attempts": 3}
}
```
This independently confirms the described mechanism: renumbering to
`slot=1` writes into the *wrong* park key (the resolved one, attempts=1→2)
while the genuinely-stuck entry (attempts=3) is silently orphaned and never
re-read again by this positional scheme.

Then independently verified the landed fix closes exactly this gap, running
the real `spawn_on_pr.spawn_missing_for_pr()` (`686237cd:gates/spawn_on_pr.py:570-793`,
only `gh`/`git` boundary functions monkeypatched, decision logic untouched)
against a subject already at cumulative `attempts=3`, `max_respawn_attempts=4`.

derived: `python3 /tmp/repro_fixed.py` — result:
```
pairs spawned this tick: [('issue-88002', 'independent-verification-4')]
{'issue-88002': {'attempts': 4, 'blocked': True, 'parked': False, 'pr_number': 1}}
--- next tick, still deficit 1, unchanged ---
LEDGER: {'event': 'spawn_on_pr_respawn_ceiling_hit', 'subject': 'issue-88002', 'attempts': 4, 'max_respawn_attempts': 4}
[spawn-on-pr] CEILING HIT: 1건이 최대 재시도 횟수(4)에 도달해 자동 스폰을 멈춘다 ...
pairs spawned this tick: []
{'issue-88002': {'attempts': 4, 'blocked': True, 'ceiling_hit': True, 'parked': True, 'pr_number': 1}}
```
The ceiling trips at the correct cumulative count regardless of how sibling
slots were renumbered along the way — the subject-level `park_state` key
(keyed on `subject` alone, `attempts` monotonically increasing from the
subject's own history, never from the live deficit) is immune to the
renumbering collision the old per-role keys were vulnerable to.

acceptance: `python3 -m pytest gates/test_spawn_on_pr.py test/test_verifies_subject_scaffold.py test/test_watchdog_heartbeat_noise.py test/test_merge_gate_record_kind.py -q`
(run in /tmp/verify-2628-worktree) — result:
```
43 passed
```
matching the PR's claimed count exactly. Acceptance requirement met — the
fix holds under independent reproduction of the exact adversarial scenario
described as the first pass's defect.

One design point worth naming (not a defect, a genuine behavior narrowing
already implicit in the fix, not separately called out in the PR body):
derived: read `686237cd:gates/spawn_on_pr.py:635-661` (`spawn_missing_for_pr`'s
ceiling check) — the old per-role park state gave each of the two fixed
roles its own independent 4-attempt ceiling (up to 8 cumulative respawns
tolerated per subject before any ceiling hit). The new subject-level
counter enforces one shared 4-attempt ceiling across *all* of a subject's
verification slots combined — a subject needing 2 verifications that each
take 2 respawns (4 total) now hits the ceiling, where the old per-role
scheme would not have. This is a tightening, not a weakening, of the
backstop issue #2238 built, so it does not introduce a new failure mode —
flagging only because it is a quantitative behavior change the PR body does
not explicitly state in those terms.

## Why

Followed the spawning task's explicit re-derivation requirement: independent
verification means re-running every check against the branch tip and
`origin/main` in a fresh worktree, not accepting the PR body's or the
implementation record's pasted output. Used a worktree
(`git worktree add /tmp/verify-2628-worktree origin/issue-2628/...`) rather
than switching this session's own branch, to keep this record's own working
tree untouched while checking out the subject's code. Applied
`conformance-review-verdict-assignment` rule 6 (re-check a plausible false
positive before finalizing) to the `audit_removal_claim.py` hits — regrepped
every file independently rather than trusting the PR record's
classification.

Rule 1 (Surface vs Present) and rule 5 (name the failing clause) shaped how
the two load-bearing claims are reported. Claim 1's verdict (Present-as-
scoped) and claim 2's verdict (Present) both rest on the executed evidence
already cited under "Load-bearing claim 1" and "Load-bearing claim 2" above
— canonical: `python3 /tmp/repro_fixed.py` and
`python3 -m pytest gates/test_spawn_on_pr.py -q` (both re-run in this
section's cited evidence above, `686237cd:gates/spawn_on_pr.py:570-793`),
not re-derived a second time here.

## What did not work

The only wrinkle: `eb61de56` (the pre-fix commit cited in PR #2640's hunt
record) was not reachable in git history to check out directly — handled by
re-implementing the described buggy fragment independently instead (see
"Load-bearing claim 2" above, `python3 /tmp/repro_prefix_bug.py`).

## Upstream basis

- `gates/spawn_on_pr.py`, `gates/test_spawn_on_pr.py`,
  `test/test_verifies_subject_scaffold.py` — PR #2640, branch
  `issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41`
  (untracked in this branch), sha `686237cdf8f180d84de55c3e2eaf4d882875a87a`.
- `gates/merge_gate.py` — read at the same branch tip for comparison; zero
  diff vs. `origin/main` (`2cb0bab2cd4c3cd376af29b838bd81e2635b0e5f`) in this
  PR — canonical: `git diff origin/main...HEAD --stat` (above, `must not`
  clause section).
- PR #2640's own record and nested hunt record (untracked in this branch;
  on branch `issue-2628/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41`,
  sha `686237cd`) — read for their claims, then independently re-checked
  rather than cited as evidence on their own.

## Open findings

None open. Both load-bearing claims hold (claim 1 narrowly scoped and
correctly so; claim 2's ceiling fix independently reproduced as sound,
canonical: `python3 /tmp/repro_fixed.py`, above). One design point (shared
vs. per-role respawn budget, "Load-bearing claim 2" above) is worth stating
explicitly in a future record but is not a defect — tightening a safety
backstop is not a regression.

## Next steps

None for this issue. `loop_state: landed`.

amendments-reconciled: issuecomment-5436750956 — canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5436750956`. Posted
mid-session (2026-08-27T08:59:31Z), reporting that the currently-deployed
(pre-PR-#2640) `AUTO_SPAWN_ROLES` path was inviting `conformance-review` by
name even though `python3 spawn.py --skills conformance-review ...` refuses
it outright ("모르는 스킬 conformance-review" — not an installed skill since
the record-kind axis was retired). This is corroborating evidence for the
same defect this review already found Present-fixed above: the closed
name-roster went stale against the very thing it named, and nothing in a
roster-shaped mechanism could notice that on its own — exactly the failure
mode `verification_deficit()` structurally cannot have (a count has nothing
to name, so nothing to go stale against). It does not change any verdict
above; it is additional live evidence for why the fix in PR #2640 was the
right shape, not a new acceptance criterion or a contradiction.

### Skill verdicts

skill-verdict: conformance-review-verdict-assignment — applied: invoked;
rule 1 (Surface vs Present) shaped classifying the "mirrors ... exactly"
claim as accurate-as-actually-scoped rather than Surface, since the PR's own
narrower wording ("count-only branch exactly") matches what the code does;
rule 5 (name the failing clause) shaped stating precisely which branch
(`_own_pr_supplies_verification`'s `repo`/`pr` exemption) the two functions
diverge on rather than a bare "they can disagree"; rule 6 (re-check a
plausible false positive) directly drove re-grepping every
`audit_removal_claim.py` hit independently instead of accepting the PR
record's classification.

skill-verdict: conformance-review-traceability-and-evidence — applied: invoked;
rule 1 (file:line + commit sha, not a bare path) shaped every
citation above (e.g. `686237cd:gates/spawn_on_pr.py:160-174`); rule 2 (one
link per contributing file) shaped citing `gates/spawn_on_pr.py` and
`gates/merge_gate.py` as separate upstream links rather than one bundled
reference, since the comparison in claim 1 depends on reading both
independently.
