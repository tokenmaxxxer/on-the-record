---
issue: 2383
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: PR #2389 (branch issue-2383/implementation)
    sha: ef762a9fd5e1b4d1424f2bdf168b887a2d369a43
  - path: issue #2383 body (Acceptance section, 3 checks)
    sha: same-commit
subject: PR #2389 / issue-2383/implementation @ ef762a9fd5e1b4d1424f2bdf168b887a2d369a43
test: issue #2383 Acceptance checks 1-3
result: failed
assertedBy: conformance-review (issue-2383)
---

# issue-2383 — conformance-review record

## What was done

Builder-blind conformance review of PR #2389 against issue #2383's three
Acceptance checks. The issue's three checks were split into seven
checkable requirement items (two of the three bundle more than one
obligation), each independently verified against the PR's actual diff
and code — not against the builder's own
`ef762a9f:docs/issue-2383/reports/implementation.md` narrative, which was
read only after independent evidence-gathering, to cross-check its
claims rather than substitute for them.

- `role_model.txt` is untracked on both `main` and the PR branch, so
  gitignoring it is a real fix, not a no-op.
  canonical: `git ls-files | grep -x role_model.txt` (this session's own
  working directory, `main`) — no output; `git ls-tree -r
  issue-2383/implementation --name-only | grep -x role_model.txt` (this
  session) — no output.
- `roles/implementation.json` (the issue's own named example) is a
  tracked file, so its corruption remains a live, in-scope risk this PR
  leaves unaddressed.
  canonical: `git ls-files | grep -x roles/implementation.json` (this
  session's own working directory) — output `roles/implementation.json`.
- The PR's claimed test run was independently reproduced in a fresh
  worktree of `ef762a9f`, not merely read from the PR body.
  canonical: see `acceptance:` block below.
- Both of the PR's inline (uncommitted) smoke tests were independently
  re-derived against the actual `lifecycle._prune_worktrees` and
  `spawn._set_origin_head` functions at `ef762a9f`, in throwaway repos
  under `/tmp` this session created and ran directly, plus one additional
  case the PR's own smoke tests did not cover (a worktree whose
  directory is still present but old), specifically to check Acceptance
  check 2's "age" clause.
  canonical: see `acceptance:` blocks below.

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py test/test_spawn_model_override.py gates/test_clean_reconcile_safety.py -q -n auto` (run this session, in a `git worktree add /tmp/conf-review-2389 issue-2383/implementation` checkout of `ef762a9f`) — result:
```
........................................................................ [ 69%]
.........x.....................                                          [100%]
102 passed, 1 xfailed in 42.35s
```

acceptance: `lifecycle._prune_worktrees(repo)` against a real git repo with an orphaned worktree registration (script run inline this session against `ef762a9f`'s `lifecycle.py`, not committed) — result:
```
--- worktree list before prune ---
/tmp/conf-smoke/repo       f96eb76 [master]
/tmp/conf-smoke/orphan-wt  f96eb76 [orphtest] prunable
--- running _prune_worktrees ---
worktree 목록 (정리 전 2개):
  /tmp/conf-smoke/repo       f96eb76 [master]
  /tmp/conf-smoke/orphan-wt  f96eb76 [orphtest] prunable
worktree prune: Removing worktrees/orphan-wt: gitdir file points to non-existent location
--- worktree list after prune ---
/tmp/conf-smoke/repo  f96eb76 [master]
```

acceptance: `lifecycle._prune_worktrees(repo)` against a worktree whose directory is still present but backdated 90 days (script run inline this session against `ef762a9f`'s `lifecycle.py`, not committed; probes the "age" clause the PR's own smoke tests did not cover) — result:
```
--- worktree list before prune (dir still present, just old) ---
/tmp/conf-smoke/repo                f96eb76 [master]
/tmp/conf-smoke/old-but-present-wt  f96eb76 [oldtest]
worktree 목록 (정리 전 2개):
  /tmp/conf-smoke/repo                f96eb76 [master]
  /tmp/conf-smoke/old-but-present-wt  f96eb76 [oldtest]
--- worktree list after prune: is the old-but-present one gone? ---
/tmp/conf-smoke/repo                f96eb76 [master]
/tmp/conf-smoke/old-but-present-wt  f96eb76 [oldtest]
--- dir still on disk after prune? ---
/tmp/conf-smoke/old-but-present-wt
```

acceptance: `spawn._set_origin_head(work_dir)` against a real two-repo git setup (origin + clone) with a renamed default branch, called without a prior fetch (script run inline this session against `ef762a9f`'s `spawn.py`, not committed) — result:
```
origin/HEAD before _set_origin_head: origin/main
returncode: 1  error: 올바른 레퍼런스가 아닙니다: refs/remotes/origin/trunk
origin/HEAD after _set_origin_head: origin/main
```

acceptance: same setup, `git fetch origin` run first (matching the production `_fetch_or_halt(...).after=` call order) — result:
```
--- after fetch, before set-head ---
origin/main
origin/HEAD before _set_origin_head: origin/main
returncode: 0 origin/HEAD set to trunk
origin/HEAD after _set_origin_head: origin/trunk
```

## Why

Contract v3's verify-at-landing convention requires re-executing evidence
rather than accepting a builder's self-report; "builder-blind" for this
role additionally means the implementation record was treated as a claim
to be checked against the diff and live re-execution, not as evidence in
itself.

- Both non-Present verdicts below (Absent / Incorrect) surfaced only
  because underlying artifact state was checked directly this session.
  canonical: the `acceptance:` and `canonical:` entries in the section
  above this one are this session's own re-derivations, 2026-08-25.

## What did not work

- The Absent verdict (roles/implementation.json) rests on the
  `git ls-files` check in the section above plus the PR's own disclosure
  agreeing with it — no second re-check pass was needed.
  canonical: `git ls-files | grep -x roles/implementation.json` output
  cited above, this session, 2026-08-25.
- The Incorrect verdict (worktree age) rests on this session's own
  reproduced smoke test above — not a borderline reading needing a
  second pass.
  canonical: `acceptance:` block "against a worktree whose directory is
  still present but backdated 90 days" above, this session, 2026-08-25.

## Upstream basis

- issue #2383 body — the frozen Acceptance section this review checks
  against.
  canonical: `gh issue view 2383 --json title,body,state,labels` (this
  session, 2026-08-25).
- PR #2389, branch `issue-2383/implementation`, head commit
  `ef762a9fd5e1b4d1424f2bdf168b887a2d369a43` — the artifact under review.
  sha: ef762a9fd5e1b4d1424f2bdf168b887a2d369a43
  canonical: `gh pr view 2389 --json title,body,state,headRefName,...`
  and `git fetch origin issue-2383/implementation:issue-2383/implementation`
  (this session, 2026-08-25).
- `ef762a9f:docs/issue-2383/reports/implementation.md` (commit-pinned;
  this path does not exist in this session's own checkout, whose HEAD is
  `issue-2383/conformance-review` — read via `git show
  ef762a9f:docs/issue-2383/reports/implementation.md`, this session) —
  read for its own Open Findings disclosures, cross-checked rather than
  trusted; where its claims were independently reproduced (test run,
  both smoke tests) this record says so explicitly above rather than
  restating them as fact.

## Requirement findings

---
requirement: "audit what regularly leaves untracked/modified files in the orchestrator's own CHECKOUT working tree between sessions" (dimension: scope-boundary)
spec_ref: issue #2383, Acceptance check 1, clause 1 ("audit ... between sessions")
verdict: Present
evidence: `ef762a9f:docs/issue-2383/reports/implementation.md:182-232` (Open findings section) documents concrete, cited greps across both `tokenmaxxxer/on-the-record` and the separate `muster` checkout for `roles/*.json` writers and `git worktree add` call sites; `ef762a9f:docs/issue-2383/reports/implementation.md:25-38` (item 1 of "What was done") cites `ef762a9f:gates/check_runner.py:22,484` and a `git status --porcelain` run for the `.on-the-record/directive/` finding.
rationale: The audit is not merely asserted, each finding cites the actual command run and its output — Analysis-method evidence (tracing code/greps), sufficient for a structural "was an audit performed" check.
canonical: read via `git show ef762a9f:docs/issue-2383/reports/implementation.md`, this session, 2026-08-25.
---

---
requirement: "either gitignore intentional scratch ... [files]" (dimension: functional)
spec_ref: issue #2383, Acceptance check 1, clause 2a ("gitignore intentional scratch")
verdict: Present
evidence: `ef762a9f:.gitignore` lines 3-5 add `.on-the-record/check-run-artifact.json`, `.on-the-record/directive/`, `role_model.txt`.
rationale: The three added entries are verified-untracked on both `main` and the PR branch, matching the "intentional scratch" case the clause names, rather than silently gitignoring a file still under version control.
canonical: `git show ef762a9f:.gitignore`, `git ls-files | grep -x role_model.txt` (no match, `main`), `git ls-tree -r issue-2383/implementation --name-only | grep -x role_model.txt` (no match) — all this session, 2026-08-25.
---

---
requirement: "... or fix the process writing garbage into tracked files (e.g. roles/implementation.json getting emptied)" (dimension: functional)
spec_ref: issue #2383, Acceptance check 1, clause 2b, named example
verdict: Absent
evidence: `ef762a9f:docs/issue-2383/reports/implementation.md:184-201` (first Open findings bullet, "`roles/implementation.json`'s corruption is not root-caused") states no writer for this file was found after grepping both repos, and no fix was applied to it. `git diff main...issue-2383/implementation` (this session) confirms none of the four changed files (`.gitignore`, `lifecycle.py`, `spawn.py`, `tests/test_spawn_pipeline.py`) touch `roles/implementation.json` or any code path that writes it.
rationale: The issue names this file as its concrete illustration of the "fix the process" remedy path; the builder's own record confirms the corrupting process was never located, only filed as an open finding for a future session. Absent is the correct verdict (nothing addresses the requirement) rather than Incorrect (which would require an attempted-but-wrong fix).
canonical: `git ls-files | grep -x roles/implementation.json` (this session, `main` — match, i.e. tracked and still exposed); `git diff main...issue-2383/implementation --name-only` (this session) — `.gitignore lifecycle.py spawn.py tests/test_spawn_pipeline.py`, no `roles/` path.
---

---
requirement: "`git worktree list` count ... is monitored/pruned (`git worktree prune` or equivalent) as part of routine landing/cleanup" (dimension: functional)
spec_ref: issue #2383, Acceptance check 2, clause 1 ("count ... monitored/pruned ... routine landing/cleanup")
verdict: Present
evidence: `ef762a9f:lifecycle.py:694-712` (`_prune_worktrees`, new), `ef762a9f:lifecycle.py:716,726` (`roster_clean()` now calls it when a `repo` is passed), `ef762a9f:spawn.py:1490-1491` (`spawn.py clean` CLI dispatch passes `Path(a.cwd).resolve()`); `ef762a9f:on-the-record/commands/run.md:688` documents `spawn.py clean` as the operator's routine post-merge-landing cleanup step.
rationale: This session's own re-run smoke test confirms the count-of-registered-but-backing-dir-gone case is genuinely pruned, printing the pre-prune list first, and the call site is wired into the documented routine-cleanup entry point rather than a stray unused function.
canonical: `acceptance:` block "`lifecycle._prune_worktrees(repo)` against a real git repo with an orphaned worktree registration" above, this session, 2026-08-25.
---

---
requirement: "`git worktree list` ... age is monitored/pruned (`git worktree prune` or equivalent) as part of routine landing/cleanup, not left to accumulate indefinitely" (dimension: edge-case)
spec_ref: issue #2383, Acceptance check 2, clause 2 ("age ... monitored/pruned")
verdict: Incorrect
evidence: `ef762a9f:lifecycle.py:694-712` (`_prune_worktrees`) only calls `git worktree list` (printed, no age comparison) and `git worktree prune -v`, which by `git-worktree(1)` semantics only removes entries whose backing directory no longer exists — it is indifferent to how long a still-present worktree has gone unused.
spec_vs_built: Spec requires worktree *age* to be monitored/pruned so accumulation is bounded over time, independent of directory existence. What was built only removes registrations for worktrees whose directory is already gone (existence, not age) and never reports or acts on a still-present worktree's age — the issue's own observed evidence ("30+ ... worktrees still registered ... never pruned") is only partly covered by this fix: caught if the backing dir has since vanished, not caught if merely old and idle.
rationale: This session's own reproduction (a worktree directory backdated 90 days survived `_prune_worktrees` unchanged and unflagged) directly demonstrates the code performs a real check that does not fire on the condition the clause names ("age"). Incorrect, not Absent, because a worktree-cleanup mechanism was genuinely added and does something — just not the age-bounding this clause requires; Incorrect, not Surface, because the "count" half of check 2 (previous requirement) is a real, functioning check, only the "age" half is unmet.
canonical: `acceptance:` block "`lifecycle._prune_worktrees(repo)` against a worktree whose directory is still present but backdated 90 days" above, this session, 2026-08-25.
---

---
requirement: "determine whether stale worktrees/refs contributed to #2379's corrupted merge-base" (dimension: functional)
spec_ref: issue #2383, Acceptance check 3, clause 1 ("determine whether ... contributed")
verdict: Present
evidence: `ef762a9f:docs/issue-2383/reports/implementation.md:146-165` ("What did not work" — documents and corrects an initial mistrace into a separate, stale `muster` checkout) and `ef762a9f:docs/issue-2383/reports/implementation.md:90-107` (item 4 of "What was done" — identifies the specific code asymmetry: `board.py:715-725`'s `_base()` trusts a present `origin/HEAD` symref unconditionally, and `issue_workspace()`'s reuse paths, unlike its new-clone path, never refreshed it after issue #221).
rationale: This is Analysis-method evidence (the actual #2379 workspace state cannot be reproduced after the fact) reaching a specific, falsifiable, code-grounded hypothesis rather than a guess. The record itself calls this "a plausible #2379 mechanism," not a forensically confirmed one — this review treats that as the practical ceiling for "determine" on an already-resolved historical incident with no surviving corrupted workspace to inspect. Present is assigned because a genuine determination effort produced a concrete, checkable finding, not because certainty was reached; the causal link to #2379 specifically should be read as evidenced-but-unconfirmed.
canonical: read via `git show ef762a9f:docs/issue-2383/reports/implementation.md`, this session, 2026-08-25.
---

---
requirement: "... and if so, fix the branch-cut step to be immune to it" (dimension: functional, conditional on the prior requirement's outcome)
spec_ref: issue #2383, Acceptance check 3, clause 2 ("if so, fix")
verdict: Present
evidence: `ef762a9f:spawn.py:1703-1717` (`_set_origin_head`, new helper), wired via `after=` at `ef762a9f:spawn.py:1762` (cwd-is-workspace reuse path) and `ef762a9f:spawn.py:1787` (existing-directory reuse path); `ef762a9f:spawn.py:1831` shows the pre-existing new-clone path already had equivalent inline logic, now deduplicated through the same helper.
rationale: This session's own re-run smoke tests (direct call without a prior fetch fails as expected since the local remote-tracking ref does not exist yet; with `git fetch origin` first, matching the real `_fetch_or_halt(...).after=` call order, `origin/HEAD` correctly flips from stale `origin/main` to correct `origin/trunk`) confirm the fix functions as claimed and is wired at the same three call sites the diff shows.
canonical: `acceptance:` blocks "`spawn._set_origin_head(work_dir)` against a real two-repo git setup..." (both variants) above, this session, 2026-08-25.
---

## Open findings

- REQ-1c (Absent) and REQ-2b (Incorrect) above are the two conformance
  gaps this review found. REQ-1c matches the PR's own first Open
  Finding; REQ-2b is a review-only finding — the PR's own smoke tests
  never probed the still-present-but-old worktree case this session
  added.
  canonical: requirement findings section above, this record, 2026-08-25.
  resolution path: for REQ-1c, a future session needs live capture of
  the corrupting process (parent PID/cwd/argv at time of write), per the
  PR's own resolution path, since static grepping across both repos has
  now been exhausted twice (once by the PR, once by this review). For
  REQ-2b, a future session should add an age-threshold check to
  `lifecycle._prune_worktrees` (e.g. flag/report or `git worktree remove
  --force` any entry whose directory mtime exceeds a bound, mirroring
  `auto_sweep()`'s existing `max_age_days` pattern for workspace
  directories) rather than relying on `git worktree prune`'s
  existence-only semantics.
- `_prune_worktrees` is wired only into the manual `spawn.py clean` path
  (`roster_clean()`), not into `auto_sweep()`, the automatic spawn-time
  sweep issue #1179 added specifically because `roster_clean()`/
  `spawn.py clean` was "manual-only".
  canonical: `git show ef762a9f:docs/issue-1179/proposals/automatic-lifecycle-cleanup.md`
  line 16 ("Workspace clones under ~/.tokenmaxxxer/work accumulate
  unboundedly because spawn.py clean is manual-only"), read this
  session, 2026-08-25; `git show ef762a9f:lifecycle.py` (`auto_sweep()`
  definition, this session) shows it does not call `_prune_worktrees` or
  `roster_clean()`.
  This is not scored as a requirement failure above because
  `ef762a9f:on-the-record/commands/run.md:688` documents `spawn.py
  clean` as the actual routine post-merge-landing step operators are
  instructed to run, which is what Acceptance check 2's "routine
  landing/cleanup" wording appears to reference — but a reader should
  know the worktree sweep does not run unattended the way
  `auto_sweep()`'s workspace-age bounding does.
  resolution path: a future session should decide whether worktree
  pruning belongs in `auto_sweep()` too, or whether the manual `spawn.py
  clean` step is the intended enforcement point long term.
- `.orchestrate-hook-fires.log`, disclosed in the PR's own Open Findings
  as a live, currently-unfixed instance of the exact bug class
  acceptance check 1 asks about (a tracked, unboundedly-growing
  append-only log), is out of this PR's stated scope and not one of the
  issue's three named checks, so it is not scored as a requirement
  above.
  canonical: `git show ef762a9f:docs/issue-2383/reports/implementation.md`
  lines 225-238, read this session, 2026-08-25.
  resolution path: builder's own proposal stands — a follow-up issue
  applying the same per-session sharding issue #2333 used for
  `consult-log`.

## Next steps

None — `loop_state: reported`, this record is terminal for the
conformance-review role. The three open findings above each carry their
own resolution path for a future session; this review does not open a
follow-up issue itself.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; split issue #2383's two multi-clause Acceptance checks (1 and
2) into 5 line items plus check 3's conditional pair, tagged each with a
dimension, in "Requirement findings" above.
skill-verdict: conformance-review-verification-method-selection —
applied: invoked; Analysis for the audit/determination items (REQ-1a,
REQ-3a — historical/unreproducible), Inspection for the gitignore item
(REQ-1b — structural), Demonstration/re-run for the worktree-prune and
origin/HEAD items (REQ-2a, REQ-2b, REQ-3b — this session's own
`acceptance:` smoke-test re-derivations rather than a read-only code
inspection), Test-reuse for the pytest suite (`acceptance:` block,
re-running the PR's own cited test command rather than deriving a
parallel check).
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
Absent (not Incorrect) for REQ-1c since no fix was attempted, only
disclosed as unresolved; Incorrect (not Surface or Absent) for REQ-2b
since a real, functioning-but-wrong-scope check was added; named the
failing clause via `spec_vs_built` for both non-Present verdicts.
skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; all evidence citations pinned to `ef762a9f:<path>:<line>`
rather than a bare working-tree path (this session's own checkout HEAD
is a different branch), with a `canonical:`/`acceptance:` tag per claim
naming the exact command run.
skill-verdict: conformance-review-finding-record — applied: invoked; all
seven requirement blocks carry the full field list (requirement,
spec_ref, verdict, evidence, rationale, plus spec_vs_built on the two
non-Present verdicts), written only into this file.
skill-verdict: conformance-review-sampling-derivation — not-applicable:
issue #2383's Acceptance section names exactly 3 checks over 4 changed
files; full enumeration was feasible, no sampling scope was needed.
skill-verdict: conformance-review-severity-classification —
not-applicable: no request to risk-weight the two findings beyond their
Present/Absent/Incorrect verdicts was made; ordinary fidelity-checking
only.
other mounted skills: not triggered.
