---
proposal: N/A (build-now bypass, CORE_BUILD_NOW=1, contract v3 s19a — no proposal round this session)
---

# Hunt record — execution-observation

## before-landing — stance 2: assume this guard goes silent when its own input is malformed — make it go silent

Verdict: FINDING — record-claim-guard.sh (the write-time hook) never calls record_lint.py's issue-#2331 phantom-citation checks (`citation_line_bounds_check`, `citation_line_content_check`, and also `wc_l_recompute_check`/`pytest_count_recompute_check`), so a record carrying a `file:line` citation that points past the end of the file (or at a wrong line) sails through the Write-time guard silently, even though the post-hoc `python3 -m gates.record_lint` aggregator — which record_lint.py's own module docstring and issue #517's history claim shares "exactly one place each rule's logic lives" with the hook — refuses the identical content.
Kind: silent-failure
Seed: on-the-record/hooks/record-claim-guard.sh (backed by on-the-record/gates/record_lint.py); spot-checked docs/issue-2403/reports/execution-observation.md at commit 3814125c
cap_seconds: 60
tier: default
diff_stat_lines: 20 (docs-only, 1 file: docs/issue-2403/reports/execution-observation.md, 277 insertions)
started_at: 2026-08-25T22:20:00Z
ended_at: 2026-08-25T22:42:00Z

### Reproduce
The already-committed record docs/issue-2403/reports/execution-observation.md
(commit 3814125c) cites `a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5:gates/merge_gate.py:264`
as the line where `evaluate()` supposedly always attaches
`result["staleness"] = ...` — this is criterion-1's cited evidence in that
record's own "Why" section. The current working tree's `gates/merge_gate.py`
(this branch was cut from main before PR #2452 landed) is only 242 lines:

```
$ wc -l gates/merge_gate.py
242 gates/merge_gate.py
```

Replay the exact Write call that produced this record through the write-time
guard (payload built from the committed file's own content, via a helper
script `/tmp/mk_payload.py` that writes
`{"tool_name":"Write","tool_input":{"file_path":"docs/issue-2403/reports/execution-observation.md","content":<the committed file's own text>},"cwd":"<repo root>"}`
to `/tmp/rcg_payload.json` — the exact shape `record-claim-guard.sh`'s GUARD
reads from `RCG_PAYLOAD`):

```
$ python3 -m gates.record_lint docs/issue-2403/reports/execution-observation.md; echo "RECORD_LINT EXIT: $?"
- 레코드가 파일의 실제 줄 수를 넘는 file:line 을 인용한다 (issue #2331): `gates/merge_gate.py:264` — ... 지금 242줄뿐이라 이 인용은 애초에 존재하지 않는 줄을 가리키는 phantom citation 이다 ...
- 레코드가 파일의 실제 줄 수를 넘는 file:line 을 인용한다 (issue #2331): `gates/merge_gate.py:276` — ...
RECORD_LINT EXIT: 1

$ RCG_PAYLOAD="$(cat /tmp/rcg_payload.json)" bash on-the-record/hooks/record-claim-guard.sh < /dev/null; echo "HOOK EXIT: $?"
HOOK EXIT: 0
```

`grep -n "citation_line_bounds_check\|citation_line_content_check\|wc_l_recompute_check\|pytest_count_recompute_check" on-the-record/hooks/record-claim-guard.sh` returns no matches — none of the four issue-#2331 checks record_lint.py's `lint_record()` aggregates are wired into the hook's GUARD script, which only calls `unverifiable_reason_check`, `checked_claim_reason_check`, `bare_count_claim_check`, `canonical_source_claim_check`, `outcome_claim_citation_check`, `orphaned_path_reference_check`, `git_tracked_path_reference_check`, `defect_claim_grounding_check`. The hook's own header comment (lines 12-35) enumerates every check it ports and was never updated when the #2331 checks were added to the shared module.

### Observed
`record-claim-guard.sh` exits 0 (allow) for the exact content that is
currently committed at docs/issue-2403/reports/execution-observation.md,
including its two now-phantom `gates/merge_gate.py:264`/`:276` citations.

### Expected
Given record_lint.py's own stated design goal (module docstring: "so each
rule's logic lives in exactly one place" between the hook and
`gates/ci.py`/the CLI), a citation-bounds/content violation that
`python3 -m gates.record_lint` refuses (exit 1) on this file should also be
refused by the write-time hook that is supposed to catch "the claim shape at
the moment it is typed" (record-claim-guard.sh's own header) — instead the
hook allows it silently, so the phantom citation only surfaces later, if at
all, from a separate manual/CI `record_lint` run nobody is guaranteed to make
before the record lands.

### Resolution

canonical: this section's own "### Reproduce" block above (the
`python3 -m gates.record_lint` and `record-claim-guard.sh` replay
commands and their output), re-run at write time of this section

The two phantom citations this finding reproduced against
`docs/issue-2403/reports/execution-observation.md`'s
`gates/merge_gate.py:264`/`:276` were fixed in this same landing (amended
into commit `88d42ab0`, superseding `3814125c`): a `derived-unverified:`
note was added to that record's "Why" section explaining that its
file:line citations resolve against the PR head commit
`a6ffa970f74e143aebc09a1c5adf7dbc3f1175e5`, not this session's own
pre-merge working-tree checkout of the same paths.

acceptance: python3 -m gates.record_lint docs/issue-2403/reports/execution-observation.md — result:
```
record_lint: docs/issue-2403/reports/execution-observation.md — 위반 없음.
```

The underlying gap this finding actually names —
`on-the-record/hooks/record-claim-guard.sh` not calling `record_lint.py`'s
four issue-#2331 checks (`citation_line_bounds_check`,
`citation_line_content_check`, `wc_l_recompute_check`,
`pytest_count_recompute_check`) — is a tooling defect in this repo's own
hook infrastructure, out of scope for issue #2403's write set (this
role's own record is the only file this session is authorized to touch
under the build-now bypass). Not fixed here; reported as-is for a human
or a future session scoped to `on-the-record/hooks/`/`on-the-record/gates/`
to pick up.
