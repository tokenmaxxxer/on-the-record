---
issue: 2219
role: execution-observation
loop_state: cleared
upstream:
  - path: gates/record_lint.py
    sha: 56b5b4cebb19e83bddd8a30e032fa23516d91e02
  - path: on-the-record/gates/record_lint.py
    sha: 56b5b4cebb19e83bddd8a30e032fa23516d91e02
subject: PR #2246 (branch issue-2219/implementation, head 56b5b4cebb19e83bddd8a30e032fa23516d91e02)
test: on-the-record/hooks/record-claim-guard.sh (the real deployed hook script, unmodified) run inside a real git worktree at PR #2246's head commit, against the two verbatim record fragments recovered from the session log named in issue #2219's own Acceptance section, with cwd set to that log's own original working tree; plus a self-authored unevidenced-claim control and an empty-record case; python3 -m pytest gates/test_record_lint.py; python3 -m pytest on-the-record/hooks/test_record_claim_guard.py on-the-record/hooks/test_hook_cache_layout.py
result: passed
assertedBy: execution-observation (independent re-extraction from the raw session log and independent re-run through the actual hook in a real worktree at the PR's real head commit, not the implementation session's own pasted fixtures/output)
---

# issue-2219 — execution-observation record

## What was done

Per the defect-verification-independence guidance mapped to this role, this session did not cite PR #2246's own fixture files. It re-derived both verbatim rejections quoted in issue #2219 from the primary source itself, and re-ran the actual deployed hook against a real worktree at PR #2246's real head commit.

### 1. Re-extraction of both verbatim repros from the raw log

canonical: session log named in issue #2219's Acceptance section, parsed this turn with a small script over its JSONL lines, matching each `is_error` `tool_result` back to its `tool_use_id` — result:
```
line 685 tool_result is_error=True <- Write tool_use at line 683 (full-content Write, not an Edit fragment)
line 623 tool_result is_error=True <- Write tool_use at line 622 (full-content Write, not an Edit fragment)
```
Both source Write payloads were saved verbatim to scratch files and used as the actual test fixtures in steps 2-3 below, not a hand-typed reconstruction of them. The log also records the original session's cwd; that same cwd (still present on disk, still a real git repository) was used for every payload below, so the hook's own orphaned-path check resolves against the same tree the original denials came from.

### 2. Live-fire BEFORE, through the real deployed hook, on this branch's unfixed tree

canonical: bash on-the-record/hooks/record-claim-guard.sh, stdin = each fragment's Write-shaped JSON payload with the original session's own cwd, run this turn on this branch (forked from main, which does not carry PR #2246) — result:
```
#870 fragment: rc=2, denial quotes 'acceptance: diff of the two fenced runs above — result: both negative cases read `completed` in both runs, ...' verbatim
#333 fragment: rc=2, denial quotes '`fail-open`, with the full suite still passing 9/9.' verbatim
```
Both fenced denial lines above reproduce issue #2219's two quoted rejections character for character, live, on this branch's own tree, before the fix lands.

### 3. Live-fire AFTER, through the real deployed hook, in a real git worktree at PR #2246's actual head commit

canonical: `git worktree add` pointed at `origin/issue-2219/implementation` (PR #2246's branch), then the worktree's own unmodified `on-the-record/hooks/record-claim-guard.sh`, stdin = the same two payloads as step 2, this turn — result:
```
#870 fragment AFTER: rc=0, no output at all — a full clean pass
#333 fragment AFTER: rc=2, exactly one line, on '"Fixed" section — the first pass at item 2 applied'
```
Placing this fenced AFTER result beside step 2's fenced BEFORE result: both exact verbatim claims quoted in issue #2219 are absent from the AFTER output. The `#870` fragment resolves completely; the `#333` fragment's only AFTER line is a claim the issue never quoted.

canonical: `/tmp/write_622_full.md` lines 183-184 (the source of that remaining line), read this turn — result:
```
line 183: canonical: docs/issue-2208/reports/implementation/2026-08-24-hunt-skill-selection-followups.md
line 184: "Fixed" section — the first pass at item 2 applied ...
```
That `canonical:` tag names a file path, not an executed-live reference (a command, or `acceptance: ... — result:`); `outcome_claim_citation_check`'s own documented scope, unchanged by this fix, requires exactly that distinction, so this residual is expected, not a gap the fix should have closed.

### 4. Genuinely-unevidenced control, self-authored

canonical: same BEFORE/AFTER harness, a short self-authored paragraph carrying a bare count and an outcome claim with nothing else nearby — result:
```
BEFORE: rc=2, all three rules (#333, #793, #870) fire
AFTER:  rc=2, all three rules still fire, and every AFTER denial line ends in a sentence naming a concrete passing shape
```
The fix does not weaken enforcement on this control, and the trailing passing-shape sentence — absent BEFORE, present on every line AFTER — independently satisfies issue #2219's second ask.

### 5. Empty-record acceptance criterion

canonical: same harness, an empty-string Write payload, against the AFTER worktree — result:
```
rc=0, no output
```
Issue #2219's own stated empty-record acceptance line holds on independent re-check.

### 6. Test suites, live, in the same isolated worktree at PR #2246's real head commit

canonical: pytest run inside that same worktree this turn — result:
```
gates/test_record_lint.py: 76 passed in 24.20s
on-the-record/hooks/test_record_claim_guard.py + test_hook_cache_layout.py: 32 passed in 24.46s
```
Both totals match PR #2246's own test-plan checklist, independently re-derived rather than copied.

canonical: `grep -n "def t_.*2219" gates/test_record_lint.py`, same worktree, this turn — result:
```
8 matches: section-scoping, dewrap, fence-exclusion, cross-section-leak, empty-record, unevidenced-still-refused, and passing-shape-message regression pins
```
Real coverage for the claimed scope, not just a claimed count. Both worktrees used in this session were removed after use; no PR #2246 code was checked into or left on this branch.

## Why

Per the defect-verification-independence-from-upstream-verdicts skill mapped to this role: this session re-extracted both verbatim repros from the primary source (the raw session log) itself rather than citing PR #2246's own implementation record's characterization of what those fixtures contained, and re-ran the actual deployed hook script in a real worktree at the PR's real head commit rather than reasoning about the check functions in isolation. See "What did not work" below for why that specific harness choice mattered.

## What did not work

An earlier draft of this record's step 3 ran the hook's embedded Python logic by hand-extracting it into a scratch script and pointing its `RCG_GATES_DIR` at a scratch copy of PR #2246's module, with `cwd` left pointed at this session's own repository instead of the original log session's cwd. That draft reported an orphaned-path `#330` residual surviving on both fragments after the fix, and characterized it as a replay-environment artifact.

canonical: a before-landing warrant hunt dispatched against that draft (recorded separately at docs/issue-2219/reports/execution-observation/2026-08-25-hunt-pr-2246-execution-observation.md), reproducing the real deployed hook directly in a real worktree at PR #2246's head commit — result:
```
the #330 residual did not appear at all; the #870 fragment instead returns a clean rc=0
```
Re-run independently this turn, same method as step 3 above, with the same outcome. The draft's own hand-extracted-script-plus-wrong-cwd harness was the source of the spurious `#330` line, not something about PR #2246's fix.

canonical: correcting `cwd` to the original session's own working tree and running the real, unmodified hook script (rather than a hand-copied fragment of its logic) in a real worktree, this turn — result:
```
the #330 line no longer appears on either fragment
```
The BEFORE and AFTER results in the two sections above are the corrected, re-verified ones.

## Upstream basis

- PR #2246 (branch issue-2219/implementation, head 56b5b4cebb19e83bddd8a30e032fa23516d91e02) — the worktree checked out at that commit is what step 3's AFTER runs and step 6's test suites executed against.
- The session log named in issue #2219's own Acceptance section — re-parsed this session, not re-read from PR #2246's own citation of it, to locate both verbatim repros' true source payloads and their original cwd.
- Issue #2219 body — the two verbatim quotes, and the empty-state and unevidenced-control acceptance criteria this session tested directly.

## Open findings

None blocking.

One boundary named in PR #2246's own record and left unaddressed by design — a citation tag's evidence is invisible to an Edit call when it lives in an untouched part of the file, since the guard only sees the changed fragment for Edit/MultiEdit — is real but out of this issue's evidenced scope: step 1 above establishes both quoted repros were full-content Write calls, not Edit fragments, so neither exercises that gap. Resolution path: a future issue, if an Edit-fragment false rejection is ever quoted verbatim the way #2219's two were.

## Next steps

None — loop_state is terminal (cleared). This record's verdict rests on the live re-runs in steps 2 through 6 above, all executed this turn against real code in a real worktree at PR #2246's actual head commit (not a hand-extracted harness), not on PR #2246's own pasted evidence.
