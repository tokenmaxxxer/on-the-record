---
issue: 2315
role: conformance-review
loop_state: reported
upstream:
  - path: PR #2321 (branch issue-2315/implementation)
    sha: 2d3c38a42625cb2c3afcf6baf84690ba8d56847e
subject: PR #2321 (tokenmaxxxer/on-the-record) — gh_delta 304-before-returncode reorder for issue #2315
test: issue-2315#Ask + issue-2315#Acceptance (gate / empty state / provenance) + operator-frozen load-reduction constraint
result: passed
assertedBy: issue-2315/conformance-review session (builder-blind), 2026-08-25
---

# issue-2315 — conformance-review record

## What was done

canonical: `git fetch origin issue-2315/implementation` + `git worktree add
/tmp/pr2321-review origin/issue-2315/implementation` (PR #2321 head
`2d3c38a42625cb2c3afcf6baf84690ba8d56847e`), plus `gh issue view 2315` and
`gh pr view 2321` / `gh pr diff 2321` — every citation, test run, and live
probe below was read/executed this session, independent of the builder's
own account of itself, pinned at
`2d3c38a42625cb2c3afcf6baf84690ba8d56847e:docs/issue-2315/reports/implementation.md`
(that path is PR-only and does not exist on this `conformance-review`
branch, hence the sha pin rather than a bare path throughout this
record).

Requirement extraction (conformance-review-requirement-extraction): issue
#2315's Ask paragraph has two independent obligations ("parse the `-i`
status line first; treat page-1 304 as no-change before the returncode
check" and "keep genuine failures classified error") — split into R1/R2
(rule 1). The Acceptance block has four lines: `gate` (R3), `empty state`
(R4), `provenance` — which bundles three obligations (a real cache-valid
no-change probe, a real still-classified-error probe, before/after
heartbeat lines pasted) split into R5/R6/R7 per rule 1 — and
`infrastructure/no-direct-requirement`, which is an issue-classification
tag with no observable success condition of its own (not a checkable
obligation under rule 2, so it is noted here and not scored as an
R-item). The issue body separately freezes an operator constraint
("systemic for every consumer session; the fix REDUCES load by
construction — state that measured in the record"), captured verbatim
into `docs/reports/product/priorities.md` by the builder's second commit
— kept as its own item, R8, since it is a distinct systemic obligation,
not a restatement of R1/R2.

acceptance: `cd /tmp/pr2321-review && git diff --stat main...HEAD` — result:
```
docs/issue-2315/reports/implementation.md | 255 +++++++++++++++++++++++++++
docs/reports/product/priorities.md        |  10 ++
gates/gh_delta.py                         |   2 +-
gates/test_gh_delta.py                    |  31 +++-
4 files changed, 296 insertions(+), 2 deletions(-)
```
small enough that every requirement-bearing hunk was read directly, so
conformance-review-sampling-derivation is not applicable (see
skill-verdict below).

### R1 — Ask: page-1 304 short-circuits to no-change before the returncode check

- requirement: "Parse the `-i` status line first; treat page-1 304 as
  no-change before the returncode check (the consumer's patch shape)."
- spec_ref: issue #2315 Ask, sentence 1
- verdict: **Present**
- canonical: `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:gates/gh_delta.py:172-182`
  (read this session in the worktree):
```
        try:
            r = run(cmd, cwd=root, capture_output=True, text=True)
        except OSError:
            return None, (cur["since"] if cur else None), "error"

        status, headers, body = _split_gh_api_i_output(r.stdout)
        if page == 1 and status == 304:
            got_304 = True
            break
        if r.returncode != 0:
            return None, (cur["since"] if cur else None), "error"
```
- canonical: `main:gates/gh_delta.py:176-181` (this branch's own base,
  read this session) — the same two checks in the opposite order:
```
        if r.returncode != 0:
            return None, (cur["since"] if cur else None), "error"

        status, headers, body = _split_gh_api_i_output(r.stdout)
        if page == 1 and status == 304:
            got_304 = True
            break
```
- rationale: Inspection (conformance-review-verification-method-selection
  rule 1) — a structural code-order property, established by reading
  both versions directly (the two fences above) rather than trusting the
  diff's own framing.

### R2 — Ask: genuine failures still classify error

- requirement: "Keep genuine failures classified error."
- spec_ref: issue #2315 Ask, sentence 2
- verdict: **Present**
- acceptance: `cd /tmp/pr2321-review && python3 -m pytest gates/test_gh_delta.py -v -k test_genuine_non_304_error_still_classifies_error` — result:
```
gates/test_gh_delta.py::test_genuine_non_304_error_still_classifies_error PASSED
1 passed in 26.63s
```
- acceptance: `GH_TOKEN=invalid_bad_token_xyz python3 -c "..."` (fetch_delta against the real repo with a real bad credential, this session) — result:
```
classification (bad token): error items: None cursor: None
```
- rationale: Test-method reuse of the existing regression test (rule 4)
  plus an independent live reproduction against real `gh` with a genuine
  bad credential — both agree the returncode check still fires for every
  non-304 failure.

### R3 — Acceptance gate: gates/test_gh_delta.py

- requirement: `gate: gates/test_gh_delta.py`
- spec_ref: issue #2315 Acceptance, line `gate`
- verdict: **Present**
- acceptance: `cd /tmp/pr2321-review && python3 -m pytest gates/test_gh_delta.py -v` — result:
```
gates/test_gh_delta.py::test_corrupted_cursor_file_classifies_full_rescan PASSED
gates/test_gh_delta.py::test_pagination_follows_pages_burst_over_30_never_dropped PASSED
gates/test_gh_delta.py::test_no_change_tick_makes_exactly_one_probe_and_zero_detail_fetches PASSED
gates/test_gh_delta.py::test_genuine_non_304_error_still_classifies_error PASSED
gates/test_gh_delta.py::test_pulls_resource_hits_issues_endpoint_no_since_symmetry_bug PASSED
gates/test_gh_delta.py::test_page_overflow_beyond_max_pages_classifies_full_rescan PASSED
gates/test_gh_delta.py::test_delta_returns_items_since_cursor_and_persists_advanced_cursor PASSED
gates/test_gh_delta.py::test_periodic_reconciliation_forces_full_rescan_even_without_corruption PASSED
gates/test_gh_delta.py::test_missing_since_key_in_cursor_file_classifies_full_rescan PASSED
gates/test_gh_delta.py::test_issues_resource_excludes_pull_requests PASSED

10 passed in 13.32s
```
- rationale: Test-method reuse of the full gate file (rule 4) —
  independently rerun in an isolated worktree twice this session (the
  fence above is the second run), not copied from the PR's own pasted
  transcript.

### R4 — Acceptance empty state: no cursor → no If-None-Match, classification unchanged

- requirement: "empty state: no cursor — no If-None-Match sent,
  classification unchanged."
- spec_ref: issue #2315 Acceptance, line `empty state`
- verdict: **Present**
- acceptance: `cd /tmp/pr2321-review && python3 -m pytest gates/test_gh_delta.py -v -k test_issues_resource_excludes_pull_requests` — result:
```
gates/test_gh_delta.py::test_issues_resource_excludes_pull_requests PASSED
1 passed in 33.24s
```
  (no cursor file is written in this test — `_load_cursor` returns
  `None` — and its `fake_run` asserts `"since=" not in " ".join(cmd)`
  and `"If-None-Match" not in " ".join(cmd)`, `gates/test_gh_delta.py:205-208`.)
- acceptance: `python3 -c "..."` calling `gh_delta.fetch_delta` with a
  fresh no-cursor call against both the post-fix worktree and `main`
  directly, this session — result:
```
POST-FIX empty-state classification: full-rescan
PRE-FIX (main) empty-state classification: full-rescan
```
- rationale: Test reuse (rule 4) confirms "no If-None-Match sent"; the
  Analysis-method comparison above against the actual pre-fix baseline
  (not just the same code read twice) confirms "classification
  unchanged" is literally true across the fix.

### R5 — Acceptance provenance: real cache-valid probe → no-change, 1 gh call, 0 detail fetches

- requirement: "a real cache-valid probe showing classification no-change
  with exactly 1 gh call and zero detail fetches" (Acceptance
  `provenance`, obligation 1)
- spec_ref: issue #2315 Acceptance, line `provenance`
- verdict: **Present**
- acceptance: `python3 -c "..."` — a counting wrapper around
  `subprocess.run`, calling `gh_delta.fetch_delta` against the real
  `tokenmaxxxer/on-the-record` repo with a primed etag, this session —
  result:
```
classification: no-change gh call count: 1 items returned: []
gh api repos/tokenmaxxxer/on-the-record/issues --method GET -f state=all -f sort=updated -f direction=asc -f per_page=100 -f page=1 -i -f since=2026-08-25T04:11:27Z -H If-None-Match: W/"1a3b52494022e35275512d74695e299097ff13f8e8ee3262682086b05a731cc3"
```
- rationale: Demonstration/Test against the real repo and real `gh`
  binary, executed independently this session (see "What did not work"
  for the first attempt that did not reproduce a genuine cache-valid
  tick).

### R6 — Acceptance provenance: real error still classified error

- requirement: "a real error (bad token or 5xx sim) still classified
  error" (Acceptance `provenance`, obligation 2)
- spec_ref: issue #2315 Acceptance, line `provenance`
- verdict: **Present**
- acceptance: `GH_TOKEN=invalid_bad_token_xyz python3 -c "..."` (same
  probe as R2, real `gh`, real repo, real 401), this session — result:
```
classification (bad token): error items: None cursor: None
```
  The PR's own record instead used a nonexistent-repo-slug 404; both are
  real, independently-genuine failure modes confirming the same clause.
- rationale: Demonstration against real `gh`, run independently this
  session rather than accepted from the builder's own probe.

### R7 — Acceptance provenance: before/after heartbeat lines pasted

- requirement: "before/after heartbeat lines pasted" (Acceptance
  `provenance`, obligation 3)
- spec_ref: issue #2315 Acceptance, line `provenance`
- verdict: **Present**
- canonical: `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:docs/issue-2315/reports/implementation.md:188-197`
  pastes literal before/after `watchdog.py` print lines.
- canonical: `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:watchdog.py:953-961`
  (read this session), the actual source the paste above is checked
  against:
```
953: if delta_classification == "error":
954:     print("[watchdog] board-sweep: gh_delta 프로브 실패 (error 분류) — "
955:           "보수적으로 오늘의 전체 로직으로 폴백")
956: elif delta_classification == "no-change":
957:     closure_sweep.record_sweep_result(backoff_state, "board-sweep", False)
958:     closure_sweep.save_backoff_state(root, backoff_state)
959:     print("[watchdog] board-sweep: no-change (delta empty) — "
960:           "상세 조회/전체 재훑기 건너뜀")
961:     _run_local_only_signals(skip_requirement_drift=True)
```
  the record's pasted before/after strings match these print lines
  exactly, not paraphrased.
- rationale: Inspection — a textual presence-and-accuracy check,
  confirmed by diffing the record's paste against the real source
  line-for-line myself (the two fences above) rather than trusting it
  was copied correctly.

### R8 — Operator-frozen constraint: fix reduces load by construction, measured in the record

- requirement: "systemic for every consumer session; the fix REDUCES
  load by construction — state that measured in the record."
- spec_ref: issue #2315 body, "Operator-frozen constraint (2026-08-25)"
- verdict: **Present**
- canonical: `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:watchdog.py:956-968`
  (read this session) — the `no-change` branch performs backoff
  bookkeeping, prints the no-change line, then calls
  `_run_local_only_signals(skip_requirement_drift=True)` and returns
  early — skipping both the detail-fetch path and the full board-sweep
  logic (closure-sweep + requirement-drift) that the `error`/
  `full-rescan` branches (`watchdog.py:953-955`, `963-968`) still run.
- canonical: `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:docs/issue-2315/reports/implementation.md:199-208`
  states this same reduction in the record, matching what is
  independently read in `watchdog.py` above.
- rationale: Analysis, not Demonstration (verification-method-selection
  rule 2) — live production call-volume-under-load isn't reproducible in
  a review session, so the correct check is tracing the code path: the
  classification value structurally gates less work, not merely that the
  classification changed. "Measured" here is the record naming exactly
  which calls are skipped and why, consistent with the constraint's own
  "by construction" (structural, not runtime-metered) wording.

## Why

Builder-blind means every claim above was re-derived or re-executed this
session rather than taken from the builder's own account of itself
(pinned at
`2d3c38a42625cb2c3afcf6baf84690ba8d56847e:docs/issue-2315/reports/implementation.md`).
conformance-review-verification-method-selection routed R2/R3 to Test
(existing coverage reused per its rule 4, rerun rather than re-derived),
R1/R4(cursor-shape)/R7 to Inspection (structural code-order and
textual-accuracy questions per its rule 1), R4(classification-comparison)/
R5/R6 to Analysis/Demonstration against the real repo and real `gh`
(conditions a static unit test alone cannot establish), and R8 to
Analysis (production load reduction is a code-path tracing question, not
one this session can reproduce under real load).
conformance-review-sampling-derivation was judged not-applicable and
skipped: the diff is 4 files, 296 insertions / 2 deletions — derived:
`git diff --stat main...HEAD` (fenced in full under "What was done") —
small enough that every requirement-bearing hunk was read in full.

## What did not work

- derived: first live cache-valid-probe attempt for R5 (this session,
  `python3 -c "..."` calling `gh_delta.fetch_delta` twice back-to-back
  against the real repo) did not hold — a cursor was primed, then
  immediately re-probed with its etag, expecting a 304; the second call
  instead classified `delta` with one real item, because this repository
  is under live, continuous write traffic from other concurrent
  sessions and a genuine content change landed between the two calls a
  few hundred milliseconds apart. Retried with a fresh prime/re-probe
  pair; that second attempt reproduced a genuine `no-change` (the fence
  pasted under R5), so the requirement is still independently confirmed
  Present — this is a note for the next reviewer attempting the same
  live probe on this repo, not a defect in the PR.

## Upstream basis

- PR #2321, `tokenmaxxxer/on-the-record`, head commit
  `2d3c38a42625cb2c3afcf6baf84690ba8d56847e` (branch
  `issue-2315/implementation`) — sha for every `gates/gh_delta.py`,
  `gates/test_gh_delta.py`, and `watchdog.py` citation above; fetched
  this session via `git fetch origin issue-2315/implementation` and
  `git worktree add /tmp/pr2321-review origin/issue-2315/implementation`.
- `2d3c38a42625cb2c3afcf6baf84690ba8d56847e:docs/issue-2315/reports/implementation.md`
  — the builder's own record, read only to locate what to independently
  re-check; not present on this `conformance-review` branch (PR-only,
  unmerged), hence the sha-pinned citation throughout this record.
- issue #2315 itself (Ask, Acceptance, operator-frozen constraint) —
  `gh issue view 2315`, this session.
- `main:gates/gh_delta.py:176-181` (this branch's own base, no fix) —
  read this session, used as the pre-fix baseline for R1 and R4's
  comparison.

## Open findings

None — all eight Ask/Acceptance/operator-constraint-derived requirements
(R1–R8) independently re-verified as Present against PR #2321's head
commit; no gap surfaced beyond the frozen scope. resolution path: none
(no open findings to resolve).

## Next steps

`loop_state` is `reported` (terminal for a review-record per the session
protocol's kind table) — nothing pending from this record itself.

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; split the Ask's two sentences into R1/R2 and Acceptance's
`provenance` line into R5/R6/R7 (rule 1), kept the separately-frozen
operator constraint as its own item R8, and excluded the
`infrastructure/no-direct-requirement` tag from the checkable list as an
issue-classification tag with no observable success condition (rule 2).
skill-verdict: conformance-review-verification-method-selection —
applied: invoked; routed R2/R3 to Test (existing coverage reused per rule
4), R1/R4(shape)/R7 to Inspection (rule 1), R4(comparison)/R5/R6 to
Analysis/Demonstration against the real repo, R8 to Analysis (rule 2 —
production load isn't reproducible under review-session conditions).
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
all eight requirements independently re-verified and assigned Present;
no Incorrect/Absent/Unverifiable verdict was needed, so no
`spec_vs_built` field or missing-evidence naming was required.
skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every evidence citation above is pinned to file:line plus the
PR's head sha `2d3c38a42625cb2c3afcf6baf84690ba8d56847e` (or `main`'s for
the pre-fix baseline), re-executed this session rather than paraphrased
from the builder's record.
skill-verdict: conformance-review-finding-record — applied: invoked;
this file, one block per requirement with requirement/spec_ref/verdict/
evidence/rationale; no `spec_vs_built` field needed since no requirement
verdicted `Incorrect`.
other mounted skills: conformance-review-sampling-derivation (full
enumeration was feasible — 4-file, 296-line diff — not-applicable),
conformance-review-severity-classification (scope was not extended into
risk-weighting a recorded finding — there are no findings to weight —
not-applicable), implementation-audit (cross-family keyword match only —
this role's own conformance-review skill family already governs this
exact task more specifically — not-applicable) — not triggered.

warrant-hunter before-landing dispatch: skipped. This session's own diff
is a single new file under `docs/issue-2315/reports/`, which the
warrant-protocol directive's DOCS-ONLY FAST PATH explicitly skips at
before-landing; separately, `CORE_BUILD_NOW=1` bypassed the proposal
round entirely (contract v3 s19a), so there is no proposal file/slug to
key a `hunt-<proposal-slug>.md` record path off of. Reason recorded here
per the directive's own "a skip is never silent" requirement, since no
proposal exists for this build-now delivery to attach a separate
hunt-record file to.
