---
issue: 2695
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: on-the-record/commands/run.md (PR #2697 branch issue-2695/requirements-quality+technical-writing-minimalism-scoping-37ef6c94)
    sha: a7642fe4eeff2e80bf6d1632dca5157444e88ff1
  - path: docs/specs/enforcement-boundary.md (same branch/commit)
    sha: a7642fe4eeff2e80bf6d1632dca5157444e88ff1
---

# issue-2695 — independent-verification-1 record

## What was done

Build-now bypass (contract v3 s19a): `CORE_BUILD_NOW=1` was set in this
session's environment by the spawner — checked: `printenv | grep
CORE_BUILD_NOW` — result: `CORE_BUILD_NOW=1`. So this record delivers
directly, no phase-1 proposal round.

Independent verification of PR #2697
(`issue-2695/requirements-quality+technical-writing-minimalism-scoping-37ef6c94`,
head `a7642fe4eeff2e80bf6d1632dca5157444e88ff1`), which claims to close
issue #2695 by retiring `on-the-record/commands/run.md`'s two dead-machinery
mandatory steps (the four-name request classification, and the
remediation-queue check) and by fixing an orphaned spec-doc row in
`docs/specs/enforcement-boundary.md`. The subject's own record,
`docs/issue-2695/reports/requirements-quality+technical-writing-minimalism-scoping-37ef6c94.md`
(untracked / not present in this worktree — this worktree is
`issue-2695/independent-verification-1`, cut from `main`, and that path
lands only on PR #2697's branch), was read via `git show
pr-2697-verify:docs/issue-2695/reports/requirements-quality+technical-writing-minimalism-scoping-37ef6c94.md`
against a local `pr-2697-verify` branch fetched from `pull/2697/head`, for
context only; every claim below was independently re-derived, not taken
from that read.

Re-ran all three of #2695's acceptance checks independently, from a fresh
git worktree checked out at the PR's own head commit (`git fetch origin
pull/2697/head:pr-2697-verify && git worktree add /tmp/pr2697check
pr-2697-verify`), rather than trusting the subject record's own transcript
of running them.

**Acceptance check 1** (four-name classification gone from `run.md`):
canonical: `grep -nE 'feasibility|ux-design|리드 역할'
on-the-record/commands/run.md` run in `/tmp/pr2697check` — no output,
exit 1 (0 occurrences). Matches PR #2697's claim exactly.

**Acceptance check 2** (remediation-queue step gone; queue shown unable to
produce a line): canonical: `python3 gates/remediation_spawn.py --issue <n>
-C .` run in `/tmp/pr2697check` against the same 5 real board issues the
subject record cites (2695, 2690, 2688, 2686, 2682) — empty stdout, exit 0,
on every one. Also independently confirmed `grep -n "remediation"
on-the-record/commands/run.md` returns nothing (exit 1) in the post-diff
file — the step text itself is gone, not merely softened.

**Acceptance check 3** (an orchestrator following the edited directive
reaches a spawn that produces a PR): canonical: `gh pr view 2696
--repo tokenmaxxxer/on-the-record` — `title: issue-2503: acceptance-format
role-forbidden-action rule + authoring gate`, `state: OPEN`, `additions:
305`, body ends `Closes #2503`, author `JiwonJung94`. This is a real, open,
running-repo PR produced by the step-4 spawn the subject record describes
(`spawn.py --skills requirements-quality ... --issue 2503`), not a
simulated or dry-run demonstration.

**Renumbering / dangling-reference check** (not itself one of the three
acceptance checks, but load-bearing for "the directive matches what it can
actually produce" — a dangling step-number reference would leave the
directive internally inconsistent even with the dead steps removed):
canonical: `grep -n "^[0-9]\+\. \*\*" on-the-record/commands/run.md` in
`/tmp/pr2697check` — top-level steps now run 1–6 (요구사항→이슈 / 판단 /
누구를 깨울지 / 띄운다 / PR 을 설명한다 / 사용자의 결정을 중계한다); cross-
checked every `grep -n "번 스텝" on-the-record/commands/run.md` hit by hand
against that list — all "6번 스텝" refs resolve to the decision-relay step
(line 313), all "5번 스텝" refs to the PR-description step (line 124), all
"3번 스텝"/"4번 스텝" refs to the spawn-basis/spawn steps (lines 99/105),
and the "2번 스텝" ref at line 409 to the renamed judgment step (line 89,
now "판단" not "분류", matching the ref's own wording "2번 스텝의 판단에서
이어짐"). No dangling reference found — independently reproduces the
subject's own before-landing warrant-hunter's "no findings" verdict on this
point.

**`must not` constraint check** (issue #2695: do not replace the four-name
table with a different fixed list of names): read the new step 2 text in
`/tmp/pr2697check/on-the-record/commands/run.md:89-99` directly. It asks
the orchestrator to state in one line whether anything is unresolved
(investigation / requirements / UX judgment) or state readiness to
implement, and explicitly disclaims fixed-name classification ("이 판단은
고정된 이름(역할/카테고리)으로 분류하지 않는다"). No table, no enumerated
identity set — the constraint holds.

**Non-goals check** (do not touch `gates/remediation_spawn.py` or
`delegated-judgment-gate.sh`'s escalate branch): canonical: `gh pr diff
2697 --name-only` — only `on-the-record/commands/run.md`,
`docs/specs/enforcement-boundary.md`, and two files under
`docs/issue-2695/reports/` are touched. Neither `gates/remediation_spawn.py`
nor `on-the-record/hooks/delegated-judgment-gate.sh` appears in the diff —
non-goal respected.

**Subject's "What did not work" claim** (spec_index.py raises
`FileNotFoundError` on `roles/specs/brand-design.spec.json`,
independent of this diff): reproduced independently — ran `python3
gates/spec_index.py --update` in `/tmp/pr2697check` (the PR's own worktree,
which already contains the diff) and got the identical
`FileNotFoundError: [Errno 2] No such file or directory:
'.../roles/specs/brand-design.spec.json'`. Confirms the generator is
broken for a pre-existing reason unrelated to this PR's edits, so leaving
`docs/specs/reconciled-index.md` unregenerated is not a shortcut taken by
this delivery.

## Why

Independent verification exists so a subject's own acceptance-check
transcript is not the only evidence a merge relies on. canonical: the
acceptance-check command outputs quoted above in `## What was done`, all
executed live in `/tmp/pr2697check` — a worktree checked out at PR #2697's
own head commit `a7642fe4eeff2e80bf6d1632dca5157444e88ff1`, not inherited
from the subject PR's own record. Re-deriving every claim from that fresh
worktree, rather than re-reading the subject record and taking its command
output on faith, is what makes this a genuine second check rather than a
restatement.

## What did not work

None.

## Upstream basis

- PR #2697, branch `issue-2695/requirements-quality+technical-writing-minimalism-scoping-37ef6c94`,
  head `a7642fe4eeff2e80bf6d1632dca5157444e88ff1` — the subject PR verified.
- The subject's own record (untracked in this worktree; present only on
  PR #2697's branch), read via `git show
  pr-2697-verify:docs/issue-2695/reports/requirements-quality+technical-writing-minimalism-scoping-37ef6c94.md`
  — read for context only, not relied on as evidence; every claim in it
  was independently re-derived above.
- `docs/handbooks/observer-verification.md` — the mechanism this record's
  `verifies_subject: true` / `author:` fields satisfy.

## Open findings

None — all three acceptance checks, the `must not` constraint, and the
non-goals constraint independently reproduced. No new gap surfaced beyond
what PR #2697's own before-landing warrant-hunter already disclosed and
fixed in the same commit (the `enforcement-boundary.md` orphaned-reachability
row).

## Next steps

None — `loop_state: landed`.

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; used to write this
record and all verification commands/reasoning in English, with the final
chat summary to the user in Korean.
other mounted skills: not triggered — none of the other mounted skills
(dataviz, code-review, simplify, run, etc.) match an independent-
verification-of-a-directive-edit task; no chart/UI/app-launch/broad-review
surface here.
