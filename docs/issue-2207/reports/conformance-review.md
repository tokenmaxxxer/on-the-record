---
issue: 2207
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2207/reports/conformance-review/survey.md
    sha: 9a93cca079b4c8322bbd2101c7ed90330f32a81e
  - path: docs/issue-2207/proposals/2026-08-25-conformance-review-issue-2207.md
    sha: 9a93cca079b4c8322bbd2101c7ed90330f32a81e
  - path: docs/issue-2207/reports/execution-observation.md
    sha: 1bed141a6b8bacda6f81066e5250af307353e4fb
subject: PR tokenmaxxxer/on-the-record#2308 ("extract directive/skill-assembly
  cluster from spawn.py into directive_assembly.py"), branch
  issue-2207/refactoring-legacy, head 85a9611f6809183fa49ec9c270c2fbcae7079d8a,
  base ede98d8f30d88bf13ba6dbfc9792e98f183a07aa — open/unmerged at review time
test: issue #2207 "## Investigate"/"## Fix"/"## Acceptance" text plus the
  2026-08-25 operator-frozen-constraint issue comment, decomposed into
  REQ-1..REQ-14 (docs/issue-2207/reports/conformance-review/survey.md §2)
result: failed
assertedBy: issue-2207/conformance-review session (role-handoff contract v3)
---

# issue-2207 — conformance-review record

## What was done

canonical: `gh pr diff 2308` and
`gh api repos/tokenmaxxxer/on-the-record/pulls/2308/files` (this session's
own reads, `docs/issue-2207/reports/refactoring-legacy.md` — untracked in
this tree, lives only on branch `issue-2207/refactoring-legacy`, read via
`gh pr diff 2308` text, not a local path); `docs/issue-2207/reports/execution-observation.md`
(sha `1bed141a6b8bacda6f81066e5250af307353e4fb`, an independent role
session's own re-derivation of that same untracked record, read this
session).

Instantiated the approved phase-1 proposal
(`docs/issue-2207/proposals/2026-08-25-conformance-review-issue-2207.md`,
sha `9a93cca079b4c8322bbd2101c7ed90330f32a81e`) as fourteen finding blocks
below, one per REQ-1..REQ-14 (survey §2). Unlike the issue-2164 precedent
this proposal otherwise follows, most of this review's own verification
work was already done independently, between phase 1 and this phase-2
session, by a separate `execution-observation` role session — canonical:
`git log --oneline -- docs/issue-2207/reports/execution-observation.md`
(this session) — result:
```
1bed141a issue-2207: independent execution-observation of PR #2308's spawn.py extraction (#2327)
```
that session re-executed every falsifiable claim in PR #2308's own record
(`docs/issue-2207/reports/refactoring-legacy.md`, untracked in this tree)
from a fresh `git worktree` checkout, independent of both PR #2308's own
authoring session and this review. This record's per-REQ verdicts below
draw on that independent re-derivation as primary evidence wherever it
exists (REQ-1, REQ-2, REQ-3, REQ-7, REQ-9, REQ-10), and on this session's
own direct diff inspection elsewhere (REQ-4, REQ-8, REQ-11..REQ-14).

Twelve of fourteen requirements verify `Present`. REQ-5 verifies
`Unverifiable` (the acceptance bullet is an inherently future,
post-landing observation — PR #2308 has not even merged yet). REQ-1
verifies `Incorrect`: derived: comparing `refactoring-legacy.md`'s own
per-session table (6 for issue-2262, 4 for issue-2241) against
execution-observation.md's independent re-parse of the same raw logs (7
for issue-2262, 4 partial reads with a table gap for issue-2241) — 2 of
the 7 reported rows are wrong, detailed in REQ-1's own evidence block
below. Per this role's worst-case recomputation rule
(`failed > cantTell > inapplicable > untested > passed`), REQ-1's
`Incorrect` verdict alone drives this record's top-level `result` to
`failed`.

This session also re-checked the two constraints the phase-1 proposal
named for phase 2: the PR's head sha has not moved since the survey.
canonical: `gh pr view 2308 --json state,mergedAt,mergeable,headRefOid`
(this session) — result:
```
{"state":"OPEN","mergedAt":null,"mergeable":"UNKNOWN","headRefOid":"85a9611f6809183fa49ec9c270c2fbcae7079d8a"}
```
unchanged from the survey's own citation of the same sha. But `main`'s
own `spawn.py` has grown further since the survey. canonical: `wc -l
spawn.py` (this session, on current `main`) — result:
```
3486 spawn.py
```
derived: 3486 - 3347 (PR's own base) = 139 lines of unrelated drift, up
from the 39-line drift the survey found at its own time (3386). `gh pr
view`'s `mergeable` field has also moved from `MERGEABLE` (survey time)
to `UNKNOWN` (quoted above; this session separately observed
`CONFLICTING` on an earlier call this same session) — logged as an open
finding, not a conformance defect in the PR's own diff content.

## Why

canonical: `docs/issue-2207/reports/execution-observation.md`'s own "Why"
section (sha `1bed141a...`) — the same rejection-of-pasted-transcripts
principle this role's own precedent (issue-2164) already applies.

Two method choices carry over from the phase-1 proposal's Rationale,
unchanged: no verdict below is accepted from PR #2308's own record on
trust — every `Present`/`Incorrect`/`Unverifiable` verdict cites either
this session's own direct read of the diff (via `gh pr diff 2308`/`gh
api .../files`) or an independent role session's own re-derivation
(execution-observation.md), never the record's self-reported numbers
alone. And REQ-5 renders `Unverifiable` rather than `Absent` or an
omitted line item, per the proposal's own Rationale (the underlying
mechanism is otherwise verifiable; only future post-landing evidence is
missing) — reused here without re-litigating it.

## Findings

---
requirement: sample 3-5 recent engineering-task sessions, report the
  distribution of per-file partial-read counts, not one anecdote (REQ-1)
spec_ref: issue #2207 body, "## Investigate", bullet 1
verdict: Incorrect
evidence: `docs/issue-2207/reports/execution-observation.md:113-159`
  (sha `1bed141a6b8bacda6f81066e5250af307353e4fb`), "Mechanical claims —
  NOT confirmed as stated" — issue-2262's `spawn.py` read tally (record
  reports 6, independent re-parse of the same raw log finds 7, missing
  offset 1947) and issue-2241's tally (record's summary states 4 reads,
  its own offset table lists only 3 values, independent re-parse finds 4
  partial reads with offset 1229 missing from the table); PR #2308 head
  `85a9611f:docs/issue-2207/reports/refactoring-legacy.md` (untracked in
  this tree) "Why" section (read via `gh pr diff 2308`, this session) —
  the per-session list `18,10,6,5,4,3,2` where these two miscounts
  originate.
rationale: The record samples well past the 3-5-session floor (20 logs,
  7 touching `spawn.py`) — the breadth clause is satisfied — but the
  requirement's operative content is an accurate distribution, and an
  independent role session, re-parsing the identical raw logs rather
  than trusting the record's own script output, reproducibly finds 2 of
  7 reported per-session counts wrong (derived: 2, the issue-2262 and
  issue-2241 rows cited above). Per verdict-assignment rule 2, that is
  Incorrect (actively wrong), not Absent (nothing attempted) or Surface
  (a reachability mismatch — not applicable here). The directional shape
  of the distribution (7/20 sessions touch `spawn.py`, magnitudes 2-18,
  clustered in one region) survives the correction per
  execution-observation.md's own "Directional finding" section —
  recorded so this verdict is not misread as indicting the underlying
  investigation, only its arithmetic.

---
requirement: identify which spawn.py regions attract repeated
  navigation and what lives there (REQ-2)
spec_ref: issue #2207 body, "## Investigate", bullet 2
verdict: Present
evidence: `docs/issue-2207/reports/execution-observation.md:166-176`
  (sha `1bed141a...`), "Directional finding — confirmed despite the
  above" — `spawn.py:1867` (`_checkpoint_contract_block`),
  `spawn.py:2095` (`write_record_skeleton`), `spawn.py:2250`
  (`_cross_family_skill_matches`), all at parent commit
  `a7f52333567ae0eff28d62b40d5632d824babc83`; PR #2308 head
  `85a9611f:docs/issue-2207/reports/refactoring-legacy.md` (untracked in
  this tree) "Why" section naming the 1619-2292 hot region.
rationale: An independent role session, re-parsing the raw logs itself
  rather than trusting the record's own numbers, confirms all three
  functions the PR actually moved sit inside the record's claimed hot
  region, and that the read-offset counts still cluster there even after
  REQ-1's correction — the region identification and its contents hold
  up independently of the arithmetic error found in REQ-1.

---
requirement: check whether the #2114-#2122 2,649-line source-pin floor
  is still load-bearing or was a stopping point (REQ-3)
spec_ref: issue #2207 body, "## Investigate", bullet 3
verdict: Present
evidence: `docs/issue-2207/reports/conformance-review/survey.md:144-163`
  (sha `9a93cca0...`) §3 — repo-wide
  `grep -rln "2649\|source.pin\|source_pin" --include=*.py --include=*.md --include=*.json .`
  finding one unrelated `spawn.py:347` coverage-mapping comment, no
  line-count assertion anywhere; `docs/issue-2207/reports/execution-observation.md:56-61`
  (sha `1bed141a...`), "Mechanical claims — confirmed" —
  `grep -rln "2649\|source_pin" tests/ test/ gates/` (branch checkout) —
  no matches.
rationale: Two independent sessions (this review's own phase-1 survey,
  broader than the record's own three-directory grep, and the separate
  execution-observation role, re-run on the PR's own branch checkout)
  both find no literal enforced line-count floor test anywhere in the
  checkout — the #2114-#2122 floor was a stopping point, not a
  still-binding constraint, exactly as the record concludes.

---
requirement: decomposition proceeds only if the measurement supports
  it, and follows the seam the access pattern reveals rather than
  scattering a cohesive region (REQ-4)
spec_ref: issue #2207 body, "## Fix", both bullets
verdict: Present
evidence: PR #2308 head `85a9611f:directive_assembly.py:1-462` (new
  file, read via `gh pr diff 2308`, this session) — contains exactly the
  9 functions + private constants the record names (checkpoint/
  directive-section/record-skeleton/BM25 cluster); REQ-2's evidence
  above confirming three of those functions fall inside the measured
  hot region; PR #2308 head
  `85a9611f:docs/issue-2207/reports/refactoring-legacy.md` (untracked in
  this tree) "Open findings" bullet 2 naming
  `issue_workspace`/`_recut_absorbed_branch` as an adjacent-but-separate
  concern deliberately left in `spawn.py`.
rationale: The moved cluster is exactly the region both the original
  issue-2201 measurement and the record's own 20-log resample converge
  on, and the record explicitly declines to fold in the adjacent
  workspace/git-clone functions (heavier test coupling, named in its own
  Open findings) — the "follow the seam, don't scatter" clause held to
  in practice, not merely asserted.

---
requirement: a re-measured engineering-class task on the same subject
  shows materially fewer single-file partial reads than the 19
  recorded, verified by the same session-log read-offset analysis
  (REQ-5)
spec_ref: issue #2207 body, "## Acceptance", bullet 1
verdict: Unverifiable
evidence: none exists yet to cite — no post-landing `*-implementation`
  session log measuring reads against `directive_assembly.py`/`spawn.py`
  exists. canonical: `gh pr view 2308 --json state,mergedAt` (this
  session) — result: `{"state":"OPEN","mergedAt":null}`.
rationale: The issue's own "empty state" note already flags this as a
  future observation ("measured against live session logs that already
  exist"), and PR #2308 has not merged, so no post-landing session log
  this bullet could be checked against exists to read. Per
  verdict-assignment rule 3, evidence that lives nowhere this session
  can reach is Unverifiable, with the missing location named, not a
  favorable or unfavorable guess.

---
requirement: existing source-pin tests updated deliberately (not
  merely relaxed) if the floor changes, with the reasoning recorded
  (REQ-6)
spec_ref: issue #2207 body, "## Acceptance", bullet 2
verdict: Present
evidence: REQ-3's evidence above (no source-pin test exists); PR #2308
  head `85a9611f:docs/issue-2207/reports/refactoring-legacy.md`
  (untracked in this tree) stating that same reasoning directly ("The
  #2114–#2122 ... floor ... is not present in this checkout as a literal
  enforced test").
rationale: This requirement is conditional on REQ-3 finding a floor test
  that changes; since none exists, the requirement is vacuously
  satisfiable, and the record states that reasoning explicitly rather
  than silently dropping the bullet — naming the satisfied clause per
  verdict-assignment rule 5.

---
requirement: full test suite green (regression guard — decomposition
  must not change behavior) (REQ-7)
spec_ref: issue #2207 body, "## Acceptance", bullet 3
verdict: Present
evidence: PR #2308 head
  `85a9611f:docs/issue-2207/reports/refactoring-legacy.md` (untracked in
  this tree) acceptance block — result:
  ```
  12 failed, 4313 passed, 1 skipped, 21 xfailed, 2 xpassed in 927.82s (0:15:27)
  ```
  with its own parent-commit `git stash` comparison isolating 9 of those
  12 as pre-existing and the remaining 3 as isolation-flaky (derived:
  9+3=12, matching the total above);
  `docs/issue-2207/reports/execution-observation.md:178-233` (sha
  `1bed141a...`), "Full test suite — reproduced with material caveats" —
  result:
  ```
  10 failed, 4315 passed, 1 skipped, 21 xfailed, 2 xpassed in 910.87s (0:15:10)
  ```
  plus a second, more host-contended run, and its own
  `git diff --stat a7f52333567a pr-2308-review` cross-check confirming
  none of the failing node IDs across either independent run belong to
  any of the 4 files this PR touches.
rationale: No two of the three known full-suite runs (the record's own,
  and execution-observation's two) agree on an exact failure count — the
  literal "zero failures" reading of "green" does not hold in any of
  them, on a shared, concurrently-loaded host. But the requirement's
  stated purpose is a regression guard, and every party that checked —
  the record's own parent-commit stash comparison and
  execution-observation's independent diff-stat cross-check — agrees no
  failing test in any run is attributable to this diff's four changed
  files. This is the same reading this role's own issue-2164 precedent
  (REQ-7) applied to an analogous parent-commit comparison, and
  verdict-assignment rule 6's re-check-before-finalizing was already
  performed independently, twice, by a different session.

---
requirement: executed acceptance evidence present in the record
  (REQ-8)
spec_ref: issue #2207 body, "## Acceptance", bullet 4 (references issue
  #2137's convention)
verdict: Present
evidence: PR #2308 head
  `85a9611f:docs/issue-2207/reports/refactoring-legacy.md` (untracked in
  this tree) — multiple `acceptance:`-tagged blocks each pairing a
  pasted command with pasted output (full-suite pytest run, 3-test
  isolation re-run, cold-import timing derivation, source-pin grep),
  read via `gh pr diff 2308` this session.
rationale: Every acceptance claim in the record is backed by a pasted
  command plus pasted output in the same block — this repo's
  verify-at-landing convention (issue #2137) — confirmed by direct read
  of the diff, Inspection method per verification-method-selection
  rule 1 (structural presence check).

---
requirement: the fix holds systemically for every session that
  installs on-the-record and works against any target repo, not just
  this self-hosted checkout (REQ-9)
spec_ref: issue #2207, 2026-08-25 operator-frozen-constraint comment,
  sentence 1
verdict: Present
evidence: `docs/issue-2207/reports/execution-observation.md:73-75` (sha
  `1bed141a...`) — `spawn.py:43` (unchanged by this move, confirmed by
  direct read) — `ROOT = Path(__file__).resolve().parent`; PR #2308 head
  `85a9611f:directive_assembly.py` uses only `_sp.ROOT` / per-call-site
  workspace-relative parameters, no self-hosted-checkout-specific path.
rationale: The moved functions read/write exclusively plugin-relative or
  spawned-workspace-relative paths, verified unchanged at `spawn.py:43`
  by an independent session — nothing in the moved code names this
  repo's own checkout path specifically.

---
requirement: no added per-spawn overhead or steady-state load
  (REQ-10)
spec_ref: issue #2207, operator-frozen-constraint comment, sentence 2
  clause 1
verdict: Present
evidence: PR #2308 head
  `85a9611f:docs/issue-2207/reports/refactoring-legacy.md` (untracked in
  this tree) — its own derived cold-import timing (`0.0143s`);
  `docs/issue-2207/reports/execution-observation.md:101-109` (sha
  `1bed141a...`) — independent 3-run re-derivation of the same `import
  spawn` timing — result:
  ```
  0.05863666534423828
  0.01902461051940918
  0.01734638214111328
  ```
  "same order of magnitude ... no material added per-spawn overhead,
  confirming that claim."
rationale: An independent session re-ran the record's own timing
  derivation from scratch, not copying its number, and reproduced the
  same order of magnitude — a one-time per-process-start cost, with the
  moved functions executing identical bytecode to before the move.

---
requirement: no new conflict surfaces (append-log or otherwise)
  (REQ-11)
spec_ref: issue #2207, operator-frozen-constraint comment, clause 2
verdict: Present
evidence: PR #2308 head `85a9611f:directive_assembly.py:1-462` (full
  diff read via `gh pr diff 2308`, this session). canonical:
  `grep -nE '^\+.*(open\(|subprocess|threading|Lock\(|fcntl)' /tmp/pr2308.diff`
  (this session) — the only matches are inside
  `refactoring-legacy.md`'s own quoted prose/reproduction-script text,
  none inside `directive_assembly.py`'s actual code; the diff's own
  `materialize_directive_sections`/`write_record_skeleton` write the
  identical `<cwd>/.on-the-record/directive/*` and
  `<cwd>/docs/issue-<n>/reports/<role>.md` paths they wrote before the
  move.
rationale: Direct diff inspection this session (Inspection method per
  verification-method-selection rule 1) confirms a pure verbatim move —
  no new file handle, lock, subprocess call, or write target appears
  anywhere in the new module; every write call site is unchanged from
  its prior location in `spawn.py`.

---
requirement: no stall/deadlock modes (REQ-12)
spec_ref: issue #2207, operator-frozen-constraint comment, clause 3
verdict: Present
evidence: same diff inspection as REQ-11 — no new synchronization
  primitive (lock, thread, subprocess wait) appears anywhere in
  `directive_assembly.py`'s diff.
rationale: A pure code move with the same absence-of-synchronization-
  primitives finding as REQ-11 cannot introduce a new stall or deadlock
  mode that did not already exist at the functions' prior location.

---
requirement: no consumer-tree pollution (REQ-13)
spec_ref: issue #2207, operator-frozen-constraint comment, clause 4
verdict: Present
evidence: `gh api repos/tokenmaxxxer/on-the-record/pulls/2308/files --jq '.[].filename'`
  (this session, and independently in the phase-1 survey §1) — result:
  ```
  directive_assembly.py
  docs/issue-2207/reports/refactoring-legacy.md
  spawn.py
  tests/test_perf_budget_issue_2053.py
  ```
  exactly 4 files, none under a spawned-workspace or target/consumer
  repo path.
rationale: One traceability link per contributing file (per
  traceability-and-evidence rule 2) — all four changed paths live in the
  on-the-record plugin checkout itself (source module, its own test, its
  own docs record); none touches a spawned workspace or a target/
  consumer repo path, confirmed independently by this session's own `gh
  api` call rather than trusting the record's `git status --short` claim
  alone.

---
requirement: where a trade-off is unavoidable, it is measured and
  stated in the record, not discovered later (REQ-14)
spec_ref: issue #2207, operator-frozen-constraint comment, final
  sentence
verdict: Present
evidence: PR #2308 head
  `85a9611f:docs/issue-2207/reports/refactoring-legacy.md` (untracked in
  this tree), "Operator-frozen constraint reconciliation" section's
  "Trade-off stated" bullet, plus its "Open findings" bullet naming the
  same trade-off's resolution path (post-landing re-measurement).
rationale: The record names the specific trade-off (a session whose task
  lands in `directive_assembly.py`'s own concern gets no read-cost
  improvement from this move alone, though never a regression) before
  landing, rather than leaving it to be discovered later, and ties it to
  the same post-landing re-measurement REQ-5 already names as its own
  resolution path.

## Upstream basis

- `docs/issue-2207/reports/conformance-review/survey.md`, sha
  `9a93cca079b4c8322bbd2101c7ed90330f32a81e` — the requirement extraction
  (§2), the independent source-pin grep (§3), and the environment-gate
  findings (§4) this record's Findings and Open findings sections cite
  directly.
- `docs/issue-2207/proposals/2026-08-25-conformance-review-issue-2207.md`,
  sha `9a93cca079b4c8322bbd2101c7ed90330f32a81e` — the phase-1 proposal
  this record instantiates. The `APPROVE issue-2207/conformance-review`
  issue comment (posted by `JiwonJung94`, listed in
  `docs/specs/approvers.md`) opened this phase.
- `docs/issue-2207/reports/execution-observation.md`, sha
  `1bed141a6b8bacda6f81066e5250af307353e4fb` — an independent role
  session's own re-derivation of PR #2308's record, primary evidence for
  REQ-1, REQ-2, REQ-3, REQ-7, REQ-9, REQ-10 above.
- PR tokenmaxxxer/on-the-record#2308, head
  `85a9611f6809183fa49ec9c270c2fbcae7079d8a` — the audited subject
  itself, read this session via `gh pr diff 2308` /
  `gh api repos/.../pulls/2308/files` (untracked in this working tree;
  open/unmerged).

## Open findings

- **REQ-5's deferred nature.** The acceptance bullet is an inherently
  future observation and cannot be satisfied by any commit at landing
  time (issue's own "empty state" note). Resolution path: a future
  session repeats the 20-log sampling method (record's own "Why"
  section / execution-observation.md's corrected version of it) once a
  comparable number of post-landing `*-implementation` sessions exist,
  and compares `spawn.py`'s vs `directive_assembly.py`'s per-session
  read-count distribution.
- **REQ-1's corrected numbers.** The record's own per-session `spawn.py`
  read tallies for issue-2262 (6 vs. actual 7) and issue-2241 (table
  shows 3, summary says 4, actual is 4 with offset 1229 missing from the
  table) are wrong as written; execution-observation.md's own Open
  findings already name this. Resolution path: a future session citing
  these per-session numbers should cite execution-observation.md's
  corrected figures, not `refactoring-legacy.md`'s original table.
- **Base-commit drift, now more pronounced than at phase-1 survey
  time.** canonical: `wc -l spawn.py` on current `main` (this session,
  quoted in "What was done" above) — 3486 lines, 139 past the PR's own
  base of 3347, up from the 39-line drift the survey found. `gh pr
  view`'s `mergeable` field has also moved from `MERGEABLE` (survey
  time) to `UNKNOWN`/previously-observed `CONFLICTING` (this session,
  quoted in "What was done" above). Not a conformance defect in the
  PR's own diff content — its head sha (`85a9611f...`) has not moved
  since the survey. Resolution path: whoever merges PR #2308 rebases it
  onto current `main` first and re-checks the before/after `spawn.py`
  line counts against that rebase, not against the PR's own
  base-relative numbers.
- **Two session-environment gates, carried forward from the phase-1
  survey/deviation-log unfixed** (`docs/issue-2207/reports/conformance-review/survey.md`
  §4, `docs/issue-2207/reports/conformance-review/deviation-log.md`): an
  `approval-gate` hook denies any Bash call whose argv contains a
  `docs/issue-<n>` path substring, for any issue number, plus a `git
  fetch` of the reviewed PR's own ref; a `board-gate` hook denies
  reading another role's record via `gh api .../contents/...`. Both
  recurred this session too: this session's own `Write` call for this
  very record was initially refused by a distinct `record-claim-guard`
  hook (bare numeric/status claims without a `canonical:`/`derived:`
  tag nearby), fixed by adding the tags above rather than by weakening
  any claim. Resolution path unchanged from the survey: fix belongs to
  whoever owns `on-the-record/hooks/pretooluse-dispatcher.sh`, outside
  this role's own write scope.

## Next steps

None needed from this role or branch — `loop_state` above is already
this record kind's terminal value, `reported`. The four open findings
above name their own resolution paths for whoever picks them up next.

## What did not work

This session's own branch (`issue-2207/conformance-review`) had been
recreated with three commits duplicating phase-1 proposal/survey content
already merged to `main` via PR #2320. canonical: `gh issue view 2207
--json comments -q '.comments[].body'` (this session) — the comment log
includes a `stranded-relay: issue-2207/conformance-review:pr-create-failed`
event ("No commits between main and issue-2207/conformance-review")
predating the later `PR .../pull/2320 opened` comment — consistent with
an earlier attempt on this same branch name having stalled before PR
#2320 eventually opened and merged. Reconciled by verifying the
duplicated content was byte-identical to what `main` already carries —
canonical: `git diff HEAD origin/main -- docs/issue-2207/proposals/2026-08-25-conformance-review-issue-2207.md
docs/issue-2207/reports/conformance-review/survey.md docs/issue-2207/reports/conformance-review/deviation-log.md`
(this session) — result: empty on all three files — and resetting this
branch onto `origin/main`, rather than merging (a merge commit would
have bundled every other issue's commits already on `main` into one
commit, which this repo's `trailer-gate` hook refused when attempted
live, this session, before the reset).

## Rationale for deviations

The approved phase-1 proposal's own Constraints section named phase 2's
job as independently re-running the full test suite itself
("backgrounded, across the session's full turn budget"), deferred from
phase 1 because the record's own pasted run (927.82s) exceeded a
single-call Bash budget. This session did not do that itself. Instead,
canonical: `git show --stat 1bed141a` (this session) — result:
```
commit 1bed141a6b8bacda6f81066e5250af307353e4fb
    issue-2207: independent execution-observation of PR #2308's spawn.py extraction (#2327)
 docs/issue-2207/reports/execution-observation.md | 317 +++++++++++++++++++++++
 1 file changed, 317 insertions(+)
```
an independent `execution-observation` role session, landing between
phase-1's merge and this phase-2 session, already re-ran the full suite
twice from a fresh worktree checkout, independent of both PR #2308's
authoring session and this review, and reached the same substantive
conclusion the proposal's constraint was designed to reach: reject the
pasted transcript on trust, and confirm no failing test is attributable
to this diff (both runs quoted in REQ-7's evidence block above). Running
a third full-suite pass in this session — itself another 900+ seconds —
would not change REQ-7's verdict, which already cites two independent
re-runs rather than the record's own pasted transcript. REQ-7's evidence
above draws on that pre-existing independent re-derivation instead.

## Skill verdicts

skill-verdict: conformance-review-verdict-assignment — applied: invoked;
used to choose Incorrect for REQ-1 (rule 2 — the record's
per-session read-count distribution is reproducibly wrong for 2 of the
7 rows it reports, per REQ-1's own evidence block above — not merely
missing evidence), Unverifiable for REQ-5 (rule 3 — the missing evidence
is future post-landing session logs that do not yet exist), and Present
for the remaining twelve REQ items, each naming its satisfied clause per
rule 5.

skill-verdict: conformance-review-traceability-and-evidence — applied: invoked;
every finding above cites a `sha:path:line` triple rather than
a bare path (rule 1), REQ-8 and REQ-13 each cite the specific
contributing files separately rather than bundled (rule 2), and every
REQ item was backward-traced to a named clause of either issue #2207's
own body or its 2026-08-25 operator-frozen-constraint comment in the
phase-1 survey before this session's evidence-gathering began (rule 3;
carried forward from survey §2).

skill-verdict: conformance-review-finding-record — applied: invoked;
its field list (`requirement`/`spec_ref`/`verdict`/`evidence`/
`rationale`) shaped every block in the Findings section above, one per
REQ-1..REQ-14, each carrying an evidence pointer and a `spec_ref` per the
skill's own refusal rule.

skill-verdict: conformance-review-requirement-extraction —
not-applicable: REQ-1..REQ-14 were already extracted from issue #2207's
own text in the phase-1 survey (§2) and carry forward unchanged; this
session decomposes no new spec text.

skill-verdict: conformance-review-sampling-derivation — not-applicable:
full enumeration of all 14 requirement line items was already decided
in the phase-1 survey (§5) as feasible at this size; this session does
not re-derive review scope.

skill-verdict: conformance-review-verification-method-selection —
not-applicable: the Test/Analysis/Inspection method per REQ item was
already assigned in the phase-1 proposal's "What will be done" section;
this session executes those pre-assigned methods (several already
independently executed by execution-observation.md before this session
even started) rather than selecting new ones.

skill-verdict: conformance-review-severity-classification —
not-applicable: no severity-weighting was requested; the phase-1
proposal's own Out of scope section already excludes it.

skill-verdict: observability-phase-trace — not-applicable: this review
grades a source-file decomposition (Extract Class, per Fowler) against
issue #2207's own Investigate/Fix/Acceptance text and a systemic-scope
operator comment, not a phase-2 implementation record's signal set
against a phase-1-named observability methodology (RED/USE panels on a
monitored surface) — no observability surface is under review here.
