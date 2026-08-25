---
proposal: docs/issue-2313 (no separate proposals/ doc found in this checkout — hunted directly against the working-tree diff for issue #2313's check_runner.py fix)
---

# Hunt record — compound-check-classification

## after-proposal — stance 1: does `_artifact_touched(cmd, declared)` receiving the full (non-split) `cmd` create an inconsistency now that classification uses the final segment?

Verdict: FINDING — a compound check like `cd frontend && node dist/bundle.js` that touches a declared `runtime-artifacts` path is silently misclassified as `test` instead of `artifact-smoke`, because `parse_checks()` still calls `_artifact_touched(cmd, declared)` with the *full* compound string while every other classification branch in the same loop iteration was switched to `classify_cmd` (the final segment). `artifact_smoke_rule.command_touches_artifact()` only matches when `tokens[0]` (here `"cd"`) is in its closed verb allowlist, so it always returns `None` for any `cd X && <verb> ...` compound command, regardless of what the real (final-segment) command is.
Kind: composition
Seed: gates/check_runner.py diff (issue #2313) — `_final_segment()`/`classify_cmd` introduced for the `test`/`file-existence` branches at parse_checks() lines ~166-198, but the `artifact = _artifact_touched(cmd, declared)` call just above it (line 169) was left unchanged, still passing the untouched full compound string.
cap_seconds: not specified by dispatcher (standalone invocation)
tier: default
diff_stat_lines: 121 insertions(+), 13 deletions(-) across gates/check_runner.py, gates/test_check_runner.py, on-the-record/directive/merge-gates.md
started_at: 2026-08-25T00:00:00Z (approx, standalone session, no dispatcher-supplied timestamp)
ended_at: 2026-08-25T00:20:00Z (approx)

### Reproduce
```
python3 -c "
import sys
sys.path.insert(0, 'gates')
import check_runner

declared = ['dist/bundle.js']

section1 = '\n- check: \`node dist/bundle.js\`\n'
print('non-compound:', check_runner.parse_checks(section1, declared))

section2 = '\n- check: \`cd frontend && node dist/bundle.js\`\n'
print('compound:    ', check_runner.parse_checks(section2, declared))
"
```

### Observed
```
non-compound: [{'type': 'artifact-smoke', 'raw': '`node dist/bundle.js`', 'command': 'node dist/bundle.js', 'artifact': 'dist/bundle.js'}]
compound:     [{'type': 'test', 'raw': '`cd frontend && node dist/bundle.js`', 'command': 'cd frontend && node dist/bundle.js'}]
```
The compound check gets `type: 'test'` and loses the `artifact` field entirely, even though it names the exact same declared artifact via the exact same allowlisted verb (`node`) as the non-compound case that correctly classifies as `artifact-smoke`. This is exactly the compound shape issue #2313's own fix targets (`cd frontend && node scripts/check-hex-tokens.mjs` is the fix's own worked example), so any declared-runtime-artifacts issue whose artifact-smoke check happens to need a `cd` prefix (e.g. a frontend build step) silently loses its artifact-smoke classification post-fix. It still executes and can still PASS/FAIL correctly (run_checks treats `test`/`artifact-smoke` identically for execution), but `gates/check_run_artifact.py`'s `_is_non_hermetic()` keys off `type == "test"` specifically (treating `artifact-smoke` as hermetic/False, `test` as non-hermetic/True), so the misclassification also flips the `non_hermetic` flag recorded in the check-run artifact for this entry — silently, with no error and a full green run.
No existing test in gates/test_check_runner.py covers this: `t_declared_artifact_command_classifies_as_artifact_smoke` only exercises a non-compound command, and none of the four new `#2313` compound tests pass a `runtime_artifacts` declaration.

### Expected
`_artifact_touched()` should be checked against the final segment (`classify_cmd`) for compound commands too — consistent with how `test`/`file-existence` classification was updated — so `cd frontend && node dist/bundle.js` classifies as `artifact-smoke` with `artifact: 'dist/bundle.js'`, exactly like its non-compound equivalent.
