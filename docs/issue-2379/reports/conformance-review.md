---
issue: 2379
role: conformance-review
author: conformance-review
loop_state: complete
upstream:
  - path: baef6d2dc3eaac385d24522831316129065f2d50:docs/issue-2379/reports/implementation.md
    sha: baef6d2dc3eaac385d24522831316129065f2d50
subject: PR #2448 (issue-2379/implementation)
test: tests/test_spawn_pipeline.py
result: passed
assertedBy: conformance-review (independent re-run, this session)
---

# issue-2379 — conformance-review record

## What was done

Builder-blind conformance review of PR #2448 (`issue-2379/implementation`,
head `baef6d2dc3eaac385d24522831316129065f2d50`, hereafter `baef6d2d`)
against issue #2379's own Acceptance section, never against the PR's own
account of itself.

derived: git worktree add /tmp/review-2379 origin/issue-2379/implementation — result:
```
HEAD의 현재 위치는 baef6d2d입니다 issue-2379: add skill-verdict line to implementation record
```

Note: the implementation record at
`baef6d2d:docs/issue-2379/reports/implementation.md` exists only on PR
#2448's branch, not on this review's own branch — every citation to it
below is commit-pinned (`baef6d2d:<path>:<line>`), not a bare
repo-relative path, since that path is absent on `main`/this branch as
of this writing.

The issue's 3 Acceptance lines split into 4 checkable requirements (one
line bundles "verifies...and refuses/retries", which are two distinct
obligations: a check, and one of two possible responses to a failed
check):

- REQ-1 (edge-case): reproduce the corrupted-merge-base condition under
  concurrent spawn load, **or** determine it cannot be reproduced and
  downgrade the issue to a documented one-off, with a guard added
  regardless.
- REQ-2 (functional): the branch-cut step verifies the new branch's
  merge-base with main is recent/sane before opening the PR.
- REQ-3 (error-handling): the branch-cut step refuses, or retries once
  then refuses, when that check fails.
- REQ-4 (test-coverage gate): a new regression test exists that would
  have caught the original incident.

### REQ-1 — Present

verification method: Analysis (a live concurrent-spawn race against a
real GitHub remote is not reproducible from this sandbox — no outbound
network to a forge, no way to race concurrent processes against it in
this turn; matches conformance-review-verification-method-selection
rule 2) for the "cannot reproduce" determination, plus Test for the
"guard added anyway" half.

- requirement: "reproduce...or determine it cannot be reproduced...with
  a guard added anyway"
- spec_ref: issue #2379 Acceptance, bullet 1
- canonical: baef6d2d:docs/issue-2379/reports/implementation.md (the "Reproduction" paragraph — quoted verbatim from `gh pr diff 2448`, this session)
```
**Reproduction.** The original incident needs a live GitHub remote,
concurrent spawns, and a race between a narrow-refspec fetch and
`origin/HEAD` resolution — not reproducible deterministically inside this
sandbox (no outbound network to a real forge, no way to race concurrent
spawn processes against it in this turn). Per the acceptance criterion's
own fallback ("or determine it cannot be reproduced... and add a guard
anyway"): `test_checkout_refuses_branch_with_corrupted_merge_base`
reproduces the *state* the race produces instead...
```
- acceptance: (from /tmp/review-2379) python3 -m pytest tests/test_spawn_pipeline.py -k test_checkout_refuses_branch_with_corrupted_merge_base -v — result:
```
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_refuses_branch_with_corrupted_merge_base PASSED
1 passed in 1.24s
```
- rationale: the acceptance line is an explicit OR — this sandbox
  genuinely cannot race a real remote (no outbound network), and the
  implementation record documents that limitation instead of silently
  skipping it (canonical above); the "guard added anyway" branch is
  independently re-run in this same session (acceptance above), not
  copied from the PR body, and reproduces the *state* a race would leave
  behind (two independently-diverged lineages sharing only a root
  commit). Same test also satisfies REQ-4 below — collapsed to one
  citation there per conformance-review-traceability-and-evidence rule 4
  rather than duplicated in full.
- Note: the issue's own wording is "downgrade this issue to a documented
  one-off" — no separate issue-label/comment action was taken; the
  downgrade is documented in the implementation record's own "Why"
  section rather than as a GitHub-side action. Treated as satisfying the
  intent rather than a literal mechanic, since the issue names no
  specific GitHub downgrade action.

### REQ-2 — Present

verification method: Inspection (structural: does a merge-base check
exist ahead of every branch-cut return) + Test (existing regression
test exercises it).

- requirement: "spawn.py's branch-cut step verifies its new branch's
  merge-base with main is recent...before opening the PR"
- spec_ref: issue #2379 Acceptance, bullet 2 (first clause)
- canonical: baef6d2d:pipeline.py:958-997 (`_verify_branch_base_sane`, read directly in /tmp/review-2379, this session)
```
def _verify_branch_base_sane(cwd: str, br: str, base: str) -> str | None:
    def git(*a):
        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
    mb = git("merge-base", br, base)
    if mb.returncode != 0 or not mb.stdout.strip():
        return None
    merge_base_sha = mb.stdout.strip()
    base_sha_r = git("rev-parse", "-q", "--verify", base)
    base_sha = base_sha_r.stdout.strip() if base_sha_r.returncode == 0 else None
    if base_sha is not None and merge_base_sha == base_sha:
        return None
    stat_r = git("diff", "--shortstat", merge_base_sha, br)
    if stat_r.returncode != 0 or not stat_r.stdout.strip():
        return None
    m = _DIFF_SHORTSTAT_RE.search(stat_r.stdout)
    if not m:
        return None
    files = int(m.group(1))
    lines = int(m.group(2) or 0) + int(m.group(3) or 0)
    if files > _branch_base_max_files() or lines > _branch_base_max_lines():
        return (f"merge-base {merge_base_sha[:12]} vs {br}: {files} files changed, "
                f"{lines} lines...")
    return None
```
- canonical: baef6d2d:pipeline.py:1001-1051 (`_checkout_named_branch`, read directly in /tmp/review-2379, this session) — confirms the guard call sits once, after the recut/origin-tracking/fresh-cut/absorbed-reuse if/elif/else block, so every sub-path converges through it before returning `br`
```
    if git("rev-parse", "--verify", "-q", br).returncode == 0:
        r = _sp._recut_absorbed_branch(cwd, br)
    elif git("rev-parse", "--verify", "-q", f"origin/{br}").returncode == 0:
        r = git("checkout", "-b", br, f"origin/{br}")
    else:
        base = _sp._base(cwd)
        r = git("checkout", "-b", br, base)
        if r.returncode != 0:
            r = git("checkout", "-b", br)
    if r.returncode != 0:
        sys.exit(f"브랜치 {br} 로 못 갈아탔다: {r.stderr.strip()[:200]}")
    base = _sp._base(cwd)
    diag = _sp._verify_branch_base_sane(cwd, br, base)
    ...
```
- derived: grep -n "_checkout_named_branch" /tmp/review-2379/pipeline.py — result:
```
1001:def _checkout_named_branch(cwd: str, br: str) -> str:
1071:def checkout_issue_branch(cwd: str, issue: int, role: str) -> str:
1077:    return _sp._checkout_named_branch(cwd, f"issue-{issue}/{role}")
1080:def checkout_issue_branch_for_skill(cwd: str, issue: int, skill: str,
1094:    return _sp._checkout_named_branch(cwd, f"issue-{issue}/{skill}-{disambiguator}")
```
  — confirms both public entry points delegate to the one guarded
  choke point.
- acceptance: (from /tmp/review-2379) python3 -m pytest tests/test_spawn_pipeline.py -k "corrupted_merge_base or bounded_diff_from_old_merge_base" -v — result:
```
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_refuses_branch_with_corrupted_merge_base PASSED
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base PASSED
2 passed in 1.38s
```
- rationale: the requirement's actual condition — catch a branch whose
  history diverged from an unrelated point before a PR opens — is
  demonstrated to fire (first line of the acceptance re-run above). The
  implementation substitutes a diff-size heuristic for the
  parenthetical's illustrative age/commit-count/SHA-match examples; the
  second re-run line above (bounded-diff-from-old-merge-base) confirms a
  calendar-old, commit-count-old, but small-diff branch is accepted
  rather than false-flagged, matching the design rationale in
  `baef6d2d:docs/issue-2379/reports/implementation.md`'s "Why" section
  (this repo's own multi-day approval-wait workflow would otherwise
  false-positive under an age-based check). Since the parenthetical is
  prefixed "e.g." (illustrative, not the requirement text itself) and
  the substitute measurably catches the condition the issue actually
  describes, this is Present, not a deviation from the requirement.

### REQ-3 — Present (refuse path), Surface (retry-recovery path)

verification method: Test (refuse path, existing regression test) +
Inspection (retry path, no test exercises the self-heal branch).

- requirement: "...and refuses/retries if not"
- spec_ref: issue #2379 Acceptance, bullet 2 (second clause)
- canonical: baef6d2d:pipeline.py:1043-1067 (read directly in /tmp/review-2379, this session)
```
    diag = _sp._verify_branch_base_sane(cwd, br, base)
    if diag is not None:
        git("remote", "set-head", "origin", "-a")
        git("fetch", "--prune", "-q", "origin")
        base = _sp._base(cwd)
        diag = _sp._verify_branch_base_sane(cwd, br, base)
    if diag is not None:
        sys.exit(f"브랜치 {br} 의 merge-base 가 base({base})와 크게 어긋나 "
                 f"있다 (이슈 #2379 가드) — {diag}. ...")
    return br
```
- acceptance: (from /tmp/review-2379) python3 -m pytest tests/test_spawn_pipeline.py -k test_checkout_refuses_branch_with_corrupted_merge_base -v — result:
```
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_refuses_branch_with_corrupted_merge_base PASSED
1 passed in 1.24s
```
- derived: grep -n "def test_checkout_refuses_branch_with_corrupted_merge_base\|def test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base" /tmp/review-2379/tests/test_spawn_pipeline.py — result:
```
1108:    def test_checkout_refuses_branch_with_corrupted_merge_base(self):
1166:    def test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base(self):
```
  — confirms neither of the two new tests stages a *transient* stale
  `origin/HEAD` that the retry block (`git remote set-head` + `fetch
  --prune`) is meant to recover from before re-checking; one test never
  reaches a corrupted state at all (control), the other's corruption is
  a genuinely divergent lineage that re-fetching cannot fix, so the
  retry always falls through to refuse in both — the retry's own
  recovery branch is exercised by neither.
- rationale: the refuse half is Present per the acceptance re-run above
  — implemented, reachable through the shared choke point (REQ-2's
  canonical citation), and demonstrated by a re-run test this session.
  The retry half is Surface per
  conformance-review-verdict-assignment rule 1: matching code exists
  (canonical above) and is wired into the same guarded path, but the
  `derived:` grep above confirms no test in the diff constructs the one
  condition the retry exists to handle — a stale `origin/HEAD` that
  self-heals on re-fetch — so its correctness rests on inspection only,
  not a demonstrated pass.

### REQ-4 — Present

verification method: Test, reused per
conformance-review-verification-method-selection rule 4 (existing
executable tests already claim this coverage — not re-derived as a
parallel manual check).

- requirement: "a new regression test that would have caught this"
- spec_ref: issue #2379 Acceptance, bullet 3 (gate)
- canonical: baef6d2d:tests/test_spawn_pipeline.py:1108-1200 (both new test bodies, read directly in /tmp/review-2379, this session — full bodies in `gh pr diff 2448`, not reproduced verbatim here per traceability rule 4 collapse with REQ-1/REQ-2/REQ-3's citations of the same tests)
- acceptance: (from /tmp/review-2379) python3 -m pytest tests/test_spawn_pipeline.py -k "corrupted_merge_base or bounded_diff_from_old_merge_base" -v — result:
```
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_refuses_branch_with_corrupted_merge_base PASSED
tests/test_spawn_pipeline.py::WorkspaceSyncFailClosed::test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base PASSED
2 passed in 1.38s
```
- acceptance: (from /tmp/review-2379) python3 -m pytest tests/test_spawn_pipeline.py -q — result:
```
........................................................................ [ 79%]
.................[execution-observation] auto-sweep(백그라운드) 1.086s 만에 끝남 (지움 0, 실패 0)
..                                                      [100%]
91 passed in 8.73s
```
  (Matches PR #2448's own claimed counts exactly — independently
  reproduced in a fresh worktree this session, not copied from the PR
  body.)
- rationale: the acceptance text's parenthetical suggests "mock a stale
  ref"; the actual tests instead build two real, independently-diverged
  git lineages sharing only a root commit and check out a branch from
  the stale one (`test_checkout_refuses_branch_with_corrupted_merge_base`)
  plus a control with a real 50-commit-ahead `main` and a legitimately
  old-but-small branch diff
  (`test_checkout_accepts_branch_with_bounded_diff_from_old_merge_base`)
  — a real-fixture reproduction of the corrupted state, at least as
  strong evidence as a mock would be for "would have caught this," so
  this satisfies the requirement's intent.

## Why

Sampling: full enumeration used, not a derived sample —
conformance-review-sampling-derivation is not applicable here (only 3
acceptance lines / 4 extracted requirements, one PR, two files changed
in production code plus one test file; no cross-product large enough to
need stratification). conformance-review-severity-classification is
also not applicable — this review's scope was not extended into
risk-weighting a finding, only ordinary fidelity-checking.

acceptance: (from /tmp/review-2379) python3 -m pytest tests/test_spawn_pipeline.py -q — result:
```
91 passed in 8.73s
```

Every Present/Surface verdict in "What was done" above was independently
re-derived this session (fresh worktree at PR head `baef6d2d`, own
pytest invocations quoted per-requirement above, own `grep`/direct-read
of the actual files) — none copied from the PR body or
`baef6d2d:docs/issue-2379/reports/implementation.md`'s pasted output,
per this role's builder-blind mandate. The full-suite re-run
(immediately above) and the two targeted-test re-runs (REQ-2/REQ-4
above) both independently matched PR #2448's own claimed counts exactly.

## Upstream basis

`baef6d2d:docs/issue-2379/reports/implementation.md` (PR #2448 head,
`baef6d2dc3eaac385d24522831316129065f2d50` — not landed on `main`/this
branch, hence the commit-pinned citations throughout rather than a bare
path) is the implementation this record reviews.

## Open findings

1. **REQ-3 retry-recovery path is Surface, not Present** — the
   recompute-`origin/HEAD`-and-refetch retry block
   (`baef6d2d:pipeline.py:1052-1059`) is real and wired into the guarded
   path, but the `derived:` grep in REQ-3 above confirms no test
   constructs a transient-staleness case that the retry actually
   resolves. Resolution path: a follow-up test that stages a wrong
   `origin/HEAD` symref, has the retry's `set-head -a` + `fetch --prune`
   correct it, and asserts `checkout_issue_branch` succeeds afterward.
   Non-blocking — the refuse path (the actual safety property the issue
   cares about) is fully demonstrated (REQ-3 acceptance re-run); an
   unverified-but-plausible self-heal branch is on the safe side (worst
   case, a working self-heal is skipped and a legitimate branch gets
   refused with a clear diagnostic and a manual recovery command, not
   silently corrupted).
2. **REQ-1's "downgrade" is documentary, not a GitHub-side action** — no
   issue comment/label change found; the reasoning lives only in
   `baef6d2d:docs/issue-2379/reports/implementation.md`. Non-blocking
   per REQ-1's own note above — the issue names no specific downgrade
   mechanic.

## Next steps

None. If REQ-3's retry-recovery path is ever exercised by a future
session, add the transient-staleness test named in Open finding 1 — no
code change is being requested by this review itself.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue's 3 acceptance lines into 4 one-obligation items (REQ-2/REQ-3 split from one bundled "verifies...and refuses/retries" line), dimension-tagged each.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; Analysis for the unreproducible-in-sandbox concurrent-spawn race (REQ-1), Inspection for the structural choke-point claim (REQ-2), Test reused (not re-derived) for REQ-3's refuse path and REQ-4.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; REQ-3 split into Present (refuse, demonstrated) and Surface (retry-recovery, code exists but unexercised) per rule 1 rather than one bare verdict for the whole line.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every evidence line cites file:line-range plus the commit sha actually read (`baef6d2d`, this review's own checkout, not the PR body); REQ-1's and REQ-4's shared test evidence collapsed to one citation per rule 4 instead of duplicated in full.
skill-verdict: conformance-review-finding-record — applied: invoked; every requirement block carries requirement/spec_ref/verdict/evidence/rationale; Open findings section states each finding's resolution path.
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of all 4 extracted requirements was feasible (one PR, two production files plus one test file changed), no stratified sample was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: review scope was ordinary fidelity-checking, never extended into risk-weighting a recorded finding.
skill-verdict: implementation-audit — not-applicable: this session is the independent evaluator half of that protocol by construction (builder-blind conformance-review against a separately-authored implementation PR), not a case requiring the cross-family protocol to be separately invoked.
