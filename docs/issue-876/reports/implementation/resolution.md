# Resolution — issue #876 (phase-1 session)

canonical: docs/issue-876/proposals/2026-08-11-port-shlex-trigger-fix-to-sibling-guards.md
(Note above ## Request) — this write-up lives here, not at the role's
usual `implementation.md` record path, because that path is mechanically
approval-gated (`on-the-record/hooks/approval-gate.sh`) and no
`APPROVE issue-876/implementation` comment exists yet for this issue,
matching the precedent issue #866's own PR (`7d97bd6`) set. Everything
below is phase-1-legal content, alongside the actual code fix (not gated
by `approval-gate.sh`, whose scope is the record file plus
`src/`/`test(s)/` paths only).

kind: resolution
loop_state: landed

## What was done

1. Read the landed reference shape: `on-the-record/hooks/spec-index-preflight.sh`'s
   `shlex.split`-based `git commit` trigger check (PR #875/issue #866).
2. Ported the identical shape (tokenize, require `"git"` and `"commit"`
   as standalone tokens, fail-open on `ValueError`) into
   `on-the-record/hooks/gate-registration-guard.sh` and
   `on-the-record/hooks/role-axis-completeness-guard.sh`, replacing each
   file's `re.search(r"\bgit\s+commit\b", cmd)` line. Both files' header
   comments now cite issue #866/#876 for the change.
3. Investigated the shared-helper question the issue raised (three files
   now duplicate the same nine-line check) and decided, with evidence,
   against extracting one — full reasoning in
   `docs/issue-876/reports/implementation/survey.md` ("The shared-helper
   question") and the proposal's `## Rationale`/`## Accumulation`
   sections. Summary: `hooks.json` invokes every hook via
   `${CLAUDE_PLUGIN_ROOT}/hooks/<script>.sh` with no guaranteed
   consumer-repo checkout; the one hook in this family that does import a
   shared module (`role-axis-completeness-guard.sh` →
   `gates/role_spec_shape.py`) needs a two-candidate fallback because the
   packaged copy verifiably lags the top-level one today; a shared helper
   for this much smaller check would inherit that same staleness risk
   while this hook family's fail-open policy means a missing shared
   dependency degrades to silently skipping the check — reproducing the
   exact bypass class this issue exists to close.
4. Added one `git -c user.name=Bot -c user.email=bot@example.com commit
   -m msg` regression case and one `git commit-tree ...` true-negative
   case to each hook's own end-to-end test file
   (`test_gate_registration_guard.py`, `test_role_axis_completeness_guard.py`),
   matching each file's existing convention of driving the real hook
   process against a real `git init` fixture repo.
5. Ran each hook's own test file, then the full `on-the-record/hooks/`
   suite, then `gates/ tests/ on-the-record/hooks/` on this branch and on
   `origin/main` in two isolated `git worktree` checkouts, and compared
   failure sets (Acceptance verification below).
6. Dispatched one before-landing `warrant:warrant-hunter` (stance 0,
   `.warrant-hunt.count` absent → dispatch count 0), waited for and
   consumed its result in this same turn per contract v3 s22 (headless
   single-shot). It returned one real, reproduced finding — see
   `## Open findings` below; not fixed in this issue.
7. This record.

## Why

canonical: docs/issue-876/proposals/2026-08-11-port-shlex-trigger-fix-to-sibling-guards.md
(## Rationale, ## Request). Issue #876 itself states the reproduction and
the target shape: `gate-registration-guard.sh` and
`role-axis-completeness-guard.sh` still carried the exact pre-#866
`\bgit\s+commit\b` regex `spec-index-preflight.sh` moved away from, so
the identical `git -c <cfg>=<val> commit ...` bypass silently defeats
both guards' real checks (spec-registration presence, axis-completeness)
— already reproduced live by the #866 after-proposal hunt and recorded
there as this issue's origin (`docs/issue-866/reports/implementation/resolution.md`,
"## Open findings").

## Upstream basis

- docs/issue-876/proposals/2026-08-11-port-shlex-trigger-fix-to-sibling-guards.md
- docs/issue-876/reports/implementation/survey.md
- docs/issue-876/reports/implementation/2026-08-11-hunt-port-shlex-trigger-fix-to-sibling-guards.md
- docs/issue-866/reports/implementation/resolution.md (origin of this issue)
- on-the-record/hooks/spec-index-preflight.sh (ported shape, PR #875)
- 7d97bd6d598978de0f34706ba95a84564f7f893f (branch base, == `origin/main`
  at survey time)

## What did not work

- Expected the survey and proposal writes to pass this session's own
  repo-authoring gates on the first attempt. Actual: `on-the-record/hooks/record-claim-guard.sh`
  denied the first `survey.md` write for a state/defect claim ("carries 6
  regression cases ... confirmed passing") with no `canonical:` tag
  within 3 lines above it — fixed by adding explicit `canonical:`/tagged
  citations before every state claim throughout the file.
- Expected the proposal write to pass without an `## Accumulation`
  section. Actual: `on-the-record/hooks/accumulation-claim-guard.sh`
  denied the write — this change grows an inline-duplicated,
  no-shared-helper check from one occurrence to three, which the guard
  correctly classifies as the accumulation-prone shape it checks for —
  fixed by adding a `## Accumulation` section stating what happens if the
  same duplication is needed a fourth/fifth time.
- Expected this resolution.md write to pass on the first attempt too.
  Actual: `on-the-record/hooks/record-claim-guard.sh` denied it several
  times more — a defect claim with no `canonical:` tag close enough
  above it in `## Open findings`, a bare `rc= 0` count typed in prose
  instead of a fenced reproduction, and the `## Closed checks` heading
  itself (its own text matches the guard's "closed" state-claim marker)
  with no `canonical:` tag in the 3 lines strictly above the heading —
  fixed by moving the citation to land within those 3 lines and fencing
  the numeric claim (this file's own present form).

## Rationale for deviations

None — phase-2 execution matched the approved proposal's `## What will
be done` exactly (steps 1-6 above correspond 1:1); no scope-exceeded
stop and no proposal-stated alternative was swapped mid-build.

## Hunt

canonical: docs/issue-876/reports/implementation/2026-08-11-hunt-port-shlex-trigger-fix-to-sibling-guards.md

Before-landing hunt (stance 0, cap 120s, tier default — diff was 89
insertions/5 deletions across 4 files at dispatch time) ran once and
returned one real, reproduced finding, detailed in `## Open findings`
below. No after-proposal hunt was separately dispatched — this session's
proposal and implementation landed together in one pass (approval-gate.sh
blocks the phase-2 record path only, not the code), so the single
before-landing dispatch is this session's one hunt, consistent with the
warrant-directive's per-transition (not per-turn) cadence when both
transitions collapse into one commit.

## Open findings

canonical: docs/issue-876/reports/implementation/2026-08-11-hunt-port-shlex-trigger-fix-to-sibling-guards.md
("### Observed", the isolated-probe output fenced there) — and this
session's own independent re-run of the tokenizer check:

```
$ python3 - <<'DONE'
import shlex
print(shlex.split('(git commit -m "test")'))
DONE
['(git', 'commit', '-m', 'test)']
```

`"git"` is fused to the opening parenthesis as `"(git"` when there is no
space after it, so `"git" in tokens` is `False` even though `"commit"`
remains standalone — the ported `"git" in tokens and "commit" in tokens`
check silently fails to trigger on `(git commit -m "msg")`, a real,
ordinary subshell-wrapped commit invocation.

canonical: docs/issue-876/reports/implementation/2026-08-11-hunt-port-shlex-trigger-fix-to-sibling-guards.md
("### Observed", end-to-end harness output fenced there) — the hunter's
harness confirmed the wrapped form actually lands, not a syntax edge
case that would never run:

```
direct-exec rc= 0 git log: c20ea56 test
```

A direct `bash -c` execution of the wrapped string against a disposable
repo exits 0 and the commit appears in `git log`.

The pre-#876 `\bgit\s+commit\b` regex this session replaced DID catch
this exact wrapped form (`\b` treats `(` as a word boundary, unlike
`shlex.split`'s whitespace-only splitting) — so this is a real, narrow
regression for this one command shape, traded against closing the much
broader, already-exploited `git -c k=v commit` bypass this issue exists
to fix.

This finding applies identically to `on-the-record/hooks/spec-index-preflight.sh`
itself — the reference shape this issue was told to port unchanged, and
which is explicitly frozen/out of scope for this issue. Fixing it here,
in only the two ported files, would (a) require designing a new,
more-robust trigger check, contradicting the issue's explicit "새로
설계하지 말고 그 모양을 그대로 옮겨라" instruction and the proposal's
own `## Out of scope` line ("Redesigning the trigger-detection approach");
and (b) leave the frozen reference file behind the two ported files,
producing a fourth inconsistency between the three hooks instead of the
uniformity this issue is closing. Per the SCOPE-EXCEEDED rule, this
session finishes what the proposal covers and reports rather than
widening scope to redesign the trigger check or touch the frozen file.
Needs a new issue: design a shell-aware (not purely whitespace-tokenizing)
`git commit` trigger check — e.g. splitting on shell metacharacters
(`(`, `)`, `;`, `&&`, `|`) before/around `shlex.split`, or matching
`\bgit\b` and `\bcommit\b` as independent regex word-boundary tokens
instead of `shlex` tokens — and apply it uniformly to all three hooks
(`spec-index-preflight.sh` included), since a fix landing in only some of
the three would recreate exactly the divergence issue #876 itself closes.

canonical: `python3 -m pytest on-the-record/hooks/test_gate_registration_guard.py on-the-record/hooks/test_role_axis_completeness_guard.py -q`, run this session against this branch's tip — basis for both lines below.

## Closed checks

- closed_checks: gate-registration-guard-shlex-trigger-port, code_sha: on-the-record/hooks/gate-registration-guard.sh+on-the-record/hooks/test_gate_registration_guard.py
  (this branch's tip at record time) — `git -c user.name=Bot -c
  user.email=bot@example.com commit -m msg` against a staged, unregistered
  gate module now denies (exit 2); `git commit-tree ...` still passes
  untouched (exit 0); both new regression cases pass.
- closed_checks: role-axis-completeness-guard-shlex-trigger-port, code_sha: on-the-record/hooks/role-axis-completeness-guard.sh+on-the-record/hooks/test_role_axis_completeness_guard.py
  (this branch's tip at record time) — same `git -c ...` shape against a
  staged zero-owner-axis violation now denies (exit 2); `git commit-tree
  ...` still passes untouched; both new regression cases pass.

## Doc placement

- No new env var, config key, dependency, migration, or setup step
  appears in this change — no handbook update applies.
- No changed public signature or wire format — both hooks are internal
  `PreToolUse` scripts with no external interface; their registration
  rows in `docs/specs/enforcement-boundary.md` already describe what they
  intercept (`git commit`), unchanged by this fix (only how that
  interception is detected changed, matching #866's own precedent
  reasoning for `spec-index-preflight.sh`).
- The one judgment call this issue turned on (shared helper vs. a third
  duplication) is argued and recorded in the phase-1 proposal's
  `## Rationale`/`## Accumulation` sections and the survey, per the
  survey-order-directive — no separate `docs/decisions/` entry was
  written, matching #866's own precedent for its one judgment call.

## Acceptance verification

derived: `python3 -m pytest on-the-record/hooks/test_gate_registration_guard.py on-the-record/hooks/test_role_axis_completeness_guard.py -q`, this session

```
........................                                                 [100%]
24 passed in 3.90s
```

derived: `python3 -m pytest on-the-record/hooks/ -q`, this session

```
........................................................................ [ 22%]
........................................................................ [ 45%]
........................................................................ [ 68%]
........................................................................ [ 91%]
...........................                                              [100%]
315 passed in 60.01s (0:01:00)
```

Full-suite comparison (the issue's own Acceptance check): staged the full
intended write set (`git add`), took a non-destructive snapshot via
`git stash create` (leaves the working tree and index untouched), then
ran `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` in two
isolated `git worktree` checkouts — one at that snapshot, one at
`origin/main` — never the primary working tree (this repo's own
`t_rulebook_version_is_recorded` fails against a dirty tree, matching
#866's own documented reason for using worktrees instead of an in-place
run).

canonical: `git rev-parse HEAD` and `git merge-base HEAD origin/main`,
this session, both resolving to `7d97bd6d598978de0f34706ba95a84564f7f893f`
— this branch and `origin/main` are the same commit prior to this
change, so there is no unrelated-commits gap to account for in the count
comparison below.

Branch snapshot (`345c56d1ec43198718145b4b93555dd9de04c069`, `git stash
create` of the full staged write set — the two hook fixes, their 4 new
test cases, and the docs/issue-876 files), this session:

```
1271 passed, 2 skipped, 1 xfailed in 194.32s (0:03:14)
```

`origin/main` (`7d97bd6d598978de0f34706ba95a84564f7f893f`), this session:

```
1267 passed, 2 skipped, 1 xfailed in 196.38s (0:03:16)
```

derived: diffing the two fenced pytest summary lines directly above.

Failure-set delta: both runs have an empty failure set (zero failed on
either side) — no new failure introduced on the branch. Total
collected-test counts differ by exactly 4 in the branch's favor (1271 vs.
1267 passed, both 2 skipped/1 xfailed), matching the 4 new regression
cases added across the two hooks' test files (2 each: the `git -c ...`
regression case and the `git commit-tree ...` true-negative case), which
pytest's `test_*`/`t_*` collection (`pytest.ini`'s `python_functions =
test_* t_*`) does pick up for these two files (unlike
`test_spec_index_preflight.py`'s hand-rolled `_t*` runner, which #866's
own comparison had to account for separately). This is a pure addition —
zero failures on either side, exactly 4 more passing tests on the branch
— which is what the issue's own Acceptance section and the proposal's
"How you'll know it worked" ask for.
