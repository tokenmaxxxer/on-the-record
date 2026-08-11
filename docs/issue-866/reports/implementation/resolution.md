# Resolution — issue #866 spec-index fix (phase-1 session)

canonical: docs/issue-866/proposals/2026-08-11-regenerate-spec-index-and-record-preflight-gap.md
(Note above ## Request) — this write-up lives here, not at the role's usual
implementation.md record path, because that path is
mechanically approval-gated (`on-the-record/hooks/approval-gate.sh`)
and no `APPROVE issue-866/implementation` comment exists yet for this
issue. Everything below is phase-1-legal content: research findings,
reproductions, and the verification this session actually ran against
its own committed fix.

## What was done

1. Regenerated `docs/specs/reconciled-index.md` via
   `python3 gates/spec_index.py --update` — the one drifted row
   (`docs/handbooks/setup.md`, changed by PR #863 without a matching
   index regen) is now recorded at its current hash; no other row
   changed.
2. Read PR #863's full `docs/handbooks/setup.md` diff and
   `docs/specs/reconciled-index.md`'s "Resolved ambiguities" section in
   full: the diff is a pure addition (two new paragraphs documenting
   `MUSTER_STATE_ROOT`) that neither edits nor contradicts the file's one
   existing entry (ledger storage location) or any other tracked
   document. No new "Resolved ambiguities" entry was added — a checked
   decision, not a default.
3. Reproduced — live, not by static reading — why
   `on-the-record/hooks/spec-index-preflight.sh` didn't stop PR #863's
   drift from landing: staged the exact same change-set in an isolated
   worktree and ran the unmodified hook against it. Its
   staged-content-vs-index-hash comparison logic denies correctly (exit
   2). The commit that actually broke `origin/main` (`502981d`) carries
   committer `GitHub <noreply@github.com>`, is GPG-signed, and has a
   single parent — a GitHub server-side squash-merge, which a
   `PreToolUse` hook structurally cannot see (it only fires on Bash tool
   calls a Claude Code session itself issues). No code change to this
   hook can close that particular gap; full detail in
   `docs/issue-866/reports/implementation/survey.md`.
4. This session's after-proposal warrant hunt (stance 0, "assume the
   gate just touched is bypassable") surfaced a second, separate, and
   fixable gap in the same file: the hook's own trigger-detection regex,
   not its hash-comparison logic. See `## What did not work` below for
   the finding and its resolution.
5. Ran `gates/ tests/ on-the-record/hooks/` on this branch and on
   `origin/main` in two isolated `git worktree` checkouts and compared
   failure sets (Acceptance verification below).
6. This session's before-landing warrant hunt (stance 1, "assume this
   change and another plugin's rule cancel each other") surfaced that two
   sibling `PreToolUse`/`Bash` hooks — `gate-registration-guard.sh` and
   `role-axis-completeness-guard.sh` — carry the exact same
   pre-fix trigger regex `spec-index-preflight.sh` just moved away from,
   so the same `git -c <cfg>=<val> <verb> ...` shape still silently
   bypasses those two. Out of this issue's frozen write set; recorded as
   an open finding below, not fixed here.
7. This record.

## Why

canonical: docs/issue-866/proposals/2026-08-11-regenerate-spec-index-and-record-preflight-gap.md
(## Rationale) and docs/issue-866/reports/implementation/survey.md (full
reproduction). The proposal's original Rationale argued no code change to
`spec-index-preflight.sh` was needed, reasoning entirely from the
hash-comparison logic (independently verified correct). The after-proposal
hunt showed that reasoning was incomplete — it never exercised the
trigger-detection step in front of that logic — and surfaced a live,
reproducible bypass there instead. That distinction (comparison logic
correct; trigger detection had a real hole) is the actual shape of this
fix.

## Upstream basis

- docs/issue-866/proposals/2026-08-11-regenerate-spec-index-and-record-preflight-gap.md
- docs/issue-866/reports/implementation/survey.md
- docs/issue-866/reports/implementation/2026-08-11-hunt-regenerate-spec-index-and-record-preflight-gap.md
  (both stances — stance 0's finding and resolution summarized in
  `## What did not work` below; stance 1's finding is open, see
  `## Open findings`)
- 103749e4de93d26ce061c88ada92f3edfa3a36b3 (branch base, == `origin/main`
  at survey time)

## What did not work

The proposal's original plan (`## What will be done`, step 3) was to
leave `on-the-record/hooks/spec-index-preflight.sh` and its test
unmodified, on the expectation that the hook's own logic — verified
correct in the survey's live reproduction — meant there was nothing left
in this file to fix.

canonical: this session's after-proposal `warrant:warrant-hunter`
dispatch (stance 0) and this session's own independent re-run of its
reproduction (transcript in Acceptance verification below).

Actual: the hunter surfaced, and this session verified live, that
`git -c commit.gpgsign=false commit -m "test"` — fed the identical staged
PR #863-shaped drift the survey used to verify the hash-comparison
logic — exits 0 with no stderr, silently letting the drift land. The
gap was not in the comparison logic itself but in the trigger-detection
regex gating it (`\bgit\s+commit\b` requires `commit` to follow `git`
with only whitespace between them; a `-c <cfg>=<val>` or any other global
option in between defeats it, even though git itself parses the command
as `git commit` without issue).

Resolved by widening the trigger check to a `shlex.split`-based token
test (`"git" in tokens and "commit" in tokens`), which tolerates any
number of intervening global options while still not matching `commit`
inside an unrelated token (`--grep=commit`, `commit-tree`) or inside a
quoted string. Re-ran the hunter's exact reproduction after the fix —
denies (exit 2) — and added 6 regression cases to
`on-the-record/hooks/test_spec_index_preflight.py` covering the fixed
shape and its neighboring true-negative/fail-open cases.

## Rationale for deviations

canonical: the diff between the approved proposal's `## What will be
done` step 3 (leave the hook and its test unmodified) and what this
session actually left on the branch (the hook's trigger check rewritten,
6 new test cases added).

The proposal's step 3 was written before the after-proposal hunt ran; the
hunt is a mandatory step in the same phase, not an optional check, and
it surfaced a real, live-reproducible bypass in a file already inside
this issue's frozen write set (`on-the-record/hooks/spec-index-preflight.sh`
and its test were both listed as candidate write targets from the start,
conditioned on the proposal's own fix-if-warranted language). No path outside that pre-declared
write set was touched to resolve it. The change itself does not alter
the hash-comparison logic the original Rationale argued was correct —
it only widens what commands reach that logic, which is exactly what
the finding showed was missing. Gap B (the GitHub server-side
squash-merge blind spot) and Gap A (why the original branch commit
`ac8156d6` wasn't denied — no session transcript exists to settle it)
are unaffected by this fix and remain as the survey described; the fix
gives Gap A a plausible (not settled) mechanism, detailed in the
survey's "After-proposal hunt finding and resolution" section.

## Hunt

canonical: docs/issue-866/reports/implementation/2026-08-11-hunt-regenerate-spec-index-and-record-preflight-gap.md

After-proposal hunt (stance 0, cap 60s, tier default — diff was
docs-only at dispatch time) ran once and returned the finding resolved
in `## What did not work` above.

Before-landing hunt (stance 1, cap 180s, tier size:large — diff had
grown to 6 files / 509 insertions after the stance-0 fix) ran once and
returned one finding, verified independently by this session (below,
not fixed — see `## Open findings`).

## Open findings

canonical: docs/issue-866/reports/implementation/2026-08-11-hunt-regenerate-spec-index-and-record-preflight-gap.md
(before-landing, stance 1), and this session's own independent check —
`grep`-equivalent read of both files, this session:

```
on-the-record/hooks/role-axis-completeness-guard.sh:60:if not re.search(r"\bgit\s+commit\b", cmd):
on-the-record/hooks/gate-registration-guard.sh:56:if not re.search(r"\bgit\s+commit\b", cmd):
```

Both lines verified present, byte-identical to the regex this issue's
fix just moved `spec-index-preflight.sh` away from. The hunter's own
live reproduction (in the hunt record) staged an unregistered
scratch module under gates/ (deleted after the probe, per the hunt
record's own reproduction script) and showed `gate-registration-guard.sh`
denies it (exit 2) under a plain `git commit -m msg`, but exits 0 with
no stderr under `git -c user.name=Bot -c user.email=bot@example.com
commit -m msg` against the identical staged violation.

This is a real, reproduced finding — and out of this issue's frozen
write set (`docs/specs/reconciled-index.md`,
`on-the-record/hooks/spec-index-preflight.sh` + its test, and
`docs/issue-866/`). Per the SCOPE-EXCEEDED rule, this session finishes
what the proposal covers and reports rather than widening the write set
mid-build to patch two files never proposed for this issue. Needs a new
issue: port the same `shlex.split`-based trigger fix to
`gate-registration-guard.sh` and `role-axis-completeness-guard.sh` (both
already cite `spec-index-preflight.sh`'s trigger line as their own
precedent, canonical: the hunt record's stance-1 section), each with its
own regression test mirroring the six cases added here (derived: `on-the-record/hooks/test_spec_index_preflight.py`, this session).

## Closed checks

- closed_checks: spec-index-drift-baseline-regen, code_sha: docs/specs/reconciled-index.md
  (this branch's tip at record time) — `t_baseline_repo_passes` in `tests/test_spec_index.py`
  no longer fails (Acceptance verification below).
- closed_checks: spec-index-preflight-trigger-bypass, code_sha: on-the-record/hooks/spec-index-preflight.sh+on-the-record/hooks/test_spec_index_preflight.py
  (this branch's tip at record time) — the hunter's exact reproduction
  (`git -c commit.gpgsign=false commit -m "test"` against the PR
  #863-shaped staged drift) now denies; 6 new regression cases pass.

## Doc placement

- No new env var, config key, dependency, migration, or setup step
  appears in this change — no handbook update applies.
- No changed public signature or wire format — `spec-index-preflight.sh`
  is an internal hook script with no external interface; its
  registration row in `docs/specs/enforcement-boundary.md` and
  `docs/specs/generated-paths.md` already describes it as intercepting
  `git commit` and stays accurate after this fix (the trigger condition
  changed how that interception is detected, not what it intercepts).
- The two judgment calls this issue turned on (whether "Resolved
  ambiguities" needed an update; whether the hook was fixable) were
  argued and recorded in the phase-1 proposal and survey per the
  survey-order-directive — no separate decisions record was written.

## Acceptance verification

derived: `python3 -m pytest tests/test_spec_index.py -q`, this session,
working tree with the index regen applied

```
....                                                                     [100%]
4 passed in 0.02s
```

canonical: this session's own edit to `docs/specs/reconciled-index.md`,
cross-referenced against the fenced transcript above.

derived: `python3 on-the-record/hooks/test_spec_index_preflight.py`,
this session, working tree with the hook fix and its 6 new regression
cases applied

```
PASS: red: tracked file staged content changed, index not staged -> mismatch
PASS: red: tracked file changed, index staged but still carries OLD hash
PASS: green: tracked file changed, staged index carries matching NEW hash
PASS: green: unrelated file staged, tracked file untouched -> no mismatch
PASS: green: tracked file staged but content unchanged -> no mismatch
PASS: skip: tracked file staged but git show failed (deletion) -> no mismatch
PASS: trigger: plain `git commit` is recognized
PASS: trigger: issue #866 regression — `git -c k=v commit` is recognized
PASS: trigger: `git log --grep=commit` is not a commit invocation
PASS: trigger: `git commit-tree` is not `git commit`
PASS: trigger: 'commit' only inside a quoted string is not a commit invocation
PASS: trigger: unparseable command (unbalanced quote) fails open -> False
all tests passed
```

Full-suite comparison (the issue's own Acceptance check): staged the full
intended write set (`git add`), took a non-destructive snapshot via
`git stash create` (leaves the working tree and index untouched), then
ran `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` in two
isolated `git worktree` checkouts — one at that snapshot, one at
`origin/main` — never the primary working tree (this repo's own
`t_rulebook_version_is_recorded` fails against a dirty tree, so a direct
in-place run is not a valid comparison method).

canonical: `git rev-parse HEAD` and `git merge-base HEAD origin/main`,
this session, both resolving to `103749e4de93d26ce061c88ada92f3edfa3a36b3`
— this branch and `origin/main` are the same commit prior to this
change, so there is no unrelated-commits gap to account for in the
count comparison below.

Branch snapshot (`2088a8b453afc0baa8fdfb744c572053056e3e51`, `git stash
create` of the full staged write set — index regen, hook fix, its 6 new
tests, and the docs/issue-866 files), this session:

```
1255 passed, 2 skipped, 1 xfailed in 199.29s (0:03:19)
```

`origin/main` (`103749e4de93d26ce061c88ada92f3edfa3a36b3`), this session:

```
=================================== FAILURES ===================================
____________________________ t_baseline_repo_passes ____________________________

    def t_baseline_repo_passes():
        """현재 저장소 상태에서 인덱스와 실제 파일이 일치해야 한다."""
        bad = spec_index.check(REPO_ROOT)
>       assert bad == [], bad
E       AssertionError: ['docs/handbooks/setup.md: 내용이 바뀌었는데 docs/specs/reconciled-index.md 의 기록된 해시와 다르다 (기록=df9c71068366…, 실제=240ea33619b4…) — 의도된 변경이면 `python3 gates/spec_index.py --update` 로 재생성하고 관련 있다면 "Resolved ambiguities" 도 갱신하라']
E       assert ['docs/handbo...ties" 도 갱신하라'] == []

tests/test_spec_index.py:35: AssertionError
=========================== short test summary info ============================
FAILED tests/test_spec_index.py::t_baseline_repo_passes - AssertionError: ['d...
1 failed, 1254 passed, 2 skipped, 1 xfailed in 198.08s (0:03:18)
```

derived: diffing the two fenced pytest summary lines directly above.

Failure-set delta: the branch run's failure set is empty;
`origin/main`'s failure set contains exactly `t_baseline_repo_passes`.
Total collected-test counts differ by exactly one in the same direction
(branch 1255 passed vs. `origin/main` 1254 passed + 1 failed = 1255
collected either way) — the 6 new regression cases added to
`on-the-record/hooks/test_spec_index_preflight.py` are exercised by that
file's own hand-rolled `main()` runner (function names `_t7`-`_t12`, not
pytest's `test_*` collection convention, matching this file's
pre-existing `_t1`-`_t6` cases), so they are not separately collected by
`pytest gates/ tests/ on-the-record/hooks/` and do not add to this
count — their own pass/fail is the fenced transcript above this
section. This is exactly minus one failure — the target failure — with
no new failure introduced on the branch side, which is what the issue's
Acceptance section and the proposal's "What will be done" ask for.
