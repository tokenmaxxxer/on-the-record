---
proposal: docs/issue-2204/proposals/2026-08-24-conformance-review-issue-2204.md
---

# Hunt record — conformance-review-issue-2204

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass, or the nearest analogue for a docs-only change

Verdict: FINDING — the proposal's own "How you'll know it worked" bullet
names `python3 -m gates.record_lint docs/issue-2204/reports/conformance-review.md`
as the phase-2 verification command; run exactly as stated, it crashes
before inspecting the file, instead of reporting "zero violations."
Kind: design-error
Seed: docs/issue-2204/proposals/2026-08-24-conformance-review-issue-2204.md, docs/issue-2204/reports/conformance-review/survey.md (two new files, docs-only, no code touched)
cap_seconds: 60
tier: default (size:docs-only)
diff_stat_lines: 2 new files under docs/issue-2204/ (proposal + survey)
started_at: 2026-08-24T00:00:00Z
ended_at: 2026-08-24T00:15:00Z

### Reproduce
```
$ python3 -m gates.record_lint docs/issue-2204/reports/conformance-review.md
```
canonical: docs/issue-2204/proposals/2026-08-24-conformance-review-issue-2204.md
— "How you'll know it worked" bullet: "`python3 -m gates.record_lint
docs/issue-2204/reports/conformance-review.md` reports zero violations
against the written record" — this is that exact command, pasted above.

### Observed
```
Traceback (most recent call last):
  File "/usr/lib/python3.10/runpy.py", line 196, in _run_module_as_main
    return _run_code(code, main_globals, None,
  File "/usr/lib/python3.10/runpy.py", line 86, in _run_code
    exec(code, run_globals)
  File "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2204-conformance-review/gates/record_lint.py", line 31, in <module>
    RECORD_PATH = gates.RECORD_PATH  # docs/issue-<n>/reports/<role>.md
AttributeError: module 'gates' has no attribute 'RECORD_PATH'
```
derived: python3 -m gates.record_lint docs/issue-2204/reports/conformance-review.md
— pasted exit trace above (executed this session), not "zero violations."

### Root cause
```
sys.path.insert(0, str(Path(__file__).parent))
import gates

RECORD_PATH = gates.RECORD_PATH  # docs/issue-<n>/reports/<role>.md
```
canonical: gates/record_lint.py lines 28-31 — pasted above verbatim.
`gates/` is a namespace package (no `__init__.py`); `python3 -m
gates.record_lint` binds that namespace package into
`sys.modules['gates']` before this line runs, so `import gates` above
reuses the cached namespace object instead of resolving `gates/gates.py`
via the freshly-prepended `sys.path` entry, and `gates.RECORD_PATH` is
absent from it — matching the traceback pasted in Observed above.

```
  python3 -m gates.record_lint <record-path>
  python3 -m gates.record_lint            # scans the whole repo
```
canonical: gates/record_lint.py lines 18-19 (module docstring) — pasted
above verbatim; this is the exact `-m` invocation form the proposal's
own bullet reuses, and it is the form that crashes.

Direct-script invocation, as a control:
```
$ python3 gates/record_lint.py docs/issue-2204/reports/conformance-review/survey.md
- 레코드 경로 형태가 아니다: docs/issue-2204/reports/conformance-review/survey.md — docs/issue-<n>/reports/<role>.md 형태여야 한다.
```
derived: python3 gates/record_lint.py docs/issue-2204/reports/conformance-review/survey.md
— pasted output above (executed this session); this correctly rejects a
non-record path instead of crashing.

### Expected
```
  python3 -m gates.record_lint <record-path>
```
canonical: gates/record_lint.py line 18 — the module's own documented
CLI form, matching the proposal's own bullet, should run and report
violations (or none) against the file argument, not crash on import
before reading it.
