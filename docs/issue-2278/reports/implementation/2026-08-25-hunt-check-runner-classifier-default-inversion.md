---
proposal: docs/issue-2278/reports/implementation.md
---

# Hunt record — check-runner-classifier-default-inversion

## before-landing hunt

Verdict: FINDING — inverting the classifier default from file-existence to judgment removes the mechanical safety net for real extensionless artifact names (e.g. `LICENSE`), letting a genuinely missing declared artifact pass silently instead of hard-failing
Kind: composition
Seed: commit 41be748d (`gates/check_runner.py` `_looks_like_path()`/`_PATH_EXTENSIONS`, `gates/test_check_runner.py` new pins) — build-now, no separate proposal file
cap_seconds: 180
tier: gates-touch-full
diff_stat_lines: 272 insertions(+), 1 deletion(-) across gates/check_runner.py, gates/test_check_runner.py, docs/issue-2278/reports/implementation.md
started_at: 2026-08-25T10:20:00+09:00
ended_at: 2026-08-25T10:38:00+09:00

### Stance 0 — "find the bypass"

Read `gates/check_runner.py` as committed (`_looks_like_path()`, `_PATH_EXTENSIONS`) and `gates/requirement_met.py`'s `_artifact_in_diff_hunk()`/structural-blocking path to see what backs a `judgment`-classified check once check_runner stops mechanically running it.

`_PATH_EXTENSIONS` only recognizes tokens with a `.` in them; a bare filename with no extension and no `/` — a real, common naming convention (`LICENSE`, `Makefile`, `Dockerfile`, `Procfile`, `CHANGELOG`) — now classifies as `judgment` even though it unambiguously names a file. Before this commit it classified `file-existence` and `run_checks()` would deterministically FAIL if the file were absent. After this commit, `parse_checks()` routes it to the `judgment` bucket, `check_runner.run_checks()` never touches it (it becomes a `skipped` entry, not a checked-and-failed one), and the only remaining defenses are (a) the LLM semantic verdict in `requirement_met.py`, which the module's own docstring calls gameable/advisory-only and never blocking alone, and (b) `_artifact_in_diff_hunk()`, a deterministic but weak substring check that only requires the literal token to appear in *some* added non-comment code line of the diff — it does not require the artifact to actually exist as a file. I confirmed both halves of the chain live:

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2278-implementation
python3 -c "
import sys, tempfile
sys.path.insert(0,'gates')
import check_runner as cr
section = '''
- check: \`LICENSE\` file is added to the repo root
'''
checks = cr.parse_checks(section)
print('classified as:', checks)
with tempfile.TemporaryDirectory() as td:
    mech = [c for c in checks if c['type'] != 'judgment']
    skipped = [c for c in checks if c['type'] == 'judgment']
    results = cr.run_checks(td, mech)
    print('mechanical results (LICENSE never created in td):', results)
    print(cr.format_comment(results, skipped))
"
python3 -c "
import sys
sys.path.insert(0,'gates')
import requirement_met as rm
diff = '''diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1,1 +1,2 @@
 x = 1
+NOTE = \"see LICENSE for terms, not actually adding the file\"
'''
print('artifact_in_diff satisfied without the file existing:', rm._artifact_in_diff_hunk('LICENSE', diff))
"
```

### Observed
```
classified as: [{'type': 'judgment', 'raw': '`LICENSE` file is added to the repo root'}]
mechanical results (LICENSE never created in td): []
## Acceptance check-runner result: no checks declared

이 이슈의 `## Acceptance` 절에 있는 1개 `check:`/`gate:` 항목이 전부 판단이 필요한(judgment) 기준이라 기계적으로 실행할 검사가 없다. ...
- `LICENSE` file is added to the repo root

artifact_in_diff satisfied without the file existing: True
```
The `LICENSE` file was never created anywhere in the fixture, yet check_runner records zero mechanical checks (the criterion is fully skipped, not failed), and `requirement_met.py`'s only remaining deterministic sub-check (`_artifact_in_diff_hunk`) is satisfied by an unrelated prose-in-code mention of the string "LICENSE" — no actual file needed. Nothing in the pipeline any longer hard-fails a PR that claims `check: \`LICENSE\` file is added\` but never adds it.

### Expected
A criterion that literally names a bare filename (extensionless, no `/`) and claims a file with that exact name is added should still classify `file-existence` and mechanically FAIL when the named file is absent, the same as it did before this commit for e.g. `existing.txt`. The fix's own stated intent ("path-shaped-but-missing artifacts still classify file-existence and still genuinely FAIL") does not hold for this whole class of real, extensionless filenames because `_looks_like_path()` requires a `.`-delimited known extension whenever there is no `/` in the token — it has no fallback for bare-filename tokens that are neither commands, measurement prose, nor slash-qualified paths.

### Stance 4 — "find the write-set gap"

Grepped for other callers of `check_runner.parse_checks`/its classifier contract outside the three already-rerun test files. `tests/test_check_run_artifact.py` references `check_runner` but builds its `_sample_checks()` fixture as a hand-written dict literal (`{"type": "file-existence", "raw": "\`existing.txt\`", "path": "existing.txt"}`) rather than calling `parse_checks()`, so it is not exercising the classifier and is unaffected by the default flip. `docs/specs/artifact-smoke-contract.md`'s "Mechanical layer" section documents the interpreter-allowlist and artifact-smoke behavior of `check_runner.py` but makes no claim about the file-existence-vs-judgment default, so it isn't rendered stale by this change either. No other file in the repo asserts on or documents the old unmatched-backtick-defaults-to-file-existence contract. NO FINDING for this stance (superseded in this dispatch by the stance-0 finding above, per the one-finding cap).
