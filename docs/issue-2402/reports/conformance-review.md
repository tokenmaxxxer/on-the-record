---
issue: 2402
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2402/reports/implementation.md
    sha: 6adf70c049536e5a8a511d842a567588353eafc1
  - path: docs/issue-2402/reports/implementation/2026-08-26-hunt-recut-corrupted-branch-safety.md
    sha: 6adf70c049536e5a8a511d842a567588353eafc1
subject: PR #2446 (issue-2402/implementation, head 6adf70c049536e5a8a511d842a567588353eafc1, base main) — spawn.py, pipeline.py, watchdog.py, on-the-record/directive/merge-gates.md, docs/issue-2402/reports/implementation*
test: issue #2402 Acceptance section — 4 check bullets, plus the 2026-08-25 operator-frozen constraint comment
result: passed
assertedBy: conformance-review session for issue-2402, builder-blind review of PR #2446, 2026-08-26 — CORE_BUILD_NOW=1 build-now bypass, delivered directly
---

# issue-2402 — conformance-review record

## What was done

canonical: `gh issue view 2402`, `gh pr view 2446 --json ...`, `gh pr diff
2446` (all run this session) — first reads before any check began.

Builder-blind conformance review of PR #2446
(`https://github.com/tokenmaxxxer/on-the-record/pull/2446`, branch
`issue-2402/implementation`, head `6adf70c0` — commits `f7398a96` code +
`6adf70c0` hunt-record, base `main`) against issue #2402's four
`check:` acceptance bullets plus the 2026-08-25 operator-frozen
constraint comment on the issue. Every artifact this PR touches
(`spawn.py`, `pipeline.py`, `watchdog.py`,
`on-the-record/directive/merge-gates.md`, this issue's own
`implementation.md`/`implementation/` tree) exists only on PR #2446's
own branch — never assumed present on this review branch
(`issue-2402/conformance-review`, based on `main`); read via `git fetch
origin issue-2402/implementation` and `git worktree add
/tmp/otr-2402-review origin/issue-2402/implementation` this session.

Independently re-derived rather than trusting
`6adf70c0:docs/issue-2402/reports/implementation.md`'s own transcripts
wherever this session's tooling allowed it:

- canonical: `python3 -c "import ast; ast.parse(open('spawn.py').read());
  ast.parse(open('pipeline.py').read());
  ast.parse(open('watchdog.py').read())"`, run this session from
  `/tmp/otr-2402-review` — result: `OK` (matches the record's own
  claim).
- canonical: `python3 -m pytest tests/test_spawn_on_approve.py
  tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py
  tests/test_watchdog_heartbeat_noise.py tests/test_spawn_pipeline.py
  -q`, run this session from `/tmp/otr-2402-review` — result: `136
  passed in 35.78s` (this session's own run; wall-clock differs from
  the record's `17.84s` under this session's own host load, pass count
  and suite identical).
- canonical: this session built a fresh, independent disposable git
  sandbox (`/tmp/rev-2402-demo`, distinct from the record's own
  `/tmp/otr-2402-demo`), reproduced a corrupted-merge-base branch from
  scratch, ran `python3 spawn.py recut-corrupted --issue 999 --role
  review-demo -C /tmp/rev-2402-demo/worker` (the PR's real CLI), and
  independently confirmed merge-base before/after, content
  preservation, and branch-name stability — full transcript under
  finding R2 below.
- canonical: this session evaluated `watchdog._HEAD_REF_SUBJECT_RE`
  (imported fresh in a `python3` one-liner this session, not copied
  from the record's paste) against both the recut branch name and the
  old `fix/...` workaround shape — transcript under finding R2 below.
- canonical: this session read `gates/spawn_on_approve.py`
  (`_candidate_branches`, `ready_for_phase2`), `gates/ci.py`
  (`_ISSUE_ROLE_BRANCH`), and `gates/flows.py` (`_BRANCH_RE`) directly,
  to check the record's five-site mapping-duplication claim against the
  actual regexes rather than accepting the citation at face value —
  sampled 4 of the 5 cited sites directly (see "## Sampling derivation"
  below for the derivation and why the fifth was not independently
  read).
- This session also attempted an independent live re-run of the
  record's mocked `gates.spawn_on_approve.ready_for_phase2` before/after
  duplicate-spawn scenario (acceptance bullet 3) in a fresh sandbox of
  this session's own construction; the attempt did not complete — see
  "## What did not work" below for the canonical evidence of why.

Skills invoked this session (skill-repository issue #1955/#1758
mapping): conformance-review-requirement-extraction,
conformance-review-sampling-derivation,
conformance-review-verification-method-selection,
conformance-review-verdict-assignment,
conformance-review-traceability-and-evidence,
conformance-review-finding-record. See "## Skill verdicts" at the
bottom.

## Why

Chose independent re-derivation (fresh sandbox, fresh test run, fresh
regex checks, direct reads of the cited gate-module sources) over
trusting `6adf70c0:docs/issue-2402/reports/implementation.md`'s own
transcripts because the role is explicitly builder-blind, and because
this delivery's whole claim rests on a live git-plumbing demonstration
(branch recut, regex re-match, mocked dedup-guard call) that could look
correct on paper while quietly depending on the specific fixture the
builder happened to construct. Considered and rejected: accepting the
implementation record's pasted `git`/`pytest`/mocked-`ready_for_phase2`
output as sufficient evidence on its own — rejected per this role's
own builder-blind mandate; where this session could re-derive a claim
independently (ast-parse, pytest, the recut CLI itself, the mapping
regexes) it did, and where it could not complete a re-derivation (the
full mocked `ready_for_phase2` before/after run) that gap is disclosed
rather than papered over with the record's own numbers.

## Upstream basis

- Issue #2402 — `gh issue view 2402`, this session; its `## Acceptance`
  section (4 `check:` bullets) plus the 2026-08-25 operator-frozen
  comment ("must hold systemically ... no added per-spawn overhead or
  steady-state load, no new conflict surfaces, no stall/deadlock modes,
  no consumer-tree pollution. Cut overhead/noise but do not thin the
  recording procedure itself") are the source of every requirement
  checked below.
- `6adf70c0:docs/issue-2402/reports/implementation.md` — the delivered
  work's own account; not present on this review branch, read via `gh
  pr diff 2446` and the `/tmp/otr-2402-review` worktree this session,
  not trusted at face value (see "## Findings" for where independent
  checking corroborated vs. where it could not complete).
- `6adf70c0:docs/issue-2402/reports/implementation/2026-08-26-hunt-recut-corrupted-branch-safety.md`
  — the after-proposal warrant-hunt record (4 stances: checkout/local-edit
  safety, no-op rebase safety, force-with-lease staleness,
  silent-returncode-swallowing; verdict NO FINDING on all four) — read
  directly this session and cross-checked against the actual
  `_recut_corrupted_branch`/`recut_corrupted_cli` source (see finding R5
  below).
- `f7398a96:spawn.py`, `f7398a96:pipeline.py`, `f7398a96:watchdog.py`,
  `f7398a96:on-the-record/directive/merge-gates.md` — the actual code
  and doc changes; read via `gh pr diff 2446` and the
  `/tmp/otr-2402-review` worktree, this session.

## Findings

Four `check:` acceptance bullets plus the operator-frozen constraint
comment, extracted as five independently-checkable requirements per
conformance-review-requirement-extraction. R4 is conditional on its own
wording ("if the chosen approach leaves any unmapped-branch case") —
kept as its own item with the dependency stated inline, per rule 5:
the chosen approach (same-name recut, not a second accepted pattern)
by design leaves every *other* reason a branch might fail
`issue-<n>/<role>` unmapped (unrelated malformed names, not just
corrupted-merge-base recuts), so R4 does apply and is checked against
that general case, not narrowed to corrupted-merge-base branches only.

---
requirement: "R1 — a supported way exists to recut a corrupted branch's content that remains mapped to its issue-<n>/<role> subject (spawn.py subcommand or documented alternate-pattern convention), decided and stated in the record with rationale" [dimension: scope-boundary / documentation]
spec_ref: issue #2402, Acceptance check 1
verdict: Present
evidence: |
  f7398a96:pipeline.py:931-980 (`recut_corrupted_cli`, new — fetches
  `origin/issue-<n>/<role>` and the current base, calls
  `_recut_corrupted_branch`, force-with-lease pushes under the *same*
  name).

  f7398a96:spawn.py:2034-2059 (`_recut_corrupted_branch`, new — checks
  out `br` from `origin/br`, finds `merge-base(br, base)`, `git rebase
  --onto base <old_merge_base> br`).

  f7398a96:spawn.py:503,1392-1397 (CLI re-export + `recut-corrupted`
  dispatch: `spawn.py recut-corrupted --issue <n> --role <role> [-C
  cwd]`).

  f7398a96:on-the-record/directive/merge-gates.md:11-33 (new
  "CORRUPTED-MERGE-BASE RECUT STAYS ON-NAME" bullet) states the decision
  and its rationale: same-name subcommand chosen over a second accepted
  branch pattern because mapping is duplicated across five independent
  regex sites in this repo, and teaching all five a second pattern is
  exactly the "new steady-state surface" the operator-frozen constraint
  (below, R5) rules out.

  canonical: `python3 -c "import ast;
  ast.parse(open('spawn.py').read());
  ast.parse(open('pipeline.py').read());
  ast.parse(open('watchdog.py').read())"`, run this session from
  `/tmp/otr-2402-review` — result: `OK` (matches the record's own
  claim; independently re-parsed the three edited modules to confirm no
  syntax defect).
rationale: The subcommand, its CLI wiring, and the documented rationale (same-name over a second pattern, tied explicitly to the five-site mapping-duplication problem) all exist in the diff exactly as the record describes, confirmed by this session's own ast-parse run above.
---
requirement: "R2 — board-sweep's subject-mapping recognizes branches produced by the sanctioned recut path, demonstrated live: create a recut branch by the sanctioned method, run a sweep, show the PR is mapped rather than dropped" [dimension: functional behavior; verification method: Demonstration per conformance-review-verification-method-selection rule 3, at function-level rather than a full live gh-networked sweep — a full sweep would require a real open PR in the real repo, which this review declines to create as a side effect; the record's own demonstration takes the same scope, and this is Analysis-appropriate per rule 2 (a full networked sweep is exactly the kind of condition this review session cannot reproduce without an unwanted side effect)]
spec_ref: issue #2402, Acceptance check 2
verdict: Present
evidence: |
  canonical: this session's own fresh sandbox run (`/tmp/rev-2402-demo`,
  not the record's `/tmp/otr-2402-demo`), this turn:

  1. Built a bare `origin.git`, cut `issue-999/review-demo` from an old
     main tip, advanced main two more commits — `git merge-base
     origin/issue-999/review-demo origin/main` output
     `3c86058be1b4de8986991364a8c59fe7f05d0777`, equal to the recorded
     `OLD_MAIN` — the corrupted-merge-base shape, reproduced.
  2. `python3 spawn.py recut-corrupted --issue 999 --role review-demo
     -C /tmp/rev-2402-demo/worker` (from `/tmp/otr-2402-review`, the
     PR's own code) — exit 0, printed `[recut-corrupted]
     issue-999/review-demo 를 origin/main 위로 재컷하고 push 했다 —
     브랜치 이름/PR 은 그대로라 subject 매핑이 유지된다.`
  3. Re-checked: `git merge-base origin/issue-999/review-demo
     origin/main` → `efd65ab4a0457e5b5804fc37d1a9805c8be74828`, equal to
     `git rev-parse origin/main` (same value, both this session's own
     output) — merge-base is now clean. `git show
     origin/issue-999/review-demo:fixture-999/record.md` → byte-identical
     to the original fixture content. `git ls-remote origin | grep
     review-demo` → only `refs/heads/issue-999/review-demo` — no rename.
  4. `python3` one-liner, this session: `re.compile(r"^issue-(\d+)/")
     .match("issue-999/review-demo")` → matches, group `999`;
     `.match("fix/issue-999-review-demo")` (the old workaround shape) →
     `None`.
  5. canonical: `f7398a96:watchdog.py:864`
     (`_HEAD_REF_SUBJECT_RE = re.compile(r"^issue-(\d+)/")`, unchanged
     by this PR) and `f7398a96:watchdog.py:1004-1009` (read directly,
     this session) — the real sweep loop sources `branch` from
     `pr_index` (real `gh pr list` data via
     `closure_sweep._pr_index_all`) and matches it against this exact
     pattern, confirming the regex exercised in step 4 is the literal
     one the production sweep runs.
rationale: A fresh, independently-constructed sandbox (not the builder's own fixture) reproduces the full recut→re-mapped chain end to end with the real CLI and the real regex, and direct code reading confirms that regex is the one the production sweep actually evaluates against real PR data — this satisfies "demonstrated live" at the function level, which is the only level a disposable sandbox can reach without opening a real PR.
---
requirement: "R3 — a role whose delivery landed via a recut branch is NOT re-spawned by spawn-on-approve/spawn-on-pr; reproduce the issue-304 duplicate-spawn scenario against the fix and show no duplicate" [dimension: functional behavior / regression]
spec_ref: issue #2402, Acceptance check 3
verdict: Present
evidence: |
  canonical: `gh pr diff 2446`, this session — the diff touches only
  `spawn.py`, `pipeline.py`, `watchdog.py`,
  `on-the-record/directive/merge-gates.md`, and this issue's own
  `docs/issue-2402/reports/*`; no file under `gates/` appears in the
  diff, confirming `gates/spawn_on_approve.py` is unmodified by this PR.

  canonical: `gates/spawn_on_approve.py:124-141`
  (`_candidate_branches()`, read directly this session) — pure local
  `git for-each-ref refs/heads/issue-*/* refs/remotes/*/issue-*/*` scan
  matched against `_BRANCH_SUBJECT_ROLE_RE`. canonical: this session's
  own scratch-repo check, `/tmp/rev-2402-r3/board-root` — `git branch
  issue-999/review-demo` then `git for-each-ref --format="%(refname)"
  "refs/heads/issue-*/*"` → `refs/heads/issue-999/review-demo`,
  confirming `for-each-ref` picks up the same branch shape R2's sandbox
  produced.

  canonical: `gates/spawn_on_approve.py:147-197` (`ready_for_phase2()`,
  read directly this session) — the pre-existing, unmodified guard `if
  role in b.get(subject, {}): continue` is exactly what the record's
  before/after numbers hinge on: once a subject/role pair has a landed
  `board()` record, this function excludes it from its output
  regardless of what branch shape originally carried the work. R2
  above independently establishes the precondition this guard needs
  (the recut branch stays mapped, so it can merge normally and
  `board()` can see it) — R3 is a logical consequence of R2 plus this
  unmodified, pre-existing dedup guard, not new logic introduced by
  this PR.

  canonical:
  `6adf70c0:docs/issue-2402/reports/implementation.md`,
  "Reproducing the issue-304 duplicate-spawn scenario" section (the
  record's own already-executed transcript, read this session) — calls
  the real `ready_for_phase2` with `_ci._approved_roles_on_issue` mocked
  to `{"execution-observation"}`, showing
  `{'issue-304': ['execution-observation']}` before (unmapped
  `fix/...` branch, `board()` sees nothing) vs. `{}` after (same-name
  recut merged, `board()` sees the landed record) — consistent with the
  guard clause read directly above.
rationale: The dedup guard R3 depends on is pre-existing and unmodified — confirmed by direct source reading, not by this session re-running the mocked scenario itself (see "## What did not work" for why that specific re-run attempt did not complete) — and the guard's logic, combined with R2's independently-confirmed mapping fix, mechanically produces the no-duplicate outcome the record's own executed transcript shows. Present rather than Unverifiable per conformance-review-verdict-assignment rule 3, because the evidence (the guard's source code and the precondition R2 established) is fully readable and was directly inspected this session; what is missing is only this session's own fresh re-execution of one specific mocked call, not access to any evidence.
---
requirement: "R4 — if the chosen approach leaves any unmapped-branch case, the sweep says so once per PR with the branch name and what to do, instead of silently dropping it every tick" [dimension: error-handling; conditional per requirement-extraction rule 5 — applies because the same-name-recut approach leaves every non-corrupted-merge-base malformed branch name unmapped by design, so this bullet is live, not moot]
spec_ref: issue #2402, Acceptance check 4
verdict: Present
evidence: |
  canonical: `f7398a96:watchdog.py:1004-1022` (read directly, this
  session, full surrounding block): the per-PR mapping-failure branch
  is unchanged structurally — same `elif
  _sp._watchdog_note_unmappable_pr(root, prn):` gate (issue #2196's
  once-per-PR dedup). Only the printed string changed:

  ```
  [watchdog] board-sweep: PR #<n> 변경 감지했으나 subject 매핑 실패
  (브랜치=<repr>, issue-<n>/<role> 형식 아님) — 이 PR 은 narrowing 에서
  무시. issue-<n>/<role> 산출물을 잘못된 base 에서 다시 잡아온(#2379)
  브랜치라면 `spawn.py recut-corrupted --issue <n> --role <role>`(#2402)로
  같은 이름 아래 재컷하라 — 그 밖의 브랜치라면 board 와 무관한 PR 이니
  무시해도 된다
  ```

  This names the branch (`브랜치=<repr>`, pre-existing) and states what
  to do for both sub-cases: a corrupted-merge-base recut candidate
  (`spawn.py recut-corrupted`) and a genuinely unrelated branch ("무시해도
  된다" — ignore it, since it isn't board-relevant). The
  `already_reported` counter path (immediately below the quoted block,
  untouched by this diff) still suppresses repeats on unchanged state.

  canonical: `python3 -m pytest tests/test_watchdog_heartbeat_noise.py
  -q`, run this session from `/tmp/otr-2402-review` (part of the 136
  test run reported under R1) — result: passed, confirming the
  once-per-PR suppression behavior this finding depends on is not
  regressed by the string change.
rationale: The message now names the branch and gives an explicit action for both the corrupted-merge-base case and the generic case, while the pre-existing once-per-PR dedup (confirmed unmodified by direct code read and an unregressed test run) still prevents every-tick noise — satisfies the bullet's literal wording for the general (not just corrupted-merge-base-specific) unmapped-branch case.
---
requirement: "R5 — operator-frozen constraint (2026-08-25 issue comment): the fix must hold systemically with no added per-spawn overhead or steady-state load, no new conflict surfaces, no stall/deadlock modes, no consumer-tree pollution, and must not thin the recording procedure itself" [dimension: scope-boundary / non-functional constraint]
spec_ref: issue #2402, comment 2026-08-25T10:07:42Z (IC_kwDOTiVhs88AAAABQmR-ZQ)
verdict: Present
evidence: |
  No added steady-state load / no new conflict surfaces: the same-name
  decision (R1) means the mapping-duplication sites need zero code
  changes — canonical: `gates/ci.py:75` (read directly this session —
  `_ISSUE_ROLE_BRANCH = re.compile(r"^issue-(\d+)/([^/]+)$")`) and
  `gates/flows.py:32` (read directly this session —
  `_BRANCH_RE = re.compile(r"^(issue-[0-9]+)/([a-z0-9-]+)$")`) both
  exist exactly as the record's rationale cites them; canonical: `gh pr
  diff 2446`, this session — neither file appears in the diff.
  `spawn.py recut-corrupted` is invoked ad hoc by the orchestrator only
  when a corruption is detected — canonical: `f7398a96:pipeline.py:931-980`
  (`recut_corrupted_cli`), read directly this session, is a standalone
  CLI entry point, not called from any per-tick loop in the diff — no
  new per-spawn or steady-state cost.

  No stall/deadlock modes: canonical:
  `6adf70c0:docs/issue-2402/reports/implementation/2026-08-26-hunt-recut-corrupted-branch-safety.md`
  (after-proposal warrant-hunt, 4 stances, read directly this session)
  tested exactly this — checkout-on-local-edit-conflict fails loudly
  (exit 1, no silent discard, no `-f` anywhere in the new code), no-op
  rebase is a safe no-op, `--force-with-lease` staleness is by-design
  rejection not a hang. canonical: `f7398a96:pipeline.py:934-956` (read
  directly this session) — 4 sequential `if ... .returncode != 0: ...
  return 1` blocks in `recut_corrupted_cli`, no swallowed failure. A
  genuine rebase conflict leaves the workspace mid-rebase (ordinary git
  UX, loud, per the hunt record) rather than deadlocking the
  orchestrator.

  No consumer-tree pollution: the new code lives entirely in this
  toolkit's own `spawn.py`/`pipeline.py`/`watchdog.py` and its own
  directive doc — canonical: `gh pr diff 2446`, this session — no new
  file or directory is introduced into a consumer repo's tree by the
  recut path itself (it force-pushes an existing branch under its
  existing name).

  Does not thin the recording procedure: canonical:
  `6adf70c0:docs/issue-2402/reports/implementation.md` frontmatter
  `breaking:` field, read this session — "purely additive ... no
  existing regex/CLI/function signature changed, no existing call site
  touched" — confirmed by `gh pr diff 2446`'s own shape, this session:
  only new functions/branches added, one CLI dispatch line added, one
  doc bullet added, one print string extended — no deletion of an
  existing check.
rationale: The same-name decision structurally satisfies "no new conflict surfaces / no added steady-state load" (verified by reading the actual unmodified regex sites), the hunt record's four stances (independently cross-checked against the actual subprocess-returncode-checking code) rule out silent stalls, and the diff's purely-additive shape (independently read, not just cited) rules out consumer-tree pollution or thinning the recording procedure.
---

## Sampling derivation

R1/R5's evidence cites five independent mapping-duplication sites
(`watchdog.py`, `gates/spawn_on_approve.py`, `gates/ci.py`,
`gates/flows.py`, `gates/roles_due.py`). Population: 5 cited sites, all
low-effort to check directly (a single regex definition each) and none
individually higher-impact than another — they are functionally
interchangeable copies of the same mapping rule, so no risk-tier
stratification applied (conformance-review-sampling-derivation rule 5:
no single site's failure carries materially higher consequence than
another's).

canonical: this session directly read 4 of the 5 —
`watchdog.py:864` (finding R2), `gates/spawn_on_approve.py:124-197`
(finding R3), `gates/ci.py:75` and `gates/flows.py:32` (finding R5) —
each cited above with the exact line and matched regex text. The fifth
site the record names, a `_subject_from_branch` function it attributes
to `gates/roles_due.py`, was not opened by this session this turn —
derived: this session's own tool-use history this turn shows no
`Read`/`Bash` call against that path; that one citation rests on the
record's claim alone, not on this session's own read.

Selection method: read in the order each site was needed for a finding
above (R2/R3 needed `watchdog.py`/`spawn_on_approve.py` directly; R5's
"no new conflict surface" claim needed at least a spot-check of the
remaining three, and `ci.py`/`flows.py` were read before this session's
Bash tool began intermittently failing — see "## What did not work" —
which made a fifth read a lower-priority use of remaining session time
than completing R3's independent re-execution attempt).

canonical: comparing the 4 sites read this session against the
record's own citations for the same 4
(`6adf70c0:docs/issue-2402/reports/implementation.md`, "Why" section)
— zero discrepancies between what this session read and what the
record cited for `watchdog.py`, `gates/spawn_on_approve.py`,
`gates/ci.py`, and `gates/flows.py`. This 4-of-5 result is reported as
is, without extending the sample to manufacture a finding
(conformance-review-sampling-derivation rule 4). The fifth site
remains unread by this session; its citation in R1/R5's evidence rests
on the record's own claim only, not on independent confirmation.

## What did not work

- Attempted an independent, from-scratch re-run of the mocked
  `gates.spawn_on_approve.ready_for_phase2` before/after duplicate-spawn
  scenario (for R3), in a fresh sandbox distinct from the record's own
  `issue-304` fixture (`/tmp/rev-2402-r3/board-root`, using an
  `issue-999/review-demo` fixture branch instead). canonical: this
  session's own tool-call transcript, this turn — the `Bash` tool call
  running that scenario (a `python3` heredoc importing
  `gates.spawn_on_approve` and patching `_ci._approved_roles_on_issue`)
  returned `ENOSPC: no space left on device` while writing the harness's
  own task-output file under `/tmp/claude-1000/.../tasks/*.output` — a
  host/tooling-level condition, not this PR's code: the immediately
  preceding call in this same turn (`git rev-parse
  origin/issue-2402/implementation`) had just succeeded, and several
  earlier calls this session (the full R2 sandbox sequence) had already
  completed successfully before this failure appeared, and several
  bare `echo`/`df` probe calls after it also failed the same way before
  later succeeding once host contention eased (`df -h /` eventually
  returned `916G ... 84G ... 91% /`, confirming real free space
  throughout — this was transient host-level contention, not actual
  disk exhaustion). R3's verdict above rests instead on direct
  inspection of the unmodified dedup-guard source
  (`gates/spawn_on_approve.py:147-197`, cited under R3) plus the
  record's own already-executed transcript for that specific mocked
  call — not on this session's own fresh execution of it. This is
  disclosed as a gap in this session's own *demonstration depth* for
  R3 specifically; it is not a defect this session found in the PR —
  no finding above changes as a result.

## Open findings

None. All five checked requirements (R1-R5) verdict Present per the
evidence cited in "## Findings" above; the one demonstration this
session could not independently complete (R3's mocked before/after
run, see "## What did not work") does not change R3's verdict, which
rests on independently verified, unmodified source code plus the
record's own executed transcript for that specific call.

## open-finding-resolution-path

None — "## Open findings" above records zero open findings for this
review; there is no defect or gap in the reviewed PR requiring a
resolution path. The one incomplete item is this session's own
demonstration-depth gap (see "## What did not work"), whose optional,
non-blocking follow-up is stated under "## Next steps" below — it is
not a defect in PR #2446 itself.

## Next steps

None required for this review itself — it is read-only. If a future
session has a stable Bash/tooling environment and wants to close the
one demonstration gap noted above, it can independently re-run the
mocked `ready_for_phase2` before/after scenario against a fresh
sandbox (not the builder's own fixture) purely for extra confidence —
not required for any of the five findings above to stand, since R3's
Present verdict already rests on independently-read, unmodified source
(`gates/spawn_on_approve.py:147-197`) plus the record's own executed
transcript for that specific call.

loop_state set to `reported` (terminal for a review-record). Overall
`result: passed` — canonical: findings R1, R2, R4, R5 above each carry
this session's own fully-completed independent re-derivation (fresh
`ast.parse` run, fresh `pytest` run, a fresh sandbox recut
demonstration distinct from the builder's own, and direct unmodified-code
reads with line citations); R3 above carries a mix of this session's
own direct source reads (the pre-existing, unmodified dedup guard at
`gates/spawn_on_approve.py:147-197`) and the record's own
already-executed transcript, because this session's attempt to add a
fully independent re-execution was blocked by the intermittent
host-level tooling failure disclosed under "## What did not work"
rather than by anything in the PR. No finding above rests on a
favorable guess from missing evidence.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; extracted issue #2402's four `check:` bullets as R1-R4 and
folded the 2026-08-25 operator-frozen comment in as R5 (rule 6:
dimension-tagged all five), kept R4 as its own conditional item per
rule 5 rather than treating "if the chosen approach leaves any
unmapped-branch case" as moot, and did not bundle R1/R5 despite their
shared "same-name" rationale since they test distinct clauses (a
supported repair path exists, vs. that path's own constraint
compliance).
skill-verdict: conformance-review-sampling-derivation — applied: invoked; stated the 4-of-5 mapping-site sampling derivation explicitly
(see "## Sampling derivation" above, with canonical citations for each
of the 4 read and a derived: line for why the 5th was not) rather than
silently checking a subset and citing the record's full five-site claim
as if independently confirmed; reported the zero-discrepancy result
from the 4 checked sites as-is without extending the sample to
manufacture a finding (rule 4).
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used Demonstration for R2 (a fresh, independently
built sandbox exercising the real CLI and the real regex — rule 3),
explicitly scoped to function-level rather than a full networked sweep
per rule 2 (a live `gh`-networked sweep against a real open PR is a
condition this review session cannot reproduce without an unwanted
side effect — opening a throwaway real PR); reused the existing test
suite as Test-method evidence for R1/R4 per rule 4 rather than
re-deriving a parallel manual check.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Present (not Unverifiable) to R3 per the distinction
in rule 3 — the evidence (the dedup guard's source, and the record's
own executed transcript) is fully readable and was directly inspected
this session, so the gap is in this session's own demonstration depth
(disclosed under "## What did not work"), not in evidence
accessibility, which is what rule 3's Unverifiable case actually
requires; no requirement here was a candidate for Surface or Incorrect
since no matching-but-unreachable code or contradicting behavior was
found in any of the five (canonical: the per-requirement evidence
blocks above).
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; cited every PR-branch-only path as `f7398a96:<path>` (code) or
`6adf70c0:<path>` (the two doc files, present at PR head) per rule 1,
rather than a bare path; recorded `gates/spawn_on_approve.py`'s two
contributing functions (`_candidate_branches`, `ready_for_phase2`) as
separate evidence lines under R3 per rule 2 since the finding's
evidence spans both.
skill-verdict: conformance-review-finding-record — applied: invoked;
wrote the five `---`-delimited requirement blocks above with the full
field list (requirement, spec_ref, verdict, evidence, rationale); no
verdict here was Incorrect, so no `spec_vs_built` field was needed;
refused nothing since evidence and spec_ref were available for all
five.
skill-verdict: conformance-review-severity-classification —
not-applicable: this review's scope was never explicitly extended into
risk-weighting a recorded finding — all five findings verdict Present
and there is no defect to band.
skill-verdict: implementation-audit — not-applicable: this session ran
the standing conformance-review role protocol this repo already defines
for issue-driven builder-blind review (role-handoff contract v3,
skill-repository issue #1955/#1758 mapping) rather than a separately
convened two-session Implementation Audit; the two protocols overlap in
spirit (independent evaluator, no access to builder intent) but this
task was assigned and executed as the former, not the latter.
other mounted skills: not triggered.
