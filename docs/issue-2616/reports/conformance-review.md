---
issue: 2616
role: conformance-review
author: conformance-review
loop_state: reported
type: review-record
code_under_review:
  - pipeline.py:369-401 (`_report_managed_clone_staleness()`, new)
  - pipeline.py:432 (`core_root()` wiring)
  - skills.py:73-81 (`_skill_repo_managed_root()` wiring)
  - spawn.py:543 (re-export)
  - 434ac942:test/test_managed_clone_staleness_report.py (new)
breaking: "none — this is a review record, no code changed by this role"
verdict: "pass — canonical: `python3 -m pytest test/test_managed_clone_staleness_report.py test/test_checkout_staleness.py -q` (this session, worktree at 606f69cc) — 15 passed; `python3 -m pytest test/ -q` (same worktree) — 15 failed, 316 passed, the 15 failures identical to the pre-existing baseline documented in docs/issue-2603"
upstream:
  - path: docs/issue-2616/reports/silent-failure-audit+observability-explorability-d0acabc7.md
    sha: 606f69cc51fa59a6ba4dbff3b34dbeb7ad426829
subject: PR #2618 (branch issue-2616/silent-failure-audit+observability-explorability-d0acabc7, HEAD 606f69cc51fa59a6ba4dbff3b34dbeb7ad426829)
test: issue #2616's own Acceptance section, https://github.com/tokenmaxxxer/on-the-record/issues/2616
result: passed
assertedBy: conformance-review session, issue-2616 (builder-blind; independently reproduced the deliberately-stale-clone and non-git-clone scenarios against the actual reporting function, in a fresh worktree, rather than trusting the implementation record's pasted output)
---

# issue-2616 — conformance-review record

Builder-blind conformance review of PR #2618 (branch
`issue-2616/silent-failure-audit+observability-explorability-d0acabc7`,
HEAD `606f69cc`) against issue #2616's own Acceptance text, not against
the implementation session's self-report.

canonical: `git worktree add /tmp/pr2618-review 606f69cc` (this session), `git -C /tmp/pr2618-review rev-parse HEAD` —
```
606f69cc51fa59a6ba4dbff3b34dbeb7ad426829
```

Note on the implementation record's path:
`docs/issue-2616/reports/silent-failure-audit+observability-explorability-d0acabc7.md`
is untracked in this checkout (`issue-2616/conformance-review`, based on
`main`) — it exists only on the unmerged branch
`issue-2616/silent-failure-audit+observability-explorability-d0acabc7`
(commit `606f69cc`). This session read it via `git fetch origin
issue-2616/silent-failure-audit+observability-explorability-d0acabc7` and
`git worktree add /tmp/pr2618-review 606f69cc`, both executed above.
Every further citation of that same untracked path below is to the
worktree-read file, not a path present in this branch's own tree.

skill-verdict: conformance-review-verdict-assignment — applied: invoked; used rule 1 (Surface vs Present — checked whether the wiring actually fires on the real `core_root()`/`_skill_repo_managed_root()` bootstrap path, not just that matching code exists) and rule 6 (re-checked the must-not verdict against the actual `checkout_staleness()` body before finalizing) to assign every requirement below.
skill-verdict: conformance-review-finding-record — applied: invoked; every requirement below carries a stable id, a verdict from the five-value set, a file:line evidence pointer, and a one-line rationale connecting the two.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence citation below is pinned to file:line-range plus the commit sha this session actually read (`606f69cc`, or `434ac942` where the citation is to that commit's diff specifically).
skill-verdict: work-in-english — applied: invoked; this record and all commands run this session are in English; the final chat summary to the user is in Korean per the skill's routing rule.

## What was done

Reviewed PR #2618 (issue #2616's implementation) for conformance against
the issue's own Acceptance text: added a `git worktree` pinned to the
PR's actual head (`606f69cc`), read the changed code in `pipeline.py`,
`skills.py`, and `spawn.py` directly, and independently re-executed every
test the PR's test plan cites rather than trusting its pasted output.

derived: `python3 -m pytest test/test_managed_clone_staleness_report.py test/test_checkout_staleness.py -q` (this session, fresh worktree at `606f69cc`) —
```
15 passed in 0.98s
```

derived: `python3 -m pytest test/ -q` (same worktree) —
```
15 failed, 316 passed in 2.72s
```
The 15 failure names matched exactly (`test_convention_equivalence.py`,
`test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py` cases) what the PR's own
test plan and implementation record report as pre-existing/unrelated
failures (documented in docs/issue-2603) — no regression introduced by
this PR's new test file or its three changed source files.

Also independently reproduced the two `check:` scenarios from the
Acceptance section myself, against the actual reporting function rather
than trusting the implementation record's test output: built a scratch
bare-repo origin plus two clones, advanced one clone by a commit, and
called `pipeline._report_managed_clone_staleness()` directly against both
the deliberately-stale clone and a plain non-git directory (see AC-1 and
AC-2 below for the exact commands and captured output).

## Requirement list

- AC-1 (functional-behavior): a session bootstrap reports when the core
  rulebook clone is behind its origin, naming the clone and how far
  behind — check: put the clone one commit behind deliberately, spawn a
  session, and show the reported line; empty state: clone level with
  origin — no line, exactly as today.
- AC-2 (functional-behavior): the report distinguishes "behind" from
  "could not determine" — check: run the same detection against a path
  that is not a git clone and show it reports undetermined rather than
  current.
- AC-3 (disclosure): whether the clone is auto-updated is decided
  explicitly and the reasoning recorded, not left implicit, with an
  actionable command a reader would run either way.
- MUST-NOT-1 (scope-boundary): must not auto-mutate the clone silently as
  a side effect of an unrelated operation, and must not report the clone
  as current when a fetch has not happened.
- NON-GOAL-1 (scope-boundary, disclosure): the skill-repository clone is
  out of scope unless it shares the same code path as the core rulebook
  clone — check, and say which.

## AC-1 — Present

canonical: `606f69cc:pipeline.py:369-401` (this session, worktree read) —
`_report_managed_clone_staleness(d, label)` calls
`spawn.checkout_staleness(root=d, fetch=True)` and, when `checked and
stale`, prints `f"[{label}] {d} 이(가) origin 대비 {behind}개 커밋
뒤처졌다 — 고치려면: git -C {d} pull --ff-only"` to stderr (lines
394-397); when `checked and not stale`, returns with no output at all
(lines 392-393, the empty-state clause). Wired into `pipeline.core_root()`
at `606f69cc:pipeline.py:432`, on the branch that reuses an
already-valid, previously-cloned `tokenmaxxxer-core` checkout — the exact
bootstrap path a spawned session takes on every run once the clone
exists. `606f69cc:spawn.py:3675-3681` confirms `core_root()` (via
`core_plugin_dirs()`) is called on the actual session-spawn path, ahead of
directive assembly.

derived (this session, independent reproduction, not the implementation's
own test — a scratch bare origin + two clones, one advanced one commit
past the other, mirroring the issue's own measured incident): built
`checkout-a`/`checkout-b` off a bare `origin.git`, committed and pushed
one extra commit from `checkout-b`, left `checkout-a`'s own cached
`origin/main` stale (never re-fetched), then called
`pipeline._report_managed_clone_staleness(checkout_a, "core")` directly —
result:
```
[core] /tmp/tmprodcxl6o/checkout-a 이(가) origin 대비 1개 커밋 뒤처졌다 — 고치려면: git -C /tmp/tmprodcxl6o/checkout-a pull --ff-only
```
Names the clone path and the exact behind-count (1), and gives the fix
command — matches AC-1's check literally, reproduced independently rather
than trusted from the implementation record's own test output.

derived (same session): calling the same function again against the
now-current `checkout-a` (no advance since the fetch inside the call)
produces empty stderr output — confirms the empty-state clause holds:
`checked: True, stale: False` prints nothing, same as today.

Rationale: the function fires on the real bootstrap path
(`core_root()`, itself reached from the actual spawn flow), names the
clone path and the exact behind-count in its output, and the empty state
is silent — all three clauses of AC-1 hold under an independent
reproduction, not just the implementation's own test suite.

## AC-2 — Present

canonical: `606f69cc:pipeline.py:394-401` (this session) — the `if
result["checked"]:` branch (stale, lines 394-397) and the `else:` branch
(`checked: False`, lines 398-401) are textually distinct: the former says
"...개 커밋 뒤처졌다" (behind), the latter says "...최신 여부를 판정할 수
없다" (cannot be determined) and names `result["detail"]`. Nothing in
either branch collapses to a shared "current" wording.

derived (this session, independent reproduction): created a plain
non-git directory and called
`pipeline._report_managed_clone_staleness(not_a_clone, "core")` — result:
```
[core] /tmp/tmprodcxl6o/plain-dir 의 origin 대비 최신 여부를 판정할 수 없다 (HEAD 를 resolve 할 수 없다) — 확인하려면: git -C /tmp/tmprodcxl6o/plain-dir fetch origin && git -C /tmp/tmprodcxl6o/plain-dir status -sb
```
Reports "판정할 수 없다" (cannot be determined), never "현재"/"뒤처졌다"
— distinguishes undetermined from both current and behind, matching
AC-2's check literally.

Rationale: the undetermined path is reached and worded distinctly from
both the current (silent) and stale (behind-count) paths, reproduced
independently against the actual function rather than a mock.

## AC-3 — Present

canonical: `docs/issue-2616/reports/silent-failure-audit+observability-explorability-d0acabc7.md`
— untracked in this checkout, lines 92-134, read at commit `606f69cc`
via the git worktree noted at the top of this record (this session) —
the `## Why` section states the design decision explicitly: "the clone
stays on its existing auto-update path (TTL-gated `git pull --ff-only`
in `core_root()` / `_skill_repo_managed_root()`), unchanged. This session
does not add a second, staleness-triggered auto-update," with reasoning
(the existing pull mechanism is already the deliberate auto-update
choice, exercised on every spawn; changing its trigger would touch a hot
path the issue's acceptance does not ask for) and the consequence for
sessions already spawned inside the TTL window ("still bootstraps against
the old code... but it no longer does so silently"). Names the exact
reader command: `git -C runs/rulebooks/tokenmaxxxer-core pull --ff-only`
— the same command the stale-path report line itself prints
(`606f69cc:pipeline.py:396`), so the record's stated command and the
runtime's actual output are the same string, not two independently
drifting claims.

Rationale: the decision (no new auto-update path) and its reasoning are
both recorded in prose, not left implicit, and the actionable command a
reader would run is named in both the record and the tool's own output —
satisfies AC-3's "read" provenance requirement directly.

## MUST-NOT-1 — Present

canonical: `606f69cc:pipeline.py:391` (this session) —
`_report_managed_clone_staleness()`'s only git-touching call is
`_sp.checkout_staleness(root=d, fetch=True)`; `fetch=True` is
unconditional (not gated behind the TTL marker), so the report never
runs against a state that skipped its own fetch.

derived: `sed -n '2566,2634p' spawn.py | grep -n "reset\|checkout\|merge \|git\", \""` (this session, same worktree) —
result: the only git subcommands `checkout_staleness()` invokes are
`fetch --quiet origin`, `rev-parse HEAD`, `rev-parse origin/HEAD`,
`merge-base --is-ancestor`, and `rev-list --count` — no `reset`,
`checkout`, `merge`, `commit`, or `push` appears anywhere in the function
or in `_report_managed_clone_staleness()` itself. `checkout_staleness()`
predates this issue (landed by issue #2506, PR #2612,
`c87423c171c94aeef425bbf01876355e0ec6667d`) and was already independently
re-verified non-mutating in `docs/issue-2506/reports/conformance-review.md`'s
R2c — this session re-confirmed the same grep against the current tree
rather than carrying the prior verdict forward blind, since this PR calls
the function from two new call sites.

Rationale: the report path fetches unconditionally before ever judging
"current," and touches the working tree with no mutating git command —
both clauses of the must-not hold.

## NON-GOAL-1 — Present

canonical: `606f69cc:skills.py:73-81` (this session) —
`_skill_repo_managed_root()`'s existing-valid-clone branch calls
`_sp._pull_is_fresh(d)` / `_sp._run_net(...)` / `_sp._mark_pulled(d)` —
the identical three helpers `pipeline.core_root()` calls at
`606f69cc:pipeline.py:429-431` — before reaching
`_sp._report_managed_clone_staleness(d, "skill-repo")` at line 81. Same
helper names, same TTL semantics, same call order as `core_root()`.

Rationale: the skill-repository managed clone shares the identical
TTL-pull code path as the core rulebook clone (confirmed directly by
reading both call sites side by side, not by trusting the implementation
record's own claim), so wiring the same report into it is in scope under
the issue's own non-goal carve-out ("unless it shares the same code
path... check, and say which") rather than an out-of-scope addition.

## Open findings

canonical: `606f69cc:pipeline.py:429-431` and `606f69cc:skills.py:73-76`
(this session, worktree read) — both blocks discard the
`_run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"], ...)` return
value and call `_mark_pulled(d)` unconditionally on the next line,
regardless of the pull's `returncode`.

- **Pre-existing gap in the pull path itself, not a defect against this
  issue's acceptance** (same code shape as the implementation record's
  own "Open findings" section, cited above: a pull failure can still
  stamp the TTL marker as fresh, so a subsequent spawn inside the TTL
  window skips pulling while believing a pull just succeeded). This does
  not affect AC-1/AC-2: the new report line always independently
  fetches+compares via `checkout_staleness(fetch=True)`, regardless of
  whether the TTL marker itself is trustworthy, so the staleness report
  this issue asks for stays correct even when this separate bug fires.
  Not scored as a failure of this issue's acceptance for that reason.
  Resolution path: file a follow-up issue against `pipeline.core_root()` /
  `skills._skill_repo_managed_root()` to only call `_mark_pulled(d)` when
  the pull's `returncode == 0` — the same remedy the implementation record
  itself suggests.

## What did not work

None — this session performed only review actions (read, `pytest`,
`grep`, a scratch reproduction script, `git worktree`) against the
existing worktree; no code or test file governed by this PR was modified.

## Why

Re-executed every test the implementation PR cites, and additionally
reproduced both `check:` scenarios from the Acceptance section myself
against the real `_report_managed_clone_staleness()` function (a scratch
bare-repo fixture, not the implementation's own test file) rather than
trusting either the PR's pasted output or its test suite's framing —
per builder-blind convention (`docs/issue-2506/reports/conformance-review.md`
precedent). All three formal Acceptance bullets (AC-1/AC-2/AC-3), the
must-not clause, and the non-goal carve-out check verdicted Present. The
pull-path gap named under Open Findings above is out of this issue's
acceptance scope (it does not affect the staleness report's own
correctness) and was already disclosed by the implementation record, not
newly discovered by this review — recorded there with a resolution path
rather than scored as a failed requirement.

## Upstream basis

`docs/issue-2616/reports/silent-failure-audit+observability-explorability-d0acabc7.md`
is untracked in this checkout's own tree (commit
`606f69cc51fa59a6ba4dbff3b34dbeb7ad426829`, read via the worktree noted
at the top of this record) and is the implementation record this review
checked against issue #2616's own Acceptance text (not against the
record's self-assessment). `pipeline.py`, `skills.py`, and `spawn.py` at
the same commit are the code under review. `spawn.checkout_staleness()`
(issue #2506, `c87423c171c94aeef425bbf01876355e0ec6667d`) is the
pre-existing, separately-reviewed detector this PR reuses without
modification.

## Next steps

None — `loop_state: reported` is terminal for this record kind.
