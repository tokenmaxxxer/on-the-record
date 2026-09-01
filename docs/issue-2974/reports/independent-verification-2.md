---
issue: 2974
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
code_under_review: 36b61cf3:gates/check_runner.py, 36b61cf3:gates/merge_gate.py, 36b61cf3:gates/risk_report.py, 36b61cf3:on-the-record/hooks/impact-guard.sh, 36b61cf3:docs/specs/requirements.md, 36b61cf3:docs/specs/requirement-digest.md, 36b61cf3:gates/test_check_runner.py, 36b61cf3:gates/test_risk_report.py
type: verification-record
breaking: false
verdict: claims-confirmed-no-regressions-one-non-blocking-open-finding
loop_state: landed
upstream:
  - path: PR #2994 (issue-2974/merge-gates+test-derivation-98d98713)
    sha: 36b61cf339dce5651f8c94016d4da3c6233e7259
  - path: 36b61cf3:docs/issue-2974/reports/merge-gates+test-derivation-98d98713.md
    sha: 36b61cf339dce5651f8c94016d4da3c6233e7259
skill-verdict: work-in-english — applied: invoked; loaded the SKILL.md via the Skill tool before writing this record. This record, all commands, and the PR text are in English; only the final chat summary to the user is in Korean.
other mounted skills: not triggered — this is a single-PR read-and-reproduce audit (checkout the branch, re-run the four cited acceptance checks plus the full gate suite, verify each `derived:`/`canonical:` claim in the subject's own record), not a multi-module build; freelunch's fan-out threshold (width >= 2 units, ~100+ lines each) did not apply — a single sequential audit thread covers the whole unit faster than splitting it; no other mounted skill's trigger matched.
---

# issue-2974 — independent-verification-2 record

## What was done

canonical: `gh issue view 2974` (full body, three lettered findings A/B/C, Acceptance section) and `gh pr view 2994 --json body,commits,files,additions,deletions` — read in full before checking out the branch.

Fetched PR #2994 (`issue-2974/merge-gates+test-derivation-98d98713`, tip `36b61cf3`) into an isolated `git worktree` (`/tmp/verify-2974`) and independently re-ran every claim in the subject's own record (`36b61cf3:docs/issue-2974/reports/merge-gates+test-derivation-98d98713.md`) from scratch rather than trusting its prose.

### Acceptance checks re-run against PR #2994's head (isolated worktree)

1. derived: `python3 -m pytest gates/ -k record_only_pr_not_scored -q` — result: `2 passed in 0.87s`. Matches the subject's record and PR body.
2. derived: `python3 -m pytest gates/ -k record_signal_disagreement -q` — result: `2 passed in 0.85s`. Matches.
3. derived: `python3 -m pytest gates/ -k batch_merge_unrelated_proposal -q` — result: `4 passed in 0.86s`. Matches.
4. derived: `grep -c "^R[0-9]" docs/specs/requirement-digest.md` — result: `0` (exit 1). Confirmed live — every digest line is bullet-prefixed (`- R001: ...`), so the anchored literal never matches, regardless of R-ID count. The subject's record disclosed this as `unverifiable:` with a documented reason rather than silently claiming pass; independently reproduced the same result.
5. derived: `python3 -m pytest gates/ -q` (full gate suite regression check) — result: `42 passed in 0.93s`. No regressions.
6. derived: `bash -n on-the-record/hooks/impact-guard.sh` — result: exit 0, no output. Shell syntax valid.

### Canon-growth claim (finding A) independently reproduced

derived: `git show 167cc19a:docs/specs/requirement-digest.md | grep -c "R[0-9]"` (base commit, before this PR) — result: `4`. derived: `grep -c "R[0-9]" docs/specs/requirement-digest.md` (PR head) — result: `6`. Confirms the record's before/after canon-growth claim (4 → 6) exactly.

### R005/R006 quotes checked against source issues for fabrication

derived: `gh issue view 1664 --json body -q .body` — the issue body contains, verbatim: "a PR is refused when merging it would delete or overwrite content that exists at the base branch HEAD but was added by a commit the PR's merge-base does NOT contain (i.e. the PR is stale relative to that commit and its merge reverts it)" — exact match to R005's `quote:` in `docs/specs/requirements.md`. CONFIRMED, not fabricated.

derived: `gh issue view 511 --json body -q .body` — the issue body's requirement 3 contains, verbatim: "Dominant-axis rule: no summing/averaging across axes; worst reversibility grade alone forces individual human approval." — exact match to R006's `quote:`. CONFIRMED, not fabricated.

derived: `grep -n "^def classify" gates/stale_revert_guard.py` — result: `89:def classify(...)`. derived: `grep -n "^def classify_axes" gates/risk_report.py` — result: `185:def classify_axes(...)`. Both `check:` targets named by R005/R006 exist and are the functions the digest cites. CONFIRMED.

### Must-not list audited against the diff

- "do not loosen, special-case, or exempt the requirement-ID gate" / "do not add a new blanket escape tag" — canonical: `gh pr diff 2994` (full diff, read in full this session) — the diff touches only `docs/specs/requirements.md` and `docs/specs/requirement-digest.md` (canon growth); no change to the gate that enforces the R-ID citation, no new tag introduced. CONFIRMED not violated.
- "do not decide record-only status from frontmatter alone, and do not decide it from a filename, branch name, or skill name" — canonical: `36b61cf3:gates/check_runner.py` `main()` (read in full this session) — the diff-based `touches_implementation_paths()` signal alone decides `record_only`; `frontmatter_record_only_signal()` only ever populates a `disagreement` flag, never overrides the decision. CONFIRMED by direct code read, corroborated by derived: `python3 -m pytest gates/test_check_runner.py -k record_only_diff_wins_over_implementation_kind -q` — result: `1 passed` (diff says record-only, frontmatter says implementation, diff wins).
- "do not make the check-runner skip scoring for any PR that does touch implementation paths" — derived: `python3 -m pytest gates/test_check_runner.py -k fails_closed_to_scored -q` — result: `1 passed` (`touches_implementation_paths(None) is True` and `touches_implementation_paths([]) is True`, fail-closed to scored on unreadable diff). CONFIRMED.
- "do not weaken the batch-merge approval requirement for proposals a batch genuinely does implicate" — derived: `python3 -m pytest gates/test_risk_report.py -k implicated_proposal_still_blocks -q` — result: `1 passed`; an implicated proposal is still returned by `batch_blocked()`. CONFIRMED.

### merge_gate.py record_only pass-through, manually reproduced end-to-end

The subject's record does not point to a dedicated `gates/`-suite test that exercises `merge_gate.parse_check_runner_result()`/`evaluate()`'s new `record_only` branch (only `check_runner.py`'s `main()` is covered by the three required `-k` filters). Manually reproduced the full round trip live:

derived:
```
python3 -c "
import sys; sys.path.insert(0, 'gates')
import check_runner, merge_gate
comment = check_runner.format_record_only_comment(None, False)
print(merge_gate.parse_check_runner_result(comment))
"
```
result: `{'record_only': True}`

canonical: `36b61cf3:gates/merge_gate.py` `evaluate()` (the `elif result.get("record_only"): pass` branch, read in full this session) — a record-only result adds no refusal reason, while `required_verification_missing()`, `stale_revert_reasons()`, and `staleness_for_pr()` all still run afterward — a record-only PR still has to pass every other gate, it only skips the implementation-acceptance scoring it was never eligible for. CONFIRMED working correctly; logged as an open finding below since it lacks its own committed regression test.

## Why

An independent verification is only worth landing if it could have caught a wrong or unreproducible claim, not if it just echoes the subject's own record — so every `derived:`/`canonical:` claim in the subject's record was re-executed from a fresh worktree checkout rather than re-stated, including the two source-issue quote checks (fabrication is the failure mode this role exists to catch on a quote-sourced canon-growth change) and the must-not-list audit (the issue's consult explicitly rejected loosening the R-ID gate, making a must-not violation the highest-value thing to check independently).

## What did not work

None.

## Upstream basis

PR #2994 (`issue-2974/merge-gates+test-derivation-98d98713`, tip `36b61cf339dce5651f8c94016d4da3c6233e7259`) is the deliverable under review; `sha: same-commit` does not apply since none of the reviewed code lands in this record's own commit — all cited paths carry the real PR tip sha per contract §1.

## Open findings

1. **`merge_gate.py`'s new `record_only` branch (in `parse_check_runner_result()`/`evaluate()`) has no dedicated committed regression test** — canonical: `git -C /tmp/verify-2974 ls-files gates/` (read this session) shows no `gates/test_merge_gate.py`; `test/test_merge_gate_record_kind.py` covers a different concern (record `kind:` frontmatter, not the check-runner-comment marker). The three required `-k` filters (`record_only_pr_not_scored`, `record_signal_disagreement`, `batch_merge_unrelated_proposal`) all target `check_runner.py`/`risk_report.py`; nothing in `gates/` exercises `merge_gate.py`'s consumption of the new `RECORD_ONLY_MARKER`. Manually verified correct end-to-end above (marker round-trips through `parse_check_runner_result()` to `{"record_only": True}`, and `evaluate()`'s handling was confirmed by direct code read), so this is not a functional defect — it is a coverage gap that a future change to `_RESULT_HEADER` or `RECORD_ONLY_MARKER` could silently break without a test catching it. Resolution path: a follow-up test in a new `gates/test_merge_gate.py` asserting `parse_check_runner_result()` returns `{"record_only": True}` for the marker and that `evaluate()` adds no refusal reason for it. Non-blocking — not required by the issue's acceptance criteria, and the behavior it would cover is already confirmed working.

## Next steps

None — loop_state: landed.
