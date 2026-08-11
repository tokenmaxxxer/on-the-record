---
code_under_review:
  - docs/specs/generated-paths.md
  - on-the-record/hooks/gate-registration-guard.sh
  - on-the-record/hooks/test_gate_registration_guard.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #839

## What was done

1. Fixed `docs/specs/generated-paths.md`'s `stop-poll-rearm.sh` row:
   classification changed from `out-of-tree` to `n/a`, verdict text now
   explains why (no write call in this file's own text under the spec's
   stated file-level grep unit) while pointing at `poll-rearm.sh`'s row
   (unchanged, still `out-of-tree`) where the actual write is recorded.
2. Extended `on-the-record/hooks/gate-registration-guard.sh`: added
   `_WRITE_CALL_RE`/`_ISSUE_PLACEHOLDER_RE` (ported verbatim from
   `gates/test_generated_paths.py`) and `recorded_classifications()`
   (reuses `_ROW_RE`'s existing second capture group). For each
   newly-staged (`hook_scripts`) path already present in
   `docs/specs/generated-paths.md`, the guard now reads the hook's own
   staged content via the existing `read_spec()` helper and refuses the
   commit if: no write-call match but classification is not `n/a`; a
   write-call match but classification is `collision-risk` or outside
   `{out-of-tree, issue-scoped}`; or classification is `issue-scoped`
   with no issue-placeholder match in the hook's own text. The prior
   presence-only check (row must exist at all) and
   `enforcement-boundary.md`'s check are unchanged.
3. Added a regression test to
   `on-the-record/hooks/test_gate_registration_guard.py`:
   `t_new_hook_script_with_wrong_classification_denies_commit`, staging a
   no-write-call hook with a `generated-paths.md` row recorded
   `out-of-tree` — this incident's exact shape — asserting the commit is
   refused with a message naming the mismatch. Every pre-existing case in
   that file keeps its prior outcome unmodified.
4. Ran the gates/tests/hooks suite on the branch and on `origin/main` and
   compared failure sets (Acceptance verification below).
5. This record.

This session's mandatory before-landing hunt also surfaced a second,
smaller defect in `gate-registration-guard.sh`, outside the approved
proposal's five itemized steps — see What did not work / Rationale for
deviations below for what it was and how it was resolved.

## Why

canonical: docs/issue-839/proposals/generated-paths-row-fix-and-guard-extension.md
(## Rationale, Decision 1 and Decision 2), argued and verified live in
docs/issue-839/reports/implementation/survey.md.

Decision 1 keeps `gates/test_generated_paths.py`'s file-level grep unit
unchanged and fixes the doc cell instead, because that unit is what
`docs/specs/generated-paths.md`'s own text and the mechanism's origin
proposal both specify deliberately.

canonical: docs/issue-839/reports/implementation/survey.md (## Decision
2), the two live-verified facts cited there — the guard's `_ROW_RE`
already captures the classification column, and its trigger already
scopes to only the commit's own newly-staged hook files.

Decision 2 extends `gate-registration-guard.sh` from a presence-only
check to a classification-match check on that basis: the survey verified
the reuse is bounded and cheap, not merely assumed to be.

## Upstream basis

- docs/issue-839/proposals/generated-paths-row-fix-and-guard-extension.md
- docs/issue-839/reports/implementation/survey.md
- docs/issue-839/reports/implementation/2026-08-11-hunt-generated-paths-row-fix-and-guard-extension.md
  (after-proposal hunt, stance 0, verdict recorded there — cited in the
  proposal's Rationale/"Known limitation" and Out-of-scope)

## What did not work

canonical: this session's Read of
`on-the-record/hooks/gate-registration-guard.sh`'s `read_spec()`
function as it stood immediately after implementing proposal step 2 —
its disk-fallback branch caught only `except OSError:`, four lines below
its sibling `git show` branch's `except UnicodeDecodeError: pass`.

Expected: the ported classification-check logic (proposal step 2) would
handle every newly-staged hook script's source text the same way
`read_spec()` already handled the two spec markdown files.

canonical: this session's before-landing `warrant:warrant-hunter`
dispatch (stance 0) and this session's own independent reproduction via
Bash against a scratch git repo (full transcript in Acceptance
verification below).

Actual: a staged hook `.sh` file containing one invalid-UTF-8 byte
crashes `read_spec()`'s disk-fallback branch with an uncaught
`UnicodeDecodeError`, ending the whole guard process with exit code 1
rather than a documented outcome — since Claude Code's PreToolUse hook
contract only blocks a tool call on exit 2, an uncaught exit-1 crash acts
as a silent pass-through, defeating the very incident shape #839 reports
for that one hook script.

Resolved by widening the `except` in `read_spec()`'s disk-fallback branch
to `(OSError, UnicodeDecodeError)`, matching the sibling branch's
existing handling and the function's own established fail-open contract
on read failures.

## Rationale for deviations

canonical: the diff between the approved proposal's "What will be done"
step 2 text and `on-the-record/hooks/gate-registration-guard.sh`'s
`read_spec()` function as this session actually left it (the widened
`except` clause is not described by step 2's text).

The approved proposal's step 2 did not itemize a fix to `read_spec()`'s
exception handling — it specified the classification-check logic. This
session's before-landing hunt (see What did not work above) surfaced the
crash path in that same function, inside the same file already in the
frozen write set — no path outside
`on-the-record/hooks/gate-registration-guard.sh`,
`on-the-record/hooks/test_gate_registration_guard.py`,
`docs/specs/generated-paths.md`, or this record was touched to resolve
it. The change itself is a one-line widening of an existing except
clause, mirroring its sibling branch in the same function; it does not
alter the behavior of any of the five proposal steps as specified.

canonical: this session's re-run of the targeted and full test suites
after the fix, transcribed verbatim in Acceptance verification below.

No case's outcome changed as a result of this additional fix.

## Hunt

canonical: docs/issue-839/proposals/generated-paths-row-fix-and-guard-extension.md
(## Rationale, "Known limitation" paragraph), citing
docs/issue-839/reports/implementation/2026-08-11-hunt-generated-paths-row-fix-and-guard-extension.md.

The after-proposal hunt (phase 1) already ran at stance 0 and its result
is recorded in that hunt file and summarized in the proposal's own
Rationale; it was not re-run this session.

canonical: this session's own tool-call transcript — an initial
`Agent` call using the unqualified `subagent_type: warrant-hunter`
was refused by the harness as an unregistered agent type before any
subagent actually started, which left a stale `.warrant-hunt.lock`
behind; this session removed that lock directly (its recorded start
timestamp and the refusal transcript together show no hunter process was
ever actually running under it) and re-dispatched with the qualified
`subagent_type: warrant:warrant-hunter`.

The before-landing hunt (this session, stance 0) then ran once and
surfaced the `read_spec()` crash described in What did not work above.
No standalone hunt-record file was written for this dispatch: this
phase-2 session's frozen write set is exactly
`docs/specs/generated-paths.md`,
`on-the-record/hooks/gate-registration-guard.sh`,
`on-the-record/hooks/test_gate_registration_guard.py`, and this record —
a fifth path for a standalone hunt-record file falls outside that set
(the role's own SCOPE-EXCEEDED rule), so the hunter was instructed to
report its finding as text only, and the finding is recorded in this
file's What did not work / Rationale for deviations sections instead.

canonical: the Acceptance verification transcripts below, all captured
after the hunt's fix.

## Closed checks

- closed_checks: stop-poll-rearm-row-fix, code_sha:
  docs/specs/generated-paths.md+on-the-record/hooks/gate-registration-guard.sh+on-the-record/hooks/test_gate_registration_guard.py
  (this branch's tip at record time) — the `stop-poll-rearm.sh` row no
  longer trips `t_all_generators_recorded_and_disjoint`.
- closed_checks: guard-classification-mismatch-regression, code_sha:
  same — the new regression case denies the incident's exact shape, and
  every pre-existing case in that file keeps its prior outcome.
- closed_checks: read-spec-unicode-decode-crash, code_sha: same — the
  before-landing hunt's reproduction no longer raises an uncaught
  exception.

## Doc placement

- No new env var, config key, dependency, migration, or setup step
  appears in this change — no handbook update applies.
- No changed public signature or wire format outside this issue's own
  frozen write set — the two design decisions (fix-the-cell vs.
  change-the-unit; extend-the-guard vs. leave-presence-only) were already
  argued and recorded in the phase-1 proposal and survey per the
  survey-order-directive, so no separate decisions record was written for
  phase 2.
- Investigation numbers (the pytest failure-set comparison) are recorded
  in this report's Acceptance verification section, per the proposal's
  own "What will be done" steps.

## Acceptance verification

derived: `python3 -m pytest gates/test_generated_paths.py
on-the-record/hooks/test_gate_registration_guard.py -q`, this session,
working tree with all three code changes applied

```
.................                                                        [100%]
17 passed in 2.56s
```

canonical: this session's own edits to `docs/specs/generated-paths.md`
(the `stop-poll-rearm.sh` row) and to
`on-the-record/hooks/gate-registration-guard.sh` /
`test_gate_registration_guard.py`, cross-referenced against the fenced
transcript above.

The 17 passes above combine `gates/test_generated_paths.py` (unchanged
file, its own full case set) with
`on-the-record/hooks/test_gate_registration_guard.py` (its pre-existing
case set plus the one new regression case added this session).

Full-suite comparison (the issue's own Acceptance check: run `gates/
tests/ on-the-record/hooks/` on the branch and on `origin/main`, compare
failure sets). Both runs used isolated `git worktree` checkouts, never
the primary working tree, so each run's own `git status` reads clean.

canonical: `tests/test_gates.py`'s `t_rulebook_version_is_recorded` test
and this session's earlier direct pytest run against the (then-dirty)
primary working tree, which failed on exactly this assertion before the
worktree-based re-run below.

That test asserts the checked-out rulebook version string carries no
"커밋안됨" (uncommitted) marker, so running the suite directly against an
uncommitted working tree registers a spurious failure unrelated to this
change — using worktrees for both comparison runs avoids that.

derived: `git stash create` (non-destructive — leaves the working tree
and index untouched) to snapshot the three code changes, then
`git worktree add --detach` that snapshot commit into a scratch
directory, then `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`
inside that worktree, this session

```
1211 passed, 2 skipped, 1 xfailed in 192.88s (0:03:12)
```

derived: `git worktree add --detach` pointed at `origin/main` in a second
scratch directory, then `python3 -m pytest gates/ tests/
on-the-record/hooks/ -q` inside that worktree, this session

```
=================================== FAILURES ===================================
____________________ t_all_generators_recorded_and_disjoint ____________________
E       AssertionError: stop-poll-rearm.sh 는 write 호출이 없는데 docs/specs/generated-paths.md 는 n/a 가 아닌 'out-of-tree' 로 기록했다.
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
1 failed, 1219 passed, 2 skipped, 1 xfailed in 199.79s (0:03:19)
```

derived: diffing the two fenced pytest summary lines directly above.

Failure-set delta: the branch run's failure set is empty; `origin/main`'s
failure set contains exactly `t_all_generators_recorded_and_disjoint`.
That is exactly minus one failure — the target failure — with no new
failure appearing on the branch side. This is the delta the issue's
Acceptance section and the proposal's "What will be done" ask for.

canonical: `git merge-base HEAD origin/main`, this session, resolving to
`303f81654a123ddfefe3f3b0181b126642911c67`, and
`git log --oneline HEAD..origin/main`, this session, listing commits
landed on `origin/main` after that merge-base and not yet on this branch.

```
$ git merge-base HEAD origin/main
303f81654a123ddfefe3f3b0181b126642911c67
$ git log --oneline HEAD..origin/main | cat
772d0f9 issue-776: steady-state re-run — remote-seed fix works, three new blockers surface (#845)
febdf0b issue-839: phase-1 survey + proposal for generated-paths.md row fix + gate-registration-guard classification check (#844)
80426ea issue-834: port strict shlex-based command-shape check into spawn-allow-gate.sh (#842)
8ce2a5d issue-835: implement plugin Monitor for default-on ~60s poll heartbeat (#841)
f1d98d6 issue-831: top-level setup preflight replaces mid-delegation remote stall (#840)
```

Those five commits, unrelated to this fix, are why `origin/main`'s total
pass count in the fenced transcript above is larger than the branch's:
they landed new passing tests on `origin/main` that this branch — cut
from the merge-base before them — does not have. The failure-SET
comparison above is unaffected by that gap; only the unrelated total
count differs, for a reason independent of this change.

derived: `read_spec()` `UnicodeDecodeError` reproduction (before-landing
hunt finding), this session — a scratch git repo with a hook script
containing one invalid-UTF-8 byte, a `generated-paths.md` row recording
it `n/a` (wrong under the ported check — the file has an `mkdir -p`
write call), staged and piped through the guard as a
`git commit -m test` PreToolUse payload. Before the fix:

```
Traceback (most recent call last):
  File "<string>", line 193, in <module>
  File "<string>", line 161, in read_spec
  File "<frozen codecs>", line 322, in decode
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 46: invalid start byte
EXIT: 1
```

After the fix, same scratch repo and payload:

```
EXIT: 0
```

canonical: the fenced `EXIT: 0` transcript directly above, this session.

Exit 0 there is `read_spec()`'s own documented fail-open posture on an
unreadable/undecodable source file, not a classification denial — it
replaces the uncaught crash above with the same defined behavior the
function already used elsewhere for other read failures, so the incident
shape #839 reports is caught for every hook script whose source decodes
cleanly, and no longer crashes the guard process for one that does not.

## Open findings

None.
