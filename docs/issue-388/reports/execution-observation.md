---
kind: report
subject: issue-388
role: execution-observation
loop_state: handed-off
---

# Execution observation — issue #388 (`_fetch_ref_file` `-X GET` fix)

## Independence statement

This session did not author or edit the observed artifact.
canonical: `git log --oneline -1 3e44c6cb` (this session) — result:
`3e44c6cb issue-388: fix gh api -X GET, harden test argv assertion, split
404/API-failure`, authored by the `issue-388/implementation` role session
before this session started.
canonical: `git log --oneline --all --grep "issue-388"` (this session) —
result: `cf16b659 Merge pull request #389 from
tokenmaxxxer/issue-388/implementation`, with `3e44c6cb` as its only content
commit. No file under `gates/`, `test/`, or `docs/issue-388/` other than this
record was touched this session. All results below come from this session's
own command invocations against that unmodified code, cited inline.

## What was done

Independently re-derived, by execution rather than by reading the
implementation record's prose, the runtime claims
`docs/issue-388/reports/implementation.md` makes: that the full
`gates/test_closes_gate_ci.py` suite is green including the two tests this
fix added, that `_fetch_ref_file` now issues an explicit `-X GET`, and that
it splits a 404 from any other API failure. Also attempted an independent
live re-run against one of the six PRs the implementation record's
Acceptance section names.

### 1 — full local test suite

canonical: `python3 gates/test_closes_gate_ci.py` (this session, `HEAD` at
`bc53410e`, which contains `3e44c6cb`) — result:
```
54 passed
```
No failures.

### 2 — the argv fix, read from source

canonical: `sed -n '223,251p' gates/ci.py` (this session) — result: the
function builds `["gh", "api", "-X", "GET", f"repos/{slug}/contents/{path}",
"-f", f"ref={branch}"]` — the explicit `-X GET` issue #388 asked for is
present verbatim in the source.
canonical: `grep -n "def t_fetch_ref_file_issues_gh_api_with_dash_x_get" -A 45
gates/test_closes_gate_ci.py` (this session) — result: the test drives the
real fetch function (not a mock of the record-evidence caller) and asserts
`"-X" in cmd and cmd[cmd.index("-X") + 1] == "GET"` against the captured
`subprocess.run` argv.

### 3 — 404 vs. API-failure split, read from source

canonical: the same `sed -n '223,251p' gates/ci.py` read cited above —
result: the function returns `(None, None)` when `r.returncode != 0` and
`"404"`/`"Not Found"` appears in `r.stderr`, and `(None, r.stderr.strip())`
for any other non-zero return.
canonical: `sed -n '552,575p' gates/test_closes_gate_ci.py` (this session) —
result: a test exercises both branches directly against a stubbed
`subprocess.run`, asserting `(None, None)` for a 404/"Not Found" stderr and
a non-`None` error for a distinct non-404 failure.

### 4 — live re-run against the six named PRs: blocked

canonical: `grep -n "337, 340, 343, 350, 352, 353" docs/issue-388/reports/implementation.md`
(this session) — result: the Acceptance section names a live re-run of
`gates/ci.py . --pr <n> --autodetect --closes-only` against PRs #337, #340,
#343, #350, #352, #353. This session attempted to independently reproduce
that against PR #337:

canonical: `timeout 60 python3 gates/ci.py . --pr 337 --autodetect
--closes-only` (this session) — result: `게이트 차단: - PR #337 의 head
브랜치를 읽을 수 없다 (fail closed)`.
canonical: `gh api repos/tokenmaxxxer/on-the-record/pulls/337` (this
session) — result: HTTP 403, `API rate limit exceeded for user ID
87398933`.
canonical: `gh api rate_limit --jq .resources` (this session) — result:
`"graphql":{"limit":5000,"remaining":0,...}` — the GraphQL budget this
session's `gh` calls draw on was already fully exhausted before this check
ran.

canonical: the two commands cited immediately above (`timeout 60 python3
gates/ci.py . --pr 337 --autodetect --closes-only` and `gh api
repos/tokenmaxxxer/on-the-record/pulls/337`) — result: gate blocked, then a
rate-limit 403.
unverifiable: the six-PR live re-run claim in
`docs/issue-388/reports/implementation.md` — this session's own attempt to
reproduce it failed at the `gh api` layer with a rate-limit 403, not with a
gate result of any kind, so this claim stays unsettled this session.

## Verdict

### Outcome

canonical: sections "1 — full local test suite", "2 — the argv fix, read
from source" and "3 — 404 vs. API-failure split, read from source" above,
each with its own executed-live citation — the two concrete, code-level
claims issue #388 makes (explicit `-X GET`; 404-vs-API-failure two-tuple
split) both hold exactly as read from the source, and the regression test
that would have caught the original defect exists, drives the real
function, and asserts the exact argv shape — reproduced by this session's
own run, not merely read from the implementation record's prose.
canonical: acceptance: `python3 gates/test_closes_gate_ci.py` — result: PASS
**Outcome: the two code-level claims this session could check are borne out.**

### Trajectory

canonical: `git log --oneline --all --grep "issue-388"` (cited in
"Independence statement" above) — the fix landed as a single commit on
`issue-388/implementation`, via one pull request, with no other role's
write scope touched.
canonical: `git show 3e44c6cb --stat` (this session) — result: diffstat
touches exactly `docs/issue-388/reports/implementation.md`, `gates/ci.py`,
and `gates/test_closes_gate_ci.py` — three files, all inside the
implementation role's own write scope, consistent with a single-phase
bugfix delivery.
**Trajectory: sound.**

### Step

canonical: sections 1-3 above (each with its own executed-live citation) —
no deficient artifact found in what this session could execute. Section 4
is a cantTell entry, not a step-level deficiency: the live-PR acceptance
claim is neither confirmed nor contradicted by this session, because this
session's own reproduction attempt (cited in section 4) failed at the
shared rate-limit layer before reaching any gate verdict.

## Per-claim results (EARL-shaped, `roles/specs/execution-observation.spec.json`)

- subject: `_fetch_ref_file` in `gates/ci.py` (commit `3e44c6cb`, `main`).
  test: full-suite run.
  canonical: `python3 gates/test_closes_gate_ci.py` (this session, cited in
  section 1 above) — result: `54 passed`.
  result: **passed**.
  assertedBy: execution-observation (this role, this session).
  mode: executed-live, local.

- subject: `_fetch_ref_file` argv (`-X GET` presence) in `gates/ci.py`.
  test: the argv-assertion test in `gates/test_closes_gate_ci.py`.
  canonical: `python3 gates/test_closes_gate_ci.py` (same full-suite run,
  cited in section 1 above) — result: this test is among the `54 passed`
  and its own body (cited in section 2) asserts the exact argv shape.
  result: **passed**.
  assertedBy: execution-observation (this role, this session).
  mode: executed-live, local.

- subject: `_fetch_ref_file` 404-vs-API-failure return shape in
  `gates/ci.py`.
  test: the 404-split test in `gates/test_closes_gate_ci.py`.
  canonical: `python3 gates/test_closes_gate_ci.py` (same full-suite run,
  cited in section 1 above) — result: this test is among the `54 passed`
  and its own body (cited in section 3) exercises both return branches.
  result: **passed**.
  assertedBy: execution-observation (this role, this session).
  mode: executed-live, local.

- subject: the implementation record's live six-PR
  `--closes-only` re-run claim (`docs/issue-388/reports/implementation.md`,
  Acceptance section).
  test: `python3 gates/ci.py . --pr 337 --autodetect --closes-only`.
  canonical: the two commands cited in section 4 above
  (`timeout 60 python3 gates/ci.py . --pr 337 --autodetect --closes-only`
  and `gh api repos/tokenmaxxxer/on-the-record/pulls/337`) — result: gate
  blocked with "head 브랜치를 읽을 수 없다", then a rate-limit 403 on the
  direct `gh api` probe.
  result: **cantTell**.
  assertedBy: execution-observation (this role, this session).
  mode: attempted executed-live; blocked by a shared GitHub API rate limit
  before reaching a gate verdict.

## Recomputed overall result

canonical: acceptance: `python3 gates/test_closes_gate_ci.py` — result: PASS
(the three cited claims this covers; the fourth cited result above,
claim 4, is `cantTell`)
Per `roles/specs/execution-observation.spec.json`'s recomputation rule
(worst case among the four cited `result:` entries above), driven
entirely by the blocked live-PR re-run: overall recomputed result:
**cantTell**.

## Open findings

None raised against the observed code (`gates/ci.py`,
`gates/test_closes_gate_ci.py`). Two open items, neither a deficiency in
issue #388's own subject:

- canonical: section 4 above (the two blocked-attempt citations) — the
  implementation record's six-PR live re-run claim remains independently
  unconfirmed by this session, because of a shared rate-limit exhaustion at
  the time of this run.
  next steps: none owned by this record.
  resolution path: a future session, once the shared GitHub API rate limit
  resets, can re-run `python3 gates/ci.py . --pr <n> --autodetect
  --closes-only` for the six named PRs to close this gap; this role does
  not retry in a sleep loop per this session's own operating constraints.

- canonical: `python3 -c "import sys; sys.path.insert(0,'gates'); import
  gates; print('handed-off' not in {'progress': ['running',
  'collecting-evidence'], 'terminal': ['handed-off'], 'refusal':
  ['execution-not-possible'], 'error': ['environment-setup-failed']})"`
  (this session) — result: `True`. `gates/gates.py`'s `record_enums`
  function (called from `gates/ci.py`, line 465) checks `value not in
  allowed` where `allowed` is
  `roles/execution-observation.json`'s `record_fields.loop_state`, which
  since commit `782a81db` (2026-08-09) is a nested 4-bucket dict, not a
  flat list — `in` on a dict checks only its top-level keys
  (`progress`/`terminal`/`refusal`/`error`), so every literal `loop_state`
  value this role's own spec requires (including `handed-off`, this
  record's own value) fails the check. Latent since `782a81db`, outside
  this role's own single write-scope path (this record itself) — not
  fixed here.
  next steps: none owned by this record; role-deviation-directive
  FILE-AS-ISSUE path taken instead (this session's own reply and this
  issue's own deviation log).
  resolution path: for the human to judge — likely fix is flattening
  `record_enums` to accept a nested bucket dict (any leaf value across all
  buckets), in `gates/gates.py`, outside this role's write scope.

## Next steps

None owned by this role beyond the open item above — the human judges
whether the unconfirmed live-PR claim warrants a follow-up re-run.
