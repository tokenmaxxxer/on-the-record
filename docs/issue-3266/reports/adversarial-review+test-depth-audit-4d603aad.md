---
issue: 3266
role: adversarial-review+test-depth-audit-4d603aad
author: adversarial-review+test-depth-audit-4d603aad
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true
loop_state: done
upstream:
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/3269
    sha: 9f25370868cff8f7a156457e7510105b2eff30ae
  - path: docs/issue-3266/reports/silent-failure-audit+test-derivation+implementation-blueprint-0ba690d0.md
    sha: same-commit
---

# issue-3266 — adversarial-review+test-depth-audit-4d603aad record

## What was done

Independent re-derivation of every load-bearing claim in PR #3269
(`_is_harness_scaffolding_path()` / `_report_stub_has_no_content()` in
`lifecycle.py`), without trusting the PR's own prose. Checked out
`origin/pull/3269/head` into `/tmp/pr3269-wt` (head
`9f25370868cff8f7a156457e7510105b2eff30ae`) and `main` into
`/tmp/main-wt`, and ran everything myself.

acceptance: `python3 -m pytest tests/test_issue_3266_reclaimable_stub.py -q` (from `/tmp/pr3269-wt`) — result: 4 passed.

acceptance: `python3 -m pytest test/test_workspace_dirty_classification.py -q` (from `/tmp/pr3269-wt`) — result: 12 passed.

Both match the PR's own reported test-plan counts.

acceptance: `python3 -m pytest -q` (from `/tmp/pr3269-wt`, 46.75s) — result: `2 failed, 1563 passed, 3 xfailed`, exact match to the PR's reported full-suite numbers.

derived: `python3 -m pytest -q harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace on-the-record/checks/test_macos_bash32_compat.py` (from `/tmp/main-wt`, `main` branch) — result: both of the same tests fail with the same assertion content on `main` alone, confirming the failures pre-exist and were not introduced by this PR.

Boundary-probed `_report_stub_has_no_content()` directly (imported
`lifecycle` from `/tmp/pr3269-wt`, called the function against
constructed fixtures) across: frontmatter + one real sentence,
frontmatter + heading-only, a one-line consult-log entry, whitespace-only
body, a bullet-point-only body, a blockquote-only body, `None.`
(skeleton default) vs `none.` (lowercase), and content expressed only
inside a markdown heading or a bare line starting with `#`. Found one
real over-deletion gap — see Open findings #1.

Re-derived the corpus-validation number independently against the
salvage directory named in the issue's acceptance text
(`~/.tokenmaxxxer/salvage-20260903` on this machine), rather than
trusting the PR's own reported figure.

derived: `find ~/.tokenmaxxxer/salvage-20260903 -type f -name '*.md' -path '*/reports/*' | wc -l` — result: 151.

derived: ran `_report_stub_has_no_content()` from PR head
`9f25370868cff8f7a156457e7510105b2eff30ae`'s `lifecycle.py` against all
151 of those files (matched against each file's path relative to its own
workspace root) via a script at `/tmp/probe_corpus.py` — result: 131
classified as content-free stub, 20 classified as having content
(131 + 20 = 151). Both figures reproduce the PR's own claim exactly. See
Open findings #3 for a caveat on 5 of the 20.

Ran `python3 spawn.py clean --dry-run` on both `main` and the PR branch,
back to back, against this machine's current live workspaces.

derived: `python3 spawn.py clean --dry-run` (from `/tmp/pr3269-wt`) — result: `정리 끝 — 지움 0, 남김 34`.

derived: `python3 spawn.py clean --dry-run` (from `/tmp/main-wt`) — result: `정리 끝 — 지움 0, 남김 34`.

Both runs enumerate the identical set of workspace paths (captured back
to back in the same turn), so the per-workspace diff in Open findings #4
compares like-for-like. This machine's live workspace count has drifted
since the orchestrator's own most recent issue comment (see Upstream
basis) — the qualitative comparison in finding #4 is unaffected by that
drift since both of my own runs used the same snapshot.

derived: `gh pr diff 3269 --repo tokenmaxxxer/on-the-record` — result:
the `git fetch --all`-then-recheck block inside `_workspace_clean_state()`
is absent from the diff entirely — the PR's new filtering happens
earlier, inside `_workspace_untracked_not_ignored()`, and only changes
which files feed the `not_ignored` list that the existing `ahead`/fetch
logic already consumes downstream.

Checked the PR's own trailer against the orchestrator's most recent
issue comment for consistency — see Open findings #2.

## Why

The task asked for re-derivation, not trust in the PR's prose, and
asked this session to tell apart a fix whose real-world effect is small
because its target cause is small on this machine, from a classifier
that plain does not fire on the shape it was built for. Every one of the
four judgment axes in the task (over-deletion, under-deletion, the two
must-nots, and the scope question) is falsifiable by running code
directly against the PR's own checked-out branch, so that is what this
session did for all four, plus checked the PR's `Closes` trailer against
the orchestrator's own most recent comment since that comment postdates
the PR's last update.

## What did not work

None.

## Upstream basis

- PR #3269 (branch `pr-3269-review`, head
  `9f25370868cff8f7a156457e7510105b2eff30ae`) — the code under review.
- Issue #3266 — canonical: `gh issue view 3266 --repo tokenmaxxxer/on-the-record --comments` (includes the orchestrator's revised-acceptance comment and its post-PR "fix is sound, problem is not solved" comment, both read in full this turn — the latter reports its own re-measurement as `정리 끝 — 지움 1, 남김 32` on the PR branch vs `정리 끝 — 지움 0, 남김 32` on `main`).
- The salvage directory named in the issue's acceptance text, read directly on this machine.

## Open findings

1. **Over-deletion gap, narrow but real (not yet fixed).**
   `_report_stub_has_no_content()` treats *any* line whose stripped form
   starts with `#` as skippable heading noise, not only genuine ATX
   markdown headings — quoted verbatim from
   `9f25370868cff8f7a156457e7510105b2eff30ae:lifecycle.py:876-881`:

   ```python
   text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
   for line in text.splitlines():
       s = line.strip()
       if not s or s.startswith("#") or s == "None.":
           continue
       return False
   return True
   ```

   derived: probed directly against the PR branch's
   `lifecycle._report_stub_has_no_content()` via a script at
   `/tmp/probe_stub2.py` run from `/tmp/pr3269-wt` — result:
   - A report whose only body line is a sub-heading carrying the actual
     finding (`### Root cause: retry loop lacked backoff, saturating one
     core under sustained 503s`, nothing else) classifies as
     `no_content=True` (stub). The finding is real prose; it is only
     lost because it sits after `###` rather than as a plain paragraph.
   - A bare line starting with `#` that is not a heading at all (e.g.
     `#3266 was the root cause, confirmed via bisect against commit
     abc123.`) also classifies as `no_content=True`.

   derived: control probe, same script family (`/tmp/probe_stub.py`) —
   result: frontmatter + one plain sentence (`Fixed the retry loop.`)
   classifies as `no_content=False`; a bullet-point-only body and a
   blockquote-only body both classify as `no_content=False`.

   Severity calibration — derived: ran the same function against every
   git-tracked file matching `docs/issue-\d+/reports/.*\.md$` in this
   repo's own history via `/tmp/probe_real_reports.py`
   (`git -C /tmp/pr3269-wt ls-files docs`) — result: found tracked
   report files (count derived: `git -C /tmp/pr3269-wt ls-files docs | grep -cE '^docs/issue-[0-9]+/reports/.*\.md$'` = 3073), of which 0 misclassified as content-free stubs.
   So this shape does not appear to occur in this repo's actual
   report-writing style to date, and is not present in the acceptance's
   own salvage corpus either — the 20 non-stub corpus files from the
   "What was done" corpus re-derivation were inspected directly and none
   rely on heading-only content. It is a real latent gap on the
   dangerous (over-deletion) side, triggerable only when a session's
   entire substantive content for a report happens to live in heading
   text (or a `#`-prefixed line) with that file being the workspace's
   only untracked item and no other blocker present — narrow, but not
   theoretical, since it requires no adversarial input, just a terse
   writing style this same harness's own `terse` skill actively
   encourages. Resolution path: tighten the skip condition so a
   heading's own text is not treated as disposable content, and add a
   regression test for the "content only in a sub-heading" shape before
   this ships. derived: read both new test files in full via
   `gh pr diff 3269 --repo tokenmaxxxer/on-the-record`; confirmed no
   test case in either file constructs a heading-only or bare-`#`-line
   body.

2. **PR's `Closes #3266` trailer is stale against the orchestrator's own
   most recent comment (not yet fixed).**

   canonical: `gh pr view 3269 --repo tokenmaxxxer/on-the-record --json body -q .body` — result: body still ends with a bare `Closes #3266` line.

   canonical: `gh pr view 3269 --repo tokenmaxxxer/on-the-record --json createdAt,updatedAt` — result: `createdAt: 2026-09-03T04:35:19Z`, `updatedAt: 2026-09-03T04:41:34Z`.

   canonical: `gh issue view 3266 --repo tokenmaxxxer/on-the-record --json comments -q '.comments[-1].createdAt'` — result: `2026-09-03T04:42:24Z` for the orchestrator's "the fix is sound and the problem is not solved... it does not close #3266" comment.

   That comment postdates the PR's last update, and the PR body was not
   seen to change afterward. If this PR merges with `Closes #3266`
   intact, the issue auto-closes on merge, directly contradicting the
   orchestrator's explicit instruction that it "stays open for the
   remaining causes." Per this repo's own PR-trailer convention for
   intentional partial delivery (`Advances #<n>` / `Part of #<n>`
   instead of `Closes #<n>`), this trailer should be corrected before
   merge. This is a metadata fix, not a code change, and does not
   implicate the correctness of `lifecycle.py`'s logic.

3. **Corpus-validation denominator overstates exercised coverage by a
   handful of files (informational, not a defect).** derived:
   cross-referenced the 151-file list from the "What was done" corpus
   re-derivation against `_REPORT_STUB_PATH_RE`
   (`^docs/issue-\d+/reports/.*\.md$`) via
   `find ~/.tokenmaxxxer/salvage-20260903 -type f -name '*.md' -path '*/reports/*' | grep -vE 'docs/issue-[0-9]'` — result: 5 matches, all
   sitting at a `reports/` path with no `issue-<n>/` segment above it
   (one example, a consult-log entry under a workspace's own
   `docs/reports/consult-log/` tree). `_report_stub_has_no_content()`
   rejects all 5 by path before any content is read, so they count
   toward the PR's "correctly retains real content" tally without the
   content-parsing logic ever running on them. All 5 were read directly
   this turn and do contain real prose (a consult-log entry, two
   priority-capture notes carrying their own `canonical:` citation
   lines), so no unsafe classification resulted — this is a
   measurement-methodology note about how many distinct content shapes
   the corpus validation actually exercised, not something requiring a
   code change.

4. **Scope question (item 4 of the task) — resolved: narrow cause, not
   a non-firing fix.** derived: diffed the per-workspace
   `[미추적 파일 N건]` counts between the two `spawn.py clean --dry-run`
   runs in "What was done" line by line — result: in the majority of
   workspaces the untracked-file count drops under the PR (concrete
   pairs observed, main→PR: `video_producer-issue-1-...-294fc598`:
   `[미추적 파일 9건]` → `[미추적 파일 1건]`;
   `video_producer-issue-1-...-edd617fe`: `[미추적 파일 8건]` → no
   `[미추적 파일 ...]` clause at all;
   `video_producer-issue-4-...-1fec77e7`: `9건` → `1건`;
   `on-the-record-issue-3245-...-6bb2df31`: `5건` → `4건`;
   `on-the-record-issue-3245-...-a879dc35`: `4건` → `3건`), while
   `[미push 커밋 N건]` remains present in every one of those same
   workspaces in both runs. This means the classification logic is
   visibly firing and correctly stripping scaffolding/stub noise from
   the untracked count, but on this particular machine — already
   hand-cleaned once per the issue's own account of its 2026-09-03
   manual cleanup — an unrelated and unaddressed blocker (unpushed
   commits) co-occurs in nearly every surviving workspace, so the final
   dirty/reclaimable verdict rarely flips end to end. This independently
   confirms the orchestrator's own read from its post-PR issue comment
   (see Upstream basis): the fix is correctly scoped to the
   untracked-stub cause the issue named, and the low real-machine flip
   count reflects that this machine's remaining disk pressure now comes
   from a different, legitimately out-of-scope cause — not evidence
   that the fix under-fires on its own target shape. The issue should
   stay open rather than close on this PR (contingent on finding #2
   being fixed so the trailer matches that intent).

## Next steps

None from this record — it is a read-only independent verification and
does not open a build phase. Findings #1 and #2 are actionable follow-up
for whoever next touches PR #3269 (its own author/session, or a
follow-up issue); this record does not fix them itself, per the task's
explicit "do not edit or merge PR #3269" constraint.

skill-verdict: adversarial-review — applied: invoked; ran the full
independent-verification protocol against PR #3269 — checked out both
branches, re-ran every claimed check myself, and constructed fixtures
the PR's own tests do not cover (heading-only content, bare `#`-line
content) rather than trusting the PR's reported test-plan output.

skill-verdict: test-depth-audit — applied: invoked; classified both new
test files (commit-pinned:
`9f25370868cff8f7a156457e7510105b2eff30ae:tests/test_issue_3266_reclaimable_stub.py`,
`9f25370868cff8f7a156457e7510105b2eff30ae:test/test_workspace_dirty_classification.py`)
as Genuine Assertion throughout — all exercise real git repos and real
filesystem state (no mocks), assert on concrete `(reason, detail)`
tuples and detail substrings, and include one must-not case
(unpushed-commit dominance) and one squash-merge-corollary case that
actually reproduces the false-"ahead" precondition before asserting it
clears. derived: cross-referenced against Open finding #1 above (same
`gh pr diff 3269` read) — neither test file covers the
heading-only-content shape described there, which is exactly the kind of
coverage gap this audit exists to surface.

skill-verdict: work-in-english — applied: invoked; wrote this record,
the commit message, and the PR title/body in English per the skill's
routing rule, and reserved Korean for the end-of-turn summary read by
the user.

other mounted skills: not triggered (implementation-audit, merge-gates,
parallel-decomposition, defect-verification-independence-from-upstream-verdicts
were surfaced by the post-dispatch skill_judge amendment but the Skill
tool did not recognize them by name in this session — read their
SKILL.md directly from the local skill registry instead;
defect-verification-independence-from-upstream-verdicts' guidance
(re-derive rather than cite, include edge/negative cases, treat a
not-reproduced result with the same rigor as a reproduced one) was
followed in substance throughout this record even though the skill
itself could not be invoked through the Skill tool).
