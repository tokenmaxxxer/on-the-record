---
issue: 2395
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: PR #2404 (branch issue-2395/implementation)
    sha: a76df56f962f7206c2753a7d82638690828d235f
  - path: issue #2395 body (Ask / consumer report / Direction / Acceptance, 6 checks)
    sha: same-commit
subject: PR #2404 / issue-2395/implementation @ a76df56f962f7206c2753a7d82638690828d235f
test: issue #2395 Acceptance checks 1-6
result: failed
assertedBy: conformance-review (issue-2395)
---

# issue-2395 — conformance-review record

## What was done

Builder-blind conformance review of PR #2404 against issue #2395's six
Acceptance checks. The checks were split into 9 checkable requirement
items (checks 1 and 4 each bundle more than one obligation), each
independently re-derived against the PR's actual code — not against the
builder's own `a76df56f:docs/issue-2395/reports/implementation.md`
narrative, which was read after independent code inspection and, for
the code-level claims, after independently reproducing the relevant
commands myself in a fresh `git worktree add /tmp/pr2404-check
pr-2404-review` checkout of `a76df56f`, rather than trusting its pasted
transcripts as-is.

- The record's own "live spawn" evidence for Acceptance checks 1 and 3
  calls `spawn._spawn_one()` directly (bypassing `spawn.py main()`'s CLI
  argument parsing and its gate sequence entirely). Re-running the
  *actual* `spawn.py` CLI entry point this session, for the exact same
  repo+issue pair the record used for its "before/after" transcript
  (`tokenmaxxxer/on-the-record#1`), shows that entry point never reaches
  the new echo — it is refused earlier by a pre-existing gate
  (`require_requirement_linkage`), with a message that does not name a
  repo mismatch at all. See REQ-REPRO and REQ-CWD-WRONGREPO below; this
  is the review's central finding.
  canonical: `acceptance:` blocks below, this session, 2026-08-25.
- The three orchestrator-side cwd variants (Acceptance check 4) were
  independently re-run against `a76df56f`'s actual `spawn.py`, not read
  from the record. Two of the three verify as claimed; the third
  ("wrong repo root") does not, for the same reason as the point above.
  canonical: `acceptance:` blocks below, this session, 2026-08-25.
- The `gh_rest` unit-test claim (10/10) and the one named regression-fix
  test (`test_dry_run_non_refused_spawn_exits_zero`) were independently
  rerun this session and reproduced exactly as claimed.
  canonical: `acceptance:` blocks below, this session, 2026-08-25.
- The no-added-`gh`-round-trip latency claim (Acceptance check 2) was
  verified by Analysis (reading `gates/gh_rest.py:23-35,57-68` directly)
  rather than by re-running the record's own 5-rep network timing
  script, since the falsifiable part of the claim — whether a `gh` call
  was added — is a structural property of the code, not a timing
  measurement that needs re-executing to confirm (per
  conformance-review-verification-method-selection rule 1: inspection
  for a structural property, not execution).

acceptance: `git worktree add /tmp/pr2404-check pr-2404-review` (this session, `a76df56f`) — result:
```
HEAD의 현재 위치는 a76df56f입니다 issue-2395: add skill-verdict lines to implementation record
```

acceptance: `python3 spawn.py implementation "test" --issue 1 -C /tmp/pr2404-check/gates --dry-run` (this session, in the `a76df56f` worktree) — result:
```
-C 가 레포 루트가 아니라 그 하위 디렉터리다: /tmp/pr2404-check/gates
  실제 레포 루트: /tmp/pr2404-check
  cwd 가 생각하는 그 레포가 맞는지부터 확인해라 — -C /tmp/pr2404-check 로 다시 잡거나, 그 루트에서 -C 없이 불러라(이슈 #2395).
exit=1
```

acceptance: `python3 spawn.py implementation "test" --issue 1 -C /tmp/pr2404-does-not-exist --dry-run` (this session) — result:
```
-C 가 존재하지 않는 디렉터리다: /tmp/pr2404-does-not-exist
  cwd 는 레포 루트를 가리켜야 한다 — 경로를 다시 확인해라.
exit=1
```

acceptance: `python3 spawn.py implementation "test" --issue 1 -C /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2395-conformance-review --dry-run` (this session; the `-C` target is a real, valid, different git-repo-root checkout — the "wrong repo root" shape, and the same `on-the-record#1` issue the record's own live-demo used) — result:
```
[acceptance-gate] 경고: 이슈 #1 의 'Acceptance' 절이 지금 형식대로면 phase-2 승인 후 스폰이 거절된다:
  - 이슈 #1 본문에 '## Acceptance' 절이 없다 ...
이슈 #1 가 요구 연결이 없다:
  - 이슈 #1 본문이 요구 ID(`R\d+` 또는 'northpole req#<n>')를 하나도 인용하지 않고, 명시적 태그 'infrastructure/no-direct-requirement' 도 없다 ...
  세션을 안 띄운다 — 요구 ID(`R\d+` 또는 'northpole req#<n>')를 인용하거나 'infrastructure/no-direct-requirement' 태그를 달아야 한다(issue #1017, northpole req#6).
exit=1
```

acceptance: `python3 spawn.py implementation "test" --issue 2395 --dry-run` (this session, run from the `a76df56f` worktree's own root, no `-C` flag — the literal `cd repo && spawn.py <role> "<task>" --issue N` shape) — result:
```
{ ... role_settings JSON ... }
--model sonnet
exit=0
```

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py::GateRefusalExitCodeTest::test_dry_run_non_refused_spawn_exits_zero -q` (this session, `a76df56f` worktree) — result:
```
1 passed in 17.93s
```

acceptance: `python3 gates/test_gh_rest.py` (this session, `a76df56f` worktree) — result:
```
ok - t_owner_repo_parses_ssh_remote
ok - t_fetch_issue_body_returns_body_on_success
ok - t_fetch_issue_body_returns_none_on_rest_failure
ok - t_fetch_issue_body_returns_none_when_no_gh
ok - t_fetch_pr_body_returns_body_on_success
ok - t_fetch_issue_returns_title_and_body_together
ok - t_fetch_open_prs_uses_rest_never_graphql
ok - t_fetch_open_prs_requests_100_per_page
ok - t_fetch_open_prs_304_reuses_cache_no_fresh_body
ok - t_fetch_open_prs_returns_none_on_rest_failure
10/10 passed
```

## Why

Contract v3's verify-at-landing convention requires re-executing evidence
rather than accepting a builder's self-report. "Builder-blind" for this
role means the implementation record (`a76df56f:docs/issue-2395/reports/implementation.md`)
was treated throughout as a claim to be checked against the code and,
where practical, live re-execution — not as evidence in itself. Doing so
surfaced a real gap between what the record's evidence demonstrates and
what Acceptance checks 3 and 4 actually require: `spawn._spawn_one()`,
called directly, is not the same code path as `spawn.py`'s real CLI
entry point, because `main()` runs `require_acceptance_gate` and
`require_requirement_linkage` *before* calling `_spawn_one()`
(`a76df56f:spawn.py:1706-1707,1718`), and the new echo logic lives
*inside* `_spawn_one()` (`a76df56f:spawn.py:2364-2370`, inside the
`_run_auto_sweep` closure at `spawn.py:2276`). A demonstration that
skips straight to `_spawn_one()` cannot show whether those two
pre-existing gates would have refused the spawn first in a real
invocation — and, re-run through the real entry point, they do, for the
exact repo+issue pair the record chose.
canonical: the `-C .../on-the-record-issue-2395-conformance-review` and
`--issue 2395 --dry-run` `acceptance:` blocks above, this session,
2026-08-25.

## What did not work

None.
canonical: the `acceptance:` blocks in "What was done" above, this
session, 2026-08-25.

## Upstream basis

- issue #2395 body — the frozen Ask / consumer report / Direction /
  Acceptance sections this review checks against.
  canonical: `gh issue view 2395` (this session, 2026-08-25).
- PR #2404, branch `issue-2395/implementation`, head commit
  `a76df56f962f7206c2753a7d82638690828d235f` — the artifact under review.
  sha: a76df56f962f7206c2753a7d82638690828d235f
  canonical: `gh pr view 2404`, `gh pr diff 2404`, and
  `git fetch origin pull/2404/head:pr-2404-review` (this session,
  2026-08-25).
- `a76df56f:docs/issue-2395/reports/implementation.md` — read for its
  own evidence and reasoning, cross-checked rather than trusted; where
  its claims were independently reproduced (the two unit-test runs) this
  record says so explicitly; where re-execution surfaced a gap (the
  `_spawn_one()`-direct demonstration vs. the real CLI entry point) this
  record says that explicitly too, rather than restating the claim as
  fact.

## Requirement findings

---
requirement: "the resolved `owner/repo#<n>` and the issue title appear in the spawn's own stdout preamble" (dimension: functional)
spec_ref: issue #2395, Acceptance check 1, clause 1 ("appear in the spawn's own stdout preamble")
verdict: Present
evidence: `a76df56f:spawn.py:2364-2370` builds `resolved_line` from `resolved_owner`/`resolved_repo`/`title` (all sourced from the single `gh_rest.fetch_issue()` response at `spawn.py:2342-2348`) and unconditionally `print()`s it (no `file=sys.stderr`) as `[{role}] {resolved_line.strip()}` — reached whenever `_run_auto_sweep`'s issue-fetch block executes, i.e. on every `--issue`-scoped spawn that reaches that point.
rationale: The print is unconditional on this line being reached, and both facts (owner/repo#n, title) come from one shared string built once — a partial build (e.g. title present but repo absent) is structurally impossible here since both are read from the same dict in the same block.
canonical: read via the `a76df56f` worktree this session, 2026-08-25; corroborated by the `a76df56f:docs/issue-2395/reports/implementation.md` live-demo transcripts, not independently re-run over network by this session (see "Why").
---

---
requirement: "the resolved `owner/repo#<n>` and the issue title appear in ... the role session's injected directive" (dimension: functional)
spec_ref: issue #2395, Acceptance check 1, clause 2 ("in the role session's injected directive")
verdict: Present
evidence: `a76df56f:spawn.py:2385` (`task = _dp("issue-preamble-index", ... + resolved_line + req_line + goal_pin + ...)`) prepends the exact same `resolved_line` string used for the stdout print into the directive text handed to the spawned role session, immediately after the `당신의 이슈: #<n> ...` line, unconditionally — unlike the pre-existing `이슈 제목(원본 목표):` line inside `goal_pin`, which only appears when the issue body has an `## Acceptance` section.
rationale: Same shared-string reasoning as the stdout requirement above; the fix is genuinely unconditional where the pre-existing title surfacing was not.
canonical: read via the `a76df56f` worktree this session, 2026-08-25.
---

---
requirement: "measured before/after per-spawn latency for the echo, confirming no added `gh` round-trip" (dimension: non-functional)
spec_ref: issue #2395, Acceptance check 2
verdict: Present
evidence: `a76df56f:gates/gh_rest.py:23-35` (`owner_repo()`) issues one local `git remote get-url origin` subprocess call, never a `gh` call. `a76df56f:gates/gh_rest.py:57-68` (`fetch_issue()`) calls `owner_repo()` once more on top of the call `_api_json()` already makes internally to build the REST path (`gh_rest.py:40`) — i.e. the change adds one extra *local* `git` call per `fetch_issue()`, never a `gh` network call.
rationale: This is a structural property of the code (does a new call site invoke `gh` or not), correctly checked by Inspection rather than by re-running the record's own network timing script (conformance-review-verification-method-selection rule 1). The record's own 5-rep measurement (474.2ms → 469.9ms avg, gh-call-count unchanged at 5, git-call-count 5→10) is consistent with this code-level reading and is not disputed.
canonical: read via the `a76df56f` worktree this session, 2026-08-25.
---

---
requirement: "live reproduction of the consumer's exact failure (spawn for issue N from a cwd whose repo also has an issue N, both existing) shows the wrong-repo resolution named in the output — before/after transcript" (dimension: edge-case)
spec_ref: issue #2395, Acceptance check 3
verdict: Incorrect
evidence: The record's reproduction (`a76df56f:docs/issue-2395/reports/implementation.md`, "Acceptance check — live reproduction...") calls `spawn._spawn_one()` directly for `-C /tmp/otr-clean --issue 1` (`tokenmaxxxer/on-the-record#1`) and pastes a transcript where the echo appears. Re-running the *actual* `spawn.py` CLI — the entry point a real consumer uses, and the one `main()` wires `require_repo_root`/`require_acceptance_gate`/`require_requirement_linkage` into ahead of `_spawn_one()` (`a76df56f:spawn.py:1703-1707,1718`) — for the identical repo+issue pair this session (see the "wrong repo root" `acceptance:` block above) produces `exit=1` at `require_requirement_linkage`, with no repo-mismatch content in the message at all: "이슈 #1 가 요구 연결이 없다 ... 세션을 안 띄운다." The echo this check requires is never reached.
spec_vs_built: The check requires a transcript through a live spawn that shows the wrong-repo resolution named in the output for a real, existing same-numbered-issue pair. What was built and demonstrated instead re-derives the echo through an internal function call that bypasses two of the four gates `main()` actually runs before a real spawn — for the exact pair chosen, the real CLI never reaches the code under test, so the "before/after transcript" does not represent what a consumer running `spawn.py` would actually see for that pair.
rationale: This is not a borderline reading — it is a directly reproduced, deterministic `exit=1` at a named pre-existing gate, for the identical command shape and identical repo/issue the record itself selected. It also matches the issue body's own account of a real prior incident with the identical failure signature (the issue's "#574 conformance-review 재스폰이 'no requirement linkage'로 거절됐다 — 같은 원인, on-the-record 의 #574 를 채점"), which this PR does not fix.
canonical: the "wrong repo root" `acceptance:` block above, this session, 2026-08-25.
---

---
requirement: "the cwd variant 'non-repo-root subdirectory' produces a message naming the actual problem — 'cwd is not the repo you think' — rather than a downstream symptom" (dimension: error-handling)
spec_ref: issue #2395, Acceptance check 4, variant 1 (`-C on-the-record`, "a plugin content subdirectory, not a repo root")
verdict: Present
evidence: `a76df56f:board.py:232-241` (`require_repo_root`'s third branch); re-run this session against a real subdirectory, `-C /tmp/pr2404-check/gates`.
rationale: The message directly states "cwd 가 생각하는 그 레포가 맞는지부터 확인해라" (check whether cwd is the repo you think it is first) and names the real repo root — this is the requirement's quoted phrasing almost verbatim, not a downstream gate's unrelated symptom.
canonical: the `-C /tmp/pr2404-check/gates` `acceptance:` block above, this session, 2026-08-25.
---

---
requirement: "the cwd variant 'wrong repo root' produces a message naming the actual problem — 'cwd is not the repo you think' — rather than a downstream symptom" (dimension: error-handling)
spec_ref: issue #2395, Acceptance check 4, variant 2 (`-C /home/jwjung/tokenmaxxxer`, "wrong repo entirely for a core issue")
verdict: Incorrect
evidence: `a76df56f:board.py:202-215` (`require_repo_root`'s own docstring) explicitly scopes the gate to exactly three structural cases — nonexistent path, not-a-git-repo, subdirectory-of-a-repo — and explicitly excludes "wrong repo entirely" by design, deferring to the echo. Re-run this session for a real, valid, different repo root produces the pre-existing, unrelated `require_acceptance_gate`/`require_requirement_linkage` refusal shown in REQ-REPRO above — the same "downstream symptom" class (an unrelated gate message with no repo-mismatch content) the issue's own "Not consumer-only" paragraph names as the problem for this exact variant ("Acceptance 절이 없다").
spec_vs_built: The check requires this variant to produce a message naming "cwd is not the repo you think," same as the other two variants. What was built produces, for the realistic case where the wrong repo's same-numbered issue fails a pre-existing gate (as the issue's own two self-reported incidents for this variant did — "Acceptance 절이 없다" and "no requirement linkage"), the exact same unrelated gate message as before this PR, with zero repo-mismatch content. Where the wrong repo's issue happens to pass those gates, the only signal is the informational echo line (REQ-STDOUT/REQ-DIRECTIVE) — a statement of resolved fact the reader must notice is unexpected, not a message that itself names "cwd is not the repo you think" the way the other two variants' refusals do.
rationale: Incorrect, not Surface: `require_repo_root` does not silently fail to fire on this condition by accident — it is deliberately scoped to exclude it, and the code path that was supposed to be this variant's stated defense (the echo) provably does not survive the pre-existing gates for the issue's own cited real incidents. Incorrect, not Absent: an echo mechanism was genuinely added and does help in the subset of wrong-repo cases whose issue happens to be gate-shaped-valid — it is not a total non-attempt, just one that fails on the condition (a gate-failing target issue) the issue's own report shows is common.
canonical: the "wrong repo root" `acceptance:` block above, this session, 2026-08-25.
---

---
requirement: "the cwd variant 'non-existent path' produces a message naming the actual problem — 'cwd is not the repo you think' — rather than a downstream symptom" (dimension: error-handling)
spec_ref: issue #2395, Acceptance check 4, variant 3 (`-C .../tokenmaxxxer-core`, "a path that no longer exists")
verdict: Present
evidence: `a76df56f:board.py:224-227` (`require_repo_root`'s first branch); re-run this session against a real nonexistent path, `-C /tmp/pr2404-does-not-exist`.
rationale: The message names the actual cause ("-C 가 존재하지 않는 디렉터리다") rather than the pre-existing downstream symptom this variant used to produce (an `approvers.md` or later-gate error). It does not use the literal phrase "cwd is not the repo you think," but a nonexistent path has no repo to be mistaken about — naming the path as nonexistent is the correct-shaped equivalent for this specific variant, and is a strict improvement over the prior undifferentiated failure.
canonical: the `-C /tmp/pr2404-does-not-exist` `acceptance:` block above, this session, 2026-08-25.
---

---
requirement: "the normal consumer call shape (`cd repo && spawn.py <role> \"<task>\" --issue N`, no path flag) still works unchanged — demonstrated, not asserted" (dimension: scope-boundary)
spec_ref: issue #2395, Acceptance check 5
verdict: Present
evidence: Re-run this session from the `a76df56f` worktree's own root, no `-C` flag: `python3 spawn.py implementation "test" --issue 2395 --dry-run` exits 0 with a normal `role_settings` JSON payload, matching pre-existing `--dry-run` output shape.
rationale: This is a live demonstration of the literal no-flag shape the check names, not an inference from the "paths are equal" check the record itself substitutes (`a76df56f:docs/issue-2395/reports/implementation.md`, "Acceptance check — normal consumer call shape unchanged," which only shows `pwd` matching `git rev-parse --show-toplevel` — true of any repo root and not itself a spawn demonstration). Re-deriving the actual demonstration this session closes that gap.
canonical: the `--issue 2395 --dry-run` `acceptance:` block above, this session, 2026-08-25.
---

---
requirement: "if the delivery adds any refusal path, the record states which legitimate spawns it could block and why that is acceptable" (dimension: scope-boundary)
spec_ref: issue #2395, Acceptance check 6, first branch (the delivery does add a refusal path, so the second branch — "if it adds none, the record states why echo alone is sufficient" — does not apply)
verdict: Present
evidence: `a76df56f:docs/issue-2395/reports/implementation.md`, "Acceptance check — refusal-path honesty" states the two refused shapes were already-certain failures before this PR (no currently-working call shape is newly blocked) and gives the reason the third shape is deliberately not refused (no `--repo` flag exists to conflict-check against).
rationale: The check asks whether the record *states* this reasoning, which it does. This verdict is Present on that literal question only — it does not certify that the stated reasoning is sound: REQ-CWD-WRONGREPO above shows the "echo alone is sufficient" half of that reasoning does not hold for the issue's own cited real incidents, because the echo does not survive the pre-existing gates. A reader relying on this Present verdict alone, without also reading REQ-CWD-WRONGREPO, would be misled about the delivery's actual coverage.
canonical: read via the `a76df56f` worktree this session, 2026-08-25.
---

## Open findings

- REQ-REPRO (Incorrect) and REQ-CWD-WRONGREPO (Incorrect) are one root
  cause, not two independent defects: the new echo (`spawn.py:2364-2370`)
  lives inside `_spawn_one()`, downstream of `main()`'s pre-existing
  `require_acceptance_gate`/`require_requirement_linkage` calls
  (`spawn.py:1706-1707`). For a wrong-repo cwd whose resolved issue fails
  either of those two gates — which is exactly what happened in both of
  the issue's own self-reported incidents for this variant
  ("Acceptance 절이 없다", "no requirement linkage") — the spawn is
  refused before the echo ever prints, so the orchestrator sees the
  same undifferentiated downstream symptom this issue exists to
  eliminate. Resolution path: either move a repo/issue-identity echo
  ahead of those two gates (independent of whether the target issue is
  gate-shaped-valid), or have `require_acceptance_gate`/
  `require_requirement_linkage`'s own refusal messages include the
  resolved `owner/repo#n` they are refusing, so the mismatch is visible
  even when the spawn is blocked. Left to a future session to decide
  and build — this review does not patch what it finds.
  canonical: the "wrong repo root" `acceptance:` block above, this
  session, 2026-08-25.
- All other findings (REQ-STDOUT, REQ-DIRECTIVE, REQ-LATENCY,
  REQ-CWD-SUBDIR, REQ-CWD-NOTEXIST, REQ-NORMAL-SHAPE,
  REQ-REFUSAL-DISCLOSURE): none — independently re-verified as Present
  this session, per the `acceptance:` blocks cited in each finding above.

## Next steps

None — `loop_state: reported`. The open finding above names its own
resolution path for whichever session picks it up next; this record
does not implement it.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; issue #2395's six Acceptance checks were split into 9 checkable, dimension-tagged requirement items above (checks 1 and 4 each bundled more than one obligation under "and").
skill-verdict: conformance-review-verification-method-selection — applied: invoked; Inspection used for the gh-round-trip structural claim (REQ-LATENCY) instead of re-running network timing; Test-method reuse (rule 4) for the two existing-test reruns; Demonstration/live re-execution used for the cwd-gate and normal-shape claims rather than trusting the record's pasted transcripts.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; Incorrect (not Absent/Surface) assigned to REQ-REPRO and REQ-CWD-WRONGREPO per rule 2, each with its failing clause named via spec_vs_built per rule 5; both re-checked once against live code before finalizing per rule 6.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every finding cites file:line plus the `a76df56f` commit sha and, where re-executed, the exact command this session ran, per rules 1 and 3 (backward-traced each clause to the live issue #2395 body before checking its implementation).
skill-verdict: conformance-review-finding-record — applied: invoked; all 9 finding blocks carry the full field list (requirement/spec_ref/verdict/evidence/rationale, plus spec_vs_built on both Incorrect verdicts); no verdict was written without an evidence pointer and spec_ref.
skill-verdict: conformance-review-sampling-derivation — not-applicable: all 6 Acceptance checks and both PR-touched non-test/non-log source files (`board.py`, `gates/gh_rest.py`; `spawn.py`'s changed hunks) were reviewed in full — the change is small enough that full enumeration was feasible, so no sampling scope was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting; it stops at fidelity verdicts (Present/Incorrect) per the base conformance-review task.
skill-verdict: implementation-audit — not-applicable: this session is the independent evaluator half of that protocol as already structured by the conformance-review role itself (builder-blind review of a separate builder session's PR); the skill's own procedure (extractor session + independent evaluator session) is what this role assignment already implements, not a separate technique to additionally invoke.
other mounted skills: not triggered (freelunch:freelunch-code-fanout, freelunch:freelunch-site-fanout, terse:terse, dataviz, update-config, keybindings-help, code-review, simplify, fewer-permission-prompts, loop, schedule, claude-api, run, init, security-review) — none apply to a docs-only conformance review of a small, already-scoped PR.
