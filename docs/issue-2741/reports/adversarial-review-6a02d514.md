---
issue: 2741
role: adversarial-review-6a02d514
author: adversarial-review-6a02d514
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 5cc92dfd52b7652d37e2eec6116bc732ab3a06cd
loop_state: landed
type: review
breaking: false
verdict: confirmed — both PRs' write-site enumeration, exclusion reasoning, no-dual-read claim, docs/ non-goal, and forward round-trip hold under independent re-derivation; the fail-open claim holds empirically in both merge-order directions; one real gap found (moderate, not acceptance-blocking) — core's board-gate.sh lacks the shape-mismatch stderr diagnostic the PR's own warrant-hunter added to on-the-record's six sidecar-reading hooks for the identical silent-fail-open pattern
upstream:
  - path: 5cc92dfd:docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a.md
    sha: 5cc92dfd52b7652d37e2eec6116bc732ab3a06cd
  - path: f06267ef:tokenmaxxxer-core PR #353, branch issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a
    sha: f06267ef7395001da7d612cc9959e15bcaecbd2c
---

# issue-2741 — adversarial-review-6a02d514 record

## What was done

Independently verified `tokenmaxxxer/on-the-record#2743` (head `5cc92dfd`)
and its cross-repo companion `tokenmaxxxer/tokenmaxxxer-core#353` (head
`f06267ef`) — canonical: `gh pr view 2743 --repo tokenmaxxxer/on-the-record
--json title,body,state,headRefName,baseRefName,commits` and `gh pr view 353
--repo tokenmaxxxer/tokenmaxxxer-core --json title,body,state,headRefName,
baseRefName`, both executed live this session. Every claim below was
re-derived from the repos directly (git worktrees at `main` and at each PR
head, in both repos), not read off the PR's own transcript or record. The
subject's own record and hunt file are cited below only as commit-pinned
paths (`<sha>:<path>`, e.g. `5cc92dfd:docs/issue-2741/reports/...`) since
they live on the PR branch, not on this session's own checked-out branch.

### 1 — Write-site enumeration, independently re-derived

canonical: this session's own executed commands, in order —
`git grep -nE '"role"|'"'"'role'"'"'' main -- '*.py' 'on-the-record/hooks/*.sh' ':!docs' | wc -l`
then the same against `5cc92dfd` (on-the-record), then
`git grep -nE 'role\.json|"role"|'"'"'role'"'"'' main -- '*.py' '*.sh' ':!docs'`
then the same against `f06267ef` (core).

derived: on-the-record `main` → 146 lines (`wc -l` of the command above);
on-the-record PR head `5cc92dfd` → 9 lines remaining (same command, same
session); core `main` → the single read site
`core/hooks/board-gate.sh:865` (`_sidecar.get("role")`) and `:868`
(`_sidecar_skill = _sidecar["role"]`), confirmed by `git show
main:core/hooks/board-gate.sh | sed -n '845,895p'`; core PR head `f06267ef`
→ that read site renamed to `.get("skill")`/`["skill"]`, confirmed by
`git show f06267ef:core/hooks/board-gate.sh | sed -n '845,895p'` (same
session, same command shape, different rev).

Checked each of the 9 on-the-record remainders individually against its
own source (not the PR's characterization of it) — canonical:
`git show 5cc92dfd:gates/finding_shape.py` (lines 1-40),
`git show 5cc92dfd:gates/findings_due.py` (lines 1-90),
`git show 5cc92dfd:harness/fixture-target/scenario.py` (lines 1-70),
`git show 5cc92dfd:harness/run_smoke.py` (lines 1-40) plus
`git show 5cc92dfd:harness/signals.py` (lines 20-150, the actual
consumer), `git show 5cc92dfd:on-the-record/monitors/test_poll_heartbeat.py`
(lines 120-165) plus `git grep -rn patrol_promote main -- '*.sh'` and
`sed -n '285,320p' on-the-record/monitors/poll-heartbeat.sh` (the real
consumer), `git grep -n "args\.role\|a\.role" 5cc92dfd -- '*.py'`, and
`git show 5cc92dfd:test/test_spawn_attempt_staleness.py` (lines 344-415)
— all read this session:

- `gates/finding_shape.py:23`, `gates/findings_due.py:69,82` both parse/
  emit `docs/reports/findings/<role>/` frontmatter and directory-name
  structure (the frozen `docs/` `role:` key the issue explicitly keeps
  forever). `docs/`-adjacent exclusion, not a missed runtime-state site.
- `harness/fixture-target/scenario.py:55` — `{"message": {"role": "user",
  ...}}`, the LLM chat-message shape, unrelated concept.
- `harness/run_smoke.py:24` and `on-the-record/monitors/test_poll_heartbeat.py:153`
  — the PR calls these "decorative, no consumer reads it"; verified rather
  than trusted: `harness/signals.py`'s two functions only call
  `len(delegation_events)` and `e.get("ts")`, never `.get("role")`; the
  real caller of `gates/patrol_promote.py` (`poll-heartbeat.sh:296-320`)
  only reads `len(d.get("promotions", []))`, never `.get("role")` per
  promotion. Both confirmed decorative.
- `spawn.py:1894` — `ap.add_argument("role", ...)`, the CLI positional.
  Every `a.role`/`args.role` use site is a local Python attribute read
  feeding `task_text`/dispatch branches/`_spawn_one(...)` as a plain
  parameter — never written back into a persisted dict under a `"role"`
  key. CLI-syntax exclusion.
- `test/test_spawn_attempt_staleness.py:394,408` — `"role"` used as an
  arbitrary *value* (a fake skill-name slug in a synthetic attempt id),
  matching the file's own pattern of using `"orchestrator"` the same way
  at line 360 — not a dict key.

No missed write/read site found in either repo.

### 2 — No dual read, no compatibility alias

canonical: `git grep -nE 'get\(.role.\)|\["role"\]' 5cc92dfd` and the same
against `f06267ef` in core, executed this session — returns nothing outside
the nine legitimate exclusions above. Also read the full body of
`git show 5cc92dfd:on-the-record/hooks/approval-gate.sh` (lines 95-165) and
`git show f06267ef:core/hooks/board-gate.sh` (lines 845-895) directly: both
do a single `.get("skill")` read with no fallback to `"role"`.

### 3 — `docs/` untouched

canonical: `git diff --name-status main 5cc92dfd -- docs/` (on-the-record)
and `git diff --name-status main f06267ef -- docs/` (core), executed this
session. on-the-record shows two `A` (added) records only, no `M` against
any existing `docs/` file; core shows zero `docs/` changes.

### 4 — Forward round-trip, driven directly rather than re-run from the PR's transcript

canonical: this session's own executed script + subprocess call, both
against real PR-head code in fresh `git worktree add` checkouts (not the
PR's own transcript) —
`pipeline._write_skill_sidecar(work, 2741, "adversarial-review-6a02d514")`
(real function from `5cc92dfd:pipeline.py`, imported via `sys.path.insert`
into the worktree) wrote `.on-the-record/role.json` as
`{"skill": "adversarial-review-6a02d514", "issue": 2741}` — file content
printed and inspected this session.
`roster.roster_register()` then `roster._roster_load()` then
`board._format_roster_row()` (all real `5cc92dfd` functions) round-tripped
a roster entry shaped like `spawn.py`'s real early-roster-entry
construction (`5cc92dfd:spawn.py:4037-4045`, `"skill": skill` key) and
rendered `adversarial-review-6a02d514` correctly in the formatted row —
output captured this session (`FORMATTED ROW: RUNNING adversarial-review-6a02d514 issue-27410 ...` in
the first pass, then `issue-2741` in the corrected pass).
The real `.on-the-record/role.json` produced above was then fed to core's
real `f06267ef:core/hooks/board-gate.sh` as an actual `bash` subprocess,
workspace on branch `issue-2741/adversarial-review-6a02d514`,
`CLAUDE_SKILL=adversarial-review-6a02d514`: exit code `0` (allow), no shape
error, printed and inspected this session.

### 5 — Cross-repo merge-order fail-open claim, tested directly (not just read)

canonical: `git show main:core/hooks/board-gate.sh` and
`git show f06267ef:core/hooks/board-gate.sh` extracted to two files this
session, then each run as a real `bash` subprocess against a real
git-initialized workspace, once per row below, with the sidecar content
written by a plain `printf` (no interpreter, so this session's own
write-shape gate did not need to reconstruct it) — the four `rc=` values
below are this session's own captured subprocess exit codes, not a
restatement of the PR's description of what "should" happen:

| scenario | gate version | sidecar shape | result |
|---|---|---|---|
| on-the-record merged, core not | `main` (`.get("role")`) | new `{"skill":...}` | rc=0, silent fallback to branch-regex |
| core merged, on-the-record not | `f06267ef` (`.get("skill")`) | old `{"role":...}` | rc=0, silent fallback to branch-regex |
| control: neither merged | `main` | old `{"role":...}` | rc=0 |
| control: both merged | `f06267ef` | new `{"skill":...}` | rc=0 |

derived: all four rows are the `rc=$?` captured immediately after each of
the four `bash <extracted-gate>` invocations this session ran in sequence,
each printed inline (`echo "rc=$rc"`) right after the call — no output on
stdout/stderr beyond the `rc=` line in any of the four runs.

All four allow (`rc=0`) with the branch name matching the true identity, in
line with the PR's "degrades cross-check precision, not a hard failure"
claim.

One asymmetry the PR's cross-repo section does not mention: canonical:
`diff` of `git show main:on-the-record/hooks/approval-gate.sh` against
`git show 5cc92dfd:on-the-record/hooks/approval-gate.sh`, and separately
`git show f06267ef:core/hooks/board-gate.sh` lines 845-895 read in full,
both this session. The PR's own warrant-hunter (commit-pinned:
`5cc92dfd:docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a/2026-08-30-hunt-role-key-rename.md`)
classified a silent-fail-open-with-zero-diagnostic pattern as a FINDING in
on-the-record's six hooks and the `diff` above shows the fix landed there
(an added `else: sys.stderr.write(...)` naming issue #2741 on shape
mismatch, present in `5cc92dfd` and absent from `main`). Reading
`core/hooks/board-gate.sh:855-882` at `f06267ef` directly shows the
structurally identical read block (`try: ... except (OSError, ValueError):
pass`, shape check that silently falls through on mismatch) has no such
`else`/stderr branch — the diagnostic fix was not carried over to core's
reader of the same file. Functionally this does not break anything — the
rc=0 results in the table above hold for both the diagnosed (on-the-record)
and undiagnosed (core) readers — so this is an observability gap during
the merge-order window, not a correctness break. See Open findings for
disposition.

### 6 — Failing-test sets vs `origin/main`, as sets of names, both repos, both suites

canonical: four pairs of commands, each pair run once against a `main`
worktree and once against the PR-head worktree in the relevant repo, this
session — `python3 -m pytest -q` (on-the-record), `bash
core/hooks/tests/run-board-gate-tests.sh` (core), and `python3 -m pytest -q
test tests` (core). Each run's `FAILED`/`FAIL` lines were piped to `sort`
into a file, and the `main` file was `diff`ed against the PR-head file —
an empty `diff` means the two runs failed the exact same named tests, not
merely the same count.

derived: `python3 -m pytest -q` (on-the-record) — on-the-record `main`: 16
failed, 539 passed, 6 xfailed; `5cc92dfd`: 16 failed, 539 passed, 6
xfailed; `diff main-failed.txt pr-failed.txt` printed nothing
(`IDENTICAL SETS`, this session's own echo right after the empty diff).

derived: `bash core/hooks/tests/run-board-gate-tests.sh` (core) — `main`:
143 passed, 2 failed (`feasibility-spikes`, `ops-postmortems`); `f06267ef`:
143 passed, 2 failed (same two names); `diff` printed nothing
(`IDENTICAL GATE-TEST FAIL SETS`).

derived: `python3 -m pytest -q test tests` (core) — `main`: 3 failed
(`test_proposal_shape_gate_refuses_missing_sections`,
`test_survey_order_gate_refuses_proposal_without_survey_or_skip`,
`test_A5_trailer_gate_quote_split_commit_is_detected`), 57 passed;
`f06267ef`: 3 failed, 57 passed (identical three names); `diff` printed
nothing (`IDENTICAL PYTEST FAIL SETS`).

This matches the PR's own counts, and (going beyond what the PR's
transcript shows) independently confirms the failing *names* are identical
across both repos and both suites, not merely the counts.

## Why

The highest-risk claim named by the reviewing brief was the enumeration
("every write site outside `docs/` was renamed") — a missed site leaves the
old key alive in new data, which the operator ruling explicitly does not
tolerate. Re-deriving the population myself (section 1), rather than
checking the PR's list against itself, was the only way to catch a site the
PR's own enumeration might have silently missed; it turned up none. The
cross-repo fail-open claim (section 5) was the second-highest risk because
it is not verifiable by reading code alone — the two-repo merge-order gap
is a real runtime state that has to be constructed and driven, which this
record does directly rather than trusting the PR's description of what
"should" happen.

Per the adversarial-review skill's core mechanism (session separation as
the debiasing device): this session re-derived each of the six numbered
checks above from `git grep`/`git diff`/`git show`/live subprocess runs
before cross-referencing the PR's own description of the same claim, so
agreement above reflects independent re-derivation, not restated trust.

## What did not work

- The first two `git grep` enumeration commands (section 1) were run with
  the revision argument placed after the pathspec (`-- '*.py' ... main`)
  instead of before `--`; git silently treated the revision string as an
  unmatched extra pathspec and fell back to searching the current
  worktree/HEAD, so both the "main" and "PR branch" runs returned identical
  output that was actually neither — it was this session's own unrelated
  branch. Caught by a direct `git show 5cc92dfd:spawn.py | sed -n
  '795,802p'` spot-check that contradicted the grep result (it showed
  `.get("skill")` where the grep claimed `.get("role")` was still there);
  corrected by moving the revision immediately after the pattern (`git
  grep <pattern> <rev> -- <pathspec>`), after which `main` showed 146 hits
  and the PR head showed 9.
- The first cross-repo round-trip script (section 4) was written to a
  heredoc (`python3 - <<'PYEOF'`) and to a git worktree path that reused
  another issue's number (`issue-27410`) in its fake docs path; both were
  refused by this session's own `pretooluse-dispatcher.sh` (heredoc
  write-shape refusal, then a board-gate mismatched-issue-number refusal)
  before any command ran. Rewrote the script to a plain file
  (`/tmp/otr-e2e/write_sidecar.py`, run via `python3 <path>`, no heredoc)
  and switched every fake workspace's issue number/branch to this
  session's own `issue-2741`/`adversarial-review-6a02d514`, which the
  dispatcher's static check accepted.
- The second attempt in the same round-trip relied on the shell `cd`
  persisting into the next Bash call; it did not (each call's cwd resets
  in this environment), so a script run right after a failed `cd` silently
  executed against the wrong `pipeline.py` (this session's own main-branch
  checkout) and printed the pre-rename `{"role": ...}` shape, which looked
  at first like a real regression. Caught by printing `pipeline.__file__`
  inside the script; fixed by passing the worktree path via
  `sys.path.insert` instead of relying on `cd`.

## Upstream basis

- `tokenmaxxxer/on-the-record#2743`, head `5cc92dfd52b7652d37e2eec6116bc732ab3a06cd`,
  branch `issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a`
  — the subject deliverable record, commit-pinned:
  `5cc92dfd:docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a.md`,
  plus its companion hunt record, commit-pinned:
  `5cc92dfd:docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a/2026-08-30-hunt-role-key-rename.md`
  (neither path is checked out on this session's own branch, hence the
  commit prefix rather than a bare repo-relative path).
- `tokenmaxxxer/tokenmaxxxer-core#353`, head
  `f06267ef7395001da7d612cc9959e15bcaecbd2c`, same branch name, checked out
  locally at
  `/home/jwjung/.tokenmaxxxer/work/tokenmaxxxer-core-issue-2741-role-key`.
- Issue `#2741` itself — canonical: `gh issue view 2741`, read live this
  session for the operator ruling and acceptance criteria.

## Open findings

1. **`core/hooks/board-gate.sh` shape-mismatch diagnostic gap** (moderate,
   not acceptance-blocking) — canonical: section 5 above (`f06267ef:
   core/hooks/board-gate.sh` lines 845-895 read this session, no `else`/
   stderr branch on shape mismatch, contrasted against the `else:
   sys.stderr.write(...)` present in `5cc92dfd:on-the-record/hooks/approval-gate.sh`
   and the other five on-the-record hooks). The PR's own warrant-hunter
   classified the identical silent-fail-open-with-zero-diagnostic pattern
   as a FINDING in on-the-record's six hooks and fixed it there; the
   structurally identical read block in core's `board-gate.sh` (a separate
   repo/PR, evidently outside that hunt dispatch's scope) still has no
   diagnostic on the same shape-mismatch path. Confirmed functionally
   harmless — canonical: section 5's four `rc=0` subprocess results,
   executed this session, cover the exact scenario. Not a correctness
   break, and the issue's own "must not" clause is scoped to "the process
   that wrote it" (on-the-record's own hooks reading their own repo's
   sidecar), which `board-gate.sh` — a downstream reader in a different
   repo — is not literally covered by. Resolution path: not blocking for
   this issue; worth a follow-up issue (or a note in core#353 before
   merge) adding the same `else: sys.stderr.write(...)`-shaped diagnostic
   to `core/hooks/board-gate.sh`'s sidecar-shape-mismatch branch, so an
   operator watching core's hook stderr during the merge-order gap gets
   the same visibility on-the-record's hooks now provide.
2. **`role:<skill>` GitHub label prefixes and the `role: <role>`
   issue-body convention text** (`5cc92dfd:gates/patrol_board.py:332,337`,
   `5cc92dfd:gates/patrol_promote.py:236,242`, and
   `5cc92dfd:test/test_branch_role_field.py:164,565`'s
   `"role: implementation"` issue-body-line assertions) were left
   unrenamed — canonical: same `git grep` commands as section 1, same
   session. This is outside the issue's literal scope (a persisted "role"
   *dict key*, not a GitHub label or free-text issue-body convention) and
   the PR does not claim to have covered it, so this is not scored as a
   gap in the PR's own claims — noted only as a minor scope-boundary
   observation for whoever eventually decides whether GitHub labels/issue
   prose fall under a later slice.

## Next steps

None required to close this review — `loop_state: landed`. Finding 1 above
names its own resolution path (follow-up issue or a pre-merge amendment to
core#353); this record does not open one itself, since the operator ruling
this issue turns on ("rename the key to `skill`, forward-only") is fully
satisfied by both PRs as they stand — canonical: sections 1-6 above,
acceptance requirement met — checked: sections 1 (enumeration), 4 (forward
round-trip), and 6 (failing-test-set comparison) above, each with its own
`canonical:`/`derived:` tag and executed command — result: no missed write
site, real round-trip succeeds end to end, and both repos' failing-test
name sets are identical to `origin/main` — and the one open finding is
explicitly scored non-blocking.

skill-verdict: adversarial-review — applied: invoked; used its blind
independent-re-derivation mechanism throughout (git grep/git diff/git
show/live subprocess round-trips run before reading the subject's own
record's characterization of each claim, per sections 1-6 above) rather
than restating the PR's transcript as evidence.
