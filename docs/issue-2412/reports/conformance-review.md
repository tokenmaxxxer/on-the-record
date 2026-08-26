---
issue: 2412
role: conformance-review
author: conformance-review
loop_state: reported
type: review-record
code_under_review:
  - docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md
  - docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md
  - docs/issue-2412/reports/implementation/stage-proposal-path-corrections.md
breaking: "none — this is a review record, no code changed by this role"
verdict: fail
upstream:
  - path: docs/issue-2412/reports/implementation.md
    sha: 7e433ba19bd150829db0563f1c9b517c3c9628bf
  - path: docs/issue-2412/reports/implementation/stage-proposal-path-corrections.md
    sha: 7e433ba19bd150829db0563f1c9b517c3c9628bf
  - path: docs/issue-2412/reports/execution-observation.md
    sha: 4f4091fbdcba93c52d676c0aa27a6e9ef1307101
subject: PR #2449 (issue-2412/implementation, HEAD 7e433ba1) — "resolve stage-proposal path collision with board-gate R4/R5"
test: issue #2412's 4 acceptance-criteria checkboxes, independently re-derived against PR #2449's delivered artifact
result: failed
assertedBy: conformance-review session, issue-2412 (builder-blind)
---

# issue-2412 — conformance-review record

Builder-blind conformance review of PR #2449 against issue #2412's own
Acceptance text.

canonical: `git fetch origin pull/2449/head:pr-2449-local && git show
pr-2449-local:docs/issue-2412/reports/implementation.md | grep -n "^verdict:\|^loop_state:"` (this session) —
```
verdict: pass
loop_state: landed
```
canonical: `git fetch origin pull/2454/head:pr-2454-local && gh pr view
2454 --json commits -q '.commits[-1].oid'` (this session) —
```
4f4091fbdcba93c52d676c0aa27a6e9ef1307101
```

## What was done

Decomposed issue #2412's Acceptance section into 4 discrete requirements
(conformance-review-requirement-extraction): AC1 unconditional; AC2/AC3 a
conditional pair whose applicability depends on AC1's outcome, kept as
separate line items (extraction rule 5); AC4 unconditional. Sampling not
applicable (conformance-review-sampling-derivation) — scope is 4 bullets
against 2 named proposal files, small enough for full enumeration.

canonical: `grep -n "^# --- R" "$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh"` (this session) —
```
726:# --- R1: docs/ layout ---------------------------------------------------
764:# --- R2: the board requires the user's approvers.md ----------------------
774:# --- R3: no role, no board writes ---------------------------------------
797:# --- R4: the role's own issue branch ------------------------------------
899:# --- R5: reports/ ownership ---------------------------------------------
```
Five rules, `R1`-`R5`, no `R6`+.

canonical: `grep -n "maintenance-targets\|_maint_targets" "$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh" | head -3` (this session) —
```
842:# R4 maintenance-targets exception (issue-222): a role's own issue may
845:# literal `maintenance-targets: <tree list>` line naming OTHER
851:_maint_targets = None  # lazily resolved set of "issue-<n>" strings; None = not fetched yet
```
The exemption mechanism exists.

canonical: `git log --oneline -- docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md` (this session) —
```
135712e8 issue-2241: staged proposal for retiring the role axis (#2252)
```
derived: one line of output = one commit touching either file, dated
before issue #2412 was opened — neither proposal has ever been edited.

canonical: `grep -c "docs/issue-2241/reports/architecture/board-gate-r5-migration.md" docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md` (this session) —
```
2
```
That path (untracked, never created — see the `ls` transcript below) is
still named twice in the stage-3 proposal, in `files:` frontmatter and in
body text.

canonical: `grep -c "docs/issue-2241/reports/architecture/in-flight-branch-migration.md" docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md` (this session) —
```
2
```
Same shape for stage 4's path (also untracked, never created — same `ls`
transcript below).

canonical: `grep -c -i "issue-2412\|issue-2286\|redirect\|see issue" docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md` and the same substituting `issue-2432` for stage 4 (this session) —
```
0
0
```
derived: 0 = no pointer from either proposal file to issue #2412, to the
sibling issue that actually landed the doc, or to a redirect of any kind.

canonical: `grep -n "docs/issue-2241" docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md` (this session) — no output (exit 1) — stages 5-6 name no `docs/issue-2241/` destination, so neither collides.

canonical: `gh issue view 2286 --repo tokenmaxxxer/on-the-record --json body -q .body | grep -c -i maintenance-targets` and the same for issue #2432 (this session) —
```
0
0
```
Neither issue body declares the exemption.

canonical: `ls docs/issue-2286/reports/implementation/board-gate-r5-migration.md docs/issue-2432/reports/implementation/in-flight-branch-migration.md` (this session) —
```
docs/issue-2286/reports/implementation/board-gate-r5-migration.md
docs/issue-2432/reports/implementation/in-flight-branch-migration.md
```
Both real, already-landed corrected destinations — distinct from the two
untracked, never-created `docs/issue-2241/reports/architecture/*` paths
the proposals still name.

canonical: own live `Edit` tool call against
`docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`,
this session, branch `issue-2412/conformance-review` — refused verbatim:
```
board-gate: writing docs/issue-2241/ requires branch
issue-2241/conformance-review (current: issue-2412/conformance-review),
and issue #2412's body declares no matching `maintenance-targets:` entry
for issue-2241. Every role output reaches main only through a PR the
human merges — never a direct write from another branch. (contract v3
s10)
```
Third independent reproduction of this refusal, after the implementation
session's own and PR #2454's — three different roles/branches, same wall.

canonical: `gh issue view 2241 --repo tokenmaxxxer/on-the-record --json comments -q '.comments[-1].body' | head -1` (this session) —
```
issue-2412 build (this session, branch issue-2412/implementation): decided the stage-3/stage-4 proposal path collision (board-gate.sh R4/R5, delivering-role write scope) is resolved by amending each proposal's named migration-doc destination to the delivering child issue's own reports/implementation tree, not by amending R4 itself.
```
The claimed `gh issue comment 2241` was filed; it is not reachable from
either proposal file (the 0/0 grep counts above cover both).

## Findings

Fields per conformance-review-finding-record: requirement, spec_ref, verdict,
evidence, rationale.

---
requirement: R1 — decide and state which resolution applies (amend the proposal-named paths, or carve a narrow R4 exemption), with the reasoning and the rejected alternative recorded
spec_ref: issue #2412 Acceptance bullet 1
verdict: Present
evidence: `7e433ba1:docs/issue-2412/reports/implementation.md` "Why" section — chosen: amend the proposal-named destinations; rejected: a narrow R4 exemption, on two grounds (the `maintenance-targets:` exemption already covers this shape and went unused on #2286/#2432; an R4-only exemption would not clear R5)
rationale: independently checked this session against `board-gate.sh`'s actual R1-R5/`maintenance-targets` code and against issue #2286/#2432's actual bodies (both "What was done" above) — the record's reasoning matches what the gate and the two prior issues actually show
---
requirement: R2 — if paths are amended (as R1 decided), the stage-3 proposal and any sibling stage proposals (stages 4-6) are updated so their named destinations are ones the assigned role can actually write, verified by naming the permitting gate rule
spec_ref: issue #2412 Acceptance bullet 2 (conditional on bullet 1; applies here since R1's resolution is "amend the paths")
verdict: Absent
evidence: `git log --oneline` against both proposal files ("What was done" above) — one commit each, pre-dating issue #2412; the two `grep -c` counts against each file's own dead path — 2 and 2, unchanged; own live `Edit`-tool R4 refusal (same section) confirms this session's own role/branch cannot make the edit either
rationale: the acceptance text requires the proposal files themselves to be updated. What was delivered is a correct, unapplied patch document plus a `gh issue comment`, neither of which edits `docs/issue-2241/proposals/*.md`. Omission, not contradiction — Absent, not Incorrect. Stages 5-6 correctly need no amendment (grep, no output, "What was done" above); the stage-3/stage-4 part of R2 is unmet.
---
requirement: R3 — if instead R4 is amended, a live demonstration that a role session can write the parent-program path AND still cannot write another role's record area — both halves shown, not asserted
spec_ref: issue #2412 Acceptance bullet 3 (conditional on bullet 1; correctly inapplicable — R1's resolution is "amend the paths," not "amend R4")
verdict: Present
evidence: `7e433ba1:docs/issue-2412/reports/implementation.md` "Why" states the chosen resolution is path-amendment; `gh pr view 2449 --json files -q '.files[].path'` (this session) lists 3 new docs files, no `.sh` file
rationale: a conditional requirement that correctly does not apply, and is not attempted, satisfies its own text
---
requirement: R4 — the already-landed stage-3 migration doc ends up discoverable from the proposal (a pointer, a move, or a stated convention) so a reader following the proposal does not hit a path that exists nowhere
spec_ref: issue #2412 Acceptance bullet 4
verdict: Absent
evidence: the `grep -c -i "issue-2412\|issue-2286\|redirect\|see issue"` count against the stage-3 proposal ("What was done" above) — 0; same for stage-4 against `issue-2432` — 0; the landed doc itself exists (`ls` transcript, same section)
rationale: the landed doc is discoverable from the patch doc and from the `gh issue comment`, but not "from the proposal" as the acceptance text requires — a reader opening the stage-3 proposal today finds only the dead path with nothing pointing anywhere else. Absent, not Incorrect: the proposal file was never touched.
---

## Why

Reviewed builder-blind against the issue's own Acceptance text — decomposed
into the 4 requirements above before reading PR #2449's own self-reported
result (this record's opening section) at all. Inspection for R1
(structural: does the reasoning match `board-gate.sh`'s actual code and
the two prior issues' actual bodies) and for R2/R4 (structural: do the
named files contain the required edit/pointer). Demonstration for R2's
writability claim — a live `Edit`-tool probe ("What was done" above), not
an inference from source, per conformance-review-verification-method-selection
rule 3. R3 needed only confirming its precondition doesn't hold
(Inspection).

canonical: `grep -c "docs/issue-2241/reports/architecture/board-gate-r5-migration.md" docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md && grep -c -i "issue-2412\|issue-2286\|redirect\|see issue" docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md` (this session, re-run) —
```
2
0
```
Per conformance-review-verdict-assignment rule 6, both Absent verdicts
(R2, R4) were re-checked this way before finalizing — same as the first
run cited in "What was done" above.

## Upstream basis

- `7e433ba1:docs/issue-2412/reports/implementation.md` and
  `7e433ba1:docs/issue-2412/reports/implementation/stage-proposal-path-corrections.md`
  — PR #2449's own record and patch doc, untracked on this branch (PR
  #2449 unmerged); read via `git show pr-2449-local:<path>`, this session
  (opening transcript above), for the resolution and patch text —
  re-derived independently in "Findings" rather than trusted at face value.
- `4f4091fb:docs/issue-2412/reports/execution-observation.md` — PR #2454's
  independent execution-observation, read via `git show
  pr-2454-local:<path>` after this review's own "What was done" checks
  were complete. canonical: `git show
  pr-2454-local:docs/issue-2412/reports/execution-observation.md | grep -n "^result:"` (this session) —
  ```
  result: failed
  ```
  Consulted as a cross-check only — every "Findings" citation traces to
  this session's own commands, not to #2454's transcript.
- The four stage-3/4/5/6 proposal files under `docs/issue-2241/proposals/`
  — all present on this branch; stages 3/4 at the same commit. canonical:
  `git log -1 --format=%H -- docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md` (this session) —
  ```
  135712e8e4c56195aa0dedab6060db1610f3dc13
  ```
- `$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh` — mounted core-plugin
  checkout, not repo-versioned, read live this session at the line ranges
  cited in "What was done"; authoritative over any paraphrase.
- `gh issue view 2241/2286/2432` — live GitHub API reads, this session,
  transcripts in "What was done" above.

## What did not work

Nothing — every command produced usable evidence on its first run; the
Absent-verdict re-checks (see "Why") reproduced identical counts on a
second run.

## Open findings

- **R2/R4 unmet, no owner assigned.** Same open finding PR #2449's own
  record and PR #2454's execution-observation already disclose.
  Resolution path: a session spawned on `issue-2241/implementation` (or
  whichever role owns that tree) applies `stage-proposal-path-corrections.md`
  to the two proposal files and adds a pointer reachable from the stage-3
  proposal to the landed doc, or a human adds a `maintenance-targets:`
  line naming issue #2241 to a future delivering issue's body first. The
  `gh issue comment 2241` transcript above names the fix but assigns no
  owner or date.
- none beyond the one above.

## Next steps

None — `loop_state: reported` (terminal for this record's kind). PR
#2449's own self-reported result (opening transcript above) is
contradicted by this record's R2/R4 findings (both Absent) — whoever
reviews/merges PR #2449 should weigh this independently-derived result,
since the issue's acceptance text requires all applicable bullets to
hold, not a majority.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2412's 4 Acceptance bullets into 4 requirements, kept AC2/AC3 as separate conditional line items rather than merging them (rule 5), no bundled "and"-clauses needed splitting (rule 1), no summary line to drop (rule 3), no sampling-derivation override stated in the issue (rule 4 n/a)
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of all 4 extracted requirements against the 2 named proposal files plus PR #2449's own 3 files was feasible in one session — no reduction to a sample was needed
skill-verdict: conformance-review-verification-method-selection — applied: invoked; Inspection for R1/R3/R4's structural checks, Demonstration for R2's writability claim (a live `Edit`-tool probe, not an inference from source)
skill-verdict: conformance-review-verdict-assignment — applied: invoked; R1/R3 rendered Present, R2/R4 rendered Absent (not Incorrect — omission, not contradiction, per rule 2) with the failing clause named in each rationale (rule 5); both Absent verdicts re-checked once before finalizing, per rule 6
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every Findings entry cites file/path plus commit sha or live-command transcript this session actually read (rule 1); R2's evidence spans both proposal files, cited separately (rule 2); each requirement backward-traced to its issue bullet before its evidence was checked (rule 3); no duplicate-evidence entries to collapse (rule 4 n/a); single spec version in play (rule 5 n/a)
skill-verdict: conformance-review-finding-record — applied: invoked; wrote all 4 finding blocks with the full field list (requirement, spec_ref, verdict, evidence, rationale); no Incorrect verdicts rendered so `spec_vs_built` was not needed; every verdict carries an evidence pointer and a spec_ref
skill-verdict: conformance-review-severity-classification — not-applicable: review scope was not extended into risk-weighting; findings are recorded as unmet acceptance criteria, not banded defects
skill-verdict: implementation-audit — not-applicable: this session ran under this repo's own role-handoff/conformance-review contract (a structurally independent evaluator session reviewing a separate builder session's delivery, builder-blind) — the same shape implementation-audit describes, but the mechanism in force here is the repo's native contract v3, not a separately-invoked implementation-audit protocol
