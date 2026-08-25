---
proposal: docs/issue-2293/reports/conformance-review.md
---

# Hunt record — conformance-review

## before-landing — stance 0: citation integrity of file:line evidence against PR #2306 head

Verdict: FINDING — REQ-F's evidence cites `760390cc:pipeline.py:2313` for the `ADMISSION_CHECKS` row, but PR #2306 head's `pipeline.py` has only 1588 lines total and never defines `ADMISSION_CHECKS` at all (it lives in `spawn.py:2293`, not `pipeline.py`); REQ-A's own citation for the same row, `spawn.py:2313`, is also off (actual line is `spawn.py:2294`).
Kind: silent-failure
Seed: docs/issue-2293/reports/conformance-review.md, REQ-A and REQ-F evidence lines, checked against PR #2306 head 760390cceaa1b4aeac018460a08a39d1076f614b (`git fetch origin pull/2306/head`)
cap_seconds: unspecified (dispatcher default)
tier: default
diff_stat_lines: docs-only, single new file (conformance-review.md, ~575 lines)
started_at: 2026-08-25T14:10:00+09:00
ended_at: 2026-08-25T14:35:00+09:00

### Reproduce
```
git fetch origin pull/2306/head:pr-2306-check
git show pr-2306-check:pipeline.py | wc -l
git show pr-2306-check:pipeline.py | grep -n "^ADMISSION_CHECKS"; echo "exit: $?"
git show pr-2306-check:spawn.py | grep -n "^ADMISSION_CHECKS"
```

### Observed
```
$ git show pr-2306-check:pipeline.py | wc -l
1588
$ git show pr-2306-check:pipeline.py | grep -n "^ADMISSION_CHECKS"; echo "exit: $?"
exit: 1
$ git show pr-2306-check:spawn.py | grep -n "^ADMISSION_CHECKS"
2293:ADMISSION_CHECKS: list[tuple] = [
```
`pipeline.py` at the PR head is only 1588 lines long and contains no
`ADMISSION_CHECKS` definition anywhere, so the record's REQ-F citation
`760390cc:pipeline.py:2313 (ADMISSION_CHECKS row, ...)` points past the
end of the wrong file. The actual `ADMISSION_CHECKS` list lives in
`spawn.py:2293`. REQ-A's separate citation for the same row,
`spawn.py:2313`, is also wrong by 19 lines — line 2313 in `spawn.py` at
the PR head falls inside the unrelated `drive()` docstring
(`main() 과 drive() 가 같은 몸통을 쓴다 ...`), not the
`ADMISSION_CHECKS` row.

### Expected
Both citations should resolve to `spawn.py:2293-2294`
(`ADMISSION_CHECKS: list[tuple] = [` / `("degenerate-task",
_admission_check_degenerate_task),`) — the record's REQ-F verdict
(Present) and rationale ("neither new code path is gated behind a
consumer identity...") may still be correct in substance, but the cited
evidence does not back it: one citation names a file that doesn't
contain the cited construct at that line (and is shorter than the line
number itself), the other names a different, wrong line in the correct
file. Per `roles/specs/conformance-review.spec.json`'s
`reference_resolution` rule, evidence citations must resolve to a real
repo path/line; these do not.
