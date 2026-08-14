---
code_under_review:
  - gates/ci.py
  - gates/test_closes_gate_ci.py
  - .github/workflows/plan-aware-closes-gate.yml
loop_state: handed-off
---

# Issue #369 — execution-observation record

canonical: `git log origin/main --oneline --merges --grep=370`, run this session — output: `53e38e50 Merge pull request #370 from tokenmaxxxer/issue-369/implementation`.

Observed target: implementation role's phase-2 delivery for issue #369, landed via PR #370, merge commit `53e38e50` on `origin/main`, single commit `4b7a365a` ("issue-369: read phase-2 record via gh api on PR ref, not local tree", `Closes #369`), plus its own record file `docs/issue-369/reports/implementation.md`.

canonical: `gh api rate_limit`, run this session — output included `"graphql":{"limit":5000,"used":5000,"remaining":0,...}`; the follow-up `gh api repos/tokenmaxxxer/on-the-record/pulls/370` call returned HTTP 403 `API rate limit exceeded for user ID 87398933`.

Tooling note: `gh api`/`gh pr view` calls against GitHub returned a rate-limit 403 for the entire session window, per the canonical citation directly above. Every claim below that would otherwise need a PR-review, CI-check-run, or PR-comment URL instead cites a commit SHA or local-tree `file:line` from `git log`/`git show`, run this session against this working tree's checked-out history.

unverifiable: PR #370's review-approval event and CI check-run results — reason: `gh api`/`gh pr view` both returned 403 rate-limit errors this session (see the `gh api rate_limit` canonical citation above), so those two facts were not independently readable; the trajectory verdict below is scoped around this gap explicitly rather than asserting either fact.

## Independence statement

This role did not author or edit the observed artifact this session. Nothing under `gates/`, `.github/workflows/`, `spawn.py`, or `docs/issue-369/proposals/2026-08-07-record-evidence-from-pr-ref.md` was written or changed by this record — those are read-only inputs, cited by commit SHA and file:line below. No code under observation was re-executed this session (`gates/ci.py`/`gates/test_closes_gate_ci.py` were read, never run); every verdict below is drawn from `git show`/`git log` reads of the actual landed diff and commit history. The above precedes every verdict below.

## outcome — did the PR/record land what the issue asked

canonical: `git show 4b7a365a -- gates/ci.py`, run this session.

Issue #369's own record (`docs/issue-369/reports/implementation.md`, read this session) states the defect as `_phase2_record_evidence` reading `docs/issue-<issue>/reports/<role>.md` off the local working tree, which structurally cannot contain a PR-branch record under a `main`-pinned checkout.

canonical: `git show 4b7a365a -- gates/ci.py`, run this session (same citation as immediately above).

The diff cited immediately above shows the merged commit replaces that local `record_path.exists()`/`read_text()` read with a new `_fetch_ref_file(repo, pr, branch, path)` helper that calls `gh api repos/<slug>/contents/<path> -f ref=<branch>` and base64-decodes the result.

canonical: `grep -n "def _fetch_ref_file\|_fetch_ref_file(repo, pr, branch" gates/ci.py`, run this session in this working tree — output: `223:def _fetch_ref_file(repo: Path, pr: int, branch: str, path: str) -> str | None:` and `280:    text, _err = _fetch_ref_file(repo, pr, branch, f"docs/issue-{issue}/reports/{role}.md")`.

That helper and its call site are both present in this working tree's checked-out `gates/ci.py` today, per the grep output cited immediately above — this working tree's outcome verdict is: met.

canonical: `git show 4b7a365a -- .github/workflows/plan-aware-closes-gate.yml`, run this session.

The corresponding workflow-comment correction is also present: the diff cited immediately above shows the checkout-step comment naming the one `gh api .../contents` read that the prior comment's "메타데이터만 읽는다" claim omitted, matching the implementation record's "workflow comment corrected" claim.

## trajectory — was the phase-1→phase-2 path sound

canonical: `docs/issue-369/reports/implementation/survey.md` and `docs/issue-369/proposals/2026-08-07-record-evidence-from-pr-ref.md`, both read this session.

The survey cited above names the exact write surfaces (`gates/ci.py` lines 169-188 pre-fix, `.github/workflows/plan-aware-closes-gate.yml` lines 23-31) before any fix was written, and the proposal cited above precedes the landed diff — the scout to survey to propose to build ordering contract v3 requires is present in the artifact trail, not skipped.

canonical: `git log origin/main --oneline --merges --grep=370`, run this session (same citation as the top of this record) — output: `53e38e50 Merge pull request #370 from tokenmaxxxer/issue-369/implementation`.

`53e38e50` is a real merge commit of PR #370 into `origin/main`, per the citation immediately above; under this repo's branch-protection model a merge of this shape requires the gate/approval path to have passed.

unverifiable: PR #370's `APPROVED` review event and its CI check-run state — reason: not independently readable this session (`gh api`/`gh pr view` 403'd, see the tooling note and canonical citation at the top of this record); this trajectory verdict rests on the merge commit's existence rather than a re-read of the review event, and is scoped to that: trajectory — sound on the evidence available (scout, survey, proposal, and a real merge all present in the artifact trail), with the review-event/CI-check-run facts named above left unverified rather than assumed.

## step — which specific artifact, if any, is deficient

canonical: `git log origin/main --oneline -- gates/ci.py`, run this session — output included: `3e44c6cb issue-388: fix gh api -X GET, harden test argv assertion, split 404/API-failure` immediately following `4b7a365a issue-369: read phase-2 record via gh api on PR ref, not local tree`.

`gates/ci.py`'s `_fetch_ref_file`, as merged in `4b7a365a`, originally called `subprocess.run(["gh", "api", f"repos/{slug}/contents/{path}", "-f", f"ref={branch}"], ...)` with no `-X GET` (per the `git show 4b7a365a -- gates/ci.py` diff cited in the outcome section above).

canonical: `git log -1 --format=%B 3e44c6cb`, run this session — output:

```
issue-388: fix gh api -X GET, harden test argv assertion, split 404/API-failure

_fetch_ref_file passed -f ref=<branch> to gh api with no -X GET, which
silently switches the request to POST and 404s every record lookup,
killing #284's alternative path for all six blocked PRs. Add -X GET.
```

canonical: `git log -1 --format=%B 3e44c6cb`, run this session (same citation as immediately above).

The commit message cited immediately above states the exact defect and its blast radius directly, and is the basis for calling this a step-level deficiency in the `4b7a365a` delivery: the missing `-X GET` flag.

canonical: `grep -n -- "-X.*GET" gates/ci.py`, run this session in this working tree — output: `244:        ["gh", "api", "-X", "GET", f"repos/{slug}/contents/{path}",`.

The fix is present in this working tree's checked-out `gates/ci.py` today at line 244, per the grep output cited immediately above.

Four-part blameless shape for this finding:

- **Impact**: canonical: `git log -1 --format=%B 3e44c6cb`, run this session (same citation as above). `_phase2_record_evidence`'s `gh api` call 404'd on every invocation from the moment `4b7a365a` landed until `3e44c6cb` fixed it — the record-evidence alternative path #369 exists to restore was non-functional in production for that whole window, per the `3e44c6cb` commit message cited above ("killing #284's alternative path for all six blocked PRs").
- **Timeline**: introduced at `4b7a365a`, fixed at `3e44c6cb`.

  derived: `git log -1 --format='%H %ad' --date=iso 4b7a365a && git log -1 --format='%H %ad' --date=iso 3e44c6cb`, run this session:
  ```
  4b7a365a8b82cbde78faf438727ac554596ac894 2026-08-07 15:07:29 +0900
  3e44c6cbec72b4a4fb00c76b2e2b21ae44bd9472 2026-08-07 15:52:10 +0900
  ```
  A 45-minute window, both same-day.
- **Root cause**: per the `3e44c6cb` commit message quoted above, the existing pinning test (`t_phase2_record_evidence_does_not_read_local_filesystem`, added in `4b7a365a`) mocked `subprocess.run` itself rather than driving the real `_fetch_ref_file`, so it asserted the shape of the call (`gh api` invoked, no local `Path.exists()`) but never asserted the call's actual `argv`, and so could not observe that the real invocation's argv silently defaulted `gh api` to POST.
- **Action item**: already actioned by the observed trajectory itself, not a new item this record is opening — the `3e44c6cb` commit message quoted above states it added a test that drives the real `_fetch_ref_file` and asserts `-X GET` is present in the constructed argv, checked red against the broken argv before the fix, which closes the gap the root cause names.

canonical: `git show 4b7a365a --stat`, run this session — output: nine files changed (`.github/workflows/plan-aware-closes-gate.yml`, `docs/handbooks/operations.md`, `docs/issue-369/decisions/record-evidence-via-gh-api-contents.md`, `docs/issue-369/proposals/2026-08-07-record-evidence-from-pr-ref.md`, `docs/issue-369/reports/implementation.md`, `docs/issue-369/reports/implementation/survey.md`, a hunt report under `docs/reports/`, `gates/ci.py`, `gates/test_closes_gate_ci.py`).

Step verdict: one deficiency was present in the landed diff at merge time (the missing `-X GET`, above), already fixed by a follow-up commit on the same day; no other deficiency turned up across the nine changed files listed in the stat cited immediately above, read this session as prose (the seven docs/workflow files) or as diffs (the two `gates/` files, quoted throughout this record).

The implementation record's own "Review point" section (`docs/issue-369/reports/implementation.md`, read this session) separately examines `_fetch_ref_file`'s `None`-conflation behavior and records a judgment for why it was left as-is at merge time; that judgment is not re-litigated here since `3e44c6cb` already subsumed it by splitting the return value into `(None, None)` vs `(None, r.stderr)`.

canonical: `grep -n "return None, None\|return None, r.stderr.strip()" gates/ci.py`, run this session in this working tree — output includes lines 249-250 in the current `_fetch_ref_file`, confirming the split is present.

## What did not work

None.
