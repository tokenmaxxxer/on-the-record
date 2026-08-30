---
issue: 2135
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
loop_state: complete
code_under_review: spawn.py (PR #2143, merged commit 44eef203, carried
  forward through the issue-2207 spawn.py -> directive_assembly.py extract)
type: independent-verification
breaking: false
verdict: pass-with-caveat
upstream:
  - path: fix/2135-session-context-diet (PR #2143)
    sha: 44eef203fc2358c1d6f7ad16ca90f31fe2ab7982
---

# issue-2135 — independent-verification-2 record

## What was done

Independently audited PR #2143 ("issue-2135: spawned-session context diet —
directive index + workspace section files, setting-sources diet, record
skeleton, landing batching"), the only merged implementation-shaped PR
against issue #2135, against the four ordered items its own body claims.

- canonical: `gh pr view 2143 --repo tokenmaxxxer/on-the-record --json
  title,body,mergedAt,mergeCommit,files,headRefName` — mergedAt
  2026-08-24T00:17:58Z, mergeCommit.oid `1f6ee706ce2dac8a0a0b07700d90cf648fbe0a7e`.
  derived: `git log --oneline --all --grep="issue-2135"` shows `44eef203`
  reachable from today's `main` (same commit message/tree, referencing
  #2143) — this is the landed commit this record verifies. A
  duplicate-message commit `1b859017` also exists but is not on `main`'s
  current line (`git log --graph --oneline -5 44eef203` puts `44eef203`
  directly below `7222c6b9`/issue-2137 on the mainline graph).
- Item 2 (setting-sources diet) — canonical: `pipeline.py:676-681`
  ```
  676:    setting_sources = os.environ.get("MUSTER_SETTING_SOURCES",
  677-        ...)
  680:    if setting_sources:
  681:        cmd += ["--setting-sources", setting_sources]
  ```
  derived: `grep -n "setting-sources\|MUSTER_SETTING_SOURCES" pipeline.py`
  — confirms the claimed kill-switch/env-override shape is live in the
  current tree, matching PR #2143's claim.
- Item 2 (directive index + workspace materialization) — canonical:
  `directive_assembly.py:607` (`def write_record_skeleton(...)`) and
  `directive_assembly.py:675` (`def composition_breakdown(...)`).
  derived: `git log --oneline --all -- directive_assembly.py` shows this
  file (and both functions) survived through 15+ subsequent commits
  after PR #2143 landed (issues 2185, 2190, 2204, 2211, 2262, 2409, 2479,
  2508, 2527, 2559, 2575, 2592, 2609, 2670, 2720, 2600) rather than being
  a one-off that later regressed — most notably issue-2207's extract-class
  refactor moved these functions out of `spawn.py` into their own module
  without deleting them.
- Item 2 (materialized section files) — canonical: `ls
  .on-the-record/directive/` in this workspace lists
  `completion-and-landing.md` and `skill-obligations.md` (both named as
  destinations in PR #2143's own content-mapping table), plus 6 newer
  files added by later issues. This session's own SessionStart context
  (visible verbatim at the top of this conversation, e.g. the
  "Landing batching (issue #2135, guidance only — no gate)" paragraph
  inside `completion-and-landing.md`) IS the diet's live output, read
  firsthand in this same session rather than re-derived from a log.
- Item 3 (record skeleton pre-write) — canonical: this session's own
  `git status` at session start (shown in the environment context for
  this turn) listed only the untracked `docs/issue-2135/` directory
  containing this very file, already populated with frontmatter and
  section headings before this session touched it — direct, firsthand
  confirmation of the `write_record_skeleton()` behavior PR #2143
  claims.
- Item 4 (landing batching guidance) — canonical:
  `.on-the-record/directive/completion-and-landing.md`, read in this
  session, contains the "Landing batching (issue #2135, guidance only —
  no gate)" paragraph verbatim, matching the content-mapping table's
  claimed destination for this item.
- Test-count claim — canonical: `git show
  44eef203:tests/test_directive_diet_2135.py | grep -c "def test_"` →
  `10`, matching the PR body's "New `tests/test_directive_diet_2135.py`
  (10 tests)" claim exactly. Path note: this path is untracked on current
  `main` — deleted by commit `a555e169` (issue #2525, "retire the
  plugin's own test suite"), a later, unrelated policy change; the `git
  show <sha>:<path>` form above reaches it at the historical commit where
  it existed, not the working tree.
- unverifiable: could not re-run the deleted `test_directive_diet_2135.py`
  (untracked on current `main`, removed by `a555e169`/issue #2525, see
  bullet above) or the fast/slow-tier pass counts quoted in the PR body
  today — reason: repo-wide test-suite retirement happened after PR
  #2143 landed, per an operator decision extending #2137's
  record-is-the-regression-suite ruling to the plugin's own tooling.
  This is a subsequent policy change, not evidence against PR #2143's
  own correctness at landing time; the live, currently-running artifacts
  audited above (canonical citations, not the retired suite) independently
  corroborate the same four claims.

## Why

Issue #2135 requires `REQUIRED_INDEPENDENT_VERIFICATIONS = 2` (canonical:
`docs/handbooks/observer-verification.md`, "Current mechanism" section)
qualifying records before the subject (PR #2143's landed diet) satisfies
`gates/merge_gate.py`'s `required_verification_missing()`. This record is
slot 2 (`independent-verification-2`, per the spawning prompt). derived:
`gh pr list --repo tokenmaxxxer/on-the-record --search "2143"` and
`--search "2135 independent-verification"` (both run this session) show
no independent-verification PR for this subject besides this one in
flight; this record proceeds independently regardless, since the
requirement is a self-declared count, not an ordering between slots.

## What did not work

None — every claim checked (setting-sources diet, directive-index
materialization, record-skeleton pre-write, landing-batching guidance,
test count) reproduced against the current tree or this session's own
firsthand experience of the mechanism, with one path (the retired,
untracked test file) reachable only at its historical commit rather than
the working tree, as noted above.

## Upstream basis

- `fix/2135-session-context-diet` (PR #2143), merge commit
  `44eef203fc2358c1d6f7ad16ca90f31fe2ab7982` — the subject of this
  verification.
- `directive_assembly.py` (current `main`, post issue-2207 extract) —
  where `write_record_skeleton()` and `composition_breakdown()` now live,
  sha: same-commit (read at HEAD, not modified by this record).
- `.on-the-record/directive/completion-and-landing.md`,
  `.on-the-record/directive/skill-obligations.md` — this session's own
  materialized workspace section files, sha: same-commit (read at HEAD,
  not modified by this record).
- `docs/handbooks/observer-verification.md`, sha: same-commit (read at
  HEAD, not modified) — governs the `verifies_subject: true`
  self-declaration and count mechanism used to close out this record.

## Open findings

1. canonical: PR #2143's own body — "Honest verdict: the issue's ≤25K /
   ≥30%-cost-cut acceptance is NOT met" — names the dominant remaining
   lever (per-turn UserPromptSubmit re-injections, ~11K/turn, living in
   tokenmaxxxer-core) as out of this repo's scope. canonical: `gh issue
   view 2135 --repo tokenmaxxxer/on-the-record --comments` (this session)
   shows a 2026-08-28 triage comment stating the tokenmaxxxer-core#278
   follow-up is closed, and a most-recent comment (2026-08-30) reporting
   PR #2825 opened from branch
   `issue-2135/diagnose-first+technical-writing-minimalism-scoping-5676d1d0`
   whose own title states standing context is now 44,840 tokens — still
   over the ≤25K target. This is not a defect in what PR #2143 shipped
   (it shipped and disclosed exactly what it measured, honestly, in its
   own body); it means issue #2135's own acceptance bar is not yet met
   by the commits landed so far. Resolution path: PR #2825 (open at
   audit time) is the in-flight vehicle for closing this gap, not this
   verification record.
2. The plugin's own pytest suite (including the now-untracked
   `test_directive_diet_2135.py`) was retired by a later, unrelated
   commit — canonical: `git show a555e169 --stat` (this session) shows
   commit message "issue-2525: retire the plugin's own test suite
   (#2528)", deleting `tests/*.py` repo-wide. Resolution path: none
   needed — this is a standing operator decision
   (record-is-the-regression-suite) applied repo-wide after PR #2143
   landed; it does not indicate a regression in PR #2143's mechanism,
   which this record corroborates via live, currently-running artifacts
   instead (see "What was done" above).

## Next steps

None required from this record. canonical: this record's own frontmatter
(`loop_state: complete`, `verifies_subject: true`) is the terminal state
for this independent-verification slot; the underlying issue #2135
remains open pending PR #2825's re-measurement resolving Open finding 1
above, which is outside this verification's scope.

skill-verdict: work-in-english — applied: invoked; this record, its
commit message, and the PR title/body are written in English per policy
(Korean-language session, repo-bound artifacts); the final user-facing
turn summary is written in Korean.
