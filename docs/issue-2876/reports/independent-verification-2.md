---
issue: 2876
role: independent-verification-2
author: independent-verification-2
verifies_subject: true  # this record is an independent verification of PR #2881 (issue-2876/silent-failure-audit-133bcbf6)
code_under_review: gates/retirement_count.py, gates/retirement_count.sh, gates/flows.py, gates/patrol_board.py, on-the-record/hooks/plan-order-guard.sh, test/test_convention_equivalence.py, test/test_retirement_count.py, docs/specs/enforcement-boundary.md
type: verification-record
breaking: false
verdict: PASS-with-one-inaccurate-narrative-claim — the corrected checker, its plural/case/snake_case coverage, the fix-forward renames, the no-compat-alias rule, the docs/ boundary, and the no-new-bug test-set identity all independently reproduced; one specific sub-claim in the implementation record ("all 16 pre-existing failures share one fetch-related cause") is false, though the acceptance criterion it sits inside (failing-test-NAME sets identical to origin/main) reproduced correctly
loop_state: landed
upstream:
  - path: docs/issue-2876/reports/silent-failure-audit-133bcbf6.md
    sha: 6b7d78df2425e745381d7ffa29329d5a8daa304c
---

# issue-2876 — independent-verification-2 record

## What was done

canonical: `gh issue view 2876 --comments` (read this session, before starting).

Independent verification of PR #2881 (`issue-2876/silent-failure-audit-133bcbf6` → `main`, `Closes #2876`), the fix for the `\brole\b`/`\broles\b` plural blind spot in the retirement-invariant check. Checked out both `origin/issue-2876/silent-failure-audit-133bcbf6` (commit `ed92f411`) and `origin/main` (commit `d514d2c7`) into separate scratch worktrees (`/tmp/verify-2876`, `/tmp/verify-2876-main`, both removed with `git worktree remove --force` at the end of this session) and re-ran the PR's key claims from scratch rather than trusting its record, per `defect-verification-independence-from-upstream-verdicts`. Note throughout: `gates/retirement_count.py` and `gates/retirement_count.sh` are new files added by this PR — untracked on `main` and on this verification branch (`issue-2876/independent-verification-2`), present only in the `/tmp/verify-2876` PR-branch worktree (or copied from there, as stated below).

Reproduced independently, this session:

- **Old vs. corrected count on the PR branch.** In the `/tmp/verify-2876` worktree: `git ls-files "*.py" "*.sh" | grep -v '^docs/' | xargs grep -c '\brole\b' | awk -F: '{s+=$2} END{print s}'` → `985`. `bash gates/retirement_count.sh 2>&1 >/dev/null | tail -1` (the PR-branch-only checker cited above) → `retirement_count: 1179 occurrence(s)`. Both exactly match the PR record's Part-4 numbers.
- **The tokenizer's own unit tests.** `python3 -m pytest test/test_retirement_count.py -q` (also a PR-branch-only file, same as the checker itself) → `10 passed`, matching the record.
- **Scratch-branch plural-injection demonstration, re-run from scratch (not trusting the PR's own worktree-cleanup claim).** Added `ACTIVE_KINDS = ["roles"]` as `probe_2876.py` in the PR-branch worktree, `git add`ed it: `grep -c '\brole\b' probe_2876.py` → `0` (old check blind). Re-ran the PR-branch-only checker → `1180` (baseline `1179` + 1). Removed the file and unstaged it → back to `1179`. Confirms the +1/−1 exactness the PR claims, independently.
- **Delta reproduced against `main` (pre-fix) directly**, not just cited from the PR record: copied the two PR-branch-only checker files (untracked on `main`, per the note above) into the `main` worktree and ran the checker there → `1192`. Old case-insensitive `\brole\b` line-count on the same pre-fix tree (`git ls-files "*.py" "*.sh" | grep -v '^docs/' | xargs grep -in '\brole\b' | wc -l`) → `975`. derived: `1192 − 975 = 217`, matching the PR record's Part-2 delta count of 217 independently, from a different old-check invocation (case-insensitive line count vs. the record's own `comm`-based method) landing on the same number.
- **No compatibility alias.** `grep -rn '\.get(.roles.\|\.get("roles"' gates/flows.py gates/patrol_board.py on-the-record/hooks/plan-order-guard.sh` → 0 hits (plain-subscript reads only, as claimed). Repo-wide `grep -rln '\["roles"\]' --include=*.py --include=*.sh . | grep -v '^\./docs/'` found exactly one file beyond the PR's own new test fixture: `gates/model_routing.py:21` — read it directly, it is a Korean comment narrating already-removed code (`role in tier["roles"]` membership test deleted by issue #2631), not a live reader of `flows.py`'s renamed key. No straggler reader found.
- **`docs/` boundary.** `git diff --stat 1aeecaf8..HEAD -- docs/` shows only the PR's own new `docs/issue-2876/reports/` files, one new row in `docs/reports/product/priorities/`, and the one claimed row in `docs/specs/enforcement-boundary.md` — no historical record touched. Independently confirmed `on-the-record/hooks/gate-registration-guard.sh` exists in the tree (backs the claimed reason for that one `docs/specs/` row), and that `gates/flows.py`'s `_plan_from_body`/`flows_payload` write only into an in-memory dict (`plan_by_issue[n] = ...`, gates/flows.py:340), never to a file — supports the "no on-disk data to migrate" claim for the flows.py rename sites.
- **No-new-bug acceptance criterion, re-run from scratch on both trees, not diffed against the PR's own pasted output.** `python3 -m pytest . -q` on the PR-branch worktree → `16 failed, 605 passed, 3 xfailed`; on a fresh `origin/main` worktree → `16 failed, 595 passed, 3 xfailed`. Extracted both `FAILED ...` line sets with `grep '^FAILED' | sort`, diffed them with plain `diff`: byte-identical, 16 lines on each side (derived: `wc -l /tmp/main_failed.txt /tmp/pr_failed.txt` → `16` / `16`), empty diff. This independently confirms the acceptance criterion ("failing-test-name sets identical to origin/main baseline").
- **Historical-citation spot check.** Grepped 4 of the record's "dead symbol, comment-only" examples (derived: `grep -rn "<symbol>" --include=*.py --include=*.sh . | grep -v '^\./docs/'` for each of `role_settings`, `resolve_role_family_source`, `_ROLE_SKILLS`, `_exempt_own_role`) repo-wide outside `docs/`: every hit found (in `pipeline.py`, `consult.py`, `skills.py`, `spawn.py`, `gates/merge_gate.py`, several `test/*.py`) is inside a Korean/English comment or docstring — no live definition or call site. Confirms this sample of the 128-site historical-citation bucket.
- **Pre-existing baseline claims.** `python3 gates/spec_index.py --update` on the `main` worktree independently reproduces the same `FileNotFoundError: .../roles/specs/brand-design.spec.json` the PR record cites as pre-existing and out of scope. `git blame -L 36,36 gates/gates.py` on the PR branch → `f4a2221f0` (2026-07-25), matching the record's claim that `PROTECTED_ROOT_DIRS`'s `"roles"` entry predates both flagged retirement commits.

## Why

Chose to re-derive rather than re-read: this PR's own record is unusually dense with `derived:`/`canonical:` tags, which makes it easy to *cite* without *checking*. Per `defect-verification-independence-from-upstream-verdicts`, an independent-verification session's value is in re-running the commands itself in a separate worktree, not in confirming the record's prose reads consistently. Picked the highest-leverage claims to re-run from scratch (the two headline counts, the scratch-branch demo, the no-compat-alias rule, the docs/ boundary, and the no-new-bug test identity) rather than every one of the 217 per-site dispositions, and additionally sampled the claim that looked most likely to be an unearned assumption on inspection: the "all 16 fail with the same fetch error" sentence reads like a generalization dressed as a finding — nothing in the surrounding `derived:` block actually ties each of the 16 to that specific error string, only to the byte-identical *name* sets.

Sampling that claim paid off: it is false. Ran 3 of the 16 pre-existing failing tests individually and read their actual tracebacks — none show `fetch 실패` or any git-remote error. They fail for three unrelated reasons: a BM25 cross-family-skill-matching assertion (`test_family_skill_never_returned_as_cross_family_candidate`), a golden-text mismatch against a hook file's actual current contents (`test_hook_file_exists_and_has_expected_shape`), and a missing source string (`test_origin_captured_before_workspace_reassignment`). This is a specific, falsifiable claim in the PR's implementation record that does not hold — the *broader* acceptance criterion it's attached to (failing-test-NAME sets identical between `main` and the PR branch) is true and reproduced independently above, so this does not change the overall PASS verdict, but the record overstates what it verified: "compared this session by reading both `short test summary info` blocks in full" establishes name-set identity, not a shared root cause, and the record asserts the latter as if it too were checked.

## What did not work

None — every independently re-run command reproduced its claimed output on the first attempt; no approach was tried and abandoned this session.

## Upstream basis

- `docs/issue-2876/reports/silent-failure-audit-133bcbf6.md` (untracked on this verification branch — exists on `issue-2876/silent-failure-audit-133bcbf6`; commit `6b7d78df2425e745381d7ffa29329d5a8daa304c` is that branch's first substantive commit, and the record file itself lands at `d1909ff5` on the same branch) — the implementation record under verification.
- PR #2881 (`gh pr view 2881`, `gh pr diff 2881`), read in full this session.
- `origin/main` at `d514d2c7` — the pre-fix baseline used for every independent re-derivation above.

## Open findings

1. **The PR record's "all 16 fail with `fetch 실패`" claim is false** (see Why, above). Not a defect in the delivered code or in the actual acceptance criterion (test-name-set identity, which holds), but a fabricated-sounding specific detail inside an otherwise well-evidenced record — the kind of thing that erodes trust in the surrounding `derived:` tags if it goes unflagged. Resolution path: none needed for this issue's acceptance (the underlying criterion is met); flagging here so a future reader doesn't take the "shared cause" framing as independently established.
2. The 217-site delta's 128/89 historical-citation-vs-live-candidate split was spot-checked (symbols `role_settings`, `resolve_role_family_source`, `_ROLE_SKILLS`, `_exempt_own_role` on the historical side, cross-referenced against `git blame` on the `gates/gates.py:36` pending-migration example, both cited in "What was done" above) but not re-run in full via the record's own `ast`/`tokenize` classifier script — that script's source was not included in the PR diff (only its output is cited in the PR branch's own implementation record), so a full independent re-classification of all 217 lines was not feasible within this session's scope. Resolution path: none required — the samples checked were all consistent with the record's classification, and the two headline counts (985 vs. 1179 on the PR branch, and the 1192−975=217 delta on `main`, both derived per "What was done" above) were reproduced by an independent method rather than by trusting the record's own `comm`-based derivation.

## Next steps

None — `loop_state: landed`. This verification is complete; no further action needed from this role.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-ran the PR's headline claims (counts, scratch-branch demo, no-compat-alias, docs/ boundary, no-new-bug test identity) from scratch in separate worktrees rather than citing the PR record's own `derived:`/`canonical:` tags, which is what surfaced the false "all 16 share one cause" claim that a citation-only pass would have missed.
other mounted skills: not triggered (work-in-english — this response and record are already in English per that skill's standing policy, so no separate invocation was needed to change behavior already being followed).
