---
issue: 2432
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
  - path: docs/issue-2432/reports/implementation.md
    sha: 1f1c06773d70deb528b508fe013d98ca39bcf2fc
  - path: docs/issue-2432/reports/implementation/in-flight-branch-migration.md
    sha: 1f1c06773d70deb528b508fe013d98ca39bcf2fc
  - path: docs/issue-2432/reports/implementation/deviation-log/20260825T135027234095-1af27b595645d6f8.md
    sha: 1f1c06773d70deb528b508fe013d98ca39bcf2fc
subject: PR #2436 (issue-2432/implementation, head 1f1c06773d70deb528b508fe013d98ca39bcf2fc, base 8d100d660ddb2ce4ece97de248688564763738d8) — board.py, pipeline.py, roster.py, spawn.py, docs/handbooks/branch-naming.md, docs/issue-2432/reports/implementation*, test/test_branch_naming_dual_scheme.py
test: issue #2432 Acceptance section — 3 check bullets + 2 gate bullets
result: failed
assertedBy: conformance-review session for issue-2432, builder-blind review of PR #2436, 2026-08-25 — CORE_BUILD_NOW=1 build-now bypass, delivered directly
---

# issue-2432 — conformance-review record

## What was done

canonical: `gh issue view 2432`, `gh pr view 2436`, `gh pr diff 2436`
(all run this session) — first reads before any check began.

Builder-blind conformance review of PR #2436
(`https://github.com/tokenmaxxxer/on-the-record/pull/2436`, branch
`issue-2432/implementation`, head `1f1c06773d70deb528b508fe013d98ca39bcf2fc`
— hereafter `1f1c0677`, base `8d100d660ddb2ce4ece97de248688564763738d8`)
against issue #2432's five acceptance items (three `check:` bullets,
two `gate:` bullets). Every artifact this PR touches — the
board-discovery module, the branch-checkout module, the roster module,
the spawn re-export surface, the new branch-naming handbook doc, this
issue's own implementation record and its `implementation/` subtree,
and the new dual-scheme test file — exists only on PR #2436's own
branch (head `1f1c0677`), not on this review branch
(`issue-2432/conformance-review`, based on `main`) — every citation to
one of those paths below is pinned as `1f1c0677:<path>` and was read
this session via `git fetch origin pull/2436/head` + `git worktree add
/tmp/pr2436-wt FETCH_HEAD`, never assumed present on this branch.

Independently re-derived every claim rather than trusting
`1f1c0677:docs/issue-2432/reports/implementation.md`'s own transcripts:
ran the shipped test suite myself from the `/tmp/pr2436-wt` worktree,
ran `spawn.board()` myself against the real (not synthetic) `docs/`
tree of ~400 existing issues to confirm the dual-scheme reader doesn't
crash or drop anything, ran `gh pr list --state open` myself live (not
copied from the PR's own paste), and independently located and read
the actual `board-gate.sh` gate script (outside this repo, in the core
plugin tree) to check the PR's quoted gate-refusal text against the
gate's real rule numbering rather than accepting the citation at face
value.

Skills invoked this session (skill-repository issue #1955/#1758
mapping): conformance-review-requirement-extraction,
conformance-review-verification-method-selection,
conformance-review-verdict-assignment,
conformance-review-traceability-and-evidence,
conformance-review-finding-record. See "## Skill verdicts" at the
bottom.

## Why

Chose independent re-derivation (fresh worktree, fresh test run, fresh
`gh pr list`, and reading the actual gate script rather than the PR's
paraphrase of it) over trusting the implementation record's own
transcripts and citations because the role is explicitly builder-blind,
and because this stage's own deliverable is unusually self-referential
— it modifies the exact discovery mechanism (`board.py`) this review's
own evidence-gathering depends on, so verifying "does the dual-scheme
reader actually work" from a description alone would not catch a
reader that looks correct on paper but breaks against the repo's real,
large `docs/` tree. Considered and rejected: accepting the
implementation record's pasted `gh pr list` output and pytest summary
as sufficient evidence — rejected per this role's own builder-blind
mandate and because the task brief explicitly asked for a live,
non-simulated re-check at review time, which by definition cannot be
satisfied by re-pasting the builder's own earlier output.

## Upstream basis

- `docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md`
  (sha `135712e8e4c56195aa0dedab6060db1610f3dc13`, present on this
  branch — `git ls-files`, this session) — the approved stage-4
  proposal; its `files:` frontmatter list, `## Rationale`, and `## How
  you'll know it worked` are the source of every acceptance item
  checked below.
- Issue #2432 — `gh issue view 2432`, this session; its `## Acceptance`
  section is verbatim-identical to the proposal's `## How you'll know
  it worked` plus the two `gate:` lines.
- `1f1c0677:docs/issue-2432/reports/implementation.md`,
  `1f1c0677:docs/issue-2432/reports/implementation/in-flight-branch-migration.md`,
  `1f1c0677:docs/issue-2432/reports/implementation/deviation-log/20260825T135027234095-1af27b595645d6f8.md`
  — the delivered work and its own deviation disclosure; not present on
  this review branch, read via `gh pr diff 2436` and the
  `/tmp/pr2436-wt` worktree this session, not trusted at face value
  (see findings G2 and OF-1 below for where independent checking
  diverged from the record's own framing).
- `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/hooks/board-gate.sh`
  — the actual gate script whose refusal text PR #2436 quotes; read
  directly this session to check the quotes and rule numbers, not
  sourced from any docs/ path in this repo.

## Findings

Five acceptance items; item 1 bundles three independently testable
clauses ("a session spawned under the new scheme produces a
board-visible record", "a pre-existing role-named branch's record
remains board-visible unchanged", "both appear together in one
`board.py` listing") and is split into C1a/C1b/C1c per
conformance-review-requirement-extraction rule 1. Every module/test
citation below is pinned `1f1c0677:<path>` — none of those paths exists
on this review branch; all were read via the `/tmp/pr2436-wt` worktree
this session (see "## What was done" above).

---
requirement: "C1a — a session spawned under the new scheme produces a board-visible record" [dimension: functional behavior]
spec_ref: issue #2432, Acceptance bullet 1 (`check: test/test_branch_naming_dual_scheme.py`), clause 1
verdict: Present
evidence: |
  1f1c0677:board.py:694-728 (`_skill_axis_report_names()`, new) and
  1f1c0677:board.py:731-752 (`board()`, now merges
  `_skill_axis_report_names()`'s results into the per-subject `roles`
  dict alongside the fixed-`ROLES` loop).

  canonical: `cd /tmp/pr2436-wt && python3 -m pytest
  1f1c0677:test/test_branch_naming_dual_scheme.py -v` (this session, PR
  head `1f1c0677`, independent worktree) —
  `DualSchemeBoardDiscoveryTest::test_new_scheme_skill_record_is_board_visible
  PASSED`, full run derived: `9 passed in 1.05s` (pytest summary line,
  this session's own run).
rationale: Code path and an independently re-run test both confirm a record filed under `issue-<n>/<skill>-<disambiguator>` naming is picked up by `board()`.
---
requirement: "C1b — a pre-existing role-named branch's record remains board-visible unchanged" [dimension: functional behavior / regression]
spec_ref: issue #2432, Acceptance bullet 1, clause 2
verdict: Present
evidence: |
  1f1c0677:board.py:731-737 — the existing `for r in _sp.ROLES` loop is
  byte-identical to pre-stage-4 `main` (PR #2436's diff hunk, `gh pr
  diff 2436` this session, only adds lines after it, does not edit it).

  canonical: `cd /tmp/pr2436-wt && python3 -m pytest
  1f1c0677:test/test_branch_naming_dual_scheme.py -v` (this session) —
  `DualSchemeBoardDiscoveryTest::test_old_scheme_role_record_stays_board_visible_unchanged
  PASSED` and
  `CheckoutNamingSchemeTest::test_old_scheme_branch_shape_byte_identical
  PASSED`, derived: `9 passed in 1.05s`.

  derived: this session also ran `spawn.board()` from the same
  worktree against this repo's real `docs/` tree (not a synthetic
  fixture, via a script placed outside the worktree to avoid a
  `spawn.py` module-name collision under `/tmp`) — returned role-axis
  entries for roughly 400 real `issue-<n>` directories (e.g.
  `issue-2241: ['architecture', 'conformance-review',
  'execution-observation', 'implementation']`) with no crash and no
  dropped entry, confirming the merge doesn't regress the old-scheme
  path at real scale, not just in the two-record unit-test fixture.
rationale: Both an independently re-run existing test and an independent live run against the real docs/ tree confirm the old-scheme loop is unedited and still resolves.
---
requirement: "C1c — both schemes appear together in one `board.py` listing" [dimension: functional behavior]
spec_ref: issue #2432, Acceptance bullet 1, clause 3
verdict: Present
evidence: |
  canonical: `cd /tmp/pr2436-wt && python3 -m pytest
  1f1c0677:test/test_branch_naming_dual_scheme.py -v` (this session) —
  `DualSchemeBoardDiscoveryTest::test_both_schemes_appear_together_in_one_listing
  PASSED`, derived: `9 passed in 1.05s`.
rationale: Independently re-run test confirms a single `board()` call returns both an old-scheme and a new-scheme record for the same subject.
---
requirement: "C2 — a live re-check of `gh pr list --state open` at landing time confirms every currently-open PR still resolves correctly under the dual-scheme reader (none becomes invisible to the board); run this literally, not simulated, and paste the actual output" [dimension: scope-boundary / regression; verification method: Demonstration, run live by this review session per conformance-review-verification-method-selection rule 3 — not reused from the PR's own paste, since the instruction specifically asks for a live re-check at review/landing time]
spec_ref: issue #2432, Acceptance bullet 2
verdict: Present
evidence: |
  canonical, this session's own live run (not copied from PR #2436's
  paste), `gh pr list --state open --json number,headRefName,title`:
  ```json
  [{"headRefName":"issue-2431/conformance-review","number":2437,"title":"issue-2431: builder-blind conformance review of PR #2434"},{"headRefName":"issue-2432/implementation","number":2436,"title":"issue-2432: branch/record naming to skill axis + lease disambiguator (dual-scheme, stage 4)"},{"headRefName":"issue-2431/implementation","number":2434,"title":"issue-2431: drop the calendar bound for confirmed-dead-pid spawn-attempt orphans"},{"headRefName":"issue-2409/conformance-review","number":2420,"title":"issue-2409: conformance-review phase-1 (survey + proposal)"},{"headRefName":"issue-2409/execution-observation","number":2419,"title":"issue-2409: execution-observation phase-1 (survey + proposal)"},{"headRefName":"issue-2409/implementation","number":2416,"title":"issue-2409: attack exploratory-Bash, hook-refusal, and redundant-read waste"}]
  ```
  All 6 open PRs listed above use `issue-<n>/<role>` shape branch names
  (`implementation`, `conformance-review`, `execution-observation`) —
  none uses the new `<skill>-<disambiguator>` shape yet (expected: no
  live spawn path produces that shape yet, per finding C1b's evidence
  that `board.board()`'s change is additive-only). None of these 6
  branches' role segments are affected by a purely additive read.
rationale: A live `gh pr list` run by this review session (not the builder's) shows every currently-open PR still uses the unaffected old-scheme shape, and the dual-scheme reader change is provably additive, so none becomes invisible.
---
requirement: "C3 — no existing open PR's branch name or content changes as a result of this stage landing; verify by diffing the open-PR list before/after" [dimension: scope-boundary]
spec_ref: issue #2432, Acceptance bullet 3
verdict: Present
evidence: |
  canonical: PR #2436's own diff (`gh pr diff 2436`, this session, 859
  lines) touches only `board.py`, `pipeline.py`, `roster.py`,
  `spawn.py` (new functions/re-exports, no deletion or rename of an
  existing function), `1f1c0677:docs/handbooks/branch-naming.md` (new
  file), `1f1c0677:docs/issue-2432/reports/implementation.md` and its
  `implementation/` subtree (new files, this issue's own tree), and
  `1f1c0677:test/test_branch_naming_dual_scheme.py` (new file). No
  `git branch`, `push --force`, or `gh pr edit`/`gh pr close`
  invocation appears anywhere in the diff.

  derived: diffing the "before" list in
  `1f1c0677:docs/issue-2432/reports/implementation/in-flight-branch-migration.md`'s
  "Live re-check at landing time" section (5 PRs: #2435, #2434, #2420,
  #2419, #2416) against this finding's own C2 live list (6 PRs) — the
  only changes are PR #2436 itself appearing as a 6th entry and a new
  PR #2437 (`issue-2431/conformance-review`) appearing; PR #2435
  (`issue-2414/conformance-review`) is no longer open. All of #2434,
  #2420, #2419, #2416 are present in both lists with unchanged
  `headRefName`. #2437's appearance and #2435's disappearance are
  ordinary unrelated repo activity (a new conformance-review session on
  a different issue opening its own PR, and a different PR closing) —
  PR #2436's own diff cannot close or open a PR (no such invocation in
  the diff), so neither event is caused by this stage's changes.
rationale: The diff is provably scoped to new files plus additive functions in 4 modules, and an independent before/after `gh pr list` diff shows only unrelated-cause changes (a new unrelated PR, one unrelated closure), never a rename/re-point/content change on any of the 4 continuously-open PRs.
---
requirement: "G1 — `1f1c0677:docs/handbooks/branch-naming.md` documents both schemes and the coexistence window (start = this stage's landing commit; intended end = stage 6)" [dimension: scope-boundary / documentation]
spec_ref: issue #2432, Acceptance gate 1
verdict: Present
evidence: |
  `1f1c0677:docs/handbooks/branch-naming.md:1-149` (new file, not
  present on this review branch — read via `gh pr diff 2436`, this
  session). Documents both schemes under "## 두 스킴"
  (`issue-<n>/<role>` and `issue-<n>/<skill>-<lease-disambiguator>`),
  and the coexistence window under "## 공존 기간 (coexistence
  window)": "시작: 이 stage(#2432)가 landing 된 커밋. 의도된 끝: stage
  6 (role 삭제)".
rationale: The required file exists at the specified path and states both the start (this stage's landing commit) and intended end (stage 6) of the coexistence window, matching the proposal's own "What will be done" wording almost verbatim.
---
requirement: "G2 — `docs/issue-2241/reports/architecture/in-flight-branch-migration.md` (untracked) states the in-flight-branch handling plainly, matching the proposal's Rationale" [dimension: scope-boundary / documentation]
spec_ref: issue #2432, Acceptance gate 2; proposal `files:` frontmatter line 11 and `## Rationale` (docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md:11,39-55)
verdict: Absent
evidence: |
  canonical, this session: `ls docs/issue-2241/reports/architecture/`
  → `2026-08-25-hunt-retire-role-axis-staging.md`, `scout-brief.md`,
  `survey.md` — no `in-flight-branch-migration.md` at the frozen path
  the proposal's own `files:` list names; that path is untracked (never
  created, on `main` or any branch this session could reach) and PR
  #2436's diff (`gh pr diff 2436`, this session) does not touch it at
  all — confirmed against the full 859-line diff read this session.
rationale: The gate names one specific file path as the deliverable; nothing exists at that untracked path in the reviewed PR. Equivalent content was placed at a different path instead (see finding OF-1/OF-2 below for the disclosed reason and this record's assessment of that disclosure) — but the literal gate, checked at the untracked path it names, is not satisfied by this PR.
---

## Open findings

canonical for this whole section: `1f1c0677:docs/issue-2432/reports/implementation.md`
("Rationale for deviations"),
`1f1c0677:docs/issue-2432/reports/implementation/in-flight-branch-migration.md`,
and
`1f1c0677:docs/issue-2432/reports/implementation/deviation-log/20260825T135027234095-1af27b595645d6f8.md`
— none present on this review branch, all read via `gh pr diff 2436`
and the `/tmp/pr2436-wt` worktree this session, cross-checked against
`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/hooks/board-gate.sh`
and live `gh` calls, also this session, as detailed per item below.

1. **OF-1 — the gate-2 deviation (G2) is real and substantially
   disclosed, but its second gate-refusal citation misidentifies the
   rule number.** The three sources above all state that
   `board-gate.sh` "R4 and then R11" refused the frozen-path write, and
   quote R4's refusal text verbatim and accurately. canonical, this
   session: read
   `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/hooks/board-gate.sh`
   directly — its own rule-list comment (lines 6-30) and section
   markers (`grep -n "^# --- R"`, this session) show exactly five
   rules, R1-R5; there is no R11 anywhere in the script. The second
   refusal's quoted text ("docs/issue-2432/reports/architecture/in-flight-branch-migration.md
   belongs to another role. implementation writes only
   implementation.md, implementation/\*\* — never a foreign record.")
   matches, word-for-word, the `deny()` call format string at
   board-gate.sh:1019-1022, which sits under the section explicitly
   marked `# --- R5: reports/ ownership` (board-gate.sh:899) — not R11.
   The refusal itself is genuine and the quoted text is accurate; only
   the rule number attached to it is wrong (should read R5, not R11),
   which would mislead a reader who tries to independently verify the
   citation by searching the gate script for "R11". This is a
   documentation-accuracy defect in the disclosure, not a defect in the
   underlying deviation-handling behavior itself.
2. **OF-2 — the disclosure's other components check out.** canonical,
   this session: `gh issue view 2432 --json comments` shows a comment
   at `https://github.com/tokenmaxxxer/on-the-record/issues/2432#issuecomment-5411258350`,
   authored by the same account as the issue (`JiwonJung94`), whose
   body opens "stage-4 build (this session, branch
   issue-2432/implementation): the acceptance gate's second deliverable
   is a doc at the parent program issue's own architecture-reports tree
   (issue #2241). board-gate.sh R4 refuses that write from this
   branch..." — matching the record's claim of having filed this
   comment. canonical: `gh issue view 2432 --json body -q .body`, this
   session, contains no `maintenance-targets:` line naming issue-2241,
   matching the record's claim that the exception condition genuinely
   wasn't met. The content actually delivered at
   `1f1c0677:docs/issue-2432/reports/implementation/in-flight-branch-migration.md`
   substantively restates the proposal's own Rationale (every branch
   open at landing time keeps its old name and finishes its lifecycle
   unchanged; no rename/re-point/force-push; only future spawns use the
   new scheme) — this part of finding G2's requirement (content
   accuracy) would be Present if it were being checked at the path it
   actually landed at; it is scored Absent above only because the gate
   names a specific different, untracked path.
3. **OF-3 — a minor count error in the implementation record's "What
   was done."** canonical, this session: PR #2436's `spawn.py` diff
   hunk (`gh pr diff 2436`) adds exactly 4 new re-export lines
   (`new_lease_disambiguator`, `_skill_axis_report_names`,
   `checkout_issue_branch_for_skill`, `_checkout_named_branch`) —
   derived: counting the `+` lines in that hunk, this session — but
   `1f1c0677:docs/issue-2432/reports/implementation.md` states
   "`spawn.py` — re-exports the five new names" and then
   parenthetically lists only those same 4 names. Cosmetic — does not
   affect any of the five acceptance items above — noted here for the
   upstream record's own accuracy.

## open-finding-resolution-path

- OF-1 resolution path: a follow-up edit to
  `1f1c0677:docs/issue-2432/reports/implementation.md`,
  `1f1c0677:docs/issue-2432/reports/implementation/in-flight-branch-migration.md`,
  and
  `1f1c0677:docs/issue-2432/reports/implementation/deviation-log/20260825T135027234095-1af27b595645d6f8.md`,
  correcting "R11" to "R5" wherever the second gate refusal is cited —
  derived: OF-1's own citation of board-gate.sh's five-rule (R1-R5)
  list above, this session. Not required for any of the five acceptance
  items above to pass or fail — derived: see the six Present verdicts
  and one Absent verdict recorded in "## Findings" above, none of which
  depends on this citation's rule number — this is a citation-accuracy
  fix, not a behavior fix.
- OF-2 resolution path: none — recorded as a confirming finding, not a
  defect.
- OF-3 resolution path: a one-word fix in
  `1f1c0677:docs/issue-2432/reports/implementation.md` ("five" →
  "four") — derived: this session's own count of the `+` lines in
  `spawn.py`'s diff hunk, cited under OF-3 above. Not required for any
  acceptance item above — derived: see "## Findings" above, none of
  which cites this count.
- G2's own resolution path (the underlying gate-2 gap, distinct from
  OF-1/OF-2/OF-3's documentation-accuracy notes): either a session
  spawned on `issue-2241/implementation` moves/authors the content at
  the frozen path, or a human adds a `maintenance-targets: issue-2241`
  line to issue #2432's body so a future session from this issue's own
  branch can write there directly — canonical: both paths are named in
  the issue-2432 comment cited under OF-2 above
  (`https://github.com/tokenmaxxxer/on-the-record/issues/2432#issuecomment-5411258350`,
  confirmed filed via `gh issue view 2432 --json comments`, this
  session).

## Next steps

None required for this review itself — it is read-only. canonical: `gh
issue view 2432 --json comments`, this session — confirms the
issue-2432 comment cited under OF-2/the resolution-path section above
was genuinely filed and names both unblock paths for G2's frozen-path
gap; no action on this review's own part is needed beyond what's
already recorded above. A follow-up correcting the "R11" → "R5"
citation and the "five" → "four" count (OF-1/OF-3) would remove those
two open findings but is not required for any of the five acceptance
items to pass or fail.

loop_state set to `reported` (terminal for a review-record). Overall
`result: failed` per EARL worst-case recomputation: findings C1a, C1b,
C1c, C2, C3, G1 all verdict Present — derived: this session's own `9
passed in 1.05s` pytest run, cited under C1a/C1b/C1c above, and this
session's own live `gh pr list --state open` paste, cited under C2
above — while finding G2 verdicts Absent — derived: this session's own
`ls docs/issue-2241/reports/architecture/` run, cited under G2 above.
This reflects the frozen-path gate deliverable's genuine absence, not a
defect in the dual-scheme naming/discovery mechanism itself, which is
fully Present across all three `check:` items and `gate:` item G1.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2432's bundled Acceptance bullet 1 (new-scheme-visible + old-scheme-unchanged + both-together) into findings C1a/C1b/C1c per rule 1, dimension-tagged all seven findings, and kept the two `gate:` lines as their own list items (G1/G2), distinct from the three `check:` items (C1-C3).
skill-verdict: conformance-review-verification-method-selection — applied: invoked; reused the dual-scheme test file's existing test cases as Test-method evidence per rule 4 for C1a/C1b/C1c — derived: `9 passed in 1.05s`, this session's own worktree run, cited in full under findings C1a/C1b/C1c above — rather than re-deriving a parallel manual check, and used Demonstration (a live, this-session `gh pr list --state open` run, cited under C2 above) rather than Inspection for C2 per rule 3, since the acceptance text explicitly asks for a live re-check, not a static read.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Absent (not Incorrect) to G2 per rule 2 — the PR does not contradict the requirement, it omits the file at the frozen path entirely, which is the Absent case, not the Incorrect case; named the specific missing evidence location (the frozen path itself) per rule 5, and re-checked the Absent verdict once against the live artifact (canonical: `ls docs/issue-2241/reports/architecture/`, this session, cited under G2 above) per rule 6 before finalizing it.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; cited every PR-branch-only path as `1f1c0677:<path>` (the PR head sha) rather than a bare path, per rule 1, and cited `board-gate.sh` (outside this repo's docs/ tree, in the core plugin) directly by its real filesystem path rather than trusting PR #2436's own paraphrase of it; recorded `board.py`/`pipeline.py`/`spawn.py` as separate evidence lines where a finding's evidence actually spans them (C1a/C1b), per rule 2.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote the seven `---`-delimited requirement blocks above with the full field list (requirement, spec_ref, verdict, evidence, rationale), sourced every verdict from this session's own worktree/test-run/live-`gh`/gate-script reads rather than the implementation record's account of its own work.
other mounted skills: not triggered (conformance-review-sampling-derivation — full enumeration of all five acceptance items, three test-file assertions plus two gate docs, was feasible in one PR-sized (859-line) diff, no sampling needed; conformance-review-severity-classification — this review's scope was not explicitly extended into risk-weighting, and the one Absent finding (G2) is disclosed in-record with its own rationale rather than needing a severity band; adversarial-review — this task is verification against a known-correct spec (issue #2432's own Acceptance section), which is exactly the case adversarial-review's own trigger excludes in favor of this conformance-review family).
