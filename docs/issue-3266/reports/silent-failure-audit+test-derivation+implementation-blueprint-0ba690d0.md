---
issue: 3266
role: silent-failure-audit+test-derivation+implementation-blueprint-0ba690d0
author: silent-failure-audit+test-derivation+implementation-blueprint-0ba690d0
skills: silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: done
upstream:
  - path: lifecycle.py (_workspace_untracked_not_ignored, _workspace_clean_state)
    sha: bac2cef31c19680578dcec807ebaef43a20cb820
---

# issue-3266 — silent-failure-audit+test-derivation+implementation-blueprint-0ba690d0 record

acceptance: `python3 -m pytest tests/test_issue_3266_reclaimable_stub.py -q` — result:
```
4 passed in 0.88s
```
acceptance: `python3 -m pytest test/test_workspace_dirty_classification.py -q` — result:
```
12 passed in 0.87s
```

## What was done

Built directly under the build-now bypass (`CORE_BUILD_NOW=1`, contract v3
s19a) — no separate phase-1 proposal round.

- `lifecycle.py` (commit `bac2cef3`): added three helpers ahead of
  `_workspace_untracked_not_ignored()` —
  - `_is_harness_scaffolding_path(rel)`: any path under `.on-the-record/`
    is harness-owned, never session work.
  - `_report_stub_has_no_content(w, rel)`: for a path matching
    `^docs/issue-\d+/reports/.*\.md$`, strips YAML frontmatter, markdown
    ATX headings, HTML comments (`<!-- fill: ... -->`), and the skeleton's
    literal default `None.` line; returns True only if nothing real is
    left.
  - `_is_reclaimable_untracked_noise(w, rel_bytes)`: the OR of the two
    above, called from `_workspace_untracked_not_ignored()`'s return so
    both `roster_clean()` and `auto_sweep()` pick up the fix through the
    one predicate they already share.
- `spawn.py` (commit `bac2cef3`): re-exported the three new names,
  matching every other lifecycle-extraction re-export already in that
  block.
- `tests/test_issue_3266_reclaimable_stub.py` — the acceptance's two
  `check:` cases plus its two `must not:` guards, run against
  `spawn._workspace_clean_state()`:
  reclaimable (scaffolding + empty stub, nothing else, pushed), never
  reclaimed (real report body), unpushed-commit-still-dirty even with
  scaffolding+stub present, and the squash-merge/stale-remote-tracking
  case still resolving to safe through the untouched `git fetch --all`
  recheck.
  derived: `python3 -m pytest tests/test_issue_3266_reclaimable_stub.py -v 2>&1 | grep -c PASSED`
  ```
  4
  ```
- `test/test_workspace_dirty_classification.py` — unit-level coverage of
  the two new predicates (nested `.on-the-record/` paths, unrelated
  dotfiles, a one-line consult-log entry that must NOT read as an empty
  stub, a non-`reports/` path that must never match, a missing file) plus
  3 end-to-end `_workspace_clean_state()` cases, including a
  stub-plus-unrelated-artifact workspace that must stay dirty.
  derived: `python3 -m pytest test/test_workspace_dirty_classification.py -v 2>&1 | grep -c PASSED`
  ```
  12
  ```
- `scripts/preflight/consumer_preconditions.py` (commit `bac2cef3`): fixed
  7 line-number citations that `tests/test_issue_3182_citation_line_accuracy.py`
  caught as stale after the `spawn.py` re-export block gained 3 lines.
  acceptance: `python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q` — result:
  ```
  10 passed in 0.90s
  ```

acceptance: `python3 -m pytest -q` — result (tail):
```
FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
FAILED on-the-record/checks/test_macos_bash32_compat.py -- MacosBash32CompatTest.test_current_head_is_clean
2 failed, 1563 passed, 3 xfailed, 2 warnings in 47.18s
```
Both failures reproduce identically with this session's edits stashed out:
derived: `git stash && python3 -m pytest harness/fixture-operator-experience/test_flow.py -q on-the-record/checks/test_macos_bash32_compat.py -q; git stash pop`
```
FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
FAILED on-the-record/checks/test_macos_bash32_compat.py -- MacosBash32CompatTest.test_current_head_is_clean
2 failed in 0.87s
```
— confirming both are pre-existing and unrelated to this change, satisfying the acceptance's third `must not:` (no new failures relative to `main`).

## Why

**What "unpreserved work" means now, precisely:** an untracked,
non-gitignored file counts as work-to-lose unless it is (a) anything
under `.on-the-record/` — the harness plants this at spawn time
(`role.json`, `model-routing.json`, `directive/*.md`, etc.) — or (b) a
`docs/issue-<n>/reports/**/*.md` file whose body, after stripping
frontmatter/headings/comments/the skeleton's `None.` default, is empty.
Everything else — a report with even one real sentence, a one-line
consult-log entry, an unrelated untracked artifact (e.g. an experiment's
`manifest.json`) — still counts, unchanged.

**Why check-ignore-passing status wasn't enough on its own (the seam the
issue names, `lifecycle.py:_workspace_untracked_not_ignored()`):**
`.gitignore` already filters build noise per-repo; the two new predicates
catch what gitignore structurally cannot know about — scaffolding the
harness writes independent of any repo's `.gitignore` content, and a
*content* judgment (stub vs. filled) that no path-based ignore rule can
express.

**Why the report-stub check is content-based and path-scoped to
`reports/`, not name- or size-based:** a size/line-count heuristic breaks
the moment the skeleton template gains or loses a line — two still-live,
unfilled stubs on this machine from the same skill family, one with the
current skeleton's `## What did not work` section and one without it:
derived: `wc -l ~/.tokenmaxxxer/work/on-the-record-issue-3245-experiment-trust+silent-failure-audit+implementation-blueprint-3edbb1a6/docs/issue-3245/reports/experiment-trust+silent-failure-audit+implementation-blueprint-3edbb1a6.md ~/.tokenmaxxxer/salvage-20260903/on-the-record-issue-2919-refactoring-legacy-seam-selection-8b6d2268/docs/issue-2919/reports/refactoring-legacy-seam-selection-8b6d2268.md`
```
 40 .../-3edbb1a6/docs/issue-3245/reports/experiment-trust+...-3edbb1a6.md
 36 .../on-the-record-issue-2919-.../refactoring-legacy-seam-selection-8b6d2268.md
```
Stripping frontmatter + headings + HTML comments + the literal `None.`
default and checking what's left is robust to that churn — both files
classify as content-free stubs under `_report_stub_has_no_content()`
despite the 4-line skeleton drift between them.

**Corpus validation** (`~/.tokenmaxxxer/salvage-20260903`, the 2026-09-03
manual-cleanup salvage the issue points at as the shape source — read
only while deriving the fixtures, not from test code, per the issue's own
instruction that this path is machine-local and absent in CI):
derived: a script applying the same strip-frontmatter/strip-headings/strip-comments/strip-`None.` rule as `_report_stub_has_no_content()` across `find ~/.tokenmaxxxer/salvage-20260903 -iname '*.md' -path '*reports*'`
```
stub: 131 real: 20 total: 151
```
Every short consult-log entry checked by hand classified as real content
under that same rule — none false-positived as a stub despite being only
one line, and that shape is now covered directly as
`test_one_line_consult_log_entry_has_content` in
`test/test_workspace_dirty_classification.py`.

**Why not reuse `_classify_workspace_completion()`'s existing
frontmatter-strip check** (`lifecycle.py:363-369`):
```
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                body = text[end + 4:]
        if body.strip():
            return "finished"
    return "unfinished"
```
that check is frontmatter-only strip, no heading/comment removal —
deliberately permissive because its output only decides whether to
prepend a continuation-preamble string to a respawned session's prompt;
over-calling a stub "finished" costs nothing there. Reusing it here would
have called the exact skeleton-only stub in this issue's report
"finished" (it has headings and `<!-- fill -->` comments, so
`body.strip()` is truthy) — i.e. never reclaimable — reproducing the bug
this issue exists to fix. The two functions now intentionally diverge in
strictness because they sit on opposite sides of a decide-to-delete vs.
decide-to-remind line, and scoping the new predicate's path pattern to
`^docs/issue-\d+/reports/.*\.md$` keeps it from ever firing on a
proposal, a code file, or a JSON artifact regardless of that file's
content.

**Must-not preservation, unmodified:** this fix only ever removes entries
from the `not_ignored` list feeding the existing `ahead`
(unpushed-commit) check; it cannot change that computation or the
`git fetch --all`-then-recheck ahead of it, so a workspace with a
genuinely unpushed, unreachable-elsewhere commit stays `dirty` exactly as
before, and the squash-merge/stale-remote-tracking case still resolves
through that same fetch-recheck once the stub/scaffolding noise stops
masking it. Both are exercised directly in
`tests/test_issue_3266_reclaimable_stub.py`, method names
`test_unpushed_commit_with_stub_and_scaffolding_is_never_deleted` and
`test_squash_merged_branch_with_stub_is_reclaimable_after_fetch`; both
pass per the acceptance block above.

**Measured effect on this machine** (this machine's disk had already been
through the manual 2026-09-03 cleanup the issue describes, so it is not
at the 298-workspace/19G state the issue observed):
derived: a script calling `spawn._workspace_untracked_not_ignored()` (old vs. new, old simulated with the new predicates monkeypatched to always-False) and `spawn._workspace_clean_state(..., live={}, unreadable=None)` (old vs. new) over every directory under `~/.tokenmaxxxer/work` containing a `.git` dir
```
live workspaces (git checkouts): 30
untracked-check flips from dirty->clear: 3
untracked-check flips from clear->dirty (should be 0): 0
unchanged: 27
workspaces flipping to reclaimable (dirty->None): 1
    on-the-record-issue-3245-experiment-trust+silent-failure-audit+implementation-blueprint-5a84e9ed
workspaces flipping the other direction (should be 0): 0
```
0 workspaces flipped in the unsafe direction. The other 2 of the 3
untracked-list changes still carry unrelated untracked experiment
artifacts (`_assets/*.json`) that correctly keep them dirty overall. This
machine's current population (already post-cleanup) gives a much smaller
yield than the issue's reported figure, because most of the reclaimable
backlog the issue describes was already removed manually before this
session started; the corpus stub/real split established above is the
more representative measure of the predicate's hit rate against the
population the issue actually observed.

**Skill verdicts** (issue #2039/#2153/#2062):
- skill-verdict: test-derivation — applied: invoked; used to structure the
  test suite as equivalence-partitioned workspace-state scenarios
  (scaffolding-only, stub-only, both, real-content, real-content+
  scaffolding, stub+unrelated-artifact, unpushed-commit, squash-merge/
  stale-ref) — classified this requirement set as Medium depth (user-
  facing-ish infra behavior, not safety-critical numeric thresholds; no
  requirement routes to decision-table/state-transition/pairwise shapes
  since there is one boolean-ish predicate over independent file-shape
  conditions) — GWT scenarios are the unittest methods themselves, one
  per acceptance branch, with explicit boundary cases (one-line-but-real
  content, non-`reports/` path, missing file) rather than full numeric
  BVA since there are no ordered numeric partitions here.
- skill-verdict: implementation-blueprint — applied: invoked; ran
  `scripts/prep.py classify --single-file`, got VETO (single file, single
  concern, no new callers beyond the one existing call site) — honored
  the veto: three flat helper functions in the existing module, no new
  module/class structure introduced.
- skill-verdict: silent-failure-audit — not-applicable: no new
  try/except, Promise-rejection, or error-callback path was added or
  touched; the new predicates are pure boolean classification with no
  fallible I/O beyond `Path.read_text(errors="replace")` guarded by an
  existing `except OSError`.
- other mounted skills: not triggered (work-in-english guidance applied
  throughout without a separate invocation; model-routing/prose-modes
  named by the delayed skill_judge amendment do not appear in this
  session's Skill-tool listing and so could not be invoked).

## What did not work

None.

## Upstream basis

No prior `docs/issue-3266/` proposal or survey exists — build-now bypass
skipped the phase-1 round. Upstream basis is the GitHub issue #3266 body
and the orchestrator's issue comment carrying the revised, runnable
Acceptance section:
canonical: `gh issue view 3266 --repo tokenmaxxxer/on-the-record --json comments -q '.comments[] | .body'` output, second comment, headed "## Acceptance (revised by the orchestrator — the original wording was not runnable)"
plus the pre-existing code seam this fix modifies
(`lifecycle.py:_workspace_untracked_not_ignored`,
`lifecycle.py:_workspace_clean_state`,
`lifecycle.py:_classify_workspace_completion`) and the salvage corpus at
`~/.tokenmaxxxer/salvage-20260903` (read only to derive test fixture
shapes, per the issue's own instruction, not read at test time).

## Open findings

- none. The `.on-the-record/` scaffolding-leak half of the issue's
  observation was not reproducible on this machine's current live
  workspaces before this fix:
  derived: a script running `git ls-files -z --others` + `git check-ignore -z --stdin` over every `.git` checkout under `~/.tokenmaxxxer/work` and grepping the not-ignored results for a `.on-the-record/` prefix
  ```
  0 of 30 workspaces had a .on-the-record/-prefixed path survive check-ignore
  ```
  (this repo's `.gitignore` plus `.git/info/exclude` already caught it
  here). The fix still includes the unconditional path-prefix exclusion
  because the issue explicitly observed it leaking on a different
  (macOS) machine, and the exclusion is unconditionally safe regardless
  of a given workspace's `.gitignore` contents.
- Two pre-existing test failures unrelated to this change (see the
  `git stash` reproduction in "What was done") are left untouched as out
  of this issue's scope.

## Next steps

None.
