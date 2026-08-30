---
issue: 2135
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
code_under_review: PR #2825 (branch issue-2135/diagnose-first+technical-writing-minimalism-scoping-5676d1d0, head 1835fcfe632ebe76ddd71a131cf7369f7331257e)
type: verification
breaking: false
verdict: PASS
loop_state: landed
upstream:
  - path: docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0.md  # untracked on this branch — lives on PR #2825's branch, unmerged
    sha: 1835fcfe632ebe76ddd71a131cf7369f7331257e
  - path: docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0/composition-breakdown-2026-08-30.md  # untracked on this branch — lives on PR #2825's branch, unmerged
    sha: 83f4ea58fd31d36e52594d91124c5eeddeeefd62
---

# issue-2135 — independent-verification-1 record

## What was done

Independently audited PR #2825 ("issue-2135: re-measure standing context
post-diet -- 44,840 tokens, still over 25K"), the docs-only re-measurement
delivery against issue #2135's 2026-08-28 triage narrowing. canonical:
`gh pr view 2825 --json title,body,commits,files,additions,deletions` —
2 files added (`docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0.md`,
`.../composition-breakdown-2026-08-30.md` — both untracked on this branch,
they live only on PR #2825's own branch, unmerged), 355 additions, 0
deletions, `mergeable: MERGEABLE`.

Checks run this session, all against the PR's own head commit:

1. **Cited commits exist.** derived: `git log --oneline -1 83f4ea58` →
   `83f4ea58 issue-2135: fresh composition breakdown, re-measurement
   (2026-08-30)`; `git log --oneline -1 1b859017` → `1b859017 issue-2135:
   spawned-session context diet ... (#2143)`. Both commits the record
   cites as its own basis are real, reachable history.

2. **Diff scope matches the "no code changed" claim.** derived: `git
   fetch origin issue-2135/diagnose-first+technical-writing-minimalism-scoping-5676d1d0`
   then `git diff origin/main FETCH_HEAD --stat` → only the 2 new files
   under `docs/issue-2135/reports/` (a third line showing
   `docs/issue-2755/reports/test-depth-audit-90515b4a.md` deleted is base
   drift, not part of the PR — `origin/main` advanced past the PR's fork
   point via commit `bb20419c`, landed after PR #2825 was branched; `gh
   pr diff 2825` — result: only the 2 added files — confirms the PR
   itself touches nothing else). No `spawn.py`, `directive_assembly.py`,
   or `on-the-record/directive/*.md` path appears in either diff.

3. **Both pytest claims reproduce exactly.** Checked out the PR head into
   a scratch worktree (`git worktree add /tmp/pr2825-check FETCH_HEAD`)
   and re-ran both commands the record cites:
   - derived: `python3 -m pytest -m "not slow" -q` — result: `16 failed,
     570 passed, 3 xfailed in 33.19s`, and the 16 failing test names
     printed by this run are the identical set (harness/fixture, 2x
     test_convention_equivalence, 1x test_local_dependency_env, 9x
     test_spawn_cross_family_skill_selection, 2x
     test_spawn_artifact_skill_pairing, 3x
     test_spawn_skill_judge_haiku_timeout_overlap) listed verbatim in the
     record's Acceptance verification section — an exact match, not just
     a matching count.
   - derived: `python3 -m pytest -m "not slow" -q -k "watchdog or
     heartbeat or monitor or watch"` — result: `45 passed in 3.76s`,
     matching the record's claim exactly.
   Worktree removed afterward: `git worktree remove /tmp/pr2825-check
   --force`.

4. **The `directive_assembly.py` lines 480-490 quote is verbatim.**
   derived: `sed -n '475,495p' directive_assembly.py` on the PR head —
   result: the Issue #2204 comment block matches the record's quoted text
   word-for-word, including the "~46s" figure and the "no Read tool call,
   no round trip" phrasing.

5. **Arithmetic in the composition breakdown checks out.** Recomputed by
   hand from the numbers the record states as measured (not re-measuring
   the underlying session log itself, which is this session's own
   independent measurement problem — see Open findings):
   - `9797 + 35043 = 44840` (the headline number).
   - `2563 + 12384 + 2969 = 17916` bytes; `17916 / 4 = 4479` tokens,
     matching the record's own per-row B→tok conversions: `2563/4=641`,
     `12384/4=3096`, `2969/4=742` (rounded).
   - `4479 / 44840 = 0.0999` → "10%", matches.
   - `44840 - 4479 = 40361`, matches the row-4 remainder; `40361 / 25000
     = 1.614` → "1.61x over", matches.
   - `44840 - 25000 = 19840`, matches the stated miss.
   - `44840 / 55505 = 0.8078` → a 19.2% reduction from the 2026-08-24
     baseline, matches.
   All five derived figures are internally consistent; no arithmetic
   error found.

6. **Issue-comment citations are accurate.** canonical: `gh issue view
   2135 --repo tokenmaxxxer/on-the-record --comments` (read this
   session) — the 2026-08-24 comment's "31,073 cache-creation + 24,432
   cache-read = 55,505 tokens" and the 2026-08-28 comment's "re-run the
   first-turn standing-context measurement on the same shape PR #2143
   measured... then close, or reopen the diet with a fresh breakdown if
   it still misses" / "Do not treat this as an open design question...
   only the number is unverified" are quoted accurately in both the
   record and the composition-breakdown file.

No discrepancy found between the PR's claims and what this session could
independently re-derive or re-run.

## Why

Issue #2135 needs 2 independent-verification records for its
`issue-2135/implementation` deliverable stream, this session is slot
`independent-verification-1`, and the spawn task is explicit: read PR
#2825, audit it, and leave `verifies_subject: true` if the audit holds.
The PR is docs-only (a measurement re-run, not a code change), so the
audit strategy was: re-derive every number the record presents as
`derived:`, re-run every command it presents as `derived:` where
reproducible in a fresh worktree, and spot-check every `canonical:`
citation against the actual issue thread and actual git history — rather
than trusting the record's own arithmetic or trusting that its cited
commits exist. Both pytest re-runs and the `directive_assembly.py`
citation matched exactly, and five independent arithmetic identities
derived from the record's own raw inputs all closed, so the audit found
no basis to withhold `verifies_subject: true`.

## What did not work

None.

## Upstream basis

- `docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0.md`
  (untracked on this branch — lives on PR #2825's branch, unmerged; sha:
  `1835fcfe632ebe76ddd71a131cf7369f7331257e`, the PR head) — the record
  under audit.
- `docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0/composition-breakdown-2026-08-30.md`
  (untracked on this branch — lives on PR #2825's branch, unmerged; sha:
  `83f4ea58fd31d36e52594d91124c5eeddeeefd62`) — the evidence file under
  audit.
- PR #2143 (`1b859017`) — derived: `git log --oneline -1 1b859017` →
  present, matching item 1 above.
- tokenmaxxxer-core#278 (external repo, closed) — canonical: `gh issue
  view 2135 --repo tokenmaxxxer/on-the-record --comments` (2026-08-28
  comment: "That follow-up exists and is closed: tokenmaxxxer-core#278").

## Open findings

- This session did not re-derive PR #2825's headline `9797 35043` token
  figures from the raw session log itself — that log
  (`on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.session.20260830T112629.3582248.log`)
  belongs to a different session's workspace and was not accessible from
  this session's own workspace. unverifiable: the exact
  `cache_creation_input_tokens`/`cache_read_input_tokens` pair for that
  specific prior spawn — reason: the source session log is not on this
  session's filesystem; verification here is limited to internal
  arithmetic consistency (item 5 above) and cross-checking the
  reproducible claims (diff scope, pytest runs, code citation), all of
  which held. Resolution path: the second independent-verification slot
  for this subject can re-attempt log access if it runs in a workspace
  with visibility into that log path; otherwise this class of claim
  remains verified only by consistency, not by raw-log reproduction.
- PR #2825 itself flags (in its own Open findings) that the ≥30%
  per-task cost / unchanged-verdicts ablation leg of issue #2135's
  Acceptance was not re-run, deferred as out of the 2026-08-28 triage's
  narrowed scope. canonical: `gh pr view 2825 --json body` — the PR
  body's "What did not run" citation makes the same deferral. Resolution
  path: unchanged from the PR's own statement — a human maintainer
  decides whether to close #2135 on the "repo-scope work is done" basis
  or open a follow-up ablation, per the PR body's own Recommendation
  section (canonical: `gh pr view 2825 --json body`, cited above); this
  verification session does not file that itself.

## Next steps

None — this record is terminal (`loop_state: landed`). The subject's
second independent-verification slot remains open per issue #2135's
"needs 2" requirement.

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; wrote this record's
body, all commit messages, and internal reasoning in English per the
skill (the spawning task text was Korean), reserving Korean only for the
final chat summary to the user.
