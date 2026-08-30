---
proposal: none (build-now bypass, CORE_BUILD_NOW=1)
---

# Hunt record — per-file-timeout-ship

## before-landing — stance 0: assume the gate/hook just touched is bypassable -- find the bypass

Verdict: FINDING — a `file_path` containing a `..` segment that textually matches the bash fast path's `*/docs/*` glob (e.g. `docs/../on-the-record/hooks/foo.py`) makes the hook silently skip ALL lint/test checks for a real, non-docs code file, because bash's `case` match runs on the raw un-normalized path and exits the whole hook (`trap - EXIT; exit 0`) before python3 — which is where the only normpath-aware, authoritative re-check lives — is ever invoked.
Kind: silent-failure
Seed: on-the-record/hooks/lint-test-on-edit.sh (new PostToolUse hook), on-the-record/hooks/otr_lint_test_timeout_plugin.py, tests/test_spawn_gate_wiring.py, on-the-record/hooks/hooks.json (4 files, ~879 lines added, staged)
cap_seconds: 180
tier: full (forced by hooks/ path rule, per warrant protocol)
diff_stat_lines: 879
started_at: 2026-08-30T00:00:00Z
ended_at: 2026-08-30T00:20:00Z

### Reproduce
```bash
cd on-the-record/hooks
# a real code file with a syntax error
printf 'def broken(:\n    pass\n' > _bypass_target.py

# 1) baseline: direct (non-tricky) file_path correctly flags the syntax error
python3 -c "import json; print(json.dumps({'tool_name':'Write','tool_input':{'file_path':'on-the-record/hooks/_bypass_target.py','content':'x'},'cwd':'<repo-root>'}))" > /tmp/payload_direct.json
bash lint-test-on-edit.sh post < /tmp/payload_direct.json
# -> emits additionalContext with "lint failed ... SyntaxError: invalid syntax"

# 2) same target file, file_path shaped with a docs/.. traversal segment
python3 -c "import json; print(json.dumps({'tool_name':'Write','tool_input':{'file_path':'docs/../on-the-record/hooks/_bypass_target.py','content':'x'},'cwd':'<repo-root>'}))" > /tmp/payload_bypass.json
bash lint-test-on-edit.sh post < /tmp/payload_bypass.json
echo "EXIT: $?"

rm _bypass_target.py
```

### Observed
Case 2 prints nothing (no `hookSpecificOutput`/`additionalContext` at all) and exits 0 — identical to a genuine docs-only skip. Confirmed the bash `case` glob is what fires, on the raw (pre-normalization) path:
```
$ bash -c 'case "docs/../on-the-record/hooks/_bypass_target.py" in docs/*|*/docs/*|*.md|*.txt|*.rst) echo MATCH;; *) echo NOMATCH;; esac'
MATCH
```
And confirmed python's own `posixpath.normpath` (used further down in the same hook's authoritative python body, which is never reached) resolves this to a plainly non-docs path:
```
$ python3 -c "import posixpath; print(posixpath.normpath('docs/../on-the-record/hooks/_bypass_target.py'))"
on-the-record/hooks/_bypass_target.py
```
So the file actually being edited is a normal `.py` file under `on-the-record/hooks/`, with a real syntax error, and the hook reports nothing.

### Expected
The docs-only fast path's stated purpose (per the hook's own header comment) is "zero added latency" for the empty state of *actually* docs-only edits, with the python body doing "the real, authoritative parse" for every path the bash fast path doesn't catch. A `file_path` that only superficially contains `/docs/` as a substring via a `..` traversal segment is not a docs-only edit — `posixpath.normpath` (already used by the python body two lines later) shows it resolves to a normal code file. The hook should either normalize the path before the bash glob check, or make the python re-check something the bash fast path cannot bypass entirely (e.g. never `exit 0` from bash alone without at least confirming no `..`/`.` segment is present). As shipped, this file_path shape defeats the lint + impacted-test-selection entirely and silently, for any code file whose path can be dressed with a `docs/..` prefix.

### Fix applied
Fixed in `on-the-record/hooks/lint-test-on-edit.sh` before landing: the bash `case` statement now has a leading `*..*)` arm that falls through to python's authoritative `posixpath.normpath` check instead of fast-path-exiting, for any raw guess containing `..`. Re-ran the exact repro above post-fix: case 2 now correctly emits `additionalContext` with `lint failed ... SyntaxError: invalid syntax`, matching case 1. Regression test added: `tests/test_spawn_gate_wiring.py::DocsOnlyEmptyState::test_dotdot_traversal_does_not_fool_the_docs_fast_path`.
