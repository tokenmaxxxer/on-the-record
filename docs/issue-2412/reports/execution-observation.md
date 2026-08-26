---
issue: 2412
role: execution-observation
author: execution-observation
loop_state: observed
upstream:
  - path: docs/issue-2412/reports/implementation.md
    sha: 7e433ba19bd150829db0563f1c9b517c3c9628bf
  - path: docs/issue-2412/reports/implementation/stage-proposal-path-corrections.md
    sha: 7e433ba19bd150829db0563f1c9b517c3c9628bf
  - path: docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
  - path: docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
subject: PR #2449 (branch issue-2412/implementation, HEAD commit 7e433ba1) — the decided resolution to issue #2412's board-gate R4/R5 proposal-path collision
test: issue #2412's four acceptance-criteria checkboxes, re-derived independently against the delivered PR rather than accepted from the implementation record's self-reported verdict
result: failed
assertedBy: execution-observation — live, independent reproduction this session (own Edit-tool probe from a different role/branch than the implementation session used, plus git log/grep against the actual proposal files on this branch)
---

# issue-2412 — execution-observation record

## What was done

Independently re-derived each of issue #2412's four acceptance-criteria
checkboxes against PR #2449, rather than accepting the implementation
record's self-reported verdict. canonical: `gh pr view 2449 --json
body,commits,files`, this session, and `git show
origin/issue-2412/implementation:docs/issue-2412/reports/implementation.md`,
this session (that record is untracked on this branch — PR #2449 is
unmerged; reached here via `git show <remote-branch>:<path>`, not a
local path).

- **AC1 (decide + record resolution + rejected alternative) — met.**
  canonical: `grep -n "^# --- R" "$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh"`,
  this session — five matches (`R1`..`R5`), no `R6` or higher, confirming
  the record's claim that there is no `R11` and the correct cite for the
  second refusal is `R5`. canonical: `Read
  "$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh"` lines 740-1034, this
  session — R4's `maintenance-targets` exception (the `if issue_dir in
  _maint_targets: continue` check the record cites is at line 890) and
  R5's `reports/` ownership check (deny format string at lines
  1019-1022) both match the record's description. canonical: `gh issue
  view 2286 --json body -q .body | grep -i maintenance-targets` and `gh
  issue view 2432 --json body -q .body | grep -i maintenance-targets`,
  this session — no match on either (exit 1 both times), confirming the
  "exemption exists, unused twice" claim. derived: the record's "Why"
  section (`git show
  origin/issue-2412/implementation:docs/issue-2412/reports/implementation.md`)
  states the reasoning and names the rejected alternative (an R4
  exemption) — present, matches what board-gate.sh actually does.
- **AC2 (stage-3 and sibling proposals actually updated, destination
  verified writable) — NOT met.** canonical: reproduced the R4 refusal
  myself, live, this session, from branch `issue-2412/execution-observation`
  (a different role/branch than the implementation session's
  `issue-2412/implementation`) via an `Edit` tool call against
  `docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`
  — refused verbatim:
  ```
  board-gate: writing docs/issue-2241/ requires branch
  issue-2241/execution-observation (current: issue-2412/execution-observation),
  and issue #2412's body declares no matching `maintenance-targets:`
  entry for issue-2241. Every role output reaches main only through a
  PR the human merges — never a direct write from another branch.
  (contract v3 s10)
  ```
  canonical: `git log --oneline --
  docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`,
  this session — exactly one commit, `135712e8` (the original stage-3
  staging, pre-dating issue #2412); no correction has ever landed there.
  canonical: `grep -n "docs/issue-2241/reports"
  docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md
  docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md`,
  this session — both files still name their original destinations,
  `docs/issue-2241/reports/architecture/board-gate-r5-migration.md`
  (untracked, never created) and
  `docs/issue-2241/reports/architecture/in-flight-branch-migration.md`
  (untracked, never created) — confirmed via `ls`, this session, no such
  files exist anywhere in this repo — in `files:` frontmatter and body
  text. The acceptance item requires the proposals to actually be
  updated; a written, unapplied patch doc plus a `gh issue comment`
  (both real — see below — but neither edits the proposal files) does
  not satisfy that text.
- **AC3 (if R4 amended instead, live two-halves demo) — correctly
  inapplicable.** derived: the implementation record's "Why" section
  states the chosen resolution is "amend the proposal-named paths," not
  "amend R4," so no such demonstration was owed; none was attempted or
  claimed.
- **AC4 (already-landed stage-3 doc discoverable from the proposal) —
  NOT met.** canonical: `grep -n -i
  "issue-2412\|issue-2286\|redirect\|corrected\|see issue"
  docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`,
  this session — two matches, both the unrelated word "corrected" in a
  different sentence about `EXTRA_SUBTREE` keys, not a pointer to issue
  #2412 or to `docs/issue-2286/reports/implementation/board-gate-r5-migration.md`
  (that landed file does exist — confirmed via `ls`, this session).
  canonical: the same grep against
  `docs/issue-2241/proposals/2026-08-25-stage-4-branch-record-naming-cutover.md`,
  this session — zero matches. canonical: `gh issue view 2241 --json
  comments -q '.comments[-1].body'`, this session, confirms the
  implementation record's claimed `gh issue comment` on issue #2241 was
  actually filed and names both destinations. But none of the three
  places the implementation record cites (that comment, its own patch
  doc, or itself) is reachable *from the proposal file* — a reader who
  opens
  `docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`
  today (verified live, this session) finds only the dead,
  never-created path with nothing pointing anywhere else. The
  acceptance text says "discoverable from the proposal," not
  "discoverable somewhere in the repo by someone who already knows to
  search issue #2412 or issue #2241's comments."
- canonical: `grep -n "docs/issue-2241"
  docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md
  docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md`, this
  session — no match, confirming stages 5-6 do not collide the way
  stages 3-4 do.

## Why

This role's charge is independent verification, not restating an
upstream self-assessment — this session's routed
`defect-verification-independence-from-upstream-verdicts` guidance: a
record marked pass/landed is re-derived here, not cited. Two of the
four acceptance checkboxes fail that re-derivation even though the
underlying gate analysis (AC1) is sound and independently verified
against `board-gate.sh`'s actual code and live behavior this session
(see "What was done" above for both canonical citations). derived: the
failure is structural, not sloppy — `board-gate.sh` R4 (per the code
read above, lines 878-897) has no append-only carve-out the way R5
(lines 981-991) does, and blocks every write under a foreign issue's
`docs/issue-<n>/` tree regardless of write shape; a role session cannot
self-grant the `maintenance-targets:` escape (`gh-guard` denies `gh
issue edit`, cited in both this issue's and the two prior issues'
records) or spawn a peer role on its own initiative. canonical: this is
the third consecutive occurrence of the identical wall —
`docs/issue-2286/reports/implementation.md` and
`docs/issue-2432/reports/implementation/deviation-log/20260825T135027234095-1af27b595645d6f8.md`
(both present on this branch, read live this session) record the first
two. Issue #2412 was chartered specifically to resolve this pattern;
the decision reached here is sound, but the acceptance criteria as
written assumed the fix was executable within one delivering session's
write scope, which board-gate's own rules make structurally impossible
without either a human step or a session dispatched directly onto issue
#2241's own branch. Neither happened in this PR.

## Upstream basis

- `docs/issue-2412/reports/implementation.md` — untracked on this
  branch (PR #2449, branch `issue-2412/implementation`, unmerged);
  reached via `git show
  origin/issue-2412/implementation:docs/issue-2412/reports/implementation.md`,
  this session, sha `7e433ba19bd150829db0563f1c9b517c3c9628bf` (PR #2449
  HEAD). canonical: `gh pr view 2449 --json body`, this session, shows
  the PR's own self-reported result frontmatter — re-derived
  independently above (see "What was done", AC1-AC4) rather than
  trusted at face value.
- `docs/issue-2412/reports/implementation/stage-proposal-path-corrections.md`
  — same branch/commit, same untracked-on-this-branch caveat — the
  unapplied patch, read via the same `git show`, this session.
- `docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-author-identity.md`
  and `.../2026-08-25-stage-4-branch-record-naming-cutover.md`, both
  present on this branch, `sha: 135712e8e4c56195aa0dedab6060db1610f3dc13`
  — read live this session; both still carry their original,
  uncorrected destinations (see "What was done", AC2, for the canonical
  grep/git-log citations).
- `$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh` — mounted core-plugin
  checkout, not repo-versioned (no sha), read live this session at the
  line ranges cited above; authoritative over any paraphrase, including
  this record's own.
- canonical: `gh issue view 2241 --json comments`, this session, and `gh
  issue view 2286 --json body` / `gh issue view 2432 --json body`, this
  session — all four read live (GitHub API responses, no file sha).

## Open findings

- **AC2/AC4 unmet, no owner assigned.** Resolution path is exactly what
  the implementation record already names: a session spawned on
  `issue-2241/implementation` (or whichever role owns that tree) applies
  `stage-proposal-path-corrections.md`, or a human adds a
  `maintenance-targets:` line naming issue #2241 to a future delivering
  issue's body first. Neither has an owner or a date yet. canonical: `gh
  issue view 2241 --json comments -q '.comments[-1].body'`, this
  session — the filed comment names the fix but assigns no owner or
  date for applying it.
- **Recurring structural mismatch between this repo's acceptance-writing
  convention and board-gate's write-scope rules.** This is the third
  issue in a row (#2286, #2432, now #2412) where an issue's acceptance
  criteria assumed a delivering role session could write into a
  parent-program tree it structurally cannot reach. Worth surfacing to
  whoever queues issue #2241's own follow-up work or writes its next
  stage's acceptance criteria, so a fourth occurrence doesn't repeat the
  same unmet checkbox. No resolution path claimed here beyond surfacing
  it — out of this record's own write scope to fix.
- None beyond the two above.

## Next steps

None from this session — `loop_state: observed` (terminal for this
record kind). Whoever reviews/merges PR #2449 should treat AC2 and AC4
as genuinely unmet rather than resolved-in-spirit. canonical: the live
`Edit`-tool R4 refusal and the `git log`/`grep` results cited under
"What was done" above are this record's own, independently produced
evidence this session, not a restatement of the implementation record —
they land on the same wall the implementation record itself disclosed
under its "Open findings" section; the disagreement is only about
whether that disclosed gap still counts as satisfying the issue's own
acceptance text as written.
